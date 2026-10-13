# QUALITY.md

Code quality baseline metrics, complexity gates, and refactoring tracking.

---

## 1. Baseline Measurements (Step 1)

Date: 2026-10-13

### Backend Quality Metrics

#### Ruff Complexity (`--select C901,PLR0911,PLR0912,PLR0913,PLR0915 core api`)
- **Total Diagnostic Issues**: 26 (19 in core/api production code, 7 in test helpers)
- **Top Offenders**:
  1. `api/errors.py`: `custom_exception_handler` — complexity 18 (C901), 12 returns (PLR0911), 20 branches (PLR0912)
  2. `core/providers/weather_openmeteo.py`: `_parse_weather_series` — complexity 21 (C901), 24 branches (PLR0912), 63 statements (PLR0915)
  3. `core/services/trip_analysis.py`: `TripAnalysisService.analyze` — complexity 14 (C901), 13 branches (PLR0912), 62 statements (PLR0915)
  4. `core/domain/corridor.py`: `generate_corridor_cells` — complexity 15 (C901), 15 branches (PLR0912)
  5. `core/providers/geocoding_tomtom.py`: `search` — complexity 13 (C901), 13 branches (PLR0912); `_execute_request` — complexity 11 (C901)
  6. `core/providers/routing_tomtom.py`: `_execute_request` — complexity 11 (C901); `_parse_timeline` — complexity 11 (C901)
  7. `core/providers/weather_openmeteo.py`: `_execute_request` — complexity 12 (C901); `__init__` — 6 args (PLR0913)
  8. `core/domain/types.py`: `RawRoute.__post_init__` — complexity 11 (C901)
  9. `core/domain/ranking.py`: `_comparison_message` — 8 returns (PLR0911)

#### Backend Code Duplication (`npx jscpd core api --min-lines 6 --min-tokens 50 --ignore "**/tests/**"`)
- **Files Analyzed**: 29
- **Total Lines**: 4,213
- **Total Tokens**: 22,869
- **Clones Found**: 6
- **Duplicated Lines**: 78 (1.85%)
- **Duplicated Tokens**: 468 (2.05%)
- **Top Offenders**:
  1. `providers/geocoding_tomtom.py` [22-51] vs `providers/routing_tomtom.py` [89-118] (HTTP retry and exception mapping: 30 lines, 160 tokens)
  2. `domain/types.py` [449-455] vs [563-569] (coordinate sequence validation: 7 lines, 66 tokens)
  3. `domain/types.py` [479-486] vs [623-630] (warning tuple normalization: 8 lines, 61 tokens)
  4. `domain/weather_align.py` [17-26] vs [56-65] (time window arithmetic: 10 lines, 61 tokens)
  5. `providers/geocoding_tomtom.py` [86-95] vs `providers/routing_tomtom.py` [197-206] (10 lines, 60 tokens)
  6. `services/heatmap_service.py` [29-41] vs `services/trip_analysis.py` [31-43] (constructor dependencies: 13 lines, 60 tokens)

#### Dead Code (`vulture core api --min-confidence 80`)
- **Unused Items Found**: 2
  - `api/tests/test_api.py:232`: unused variable `args` (100% confidence)
  - `api/tests/test_api.py:232`: unused variable `kwargs` (100% confidence)
- **Production Code Unused Items**: 0

---

### Frontend Quality Metrics

#### Frontend Code Duplication (`npx jscpd src --min-lines 8 --min-tokens 60 --ignore "**/*.test.*,**/fixtures/**"`)
- **Files Analyzed**: 39
- **Total Lines**: 6,371
- **Total Tokens**: 33,257
- **Clones Found**: 4
- **Duplicated Lines**: 61 (0.96%)
- **Duplicated Tokens**: 270 (0.81%)
- **Top Offenders**:
  1. `components/RiskStrip.tsx` [35-51] vs [65-81] (17 lines, 67 tokens)
  2. `features/results/RouteProfileCard.tsx` [121-139] vs [146-164] (19 lines, 76 tokens)
  3. `features/results/RouteProfileCard.tsx` [100-114] vs [125-139] (15 lines, 61 tokens)
  4. `test/setup.ts` [37-46] vs [47-56] (10 lines, 66 tokens)

#### Dead Code & Unused Exports (`npx knip`)
- **Unused devDependencies**: 2 (`jscpd`, `madge`)
- **Unused exports**: 2 (`API_BASE_URL` in `src/api/client.ts:9`, `fetchHealth` in `src/api/client.ts:143`)
- **Unused exported types**: 22 (interfaces exported from leaf components)

#### Circular Dependencies (`npx madge --circular --extensions ts,tsx src`)
- **Processed Files**: 64
- **Circular Dependencies**: 0

#### Large Files (>250 Lines)
- `frontend/src/features/results/CheckpointList.tsx`: 697 lines
- `frontend/src/features/results/RouteCard.tsx`: 375 lines
- `frontend/src/App.tsx`: 340 lines
- `frontend/src/features/trip-form/TripForm.tsx`: 326 lines
- `frontend/src/theme/theme.ts`: 260 lines
- `backend/core/domain/types.py`: 631 lines

---

## 2. Before vs After Summary (Final Step 5 Verification)

| Metric | Baseline (Step 1) | Post-Refactor (Step 5) | Status |
|---|---|---|---|
| **Backend Ruff Complexity Issues** | 26 (19 prod, 7 test) | **0 issues** (`All checks passed!`) | **100% Resolved** |
| **Backend Clones (`jscpd`)** | 6 clones (78 lines, 1.85%) | **4 clones (60 lines, 1.37%)** | **Reduced (2 clusters eliminated)** |
| **Backend Dead Code (`vulture`)** | 0 in prod (2 in test helpers) | **0 in prod (2 in test helpers)** | **Clean** |
| **Backend Large File (`types.py`)** | 631 lines | **69 lines** (split into 5 modular files <= 149 lines) | **Resolved** |
| **Frontend Large Files (>250 lines)** | 5 files (`CheckpointList`, `RouteCard`, `App`, `TripForm`, `theme`) | **0 files** (all targeted modules <= 245 lines) | **100% Resolved** |
| **Frontend Circular Dependencies (`madge`)** | 0 (64 files) | **0 (80 files)** | **Clean** |
| **Frontend Knip Unused Exports** | 2 exports (`API_BASE_URL`, `fetchHealth`) | **0 unused exports** | **100% Cleaned** |
| **Frontend Clones (`jscpd`)** | 4 clones (61 lines, 0.96%) | **4 clones (61 lines, 0.93%)** | **Maintained** |
| **Backend Test Suite (`pytest`)** | 565 passed | **565 passed** | **100% Passing** |
| **Frontend Test Suite (`vitest`)** | 107 passed (20 files) | **107 passed (20 files)** | **100% Passing** |
| **Frontend Typecheck (`tsc --noEmit`)** | 0 errors | **0 errors** | **Passing** |
| **Frontend ESLint** | 0 errors | **0 errors** | **Passing** |
| **Frontend Production Build** | Success | **Success (`vite build` in 4.58s)** | **Passing** |

---

## 3. Modular Architecture Breakdown

### Backend Decompositions
- **`core/providers/base_http.py`**: Extracted shared HTTP request, backoff, and retry logic.
- **`core/providers/weather_openmeteo.py`**: Split monolithic Open-Meteo series parsing into pure coordinate, series, and parameter extraction helpers.
- **`api/errors.py`**: Converted procedural branching exception handler into a declarative, table-driven dictionary mapping.
- **`core/services/trip_analysis.py`**: Decomposed `TripAnalysisService.analyze` into discrete private pipeline methods (`_resolve_route_alternatives`, `_generate_corridor_weather_grid`, `_align_and_assess_route`, etc.).
- **`core/domain/types.py` (69 lines)**: Deduplicated numeric & tuple validation into `_validation.py` (147 lines), and separated domain definitions into `risk_types.py` (140 lines), `route_types.py` (116 lines), `weather_types.py` (91 lines), and `analysis_types.py` (149 lines) with zero breaking changes via top-level re-exports.

### Frontend Decompositions (<250 Line Enforcement)
- **`theme/theme.ts` (79 lines)**: Extracted MUI component overrides into `componentOverrides.ts` (146 lines) and `inputOverrides.ts` (152 lines).
- **`CheckpointList.tsx` (168 lines)**: Extracted row rendering into `CheckpointItem.tsx` (208 lines), corridor milestone name mapping into `checkpointListUtils.ts` (216 lines), and vector icons into `CheckpointIcons.tsx` (48 lines).
- **`RouteCard.tsx` (245 lines)**: Extracted circular risk gauge into `RouteRiskGauge.tsx` (64 lines), weather exposure miles into `RouteWeatherMiles.tsx` (64 lines), and status/recommendation chips into `RouteCardTags.tsx` (91 lines).
- **`TripForm.tsx` (243 lines)**: Extracted origin/destination autocomplete into `TripPlacesInputs.tsx` (106 lines), checkpoint interval selector into `TripIntervalSelector.tsx` (64 lines), departure/weight fields into `TripDepartureWeightInputs.tsx` (94 lines), form header into `TripFormHeader.tsx` (33 lines), submit button into `TripSubmitButton.tsx` (44 lines), and feedback alerts into `TripFormAlerts.tsx` (61 lines).
- **`App.tsx` (229 lines)**: Extracted application branding and status indicators into `AppHeader.tsx` (142 lines) and mobile navigation tabs into `MobileBottomNav.tsx` (126 lines).
- **`api/client.ts` (154 lines)**: Cleaned unused exports (`API_BASE_URL`, `fetchHealth`), ensuring optimal tree-shaking and zero dead exports.

