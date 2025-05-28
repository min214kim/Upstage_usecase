import streamlit as st
from utils import document_parser, text_cleaner, summarizer, embedder, search_faiss, classifier, mailer

st.set_page_config(page_title="상담 기록 분석", layout="wide")

st.title("📝 상담 기록 분석 데모")

# -----------------------
# 1. PDF 업로드
# -----------------------
uploaded_file = st.file_uploader("📄 상담 기록 PDF 업로드", type=["pdf"])


if uploaded_file:
    st.success("✅ 파일 업로드 성공!")

    # 2. 문서 파싱
    with st.spinner("문서 분석 중..."):
        raw_text = document_parser.parse(uploaded_file)
    
    # 3. 텍스트 정제 및 익명화
    clean_text = text_cleaner.clean(raw_text)

    # 4. 요약 
    summary = summarizer.summarize(clean_text)

    # 5. 임베딩 & 유사 사례 검색
    vector = embedder.embed(clean_text)
    similar_cases = search_faiss.search(vector)

    # 6. 분류
    classification = classifier.classify(summary, similar_cases)

    
    # -----------------------
    # streamlit UI
    # -----------------------

    # 요약결과
    st.subheader("🧠 상담 요약 결과")
    st.write(summary)
    st.write(f"상담 유형 : {classification['type']}")

    # 위험분석
    st.subheader("📌 위험 분석")
    # 위험 단계 badge 색상
    risk = int(classification['risk_level'])
    color = "red" if risk >= 4 else "orange" if risk == 3 else "green"
    st.markdown(f"<span style='color:white; background-color:{color}; padding:4px 8px; border-radius:6px;'>위기 단계 {risk}</span>", unsafe_allow_html=True)
    # 학대 칩
    abuse = classification['abuse_type']
    if abuse and abuse.lower() != "해당없음":
        st.markdown(f"<span style='background-color:#e0e0e0; padding:4px 8px; border-radius:16px;'>{abuse}</span>", unsafe_allow_html=True)

    # 유사사례 요약 카드
    st.subheader("🔍 유사 사례")

    cols = st.columns(len(similar_cases))
    for i, case in enumerate(similar_cases):
        with cols[i]:
            # 유사사례에 대한 요약 생성? 
            sum = summarizer.summarize(case['text'])
            st.markdown(
                f"""
                <div style="border:1px solid #ddd; border-radius:12px; padding:16px; margin:8px;">
                    <p><b>요약:</b> {sum}</p>
                    <p><b>유사도:</b> {case['score']:.2f}</p>
                </div>
                """, unsafe_allow_html=True
            )



    # -----------------------
    # 7. 위험 알림
    if int(classification['risk_level']) >= 3 or classification['abuse_type'] != "해당없음":
        mailer.send_alert(classification)
        st.warning("🚨 위험 상담 감지됨! 관리자에게 알림 발송됨")

    # 8. 로그
    st.subheader("🕒 알림 로그")
    st.code(f"메일 발송 완료: {classification['timestamp']}")