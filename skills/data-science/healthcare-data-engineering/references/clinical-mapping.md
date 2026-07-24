# SLP Missed Opportunity Detection — Clinical Mapping Reference

## Purpose
This file provides detailed MDS/RAI field-to-CMI-category mappings for building deterministic mismatch detection rules. Based on CMS RAI Manual v3.8 (current as of investigation date).

## SLP CMI Categories (Appendix DD Diagnostic Classifications)

### SB — Dysphagia with Nutritional Consequence (PRIMARY SLU OMI DRIVER)
**Clinical meaning:** Patient has documented swallowing difficulty AND nutritional consequence, triggering higher PDPM classification.

**Required evidence chain:**
1. Swallowing difficulty identified → K0300 = 02A or 03A (altered texture diet OR supplement use)
2. Therapeutic diet ordered → K0400 = 02 (therapeutic diet for dysphagia)
3. Eating impairment exists → AA010 ≠ "independent"
4. Nutritional consequence present → BB section has at least one positive indicator

**Key fields and codes:**

| MDS Section | Item | Description | Key Codes for SB |
|-------------|------|-------------|-----------------|
| K0300 | Swallowing Difficulty | Identifies actual/historical swallowing problems | **02A** (history + altered diet/supplement), **03A** (actual difficulty + altered diet/supplement) |
| K0400 | Dysphagia/Therapeutic Diet | Specific therapeutic diet for dysphagia | **02** (therapeutic diet prescribed) |
| AA010 | Level of Eating Assistance | How much help patient needs during meals | A (independent) through G (total dependence) — any ≠ A supports SB |
| BB100 | Caloric Intake Less than Required | Below-calorie intake risk | Positive = 1 |
| BB200 | Protein Intake Less than Required | Below-protein intake risk | Positive = 1 |
| BB300 | Self-dehydration Risk | Dehydration behavior | Positive = 1 |
| BB400 | Unwanted Weight Loss (>5 lbs in 7 days) | Recent significant weight loss | Positive = 1 |

### SE — Urinary/Fecal Incontinence
**Less direct SLP relevance**, but may co-occur with neurogenic swallowing disorders. Focus mainly on G section elimination coding.

### SH — Cognitive Behaviors Impacting Rehab
**Indirect SLP relevance** via cognitive-communication deficits. Check EE section for behavioral patterns and GG functional sections.

### SK — Behavioral Health Issues (Depression/Anxiety)
**Indirect SLP relevance** when mood disorders impact therapy engagement/rehab potential. Check II section for mood/cognition.

---

## MDS Section K Detailed Definitions (RAI v3.8)

### K0300: Swallowing Difficulty
```
01 - No swallowing difficulty present
02 - History of or compensated swallowing difficulty
    A. Altered texture diet AND/OR supplement use for nutrition
    B. Throat-clearing maneuver only
    C. Observed chewing/swallowing problem BUT compensated WITHOUT altered diet/supplement
    D. No evidence of swallowing difficulty BUT previously observed difficulty
03 - Actual swallowing difficulty
    A. Altered texture diet AND/OR supplement use for nutrition  
    B. Throat-clearing maneuver only
    C. Observed chewing/swallowing problem BUT compensated WITHOUT altered diet/supplement
    D. No evidence of swallowing difficulty BUT previously observed difficulty
```

**Critical for OMI:** Codes **02A** and **03A** are the primary triggers — they indicate BOTH a swallowing problem AND an intervention (altered diet or supplements). Missing these when clinically indicated = missed SB opportunity.

### K0400: Dysphagia / Therapeutic Diet
```
01 - None of the following
02 - Therapeutic diet for dysphagia
    A. Thin liquids OR honey-thick liquids OR nectar-thick liquids prescribed
       AND pureed/chopped-modular OR mechanical-soft diet prescribed
    B. Pureed diet alone OR thickened liquids alone prescribed
    C. Mechanical soft diet OR chopped-modular diet alone prescribed
    D. Nectar-thick liquids prescribed ONLY
```

**Critical for OMI:** Code **02** means therapeutic diet is present. The sub-codes (A-D) specify diet texture combinations. Absence of code 02 when SLP recommended diet modification = potential miss.

### K0500-K0699: Other Section K Items
- K0500: Tooth structure/conditions
- K0600: Unwanted weight loss (correlates with BB400)
- K0610/K0620: Artificial teeth status
- These are less directly relevant to SLP OMI but may affect overall PDPM

---

## Primary Deterministic Mismatch Patterns

### Pattern 1: Section K + No Altered Diet
**Trigger:** K0300 = 02A or 03A AND no K0400 = 02 (no therapeutic diet coded)
**Interpretation:** Swallowing difficulty documented with nutritional consequence indicators, but NO formal therapeutic diet order in MDS.
**Likely root cause:** SLP recommended dietary changes but facility didn't translate to MDS coding, or orders were placed but never captured in MDS assessment window.
**Severity:** HIGH — SB CMI category requires both swallowing difficulty AND nutritional consequence. If clinical evidence supports SB but coding doesn't reflect it, revenue impact is real.

### Pattern 2: Altered Diet + No Section K Evaluation
**Trigger:** Diet records show altered texture/thickened liquids BUT K0300 = 01 or 02B/C/D (no nutritional consequence coding)
**Interpretation:** Patient receiving diet interventions without formal swallowing evaluation coded in MDS.
**Likely root cause:** SLP completed evaluation and recommended diet change, but MDS coordinator didn't see/find the eval, or eval fell outside MDS assessment window.
**Severity:** HIGH — could also mean SLP evaluation itself was not initiated despite red flags visible in routine care.

### Pattern 3: NetHealth Eval Exists + PCC No Coding
**Trigger:** NetHealth contains SLP evaluation document recommending intervention AND PCC MDS shows no corresponding coding (K0300/K0400 unchanged)
**Interpretation:** Clinical recommendation exists in rehab system but wasn't reflected in MDS/potentially not implemented.
**Likely root cause:** Communication gap between rehab vendor and facility nursing/MDS staff, or timing mismatch (evaluation done mid-MDS cycle).
**Severity:** MEDIUM-HIGH — depends on whether recommendation was actually implemented outside MDS (i.e., diet changed even if not coded).

### Pattern 4: Strong Clinical Picture + Weak Coding
**Trigger:** Multiple supporting indicators present across sections (K + AA + BB all positive) BUT CMI category missing or understated
**Interpretation:** Comprehensive evidence supports higher CMI classification but coding reflects lower category.
**Example:** K0300=03A, AA010=D (moderate assistance), BB400=positive (weight loss) → STRONG case for SB CMI. If only basic coding submitted, lost revenue.
**Severity:** HIGH — this represents clear undercoding with strong evidentiary support.

---

## Cross-System Data Requirements

### PointClickCare (PCC) Required Fields
| Field | Location | Notes |
|-------|----------|-------|
| MDS Assessment Header | MDS module | Need assessment type (RAI, PSDA, etc.), dates |
| Section K items (K0300-K0699) | MDS module | Most critical area |
| AA Section (AA010+) | MDS module | Eating impairment severity |
| BB Section (BB100-BB500) | MDS module | Nutritional status indicators |
| Therapy encounter dates/types | Therapy/Rehab tab | When were sessions delivered? |
| SLP diagnosis notes | Therapy notes | Free text or structured |
| Care plan activity indicators | Care Plan module | Linked to assessments |
| Diet order modifications | Nutrition/Diet module | When did diet changes occur? |

### NetHealth Rehab Optima Required Fields
| Field | Location | Notes |
|-------|----------|-------|
| SLP evaluation documents | Evaluation module | Structured eval data |
| Diagnosis/coding (ICD-10) | Diagnosis entry | CMI categories |
| Session notes/progress notes | Visit documentation | Visit-level notes |
| Treatment goals/frequencies | Plan of care | Goal statements |
| Functional scores | Assessment module | FIM or similar |
| Physician referral source | Referral module | Why SLP was consulted |

---

## Version Control
- RAI Manual version: v3.8 (current as of this writing)
- Always verify current version before using in production
- New RAI updates can change item definitions, codes, and CMI eligibility

---

Last updated: Initial creation during SLP OMI research project
Next review: Before each major implementation phase
