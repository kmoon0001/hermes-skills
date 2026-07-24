#!/usr/bin/env node
// topic_lint.cjs - Lint Copilot Studio topic YAML before publish
//
// Authoritative source: Microsoft Learn
//  - botcomponent table: https://learn.microsoft.com/power-apps/developer/data-platform/reference/entities/botcomponent
//  - topic authoring:      https://learn.microsoft.com/microsoft-copilot-studio/authoring-create-edit-topics
//  - system topics / fall-back: https://learn.microsoft.com/microsoft-copilot-studio/authoring-system-topics
//
// Hard rules this linter enforces (each maps to a known Copilot Studio failure mode):
//  R1  Topic name cannot contain a period (`.`) — export solution will fail.
//      Source: authoring-create-edit-topics ("Avoid using periods in topic names").
//  R2  Custom topic must not declare `beginDialog.kind: OnUnknownIntent` —
//      that is a system-topic trigger and overrides the platform fallback,
//      which breaks publish on some content combinations.
//  R3  Empty `actions:` array (no body nodes) — empty AdaptiveDialog crashes publish.
//  R4  Any Question node must be followed by a Condition/branch or EndDialog —
//      orphan Question nodes break multi-turn eval (this is the 95->12% regression mode).
//  R5  Trigger phrase overlap across topics > 60% (token Jaccard) → routing drift.
//      Known to cause unpredictable topic-firing across eval runs.
//  R6  Topic must end with EndDialog (or be cleanly terminated) — required structure.
//  R7  Topic must declare at least 3 trigger phrases (too few yields low NLU confidence).
//
// Usage:
//   node topic_lint.cjs <directory-with-yaml-files>
//   node topic_lint.cjs file1.yaml file2.yaml ...
//   node topic_lint.cjs          (lints ./topic_templates default)
//
// Exit codes:
//   0 = clean (lint pass)
//   1 = blocking errors (publish must not proceed)
//   2 = warnings only (publish may proceed, but reviewer should look)

'use strict';

const fs = require('fs');
const path = require('path');

// ---------- YAML loader ----------
// js-yaml is the canonical deep parser. Hand-rolls the parsing logic
// wouldn't get us branch-supporting conditional blocks right; we tried.
const yaml = require('js-yaml');

function parseYaml(text) {
  // Multi-doc via loadAll if we have proper `---` separators
  if (text.indexOf('\n---') !== -1 && /^---\s*$/m.test(text)) {
    return yaml.loadAll(text);
  }
  // Try strict single-doc first
  try {
    return [yaml.load(text) || {}];
  } catch (e) {
    // Fallback: split hand-concatenated docs (no `---` separators but multiple
    // top-level `kind: AdaptiveDialog` resets, like all_topics_consolidated.yaml).
    // We split on a newline at column 0 that's followed by a top-level key.
    const docs = [];
    const lines = text.split(/\r?\n/);
    let buf = [];
    for (const line of lines) {
      // Top-level key (no leading whitespace) starts a new doc if we already have one
      if (/^[A-Za-z_]/.test(line) && buf.length > 0) {
        const block = buf.join('\n');
        try { const d = yaml.load(block); if (d) docs.push(d); } catch (_) { docs.push({ _parseError: true, _raw: block.slice(0, 200) }); }
        buf = [];
      }
      buf.push(line);
    }
    if (buf.length) {
      const block = buf.join('\n');
      try { const d = yaml.load(block); if (d) docs.push(d); } catch (_) { docs.push({ _parseError: true, _raw: block.slice(0, 200) }); }
    }
    if (!docs.length) throw e;  // re-raise original if the split rescued nothing
    return docs;
  }
}

// ---------- Lint rules ----------
function jaccardTokens(a, b) {
  const ta = new Set(a.toLowerCase().split(/\W+/).filter(Boolean));
  const tb = new Set(b.toLowerCase().split(/\W+/).filter(Boolean));
  if (!ta.size || !tb.size) return 0;
  let inter = 0;
  for (const t of ta) if (tb.has(t)) inter++;
  return inter / (ta.size + tb.size - inter);
}

function walkActions(actions) {
  const out = [];
  function walk(nodes, pathSoFar) {
    if (!Array.isArray(nodes)) return;
    for (let idx = 0; idx < nodes.length; idx++) {
      const n = nodes[idx] || {};
      const here = pathSoFar + '[' + idx + ']';
      out.push(Object.assign({ _path: here }, n));
      if (n.actions) walk(n.actions, here + '.actions');
      if (n.elseActions) walk(n.elseActions, here + '.elseActions');
    }
  }
  walk(actions, 'actions');
  return out;
}

function lintTopic(name, doc) {
  const errors = [];
  const warnings = [];

  if (!doc || typeof doc !== 'object') {
    errors.push({ rule: 'R0', msg: 'Empty or unparseable document' });
    return { errors, warnings };
  }

  // R1: topic display name can't have a period (MS Learn rule on the bot name,
  // not the filename — filenames are fine. We strip extension and look for
  // either a `name:` field or a `# TOPIC: ...` comment in the file.)
  let topicName = doc && (doc.name || doc.displayName);
  if (!topicName) {
    // Look for a "# TOPIC: Foo" marker near top of the source file (multi-doc files only have it as comment)
    // We rely on the filename sans extension for single-doc files.
    topicName = name.replace(/\.(ya?ml)$/i, '');
  }
  if (/\./.test(topicName)) {
    errors.push({ rule: 'R1', msg: `Topic name "${topicName}" contains a period — periods in topic names break solution export.` });
  }

  // R2: forbid OnUnknownIntent in custom topics (system-topic trigger)
  const bdKind = doc.beginDialog && doc.beginDialog.kind;
  if (bdKind === 'OnUnknownIntent') {
    errors.push({ rule: 'R2', msg: 'beginDialog.kind: OnUnknownIntent — overrides platform fallback and breaks publish on topic-content overlap. Use a custom topic name + a normal OnRecognizedIntent trigger instead.' });
  }

  // R3: actions array must be non-empty
  const actions = doc.beginDialog && doc.beginDialog.actions;
  if (!Array.isArray(actions) || actions.length === 0) {
    errors.push({ rule: 'R3', msg: 'beginDialog.actions is empty — empty AdaptiveDialog crashes publish.' });
  }

  // R4: every Question node must have a downstream branch (Condition/EndDialog)
  const flat = walkActions(actions);
  for (let i = 0; i < flat.length; i++) {
    const n = flat[i];
    if (n.kind === 'Question') {
      const hasBranch = (n.actions && n.actions.length) || n.property || n.elseActions;
      if (!hasBranch) {
        errors.push({ rule: 'R4', msg: `Orphan Question node at ${n._path} (no property/condition/branch) — known cause of SR 95→12%. Add an EndDialog or Condition after it.` });
      }
    }
    if (n.kind === 'SearchAndSummarizeContent' || n.kind === 'SendActivity') {
      // Look ahead — must be followed by EndDialog (last action) or a branching shape
      const next = flat[i + 1];
      if (next && next.kind !== 'EndDialog' && next.kind !== 'Condition' && next.kind !== 'Question') {
        warnings.push({ rule: 'R4w', msg: `${n.kind} at ${n._path} not followed by EndDialog (next is ${next.kind}) — possible orphan response.` });
      }
    }
  }

  // R6: must end with EndDialog
  if (Array.isArray(actions) && actions.length) {
    const last = actions[actions.length - 1];
    if (last && last.kind !== 'EndDialog') {
      warnings.push({ rule: 'R6', msg: `Last action is ${last.kind}, not EndDialog — topic should terminate cleanly.` });
    }
  }

  // R7: trigger phrase count
  const triggers = (doc.beginDialog && doc.beginDialog.intent && doc.beginDialog.intent.triggerQueries) || [];
  if (Array.isArray(triggers) && triggers.length < 3) {
    warnings.push({ rule: 'R7', msg: `Only ${triggers.length} trigger phrases — fewer than 3 leads to low NLU confidence.` });
  }

  return { errors, warnings, triggers: Array.isArray(triggers) ? triggers : [] };
}

// ---------- Driver ----------
function main() {
  const args = process.argv.slice(2);
  const inputs = args.length ? args : ['D:/my agents copilot studio/topic_templates'];

  const files = [];
  for (const a of inputs) {
    const stat = fs.statSync(a);
    if (stat.isDirectory()) {
      for (const f of fs.readdirSync(a)) {
        if (/\.(yml|yaml)$/i.test(f)) files.push(path.join(a, f));
      }
    } else {
      files.push(a);
    }
  }

  console.log(`topic_lint: scanning ${files.length} file(s)\n`);

  const results = [];
  let totalErrors = 0;
  let totalWarnings = 0;

  // First pass — per-topic lint
  for (const f of files) {
    let parsed = [];
    try {
      const text = fs.readFileSync(f, 'utf8');
      parsed = parseYaml(text);
      if (!Array.isArray(parsed)) parsed = [parsed];
    } catch (e) {
      console.log(`  ${path.basename(f)}  :  PARSE ERROR (${e.message})`);
      results.push({ file: f, errors: [{ rule: 'RX', msg: 'YAML parse error: ' + e.message }], warnings: [], triggers: [] });
      totalErrors++;
      continue;
    }
    // Multi-doc file → run lint on each topic inside
    const base = path.basename(f).replace(/\.(ya?ml)$/i, '');
    for (let idx = 0; idx < parsed.length; idx++) {
      const subLabel = parsed.length > 1
        ? `${base} [topic ${idx + 1}/${parsed.length}]`
        : base;
      const docName = (parsed[idx] && (parsed[idx].name || parsed[idx].displayName)) ||
                      (parsed.length > 1 ? `${base}#${idx + 1}` : base);
      const r = lintTopic(docName, parsed[idx] || {});
      // Tag the result with display info for output
      r.file = f;
      r.label = subLabel;
      results.push(r);
      totalErrors += r.errors.length;
      totalWarnings += r.warnings.length;
    }
  }

  // Second pass — R5 trigger overlap across topics (Jaccard > 0.60 = overlap).
  // Skip aggregate files (filenames containing 'consolidated' or 'fine_tuned')
  // because they intentionally duplicate topic content.
  const isAggregate = (f) => /(consolidated|fine_tuned|all_topics|backup|archive)/i.test(path.basename(f));
  const overlapWarn = [];
  for (let i = 0; i < results.length; i++) {
    if (isAggregate(results[i].file)) continue;
    for (let j = 0; j < results.length; j++) {
      if (i === j) continue;
      // Suppress overlaps where the OTHER side is an aggregate — the
      // overlap is informational: aggregate files intentionally contain copies.
      if (isAggregate(results[j].file)) continue;
      const A = results[i], B = results[j];
      if (!A.triggers.length || !B.triggers.length) continue;
      let max = 0, pair = null;
      for (const a of A.triggers) {
        for (const b of B.triggers) {
          const j_ = jaccardTokens(a, b);
          if (j_ > max) { max = j_; pair = [a, b]; }
        }
      }
      if (max >= 0.60) {
        overlapWarn.push({ a: A.label, b: B.label, score: max, pair });
        totalWarnings++;
      }
    }
  }

  // Print report
  for (const r of results) {
    const e = r.errors.length, w = r.warnings.length;
    const mark = e ? '✗' : (w ? '⚠' : '✓');
    console.log(`  ${mark} ${r.label || path.basename(r.file)}   (errors=${e}, warnings=${w})`);
    for (const x of r.errors)   console.log(`      [${x.rule}] ERR   ${x.msg}`);
    for (const x of r.warnings) console.log(`      [${x.rule}] WARN  ${x.msg}`);
  }
  if (overlapWarn.length) {
    console.log('\n  Cross-topic trigger overlap (R5):');
    for (const o of overlapWarn) {
      console.log(`    ⚠ ${o.a} ↔ ${o.b}   jaccard=${o.score.toFixed(2)}   ("${o.pair[0]}" vs "${o.pair[1]}")`);
    }
  }

  console.log(`\n  TOTAL: ${totalErrors} error(s), ${totalWarnings} warning(s) across ${files.length} file(s)`);

  if (totalErrors > 0) process.exit(1);
  if (totalWarnings > 0) process.exit(2);
  process.exit(0);
}

main();
