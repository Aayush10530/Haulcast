import type { Components, Theme } from '@mui/material/styles';
import { inputOverrides } from './inputOverrides';
import { colorTokens, shapeTokens } from './tokens';

export const componentOverrides: Components<Theme> = {
  MuiCssBaseline: {
    styleOverrides: {
      body: {
        backgroundColor: colorTokens.canvas,
        color: colorTokens.text,
        WebkitFontSmoothing: 'antialiased',
        MozOsxFontSmoothing: 'grayscale',
        margin: 0,
        padding: 0,
      },
      '::-webkit-scrollbar': {
        width: '6px',
        height: '6px',
      },
      '::-webkit-scrollbar-thumb': {
        backgroundColor: colorTokens.border,
        borderRadius: '3px',
      },
      '::-webkit-scrollbar-thumb:hover': {
        backgroundColor: colorTokens.textMuted,
      },
      '::-webkit-scrollbar-track': {
        backgroundColor: 'transparent',
      },
      '.leaflet-popup-content-wrapper': {
        backgroundColor: colorTokens.surfaceRaised,
        color: colorTokens.text,
        border: `1px solid ${colorTokens.border}`,
        borderRadius: `${shapeTokens.borderRadius}px`,
        boxShadow: 'none',
      },
      '.leaflet-popup-tip': {
        backgroundColor: colorTokens.surfaceRaised,
      },
      '.leaflet-control-zoom a': {
        backgroundColor: `${colorTokens.surfaceRaised} !important`,
        color: `${colorTokens.text} !important`,
        border: `1px solid ${colorTokens.border} !important`,
      },
      '.leaflet-control-attribution': {
        backgroundColor: `rgba(17, 30, 36, 0.8) !important`,
        color: `${colorTokens.textMuted} !important`,
        fontSize: '11px !important',
      },
    },
  },
  MuiButton: {
    defaultProps: {
      disableElevation: true,
      size: 'small',
    },
    styleOverrides: {
      root: {
        textTransform: 'none',
        fontWeight: 600,
        borderRadius: shapeTokens.borderRadius,
        transition:
          'transform 180ms cubic-bezier(0.16, 1, 0.3, 1), box-shadow 180ms cubic-bezier(0.16, 1, 0.3, 1), background-color 180ms ease, border-color 180ms ease',
        '&.Mui-focusVisible, &:focus-visible': {
          outline: `2px solid ${colorTokens.brand}`,
          outlineOffset: '2px',
        },
      },
      contained: {
        backgroundColor: colorTokens.brand,
        color: colorTokens.onBrand,
        backgroundImage: 'none',
        boxShadow: 'none',
        '&:hover': {
          backgroundColor: colorTokens.brandStrong,
          transform: 'translateY(-1.5px)',
          boxShadow: '0 6px 20px rgba(0, 229, 255, 0.35)',
        },
        '&:active': {
          transform: 'translateY(0) scale(0.98)',
        },
      },
      text: {
        color: colorTokens.brand,
        '&:hover': {
          backgroundColor: 'rgba(0, 229, 255, 0.08)',
          color: colorTokens.brandStrong,
        },
      },
      outlined: {
        borderColor: colorTokens.border,
        color: colorTokens.text,
        '&:hover': {
          borderColor: colorTokens.brand,
          backgroundColor: 'rgba(0, 229, 255, 0.08)',
          transform: 'translateY(-1px)',
        },
        '&:active': {
          transform: 'translateY(0) scale(0.98)',
        },
      },
    },
  },
  MuiPaper: {
    defaultProps: {
      variant: 'outlined',
      elevation: 0,
    },
    styleOverrides: {
      root: {
        backgroundColor: colorTokens.surface,
        borderColor: colorTokens.border,
        borderRadius: shapeTokens.panelBorderRadius,
        backgroundImage: 'none',
        boxShadow: 'none',
      },
    },
  },
  MuiCard: {
    defaultProps: {
      variant: 'outlined',
      elevation: 0,
    },
    styleOverrides: {
      root: {
        backgroundColor: colorTokens.surface,
        borderColor: colorTokens.border,
        borderRadius: shapeTokens.panelBorderRadius,
        backgroundImage: 'none',
        boxShadow: 'none',
      },
    },
  },
  MuiChip: {
    defaultProps: {
      size: 'small',
    },
    styleOverrides: {
      root: {
        borderRadius: shapeTokens.borderRadius,
        fontWeight: 500,
      },
    },
  },
  ...inputOverrides,
};
