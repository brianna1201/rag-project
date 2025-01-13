import json
import requests
import pandas as pd

from config import *
 
def query_new_trends(search):
    query = {
    "query": {
        "match": {
        "title": "금리"
        }
    },
    "size": 0,
    "aggs": {
        "group_by_date": {
        "date_histogram": {
            "field": "created_at",
            "interval": "day"
        }
        }
    }
    }

    if search:
        query['query'] = {
            'match': {
                'title': search
            }
        }

    query = json.dumps(query)

    headers = {
        'Content-Type': 'application/json'
    }

    resp = requests.get(
        f"{OPENSEARCH_URL}/news/_search",
        headers=headers,
        data=query,
        auth=OPENSEARCH_AUTH,
    )

    print(f'Status code: {resp.status_code}')

    results = resp.json()
    buckets = results['aggregations']['group_by_date']['buckets']

    if len(buckets) == 0:
        return []

    df = pd.DataFrame(buckets)
    df['date'] = df['key_as_string'].str[:10]
    df = df[['date', 'doc_count']]

    return df.to_dict(orient='records')

def main(event, context):
    params = event.get('queryStringParameters')

    if params:
        search = params.get('search')
    else:
        search = None

    trends = query_new_trends(search)

    body = {
        'trends': trends,
    }

    print('body')

    response = {
        "statusCode": 200,
        "body": json.dumps(body),
        # CORS
        "headers": {
            "Content-Type": "application/json",
            "Access-Control-Allow-Origin": "*",
            "Access-Control-Allow-Credentials": True,
        }
    }

    return response