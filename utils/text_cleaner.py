import os
import concurrent.futures
import asyncio
from langchain_upstage import ChatUpstage
from langchain_core.messages import HumanMessage
from langchain.text_splitter import RecursiveCharacterTextSplitter
import pickle
import numpy as np
import streamlit as st 


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

async def process_chunk_async(index, chunk, api_key, progress_callback):
    chat = ChatUpstage(api_key=api_key, model="solar-mini", temperature=0.2)

    prompt = f"""
    다음 상담 기록에서 개인정보를 익명화하고, 불필요한 특수문자나 공백을 정리해주세요.
    이름, 학교, 지역명 등은 모두 [이름], [학교], [지역] 등으로 마스킹 처리해주세요.

    상담 기록:
    {chunk}
    """
    messages = [HumanMessage(content=prompt)]

    try:
        response = await chat.ainvoke(messages)  # must be awaitable
        if progress_callback:
            progress_callback()  # no need to pass index
        print(f"청크 {index + 1} 처리 완료")
        return (index, response.content)
    except Exception as e:
        print(f"청크 {index + 1} 처리 중 오류 발생: {str(e)}")
        return (index, f"[오류 발생: {str(e)}]")

async def clean_async(text, progress_callback=None):
    api_keys = []
    i = 1
    while True:
        key = st.secrets.get(f"UPSTAGE_API_KEY_{i}")
        if not key:
            break
        api_keys.append(key)
        i += 1

    if not api_keys:
        default_key = st.secrets.get("UPSTAGE_API_KEY")
        if default_key:
            api_keys.append(default_key)
        else:
            raise ValueError("UPSTAGE_API_KEY 환경 변수가 설정되지 않았습니다.")

    chunks = chunk_text(text)
    cleaned_chunks = [None] * len(chunks)

    print(f"총 청크 수: {len(chunks)}, API 키 수: {len(api_keys)}")

    # Dispatch async tasks
    tasks = []
    for idx, chunk in enumerate(chunks):
        api_key = api_keys[idx % len(api_keys)]
        tasks.append(process_chunk_async(idx, chunk, api_key, progress_callback))

    results = await asyncio.gather(*tasks)
    for idx, result in results:
        cleaned_chunks[idx] = result

    return "\n".join(cleaned_chunks)