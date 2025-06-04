import os
import json
from langchain_upstage import ChatUpstage
from langchain_core.messages import HumanMessage
import streamlit as st 



def summarize(text):
    """
    상담 내용을 요약
    """
    chat = ChatUpstage(api_key=st.secrets["UPSTAGE_API_KEY"], model="solar-pro", temperature=0.2)
    
    prompt = f"""
    다음 상담 기록을 분석하여 구조화된 형식으로 요약해주세요.
    반드시 아래 형식으로 응답해주세요. 다른 설명은 하지 마세요.

    [신상 정보]
    나이: [나이]
    성별: [성별]
    가족 구성: [가족 구성]

    [주요 문제점]
    [주요 문제점 요약]

    [생활 및 환경]
    가정 환경: [가정 환경]
    학교 환경: [학교 환경]
    사회적 관계: [사회적 관계]

    [학대 평가]
    유형: [학대 유형 (해당없음/신체적/정서적/성적/방임)]
    심각도: [심각도 (1-5)]
    상세 내용: [상세 내용]

    [응급도]
    수준: [응급도 (1-5)]
    이유: [응급 판단 이유]

    [종합 소견]
    1. 현재 상황: [현재 상황 분석]
    2. 주요 문제점: [주요 문제점]
    3. 위험 요소: [위험 요소]
    4. 개입 필요성: [개입 필요성]
    5. 권장 조치사항: [권장 조치사항]
    
    상담 기록:
    {text}
    """
    
    messages = [HumanMessage(content=prompt)]
    response = chat.invoke(messages)
    
    # 응답에서 텍스트 부분만 추출
    response_text = response.content.strip()
    if response_text.startswith("```"):
        response_text = response_text[3:]
    if response_text.endswith("```"):
        response_text = response_text[:-3]
    
    return response_text.strip()




