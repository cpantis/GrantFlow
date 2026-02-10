"""Orchestrator Agent - Coordinates all AI agents for Application (Dosar) workflow"""
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


async def run_orchestrator_check(app: dict, org: dict, db, user_id: str = None) -> dict:
    """Analyze application state and determine what each agent should do next."""

    # Load custom rules for all agents
    all_rules = {}
    async for rule_doc in db.agent_rules.find({}, {"_id": 0}):
        aid = rule_doc.get("agent_id")
        all_rules.setdefault(aid, []).extend(rule_doc.get("reguli", []))

    orchestrator_rules = all_rules.get("orchestrator", [])
    extra_rules = "\n".join(orchestrator_rules)

    guide_assets = app.get("guide_assets", [])
    req_docs = app.get("required_documents", [])
    docs = app.get("documents", [])
    drafts = app.get("drafts", [])
    status = app.get("status", "draft")

    checks = []

    # 1. Call selected?
    has_call = bool(app.get("call_id"))
    checks.append({"agent": "Configurare", "status": "ok" if has_call else "actiune_necesara",
                    "issues": [] if has_call else ["Sesiune de finanțare neselectată"]})

    # 2. Guide uploaded?
    checks.append({"agent": "Ghid & Anexe", "status": "ok" if len(guide_assets) > 0 else "actiune_necesara",
                    "issues": [] if guide_assets else ["Ghidul solicitantului nu este încărcat"]})

    # 3. Checklist defined?
    frozen = app.get("checklist_frozen", False)
    checks.append({"agent": "Checklist", "status": "ok" if frozen else ("atentie" if len(req_docs) > 0 else "actiune_necesara"),
                    "issues": ([] if frozen else (["Checklist-ul nu este înghețat"] if req_docs else ["Lista documente cerute nu este definită"]))})

    # 4. Colector - firm data complete?
    colector_issues = []
    if not org.get("caen_principal"): colector_issues.append("CAEN principal lipsă")
    if not org.get("date_financiare") and not org.get("date_financiare_ocr"): colector_issues.append("Date financiare lipsă")
    if org.get("sursa_date", "").startswith("Manual"): colector_issues.append("Date firmă manuale - verificare CUI recomandată")
    checks.append({"agent": "Colector", "status": "ok" if not colector_issues else "actiune_necesara", "issues": colector_issues})

    # 5. Documents vs checklist
    missing_docs = [rd for rd in req_docs if rd.get("status") == "missing"]
    uploaded_docs = [rd for rd in req_docs if rd.get("status") == "uploaded"]
    doc_pct = (len(uploaded_docs) / len(req_docs) * 100) if req_docs else 0
    checks.append({"agent": "Documente", "status": "ok" if not missing_docs else "actiune_necesara",
                    "issues": [f"{len(missing_docs)} documente lipsă din {len(req_docs)} cerute ({doc_pct:.0f}% complet)"] if missing_docs else []})

    # 6. Redactor - drafts generated?
    checks.append({"agent": "Redactor", "status": "ok" if len(drafts) >= 2 else "actiune_necesara",
                    "issues": [f"Doar {len(drafts)} drafturi generate (recomandat: Cerere finanțare, Plan afaceri, Declarații)"] if len(drafts) < 2 else []})

    # 7. Validator
    val_reports = await db.compliance_reports.count_documents({"application_id": app["id"], "type": "validation"})
    checks.append({"agent": "Validator", "status": "ok" if val_reports > 0 else "actiune_necesara",
                    "issues": ["Validare coerență neefectuată"] if val_reports == 0 else []})

    # 8. Eligibilitate
    elig_reports = await db.compliance_reports.count_documents({"application_id": app["id"], "type": "evaluation"})
    checks.append({"agent": "Eligibilitate", "status": "ok" if elig_reports > 0 else "actiune_necesara",
                    "issues": ["Evaluare eligibilitate neefectuată"] if elig_reports == 0 else []})

    all_issues = []
    for c in checks: all_issues.extend(c.get("issues", []))
    needs_action = any(c["status"] == "actiune_necesara" for c in checks)

    # AI analysis
    # Include all agent custom rules in orchestrator prompt
    rules_section = ""
    if all_rules:
        rules_parts = []
        for agent_name, agent_rules in all_rules.items():
            if agent_rules:
                rules_parts.append(f"**{agent_name}**: {'; '.join(agent_rules)}")
        if rules_parts:
            rules_section = "\n\n## Reguli custom active per agent:\n" + "\n".join(rules_parts)

    chat = _get_chat(
        "Ești Orchestratorul GrantFlow. Analizezi starea completă a unui dosar de finanțare "
        "și determini acțiunile prioritare per agent. Ții cont de regulile custom setate pentru fiecare agent. "
        "Oferă un raport structurat cu pași concreți."
        + (f"\nReguli orchestrator: {extra_rules}" if extra_rules else "")
    )
    prompt = (
        f"**Dosar:** {app.get('title')} | Status: **{app.get('status_label')}**\n"
        f"**Firmă:** {org.get('denumire')} (CUI: {org.get('cui')})\n"
        f"**Sesiune:** {app.get('call_name')} ({app.get('program_name')})\n\n"
        f"**Stare agenți:**\n"
    )
    for c in checks:
        icon = "OK" if c["status"] == "ok" else "ACȚIUNE" if c["status"] == "actiune_necesara" else "ATENȚIE"
        prompt += f"- **{c['agent']}**: {icon} {', '.join(c['issues']) if c['issues'] else 'în regulă'}\n"
    prompt += f"\nGhid: {len(guide_assets)} fișiere | Documente: {len(docs)}/{len(req_docs)} | Drafturi: {len(drafts)}\n"
    prompt += "\nOferă raport cu prioritizare și pași concreți."

    try:
        ai_response = await chat.send_message(UserMessage(text=prompt))
    except Exception as e:
        logger.error(f"Orchestrator AI failed: {e}")
        ai_response = "Eroare la generarea analizei."

    result = {
        "id": str(uuid.uuid4()),
        "application_id": app["id"],
        "checks": checks,
        "needs_action": needs_action,
        "total_issues": len(all_issues),
        "ai_analysis": ai_response,
        "timestamp": datetime.now(timezone.utc).isoformat()
    }

    await db.agent_runs.insert_one({
        "id": str(uuid.uuid4()), "agent_id": "orchestrator",
        "application_id": app["id"], "action": "orchestrator_check",
        "applied_rules": (custom_rules.get("reguli", []) if custom_rules else []),
        "output": {"needs_action": needs_action, "total_issues": len(all_issues)},
        "timestamp": datetime.now(timezone.utc).isoformat()
    })

    await db.audit_log.insert_one({
        "id": str(uuid.uuid4()), "action": "orchestrator.check",
        "entity_type": "application", "entity_id": app["id"],
        "user_id": "system", "details": {"needs_action": needs_action, "issues": len(all_issues)},
        "timestamp": datetime.now(timezone.utc).isoformat()
    })

    return result


async def auto_process_upload(doc_id, doc_type, filename, org_id, project_id, db):
    """Auto-process uploaded document."""
    from services.ocr_service import process_ocr
    ocr_result = await process_ocr(doc_id, doc_type, filename, db)
    actions = ["OCR executat"]
    if ocr_result.get("extracted_fields"):
        fields = ocr_result["extracted_fields"]
        if doc_type in ["bilant", "balanta"] and org_id:
            await db.organizations.update_one({"id": org_id}, {"$set": {"date_financiare_ocr": fields, "updated_at": datetime.now(timezone.utc).isoformat()}})
            actions.append("Date financiare extrase")
        if doc_type == "factura" and project_id:
            try:
                total = float(str(fields.get("total", "0")).replace(",", ".").replace(" ", ""))
                if total > 0:
                    await db.applications.update_one({"id": project_id}, {"$inc": {"expenses_total": total}})
                    actions.append(f"Cheltuială {total} RON detectată")
            except (ValueError, TypeError): pass
    return {"ocr_result": ocr_result, "actions_taken": actions, "auto_processed": True}
