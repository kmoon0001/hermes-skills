# Batch Retry Pattern — Focused re-run of failures

When a batch scraping job finishes with `ERROR:MAX_RETRIES` entries, do not re-run the entire batch. Create a focused retry with escalated parameters.

## Workflow

### 1. Identify the failures

From the results CSV, find rows with `ERROR:MAX_RETRIES`:

```
grep "MAX_RETRIES" results.csv
```

Or use Python for structured analysis:

```python
import csv
with open('results.csv') as f:
    rows = list(csv.DictReader(f, delimiter='|'))
max_retries = [r for r in rows if 'MAX_RETRIES' in r['rating']]
```

### 2. Create a focused input file

Look up each failed entry in the original input file (which has the full pipe-delimited row) and write only those lines to a new file:

```python
with open('original_input.txt') as f:
    input_rows = {line.split('|')[0]: line for line in f}

with open('retry_input.txt', 'w') as f:
    for r in max_retries:
        f.write(input_rows[r['row']])
```

### 3. Escalate retry parameters

Write a modified copy of the batch script with:

| Parameter | Normal run | Retry run |
|-----------|-----------|-----------|
| Max retries | 3 | 5 |
| Page goto timeout | 25s | 30s |
| Post-navigation wait | 3s | 4s |
| Retry backoff base | 5s | 5s × (retry+1) |

Reset the state file so the retry starts fresh on the focused input:

```js
if (fs.existsSync(STATE_FILE)) fs.unlinkSync(STATE_FILE);
fs.writeFileSync(RESULTS_FILE, 'row|name|city|state|rating\n');
```

### 4. Run and merge

Run the retry script in background (may take 15-40 minutes for 20 facilities). When it finishes, merge the new results back into the master results file and final file.

## When to use this pattern

- A batch job completed but some entries hit `MAX_RETRIES`
- The failing entries are concentrated in specific states/regions (suggesting CDN regional rate-limiting)
- Re-running the full batch would waste time on already-successful entries
- The failures are likely transient (CDN blips, temporary rate limits) rather than permanent (404/blocked site)

## Pitfalls

- **Don't run the retry and the main cron simultaneously** — they'll conflict on the state/log/results files. Either pause the cron or use separate output files.
- **If retries still fail with MAX_RETRIES**, the site is persistently blocking those queries. Consider different IP, proxy rotation, or accepting them as permanently unfetchable.
- **Check the retry log for patterns** — if all failures are in one state, the CDN may be rate-limiting that region specifically.
- **Merge results after the retry** — the retry output file doesn't update the main results file automatically.
