import os
import pickle
import numpy as np
from dotenv import load_dotenv
from langchain_upstage import UpstageEmbeddings
from langchain.text_splitter import RecursiveCharacterTextSplitter
from langchain.vectorstores import FAISS

load_dotenv()

def chunk_text(text, chunk_size=1000, chunk_overlap=200):
    """
    텍스트를 청크로 분할
    """
    text_splitter = RecursiveCharacterTextSplitter(
        chunk_size=chunk_size,
        chunk_overlap=chunk_overlap,
        length_function=len,
    )
    return text_splitter.split_text(text)

def search(text):
    """
    FAISS를 사용하여 유사 사례 검색
    Args:
        text: 검색할 텍스트
    Returns:
        list: 검색 결과 리스트
    """
    # FAISS 인덱스 경로
    index_path = os.path.join(os.path.dirname(os.path.dirname(__file__)), "faiss_index")
    if not os.path.exists(index_path):
        raise FileNotFoundError(f"FAISS 인덱스 디렉토리를 찾을 수 없습니다: {index_path}")
    
    # Upstage 임베딩 초기화
    embeddings = UpstageEmbeddings(
        api_key=os.getenv("UPSTAGE_API_KEY"),
        model="embedding-query"
    )
    
    # FAISS 인덱스 로드 (pickle 파일 로드 허용)
    vectorstore = FAISS.load_local(
        index_path,
        embeddings,
        allow_dangerous_deserialization=True  # pickle 파일 로드 허용
    )
    print(f"Vectorstore type: {type(vectorstore)}")  # 디버깅: vectorstore 타입 확인
    
    # 검색 수행
    k = 3  # 상위 3개 결과
    results = vectorstore.similarity_search_with_score(text, k=k)
    
    # 결과 포맷팅
    formatted_results = []
    for doc, score in results:
        formatted_results.append({
            "text": doc.page_content,  # 문서 내용
            "details": doc.metadata.get("details", ""),  # 메타데이터에서 상세 정보
            "date": doc.metadata.get("date", ""),  # 메타데이터에서 날짜
            "file_path": doc.metadata.get("file_path", ""),  # 메타데이터에서 파일 경로
            "score": float(1 / (1 + score))  # 거리를 유사도 점수로 변환
        })
    
    return formatted_results

def embed(text):
    """
    텍스트를 벡터로 임베딩
    Args:
        text: 문자열 또는 문자열 리스트
    Returns:
        numpy.ndarray: 임베딩 벡터
    """
    embeddings = UpstageEmbeddings(
        api_key=os.getenv("UPSTAGE_API_KEY"),
        model="embedding-query"
    )
    
    # 임베딩 생성
    response = embeddings.embed_query(text)
    
    # 응답에서 실제 임베딩 벡터만 추출
    if isinstance(response, dict) and "data" in response:
        # API 응답 형식인 경우
        embedding_vector = response["data"][0]["embedding"]
    else:
        # 이미 벡터인 경우
        embedding_vector = response
    
    return embedding_vector
