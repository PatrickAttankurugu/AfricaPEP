# API Guide

## Screening Endpoint

### POST /api/v1/screen

Screen a single person against the PEP database.

#### Request Body

| Field | Type | Required | Description |
|---------|---------|---------|---------|
| name | string | Yes | Person name to screen |
| country | string | No | ISO country code |
| threshold | float | No | Match threshold (0-1) |

#### Example

```bash
curl -X POST https://api-pep.patrickaiafrica.com/api/v1/screen \
-H "Content-Type: application/json" \
-d '{
  "name": "John Mahama",
  "threshold": 0.75
}'
```

#### Example Response

```json
{
  "matches": []
}
```

---

## Batch Screening

### POST /api/v1/screen/batch

Screen multiple names in a single request.

Maximum batch size: 50 names.

#### Example

```bash
curl -X POST https://api-pep.patrickaiafrica.com/api/v1/screen/batch \
-H "Content-Type: application/json" \
-d '{
  "threshold": 0.75,
  "names": [
    {
      "name": "John Mahama",
      "country": "GH"
    },
    {
      "name": "William Ruto",
      "country": "KE"
    }
  ]
}'
```

---

## Search

### GET /api/v1/search

Search PEP profiles.

#### Query Parameters

| Parameter | Description |
|------------|------------|
| q | Search term |
| country | ISO country code |
| tier | Risk tier |
| active | Active status |
| page | Page number |
| limit | Results per page |

#### Example

```bash
curl "https://api-pep.patrickaiafrica.com/api/v1/search?q=mahama&country=GH"
```

---

## Profile Detail

### GET /api/v1/pep/{pep_id}

Retrieve the complete profile for a PEP.

#### Example

```bash
curl https://api-pep.patrickaiafrica.com/api/v1/pep/PEP-GH-00123
```

Returns detailed profile information including:

- Name
- Aliases
- Nationality
- Positions held
- Sources
- Risk tier
- Active status

---

## Rate Limits

| Endpoint | Limit |
|-----------|--------|
| /screen | 60 requests/minute |
| /screen/batch | 20 requests/minute |