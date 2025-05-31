import os
from dotenv import load_dotenv
from langchain_upstage import UpstageEmbeddings

load_dotenv()

def embed(text):
    """
    텍스트를 벡터로 임베딩
    Args:
        text: 문자열 또는 문자열 리스트
    """
    embeddings = UpstageEmbeddings(
        api_key=os.getenv("UPSTAGE_API_KEY"),
        model="embedding-query"
    )
    
    vector = embeddings.embed_query(text)
    return vector
