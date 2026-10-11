# DESIGN.md

Visual direction and UI rules (version 2, dark). Read before any frontend task. It supersedes the first light version. Where this file and the mockup (`docs/design/mockup.png`) differ, this file wins.

Goal: a dispatcher's console that looks designed, not generated. Dark, flat, dense, map-first. Performance is graded, so nothing here may cost map frame rate.

---

## 1. Direction

**Single-page dashboard. No routing library, no extra pages.** One screen: form, map, results. Selecting a route expands detail in place.

- Product name in the header: **StormRoute**, subtitle "Weather-Aware Truck Router" (from the mockup; changing it later is a one-line edit).
- Tone: precise, calm, industrial. Information-dense but never cramped.
- **Flat.** Solid colors, 1 px borders. No gradients, no glow, no glass/blur, no drop shadows (only the floating map controls get one subtle shadow).

## 2. What we take from the mockup, and what we do not

Take: three-column desktop layout, swap button, 10/25/50 interval buttons, forecast slider across the top of the map, risk legend on the map, route cards with miles by risk, checkpoint timeline with expandable weather detail, bottom tab bar on mobile (Plan | Map | Routes).

Do not build (no spec requirement, no data behind it, or fake): sidebar navigation (History, Saved, Alerts, Settings), search bar, notification bell, profile menu, "Drive Safer" hero card, elevation profile, route detail page with tabs, Radar/Satellite/Terrain switch, comparison bar chart, place names for checkpoints, 0-100 risk score.

Change: the route "score" ring shows our real average risk on the 0-4 scale (neutral ring fill, number in the middle, label "Avg risk"). Route lines never use risk colors (see §3). "Recommended" uses brand teal, not green. Copy is plain (see §6). The heatmap is our corridor risk heatmap, not weather radar imagery.

## 3. Tokens (`theme/tokens.ts`)

**Typography** (self-hosted `@fontsource`, latin subset, only used weights)
- UI and headings: **Barlow** 400, 500, 600, 700. Numbers (miles, durations, ETAs, mph, in/hr): **JetBrains Mono** 400, 500.
- Scale: panel title 20/28 600; section heading 15/22 600; body 14/20; caption 12/16; label 11/16 600 with 0.06em tracking (labels only may be uppercase); mono 13/18.
- Buttons: no uppercase.

**Color**
| Token | Value | Use |
|---|---|---|
| canvas | `#0B1418` | app background, map surround |
| surface | `#111E24` | panels, header |
| surface-raised | `#16262E` | inputs, cards on a panel, popups |
| border | `#25383F` | 1 px borders |
| text | `#E6EEF0` | primary text |
| text-muted | `#8FA4AB` | secondary text |
| brand | `#2DB8C5` | primary buttons, links, focus ring, recommended route |
| brand-strong | `#5CCBD5` | hover |
| on-brand | `#07171C` | text on brand fills |

**Risk scale** (`theme/riskColors.ts`; keys `low | moderate | high | severe | no_travel`)
| Level | Fill | Text on fill |
|---|---|---|
| low | `#3FA66B` | `#07171C` |
| moderate | `#E2C044` | `#07171C` |
| high | `#E8872B` | `#07171C` |
| severe | `#E5484D` | `#07171C` |
| no_travel | `#A78BFA` | `#07171C` |

- All five text-on-fill pairs must pass WCAG AA (4.5:1). Keep the contrast unit test and add pairs for `text`/`text-muted` on `surface`, `brand` on `surface`, and `on-brand` on `brand`.
- Risk is always text plus color plus a driver icon. Chips: colored fill with label; never color alone.
- Brand teal and the risk scale never overlap. Risk colors are never used for decoration.

**Route line colors** (never risk colors): recommended = `#2DB8C5` solid; second = `#7C9BFF` dashed (10 6); third = `#C9D4D8` dotted (2 6). Each line has a `#0B1418` casing 2 px wider. Route letters A/B/C are always shown.

**Shape and depth (D-025):** floating cards on canvas with 12 px gap. Radii: 8 px inputs, buttons, and chips; 10 px panels, header, and map card. Borders 1 px `border`. Surface fill (`#111E24`). Map card clips its content (`overflow: hidden`). Spacing base 8 px. Compact density.

## 4. MUI theme (`theme/theme.ts`)

- `palette.mode: 'dark'`; primary = brand with `on-brand` contrast text; background default = canvas, paper = surface; text and divider from tokens.
- `Button` contained: flat brand fill, `on-brand` text, hover brand-strong, no elevation, no gradient, weight 600, radius 8 px. `Button` text variant for secondary actions. Primary action button 44 px high.
- `Paper`/`Card`: outlined, no elevation, `surface` background, radius 10 px. Selected route card: 1.5 px brand border and a faint brand tint, flat, no glow.
- `TextField`/`Select`/`Autocomplete`: outlined, small, `surface-raised` fill, `border` outline, brand outline on focus, radius 8 px. Start icons: Place for origin, Flag for destination, CalendarToday for departure, Scale for load weight.
- `ToggleButtonGroup` (interval selector): small, radius 8 px, selected = brand text and brand border on `surface-raised`.
- `Chip`: radius 8 px, used for risk (fill from risk scale) and tags.
- `Alert`: outlined with 4 px left border in the severity color, radius 8 px.
- `Slider`: thin 3 px track, 14 px thumb in brand.
- `Tooltip` and Leaflet popups: `surface-raised` background, `border`, text color (global CSS overrides for `.leaflet-popup-content-wrapper`, `.leaflet-control`).
- Focus ring: 2 px brand, 2 px offset, on every interactive element (applied to the correct element for each input, tested by keyboard).
- `CssBaseline`: dark scrollbars (thin, `border` thumb), font smoothing. No `fontFeatureSettings`.

## 5. Layout (D-025)

- **Floating cards on canvas:** panels, header, and map become floating cards on the canvas: 12 px gap, 10 px radius, 1 px border, surface fill (`#111E24`). The map card clips its content (`overflow: hidden`).
- **>= 1440 px (three columns):** floating header 56 px. 12 px gap. Left column 340 px (form). Center: map card fills the rest. Right column 380 px (results). 12 px gap between columns. Columns scroll internally; the page does not scroll.
- **900-1439 px (two columns):** floating header. 12 px gap. Left panel 400 px holds the form on top and results below with 12 px gap, scrolling internally. Map card fills the rest.
- **< 900 px (mobile):** floating header 48 px. 12 px gap. Active tab region rendered as a floating card. Fixed bottom tab bar with three tabs: Plan (form), Map (map plus heatmap bar), Routes (results). The map tab keeps the heatmap controls docked at its top. Touch targets at least 40 px. No horizontal scroll.
- **Header:** floating card with wordmark and subtitle on the left; on the right a small status dot with "API online" / "API offline" driven by `GET /api/health/` (real, polled on load and every 60 s). Nothing else.

## 6. Components

**Trip form (left column):** title "Trip planning" (20/28), subtitle "Plan a safer route with the weather forecast". Origin and destination place fields with start icons (Place, Flag) and a swap icon button between them. Departure date and time with CalendarToday start icon (native `datetime-local` input styled by the theme; helper "Local time at origin"). Load weight in lb with Scale start icon (helper "Wind rules apply above 30,000 and 40,000 lb"). Checkpoint interval toggle: Auto, 10 mi, 25 mi, 50 mi (default Auto). Primary button "Generate routes" (44 px high, flat brand fill). Text button "Try an example trip" (fills the form, no fake results).

**Results (right column):** header "Route options (3)". Recommendation banner: 4 px brand left border, headline from the API, caption "Decided by: <factor>". Three route cards:
- Letter badge A/B/C (28 px square, mono), tag chips ("Recommended" in brand, "Fastest" outlined), avg-risk ring (neutral fill, number inside, label "Avg risk").
- Mono line: `12h 56m · 799 mi`. Two-dot vertical timeline: departure and arrival with local times.
- **RiskStrip** (`components/RiskStrip.tsx`): 8 px bar split by miles per level in risk colors, plus `Severe 34 mi · High 12 mi` in mono. `role="img"` with a full `aria-label`.
- Delta line: "+47 min vs fastest" when applicable.
- Selecting a card selects the route on the map and expands its **checkpoint list**.

**Checkpoint list:** vertical timeline (dot colored by level, mile, local ETA, risk chip with driver icon: Air, WaterDrop, AcUnit, Scale for load rule). Sort toggle "Mile / Risk". Row click pans the map to the checkpoint and opens its popup; expanded row shows wind, rain, snow (mono), and the API `reason` text. Unavailable weather is shown as "Forecast unavailable" in muted text.

**Map (center):** dark basemap (one muted dark tile layer, with attribution; check usage terms). `preferCanvas`. Three routes with casing and the line styles above, selected route thicker. A small label pill at each route's midpoint (`A · 12h 56m`, click selects). Checkpoint circle markers: radius 5 on the selected route, 3 on others, fill = risk fill, 1.5 px `canvas` stroke. Popups: mile, local ETA, wind/rain/snow, level chip, driver, reason. Risk legend at bottom-left. Zoom controls at the right.

**Heatmap bar (top of the map, floating):** play/pause, slider 0-48 h with 6 h ticks, label like `Mon 14:00 CDT (+6 h)`, layer toggle (Overall, Wind, Rain, Snow) as a compact icon toolbar with tooltips. Updating the slider must not re-render React components outside this bar.

**Empty and loading states:** idle: the map shows the contiguous US and the results column shows a short text and the example button. Loading: skeletons that match the final card layout; heatmap bar disabled with a spinner until frames arrive. Errors: outlined Alert with a plain sentence and a retry button.

**Copy:** direct and human. "Leave 08:00 CDT · 799 mi". "No safe route right now. Try a later departure." Never "real-time" (we use the forecast at your ETA), never "unlock", "supercharge", "seamless", "Drive Safer, Plan Smarter".

**Motion:** 150 ms ease-out for panel and card changes. Nothing animates on the map except the heatmap play. Respect `prefers-reduced-motion`.

## 7. Banned

Gradients (including on buttons), glows, glassmorphism and blur panels, radar or satellite imagery, emoji as icons, identical card grids without hierarchy, heavy shadows, centered hero layouts, default MUI blue and Roboto, decorative animation, placeholder buttons, any color for risk outside `riskColors.ts`, risk colors on route lines.

## 8. Self-check before finishing any UI task

1. Cover the wordmark. Could this be any MUI dark template? If yes, find what is still default and fix it.
2. Is every risk shown with text and an icon as well as color?
3. Do all numbers use the mono face and line up?
4. Does the slider stay smooth while scrubbing (browser performance panel)?
5. Does it work at 360, 768, 1280 and 1920 px?
6. Loading, empty and error states present? Keyboard focus visible everywhere?
