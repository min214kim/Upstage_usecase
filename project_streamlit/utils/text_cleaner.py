import os
import concurrent.futures
from dotenv import load_dotenv
from langchain_upstage import ChatUpstage
from langchain_core.messages import HumanMessage
from langchain.text_splitter import RecursiveCharacterTextSplitter
import pickle
import numpy as np
import streamlit as st 

load_dotenv()

def chunk_text(text, chunk_size=1000, chunk_overlap=100):
    """
    텍스트를 청크로 분할
    """
    text_splitter = RecursiveCharacterTextSplitter(
        chunk_size=chunk_size,
        chunk_overlap=chunk_overlap,
        length_function=len,
    )
    return text_splitter.split_text(text)

def process_chunk(chunk, api_key):
    """
    단일 청크 처리
    """
    chat = ChatUpstage(api_key=api_key, model="solar-mini", temperature=0.2)
    
    prompt = f"""
    다음 상담 기록에서 개인정보를 익명화하고, 불필요한 특수문자나 공백을 정리해주세요.
    이름, 학교, 지역명 등은 모두 [이름], [학교], [지역] 등으로 마스킹 처리해주세요.
    
    상담 기록:
    {chunk}
    """
    
    messages = [HumanMessage(content=prompt)]
    response = chat.invoke(messages)
    return response.content

def clean(text, progress_callback=None):
    """
    텍스트 정제 및 익명화 (병렬 처리)
    """
    # API 키 목록 가져오기
    api_keys = []
    i = 1
    while True:
        key = st.secrets.get(f"UPSTAGE_API_KEY_{i}")
        if not key:
            break
        api_keys.append(key)
        i += 1
    
    # 기본 API 키 추가
    if not api_keys:
        api_keys.append(st.secrets.get("UPSTAGE_API_KEY"))
    
    if not api_keys:
        raise ValueError("UPSTAGE_API_KEY 환경 변수가 설정되지 않았습니다.")
    
    # 텍스트를 청크로 분할
    chunks = chunk_text(text)
    cleaned_chunks = [None] * len(chunks)  # 결과를 저장할 리스트
    
    # 청크를 API 키 수에 맞게 분배
    chunk_distribution = [[] for _ in range(len(api_keys))]
    for i, chunk in enumerate(chunks):
        chunk_distribution[i % len(api_keys)].append((i, chunk))
    
    print(f"총 청크 수: {len(chunks)}, API 키 수: {len(api_keys)}")
    
    # 각 API 키별로 병렬 처리
    with concurrent.futures.ThreadPoolExecutor(max_workers=len(api_keys)) as executor:
        # 각 API 키에 할당된 청크들을 처리하는 함수
        def process_chunks_for_api(api_key, assigned_chunks):
            results = []
            for chunk_index, chunk in assigned_chunks:
                try:
                    result = process_chunk(chunk, api_key)
                    results.append((chunk_index, result))
                    print(f"청크 {chunk_index + 1}/{len(chunks)} 처리 완료")
                except Exception as e:
                    print(f"청크 {chunk_index + 1} 처리 중 오류 발생: {str(e)}")
                    results.append((chunk_index, f"[오류 발생: {str(e)}]"))
            return results
        
        # 각 API 키에 청크 처리 작업 제출
        future_to_api = {
            executor.submit(process_chunks_for_api, api_key, chunks): api_key
            for api_key, chunks in zip(api_keys, chunk_distribution)
        }
        
        # 완료된 작업 처리
        completed = 0
        for future in concurrent.futures.as_completed(future_to_api):
            try:
                results = future.result()
                for chunk_index, result in results:
                    cleaned_chunks[chunk_index] = result
                    completed += 1
                    if progress_callback:
                        progress_callback(completed)
            except Exception as e:
                print(f"API 키 {future_to_api[future]} 처리 중 오류 발생: {str(e)}")
    
    # 청크들을 하나의 텍스트로 합치기
    return "\n".join(cleaned_chunks)

