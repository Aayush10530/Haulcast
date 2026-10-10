/**
 * Single source of truth for risk scale colors per DESIGN.md §2.
 * Keyed strictly by low | moderate | high | severe | no_travel.
 * Brand teal NEVER appears inside the risk scale, and risk colors
 * NEVER appear as brand decoration.
 *
 * All text pairings meet WCAG AA (contrast ratio >= 4.5:1):
 * - ink (#0F2A33) on low (#3FA66B), moderate (#E2C044), high (#E8872B)
 * - white (#FFFFFF) on severe (#D1342F), no_travel (#4B1D6B)
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
    contrastText: '#0F2A33',
    label: 'Low',
  },
  moderate: {
    background: '#E2C044',
    contrastText: '#0F2A33',
    label: 'Moderate',
  },
  high: {
    background: '#E8872B',
    contrastText: '#0F2A33',
    label: 'High',
  },
  severe: {
    background: '#D1342F',
    contrastText: '#FFFFFF',
    label: 'Severe',
  },
  no_travel: {
    background: '#4B1D6B',
    contrastText: '#FFFFFF',
    label: 'No Travel',
  },
} as const;
