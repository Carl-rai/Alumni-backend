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
