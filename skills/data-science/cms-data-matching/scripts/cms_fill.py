"""
CMS-to-USNews spreadsheet filler.
Downloads all CMS provider ratings, matches facilities by state+fuzzy name,
writes CMS sub-ratings to spreadsheet columns adjacent to US NEWS column.

Usage:
  python cms_fill.py <spreadsheet.xlsx>

Expected sheet layout (inserts CMS columns after US NEWS 2026):
  Col 1: US NEWS 2026 (existing, may already have data)
  Col 2-9: CMS columns (created by this script)
  Col 10+: Original facility data

Configurable column mapping at bottom of script.
"""
import csv, re, openpyxl, sys, urllib.request, json, time
from difflib import SequenceMatcher
from collections import defaultdict

# ── 1. Download CMS data ─────────────────────────────────
def download_cms_data():
    """Download all CMS provider records, return list of dicts with rating fields."""
    total = 14695
    page_size = 1500
    all_rows = []
    headers = None
    
    for page in range((total + page_size - 1) // page_size):
        offset = page * page_size
        url = (f"https://data.cms.gov/provider-data/api/1/datastore/query/4pq5-n9py/0"
               f"?limit={page_size}&offset={offset}&format=csv&results=true"
               f"&count=false&keys=false")
        req = urllib.request.Request(url, headers={"User-Agent": "Mozilla/5.0"})
        with urllib.request.urlopen(req, timeout=30) as resp:
            content = resp.read().decode('utf-8').strip().split('\n')
            reader = csv.reader(content)
            page_rows = list(reader)
            if page == 0:
                headers = page_rows[0]
                all_rows.extend(page_rows[1:])
            else:
                all_rows.extend(page_rows[1:])
        time.sleep(0.3)
    
    # Map to dicts
    result = []
    for row in all_rows:
        d = {}
        for i, h in enumerate(headers):
            d[h] = row[i] if i < len(row) else ''
        result.append(d)
    return result

# ── 2. Name matching ────────────────────────────────────
STOP_WORDS = {'the','and','of','at','for','a','an','in','to','llc','inc','lp','&'}

def norm(name):
    return re.sub(r'\s+', ' ', re.sub(r'[^a-z0-9\s]', '', name.lower())).strip()

def match_score(a, b):
    na, nb = norm(a), norm(b)
    sa, sb = set(na.split()) - STOP_WORDS, set(nb.split()) - STOP_WORDS
    if not sa or not sb:
        return 0.0
    j = len(sa & sb) / len(sa | sb)
    t = SequenceMatcher(None, na, nb).ratio()
    return 0.7 * j + 0.3 * t

def find_match(name, state, cms_by_state, threshold=0.35):
    """Find best CMS match for name in given state."""
    candidates = []
    for p in cms_by_state.get(state, []):
        s = match_score(name, p['Provider Name'])
        if s >= threshold:
            candidates.append((s, p))
    if not candidates:
        return None, 0
    candidates.sort(key=lambda x: -x[0])
    return candidates[0]

# ── 3. Rating field mapping ──────────────────────────────
RATING_FIELDS = [
    ('Overall Rating', 32),
    ('Health Inspection Rating', 34),
    ('Staffing Rating', 42),
    ('QM Rating', 36),
    ('Long-Stay QM Rating', 38),
    ('Short-Stay QM Rating', 40),
]

CMS_TO_USNEWS = {'5': 'High Performing', '4': 'As Expected',
                  '3': 'As Expected', '2': 'As Expected', '1': 'As Expected'}
# Note: This is an approximation. See references/cms-data-structure.md for caveats.

# ── 4. Main ──────────────────────────────────────────────
if __name__ == '__main__':
    path = sys.argv[1] if len(sys.argv) > 1 else r'ENSG Facilities Only 6.1.26.xlsx'
    
    print("Downloading CMS data...")
    cms = download_cms_data()
    print(f"  {len(cms)} records loaded")
    
    # Group by state
    state_abbrev = {'Alabama':'AL','Alaska':'AK','Arizona':'AZ','California':'CA',
        'Colorado':'CO','Idaho':'ID','Iowa':'IA','Kansas':'KS','Nebraska':'NE',
        'Nevada':'NV','Oregon':'OR','South Carolina':'SC','Tennessee':'TN',
        'Texas':'TX','Utah':'UT','Washington':'WA','Wisconsin':'WI'}
    # Add full mapping as needed
    
    cms_by_state = defaultdict(list)
    for p in cms:
        cms_by_state[p['State']].append(p)
    
    print("Matching facilities...")
    wb = openpyxl.load_workbook(path)
    ws = wb.active
    
    # Detect current layout
    headers = [ws.cell(1, c).value for c in range(1, ws.max_column + 1)]
    usnews_col = next((c for c, h in enumerate(headers, 1) if h == 'US NEWS 2026'), None)
    next_col = usnews_col + 1 if usnews_col else ws.max_column + 1
    
    # Add CMS columns
    cms_headers = ['CMS Overall','CMS Health Insp','CMS Staffing','CMS QM',
                   'CMS Long-Stay QM','CMS Short-Stay QM','CMS CCN','CMS Provider Name']
    
    if next_col <= ws.max_column:
        ws.insert_cols(next_col, len(cms_headers))
    for i, h in enumerate(cms_headers):
        ws.cell(1, next_col + i).value = h
    
    # Column positions (after insert)
    col_loc = usnews_col + len(cms_headers) + 1 if usnews_col else 1  # LOCATION
    # Adjust based on actual sheet layout
    
    # Fill
    matched = low_conf = 0
    for row in range(2, ws.max_row + 1):
        name = ws.cell(row, col_loc).value
        state = ws.cell(row, col_loc + 8).value  # adjust offset as needed
        if not name:
            continue
        
        match, score = find_match(name, state, cms_by_state)
        if match:
            ws.cell(row, next_col).value = match.get('Overall Rating', '')
            ws.cell(row, next_col+1).value = match.get('Health Inspection Rating', '')
            ws.cell(row, next_col+2).value = match.get('Staffing Rating', '')
            ws.cell(row, next_col+3).value = match.get('QM Rating', '')
            ws.cell(row, next_col+4).value = match.get('Long-Stay QM Rating', '')
            ws.cell(row, next_col+5).value = match.get('Short-Stay QM Rating', '')
            ws.cell(row, next_col+6).value = match.get('CMS Certification Number (CCN)', '')
            ws.cell(row, next_col+7).value = match.get('Provider Name', '')
            matched += 1
            if score < 0.5:
                low_conf += 1
    
    wb.save(path)
    print(f"\nDone: {matched} matched ({low_conf} low confidence)")
