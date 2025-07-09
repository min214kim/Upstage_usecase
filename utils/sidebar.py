import os
import streamlit as st

def init_sidebar():
    st.sidebar.title("ℹ️ 도움말")
    
    # API 키 입력 섹션
    with st.sidebar.container(border=True):
        st.markdown("##### 🔑 Upstage API 설정")
        
        # 세션 상태 초기화
        if "api_keys" not in st.session_state:
            st.session_state.api_keys = {
                "main": "",
                "keys": [""] * 8
            }
        
        # 메인 API 키 입력
        main_api_key = st.text_input(
            "Upstage API Key (필수)",
            value=st.session_state.api_keys["main"],
            type="password",
            placeholder="upstage-api-key-here",
            help="Document AI, Embedding, LLM에 사용될 API 키"
        )
        
        # 병렬 처리용 추가 API 키 (선택사항)
        with st.expander("🚀 병렬 처리용 추가 API 키 (선택사항)", expanded=False):
            st.caption("텍스트 정제 속도 향상을 위한 추가 키 (최대 8개)")
            
            for i in range(8):
                key = st.text_input(
                    f"API Key {i+1}",
                    value=st.session_state.api_keys["keys"][i],
                    type="password",
                    placeholder=f"upstage-api-key-{i+1}",
                    key=f"api_key_{i}"
                )
                st.session_state.api_keys["keys"][i] = key
        
        # API 키 저장
        st.session_state.api_keys["main"] = main_api_key
        
        # 유효성 검사
        if main_api_key:
            st.success("✅ API 키 입력됨")
        else:
            st.warning("⚠️ API 키를 입력해주세요")

    # 예시 PDF 다운로드 도움말 출력
    pdf_dir = img_path = os.path.join("document_example", "업스테이지 예시 문서")
    pdf_image_path = os.path.join("document_example", "예시 문서 사진", "예시1_screenshot.jpeg")
    with st.sidebar.container(border=True):
        st.markdown("##### 예시 PDF 다운로드")

        for start in range(1, 5, 2):            # 1, then 3
            cols = st.columns(2)
            for offset, col in enumerate(cols):
                i = start + offset            # maps to 1→col0, 2→col1 then 3→col0, 4→col1
                path = os.path.join(pdf_dir, f"예시{i}.pdf")
                if os.path.isfile(path):
                    data = open(path, "rb").read()
                    with col:
                        st.download_button(
                            label=f"예시{i}.pdf",
                            data=data,
                            file_name=f"상담기록_예시{i}.pdf",
                            mime="application/pdf",
                            icon=":material/download:",
                            key=f"dl{i}",
                            help=f"예시 PDF 상담기록_예시{i}.pdf 다운로드"
                        )
                else:
                    with col:
                        st.warning(f"예시{i}.pdf 없음")

    # 예시 PDF 보기 도움말 출력
    with st.sidebar.expander("📄 예시 PDF 보기"):
        st.image(pdf_image_path, caption="이런 형태의 PDF 올려주세요!")
    
    # 심각도 측정 도움말
    with st.sidebar.expander("🚨 심각도 측정 정의"):
        st.markdown("""
        본 서비스는 상담 요약 및 유사 사례들과 함께 심층 분석을 진행하며, **상담 유형**, **심각도**, **학대 유형**을 도출합니다.
        심각도(`risk_level`)는 내담자의 위기 가능성과 개입 필요성을 고려하여 아래 기준에 따라 평가됩니다:

        | 심각도 | 설명 |
        |--------|------|
        | **1단계 (매우 낮음)** | 일반적인 고민이나 일상적인 스트레스 수준으로, 위기 징후 없음 |
        | **2단계 (낮음)** | 반복적이거나 장기적인 스트레스가 있으나, 자해나 타해 위험 없음 |
        | **3단계 (보통)** | 감정적 불안정이나 대인관계 문제 등으로 주의가 필요한 상태 |
        | **4단계 (높음)** | 자해 또는 타해 충동 가능성이 감지되며, 개입 필요성이 높음 |
        | **5단계 (매우 높음)** | 즉각적인 개입이 필요한 응급 상황, 심각한 위기 상태 |
        """)

    # 앱 비밀번호 발급 도움말 출력 
    with st.sidebar.expander("📘 Gmail 앱 비밀번호 발급 가이드"):
        st.markdown("""
        **"앱 비밀번호"는 일반 비밀번호 대신 외부 앱에서 Gmail SMTP로 로그인할 때 사용하는 16자리 전용 비밀번호입니다.**  
        이메일 데모를 사용하려면 아래 과정을 따라 앱 비밀번호를 발급받아 입력해주세요.

        #### 1. Google 계정 보안 페이지로 이동
        👉 https://myaccount.google.com/security  

        #### 2. 2단계 인증 설정
        앱 비밀번호는 2단계 인증이 켜져 있어야 발급 가능합니다.  
        - 보안 탭에서 2단계 인증 항목 확인 - "사용"으로 설정되어 있지 않다면 먼저 활성화해주세요.  
        - 전화번호 등록 → 보안 코드(문자 또는 앱) 수신  

        #### 3. 앱 비밀번호 생성
        👉 https://myaccount.google.com/apppasswords

        #### 4. 생성된 16자리 비밀번호 복사
        노란 배경에 표시된 16자리 숫자/문자 조합을 복사  
        *예: `abcd efgh ijkl mnop`*  

        #### 5. 데모 앱에 붙여넣기 
        위 16자리 코드를 "앱 비밀번호" 입력칸에 붙여넣고  
        [이메일 보내기] 버튼 누르면 정상 발송됩니다.  

        #### 🛑 주의점  
        - 이 앱 비밀번호는 Gmail 웹/앱 로그인에 사용되지 않습니다.  
        - 잘못 입력 시 SMTP 인증 오류가 발생하니, 반드시 복사 + 붙여넣기 해주세요.
        """)