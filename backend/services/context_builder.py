"""Project Context Builder - Builds complete context for all agents from all available data"""

async def build_full_context(app_id: str, db) -> dict:
    """
    Aggregates ALL available data for a project into a single context dict.
    Used by every agent to have complete awareness of the project state.
    """
    app = await db.applications.find_one({"id": app_id}, {"_id": 0})
    if not app:
        return {}

    org = await db.organizations.find_one({"id": app.get("company_id")}, {"_id": 0})

    # --- Firm data ---
    firma = {}
    if org:
        firma = {
            "denumire": org.get("denumire"),
            "cui": org.get("cui"),
            "forma_juridica": org.get("forma_juridica"),
            "nr_reg_com": org.get("nr_reg_com"),
            "adresa": org.get("adresa"),
            "judet": org.get("judet"),
            "stare": org.get("stare"),
            "stare_detalii": org.get("stare_detalii"),
            "data_infiintare": org.get("data_infiintare"),
            "caen_principal": org.get("caen_principal"),
            "caen_secundare": org.get("caen_secundare", []),
            "nr_angajati": org.get("nr_angajati"),
            "capital_social": org.get("capital_social"),
            "telefon": org.get("telefon"),
            "date_financiare": org.get("date_financiare") or org.get("date_financiare_ocr"),
        }

    # --- Program / Call data ---
    program = {
        "program": app.get("program_name"),
        "masura": app.get("measure_name"),
        "masura_cod": app.get("measure_code"),
        "sesiune": app.get("call_name"),
        "sesiune_cod": app.get("call_code"),
        "buget_sesiune": app.get("call_budget"),
        "valoare_min": app.get("call_value_min"),
        "valoare_max": app.get("call_value_max"),
        "beneficiari_eligibili": app.get("call_beneficiaries", []),
        "regiune": app.get("call_region"),
        "data_start": app.get("call_start_date"),
        "data_sfarsit": app.get("call_end_date"),
    }

    # --- Guide extracted data ---
    guide_data = {}
    guide_assets = app.get("guide_assets", [])
    for g in guide_assets:
        ec = g.get("extracted_content", {})
        if ec:
            # Merge all guide extractions
            for k, v in ec.items():
                if v and (k not in guide_data or not guide_data[k]):
                    guide_data[k] = v

    criterii_ghid = app.get("criterii_eligibilitate_ghid", []) or guide_data.get("criterii_eligibilitate", [])
    grila_ghid = app.get("grila_conformitate_ghid", []) or guide_data.get("grila_conformitate", [])
    docs_obligatorii_ghid = guide_data.get("documente_obligatorii", [])
    activitati_ghid = app.get("activitati_eligibile", []) or guide_data.get("activitati_eligibile", [])
    cheltuieli_ghid = app.get("cheltuieli_eligibile", []) or guide_data.get("cheltuieli_eligibile", [])

    # --- Extracted from links ---
    link_data = app.get("extracted_data", {}).get("scraped_info", "")

    # --- Project config ---
    config = {
        "titlu": app.get("title"),
        "descriere": app.get("description"),
        "buget_estimat": app.get("budget_estimated"),
        "tip_proiect": app.get("tip_proiect"),
        "locatie": app.get("locatie_implementare"),
        "judet_implementare": app.get("judet_implementare"),
        "tema": app.get("tema_proiect"),
        "status": app.get("status"),
        "status_label": app.get("status_label"),
    }

    # --- Documents status ---
    req_docs = app.get("required_documents", [])
    uploaded_docs = app.get("documents", [])
    drafts = app.get("drafts", [])
    achizitii = app.get("achizitii", [])

    docs_summary = {
        "total_cerute": len(req_docs),
        "total_incarcate": len(uploaded_docs),
        "total_lipsa": len([r for r in req_docs if r.get("status") == "missing"]),
        "checklist_frozen": app.get("checklist_frozen", False),
        "drafturi_generate": len(drafts),
        "ghiduri_incarcate": len(guide_assets),
        "achizitii_count": len(achizitii),
        "achizitii_total": sum(a.get("cantitate", 1) * a.get("pret_unitar", 0) for a in achizitii),
    }

    # Detailed doc list
    doc_list = []
    for d in uploaded_docs:
        detail = {"filename": d.get("filename"), "folder": d.get("folder_group"), "tip": d.get("tip_document"), "status": d.get("status"), "ocr_status": d.get("ocr_status")}
        if d.get("ocr_data", {}).get("extracted_fields"):
            detail["ocr_extras"] = {k: str(v)[:80] for k, v in list(d["ocr_data"]["extracted_fields"].items())[:10]}
        doc_list.append(detail)

    # --- Compliance reports ---
    reports = await db.compliance_reports.find({"application_id": app_id}, {"_id": 0}).sort("created_at", -1).to_list(5)
    reports_summary = [{"type": r.get("type"), "date": r.get("created_at", "")[:10]} for r in reports]

    return {
        "firma": firma,
        "program": program,
        "config": config,
        "ghid": {
            "criterii_eligibilitate": criterii_ghid,
            "grila_conformitate": grila_ghid,
            "documente_obligatorii": docs_obligatorii_ghid,
            "activitati_eligibile": activitati_ghid,
            "cheltuieli_eligibile": cheltuieli_ghid,
            "rezumat_ghid": guide_data.get("rezumat", ""),
            "date_din_linkuri": link_data[:1500] if link_data else "",
        },
        "documente": docs_summary,
        "documente_detaliu": doc_list,
        "rapoarte_anterioare": reports_summary,
    }
