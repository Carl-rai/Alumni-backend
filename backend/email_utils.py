import logging
import os
import threading

logger = logging.getLogger(__name__)


def _get_sendgrid_api_key():
    key = os.getenv("SENDGRID_API_KEY", "").strip()
    if not key:
        raise RuntimeError("SENDGRID_API_KEY is not configured in environment variables.")
    return key


def _get_from_email():
    return os.getenv("DEFAULT_FROM_EMAIL", "").strip()


def send_system_email(subject, message, recipient):
    from sendgrid import SendGridAPIClient
    from sendgrid.helpers.mail import Mail
    recipient = (recipient or "").strip()
    if not recipient:
        raise ValueError("Recipient email is required.")
    mail = Mail(
        from_email=_get_from_email(),
        to_emails=recipient,
        subject=subject,
        plain_text_content=message,
    )
    sg = SendGridAPIClient(_get_sendgrid_api_key())
    sg.send(mail)
    return True


def send_system_html_email(subject, text_body, html_body, recipient):
    from sendgrid import SendGridAPIClient
    from sendgrid.helpers.mail import Mail
    recipient = (recipient or "").strip()
    if not recipient:
        raise ValueError("Recipient email is required.")
    mail = Mail(
        from_email=_get_from_email(),
        to_emails=recipient,
        subject=subject,
        plain_text_content=text_body,
        html_content=html_body,
    )
    sg = SendGridAPIClient(_get_sendgrid_api_key())
    sg.send(mail)
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
    api_key = os.getenv("SENDGRID_API_KEY", "").strip()
    from_email = _get_from_email()

    result = {
        "provider": "sendgrid",
        "has_api_key": bool(api_key),
        "from_email": from_email,
        "connect_ok": bool(api_key),
        "auth_ok": bool(api_key),
        "error": None if api_key else "SENDGRID_API_KEY is not set.",
    }

    if api_key and from_email:
        try:
            from sendgrid import SendGridAPIClient
            from sendgrid.helpers.mail import Mail
            mail = Mail(
                from_email=from_email,
                to_emails=from_email,
                subject="Alumni System - Email Test",
                plain_text_content="This is a test email from your Alumni System.",
            )
            sg = SendGridAPIClient(api_key)
            response = sg.send(mail)
            result["test_email_status"] = response.status_code
        except Exception as e:
            result["auth_ok"] = False
            result["connect_ok"] = False
            result["error"] = str(e)

    return result
