import smtplib
import imaplib
import email
import os
import logging
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
from email.mime.base import MIMEBase
from email import encoders
from email.header import decode_header
from datetime import datetime
from typing import List, Dict, Optional
from jinja2 import Environment, FileSystemLoader, select_autoescape

logger = logging.getLogger(__name__)

EMAIL_ADDRESS = os.getenv("EMAIL_ADDRESS", "")
EMAIL_PASSWORD = os.getenv("EMAIL_PASSWORD", "")
SMTP_HOST = os.getenv("SMTP_HOST", "smtp.gmail.com")
SMTP_PORT = int(os.getenv("SMTP_PORT", "587"))
IMAP_HOST = os.getenv("IMAP_HOST", "imap.gmail.com")
IMAP_PORT = int(os.getenv("IMAP_PORT", "993"))
COMPANY_NAME = os.getenv("COMPANY_NAME", "Our Company")
SENDER_NAME = os.getenv("SENDER_NAME", "")
SENDER_TITLE = os.getenv("SENDER_TITLE", "Business Development")
COMPANY_WEBSITE = os.getenv("COMPANY_WEBSITE", "")
COMPANY_PHONE = os.getenv("COMPANY_PHONE", "")

TEMPLATE_DIR = os.path.join(os.path.dirname(__file__), "..", "templates")
jinja_env = Environment(
    loader=FileSystemLoader(TEMPLATE_DIR),
    autoescape=select_autoescape(["html", "xml"]),
)


def render_outreach_email(agency_name: str, contact_person: Optional[str] = None) -> str:
    try:
        template = jinja_env.get_template("outreach_email.html")
        return template.render(
            agency_name=agency_name,
            contact_person=contact_person or "Care Team",
            company_name=COMPANY_NAME,
            sender_name=SENDER_NAME,
            sender_title=SENDER_TITLE,
            company_website=COMPANY_WEBSITE,
            company_phone=COMPANY_PHONE,
        )
    except Exception as e:
        logger.error(f"Template render error: {e}")
        return f"<p>Dear {contact_person or 'Care Team'},</p><p>We would love to connect with {agency_name}.</p>"


def send_email(
    to_address: str,
    subject: str,
    html_body: str,
    attachment_path: Optional[str] = None,
) -> bool:
    """Send an HTML email via SMTP. Returns True on success."""
    if not EMAIL_ADDRESS or not EMAIL_PASSWORD:
        logger.warning("Email credentials not configured")
        return False
    try:
        msg = MIMEMultipart("alternative")
        msg["From"] = f"{SENDER_NAME} <{EMAIL_ADDRESS}>" if SENDER_NAME else EMAIL_ADDRESS
        msg["To"] = to_address
        msg["Subject"] = subject

        msg.attach(MIMEText(html_body, "html"))

        if attachment_path and os.path.exists(attachment_path):
            with open(attachment_path, "rb") as f:
                part = MIMEBase("application", "octet-stream")
                part.set_payload(f.read())
            encoders.encode_base64(part)
            part.add_header(
                "Content-Disposition",
                f"attachment; filename={os.path.basename(attachment_path)}",
            )
            msg.attach(part)

        with smtplib.SMTP(SMTP_HOST, SMTP_PORT) as server:
            server.ehlo()
            server.starttls()
            server.login(EMAIL_ADDRESS, EMAIL_PASSWORD)
            server.sendmail(EMAIL_ADDRESS, to_address, msg.as_string())

        logger.info(f"Email sent to {to_address}")
        return True
    except Exception as e:
        logger.error(f"Failed to send email to {to_address}: {e}")
        return False


def _decode_header_value(value: str) -> str:
    parts = decode_header(value)
    decoded = []
    for part, charset in parts:
        if isinstance(part, bytes):
            decoded.append(part.decode(charset or "utf-8", errors="replace"))
        else:
            decoded.append(part)
    return " ".join(decoded)


def _get_email_body(msg) -> str:
    body = ""
    if msg.is_multipart():
        for part in msg.walk():
            ct = part.get_content_type()
            if ct == "text/html":
                body = part.get_payload(decode=True).decode("utf-8", errors="replace")
                break
            elif ct == "text/plain" and not body:
                body = part.get_payload(decode=True).decode("utf-8", errors="replace")
    else:
        body = msg.get_payload(decode=True).decode("utf-8", errors="replace")
    return body


def fetch_inbox(max_emails: int = 50, mailbox: str = "INBOX") -> List[Dict]:
    """Fetch recent emails from IMAP inbox."""
    if not EMAIL_ADDRESS or not EMAIL_PASSWORD:
        logger.warning("Email credentials not configured")
        return []

    results = []
    try:
        with imaplib.IMAP4_SSL(IMAP_HOST, IMAP_PORT) as mail:
            mail.login(EMAIL_ADDRESS, EMAIL_PASSWORD)
            mail.select(mailbox)

            _, data = mail.search(None, "ALL")
            ids = data[0].split()
            recent_ids = ids[-max_emails:] if len(ids) > max_emails else ids

            for msg_id in reversed(recent_ids):
                _, msg_data = mail.fetch(msg_id, "(RFC822)")
                raw = msg_data[0][1]
                msg = email.message_from_bytes(raw)

                subject = _decode_header_value(msg.get("Subject", "(no subject)"))
                from_addr = _decode_header_value(msg.get("From", ""))
                date_str = msg.get("Date", "")
                message_id = msg.get("Message-ID", str(msg_id.decode()))
                body = _get_email_body(msg)

                try:
                    parsed_date = email.utils.parsedate_to_datetime(date_str)
                except Exception:
                    parsed_date = datetime.utcnow()

                results.append({
                    "message_id": message_id,
                    "email_from": from_addr,
                    "subject": subject,
                    "message": body,
                    "date": parsed_date.isoformat(),
                    "direction": "received",
                })

        return results
    except Exception as e:
        logger.error(f"IMAP fetch error: {e}")
        return []
