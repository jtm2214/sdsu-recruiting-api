# test_email.py
import os
from utils.email_alerts import send_email

os.environ.update({
  "SMTP_HOST": "smtp.gmail.com",
  "SMTP_PORT": "587",
  "EMAIL_USER": "you@gmail.com",
  "EMAIL_PASS": "your_app_password",
  "EMAIL_TO": "gm@sdsu.edu"
})

send_email("API Test", "If you see this, email works! 🎉")
print("✅ Email send() returned without exception.")
