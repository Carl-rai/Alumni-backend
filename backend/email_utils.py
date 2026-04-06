import logging
import os
import threading

logger = logging.getLogger(__name__)


def _get_resend_api_key():
    key = os.getenv("RESEND_API_KEY", "").strip()
    if not key:
        raise RuntimeError("RESEND_API_KEY is not configured in environment variables.")
    return key


def _get_from_email():
    # Resend requires a verified domain, use their shared sender
    # but set reply-to as the real Gmail so replies go there
    return "Alumni Management System <onboarding@resend.dev>"


def _get_reply_to():
    return os.getenv("DEFAULT_FROM_EMAIL", "").strip()


def send_system_email(subject, message, recipient):
    import resend
    recipient = (recipient or "").strip()
    if not recipient:
        raise ValueError("Recipient email is required.")
    resend.api_key = _get_resend_api_key()
    resend.Emails.send({
        "from": _get_from_email(),
        "reply_to": [_get_reply_to()],
        "to": [recipient],
        "subject": subject,
        "text": message,
    })
    return True


def send_system_html_email(subject, text_body, html_body, recipient):
    import resend
    recipient = (recipient or "").strip()
    if not recipient:
        raise ValueError("Recipient email is required.")
    resend.api_key = _get_resend_api_key()
    resend.Emails.send({
        "from": _get_from_email(),
        "reply_to": [_get_reply_to()],
        "to": [recipient],
        "subject": subject,
        "text": text_body,
        "html": html_body,
    })
    return True


def send_system_email_async(subject, message, recipient):
    def _send():
        try:
            send_system_email(subject, message, recipient)
        except Exception as e:
            logger.error("Failed to send email to %s: %s", recipient, e)
    threading.Thread(target=_send, daemon=True).start()


def send_system_html_email_async(subject, text_body, html_body, recipient):
    def _send():
        try:
            send_system_html_email(subject, text_body, html_body, recipient)
        except Exception as e:
            logger.error("Failed to send HTML email to %s: %s", recipient, e)
    threading.Thread(target=_send, daemon=True).start()


def smtp_connection_diagnostics(timeout=10):
    api_key = os.getenv("RESEND_API_KEY", "").strip()
    from_email = _get_from_email()
    return {
        "provider": "resend",
        "has_api_key": bool(api_key),
        "from_email": bool(from_email),
        "connect_ok": bool(api_key),
        "auth_ok": bool(api_key),
        "error": None if api_key else "RESEND_API_KEY is not set.",
    }
