import json
import pdb
import requests
import datetime as dt
import shortuuid
import datetime

from openai import OpenAI
from config import *

def fetch_schedule(user_id, date):
    query = {

        "query": {
            "bool": {
            "must": [
                {"match": {"user_id": user_id}},
                {"match": {"date": date}}
            ]
            }
        },
        "sort": [
            {"timestamp": {"order": "desc"}}
        ],
        "size": 10
        }
    
    # print(query)
    resp = requests.get(
        url = f"{OPENSEARCH_URL}/schedule/_search",
        data = json.dumps(query),
        headers = OPENSEARCH_HEADERS,
        auth = OPENSEARCH_AUTH,
    )

    # assert resp.status_code == 200
    
    results = resp.json()
    print(results)
    hits = results['hits']['hits']
    schedules = [x['_source'] for x in hits]
    schedules.sort(key=lambda x: x['timestamp'])


    return schedules

def generate_schedule_answer(user_id, utterance):
    nowtime = datetime.datetime.now()
    dateDict = {0: '월요일', 1:'화요일', 2:'수요일', 3:'목요일', 4:'금요일', 5:'토요일', 6:'일요일'}

    client = OpenAI()
    
    messages = [
        {
        'role': 'system',
        'content': f"""
        답변은 반드시 주어진 두 가지 중 한가지 방식으로 해야돼.
        """
        },
        {'role': 'user',
        'content': f"""
        다음 대사가 아래 둘 중 어떤 상황인지 파악하고 그것에 맞는 답변을 줘.
        (1)이나 (2)같은 표시는 빼고.
        대사: "{utterance}"

        (1) 일정을 기억하려는 경우 아래와 같이 한다.
        만약 일정을 기억하려는 것이라면, 오늘 날짜가 {nowtime.date()} {dateDict[nowtime.weekday()]} 이니까 
        '{utterance}' 라고 한 이 일정의 이름과 실제 날짜를 '[이름] YYYY-MM-DD HH:mm' 형식으로 알려줘. 
        [이름]에는 날짜와 관련된 단어가 들어가면 안되고 네가 요약한 키워드를 대신 넣어줘.
        답변 양식: '[이름] YYYY-MM-DD HH:mm'

        (2) 일정은 확인하려는 경우 아래와 같이 한다
        '{utterance} 라는 내용이 언제 어떤 일정이 있는지 궁금하다는 내용이면,
        우리의 데이터 중에서 그 일정을 찾을 수 있도록 중요한 키워드로 요약해줘.
        이때는 "['일정검색'] YYYY-MM-DD" 형식으로 알려줘. '일정검색'은 그대로 유지해야돼.
        답변 양식: "['일정검색'] YYYY-MM-DD"
        """
        }
    ]

    resp = client.chat.completions.create(
    model="gpt-4o",
    messages=messages,
    )

    answer  = resp.choices[0].message.content.strip()

    print(answer)


    if "일정검색" in answer:
        date = answer[-11:].strip()
        # print(date)
        # 일정이 궁금하면 opensearch schedule에서 검색
        schedules = fetch_schedule(user_id, date)
        print(schedules)
        if schedules == []:
            answer = "일정이 없습니다"
            return answer

        answer = f"{schedules[0]['date']} {schedules[0]['time']} 일정은 {schedules[0]['text']}입니다."

        return answer

    
    else: # opensearch schedule 문서에 해당 일정 저장
        doc = {
            'user_id': user_id,
            'date': answer[-16:-6],
            'time': answer[-6:],
            'text':answer[1:-18],        
            'timestamp': dt.datetime.now().isoformat() # 현재 시간을 isoformat으로 저장
        }
        doc_id = shortuuid.uuid() # doc의 uuid 생성

        resp = requests.put(
            url = f"{OPENSEARCH_URL}/schedule/_doc/{doc_id}",
            data = json.dumps(doc),
            headers = OPENSEARCH_HEADERS,
            auth = OPENSEARCH_AUTH,
        )

        answer = f"다음 일정을 저장했습니다. {answer}"
        return answer

    assert resp.status_code // 100 == 2  # 성공 상태 코드 확인



    # print(resp)










