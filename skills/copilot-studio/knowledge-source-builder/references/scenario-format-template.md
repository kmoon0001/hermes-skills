# Scenario Format Template

Every clinical scenario in a knowledge source must follow this exact format.
The template is designed for Copilot Studio knowledge indexing — consistent
structure improves retrieval accuracy.

## Template

```markdown
### Scenario [N]: [Descriptive Title]
**Domain:** [Governing Body Domain Name]
**Competency:** [Specific competency code, e.g., PC 4, KP 1]
**Difficulty:** [Novice | Moderate | Hard | Expert]
**Format:** [Multiple Choice | Select All That Apply | Free Text | Prioritization | Matching]

**Patient Presentation:**
[2-4 sentences: age, diagnosis, relevant PMH, prior level of function, SNF setting context]

**Scenario:**
[2-4 sentences: the specific clinical situation, assessment findings with specific
numbers/measurements, what clinical decision needs to be made]

**Question:**
[Clear, specific, answerable question. One sentence. For Select All That Apply,
explicitly say "Select ALL that apply."]

**Options:** (for multiple choice)
A) [Plausible but incorrect option that tests a real misconception]
B) [Correct answer — don't make it obviously the right one]
C) [Plausible distractor — common clinical error]
D) [Plausible distractor — different but reasonable approach]

**Correct Answer:** [Letter and text of correct answer]

**Clinical Reasoning:**
[3-5 sentences explaining WHY this is correct. Cite specific clinical guidelines,
evidence, or governing body standards. Reference the competency code, framework
element, or published standard being tested. Include the pathophysiological or
biomechanical rationale where relevant.]

**Incorrect Answer Analysis:**
- A) [Option text]: Why it's wrong — specifically what clinical misconception
  or error this represents
- C) [Option text]: Why it's wrong
- D) [Option text]: Why it's wrong

**SNF Relevance:** [1-2 sentences on why this scenario specifically matters in
the skilled nursing facility context vs. acute care or outpatient]
```

## Format Notes

### Difficulty Distribution
Aim for this distribution across a 35-scenario bank:
- Novice: 3-5 (foundational knowledge, clear-cut presentations)
- Moderate: 15-20 (standard clinical practice, multi-system considerations)
- Hard: 8-12 (multiple comorbidities, atypical presentations, ethical dimensions)
- Expert: 2-4 (rare conditions, nuanced differential diagnosis, practice-edge cases)

### Wrong Answers MUST Be Teaching Tools
Every distractor should represent a REAL clinical misconception:
- A common but outdated practice
- A guideline from a different setting misapplied to SNF
- A reasonable approach that's wrong for THIS specific patient presentation
- A treatment that would be correct for a different phase of recovery

Never use obviously wrong answers ("do nothing," "discharge the patient").
The incorrect answer analysis is where learning happens.

### Clinical Specificity
- Include specific numbers: vital signs, ROM values, outcome measure scores,
  assist levels, distances, weights, lab values
- Use real assessment names: Berg Balance Scale, TUG, Tinetti, MRC scale,
  Modified Ashworth, Borg RPE, etc.
- Reference real governing body standards by code: APTA PC 4, AOTA Standard 2,
  ASHA DCVT Clinical Swallow Assessment section

### SNF Context
Every scenario must justify why it's SNF-specific. Examples:
- "Post-TKA Day 2 mobility progression defines the early SNF rehab trajectory"
- "Weekend handoffs are a major source of adverse events in 24/7 SNF settings"
- "Under PDPM, GG coding directly affects payment — unlike acute care"

## Annotated Example

```markdown
### Scenario 1: Fall Risk Interpretation
**Domain:** Clinical Reasoning — Knowledge for Practice
**Competency:** KP 1, PC 7
**Difficulty:** Moderate
**Format:** Multiple Choice

**Patient Presentation:**
82 y/o female admitted to SNF post-UTI with generalized weakness. PMH: HTN,
OA bilateral knees. Independent prior to hospitalization. Now reports
"feeling unsteady."

**Scenario:**
PT performs standardized assessments: Berg Balance Scale = 42/56, Tinetti
Gait = 8/12, Tinetti Balance = 12/16 (total 20/28), TUG = 18 seconds.
Patient required verbal cues during TUG and lost balance once when turning.
She lives alone in a 2-story home.

**Question:**
Based on these findings, what is the patient's fall risk level and the MOST
appropriate next step?

**Options:**
A) Low fall risk — provide HEP and discharge
B) Moderate fall risk — skilled PT 3x/week for balance and gait training,
   home safety education, recommend grab bars
C) High fall risk — recommend SNF long-term placement
D) Moderate fall risk — restorative nursing program only

**Correct Answer:** B

**Clinical Reasoning:**
Berg score 42/56 is below the 45/56 cutoff for increased fall risk in
community-dwelling older adults. Tinetti total 20/28 falls in the moderate
risk range (19-24). TUG of 18 seconds exceeds the 13.5-second cutoff.
Combined, these indicate moderate fall risk requiring skilled PT intervention.
The patient has potential to improve and return home with modifications.

**Incorrect Answer Analysis:**
- A) Berg 42 is below the 45 threshold for low fall risk. TUG 18s is well
  above age-matched norms. Discharging with HEP alone underestimates risk.
- C) Recommending long-term care after a single UTI-related decline without
  a skilled intervention trial is premature. Patient has improvement potential.
- D) Restorative nursing is appropriate for maintenance, not for active
  decline requiring skilled assessment and progressive intervention.

**SNF Relevance:** Fall risk assessment is the most common PT evaluation in SNFs.
Accurate interpretation of standardized measures determines appropriate level
of care and discharge planning.
```
