# Proof Checklist for Assignment 3

## My ownership: OpenSearch and indexing side

### AWS resources created

- [x] S3 photos bucket B2: `smart-photo-search-b2-vandana-2026`
- [x] OpenSearch domain: `photos`
- [x] OpenSearch index: `photos`
- [x] Lambda LF1: `index-photos`
- [x] IAM role for LF1: `index-photos-lambda-role`
- [x] S3 ObjectCreated trigger from B2 to LF1

### Verified functionality

- [x] Uploading a photo to B2 invokes LF1.
- [x] LF1 receives the S3 PUT event.
- [x] LF1 extracts bucket name and object key.
- [x] LF1 calls S3 `head_object`.
- [x] LF1 reads custom labels from S3 metadata.
- [x] LF1 calls Rekognition `detect_labels`.
- [x] LF1 normalizes and deduplicates labels.
- [x] LF1 indexes the photo document into OpenSearch.
- [x] OpenSearch search by custom label returns the photo.
- [x] OpenSearch group label query returns the photo.

### Screenshots saved

- [ ] GitHub repo structure
- [ ] B2 bucket details
- [ ] S3 event notification
- [ ] LF1 Lambda overview
- [ ] LF1 environment variables
- [ ] IAM role permissions
- [ ] CloudWatch log showing LF1 invoked
- [ ] CloudWatch log showing final indexed document
- [ ] OpenSearch domain active
- [ ] OpenSearch index mapping
- [ ] OpenSearch custom label search result
- [ ] OpenSearch group query result
- [ ] GitHub push proof

### Integration constants

```text
B2 photos bucket: smart-photo-search-b2-vandana-2026
OpenSearch domain: photos
OpenSearch index: photos
OpenSearch region: us-east-1
OpenSearch endpoint: https://search-photos-4bjfzgq4g5ccsmejeprhyoizxe.us-east-1.es.amazonaws.com
LF1 name: index-photos
Custom labels upload header: x-amz-meta-customLabels
S3 Console metadata key: customLabels