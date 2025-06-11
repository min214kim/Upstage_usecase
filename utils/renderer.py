import re
import html
import streamlit as st

def render_summary_text(summary_text: str):
    """
    Render a structured summary using minimal headings and bolded key-value pairs.
    Each section header is shown with a small heading, and inside each section,
    lines are parsed so that the part before the colon is bolded.
    """
    blocks = re.split(r"\n?\[([^\[\]]+)\]", summary_text)

    for i in range(1, len(blocks), 2):
        section_title = blocks[i].strip()
        section_body_raw = blocks[i + 1].strip()

        section_container = st.container(border=True)

        with section_container:
            # Render section header (compact)
            st.markdown(f"#### {section_title}")

            # Format each line: bolden text before colon
            for line in section_body_raw.splitlines():
                if ":" in line:
                    key, value = line.split(":", 1)

                    key_stripped = key.strip()
                    if(key_stripped == "심각도"):
                        st.markdown(f"**{key.strip()}**: {value.strip()}", help="왼쪽 사이드바 \"심각도 측정 정의\" 참조 바랍니다.")
                    else:
                        st.markdown(f"**{key.strip()}**: {value.strip()}")
                else:
                    st.markdown(f"{line.strip()}")

def render_case_text(case_text: str):
    """
    Render case text block-by-block inside styled HTML with bolded labels (before ':').
    """
    blocks = re.split(r"\n?\[([^\[\]]+)\]", case_text)

    for i in range(1, len(blocks), 2):
        section_title = blocks[i].strip()
        section_body_raw = blocks[i + 1].strip()

        # Preprocess each line to bolden label before colon
        processed_lines = []
        for line in section_body_raw.splitlines():
            if ":" in line:
                key, value = line.split(":", 1)
                bolded = f"<strong>{html.escape(key.strip())}</strong>: {html.escape(value.strip())}"
                processed_lines.append(bolded)
            else:
                processed_lines.append(html.escape(line.strip()))

        # Join lines with <br> for rendering inside styled HTML
        section_body = "<br>".join(processed_lines)

        # with st.expander(f"케이스 {i}: {section_title}", expanded=False):
        st.caption(f"케이스 {i}: {section_title}")
        st.markdown(
            f"""
            <div style="background-color: #f9f9f9; padding: 16px; border-radius: 8px; margin-bottom: 16px; border-left: 4px solid #4a90e2;">
                <div style="
                    background-color: #ffffff;
                    padding: 12px;
                    border-radius: 4px;
                    border: 1px solid #ddd;
                    font-size: 14px;
                    line-height: 1.6;
                    color: #333;
                    white-space: normal;
                ">{section_body}</div>
            </div>
            """,
            unsafe_allow_html=True
        )

def render_json_blocks(data):
    prev_title = ""
    for entry in data:
        # with st.expander(f"문항: {entry.get('문항', '')}", expanded=False):
        title = entry.get('문항', '')

        if title != prev_title:
            st.caption(f"문항: {title}")
            prev_title = title

        st.markdown(
            f"""
            <div style="background-color: #f9f9f9; padding: 16px; border-radius: 8px; margin-bottom: 12px; border-left: 4px solid #4a90e2; font-size: 14px; line-height: 1.4;">
                <p style="margin: 4px 0;"><strong>점수:</strong> {entry.get('점수', '')}</p>
                <p style="margin: 4px 0;"><strong>임상가코멘트:</strong> {entry.get('임상가코멘트', entry.get('임상가코 멘트', '없음'))}</p>
                <p style="margin: 4px 0;"><strong>문제요인:</strong> {entry.get('문제요인', '')}</p>
                <p style="margin: 4px 0;"><strong>기타 정보:</strong></p>
                <ul style="margin: 4px 0 4px 16px; padding-left: 0;">
                    {"".join(f"<li style='margin:2px 0;'><b>{k}:</b> {v}</li>" for k, v in entry.items() if k not in ['문항', '항목', '점수', '임상가코멘트', '임상가코 멘트', '문제요인'])}
                </ul>
            </div>
            """,
            unsafe_allow_html=True
        )