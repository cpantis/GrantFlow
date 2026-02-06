"""MOCK ANAF Service - Simulates Romanian Tax Authority API"""
import random

async def get_financial_data(cui: str, year: int = 2024) -> dict:
    base_revenue = random.randint(100000, 5000000)
    return {
        "success": True,
        "data": {
            "cui": cui,
            "an": year,
            "cifra_afaceri": base_revenue,
            "profit_net": int(base_revenue * random.uniform(0.05, 0.25)),
            "numar_angajati": random.randint(5, 100),
            "datorii_totale": int(base_revenue * random.uniform(0.1, 0.4)),
            "active_totale": int(base_revenue * random.uniform(0.5, 1.5)),
            "capitaluri_proprii": int(base_revenue * random.uniform(0.2, 0.8)),
            "impozit_profit": int(base_revenue * random.uniform(0.01, 0.05)),
            "tva_platit": int(base_revenue * 0.19 * random.uniform(0.3, 0.7)),
            "obligatii_restante": random.choice([0, 0, 0, random.randint(1000, 50000)]),
            "status_fiscal": "ACTIV" if random.random() > 0.1 else "INACTIV",
            "platitor_tva": random.choice([True, True, True, False]),
            "sursa": "ANAF_MOCK"
        }
    }

async def get_financial_history(cui: str, years: int = 3) -> dict:
    history = []
    for y in range(2024, 2024 - years, -1):
        result = await get_financial_data(cui, y)
        history.append(result["data"])
    return {"success": True, "data": history}

async def check_obligatii_restante(cui: str) -> dict:
    has_debts = random.random() < 0.15
    return {
        "success": True,
        "data": {
            "cui": cui,
            "are_obligatii_restante": has_debts,
            "suma_restanta": random.randint(5000, 100000) if has_debts else 0,
            "data_verificare": "2025-12-15",
            "sursa": "ANAF_MOCK"
        }
    }
