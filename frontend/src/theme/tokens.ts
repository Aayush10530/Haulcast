/**
 * Design tokens per DESIGN.md §2.
 * Strictly defines fonts, color tokens, and spatial constants.
 */

export const typographyTokens = {
  fontFamilyUi:
    "'Barlow', -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, sans-serif",
  fontFamilyMono:
    "'JetBrains Mono', SFMono-Regular, Menlo, Monaco, Consolas, monospace",
  panelTitle: {
    fontSize: '22px',
    lineHeight: '28px',
    fontWeight: 600,
  },
  sectionHeading: {
    fontSize: '16px',
    lineHeight: '24px',
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
  ink: '#0F2A33',
  inkMuted: '#52666E',
  brand700: '#0B4F5F',
  brand500: '#0E7C86',
  brand50: '#E8F3F5',
  canvas: '#F3F5F4',
  surface: '#FFFFFF',
  border: '#D5DDDC',
} as const;

export const shapeTokens = {
  borderRadius: 4,
  panelBorderRadius: 6,
  controlPanelWidth: 420,
  headerHeight: 56,
} as const;
