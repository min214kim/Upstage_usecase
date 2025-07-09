import asyncio
from dataclasses import dataclass
import json
from threading import Lock
from typing import Any, Dict, List
import os

import streamlit as st
from langchain.globals import set_verbose
from utils import document_parser, text_cleaner, summarizer, embedder, search_faiss, classifier, mailer, renderer, sidebar


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

# LangChain verbose 설정
set_verbose(True)

# streamlit 파일 처리 결과 state
@dataclass
class AnalysisResult:
    clean_text: str
    summary: str
    similar_cases: List[Dict[str, Any]]
    classification: Dict[str, Any]

if "result" not in st.session_state:
    st.session_state.result = None

# streamlit 페이지 설정
st.set_page_config(page_title="상담 기록 분석", layout="wide")

# 도움말 출력 
sidebar.init_sidebar()

st.title("🪽 마음한켠")
st.markdown(
    ":violet-badge[:material/star: 마음을 담아] :orange-badge[:material/manage_search: Upstage Solar Embedding] :blue-badge[:material/smart_toy: Upstage Solar Pro] :gray-badge[Demo/데모]"
)

st.markdown(
    """
    #### 📝 상담 기록, 이제는 AI가 자동으로 정리해드립니다.

    비영리 현장에서 매일 쌓이는 상담 보고서,<br>
    일일이 열어보고 정리하느라 지치셨죠?

    이 데모는 여러분의 업무를 덜어주기 위해 만들어졌습니다.<br>
    PDF 상담 기록을 업로드만 하면,<br>
    
    ###### AI가 자동으로 다음 작업을 수행합니다:
    
    - PDF로 구성된 상담 기록 자동 구조화, 핵심 내용 요약 (누구, 어떤 문제, 어떤 감정 상태인지)
    - 유사 사례 자동 탐색 (과거 사례 기반한 상담 기록 분석해 얼마나 비슷한지 분석)
    - 위기 등급 자동 분류 (일반/위기/응급, 학대 유형 포함)
    - 위험 사례 감지 시, 관리자에게 이메일 발송
    """, 
    unsafe_allow_html=True)
st.markdown("""
    ###### 📌 누구에게 추천하나요?
            
    - 아동·청소년 상담, 위기 개입, 사례관리를 수행하는 NGO/NPO 담당자 
    - 상담 내용을 체계적으로 정리하고, 위기 징후에 빠르게 대응하고 싶은 분
    - 수작업 업무를 줄이고, 실무에 집중하고 싶은 실무자
    """)
st.markdown(
    """
    ###### 💡 이 데모로 기대할 수 있는 효과
    <p style="margin: 0.1em 0;">✔ Save time! 반복적 수작업 감소</p>
    <p style="margin: 0.1em 0;">✔ Real-time Monitoring! 놓치기 쉬운 위험 징후 실시간 감지</p>
    <p style="margin: 0.1em 0;">✔ Fast & Accurate! 사례 대응의 정확도와 속도 향상</p>
    <div style="height: 30px;"></div>
    """, 
    unsafe_allow_html=True
    )
st.markdown(
    """
    ###### 👇 지금 바로 여러분의 상담 기록 PDF를 업로드해 보세요!
    """, 
    unsafe_allow_html=True)

# PDF 업로드를 위한 컨테이너
upload_container = st.container(border=True)

# 진행 상태 표시를 위한 컨테이너
processing_container = st.empty()

with processing_container.container(border=True):
    progress_container = st.empty()
    status_container = st.empty()
    progress_container.progress(0, "문서 파싱 시작 전")
    status_container.info("")

# 결과 표시 탭
tab1, tab2, tab3 = st.tabs(["🧠 Step 1: 현 상담 내용 요약", "🔍 Step 2: 과거 유사 사례 보기", "📊 Step 3: 상담 분석 결과 보기, 자동화 메일 발송"])

# -----------------------
# PDF 업로드 단계
# -----------------------

with upload_container:
    uploaded_file = st.file_uploader("", help="상담 기록 PDF 파일을 여기 업로드 해주세요!", type=["pdf"])

    if uploaded_file:
        st.session_state["uploaded_file"] = uploaded_file
        #st.success("✅ 파일 업로드 성공!")

# -----------------------
# PDF 분석 단계
# -----------------------

if uploaded_file:
    uploaded_file = st.session_state["uploaded_file"]

    # API 키가 입력되었는지 확인
    if "api_keys" not in st.session_state or not st.session_state.api_keys["main"]:
        st.error("⚠️ API 키가 입력되지 않았습니다. 왼쪽 사이드바에서 Upstage API 키를 입력해주세요.")
    elif st.session_state.result is None:
        try:
            # 문서 파싱
            status_container.info("📄 PDF 파일 파싱 중...")
            progress_container.progress(0, "문서 파싱 시작")

            raw_text = document_parser.parse(uploaded_file)
            progress_container.progress(10, "문서 파싱 완료")
            
            # 텍스트 정제 및 익명화
            status_container.info("🧹 텍스트 정제 및 익명화 중...")

            chunks = text_cleaner.chunk_text(raw_text)
            total_chunks = len(chunks) # 청크 수에 따라 진행률 계산
            
            def make_progress_callback(total_chunks, progress_container):
                completed = {"count": 0}
                lock = Lock()

                def update_progress():
                    with lock:
                        completed["count"] += 1
                        chunk_num = completed["count"]
                        base_progress = 10
                        chunk_progress = (chunk_num / total_chunks) * 40
                        total_progress = base_progress + chunk_progress
                        progress_container.progress(
                            min(100, int(total_progress)),
                            f"텍스트 정제 중... ({chunk_num}/{total_chunks})"
                        )

                return update_progress
            
            # 진행률 업데이트 콜백 함수를 전달
            update_progress = make_progress_callback(len(chunks), progress_container)
            clean_text = asyncio.run(text_cleaner.clean_async(raw_text, progress_callback=update_progress))
            progress_container.progress(50, "텍스트 정제 완료")

            # 상단 내용 요약 
            status_container.info("📝 상담 내용 요약 중...")
            summary = summarizer.summarize(clean_text)
            progress_container.progress(60, "요약 완료")

            # 유사 사례 검색
            status_container.info("🔍 유사 사례 검색 중...")
            all_results = []
            
            # 각 청크별 검색 결과 수집
            for i, chunk in enumerate(chunks):
                try:
                    chunk_results = search_faiss.search(chunk)
                    if chunk_results:  # 결과가 있는 경우만 추가
                        all_results.extend(chunk_results)
                    # 진행률 업데이트
                    chunk_progress = ((i + 1) / len(chunks)) * 20
                    progress_container.progress(60 + int(chunk_progress), f"유사 사례 검색 중... ({i+1}/{len(chunks)})")
                except Exception as e:
                    st.error(f"청크 {i+1} 검색 중 오류 발생: {str(e)}")
                    continue
            
            # 결과가 없는 경우 처리
            if not all_results:
                st.warning("유사 사례를 찾을 수 없습니다.")
                similar_cases = []
            else:
                # 결과를 점수별로 정렬하고 중복 제거
                seen_docs = set()  # (file_path, text) 튜플을 저장
                similar_cases = []
                
                # 점수 기준 정렬 (높은 점수가 더 유사함)
                sorted_results = sorted(all_results, key=lambda x: x.get('score', 0), reverse=True)
                
                for result in sorted_results:
                    if not isinstance(result, dict):  # 결과 형식 검증
                        continue
                        
                    # 파일 경로와 텍스트 내용을 함께 사용하여 중복 체크
                    doc_key = (result.get('source', ''), result.get('text', ''))
                    if doc_key not in seen_docs and doc_key[0] and doc_key[1]:  # 빈 값 제외
                        seen_docs.add(doc_key)
                        similar_cases.append(result)
                        if len(similar_cases) >= 3:  # 상위 3개 결과만 유지
                            break
            
            progress_container.progress(80, "유사 사례 검색 완료")

            # 상담 분류
            status_container.info("🏷️ 상담 분류 중...")
            classification = classifier.classify(summary, similar_cases)
            progress_container.progress(100, "분류 완료")

            st.session_state.result = AnalysisResult(
                clean_text      = clean_text,
                summary         = summary,
                similar_cases   = similar_cases,
                classification  = classification
            )
            
            # 진행 상태 컨테이너 초기화
            progress_container.empty()
            status_container.empty()
            processing_container.empty()
        except FileNotFoundError as e:
            st.error(f"❌ 오류 발생: {str(e)}")
            st.info("💡 해결 방법: faiss_index 디렉토리에 필요한 파일들을 생성해주세요.")
        except Exception as e:
            st.error(f"❌ 오류 발생: {str(e)}")

# -----------------------
# 결과 출력
# -----------------------
    
if st.session_state.result:
    res: AnalysisResult = st.session_state.result

    # 원본 텍스트 (접을 수 있는 섹션)
    with tab1:
        with st.expander("📄 원본 텍스트 보기"):
            st.text_area("정제된 텍스트", res.clean_text, height=200)

        # 구조화된 요약 결과
        st.subheader("🧠 현 상담 내용 요약")
        renderer.render_summary_text(res.summary)  # 요약 텍스트를 그대로 표시

    # 유사사례 요약 카드
    with tab2:
        st.subheader("🔍 과거 유사 사례 보기")
        for i, case in enumerate(res.similar_cases):
            with st.container(border=True):
                st.caption(f"유사 사례 {i+1} (유사도: {case.get('score', 0):.2f})")

                # # 문서 원본 데이터 확인 (디버그)
                # source = os.path.join("processed", case.get('source'))
                # original = os.path.join("origin", case.get('source'))

                # if original and os.path.exists(original):
                #     with open(original, "r", encoding="utf-8") as f:
                #         data = json.load(f)
                        
                #         with st.expander("원본 데이터 보기"):
                #             st.json(data)
                
                st.markdown("#### 🧾 상세 정보")
                info = case.get("info", {})

                # 해당 정보 없으면 정보 없음 표기
                info["상담유형"] = info.get("유형구분", "정보 없음")
                info["상담자"] = info.get("작성자(상담사)", "정보 없음")
                info["상담일"] = info.get("상담일자", "정보 없음")
                info["심각도"] = info.get("위기단계", "정보 없음")
                info["학대유형"] = info.get("학대의심", "정보 없음")
                
                # 상세 정보 표시
                col1, col2 = st.columns(2)
                with col1:
                    st.write("**ID:**", case.get("id", "정보 없음"))
                    st.write("**상담일:**", info.get("상담일"))
                    st.write("**상담자:**", info.get("상담자"))
                    st.write("**성별:**", info.get("성별", "정보 없음"))
                    st.write("**나이:**", info.get("나이", "정보 없음"))

                with col2:
                    st.write("**상담 유형:**", info.get("상담유형"))
                    st.markdown(f"**심각도:** {info.get("심각도")}", help="왼쪽 사이드바 \"심각도 측정 정의\" 참조 바랍니다.")
                    st.write("**학대 유형:**", info.get("학대유형"))
                    st.write("**학년:**", info.get("학년", "정보 없음"))
                    st.write("**가정환경:**", info.get("가정환경", "정보 없음"))
                
                st.divider()

                with st.expander("📁 상담 내용, 문항별 정보 보기", expanded=False):
                    col2_1, col2_2 = st.columns(2)
                    with col2_1:
                        st.markdown("#### 📄 상담 내용")
                        renderer.render_case_text(case.get("text", "내용 없음"))
                    with col2_2:
                        st.markdown("#### 📋 문항별 정보")
                        renderer.render_json_blocks(case.get("문항별정보", {}))

    # 위험 메일 알림
    with tab3:
        st.subheader("📊 상담 분석 결과 및 자동화 메일 발송")

        log_container = st.container(border=True)
        with log_container:
            # 상담 내용 분석 결과 표시
            st.markdown("##### 📊 분석 결과")

            classification_data = res.classification
            case_type = classification_data.get('type', '분류되지 않음')
            risk_level = res.classification.get("risk_level", "0")
            abuse_type = res.classification.get("abuse_type", "해당없음")
            timestamp = classification_data.get('timestamp', '')
            
            col1, col2 = st.columns(2)
            with col1:
                st.write("**상담 유형:**", case_type)
                st.markdown(f"**심각도:** {risk_level}/5", help="왼쪽 사이드바 \"심각도 측정 정의\" 참조 바랍니다.")
            with col2:
                st.write("**학대 유형:**", abuse_type)
                st.write("**처리 시간:**", timestamp)
            
            st.divider()

            if int(risk_level) >= 3 or abuse_type != "해당없음":
                processing_container.warning("🚨 위험 상담 감지됨! 관리자에게 메일 발송 권장합니다.") # 진행 상태 표시 위치에 표시
                st.warning("⚠️ **위험 처리:** 아래 메일 보내기 확인하세요.")

        if int(risk_level) >= 3 or abuse_type != "해당없음":
            with st.container(border=True):
                # 위험 알림 메일 보내기
                st.markdown("##### 📮위험 알림 메일 보내기")

                mailcol1, mailcol2 = st.columns([1, 2])

                with mailcol1:
                    sender_email = st.secrets.get("SENDER_EMAIL", "")
                    sender_password = st.secrets.get("SENDER_PASSWORD", "")
                    receiver_email = st.secrets.get("RECEIVER_EMAIL", "")

                    user_email = st.text_input("발신자 이메일:", 
                                               value=sender_email, 
                                               placeholder="your.email@example.com")
                    user_email_password = st.text_input("앱 비밀번호:", 
                                                        value=sender_password, 
                                                        type="password", 
                                                        placeholder="**** **** **** ****", 
                                                        help="왼쪽 사이드바에서 \"Gmail 앱 비밀번호 발급 가이드\" 참조 바랍니다.")
                    destination_email = st.text_input("수신자 이메일:", 
                                                      value=receiver_email, 
                                                      placeholder="receiver.email@example.com")

                with mailcol2:
                    # 메일 본문 (수정 금지)
                    default_subject = f"🚨 [위험 상담 감지] 즉각적인 확인 및 조치가 필요합니다"
                    default_body = f"""\
안녕하세요, 담당자님.

마음 한켠, 상담 기록 분석 서비스를 통해 심각도가 높은 상담 사례가 감지되어 아래와 같이 알려드립니다.
즉각적인 확인 및 조치를 부탁드립니다.

🧾 상담 분석 요약
상담 유형: {case_type}
심각도 점수: {risk_level} / 5
감지된 학대 유형: {abuse_type}

상담 요약:

AI 분석 시각: {timestamp}

📌 조치 권장 사항
본 상담 사례에 대해 2 영업일 이내 검토 및 대응 부탁드립니다.
필요 시, 지역 보호기관 또는 전문 의료기관과 연계 조치를 검토해 주세요.

감사합니다,
마음한켠 상담 분석 시스템 드림
"""

                    user_subject = st.text_input("주제:", value=default_subject)
                    user_body = st.text_area("메일 본문:", height=600, value=default_body)

                    if st.button("📨 메일 보내기"):
                        with st.spinner("메일 발송 중..."):
                            success, msg = mailer.send_alert_email(user_subject, user_body,
                                                             sender_email=user_email, 
                                                             sender_password=user_email_password, 
                                                             receiver_email=destination_email)
                                
                        if(success):
                            st.success("✅ 이메일이 성공적으로 발송되었습니다.")
                            st.toast(msg, icon='✅')
                        else:
                            st.error(f"❌ 이메일 발송 실패했습니다.")
                            st.toast(msg, icon='❌')
        else:
            st.info("✅ **정상 처리:** 위험 수준이 낮아 메일이 발송되지 않았습니다.")