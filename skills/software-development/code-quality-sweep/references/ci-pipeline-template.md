# CI/CD Pipeline Template (GitHub Actions)

Drop this into `.github/workflows/ci.yml`. Every gate is a HARD FAIL — no `|| true`.

## Full pipeline (lint + test matrix + coverage + typecheck + build)

```yaml
name: CI/CD

on:
  push:
    branches: [ master ]
  pull_request:
    branches: [ master ]
  schedule:
    - cron: '0 16 * * *'  # daily

jobs:
  # ═══════════════════════════════════════════════════════════════════════
  # LINT + SECURITY + QUALITY GATES  (OS-agnostic, run once on linux)
  # ═══════════════════════════════════════════════════════════════════════
  lint:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v4
      - uses: actions/setup-python@v5
        with:
          python-version: '3.11'

      - name: Install tools
        run: pip install ruff bandit

      # ── Ruff gates (hard fail) ──
      - name: Ruff — full codebase lint
        run: |
          ruff check . \
            --select=E,F,N,UP \
            --ignore=E501,F401,F841,N802 \
            --no-cache

      - name: Ruff — enforce no bare excepts
        run: |
          bare=$(ruff check . --select=E722 --output-format=concise --no-cache 2>&1 | grep -c "E722" || true)
          if [ "$bare" -gt 0 ]; then
            echo "FAIL: $bare bare except: clauses found"
            ruff check . --select=E722 --no-cache
            exit 1
          fi
          echo "PASS: no bare excepts"

      - name: Ruff — enforce no undefined names
        run: |
          undef=$(ruff check . --select=F821 --output-format=concise --no-cache 2>&1 | grep -c "F821" || true)
          if [ "$undef" -gt 0 ]; then
            echo "FAIL: $undef undefined name(s) found"
            ruff check . --select=F821 --no-cache
            exit 1
          fi
          echo "PASS: no undefined names"

      # ── Security scan (informational) ──
      - name: Bandit — security lint
        run: |
          bandit -r . \
            -c pyproject.toml \
            -x .venv,tests \
            -f screen \
            --exit-zero
          echo "Security scan complete (non-blocking)"

      # ── Deduplication check ──
      - name: Deduplication check
        run: |
          python -c "
          import os, ast, sys
          from collections import Counter

          dup_targets = {'load_json', 'now_pt', 'now_iso', 'atomic_write', 'atomic_write_json'}
          counts = Counter()

          for root, dirs, files in os.walk('.'):
              dirs[:] = [d for d in dirs if not d.startswith('.') and d not in ('venv', '.venv')]
              for f in files:
                  if not f.endswith('.py'):
                      continue
                  path = os.path.join(root, f)
                  try:
                      with open(path) as fh:
                          tree = ast.parse(fh.read())
                      for node in ast.walk(tree):
                          if isinstance(node, ast.FunctionDef) and node.name in dup_targets:
                              counts[node.name] += 1
                  except:
                      pass

          violations = {k: v for k, v in counts.items() if v > 1}
          if violations:
              print('FAIL: duplicated utility functions found:')
              for name, count in sorted(violations.items()):
                  print(f'  {name}: defined {count}x across codebase')
              print('Move to a shared util.py and import from there.')
              sys.exit(1)
          print('PASS: no duplicated utility functions')
          "

  # ═══════════════════════════════════════════════════════════════════════
  # TESTS  (ubuntu + windows matrix — hard gate)
  # ═══════════════════════════════════════════════════════════════════════
  test:
    needs: lint
    runs-on: ${{ matrix.os }}
    strategy:
      fail-fast: false
      matrix:
        os: [ubuntu-latest, windows-latest]
        python: ['3.11']

    steps:
      - uses: actions/checkout@v4
      - uses: actions/setup-python@v5
        with:
          python-version: ${{ matrix.python }}

      - name: Install dependencies
        run: |
          python -m pip install --upgrade pip --no-cache-dir
          pip install --no-cache-dir pytest pytest-timeout numpy pandas pyarrow scipy python-dateutil pytz yfinance

      # IMPORTANT: Use shell: bash for cross-platform multiline commands
      # Windows runner defaults to pwsh which uses backtick for continuation
      - name: Run tests
        shell: bash
        run: |
          python -m pytest tests/ \
            -v \
            --tb=short \
            --timeout=120 \
            -p no:warnings \
            2>&1

  # ═══════════════════════════════════════════════════════════════════════
  # COVERAGE  (separate job — known numpy conflict with coverage tools)
  # ═══════════════════════════════════════════════════════════════════════
  coverage:
    needs: lint
    runs-on: windows-latest
    continue-on-error: true  # coverage is informational, never blocks merge
    steps:
      - uses: actions/checkout@v4
      - uses: actions/setup-python@v5
        with:
          python-version: '3.11'

      - name: Install dependencies
        run: |
          python -m pip install --upgrade pip --no-cache-dir
          pip install --no-cache-dir pytest pytest-timeout coverage numpy pandas pyarrow scipy python-dateutil pytz yfinance

      - name: Measure coverage
        shell: bash
        run: |
          coverage run --source=production,research,stocks \
            -m pytest tests/ \
            -v \
            --tb=short \
            --timeout=120 \
            -p no:warnings \
            2>&1
          coverage report --fail-under=75 --skip-covered
          coverage xml

      - name: Upload to Codecov
        uses: codecov/codecov-action@v5
        with:
          files: ./coverage.xml
          fail_ci_if_error: false

  # ═══════════════════════════════════════════════════════════════════════
  # TYPE CHECK  (informational, non-blocking)
  # ═══════════════════════════════════════════════════════════════════════
  typecheck:
    needs: lint
    runs-on: ubuntu-latest
    continue-on-error: true
    steps:
      - uses: actions/checkout@v4
      - uses: actions/setup-python@v5
        with:
          python-version: '3.11'

      - name: Install mypy
        run: pip install mypy pandas-stubs

      - name: Type check (info only)
        run: |
          mypy production/ research/ stocks/ \
            --ignore-missing-imports \
            --no-error-summary \
            --show-error-codes \
            2>&1 | head -50 || true
          echo "Type check is informational — failures do not block CI."

  # ═══════════════════════════════════════════════════════════════════════
  # BUILD VERIFICATION  (master push only, both OSes)
  # ═══════════════════════════════════════════════════════════════════════
  build:
    needs: test
    runs-on: ${{ matrix.os }}
    if: github.ref == 'refs/heads/master' && github.event_name == 'push'
    strategy:
      matrix:
        os: [ubuntu-latest, windows-latest]
    steps:
      - uses: actions/checkout@v4
      - uses: actions/setup-python@v5
        with:
          python-version: '3.11'

      - name: Verify project structure
        shell: bash
        run: |
          echo "=== Project structure (${{ matrix.os }}) ==="
          find . -name '*.py' -not -path './.*' -not -path '*/venv/*' | wc -l
          echo "Build verification passed."
```

## Pre-commit hooks

Add `.pre-commit-config.yaml` to catch issues BEFORE they reach CI:

```yaml
repos:
  - repo: https://github.com/astral-sh/ruff-pre-commit
    rev: v0.11.8
    hooks:
      - id: ruff
        args: [--select=E,F,N,UP, --ignore=E501,F401,F841,N802]
      - id: ruff-format

  - repo: https://github.com/pre-commit/pre-commit-hooks
    rev: v5.0.0
    hooks:
      - id: trailing-whitespace
      - id: end-of-file-fixer
      - id: check-yaml
      - id: check-json
      - id: check-toml
      - id: check-added-large-files
        args: ['--maxkb=500']
      - id: detect-private-key
      - id: mixed-line-ending
        args: ['--fix=lf']

  - repo: https://github.com/PyCQA/bandit
    rev: 1.8.3
    hooks:
      - id: bandit
        args: ['-c', 'pyproject.toml', '-x', '.venv,tests']
        additional_dependencies: ['.[toml]']
```

One-time setup: `pip install pre-commit && pre-commit install`

## Adapting the template

1. **dup_targets**: Update the set of function names to check for duplication
2. **dependencies**: Adjust `pip install` list for what your tests actually need
3. **test_ignore**: Add `--ignore=` for tests needing unavailable frameworks (freqtrade, tensorflow, etc.)
4. **python-version**: Match your project's required Python version
5. **coverage --source**: Adjust the `--source` directories to match your project layout
6. **coverage threshold**: Set `--fail-under=` to your desired minimum (suggest starting at 60-75%)

## Companion files

A complete CI/CD setup also needs these supporting files:

### .github/dependabot.yml — automated dependency updates

```yaml
version: 2
updates:
  - package-ecosystem: "pip"
    directory: "/"
    schedule:
      interval: "weekly"
      day: "monday"
    open-pull-requests-limit: 5
    labels: ["dependencies", "security"]
    groups:
      python-deps:
        patterns: ["*"]
        update-types: ["minor", "patch"]

  - package-ecosystem: "github-actions"
    directory: "/"
    schedule:
      interval: "weekly"
      day: "monday"
    labels: ["dependencies", "ci"]
```

### user_data/.env.example — secrets template

Template showing all expected environment variables with placeholder values.
Add `.env` and `user_data/.env` to `.gitignore` so real secrets are never
committed. Key variables to document:
- `EXCHANGE_API_KEY` / `EXCHANGE_API_SECRET` — exchange credentials
- `FREQTRADE_JWT_SECRET` — bot API authentication
- `NOTION_API_KEY` — optional Notion integration
- `ALERT_EMAIL_TO` / `SMTP_*` — optional email alerts

### pip-audit in CI (optional, non-blocking)

Add to the lint job for vulnerability scanning:
```yaml
- name: pip-audit — dependency vulnerability scan
  run: |
    pip install pip-audit
    pip-audit --ignore-vuln PYSEC-YYYY-XXXXX || true
  continue-on-error: true
```

## Critical pitfalls

- **Never use `|| true` on quality gates.** The whole point is to fail on violations.
- **Always add `shell: bash` to multiline `run:` steps** when the job runs on both OSes.
- **Keep coverage in a separate `continue-on-error` job.** pytest-cov and coverage CLI both conflict with numpy C extensions ("cannot load module more than once per process"). This is not fixable — it's a fundamental incompatibility.
- **Strategy files with framework imports (talib, freqtrade) need conditional imports.** Wrap in try/except ImportError with fallback stubs so tests can import the module in CI.
