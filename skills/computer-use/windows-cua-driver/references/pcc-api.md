# PointClickCare EHR REST API v2

## Source

OpenAPI spec and Postman collection from:
`https://github.com/api-evangelist/pointclickcare`

## API Overview

| Property | Value |
|----------|-------|
| Base URL | `https://api.pointclickcare.com/v2` |
| Auth | OAuth2 Authorization Code Flow (client_credentials also supported) |
| Auth URL | `https://login.pointclickcare.com/oauth2/authorize` |
| Token URL | `https://login.pointclickcare.com/oauth2/token` |
| Scopes | `patient.read`, `clinical.read`, `facility.read` |
| Format | JSON |
| Rate Limit | Unknown (pagination: offset/limit, max 200 per page) |

## Endpoints

```
GET  /patients
     → List residents, filter by facilityId, status, unitId, updatedSince
     → Returns: patientId, facilityId, mrn, firstName, lastName, DOB, status, admit/discharge dates, payer

GET  /patients/{patientId}
     → Full patient detail: demographics + SSN (last 4), physician NPI, emergency contact, allergies, advance directive, language

GET  /patients/{patientId}/assessments
     → Clinical assessments, filter by ?assessmentType=MDS-3.0-ADMISSION
     → Returns: assessmentId, assessmentType, assessmentDate, status, completedBy, score, riskLevel
     → Types: MDS-3.0-ADMISSION, MDS-3.0-QUARTERLY, MDS-3.0-ANNUAL, MDS-3.0-SIGNIFICANT-CHANGE, FALL-RISK, BRADEN-SKIN
     → Statuses: DRAFT, COMPLETE, LOCKED, TRANSMITTED

GET  /patients/{patientId}/diagnoses
     → ICD-10-CM coded diagnoses, filter by ?status=ACTIVE|INACTIVE|ALL
     → Returns: diagnosisId, icdCode, description, diagnosisType (PRIMARY|SECONDARY|COMORBIDITY|COMPLICATION)

GET  /patients/{patientId}/vitals
     → Vital signs with date range and type filters
     → Types: BLOOD_PRESSURE, HEART_RATE, TEMPERATURE, WEIGHT, OXYGEN_SATURATION, RESPIRATION_RATE, BLOOD_GLUCOSE

GET  /patients/{patientId}/medications
     → Medication orders, filter by status (ACTIVE|DISCONTINUED|COMPLETED|ON_HOLD)

GET  /patients/{patientId}/medications/mar
     → Medication administration records

GET  /facilities
     → List authorized facilities
```

## ALSO: FHIR API

Separate HL7 FHIR-compliant API for interoperability — may expose more granular MDS data as FHIR Observation resources.

## Access Tiers

| Tier | What You Get | How |
|------|-------------|-----|
| **USCDI Connector** | Cures Act FHIR APIs, Extended Support | Self-serve signup |
| **Marketplace Partner** | Full proprietary APIs, Sandbox, Webhooks, Login w/ PCC | Apply at `developer.pointclickcare.com/spa` |

## Assessment Data Limitation

The v2 REST API returns assessment **summaries** (type, date, score, status). Detailed MDS section items (K0300 swallowing, K0400 diet texture, AA eating impairment, BB nutritional status) may require:
- A separate detailed assessment endpoint (not in public OpenAPI spec)
- The FHIR API (Observation resources)
- Direct MDS export from PCC UI

## ICD-10 Swallowing/Dysphagia Codes

Codes relevant to SLP CMI SB (dysphagia with nutritional consequence):

```
R13.10, R13.11, R13.12, R13.13, R13.14  # Dysphagia
R13.0, R13.1, R13.2                       # Aphagia/Dysphagia NOS
I69.391, I69.392, I69.393                 # Dysphagia post-stroke
J69.0                                      # Pneumonitis due to food/vomit
```

## GitHub Resources

- `api-evangelist/pointclickcare` — OpenAPI spec, Postman collection, JSON Schema, JSON-LD context
- `gnickm/pcc-adt-node` — PCC ADT SOAP web service (HL7 integration, server-side)
- `VorroBG/n8n-nodes-bridgegate` — n8n integration node supporting PCC
- `wonkas-factory/PointClickCare` — Selenium test example for PCC UI
