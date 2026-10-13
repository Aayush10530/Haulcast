import type { Components, Theme } from '@mui/material/styles';
import { colorTokens, shapeTokens, typographyTokens } from './tokens';

export const inputOverrides: Components<Theme> = {
  MuiTextField: {
    defaultProps: {
      size: 'small',
      variant: 'outlined',
    },
  },
  MuiOutlinedInput: {
    styleOverrides: {
      root: {
        backgroundColor: colorTokens.surfaceRaised,
        borderRadius: shapeTokens.borderRadius,
        '& .MuiOutlinedInput-notchedOutline': {
          borderColor: colorTokens.border,
          borderWidth: '1px',
        },
        '&:hover .MuiOutlinedInput-notchedOutline': {
          borderColor: colorTokens.textMuted,
        },
        '&.Mui-focused .MuiOutlinedInput-notchedOutline': {
          borderColor: colorTokens.brand,
          borderWidth: '1px',
        },
        '&.Mui-focused': {
          outline: `2px solid ${colorTokens.brand}`,
          outlineOffset: '2px',
        },
      },
      input: {
        padding: '8px 12px',
        color: colorTokens.text,
        '&::placeholder': {
          color: colorTokens.textMuted,
          opacity: 1,
        },
      },
    },
  },
  MuiToggleButtonGroup: {
    defaultProps: {
      size: 'small',
    },
    styleOverrides: {
      root: {
        backgroundColor: colorTokens.surface,
        border: `1px solid ${colorTokens.border}`,
        borderRadius: shapeTokens.borderRadius,
      },
    },
  },
  MuiToggleButton: {
    styleOverrides: {
      root: {
        border: 'none',
        color: colorTokens.textMuted,
        textTransform: 'none',
        fontWeight: 500,
        padding: '4px 12px',
        '&.Mui-selected': {
          backgroundColor: colorTokens.surfaceRaised,
          color: colorTokens.brand,
          '&:hover': {
            backgroundColor: colorTokens.surfaceRaised,
          },
        },
        '&:hover': {
          backgroundColor: colorTokens.surfaceRaised,
        },
        '&.Mui-focusVisible, &:focus-visible': {
          outline: `2px solid ${colorTokens.brand}`,
          outlineOffset: '2px',
          zIndex: 1,
        },
      },
    },
  },
  MuiAlert: {
    defaultProps: {
      variant: 'outlined',
    },
    styleOverrides: {
      root: {
        borderRadius: shapeTokens.borderRadius,
        backgroundColor: colorTokens.surfaceRaised,
        borderWidth: '1px',
        borderStyle: 'solid',
        borderLeftWidth: '4px',
        borderColor: colorTokens.border,
        color: colorTokens.text,
        '&.MuiAlert-colorError': {
          borderLeftColor: '#E5484D',
        },
        '&.MuiAlert-colorWarning': {
          borderLeftColor: '#E8872B',
        },
        '&.MuiAlert-colorInfo': {
          borderLeftColor: colorTokens.brand,
        },
        '&.MuiAlert-colorSuccess': {
          borderLeftColor: '#3FA66B',
        },
      },
    },
  },
  MuiSlider: {
    styleOverrides: {
      root: {
        color: colorTokens.brand,
        height: 3,
        padding: '13px 0',
      },
      track: {
        height: 3,
        border: 'none',
        backgroundColor: colorTokens.brand,
      },
      rail: {
        height: 3,
        opacity: 1,
        backgroundColor: colorTokens.border,
      },
      thumb: {
        height: 14,
        width: 14,
        backgroundColor: colorTokens.brand,
        border: 'none',
        '&:focus, &:hover, &.Mui-active, &.Mui-focusVisible': {
          boxShadow: `0 0 0 6px rgba(45, 184, 197, 0.2)`,
        },
      },
    },
  },
  MuiTooltip: {
    styleOverrides: {
      tooltip: {
        backgroundColor: colorTokens.surfaceRaised,
        border: `1px solid ${colorTokens.border}`,
        color: colorTokens.text,
        fontSize: typographyTokens.caption.fontSize,
        borderRadius: shapeTokens.borderRadius,
        boxShadow: 'none',
        padding: '4px 8px',
      },
      arrow: {
        color: colorTokens.surfaceRaised,
      },
    },
  },
};
