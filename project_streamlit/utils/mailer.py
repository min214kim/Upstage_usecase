import os
import smtplib
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
from dotenv import load_dotenv

load_dotenv()

def send_alert(classification):
    """
    위험 알림 메일 발송
    """
    # 메일 서버 설정
    smtp_server = os.getenv("SMTP_SERVER")
    smtp_port = int(os.getenv("SMTP_PORT"))
    sender_email = os.getenv("SENDER_EMAIL")
    sender_password = os.getenv("SENDER_PASSWORD")
    receiver_email = os.getenv("RECEIVER_EMAIL")
    
    # 메일 내용 구성
    msg = MIMEMultipart()
    msg['From'] = sender_email
    msg['To'] = receiver_email
    msg['Subject'] = f"🚨 위험 상담 감지 - 위기 단계 {classification['risk_level']}"
    
    body = f"""
    위험 상담이 감지되었습니다.
    
    상담 유형: {classification['type']}
    위기 단계: {classification['risk_level']}
    학대 유형: {classification['abuse_type']}
    감지 시간: {classification['timestamp']}
    """
    
    msg.attach(MIMEText(body, 'plain'))
    
    # 메일 발송
    with smtplib.SMTP(smtp_server, smtp_port) as server:
        server.starttls()
        server.login(sender_email, sender_password)
        server.send_message(msg)
