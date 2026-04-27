# 🔍 Smart Photo Search — LF2 (Search Photos Lambda)

## 📌 Overview

This Lambda function implements the **search functionality (LF2)** for the Smart Photo Search application.

It processes user queries, extracts keywords using Amazon Lex, and retrieves matching photos from OpenSearch.

---

## ⚙️ Architecture Flow

User → API Gateway → Lambda (Search Photos) → Amazon Lex → OpenSearch → Results

---

## 🚀 Features

* Natural language query processing using Amazon Lex
* Supports:

  * Single keyword search (`dog`)
  * Sentence-based search (`show me dogs`)
  * Multi-keyword search (`cats and dogs`)
* Uses **OR-based search logic** for better recall
* Returns matching photos with metadata

---

## 🧠 Search Logic

The system follows **flexible search behavior**:

### 1. Independent Search

Query:

```
dog
```

Returns all photos where:

```
labels contains "dog"
```

---

### 2. Sentence Search

Query:

```
show me dogs
```

Lex extracts:

```
dogs
```

---

### 3. Group Search (Recommended OR logic)

Query:

```
cats and dogs
```

OpenSearch query:

```json
{
  "query": {
    "bool": {
      "should": [
        { "match": { "labels": "cats" } },
        { "match": { "labels": "dogs" } }
      ],
      "minimum_should_match": 1
    }
  }
}
```

Ranking behavior:

* Photos with both labels → higher relevance
* Photos with one label → still returned

---

## 🌐 API Endpoint

### GET /search

#### Example:

```
/search?q=dogs and people
```

#### Sample Response:

```json
{
  "keywords": ["dogs", "people"],
  "results": [
    {
      "objectKey": "image1.jpg",
      "bucket": "smart-photo-search-b2-vandana-2026",
      "labels": ["dog", "park"]
    }
  ]
}
```

---

## 🔧 Environment Variables

| Variable            | Description                            |
| ------------------- | -------------------------------------- |
| BOT_ID              | Amazon Lex bot ID                      |
| BOT_ALIAS_ID        | Lex bot alias ID                       |
| OPENSEARCH_HOST     | OpenSearch endpoint (without https://) |
| OPENSEARCH_INDEX    | Index name (`photos`)                  |
| OPENSEARCH_USERNAME | Master username                        |
| OPENSEARCH_PASSWORD | Master password                        |

---

## 📦 Dependencies

```
boto3
```

---

## ⚠️ Notes

* This function depends on **LF1 (index-photos Lambda)** to populate OpenSearch.
* If no data is indexed, the API will return:

```json
{
  "results": []
}
```

---


