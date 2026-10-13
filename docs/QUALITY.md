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

## 2. Before vs After Summary (To be finalized in Step 5)

| Metric | Baseline | Target / After |
|---|---|---|
| Backend Ruff Complexity Issues | 26 (19 prod) | Reduced (extracted helpers, HTTP client, exception mapping) |
| Backend Clones (jscpd) | 6 clones (78 lines) | Reduced (shared HTTP retry, unified validation) |
| Frontend Clones (jscpd) | 4 clones (61 lines) | Reduced (extracted common sx & card helpers) |
| Frontend Large Files (>250 lines) | 5 files | 0 files |
| Frontend Circular Dependencies | 0 | 0 |
| Knip Unused Exports | 2 exports | Cleaned |
