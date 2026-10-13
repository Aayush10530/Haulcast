import React from 'react';
import { Box, Chip } from '@mui/material';
import { colorTokens, typographyTokens } from '../../theme/tokens';

export interface RouteCardTagsProps {
  isDataAvailable: boolean;
  unavailableMiles: number;
  hasRecommendedTag: boolean;
  hasFastestTag: boolean;
}

export const RouteCardTags: React.FC<RouteCardTagsProps> = ({
  isDataAvailable,
  unavailableMiles,
  hasRecommendedTag,
  hasFastestTag,
}) => {
  return (
    <Box sx={{ display: 'flex', alignItems: 'center', gap: 1 }}>
      {!isDataAvailable ? (
        <Chip
          size="small"
          label="Weather Unavailable"
          data-testid="tag-unavailable"
          sx={{
            height: 20,
            borderRadius: '10px',
            backgroundColor: 'rgba(255, 75, 75, 0.15)',
            color: '#FF6B6B',
            border: '1px solid rgba(255, 75, 75, 0.3)',
            fontFamily: typographyTokens.fontFamilyUi,
            fontWeight: 600,
            fontSize: '0.65rem',
            px: 0.5,
          }}
        />
      ) : unavailableMiles > 0 ? (
        <Chip
          size="small"
          label={`${unavailableMiles} mi unmonitored`}
          sx={{
            height: 20,
            borderRadius: '10px',
            backgroundColor: 'rgba(255, 255, 255, 0.08)',
            color: colorTokens.textMuted,
            fontFamily: typographyTokens.fontFamilyUi,
            fontWeight: 600,
            fontSize: '0.65rem',
            px: 0.5,
          }}
        />
      ) : null}

      {hasRecommendedTag && (
        <Chip
          size="small"
          label="Recommended"
          data-testid="tag-recommended"
          sx={{
            height: 20,
            borderRadius: '10px',
            backgroundColor: '#00E676',
            color: '#07171C',
            fontFamily: typographyTokens.fontFamilyUi,
            fontWeight: 700,
            fontSize: '0.65rem',
            px: 0.5,
          }}
        />
      )}

      {hasFastestTag && (
        <Chip
          size="small"
          label="Fastest"
          variant="outlined"
          data-testid="tag-fastest"
          sx={{
            height: 20,
            borderRadius: '10px',
            borderColor: colorTokens.border,
            color: colorTokens.text,
            fontFamily: typographyTokens.fontFamilyUi,
            fontWeight: 600,
            fontSize: '0.65rem',
          }}
        />
      )}
    </Box>
  );
};
