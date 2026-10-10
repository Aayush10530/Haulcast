/**
 * Single source of truth for risk scale colors per DESIGN.md §2.
 * Keyed strictly by low | moderate | high | severe | no_travel.
 * Brand teal NEVER appears inside the risk scale, and risk colors
 * NEVER appear as brand decoration.
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
    contrastText: '#FFFFFF',
    label: 'Low',
  },
  moderate: {
    background: '#E2C044',
    contrastText: '#0F2A33', // Dark text per DESIGN.md table note
    label: 'Moderate',
  },
  high: {
    background: '#E8872B',
    contrastText: '#FFFFFF',
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
