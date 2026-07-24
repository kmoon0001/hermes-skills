# PointClickCare (PCC) API Reference

> Discovered 2025-07-03 via `api-evangelist/pointclickcare` GitHub repo and direct dev portal exploration.
> **Validated as of investigation date.** Always check for version updates before building.

## API Overview

| Property | Value |
|----------|-------|
| Base URL | `https://api.pointclickcare.com/v2` |
| API Version | 2.0.0 |
| Auth | OAuth2 Authorization Code Flow |
| Auth URL | `https://login.pointclickcare.com/oauth2/authorize` |
| Token URL | `https://login.pointclickcare.com/oauth2/token` |
| Scopes | `patient.read`, `clinical.read`, `facility.read` |
| Format | JSON |
| OpenAPI Spec | `https://raw.githubusercontent.com/api-evangelist/pointclickcare/main/openapi/pointclickcare-ehr-openapi.yml` |
| Postman Collection | `https://raw.githubusercontent.com/api-evangelist/pointclickcare/main/collections/pointclickcare-ehr.postman_collection.json` |
| Dev Portal | `https://developer.pointclickcare.com/spa` (SPA, gated behind login) |
| FHIR API | Also available for HL7 FHIR-compliant access |

## Access Tiers

### USCDI Connector (Free)
- Cures Act proprietary APIs (FHIR-based)
- Limited scope but faster approval
- Self-serve documentation + community forums

### Marketplace Partner (Full)
- All proprietary REST APIs
- Development sandbox with UI access
- Real-time webhooks for data change notifications
- Login with PointClickCare + user management
- Dedicated partner manager + support
- Technical validation for app readiness

**Application URL:** `https://developer.pointclickcare.com/spa` → "Apply For Partnership"

### Application Form Details

The "Apply For Partnership" link opens a **Salesforce-hosted intake form** (not the developer SPA). Required fields:

- First/Last Name, Email, Phone
- **Company Name** — this is the blocker for individual/facility-level access without a company backing you
- Job Title, Website
- Full address (Country, Street, City, State/Province, Zip)
- Number of Employees (dropdown: 1-5 through 500+)
- Partner Company Description (free text — describe what you're building)
- **Solution Category:** "Analytics" or "Therapy" are the best fits for clinical audit/review tools
- Whether you have a mutual PCC customer (answer "Yes" if your facility uses PCC)
- Additional comments/needs

This is a full B2B partnership intake form reviewed by PCC's sales team — not instant self-serve. The **USCDI Connector** path (self-serve, Cures Act FHIR APIs only) is the faster alternative for facility-level access without company backing.

## Endpoint Catalog

### Patients
```
GET /patients?facilityId={id}&status=ACTIVE&unitId={uid}&updatedSince={ISO8601}&offset=0&limit=200
    → Paginated list. Patient object: patientId, facilityId, mrn, firstName, lastName,
      dateOfBirth, gender (M/F/U), status (ACTIVE/DISCHARGED/DECEASED/RESPITE/LOA),
      admissionDate, dischargeDate, unitId, roomNumber, bedNumber, payerType
      (MEDICARE/MEDICAID/PRIVATE_PAY/INSURANCE/VA), lastUpdateDatetime

GET /patients/{patientId}
    → Full detail extending Patient with: ssn (last 4), primaryPhysician {npi, name},
      emergencyContact {name, relationship, phone}, allergies[], advanceDirective
      (FULL_CODE/DNR/DNI/COMFORT_CARE/UNKNOWN), language
```

### Assessments (MDS)
```
GET /patients/{patientId}/assessments?assessmentType=MDS-3.0-ADMISSION
    → Filterable by type (MDS-3.0-ADMISSION, FALL-RISK, BRADEN-SKIN, etc.)
    → Assessment object: assessmentId, patientId, assessmentType, assessmentDate,
      status (DRAFT/COMPLETE/LOCKED/TRANSMITTED), completedBy, score (nullable),
      riskLevel (nullable)
    → ⚠️ UNKNOWN: whether response includes detailed MDS section items (K0300, K0400,
      AA, BB) or only summary-level data. The OpenAPI schema shows summary fields only.
      Verify via sandbox after obtaining access.
```

### Diagnoses
```
GET /patients/{patientId}/diagnoses?status=ACTIVE
    → Status filter: ACTIVE/INACTIVE/ALL (default: ACTIVE)
    → Diagnosis object: diagnosisId, patientId, icdCode (e.g. "I10", "E11.9"),
      icdCodeSet (ICD-10-CM/ICD-9-CM), description, diagnosisType
      (PRIMARY/SECONDARY/COMORBIDITY/COMPLICATION), status
```

### Medications
```
GET /patients/{patientId}/medications?status=ACTIVE&startDate={date}&endDate={date}
    → Status filter: ACTIVE/DISCONTINUED/COMPLETED/ON_HOLD

GET /patients/{patientId}/medications/mar
    → Medication Administration Records
```

### Vitals
```
GET /patients/{patientId}/vitals?startDate={date}&endDate={date}&vitalType={type}
    → vitalType: BLOOD_PRESSURE, HEART_RATE, TEMPERATURE, WEIGHT, OXYGEN_SATURATION,
      RESPIRATION_RATE, BLOOD_GLUCOSE
    → VitalSign object: vitalId, patientId, vitalType, recordedDatetime, systolic,
      diastolic, heartRate, temperature, temperatureUnit (F/C), weight, weightUnit
      (LBS/KG), oxygenSaturation
```

### Facilities
```
GET /facilities
    → List of facilities accessible to the authenticated application.
```

## Known Gaps (as of investigation)

1. **MDS Detail Level:** Do assessment responses include section-level items (K0300, K0400, AA, BB)? Or only summary scores/risk levels? The spec suggests summaries only. FHIR API may expose Observation resources for granular items.
2. **Diet/Nutrition Module:** No dedicated diet order endpoint in the v2 REST spec.
3. **Therapy Encounters:** No dedicated endpoint for therapy/rehab sessions or notes. SLP evaluations likely stored as clinical notes, not structured data.
4. **Care Plans:** Mentioned in API description but no specific endpoint in the 697-line spec.

## GitHub Resources

| Repo | What It Provides |
|------|-----------------|
| `api-evangelist/pointclickcare` | Full OpenAPI spec, Postman collection, JSON schema, JSON-LD context |
| `gnickm/pcc-adt-node` | SOAP/HL7 ADT integration server (receives HL7 from PCC, not API client) |
| `wonkas-factory/PointClickCare` | Selenium test example — scraping pattern reference |
| `VorroBG/n8n-nodes-bridgegate` | n8n integration node supporting PCC |
| `wipfli-businesscentral/Wipfli-PCC-PointClickCare-Integration` | Wipfli business central integration |

## Discovery Technique

**Key learning:** PCC's developer portal (`developer.pointclickcare.com/spa`) is a gated SPA that hides API docs behind login. The `api-evangelist` GitHub organization mirrors API documentation for many healthcare platforms including PCC. When investigating a healthcare vendor:

1. Search GitHub: `https://api.github.com/search/repositories?q={vendor}+api&sort=stars`
2. Check `api-evangelist/{vendor}` repos specifically — they maintain OpenAPI specs, Postman collections, and JSON schemas
3. Pull raw OpenAPI YAML to enumerate endpoints, auth flows, and data schemas
4. Cross-reference with the vendor's dev portal for access tiers and pricing

This pattern worked for PCC and may work for other healthcare platforms that gate their docs.
