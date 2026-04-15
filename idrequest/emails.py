import threading

from django.conf import settings
from django.core.mail import EmailMultiAlternatives


def _get_from_email():
    return settings.DEFAULT_FROM_EMAIL or settings.EMAIL_HOST_USER


def _full_name(user):
    middle = f" {user.middle_name}" if getattr(user, "middle_name", None) else ""
    return f"{user.first_name}{middle} {user.last_name}".strip()


def build_id_request_export_email(id_request):
    user = id_request.user
    full_name = _full_name(user)
    subject = "ID Request Processed - SCSIT Alumni"

    text_body = f"""Dear {full_name},

Your alumni ID request has been processed by the SCSIT Alumni ID staff.
Your request has been exported and is now being prepared for printing.

Request details:
Alumni ID: {user.alumni_id or "N/A"}
Name: {full_name}
Email: {user.email}
Requested at: {id_request.created_at.strftime("%B %d, %Y %I:%M %p")}

We will email you again once your ID is ready to claim.

Best regards,
SCSIT Alumni
{settings.DEFAULT_FROM_EMAIL}
"""

    return {"subject": subject, "recipient": user.email, "text_body": text_body}


def build_id_request_ready_email(id_request):
    user = id_request.user
    full_name = _full_name(user)
    subject = "Your Alumni ID Is Ready to Claim - SCSIT Alumni"

    text_body = f"""Dear {full_name},

Good news. Your alumni ID is now ready to claim at SCSIT Alumni.

Request details:
Alumni ID: {user.alumni_id or "N/A"}
Name: {full_name}
Email: {user.email}
Course: {user.course or "N/A"}
Year Graduated: {user.year_graduate or "N/A"}
Request Note: {id_request.note or "N/A"}
Status: Ready to Claim

Please bring any valid identification required by the office when you visit.

Best regards,
SCSIT Alumni
{settings.DEFAULT_FROM_EMAIL}
"""

    return {"subject": subject, "recipient": user.email, "text_body": text_body}


def _send_email(subject, recipient, text_body):
    recipient = (recipient or "").strip()
    if not recipient:
        raise ValueError("Recipient email is required.")

    message = EmailMultiAlternatives(
        subject=subject,
        body=text_body,
        from_email=_get_from_email(),
        to=[recipient],
    )
    message.send(fail_silently=False)


def _send_email_async(subject, recipient, text_body):
    def _send():
        try:
            _send_email(subject, recipient, text_body)
        except Exception:
            # Let the request continue; the API response can still succeed
            # even if SMTP is temporarily unavailable.
            pass

    threading.Thread(target=_send, daemon=True).start()


def send_id_request_export_email(id_request):
    email_data = build_id_request_export_email(id_request)
    _send_email_async(email_data["subject"], email_data["recipient"], email_data["text_body"])
    return {
        "email_delivery_mode": "backend",
        "email_payload": {
            "to": email_data["recipient"],
            "subject": email_data["subject"],
            "text": email_data["text_body"],
        },
        "email_sent_by_backend": True,
    }


def send_id_request_ready_email(id_request):
    email_data = build_id_request_ready_email(id_request)
    _send_email_async(email_data["subject"], email_data["recipient"], email_data["text_body"])
    return {
        "email_delivery_mode": "backend",
        "email_payload": {
            "to": email_data["recipient"],
            "subject": email_data["subject"],
            "text": email_data["text_body"],
        },
        "email_sent_by_backend": True,
    }
