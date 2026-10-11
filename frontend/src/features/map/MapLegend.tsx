import React from 'react';
import { Box, Typography } from '@mui/material';
import { RiskLevelKey, riskColors } from '../../theme/riskColors';
import { colorTokens, typographyTokens } from '../../theme/tokens';

const ORDERED_LEVELS: RiskLevelKey[] = ['low', 'moderate', 'high', 'severe', 'no_travel'];

export const MapLegend: React.FC = () => {
  return (
    <Box
      data-testid="map-legend"
      sx={{
        position: 'absolute',
        bottom: 20,
        left: 20,
        zIndex: 1000,
        backgroundColor: 'rgba(11, 27, 43, 0.9)',
        backdropFilter: 'blur(8px)',
        border: `1px solid ${colorTokens.border}`,
        borderRadius: '20px',
        px: 2,
        py: 0.85,
        display: 'flex',
        alignItems: 'center',
        gap: 2,
        pointerEvents: 'auto',
        boxShadow: '0 4px 16px rgba(0,0,0,0.4)',
      }}
    >
      <Typography
        sx={{
          fontFamily: typographyTokens.fontFamilyUi,
          fontSize: '0.6875rem',
          fontWeight: 700,
          textTransform: 'uppercase',
          letterSpacing: '0.05em',
          color: colorTokens.textMuted,
          display: { xs: 'none', sm: 'block' },
        }}
      >
        Weather Risk
      </Typography>

      <Box sx={{ display: 'flex', gap: 1.75, alignItems: 'center', flexWrap: 'wrap' }}>
        {ORDERED_LEVELS.map((level) => {
          const spec = riskColors[level];
          return (
            <Box
              key={level}
              data-testid={`legend-item-${level}`}
              sx={{ display: 'flex', alignItems: 'center', gap: 0.75 }}
            >
              <Box
                sx={{
                  width: 8,
                  height: 8,
                  borderRadius: '50%',
                  backgroundColor: spec.background,
                  boxShadow: `0 0 6px ${spec.background}`,
                  flexShrink: 0,
                }}
              />
              <Typography
                sx={{
                  fontFamily: typographyTokens.fontFamilyUi,
                  fontSize: '0.75rem',
                  fontWeight: 600,
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
