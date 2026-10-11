# CODING_RULES.md

One style for the whole repo. If a rule here conflicts with a habit, the rule wins. If a rule is wrong, change it here first, log it in FEATURE_LOG.md, then follow the new version.

---

## 1. General

1. Plain, boring, readable code. Clarity beats cleverness.
2. Modules, not whole systems. One task = one small, finished piece.
3. Reuse before you write. Search for an existing util or component first.
4. No duplicated logic. Business rules exist in exactly one place (`core/domain`).
5. No dead code, no commented-out code, no TODOs without a FEATURE_LOG.md entry.
6. No placeholder buttons, no fake data shown as real, no hardcoded demo results.
7. Comments explain why, not what. Docstrings only where behaviour is not obvious.
8. Do not rename or move folders without updating ARCHITECTURE.md and logging a decision.
9. Keep files small. Over about 250 lines is a signal to split.

## 2. Layer rules (strict)

| Layer | May import | Must not |
|---|---|---|
| `core/domain` | stdlib only | Django, httpx, settings, env vars, current time (`datetime.now`), I/O |
| `core/services` | domain, provider Protocols, `infra.Cache` Protocol | Django, concrete providers, settings |
| `core/providers` | domain types, httpx | Django, business rules (risk, ranking) |
| `core/infra` | Django cache | business rules |
| `api` | services, serializers, DRF | business rules, vendor calls |
| `frontend` UI | API types, theme | Classify risk, compute ETAs or miles, rank routes, apply thresholds |

Frontend allowed logic: formatting (durations, miles, dates from API-provided ISO strings and tz names), mapping a level string to a color/label, form validation of shape and range.

## 3. Naming

**Python**
- Modules and functions: `snake_case`. Classes: `PascalCase`. Constants: `UPPER_SNAKE_CASE`.
- Booleans start with `is_`, `has_`, `should_`.
- Units in names when ambiguous: `distance_miles`, `duration_seconds`, `load_weight_lb`, `wind_mph`, `rain_in_hr`.
- Test files `test_<module>.py`. Test functions `test_<unit>_<scenario>_<expected>`.

**TypeScript / React**
- Components: `PascalCase.tsx`, one exported component per file, named exports only (no default exports).
- Hooks: `useThing.ts`. Utilities: `camelCase.ts`. Variables and functions: `camelCase`. Types and interfaces: `PascalCase`. Constants: `UPPER_SNAKE_CASE`.
- Props types: `<Component>Props`.
- Tests next to the file: `thing.test.ts(x)`.
- Exception: API DTO fields stay `snake_case` exactly as the backend sends them. No key-conversion layer.

**API/JSON:** `snake_case` keys. Level values are lowercase strings: `low`, `moderate`, `high`, `severe`, `no_travel`. Timestamps are ISO 8601 with offset or `Z`.

## 4. Formatting and tooling

- Python: `ruff format` and `ruff check`, line length 100, type hints on all function signatures, `from __future__ import annotations` not required. Python 3.12.
- TypeScript: `strict: true`, no `any` (use `unknown` and narrow), no non-null assertions without a comment, Prettier defaults plus single quotes, ESLint with react-hooks rules.
- Imports sorted by the tool. No wildcard imports.
- Run before every commit: backend `ruff check . && ruff format --check . && pytest`; frontend `npm run lint && npm run typecheck && npm test`.

## 5. Backend patterns

- Domain types: `@dataclass(frozen=True, slots=True)`. Enums for levels and drivers. No mutable defaults.
- Pure functions in domain. Pass time in as an argument. Return new objects.
- Services receive providers and cache through constructor arguments (dependency injection). Wiring happens only in `api/container.py`.
- All constants and thresholds in `core/domain/rules_config.py`. No magic numbers in code or tests (tests may use literal values from the spec on purpose).
- Typed exceptions for provider and domain failures. Translate to HTTP in `api/errors.py` only. Never catch bare `Exception` except at the API boundary to return `internal_error`.
- Logging: `logging.getLogger(__name__)`. No `print`. Never log API keys, full vendor URLs or request bodies with secrets. Set `httpx` logger to WARNING.
- Serializers validate input and shape output. Views stay under about 30 lines.
- Timezones: store and compute in UTC. Convert to local only for display strings and the departure input, using `zoneinfo`. Add `tzdata` to requirements.
- Floating point: compare rounded values where the spec says so (ranking). Never compare floats with `==` in logic.

## 6. Frontend patterns

- Feature folders (`features/trip-form`, `results`, `map`). Shared pieces in `components/`.
- Presentational components take props and render. Data fetching lives in hooks in `hooks/` or feature hooks.
- Server data through TanStack Query. No `useEffect` + `fetch` for API calls.
- All HTTP in `api/` (one client, typed functions). Components never call `fetch`.
- MUI only for UI. Use theme tokens (`theme.spacing`, palette, typography variants). No ad-hoc pixel values except map container sizing. Use `sx` for small tweaks only; repeated styling becomes a themed component.
- Risk colors in one file: `theme/riskColors.ts`. Color is never the only signal: pair with text.
- Every async view has loading, empty and error states.
- Memoize expensive derived data (heat frames) with `useMemo`. Keep the heatmap slider path free of React re-renders (update the Leaflet layer directly).
- No inline anonymous components inside render. No index keys for dynamic lists that reorder.
- Map: canvas rendering, `CircleMarker`, no DOM markers for checkpoints.

## 7. API conventions

- REST-ish, JSON only. Status codes per ARCHITECTURE §8. One error envelope. No 200 responses carrying errors.
- Validation errors list fields. Messages are human-readable and say what to do.
- Never return stack traces or vendor error bodies.
- Add a field to a response only if the UI or a test uses it.

## 8. Testing rules

- Write the test with the code, not after. Domain logic: tests first when practical.
- No live network in tests. Providers are faked or mocked with fixtures.
- Parametrize boundary cases. Every threshold boundary in the spec has a test on both sides.
- Test failures paths: provider timeout, 429, malformed data, missing weather, empty results.
- Frontend: test validation logic, formatting, heat frame conversion, and the main form-to-results path with a mocked API.
- Coverage guidance: domain 90%+, services 80%+, API 80%+. Do not chase coverage numbers with meaningless tests.
- A bug fix starts with a failing test.

## 9. Dependencies

- Add a dependency only if it saves real effort and is maintained. Prefer stdlib and what is already installed.
- Before adding: check the exact package name on PyPI/npm (typosquatting is real), check last release date and weekly downloads, avoid versions published in the last 14 days, check peer dependencies (react-leaflet vs React version).
- Pin exact versions. Commit lockfiles (`package-lock.json`, pinned `requirements.txt`).
- Every addition gets a row in PROJECT_CONTEXT.md §9 and a line in FEATURE_LOG.md.
- Do not add Redis, Celery, Kubernetes, Docker orchestration, a database, an auth system or a state-management library beyond TanStack Query unless a documented requirement needs it.

## 10. Git

- Conventional Commits: `feat(domain): ...`, `fix(api): ...`, `test(...)`, `refactor(...)`, `docs: ...`, `chore: ...`.
- Commit after every stable feature: tests green, lint clean, FEATURE_LOG updated. Never commit a broken build.
- Small commits. One concern per commit. No "wip", no "fix stuff".
- Never commit: `.env`, keys, `node_modules`, build output, caches, local DBs, IDE files.
- Tag the submitted state `v1.0-submission` and test exactly that commit on the hosted site.

## 11. Security and config

- Secrets from env only. `.env.example` lists every variable with a dummy value.
- Validate all input on the server even if the UI validates.
- No wildcard CORS in production. No `DEBUG=True` in production.

## 12. Documentation upkeep

After any major change (new module, changed contract, new dependency, changed assumption, changed folder):
1. Update PROJECT_CONTEXT.md (assumptions, stack, dependency register).
2. Update ARCHITECTURE.md (structure, flows, contract).
3. Add a FEATURE_LOG.md entry (what, why, files, tests, commit).
README is written in P7 from these files, not from memory.

## 13. Forbidden

- Business logic in React components, views or serializers.
- Hardcoded API keys, hardcoded risk numbers outside `rules_config.py`.
- Fake or sample data presented as live data. (A clearly labeled example trip button is fine; fabricated weather is not.)
- Silent fallbacks that hide missing data (for example treating missing weather as 0).
- `any`, `# type: ignore`, `eslint-disable`, `noqa` without a one-line reason comment.
- New top-level folders, new frameworks, rewrites "for cleanliness" mid-phase.
- Building features not in FEATURE_LOG.md.
