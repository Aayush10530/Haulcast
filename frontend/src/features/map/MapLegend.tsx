import React from 'react';
import { Box, Typography } from '@mui/material';
import { RiskLevelKey, riskColors } from '../../theme/riskColors';
import { colorTokens, shapeTokens, typographyTokens } from '../../theme/tokens';

const ORDERED_LEVELS: RiskLevelKey[] = ['low', 'moderate', 'high', 'severe', 'no_travel'];

export const MapLegend: React.FC = () => {
  return (
    <Box
      data-testid="map-legend"
      sx={{
        position: 'absolute',
        bottom: 16,
        left: 16,
        zIndex: 1000,
        backgroundColor: 'rgba(17, 30, 36, 0.92)',
        border: `1px solid ${colorTokens.border}`,
        borderRadius: `${shapeTokens.borderRadius}px`,
        p: '6px 10px',
        display: 'flex',
        flexDirection: 'column',
        gap: 0.5,
        pointerEvents: 'auto',
      }}
    >
      <Typography
        sx={{
          fontFamily: typographyTokens.fontFamilyUi,
          fontSize: '0.625rem',
          fontWeight: 700,
          textTransform: 'uppercase',
          letterSpacing: '0.05em',
          color: colorTokens.textMuted,
          mb: 0.25,
        }}
      >
        Weather Risk
      </Typography>

      <Box sx={{ display: 'flex', gap: 1.25, alignItems: 'center', flexWrap: 'wrap' }}>
        {ORDERED_LEVELS.map((level) => {
          const spec = riskColors[level];
          return (
            <Box
              key={level}
              data-testid={`legend-item-${level}`}
              sx={{ display: 'flex', alignItems: 'center', gap: 0.5 }}
            >
              <Box
                sx={{
                  width: 8,
                  height: 8,
                  borderRadius: '50%',
                  backgroundColor: spec.background,
                  flexShrink: 0,
                }}
              />
              <Typography
                sx={{
                  fontFamily: typographyTokens.fontFamilyUi,
                  fontSize: '0.6875rem',
                  fontWeight: 500,
                  color: colorTokens.text,
                }}
              >
                {spec.label}
              </Typography>
            </Box>
          );
        })}
      </Box>
    </Box>
  );
};
