import os
import requests 
from langchain_upstage import ChatUpstage
from langchain_core.messages import HumanMessage
from dotenv import load_dotenv
load_dotenv()

def summarize(text):
    """
    Solar LLM을 사용하여 텍스트를 요약합니다.
    -  input : text
    -  output : text
    """
    print("------summarize함수------")

    API_KEY = os.getenv("UPSTAGE_API_KEY")
    if not API_KEY:
        raise ValueError("UPSTAGE_API_KEY 환경 변수가 설정되지 않았습니다.")

    prompt = f"""
        다음 상담 내용을 세 문장으로 요약하세요. 

        상담 내용:
        {text}

        요약:
    """
    
    chat = ChatUpstage(api_key=API_KEY, model="solar-pro")
    
    messages = [
        HumanMessage(
            content= prompt
        )
    ]
    
    response = chat.invoke(messages)
    print(response)
    summary_text = response.content.strip()
    return summary_text




