# index-photos Lambda

LF1 for NYU Cloud Computing Assignment 3.

## Purpose

Triggered by S3 ObjectCreated events from the B2 photos bucket.

The Lambda:

1. Reads the uploaded S3 bucket and object key.
2. Calls S3 `head_object` to retrieve upload metadata.
3. Extracts custom labels from `x-amz-meta-customLabels`.
4. Calls Rekognition `detect_labels`.
5. Normalizes and deduplicates Rekognition + custom labels.
6. Indexes the final photo document into OpenSearch index `photos`.

## Required environment variables

```text
OPENSEARCH_ENDPOINT=https://search-photos-4bjfzgq4g5ccsmejeprhyoizxe.us-east-1.es.amazonaws.com
OPENSEARCH_INDEX=photos
REGION=us-east-1