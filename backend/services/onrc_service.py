"""MOCK ONRC Service - Simulates Romanian Trade Registry API"""
import random

MOCK_COMPANIES = {
    "12345678": {
        "cui": "12345678",
        "denumire": "SC TECH SOLUTIONS SRL",
        "forma_juridica": "SRL",
        "nr_reg_com": "J40/1234/2020",
        "adresa": "Str. Victoriei nr. 10, Sector 1, București",
        "cod_postal": "010061",
        "judet": "București",
        "localitate": "București",
        "stare": "ACTIVA",
        "data_infiintare": "2020-03-15",
        "capital_social": 200,
        "caen_principal": {"cod": "6201", "descriere": "Activități de realizare a soft-ului la comandă"},
        "caen_secundare": [
            {"cod": "6202", "descriere": "Activități de consultanță în tehnologia informației"},
            {"cod": "6311", "descriere": "Prelucrarea datelor, administrarea paginilor web"},
            {"cod": "7022", "descriere": "Activități de consultanță pentru afaceri și management"}
        ],
        "administratori": [
            {"nume": "POPESCU ION", "functie": "Administrator", "data_numire": "2020-03-15"}
        ],
        "asociati": [
            {"nume": "POPESCU ION", "procent": 60},
            {"nume": "IONESCU MARIA", "procent": 40}
        ],
        "sedii_secundare": [],
        "nr_angajati": 15
    },
    "87654321": {
        "cui": "87654321",
        "denumire": "SC GREEN ENERGY PROIECT SA",
        "forma_juridica": "SA",
        "nr_reg_com": "J40/5678/2018",
        "adresa": "Bd. Unirii nr. 45, Sector 3, București",
        "cod_postal": "030167",
        "judet": "București",
        "localitate": "București",
        "stare": "ACTIVA",
        "data_infiintare": "2018-06-20",
        "capital_social": 500000,
        "caen_principal": {"cod": "3511", "descriere": "Producția de energie electrică"},
        "caen_secundare": [
            {"cod": "3514", "descriere": "Comercializarea energiei electrice"},
            {"cod": "7112", "descriere": "Activități de inginerie și consultanță tehnică"},
            {"cod": "4221", "descriere": "Lucrări de construcții a proiectelor utilitare"}
        ],
        "administratori": [
            {"nume": "VASILESCU ANDREI", "functie": "Director General", "data_numire": "2018-06-20"},
            {"nume": "DUMITRESCU ELENA", "functie": "Director Financiar", "data_numire": "2019-01-10"}
        ],
        "asociati": [
            {"nume": "VASILESCU ANDREI", "procent": 51},
            {"nume": "FOND INVEST SRL", "procent": 49}
        ],
        "sedii_secundare": [
            {"adresa": "Str. Fabricii nr. 12, Ploiești, Prahova"}
        ],
        "nr_angajati": 85
    }
}

async def lookup_cui(cui: str) -> dict:
    if cui in MOCK_COMPANIES:
        return {"success": True, "data": MOCK_COMPANIES[cui]}
    # Generate random company for any CUI
    return {
        "success": True,
        "data": {
            "cui": cui,
            "denumire": f"SC COMPANIE {cui[:4]} SRL",
            "forma_juridica": "SRL",
            "nr_reg_com": f"J40/{random.randint(1000,9999)}/2022",
            "adresa": f"Str. Exemplu nr. {random.randint(1,100)}, București",
            "cod_postal": "010000",
            "judet": "București",
            "localitate": "București",
            "stare": "ACTIVA",
            "data_infiintare": "2022-01-15",
            "capital_social": 200,
            "caen_principal": {"cod": "6201", "descriere": "Activități de realizare a soft-ului la comandă"},
            "caen_secundare": [],
            "administratori": [{"nume": "ADMINISTRATOR IMPLICIT", "functie": "Administrator", "data_numire": "2022-01-15"}],
            "asociati": [{"nume": "ADMINISTRATOR IMPLICIT", "procent": 100}],
            "sedii_secundare": [],
            "nr_angajati": random.randint(1, 50)
        }
    }

async def get_certificat_constatator(cui: str) -> dict:
    company = await lookup_cui(cui)
    if not company["success"]:
        return {"success": False, "error": "CUI invalid"}
    data = company["data"]
    return {
        "success": True,
        "certificat": {
            "numar": f"CC-{cui}-{random.randint(10000,99999)}",
            "data_emitere": "2025-12-01",
            "valabil_pana": "2026-01-01",
            "firma": data,
            "status": "VALID"
        }
    }
