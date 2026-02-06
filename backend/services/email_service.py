"""Email Service - Sends transactional emails via Resend"""
import os
import asyncio
import logging
import resend

logger = logging.getLogger(__name__)

resend.api_key = os.environ.get("RESEND_API_KEY", "")
SENDER_EMAIL = os.environ.get("SENDER_EMAIL", "onboarding@resend.dev")
APP_NAME = "GrantFlow"


def _base_template(content: str) -> str:
    return f"""
    <div style="font-family: 'Helvetica Neue', Arial, sans-serif; max-width: 560px; margin: 0 auto; padding: 32px 24px; background: #ffffff; color: #1a1a1a;">
      <div style="text-align: center; margin-bottom: 32px;">
        <div style="display: inline-block; background: #2563eb; color: white; font-weight: 700; font-size: 18px; padding: 8px 16px; border-radius: 8px; letter-spacing: -0.5px;">
          {APP_NAME}
        </div>
      </div>
      {content}
      <div style="margin-top: 40px; padding-top: 20px; border-top: 1px solid #e5e7eb; text-align: center; font-size: 12px; color: #9ca3af;">
        &copy; 2026 {APP_NAME}. Toate drepturile rezervate.
      </div>
    </div>
    """


async def send_verification_email(to_email: str, token: str, user_name: str) -> dict:
    verification_url = f"#/verify-email?token={token}"
    html = _base_template(f"""
      <h2 style="font-size: 22px; font-weight: 600; margin: 0 0 8px;">Bun venit, {user_name}!</h2>
      <p style="color: #6b7280; font-size: 15px; line-height: 1.6; margin: 0 0 24px;">
        Contul tău a fost creat cu succes. Te rugăm să verifici adresa de email pentru a activa complet contul.
      </p>
      <p style="font-size: 14px; color: #6b7280; margin: 0 0 12px;">Codul tău de verificare:</p>
      <div style="background: #f3f4f6; border: 1px solid #e5e7eb; border-radius: 8px; padding: 16px; text-align: center; margin-bottom: 24px;">
        <code style="font-size: 16px; font-weight: 600; color: #2563eb; letter-spacing: 1px; word-break: break-all;">{token}</code>
      </div>
      <p style="font-size: 13px; color: #9ca3af; margin: 0;">Acest cod expiră în 24 de ore.</p>
    """)

    return await _send(to_email, f"{APP_NAME} - Verificare email", html)


async def send_password_reset_email(to_email: str, token: str, user_name: str) -> dict:
    html = _base_template(f"""
      <h2 style="font-size: 22px; font-weight: 600; margin: 0 0 8px;">Resetare parolă</h2>
      <p style="color: #6b7280; font-size: 15px; line-height: 1.6; margin: 0 0 24px;">
        Salut {user_name}, am primit o cerere de resetare a parolei pentru contul tău.
      </p>
      <p style="font-size: 14px; color: #6b7280; margin: 0 0 12px;">Codul tău de resetare:</p>
      <div style="background: #fef3c7; border: 1px solid #fde68a; border-radius: 8px; padding: 16px; text-align: center; margin-bottom: 24px;">
        <code style="font-size: 16px; font-weight: 600; color: #92400e; letter-spacing: 1px; word-break: break-all;">{token}</code>
      </div>
      <p style="font-size: 13px; color: #9ca3af; margin: 0 0 4px;">Acest cod expiră într-o oră.</p>
      <p style="font-size: 13px; color: #9ca3af; margin: 0;">Dacă nu ai solicitat resetarea, ignoră acest email.</p>
    """)

    return await _send(to_email, f"{APP_NAME} - Resetare parolă", html)


async def _send(to_email: str, subject: str, html: str) -> dict:
    if not resend.api_key:
        logger.warning("RESEND_API_KEY not set, skipping email send")
        return {"success": False, "error": "Email service not configured"}

    params = {
        "from": f"{APP_NAME} <{SENDER_EMAIL}>",
        "to": [to_email],
        "subject": subject,
        "html": html
    }

    try:
        result = await asyncio.to_thread(resend.Emails.send, params)
        logger.info(f"Email sent to {to_email}: {result}")
        return {"success": True, "email_id": result.get("id") if isinstance(result, dict) else str(result)}
    except Exception as e:
        logger.error(f"Failed to send email to {to_email}: {e}")
        return {"success": False, "error": str(e)}
