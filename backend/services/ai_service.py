"""AI Service - Orchestrates AI Agents using OpenAI GPT-5.2 via Emergent"""
import os
import uuid
import logging
from emergentintegrations.llm.chat import LlmChat, UserMessage

logger = logging.getLogger(__name__)

def _get_chat(system_message: str, session_id: str = None) -> LlmChat:
    chat = LlmChat(
        api_key=os.environ["EMERGENT_LLM_KEY"],
        session_id=session_id or str(uuid.uuid4()),
        system_message=system_message
    )
    chat.with_model("openai", "gpt-5.2")
    return chat

async def check_eligibility(firm_data: dict, program_info: dict) -> dict:
    chat = _get_chat(
        "Ești un expert în finanțări europene și naționale din România. "
        "Analizează datele firmei și cerințele programului de finanțare. "
        "Răspunde DOAR în format JSON cu câmpurile: eligible (bool), score (0-100), "
        "blocaje (lista), recomandari (lista), detalii (string)."
    )
    prompt = (
        f"Analizează eligibilitatea firmei pentru programul de finanțare:\n\n"
        f"Date firmă: {firm_data}\n\n"
        f"Cerințe program: {program_info}\n\n"
        f"Oferă un raport de eligibilitate detaliat."
    )
    try:
        response = await chat.send_message(UserMessage(text=prompt))
        return {"success": True, "result": response}
    except Exception as e:
        logger.error(f"AI eligibility check failed: {e}")
        return {"success": False, "error": str(e)}

async def generate_document_section(template: str, data: dict, section: str) -> dict:
    chat = _get_chat(
        "Ești un expert în redactarea documentelor pentru proiecte de finanțare în România. "
        "Completează secțiunile documentului pe baza datelor furnizate. "
        "NU inventa date. Folosește doar informațiile din contextul furnizat. "
        "Scrie într-un stil formal, profesional, adecvat documentelor oficiale."
    )
    prompt = (
        f"Completează secțiunea '{section}' a documentului:\n\n"
        f"Template: {template}\n\n"
        f"Date disponibile: {data}\n\n"
        f"Generează textul secțiunii conform cerințelor."
    )
    try:
        response = await chat.send_message(UserMessage(text=prompt))
        return {"success": True, "result": response}
    except Exception as e:
        logger.error(f"AI doc generation failed: {e}")
        return {"success": False, "error": str(e)}

async def validate_coherence(documents: list, project_data: dict) -> dict:
    chat = _get_chat(
        "Ești un validator de coerență pentru dosare de finanțare. "
        "Verifică consistența între documente, buget, achiziții și descrierea proiectului. "
        "Identifică orice inconsistență sau contradicție."
    )
    prompt = (
        f"Validează coerența dosarului de proiect:\n\n"
        f"Date proiect: {project_data}\n\n"
        f"Documente: {documents}\n\n"
        f"Identifică inconsistențe și oferă recomandări."
    )
    try:
        response = await chat.send_message(UserMessage(text=prompt))
        return {"success": True, "result": response}
    except Exception as e:
        logger.error(f"AI validation failed: {e}")
        return {"success": False, "error": str(e)}

async def chat_navigator(message: str, context: dict) -> dict:
    chat = _get_chat(
        "Ești Ghidul GrantFlow, un asistent AI care ajută utilizatorii să navigheze "
        "procesul de pregătire a dosarelor de finanțare. Explici pașii următori, "
        "clarifici blocajele și oferi recomandări. Nu ai rol decizional, doar informativ. "
        "Răspunde în limba română, concis și clar."
    )
    prompt = f"Context proiect: {context}\n\nÎntrebarea utilizatorului: {message}"
    try:
        response = await chat.send_message(UserMessage(text=prompt))
        return {"success": True, "result": response}
    except Exception as e:
        logger.error(f"AI navigator failed: {e}")
        return {"success": False, "error": str(e)}
