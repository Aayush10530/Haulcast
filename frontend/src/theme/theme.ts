import { createTheme } from '@mui/material/styles';
import { componentOverrides } from './componentOverrides';
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
  components: componentOverrides,
});
