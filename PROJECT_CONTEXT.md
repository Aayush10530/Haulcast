# PROJECT_CONTEXT.md

Project memory. Read this first in every session. Update it after any major change (CODING_RULES §12).

- Last updated: 2026-10-10
- Phase: P0 (not started)
- Owner: Aayush (directs the build; Antigravity writes code; Claude plans and reviews)

---

## 1. What this is

A weather-aware truck routing web app, built as a take-home assessment for Spotter.ai (Full Stack Developer, React + Django).

A truck driver enters origin, destination, departure date/time and load weight. The app:

1. gets 3 route options from a routing API,
2. samples weather every 10 / 25 / 50 miles along each route at the truck's ETA,
3. classifies risk per checkpoint with fixed rules,
4. recommends one route,
5. shows routes, checkpoints, risk, ETAs and summaries on a map,
6. shows a weather heatmap along the corridor with a 0-48 hour slider.

Hard limits: at most 4 days and 16 work hours. Deliverables: GitHub repo, hosted app, 5-10 min Loom.
The assessment's own rule: **"Prioritize correctness and clarity over extra features."**

## 2. Source of truth

Order of precedence: assessment snapshot (§3) > assumptions (§4) > this file > ARCHITECTURE.md > CODING_RULES.md.

If something is ambiguous and not covered in §4: stop and ask. Do not guess silently. Every new assumption goes into §4 and FEATURE_LOG.md.

## 3. Assessment snapshot (from the PDF, essentials kept verbatim)

**Inputs:** origin and destination; departure date/time; load weight.

**The app should:**
- Generate **3 route options** using a routing API.
- Sample weather every **10 / 25 / 50 miles**, using the truck's **estimated arrival time** at each checkpoint.
- Calculate weather risk using the provided risk/load rules.
- Recommend the best route, balancing **weather risk and travel time**.
- Show all routes, checkpoints, risk levels, ETAs, and route summaries on a map.
- Show a **weather heatmap along the trip corridor** with a **0-48 hour forecast slider**.
- Third-party APIs for routing, geocoding and weather are allowed. No routing engine needed.

**Risk thresholds (per checkpoint):**

| Condition | Low | Moderate | High | Severe | No Travel |
|---|---|---|---|---|---|
| Wind | <25 mph | 25-34 | 35-44 | 45-54 | >=55 mph |
| Rain | <0.10 in/hr | 0.10-0.25 | 0.25-0.50 | 0.50-1.00 | >1.00 |
| Snow | <0.5 in/hr | 0.5-1.0 | 1.0-2.0 | 2.0-3.0 | >3.0 |

**Load rules:**
- >=55 mph -> No Travel for any load
- 45-54 mph + >30,000 lb -> No Travel
- 35-44 mph + >40,000 lb -> Severe

**Route recommendation, prefer:** 1. fewest Severe miles, 2. fewest High miles, 3. lowest average risk, 4. shortest travel time.

**Deliverables:** GitHub repository, hosted application, 5-10 min Loom walkthrough.

**Evaluation:** 40% routes, weather, risk and recommendation logic. 35% UI, map and heatmap smoothness and performance. 10% code quality. 5% documentation and walkthrough.

**Submission (from the email):** attach links to the GitHub code, the hosted version and the Loom video, and upload them to the question in the email. Max 4 days and 16 work hours.

Effort follows the weights: roughly 40% of build effort on backend logic and its tests, 35% on map/heatmap/UI, the rest on code quality and docs.

## 4. Interpretations and assumptions

The spec has gaps. These are the decisions. Each must appear in the README and be explainable in the Loom.

| ID | Topic | Decision |
|---|---|---|
| A-01 | "Every 10 / 25 / 50 miles" | User picks 10, 25, 50 or Auto. Auto uses the longest route's distance: <=250 mi -> 10, <=800 mi -> 25, else 50. One interval for all 3 routes in a request. Checkpoints sit at mile 0, S, 2S, ... and always at the destination. |
| A-02 | Band boundaries | Lower bound inclusive. Wind: <25 Low, 25<=w<35 Moderate, 35<=w<45 High, 45<=w<55 Severe, >=55 No Travel. Rain: <0.10 Low, 0.10<=r<0.25 Moderate, 0.25<=r<0.50 High, 0.50<=r<=1.00 Severe, >1.00 No Travel. Snow: <0.5 Low, 0.5<=s<1.0 Moderate, 1.0<=s<2.0 High, 2.0<=s<=3.0 Severe, >3.0 No Travel. (The table has gaps like 34.5 mph and overlaps like 0.25 in/hr. This convention closes them.) |
| A-03 | Rounding | Round measurements before classifying, and show the same rounded values: wind to 1 decimal (mph), rain and snow to 2 decimals (in/hr). The UI must never show a value that contradicts its level. |
| A-04 | Load rules | They only raise risk, never lower it. "Over" is strict (30,000 lb exactly does not trigger). Final level = max(table level, load-rule level). Applied per checkpoint using the wind band (45<=w<55, 35<=w<45). |
| A-05 | Combining conditions | Checkpoint level = worst of wind, rain, snow, then load rules. The response says which factor drove it (`wind`, `rain`, `snow`, `load_rule`). |
| A-06 | Weather variables | Wind = sustained 10 m wind speed (mph). Rain = rain + showers (in/hr). Snow = snowfall (in/hr). No gusts in v1 (listed as a limitation). |
| A-07 | Time alignment | Wind is instantaneous: linear interpolation between the two surrounding hours. Rain and snow are "preceding hour" sums: use the bucket whose window contains the ETA (timestamp = floor(ETA hour) + 1h). |
| A-08 | ETA | Cumulative driving time along the route from the provider's data, interpolated by distance. Truck travel mode if the provider supports it. Continuous driving: no rest breaks, no hours-of-service, no live traffic. State this as a limitation. |
| A-09 | Miles and average risk | Each checkpoint covers half the gap to each neighbour (clipped to 0..route length). Severe/High miles are sums of covered miles. Average risk is mile-weighted on a 0-4 scale (Low 0, Moderate 1, High 2, Severe 3, No Travel 4). |
| A-10 | No Travel in ranking | The spec's ranking list omits it. Routes with any No Travel miles rank below all routes without; among those, fewer No Travel miles first, then the normal order. If every route has No Travel, still recommend the least bad one and show a clear "no safe route, consider delaying" warning. |
| A-11 | Ranking | Strict lexicographic: Severe miles, High miles, average risk, duration. Compare miles rounded to 0.1, average risk rounded to 0.01. The response states which criterion decided the winner and the time delta vs the fastest route. |
| A-12 | Departure time | The user enters local time at the origin. Backend converts to UTC with the origin's IANA timezone (zoneinfo). Allowed range: now minus 1 h to now plus 7 days, else a field error. Trip end must fall inside the weather window, else HTTP 422. |
| A-13 | Heatmap time | Slider has 49 steps: hour 0 = departure time floored to the hour (UTC), up to +48 h. Labels show origin-local time. |
| A-14 | Heatmap value | Per cell and hour: the same risk engine as checkpoints, including load rules. Layers: Overall (default), Wind, Rain, Snow. |
| A-15 | Load weight | Pounds, 0 to 120,000. A non-blocking warning above 80,000. |
| A-16 | Geography | Built and demoed for the contiguous US (mph, in/hr, lb). Other regions work only if the providers cover them. |
| A-17 | Always 3 routes | Best effort with a documented fallback (see ARCHITECTURE §6). If fewer than 3 distinct routes exist, return fewer plus a warning. Never fake a route. |
| A-18 | Out of scope | No auth, no accounts, no persistent database, no LLM calls, no hours-of-service, no live traffic, no mobile app. The recommendation logic is deterministic and explainable by design. |

## 5. Stack

Monorepo: `backend/` and `frontend/`. Pin exact versions at install time and record them in the dependency register (§9).

| Layer | Choice |
|---|---|
| Backend | Python 3.12, Django, Django REST Framework, django-cors-headers, httpx, gunicorn, tzdata |
| Backend tooling | ruff (lint + format), pytest, pytest-django, respx (mock HTTP) |
| Frontend | React 18 or 19 (match react-leaflet's peer dependency), Vite, TypeScript (strict), MUI, TanStack Query |
| Map | Leaflet + react-leaflet + leaflet.heat (canvas heat layer) |
| Frontend tooling | ESLint, Prettier, Vitest, React Testing Library |
| Cache | Django LocMemCache behind a `Cache` interface (swap point for Redis, not needed now) |
| Hosting | Frontend on Vercel or Netlify. Backend on Render, Railway or Fly. Final choice in F-060 |
| Weather | Open-Meteo (decided) |
| Routing + geocoding | Pending P0 spike. Candidates: TomTom, HERE |

## 6. External API facts

Checked against vendor docs on 2026-10-10 unless marked UNVERIFIED. Re-check anything marked UNVERIFIED in the P0 spike.

**Open-Meteo (weather, decided)**
- `/v1/forecast`, free for non-commercial use, no key. Limits: 600 calls/min, 5,000/hour, 10,000/day, 300,000/month. Attribution required (CC BY 4.0).
- Multiple coordinates per request (comma separated). Output becomes a list in the same order.
- Units: `wind_speed_unit=mph`, `precipitation_unit=inch`. Snowfall in inches then.
- `rain` is large-scale rain only. `showers` is convective. Rain rate = `rain + showers`.
- Precipitation values are "preceding hour sum". Wind is instantaneous.
- `past_hours` and `forecast_hours` use the current hour as reference. Up to 16 days of forecast.
- One request counts as 1 call unless it asks for more than 10 variables or more than 2 weeks of data per location.
- UNVERIFIED: whether each location in a multi-location request counts as its own call. Assume yes. Budget for it.
- UNVERIFIED: that `past_hours` and `forecast_hours` can be combined. Confirm in the spike.
- With `timezone=auto`, start-of-day boundaries become local per location. Use `timeformat=unixtime` and index by epoch to stay timezone-proof. Do not use `start_hour`/`end_hour` with `timezone=auto`.

**Routing candidates**
- OpenRouteService (public API): alternative routes are capped at 100 km route length. Unusable for alternatives on long truck routes. Do not use it for this.
- Mapbox Directions: `alternatives=true` returns up to two alternatives (so at most 3 routes). 100,000 free requests/month. A credit card on file is reportedly required.
- TomTom Routing: `maxAlternatives` and `travelMode=truck` supported. Free tier 2,500 requests/day, no credit card required. UNVERIFIED: the maximum alternatives value, truck parameters needed (e.g. commercial flag), and which response fields give per-segment travel time.
- HERE Routing v8: `alternatives` parameter and `transportMode=truck`. Generous free tier (about 250,000 transactions/month on the base plan). UNVERIFIED: sign-up requirements and whether alternatives count extra transactions.
- Whichever is chosen: free quotas are small. Cache routes and never call live APIs from tests.

**Geocoding**
- The public OSM Nominatim instance does not allow typeahead autocomplete. Do not use it for typing suggestions.
- Prefer the routing vendor's own geocoding/search endpoint (one key), with debounce and caching. Fallback: Photon.

**Map tiles:** OSM or CARTO raster tiles with attribution. Keep traffic low.

## 7. Environment variables

Never commit real values. Provide `.env.example` files.

Backend (`backend/.env`):
`DJANGO_SECRET_KEY`, `DJANGO_DEBUG`, `DJANGO_ALLOWED_HOSTS`, `CORS_ALLOWED_ORIGINS`, `ROUTING_PROVIDER` (tomtom or here), `TOMTOM_API_KEY`, `HERE_API_KEY`, `ROUTE_CACHE_TTL_SECONDS` (1800), `WEATHER_CACHE_TTL_SECONDS` (1800), `GEOCODE_CACHE_TTL_SECONDS` (86400), `HTTP_TIMEOUT_SECONDS` (8), `THROTTLE_ANALYZE` (e.g. 20/min), `LOG_LEVEL`.

Frontend (`frontend/.env`): `VITE_API_BASE_URL`.

## 8. Core flows (details in ARCHITECTURE.md)

- **Analyze:** validate -> origin timezone -> routes (cached) -> diversity filter -> timelines and checkpoints -> weather for unique cells (cached, batched, parallel) -> align to ETA -> classify -> summarize -> rank -> response.
- **Heatmap:** same input -> routes (from cache) -> corridor grid -> weather (shared cache) -> 49 hourly frames of levels -> response. The frontend loads it after analyze and the slider only swaps frames in memory.

## 9. Dependency register

Add a row for every dependency (CODING_RULES §9). Empty until P1.

| Package | Version | Side | Why | Added in |
|---|---|---|---|---|

## 10. Definition of done (every feature)

1. Matches the spec and the assumptions in §4.
2. Tests written and passing (unit for logic, integration for endpoints, component tests where listed).
3. Lint and format clean (ruff, ESLint, Prettier).
4. No business logic in UI. No duplicated logic.
5. Loading, empty and error states handled where the feature touches the UI.
6. FEATURE_LOG.md updated. PROJECT_CONTEXT.md and ARCHITECTURE.md updated if anything major changed.
7. Committed with a conventional message.

## 11. Time budget (16 h cap, 13.25 h planned, 2.75 h reserve)

| Phase | Scope | Hours |
|---|---|---|
| P0 | Provider spike, decisions | 0.75 |
| P1 | Scaffold, tooling | 0.5 |
| P2 | Domain core and tests | 2.25 |
| P3 | Providers, services, API | 2.5 |
| P4 | Frontend form, results, map | 2.5 |
| P5 | Heatmap backend and frontend | 1.75 |
| P6 | Polish, performance, responsive | 1.25 |
| P7 | Deploy, README, Loom, final QA | 1.75 |
| | Reserve | 2.75 |

Keep an honest time log in FEATURE_LOG.md. Stop at the cap, even if features remain.

## 12. Open items

See FEATURE_LOG.md "Open questions".
