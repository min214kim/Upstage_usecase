import os
import smtplib
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
import streamlit as st 


def send_alert(classification):
    """
    위험 알림 메일 발송
    """
    # 메일 서버 설정
    smtp_server = st.secrets["SMTP_SERVER"]
    smtp_port = int(st.secrets["SMTP_PORT"])
    sender_email = st.secrets["SENDER_EMAIL"]
    sender_password = st.secrets["SENDER_PASSWORD"]
    receiver_email = st.secrets["RECEIVER_EMAIL"]
    
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
