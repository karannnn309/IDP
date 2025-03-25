import smtplib
from email.mime.text import MIMEText

msg = MIMEText("Test message")
msg['Subject'] = 'Test'
msg['From'] = 'your@gmail.com'
msg['To'] = 'recipient@example.com'

with smtplib.SMTP_SSL('smtp.gmail.com', 465) as server:
    server.login('your@gmail.com', 'apppassword')
    server.send_message(msg)
print("Email sent!")