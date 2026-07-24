#!/usr/bin/env python3
"""
SLP OMI Pipeline — Starter Template
=====================================
Copy this template and fill in your credentials and clinical mappings.

Adapted from the working pipeline at:
  C:\Users\kevin\Desktop\Research\slp-omi\

Dependencies: pip install httpx playwright
Playwright browsers: python -m playwright install chromium
"""
import asyncio
import csv
import logging
import os
from dataclasses import dataclass, field
from datetime import date, datetime
from enum import Enum
from typing import Optional

import httpx

# ═══════════════════════════════════════════════════════════════════════════
# CONFIGURATION — Fill these in
# ═══════════════════════════════════════════════════════════════════════════

PCC_CLIENT_ID = os.environ.get("PCC_CLIENT_ID", "")
PCC_CLIENT_SECRET = os.environ.get("PCC_CLIENT_SECRET", "")
PCC_FACILITY_ID = os.environ.get("PCC_FACILITY_ID", "")
PCC_BASE_URL = "https://api.pointclickcare.com/v2"

NETHEALTH_USER = os.environ.get("NETHEALTH_USER", "")
NETHEALTH_PASS = os.environ.get("NETHEALTH_PASS", "")

# ICD-10 codes indicating swallowing/dysphagia (add facility-specific codes)
SWALLOWING_ICD_CODES = {
    "R13.10", "R13.11", "R13.12", "R13.13", "R13.14",
    "R13.0", "R13.1", "R13.2",
    "I69.391", "I69.392", "I69.393",
    "J69.0",
}

# MDS K0300 codes indicating swallowing difficulty
SWALLOWING_DIFFICULTY_CODES = {
    "02A", "02B", "02C", "02D",
    "03A", "03B", "03C", "03D",
}

# MDS K0400 codes indicating therapeutic diet
DIET_TEXTURE_CODES = {"02", "02A", "02B", "02C", "02D"}

# ═══════════════════════════════════════════════════════════════════════════
# DATA MODELS
# ═══════════════════════════════════════════════════════════════════════════

class Severity(str, Enum):
    HIGH = "high"
    MEDIUM = "medium"
    LOW = "low"


@dataclass
class Patient:
    patient_id: str = ""
    mrn: str = ""
    first_name: str = ""
    last_name: str = ""


@dataclass
class MDSAssessment:
    assessment_id: str = ""
    patient_id: str = ""
    assessment_type: str = ""
    assessment_date: Optional[date] = None
    section_k_items: dict = field(default_factory=dict)


@dataclass
class Diagnosis:
    diagnosis_id: str = ""
    patient_id: str = ""
    icd_code: str = ""
    description: str = ""


@dataclass
class SLPEvaluation:
    eval_id: str = ""
    patient_mrn: str = ""
    patient_name: str = ""
    eval_date: Optional[date] = None
    cmi_category: Optional[str] = None
    icd_codes: list = field(default_factory=list)
    swallowing_issues: bool = False
    altered_diet_recommended: bool = False
    diet_texture: Optional[str] = None
    recommendations: list = field(default_factory=list)


@dataclass
class Finding:
    patient_mrn: str
    patient_name: str
    mismatch_type: str
    severity: Severity
    description: str
    pcc_evidence: str
    nethealth_evidence: str
    recommendation: str = ""


# ═══════════════════════════════════════════════════════════════════════════
# PCC API CLIENT (minimal — extend as needed)
# ═══════════════════════════════════════════════════════════════════════════

TOKEN_URL = "https://login.pointclickcare.com/oauth2/token"


class PCCClient:
    def __init__(self, client_id: str, client_secret: str):
        self.client_id = client_id
        self.client_secret = client_secret
        self._token: Optional[str] = None
        self._http: Optional[httpx.AsyncClient] = None

    async def authenticate(self):
        self._http = httpx.AsyncClient(timeout=30.0)
        resp = await self._http.post(TOKEN_URL, data={
            "grant_type": "client_credentials",
            "client_id": self.client_id,
            "client_secret": self.client_secret,
            "scope": "patient.read clinical.read facility.read",
        })
        resp.raise_for_status()
        self._token = resp.json()["access_token"]
        logging.info("PCC authenticated")

    async def _get(self, path: str) -> dict:
        if not self._token:
            await self.authenticate()
        headers = {"Authorization": f"Bearer {self._token}"}
        resp = await self._http.get(f"{PCC_BASE_URL}{path}", headers=headers)
        if resp.status_code == 401:
            await self.authenticate()
            headers["Authorization"] = f"Bearer {self._token}"
            resp = await self._http.get(f"{PCC_BASE_URL}{path}", headers=headers)
        resp.raise_for_status()
        return resp.json()

    async def list_patients(self, facility_id: str) -> list[Patient]:
        from urllib.parse import urlencode
        params = urlencode({"facilityId": facility_id, "status": "ACTIVE", "limit": 200})
        result = await self._get(f"/patients?{params}")
        return [
            Patient(
                patient_id=p["patientId"],
                mrn=p.get("mrn", ""),
                first_name=p.get("firstName", ""),
                last_name=p.get("lastName", ""),
            )
            for p in result.get("data", [])
        ]

    async def get_assessments(self, patient_id: str, atype: str = "") -> list[MDSAssessment]:
        path = f"/patients/{patient_id}/assessments"
        if atype:
            path += f"?assessmentType={atype}"
        result = await self._get(path)
        return [
            MDSAssessment(
                assessment_id=a["assessmentId"],
                patient_id=a["patientId"],
                assessment_type=a.get("assessmentType", ""),
            )
            for a in result.get("data", [])
        ]

    async def get_diagnoses(self, patient_id: str) -> list[Diagnosis]:
        result = await self._get(f"/patients/{patient_id}/diagnoses?status=ACTIVE")
        return [
            Diagnosis(
                diagnosis_id=d["diagnosisId"],
                patient_id=d["patientId"],
                icd_code=d.get("icdCode", ""),
                description=d.get("description", ""),
            )
            for d in result.get("data", [])
        ]

    async def close(self):
        if self._http:
            await self._http.aclose()


# ═══════════════════════════════════════════════════════════════════════════
# RULE ENGINE — Extend with your facility's specific rules
# ═══════════════════════════════════════════════════════════════════════════

def check_section_k_no_diet(
    assessment: MDSAssessment,
    diagnoses: list[Diagnosis],
    slp: Optional[SLPEvaluation],
    mrn: str, name: str,
) -> Optional[Finding]:
    """RULE 1: Section K shows swallowing issue but no altered diet documented."""
    k0300 = assessment.section_k_items.get("k0300", "")
    k0400 = assessment.section_k_items.get("k0400", "")

    has_swallowing = (
        k0300 in SWALLOWING_DIFFICULTY_CODES
        or any(d.icd_code[:5] in SWALLOWING_ICD_CODES for d in diagnoses if d.icd_code)
    )
    has_diet = k0400 in DIET_TEXTURE_CODES

    if has_swallowing and not has_diet:
        dx_codes = [d.icd_code for d in diagnoses if d.icd_code]
        slp_confirms = slp and slp.swallowing_issues
        return Finding(
            patient_mrn=mrn, patient_name=name,
            mismatch_type="section_k_no_diet",
            severity=Severity.HIGH if slp_confirms else Severity.MEDIUM,
            description=f"K0300={k0300} but no altered diet (K0400={k0400}). ICD: {', '.join(dx_codes) if dx_codes else 'none'}",
            pcc_evidence=f"K0300={k0300}, K0400={k0400}",
            nethealth_evidence=f"SLP confirms: {slp_confirms}" if slp else "No NetHealth data",
            recommendation="Review SB CMI opportunity — dysphagia with nutritional consequence",
        )
    return None


def check_diet_no_section_k(
    assessment: MDSAssessment,
    slp: Optional[SLPEvaluation],
    mrn: str, name: str,
) -> Optional[Finding]:
    """RULE 2: Altered diet present but no Section K swallowing evaluation."""
    k0300 = assessment.section_k_items.get("k0300", "")
    k0400 = assessment.section_k_items.get("k0400", "")

    if k0400 in DIET_TEXTURE_CODES and k0300 not in SWALLOWING_DIFFICULTY_CODES:
        slp_confirms = slp and slp.swallowing_issues
        return Finding(
            patient_mrn=mrn, patient_name=name,
            mismatch_type="diet_no_section_k",
            severity=Severity.HIGH if slp_confirms else Severity.MEDIUM,
            description=f"Altered diet (K0400={k0400}) but no Section K evaluation (K0300={k0300})",
            pcc_evidence=f"K0400={k0400}, K0300={k0300}",
            nethealth_evidence=f"SLP confirms swallowing issues: {slp_confirms}" if slp else "",
            recommendation="Formal swallowing assessment may be warranted",
        )
    return None


def check_slp_not_in_pcc(
    assessment: MDSAssessment,
    diagnoses: list[Diagnosis],
    slp: SLPEvaluation,
    mrn: str, name: str,
) -> Optional[Finding]:
    """RULE 3: SLP evaluation findings not reflected in PCC MDS."""
    if not slp.swallowing_issues and not slp.cmi_category:
        return None

    in_mds = (
        any(d.icd_code[:5] in SWALLOWING_ICD_CODES for d in diagnoses if d.icd_code)
        or assessment.section_k_items.get("k0300", "") in SWALLOWING_DIFFICULTY_CODES
    )

    if not in_mds:
        return Finding(
            patient_mrn=mrn, patient_name=name,
            mismatch_type="slp_eval_not_in_mds",
            severity=Severity.HIGH,
            description=f"SLP found: CMI={slp.cmi_category}, swallowing={slp.swallowing_issues}, diet={slp.diet_texture}. Not in MDS.",
            pcc_evidence="MDS does not reflect SLP findings",
            nethealth_evidence=f"SLP eval: CMI={slp.cmi_category}, ICD={slp.icd_codes}",
            recommendation="Update MDS to reflect SLP evaluation findings",
        )
    return None


# Register your rules here
RULES = [
    check_section_k_no_diet,
    check_diet_no_section_k,
    check_slp_not_in_pcc,
]


# ═══════════════════════════════════════════════════════════════════════════
# MAIN PIPELINE
# ═══════════════════════════════════════════════════════════════════════════

async def run_pipeline(
    facility_id: str,
    pcc_client_id: str = "",
    pcc_client_secret: str = "",
    output_path: str = "findings.csv",
) -> list[Finding]:
    """Run the full OMI pipeline and write findings to CSV."""
    all_findings: list[Finding] = []

    # Phase 1: Pull PCC data
    if pcc_client_id:
        pcc = PCCClient(pcc_client_id, pcc_client_secret)
        try:
            patients = await pcc.list_patients(facility_id)
            logging.info("PCC: %d patients", len(patients))

            for patient in patients:
                assessments = await pcc.get_assessments(patient.patient_id, "MDS-3.0-ADMISSION")
                diagnoses = await pcc.get_diagnoses(patient.patient_id)

                for assessment in assessments:
                    name = f"{patient.first_name} {patient.last_name}"
                    for rule in RULES:
                        finding = rule(assessment, diagnoses, None, patient.mrn, name)
                        if finding:
                            all_findings.append(finding)

            await pcc.close()
        except Exception as e:
            logging.error("PCC phase failed: %s", e)

    # Phase 2: NetHealth scraping would go here
    # See nethealth_scraper.py in the full project

    # Phase 3: Output
    if all_findings:
        with open(output_path, "w", newline="", encoding="utf-8") as f:
            writer = csv.writer(f)
            writer.writerow(["MRN", "Name", "Type", "Severity", "Description", "PCC", "NetHealth", "Recommendation"])
            for finding in sorted(all_findings, key=lambda x: 0 if x.severity == Severity.HIGH else 1):
                writer.writerow([
                    finding.patient_mrn, finding.patient_name,
                    finding.mismatch_type, finding.severity.value,
                    finding.description, finding.pcc_evidence,
                    finding.nethealth_evidence, finding.recommendation,
                ])
        logging.info("Wrote %d findings to %s", len(all_findings), output_path)

    return all_findings


if __name__ == "__main__":
    logging.basicConfig(level=logging.INFO, format="%(asctime)s [%(levelname)s] %(message)s")
    findings = asyncio.run(run_pipeline(
        facility_id=PCC_FACILITY_ID,
        pcc_client_id=PCC_CLIENT_ID,
        pcc_client_secret=PCC_CLIENT_SECRET,
    ))

    high = sum(1 for f in findings if f.severity == Severity.HIGH)
    print(f"\nDone. {len(findings)} findings ({high} HIGH severity).")
