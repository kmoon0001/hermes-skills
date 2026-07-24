---
name: copilot-studio-list-kinds
description: "List all available kind discriminator values from the Copilot Studio YAML schema via schema-lookup.bundle.js."
category: copilot-studio
---

# List YAML Kinds

List all available `kind:` discriminator values from the Copilot Studio YAML schema.

## Usage

```bash
node "D:/my agents copilot studio/pipeline/scripts/schema-lookup.bundle.js" kinds [filter]
```

Filter is optional — narrows results to matching kind names.

## Output

JSON array of valid kind values with descriptions. Use these when authoring topic YAML to ensure kind values match the schema.

## Example

```bash
# List all kinds
node schema-lookup.bundle.js kinds

# Filter for send-related kinds
node schema-lookup.bundle.js kinds send
```