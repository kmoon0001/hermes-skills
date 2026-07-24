# Engine Audit Report Template

Use this structure when delivering an audit report. Keep the reader oriented:

1. Scoped files at the top
2. Findings grouped by audit category (Cat A-E from the skill)
3. Severity tags: **CRITICAL** (live-money threat, stop trading), **MAJOR** (metric distortion, fix before next run), **MINOR** (edge case, document and defer)
4. Summary table at the bottom with every finding + severity + file + line
5. "Clean Bills of Health" table for areas that passed — proves you checked them

## Example: freqtrade Simulation Engine Audit (July 2026)

See `references/freqtrade-engine-audit-july2026.md` for the full report.
