import os
import smtplib
from email.mime.multipart import MIMEMultipart
from email.mime.text import MIMEText
from dotenv import load_dotenv

load_dotenv()

SMTP_HOST = os.getenv("SMTP_HOST", "smtp.gmail.com")
SMTP_PORT = int(os.getenv("SMTP_PORT", "587"))
SMTP_USER = os.getenv("SMTP_USER", "")
SMTP_PASSWORD = os.getenv("SMTP_PASSWORD", "")

def send_digest(user_email: str, articles: list):
    """Send email digest of articles to user"""
    if not SMTP_USER or not SMTP_PASSWORD:
        print(f"SMTP credentials not configured, skipping email to {user_email}")
        return

    if not articles:
        print(f"No articles to send to {user_email}")
        return

    try:
        # Create message
        msg = MIMEMultipart("alternative")
        msg["From"] = SMTP_USER
        msg["To"] = user_email
        msg["Subject"] = f"RSS Sentinel Digest - {len(articles)} new articles"

        # Build HTML content
        html_parts = ["""
        <html>
        <body style="font-family: Arial, sans-serif; background-color: #f4f4f4; padding: 20px;">
            <div style="max-width: 600px; margin: 0 auto; background-color: white; padding: 20px; border-radius: 8px;">
                <h1 style="color: #333;">RSS Sentinel Digest</h1>
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
        msg.attach(MIMEText(html_content, "html"))

        # Send email
        with smtplib.SMTP(SMTP_HOST, SMTP_PORT) as server:
            server.starttls()
            server.login(SMTP_USER, SMTP_PASSWORD)
            server.send_message(msg)

        print(f"Email digest sent to {user_email} with {len(articles)} articles")

    except Exception as e:
        print(f"Failed to send email to {user_email}: {e}")
