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

### D-006 Routing & Geocoding Provider Selection
- Date: 2026-10-10
- Type: decision
- Phase: P0
- Summary: Select routing and geocoding vendor based on P0 spike results (TomTom vs HERE).
- Status: in progress

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
| F-000 | Provider spike (TomTom/HERE + Open-Meteo) | P0 | in progress |
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

1. **TomTom vs HERE Routing Limits & Truck Mode**: Evaluate real response structure, number of alternatives returned, and whether commercial/truck parameters are supported without credit card in P0 spike.
2. **Open-Meteo multi-location call accounting**: Confirm whether multi-point comma-delimited coords work as documented with `past_hours=3` and `forecast_hours=288`.
3. **Python Version**: Local system has Python 3.10 and 3.13. Target in PROJECT_CONTEXT is 3.12. (Decision: use 3.12 if installed or compatible 3.10/3.13 virtualenv).
