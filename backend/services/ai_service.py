"""AI Service - Orchestrates AI Agents using OpenAI GPT-5.2 via Emergent"""
import os
import uuid
import logging
from emergentintegrations.llm.chat import LlmChat, UserMessage

logger = logging.getLogger(__name__)

MARKDOWN_INSTRUCTION = (
    "\n\nFORMATARE OBLIGATORIE: Răspunde ÎNTOTDEAUNA folosind Markdown structurat:\n"
    "- Folosește **bold** pentru termeni importanți și concluzii\n"
    "- Folosește headings (## și ###) pentru secțiuni\n"
    "- Folosește liste cu bullet points (- ) pentru enumerări\n"
    "- Folosește liste numerotate (1. 2. 3.) pentru pași secvențiali\n"
    "- Folosește > blockquote pentru observații importante sau atenționări\n"
    "- Folosește `cod` pentru numere, coduri CAEN, CUI-uri, sume\n"
    "- Separă secțiunile cu linii goale pentru lizibilitate\n"
    "- Păstrează paragrafele scurte (max 3-4 rânduri)\n"
    "- Limba: română"
)

def _get_chat(system_message: str, session_id: str = None) -> LlmChat:
    chat = LlmChat(
        api_key=os.environ["EMERGENT_LLM_KEY"],
        session_id=session_id or str(uuid.uuid4()),
        system_message=system_message + MARKDOWN_INSTRUCTION
    )
    chat.with_model("openai", "gpt-5.2")
    return chat

async def check_eligibility(firm_data: dict, program_info: dict) -> dict:
    chat = _get_chat(
        "Ești un expert în finanțări europene și naționale din România. "
        "Analizează datele firmei și cerințele programului de finanțare. "
        "Oferă un raport structurat cu secțiuni clare: Rezumat, Scor Eligibilitate, "
        "Criterii Îndeplinite, Blocaje Identificate, Recomandări."
    )
    prompt = (
        f"Analizează eligibilitatea firmei pentru programul de finanțare:\n\n"
        f"**Date firmă:**\n```\n{firm_data}\n```\n\n"
        f"**Cerințe program:**\n```\n{program_info}\n```\n\n"
        f"Oferă un raport de eligibilitate detaliat și structurat."
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
        f"Completează secțiunea **'{section}'** a documentului:\n\n"
        f"**Template:** {template}\n\n"
        f"**Date disponibile:** {data}\n\n"
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
        "Identifică orice inconsistență sau contradicție. "
        "Structurează răspunsul cu: Rezumat, Verificări Efectuate, Probleme Găsite, Recomandări."
    )
    prompt = (
        f"Validează coerența dosarului de proiect:\n\n"
        f"**Date proiect:**\n```\n{project_data}\n```\n\n"
        f"**Documente:**\n```\n{documents}\n```\n\n"
        f"Identifică inconsistențe și oferă recomandări structurate."
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
        "Răspunde concis dar structurat. Folosește liste pentru pași, bold pentru elemente cheie."
    )
    prompt = f"**Context proiect:**\n```\n{context}\n```\n\n**Întrebarea utilizatorului:** {message}"
    try:
        response = await chat.send_message(UserMessage(text=prompt))
        return {"success": True, "result": response}
    except Exception as e:
        logger.error(f"AI navigator failed: {e}")
        return {"success": False, "error": str(e)}
