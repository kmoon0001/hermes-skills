#!/bin/bash
# Sync Hermes skills from coding-profile to hermes-skills git repo
# Run: bash sync-skills.sh

SRC="$HOME/AppData/Local/hermes/profiles/coding-profile"
DEST="$HOME/hermes-skills"

echo "Syncing Hermes skills from coding-profile..."
rm -rf "$DEST/skills" "$DEST/config"
cp -r "$SRC/skills" "$DEST/skills"
cp "$SRC/config.yaml" "$DEST/config/config.yaml" 2>/dev/null

COUNT=$(find "$DEST/skills" -name 'SKILL.md' | wc -l)
echo "Skills: $COUNT"

cd "$DEST"
git add -A
git commit -m "Sync: $(date '+%Y-%m-%d %H:%M') — $COUNT skills" 2>&1
git push 2>&1
echo "Done."
