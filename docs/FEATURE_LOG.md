# FEATURE_LOG.md

> Every feature, change, fix and decision, newest first within each section. Append after every change. Never delete entries; mark them superseded instead.

---

## 1. Entry format

```markdown
### [ID] Title
- Date: YYYY-MM-DD
- Type: feature | change | fix | decision | dependency
- Phase: P0..P7
- Summary: what and why, in one or two lines
- Files: paths touched (code entries)
- Status: planned | in progress | done | superseded by [ID]
```

IDs: `F-xxx` features, `C-xxx` changes, `X-xxx` fixes, `D-xxx` decisions, `P-xxx` dependencies.

---

## 2. Decisions

### D-024 dark flat theme per DESIGN.md v2
- Date: 2026-10-11
- Type: decision
- Phase: P4
- Summary: Visual direction version 2 (dark flat console, StormRoute header, Barlow & JetBrains Mono, canvas #0B1418, surface #111E24, brand #2DB8C5, risk fills with text #07171C, 3-column >= 1440 px, 2-column 900-1439 px, mobile tabs < 900 px). Supersedes D-023.
- Status: done

### D-023 Operations Console Design Direction per DESIGN.md
- Date: 2026-10-10
- Type: decision
- Phase: P0
- Summary: Follow DESIGN.md: map-first full-bleed console, docked left control panel, Barlow and JetBrains Mono fonts, brand teal palette, RiskStrip component, driver icons on risk chips, compact bottom-left heatmap toolbar, strict ban on generic templates/gradients/blue defaults.
- Status: superseded by D-024

### D-022 Open-Meteo Chunk Size 100 and Request-Index Mapping
- Date: 2026-10-10
- Type: decision
- Phase: P0
- Summary: Open-Meteo batch chunk size set to 100 coordinates (~1.2s, 0.96 MB payload); map weather responses strictly by request array index (Open-Meteo preserves request order) never by float lat/lon equality; do not compare unit label strings (API returns "mp/h").
- Status: done

### D-021 Parallel Via Fallback & Lowest-Overlap Selection
- Date: 2026-10-10
- Type: decision
- Phase: P0
- Summary: When fewer than 3 native routes are returned, dispatch all 4 via fallback requests in parallel (completes in 1.6–3.9s wall time) and select the lowest-overlap qualifying candidate (<85% overlap, <1.6x duration) rather than the first.
- Status: done

### D-020 vehicleMaxSpeed=105 km/h (65 mph) Governor Limit
- Date: 2026-10-10
- Type: decision
- Phase: P0
- Summary: Set vehicleMaxSpeed=105 (km/h ~ 65 mph) in TomTom routing requests as domain constant TRUCK_MAX_SPEED_KMH in rules_config.py to realistically govern commercial truck travel times across interstate corridors.
- Status: done

### D-019 Baseline Truck Routing with traffic=false
- Date: 2026-10-10
- Type: decision
- Phase: P0
- Summary: TomTom requests set traffic=false for deterministic, reproducible route ETAs without live congestion variance, matching A-08 / A-18 continuous driving specification while still providing full instructions and alternatives.
- Status: done

### D-018 Python 3.13 Runtime Confirmed
- Date: 2026-10-10
- Type: decision
- Phase: P0
- Summary: Python 3.13 is installed on host system and verified compatible with backend stack (stdlib, httpx, respx, Django).
- Status: done

### D-006 TomTom Routing & Geocoding Provider Decided
- Date: 2026-10-10
- Type: decision
- Phase: P0
- Summary: TomTom chosen for routing and geocoding. Spike verified: truck travelMode works out of the box, maxAlternatives 0-5 supported, exact monotonic cumulative instruction times matching route summaries, 4 long US pairs tested, and fallback via-waypoint routing successfully produced qualifying third routes on both 2-route pairs.
- Status: done

### D-005 Heatmap Representation and Architecture
- Date: 2026-10-10
- Type: decision
- Phase: P5
- Summary: 49-frame precomputed hourly risk array (0..48h) delivered via `/api/trips/heatmap/` with client-side Leaflet canvas scrub.
- Status: done

### D-004 Open-Meteo as Weather Provider
- Date: 2026-10-10
- Type: decision
- Phase: P0
- Summary: Free tier /v1/forecast without API key; 0.1° grid snapping; chunked multi-coordinate requests with past/forecast hours window.
- Status: done

### D-003 Strict Additive Load Rules and Lexicographic Ranking
- Date: 2026-10-10
- Type: decision
- Phase: P2
- Summary: Load rules only elevate risk; ranking strictly checks No Travel miles, Severe miles, High miles, Avg risk, Travel time (A-04, A-10, A-11).
- Status: done

### D-002 Boundary Convention and Pre-Classification Rounding
- Date: 2026-10-10
- Type: decision
- Phase: P2
- Summary: Lower bound inclusive for risk intervals; round measurements before classification (wind 1 dec, precip 2 dec) to avoid UI contradiction (A-02, A-03).
- Status: done

### D-001 Architecture and Layer Isolation
- Date: 2026-10-10
- Type: decision
- Phase: P1
- Summary: React/MUI/Leaflet frontend, Django/DRF API layer, pure domain logic (no I/O, no Django), provider abstractions (A-18, ARCHITECTURE.md).
- Status: done

---

## 3. Features

| ID | Feature | Phase | Status |
|---|---|---|---|
| F-000 | Provider spike (TomTom + Open-Meteo) | P0 | done |
| F-001 | Project scaffold (backend Django/DRF, frontend Vite/React/TS, tooling) | P1 | done |
| F-010 | Domain core: types, rules_config, risk assessment | P2 | done |
| F-011 | Domain core: geometry (haversine, interpolation) & sampling | P2 | done |
| F-012 | Domain core: timeline & ETA interpolation | P2 | done |
| F-013 | Domain core: weather alignment & hourly interpolation | P2 | done |
| F-014 | Domain core: scoring (miles by level, avg risk, delta) | P2 | done |
| F-015 | Domain core: route ranking & deterministic recommendation | P2 | done |
| F-016 | Timezone conversion: local departure to UTC with DST edge cases (nonexistent local time rejected, ambiguous local time uses the first occurrence), UTC to local display, departure window check (now minus 1 h to now plus 7 days) | P2 | done |
| F-020 | Provider base protocols & typed error hierarchy | P3 | done |
| F-021 | Routing provider adapter (truck mode, polyline, timeline) | P3 | done |
| F-022 | Route selection service (dedupe, detour filtering, via-fallback) | P3 | done |
| F-023 | Open-Meteo provider adapter & per-cell cache | P3 | done |
| F-024 | Geocoding adapter & `/api/geocode/` endpoint | P3 | done |
| F-025 | Trip analysis service orchestrator (verify timeline.total_miles is within 0.01 mi of route distance, else raise ProviderBadResponse; assessed checkpoints built via assess_checkpoint) | P3 | done |
| F-026 | API layer: serializers, validation, container, `/api/trips/analyze/` (per-scope throttles: analyze, heatmap, geocode) | P3 | done |
| F-030 | Frontend API client, typed DTOs, error parsing | P4 | planned |
| F-031 | TripForm & PlaceAutocomplete with validation | P4 | planned |
| F-032 | Results UI: RecommendationBanner, RouteCards, CheckpointTable | P4 | planned |
| F-033 | MapView: canvas render, route polylines, checkpoint markers, legend; remove map placeholder text | P4 | planned |
| F-034 | UX states: idle, loading skeletons, error retry, no-safe-route alert | P4 | planned |
| F-040 | Heatmap backend: corridor grid generation & `/api/trips/heatmap/` | P5 | planned |
| F-041 | Heatmap frontend: useHeatmap, HeatmapLayer, 0-48h slider controls | P5 | planned |
| F-050 | Polish: responsive layout & mobile testing | P6 | planned |
| F-051 | Performance benchmarking (cold/warm analyze, payload sizes) | P6 | planned |
| F-052 | Slow-server banner & example trip preset | P6 | planned |
| F-053 | Accessibility & contrast review | P6 | planned |
| F-060 | Production deployment configuration (set NUM_PROXIES for host & verify throttling sees real client IPs) | P7 | planned |
| F-061 | Comprehensive documentation & README | P7 | planned |
| F-062 | Fresh-clone verification test | P7 | planned |
| F-063 | Security audits (`pip-audit`, `npm audit`) | P7 | planned |
| F-064 | Tag `v1.0-submission` & final QA checklist | P7 | planned |
| F-065 | Consolidate the spike scripts into one documented script or delete them (keep results table in FEATURE_LOG.md) | P7 | planned |
| F-066 | Split types.py into focused domain modules (optional refactoring) | P7 | planned |

---

## 4. Changes

### C-003 Documentation Reorganization into docs/
- Date: 2026-10-11
- Type: change
- Phase: P4
- Summary: Moved all project specification, architecture, and design documents (ARCHITECTURE.md, CODING_RULES.md, DESIGN.md, FEATURE_LOG.md, PROJECT_CONTEXT.md, PROMPT.md) into docs/ for clean project organization. AGENTS.md remains at workspace root to preserve IDE rule discovery.
- Files: docs/ARCHITECTURE.md, docs/CODING_RULES.md, docs/DESIGN.md, docs/FEATURE_LOG.md, docs/PROJECT_CONTEXT.md, docs/PROMPT.md, AGENTS.md
- Status: done

---

## 5. Fixes

### X-002 Responsive Layouts and Mobile Tab Bar Below 1440 px
- Date: 2026-10-11
- Type: fix
- Phase: P4
- Summary: Replaced unconditional HTML `hidden` attribute with breakpoint-aware visibility so map region shows in 1100 px two-column layout; mounted mobile tab bar only below 900 px with safe-area padding and 100dvh root height.
- Files: frontend/src/App.tsx, frontend/src/App.test.tsx, frontend/src/test/setup.ts
- Status: done

### X-001 Comparison with Fastest Route in Recommendation
- Date: 2026-10-11
- Type: fix
- Phase: P3
- Summary: Compare winner against the fastest route overall (if winner is not fastest) instead of runner-up in ranking.py, ensuring accurate headline and deciding factor explanations when a safer route is slower.
- Files: backend/core/domain/ranking.py, backend/core/tests/domain/test_ranking.py
- Status: done

---

## 6. Dependencies

### P-001 P1 Scaffold Dependencies
- Date: 2026-10-10
- Type: dependency
- Phase: P1
- Summary: Pinned exact dependencies audited >= 14 days old as of 2026-10-10. Backend: Django 5.2.17 + DRF 3.18.1 on Python 3.13; Frontend: React 19.3.0 + MUI 9.4.0 + Vite 6.4.3 + Vitest 4.1.11. pip-audit and npm audit zero vulnerabilities.
- Status: done

---

## 7. Open questions

1. **TomTom vs HERE Routing Limits & Truck Mode**: Resolved by D-006 (TomTom chosen).
2. **Open-Meteo multi-location call accounting**: Resolved by D-004 & D-022 (batch chunk size 100, index mapping).
3. **Python Version**: Resolved by D-018 (Python 3.13 confirmed).
4. **Route Request Latency Optimization (F-021)**: Must tune route request latency during F-021 implementation (test maxAlternatives 2 vs 3, parallel fallback execution from the start); note that spike timings (~4-7s cold) were measured from India to US endpoints and will be faster on US-hosted environments.

---

## 8. Time log

| Phase | Description | Planned (h) | Actual (h) | Cumulative (h) | Notes |
|---|---|---|---|---|---|
| P0 | Provider spike, decisions | 0.75 | 0.75 | 0.75 | Evaluated Open-Meteo batching, TomTom truck routing, fallback, determinism |
| P1 | Scaffold, tooling | 0.5 | 0.5 | 1.25 | Backend Django 5.2/DRF scaffold, Frontend React 19/Vite/TS/MUI v9, tests & audits clean |
| P1 (cleanup) | Pre-P2 hardening | 0.25 | 0.25 | 1.50 | Settings security, WCAG AA contrast, coverage tooling |
| P2 (F-010) | Risk rules & types | 0.25 | 0.25 | 1.75 | Pure domain risk classification, load rules, describe formatting, 100% test coverage |
| P2 (F-011) | Geometry & sampling | 0.25 | 0.10 | 1.85 | Haversine, scaling, point_at_mile, iterative simplify, sampling, 100% test coverage |
| P2 (F-012) | Timeline & ETA interpolation | 0.25 | 0.15 | 2.00 | Pure domain Timeline dataclass, linear ETA interpolation, timezones & clamping, 100% test coverage |
| P2 (F-013) | Weather time alignment | 0.25 | 0.15 | 2.15 | HourlySeries & WeatherSeries, wind linear interpolation, precip bucket rule, 100% test coverage |
| P2 (F-014) | Scoring & route summary | 0.25 | 0.25 | 2.40 | AssessedCheckpoint, MilesByLevel, RouteSummary, fsum numerical precision, 100% test coverage |
| P2 (F-015) | Route ranking & recommendation | 0.25 | 0.20 | 2.60 | Lexicographic sort key, DecidingFactor mapping, headline templates, time clause, 100% test coverage |
| P2 (F-016) | Timezone conversion & departure window | 0.25 | 0.15 | 2.75 | local_to_utc, utc_to_local, DST gap & fold=0 resolution, window validation, 100% test coverage |
| P3a (F-020, F-021) | Provider base interfaces & TomTom adapter | 0.50 | 0.35 | 3.10 | Protocols, typed errors, in-memory fakes, TomTom truck adapter with retries/timeline, live tests |
| P3b (F-022) | Route diversity & selection service | 0.50 | 0.25 | 3.35 | Pure domain route diversity & selection (grid hash, 100% coverage), RouteSelectionService with parallel via fallback & caching (100% coverage) |
| P3c (F-023) | Open-Meteo weather adapter & cache | 0.50 | 0.35 | 3.70 | Grid snapping/centering, DjangoCache & InMemoryTTLCache, OpenMeteoWeatherProvider (chunking, threading, index mapping, rain sum, retry), live script |
| P3d (F-025) | Trip analysis orchestrator | 0.50 | 0.25 | 3.95 | TripRequest/Echo/TripAnalysis types, BeyondForecastHorizonError, TripAnalysisService (timeline check, dedupe cells, horizon check, load rules, warnings), 100% coverage |
| P3e (F-024, F-026) | API layer & geocoding | 0.50 | 0.35 | 4.30 | TomTomGeocodingProvider (100%), CachedGeocoding (100%), TripRequestSerializer, API views & URLs, custom error envelope, scoped throttles, GZip/CORS |
| P3 (complete) | Provider & API orchestration review | 0.25 | 0.15 | 4.45 | Verified P3 end-to-end: ranking explanation compared against fastest, cold/warm timings recorded (cold 10.33s / warm 0.18s), P3 complete |
| P4 (shell) | Dark theme & responsive app shell | 0.50 | 0.30 | 4.75 | DESIGN.md v2 tokens, risk colors (#07171C text, 100% WCAG AA), theme.ts, StormRoute header, 3-column / 2-column / mobile tab responsive shell, GET /api/health/ status dot |
