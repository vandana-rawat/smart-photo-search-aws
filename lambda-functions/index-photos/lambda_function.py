import json
import os
import re
import urllib.parse
from datetime import timezone

import boto3
import urllib3
from botocore.auth import SigV4Auth
from botocore.awsrequest import AWSRequest

print("VERIFY_CODEPIPELINE_UPDATE_latest")
s3 = boto3.client("s3")
rekognition = boto3.client("rekognition")
http = urllib3.PoolManager()

REGION = os.environ.get("REGION", "us-east-1")
OPENSEARCH_ENDPOINT = os.environ["OPENSEARCH_ENDPOINT"].rstrip("/")
OPENSEARCH_INDEX = os.environ.get("OPENSEARCH_INDEX", "photos")


def normalize_text(value):
    """
    Lowercase, trim, collapse spaces, and remove empty labels.
    """
    if not value:
        return None

    value = str(value).strip().lower()
    value = re.sub(r"\s+", " ", value)

    return value if value else None


def simple_singular(label):
    """
    Handles simple plural/singular cases for better search matching.
    Examples:
      cats -> cat
      dogs -> dog
      parties -> party
      boxes -> box
      people -> person
    """
    if not label:
        return None

    irregular = {
        "people": "person",
        "children": "child",
        "men": "man",
        "women": "woman"
    }

    if label in irregular:
        return irregular[label]

    if len(label) > 4 and label.endswith("ies"):
        return label[:-3] + "y"

    if len(label) > 4 and label.endswith("es"):
        if label.endswith(("ches", "shes", "xes", "zes", "ses")):
            return label[:-2]

    if len(label) > 3 and label.endswith("s") and not label.endswith("ss"):
        return label[:-1]

    return label


def add_normalized_label(labels_set, raw_label):
    """
    Adds the normalized label and a simple singular version if useful.
    """
    label = normalize_text(raw_label)
    if not label:
        return

    labels_set.add(label)

    singular = simple_singular(label)
    if singular:
        labels_set.add(singular)


def parse_custom_labels(metadata):
    """
    S3 user metadata keys are usually returned in lowercase by boto3.
    Header used during upload:
      x-amz-meta-customLabels: beach, family, nyc

    boto3 head_object usually exposes it as:
      Metadata["customlabels"]
    """
    if not metadata:
        return []

    custom_labels_raw = (
        metadata.get("customlabels")
        or metadata.get("customLabels")
        or metadata.get("custom-labels")
        or ""
    )

    if not custom_labels_raw:
        return []

    return [label.strip() for label in custom_labels_raw.split(",") if label.strip()]


def signed_opensearch_request(method, path, body=None):
    """
    Sends an IAM SigV4-signed request to Amazon OpenSearch Service.
    """
    url = f"{OPENSEARCH_ENDPOINT}{path}"

    if body is not None:
        body = json.dumps(body)
    else:
        body = ""

    headers = {
        "Content-Type": "application/json",
        "Host": urllib.parse.urlparse(OPENSEARCH_ENDPOINT).netloc
    }

    request = AWSRequest(
        method=method,
        url=url,
        data=body,
        headers=headers
    )

    credentials = boto3.Session().get_credentials().get_frozen_credentials()
    SigV4Auth(credentials, "es", REGION).add_auth(request)

    prepared_request = request.prepare()

    response = http.request(
        method,
        url,
        body=body,
        headers=dict(prepared_request.headers)
    )

    response_text = response.data.decode("utf-8")

    if response.status >= 300:
        raise Exception(
            f"OpenSearch request failed. "
            f"Status: {response.status}, Response: {response_text}"
        )

    return {
        "status": response.status,
        "body": response_text
    }


def index_photo_document(document):
    """
    Indexes one photo document into OpenSearch index photos.
    Uses deterministic document ID so re-uploading the same key updates the doc.
    """
    document_id = urllib.parse.quote(
        f"{document['bucket']}/{document['objectKey']}",
        safe=""
    )

    path = f"/{OPENSEARCH_INDEX}/_doc/{document_id}"
    return signed_opensearch_request("PUT", path, document)


def process_record(record):
    bucket = record["s3"]["bucket"]["name"]
    object_key = urllib.parse.unquote_plus(record["s3"]["object"]["key"])

    print(f"Processing uploaded object: s3://{bucket}/{object_key}")

    # 1. Read S3 object metadata using headObject
    head_response = s3.head_object(Bucket=bucket, Key=object_key)
    metadata = head_response.get("Metadata", {})
    print(f"S3 metadata: {json.dumps(metadata)}")

    # 2. Extract created timestamp from S3 LastModified
    last_modified = head_response["LastModified"]
    created_timestamp = (
        last_modified
        .astimezone(timezone.utc)
        .replace(microsecond=0)
        .isoformat()
        .replace("+00:00", "Z")
    )

    # 3. Detect labels using Rekognition
    rekognition_response = rekognition.detect_labels(
        Image={
            "S3Object": {
                "Bucket": bucket,
                "Name": object_key
            }
        },
        MaxLabels=20,
        MinConfidence=70
    )

    labels_set = set()

    for label in rekognition_response.get("Labels", []):
        add_normalized_label(labels_set, label.get("Name"))

    # 4. Extract custom labels from x-amz-meta-customLabels
    custom_labels = parse_custom_labels(metadata)

    for custom_label in custom_labels:
        add_normalized_label(labels_set, custom_label)

    labels = sorted(labels_set)

    # 5. Build assignment-required OpenSearch document
    document = {
        "objectKey": object_key,
        "bucket": bucket,
        "createdTimestamp": created_timestamp,
        "labels": labels
    }

    print("Document to index:")
    print(json.dumps(document, indent=2))

    # 6. Index into OpenSearch
    index_response = index_photo_document(document)

    print("OpenSearch index response:")
    print(json.dumps(index_response, indent=2))

    return document


def lambda_handler(event, context):
    print("index-photos Lambda invoked")
    print("Received event:")
    print(json.dumps(event, indent=2))

    indexed_documents = []

    for record in event.get("Records", []):
        event_source = record.get("eventSource")

        if event_source != "aws:s3":
            print(f"Skipping non-S3 event source: {event_source}")
            continue

        indexed_document = process_record(record)
        indexed_documents.append(indexed_document)

    return {
        "statusCode": 200,
        "body": json.dumps({
            "message": "Photos indexed successfully",
            "indexedCount": len(indexed_documents),
            "documents": indexed_documents
        })
    }