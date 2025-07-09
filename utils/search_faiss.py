import os
import pickle
import json
import numpy as np

from langchain_upstage import UpstageEmbeddings
from langchain.text_splitter import RecursiveCharacterTextSplitter
from langchain_community.vectorstores import FAISS
import streamlit as st 

import logging
logger = logging.getLogger(__name__)

# Configure logging
logging.basicConfig(
    level=logging.INFO,  # Options: DEBUG, INFO, WARNING, ERROR, CRITICAL
    format="%(asctime)s [%(levelname)s] %(message)s",
    handlers=[
        # logging.FileHandler("app.log"),      # Save logs to file
        logging.StreamHandler()              # Print logs to console
    ]
)

# FAISS 인덱스는 함수 호출 시에 로드하도록 변경
vectorstore = None


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

def get_original_data(file_path):
    """
    원본 JSON 파일에서 데이터를 로드
    """
    try:
        with open(file_path, 'r', encoding='utf-8') as f:
            return json.load(f)
    except Exception as e:
        print(f"원본 파일 로드 중 오류 발생: {str(e)}")
        return None

def search(query_text, k=3):
    """
    FAISS를 사용하여 유사 문서 검색
    """
    global vectorstore
    
    # 세션 상태에서 API 키 가져오기
    api_key = None
    if "api_keys" in st.session_state and st.session_state.api_keys["main"]:
        api_key = st.session_state.api_keys["main"]
    else:
        # 세션 상태에 키가 없으면 secrets 확인 (이전 방식 호환)
        api_key = st.secrets.get("UPSTAGE_API_KEY")
    
    if not api_key:
        raise ValueError("API 키가 설정되지 않았습니다. 왼쪽 사이드바에서 Upstage API 키를 입력해주세요.")
    
    # vectorstore가 없으면 로드
    if vectorstore is None:
        embeddings = UpstageEmbeddings(
            api_key=api_key,
            model="embedding-query"
        )
        
        if os.path.exists("faiss_index/index.faiss") and os.path.exists("faiss_index/index.pkl"):
            vectorstore = FAISS.load_local(
                "faiss_index", 
                embeddings,
                allow_dangerous_deserialization=True
            )
            logger.info(f"Index size: {vectorstore.index.ntotal}")
        else:
            raise FileNotFoundError("FAISS index not found. Please upload or generate the index.")
    
    try:
        # 검색 수행
        results = vectorstore.similarity_search_with_score(query_text, k=k)

        # 결과 포맷팅
        formatted_results = []
        for doc, score in results:
            source = doc.metadata.get('source', '')
            if source:
                # 원본 파일 경로에서 파일명 추출
                file_name = os.path.basename(source)
                # processed 폴더에서 원본 데이터 로드
                original_data = get_original_data(os.path.join("processed", file_name))
                
                if original_data:
                    result = {
                        'text': doc.page_content,
                        'score': float(score),
                        'source': source,
                        'id': original_data.get('id', ''),
                        'info': original_data.get('info', {}),
                        '문항별정보': original_data.get('문항별정보', {})
                    }
                else:
                    result = {
                        'text': doc.page_content,
                        'score': float(score),
                        'source': source
                    }
            else:
                result = {
                    'text': doc.page_content,
                    'score': float(score)
                }
            
            formatted_results.append(result)
        
        return formatted_results
    except Exception as e:
        logger.info(f"검색 중 오류 발생: {str(e)}")
        return []

def embed(text):
    """
    텍스트를 벡터로 임베딩
    Args:
        text: 문자열 또는 문자열 리스트
    Returns:
        numpy.ndarray: 임베딩 벡터
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
