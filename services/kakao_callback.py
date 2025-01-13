import json
import datetime as dt
import shortuuid # shortuuid 라이브러리를 사용하여 uuid 생성
import requests

from config import *
from openai import OpenAI
from libs.news_search import answer_news_search


# server에 chat-history를 저장하는 함수
def upload_chat_history(user_id, role, text):
    doc = {
        'user_id': user_id,
        'role': role,
        'text': text,
        'timestamp': dt.datetime.now().isoformat() # 현재 시간을 isoformat으로 저장
    }
    doc_id = shortuuid.uuid() # doc의 uuid 생성

    resp = requests.put(
        url = f"{OPENSEARCH_URL}/chat-history/_doc/{doc_id}",
        data = json.dumps(doc),
        headers = OPENSEARCH_HEADERS,
        auth = OPENSEARCH_AUTH,
    )

    print(f"Status Code: {resp.status_code}")

    # assert resp.status_code >=200 and resp.status_code < 300
    assert resp.status_code //100 == 2

# server에서 과거 chat-history를 가져오는 함수(최근 대화 100개)
def fetch_chat_history(user_id):
    query = {
            "query": {
                "term": {
                    "user_id": {
                        "value": user_id
                    }
                }
            },
            "sort": [
                {
                    "timestamp": {
                        "order": "desc" # timestamp를 기준으로 내림차순 정렬
                    }
                }
            ],
            "size": 100
        }
    resp = requests.get(
        url = f"{OPENSEARCH_URL}/chat-history/_search",
        data = json.dumps(query),
        headers = OPENSEARCH_HEADERS,
        auth = OPENSEARCH_AUTH,
    )

    assert resp.status_code == 200

    results = resp.json()
    hits = results['hits']['hits'] # 검색 결과는 hits에 저장되어 있음
    chats = [x['_source'] for x in hits] # _source에는 실제 데이터가 저장되어 있음
    chats.sort(key=lambda x: x['timestamp']) # timestamp를 기준으로 오름차순 정렬

    return chats

# 꺼내온 chat-history를 바탕으로 prompt를 생성하고 OpenAI API를 사용하여 답변 생성
def generate_answer(user_id, utterance):
    client = OpenAI()

    # 1) System message
    messages = [
        {
            'role': 'system', # 시스템 메시지
            'content': '네 이름은 byobyo야. 너는 친절한 챗봇이야. 아래 질문에 친절하고 위트있게 대답해줘'
        }
    ]

    # 2) User message
    chats = fetch_chat_history(user_id) # 사용자의 chat-history를 가져옴

    for x in chats:
        entry = {
            'role': x['role'],
            'content': x['text']
        }
        messages.append(entry)

    entry = {
        'role': 'user',
        'content': utterance,
    }
    messages.append(entry)

    resp = client.chat.completions.create(
	        model="gpt-4o-mini",
	        messages=messages,
	    ) # OpenAI API의 채팅에 completion 요청을 보냄
    
    answer = resp.choices[0].message.content.strip() # OpenAI API의 응답이 여러개일 수 있으니 첫번째것의 메시지의 컨텐트에 공백 제거해서 저장

    return answer

def generate_chat_talk(user_id, utterance):
    answer = generate_answer(user_id, utterance) # OpenAI API를 사용하여 답변 생성

    print(f"[Kakao Callback] Answer: {answer}")

    upload_chat_history(user_id, 'user', utterance) # user의 chat-history 업로드
    upload_chat_history(user_id, 'assistant', answer) # assistant의 chat-history 업로드

    body = {
                'version': '2.0',
                'template': {
                    'outputs': [
                        {
                            'simpleText': {
                                # 'text': f'{utterance} 라고 말했지?',
                                'text': answer,
                            }
                        }
                    ],
                },
            }
    return body

def main(event, context):
    body = json.loads(event['body']) # event['body']는 string이므로 json.loads를 사용하여 dict로 변환

    user_id = body['userRequest']['user']['id'] # 사용자 id를 가져옴
    utterance = body['userRequest']['utterance'] # 사용자 발화를 가져옴
    
    print(f"[Kakao Callback] User ID: {user_id}")
    print(f"[Kakao Callback] Utterance: {utterance}")

    if "뉴스" in utterance: # 사용자 발화에 "뉴스"가 포함되어 있으면
        body = answer_news_search(utterance) # llm-rag을 사용하여 뉴스 검색
    else:
        body = generate_chat_talk(user_id, utterance) # byobyo 챗봇과 대화

    response = {
        "statusCode": 200,
        "body": json.dumps(body)
    }

    return response

