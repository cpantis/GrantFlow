"""Legacy funding routes - delegates to v2/applications"""
from fastapi import APIRouter
from fastapi.responses import FileResponse
import os

router = APIRouter(prefix="/api/funding", tags=["funding-legacy"])
db = None

def set_db(database):
    global db
    db = database

@router.get("/drafts/download/{filename}")
async def download_draft_pdf(filename: str):
    filepath = os.path.join(os.path.dirname(os.path.dirname(__file__)), "uploads", "generated", filename)
    if not os.path.exists(filepath):
        from fastapi import HTTPException
        raise HTTPException(status_code=404, detail="Fișier negăsit")
    return FileResponse(filepath, media_type="application/pdf", filename=filename)

# SICAP search (mock)
SICAP_CPV = [
    {"cod": "30200000-1", "descriere": "Echipamente informatice", "pret_referinta_min": 500, "pret_referinta_max": 15000},
    {"cod": "30213100-6", "descriere": "Laptopuri", "pret_referinta_min": 2000, "pret_referinta_max": 8000},
    {"cod": "48000000-8", "descriere": "Software și sisteme informatice", "pret_referinta_min": 1000, "pret_referinta_max": 50000},
    {"cod": "72000000-5", "descriere": "Servicii IT", "pret_referinta_min": 5000, "pret_referinta_max": 200000},
    {"cod": "45000000-7", "descriere": "Lucrări de construcții", "pret_referinta_min": 50000, "pret_referinta_max": 5000000},
    {"cod": "42000000-6", "descriere": "Mașini industriale", "pret_referinta_min": 10000, "pret_referinta_max": 500000},
    {"cod": "09331200-0", "descriere": "Module solare fotovoltaice", "pret_referinta_min": 10000, "pret_referinta_max": 200000},
    {"cod": "34100000-8", "descriere": "Autovehicule", "pret_referinta_min": 15000, "pret_referinta_max": 150000},
]

@router.get("/sicap/search")
async def sicap_search(q: str):
    return [c for c in SICAP_CPV if q.lower() in c["descriere"].lower() or q.lower() in c["cod"]]

@router.get("/afir/preturi")
async def afir_search(q: str):
    AFIR = [
        {"categorie": "Utilaje", "subcategorie": "Tractor", "pret_min": 25000, "pret_max": 120000, "unitate": "buc"},
        {"categorie": "Utilaje", "subcategorie": "Combină", "pret_min": 80000, "pret_max": 350000, "unitate": "buc"},
        {"categorie": "Construcții", "subcategorie": "Hală depozitare", "pret_min": 200, "pret_max": 500, "unitate": "mp"},
        {"categorie": "IT", "subcategorie": "Laptop", "pret_min": 2000, "pret_max": 6000, "unitate": "buc"},
        {"categorie": "Energie", "subcategorie": "Panou fotovoltaic", "pret_min": 200, "pret_max": 500, "unitate": "buc"},
    ]
    return [p for p in AFIR if q.lower() in p["subcategorie"].lower() or q.lower() in p["categorie"].lower()]
