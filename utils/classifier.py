import os
import json
from datetime import datetime
from langchain_upstage import ChatUpstage
from langchain_core.messages import HumanMessage
import streamlit as st


def classify(summary, similar_cases):
    """
    상담 분류 및 심각도 평가
    """
    # 세션 상태에서 API 키 가져오기
    api_key = None
    if "api_keys" in st.session_state and st.session_state.api_keys["main"]:
        api_key = st.session_state.api_keys["main"]
    else:
        # 세션 상태에 키가 없으면 secrets 확인 (이전 방식 호환)
        api_key = st.secrets.get("UPSTAGE_API_KEY")
    
    if not api_key:
        raise ValueError("API 키가 설정되지 않았습니다. 왼쪽 사이드바에서 Upstage API 키를 입력해주세요.")
    
    chat = ChatUpstage(api_key=api_key, model="solar-mini", temperature=0.2)
    
    # 유사 사례 정보 포맷팅
    similar_cases_text = "\n".join([
        f"사례 {i+1}:\n{case.get('text', '')}\n"
        for i, case in enumerate(similar_cases)
    ])
    
    prompt = f"""
    다음 상담 요약과 유사 사례를 분석하여 JSON 형식으로 분류해주세요.
    반드시 아래 형식의 JSON으로 응답해주세요. 다른 설명은 하지 마세요.
    
    {{
        "type": "상담 유형 (일반/위기/응급)",
        "risk_level": "심각도 (1-5)",
        "abuse_type": "학대 유형 (해당없음/신체적/정서적/성적/방임)",
    }}
    
    상담 요약:
    {json.dumps(summary, ensure_ascii=False, indent=2)}
    
    유사 사례:
    {similar_cases_text}
    """
    
    messages = [HumanMessage(content=prompt)]
    response = chat.invoke(messages)
    
    try:
        # 응답에서 JSON 부분만 추출
        response_text = response.content.strip()
        # JSON 형식이 아닌 경우를 대비해 응답을 정리
        if response_text.startswith("```json"):
            response_text = response_text[7:]
        if response_text.endswith("```"):
            response_text = response_text[:-3]
        response_text = response_text.strip()
        
        # JSON 파싱
        classification = json.loads(response_text)
        
        # timestamp 직접 설정
        classification["timestamp"] = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
            
        return classification
    except json.JSONDecodeError as e:
        print(f"JSON 파싱 오류: {str(e)}")
        print(f"원본 응답: {response_text}")
        raise ValueError("분류 결과를 JSON으로 파싱할 수 없습니다.")