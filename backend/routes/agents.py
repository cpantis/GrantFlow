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
