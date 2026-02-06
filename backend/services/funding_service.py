"""Funding Programs Service - AFIR, SICAP, fonduri.eu mock data sources"""
import random
from datetime import datetime

# Realistic Romanian EU funding programs database
PROGRAMS = [
    {
        "id": "pnrr",
        "denumire": "PNRR - Planul Național de Redresare și Reziliență",
        "sursa": "fonduri.eu",
        "tip": "european",
        "masuri": [
            {
                "id": "pnrr-c9-i1",
                "cod": "C9-I1",
                "denumire": "Sprijin pentru sectorul privat, cercetare, dezvoltare și inovare",
                "buget_total": 300000000,
                "sesiuni": [
                    {"id": "pnrr-c9-i1-s1", "denumire": "Sesiunea 1/2025", "status": "activa", "data_start": "2025-01-15", "data_sfarsit": "2025-06-30", "buget_disponibil": 100000000, "tip_beneficiari": ["IMM", "Startup"], "valoare_min": 50000, "valoare_max": 500000}
                ]
            },
            {
                "id": "pnrr-c10-i1",
                "cod": "C10-I1",
                "denumire": "Fondul local - Digitalizare",
                "buget_total": 500000000,
                "sesiuni": [
                    {"id": "pnrr-c10-i1-s1", "denumire": "Sesiunea 2/2025", "status": "activa", "data_start": "2025-03-01", "data_sfarsit": "2025-09-30", "buget_disponibil": 200000000, "tip_beneficiari": ["IMM", "Mari Întreprinderi"], "valoare_min": 100000, "valoare_max": 2000000}
                ]
            },
            {
                "id": "pnrr-c11-i3",
                "cod": "C11-I3",
                "denumire": "Turism și cultură",
                "buget_total": 150000000,
                "sesiuni": [
                    {"id": "pnrr-c11-i3-s1", "denumire": "Sesiunea 1/2025", "status": "inchisa", "data_start": "2024-06-01", "data_sfarsit": "2025-01-31", "buget_disponibil": 0, "tip_beneficiari": ["IMM", "ONG"], "valoare_min": 30000, "valoare_max": 300000}
                ]
            }
        ]
    },
    {
        "id": "afir",
        "denumire": "AFIR - Agenția pentru Finanțarea Investițiilor Rurale",
        "sursa": "AFIR",
        "tip": "european",
        "masuri": [
            {
                "id": "afir-sm6-1",
                "cod": "sM6.1",
                "denumire": "Instalarea tinerilor fermieri",
                "buget_total": 200000000,
                "sesiuni": [
                    {"id": "afir-sm6-1-s1", "denumire": "Sesiunea 2025", "status": "activa", "data_start": "2025-02-01", "data_sfarsit": "2025-12-31", "buget_disponibil": 80000000, "tip_beneficiari": ["Fermieri tineri"], "valoare_min": 50000, "valoare_max": 70000}
                ]
            },
            {
                "id": "afir-sm4-1",
                "cod": "sM4.1",
                "denumire": "Investiții în exploatații agricole",
                "buget_total": 400000000,
                "sesiuni": [
                    {"id": "afir-sm4-1-s1", "denumire": "Sesiunea 1/2025", "status": "activa", "data_start": "2025-04-01", "data_sfarsit": "2025-10-31", "buget_disponibil": 150000000, "tip_beneficiari": ["Fermieri", "Cooperative"], "valoare_min": 100000, "valoare_max": 1000000}
                ]
            },
            {
                "id": "afir-sm6-4",
                "cod": "sM6.4",
                "denumire": "Investiții în crearea și dezvoltarea de activități neagricole",
                "buget_total": 250000000,
                "sesiuni": [
                    {"id": "afir-sm6-4-s1", "denumire": "Sesiunea 2025", "status": "activa", "data_start": "2025-01-15", "data_sfarsit": "2025-08-15", "buget_disponibil": 100000000, "tip_beneficiari": ["IMM rural", "PFA"], "valoare_min": 50000, "valoare_max": 200000}
                ]
            }
        ]
    },
    {
        "id": "poc",
        "denumire": "POC - Programul Operațional Competitivitate",
        "sursa": "fonduri.eu",
        "tip": "european",
        "masuri": [
            {
                "id": "poc-2-2",
                "cod": "2.2",
                "denumire": "Sprijin pentru IMM-uri în vederea creșterii competitivității",
                "buget_total": 350000000,
                "sesiuni": [
                    {"id": "poc-2-2-s1", "denumire": "Apel 2025", "status": "activa", "data_start": "2025-05-01", "data_sfarsit": "2025-11-30", "buget_disponibil": 120000000, "tip_beneficiari": ["IMM"], "valoare_min": 200000, "valoare_max": 1500000}
                ]
            }
        ]
    },
    {
        "id": "por",
        "denumire": "POR - Programul Operațional Regional",
        "sursa": "fonduri.eu",
        "tip": "european",
        "masuri": [
            {
                "id": "por-2-1a",
                "cod": "2.1A",
                "denumire": "Microîntreprinderi",
                "buget_total": 200000000,
                "sesiuni": [
                    {"id": "por-2-1a-s1", "denumire": "Sesiunea 2025", "status": "activa", "data_start": "2025-03-15", "data_sfarsit": "2025-09-15", "buget_disponibil": 80000000, "tip_beneficiari": ["Microîntreprinderi"], "valoare_min": 25000, "valoare_max": 200000}
                ]
            }
        ]
    }
]

# SICAP mock data - procurement codes and reference prices
SICAP_CPV = [
    {"cod": "30200000-1", "descriere": "Echipamente informatice și accesorii", "pret_referinta_min": 500, "pret_referinta_max": 15000},
    {"cod": "30213100-6", "descriere": "Computere portabile (laptopuri)", "pret_referinta_min": 2000, "pret_referinta_max": 8000},
    {"cod": "30213300-8", "descriere": "Computer de birou", "pret_referinta_min": 1500, "pret_referinta_max": 6000},
    {"cod": "48000000-8", "descriere": "Pachete software și sisteme informatice", "pret_referinta_min": 1000, "pret_referinta_max": 50000},
    {"cod": "72000000-5", "descriere": "Servicii IT: consultanță, dezvoltare software", "pret_referinta_min": 5000, "pret_referinta_max": 200000},
    {"cod": "45000000-7", "descriere": "Lucrări de construcții", "pret_referinta_min": 50000, "pret_referinta_max": 5000000},
    {"cod": "45210000-2", "descriere": "Lucrări de construcții de clădiri", "pret_referinta_min": 100000, "pret_referinta_max": 10000000},
    {"cod": "42000000-6", "descriere": "Mașini industriale", "pret_referinta_min": 10000, "pret_referinta_max": 500000},
    {"cod": "42900000-5", "descriere": "Mașini diverse cu destinație generală și specială", "pret_referinta_min": 5000, "pret_referinta_max": 300000},
    {"cod": "71000000-8", "descriere": "Servicii de arhitectură, construcții, inginerie", "pret_referinta_min": 3000, "pret_referinta_max": 100000},
    {"cod": "79000000-4", "descriere": "Servicii pentru întreprinderi: drept, marketing, consultanță", "pret_referinta_min": 2000, "pret_referinta_max": 80000},
    {"cod": "09331200-0", "descriere": "Module solare fotovoltaice", "pret_referinta_min": 10000, "pret_referinta_max": 200000},
    {"cod": "31520000-7", "descriere": "Lămpi și corpuri de iluminat", "pret_referinta_min": 500, "pret_referinta_max": 20000},
    {"cod": "34100000-8", "descriere": "Autovehicule", "pret_referinta_min": 15000, "pret_referinta_max": 150000},
    {"cod": "39100000-3", "descriere": "Mobilier", "pret_referinta_min": 500, "pret_referinta_max": 30000},
]

# AFIR reference prices
AFIR_PRETURI = [
    {"categorie": "Utilaje agricole", "subcategorie": "Tractor", "pret_min": 25000, "pret_max": 120000, "unitate": "buc"},
    {"categorie": "Utilaje agricole", "subcategorie": "Combină", "pret_min": 80000, "pret_max": 350000, "unitate": "buc"},
    {"categorie": "Utilaje agricole", "subcategorie": "Plug", "pret_min": 3000, "pret_max": 15000, "unitate": "buc"},
    {"categorie": "Construcții", "subcategorie": "Hală depozitare", "pret_min": 200, "pret_max": 500, "unitate": "mp"},
    {"categorie": "Construcții", "subcategorie": "Sera/Solar", "pret_min": 50, "pret_max": 150, "unitate": "mp"},
    {"categorie": "IT", "subcategorie": "Laptop", "pret_min": 2000, "pret_max": 6000, "unitate": "buc"},
    {"categorie": "IT", "subcategorie": "Server", "pret_min": 5000, "pret_max": 30000, "unitate": "buc"},
    {"categorie": "Energie", "subcategorie": "Panou fotovoltaic", "pret_min": 200, "pret_max": 500, "unitate": "buc"},
    {"categorie": "Energie", "subcategorie": "Invertor solar", "pret_min": 1000, "pret_max": 5000, "unitate": "buc"},
    {"categorie": "Transport", "subcategorie": "Autoutilitară", "pret_min": 20000, "pret_max": 80000, "unitate": "buc"},
]

PROJECT_TYPES = [
    {"id": "bunuri", "label": "Bunuri"},
    {"id": "bunuri_montaj", "label": "Bunuri cu montaj"},
    {"id": "constructii", "label": "Construcții"},
    {"id": "servicii", "label": "Servicii"},
    {"id": "mixt", "label": "Mixt (bunuri + servicii + construcții)"},
]

DRAFT_TEMPLATES = [
    {"id": "plan_afaceri", "label": "Plan de afaceri", "categorie": "principal", "sectiuni": ["Rezumat executiv", "Descrierea afacerii", "Analiza pieței", "Strategia de marketing", "Planul operațional", "Resurse umane", "Proiecții financiare"]},
    {"id": "cerere_finantare", "label": "Cerere de finanțare", "categorie": "principal", "sectiuni": ["Date solicitant", "Descriere proiect", "Obiective", "Activități", "Buget", "Calendar implementare", "Indicatori"]},
    {"id": "studiu_fezabilitate", "label": "Studiu de fezabilitate", "categorie": "principal", "sectiuni": ["Date generale", "Descriere investiție", "Analiza cererii", "Analiza ofertei", "Capacitate de producție", "Costuri estimative", "Analiza financiară"]},
    {"id": "declaratie_eligibilitate", "label": "Declarație de eligibilitate", "categorie": "declaratie", "sectiuni": ["Identificare solicitant", "Condiții eligibilitate", "Angajamente", "Semnătură"]},
    {"id": "declaratie_angajament", "label": "Declarație de angajament", "categorie": "declaratie", "sectiuni": ["Identificare", "Angajamente financiare", "Angajamente operaționale", "Semnătură"]},
    {"id": "declaratie_neincadrare", "label": "Declarație de neîncadrare în întreprindere în dificultate", "categorie": "declaratie", "sectiuni": ["Date firmă", "Verificare criterii", "Declarație pe proprie răspundere"]},
    {"id": "memoriu_justificativ", "label": "Memoriu justificativ", "categorie": "principal", "sectiuni": ["Date beneficiar", "Justificarea investiției", "Descriere tehnică", "Deviz estimativ"]},
    {"id": "deviz_general", "label": "Deviz general estimativ", "categorie": "financiar", "sectiuni": ["Cheltuieli pentru obținere avize", "Cheltuieli pentru proiectare", "Cheltuieli de construcții", "Cheltuieli cu utilaje", "Alte cheltuieli", "Total"]},
]


def get_programs():
    return PROGRAMS

def get_program(program_id: str):
    return next((p for p in PROGRAMS if p["id"] == program_id), None)

def get_masura(masura_id: str):
    for p in PROGRAMS:
        for m in p["masuri"]:
            if m["id"] == masura_id:
                return {**m, "program_id": p["id"], "program_denumire": p["denumire"]}
    return None

def get_sesiune(sesiune_id: str):
    for p in PROGRAMS:
        for m in p["masuri"]:
            for s in m["sesiuni"]:
                if s["id"] == sesiune_id:
                    return {**s, "masura_id": m["id"], "masura_cod": m["cod"], "masura_denumire": m["denumire"], "program_id": p["id"], "program_denumire": p["denumire"]}
    return None

def search_sicap(query: str):
    q = query.lower()
    return [c for c in SICAP_CPV if q in c["descriere"].lower() or q in c["cod"]]

def search_afir_preturi(query: str):
    q = query.lower()
    return [p for p in AFIR_PRETURI if q in p["subcategorie"].lower() or q in p["categorie"].lower()]

def get_project_types():
    return PROJECT_TYPES

def get_draft_templates():
    return DRAFT_TEMPLATES

def get_draft_template(template_id: str):
    return next((t for t in DRAFT_TEMPLATES if t["id"] == template_id), None)
