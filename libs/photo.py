import json
import pdb
import requests
import datetime as dt
import shortuuid

from openai import OpenAI
from config import *

##############################################
# OpenSearch 데이터 업로드
# --------------------------------------------
# 1) upload_photo
# : 사용자의 사진 업로드
# /user-photos: 사용자의 사진을 저장하는 인덱스
##############################################
def upload_photo(user_id, photo_url, description=None):
    doc = {
        'user_id': user_id,
        'photo_url': photo_url,       # 저장된 사진의 URL
        'description': description or "사용자가 업로드한 사진",   # 설명
        'timestamp': dt.datetime.now().isoformat() # 업로드 시간
    }
    doc_id = shortuuid.uuid() # doc의 uuid 생성

    try:
        resp = requests.put(
        url = f"{OPENSEARCH_URL}/user-photos/_doc/{doc_id}",
        data = json.dumps(doc),
        headers = OPENSEARCH_HEADERS,
        auth = OPENSEARCH_AUTH,
        )
        
        print(f"Status Code: {resp.status_code}")
        assert resp.status_code // 100 == 2  # 성공 상태 코드 확인

        print("[upload_photo] Successfully uploaded photo to OpenSearch.")
        return "사진이 성공적으로 저장되었습니다!"
    except Exception as e:
        print(f"[upload_photo] Error: {str(e)}")
        return "사진 업로드에 실패했습니다. 다시 시도해주세요!"
    


##############################################
# OpenSearch 데이터 조회
# --------------------------------------------
# 1) fetch_photo_by_date
# : 특정 날짜에 업로드된 사용자의 사진 조회
# /user-photos: 사용자의 사진을 저장하는 인덱스
##############################################
def fetch_photo_by_date(user_id, date):
    """
    특정 날짜에 업로드된 사용자의 사진을 검색합니다.
    """
    start_date = f"{date}T00:00:00"
    end_date = f"{date}T23:59:59"

    query = {
        "query": {
            "bool": {
                "must": [
                    {"term": {"user_id": {"value": user_id}}},
                    {"range": {"timestamp": {"gte": start_date, "lte": end_date}}}
                ]
            }
        },
        "sort": [
            {
                "timestamp": {
                    "order": "desc"
                }
            }
        ],
        "size": 100  # 최대 100개의 결과 반환
    }

    resp = requests.get(
        url=f"{OPENSEARCH_URL}/user-photos/_search",
        data=json.dumps(query),
        headers=OPENSEARCH_HEADERS,
        auth=OPENSEARCH_AUTH,
    )

    assert resp.status_code == 200

    results = resp.json()

    hits = results['hits']['hits']
    photos = [x['_source'] for x in hits]
    return photos


def generate_photo_answer(user_id, params):
    """
    사용자의 사진 업로드 요청에 대한 응답을 생성합니다.
    """
    photo_url = params.get("photo_url")
    description = params.get("description")
    photo_date = params.get("photo_date")  # 날짜가 제공된 경우

    if photo_date: # photo 의도에 날짜가 포함된 경우
        photos = fetch_photo_by_date(user_id, photo_date)
        if not photos:
            log_message = f"{photo_date}에 업로드된 사진이 없습니다."
            body = {
                "version": "2.0",
                "template": {
                    "outputs": [
                        {
                            "simpleText": {
                                "text": log_message
                            }
                        }
                    ]
                }
            }
        else:
            photo = photos[0]  # 첫 번째 사진
            log_message = f"{photo_date}에 업로드된 첫 번째 사진을 표시합니다."
            body = {
                "version": "2.0",
                "template": {
                    "outputs": [
                        {
                            "simpleImage": {
                                "imageUrl": photo['photo_url'],  # 원본 URL 사용
                                "altText": f"미리보기: {photo.get('description', '설명 없음')}"
                            }
                        }
                    ]
                }
            }
    else:
        upload_result = upload_photo(user_id, photo_url, description)
        log_message = upload_result
        body = {
            "version": "2.0",
            "template": {
                "outputs": [
                    {
                        "simpleText": {
                            "text": log_message  # 업로드 결과 메시지 반환
                        }
                    }
                ]
            }
        }
    return body, log_message