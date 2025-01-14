import json
import shortuuid
import requests
import datetime as dt

from config import *
from libs.photo import generate_photo_answer
from libs.schedule import generate_schedule_answer
from libs.news_search import answer_news_search
from libs.prompt_chains import process_user_message, detect_intent

def upload_chat_history(user_id, role, text):
    doc = {
        'user_id': user_id,
        'role': role,
        'text': text,
        'timestamp': dt.datetime.now().isoformat()
    }
    doc_id = shortuuid.uuid()

    resp = requests.put(
        url = f"{OPENSEARCH_URL}/chat-history/_doc/{doc_id}",
        data = json.dumps(doc),
        headers = OPENSEARCH_HEADERS,
        auth = OPENSEARCH_AUTH,
    )
    print(f"Status Code: {resp.status_code}")
    assert resp.status_code // 100 == 2

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

def main(event, context):
    body = json.loads(event['body'])
    user_id = body['userRequest']['user']['id']
    utterance = body['userRequest']['utterance']
    
    print(f"[Kakao Callback] User ID: {user_id}")
    print(f"[Kakao Callback] Utterance: {utterance}")

    # Get chat history for context
    chat_history = fetch_chat_history(user_id)
    
    # Process the message using our prompt chains
    intent, params = detect_intent(utterance)
    print(f"[Kakao Callback] Intent: {intent}")

    # Handle different intents
    if intent == 'chat':
        response, body = process_user_message(user_id, utterance, chat_history)
    elif intent == 'photo':
        body, response = generate_photo_answer(user_id, params)
    elif intent == 'schedule':
        response = generate_schedule_answer(user_id, utterance)
        body = {
            "version": "2.0",
            "template": {
                "outputs": [
                    {
                        "simpleText": {
                            "text": response
                        }
                    }
                ]
            }
        }
    elif intent == 'news':
        response = answer_news_search(utterance)
        body = {
            "version": "2.0",
            "template": {
                "outputs": [
                    {
                        "simpleText": {
                            "text": response
                        }
                    }
                ]
            }
        }
    else:
        response = "죄송해요, 이해하지 못했어요. 다시 말씀해 주세요!"
        body = {
            "version": "2.0",
            "template": {
                "outputs": [
                    {
                        "simpleText": {
                            "text": response
                        }
                    }
                ]
            }
        }

    print(f"[Kakao Callback] Answer: {response}")

    # Save chat history
    upload_chat_history(user_id, 'user', utterance)
    upload_chat_history(user_id, 'assistant', response)

    return {
        "statusCode": 200,
        "body": json.dumps(body)
    }

