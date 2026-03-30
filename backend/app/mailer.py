import os
import smtplib
from email.message import EmailMessage
from typing import Optional


def _env_bool(name: str, default: str = "0") -> bool:
    return os.getenv(name, default).strip() in ("1", "true", "True", "yes", "YES")


def send_email(
    to_email: str,
    subject: str,
    body_text: str,
    body_html: Optional[str] = None,
) -> None:
    host = os.getenv("SMTP_HOST", "").strip()
    port = int(os.getenv("SMTP_PORT", "587"))
    user = os.getenv("SMTP_USER", "").strip()
    password = os.getenv("SMTP_PASSWORD", "").strip()
    from_addr = os.getenv("SMTP_FROM", user).strip()

    use_tls = _env_bool("SMTP_USE_TLS", "1")
    use_ssl = _env_bool("SMTP_USE_SSL", "0")

    if not host or not user or not password:
        raise RuntimeError("SMTP config missing: SMTP_HOST/SMTP_USER/SMTP_PASSWORD")

    msg = EmailMessage()
    msg["From"] = from_addr
    msg["To"] = to_email
    msg["Subject"] = subject
    msg.set_content(body_text)

    # 可选 HTML
    if body_html:
        msg.add_alternative(body_html, subtype="html")

    if use_ssl:
        with smtplib.SMTP_SSL(host, port, timeout=20) as smtp:
            smtp.login(user, password)
            smtp.send_message(msg)
        return

    with smtplib.SMTP(host, port, timeout=20) as smtp:
        smtp.ehlo()
        if use_tls:
            smtp.starttls()
            smtp.ehlo()
        smtp.login(user, password)
        smtp.send_message(msg)
