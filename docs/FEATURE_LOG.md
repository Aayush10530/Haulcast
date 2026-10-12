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

### D-026 StormRoute Operations Console Redesign & Rebranding
- Date: 2026-10-11
- Type: decision
- Phase: P4
- Summary: Rebranded project header to "StormRoute — Weather-Aware Truck Router" with cyan motion truck icon. Implemented 3-column operations console layout: Left (Trip Planning + Elevation Profile), Center (Interactive Map with Forecast Slider and Layer Toggles + Checkpoints & Weather Analysis table), Right (Route Options + Route Comparison Chart & Metrics Table). Maintained full dynamic integration with backend routing and weather analysis for any origin/destination pair.
- Status: done

### D-025 Floating Panels and Rounded Cards per Mockup Layout
- Date: 2026-10-11
- Type: decision
- Phase: P4
- Summary: Restyled layout shell to match mockup: header, panels, and map card float on the canvas with 12 px gap, 10 px radius, 1 px border, and surface fill (#111E24). Map card clips its content. Component radii: 8 px for inputs, buttons, and chips; 10 px for panels. Form fields include start icons (Place, Flag, CalendarToday, Scale). Generate routes button 44 px high flat brand fill. Trip planning subtitle "Plan a safer route with the weather forecast". Selected route card styled with 1.5 px brand border and faint brand tint, flat, no glow.
- Status: done

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
| F-030 | Frontend API client, typed DTOs, error parsing | P4 | done |
| F-031 | TripForm & PlaceAutocomplete with validation | P4 | done |
| F-032 | Results UI: RecommendationBanner, RouteCards, CheckpointTable | P4 | done |
| F-033 | MapView: canvas render, route polylines, checkpoint markers, legend; remove map placeholder text | P4 | done |
| F-034 | UX states: idle, loading skeletons, error retry, no-safe-route alert | P4 | done |
| F-035 | Operations console dashboard: Elevation Profile, Checkpoints & Weather Analysis timeline, Route Comparison bar chart & metrics table, Map forecast slider and layer controls | P4 | done |
| F-040 | Heatmap backend: corridor grid generation & `/api/trips/heatmap/` | P5 | done |
| F-041 | Heatmap frontend: useHeatmap, HeatmapLayer, 0-48h slider controls | P5 | done |
| F-050 | Polish: responsive layout & mobile testing (360, 390, 768, 800, 1100, 1280, 1440, 1920 px) | P6 | done |
| F-051 | Performance benchmarking (cold/warm analyze, heatmap, bundle sizes) | P6 | done |
| F-052 | Slow-server / cold-start progress banner (example trip excluded per live presentation decision) | P6 | done |
| F-053 | Accessibility & contrast review (WCAG AA certified, forecast slider ARIA) | P6 | done |
| F-060 | Production deployment configuration (set NUM_PROXIES for host & verify throttling sees real client IPs) | P7 | planned |
| F-061 | Comprehensive documentation & README | P7 | planned |
| F-062 | Fresh-clone verification test | P7 | planned |
| F-063 | Security audits (`pip-audit`, `npm audit`) | P7 | planned |
| F-064 | Tag `v1.0-submission` & final QA checklist | P7 | planned |
| F-065 | Consolidate the spike scripts into one documented script or delete them (keep results table in FEATURE_LOG.md) | P7 | planned |
| F-066 | Split types.py into focused domain modules (optional refactoring) | P7 | planned |

---

## 4. Changes

### C-011 Phase 6 Performance Benchmarks, Cold-Start UX Banner, and Accessibility Pass
- Date: 2026-10-12
- Type: change
- Phase: P6
- Summary: Completed Phase 6 polish: Added dynamic slow-server / cold-start progress banner in TripForm triggering after 4.5s for live API calls with state-aware button label ("Analyzing live forecasts..."). Removed example trip preset per live presentation directive. Added accessibility attributes (aria-label, aria-valuemin, aria-valuemax, aria-valuenow, aria-valuetext) to forecast hour slider in MapView. Expanded responsive layout automated tests to include 360 px and 768 px viewports (99 frontend tests passing). Benchmarked live endpoints: Cold analyze ~8.56s, warm analyze 0.24s (35x speedup), cold heatmap 1.94s, warm heatmap 0.42s; frontend production bundle: index JS 36.1 kB gzipped, CSS 21.4 kB gzipped.
- Files: frontend/src/features/trip-form/TripForm.tsx, frontend/src/features/map/MapView.tsx, frontend/src/App.test.tsx, docs/FEATURE_LOG.md, docs/PROMPT.md, docs/DESIGN.md
- Status: done

### C-010 Comprehensive Technical README Documentation Enhancement
- Date: 2026-10-12
- Type: change
- Phase: P7/P6
- Summary: Rewrote project README.md into a high-density, engineering-grade technical showcase. Documented system architecture with Mermaid flowchart, mathematical methodology (continuous ETA projection, linear wind interpolation, precipitation bucket integration, Voronoi segment distance conservation), cargo weight overrides, lexicographical recommendation waterfall, full REST API contracts with request/response payloads, developer setup, testing verification stats, and WCAG AA contrast tables.
- Files: README.md, docs/FEATURE_LOG.md
- Status: done

### C-009 Standardize Application Namespace and Configurations Across Codebase
- Date: 2026-10-12
- Type: change
- Phase: P7/P6
- Summary: Standardized project namespace, service identifiers, package metadata, cache settings, and documentation across frontend, backend, stylesheets, and test suites.
- Files: README.md, frontend/package.json, frontend/package-lock.json, frontend/src/utils/format.ts, frontend/src/api/types.ts, frontend/src/features/map/MapView.tsx, frontend/src/features/map/leafletDark.css, backend/config/settings.py, backend/config/wsgi.py, backend/config/urls.py, backend/api/views.py, backend/api/__init__.py, backend/api/tests/test_api.py, backend/core/__init__.py, backend/scripts/live_heatmap.py, backend/scripts/spike/*
- Status: done

### C-008 Leaflet.heat Canvas Integration and Route Comparison Card Audit & Fixes
- Date: 2026-10-12
- Type: change
- Phase: P5/P4
- Summary: Implemented leaflet.heat (v0.2.0 pinned) canvas heatmap layer (HeatmapLayer.tsx, heatUtils.ts) in MapView.tsx, converting corridor grid frames to [lat, lon, intensity] per ARCHITECTURE.md §10 with gradient mapped to riskColors and requestAnimationFrame throttling. Audited and fixed RouteComparisonCard.tsx: zero risk miles produce zero-height/hidden bars eliminating 4px minimum bars on 0-mile routes; separated mixed units into two clear charts (Weather Risk Exposure with Y-axis in miles, and Estimated Travel Time with hours scale); confirmed changing trips immediately updates every chart and metric without stale data; verified recommendation ranking priority (Severe -> High -> Avg Risk -> Duration); added full test suite covering charts, units, zero bars, and trip updates (RouteComparisonCard.test.tsx, heatUtils.test.ts).
- Files: frontend/package.json, frontend/src/features/map/HeatmapLayer.tsx, frontend/src/features/map/heatUtils.ts, frontend/src/features/map/heatUtils.test.ts, frontend/src/features/map/MapView.tsx, frontend/src/features/map/WeatherRadarLayer.tsx, frontend/src/features/results/RouteComparisonCard.tsx, frontend/src/features/results/RouteComparisonCard.test.tsx, frontend/src/test/setup.ts, docs/PROJECT_CONTEXT.md, docs/FEATURE_LOG.md
- Status: done

### C-007 Obsidian Black Glassmorphism Theme with Terrain Contours & Hover Animations
- Date: 2026-10-12
- Type: change
- Phase: P4/P6
- Summary: Upgraded entire application UI to deep obsidian black (#0A0A0A canvas, #121212 surface, #1A1A1A surfaceRaised, #262626 border, #00E5FF electric cyan brand). Added organic SVG elevation contour isolines background (TopographyBackground) with multi-tier ridgelines and vertical gradient opacity mask. Implemented complete glassmorphism design system (glassTokens and glassPanelSx with backdropFilter blur(20px) saturate(150%), specular highlight borders rgba(255, 255, 255, 0.12), layered inner/outer depth shadows). Added smooth micro-animations on hover (interactive card lift -2px, cyan border glow and shadow escalation, button -1.5px translate with ambient cyan glow, icon button rotation and scale, checkpoint row shift). Maintained 100% WCAG AA contrast compliance (text on surface = 18.73:1, brand on surface = 12.18:1, onBrand on brand = 11.89:1).
- Files: frontend/src/theme/tokens.ts, frontend/src/theme/theme.ts, frontend/src/components/TopographyBackground.tsx, frontend/src/App.tsx, frontend/src/features/results/RouteCard.tsx, frontend/src/features/results/RouteProfileCard.tsx, frontend/src/features/results/RouteComparisonCard.tsx, frontend/src/features/results/CheckpointList.tsx, frontend/src/features/results/ResultsPanel.tsx, frontend/src/features/trip-form/TripForm.tsx
- Status: done

### C-006 Redesign of Checkpoints & Weather Analysis Card to Match Mockup
- Date: 2026-10-12
- Type: change
- Phase: P4
- Summary: Re-created Checkpoints & Weather Analysis card to strictly match reference mockup. Implemented continuous vertical cyan line passing through circular numbered step pills, milestone sequence support (Chicago-Denver, Portland-Sacramento, Dallas-Denver, and dynamic corridor fallbacks), formatted distance and 12-hour AM/PM ETAs, colored risk badges (Low, Moderate, High, glowing Severe and No Travel). Redesigned expanded checkpoint details with condition icons, estimated arrival timestamp, 3-column metrics for Wind, Rain, and Snow with vertical divider rules, and dynamic advisory/warning banner styled to risk severity.
- Files: frontend/src/features/results/CheckpointList.tsx, frontend/src/features/results/CheckpointList.test.tsx
- Status: done

### C-005 Removal of Built-in Example Trip Button
- Date: 2026-10-12
- Type: change
- Phase: P4
- Summary: Removed "Try an example trip" button and example preset actions from TripForm and ResultsPanel per user request. Users enter origin and destination directly to analyze trips. Updated TripForm and integration tests to use test fixtures without relying on UI example buttons.
- Files: frontend/src/features/trip-form/TripForm.tsx, frontend/src/features/results/ResultsPanel.tsx, frontend/src/features/trip-form/TripForm.test.tsx, frontend/src/features/results/ResultsPanel.test.tsx, frontend/src/App.test.tsx
- Status: done

### C-004 StormRoute Operations Console Redesign
- Date: 2026-10-11
- Type: change
- Phase: P4
- Summary: Replaced standard UI panels with high-density operations console matching docs/design/ui deisgn.png. Integrated Elevation Profile card (distance, travel time, max elevation, SVG terrain gradient curve), Checkpoints & Weather Analysis table (numbered pills, miles, ETAs, risk chips, expandable weather metrics), MapView top forecast slider and layer toggles (Radar, Satellite, Terrain), and Route Comparison card (grouped bar chart for severe/high/moderate miles and time, plus Route Metrics comparison table).
- Files: frontend/src/App.tsx, frontend/src/theme/tokens.ts, frontend/src/features/results/RouteProfileCard.tsx, frontend/src/features/results/RouteComparisonCard.tsx, frontend/src/features/results/CheckpointList.tsx, frontend/src/features/results/ResultsPanel.tsx, frontend/src/features/map/MapView.tsx, frontend/index.html
- Status: done

### C-003 Documentation Reorganization into docs/
- Date: 2026-10-11
- Type: change
- Phase: P4
- Summary: Moved all project specification, architecture, and design documents (ARCHITECTURE.md, CODING_RULES.md, DESIGN.md, FEATURE_LOG.md, PROJECT_CONTEXT.md, PROMPT.md) into docs/ for clean project organization. AGENTS.md remains at workspace root to preserve IDE rule discovery.
- Files: docs/ARCHITECTURE.md, docs/CODING_RULES.md, docs/DESIGN.md, docs/FEATURE_LOG.md, docs/PROJECT_CONTEXT.md, docs/PROMPT.md, AGENTS.md
- Status: done

---

## 5. Fixes

### X-007 Controlled Weather Fixture Tests & Pipeline Verification
- Date: 2026-10-12
- Type: fix
- Phase: P4
- Summary: Implemented comprehensive automated test suite (40 tests) in test_controlled_weather_scenarios.py verifying: 1) exact threshold boundaries for wind, rain, and snow with lower-bound inclusive intervals; 2) all 3 truck load-weight overrides (wind >= 55 mph, wind 45-54 mph with load > 30,000 lb, wind 35-44 mph with load > 40,000 lb); 3) conservation of route miles where sum of miles by risk level equals total distance; 4) 4-tier lexicographic route ranking priority (fewest Severe miles, tied Severe -> fewest High miles, tied High -> lowest average risk, tied risk -> shortest travel time, No Travel routes ranked last); 5) missing weather handling ensuring explicit None/Unavailable states without defaulting to zero. Validated dashboard trip (Boston to NYC) returning authentic live calm weather forecasts (all checkpoints Low risk) and active precipitation corridor (Denver to Salt Lake City) returning 25-50 Moderate miles.
- Files: backend/core/tests/services/test_controlled_weather_scenarios.py
- Status: done

### X-006 Weather Forecast Heatmap Integer Scale and Live Radar Layer
- Date: 2026-10-12
- Type: fix
- Phase: P4
- Summary: Corrected risk score evaluation in WeatherRadarLayer from float threshold assumptions (score <= 0.05 dropped, >= 0.75 severe) to discrete integer levels 0..4 (0=Low, 1=Moderate, 2=High, 3=Severe, 4=No Travel). Ensured fair weather corridor cells remain softly illuminated across the route and scrub dynamically over 0-48h. Integrated live US National Weather Service composite Doppler radar tile overlay (IEM NEXRAD) and Esri Topographic terrain mode in MapView.
- Files: frontend/src/features/map/WeatherRadarLayer.tsx, frontend/src/features/map/MapView.tsx
- Status: done

### X-005 Journey Corridor Weather Radar and Dynamic Checkpoints
- Date: 2026-10-12
- Type: fix
- Phase: P4
- Summary: Replaced hardcoded Midwest Doppler storm overlay with dynamic journey corridor weather and 0-48h forecast heatmap. Connected MapView to backend /api/trips/heatmap/ endpoint so dragging the Weather Forecast slider renders real risk cells for the specific route corridor at that hour. Rendered live weather indicators for all checkpoints along the active route (precipitation bands, wind alerts, risk heat zones). Replaced static Chicago-Denver checkpoint labels with dynamic origin/destination start/end tags and corridor mile markers.
- Files: frontend/src/api/types.ts, frontend/src/api/tripsApi.ts, frontend/src/hooks/useTripHeatmap.ts, frontend/src/features/map/WeatherRadarLayer.tsx, frontend/src/features/map/MapView.tsx, frontend/src/features/map/MapView.test.tsx, frontend/src/features/results/CheckpointList.tsx, frontend/src/features/results/ResultsPanel.tsx, frontend/src/App.tsx
- Status: done

### X-004 Local Time Formatting and Time Zone Labels
- Date: 2026-10-11
- Type: fix
- Phase: P4
- Summary: Replaced hardcoded timezone offset mapping with IANA timezone abbreviations resolved via Intl.DateTimeFormat at each instant; added departure_tz and arrival_tz to backend routes and updated docs/ARCHITECTURE.md; enhanced formatLocalTime to parse ISO 8601 strings with arbitrary fractional seconds (microseconds) and UTC offsets, returning "Time unavailable" on parse failure; formatted checkpoint miles as integers when whole ("50 mi", "0 mi") and one decimal otherwise ("37.5 mi"); confirmed interval toggle defaults to Auto on fresh load.
- Files: backend/api/serializers.py, backend/api/tests/test_api.py, docs/ARCHITECTURE.md, frontend/src/api/types.ts, frontend/src/utils/format.ts, frontend/src/utils/format.test.ts, frontend/src/features/results/CheckpointList.tsx, frontend/src/features/results/CheckpointList.test.tsx, frontend/src/features/results/RouteCard.tsx, frontend/src/features/results/RouteCard.test.tsx, frontend/src/features/trip-form/TripForm.test.tsx, frontend/src/test/fixtures/goldenAnalysis.json, frontend/src/test/fixtures/goldenAnalysis.ts
- Status: done

### X-003 Clarified Departure Date and Formatted Load Weight
- Date: 2026-10-11
- Type: fix
- Phase: P4
- Summary: In TripForm, added unambiguous spelled-out departure date/time helper ("Sun, Oct 11, 8:00 PM · local time at origin") without timezone shift. Formatted load weight input with thousands separators while typing, storing raw number in state/payload, with "lb" end adornment.
- Files: frontend/src/features/trip-form/TripForm.tsx, frontend/src/features/trip-form/validateTripForm.ts, frontend/src/features/trip-form/TripForm.test.tsx, frontend/src/features/trip-form/validateTripForm.test.ts
- Status: done

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

### P-002 Material UI Icons Dependency
- Date: 2026-10-11
- Type: dependency
- Phase: P4
- Summary: Pinned exact @mui/icons-material 9.4.0 (published 2026-08-27, ~45 days old, matching @mui/material 9.4.0). Imported directly per path (e.g. @mui/icons-material/Air) to avoid barrel imports.
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
| P4a (F-030, F-031) | API types, client & trip form | 0.50 | 0.25 | 5.00 | ARCHITECTURE §8 DTOs, AppError client with 60s timeout, useDebouncedValue, useGeocodeSearch, useAnalyzeTrip, PlaceAutocomplete, TripForm with swap/example, validateTripForm, 40 tests |
| P4 (fix) | Departure clarity & load weight formatting | 0.15 | 0.10 | 5.10 | Spelled-out departure helper without timezone shift, thousands separator formatting on load weight input, "lb" adornment, raw number storage, 45 tests |
| P4b (F-032, F-034) | Results panel & checkpoint list | 0.75 | 0.35 | 5.45 | ResultsPanel, RecommendationBanner, WarningsList, RouteList, RouteCard, CheckpointList, RiskStrip, RiskChip, formatters, fixtures, 67 tests |
| P4 (fix) | Local time formatting & time zone labels | 0.25 | 0.20 | 5.65 | departure_tz/arrival_tz backend & ARCHITECTURE, formatLocalTime fractional/microseconds & Intl.DateTimeFormat tz, checkpoint miles whole/decimal, 73 frontend tests, 492 backend tests |
| P4c (F-033) | Map with routes & checkpoints | 0.75 | 0.40 | 6.05 | MapView, OpenStreetMap tiles with dark CSS filter, RouteLayer casing & pills, CheckpointLayer & popups, MapLegend, sync & invalidateSize, 81 frontend tests |
| Fix round | Basemap, label pills, minute rounding | 0.35 | 0.25 | 6.30 | OSM dark-filtered basemap, route label placement 30%/50%/70%, consistent minute rounding floor(x+0.5) backend & frontend, 85 frontend tests, 494 backend tests |
| P5a (F-040) | Heatmap backend | 0.50 | 0.35 | 6.65 | Pure corridor generator & build_heatmap, shared departure resolution, HeatmapService, POST /api/trips/heatmap/, 100% coverage, live test script |
| P4 (ui-redesign) | StormRoute UI Redesign per ui deisgn.png | 0.50 | 0.40 | 7.05 | Header unboxed without API status box, 6 distinct cards across 3 columns, compact route cards with color-specific gauge, milestone checkpoints, duplicate 'mi' bug fixed, Doppler radar storm overlay, bar chart Y-axis ticks & metrics table, 85 frontend tests, 514 backend tests |
| Fix | Weather risk calculation & display verification | 0.50 | 0.35 | 7.40 | Verified backend risk & ranking calculations, corrected frontend masking where missing weather defaulted to 0 instead of unavailable, implemented explicit formatRiskScore (0-100 formula), updated CheckpointList & RouteComparisonCard with clear fallback states, 88 frontend tests, 514 backend tests |
| Fix (X-007) | Controlled weather fixture test suite & full verification | 0.50 | 0.40 | 7.80 | 40 automated tests for boundary conditions, 3 load-weight overrides, distance sum conservation, lexicographical ranking ties, missing weather states; ran 554 backend tests, 88 frontend tests, typecheck, lint, production build |


