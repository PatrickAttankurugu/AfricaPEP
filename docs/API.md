# AfricaPEP API Guide

This guide explains how to use the AfricaPEP REST API to screen names, perform batch screening, search the database, retrieve detailed Politically Exposed Person (PEP) profiles, and understand authentication and rate limiting.

## Base URL

```
https://api-pep.patrickaiafrica.com/api/v1
```

## Authentication

The following read-only endpoints are publicly accessible and **do not require** an API key:

- `POST /screen`
- `POST /screen/batch`
- `GET /search`
- `GET /pep/{pep_id}`
- `GET /stats`
- `GET /countries`

All other endpoints require an `X-API-Key` request header.

> **Note**
>
> Swagger UI (`/docs`, `/redoc`, and `/openapi.json`) is intentionally disabled in production. This document serves as the public API reference. Developers running the project locally can access the interactive API documentation.

## Content Type

All POST requests should include:

```http
Content-Type: application/json
```

---

## Screening Endpoint

Screen an individual name against the AfricaPEP database using fuzzy matching.

## Endpoint

```http
POST /screen
```

## Request Body

| Field | Type | Required | Description |
|------|------|----------|-------------|
| name | string | ✅ | Name to screen |
| threshold | float | No | Minimum similarity score used for matching |
| country | string | No | Restrict matching to a specific ISO country code |

### Validation

- `name` must be between **2 and 200 characters**.
- `threshold` defaults to **0.75** when omitted.

## Example Request

```bash
curl -X POST https://api-pep.patrickaiafrica.com/api/v1/screen \
  -H "Content-Type: application/json" \
  -d '{
    "name": "John Mahama",
    "threshold": 0.75
  }'
```

## Example Response

```json
{
  "query": "John Mahama",
  "threshold": 0.75,
  "total_matches": 2,
  "matches": [
    {
      "pep_id": "wd:Q50678",
      "matched_name": "John Mahama",
      "match_score": 1.0,
      "pep_tier": 1,
      "risk_level": "high",
      "is_active": false,
      "nationality": "GH"
    }
  ],
  "screening_id": "4820731b-862d-462f-87f1-90a9d1ce768d",
  "screened_at": "2026-07-12T17:44:39Z"
}
```

## Response Fields

| Field | Description |
|------|-------------|
| query | Original search term |
| threshold | Matching threshold used |
| total_matches | Number of matches found |
| matches | Matching PEP profiles |
| screening_id | Unique screening identifier |
| screened_at | Timestamp of the screening |

---

## Batch Screening

Screen multiple names in a single request.

## Endpoint

```http
POST /screen/batch
```

A batch request accepts a list of **objects**, not plain strings.


### Constraints

- Maximum **50 names** per request.
- Exceeding the limit returns **HTTP 400** with:

```json
{
  "detail": "...",
  "code": "BATCH_SIZE_EXCEEDED"
}
```

- `threshold` defaults to **0.65** if omitted.

## Example Request

```bash
curl -X POST https://api-pep.patrickaiafrica.com/api/v1/screen/batch \
  -H "Content-Type: application/json" \
  -d '{
    "threshold": 0.65,
    "names": [
      {
        "name": "John Mahama"
      },
      {
        "name": "Ngozi Okonjo-Iweala",
        "country": "NG"
      }
    ]
  }'
```

## Example Response

```json
{
  "results": [
    {
      "query_name": "John Mahama",
      "match_count": 2,
      "matches": [
        {
          "pep_id": "wd:Q50678",
          "matched_name": "John Mahama",
          "match_score": 1.0
        }
      ]
    },
    {
      "query_name": "Ngozi Okonjo-Iweala",
      "match_count": 0,
      "matches": []
    }
  ],
  "total_queries": 2,
  "total_matches": 2,
  "screening_id": "48807620-8c97-4d80-8310-ae53ac757d77",
  "screened_at": "2026-07-12T17:45:07Z",
  "threshold": 0.65
}
```

---

## Search

Search the AfricaPEP database using full-text search with optional filters.

## Endpoint

```http
GET /search
```

## Query Parameters

| Parameter | Type | Description |
|----------|------|-------------|
| q | string | Search query (required) |
| country | string | Filter by ISO country code |
| tier | integer | Filter by PEP tier |
| active | boolean | Filter by active status |
| page | integer | Page number |
| limit | integer | Number of results per page |


### Parameter Constraints

- `limit` defaults to **20**.
- Maximum `limit` is **100**.
- `tier` accepts values **1**, **2**, or **3**.

## Example Requests

Search by name:

```bash
curl "https://api-pep.patrickaiafrica.com/api/v1/search?q=mahama"
```

Filter by country:

```bash
curl "https://api-pep.patrickaiafrica.com/api/v1/search?q=mahama&country=GH"
```

Filter by tier:

```bash
curl "https://api-pep.patrickaiafrica.com/api/v1/search?q=mahama&tier=1"
```

## Example Response

```json
{
  "query": "mahama",
  "total": 24,
  "page": 1,
  "limit": 20,
  "results": [
    {
      "id": "wd:Q50678",
      "full_name": "John Mahama",
      "pep_tier": 1,
      "risk_level": "high",
      "is_active": false,
      "nationality": "GH"
    }
  ]
}
```

---

## Profile Detail

Retrieve the complete profile for a Politically Exposed Person.

## Endpoint

```http
GET /pep/{pep_id}
```

Use the `id` returned from the Search endpoint or the `pep_id` returned from the Screening endpoint.

## Example Request

```bash
curl "https://api-pep.patrickaiafrica.com/api/v1/pep/wd:Q50678"
```

## Example Response

```json
{
  "id": "wd:Q50678",
  "full_name": "John Mahama",
  "aliases": [
    "John Mahama",
    "Mahama, John",
    "J. Mahama"
  ],
  "date_of_birth": "1958-11-29",
  "nationality": "GH",
  "pep_tier": 1,
  "risk_level": "high",
  "is_active_pep": false,
  "positions": [
    {
      "title": "President of Ghana",
      "country": "GH",
      "is_current": false
    }
  ],
  "sources": [
    {
      "source_type": "WIKIDATA"
    }
  ]
}
```

The profile endpoint returns detailed information including:

- Personal information
- Known aliases
- Date of birth
- Nationality
- PEP tier
- Risk level
- Current and previous positions
- Source references
- Active status

---

## Rate Limits

The API enforces the following rate limits per client IP:

| Endpoint | Limit |
|----------|-------|
| `POST /screen` | 60 requests per minute |
| `POST /screen/batch` | 20 requests per minute |

When a rate limit is exceeded, the API returns **HTTP 429 Too Many Requests**.

Example response:

```json
{
  "detail": "Rate limit exceeded. Please slow down and retry shortly.",
  "code": "RATE_LIMIT_EXCEEDED"
}
```

Clients should implement retry or exponential backoff when receiving HTTP 429 responses.

---

## Error Responses

The API uses standard HTTP status codes.

| Status | Meaning                         |
| ------ | ------------------------------- |
| 200    | Request successful              |
| 400    | Invalid request                 |
| 401    | Missing or invalid API key      |
| 404    | Resource not found              |
| 429    | Too many requests               |
| 500    | Internal server error           |
| 503    | Service temporarily unavailable |


Error responses use a consistent format:

```json
{
  "detail": "...",
  "code": "..."
}
```



---

## Notes

- Use HTTPS for all requests.
- Send request bodies as JSON.
- Batch screening accepts a list of objects, not plain strings.
- Search supports filtering by country, tier, active status, pagination, and page size.
- This document is the public API reference for production deployments.
