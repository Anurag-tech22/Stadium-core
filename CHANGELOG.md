# Changelog

All notable changes to Phoenix Stadium Assistant are documented here.
Format follows [Keep a Changelog](https://keepachangelog.com/en/1.0.0/).
Versions follow [Semantic Versioning](https://semver.org/).

---

## [1.2.0] — 2026-07-14

### Added
- **VISUAL accessibility routing** — fans who need audio guidance are now routed to gates with PA/audio systems (`has_audio_guidance=True`); Gate H excluded (moved from below for clarity)
- **HEARING accessibility routing** — fans who need visual displays are routed to gates with LED boards (`has_visual_display=True`); Gate G excluded
- `has_visual_display` and `has_audio_guidance` fields on `GateStatus` schema
- `accessibility_need` field on `ResolvedContext` — LLM layer now tailors phrasing per specific need
- `accessibility_visual` and `accessibility_hearing` response templates (5 languages: EN, HI, ES, FR, PT)
- **`/.well-known/security.txt`** endpoint (RFC 9116 coordinated disclosure)
- **GitHub Actions CI** — lint (ruff), format-check, mypy, bandit, pip-audit, pytest 95% coverage floor, gitleaks, Playwright/axe accessibility scan
- **CodeQL** security analysis workflow (security-extended, weekly + every push/PR)
- **Dependabot** for automated pip and GitHub Actions dependency updates
- `CONTRIBUTING.md` with architecture principles and language-addition guide
- `CODEOWNERS` — code ownership declarations
- 12 new tests: VISUAL/HEARING filtering, Spanish phrasing, `security.txt`, enriched ops snapshot, SSE content-type, lifespan, Redis limiter, wheelchair fallback, live candidate fallback

### Changed
- `_pseudo_multiplier` replaced manual `_multiplier_cache` dict with `@lru_cache(maxsize=256)` — idiomatic Python, automatic LRU eviction, no cache-clear race condition
- Ops snapshot (`GET /api/ops/snapshot`) now returns **merged `GateStatus + WaitEstimate`** per gate — exposes `arrivals_per_min`, `capacity_per_min`, `servers_open` alongside predictions; IoT overrides now fully observable
- Transport intent template now references `{gate}` (the recommended gate) instead of hardcoded "Gate A"
- Sustainability and restroom intent templates reference the recommended `{gate}` for contextual responses
- GeminiLLM model updated from `gemini-1.5-flash` to `gemini-2.0-flash`
- All 3 ruff E402 lint errors resolved in `routes.py` (imports moved to top)
- All 4 mypy errors resolved in `main.py` (`type: ignore[return-value]`)

### Fixed
- `test_production_features` cache assertion — updated to use `_pseudo_multiplier.cache_info()` instead of removed `_multiplier_cache` dict

---

## [1.1.0] — 2026-07-13

### Added
- Erlang-C M/M/c queueing model for wait-time prediction
- Server-Sent Events (SSE) ops live stream
- IoT turnstile override endpoint (`POST /api/ops/gate-update`)
- 5-language support: EN, HI, ES, FR, PT
- WHEELCHAIR accessibility gate filtering
- Incident safety notice detection and alert phrasing
- bleach + custom sanitization layer
- slowapi rate limiting
- CSP / security headers middleware
- Bandit + pip-audit security scanning
- 31 tests, 92% coverage

---

## [1.0.0] — 2026-07-10

### Added
- Initial Phoenix Stadium fan assistant
- FastAPI application, Jinja2 templates
- Fan interface (`/`) and ops dashboard (`/ops`)
- MockLLM and GeminiLLM implementations
