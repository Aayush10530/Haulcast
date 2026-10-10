# DESIGN.md

Visual direction and UI rules. Read this before any frontend task. It sits alongside CODING_RULES.md §6. If this file and a habit conflict, this file wins.

Goal: a tool that looks like it was designed for dispatchers, not generated from a template. Distinct through a sharp MUI theme and three custom pieces (risk strip, route lines, heatmap controls), not through extra features. Performance is graded, so nothing here may cost map frame rate.

---

## 1. Direction

**Operations console.** Map-first, full-bleed. A docked control panel on the left (desktop) holds the form and results. No hero section, no centered marketing layout, no card grid.

Tone: precise, calm, slightly industrial. Information-dense but never cramped.

## 2. Tokens (put in `theme/tokens.ts`, consumed by `theme/theme.ts`)

**Typography** (self-hosted with `@fontsource` packages, latin subset, only the weights used; no external font requests)
- UI and headings: **Barlow** 400, 500, 600, 700.
- Numbers (miles, durations, ETAs, mph, in/hr, mile markers): **JetBrains Mono** 400, 500. Tabular figures so columns line up.
- Scale: panel title 22/28 600; section heading 16/24 600; body 14/20 400; caption 12/16 400; label 11/16 600 with 0.06em letter-spacing (labels only); mono 13/18.
- No uppercase buttons. Uppercase only for the 11px labels.

**Color**
| Token | Value | Use |
|---|---|---|
| ink | `#0F2A33` | text |
| ink-muted | `#52666E` | secondary text |
| brand-700 | `#0B4F5F` | header, primary buttons |
| brand-500 | `#0E7C86` | links, focus ring, recommended route |
| brand-50 | `#E8F3F5` | selected rows, tints |
| canvas | `#F3F5F4` | app background |
| surface | `#FFFFFF` | panels |
| border | `#D5DDDC` | 1px borders |

Brand teal is a nod to the assessment's header color, not a copy.

**Risk scale** (single source: `theme/riskColors.ts`, keyed by `low | moderate | high | severe | no_travel`)
| Level | Color | Notes |
|---|---|---|
| low | `#3FA66B` | |
| moderate | `#E2C044` | dark text on it |
| high | `#E8872B` | |
| severe | `#D1342F` | |
| no_travel | `#4B1D6B` | deep purple, near black on the map |

- Brand teal never appears inside the risk scale and the risk scale never appears as brand decoration.
- Risk is always text plus color. Chips show a colored dot and the label. Check the scale with a color-blindness simulator and fix by adjusting lightness, not by dropping the text.
- Route lines use non-risk colors: recommended = brand-500 solid; other routes = `#24425A` and `#7A8B93` with different dash patterns. Route letters (A/B/C) are always shown.

**Shape and depth**
- Radius 4 px (panels 6 px). 1 px borders instead of shadows. Shadow only on floating map controls (one level).
- Spacing base 8 px. Panel padding 16. Compact density: `size="small"` everywhere.

## 3. MUI theme overrides (`theme/theme.ts`)

- `shape.borderRadius: 4`; typography families and scale above.
- `Button`: `textTransform: 'none'`, weight 600, `disableElevation`. Primary = brand-700, hover brand-500.
- `Paper`/`Card`: default `variant="outlined"`, no elevation.
- `TextField`, `Select`, `Autocomplete`: outlined, small, labels above or floating consistently (pick one, keep it).
- `Chip`: square-ish (radius 4), dot + label for risk chips.
- `Alert`: outlined variant, 4 px left border in the severity color.
- `Slider`: thin track, 14 px thumb, ticks every 6 h on the heatmap slider.
- Focus ring: 2 px brand-500 with 2 px offset on every interactive element.
- `CssBaseline`: font smoothing, thin neutral scrollbars.
- Do not use MUI default blue, default Roboto, or default shadows anywhere.

## 4. Signature pieces

**RiskStrip** (`components/RiskStrip.tsx`)
A horizontal bar, 8 px high, split into segments with widths proportional to miles at each risk level, in risk colors. Under it, mono text: `Severe 34 mi · High 12 mi`. `role="img"` with an `aria-label` that spells out all levels. Used on every route card and in the recommendation comparison.

**Route lines**
Each route is drawn twice: a white casing (8 px) under the colored line (5 px). Selected route 7 px, others 4 px at 80% opacity. Route letter badge at the midpoint (small square, mono letter).

**Checkpoints**
Canvas `CircleMarker`: radius 5 on the selected route, 3 on others, fill = risk color, 1.5 px white stroke. Popup content in mono: mile, local ETA, wind, rain, snow, level chip, driver and reason.

**Heatmap controls**
A floating panel bottom-center on desktop, docked to the bottom of the map on mobile. Contains: play/pause, slider with 6 h ticks, label like `Mon 14:00 CDT (+6 h)`, layer toggle (Overall, Wind, Rain, Snow), legend. Slider updates must not re-render React components outside this panel.

## 5. Layout

- **Desktop (md and up):** header 56 px (wordmark left, small API status dot right). Below: panel 420 px fixed on the left, map fills the rest. Panel scrolls internally; the page never scrolls.
- **Mobile:** map on top at about 45% of the viewport height; panel scrolls below; heatmap controls docked at the map's bottom edge. Touch targets at least 40 px. No horizontal page scroll.
- **Wordmark:** text "Weather-Aware Truck Router" in Barlow 600 with a small inline SVG glyph of three diverging lines. No logo generator art, no emoji.
- **Map tiles:** one muted light basemap (CARTO light or OSM, with attribution; check usage terms) so risk colors and the heatmap are the loudest thing on screen.

## 6. Component rules

- Route card: letter badge (28 px square, mono), tag chip "Recommended" (filled brand-500) or "Fastest", then a 3-column mono grid (distance, drive time, arrival local), then the delta vs fastest, then the RiskStrip, then a collapsed "Checkpoints" table.
- Recommendation banner: 4 px brand-500 left border, one sentence headline, small caption "Decided by: Severe miles". No icon-in-a-circle.
- Form: grouped as Route (origin, destination), Departure (local time at origin), Load (lb with helper text), Checkpoint interval. One primary button.
- Empty state: short text and a clearly labeled "Try an example trip" button. No stock illustrations.
- Warnings and errors: outlined Alert with a plain sentence saying what happened and what to do.
- Microcopy is direct and human: "Leave 08:00 CDT · 842 mi", "No safe route at this time. Try a later departure." Never "Unlock insights", "Supercharge", "Seamless".
- Motion: 150 ms ease-out on panel and card state changes. Nothing animates on the map except the heatmap play. Respect `prefers-reduced-motion`.

## 7. Banned

Purple or blue gradients, glassmorphism and blur panels, emoji as icons, identical rounded card grids, heavy drop shadows, gradient buttons, centered hero layouts, default MUI blue and Roboto, decorative animation, skeleton loaders that do not match the final layout, any color for risk outside `riskColors.ts`.

## 8. Self-check before finishing any UI task

1. Cover the wordmark. Could this be any MUI template? If yes, find what is still default (font, blue, radius, shadows) and fix it.
2. Is every risk shown with text as well as color?
3. Do all numbers use the mono face and line up?
4. Does the slider stay smooth while scrubbing (browser performance panel)?
5. Does it work at 360, 768 and 1280 px widths?
6. Loading, empty and error states present?

## 9. Minor visual enhancements
(1) risk chips get a driver icon (@mui/icons-material: Air, WaterDrop, AcUnit, Scale for load rule) next to the dot and label; (2) a swap-origin-and-destination icon button between the two place fields; (3) heatmap layer toggle is a compact icon toolbar at the map's bottom-left, with tooltips; (4) checkpoint table has a "Sort: Mile / Risk" toggle; (5) route card header shows departure and arrival as a two-dot vertical timeline with local times. Add the icons package to the dependency register when P1 installs it.
