"""OCR Service - Simulates OCR processing pipeline for documents"""
import random
import uuid
import logging
from datetime import datetime, timezone

logger = logging.getLogger(__name__)

# Mock OCR results for different document types
MOCK_OCR_TEMPLATES = {
    "ci": {
        "fields": {
            "serie": "RX",
            "numar": str(random.randint(100000, 999999)),
            "cnp": "1850101" + str(random.randint(100000, 999999)),
            "nume": "POPESCU",
            "prenume": "ION ALEXANDRU",
            "data_nastere": "01.01.1985",
            "sex": "M",
            "cetatenie": "Română",
            "localitate": "București",
            "adresa": "Str. Exemplu nr. 10, Bl. A1, Sc. 2, Et. 3, Ap. 15",
            "emis_de": "SPCEP S1",
            "data_emitere": "15.03.2022",
            "data_expirare": "15.03.2032"
        },
        "avg_confidence": 0.92
    },
    "bilant": {
        "fields": {
            "an_fiscal": "2024",
            "cui_firma": "12345678",
            "denumire_firma": "SC TECH SOLUTIONS SRL",
            "active_imobilizate": str(random.randint(50000, 500000)),
            "active_circulante": str(random.randint(100000, 1000000)),
            "total_active": str(random.randint(200000, 2000000)),
            "capitaluri_proprii": str(random.randint(50000, 500000)),
            "datorii_totale": str(random.randint(30000, 300000)),
            "cifra_afaceri": str(random.randint(500000, 5000000)),
            "profit_brut": str(random.randint(50000, 500000)),
            "profit_net": str(random.randint(30000, 300000)),
            "numar_angajati": str(random.randint(5, 100))
        },
        "avg_confidence": 0.88
    },
    "factura": {
        "fields": {
            "numar_factura": f"FV-{random.randint(1000, 9999)}",
            "data_factura": "2025-11-15",
            "furnizor": "SC FURNIZOR SRL",
            "cui_furnizor": str(random.randint(10000000, 99999999)),
            "client": "SC TECH SOLUTIONS SRL",
            "produse": "Echipamente IT - 5 buc",
            "valoare_fara_tva": str(random.randint(5000, 50000)),
            "tva": str(random.randint(1000, 10000)),
            "total": str(random.randint(6000, 60000)),
            "moneda": "RON"
        },
        "avg_confidence": 0.90
    },
    "contract": {
        "fields": {
            "numar_contract": f"C-{random.randint(100, 999)}/2025",
            "data_contract": "2025-10-01",
            "parte_1": "SC TECH SOLUTIONS SRL",
            "parte_2": "SC FURNIZOR ECHIPAMENTE SRL",
            "obiect": "Furnizare echipamente IT conform caiet de sarcini",
            "valoare": str(random.randint(50000, 500000)),
            "durata": "12 luni",
            "data_start": "2025-10-15",
            "data_sfarsit": "2026-10-14"
        },
        "avg_confidence": 0.85
    },
    "imputernicire": {
        "fields": {
            "emitent": "SC TECH SOLUTIONS SRL",
            "cui_emitent": "12345678",
            "imputernicit": "IONESCU MARIA",
            "cnp_imputernicit": "2900215" + str(random.randint(100000, 999999)),
            "scope": "Depunere și gestionare proiecte de finanțare",
            "data_emitere": "2025-09-01",
            "data_expirare": "2026-09-01",
            "semnatura": "DA",
            "stampila": "DA"
        },
        "avg_confidence": 0.87
    }
}


async def process_ocr(doc_id: str, doc_type: str, filename: str, db) -> dict:
    """
    Simulate OCR processing on a document.
    Returns extracted fields with confidence scores.
    """
    logger.info(f"OCR processing: doc_id={doc_id}, type={doc_type}, file={filename}")

    # Determine which template to use
    template = MOCK_OCR_TEMPLATES.get(doc_type)
    if not template:
        # Generic OCR for unknown types
        template = {
            "fields": {
                "text_extras": f"Document procesat: {filename}",
                "tip_detectat": doc_type or "necunoscut",
                "pagini": str(random.randint(1, 20)),
                "limba": "română",
                "cuvinte_detectate": str(random.randint(100, 5000)),
            },
            "avg_confidence": random.uniform(0.70, 0.95)
        }

    # Generate per-field confidence scores
    extracted_fields = {}
    field_confidences = {}
    low_confidence_fields = []

    for field_name, field_value in template["fields"].items():
        confidence = min(1.0, max(0.0, template["avg_confidence"] + random.uniform(-0.15, 0.10)))
        extracted_fields[field_name] = field_value
        field_confidences[field_name] = round(confidence, 3)
        if confidence < 0.80:
            low_confidence_fields.append(field_name)

    overall_confidence = round(sum(field_confidences.values()) / len(field_confidences), 3) if field_confidences else 0

    # Determine OCR status
    if overall_confidence >= 0.85:
        ocr_status = "completed"
    elif overall_confidence >= 0.70:
        ocr_status = "needs_review"
    else:
        ocr_status = "low_confidence"

    ocr_result = {
        "id": str(uuid.uuid4()),
        "doc_id": doc_id,
        "status": ocr_status,
        "overall_confidence": overall_confidence,
        "extracted_fields": extracted_fields,
        "field_confidences": field_confidences,
        "low_confidence_fields": low_confidence_fields,
        "needs_human_review": len(low_confidence_fields) > 0,
        "processing_time_ms": random.randint(800, 3500),
        "engine": "GrantFlow OCR Mock v1.0",
        "processed_at": datetime.now(timezone.utc).isoformat()
    }

    # Update document in DB
    await db.documents.update_one({"id": doc_id}, {
        "$set": {
            "ocr_status": ocr_status,
            "ocr_data": ocr_result,
            "updated_at": datetime.now(timezone.utc).isoformat()
        }
    })

    # Store OCR result separately for history
    await db.ocr_results.insert_one({**ocr_result, "version": 1})

    logger.info(f"OCR complete: doc_id={doc_id}, confidence={overall_confidence}, status={ocr_status}")
    return ocr_result


async def correct_ocr_field(doc_id: str, field_name: str, corrected_value: str, user_id: str, db) -> dict:
    """Human-in-the-loop: correct an OCR extracted field."""
    doc = await db.documents.find_one({"id": doc_id}, {"_id": 0})
    if not doc or not doc.get("ocr_data"):
        return {"success": False, "error": "Date OCR inexistente"}

    ocr_data = doc["ocr_data"]
    old_value = ocr_data["extracted_fields"].get(field_name, "")
    ocr_data["extracted_fields"][field_name] = corrected_value
    ocr_data["field_confidences"][field_name] = 1.0  # Manual correction = 100% confidence

    # Remove from low confidence list
    if field_name in ocr_data.get("low_confidence_fields", []):
        ocr_data["low_confidence_fields"].remove(field_name)

    # Recalculate
    confs = list(ocr_data["field_confidences"].values())
    ocr_data["overall_confidence"] = round(sum(confs) / len(confs), 3) if confs else 0
    ocr_data["needs_human_review"] = len(ocr_data.get("low_confidence_fields", [])) > 0
    if not ocr_data["needs_human_review"] and ocr_data["overall_confidence"] >= 0.85:
        ocr_data["status"] = "completed"

    await db.documents.update_one({"id": doc_id}, {
        "$set": {
            "ocr_data": ocr_data,
            "ocr_status": ocr_data["status"],
            "updated_at": datetime.now(timezone.utc).isoformat()
        }
    })

    # Audit
    await db.audit_log.insert_one({
        "id": str(uuid.uuid4()),
        "action": "ocr.field_corrected",
        "entity_type": "document",
        "entity_id": doc_id,
        "user_id": user_id,
        "details": {"field": field_name, "old_value": old_value, "new_value": corrected_value},
        "timestamp": datetime.now(timezone.utc).isoformat()
    })

    return {"success": True, "ocr_data": ocr_data}
