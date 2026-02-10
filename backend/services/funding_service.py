"""Calls & Applications Service - Domain model for funding workflow"""

PROGRAMS = [
    {"id": "pnrr", "name": "PNRR", "source": "fonduri.eu", "description": "Planul Național de Redresare și Reziliență"},
    {"id": "afir", "name": "AFIR", "source": "AFIR", "description": "Agenția pentru Finanțarea Investițiilor Rurale"},
    {"id": "poc", "name": "POC", "source": "fonduri.eu", "description": "Programul Operațional Competitivitate"},
    {"id": "por", "name": "POR", "source": "fonduri.eu", "description": "Programul Operațional Regional"},
    {"id": "horizon", "name": "Horizon Europe", "source": "EU", "description": "Programul-cadru pentru cercetare și inovare"},
]

MEASURES = [
    {"id": "pnrr-c9-i1", "program_id": "pnrr", "name": "Sprijin sector privat, cercetare, dezvoltare", "code": "C9-I1"},
    {"id": "pnrr-c10-i1", "program_id": "pnrr", "name": "Fondul local - Digitalizare", "code": "C10-I1"},
    {"id": "pnrr-c11-i3", "program_id": "pnrr", "name": "Turism și cultură", "code": "C11-I3"},
    {"id": "afir-sm6-1", "program_id": "afir", "name": "Instalarea tinerilor fermieri", "code": "sM6.1"},
    {"id": "afir-sm4-1", "program_id": "afir", "name": "Investiții în exploatații agricole", "code": "sM4.1"},
    {"id": "afir-sm6-4", "program_id": "afir", "name": "Investiții activități neagricole", "code": "sM6.4"},
    {"id": "poc-2-2", "program_id": "poc", "name": "Creșterea competitivității IMM", "code": "2.2"},
    {"id": "por-2-1a", "program_id": "por", "name": "Microîntreprinderi", "code": "2.1A"},
]

CALLS = [
    {"id": "pnrr-c9-i1-2025", "measure_id": "pnrr-c9-i1", "name": "Apel C9-I1 / 2025", "code": "C9-I1-2025", "start_date": "2025-01-15", "end_date": "2025-06-30", "status": "activ", "budget": 100000000, "value_min": 50000, "value_max": 500000, "beneficiaries": ["IMM", "Startup"], "region": "Național"},
    {"id": "pnrr-c10-i1-2025", "measure_id": "pnrr-c10-i1", "name": "Apel Digitalizare / 2025", "code": "C10-I1-2025", "start_date": "2025-03-01", "end_date": "2025-09-30", "status": "activ", "budget": 200000000, "value_min": 100000, "value_max": 2000000, "beneficiaries": ["IMM", "Mari Întreprinderi"], "region": "Național"},
    {"id": "afir-sm6-4-2025", "measure_id": "afir-sm6-4", "name": "Sesiune sM6.4 / 2025", "code": "sM6.4-2025", "start_date": "2025-01-15", "end_date": "2025-08-15", "status": "activ", "budget": 100000000, "value_min": 50000, "value_max": 200000, "beneficiaries": ["IMM rural", "PFA"], "region": "Rural"},
    {"id": "poc-2-2-2025", "measure_id": "poc-2-2", "name": "Apel POC 2.2 / 2025", "code": "2.2-2025", "start_date": "2025-05-01", "end_date": "2025-11-30", "status": "activ", "budget": 120000000, "value_min": 200000, "value_max": 1500000, "beneficiaries": ["IMM"], "region": "Național"},
]

APPLICATION_STATES = [
    "draft", "call_selected", "guide_ready", "preeligibility",
    "data_collection", "document_collection", "writing",
    "validation", "ready_for_submission", "submitted",
    "contracting", "implementation", "monitoring"
]

APPLICATION_STATE_LABELS = {
    "draft": "Ciornă", "call_selected": "Sesiune aleasă", "guide_ready": "Ghid disponibil",
    "preeligibility": "Pre-eligibilitate", "data_collection": "Colectare date",
    "document_collection": "Colectare documente", "writing": "Redactare",
    "validation": "Validare", "ready_for_submission": "Pregătit depunere",
    "submitted": "Depus", "contracting": "Contractare",
    "implementation": "Implementare", "monitoring": "Monitorizare"
}

APPLICATION_TRANSITIONS = {
    "draft": ["call_selected"],
    "call_selected": ["guide_ready", "draft"],
    "guide_ready": ["preeligibility", "call_selected"],
    "preeligibility": ["data_collection", "guide_ready"],
    "data_collection": ["document_collection", "preeligibility"],
    "document_collection": ["writing", "data_collection"],
    "writing": ["validation", "document_collection"],
    "validation": ["ready_for_submission", "writing"],
    "ready_for_submission": ["submitted", "validation"],
    "submitted": ["contracting"],
    "contracting": ["implementation"],
    "implementation": ["monitoring"],
    "monitoring": []
}

DEFAULT_FOLDER_GROUPS = [
    {"key": "achizitii", "name": "01_Achiziții", "order": 1},
    {"key": "depunere", "name": "02_Depunere", "order": 2},
    {"key": "contractare", "name": "03_Contractare", "order": 3},
    {"key": "implementare", "name": "04_Implementare", "order": 4},
]

DRAFT_TEMPLATES = [
    {"id": "plan_afaceri", "label": "Plan de afaceri", "category": "principal", "sections": ["Rezumat executiv", "Descrierea afacerii", "Analiza pieței", "Strategia de marketing", "Planul operațional", "Resurse umane", "Proiecții financiare"]},
    {"id": "cerere_finantare", "label": "Cerere de finanțare", "category": "principal", "sections": ["Date solicitant", "Descriere proiect", "Obiective", "Activități", "Buget", "Calendar implementare", "Indicatori"]},
    {"id": "studiu_fezabilitate", "label": "Studiu de fezabilitate", "category": "principal", "sections": ["Date generale", "Descriere investiție", "Analiza cererii", "Capacitate producție", "Costuri estimative", "Analiza financiară"]},
    {"id": "declaratie_eligibilitate", "label": "Declarație de eligibilitate", "category": "declaratie", "sections": ["Identificare solicitant", "Condiții eligibilitate", "Angajamente", "Semnătură"]},
    {"id": "declaratie_angajament", "label": "Declarație de angajament", "category": "declaratie", "sections": ["Identificare", "Angajamente financiare", "Angajamente operaționale", "Semnătură"]},
    {"id": "memoriu_justificativ", "label": "Memoriu justificativ", "category": "principal", "sections": ["Date beneficiar", "Justificarea investiției", "Descriere tehnică", "Deviz estimativ"]},
    {"id": "deviz_general", "label": "Deviz general estimativ", "category": "financiar", "sections": ["Cheltuieli avize", "Cheltuieli proiectare", "Cheltuieli construcții", "Cheltuieli utilaje", "Alte cheltuieli", "Total"]},
]


def get_programs(): return PROGRAMS
def get_measures(program_id=None):
    if program_id: return [m for m in MEASURES if m["program_id"] == program_id]
    return MEASURES
def get_calls(measure_id=None):
    if measure_id: return [c for c in CALLS if c["measure_id"] == measure_id]
    return CALLS
def get_call(call_id):
    return next((c for c in CALLS if c["id"] == call_id), None)
def get_templates(): return DRAFT_TEMPLATES
def get_template(tid):
    return next((t for t in DRAFT_TEMPLATES if t["id"] == tid), None)
