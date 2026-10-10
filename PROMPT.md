# PROMPT.md

How to work with Antigravity on this project. Part A is the master prompt (paste it as the workspace rule or as the first message of every new session). Part B has one prompt per phase. Part C has reusable templates.

Aayush does not read code, so the agent must explain what it did in plain language and prove it with test output.

---

## Operating mode (set up once in Antigravity)

- Put the root `AGENTS.md` in the repo (it points to these files). Antigravity reads `AGENTS.md`/`GEMINI.md` at session start according to third-party guides. Confirm in the Customizations panel that it is loaded.
- Do not run in fully autonomous mode. Set review so the agent pauses before: installing dependencies, deleting files, running anything destructive, changing folder structure.
- One phase per session. Start each session by pasting Part A (short form is fine) and the phase prompt from Part B.
- Run tests yourself at the end of each phase and look at the output. Do not accept "tests pass" without seeing it.

---

## Part A. Master prompt

```
You are a senior full-stack engineer (Python/Django and React/TypeScript). You are building a take-home assessment for Spotter.ai: a weather-aware truck routing web app. Correctness and clarity matter more than extra features. The result will be reviewed by engineers and discussed in an interview, so everything must be explainable.

READ FIRST, EVERY SESSION, IN THIS ORDER:
1. PROJECT_CONTEXT.md  (spec snapshot, assumptions A-01..A-18, stack, API facts)
2. ARCHITECTURE.md     (layers, modules, algorithms, API contract)
3. CODING_RULES.md     (naming, patterns, testing, git)
4. FEATURE_LOG.md      (what is built, what is next, decisions)
If any of these conflict with your instinct, the files win. If the files conflict with each other or are silent on something that affects behaviour, STOP and ask. Do not guess.

ARCHITECTURE RULES
- Follow the current architecture strictly. Do not modify the folder structure unless I approve it; if you must, update ARCHITECTURE.md and log a decision first.
- Modular layered architecture: frontend, API layer, services, domain, providers, infra stay separated.
- Never mix business logic with UI. The frontend does not classify risk, compute ETAs, compute miles or rank routes. It displays what the API returns.
- Abstract all third-party APIs (routing, geocoding, weather) behind the provider interfaces. Services depend on interfaces, not vendors.
- Domain code is pure: no Django, no HTTP, no clock reads, no env vars.
- Reuse existing utilities and components before writing new ones. No duplicate logic.
- Follow the existing naming conventions and patterns. One coding style only (CODING_RULES.md).
- Generate scalable, maintainable, production-ready code only. No placeholders, no fake data presented as real, no TODOs without a FEATURE_LOG entry.
- Do not add dependencies, frameworks or infrastructure (Redis, Celery, Docker orchestration, databases, auth, LLM calls) unless a documented requirement needs it. Ask first.

SCOPE
- Generate modules, not entire startups. Do only the task I give you. Do not build ahead, do not add features that are not in FEATURE_LOG.md.
- The spec is the product. Implement every requirement exactly; do not invent behaviour. Where the spec is ambiguous, use the decision in PROJECT_CONTEXT.md §4.

WORKFLOW FOR EVERY TASK
1. Restate the task in 3-5 lines and list the files you will create or change. Wait for my OK if the task touches more than one layer or adds a dependency.
2. Write tests first or alongside. Domain logic gets boundary and edge-case tests.
3. Implement the smallest correct version.
4. Run lint, format check, type check and tests. Show me the actual command output.
5. Refactor continuously: remove duplication and dead code you introduced, keep files small.
6. Update FEATURE_LOG.md (status, tests, files). Update PROJECT_CONTEXT.md and ARCHITECTURE.md after any major change.
7. Commit after every stable feature with a Conventional Commit message. Never commit failing tests, secrets or .env files.

QUALITY BAR
- Handle invalid input, missing values, boundary conditions and upstream failures explicitly. Missing weather is never silently treated as zero.
- Every API call has a timeout, typed errors and no secret leakage.
- Every async UI view has loading, empty and error states.
- Performance is graded: avoid N+1 patterns and repeated upstream calls, batch and cache, keep the map and heatmap smooth.
- Never hardcode secrets. Use environment variables and .env.example.

HOW TO REPORT BACK (plain language, short)
- What you built and why, in a few sentences I can repeat in an interview.
- Files changed.
- Test, lint and type-check output.
- Anything you assumed, anything you are unsure about, anything you want to change in the docs.
- The next suggested task.

STOP AND ASK WHEN
- The spec or docs are ambiguous or contradictory.
- You want to add a dependency, change structure, or deviate from ARCHITECTURE.md.
- A third-party API behaves differently from what the docs say.
- Tests fail and the fix would change agreed behaviour.
```

---

## Part B. Phase prompts

Paste the relevant block after Part A. Claude refines each block before you use it, based on the previous phase's results.

### P0. Provider spike (0.75 h) - F-000

```
Task: decide routing and geocoding providers by testing, and confirm Open-Meteo parameters. Do not build app code yet.
Read: PROJECT_CONTEXT.md §6, ARCHITECTURE.md §5-6.
Do:
1. Create backend/scripts/spike/ (throwaway scripts, committed under scripts/spike with a README note).
2. For TomTom (and HERE if TomTom fails): request routes for 4 long US pairs: Dallas->Denver, Los Angeles->Salt Lake City, Chicago->Atlanta, Seattle->Boise. Record: how many distinct routes come back, distances, durations, whether truck mode works, which response fields give per-segment travel time or cumulative offsets, how to get the polyline, how many calls were used.
3. Test a via-waypoint request on one pair to confirm the fallback works.
4. Test the vendor's geocoding/search endpoint for typeahead quality (e.g. "dalla", "denv").
5. Open-Meteo: one request with 3 coordinates and variables wind_speed_10m,rain,showers,snowfall, wind_speed_unit=mph, precipitation_unit=inch, timeformat=unixtime, timezone=auto, past_hours=3, forecast_hours=288. Confirm past_hours and forecast_hours work together, the response is a list in request order, units are right, and timezone names come back. Print response size and time.
Output: a short results table and a recommendation. Do not install anything beyond httpx without asking. API keys come from environment variables, never printed.
Update: FEATURE_LOG.md (D-006 decided, F-000 done), PROJECT_CONTEXT.md §5-6 (remove UNVERIFIED flags that are now confirmed).
Commit: chore(spike): record provider test results
```

### P1. Scaffold (0.5 h) - F-001

```
Task: create the repo skeleton exactly as in ARCHITECTURE.md §2.
Backend: Django project `config`, app `api`, package `core` with empty modules and __init__ files, pyproject.toml (ruff, pytest), requirements.txt with pinned versions, .env.example, minimal settings (no admin/sessions/messages unless needed), CORS from env, GZip middleware, /api/health/ returning {"status":"ok"}, one passing test.
Frontend: Vite + React + TypeScript strict, MUI, TanStack Query, ESLint, Prettier, Vitest + React Testing Library, theme/theme.ts and theme/riskColors.ts (levels low, moderate, high, severe, no_travel), App renders a placeholder shell, one passing test.
Root: .gitignore (env, node_modules, caches, build, sqlite), README stub.
Do not: add anything not in the architecture. Each dependency goes into PROJECT_CONTEXT.md §9 with a reason; check peer dependencies (react-leaflet vs React) before choosing React's major version.
Acceptance: backend `ruff check . && ruff format --check . && pytest` passes; frontend `npm run lint && npm run typecheck && npm test && npm run build` passes.
Commit: chore: scaffold backend and frontend
```

### P2. Domain core (2.25 h) - F-010 to F-015

```
Task: implement the pure domain layer in backend/core/domain with exhaustive tests. One module per commit, in this order:
1. types.py + rules_config.py + risk.py (F-010). Exactly ARCHITECTURE.md §4.1 and PROJECT_CONTEXT A-02..A-05. Include every worked example from the table and every boundary pair as parametrized tests.
2. geometry.py + sampling.py (F-011). Haversine, scaling to provider distance, point_at_mile, Douglas-Peucker for display only, resolve_interval (A-01), checkpoints with coverage ranges (§4.4).
3. timeline.py (F-012). Monotonic validation, 2-point fallback, interpolation.
4. weather_align.py (F-013). Wind interpolation, precip bucket rule (A-07), missing data -> None, rounding (A-03).
5. scoring.py (F-014). Miles by level, mile-weighted average, deltas, unavailable checkpoints excluded.
6. ranking.py (F-015). Sort key, No Travel gate, decided_by, headline text, NO_SAFE_ROUTE case.
Rules: no Django, no HTTP, no current-time reads. All numbers from rules_config.py. Frozen dataclasses.
Acceptance: pytest for core/domain passes; coverage 90%+ on this package; ruff clean.
Explain in plain language, per module, what it does and the edge cases it covers.
```

### P3. Providers, services, API (2.5 h) - F-020 to F-026

```
Task: build the backend around the domain layer, in this order, one commit each:
1. providers/base.py (Protocols, typed errors) and fake providers in tests (F-020).
2. Routing adapter for the vendor chosen in P0 (F-021): truck mode if supported, miles, best-available timeline, simplified-free full polyline.
3. services/route_selection.py (F-022): dedupe, detour filter, via-waypoint fallback, labels A/B/C, warning codes. Test with fakes: 3 routes, 2 routes, 1 route, duplicates.
4. providers/weather_openmeteo.py + infra/cache.py (F-023): grid snap 0.1, chunks of ~50, thread pool, one retry, rain+showers, fixed window, per-cell cache, timezone lookup. Test with respx fixtures: success, 429, timeout, malformed, chunking, unit math.
5. Geocoding adapter + /api/geocode/ (F-024).
6. services/trip_analysis.py (F-025) following ARCHITECTURE.md §7. Test with fakes: normal, missing weather, all No Travel, interval auto, cache reuse.
7. API layer (F-026): serializers, validation (A-12, A-15), error envelope and status table (§8), throttling, container.py, /api/trips/analyze/. Test every status code.
Rules: views under about 30 lines. Vendor URLs and keys never in logs or errors. httpx logger at WARNING. No live network in tests.
Acceptance: pytest, ruff pass. A manual live smoke script (backend/scripts/live_smoke.py) runs one real analyze and prints a summary; run it once, not in a loop.
```

### P4. Frontend core (2.5 h) - F-030 to F-034

```
Task: build the UI against the real API contract in ARCHITECTURE.md §8. Do not compute anything the API already returns.
1. api/ client, typed DTOs (snake_case as sent), error parsing into one AppError type (F-030).
2. TripForm (F-031): two PlaceAutocomplete fields (debounced search via /api/geocode/, must select a result), departure picker labeled "Local time at origin", load weight (lb) with helper text, interval select (Auto, 10, 25, 50), submit. validateTripForm is a pure, unit-tested function. API field errors appear under the right fields.
3. Results (F-032): RecommendationBanner (headline, decided_by), WarningsList, RouteCard x3 (label, tags, distance, duration, arrival local time, miles by level, average risk, delta vs fastest), CheckpointTable (collapsed, per route).
4. Map (F-033): MapView with canvas rendering, 3 routes with distinct colors and the selected one emphasized, checkpoint circle markers colored by risk level with popups (mile, local ETA, wind, rain, snow, level, driver, reason), legend. Selecting a route card highlights it on the map and vice versa.
5. States (F-034): idle hint, field errors, loading skeletons, API error with retry, partial results (warnings), no-safe-route alert.
Rules: MUI components and theme tokens only. No fetch outside api/. Named exports. Level colors only from theme/riskColors.ts.
Acceptance: lint, typecheck, vitest pass; manual walkthrough against the local backend with 3 trips; screenshots saved for the README.
```

### P5. Heatmap (1.75 h) - F-040, F-041

```
Task: heatmap end to end.
Backend (F-040): domain/corridor.py (ARCHITECTURE §4.8) with unit tests; services/heatmap_service.py (§7); /api/trips/heatmap/ using the same request serializer; compact response (levels only, 49 frames). Reuse the weather cache from analyze.
Frontend (F-041): useHeatmap (enabled after a successful analyze, same input). HeatmapLayer built on leaflet.heat, created once; on slider change update the existing layer with the precomputed frame and do not re-render the map or fetch anything. HeatmapControls: slider 0-48 with the local time label, play/pause, layer toggle (Overall, Wind, Rain, Snow), loading state, legend. Convert frames to [lat, lon, intensity] arrays once with useMemo; unit-test that conversion.
Check visually: low-risk areas faint, high-risk strong, no blobby distortion from overlapping points. If leaflet.heat distorts the colors, stop and propose the custom canvas fallback described in ARCHITECTURE §10 before changing anything.
Acceptance: scrubbing the slider back and forth stays smooth (no dropped-frame stutter in the browser performance panel), response size and time recorded in FEATURE_LOG.md.
```

### P6. Polish and performance (1.25 h) - F-050 to F-054

```
Task: responsive layout, performance pass, accessibility and polish. Measure first, then fix:
- Record in FEATURE_LOG.md: analyze time (cold and warm), heatmap time, payload sizes (gzipped), number of upstream calls per analyze, bundle size.
- Fix the worst offender only if it is clearly above target (analyze cold under about 6 s, warm under about 1.5 s; heatmap scrub at 60 fps; bundle under about 350 KB gzipped).
- Responsive checks at 360, 768 and 1280 px widths. No horizontal page scroll.
- Slow-server banner if the first request exceeds 5 s. A clearly labeled "Try an example trip" button that fills the form (no fake results).
- Accessibility pass: labels, focus order, text alongside color, slider value text.
Do not add features outside F-050..F-054.
```

### P7. Ship (1.75 h) - F-060 to F-064

```
Task: deploy, document, verify.
1. Deploy backend and frontend. Set env vars in the hosts' dashboards. Configure CORS for the exact frontend origin. Add an uptime ping for /api/health/.
2. Write README.md from the docs: what it does, live URL, screenshots, architecture summary (mermaid from ARCHITECTURE.md), setup, env vars, run commands, tests, decisions and assumptions (A-xx), performance notes, known limitations, how AI tools were used and verified.
3. Fresh-clone test: clone into a new folder, follow the README exactly, fix any gap.
4. Run pip-audit and npm audit; fix or document.
5. Tag v1.0-submission; deploy that exact commit; run the FEATURE_LOG.md §6 checklist on the hosted app in an incognito window.
Optional if time remains: F-064 CI workflow.
```

---

## Part C. Templates

### Bug fix
```
Bug: <what I did, what I expected, what happened, error text/screenshot>.
First write a failing test that reproduces it. Then fix the root cause at the right layer (not in the UI if it is a logic bug). Show test output before and after. Log it in FEATURE_LOG.md. Commit as fix(<scope>): ...
```

### Review (before every phase commit)
```
Review everything changed in this phase against CODING_RULES.md and ARCHITECTURE.md. Report, do not fix silently:
1. Layer violations (business logic in UI/views, Django in domain, vendor calls outside providers).
2. Spec deviations versus PROJECT_CONTEXT.md §3-4.
3. Duplicate logic, dead code, magic numbers, files over 250 lines.
4. Missing tests for edge cases and failure paths.
5. Missing loading/empty/error states.
6. Secrets, leaked URLs, unsafe logging.
7. Anything I could not explain in an interview.
List findings by severity with file and line.
```

### Explain (interview prep)
```
Explain <module> as I would to an interviewer: what problem it solves, how it works step by step, the edge cases, the alternatives you rejected and why. 10 lines maximum, plain language.
```

### Session handoff
```
Write a handoff: what is done, what is in progress, what is next, open questions, commands to run, and the current state of each FEATURE_LOG.md row. Update FEATURE_LOG.md accordingly.
```
