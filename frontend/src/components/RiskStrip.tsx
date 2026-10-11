import React from 'react';
import { Box, Typography } from '@mui/material';
import { RiskLevelKey } from '../api/types';
import { riskColors } from '../theme/riskColors';
import { colorTokens, typographyTokens } from '../theme/tokens';
import { formatMiles } from '../utils/format';

export interface RiskStripProps {
  milesByLevel: Record<RiskLevelKey, number>;
  unavailableMiles?: number;
}

const ORDERED_LEVELS: RiskLevelKey[] = ['low', 'moderate', 'high', 'severe', 'no_travel'];

export const RiskStrip: React.FC<RiskStripProps> = ({
  milesByLevel,
  unavailableMiles = 0,
}) => {
  const low = milesByLevel?.low || 0;
  const moderate = milesByLevel?.moderate || 0;
  const high = milesByLevel?.high || 0;
  const severe = milesByLevel?.severe || 0;
  const noTravel = milesByLevel?.no_travel || 0;
  const unavail = unavailableMiles || 0;

  const total = low + moderate + high + severe + noTravel + unavail;

  // Handle all-zero state
  if (total <= 0) {
    return (
      <Box sx={{ width: '100%' }}>
        <Box
          role="img"
          aria-label="Risk distribution: no risk data"
          data-testid="risk-strip-bar"
          sx={{
            height: 8,
            width: '100%',
            backgroundColor: colorTokens.surfaceRaised,
            border: `1px solid ${colorTokens.border}`,
            borderRadius: '4px',
          }}
        />
        <Typography
          sx={{
            fontFamily: typographyTokens.fontFamilyMono,
            fontSize: '0.75rem',
            color: colorTokens.textMuted,
            mt: 0.5,
          }}
        >
          No risk data
        </Typography>
      </Box>
    );
  }

  // Handle all-unavailable state
  if (unavail > 0 && total === unavail) {
    return (
      <Box sx={{ width: '100%' }}>
        <Box
          role="img"
          aria-label="Risk distribution: forecast unavailable"
          data-testid="risk-strip-bar"
          sx={{
            height: 8,
            width: '100%',
            backgroundColor: colorTokens.surfaceRaised,
            border: `1px solid ${colorTokens.border}`,
            borderRadius: '4px',
          }}
        />
        <Typography
          sx={{
            fontFamily: typographyTokens.fontFamilyMono,
            fontSize: '0.75rem',
            color: colorTokens.textMuted,
            mt: 0.5,
          }}
        >
          Forecast unavailable
        </Typography>
      </Box>
    );
  }

  // Compose nonzero high-risk caption
  const captionParts: string[] = [];
  if (noTravel > 0) {
    captionParts.push(`No Travel ${formatMiles(noTravel)}`);
  }
  if (severe > 0) {
    captionParts.push(`Severe ${formatMiles(severe)}`);
  }
  if (high > 0) {
    captionParts.push(`High ${formatMiles(high)}`);
  }
  const captionText =
    captionParts.length > 0 ? captionParts.join(' · ') : '0 Severe or High miles';

  // Full accessible label
  const ariaLabel = `Risk distribution: Low ${formatMiles(low)}, Moderate ${formatMiles(moderate)}, High ${formatMiles(high)}, Severe ${formatMiles(severe)}, No Travel ${formatMiles(noTravel)}${unavail > 0 ? `, Unavailable ${formatMiles(unavail)}` : ''}`;

  return (
    <Box sx={{ width: '100%' }}>
      <Box
        role="img"
        aria-label={ariaLabel}
        data-testid="risk-strip-bar"
        sx={{
          height: 8,
          width: '100%',
          display: 'flex',
          overflow: 'hidden',
          borderRadius: '4px',
          backgroundColor: colorTokens.surfaceRaised,
        }}
      >
        {ORDERED_LEVELS.map((level) => {
          const miles = milesByLevel[level] || 0;
          if (miles <= 0) return null;
          const pct = (miles / total) * 100;
          return (
            <Box
              key={level}
              data-testid={`risk-segment-${level}`}
              sx={{
                width: `${pct}%`,
                height: '100%',
                backgroundColor: riskColors[level].background,
              }}
            />
          );
        })}
        {unavail > 0 && (
          <Box
            data-testid="risk-segment-unavailable"
            sx={{
              width: `${(unavail / total) * 100}%`,
              height: '100%',
              backgroundColor: colorTokens.border,
            }}
          />
        )}
      </Box>
      <Typography
        data-testid="risk-strip-caption"
        sx={{
          fontFamily: typographyTokens.fontFamilyMono,
          fontSize: '0.75rem',
          lineHeight: 1.4,
          color: colorTokens.textMuted,
          mt: 0.5,
        }}
      >
        {captionText}
      </Typography>
    </Box>
  );
};
