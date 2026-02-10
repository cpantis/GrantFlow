"""AI Service - All agents use full project context"""
import os
import uuid
import json
import logging
from emergentintegrations.llm.chat import LlmChat, UserMessage

logger = logging.getLogger(__name__)

MARKDOWN_INSTRUCTION = (
    "\n\nFORMATARE: Răspunde ÎNTOTDEAUNA în Markdown structurat (## headings, **bold**, liste, > blockquote). Limba: română."
)

def _get_chat(system_message: str, extra_rules: str = "") -> LlmChat:
    full_system = system_message + MARKDOWN_INSTRUCTION
    if extra_rules:
        full_system += f"\n\nReguli suplimentare de respectat:\n{extra_rules}"
    chat = LlmChat(api_key=os.environ["EMERGENT_LLM_KEY"], session_id=str(uuid.uuid4()), system_message=full_system)
    chat.with_model("openai", "gpt-5.2")
    return chat


def _context_to_text(ctx: dict) -> str:
    """Convert full context dict to readable text for AI prompt."""
    parts = []

    f = ctx.get("firma", {})
    if f.get("denumire"):
        parts.append(f"## Firmă\n- **{f['denumire']}** (CUI: `{f.get('cui')}`, {f.get('forma_juridica')})\n- Adresă: {f.get('adresa')}, {f.get('judet')}\n- Stare: **{f.get('stare')}** {f.get('stare_detalii', '')}\n- CAEN principal: {f.get('caen_principal')}\n- Angajați: {f.get('nr_angajati')}, Capital: {f.get('capital_social')}\n- Înființare: {f.get('data_infiintare')}")
        fin = f.get("date_financiare")
        if fin:
            parts.append(f"- Date financiare: CA={fin.get('cifra_afaceri')}, Profit={fin.get('profit_net')}, Obligații restante={fin.get('obligatii_restante', 0)}")

    p = ctx.get("program", {})
    if p.get("program"):
        parts.append(f"\n## Program\n- **{p['program']}** / {p.get('masura')} ({p.get('masura_cod')})\n- Sesiune: **{p.get('sesiune')}**\n- Buget sesiune: {p.get('buget_sesiune')} RON\n- Valoare proiect: {p.get('valoare_min')} – {p.get('valoare_max')} RON\n- Beneficiari: {', '.join(p.get('beneficiari_eligibili', []))}\n- Regiune: {p.get('regiune')}\n- Perioadă: {p.get('data_start')} → {p.get('data_sfarsit')}")

    c = ctx.get("config", {})
    if c.get("titlu"):
        parts.append(f"\n## Proiect\n- Titlu: **{c['titlu']}**\n- Buget estimat: {c.get('buget_estimat')} RON\n- Tip: {c.get('tip_proiect')}\n- Locație: {c.get('locatie')}, {c.get('judet_implementare')}\n- Temă: {c.get('tema')}\n- Status: **{c.get('status_label')}**")

    g = ctx.get("ghid", {})
    if g.get("criterii_eligibilitate"):
        parts.append(f"\n## Criterii eligibilitate (din ghid)\n" + "\n".join(f"- {c}" for c in g["criterii_eligibilitate"]))
    if g.get("grila_conformitate"):
        parts.append(f"\n## Grilă conformitate (din ghid)\n" + "\n".join(f"- {c.get('criteriu', c) if isinstance(c, dict) else c}: {c.get('punctaj_max', '') if isinstance(c, dict) else ''}" for c in g["grila_conformitate"]))
    if g.get("activitati_eligibile"):
        parts.append(f"\n## Activități eligibile\n" + "\n".join(f"- {a}" for a in g["activitati_eligibile"]))
    if g.get("cheltuieli_eligibile"):
        parts.append(f"\n## Cheltuieli eligibile\n" + "\n".join(f"- {c}" for c in g["cheltuieli_eligibile"]))
    if g.get("rezumat_ghid"):
        parts.append(f"\n## Rezumat ghid\n{g['rezumat_ghid']}")
    if g.get("date_din_linkuri"):
        parts.append(f"\n## Date extrase din linkuri\n{g['date_din_linkuri'][:800]}")

    d = ctx.get("documente", {})
    if d:
        parts.append(f"\n## Stare documente\n- Cerute: {d.get('total_cerute')}, Încărcate: {d.get('total_incarcate')}, Lipsă: {d.get('total_lipsa')}\n- Drafturi: {d.get('drafturi_generate')}, Ghiduri: {d.get('ghiduri_incarcate')}\n- Achiziții: {d.get('achizitii_count')} (total: {d.get('achizitii_total')} RON)")

    return "\n".join(parts)


async def check_eligibility(firm_data: dict, program_info: dict, full_context: dict = None, extra_rules: str = "") -> dict:
    chat = _get_chat(
        "Ești expert în finanțări europene și naționale din România. "
        "Analizezi eligibilitatea firmei pe baza TUTUROR datelor disponibile: date firmă, program, criterii din ghid, grila de conformitate. "
        "Oferă raport structurat: Rezumat, Scor, Criterii îndeplinite/neîndeplinite, Blocaje, Recomandări.",
        extra_rules
    )
    if full_context:
        prompt = f"Analizează eligibilitatea pe baza întregului context al proiectului:\n\n{_context_to_text(full_context)}"
    else:
        prompt = f"Date firmă: {json.dumps(firm_data, ensure_ascii=False, default=str)}\n\nProgram: {json.dumps(program_info, ensure_ascii=False, default=str)}"
    prompt += "\n\nOferă un raport detaliat de eligibilitate."
    try:
        response = await chat.send_message(UserMessage(text=prompt))
        return {"success": True, "result": response}
    except Exception as e:
        logger.error(f"AI eligibility failed: {e}")
        return {"success": False, "error": str(e)}


async def generate_document_section(template: str, data: dict, section: str, full_context: dict = None, extra_rules: str = "") -> dict:
    chat = _get_chat(
        "Ești expert în redactarea documentelor pentru proiecte de finanțare în România. "
        "Completezi secțiunile pe baza TUTUROR datelor disponibile din proiect. "
        "NU inventa date. Scrie formal, profesional.",
        extra_rules
    )
    if full_context:
        prompt = f"Context complet proiect:\n{_context_to_text(full_context)}\n\nCompletează: **{section}**\nTemplate: {template}"
    else:
        prompt = f"Template: {template}\nDate: {json.dumps(data, ensure_ascii=False, default=str)}\nCompletează secțiunea: {section}"
    try:
        response = await chat.send_message(UserMessage(text=prompt))
        return {"success": True, "result": response}
    except Exception as e:
        logger.error(f"AI doc generation failed: {e}")
        return {"success": False, "error": str(e)}


async def validate_coherence(documents: list, project_data: dict, full_context: dict = None, extra_rules: str = "") -> dict:
    chat = _get_chat(
        "Ești validator de coerență pentru dosare de finanțare. "
        "Verifici consistența între TOATE datele proiectului: documente, buget, achiziții, criterii ghid, grilă conformitate. "
        "Structurează: Rezumat, Verificări, Probleme, Recomandări.",
        extra_rules
    )
    if full_context:
        prompt = f"Validează coerența dosarului pe baza contextului complet:\n\n{_context_to_text(full_context)}"
    else:
        prompt = f"Documente: {json.dumps(documents, ensure_ascii=False, default=str)}\nProiect: {json.dumps(project_data, ensure_ascii=False, default=str)}"
    prompt += "\n\nIdentifică inconsistențe și oferă recomandări."
    try:
        response = await chat.send_message(UserMessage(text=prompt))
        return {"success": True, "result": response}
    except Exception as e:
        logger.error(f"AI validation failed: {e}")
        return {"success": False, "error": str(e)}


async def chat_navigator(message: str, context: dict, full_context: dict = None, extra_rules: str = "") -> dict:
    chat = _get_chat(
        "Ești Ghidul GrantFlow. Ajuți utilizatorii să navigheze procesul de finanțare. "
        "Ai acces la TOATE datele proiectului. Răspunde concis, structurat.",
        extra_rules
    )
    if full_context:
        prompt = f"Context proiect:\n{_context_to_text(full_context)}\n\nÎntrebare: {message}"
    else:
        prompt = f"Context: {json.dumps(context, ensure_ascii=False, default=str)}\n\nÎntrebare: {message}"
    try:
        response = await chat.send_message(UserMessage(text=prompt))
        return {"success": True, "result": response}
    except Exception as e:
        logger.error(f"AI navigator failed: {e}")
        return {"success": False, "error": str(e)}
