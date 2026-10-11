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
  canvas: '#06121E',
  surface: '#0B1B2B',
  surfaceRaised: '#102436',
  border: '#16324A',
  text: '#FFFFFF',
  textMuted: '#7E9BA6',
  brand: '#00E5FF',
  brandStrong: '#33EBFF',
  onBrand: '#07171C',
} as const;

export const routeLineColors = {
  recommended: '#00D2FF',
  second: '#FF8C42',
  third: '#00E676',
  casing: '#06121E',
} as const;

export const routeDashArrays = {
  recommended: '',
  second: '',
  third: '',
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
