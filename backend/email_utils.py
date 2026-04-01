import socket

from django.conf import settings
from django.core.mail import EmailMultiAlternatives, send_mail


def ensure_email_configured():
    if not settings.EMAIL_HOST_USER or not settings.EMAIL_HOST_PASSWORD:
        raise RuntimeError(
            "Email service is not configured. Set EMAIL_HOST_USER and EMAIL_HOST_PASSWORD in the deployment environment."
        )


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
        "connect_ok": False,
        "error": None,
    }

    if not host or not port:
        result["error"] = "EMAIL_HOST or EMAIL_PORT is not configured."
        return result

    try:
        with socket.create_connection((host, port), timeout=timeout):
            result["connect_ok"] = True
    except Exception as exc:
        result["error"] = str(exc)

    return result
