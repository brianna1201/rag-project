import json


def hello(event, context):
    body = {
        "message": "스테이터스코드",
        "input": event
    }

    response = {
        "statusCode": 200,
        "body": json.dumps(body)
    }

    return response

