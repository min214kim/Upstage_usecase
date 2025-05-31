import streamlit as st
import os
from utils import document_parser, text_cleaner, summarizer, embedder, search_faiss, classifier, mailer
from langchain.globals import set_verbose
import pickle

# LangChain verbose 설정
set_verbose(True)

st.set_page_config(page_title="상담 기록 분석", layout="wide")

st.title("📝 상담 기록 분석 데모")

# -----------------------
# 1. PDF 업로드
# -----------------------
uploaded_file = st.file_uploader("📄 상담 기록 PDF 업로드", type=["pdf"])

if uploaded_file:
    st.success("✅ 파일 업로드 성공!")

    # 진행 상태 표시를 위한 컨테이너
    progress_container = st.empty()
    status_container = st.empty()

    try:
        # 2. 문서 파싱
        with st.spinner("문서 분석 중..."):
            status_container.info("📄 PDF 파일 파싱 중...")
            raw_text = document_parser.parse(uploaded_file)
            progress_container.progress(20, "문서 파싱 완료")
        
        # 3. 텍스트 정제 및 익명화
        status_container.info("🧹 텍스트 정제 및 익명화 중...")
        # 청크 수에 따라 진행률 계산
        chunks = text_cleaner.chunk_text(raw_text)
        total_chunks = len(chunks)
        
        def update_progress(chunk_num):
            base_progress = 20  # 이전 단계의 진행률
            chunk_progress = (chunk_num / total_chunks) * 20  # 청크 처리 진행률
            total_progress = base_progress + chunk_progress
            progress_container.progress(int(total_progress), f"텍스트 정제 중... ({chunk_num}/{total_chunks})")
        
        # 진행률 업데이트 콜백 함수를 전달
        clean_text = text_cleaner.clean(raw_text, progress_callback=update_progress)
        progress_container.progress(40, "텍스트 정제 완료")

        # 4. 요약 
        status_container.info("📝 상담 내용 요약 중...")
        summary = summarizer.summarize(clean_text)
        progress_container.progress(60, "요약 완료")

        # 5. 유사 사례 검색
        print("🔍 유사 사례 검색 중...")
        all_results = []
        for chunk in chunks:
            # 텍스트를 직접 전달
            chunk_results = search_faiss.search(chunk)
            all_results.extend(chunk_results)
        
        # 결과를 점수별로 정렬하고 중복 제거
        seen_docs = set()  # (file_path, text) 튜플을 저장
        similar_cases = []
        for result in sorted(all_results, key=lambda x: x['score'], reverse=True):
            # 파일 경로와 텍스트 내용을 함께 사용하여 중복 체크
            doc_key = (result['file_path'], result['text'])
            if doc_key not in seen_docs:
                seen_docs.add(doc_key)
                similar_cases.append(result)
                if len(similar_cases) >= 3:  # 상위 3개 결과만 유지
                    break
        
        progress_container.progress(80, "유사 사례 검색 완료")

        # 6. 분류
        status_container.info("🏷️ 상담 분류 중...")
        classification = classifier.classify(summary, similar_cases)
        progress_container.progress(100, "분류 완료")
        
        # 진행 상태 컨테이너 초기화
        progress_container.empty()
        status_container.empty()

        # -----------------------
        # streamlit UI
        # -----------------------

        # 원본 텍스트 (접을 수 있는 섹션)
        with st.expander("📄 원본 텍스트 보기"):
            st.text_area("정제된 텍스트", clean_text, height=200)

        # 구조화된 요약 결과
        st.subheader("🧠 상담 요약 결과")
        st.write(summary)  # 요약 텍스트를 그대로 표시

        # 유사사례 요약 카드
        st.subheader("🔍 유사 사례")
        for i, case in enumerate(similar_cases):
            with st.expander(f"유사 사례 {i+1} (유사도: {case['score']:.2f})"):
                st.markdown(
                    f"""
                    <div style="border:1px solid #ddd; border-radius:12px; padding:16px; margin:8px;">
                        <p><b>제목:</b> {case['text']}</p>
                        <p><b>상세 내용:</b> {case['details']}</p>
                        <p><b>날짜:</b> {case['date']}</p>
                    </div>
                    """, unsafe_allow_html=True
                )
                
                # 문서 다운로드 버튼
                if case['file_path'] and os.path.exists(case['file_path']):
                    with open(case['file_path'], 'rb') as f:
                        file_data = f.read()
                        st.download_button(
                            label="📥 원본 문서 다운로드",
                            data=file_data,
                            file_name=os.path.basename(case['file_path']),
                            mime="application/pdf"
                        )

        # -----------------------
        # 7. 위험 알림
        if classification.get("emergency_level", 0) >= 3 or classification.get("abuse_type", "해당없음") != "해당없음":
            with st.spinner("🚨 위험 알림 발송 중..."):
                mailer.send_alert({
                    "type": classification.get("problem_type", ""),
                    "risk_level": classification.get("emergency_level", 0),
                    "abuse_type": classification.get("abuse_type", "해당없음"),
                    "timestamp": classification.get("timestamp", "")
                })
                st.warning("🚨 위험 상담 감지됨! 관리자에게 알림 발송됨")

        # 8. 로그
        st.subheader("🕒 알림 로그")
        st.code(f"메일 발송 완료: {classification.get('timestamp', '')}")

    except FileNotFoundError as e:
        st.error(f"❌ 오류 발생: {str(e)}")
        st.info("💡 해결 방법: faiss_index 디렉토리에 필요한 파일들을 생성해주세요.")
    except Exception as e:
        st.error(f"❌ 오류 발생: {str(e)}")