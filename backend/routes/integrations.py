from fastapi import APIRouter, HTTPException, Depends
from pydantic import BaseModel
from typing import Optional
import uuid
from datetime import datetime, timezone
from middleware.auth_middleware import get_current_user

router = APIRouter(prefix="/api/integrations", tags=["integrations"])
db = None

def set_db(database):
    global db
    db = database

DEFAULT_INTEGRATIONS = {
    "firme": [
        {"id": "openapi_ro", "nume": "OpenAPI.ro", "categorie": "firme", "descriere": "Date firme din Registrul Comerțului (ONRC) - CUI, denumire, adresă, CAEN, administratori", "url_config": "https://openapi.ro", "env_key": "OPENAPI_RO_KEY", "status": "activ", "fields": ["CUI", "Denumire", "Adresă", "CAEN", "Nr. Reg. Com.", "Administratori", "Asociați", "Capital social"]},
        {"id": "anaf", "nume": "ANAF", "categorie": "firme", "descriere": "Agenția Națională de Administrare Fiscală - date financiare, status TVA, obligații fiscale", "url_config": "https://webservicesp.anaf.ro", "env_key": "ANAF_API_KEY", "status": "mock", "fields": ["Cifră afaceri", "Profit", "Nr. angajați", "Status TVA", "Obligații restante"]},
        {"id": "termene_ro", "nume": "Termene.ro", "categorie": "firme", "descriere": "Date extinse firme - financiar, juridic, fiscal, istoric complet din 15+ surse oficiale", "url_config": "https://termene.ro/api", "env_key": "TERMENE_RO_KEY", "status": "neconfigurat", "fields": ["Date financiare detaliate", "Istoric juridic", "Dosare instanță", "Insolvență", "Buletine proceduri"]},
        {"id": "onrc", "nume": "ONRC Direct", "categorie": "firme", "descriere": "Oficiul Național al Registrului Comerțului - certificat constatator, acte constitutive", "url_config": "https://portal.onrc.ro", "env_key": "ONRC_API_KEY", "status": "neconfigurat", "fields": ["Certificat constatator", "Act constitutiv", "Sedii secundare", "Istoric modificări"]},
    ],
    "programe": [
        {"id": "afir", "nume": "AFIR", "categorie": "programe", "descriere": "Agenția pentru Finanțarea Investițiilor Rurale - programe agricole, dezvoltare rurală", "url_config": "https://afir.ro", "env_key": "AFIR_API_KEY", "status": "mock", "fields": ["Măsuri active", "Sesiuni deschise", "Ghiduri solicitant", "Prețuri referință"]},
        {"id": "pnrr", "nume": "PNRR", "categorie": "programe", "descriere": "Planul Național de Redresare și Reziliență - componente, investiții, apeluri", "url_config": "https://mfe.gov.ro/pnrr", "env_key": "PNRR_API_KEY", "status": "mock", "fields": ["Componente", "Investiții", "Apeluri active", "Criterii eligibilitate"]},
        {"id": "fonduri_eu", "nume": "fonduri.eu", "categorie": "programe", "descriere": "Portal agregator programe de finanțare europene și naționale", "url_config": "https://fonduri.eu", "env_key": "FONDURI_EU_KEY", "status": "mock", "fields": ["Programe active", "Calendare apeluri", "Ghiduri", "Statistici absorbție"]},
        {"id": "mysmis", "nume": "MySMIS2021", "categorie": "programe", "descriere": "Sistemul informatic de management al instrumentelor structurale", "url_config": "https://mysmis2021.gov.ro", "env_key": "MYSMIS_KEY", "status": "neconfigurat", "fields": ["Depunere proiecte", "Monitorizare", "Raportare"]},
    ],
    "achizitii": [
        {"id": "sicap", "nume": "SICAP / e-Licitație", "categorie": "achizitii", "descriere": "Sistemul Informatic Colaborativ pentru Achizițiile Publice - coduri CPV, oferte, prețuri referință", "url_config": "https://e-licitatie.ro", "env_key": "SICAP_API_KEY", "status": "mock", "fields": ["Coduri CPV", "Prețuri referință", "Oferte publice", "Furnizori"]},
        {"id": "seap", "nume": "SEAP", "categorie": "achizitii", "descriere": "Sistemul Electronic de Achiziții Publice - cataloage, oferte directe", "url_config": "https://www.e-licitatie.ro/pub/", "env_key": "SEAP_API_KEY", "status": "neconfigurat", "fields": ["Catalog produse", "Achiziții directe", "Istoric prețuri"]},
    ]
}

class ConfigureIntegrationRequest(BaseModel):
    api_key: Optional[str] = None
    api_url: Optional[str] = None
    username: Optional[str] = None
    password: Optional[str] = None
    enabled: bool = True
    notes: Optional[str] = None

@router.get("")
async def list_integrations(current_user: dict = Depends(get_current_user)):
    result = {}
    for cat, integrations in DEFAULT_INTEGRATIONS.items():
        items = []
        for integ in integrations:
            config = await db.integrations_config.find_one({"integration_id": integ["id"]}, {"_id": 0})
            item = {**integ}
            if config:
                item["status"] = "activ" if config.get("enabled", True) and config.get("api_key") else integ["status"]
                item["configured"] = True
                item["configured_at"] = config.get("configured_at")
                item["notes"] = config.get("notes")
            else:
                item["configured"] = integ["status"] == "activ"
            items.append(item)
        result[cat] = items
    return result

@router.get("/{integration_id}")
async def get_integration(integration_id: str, current_user: dict = Depends(get_current_user)):
    for cat, integrations in DEFAULT_INTEGRATIONS.items():
        for integ in integrations:
            if integ["id"] == integration_id:
                config = await db.integrations_config.find_one({"integration_id": integration_id}, {"_id": 0})
                item = {**integ}
                if config:
                    item["configured"] = True
                    item["has_api_key"] = bool(config.get("api_key"))
                    item["api_url"] = config.get("api_url")
                    item["notes"] = config.get("notes")
                    item["enabled"] = config.get("enabled", True)
                return item
    raise HTTPException(status_code=404, detail="Integrare negăsită")

@router.put("/{integration_id}")
async def configure_integration(integration_id: str, req: ConfigureIntegrationRequest, current_user: dict = Depends(get_current_user)):
    found = False
    for cat, integrations in DEFAULT_INTEGRATIONS.items():
        for integ in integrations:
            if integ["id"] == integration_id:
                found = True
                break
    if not found:
        raise HTTPException(status_code=404, detail="Integrare negăsită")

    config = {
        "integration_id": integration_id,
        "enabled": req.enabled,
        "configured_at": datetime.now(timezone.utc).isoformat(),
        "configured_by": current_user["user_id"]
    }
    if req.api_key is not None:
        config["api_key"] = req.api_key
    if req.api_url is not None:
        config["api_url"] = req.api_url
    if req.username is not None:
        config["username"] = req.username
    if req.notes is not None:
        config["notes"] = req.notes

    await db.integrations_config.update_one(
        {"integration_id": integration_id}, {"$set": config}, upsert=True
    )
    await db.audit_log.insert_one({
        "id": str(uuid.uuid4()), "action": "integration.configured",
        "entity_type": "integration", "entity_id": integration_id,
        "user_id": current_user["user_id"],
        "details": {"enabled": req.enabled, "has_key": bool(req.api_key)},
        "timestamp": datetime.now(timezone.utc).isoformat()
    })
    return {"message": f"Integrare {integration_id} configurată"}

@router.post("/{integration_id}/test")
async def test_integration(integration_id: str, current_user: dict = Depends(get_current_user)):
    """Test if an integration is working."""
    if integration_id == "openapi_ro":
        import os
        key = os.environ.get("OPENAPI_RO_KEY", "")
        if not key:
            return {"status": "eroare", "message": "API Key nu este configurată"}
        try:
            import httpx
            async with httpx.AsyncClient(timeout=10) as client:
                resp = await client.get("https://api.openapi.ro/api/companies/14399840", headers={"x-api-key": key})
            if resp.status_code == 200:
                data = resp.json()
                return {"status": "ok", "message": f"Conexiune reușită. Test: {data.get('denumire', 'OK')}"}
            return {"status": "eroare", "message": f"Cod răspuns: {resp.status_code}"}
        except Exception as e:
            return {"status": "eroare", "message": str(e)}
    # Mock test for others
    return {"status": "mock", "message": f"Integrarea {integration_id} funcționează în mod simulat (MOCK)"}
