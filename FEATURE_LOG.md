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

### D-023 Operations Console Design Direction per DESIGN.md
- Date: 2026-10-10
- Type: decision
- Phase: P0
- Summary: Follow DESIGN.md: map-first full-bleed console, docked left control panel, Barlow and JetBrains Mono fonts, brand teal palette, RiskStrip component, driver icons on risk chips, compact bottom-left heatmap toolbar, strict ban on generic templates/gradients/blue defaults.
- Status: done

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
| F-001 | Project scaffold (backend Django/DRF, frontend Vite/React/TS, tooling) | P1 | planned |
| F-010 | Domain core: types, rules_config, risk assessment | P2 | planned |
| F-011 | Domain core: geometry (haversine, interpolation) & sampling | P2 | planned |
| F-012 | Domain core: timeline & ETA interpolation | P2 | planned |
| F-013 | Domain core: weather alignment & hourly interpolation | P2 | planned |
| F-014 | Domain core: scoring (miles by level, avg risk, delta) | P2 | planned |
| F-015 | Domain core: route ranking & deterministic recommendation | P2 | planned |
| F-020 | Provider base protocols & typed error hierarchy | P3 | planned |
| F-021 | Routing provider adapter (truck mode, polyline, timeline) | P3 | planned |
| F-022 | Route selection service (dedupe, detour filtering, via-fallback) | P3 | planned |
| F-023 | Open-Meteo provider adapter & per-cell cache | P3 | planned |
| F-024 | Geocoding adapter & `/api/geocode/` endpoint | P3 | planned |
| F-025 | Trip analysis service orchestrator | P3 | planned |
| F-026 | API layer: serializers, validation, container, `/api/trips/analyze/` | P3 | planned |
| F-030 | Frontend API client, typed DTOs, error parsing | P4 | planned |
| F-031 | TripForm & PlaceAutocomplete with validation | P4 | planned |
| F-032 | Results UI: RecommendationBanner, RouteCards, CheckpointTable | P4 | planned |
| F-033 | MapView: canvas render, route polylines, checkpoint markers, legend | P4 | planned |
| F-034 | UX states: idle, loading skeletons, error retry, no-safe-route alert | P4 | planned |
| F-040 | Heatmap backend: corridor grid generation & `/api/trips/heatmap/` | P5 | planned |
| F-041 | Heatmap frontend: useHeatmap, HeatmapLayer, 0-48h slider controls | P5 | planned |
| F-050 | Polish: responsive layout & mobile testing | P6 | planned |
| F-051 | Performance benchmarking (cold/warm analyze, payload sizes) | P6 | planned |
| F-052 | Slow-server banner & example trip preset | P6 | planned |
| F-053 | Accessibility & contrast review | P6 | planned |
| F-060 | Production deployment configuration | P7 | planned |
| F-061 | Comprehensive documentation & README | P7 | planned |
| F-062 | Fresh-clone verification test | P7 | planned |
| F-063 | Security audits (`pip-audit`, `npm audit`) | P7 | planned |
| F-064 | Tag `v1.0-submission` & final QA checklist | P7 | planned |

---

## 4. Changes

_None yet._

---

## 5. Fixes

_None yet._

---

## 6. Dependencies

_None yet. Pinned at install time per CODING_RULES §9._

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
