# Mismatch Rule Framework

> Extensible templates for building deterministic mismatch detection rules across healthcare data systems.
> Rules should be OBJECTIVE — flag data inconsistencies, not subjective clinical judgments.

## Rule Anatomy

Every rule has:
1. **Trigger:** The condition that activates the rule
2. **Evidence:** What data fields are checked
3. **Flag:** What gets raised (severity + type + reasoning)
4. **Source:** Which system(s) the data comes from

## Rule Template

```python
from dataclasses import dataclass
from enum import Enum
from typing import Optional

class Severity(Enum):
    HIGH = "high"        # Clear mismatch, likely revenue impact
    MEDIUM = "medium"    # Probable mismatch, needs review
    LOW = "low"          # Possible issue, low confidence

@dataclass
class Flag:
    patient_id: str
    patient_name: str
    rule_id: str
    severity: Severity
    description: str
    evidence: dict        # {field: value} pairs that triggered the rule
    recommendation: str

class BaseRule:
    """Base class for all mismatch rules."""
    
    rule_id: str
    severity: Severity
    description: str
    
    def check(self, patient_data: dict) -> Optional[Flag]:
        """Return Flag if rule triggers, None if clean."""
        raise NotImplementedError
```

## Pattern 1: Cross-Field Consistency (same system)

**Rule:** Two fields in the same system that should correlate don't.

```python
class CrossFieldConsistencyRule(BaseRule):
    """Field A indicates condition X, but Field B (which should co-occur) is absent."""
    
    def __init__(self, field_a: str, values_a: list, field_b: str, values_b: list):
        self.field_a = field_a
        self.values_a = values_a
        self.field_b = field_b
        self.values_b = values_b
    
    def check(self, data: dict) -> Optional[Flag]:
        a_matches = data.get(self.field_a) in self.values_a
        b_matches = data.get(self.field_b) in self.values_b
        
        if a_matches and not b_matches:
            return Flag(
                rule_id=self.rule_id,
                severity=self.severity,
                description=f"{self.field_a}={data[self.field_a]} but {self.field_b} not in {self.values_b}",
                evidence={self.field_a: data[self.field_a], self.field_b: data[self.field_b]},
                recommendation=f"Verify whether {self.field_b} should be coded given {self.field_a}"
            )
        return None
```

**Example (SLP):** K0300 swallowing difficulty coded (02A) but K0400 therapeutic diet NOT coded (01 instead of 02).

## Pattern 2: Cross-System Document Mismatch

**Rule:** System A has a document/recommendation that System B doesn't reflect.

```python
class CrossSystemDocumentRule(BaseRule):
    """System A has a clinical document/recommendation, but System B shows no corresponding record."""
    
    def __init__(self, system_a_field: str, system_b_field: str, match_key: str):
        self.system_a_field = system_a_field
        self.system_b_field = system_b_field
        self.match_key = match_key
    
    def check(self, merged_data: dict) -> Optional[Flag]:
        a_value = merged_data.get(self.system_a_field)
        b_value = merged_data.get(self.system_b_field)
        
        if a_value and not b_value:
            return Flag(
                rule_id=self.rule_id,
                severity=self.severity,
                description=f"{self.system_a_field} exists in source A but {self.system_b_field} missing in source B",
                evidence={"source_a": a_value, "source_b": b_value},
                recommendation=f"Cross-reference {self.system_a_field} from system A with system B coding"
            )
        return None
```

**Example (SLP):** NetHealth has SLP evaluation recommending diet change, but PCC MDS K0400 shows no therapeutic diet.

## Pattern 3: Clinical Picture vs Coding Gap

**Rule:** Multiple clinical indicators support a higher CMI category than what's coded.

```python
class ClinicalPictureVsCodingRule(BaseRule):
    """N indicators across M sections support category C, but coding shows lower/absent category."""
    
    def __init__(self, indicator_fields: list, min_indicators: int, expected_category: str, actual_category_field: str):
        self.indicator_fields = indicator_fields
        self.min_indicators = min_indicators
        self.expected_category = expected_category
        self.actual_category_field = actual_category_field
    
    def check(self, data: dict) -> Optional[Flag]:
        positive_indicators = sum(1 for f in self.indicator_fields if data.get(f))
        actual = data.get(self.actual_category_field)
        
        if positive_indicators >= self.min_indicators and actual != self.expected_category:
            return Flag(
                rule_id=self.rule_id,
                severity=self.severity,
                description=f"{positive_indicators}/{len(self.indicator_fields)} indicators support {self.expected_category} but coded as {actual}",
                evidence={"indicators": {f: data[f] for f in self.indicator_fields if data.get(f)},
                         "actual_category": actual},
                recommendation=f"Review whether {self.expected_category} CMI classification is warranted"
            )
        return None
```

**Example (SLP):** K0300=03A + AA010=D + BB400=positive → STRONG SB evidence, but CMI shows basic coding only.

## Pattern 4: Temporal Consistency

**Rule:** Events that should happen in a specific order don't.

```python
class TemporalConsistencyRule(BaseRule):
    """Event A should precede event B within window W days."""
    
    def __init__(self, event_a_date_field: str, event_b_date_field: str, max_days: int):
        self.event_a_date_field = event_a_date_field
        self.event_b_date_field = event_b_date_field
        self.max_days = max_days
    
    def check(self, data: dict) -> Optional[Flag]:
        from datetime import datetime
        
        a_date = data.get(self.event_a_date_field)
        b_date = data.get(self.event_b_date_field)
        
        if a_date and b_date:
            a = datetime.fromisoformat(a_date)
            b = datetime.fromisoformat(b_date)
            if b < a or (b - a).days > self.max_days:
                return Flag(
                    rule_id=self.rule_id,
                    severity=self.severity,
                    description=f"{self.event_a_date_field} ({a_date}) and {self.event_b_date_field} ({b_date}) out of expected order/window",
                    evidence={"event_a_date": a_date, "event_b_date": b_date, "max_window_days": self.max_days},
                    recommendation="Verify assessment timing and re-assess if needed"
                )
        return None
```

**Example (SLP):** Diet order changed AFTER MDS assessment window closed — change can't be captured in current MDS coding cycle.

## Rule Scoring and Prioritization

When multiple rules fire for the same patient, score and sort:

```python
def score_flags(flags: list[Flag]) -> list[Flag]:
    """Score and sort flags by priority."""
    severity_weight = {Severity.HIGH: 3, Severity.MEDIUM: 2, Severity.LOW: 1}
    
    for flag in flags:
        evidence_count = len(flag.evidence)
        flag._score = severity_weight[flag.severity] * evidence_count
    
    return sorted(flags, key=lambda f: f._score, reverse=True)
```

## Output Format

```csv
patient_id,patient_name,rule_id,severity,description,recommendation
P12345,Smith John,RULE-001,HIGH,K0300=02A but K0400=01,Review diet coding
P12345,Smith John,RULE-003,HIGH,3/4 indicators support SB,Review CMI classification
P67890,Doe Jane,RULE-002,MEDIUM,NetHealth eval exists but no PCC coding,Cross-reference systems
```

## Adding New Rules

1. Identify a deterministic pattern (this field should equal that field, this document should produce that code, etc.)
2. Choose the closest pattern template above
3. Implement `check()` method
4. Test against known positive and negative cases
5. Add rule ID and description to the catalog

**Rule: never add a rule that requires subjective clinical judgment.** If you can't express it as field comparison logic, it's not ready for automation.
