# Batch Topic Fix Workflow

## Complete Workflow (Validated: OT 10/10, PT 2/2)

### Phase 1: Extract and Analyze

```bash
# Extract template (works for agents with <60 components)
pac copilot extract-template --bot "<botId>" --templateFileName "<agent>_template.yaml" --overwrite

# OT: 44 components ✅, PT: 48 ✅, SLP: 64 ❌ crashes, TDA: 67 ❌ crashes
```

### Phase 2: Find Issues

```python
# Scan for 800-char limits
with open('ot_template.yaml', 'r') as f:
    lines = f.readlines()

starts = [i for i, line in enumerate(lines) if line.startswith('  - kind:') and i > 10]

for idx in range(len(starts)):
    start = starts[idx]
    end = starts[idx + 1] if idx + 1 < len(starts) else len(lines)
    block = ''.join(lines[start:end])
    
    name = None
    for bl in lines[start:end]:
        if 'displayName:' in bl:
            name = bl.strip().split(':', 1)[1].strip().strip('"')
    
    if '800 character' in block.lower() or 'under 800' in block.lower():
        print(f"ISSUE: {name}")
```

### Phase 3: Generate Fix Files

```python
# Replace 800-char limits
fixed = content.replace(
    'Keep response under 800 characters.',
    'Be concise but complete. Prioritize accuracy over strict length limits.'
)

# Extract each topic block and save as individual file
for idx in range(len(starts)):
    start = starts[idx]
    end = starts[idx + 1] if idx + 1 < len(starts) else len(lines)
    block = ''.join(lines[start:end])
    
    if has_issue(block):
        safe_name = name.lower().replace(' ', '_')
        with open(f'fix_{safe_name}.yaml', 'w') as f:
            f.write(block)
```

### Phase 4: Get Topic GUIDs

```javascript
// From authenticated browser session
const filter = `_parentbotid_value eq '${botId}' and componenttype eq 9`;
const url = `/api/data/v9.2/botcomponents?$select=name,botcomponentid&$filter=${encodeURIComponent(filter)}&$top=100`;
```

### Phase 5: Inject via GUID URLs

```javascript
for (const [name, guid, yamlFile] of topics) {
  const url = `${BASE}/adaptive/${guid}`;
  await page.goto(url, { waitUntil: 'domcontentloaded', timeout: 15000 }).catch(() => {});
  
  // Wait for Save button (poll up to 30s)
  let found = false;
  for (let i = 0; i < 15; i++) {
    await sleep(2000);
    found = await page.evaluate(() => 
      Array.from(document.querySelectorAll('button')).some(b => b.textContent.trim() === 'Save')
    );
    if (found) break;
  }
  
  if (!found) { console.log('SKIP:', name); continue; }
  
  // More → Open code editor → Inject → Save
  await page.evaluate(() => {
    document.querySelectorAll('button').forEach(b => {
      if (b.textContent.trim() === 'More') b.click();
    });
  });
  await sleep(1500);
  
  await page.evaluate(() => {
    document.querySelectorAll('[role=menuitem]').forEach(el => {
      if (el.textContent.trim() === 'Open code editor') el.click();
    });
  });
  await sleep(5000);
  
  // Inject via textarea
  const yaml = fs.readFileSync(yamlFile, 'utf8');
  await page.evaluate((y) => {
    const ta = document.querySelector('textarea');
    if (ta) {
      const setter = Object.getOwnPropertyDescriptor(HTMLTextAreaElement.prototype, 'value').set;
      setter.call(ta, y);
      ta.dispatchEvent(new Event('input', { bubbles: true }));
    }
  }, yaml);
  
  // Unlock save
  await page.keyboard.press('End');
  await page.keyboard.type(' ', { delay: 50 });
  await sleep(200);
  await page.keyboard.press('Backspace');
  await sleep(500);
  
  // Save
  await page.evaluate(() => {
    document.querySelectorAll('button').forEach(b => {
      if (b.textContent.trim() === 'Save') b.click();
    });
  });
  await sleep(3000);
}
```

### Phase 6: Publish

```javascript
await page.goto(`${BASE}/overview`, { waitUntil: 'domcontentloaded', timeout: 15000 }).catch(() => {});
await sleep(12000);
await page.evaluate(() => {
  document.querySelectorAll('button').forEach(b => {
    if (b.textContent.trim() === 'Publish') b.click();
  });
});
await sleep(3000);
await page.evaluate(() => {
  document.querySelectorAll('button').forEach(b => {
    if (b.textContent.trim().toLowerCase() === 'publish') b.click();
  });
});
await sleep(15000);
```

## Fallback: Desktop File Delivery (when CDP automation fails)

When CDP injection is unreliable (Monaco corruption, ECONNREFUSED, SPA load failures, auth loss), switch to Desktop file delivery. This is the ONLY reliable path for Monaco code editor updates — the skill validates this repeatedly.

### Python: Write files to Desktop
```python
import os
desktop = os.path.expanduser("~/Desktop")
with open(os.path.join(desktop, f"{topic_name}_fixed.mcs.yml"), "w") as f:
    f.write(yaml_content)
```

### Open Explorer for double-click
```powershell
powershell.exe -Command "Start-Process explorer 'C:\Users\kevin\Desktop'"
```

### User workflow (per topic, ~15s)
1. Open topic → **More → Open code editor**
2. **Ctrl+A → Delete** (clear existing)
3. **Alt+Tab** to Explorer → double-click `_fixed.mcs.yml` → **Ctrl+A → Ctrl+C**
4. **Alt+Tab** back → **Ctrl+V** (paste)
5. Type **space** then **Backspace** (triggers React dirty state → enables Save)
6. **Save**
7. Click topic name dropdown → select next topic → repeat

### ⚠️ git-bash Notepad wrapper
`notepad.exe` from git-bash may open a git wrapper script (shows `unix2dos.exe`/`dos2unix.exe`) instead of the file. **This happens because git installs a `notepad` shim in MSYS.** Workaround:
- Open files directly from Explorer (double-click) — bypasses the shim
- Or use full Windows path: `powershell.exe -Command "Start-Process notepad 'C:\full\path\file.yml'"`
