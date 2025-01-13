import json
import pdb
import requests

from openai import OpenAI
from config import *

def make_basic_query(text):
    client = OpenAI()
    resp = client.embeddings.create(
                model = "text-embedding-3-large",
                input = text,
            )
    embed = resp.data[0].embedding

    # semantic search
    ## 돈 아끼기...(입문자용)
    query = {
        "query": {
            "knn" : {
                "embed" : {
                    "vector" : embed,
                    "k" : 2,
                }
            }
        },
        "size": 2, # 가장 유사한 2개의 결과를 가져옴
        "_source": ["title","summary","sources"], # 제목, 요약, 원본기사 id만 가져옴
    }
    return query

def make_advanced_query(text):
    client = OpenAI()
    resp = client.embeddings.create(
                model = "text-embedding-3-large",
                input = text,
            )
    embed = resp.data[0].embedding

    # query 검색 & embedding 검색
    # keyword search 가중치 1, embedding search 가중치 1
    query_kewords = {
        "script_score": {
            "query" : {
                "multi_match": {
                    "query": text,
                    "fields": ["title^4", "summary"],
                }
            },
            "script": {
                "source" : "_score * 1"
            }
        }
    }
    query_embedding = {
        "script_score": {
            "query": {
                "knn": {
                    "embed": {
                        "vector": embed,
                        "k": 2,
                    }
                }
            },
            "script": {
                "source": "_score * 1"
            }
        }
    }

    # should: 둘 중 하나라도 만족하면 결과에 포함
    query = {
        "query": {
            "bool": {
                "should": [query_kewords, query_embedding],
            }
        },
        "size": 2, # 가장 유사한 2개의 결과를 가져옴
        "_source": ["title","summary","sources"], # 제목, 요약, 원본기사 id만 가져옴
    }
    return query

def semantic_search(text):
    # query = make_basic_query(text)
    query = make_advanced_query(text)

    resp = requests.get(
        url = f"{OPENSEARCH_URL}/topics/_search",
        data = json.dumps(query),
        headers = OPENSEARCH_HEADERS,
        auth = OPENSEARCH_AUTH,
    )

    assert resp.status_code == 200

    results = resp.json()
    hits = results['hits']['hits'] # 검색 결과는 hits에 저장되어 있음
    docs = [x['_source'] for x in hits] # _source에는 실제 데이터가 저장되어 있음

    return docs

def generate_answer(topics, utterance):
    buffer = []

    for x in topics:
        entry = f"""
        제목: {x['title']}
        내용: {x['summary']}
        """
        buffer.append(entry)
    context = '\n'.join(buffer) # 기사들을 하나의 문자열로 합침

    prompt = f"""
    신문기사
    =======
    {context}

    사용자 질문
    =======
    {utterance}
    """
    print(prompt)

    client = OpenAI()
    messages = [
        {
            'role': 'system',
            'content': '아래 뉴스기사들을 바탕으로 사용자의 질문에 대답해줘.'
        },
        {
            'role': 'user',
            'content': prompt,
        }
    ]
    resp = client.chat.completions.create(
	        model = "gpt-4o-mini",
	        messages = messages,
	    )
    answer = resp.choices[0].message.content.strip()

    print(answer)
    return answer

def answer_news_search(utterance):
    topics = semantic_search(utterance) # 사용자 발화를 바탕으로 semantic search를 통해 관련 기사를 가져옴
    answer = generate_answer(topics, utterance) # 가져온 기사를 바탕으로 답변 생성

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