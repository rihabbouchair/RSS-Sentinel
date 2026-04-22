import os
import smtplib
import hashlib
import secrets
from email.mime.multipart import MIMEMultipart
from email.mime.text import MIMEText
from dotenv import load_dotenv

load_dotenv()

SMTP_HOST = os.getenv("SMTP_HOST", "smtp.gmail.com")
SMTP_PORT = int(os.getenv("SMTP_PORT", "587"))
SMTP_USER = os.getenv("SMTP_USER", "")
SMTP_PASSWORD = os.getenv("SMTP_PASSWORD", "")


def smtp_configured() -> bool:
    return bool(SMTP_USER and SMTP_PASSWORD)


def generate_verification_code() -> str:
    return f"{secrets.randbelow(1000000):06d}"


def hash_verification_code(code: str) -> str:
    return hashlib.sha256(code.encode("utf-8")).hexdigest()


def _send_html_email(to_email: str, subject: str, html_content: str) -> bool:
    if not smtp_configured():
        print(f"SMTP credentials not configured, skipping email to {to_email}")
        return False

    try:
        msg = MIMEMultipart("alternative")
        msg["From"] = SMTP_USER
        msg["To"] = to_email
        msg["Subject"] = subject
        msg.attach(MIMEText(html_content, "html"))

        with smtplib.SMTP(SMTP_HOST, SMTP_PORT) as server:
            server.starttls()
            server.login(SMTP_USER, SMTP_PASSWORD)
            server.send_message(msg)

        print(f"Email sent to {to_email}: {subject}")
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


def send_digest(user_email: str, articles: list) -> bool:
    if not articles:
        print(f"No articles to send to {user_email}")
        return False

    html_parts = ["""
    <html>
    <body style="font-family: Arial, sans-serif; background-color: #f4f4f4; padding: 20px;">
        <div style="max-width: 600px; margin: 0 auto; background-color: white; padding: 20px; border-radius: 8px;">
            <h1 style="color: #333;">RSS Sentinel Daily Digest</h1>
            <p style="color: #666;">Here are your latest articles:</p>
    """]

    for article in articles:
        html_parts.append(f"""
            <div style="margin-bottom: 20px; padding-bottom: 20px; border-bottom: 1px solid #eee;">
                <h3 style="margin: 0 0 10px 0;">
                    <a href="{article.get('url', '#')}" style="color: #1a73e8; text-decoration: none;">
                        {article.get('title', 'Untitled')}
                    </a>
                </h3>
                <p style="color: #666; margin: 0 0 10px 0;">{article.get('summary', '')}</p>
                <p style="color: #999; font-size: 12px; margin: 0;">
                    <strong>Category:</strong> {article.get('category', 'Unknown')} |
                    <strong>Topic:</strong> {article.get('topic', 'Unknown')} |
                    <strong>Sentiment:</strong> {article.get('sentiment', 'Unknown')}
                </p>
            </div>
        """)

    html_parts.append("""
        </div>
    </body>
    </html>
    """)

    html_content = "".join(html_parts)
    subject = f"RSS Sentinel Daily Digest - {len(articles)} articles"
    return _send_html_email(user_email, subject, html_content)
