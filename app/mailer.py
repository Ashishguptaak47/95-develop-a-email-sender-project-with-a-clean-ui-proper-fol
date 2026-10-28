import os
import re
import smtplib
from email.mime.multipart import MIMEMultipart
from email.mime.text import MIMEText
from email.mime.base import MIMEBase
from email import encoders
from typing import Dict, Any, List, Optional, Tuple

def render_template(template_str: str, context: Dict[str, Any]) -> str:
    result = template_str
    for key, val in context.items():
        result = re.sub(rf"\{{\{{\s*{re.escape(key)}\s*\}}\}}", str(val), result)
    return result

def build_email_message(
    sender_name: str,
    sender_email: str,
    recipient: str,
    subject: str,
    body_text: str,
    body_html: Optional[str] = None,
    attachments: Optional[List[Tuple[str, bytes]]] = None
) -> MIMEMultipart:
    msg = MIMEMultipart("mixed")
    msg["From"] = f"{sender_name} <{sender_email}>" if sender_name else sender_email
    msg["To"] = recipient
    msg["Subject"] = subject

    alt_container = MIMEMultipart("alternative")
    alt_container.attach(MIMEText(body_text, "plain", "utf-8"))
    if body_html:
        alt_container.attach(MIMEText(body_html, "html", "utf-8"))
    msg.attach(alt_container)

    if attachments:
        for filename, data in attachments:
            part = MIMEBase("application", "octet-stream")
            part.set_payload(data)
            encoders.encode_base64(part)
            part.add_header("Content-Disposition", f'attachment; filename="{os.path.basename(filename)}"')
            msg.attach(part)

    return msg

def send_smtp_mail(
    settings: Dict[str, Any],
    recipient: str,
    subject: str,
    body_text: str,
    body_html: Optional[str] = None,
    attachments: Optional[List[Tuple[str, bytes]]] = None
) -> Tuple[bool, Optional[str]]:
    if not recipient or not re.match(r"^[^@\s]+@[^@\s]+\.[^@\s]+$", recipient.strip()):
        return False, f"Invalid email address: {recipient}"

    is_dry_run = bool(settings.get("dry_run", 1))
    if is_dry_run:
        return True, "Sent successfully (Simulated Dry-Run Mode)"

    host = settings.get("host", "localhost")
    port = int(settings.get("port", 587))
    username = settings.get("username", "")
    password = settings.get("password", "")
    use_tls = bool(settings.get("use_tls", 0))
    use_ssl = bool(settings.get("use_ssl", 0))

    msg = build_email_message(
        sender_name=settings.get("sender_name", ""),
        sender_email=settings.get("sender_email", "noreply@example.com"),
        recipient=recipient.strip(),
        subject=subject,
        body_text=body_text,
        body_html=body_html,
        attachments=attachments
    )

    try:
        if use_ssl:
            server = smtplib.SMTP_SSL(host, port, timeout=12)
        else:
            server = smtplib.SMTP(host, port, timeout=12)
            if use_tls:
                server.starttls()

        if username and password:
            server.login(username, password)

        server.sendmail(settings.get("sender_email", "noreply@example.com"), [recipient.strip()], msg.as_string())
        server.quit()
        return True, None
    except Exception as exc:
        return False, str(exc)
