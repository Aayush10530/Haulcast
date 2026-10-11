import { createTheme } from '@mui/material/styles';
import { colorTokens, shapeTokens, typographyTokens } from './tokens';

export const theme = createTheme({
  spacing: 8,
  breakpoints: {
    values: {
      xs: 0,
      sm: 600,
      md: 900,
      lg: 1200,
      xl: 1440,
    },
  },
  shape: {
    borderRadius: shapeTokens.borderRadius,
  },
  palette: {
    mode: 'dark',
    primary: {
      main: colorTokens.brand,
      light: colorTokens.brandStrong,
      contrastText: colorTokens.onBrand,
    },
    secondary: {
      main: colorTokens.brandStrong,
      contrastText: colorTokens.onBrand,
    },
    background: {
      default: colorTokens.canvas,
      paper: colorTokens.surface,
    },
    text: {
      primary: colorTokens.text,
      secondary: colorTokens.textMuted,
    },
    divider: colorTokens.border,
  },
  typography: {
    fontFamily: typographyTokens.fontFamilyUi,
    h1: {
      fontFamily: typographyTokens.fontFamilyUi,
      fontSize: typographyTokens.panelTitle.fontSize,
      lineHeight: typographyTokens.panelTitle.lineHeight,
      fontWeight: typographyTokens.panelTitle.fontWeight,
    },
    h2: {
      fontFamily: typographyTokens.fontFamilyUi,
      fontSize: typographyTokens.sectionHeading.fontSize,
      lineHeight: typographyTokens.sectionHeading.lineHeight,
      fontWeight: typographyTokens.sectionHeading.fontWeight,
    },
    body1: {
      fontFamily: typographyTokens.fontFamilyUi,
      fontSize: typographyTokens.body.fontSize,
      lineHeight: typographyTokens.body.lineHeight,
      fontWeight: typographyTokens.body.fontWeight,
    },
    body2: {
      fontFamily: typographyTokens.fontFamilyUi,
      fontSize: typographyTokens.caption.fontSize,
      lineHeight: typographyTokens.caption.lineHeight,
      fontWeight: typographyTokens.caption.fontWeight,
    },
    caption: {
      fontFamily: typographyTokens.fontFamilyUi,
      fontSize: typographyTokens.caption.fontSize,
      lineHeight: typographyTokens.caption.lineHeight,
      fontWeight: typographyTokens.caption.fontWeight,
    },
    button: {
      fontFamily: typographyTokens.fontFamilyUi,
      textTransform: 'none',
      fontWeight: 600,
    },
  },
  components: {
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
            boxShadow: 'none',
          },
        },
        text: {
          color: colorTokens.brand,
          '&:hover': {
            backgroundColor: 'rgba(45, 184, 197, 0.08)',
            color: colorTokens.brandStrong,
          },
        },
        outlined: {
          borderColor: colorTokens.border,
          color: colorTokens.text,
          '&:hover': {
            borderColor: colorTokens.brand,
            backgroundColor: 'rgba(45, 184, 197, 0.08)',
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
          borderRadius: shapeTokens.borderRadius,
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
  },
});
