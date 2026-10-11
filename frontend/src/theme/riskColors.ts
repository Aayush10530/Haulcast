/**
 * Single source of truth for risk scale colors per DESIGN.md §3.
 * Keyed strictly by low | moderate | high | severe | no_travel.
 * Brand teal NEVER appears inside the risk scale, and risk colors
 * NEVER appear as brand decoration.
 *
 * All text pairings meet WCAG AA (contrast ratio >= 4.5:1):
 * - #07171C on all risk fills:
 *   low (#3FA66B), moderate (#E2C044), high (#E8872B),
 *   severe (#E5484D), no_travel (#A78BFA)
 */

export type RiskLevelKey = 'low' | 'moderate' | 'high' | 'severe' | 'no_travel';

export interface RiskColorSpec {
  background: string;
  contrastText: string;
  label: string;
}

export const riskColors: Record<RiskLevelKey, RiskColorSpec> = {
  low: {
    background: '#3FA66B',
    contrastText: '#07171C',
    label: 'Low',
  },
  moderate: {
    background: '#E2C044',
    contrastText: '#07171C',
    label: 'Moderate',
  },
  high: {
    background: '#E8872B',
    contrastText: '#07171C',
    label: 'High',
  },
  severe: {
    background: '#E5484D',
    contrastText: '#07171C',
    label: 'Severe',
  },
  no_travel: {
    background: '#A78BFA',
    contrastText: '#07171C',
    label: 'No Travel',
  },
} as const;
