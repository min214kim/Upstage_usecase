import streamlit as st
import os
from utils import document_parser, text_cleaner, summarizer, embedder, search_faiss, classifier, mailer
from langchain.globals import set_verbose
import pickle
import json

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
            with st.expander(f"유사 사례 {i+1} (유사도: {case.get('score', 0):.2f})"):
                st.markdown(
                    f"""
                    <div style="border:1px solid #ddd; border-radius:12px; padding:16px; margin:8px;">
                        <h4>상담 내용</h4>
                        <p>{case.get('text', '내용 없음')}</p>
                        
                        <h4>상세 정보</h4>
                        <p><b>ID:</b> {case.get('id', '정보 없음')}</p>
                        <p><b>상담일:</b> {case.get('info', {}).get('상담일', '정보 없음')}</p>
                        <p><b>상담자:</b> {case.get('info', {}).get('상담자', '정보 없음')}</p>
                        <p><b>상담 유형:</b> {case.get('info', {}).get('상담유형', '정보 없음')}</p>
                        <p><b>위험도:</b> {case.get('info', {}).get('위험도', '정보 없음')}</p>
                        <p><b>학대 유형:</b> {case.get('info', {}).get('학대유형', '정보 없음')}</p>
                        
                        <h4>문항별 정보</h4>
                        <pre style="background-color: #f5f5f5; padding: 10px; border-radius: 5px; overflow-x: auto;">
{json.dumps(case.get('문항별정보', []), ensure_ascii=False, indent=2)}
                        </pre>
                    </div>
                    """, unsafe_allow_html=True
                )
                
                # 문서 다운로드 버튼
                source = case.get('source')
                if source and os.path.exists(source):
                    with open(source, 'rb') as f:
                        file_data = f.read()
                        st.download_button(
                            label="📥 원본 문서 다운로드",
                            data=file_data,
                            file_name=os.path.basename(source),
                            mime="application/json"
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
        st.subheader("🕒 처리 로그")
        log_container = st.container()
        with log_container:
            st.markdown("### 📊 분석 결과")
            st.markdown(f"""
            - **상담 유형**: {classification.get('type', '분류되지 않음')}
            - **위험도**: {classification.get('risk_level', '0')}/5
            - **학대 유형**: {classification.get('abuse_type', '해당없음')}
            - **처리 시간**: {classification.get('timestamp', '')}
            """)
            
            if classification.get("emergency_level", 0) >= 3 or classification.get("abuse_type", "해당없음") != "해당없음":
                st.markdown("### 🚨 위험 알림")
                st.markdown(f"""
                - **알림 발송**: ✅ 완료
                - **발송 시간**: {classification.get('timestamp', '')}
                - **알림 유형**: {classification.get('problem_type', '')}
                - **위험 수준**: {classification.get('risk_level', '0')}/5
                """)
            else:
                st.markdown("### ✅ 정상 처리")
                st.markdown("위험 수준이 낮아 알림이 발송되지 않았습니다.")

    except FileNotFoundError as e:
        st.error(f"❌ 오류 발생: {str(e)}")
        st.info("💡 해결 방법: faiss_index 디렉토리에 필요한 파일들을 생성해주세요.")
    except Exception as e:
        st.error(f"❌ 오류 발생: {str(e)}")