from fastapi import APIRouter, HTTPException, Depends
from pydantic import BaseModel
from typing import Optional, List
import uuid
from datetime import datetime, timezone
from middleware.auth_middleware import get_current_user

router = APIRouter(prefix="/api/agents", tags=["agents"])
db = None

def set_db(database):
    global db
    db = database

DEFAULT_AGENTS = [
    {
        "id": "orchestrator",
        "nume": "Orchestrator",
        "descriere": "Coordonează toți agenții. Analizează starea proiectului, identifică blocajele și decide ce agent trebuie activat. Nu modifică date - doar coordonează.",
        "tip": "coordonare",
        "icon": "zap",
        "reguli_default": ["Respectă state machine-ul proiectului", "Nu modifică date critice direct", "Loghează fiecare decizie în audit"]
    },
    {
        "id": "colector",
        "nume": "Colector",
        "descriere": "Extrage date oficiale din surse externe: ONRC (OpenAPI.ro), ANAF. Validează și versionează datele firmei automat.",
        "tip": "date",
        "icon": "database",
        "reguli_default": ["Preia doar din surse oficiale", "Versionează fiecare actualizare", "Semnalează discrepanțe"]
    },
    {
        "id": "parser",
        "nume": "Parser OCR",
        "descriere": "Procesează documentele încărcate: OCR pe imagini/PDF-uri, extrage date structurate (CUI, CAEN, CNP, adrese, sume). Folosește GPT-5.2 Vision.",
        "tip": "procesare",
        "icon": "scan",
        "reguli_default": ["Extrage toate câmpurile disponibile", "Marchează câmpurile cu încredere scăzută", "Solicită revizuire umană când e necesar"]
    },
    {
        "id": "eligibilitate",
        "nume": "Eligibilitate",
        "descriere": "Verifică eligibilitatea firmei și proiectului pentru programul de finanțare selectat. Aplică reguli deterministe + interpretare semantică.",
        "tip": "verificare",
        "icon": "shield-check",
        "reguli_default": ["Nu decide eligibilitatea - o verifică", "Oferă scor explicabil", "Listează toate blocajele cu sursă"]
    },
    {
        "id": "redactor",
        "nume": "Redactor",
        "descriere": "Completează documentația proiectului pe baza datelor existente. Generează secțiuni narative, pre-completează template-uri, aliniază la ghidul solicitantului.",
        "tip": "generare",
        "icon": "pen-tool",
        "reguli_default": ["Nu inventează date", "Folosește doar informații din context", "Scrie în stil formal, profesional", "Interpretează și scrie în limba română"]
    },
    {
        "id": "validator",
        "nume": "Validator",
        "descriere": "Verifică consistența documentelor și datelor proiectului. Validare cross-document, consistență buget-achiziții, detectare inconsistențe.",
        "tip": "verificare",
        "icon": "check-circle",
        "reguli_default": ["Verifică coerența între toate documentele", "Compară bugetul cu lista de achiziții", "Semnalează contradicții"]
    },
    {
        "id": "evaluator",
        "nume": "Evaluator",
        "descriere": "Simulează evaluarea proiectului conform grilei de conformitate. Verifică checklist-ul de pregătire pentru depunere.",
        "tip": "verificare",
        "icon": "clipboard-check",
        "reguli_default": ["Evaluează strict pe grila oficială", "Oferă scoring per criteriu", "Identifică documentele lipsă"]
    },
    {
        "id": "navigator",
        "nume": "Ghid Platformă",
        "descriere": "Asistent AI orientat către utilizator. Explică pașii următori, clarifică blocajele, oferă recomandări. Nu are rol decizional.",
        "tip": "asistenta",
        "icon": "message-circle",
        "reguli_default": ["Răspunde concis și clar", "Explică în termeni non-tehnici", "Nu ia decizii în locul utilizatorului", "Interpretează și scrie în limba română"]
    }
]

class UpdateAgentRules(BaseModel):
    reguli: List[str]

class AddRuleRequest(BaseModel):
    regula: str

@router.get("")
async def list_agents(current_user: dict = Depends(get_current_user)):
    """List all agents with their custom rules."""
    user_id = current_user["user_id"]
    agents = []
    for agent in DEFAULT_AGENTS:
        custom = await db.agent_rules.find_one({"agent_id": agent["id"], "user_id": user_id}, {"_id": 0})
        a = {**agent}
        if custom:
            a["reguli_custom"] = custom.get("reguli", [])
        else:
            a["reguli_custom"] = []
        a["reguli_active"] = agent["reguli_default"] + a["reguli_custom"]
        agents.append(a)
    return agents

@router.get("/{agent_id}")
async def get_agent(agent_id: str, current_user: dict = Depends(get_current_user)):
    agent = next((a for a in DEFAULT_AGENTS if a["id"] == agent_id), None)
    if not agent:
        raise HTTPException(status_code=404, detail="Agent negăsit")
    custom = await db.agent_rules.find_one({"agent_id": agent_id, "user_id": current_user["user_id"]}, {"_id": 0})
    a = {**agent}
    a["reguli_custom"] = custom.get("reguli", []) if custom else []
    a["reguli_active"] = agent["reguli_default"] + a["reguli_custom"]
    return a

@router.post("/{agent_id}/rules")
async def add_rule(agent_id: str, req: AddRuleRequest, current_user: dict = Depends(get_current_user)):
    agent = next((a for a in DEFAULT_AGENTS if a["id"] == agent_id), None)
    if not agent:
        raise HTTPException(status_code=404, detail="Agent negăsit")
    user_id = current_user["user_id"]
    existing = await db.agent_rules.find_one({"agent_id": agent_id, "user_id": user_id})
    if existing:
        await db.agent_rules.update_one({"agent_id": agent_id, "user_id": user_id}, {"$push": {"reguli": req.regula}})
    else:
        await db.agent_rules.insert_one({"agent_id": agent_id, "user_id": user_id, "reguli": [req.regula], "created_at": datetime.now(timezone.utc).isoformat()})
    await db.audit_log.insert_one({"id": str(uuid.uuid4()), "action": "agent.rule_added", "entity_type": "agent", "entity_id": agent_id, "user_id": user_id, "details": {"regula": req.regula}, "timestamp": datetime.now(timezone.utc).isoformat()})
    return {"message": "Regulă adăugată"}

@router.delete("/{agent_id}/rules/{rule_index}")
async def delete_rule(agent_id: str, rule_index: int, current_user: dict = Depends(get_current_user)):
    user_id = current_user["user_id"]
    custom = await db.agent_rules.find_one({"agent_id": agent_id, "user_id": user_id})
    if not custom or rule_index >= len(custom.get("reguli", [])):
        raise HTTPException(status_code=404, detail="Regulă negăsită")
    reguli = custom["reguli"]
    removed = reguli.pop(rule_index)
    await db.agent_rules.update_one({"agent_id": agent_id, "user_id": user_id}, {"$set": {"reguli": reguli}})
    return {"message": f"Regulă ștearsă: {removed}"}

@router.put("/{agent_id}/rules")
async def set_rules(agent_id: str, req: UpdateAgentRules, current_user: dict = Depends(get_current_user)):
    user_id = current_user["user_id"]
    await db.agent_rules.update_one({"agent_id": agent_id, "user_id": user_id}, {"$set": {"reguli": req.reguli, "updated_at": datetime.now(timezone.utc).isoformat()}}, upsert=True)
    return {"message": "Reguli actualizate"}


# === Unified Agent Execution Endpoint ===

class RunAgentRequest(BaseModel):
    application_id: Optional[str] = None
    company_id: Optional[str] = None
    input_data: Optional[dict] = {}

@router.post("/{agent_id}/run")
async def run_agent(agent_id: str, req: RunAgentRequest, current_user: dict = Depends(get_current_user)):
    """Unified endpoint to run any agent independently."""
    agent = next((a for a in DEFAULT_AGENTS if a["id"] == agent_id), None)
    if not agent:
        raise HTTPException(404, "Agent negăsit")

    # Load custom rules
    custom_rules = await db.agent_rules.find_one({"agent_id": agent_id, "user_id": current_user["user_id"]}, {"_id": 0})
    rules = (agent.get("reguli_default", []) + (custom_rules.get("reguli", []) if custom_rules else []))
    rules_text = "\n".join(rules)

    # Load context
    app = None
    org = None
    if req.application_id:
        app = await db.applications.find_one({"id": req.application_id}, {"_id": 0})
        if app:
            org = await db.organizations.find_one({"id": app.get("company_id")}, {"_id": 0})
    if req.company_id and not org:
        org = await db.organizations.find_one({"id": req.company_id}, {"_id": 0})

    run_id = str(uuid.uuid4())
    result = {}

    # Build full project context (shared by all agents)
    from services.context_builder import build_full_context
    full_ctx = {}
    if req.application_id:
        full_ctx = await build_full_context(req.application_id, db)

    # --- COLECTOR ---
    if agent_id == "colector":
        if not org:
            raise HTTPException(400, "Firma este necesară pentru agentul Colector")
        from services.onrc_service import lookup_cui
        from services.anaf_service import get_financial_data
        actions = []
        # Refresh ONRC data
        if org.get("cui"):
            onrc = await lookup_cui(org["cui"])
            if onrc.get("success"):
                update_fields = {}
                for k in ["denumire", "adresa", "judet", "stare", "telefon", "nr_reg_com", "data_infiintare"]:
                    if onrc["data"].get(k):
                        update_fields[k] = onrc["data"][k]
                if update_fields:
                    update_fields["updated_at"] = datetime.now(timezone.utc).isoformat()
                    await db.organizations.update_one({"id": org["id"]}, {"$set": update_fields})
                    actions.append(f"Date ONRC actualizate: {', '.join(update_fields.keys())}")
            # Financial data
            fin = await get_financial_data(org["cui"])
            if fin.get("success"):
                await db.organizations.update_one({"id": org["id"]}, {"$set": {"date_financiare": fin["data"], "updated_at": datetime.now(timezone.utc).isoformat()}})
                actions.append(f"Date financiare ANAF actualizate (CA: {fin['data'].get('cifra_afaceri', 'N/A')})")
        result = {"actions": actions, "company": org.get("denumire")}

    # --- PARSER OCR ---
    elif agent_id == "parser":
        doc_id = req.input_data.get("document_id")
        if not doc_id:
            raise HTTPException(400, "document_id necesar")
        from services.ocr_service import process_ocr
        import os
        # Find file
        base_dirs = [os.path.join(os.path.dirname(os.path.dirname(__file__)), d) for d in ["uploads/app_docs", "uploads/onrc", "uploads"]]
        file_path = None
        for bd in base_dirs:
            if not os.path.exists(bd): continue
            for f in os.listdir(bd):
                if doc_id in f:
                    file_path = os.path.join(bd, f)
                    break
            if file_path: break
        tip = req.input_data.get("tip_document", "altele")
        ocr = await process_ocr(doc_id, tip, req.input_data.get("filename", ""), db, file_path=file_path)
        result = {"ocr_status": ocr.get("status"), "fields_count": len(ocr.get("extracted_fields", {})), "confidence": ocr.get("overall_confidence")}

    # --- ELIGIBILITATE ---
    elif agent_id == "eligibilitate":
        if not req.application_id:
            raise HTTPException(400, "application_id necesar")
        from services.ai_service import check_eligibility
        ai_result = await check_eligibility({}, {}, full_context=full_ctx, extra_rules=rules_text)
        report = {"id": str(uuid.uuid4()), "type": "evaluation", "application_id": req.application_id, "result": ai_result.get("result", ""), "created_at": datetime.now(timezone.utc).isoformat()}
        await db.compliance_reports.insert_one(report)
        result = {"report_id": report["id"], "success": ai_result.get("success"), "preview": ai_result.get("result", "")[:300]}

    # --- REDACTOR ---
    elif agent_id == "redactor":
        if not app:
            raise HTTPException(400, "application_id necesar")
        template_id = req.input_data.get("template_id")
        if not template_id:
            raise HTTPException(400, "template_id necesar")
        from services.ai_service import generate_document_section
        from services.funding_service import get_template
        from services.pdf_service import generate_pdf
        tpl = get_template(template_id)
        if not tpl:
            custom_tpls = app.get("custom_templates", [])
            tpl = next((t for t in custom_tpls if t["id"] == template_id), None)
        if not tpl:
            raise HTTPException(404, "Template negăsit")
        ai_result = await generate_document_section(
            template=f"{tpl['label']}: {', '.join(tpl.get('sections', []))}",
            data={}, section=req.input_data.get("section") or ", ".join(tpl.get("sections", [])),
            full_context=full_ctx, extra_rules=rules_text
        )
        content = ai_result.get("result", "")
        import os
        pdf_file = generate_pdf(tpl["label"], content, full_ctx.get("firma", {}).get("denumire", ""), app["title"])
        draft = {"id": str(uuid.uuid4()), "template_id": template_id, "template_label": tpl["label"], "content": content, "pdf_filename": pdf_file, "status": "draft", "version": 1, "created_at": datetime.now(timezone.utc).isoformat(), "created_by": current_user["user_id"], "applied_rules": rules}
        await db.applications.update_one({"id": req.application_id}, {"$push": {"drafts": draft}})
        result = {"draft_id": draft["id"], "pdf_url": f"/api/v2/drafts/download/{pdf_file}", "preview": content[:300]}

    # --- VALIDATOR ---
    elif agent_id == "validator":
        if not req.application_id:
            raise HTTPException(400, "application_id necesar")
        from services.ai_service import validate_coherence
        ai_result = await validate_coherence([], {}, full_context=full_ctx, extra_rules=rules_text)
        report = {"id": str(uuid.uuid4()), "type": "validation", "application_id": req.application_id, "result": ai_result.get("result", ""), "created_at": datetime.now(timezone.utc).isoformat()}
        await db.compliance_reports.insert_one(report)
        result = {"report_id": report["id"], "preview": ai_result.get("result", "")[:300]}

    # --- EVALUATOR (grilă conformitate) ---
    elif agent_id == "evaluator":
        if not req.application_id:
            raise HTTPException(400, "application_id necesar")
        from services.ai_service import validate_coherence
        ai_result = await validate_coherence([], {},
            full_context={**full_ctx, "instrucțiune_specială": "Evaluează conform GRILEI DE CONFORMITATE din ghid. Verifică completitudinea dosarului, documente obligatorii, coerență date, semnături. Dă scoring per criteriu."},
            extra_rules=rules_text
        )
        report = {"id": str(uuid.uuid4()), "type": "conformity_grid", "application_id": req.application_id, "result": ai_result.get("result", ""), "created_at": datetime.now(timezone.utc).isoformat()}
        await db.compliance_reports.insert_one(report)
        result = {"report_id": report["id"], "preview": ai_result.get("result", "")[:300]}

    # --- NAVIGATOR ---
    elif agent_id == "navigator":
        message = req.input_data.get("message", "")
        if not message:
            raise HTTPException(400, "message necesar")
        from services.ai_service import chat_navigator
        ai_result = await chat_navigator(message, {}, full_context=full_ctx, extra_rules=rules_text)
        result = {"response": ai_result.get("result", ""), "success": ai_result.get("success")}

    # --- ORCHESTRATOR ---
    elif agent_id == "orchestrator":
        if not app or not org:
            raise HTTPException(400, "application_id necesar")
        from services.orchestrator_service import run_orchestrator_check
        result = await run_orchestrator_check(app, org, db)

    else:
        raise HTTPException(400, f"Agent {agent_id} nu are implementare de execuție")

    # Log AgentRun
    await db.agent_runs.insert_one({
        "id": run_id, "agent_id": agent_id,
        "application_id": req.application_id, "company_id": req.company_id,
        "action": "run", "applied_rules": rules,
        "input": req.input_data or {},
        "output": {k: str(v)[:500] if isinstance(v, str) else v for k, v in result.items()},
        "timestamp": datetime.now(timezone.utc).isoformat(),
        "user_id": current_user["user_id"]
    })

    return {"agent_id": agent_id, "run_id": run_id, "applied_rules": rules, "result": result}

@router.get("/{agent_id}/runs")
async def get_agent_runs(agent_id: str, application_id: Optional[str] = None, limit: int = 20, current_user: dict = Depends(get_current_user)):
    """Get execution history for an agent."""
    q = {"agent_id": agent_id}
    if application_id:
        q["application_id"] = application_id
    runs = await db.agent_runs.find(q, {"_id": 0}).sort("timestamp", -1).to_list(limit)
    return runs
