"""OCR Service - Real document extraction using GPT-5.2 Vision"""
import os
import uuid
import json
import base64
import logging
from datetime import datetime, timezone
from emergentintegrations.llm.chat import LlmChat, UserMessage, FileContent

logger = logging.getLogger(__name__)

def _get_vision_chat(system_message: str) -> LlmChat:
    chat = LlmChat(
        api_key=os.environ["EMERGENT_LLM_KEY"],
        session_id=str(uuid.uuid4()),
        system_message=system_message
    )
    chat.with_model("openai", "gpt-5.2")
    return chat


ONRC_PROMPT = """Analizează acest document ONRC / Certificat Constatator al unei firme din România.
Extrage TOATE datele disponibile și returnează STRICT un JSON valid cu această structură:
{
  "cui": "string - Cod Unic de Înregistrare (doar cifre)",
  "denumire": "string - Denumirea completă a firmei",
  "forma_juridica": "string - SRL, SA, PFA, etc.",
  "nr_reg_com": "string - Număr registru comerțului (ex: J40/123/2020)",
  "adresa": "string - Adresa completă sediu social",
  "judet": "string - Județul",
  "localitate": "string - Localitatea",
  "cod_postal": "string",
  "telefon": "string sau null",
  "data_infiintare": "string - format YYYY-MM-DD",
  "caen_principal": {"cod": "string - cod CAEN 4 cifre", "descriere": "string"},
  "caen_secundare": [{"cod": "string", "descriere": "string"}],
  "capital_social": "number sau null - în RON",
  "administratori": [{"nume": "string", "functie": "string"}],
  "asociati": [{"nume": "string", "procent": "number"}],
  "stare": "string - ACTIVA, RADIATA, etc.",
  "obiect_activitate": "string - descriere activitate principală"
}

IMPORTANT: 
- Returnează DOAR JSON-ul, fără text suplimentar, fără markdown, fără ```json
- Dacă un câmp nu e vizibil/lizibil, pune null
- CUI trebuie să conțină doar cifre
- Extrage TOATE codurile CAEN vizibile (principal + secundare)"""

CI_PROMPT = """Analizează această Carte de Identitate (CI) / Buletin de identitate din România.
Extrage TOATE datele disponibile și returnează STRICT un JSON valid cu această structură:
{
  "serie": "string - seria CI (ex: RX)",
  "numar": "string - numărul CI",
  "cnp": "string - Cod Numeric Personal (13 cifre)",
  "nume": "string - Numele de familie",
  "prenume": "string - Prenumele complet",
  "data_nastere": "string - format YYYY-MM-DD",
  "sex": "string - M sau F",
  "cetatenie": "string",
  "localitate": "string - domiciliu localitate",
  "adresa": "string - adresa completă de domiciliu",
  "judet": "string",
  "emis_de": "string - cine a emis CI",
  "data_emitere": "string - format YYYY-MM-DD",
  "data_expirare": "string - format YYYY-MM-DD"
}

IMPORTANT:
- Returnează DOAR JSON-ul, fără text suplimentar, fără markdown
- Dacă un câmp nu e vizibil/lizibil, pune null
- CNP trebuie să aibă exact 13 cifre"""

FACTURA_PROMPT = """Analizează această factură fiscală din România.
Extrage TOATE datele și returnează STRICT un JSON valid:
{
  "numar_factura": "string",
  "data_factura": "string YYYY-MM-DD",
  "furnizor": "string - denumire furnizor",
  "cui_furnizor": "string",
  "client": "string - denumire client",
  "cui_client": "string",
  "produse": "string - lista produselor/serviciilor",
  "valoare_fara_tva": "number",
  "tva": "number",
  "total": "number - total cu TVA",
  "moneda": "string - RON/EUR"
}
IMPORTANT: Returnează DOAR JSON-ul. Dacă un câmp lipsește, pune null."""

CONTRACT_PROMPT = """Analizează acest contract din România.
Extrage datele și returnează STRICT un JSON valid:
{
  "numar_contract": "string",
  "data_contract": "string YYYY-MM-DD",
  "parte_1": "string - prima parte contractuală",
  "cui_parte_1": "string",
  "parte_2": "string - a doua parte",
  "cui_parte_2": "string",
  "obiect": "string - obiectul contractului",
  "valoare": "number",
  "moneda": "string",
  "durata": "string",
  "data_start": "string YYYY-MM-DD",
  "data_sfarsit": "string YYYY-MM-DD"
}
IMPORTANT: Returnează DOAR JSON-ul. Dacă un câmp lipsește, pune null."""

BILANT_PROMPT = """Analizează acest bilanț/balanță contabilă din România.
Extrage datele și returnează STRICT un JSON valid:
{
  "an_fiscal": "string",
  "cui_firma": "string",
  "denumire_firma": "string",
  "cifra_afaceri": "number",
  "profit_net": "number",
  "active_totale": "number",
  "datorii_totale": "number",
  "capitaluri_proprii": "number",
  "numar_angajati": "number"
}
IMPORTANT: Returnează DOAR JSON-ul. Dacă un câmp lipsește, pune null."""

GENERIC_PROMPT = """Analizează acest document.
Extrage TOATE informațiile relevante și returnează un JSON valid cu câmpurile detectate.
Structura JSON trebuie să reflecte conținutul documentului (chei descriptive, valori extrase).
IMPORTANT: Returnează DOAR JSON-ul, fără text suplimentar."""

PROMPT_MAP = {
    "ci": CI_PROMPT, "buletin": CI_PROMPT,
    "certificat": ONRC_PROMPT, "onrc": ONRC_PROMPT,
    "factura": FACTURA_PROMPT,
    "contract": CONTRACT_PROMPT,
    "bilant": BILANT_PROMPT, "balanta": BILANT_PROMPT,
}


async def process_ocr(doc_id: str, doc_type: str, filename: str, db, file_path: str = None) -> dict:
    """Process a document using GPT-5.2 Vision for real OCR extraction."""
    logger.info(f"OCR processing: doc_id={doc_id}, type={doc_type}, file={filename}")

    # Find the actual file
    if not file_path:
        base_dirs = [
            os.path.join(os.path.dirname(os.path.dirname(__file__)), "uploads"),
            os.path.join(os.path.dirname(os.path.dirname(__file__)), "uploads", "onrc"),
        ]
        for d in base_dirs:
            for f in os.listdir(d) if os.path.exists(d) else []:
                if doc_id in f:
                    file_path = os.path.join(d, f)
                    break
            if file_path:
                break

    if not file_path or not os.path.exists(file_path):
        logger.warning(f"File not found for {doc_id}, using fallback extraction")
        return _fallback_result(doc_id, doc_type)

    # Read and encode file
    with open(file_path, "rb") as f:
        file_bytes = f.read()
    file_b64 = base64.b64encode(file_bytes).decode("utf-8")

    # Determine content type
    ext = os.path.splitext(file_path)[1].lower()
    ct_map = {".pdf": "application/pdf", ".jpg": "image/jpeg", ".jpeg": "image/jpeg", ".png": "image/png"}
    content_type = ct_map.get(ext)

    # Select prompt based on doc type
    prompt = PROMPT_MAP.get(doc_type, GENERIC_PROMPT)

    try:
        chat = _get_vision_chat("Ești un expert OCR specializat pe documente oficiale românești. Extragi date structurate din imagini/PDF-uri.")

        if content_type in ["image/jpeg", "image/png", "application/pdf"]:
            # Image/PDF: send as file attachment
            message = UserMessage(
                text=prompt,
                file_contents=[FileContent(content_type=content_type, file_content_base64=file_b64)]
            )
        else:
            # Text/other: read content and send as text
            try:
                text_content = file_bytes.decode("utf-8", errors="replace")
            except Exception:
                text_content = file_bytes.decode("latin-1", errors="replace")
            message = UserMessage(text=f"{prompt}\n\nCONȚINUT DOCUMENT:\n{text_content[:8000]}")

        response = await chat.send_message(message)

        # Parse JSON from response
        extracted = _parse_json_response(response)

        if extracted:
            ocr_result = {
                "id": str(uuid.uuid4()),
                "doc_id": doc_id,
                "status": "completed",
                "overall_confidence": 0.95,
                "extracted_fields": extracted,
                "field_confidences": {k: 0.95 for k in extracted.keys() if extracted[k] is not None},
                "low_confidence_fields": [],
                "needs_human_review": False,
                "processing_time_ms": 0,
                "engine": "GPT-5.2 Vision",
                "processed_at": datetime.now(timezone.utc).isoformat()
            }
        else:
            logger.warning(f"Could not parse JSON from GPT response for {doc_id}")
            ocr_result = _fallback_result(doc_id, doc_type)
            ocr_result["raw_response"] = response[:500]

    except Exception as e:
        logger.error(f"GPT Vision OCR failed for {doc_id}: {e}")
        ocr_result = _fallback_result(doc_id, doc_type)
        ocr_result["error"] = str(e)

    # Update document in DB
    await db.documents.update_one({"id": doc_id}, {
        "$set": {
            "ocr_status": ocr_result["status"],
            "ocr_data": ocr_result,
            "updated_at": datetime.now(timezone.utc).isoformat()
        }
    })

    logger.info(f"OCR complete: doc_id={doc_id}, status={ocr_result['status']}, engine={ocr_result.get('engine')}")
    return ocr_result


def _parse_json_response(response: str) -> dict:
    """Try to parse JSON from AI response, handling various formats."""
    if not response:
        return None
    # Clean response
    text = response.strip()
    # Remove markdown code blocks
    if text.startswith("```"):
        text = text.split("\n", 1)[1] if "\n" in text else text[3:]
    if text.endswith("```"):
        text = text[:-3]
    text = text.strip()
    if text.startswith("json"):
        text = text[4:].strip()

    try:
        return json.loads(text)
    except json.JSONDecodeError:
        # Try to find JSON in the text
        start = text.find("{")
        end = text.rfind("}") + 1
        if start >= 0 and end > start:
            try:
                return json.loads(text[start:end])
            except json.JSONDecodeError:
                pass
    return None


def _fallback_result(doc_id: str, doc_type: str) -> dict:
    """Fallback when real OCR fails."""
    return {
        "id": str(uuid.uuid4()),
        "doc_id": doc_id,
        "status": "needs_review",
        "overall_confidence": 0.0,
        "extracted_fields": {},
        "field_confidences": {},
        "low_confidence_fields": [],
        "needs_human_review": True,
        "processing_time_ms": 0,
        "engine": "fallback",
        "processed_at": datetime.now(timezone.utc).isoformat()
    }


async def correct_ocr_field(doc_id: str, field_name: str, corrected_value: str, user_id: str, db) -> dict:
    """Human-in-the-loop: correct an OCR extracted field."""
    doc = await db.documents.find_one({"id": doc_id}, {"_id": 0})
    if not doc or not doc.get("ocr_data"):
        return {"success": False, "error": "Date OCR inexistente"}

    ocr_data = doc["ocr_data"]
    old_value = ocr_data.get("extracted_fields", {}).get(field_name, "")
    ocr_data.setdefault("extracted_fields", {})[field_name] = corrected_value
    ocr_data.setdefault("field_confidences", {})[field_name] = 1.0

    if field_name in ocr_data.get("low_confidence_fields", []):
        ocr_data["low_confidence_fields"].remove(field_name)

    await db.documents.update_one({"id": doc_id}, {
        "$set": {"ocr_data": ocr_data, "updated_at": datetime.now(timezone.utc).isoformat()}
    })

    await db.audit_log.insert_one({
        "id": str(uuid.uuid4()),
        "action": "ocr.field_corrected",
        "entity_type": "document",
        "entity_id": doc_id,
        "user_id": user_id,
        "details": {"field": field_name, "old_value": str(old_value)[:100], "new_value": str(corrected_value)[:100]},
        "timestamp": datetime.now(timezone.utc).isoformat()
    })

    return {"success": True, "ocr_data": ocr_data}
