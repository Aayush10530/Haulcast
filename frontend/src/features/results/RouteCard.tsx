import React from 'react';
import { Box, Chip, CircularProgress, Paper, Typography } from '@mui/material';
import { RouteDTO } from '../../api/types';
import { RiskStrip } from '../../components/RiskStrip';
import { colorTokens, typographyTokens } from '../../theme/tokens';
import { formatDelta, formatDuration, formatLocalTime, formatMiles } from '../../utils/format';

export interface RouteCardProps {
  route: RouteDTO;
  isSelected?: boolean;
  isRecommended?: boolean;
  departureLocal?: string;
  originTimezone?: string;
  onSelect?: (routeId: string) => void;
}

export const RouteCard: React.FC<RouteCardProps> = ({
  route,
  isSelected = false,
  isRecommended = false,
  departureLocal,
  originTimezone,
  onSelect,
}) => {
  // Extract route letter: e.g. "Route B" -> "B", or "route_b" -> "B"
  const letter = (
    route.label?.replace(/Route\s*/i, '') ||
    route.id.replace('route_', '').toUpperCase()
  ).slice(0, 1);

  const hasRecommendedTag = route.tags?.includes('recommended') || isRecommended;
  const hasFastestTag = route.tags?.includes('fastest');

  // Avg risk ring calculation (scale 0-4 mapped to 0-100%)
  const avgRisk = route.summary?.avg_risk_score;
  const progressValue = avgRisk !== null && avgRisk !== undefined ? Math.min(100, (avgRisk / 4) * 100) : 0;

  // Delta line
  const deltaSec = route.summary?.delta_vs_fastest_seconds || 0;
  const deltaText = deltaSec > 0 ? `${formatDelta(deltaSec)} vs fastest` : '';

  // Local departure and arrival strings
  const departDisplay = departureLocal ? formatLocalTime(departureLocal, originTimezone) : '';
  const arriveDisplay = route.arrival_local ? formatLocalTime(route.arrival_local) : '';

  return (
    <Paper
      variant="outlined"
      onClick={() => onSelect?.(route.id)}
      data-testid={`route-card-${route.id.toLowerCase()}`}
      sx={{
        p: 2,
        cursor: 'pointer',
        borderRadius: '4px',
        borderWidth: isSelected ? '2px' : '1px',
        borderColor: isSelected ? colorTokens.brand : colorTokens.border,
        backgroundColor: isSelected ? colorTokens.surfaceRaised : colorTokens.surface,
        transition: 'border-color 150ms ease-out, background-color 150ms ease-out',
        '&:hover': {
          borderColor: isSelected ? colorTokens.brand : colorTokens.textMuted,
          backgroundColor: colorTokens.surfaceRaised,
        },
      }}
    >
      {/* Top Header: Badge + Tags + Avg-Risk Ring */}
      <Box sx={{ display: 'flex', alignItems: 'flex-start', justifyContent: 'space-between', mb: 1.5 }}>
        <Box sx={{ display: 'flex', alignItems: 'center', gap: 1, flexWrap: 'wrap' }}>
          {/* 28px square mono letter badge */}
          <Box
            data-testid={`route-badge-${letter.toLowerCase()}`}
            sx={{
              width: 28,
              height: 28,
              minWidth: 28,
              borderRadius: '4px',
              display: 'flex',
              alignItems: 'center',
              justifyContent: 'center',
              fontFamily: typographyTokens.fontFamilyMono,
              fontWeight: 700,
              fontSize: '0.875rem',
              backgroundColor: isSelected ? colorTokens.brand : colorTokens.surfaceRaised,
              color: isSelected ? colorTokens.onBrand : colorTokens.text,
              border: `1px solid ${isSelected ? colorTokens.brand : colorTokens.border}`,
            }}
          >
            {letter}
          </Box>

          {/* Tags */}
          {hasRecommendedTag && (
            <Chip
              size="small"
              label="Recommended"
              data-testid="tag-recommended"
              sx={{
                height: 22,
                borderRadius: '4px',
                backgroundColor: colorTokens.brand,
                color: colorTokens.onBrand,
                fontFamily: typographyTokens.fontFamilyUi,
                fontWeight: 700,
                fontSize: '0.6875rem',
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
                height: 22,
                borderRadius: '4px',
                borderColor: colorTokens.border,
                color: colorTokens.text,
                fontFamily: typographyTokens.fontFamilyUi,
                fontWeight: 600,
                fontSize: '0.6875rem',
              }}
            />
          )}
        </Box>

        {/* Avg-Risk Ring */}
        <Box
          data-testid="avg-risk-ring"
          sx={{ position: 'relative', display: 'inline-flex', width: 56, height: 56, minWidth: 56 }}
        >
          {/* Background track */}
          <CircularProgress
            variant="determinate"
            value={100}
            size={56}
            thickness={3.5}
            sx={{ color: colorTokens.border, position: 'absolute' }}
          />
          {/* Progress fill */}
          <CircularProgress
            variant="determinate"
            value={progressValue}
            size={56}
            thickness={3.5}
            sx={{ color: colorTokens.brand }}
          />
          {/* Inside label */}
          <Box
            sx={{
              top: 0,
              left: 0,
              bottom: 0,
              right: 0,
              position: 'absolute',
              display: 'flex',
              flexDirection: 'column',
              alignItems: 'center',
              justifyContent: 'center',
            }}
          >
            <Typography
              data-testid="avg-risk-score"
              sx={{
                fontFamily: typographyTokens.fontFamilyMono,
                fontSize: '0.8125rem',
                fontWeight: 700,
                color: colorTokens.text,
                lineHeight: 1,
              }}
            >
              {avgRisk !== null && avgRisk !== undefined ? avgRisk.toFixed(2) : '--'}
            </Typography>
            <Typography
              sx={{
                fontFamily: typographyTokens.fontFamilyUi,
                fontSize: '0.5625rem',
                color: colorTokens.textMuted,
                lineHeight: 1,
                mt: 0.25,
              }}
            >
              Avg risk
            </Typography>
          </Box>
        </Box>
      </Box>

      {/* Mono Line: "duration · miles" */}
      <Box sx={{ mb: 1 }}>
        <Typography
          data-testid="route-duration-miles"
          sx={{
            fontFamily: typographyTokens.fontFamilyMono,
            fontWeight: 700,
            fontSize: '0.9375rem',
            color: colorTokens.text,
          }}
        >
          {formatDuration(route.duration_seconds)} · {formatMiles(route.distance_miles)}
        </Typography>
        {route.via && (
          <Typography
            sx={{
              fontFamily: typographyTokens.fontFamilyUi,
              fontSize: '0.75rem',
              color: colorTokens.textMuted,
              mt: 0.25,
            }}
          >
            via {route.via}
          </Typography>
        )}
      </Box>

      {/* Two-dot vertical timeline: departure and arrival local times */}
      {(departDisplay || arriveDisplay) && (
        <Box sx={{ my: 1.5, pl: 0.5 }}>
          {/* Departure dot */}
          {departDisplay && (
            <Box sx={{ display: 'flex', alignItems: 'center', gap: 1 }}>
              <Box
                sx={{
                  width: 7,
                  height: 7,
                  borderRadius: '50%',
                  backgroundColor: colorTokens.textMuted,
                  flexShrink: 0,
                }}
              />
              <Typography
                sx={{
                  fontFamily: typographyTokens.fontFamilyMono,
                  fontSize: '0.75rem',
                  color: colorTokens.textMuted,
                }}
              >
                Depart: {departDisplay}
              </Typography>
            </Box>
          )}

          {/* Vertical connecting line */}
          {departDisplay && arriveDisplay && (
            <Box
              sx={{
                width: '1px',
                height: 10,
                backgroundColor: colorTokens.border,
                ml: '3px',
                my: '1px',
              }}
            />
          )}

          {/* Arrival dot */}
          {arriveDisplay && (
            <Box sx={{ display: 'flex', alignItems: 'center', gap: 1 }}>
              <Box
                sx={{
                  width: 7,
                  height: 7,
                  borderRadius: '50%',
                  backgroundColor: colorTokens.brand,
                  flexShrink: 0,
                }}
              />
              <Typography
                sx={{
                  fontFamily: typographyTokens.fontFamilyMono,
                  fontSize: '0.75rem',
                  color: colorTokens.text,
                }}
              >
                Arrive: {arriveDisplay}
              </Typography>
            </Box>
          )}
        </Box>
      )}

      {/* Delta vs fastest */}
      {deltaText && (
        <Typography
          data-testid="route-delta"
          sx={{
            fontFamily: typographyTokens.fontFamilyMono,
            fontSize: '0.75rem',
            color: colorTokens.textMuted,
            mb: 1.25,
          }}
        >
          {deltaText}
        </Typography>
      )}

      {/* RiskStrip */}
      {route.summary?.miles_by_level && (
        <RiskStrip
          milesByLevel={route.summary.miles_by_level}
          unavailableMiles={route.summary.unavailable_miles}
        />
      )}
    </Paper>
  );
};
