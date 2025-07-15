import os
import smtplib
from email.mime.text import MIMEText


def send_email(subject, body):
    """Send alert email via SMTP."""
    host = os.getenv("SMTP_HOST")
    port = int(os.getenv("SMTP_PORT", 587))
    user = os.getenv("EMAIL_USER")
    pwd = os.getenv("EMAIL_PASS")
    recipient = os.getenv("EMAIL_TO")

    msg = MIMEText(body)
    msg["Subject"] = subject
    msg["From"] = user
    msg["To"] = recipient

    with smtplib.SMTP(host, port) as server:
        server.starttls()
        server.login(user, pwd)
        server.sendmail(user, [recipient], msg.as_string())