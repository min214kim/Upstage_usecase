import os
import tempfile
from langchain_upstage import UpstageDocumentParseLoader
import streamlit as st


def parse(file):
    """
    PDF 파일을 파싱하여 텍스트로 변환
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
    
    # 임시 파일로 저장
    with tempfile.NamedTemporaryFile(delete=False, suffix='.pdf') as tmp_file:
        tmp_file.write(file.getvalue())
        tmp_file_path = tmp_file.name
    
    try:
        # 임시 파일로 로더 생성
        loader = UpstageDocumentParseLoader(tmp_file_path, api_key=api_key, ocr="force")
        pages = loader.load()
        
        # 모든 페이지 텍스트 합치기
        full_text = "\n".join([page.page_content for page in pages])
        return full_text
    finally:
        # 임시 파일 삭제
        os.unlink(tmp_file_path)
