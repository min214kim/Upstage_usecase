import os
from langchain_upstage import UpstageEmbeddings
import streamlit as st



def embed(text):
    """
    텍스트를 벡터로 임베딩
    Args:
        text: 문자열 또는 문자열 리스트
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
    
    embeddings = UpstageEmbeddings(
        api_key=api_key,
        model="embedding-query"
    )
    
    vector = embeddings.embed_query(text)
    return vector
