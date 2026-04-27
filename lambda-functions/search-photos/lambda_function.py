import json
import os
import boto3
import urllib.request
import base64
from urllib.parse import quote
from botocore.config import Config

config = Config(
    connect_timeout=5,
    read_timeout=10,
    retries={"max_attempts": 1},
)

lex = boto3.client(
    "lexv2-runtime",
    region_name="us-east-1",
    config=config,
)

BOT_ID = os.environ["BOT_ID"]
BOT_ALIAS_ID = os.environ["BOT_ALIAS_ID"]
OPENSEARCH_HOST = os.environ["OPENSEARCH_HOST"]
OPENSEARCH_USERNAME = os.environ["OPENSEARCH_USERNAME"]
OPENSEARCH_PASSWORD = os.environ["OPENSEARCH_PASSWORD"]
OPENSEARCH_INDEX = os.environ.get("OPENSEARCH_INDEX", "photos")


def lambda_handler(event, context):
    query = event.get("queryStringParameters", {}).get("q", "")

    # Call Lex to extract keywords
    lex_response = lex.recognize_text(
        botId=BOT_ID,
        botAliasId=BOT_ALIAS_ID,
        localeId="en_US",
        sessionId="photo-search-session",
        text=query,
    )

    slots = lex_response["sessionState"]["intent"].get("slots", {})
    keywords = []

    if slots.get("KeywordOne") and slots["KeywordOne"].get("value"):
        keywords.append(slots["KeywordOne"]["value"]["interpretedValue"].lower())

    if slots.get("KeywordTwo") and slots["KeywordTwo"].get("value"):
        keywords.append(slots["KeywordTwo"]["value"]["interpretedValue"].lower())

    if not keywords:
        return build_response({"results": [], "keywords": []})

    # OpenSearch query
    search_body = {
        "query": {
            "bool": {
                "should": [
                    {"match": {"labels": keyword}}
                    for keyword in keywords
                ],
                "minimum_should_match": 1,
            }
        }
    }

    url = f"https://{OPENSEARCH_HOST}/{OPENSEARCH_INDEX}/_search"

    credentials = f"{OPENSEARCH_USERNAME}:{OPENSEARCH_PASSWORD}"
    encoded_credentials = base64.b64encode(credentials.encode()).decode()

    request = urllib.request.Request(
        url,
        data=json.dumps(search_body).encode("utf-8"),
        headers={
            "Content-Type": "application/json",
            "Authorization": f"Basic {encoded_credentials}",
        },
        method="GET",
    )

    with urllib.request.urlopen(request, timeout=10) as response:
        data = json.loads(response.read().decode("utf-8"))

    results = []

    # Build response with image URLs
    for hit in data["hits"]["hits"]:
        source = hit["_source"]

        object_key = source.get("objectKey")
        bucket = source.get("bucket")

        image_url = None
        if object_key and bucket:
            image_url = f"https://{bucket}.s3.amazonaws.com/{quote(object_key)}"

        results.append({
            "objectKey": object_key,
            "bucket": bucket,
            "url": image_url,
            "labels": source.get("labels", []),
        })

    return build_response({
        "keywords": keywords,
        "results": results,
    })


def build_response(body):
    return {
        "statusCode": 200,
        "headers": {
            "Access-Control-Allow-Origin": "*",
            "Access-Control-Allow-Headers": "*",
            "Access-Control-Allow-Methods": "GET,OPTIONS",
        },
        "body": json.dumps(body),
    }