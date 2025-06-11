import os
import re
import smtplib
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
import socket
import ssl
import streamlit as st 

import logging
logger = logging.getLogger(__name__)

# 파이썬 로깅 설정
logging.basicConfig(
    level=logging.INFO,  # Options: DEBUG, INFO, WARNING, ERROR, CRITICAL
    format="%(asctime)s [%(levelname)s] %(message)s",
    handlers=[
        # logging.FileHandler("app.log"),      # 로그 파일로 저장
        logging.StreamHandler()
    ]
)

def send_alert_email(text_subject: str, text_body: str, 
               sender_email: str = "", sender_password: str = "",
               receiver_email: str = "") -> tuple[bool, str]:
    """
    위험 알림 메일 발송
    """
    return_msg = ""

    try:            
        logger.info(f"Sending email using {sender_email} to {receiver_email}")
            
        # 메일 서버 설정
        if not sender_email:
            sender_email = st.secrets.get("SENDER_EMAIL", "")
        if not sender_password:
            sender_password = st.secrets.get("SENDER_PASSWORD", "")
        if not receiver_email:
            receiver_email = st.secrets.get("RECEIVER_EMAIL", "")
        smtp_server = st.secrets.get("SMTP_SERVER", "smtp.gmail.com")
        smtp_port = int(st.secrets.get("SMTP_PORT", "587"))

        if not isinstance(smtp_port, int):
            return "SMTP 포트 설정 오류: 올바른 숫자여야 합니다."
        
        email_re = r"[^@]+@[^@]+\.[^@]+"
        if not re.match(email_re, sender_email):
            return "발신자 이메일 형식이 잘못되었습니다."
        if not re.match(email_re, receiver_email):
            return "수신자 이메일 형식이 잘못되었습니다."
        
        # 메일 내용 구성
        msg = MIMEMultipart()
        msg['From'] = sender_email
        msg['To'] = receiver_email
        msg['Subject'] = text_subject
        
        msg.attach(MIMEText(text_body, 'plain'))
        
        # 메일 발송
        with smtplib.SMTP(smtp_server, smtp_port, timeout=10) as server:
            server.starttls()
            server.login(sender_email, sender_password)
            server.send_message(msg)

        return_msg = f"이메일 주소 {receiver_email}로 메일이 발송되었습니다." 
        return True, return_msg  # success
    except ValueError:
        return_msg = "SMTP 포트 설정 오류: 올바른 숫자여야 합니다."
    except socket.gaierror:
        return_msg = "SMTP 서버 호스트 이름을 찾을 수 없습니다. DNS 설정을 확인하세요."
    except smtplib.SMTPAuthenticationError:
        return_msg = "SMTP 인증 오류: 이메일 또는 비밀번호가 올바르지 않습니다."
    except smtplib.SMTPConnectError:
        return_msg = "SMTP 서버에 연결할 수 없습니다. 서버 주소와 포트를 확인하세요."
    except smtplib.SMTPHeloError:
        return_msg = "SMTP HELO/EHLO 명령 중 오류가 발생했습니다."
    except smtplib.SMTPRecipientsRefused:
        return_msg = "수신자 이메일이 거부되었습니다. 이메일 주소를 확인하세요."
    except smtplib.SMTPDataError:
        return_msg = "SMTP 데이터 전송 중 오류가 발생했습니다."
    except ssl.SSLError:
        return_msg = "TLS 보안 연결을 설정하지 못했습니다."
    except socket.timeout:
        return_msg = "서버 연결 시간이 초과되었습니다. 네트워크 상태를 확인하세요."
    except Exception as e:
        return_msg = f"알 수 없는 오류가 발생했습니다: {e}"

    return False, return_msg # not successful