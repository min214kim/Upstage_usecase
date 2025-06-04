import os
import tempfile
from langchain_upstage import UpstageDocumentParseLoader


def parse(file):
    """
    PDF 파일을 파싱하여 텍스트로 변환
    """
    # 임시 파일로 저장
    with tempfile.NamedTemporaryFile(delete=False, suffix='.pdf') as tmp_file:
        tmp_file.write(file.getvalue())
        tmp_file_path = tmp_file.name
    
    try:
        # 임시 파일로 로더 생성
        loader = UpstageDocumentParseLoader(tmp_file_path, ocr="force")
        pages = loader.load()
        
        # 모든 페이지 텍스트 합치기
        full_text = "\n".join([page.page_content for page in pages])
        return full_text
    finally:
        # 임시 파일 삭제
        os.unlink(tmp_file_path)
