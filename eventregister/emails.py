from django.conf import settings
from backend.email_utils import send_system_html_email_async

def send_registration_confirmation_email(registration):
    event = registration.event
    user = registration.user

    subject = f'Event Registration Confirmed - {event.title}'

    start = event.start_time.strftime('%I:%M %p')
    end = event.end_time.strftime('%I:%M %p')
    date_str = event.date.strftime('%B %d, %Y') if hasattr(event.date, 'strftime') else str(event.date)
    remarks_line = f'Your Remarks   : {registration.remarks}' if registration.remarks else ''
    venue_line = f'  Venue          : {event.venue}' if event.venue else ''

    plain_message = f"""Dear {user.first_name} {user.last_name},

Your registration has been confirmed! Here are your event details:

  Event          : {event.title}
  Date           : {date_str}
  Time           : {start} - {end}
  Location       : {event.location}
{venue_line}
  Guests         : {registration.guest_count}
{remarks_line}

Description:
{event.description}

We look forward to seeing you at the event!

Best regards,
Alumni Management Team
{settings.DEFAULT_FROM_EMAIL}
"""

    html_message = f"""
<!DOCTYPE html>
<html>
<body style="margin:0;padding:0;background:#f0f4f8;font-family:Arial,sans-serif;">
  <table width="100%" cellpadding="0" cellspacing="0" style="background:#f0f4f8;padding:40px 0;">
    <tr><td align="center">
      <table width="600" cellpadding="0" cellspacing="0" style="background:#ffffff;border-radius:12px;overflow:hidden;box-shadow:0 4px 20px rgba(0,0,0,0.1);">

        <!-- Header -->
        <tr>
          <td style="background:linear-gradient(135deg,#1e3a5f,#2563eb);padding:36px 40px;text-align:center;">
            <h1 style="margin:0;color:#facc15;font-size:26px;letter-spacing:1px;">Alumni Management System</h1>
            <p style="margin:8px 0 0;color:#bfdbfe;font-size:14px;">Event Registration Confirmation</p>
          </td>
        </tr>

        <!-- Greeting -->
        <tr>
          <td style="padding:32px 40px 0;">
            <p style="margin:0;font-size:16px;color:#1e293b;">Dear <strong>{user.first_name} {user.last_name}</strong>,</p>
            <p style="margin:12px 0 0;font-size:15px;color:#475569;">Your registration has been <strong style="color:#16a34a;">confirmed</strong>! Here are your event details:</p>
          </td>
        </tr>

        <!-- Event Card -->
        <tr>
          <td style="padding:24px 40px;">
            <table width="100%" cellpadding="0" cellspacing="0" style="background:#f8fafc;border:1px solid #e2e8f0;border-radius:10px;overflow:hidden;">
              <tr>
                <td style="background:#1e3a5f;padding:14px 20px;">
                  <h2 style="margin:0;color:#facc15;font-size:18px;">{event.title}</h2>
                </td>
              </tr>
              <tr>
                <td style="padding:20px;">
                  <table width="100%" cellpadding="6" cellspacing="0">
                    <tr>
                      <td style="color:#64748b;font-size:13px;width:120px;">&#128197; Date</td>
                      <td style="color:#1e293b;font-size:14px;font-weight:600;">{date_str}</td>
                    </tr>
                    <tr>
                      <td style="color:#64748b;font-size:13px;">&#9200; Time</td>
                      <td style="color:#1e293b;font-size:14px;font-weight:600;">{start} &ndash; {end}</td>
                    </tr>
                    <tr>
                      <td style="color:#64748b;font-size:13px;">&#128205; Location</td>
                      <td style="color:#1e293b;font-size:14px;font-weight:600;">{event.location}</td>
                    </tr>
                    {f'<tr><td style="color:#64748b;font-size:13px;">&#127968; Venue</td><td style="color:#1e293b;font-size:14px;font-weight:600;">{event.venue}</td></tr>' if event.venue else ''}
                    <tr>
                      <td style="color:#64748b;font-size:13px;">&#128101; Guests</td>
                      <td style="color:#1e293b;font-size:14px;font-weight:600;">{registration.guest_count}</td>
                    </tr>
                    {f'<tr><td style="color:#64748b;font-size:13px;">&#128172; Remarks</td><td style="color:#1e293b;font-size:14px;">{registration.remarks}</td></tr>' if registration.remarks else ''}
                  </table>
                </td>
              </tr>
            </table>
          </td>
        </tr>

        <!-- Description -->
        <tr>
          <td style="padding:0 40px 24px;">
            <p style="margin:0 0 6px;font-size:13px;color:#64748b;font-weight:600;text-transform:uppercase;letter-spacing:0.5px;">About this Event</p>
            <p style="margin:0;font-size:14px;color:#475569;line-height:1.6;">{event.description}</p>
          </td>
        </tr>

        <!-- Footer -->
        <tr>
          <td style="background:#1e3a5f;padding:24px 40px;text-align:center;">
            <p style="margin:0;color:#bfdbfe;font-size:13px;">We look forward to seeing you at the event!</p>
            <p style="margin:8px 0 0;color:#facc15;font-size:13px;font-weight:600;">Alumni Management Team</p>
            <p style="margin:4px 0 0;color:#93c5fd;font-size:12px;">{settings.DEFAULT_FROM_EMAIL}</p>
          </td>
        </tr>

      </table>
    </td></tr>
  </table>
</body>
</html>
"""

    try:
        send_system_html_email_async(
            subject=subject,
            text_body=plain_message,
            html_body=html_message,
            recipient=user.email,
        )
        return True
    except Exception as e:
        print(f"Failed to send registration email: {e}")
        return False
