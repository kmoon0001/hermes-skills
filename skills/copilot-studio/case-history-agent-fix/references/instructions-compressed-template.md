# Case History instructions body template (prefer ~6000, max 7000 chars)

Paste as the `instructions: |-` body inside componenttype 15 `GptComponentMetadata`. Pair with `references/response-format-under500.txt` as `responseInstructions:`.

Validated inject 2026-07-17: bot `f19e1c40`, component `cc349f24`, PATCH 204 + publish Succeeded. Instructions body **4641** chars; responseInstructions **495** chars.

Keep all features when compressing: primary directive (text-authoritative vs standards Q), extract list, constraints, 11-part report structure, PT/OT/SLP lens sections with insight+significance, citation/passage/course-phase/follow-up rules, CMS Ch.15 + Jimmo + 42 CFR 483 + APTA/AOTA/ASHA, meds/labs/imaging per-discipline lens, ONC HTI-1 / non-device CDS safety.

Desktop copies from that session:
- `C:\Users\kevin\Desktop\case_history_instructions_compressed.txt`
- `C:\Users\kevin\Desktop\case_history_response_format_under500.txt`
- Backup: `C:\Users\kevin\Desktop\case_history_backup_20260716\live_instructions_before_inject.yaml`

## Dense responseInstructions one-liner (≤500)

```
Friendly scannable markdown; space between sections. Full report: Snapshot → Timeline (Date—Event—Source—Course phase—Follow-up) → Referral → Hx → Course → Function/PLOF → Meds/Labs/Imaging → separate PT, OT, SLP lens sections (Insight + Significance + cites) → D/C → Gaps → 3–6 takeaways. Cite every fact [Source — Date]. Passages (H&P/notes/results): finding, source, date, course phase, follow-up or none. Missing=not found. Simple Q: 2–4 cited bullets. End: DRAFT — CLINICAL REVIEW REQUIRED.
```

## Inject checklist
1. Confirm parent bot ID on type-15 component
2. Backup live data
3. Build full GptComponentMetadata with both fields
4. CRLF line endings
5. PATCH → 204 → read-back
6. `pac copilot publish --bot <guid>`
7. Check `publishedon`; user Shift+Reload Studio tab
