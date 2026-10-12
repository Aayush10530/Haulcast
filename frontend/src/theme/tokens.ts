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
  canvas: '#0A0A0A',
  surface: '#121212',
  surfaceRaised: '#1A1A1A',
  border: '#262626',
  text: '#FFFFFF',
  textMuted: '#9E9E9E',
  brand: '#00E5FF',
  brandStrong: '#33EBFF',
  onBrand: '#07171C',
} as const;

export const routeLineColors = {
  recommended: '#00D2FF',
  second: '#FF8C42',
  third: '#00E676',
  casing: '#0A0A0A',
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

export const glassTokens = {
  surface: 'rgba(18, 18, 18, 0.75)',
  surfaceGradient:
    'linear-gradient(135deg, rgba(28, 28, 28, 0.72) 0%, rgba(14, 14, 14, 0.82) 100%)',
  surfaceRaised: 'rgba(28, 28, 28, 0.65)',
  surfaceHighlight: 'rgba(255, 255, 255, 0.06)',
  border: 'rgba(255, 255, 255, 0.12)',
  borderSubtle: 'rgba(255, 255, 255, 0.06)',
  borderGloss: 'rgba(255, 255, 255, 0.20)',
  blur: 'blur(20px) saturate(150%)',
  webkitBlur: 'blur(20px) saturate(150%)',
  shadow:
    '0 10px 36px 0 rgba(0, 0, 0, 0.65), inset 0 1px 1px 0 rgba(255, 255, 255, 0.12), inset 0 -1px 1px 0 rgba(0, 0, 0, 0.5)',
  shadowElevated:
    '0 14px 44px 0 rgba(0, 0, 0, 0.8), inset 0 1px 1.5px 0 rgba(255, 255, 255, 0.18), inset 0 -1px 1px 0 rgba(0, 0, 0, 0.6)',
} as const;

export const glassPanelSx = {
  backgroundColor: glassTokens.surface,
  backgroundImage: glassTokens.surfaceGradient,
  backdropFilter: glassTokens.blur,
  WebkitBackdropFilter: glassTokens.webkitBlur,
  border: `1px solid ${glassTokens.border}`,
  borderRadius: `${shapeTokens.panelBorderRadius}px`,
  boxShadow: glassTokens.shadow,
  transition:
    'transform 220ms cubic-bezier(0.16, 1, 0.3, 1), box-shadow 220ms cubic-bezier(0.16, 1, 0.3, 1), border-color 220ms ease',
  '&:hover': {
    borderColor: 'rgba(255, 255, 255, 0.18)',
    boxShadow: glassTokens.shadowElevated,
  },
} as const;
