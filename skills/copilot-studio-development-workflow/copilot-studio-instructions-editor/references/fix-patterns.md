# Regex Patterns for Topic-Level Fixes

When removing stale constraints from topic YAML in Copilot Studio:

## Remove 800 Char Limit

```javascript
// Remove all variants of 800 char constraint
yaml = yaml.replace(/-\s+Keep[^)]*response under 800 characters[^\n]*\n?/g, '');
yaml = yaml.replace(/-\s+Limit[^)]*800[^\n]*\n?/g, '');
yaml = yaml.replace(/-\s+800[^\n]*\n?/g, '');
```

## Remove Conflicting No-Headers Line

```javascript
yaml = yaml.replace(/-\s+No headers[^\n]*\n?/g, '');
```

## Add Missing EndDialog

For SearchAndSummarizeContent topics missing EndDialog + clearTopicQueue:

```javascript
if (yaml.includes('SearchAndSummarizeContent') && !yaml.includes('EndDialog')) {
  yaml = yaml.replace(
    /(\n\s+actions:[\s\S]*?)(\n\s*(?=kind:|modelDescription:|beginDialog:)|$)/,
    '$1\n    - kind: EndDialog\n      id: done\n      clearTopicQueue: true\n$2'
  );
}
```

## Detection Snippets

```bash
# Check if topic has 800 char limit
npx playwright-cli --session cs eval "(function(){var l=document.querySelectorAll('.view-line');var p=[];for(var x=0;x<l.length;x++)p.push(l[x].textContent);return p.join('\\n').includes('800');})"

# Check if topic has EndDialog  
npx playwright-cli --session cs eval "(function(){var l=document.querySelectorAll('.view-line');var p=[];for(var x=0;x<l.length;x++)p.push(l[x].textContent);return p.join('\\n').includes('EndDialog');})"
```

## Safe Fill via Node.js

Shell escaping multi-line YAML content fails because JSON.stringify converts newlines to `\\n` literals. Use Node.js execSync:

```bash
cd /path/to/home
node -e "
const {execSync} = require('child_process');
const fs = require('fs');
const yaml = fs.readFileSync('_fix.yaml', 'utf8');
execSync('npx playwright-cli --session cs fill e' + process.argv[1] + ' ' + JSON.stringify(yaml),
  {shell:true, timeout:15000});
"
```

Where the ref ID is passed as an argument.