"""ONRC Service - Real integration with OpenAPI.ro for Romanian company data"""
import os
import logging
import httpx

logger = logging.getLogger(__name__)

OPENAPI_BASE = "https://api.openapi.ro/api"
OPENAPI_KEY = os.environ.get("OPENAPI_RO_KEY", "")


def _headers():
    return {"x-api-key": OPENAPI_KEY}


def _parse_stare(stare_raw: str) -> str:
    """Parse the status string to a simple status."""
    if not stare_raw:
        return "NECUNOSCUT"
    s = stare_raw.upper()
    if "INREGISTRAT" in s:
        return "ACTIVA"
    if "RADIAT" in s:
        return "RADIATA"
    if "DIZOLVARE" in s:
        return "IN_DIZOLVARE"
    if "INSOLVENTA" in s or "FALIMENT" in s:
        return "INSOLVENTA"
    return stare_raw


def _parse_reg_com(nr_reg: str) -> str:
    """Parse J295462014 -> J29/546/2014"""
    if not nr_reg or len(nr_reg) < 5:
        return nr_reg or ""
    # Try to parse format like J295462014
    import re
    m = re.match(r'^([A-Z])(\d{2})(\d+?)(\d{4})$', nr_reg)
    if m:
        return f"{m.group(1)}{m.group(2)}/{m.group(3)}/{m.group(4)}"
    return nr_reg


def _extract_data_infiintare(stare_raw: str) -> str:
    """Extract founding date from stare string."""
    if not stare_raw:
        return ""
    import re
    months = {
        "Ianuarie": "01", "Februarie": "02", "Martie": "03", "Aprilie": "04",
        "Mai": "05", "Iunie": "06", "Iulie": "07", "August": "08",
        "Septembrie": "09", "Octombrie": "10", "Noiembrie": "11", "Decembrie": "12"
    }
    m = re.search(r'(\d{1,2})\s+(\w+)\s+(\d{4})', stare_raw)
    if m:
        day = m.group(1).zfill(2)
        month_name = m.group(2)
        year = m.group(3)
        month = months.get(month_name, "01")
        return f"{year}-{month}-{day}"
    return ""


async def lookup_cui(cui: str) -> dict:
    """Lookup company by CUI using OpenAPI.ro real API."""
    if not OPENAPI_KEY:
        logger.error("OPENAPI_RO_KEY not configured")
        return {"success": False, "error": "Serviciul ONRC nu este configurat"}

    # Clean CUI
    cui_clean = cui.strip().replace("RO", "").replace("ro", "").strip()

    try:
        async with httpx.AsyncClient(timeout=15) as client:
            resp = await client.get(
                f"{OPENAPI_BASE}/companies/{cui_clean}",
                headers=_headers()
            )

        if resp.status_code == 200:
            raw = resp.json()
            data = {
                "cui": raw.get("cif", cui_clean),
                "denumire": raw.get("denumire", ""),
                "forma_juridica": _detect_forma_juridica(raw.get("denumire", "")),
                "nr_reg_com": _parse_reg_com(raw.get("numar_reg_com", "")),
                "adresa": raw.get("adresa", ""),
                "cod_postal": raw.get("cod_postal", ""),
                "judet": raw.get("judet", ""),
                "localitate": _extract_localitate(raw.get("adresa", ""), raw.get("judet", "")),
                "stare": _parse_stare(raw.get("stare", "")),
                "stare_detalii": raw.get("stare", ""),
                "data_infiintare": _extract_data_infiintare(raw.get("stare", "")),
                "telefon": raw.get("telefon"),
                "fax": raw.get("fax"),
                "tva": raw.get("tva"),
                "tva_la_incasare": raw.get("tva_la_incasare", []),
                "impozit_micro": raw.get("impozit_micro"),
                "impozit_profit": raw.get("impozit_profit"),
                "ultima_declaratie": raw.get("ultima_declaratie"),
                "radiata": raw.get("radiata", False),
                "caen_principal": None,  # Not available in base endpoint
                "caen_secundare": [],
                "administratori": [],  # Not available in OpenAPI.ro free tier
                "asociati": [],
                "capital_social": None,
                "nr_angajati": None,
                "sedii_secundare": [],
                "meta": raw.get("meta", {}),
                "sursa": "OpenAPI.ro"
            }
            logger.info(f"OpenAPI.ro: Found company {data['denumire']} (CUI: {cui_clean})")
            return {"success": True, "data": data}

        elif resp.status_code == 202:
            body = resp.json()
            logger.info(f"OpenAPI.ro: CUI {cui_clean} valid but not yet in DB, will be processed")
            return {
                "success": False,
                "error": f"CUI {cui_clean} este valid dar nu este încă procesat. Încercați din nou în câteva minute.",
                "retry": True
            }

        elif resp.status_code == 404:
            body = resp.json()
            error_info = body.get("error", {})
            if isinstance(error_info, dict):
                cif_valid = error_info.get("additional_info", {}).get("cif_valid", False)
                if not cif_valid:
                    return {"success": False, "error": f"CUI {cui_clean} nu este valid"}
            return {"success": False, "error": f"Firma cu CUI {cui_clean} nu a fost găsită"}

        elif resp.status_code == 429:
            logger.warning("OpenAPI.ro rate limit exceeded")
            return {"success": False, "error": "Limita de cereri API depășită. Încercați mai târziu."}

        else:
            logger.error(f"OpenAPI.ro error: {resp.status_code} - {resp.text}")
            return {"success": False, "error": f"Eroare la interogarea ONRC (cod: {resp.status_code})"}

    except httpx.TimeoutException:
        logger.error(f"OpenAPI.ro timeout for CUI {cui_clean}")
        return {"success": False, "error": "Serviciul ONRC nu răspunde. Încercați mai târziu."}
    except Exception as e:
        logger.error(f"OpenAPI.ro exception: {e}")
        return {"success": False, "error": f"Eroare la conectarea cu ONRC: {str(e)}"}


def _detect_forma_juridica(denumire: str) -> str:
    """Detect legal form from company name."""
    d = denumire.upper()
    if "S.R.L." in d or "SRL" in d:
        return "SRL"
    if "S.A." in d or " SA " in d or d.endswith(" SA"):
        return "SA"
    if "S.C.S." in d or "SCS" in d:
        return "SCS"
    if "S.N.C." in d or "SNC" in d:
        return "SNC"
    if "P.F.A." in d or "PFA" in d:
        return "PFA"
    if "I.I." in d:
        return "II"
    if "O.N.G." in d or "ONG" in d or "ASOCIAT" in d or "FUNDATI" in d:
        return "ONG"
    return "ALTELE"


def _extract_localitate(adresa: str, judet: str) -> str:
    """Try to extract locality from address."""
    if not adresa:
        return judet or ""
    parts = adresa.split(",")
    if len(parts) >= 3:
        return parts[-1].strip()
    return judet or ""


async def get_certificat_constatator(cui: str) -> dict:
    """Get certificate data - uses same company lookup since OpenAPI.ro provides all data."""
    result = await lookup_cui(cui)
    if not result["success"]:
        return {"success": False, "error": "Nu s-au putut obține datele"}

    data = result["data"]
    return {
        "success": True,
        "certificat": {
            "numar": f"CC-{data['cui']}-OPENAPI",
            "data_emitere": data.get("meta", {}).get("updated_at", "")[:10],
            "valabil_pana": "",
            "firma": data,
            "status": "VALID",
            "sursa": "OpenAPI.ro"
        }
    }
