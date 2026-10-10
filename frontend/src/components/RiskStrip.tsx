import React from 'react';
import { Box, Typography } from '@mui/material';
import { RiskLevelKey, riskColors } from '../theme/riskColors';
import { typographyTokens } from '../theme/tokens';

export interface RiskSegment {
  level: RiskLevelKey;
  miles: number;
}

export interface RiskStripProps {
  segments?: RiskSegment[];
  totalMiles?: number;
}

export const RiskStrip: React.FC<RiskStripProps> = ({
  segments = [],
  totalMiles = 0,
}) => {
  const labelParts = segments
    .filter((s) => s.miles > 0)
    .map((s) => `${riskColors[s.level].label}: ${s.miles} mi`);

  const ariaLabel =
    labelParts.length > 0
      ? `Risk breakdown: ${labelParts.join(', ')}`
      : 'No risk segments';

  return (
    <Box sx={{ width: '100%' }}>
      <Box
        role="img"
        aria-label={ariaLabel}
        sx={{
          height: 8,
          width: '100%',
          display: 'flex',
          borderRadius: '2px',
          overflow: 'hidden',
          backgroundColor: '#E4ECEB',
        }}
      >
        {segments.map((seg, idx) => {
          const pct = totalMiles > 0 ? (seg.miles / totalMiles) * 100 : 0;
          return (
            <Box
              key={`${seg.level}-${idx}`}
              sx={{
                width: `${pct}%`,
                height: '100%',
                backgroundColor: riskColors[seg.level].background,
              }}
            />
          );
        })}
      </Box>
      {labelParts.length > 0 && (
        <Typography
          variant="caption"
          sx={{
            fontFamily: typographyTokens.fontFamilyMono,
            fontSize: typographyTokens.mono.fontSize,
            lineHeight: typographyTokens.mono.lineHeight,
            color: 'text.secondary',
            mt: 0.5,
            display: 'block',
          }}
        >
          {labelParts.join(' · ')}
        </Typography>
      )}
    </Box>
  );
};
