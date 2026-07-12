# AfricaPEP API Guide

This guide explains how to use the AfricaPEP REST API to screen names, perform batch screening, search the database, retrieve full PEP profiles, and understand the API rate limits.

**Base URL**

```
https://api-pep.patrickaiafrica.com/api/v1
```

**Content Type**

All POST requests should include:

```http
Content-Type: application/json
```

---

# Screening Endpoint

Screen an individual name against the AfricaPEP database using fuzzy matching.

**Endpoint**

```http
POST /screen
```

## Request Body

| Field | Type | Required | Description |
|-------|------|----------|-------------|
| name | string | ✅ | Name to screen |
| threshold | float | No | Minimum similarity score (default depends on API) |
| country | string | No | Restrict matching to a country (ISO country code) |

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
  "total_matches": 1,
  "matches": [
    {
      "id": "123",
      "full_name": "John Dramani Mahama",
      "score": 0.98,
      "pep_tier": 1,
      "risk_level": "High",
      "nationality": "GH"
    }
  ],
  "screening_id": "xxxxxxxx-xxxx-xxxx-xxxx-xxxxxxxxxxxx",
  "screened_at": "2025-03-09T14:30:00Z"
}
```

### Response Fields

| Field | Description |
|-------|-------------|
| query | Original search term |
| threshold | Matching threshold used |
| total_matches | Number of matches found |
| matches | Matching PEP profiles |
| screening_id | Unique screening identifier |
| screened_at | Timestamp of the screening |

---

# Batch Screening

Screen multiple names in a single request.

**Endpoint**

```http
POST /screen/batch
```

A batch request supports up to **50 names**.

## Example Request

```bash
curl -X POST https://api-pep.patrickaiafrica.com/api/v1/screen/batch \
-H "Content-Type: application/json" \
-d '{
  "threshold": 0.75,
  "names": [
    {
      "name": "John Mahama"
    },
    {
      "name": "Paul Kagame"
    },
    {
      "name": "William Ruto"
    }
  ]
}'
```

## Example Response

```json
{
  "total_screened": 3,
  "total_matches": 3,
  "results": [
    {
      "query": "John Mahama",
      "matches": []
    },
    {
      "query": "Paul Kagame",
      "matches": []
    },
    {
      "query": "William Ruto",
      "matches": []
    }
  ]
}
```

---

# Search

Search the AfricaPEP database using full-text search with optional filters.

**Endpoint**

```http
GET /search
```

## Query Parameters

| Parameter | Type | Description |
|----------|------|-------------|
| q | string | Search query (required) |
| country | string | Filter by ISO country code |
| tier | integer | Filter by PEP tier (1–3) |
| active | boolean | Filter active or former PEPs |
| page | integer | Page number (default: 1) |
| limit | integer | Results per page (maximum: 100) |

## Example

```bash
curl "https://api-pep.patrickaiafrica.com/api/v1/search?q=mahama&country=GH&tier=1&page=1&limit=20"
```

## Example Response

```json
{
  "total": 1,
  "page": 1,
  "limit": 20,
  "results": [
    {
      "id": "123",
      "full_name": "John Dramani Mahama",
      "pep_tier": 1,
      "nationality": "GH"
    }
  ]
}
```

---

# Profile Detail

Retrieve the complete profile for a Politically Exposed Person.

**Endpoint**

```http
GET /pep/{pep_id}
```

Replace `{pep_id}` with the profile identifier returned by the screening or search endpoints.

## Example

```bash
curl https://api-pep.patrickaiafrica.com/api/v1/pep/<pep_id>
```

## Example Response

```json
{
  "id": "123",
  "full_name": "John Dramani Mahama",
  "aliases": [],
  "nationality": "GH",
  "pep_tier": 1,
  "risk_level": "High",
  "is_active_pep": true,
  "positions": [
    {
      "title": "President",
      "institution": "Government of Ghana",
      "country": "GH"
    }
  ],
  "sources": [
    {
      "source_type": "Wikidata",
      "source_url": "https://www.wikidata.org/..."
    }
  ]
}
```

The profile endpoint returns detailed information including:

- Personal information
- Known aliases
- Nationality
- PEP tier and risk level
- Current and previous political positions
- Source references
- Active status

---

# Rate Limits

To ensure fair usage, the API applies rate limits to selected endpoints.

| Endpoint | Rate Limit |
|----------|------------|
| POST /screen | **60 requests per minute** |
| POST /screen/batch | **20 requests per minute** |

If a rate limit is exceeded, the API returns an HTTP **429 Too Many Requests** response.

---

# Error Responses

The API uses standard HTTP status codes.

| Status Code | Meaning |
|-------------|---------|
| 200 | Request successful |
| 400 | Invalid request |
| 404 | Resource not found |
| 429 | Rate limit exceeded |
| 500 | Internal server error |
| 503 | Database temporarily unavailable |

---

# Notes

- Use HTTPS for all requests.
- Send request bodies as JSON.
- Batch screening supports a maximum of **50 names** per request.
- Search supports filtering by country, tier, active status, pagination, and page size.
- Refer to the interactive API documentation for the latest request and response schemas.
