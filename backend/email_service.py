import os
import smtplib
import hashlib
import secrets
from email.mime.multipart import MIMEMultipart
from email.mime.text import MIMEText
from email.header import Header
from dotenv import load_dotenv

load_dotenv()

SMTP_HOST = os.getenv("SMTP_HOST", "smtp.gmail.com")
SMTP_PORT = int(os.getenv("SMTP_PORT", "587"))
SMTP_USER = os.getenv("SMTP_USER", "")
SMTP_PASSWORD = os.getenv("SMTP_PASSWORD", "")


def _normalize_text(value: str) -> str:
    if not value:
        return ""
    # Remove non-breaking spaces that often break ascii-only header serialization.
    return value.replace("\u00a0", " ").strip()


def smtp_configured() -> bool:
    return bool(SMTP_USER and SMTP_PASSWORD)


def generate_verification_code() -> str:
    return f"{secrets.randbelow(1000000):06d}"


def hash_verification_code(code: str) -> str:
    return hashlib.sha256(code.encode("utf-8")).hexdigest()


def _send_html_email(to_email: str, subject: str, html_content: str) -> bool:
    smtp_user = _normalize_text(SMTP_USER)
    smtp_password = _normalize_text(SMTP_PASSWORD)
    safe_to_email = _normalize_text(to_email)
    safe_subject = _normalize_text(subject)
    safe_html = _normalize_text(html_content)

    if not (smtp_user and smtp_password):
        print(f"SMTP credentials not configured, skipping email to {to_email}")
        return False

    try:
        msg = MIMEMultipart("alternative")
        msg["From"] = str(Header(smtp_user, "utf-8"))
        msg["To"] = safe_to_email
        msg["Subject"] = str(Header(safe_subject, "utf-8"))
        
        # Properly encode HTML content as UTF-8
        msg.attach(MIMEText(safe_html, "html", _charset="utf-8"))

        with smtplib.SMTP(SMTP_HOST, SMTP_PORT) as server:
            server.starttls()
            server.login(smtp_user, smtp_password)
            server.send_message(msg)

        print(f"Email sent to {safe_to_email}: {safe_subject}")
        return True
    except Exception as e:
        print(f"Failed to send email to {to_email}: {e}")
        return False


def send_verification_code(user_email: str, code: str) -> bool:
    html_content = f"""
    <html>
    <body style="font-family: Arial, sans-serif; background-color: #f4f4f4; padding: 20px;">
        <div style="max-width: 560px; margin: 0 auto; background-color: white; padding: 24px; border-radius: 10px;">
            <h1 style="color: #333; margin-top: 0;">Verify your email</h1>
            <p style="color: #555;">Use the code below to confirm your email address for RSS Sentinel.</p>
            <div style="margin: 24px 0; padding: 18px; text-align: center; background: #f8fafc; border: 1px solid #e5e7eb; border-radius: 8px;">
                <div style="font-size: 32px; letter-spacing: 6px; font-weight: bold; color: #111827;">{code}</div>
            </div>
            <p style="color: #666; margin-bottom: 0;">This code expires in 10 minutes.</p>
        </div>
    </body>
    </html>
    """
    return _send_html_email(user_email, "RSS Sentinel Email Verification Code", html_content)


def send_digest(user_email: str, summary_points: list) -> bool:
    if not summary_points:
        print(f"No summary points to send to {user_email}")
        return False

    html_parts = ["""
    <html>
    <body style="font-family: Arial, sans-serif; background-color: #f4f4f4; padding: 20px;">
        <div style="max-width: 600px; margin: 0 auto; background-color: white; padding: 24px; border-radius: 10px;">
            <h1 style="color: #333; margin-top: 0; font-size: 24px;">Resume IA du jour</h1>
            <p style="color: #666; margin-bottom: 24px;">Your daily AI-powered news summary</p>
    """]

    for point in summary_points[:5]:
        sentiment_color = {"Positive": "#4ade80", "Negative": "#fb7185", "Neutral": "#94a3b8"}.get(point.get("sentiment", "Neutral"), "#94a3b8")
        html_parts.append(f"""
            <div style="margin-bottom: 16px; padding: 14px; border-left: 3px solid {sentiment_color}; background: #f8fafc; border-radius: 6px;">
                <div style="display: flex; align-items: flex-start; gap: 10px;">
                    <div style="color: {sentiment_color}; font-weight: 600; flex-shrink: 0; margin-top: 2px; font-size: 12px;">
                        [{point.get('sentiment', 'Neutral')}]
                    </div>
                    <div>
                        <a href="{point.get('url', '#')}" style="color: #1a73e8; text-decoration: none; font-weight: 500; display: block; margin-bottom: 6px;">
                            {point.get('title', 'Untitled')}
                        </a>
                        <p style="color: #666; font-size: 12px; margin: 0; line-height: 1.4;">{point.get('summary', '')}</p>
                        <p style="color: #999; font-size: 11px; margin: 6px 0 0 0;">{point.get('feed_topic', 'Unknown')}</p>
                    </div>
                </div>
            </div>
        """)

    html_parts.append("""
        </div>
    </body>
    </html>
    """)

    html_content = "".join(html_parts)
    subject = "RSS Sentinel - Resume IA du jour"
    return _send_html_email(user_email, subject, html_content)
