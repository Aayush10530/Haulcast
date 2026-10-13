import React from 'react';
import { Box, Typography } from '@mui/material';
import { colorTokens, typographyTokens } from '../../theme/tokens';

export const TripFormHeader: React.FC = () => {
  return (
    <Box sx={{ mb: 0.5 }}>
      <Typography
        variant="h1"
        sx={{
          fontFamily: typographyTokens.fontFamilyUi,
          fontSize: typographyTokens.panelTitle.fontSize,
          lineHeight: typographyTokens.panelTitle.lineHeight,
          fontWeight: typographyTokens.panelTitle.fontWeight,
          color: colorTokens.text,
        }}
      >
        Trip planning
      </Typography>
      <Typography
        sx={{
          fontFamily: typographyTokens.fontFamilyUi,
          fontSize: typographyTokens.caption.fontSize,
          lineHeight: typographyTokens.caption.lineHeight,
          color: colorTokens.textMuted,
          mt: 0.5,
        }}
      >
        Plan a safer route with the weather forecast
      </Typography>
    </Box>
  );
};
