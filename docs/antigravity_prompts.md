# Antigravity build prompts — Phoenix Stadium

Feed these to Antigravity **in order**, one at a time. Each prompt maps
to specific grading parameters so nothing gets built without a reason
an evaluator can see. Paste the Phoenix Stadium zip in as the starting repo
before Prompt 1.

---

### Prompt 1 — Verify and run the base scaffold
*(Code Quality, Testing)*
```
Open this repo. Install requirements.txt in a virtualenv. Run
`pytest -v` and show me full output including coverage. Do not modify
any files yet — just confirm everything passes and report the
coverage percentage for app/core/context_engine.py and app/core/llm.py.
```

### Prompt 2 — Raise coverage to 100% on the core engine
*(Testing, Code Quality)*
```
Coverage report shows gaps in [paste the missing lines from Prompt 1].
Add pytest test cases in tests/test_engine.py that cover every branch
in context_engine.py and llm.py — including the c*mu==0 guard, the
rho>=0.999 clamp, and every intent in INTENT_KEYWORDS. Do not change
any application logic, only add tests. Re-run pytest --cov and confirm
100% on app/core/.
```

### Prompt 3 — Static analysis and type-checking
*(Code Quality)*
```
Add ruff and mypy to requirements.txt (dev extras). Run `ruff check .`
and `mypy app/` and fix every warning without changing behavior —
prefer adding type hints over ignoring errors. Save the clean output
of both commands to docs/lint-report.txt.
```

### Prompt 4 — Security scan
*(Security)*
```
Add bandit and pip-audit to requirements. Run `bandit -r app/` and
`pip-audit`. Fix any real findings (not false positives — explain any
you suppress with a comment). Save clean output to
docs/security-scan.txt. Then add three more prompt-injection strings
to tests/test_security.py's INJECTION_ATTEMPTS list that specifically
try to leak the system prompt or claim admin/developer mode, and
confirm they still can't change routing.
```

### Prompt 5 — Rate limiting and abuse hardening
*(Security, Efficiency)*
```
Review app/main.py and app/api/routes.py. The /api/assist endpoint is
rate-limited at 20/minute per IP via slowapi. Add a test in
tests/test_security.py that sends 21 requests in a loop and asserts
the 21st returns HTTP 429. Also confirm the CSP header in main.py
blocks inline scripts (there should be none in static/js/app.js —
verify and note this in the test docstring).
```

### Prompt 6 — Efficiency pass
*(Efficiency)*
```
Profile /api/ops/snapshot and /api/assist with a simple timing script
(time.perf_counter around 1000 calls to context_engine.resolve and
predict_wait). Confirm both are sub-millisecond since there's no I/O
or LLM call in the deterministic path. Save results to
docs/perf-notes.md. If MockLLM string formatting is a hotspot, note it
but don't over-optimize — the real cost center in production is the
GeminiLLM network call, which already has the offline fallback.
```

### Prompt 7 — Accessibility audit
*(Accessibility)*
```
Install axe-core (via @axe-core/cli or Playwright + axe). Run it
against http://localhost:8000/ and http://localhost:8000/ops with the
dev server running. Save the full report to
docs/accessibility-report.txt. Fix any violations found — likely
candidates: color contrast on .chip or .sub text, missing form labels,
or focus order. Do not remove the aria-live regions or semantic table
markup already in the templates; fix around them.
```

### Prompt 8 — Add a fourth intent theme (breadth without breaking discipline)
*(Problem Statement Alignment)*
```
Add one new intent to context_engine.py: "lost_and_found" (keywords:
lost, found, missing item, left behind). Add its templates in all
three languages to llm.py's _TEMPLATES dict. Add unit tests for the
new intent in tests/test_engine.py. Update the traceability table in
README.md to add a row for it under a "guest services" theme. Do not
touch any other intent's logic.
```

### Prompt 9 — End-to-end journey test
*(Testing, Problem Statement Alignment)*
```
Write one integration test in a new file tests/test_journey.py using
FastAPI's TestClient: hit /health, then /api/assist with a fan query
in Hindi asking for the wheelchair-accessible gate, then /api/ops/snapshot,
and assert each response is well-formed and mutually consistent (the
gate recommended to the fan appears in the ops snapshot with a matching
wait time). This is the single test that proves the whole pipeline
works end to end — reference it explicitly in README.md's Evaluation
Map table.
```

### Prompt 10 — Deploy and finalize
*(Problem Statement Alignment, all parameters — this is the proof step)*
```
Build the Docker image, run it locally on port 8080, and confirm
/health returns 200. Then deploy to Cloud Run (or your preferred
platform) and give me the live URL. Update README.md: replace any
placeholder URLs with the real deployed link, and add a "Live demo"
line right under the title. Do a final pass confirming every row in
the Evaluation Map table still points to a file/report that actually
exists in the repo — fix any that don't.
```

---

## Notes on using these with Antigravity

- Run them **in order** — later prompts assume earlier ones passed.
- After each prompt, actually read Antigravity's diff before accepting
  it. An AI evaluator will read the code too; don't let an agent add
  something (like a stray `console.log`, a `TODO`, or an unused
  import) that would cost you Code Quality points.
- If Antigravity suggests widening scope (more languages, more
  personas, a database), decline unless you have time to fully verify
  it — the whole strategy here is "small and 100% checkable" beats
  "large and partially verified."
- Keep MockLLM as the default provider even after wiring up Gemini.
  Never let the deployed demo depend on a live API key being valid at
  judging time.
