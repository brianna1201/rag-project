import json
import shortuuid
import requests
import datetime as dt

from config import *
from openai import OpenAI
from libs.photo import generate_photo_answer

##############################################
# OpenSearch 데이터 업로드
# --------------------------------------------
# 1) upload_chat_history
# : 사용자와 챗봇의 대화 내용 업로드
# /chat-history: 사용자와 챗봇의 대화 내용을 저장하는 인덱스
# --------------------------------------------
# 2) upload_photo
# : 사용자의 사진 업로드
# libs > photo.py에 구현
# --------------------------------------------
#TODO 3) upload_schedule
# : 사용자의 일정 업로드
# libs > schedule.py에 구현
# --------------------------------------------
#TODO 4) 뉴스 검색하기는 libs > news_search_project.py에 구현
##############################################

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
    assert resp.status_code // 100 == 2  # 성공 상태 코드 확인


##############################################
# OpenSearch 데이터 조회
# --------------------------------------------
# 1) fetch_chat_history
# : 사용자의 챗봇 대화 내용 조회
# /chat-history: 사용자와 챗봇의 대화 내용을 저장하는 인덱스
##############################################
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
                        "order": "desc"
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
    hits = results['hits']['hits']
    chats = [x['_source'] for x in hits]
    chats.sort(key=lambda x: x['timestamp'])

    return chats


##############################################
# OpenAI API를 사용하여 챗봇 답변 생성
# --------------------------------------------
# 1) generate_answer
# : OpenAI API를 사용하여 일상대화 챗봇 답변 생성
##############################################
def generate_answer(user_id, utterance):
    client = OpenAI()

    messages = [
        {
            'role': 'system',
            'content': '네 이름은 자비스야. 너는 친절한 챗봇이야. 아래 질문에 친절하게 대답해줘'
        }
    ]

    chats = fetch_chat_history(user_id)

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

    print(f"[generate_answer] Messages: {messages}")

    resp = client.chat.completions.create(
        model="gpt-4o-mini",
        messages=messages,
    )
    
    answer = resp.choices[0].message.content.strip()

    return answer


##############################################
# Main : Kakao API Gateway
##############################################

def main(event, context):
    body = json.loads(event['body'])

    user_id = body['userRequest']['user']['id']
    utterance = body['userRequest']['utterance']
    
    print(f"[Kakao Callback] User ID: {user_id}")
    print(f"[Kakao Callback] Utterance: {utterance}")

    ##############################################
    #TODO : 사용자 의도 분석
    # detect_intent 함수를 사용하여 사용자의 의도를 분석하고
    # 분석된 의도와 파라미터를 반환
    ##############################################
    def detect_intent(utterance):
        client = OpenAI()
        messages=[
            {
            "role": "system",
            "content": (
                "당신은 사용자의 의도를 파악하는 유용한 비서입니다. "
                "가능한 의도는 다음과 같습니다: "
                "‘chat’(일반 대화), ‘schedule’(일정 관리), ‘photo’(사진 관리), ‘news’(뉴스 검색) "
                "사용자의 발화를 바탕으로 의도(intent)와 필요한 매개변수(params)를 JSON 형식으로 응답하세요. "

                "만약 사용자가 jpg, png 등 사진 파일을 업로드했다면, params에는 다음 정보를 포함해야 합니다: "
                "photo_url (사용자가 업로드한 사진의 URL)과 description (사진과 관련된 설명) "
                "만약 사용자가 별도의 설명을 제공하지 않았다면 description은 '사용자가 제공하지 않음'으로 설정하세요. "
                
                "사용자가 특정 날짜에 업로드한 사진을 요청할 경우, params에는 다음 정보를 포함해야 합니다: "
                "photo_url (사용자가 업로드한 사진의 URL)과 description (사진과 관련된 설명), photo_date (YYYY-MM-DD 형식의 날짜) "
                "params가 없을 경우 빈 딕셔너리로 반환하세요."
            )
            },
            {"role": "user", "content": f"Utterance: {utterance}"}
        ]

        resp = client.chat.completions.create(
            model="gpt-4o-mini",
            messages=messages,
        )
        # 응답에서 의도 파싱
        answer = resp.choices[0].message.content.strip()

        # JSON 형태의 의도와 파라미터 추출
        try:
            result = json.loads(answer)
            intent = result.get('intent', 'chat')
            params = result.get('params', {})
        except json.JSONDecodeError:
            # 예상치 못한 응답 처리
            intent = 'chat'
            params = {}
        return intent, params

    intent, params = detect_intent(utterance)
    print(f"[Kakao Callback] Intent: {intent}")

    if intent == 'chat':
        answer = generate_answer(user_id, utterance)
    elif intent == 'photo':
        answer = generate_photo_answer(user_id, params)
    elif intent == 'schedule':
        pass
    elif intent == 'news':
        pass
    else:
        answer = "죄송해요, 이해하지 못했어요. 다시 말씀해 주세요!"

    print(f"[Kakao Callback] Answer: {answer}")

    ##############################################
    upload_chat_history(user_id, 'user', utterance)
    upload_chat_history(user_id, 'assistant', answer)

    body = {
                'version': '2.0',
                'template': {
                    'outputs': [
                        {
                            'simpleText': {
                                'text': answer,
                            }
                        }
                    ],
                },
            }

    response = {
        "statusCode": 200,
        "body": json.dumps(body)
    }

    return response

