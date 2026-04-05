import smtplib
from email.message import EmailMessage

from app.config.settings import settings


EMAIL_CONFIG = {
    "host": settings.smtp_host,
    "port": settings.smtp_port,
    "username": settings.smtp_username,
    "password": settings.smtp_password,
    "from_email": settings.smtp_from_email,
    "from_name": settings.smtp_from_name,
}


def send_email(recipient: str, subject: str, body: str) -> bool:
    if not settings.smtp_username or not settings.smtp_password:
        return False

    message = EmailMessage()
    message["Subject"] = subject
    message["From"] = f"{settings.smtp_from_name} <{settings.smtp_from_email}>"
    message["To"] = recipient
    message.set_content(body)

    with smtplib.SMTP(settings.smtp_host, settings.smtp_port) as smtp:
        smtp.starttls()
        smtp.login(settings.smtp_username, settings.smtp_password)
        smtp.send_message(message)

    return True


def send_verification_email(recipient: str, recipient_name: str, verification_token: str) -> bool:
    verification_link = f"{settings.frontend_url}/verify-email?token={verification_token}"
    email_body = (
        f"Hello {recipient_name},\n\n"
        f"Please verify your email by visiting this link:\n{verification_link}\n\n"
        f"If you did not sign up for the Complaint Management System, you can ignore this email.\n"
    )
    return send_email(recipient, "Verify your email address", email_body)


def send_complaint_resolved_email(recipient: str, recipient_name: str, complaint_title: str, complaint_id_str: str) -> bool:
    email_body = (
        f"Hello {recipient_name},\n\n"
        f"Your complaint, '{complaint_title}' (ID: {complaint_id_str}), has been marked as resolved.\n\n"
        f"You can log in to the portal to view the resolution details.\n\n"
        f"Thank you,\n"
        f"The {settings.smtp_from_name} Team"
    )
    return send_email(recipient, f"Update on your complaint: {complaint_id_str}", email_body)
