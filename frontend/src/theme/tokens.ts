/**
 * Design tokens per DESIGN.md §3.
 * Strictly defines typography, color tokens, route line styles, and spatial constants.
 */

export const typographyTokens = {
  fontFamilyUi:
    "'Barlow', -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, sans-serif",
  fontFamilyMono:
    "'JetBrains Mono', SFMono-Regular, Menlo, Monaco, Consolas, monospace",
  panelTitle: {
    fontSize: '20px',
    lineHeight: '28px',
    fontWeight: 600,
  },
  sectionHeading: {
    fontSize: '15px',
    lineHeight: '22px',
    fontWeight: 600,
  },
  body: {
    fontSize: '14px',
    lineHeight: '20px',
    fontWeight: 400,
  },
  caption: {
    fontSize: '12px',
    lineHeight: '16px',
    fontWeight: 400,
  },
  label: {
    fontSize: '11px',
    lineHeight: '16px',
    fontWeight: 600,
    letterSpacing: '0.06em',
    textTransform: 'uppercase' as const,
  },
  mono: {
    fontSize: '13px',
    lineHeight: '18px',
  },
} as const;

export const colorTokens = {
  canvas: '#0B1418',
  surface: '#111E24',
  surfaceRaised: '#16262E',
  border: '#25383F',
  text: '#E6EEF0',
  textMuted: '#8FA4AB',
  brand: '#2DB8C5',
  brandStrong: '#5CCBD5',
  onBrand: '#07171C',
} as const;

export const routeLineColors = {
  recommended: '#2DB8C5',
  second: '#7C9BFF',
  third: '#C9D4D8',
  casing: '#0B1418',
} as const;

export const routeDashArrays = {
  recommended: '',
  second: '10 6',
  third: '2 6',
} as const;

export const shapeTokens = {
  borderRadius: 8,
  panelBorderRadius: 10,
  gap: 12,
  borderWidth: 1,
  headerHeight: 56,
  headerHeightMobile: 48,
  threeColumnLeftWidth: 340,
  threeColumnRightWidth: 380,
  twoColumnLeftWidth: 400,
} as const;
