# TARF (Time Adjustment Request Form) Field Coordinates

Form: **SC RESOURCE Time Adjustment Request Form** (Rev. 8/2023)
Dimensions: 612 × 792 pt (US Letter)
Template: `C:\Users\kevin\Desktop\Healthcare_SNF_Docs\blank tarf.pdf`

## Employee Info (pre-filled constants)
| Field | x | y | Value |
|---|---|---|---|
| employee_name | 170 | 167 | Kevin Moon |
| position | 135 | 190 | SLP |
| employee_id | 370 | 190 | 123713644 |

## Shift Worked Information (critical time fields)
These are the fields that cause the sequential-fill bug. Always map by position.

| Field | x | y | Notes |
|---|---|---|---|
| date_of_adjustment | 183 | 483 | Date field |
| time_in | 310 | 509 | A.M. Shift → Time In |
| meal_start | 330 | 526 | Meal Period start (P.M. Shift) |
| meal_end | 407 | 526 | Meal Period end (P.M. Shift) |
| time_out | 320 | 543 | Night Shift → Time Out |
| total_hours | 368 | 560 | Auto-calculated |

**Smart mapping rule:**
- Time In and Time Out are ALWAYS filled
- Meal Period fields ONLY filled when meal data provided
- Total Hours = (Time Out - Time In) - (Meal End - Meal Start) when meal given

## Checkboxes (draw "X" at position)
| Field | x | y | Label |
|---|---|---|---|
| cb_missed_punch | 95 | 241 | Missed Punch |
| cb_new_hire | 95 | 258 | New Hire (Badge Pending) |
| cb_forgot_punch | 95 | 275 | Forgot to punch |
| cb_lost_badge | 95 | 292 | Lost Badge |
| cb_meal_not_taken | 95 | 310 | All or Part of a Meal Not Taken |
| cb_meeting_training | 95 | 372 | Meeting & Training Time |
| cb_travel_time | 95 | 410 | Travel Time |
| cb_dept_transfer | 95 | 448 | Department Transfer |
| cb_am_shift | 95 | 506 | A.M. Shift — **pre-printed** on blank form, requires white-out |
| cb_pm_shift | 95 | 524 | P.M. Shift |
| cb_night_shift | 95 | 542 | Night Shift |

## Comment Lines
| Field | x | y | Section |
|---|---|---|---|
| comments_meal | 186 | 333 | "All or Part of a Meal Not Taken" |
| comments_meeting | 186 | 371 | "Meeting & Training Time" |
| comments_travel | 186 | 409 | "Travel Time" |

## Dept Transfer
| Field | x | y |
|---|---|---|
| dept_from | 270 | 428 |
| dept_to | 408 | 428 |

## Signatures
| Field | x | y | Notes |
|---|---|---|---|
| employee_signature | 195 | 678 | Pre-filled as "Kevin Moon" |
| employee_date | 430 | 678 | **Leave blank** (per user request) |
| supervisor | 150 | 703 | Optional |
| supervisor_date | 432 | 703 | Optional |

## Shift Auto-Detection Logic
Based on Time In hour (mutually exclusive):
- 6:00 - 11:59 → am_shift
- 12:00 - 17:59 → pm_shift
- 18:00 - 5:59 → night_shift

## Script
Full TARF filler script: `C:\Users\kevin\Desktop\tarf_filler.py`
Uses virtual env: `C:\Users\kevin\AppData\Local\hermes\profiles\coding-profile\var\tarf_venv\Scripts\python.exe`
