import logging
import socket
from concurrent.futures import ThreadPoolExecutor

from django.conf import settings
from django.core.mail import EmailMultiAlternatives, get_connection, send_mail

logger = logging.getLogger(__name__)
_email_executor = ThreadPoolExecutor(
    max_workers=max(1, int(getattr(settings, "EMAIL_ASYNC_MAX_WORKERS", 2)))
)


def ensure_email_configured():
    if not settings.EMAIL_HOST_USER or not settings.EMAIL_HOST_PASSWORD:
        raise RuntimeError(
            "Email service is not configured. Set EMAIL_HOST_USER and EMAIL_HOST_PASSWORD in the deployment environment."
        )


def _queue_email_task(email_type, recipient, send_func, *args, **kwargs):
    recipient = (recipient or "").strip()
    if not recipient:
        raise ValueError("Recipient email is required.")

    ensure_email_configured()

    def _send():
        try:
            send_func(*args, **kwargs)
        except Exception:
            logger.exception("Failed to send %s email to %s", email_type, recipient)

    _email_executor.submit(_send)
    return True


def send_system_email(subject, message, recipient):
    recipient = (recipient or "").strip()
    if not recipient:
        raise ValueError("Recipient email is required.")

    ensure_email_configured()

    return send_mail(
        subject=subject,
        message=message,
        from_email=settings.DEFAULT_FROM_EMAIL or settings.EMAIL_HOST_USER,
        recipient_list=[recipient],
        fail_silently=False,
    )


def send_system_html_email(subject, text_body, html_body, recipient):
    recipient = (recipient or "").strip()
    if not recipient:
        raise ValueError("Recipient email is required.")

    ensure_email_configured()

    email = EmailMultiAlternatives(
        subject=subject,
        body=text_body,
        from_email=settings.DEFAULT_FROM_EMAIL or settings.EMAIL_HOST_USER,
        to=[recipient],
    )
    email.attach_alternative(html_body, "text/html")
    email.send(fail_silently=False)
    return True


def send_system_email_async(subject, message, recipient):
    """Queue plain-text email so the request can return immediately."""
    return _queue_email_task(
        "plain-text",
        recipient,
        send_system_email,
        subject,
        message,
        recipient,
    )


def send_system_html_email_async(subject, text_body, html_body, recipient):
    """Queue HTML email so the request can return immediately."""
    return _queue_email_task(
        "html",
        recipient,
        send_system_html_email,
        subject,
        text_body,
        html_body,
        recipient,
    )


def smtp_connection_diagnostics(timeout=10):
    host = (settings.EMAIL_HOST or "").strip()
    port = int(settings.EMAIL_PORT or 0)

    result = {
        "email_backend": settings.EMAIL_BACKEND,
        "host": host,
        "port": port,
        "use_tls": bool(getattr(settings, "EMAIL_USE_TLS", False)),
        "has_host_user": bool((settings.EMAIL_HOST_USER or "").strip()),
        "has_host_password": bool((settings.EMAIL_HOST_PASSWORD or "").strip()),
        "default_from_email": bool((settings.DEFAULT_FROM_EMAIL or "").strip()),
        "timeout": timeout,
        "connect_ok": False,
        "auth_ok": False,
        "error_stage": None,
        "error": None,
    }

    if not host or not port:
        result["error"] = "EMAIL_HOST or EMAIL_PORT is not configured."
        return result

    try:
        with socket.create_connection((host, port), timeout=timeout):
            result["connect_ok"] = True
    except Exception as exc:
        result["error_stage"] = "connect"
        result["error"] = str(exc)
        return result

    try:
        connection = get_connection(
            fail_silently=False,
            timeout=timeout,
        )
        connection.open()
        result["auth_ok"] = True
        connection.close()
    except Exception as exc:
        result["error_stage"] = "auth"
        result["error"] = str(exc)

    return result
