# Contributing to Phoenix Stadium Assistant

Thank you for your interest in contributing! This document outlines how to get
involved and what we expect from contributors.

## Code of Conduct

Be respectful and constructive. All contributions must be in line with the
project's safety-first, accessibility-first philosophy.

## Getting Started

```bash
git clone https://github.com/<your-org>/phoenix-stadium.git
cd phoenix-stadium
python -m venv .venv && source .venv/bin/activate   # Windows: .venv\Scripts\activate
pip install -r requirements.txt -r requirements-dev.txt
```

## Development Workflow

1. Create a feature branch: `git checkout -b feat/my-feature`
2. Make your changes
3. Run quality gates locally:
   ```bash
   ruff check app/ tests/         # lint
   ruff format app/ tests/        # format
   mypy app/ --ignore-missing-imports    # type-check
   bandit -r app/ -ll -q          # security scan
   pytest tests/ --cov=app --cov-fail-under=95  # tests + coverage
   ```
4. Commit using Conventional Commits: `feat: add X`, `fix: resolve Y`, `docs: update Z`
5. Open a pull request against `main`

## Architecture Principles

- **Deterministic core, LLM for phrasing only.** The `context_engine.py` module decides all facts (gate, wait time, incident). The LLM only phrases them. Never let the LLM make routing or safety decisions.
- **Injection-proof by design.** Raw user text never reaches the LLM prompt as instructions. It passes through `sanitize_text()` and then `classify_intent()` + `resolve()` to produce a structured `ResolvedContext`.
- **Erlang-C queueing model.** Wait-time estimates are derived from the M/M/c formula. Do not replace this with threshold comparisons or LLM guesses.
- **Offline-first.** `MockLLM` must always work without any external API. The fan assistant must never go dark.

## Adding a Language

1. Add a value to `Language` in `app/core/schemas.py`
2. Add translations for all 10 intent keys in `app/core/llm.py` (`_TEMPLATES`)
3. Add a localized congestion label row in `_CONGESTION_LABELS`
4. Add a localized alternate suffix in `_ALTERNATE_SUFFIX`
5. Add at least one language-specific test in `tests/test_engine.py`

## Test Coverage Requirements

All PRs must maintain ≥ 95% line coverage. CI enforces this automatically.
New features must come with corresponding unit tests.

## Security Vulnerabilities

Please do not open a public GitHub issue for security vulnerabilities.
Instead, report them via the coordinated disclosure contact at
`/.well-known/security.txt`.
