"""Orchestrator Agent - Coordinates all AI agents based on project/firm state"""
import os
import uuid
import logging
from datetime import datetime, timezone
from emergentintegrations.llm.chat import LlmChat, UserMessage

logger = logging.getLogger(__name__)

MARKDOWN_INSTRUCTION = (
    "\n\nRăspunde ÎNTOTDEAUNA în Markdown structurat cu ## headings, **bold**, liste, > blockquote."
    "\nLimba: română."
)

def _get_chat(system_message: str) -> LlmChat:
    chat = LlmChat(
        api_key=os.environ["EMERGENT_LLM_KEY"],
        session_id=str(uuid.uuid4()),
        system_message=system_message + MARKDOWN_INSTRUCTION
    )
    chat.with_model("openai", "gpt-5.2")
    return chat


async def run_orchestrator_check(project: dict, org: dict, documents: list, drafts: list, legislation: list, db) -> dict:
    """
    The Orchestrator Agent analyzes the entire project state and determines
    what each agent should do next.
    """
    # Build comprehensive context
    doc_summary = [{"tip": d.get("tip"), "status": d.get("status"), "ocr_status": d.get("ocr_status"), "filename": d.get("filename")} for d in documents]
    draft_summary = [{"template": d.get("template_label"), "status": d.get("status")} for d in drafts]
    leg_summary = [{"titlu": l.get("titlu"), "tip": l.get("tip")} for l in legislation]

    firm_context = {
        "denumire": org.get("denumire"),
        "cui": org.get("cui"),
        "forma_juridica": org.get("forma_juridica"),
        "judet": org.get("judet"),
        "stare": org.get("stare"),
        "caen_principal": org.get("caen_principal"),
        "nr_angajati": org.get("nr_angajati"),
        "data_infiintare": org.get("data_infiintare"),
        "date_financiare": bool(org.get("date_financiare")),
        "sursa_date": org.get("sursa_date")
    }

    project_context = {
        "titlu": project.get("titlu"),
        "stare": project.get("stare"),
        "stare_label": project.get("stare_label"),
        "program_finantare": project.get("program_finantare"),
        "tip_proiect": project.get("tip_proiect"),
        "buget_estimat": project.get("buget_estimat"),
        "tema_proiect": project.get("tema_proiect"),
        "achizitii": len(project.get("achizitii", [])),
        "obiective": project.get("obiective"),
        "locatie_implementare": project.get("locatie_implementare"),
        "sesiune": bool(project.get("sesiune")),
    }

    # Determine what each agent should check
    checks = []

    # 1. Colector - are firm data complete?
    colector_issues = []
    if not org.get("date_financiare"):
        colector_issues.append("Date financiare ANAF lipsă")
    if not org.get("caen_principal"):
        colector_issues.append("CAEN principal lipsă")
    if org.get("sursa_date") == "Manual + Upload ONRC":
        colector_issues.append("Datele firmei sunt introduse manual - recomandare verificare automată prin CUI")
    checks.append({"agent": "Colector", "status": "ok" if not colector_issues else "actiune_necesara", "issues": colector_issues})

    # 2. Parser - are there docs needing OCR?
    pending_ocr = [d for d in documents if d.get("ocr_status") == "pending"]
    needs_review = [d for d in documents if d.get("ocr_status") == "needs_review"]
    checks.append({"agent": "Parser OCR", "status": "ok" if not pending_ocr and not needs_review else "actiune_necesara",
                    "issues": ([f"{len(pending_ocr)} documente necesită OCR"] if pending_ocr else []) +
                              ([f"{len(needs_review)} documente necesită revizuire OCR"] if needs_review else [])})

    # 3. Eligibilitate - has eligibility been checked?
    elig_reports = await db.compliance_reports.count_documents({"project_id": project["id"], "type": "eligibility"})
    checks.append({"agent": "Eligibilitate", "status": "ok" if elig_reports > 0 else "actiune_necesara",
                    "issues": ["Verificare eligibilitate neefectuată"] if elig_reports == 0 else []})

    # 4. Redactor - are drafts generated?
    checks.append({"agent": "Redactor", "status": "ok" if len(drafts) >= 3 else "actiune_necesara",
                    "issues": [f"Doar {len(drafts)} drafturi generate (recomandat minim: Cerere finanțare, Plan afaceri, Declarații)"] if len(drafts) < 3 else []})

    # 5. Validator - coherence check done?
    valid_reports = await db.compliance_reports.count_documents({"project_id": project["id"], "type": {"$in": ["validation", "conformity_grid"]}})
    checks.append({"agent": "Validator", "status": "ok" if valid_reports > 0 else "actiune_necesara",
                    "issues": ["Validare coerență neefectuată"] if valid_reports == 0 else []})

    # 6. Configurare proiect
    config_issues = []
    if not project.get("tip_proiect"):
        config_issues.append("Tip proiect nesetat")
    if not project.get("tema_proiect"):
        config_issues.append("Tema proiectului nedefinită")
    if not project.get("sesiune"):
        config_issues.append("Sesiune de finanțare neselectată")
    if not project.get("achizitii") or len(project.get("achizitii", [])) == 0:
        config_issues.append("Lista achiziții goală")
    if not project.get("locatie_implementare"):
        config_issues.append("Locație implementare nedefinită")
    checks.append({"agent": "Configurare", "status": "ok" if not config_issues else "actiune_necesara", "issues": config_issues})

    # 7. Legislație
    checks.append({"agent": "Legislație", "status": "ok" if len(legislation) > 0 else "atentie",
                    "issues": ["Niciun ghid/procedură încărcată"] if not legislation else []})

    # Now ask AI for a comprehensive analysis
    all_issues = []
    for c in checks:
        all_issues.extend(c.get("issues", []))

    needs_action = any(c["status"] == "actiune_necesara" for c in checks)

    chat = _get_chat(
        "Ești Orchestratorul GrantFlow. Analizezi starea completă a unui proiect de finanțare "
        "și determini ce acțiuni trebuie luate de fiecare agent. "
        "Oferă un raport structurat cu: stare generală, acțiuni prioritare, recomandări per agent."
    )

    prompt = (
        f"**Firma:** {firm_context}\n\n"
        f"**Proiect:** {project_context}\n\n"
        f"**Documente:** {len(documents)} încărcate, {len(pending_ocr)} OCR pending\n"
        f"**Drafturi:** {len(drafts)} generate\n"
        f"**Legislație:** {len(legislation)} documente\n\n"
        f"**Verificări agenți:**\n"
    )
    for c in checks:
        status_icon = "OK" if c["status"] == "ok" else "NECESITĂ ACȚIUNE" if c["status"] == "actiune_necesara" else "ATENȚIE"
        prompt += f"- **{c['agent']}**: {status_icon}"
        if c["issues"]:
            prompt += f" - {', '.join(c['issues'])}"
        prompt += "\n"
    prompt += "\nOferă un raport complet cu prioritizare și pași concreți de urmat."

    try:
        ai_response = await chat.send_message(UserMessage(text=prompt))
    except Exception as e:
        logger.error(f"Orchestrator AI failed: {e}")
        ai_response = "Eroare la generarea raportului AI."

    result = {
        "id": str(uuid.uuid4()),
        "project_id": project["id"],
        "org_id": org.get("id"),
        "checks": checks,
        "needs_action": needs_action,
        "total_issues": len(all_issues),
        "ai_analysis": ai_response,
        "timestamp": datetime.now(timezone.utc).isoformat()
    }

    # Save to DB
    await db.orchestrator_reports.insert_one({**result})
    await db.audit_log.insert_one({
        "id": str(uuid.uuid4()),
        "action": "orchestrator.check",
        "entity_type": "project",
        "entity_id": project["id"],
        "user_id": "system",
        "details": {"total_issues": len(all_issues), "needs_action": needs_action},
        "timestamp": datetime.now(timezone.utc).isoformat()
    })

    result.pop("_id", None)
    return result


async def auto_process_upload(doc_id: str, doc_type: str, filename: str, org_id: str, project_id: str, db) -> dict:
    """Auto-process an uploaded document: OCR + extract data + update relevant records."""
    from services.ocr_service import process_ocr

    # 1. Run OCR
    ocr_result = await process_ocr(doc_id, doc_type, filename, db)

    actions_taken = ["OCR executat"]

    # 2. Based on doc type and OCR data, take automatic actions
    if ocr_result.get("status") in ["completed", "needs_review"] and ocr_result.get("extracted_fields"):
        fields = ocr_result["extracted_fields"]

        # If it's a CI, update user data
        if doc_type == "ci" and fields.get("cnp"):
            actions_taken.append("Date CI extrase (CNP, nume, adresă)")

        # If it's a balance sheet, update financial data
        if doc_type in ["bilant", "balanta"] and fields.get("cifra_afaceri"):
            if org_id:
                await db.organizations.update_one({"id": org_id}, {"$set": {
                    "date_financiare_ocr": fields,
                    "updated_at": datetime.now(timezone.utc).isoformat()
                }})
                actions_taken.append("Date financiare extrase și salvate la firmă")

        # If it's an invoice, add to project expenses
        if doc_type == "factura" and fields.get("total") and project_id:
            try:
                total = float(fields["total"].replace(",", ".").replace(" ", ""))
                await db.projects.update_one({"id": project_id}, {
                    "$push": {"expenses": {
                        "id": str(uuid.uuid4()),
                        "descriere": f"Factură OCR: {fields.get('numar_factura', 'N/A')}",
                        "suma": total,
                        "categorie": "factura_ocr",
                        "status": "de_verificat",
                        "created_at": datetime.now(timezone.utc).isoformat(),
                        "created_by": "ocr_auto"
                    }},
                    "$inc": {"cheltuieli_totale": total}
                })
                actions_taken.append(f"Cheltuială {total} RON adăugată automat la proiect")
            except (ValueError, TypeError):
                pass

        # If it's a contract, extract key dates
        if doc_type == "contract" and fields.get("data_contract"):
            actions_taken.append(f"Date contract extrase: {fields.get('numar_contract', 'N/A')}")

        # If it's an authorization/empowerment
        if doc_type == "imputernicire" and fields.get("imputernicit"):
            actions_taken.append(f"Împuternicire: {fields.get('imputernicit')} - scope: {fields.get('scope', 'N/A')}")

    return {
        "ocr_result": ocr_result,
        "actions_taken": actions_taken,
        "auto_processed": True
    }
