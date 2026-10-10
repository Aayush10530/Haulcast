import { createTheme } from '@mui/material/styles';
import { colorTokens, shapeTokens, typographyTokens } from './tokens';

export const theme = createTheme({
  spacing: 8,
  shape: {
    borderRadius: shapeTokens.borderRadius,
  },
  palette: {
    mode: 'light',
    primary: {
      main: colorTokens.brand700,
      light: colorTokens.brand500,
      contrastText: '#FFFFFF',
    },
    secondary: {
      main: colorTokens.brand500,
      contrastText: '#FFFFFF',
    },
    background: {
      default: colorTokens.canvas,
      paper: colorTokens.surface,
    },
    text: {
      primary: colorTokens.ink,
      secondary: colorTokens.inkMuted,
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
          color: colorTokens.ink,
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
          backgroundColor: '#B5C2C7',
          borderRadius: '3px',
        },
        '::-webkit-scrollbar-track': {
          backgroundColor: 'transparent',
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
          '&:focus-visible': {
            outline: `2px solid ${colorTokens.brand500}`,
            outlineOffset: '2px',
          },
        },
        contained: {
          backgroundColor: colorTokens.brand700,
          '&:hover': {
            backgroundColor: colorTokens.brand500,
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
          borderColor: colorTokens.border,
          backgroundImage: 'none',
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
          borderColor: colorTokens.border,
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
          borderRadius: shapeTokens.borderRadius,
          '&:focus-visible': {
            outline: `2px solid ${colorTokens.brand500}`,
            outlineOffset: '2px',
          },
        },
      },
    },
  },
});
