import React from 'react';
import { Box, Typography } from '@mui/material';
import { RecommendationDTO } from '../../api/types';
import { colorTokens, shapeTokens, typographyTokens } from '../../theme/tokens';

export interface RecommendationBannerProps {
  recommendation: RecommendationDTO;
}

const FACTOR_LABELS: Record<string, string> = {
  incomplete_data: 'weather data was incomplete',
  severe_miles: 'fewer Severe miles',
  high_miles: 'fewer High risk miles',
  avg_risk: 'lower average risk score',
  travel_time: 'fastest travel time with equal risk',
  user_preference: 'user preference',
};

export const RecommendationBanner: React.FC<RecommendationBannerProps> = ({
  recommendation,
}) => {
  if (!recommendation) return null;

  const factorInWords =
    FACTOR_LABELS[recommendation.decided_by] ||
    recommendation.decided_by.replace(/_/g, ' ');

  return (
    <Box
      data-testid="recommendation-banner"
      sx={{
        borderLeft: `4px solid ${colorTokens.brand}`,
        backgroundColor: colorTokens.surfaceRaised,
        borderRadius: `0 ${shapeTokens.panelBorderRadius}px ${shapeTokens.panelBorderRadius}px 0`,
        p: 2,
        mb: 2,
      }}
    >
      <Typography
        variant="subtitle1"
        sx={{
          fontFamily: typographyTokens.fontFamilyUi,
          fontWeight: 700,
          color: colorTokens.text,
          lineHeight: 1.3,
        }}
      >
        {recommendation.headline}
      </Typography>
      <Typography
        variant="caption"
        sx={{
          fontFamily: typographyTokens.fontFamilyUi,
          color: colorTokens.textMuted,
          display: 'block',
          mt: 0.5,
        }}
      >
        Decided by: {factorInWords}
      </Typography>
    </Box>
  );
};
