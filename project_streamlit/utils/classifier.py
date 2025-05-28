import os
import requests
import json
from dotenv import load_dotenv
from langchain_upstage import ChatUpstage
from langchain.prompts import PromptTemplate
from langchain.chains import LLMChain
import json
import re

load_dotenv()

API_KEY = os.getenv("UPSTAGE_API_KEY")
llm = ChatUpstage(api_key=API_KEY, model="solar-pro")


print(API_KEY)
prompt = PromptTemplate(
    input_variables=["user_summary", "case_descriptions"],
    template="""
다음은 사용자 상담 요약입니다:
{user_summary}

유사한 과거 상담 사례들:
{case_descriptions}

아래 JSON 스키마(예시)처럼, 상담을 분류해주세요.
스키마:
```json
  "type": "<string: 상담유형>",
  "risk_level": <integer 1-5>,
  "abuse_type": "<string or 해당없음>"
```
위기단계가 높을수록 더 위험한 상황입니다.
학대 정황이 없으면 "해당없음"을 반환해주세요.

결과 JSON:
"""
)

chain = LLMChain(llm=llm, prompt=prompt)

def classify(user_summary, similar_cases):
    """
    Solar LLM을 사용하여 텍스트를 요약하고 관련 태그를 생성합니다.
    -  input : 사용자 text에 대한 요약 (text), 유사 사례 N건 (list)
    -  output : json
    """

    print("------classify함수------")

    case_descriptions = "\n".join([
        f"{i+1}. 임상: {c.get('임상가 종합소견', '').strip()}, "
        f"가정환경: {c.get('가정환경', '').strip()}, "
        f"유형: {c.get('유형구분', '').strip()}, "
        f"위기: {c.get('위기단계', '').strip()}, "
        f"학대: {c.get('학대의심', '').strip()}"
        for i, c in enumerate(similar_cases)
    ])

    # LLM 호출
    raw = chain.invoke({
        "user_summary": user_summary,
        "case_descriptions": case_descriptions
    })
    print("▶ raw text result:", raw['text'])

    # chain.invoke may return a dict or a plain string
    text = raw["text"] if isinstance(raw, dict) and "text" in raw else raw

    # 코드펜스 제거 
    text = re.sub(r'```(?:json)?', '', text).strip()

    # 첫 번째 JSON 블록만 추출
    m = re.search(r'(\{[\s\S]*?\})', text)
    if not m:
        raise ValueError(f"JSON 파싱 실패, 원본 응답:\n{text}")
    json_str = m.group(1)

    # JSON 파싱
    try:
        return json.loads(json_str)
    except json.JSONDecodeError as e:
        raise ValueError(f"파싱된 JSON이 유효하지 않습니다:\n{json_str}\n\n원본 응답:\n{text}") from e