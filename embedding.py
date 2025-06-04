import os
from dotenv import load_dotenv
import json
import time
from pathlib import Path
from typing import List
from langchain_upstage import UpstageEmbeddings
from langchain_community.vectorstores import FAISS
from langchain.docstore.document import Document

load_dotenv()

def create_faiss_vector_db(json_dir: str, output_index_path: str):
    folder = Path(json_dir)

    # ❶ Upstage 임베딩 초기화
    embeddings = UpstageEmbeddings(
        api_key=os.getenv("UPSTAGE_API_KEY"),  # 여기에 본인의 API 키 입력
        model="embedding-query"
    )

    # ❷ 빈 FAISS 객체 준비
    faiss_index = None

    # ❸ 문서 순차 임베딩 및 추가
    for file in sorted(folder.glob("????.json")):
        try:
            with open(file, "r", encoding="utf-8") as f:
                data = json.load(f)
            text = data.get("text", "").strip()
            if not text:
                continue
            doc = Document(page_content=text, metadata={"source": file.name})

            # 문서별로 임베딩 후 추가
            if faiss_index is None:
                faiss_index = FAISS.from_documents([doc], embeddings)
            else:
                faiss_index.add_documents([doc])

            print(f"[✓] Embedded {file.name}")
            # time.sleep(1.0)  # 💡 Upstage Rate Limit 회피용 딜레이
        except Exception as e:
            print(f"[✗] Failed to process {file.name}: {e}")

    # ❹ 최종 인덱스 저장
    if faiss_index:
        faiss_index.save_local(output_index_path)
        print(f"[✓] FAISS index saved to {output_index_path}")
    else:
        print("[!] No documents were embedded. FAISS index not created.")

create_faiss_vector_db("processed", "faiss_index")  
