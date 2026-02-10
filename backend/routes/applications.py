"""Applications (Dosare) - Complete workflow routes"""
from fastapi import APIRouter, HTTPException, Depends, UploadFile, File, Form
from fastapi.responses import FileResponse
from pydantic import BaseModel
from typing import Optional, List
import uuid, os, json, zipfile, io
from datetime import datetime, timezone
from middleware.auth_middleware import get_current_user
from services.funding_service import (
    get_programs, get_measures, get_calls, get_call, get_templates, get_template,
    APPLICATION_STATES, APPLICATION_STATE_LABELS, APPLICATION_TRANSITIONS, DEFAULT_FOLDER_GROUPS
)
from services.ai_service import generate_document_section, validate_coherence, check_eligibility
from services.pdf_service import generate_pdf
from services.orchestrator_service import run_orchestrator_check

router = APIRouter(prefix="/api/v2", tags=["applications"])
db = None

def set_db(database):
    global db
    db = database

# --- Catalog ---
@router.get("/programs")
async def list_programs():
    programs = get_programs()
    for p in programs:
        p["measures"] = get_measures(p["id"])
        for m in p["measures"]:
            m["calls"] = get_calls(m["id"])
    return programs

@router.get("/calls")
async def list_calls(status: Optional[str] = None):
    calls = get_calls()
    if status: calls = [c for c in calls if c["status"] == status]
    for c in calls:
        m = next((m for m in get_measures() if m["id"] == c["measure_id"]), {})
        p = next((p for p in get_programs() if p["id"] == m.get("program_id")), {})
        c["measure_name"] = m.get("name", "")
        c["measure_code"] = m.get("code", "")
        c["program_name"] = p.get("name", "")
    return calls

@router.get("/calls/{call_id}")
async def get_call_detail(call_id: str):
    c = get_call(call_id)
    if not c: raise HTTPException(404, "Sesiune negăsită")
    return c

@router.get("/templates")
async def list_templates():
    return get_templates()

# SICAP / AFIR search
SICAP_CPV = [
    {"cod": "30200000-1", "descriere": "Echipamente informatice", "pret_referinta_min": 500, "pret_referinta_max": 15000},
    {"cod": "30213100-6", "descriere": "Laptopuri", "pret_referinta_min": 2000, "pret_referinta_max": 8000},
    {"cod": "48000000-8", "descriere": "Software și sisteme informatice", "pret_referinta_min": 1000, "pret_referinta_max": 50000},
    {"cod": "72000000-5", "descriere": "Servicii IT", "pret_referinta_min": 5000, "pret_referinta_max": 200000},
    {"cod": "45000000-7", "descriere": "Lucrări de construcții", "pret_referinta_min": 50000, "pret_referinta_max": 5000000},
    {"cod": "42000000-6", "descriere": "Mașini industriale", "pret_referinta_min": 10000, "pret_referinta_max": 500000},
    {"cod": "09331200-0", "descriere": "Module solare fotovoltaice", "pret_referinta_min": 10000, "pret_referinta_max": 200000},
    {"cod": "34100000-8", "descriere": "Autovehicule", "pret_referinta_min": 15000, "pret_referinta_max": 150000},
    {"cod": "39100000-3", "descriere": "Mobilier", "pret_referinta_min": 500, "pret_referinta_max": 30000},
]
AFIR_PRETURI = [
    {"categorie": "Utilaje", "subcategorie": "Tractor", "pret_min": 25000, "pret_max": 120000, "unitate": "buc"},
    {"categorie": "Utilaje", "subcategorie": "Combină", "pret_min": 80000, "pret_max": 350000, "unitate": "buc"},
    {"categorie": "Construcții", "subcategorie": "Hală depozitare", "pret_min": 200, "pret_max": 500, "unitate": "mp"},
    {"categorie": "IT", "subcategorie": "Laptop", "pret_min": 2000, "pret_max": 6000, "unitate": "buc"},
    {"categorie": "IT", "subcategorie": "Server", "pret_min": 5000, "pret_max": 30000, "unitate": "buc"},
    {"categorie": "Energie", "subcategorie": "Panou fotovoltaic", "pret_min": 200, "pret_max": 500, "unitate": "buc"},
    {"categorie": "Transport", "subcategorie": "Autoutilitară", "pret_min": 20000, "pret_max": 80000, "unitate": "buc"},
]

@router.get("/sicap/search")
async def sicap_search(q: str):
    if len(q) < 2: return []
    return [c for c in SICAP_CPV if q.lower() in c["descriere"].lower() or q.lower() in c["cod"]]

@router.get("/afir/preturi")
async def afir_search(q: str):
    if len(q) < 2: return []
    return [p for p in AFIR_PRETURI if q.lower() in p["subcategorie"].lower() or q.lower() in p["categorie"].lower()]


@router.get("/drafts/download/{filename}")
async def download_draft_pdf(filename: str):
    filepath = os.path.join(os.path.dirname(os.path.dirname(__file__)), "uploads", "generated", filename)
    if not os.path.exists(filepath):
        raise HTTPException(404, "Fișier negăsit")
    return FileResponse(filepath, media_type="application/pdf", filename=filename)

@router.get("/states")
async def get_states():
    return {"states": APPLICATION_STATE_LABELS, "transitions": APPLICATION_TRANSITIONS, "order": APPLICATION_STATES}

# --- Applications (Dosare/Proiecte) ---
class CreateApplicationRequest(BaseModel):
    company_id: str
    call_id: Optional[str] = None
    title: str
    description: Optional[str] = ""
    custom_program: Optional[str] = None
    custom_measure: Optional[str] = None
    custom_session: Optional[str] = None
    custom_links: Optional[List[str]] = []

class TransitionRequest(BaseModel):
    new_state: str
    reason: Optional[str] = ""

class GenerateDescriptionRequest(BaseModel):
    title: str
    call_id: Optional[str] = None
    custom_session: Optional[str] = None

@router.post("/applications/generate-description")
async def generate_description(req: GenerateDescriptionRequest, current_user: dict = Depends(get_current_user)):
    """AI generates a short description based on title and session info."""
    call = get_call(req.call_id) if req.call_id else None
    context = f"Titlu proiect: {req.title}"
    if call:
        context += f"\nSesiune: {call['name']}, Buget: {call.get('value_min')}-{call.get('value_max')} RON, Beneficiari: {', '.join(call.get('beneficiaries', []))}"
    if req.custom_session:
        context += f"\nSesiune custom: {req.custom_session}"

    from services.ai_service import chat_navigator
    result = await chat_navigator(
        f"Generează o descriere scurtă (2-3 propoziții) pentru un proiect de finanțare cu aceste date:\n{context}\nDescriere concisă, profesională, în limba română. Doar textul, fără formatare.",
        {}
    )
    return {"description": result.get("result", "")}

@router.post("/applications")
async def create_application(req: CreateApplicationRequest, current_user: dict = Depends(get_current_user)):
    call = get_call(req.call_id) if req.call_id else None
    org = await db.organizations.find_one({"id": req.company_id}, {"_id": 0})
    if not org: raise HTTPException(404, "Firmă negăsită")

    app_id = str(uuid.uuid4())

    if call:
        m = next((m for m in get_measures() if m["id"] == call["measure_id"]), {})
        p = next((p for p in get_programs() if p["id"] == m.get("program_id")), {})
        call_name = call["name"]
        call_code = call.get("code")
        measure_name = m.get("name")
        measure_code = m.get("code")
        program_name = p.get("name")
    else:
        call_name = req.custom_session or "Sesiune custom"
        call_code = ""
        measure_name = req.custom_measure or ""
        measure_code = ""
        program_name = req.custom_program or ""

    # If custom links provided, extract session data from pages
    extracted_data = {}
    if req.custom_links:
        try:
            import httpx
            from services.ai_service import chat_navigator
            scraped_texts = []
            async with httpx.AsyncClient(timeout=15, follow_redirects=True) as client:
                for link in req.custom_links[:3]:  # Max 3 links
                    try:
                        resp = await client.get(link, headers={"User-Agent": "GrantFlow/1.0"})
                        if resp.status_code == 200:
                            # Extract text content (strip HTML)
                            import re
                            text = re.sub(r'<[^>]+>', ' ', resp.text)
                            text = re.sub(r'\s+', ' ', text).strip()[:5000]
                            scraped_texts.append(f"[{link}]: {text}")
                    except Exception as e:
                        scraped_texts.append(f"[{link}]: Eroare acces - {str(e)[:100]}")

            if scraped_texts:
                extract_result = await chat_navigator(
                    "Din textele de mai jos (pagini web despre un program de finanțare), extrage:\n"
                    "- Numele programului\n- Codul și numele măsurii\n- Numele sesiunii/apelului\n"
                    "- Data start și end\n- Buget total\n- Valoare min/max proiect\n- Tip beneficiari\n"
                    "- Orice alte detalii relevante (criterii, documente cerute)\n\n"
                    + "\n\n".join(scraped_texts),
                    {}
                )
                extracted_data["scraped_info"] = extract_result.get("result", "")

                # Try to fill in missing fields from extraction
                if not program_name and req.custom_program:
                    program_name = req.custom_program
                if not call_name or call_name == "Sesiune custom":
                    call_name = req.custom_session or "Sesiune din link-uri"

        except Exception as e:
            import logging
            logging.getLogger(__name__).error(f"Link extraction failed: {e}")

    initial_status = "call_selected"
    initial_history = [
        {"from": None, "to": "draft", "at": datetime.now(timezone.utc).isoformat(), "by": current_user["user_id"], "reason": "Proiect creat"},
        {"from": "draft", "to": "call_selected", "at": datetime.now(timezone.utc).isoformat(), "by": current_user["user_id"], "reason": f"Sesiune: {call_name}"}
    ]

    # If we have extracted data from links, auto-advance to guide_ready
    if extracted_data.get("scraped_info"):
        initial_status = "guide_ready"
        initial_history.append({
            "from": "call_selected", "to": "guide_ready",
            "at": datetime.now(timezone.utc).isoformat(), "by": "agent_colector",
            "reason": "Date sesiune extrase automat din link-uri"
        })

    application = {
        "id": app_id, "title": req.title, "description": req.description,
        "company_id": req.company_id, "company_name": org["denumire"], "company_cui": org.get("cui"),
        "call_id": req.call_id, "call_name": call_name, "call_code": call_code,
        "measure_name": measure_name, "measure_code": measure_code,
        "program_name": program_name,
        "custom_links": req.custom_links or [],
        "extracted_data": extracted_data,
        "status": initial_status, "status_label": APPLICATION_STATE_LABELS[initial_status],
        "history": initial_history,
        "guide_assets": [], "required_documents": [], "checklist_frozen": False,
        "folder_groups": DEFAULT_FOLDER_GROUPS,
        "documents": [], "drafts": [], "procurement": [],
        "budget_estimated": call.get("value_max", 0) if call else 0,
        "budget_approved": 0, "expenses_total": 0,
        "call_budget": call.get("budget") if call else None,
        "call_value_min": call.get("value_min") if call else None,
        "call_value_max": call.get("value_max") if call else None,
        "call_beneficiaries": call.get("beneficiaries") if call else [],
        "call_region": call.get("region") if call else None,
        "call_start_date": call.get("start_date") if call else None,
        "call_end_date": call.get("end_date") if call else None,
        "company_context": {
            "denumire": org.get("denumire"), "cui": org.get("cui"),
            "forma_juridica": org.get("forma_juridica"), "caen_principal": org.get("caen_principal"),
            "adresa": org.get("adresa"), "judet": org.get("judet"),
            "nr_angajati": org.get("nr_angajati"), "data_infiintare": org.get("data_infiintare")
        },
        "created_at": datetime.now(timezone.utc).isoformat(),
        "updated_at": datetime.now(timezone.utc).isoformat(),
        "created_by": current_user["user_id"]
    }
    await db.applications.insert_one(application)

    # Log agent run for link extraction
    if extracted_data.get("scraped_info"):
        await db.agent_runs.insert_one({
            "id": str(uuid.uuid4()), "agent_id": "colector",
            "application_id": app_id, "action": "extract_from_links",
            "input": {"links": req.custom_links},
            "output": {"extracted": bool(extracted_data.get("scraped_info"))},
            "timestamp": datetime.now(timezone.utc).isoformat(), "user_id": current_user["user_id"]
        })

    await db.audit_log.insert_one({"id": str(uuid.uuid4()), "action": "application.created", "entity_type": "application", "entity_id": app_id, "user_id": current_user["user_id"], "details": {"title": req.title, "call": call_name, "links_extracted": bool(extracted_data)}, "timestamp": datetime.now(timezone.utc).isoformat()})
    application.pop("_id", None)
    return application

@router.get("/applications")
async def list_applications(company_id: Optional[str] = None, current_user: dict = Depends(get_current_user)):
    q = {}
    if company_id: q["company_id"] = company_id
    apps = await db.applications.find(q, {"_id": 0}).to_list(100)
    return apps

@router.get("/applications/{app_id}")
async def get_application(app_id: str, current_user: dict = Depends(get_current_user)):
    app = await db.applications.find_one({"id": app_id}, {"_id": 0})
    if not app: raise HTTPException(404, "Dosar negăsit")
    return app

@router.put("/applications/{app_id}")
async def update_application(app_id: str, updates: dict, current_user: dict = Depends(get_current_user)):
    """Update application config fields."""
    allowed = ["tip_proiect", "locatie_implementare", "judet_implementare", "tema_proiect", "achizitii", "budget_estimated", "description"]
    data = {k: v for k, v in updates.items() if k in allowed}
    data["updated_at"] = datetime.now(timezone.utc).isoformat()
    await db.applications.update_one({"id": app_id}, {"$set": data})
    app = await db.applications.find_one({"id": app_id}, {"_id": 0})
    return app

class CustomTemplateRequest(BaseModel):
    label: str
    sections: List[str]

@router.post("/applications/{app_id}/custom-template")
async def add_custom_template(app_id: str, req: CustomTemplateRequest, current_user: dict = Depends(get_current_user)):
    """User creates a custom draft template for this application."""
    tpl = {"id": f"custom_{uuid.uuid4().hex[:8]}", "label": req.label, "category": "custom", "sections": req.sections, "created_by": current_user["user_id"], "created_at": datetime.now(timezone.utc).isoformat()}
    await db.applications.update_one({"id": app_id}, {"$push": {"custom_templates": tpl}})
    return tpl

@router.post("/applications/{app_id}/transition")
async def transition_application(app_id: str, req: TransitionRequest, current_user: dict = Depends(get_current_user)):
    app = await db.applications.find_one({"id": app_id}, {"_id": 0})
    if not app: raise HTTPException(404, "Dosar negăsit")
    current = app["status"]
    if req.new_state not in APPLICATION_TRANSITIONS.get(current, []):
        raise HTTPException(400, f"Tranziția {current} → {req.new_state} nu este permisă")
    entry = {"from": current, "to": req.new_state, "at": datetime.now(timezone.utc).isoformat(), "by": current_user["user_id"], "reason": req.reason or ""}
    await db.applications.update_one({"id": app_id}, {"$set": {"status": req.new_state, "status_label": APPLICATION_STATE_LABELS.get(req.new_state), "updated_at": datetime.now(timezone.utc).isoformat()}, "$push": {"history": entry}})
    await db.audit_log.insert_one({"id": str(uuid.uuid4()), "action": "application.transition", "entity_type": "application", "entity_id": app_id, "user_id": current_user["user_id"], "details": {"from": current, "to": req.new_state}, "timestamp": datetime.now(timezone.utc).isoformat()})
    return {"message": f"Dosar mutat: {APPLICATION_STATE_LABELS.get(req.new_state)}", "new_state": req.new_state}

# --- Guide & Annexes ---
@router.post("/applications/{app_id}/guide")
async def upload_guide(app_id: str, file: UploadFile = File(...), tip: str = Form("ghid"), current_user: dict = Depends(get_current_user)):
    upload_dir = os.path.join(os.path.dirname(os.path.dirname(__file__)), "uploads", "guides")
    os.makedirs(upload_dir, exist_ok=True)
    fid = str(uuid.uuid4())
    ext = os.path.splitext(file.filename)[1] if file.filename else ""
    safe = f"{fid}{ext}"
    raw_content = await file.read()
    filepath = os.path.join(upload_dir, safe)
    with open(filepath, "wb") as f: f.write(raw_content)

    asset = {"id": fid, "filename": file.filename, "stored_name": safe, "file_size": len(raw_content), "tip": tip, "uploaded_at": datetime.now(timezone.utc).isoformat(), "uploaded_by": current_user["user_id"]}
    agent_actions = []

    # === AGENT PARSER: Extract text content from guide ===
    try:
        import base64
        from emergentintegrations.llm.chat import LlmChat, UserMessage, FileContent

        ext_lower = ext.lower()
        ct_map = {".pdf": "application/pdf", ".jpg": "image/jpeg", ".jpeg": "image/jpeg", ".png": "image/png"}
        content_type = ct_map.get(ext_lower)

        # Load custom rules for parser agent
        parser_rules = await db.agent_rules.find_one({"agent_id": "parser", "user_id": current_user["user_id"]}, {"_id": 0})
        parser_extra = "\n".join(parser_rules.get("reguli", [])) if parser_rules else ""

        chat = LlmChat(api_key=os.environ.get("EMERGENT_LLM_KEY", ""), session_id=str(uuid.uuid4()),
            system_message="Ești expert în analiză ghiduri de finanțare din România. Extrage informații structurate." + (f"\nReguli suplimentare: {parser_extra}" if parser_extra else ""))
        chat.with_model("openai", "gpt-5.2")

        extract_prompt = (
            "Analizează acest document (ghid solicitant / anexă / procedură de evaluare) și extrage TOATE informațiile relevante.\n"
            "Returnează un JSON STRICT cu aceste câmpuri:\n"
            '{\n'
            '  "tip_document": "ghid_solicitant / procedura_evaluare / anexa / grila_conformitate / altul",\n'
            '  "program": "numele programului",\n'
            '  "masura": "codul și numele măsurii",\n'
            '  "sesiune": "numele sesiunii/apelului",\n'
            '  "buget_total": "number sau null",\n'
            '  "valoare_min_proiect": "number sau null",\n'
            '  "valoare_max_proiect": "number sau null",\n'
            '  "beneficiari_eligibili": ["lista tipurilor de beneficiari"],\n'
            '  "criterii_eligibilitate": ["lista criteriilor de eligibilitate"],\n'
            '  "documente_obligatorii": [{"nume": "string", "obligatoriu": true/false}],\n'
            '  "grila_conformitate": [{"criteriu": "string", "punctaj_max": "number sau null"}],\n'
            '  "termene": {"data_start": "string", "data_sfarsit": "string"},\n'
            '  "activitati_eligibile": ["lista activităților eligibile"],\n'
            '  "cheltuieli_eligibile": ["lista cheltuielilor eligibile"],\n'
            '  "rezumat": "rezumat 3-5 propoziții"\n'
            '}\n'
            "IMPORTANT: Returnează DOAR JSON-ul valid. Dacă un câmp nu e disponibil, pune null."
        )

        if content_type in ["application/pdf", "image/jpeg", "image/png"]:
            b64 = base64.b64encode(raw_content).decode("utf-8")
            msg = UserMessage(text=extract_prompt, file_contents=[FileContent(content_type=content_type, file_content_base64=b64)])
        else:
            try:
                text = raw_content.decode("utf-8", errors="replace")
            except Exception:
                text = raw_content.decode("latin-1", errors="replace")
            msg = UserMessage(text=f"{extract_prompt}\n\nCONȚINUT DOCUMENT:\n{text[:8000]}")

        response = await chat.send_message(msg)

        # Parse JSON from response
        import json as json_mod, re
        clean = response.strip()
        if clean.startswith("```"): clean = clean.split("\n", 1)[1] if "\n" in clean else clean[3:]
        if clean.endswith("```"): clean = clean[:-3]
        if clean.startswith("json"): clean = clean[4:]
        clean = clean.strip()
        start = clean.find("{")
        end = clean.rfind("}") + 1
        extracted = {}
        if start >= 0 and end > start:
            try:
                extracted = json_mod.loads(clean[start:end])
            except Exception:
                pass

        asset["extracted_content"] = extracted
        asset["extraction_status"] = "completed" if extracted else "failed"
        agent_actions.append(f"Parser: Document analizat, {len(extracted)} câmpuri extrase")

        # === AUTO-ACTIONS based on extracted content ===
        app = await db.applications.find_one({"id": app_id}, {"_id": 0})

        # 1. Update program/session info if missing
        if extracted and app:
            updates = {}
            if extracted.get("program") and not app.get("program_name"):
                updates["program_name"] = extracted["program"]
            if extracted.get("masura") and not app.get("measure_name"):
                updates["measure_name"] = extracted["masura"]
            if extracted.get("sesiune") and (not app.get("call_name") or app.get("call_name") == "Sesiune custom"):
                updates["call_name"] = extracted["sesiune"]
            if extracted.get("valoare_max_proiect") and not app.get("budget_estimated"):
                try:
                    updates["budget_estimated"] = float(extracted["valoare_max_proiect"])
                    updates["call_value_max"] = float(extracted["valoare_max_proiect"])
                except (ValueError, TypeError): pass
            if extracted.get("valoare_min_proiect"):
                try: updates["call_value_min"] = float(extracted["valoare_min_proiect"])
                except (ValueError, TypeError): pass
            if extracted.get("buget_total"):
                try: updates["call_budget"] = float(extracted["buget_total"])
                except (ValueError, TypeError): pass
            if extracted.get("beneficiari_eligibili"):
                updates["call_beneficiaries"] = extracted["beneficiari_eligibili"]
            if updates:
                updates["updated_at"] = datetime.now(timezone.utc).isoformat()
                await db.applications.update_one({"id": app_id}, {"$set": updates})
                agent_actions.append(f"Colector: Actualizate {', '.join(updates.keys())}")

        # 2. Auto-propose required documents from guide
        if extracted.get("documente_obligatorii") and app and not app.get("checklist_frozen"):
            existing_names = [r.get("official_name", "").lower() for r in app.get("required_documents", [])]
            new_docs = []
            for i, doc_req in enumerate(extracted["documente_obligatorii"]):
                name = doc_req.get("nume", "") if isinstance(doc_req, dict) else str(doc_req)
                if name and name.lower() not in existing_names:
                    new_docs.append({
                        "id": str(uuid.uuid4()), "order_index": len(existing_names) + len(new_docs) + 1,
                        "official_name": name, "required": doc_req.get("obligatoriu", True) if isinstance(doc_req, dict) else True,
                        "folder_group": "depunere", "status": "missing", "source": "ghid_auto"
                    })
            if new_docs:
                await db.applications.update_one({"id": app_id}, {"$push": {"required_documents": {"$each": new_docs}}})
                agent_actions.append(f"Checklist: {len(new_docs)} documente cerute adăugate automat din ghid")

        # 3. Store eligibility criteria for later use
        if extracted.get("criterii_eligibilitate"):
            await db.applications.update_one({"id": app_id}, {"$set": {"criterii_eligibilitate_ghid": extracted["criterii_eligibilitate"]}})
            agent_actions.append(f"Eligibilitate: {len(extracted['criterii_eligibilitate'])} criterii extrase din ghid")

        # 4. Store conformity grid
        if extracted.get("grila_conformitate"):
            await db.applications.update_one({"id": app_id}, {"$set": {"grila_conformitate_ghid": extracted["grila_conformitate"]}})
            agent_actions.append(f"Evaluator: Grilă conformitate cu {len(extracted['grila_conformitate'])} criterii extrasă")

        # 5. Store eligible activities/expenses
        if extracted.get("activitati_eligibile"):
            await db.applications.update_one({"id": app_id}, {"$set": {"activitati_eligibile": extracted["activitati_eligibile"]}})
        if extracted.get("cheltuieli_eligibile"):
            await db.applications.update_one({"id": app_id}, {"$set": {"cheltuieli_eligibile": extracted["cheltuieli_eligibile"]}})

    except Exception as e:
        import logging
        logging.getLogger(__name__).error(f"Guide extraction failed: {e}")
        asset["extraction_status"] = "error"
        asset["extraction_error"] = str(e)[:200]
        agent_actions.append(f"Eroare parsare ghid: {str(e)[:100]}")

    # Save asset with extraction results
    await db.applications.update_one({"id": app_id}, {"$push": {"guide_assets": asset}, "$set": {"updated_at": datetime.now(timezone.utc).isoformat()}})

    # Auto-transition to guide_ready
    app = await db.applications.find_one({"id": app_id}, {"_id": 0})
    if app and app["status"] == "call_selected":
        await db.applications.update_one({"id": app_id}, {"$set": {"status": "guide_ready", "status_label": APPLICATION_STATE_LABELS["guide_ready"]}, "$push": {"history": {"from": "call_selected", "to": "guide_ready", "at": datetime.now(timezone.utc).isoformat(), "by": "orchestrator", "reason": "Ghid procesat automat"}}})

    # Log all agent runs
    for action in agent_actions:
        agent_name = action.split(":")[0].strip().lower()
        await db.agent_runs.insert_one({
            "id": str(uuid.uuid4()), "agent_id": agent_name if agent_name in ["parser", "colector", "eligibilitate", "evaluator", "checklist"] else "orchestrator",
            "application_id": app_id, "action": "guide_upload_processing",
            "input": {"filename": file.filename, "tip": tip},
            "output": {"action": action},
            "timestamp": datetime.now(timezone.utc).isoformat(), "user_id": current_user["user_id"]
        })

    await db.audit_log.insert_one({
        "id": str(uuid.uuid4()), "action": "guide.uploaded_and_processed",
        "entity_type": "application", "entity_id": app_id,
        "user_id": current_user["user_id"],
        "details": {"filename": file.filename, "actions": agent_actions},
        "timestamp": datetime.now(timezone.utc).isoformat()
    })

    asset["agent_actions"] = agent_actions
    return asset

# --- Required Documents (Checklist) ---
class RequiredDocumentRequest(BaseModel):
    official_name: str
    required: bool = True
    folder_group: str = "depunere"
    guide_reference: Optional[str] = None

@router.post("/applications/{app_id}/required-docs")
async def add_required_doc(app_id: str, req: RequiredDocumentRequest, current_user: dict = Depends(get_current_user)):
    app = await db.applications.find_one({"id": app_id}, {"_id": 0})
    if not app: raise HTTPException(404)
    if app.get("checklist_frozen"): raise HTTPException(400, "Checklist-ul este înghețat")
    existing = app.get("required_documents", [])
    doc = {"id": str(uuid.uuid4()), "order_index": len(existing) + 1, "official_name": req.official_name, "required": req.required, "folder_group": req.folder_group, "guide_reference": req.guide_reference, "status": "missing"}
    await db.applications.update_one({"id": app_id}, {"$push": {"required_documents": doc}})
    return doc

@router.post("/applications/{app_id}/required-docs/propose")
async def propose_required_docs(app_id: str, current_user: dict = Depends(get_current_user)):
    """AI agent proposes required documents from guide."""
    app = await db.applications.find_one({"id": app_id}, {"_id": 0})
    if not app: raise HTTPException(404)
    guide_info = ", ".join([a["filename"] for a in app.get("guide_assets", [])])
    call = get_call(app.get("call_id", ""))
    prompt_data = {"call": call, "guide_files": guide_info, "program": app.get("program_name")}
    result = await generate_document_section(template="Lista documente obligatorii conform ghidului solicitantului", data=prompt_data, section="Extrage lista completă de documente cerute, cu folder și ordine")
    # Parse proposed docs
    return {"proposed_text": result.get("result", ""), "source": "AI Agent"}

@router.post("/applications/{app_id}/required-docs/freeze")
async def freeze_checklist(app_id: str, current_user: dict = Depends(get_current_user)):
    await db.applications.update_one({"id": app_id}, {"$set": {"checklist_frozen": True, "updated_at": datetime.now(timezone.utc).isoformat()}})
    return {"message": "Checklist înghețat"}

# --- Documents in folders ---
@router.post("/applications/{app_id}/documents")
async def upload_app_document(app_id: str, file: UploadFile = File(...), folder_group: str = Form("depunere"), required_doc_id: Optional[str] = Form(None), tip_document: Optional[str] = Form(None), current_user: dict = Depends(get_current_user)):
    upload_dir = os.path.join(os.path.dirname(os.path.dirname(__file__)), "uploads", "app_docs")
    os.makedirs(upload_dir, exist_ok=True)
    did = str(uuid.uuid4())
    ext = os.path.splitext(file.filename)[1] if file.filename else ""
    safe = f"{did}{ext}"
    content = await file.read()
    filepath = os.path.join(upload_dir, safe)
    with open(filepath, "wb") as f: f.write(content)

    # Auto-detect document type from filename
    fname_lower = (file.filename or "").lower()
    if not tip_document:
        if any(k in fname_lower for k in ["factur", "invoice"]): tip_document = "factura"
        elif any(k in fname_lower for k in ["bilant", "balant", "balance"]): tip_document = "bilant"
        elif any(k in fname_lower for k in ["contract"]): tip_document = "contract"
        elif any(k in fname_lower for k in ["ci", "buletin", "carte_identitate"]): tip_document = "ci"
        elif any(k in fname_lower for k in ["certificat", "onrc"]): tip_document = "certificat"
        elif any(k in fname_lower for k in ["declarati"]): tip_document = "declaratie"
        elif any(k in fname_lower for k in ["ofert"]): tip_document = "oferta"
        elif any(k in fname_lower for k in ["cv", "curriculum"]): tip_document = "cv"
        else: tip_document = "altele"

    doc = {
        "id": did, "filename": file.filename, "stored_name": safe,
        "file_size": len(content), "content_type": file.content_type,
        "folder_group": folder_group, "required_doc_id": required_doc_id,
        "tip_document": tip_document,
        "status": "uploaded", "ocr_status": "processing",
        "uploaded_at": datetime.now(timezone.utc).isoformat(),
        "uploaded_by": current_user["user_id"]
    }
    await db.applications.update_one({"id": app_id}, {"$push": {"documents": doc}})

    # Update required doc status
    if required_doc_id:
        await db.applications.update_one(
            {"id": app_id, "required_documents.id": required_doc_id},
            {"$set": {"required_documents.$.status": "uploaded"}}
        )

    # Run OCR automatically
    ocr_actions = []
    try:
        from services.ocr_service import process_ocr
        ocr_result = await process_ocr(did, tip_document, file.filename, db, file_path=filepath)
        doc["ocr_status"] = ocr_result.get("status", "pending")
        doc["ocr_data"] = ocr_result
        ocr_actions.append(f"OCR executat: {ocr_result.get('status')} (încredere: {ocr_result.get('overall_confidence', 0):.0%})")

        # Update doc with OCR results
        await db.applications.update_one(
            {"id": app_id, "documents.id": did},
            {"$set": {
                "documents.$.ocr_status": ocr_result.get("status"),
                "documents.$.ocr_data": ocr_result
            }}
        )

        # Extract and apply data based on document type
        fields = ocr_result.get("extracted_fields", {})
        app = await db.applications.find_one({"id": app_id}, {"_id": 0})

        if fields and tip_document == "factura":
            try:
                total = float(str(fields.get("total", "0")).replace(",", ".").replace(" ", ""))
                if total > 0:
                    await db.applications.update_one({"id": app_id}, {"$inc": {"expenses_total": total}})
                    ocr_actions.append(f"Cheltuială detectată: {total} RON (factură {fields.get('numar_factura', 'N/A')})")
            except (ValueError, TypeError):
                pass

        if fields and tip_document == "bilant" and app:
            company_id = app.get("company_id")
            if company_id:
                await db.organizations.update_one({"id": company_id}, {
                    "$set": {"date_financiare_ocr": fields, "updated_at": datetime.now(timezone.utc).isoformat()}
                })
                ocr_actions.append("Date financiare extrase și salvate la firmă")

        if fields and tip_document == "contract":
            ocr_actions.append(f"Contract detectat: {fields.get('numar_contract', 'N/A')} din {fields.get('data_contract', 'N/A')}")

        if fields and tip_document in ["ci", "certificat"]:
            ocr_actions.append(f"Document identitate/ONRC procesat: {len(fields)} câmpuri extrase")

    except Exception as e:
        import logging
        logging.getLogger(__name__).error(f"OCR failed for {did}: {e}")
        doc["ocr_status"] = "error"
        ocr_actions.append(f"OCR eroare: {str(e)[:100]}")

    # Log agent run
    await db.agent_runs.insert_one({
        "id": str(uuid.uuid4()), "agent_id": "parser",
        "application_id": app_id, "action": "ocr_document",
        "input": {"filename": file.filename, "tip": tip_document, "folder": folder_group},
        "output": {"ocr_status": doc.get("ocr_status"), "actions": ocr_actions},
        "timestamp": datetime.now(timezone.utc).isoformat(),
        "user_id": current_user["user_id"]
    })

    doc["ocr_actions"] = ocr_actions
    return doc

# --- Drafts ---
class GenerateDraftRequest(BaseModel):
    template_id: str
    section: Optional[str] = None

@router.post("/applications/{app_id}/drafts/generate")
async def generate_draft(app_id: str, req: GenerateDraftRequest, current_user: dict = Depends(get_current_user)):
    app = await db.applications.find_one({"id": app_id}, {"_id": 0})
    if not app: raise HTTPException(404)
    tpl = get_template(req.template_id)
    if not tpl:
        custom_tpls = app.get("custom_templates", [])
        tpl = next((t for t in custom_tpls if t["id"] == req.template_id), None)
    if not tpl: raise HTTPException(404, "Template negăsit")

    # Build full context
    from services.context_builder import build_full_context
    full_ctx = await build_full_context(app_id, db)

    section = req.section or ", ".join(tpl.get("sections", []))
    custom_rules = await db.agent_rules.find_one({"agent_id": "redactor", "user_id": current_user["user_id"]}, {"_id": 0})
    extra_rules = "\n".join(custom_rules.get("reguli", [])) if custom_rules else ""

    result = await generate_document_section(
        template=f"{tpl['label']}: {', '.join(tpl.get('sections', []))}",
        data={}, section=section,
        full_context=full_ctx, extra_rules=extra_rules
    )
    content_text = result.get("result", "")
    org = await db.organizations.find_one({"id": app.get("company_id")}, {"_id": 0})
    pdf_file = generate_pdf(tpl["label"], content_text, (org or {}).get("denumire", ""), app["title"])
    draft = {"id": str(uuid.uuid4()), "template_id": req.template_id, "template_label": tpl["label"], "content": content_text, "pdf_filename": pdf_file, "status": "draft", "version": 1, "created_at": datetime.now(timezone.utc).isoformat(), "created_by": current_user["user_id"], "applied_rules": (custom_rules.get("reguli", []) if custom_rules else [])}
    await db.applications.update_one({"id": app_id}, {"$push": {"drafts": draft}})
    gen_dir = os.path.join(os.path.dirname(os.path.dirname(__file__)), "uploads", "generated")
    doc_entry = {"id": str(uuid.uuid4()), "filename": f"{tpl['label']}.pdf", "stored_name": pdf_file, "file_size": os.path.getsize(os.path.join(gen_dir, pdf_file)), "content_type": "application/pdf", "folder_group": "depunere", "status": "uploaded", "uploaded_at": datetime.now(timezone.utc).isoformat(), "uploaded_by": current_user["user_id"], "draft_id": draft["id"]}
    await db.applications.update_one({"id": app_id}, {"$push": {"documents": doc_entry}})
    draft["pdf_url"] = f"/api/v2/drafts/download/{pdf_file}"
    await db.agent_runs.insert_one({"id": str(uuid.uuid4()), "agent_id": "redactor", "application_id": app_id, "action": "generate_draft", "input": {"template": tpl["label"]}, "output": {"draft_id": draft["id"]}, "applied_rules": draft.get("applied_rules", []), "timestamp": datetime.now(timezone.utc).isoformat(), "user_id": current_user["user_id"]})
    return draft

@router.get("/applications/{app_id}/drafts")
async def list_drafts(app_id: str, current_user: dict = Depends(get_current_user)):
    app = await db.applications.find_one({"id": app_id}, {"_id": 0, "drafts": 1})
    return app.get("drafts", []) if app else []

# --- Validation & Evaluation ---
@router.post("/applications/{app_id}/validate")
async def validate_application(app_id: str, current_user: dict = Depends(get_current_user)):
    from services.context_builder import build_full_context
    full_ctx = await build_full_context(app_id, db)
    if not full_ctx: raise HTTPException(404)
    custom_rules = await db.agent_rules.find_one({"agent_id": "validator", "user_id": current_user["user_id"]}, {"_id": 0})
    extra = "\n".join(custom_rules.get("reguli", [])) if custom_rules else ""
    result = await validate_coherence([], {}, full_context=full_ctx, extra_rules=extra)
    report = {"id": str(uuid.uuid4()), "type": "validation", "application_id": app_id, "result": result.get("result", ""), "created_at": datetime.now(timezone.utc).isoformat()}
    await db.compliance_reports.insert_one(report)
    await db.agent_runs.insert_one({"id": str(uuid.uuid4()), "agent_id": "validator", "application_id": app_id, "action": "validate", "applied_rules": (custom_rules.get("reguli", []) if custom_rules else []), "timestamp": datetime.now(timezone.utc).isoformat(), "user_id": current_user["user_id"]})
    report.pop("_id", None)
    return report

@router.post("/applications/{app_id}/evaluate")
async def evaluate_application(app_id: str, current_user: dict = Depends(get_current_user)):
    from services.context_builder import build_full_context
    full_ctx = await build_full_context(app_id, db)
    if not full_ctx: raise HTTPException(404)
    custom_rules = await db.agent_rules.find_one({"agent_id": "eligibilitate", "user_id": current_user["user_id"]}, {"_id": 0})
    extra = "\n".join(custom_rules.get("reguli", [])) if custom_rules else ""
    result = await check_eligibility({}, {}, full_context=full_ctx, extra_rules=extra)
    report = {"id": str(uuid.uuid4()), "type": "evaluation", "application_id": app_id, "result": result.get("result", ""), "created_at": datetime.now(timezone.utc).isoformat()}
    await db.compliance_reports.insert_one(report)
    await db.agent_runs.insert_one({"id": str(uuid.uuid4()), "agent_id": "eligibilitate", "application_id": app_id, "action": "evaluate", "applied_rules": (custom_rules.get("reguli", []) if custom_rules else []), "timestamp": datetime.now(timezone.utc).isoformat(), "user_id": current_user["user_id"]})
    report.pop("_id", None)
    return report

# --- ZIP Export ---
@router.get("/applications/{app_id}/export")
async def export_application_zip(app_id: str, current_user: dict = Depends(get_current_user)):
    app = await db.applications.find_one({"id": app_id}, {"_id": 0})
    if not app: raise HTTPException(404)
    zip_buffer = io.BytesIO()
    base_dirs = [
        os.path.join(os.path.dirname(os.path.dirname(__file__)), "uploads", "app_docs"),
        os.path.join(os.path.dirname(os.path.dirname(__file__)), "uploads", "generated"),
        os.path.join(os.path.dirname(os.path.dirname(__file__)), "uploads", "guides"),
    ]
    with zipfile.ZipFile(zip_buffer, 'w', zipfile.ZIP_DEFLATED) as zf:
        manifest = {"application": app["title"], "company": app.get("company_name"), "call": app.get("call_name"), "exported_at": datetime.now(timezone.utc).isoformat(), "files": []}
        for doc in app.get("documents", []):
            folder = doc.get("folder_group", "depunere")
            folder_name = next((fg["name"] for fg in app.get("folder_groups", DEFAULT_FOLDER_GROUPS) if fg["key"] == folder), f"99_{folder}")
            fname = doc.get("filename", doc.get("stored_name"))
            # Find file
            for bd in base_dirs:
                fpath = os.path.join(bd, doc.get("stored_name", ""))
                if os.path.exists(fpath):
                    zf.write(fpath, f"{folder_name}/{fname}")
                    manifest["files"].append({"folder": folder_name, "filename": fname, "status": doc.get("status")})
                    break
        # Add guide assets
        for ga in app.get("guide_assets", []):
            for bd in base_dirs:
                fpath = os.path.join(bd, ga.get("stored_name", ""))
                if os.path.exists(fpath):
                    zf.write(fpath, f"00_Ghid/{ga['filename']}")
                    break
        zf.writestr("manifest.json", json.dumps(manifest, indent=2, ensure_ascii=False))
    zip_buffer.seek(0)
    zip_path = os.path.join(os.path.dirname(os.path.dirname(__file__)), "uploads", f"export_{app_id}.zip")
    with open(zip_path, "wb") as f: f.write(zip_buffer.getvalue())
    return FileResponse(zip_path, media_type="application/zip", filename=f"Dosar_{app.get('call_code','')}.zip")


# --- Orchestrator ---
@router.post("/applications/{app_id}/orchestrator")
async def orchestrator_check(app_id: str, current_user: dict = Depends(get_current_user)):
    """Run orchestrator agent to check all agents and determine actions."""
    app = await db.applications.find_one({"id": app_id}, {"_id": 0})
    if not app: raise HTTPException(404, "Dosar negăsit")
    org = await db.organizations.find_one({"id": app.get("company_id")}, {"_id": 0})
    if not org: raise HTTPException(404, "Firmă negăsită")
    result = await run_orchestrator_check(app, org, db)
    return result
