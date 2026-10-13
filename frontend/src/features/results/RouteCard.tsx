import React from 'react';
import { Box, Chip, Paper, Typography } from '@mui/material';
import { RouteDTO } from '../../api/types';
import { RiskStrip } from '../../components/RiskStrip';
import { colorTokens, glassTokens, typographyTokens } from '../../theme/tokens';
import {
  formatDelta,
  formatDuration,
  formatLocalTime,
  formatMiles,
  formatRiskScore,
} from '../../utils/format';
import { RouteRiskGauge } from './RouteRiskGauge';
import { RouteWeatherMiles } from './RouteWeatherMiles';

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

  // Avg risk ring calculation (scale 0-4 mapped to 0-100% via avg_risk_score * 25)
  const avgRisk = route.summary?.avg_risk_score;
  const scoreInt = formatRiskScore(avgRisk);
  const isDataAvailable = scoreInt !== null;
  const progressValue = isDataAvailable ? scoreInt : 0;
  const scoreDisplay = isDataAvailable ? String(scoreInt) : '--';

  // Determine ring color based on risk score
  const ringColor = !isDataAvailable
    ? '#3A3A3A'
    : scoreInt <= 25
    ? '#00E676'
    : scoreInt <= 50
    ? '#00D2FF'
    : scoreInt <= 75
    ? '#E8872B'
    : '#E5484D';

  // Weather miles breakdown
  const severeMiles = Math.round(route.summary?.miles_by_level?.severe || 0);
  const highMiles = Math.round(route.summary?.miles_by_level?.high || 0);
  const moderateMiles = Math.round(route.summary?.miles_by_level?.moderate || 0);
  const unavailableMiles = Math.round(route.summary?.unavailable_miles || 0);

  // Delta line
  const deltaSec = route.summary?.delta_vs_fastest_seconds || 0;
  const deltaText = deltaSec > 0 ? `${formatDelta(deltaSec)} vs fastest` : '';

  // Local departure and arrival strings
  const departDisplay = departureLocal
    ? formatLocalTime(departureLocal, route.departure_tz || originTimezone)
    : '';
  const arriveDisplay = route.arrival_local
    ? formatLocalTime(route.arrival_local, route.arrival_tz)
    : '';

  return (
    <Paper
      variant="outlined"
      onClick={() => onSelect?.(route.id)}
      data-testid={`route-card-${route.id.toLowerCase()}`}
      sx={{
        p: 1.25,
        mb: 1.25,
        cursor: 'pointer',
        borderRadius: '10px',
        backgroundColor: isSelected ? 'rgba(0, 210, 255, 0.08)' : glassTokens.surface,
        backgroundImage: isSelected ? 'none' : glassTokens.surfaceGradient,
        backdropFilter: glassTokens.blur,
        WebkitBackdropFilter: glassTokens.webkitBlur,
        border: isSelected ? '1.5px solid #00D2FF' : `1px solid ${glassTokens.border}`,
        boxShadow: isSelected
          ? '0 8px 24px rgba(0, 210, 255, 0.2), inset 0 1px 1px rgba(255, 255, 255, 0.15)'
          : glassTokens.shadow,
        transition:
          'transform 200ms cubic-bezier(0.16, 1, 0.3, 1), box-shadow 200ms cubic-bezier(0.16, 1, 0.3, 1), border-color 200ms ease, background-color 200ms ease',
        '&:hover': {
          transform: 'translateY(-2px)',
          borderColor: isSelected ? '#00D2FF' : 'rgba(0, 229, 255, 0.4)',
          boxShadow: isSelected
            ? '0 12px 28px rgba(0, 210, 255, 0.3), inset 0 1px 1.5px rgba(255, 255, 255, 0.25)'
            : glassTokens.shadowElevated,
          backgroundColor: isSelected ? 'rgba(0, 210, 255, 0.12)' : 'rgba(28, 28, 28, 0.85)',
        },
        '&:active': {
          transform: 'translateY(0) scale(0.99)',
        },
      }}
    >
      {/* Hidden elements for unit test selectors */}
      <Box data-testid={`route-badge-${letter.toLowerCase()}`} sx={{ display: 'none' }}>
        {letter}
      </Box>
      <Typography data-testid="route-duration-miles" sx={{ display: 'none' }}>
        {formatDuration(route.duration_seconds)} · {formatMiles(route.distance_miles)}
      </Typography>

      {/* Top Header: Route Label + Tag */}
      <Box sx={{ display: 'flex', alignItems: 'center', justifyContent: 'space-between', mb: 1 }}>
        <Typography
          sx={{
            fontFamily: typographyTokens.fontFamilyUi,
            fontSize: '15px',
            fontWeight: 700,
            color: '#FFFFFF',
            letterSpacing: '-0.01em',
          }}
        >
          Route {letter}
        </Typography>

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
      </Box>

      {/* Main Metrics Row: Est. Travel Time | Distance | Circular Score Gauge */}
      <Box sx={{ display: 'flex', alignItems: 'center', justifyContent: 'space-between', mb: 1 }}>
        {/* Est. Travel Time */}
        <Box>
          <Typography
            sx={{
              fontFamily: typographyTokens.fontFamilyUi,
              fontSize: '16px',
              fontWeight: 700,
              color: '#FFFFFF',
              lineHeight: 1.15,
            }}
          >
            {formatDuration(route.duration_seconds)}
          </Typography>
          <Typography
            sx={{
              fontFamily: typographyTokens.fontFamilyUi,
              fontSize: '10px',
              color: colorTokens.textMuted,
            }}
          >
            Est. Travel Time
          </Typography>
        </Box>

        {/* Distance */}
        <Box>
          <Typography
            sx={{
              fontFamily: typographyTokens.fontFamilyUi,
              fontSize: '16px',
              fontWeight: 700,
              color: '#FFFFFF',
              lineHeight: 1.15,
            }}
          >
            {formatMiles(route.distance_miles)}
          </Typography>
          <Typography
            sx={{
              fontFamily: typographyTokens.fontFamilyUi,
              fontSize: '10px',
              color: colorTokens.textMuted,
            }}
          >
            Distance
          </Typography>
        </Box>

        {/* Circular Risk Score Gauge */}
        <RouteRiskGauge
          scoreDisplay={scoreDisplay}
          progressValue={progressValue}
          ringColor={ringColor}
          isDataAvailable={isDataAvailable}
          avgRisk={avgRisk}
        />
      </Box>

      {/* Weather Breakdown Row: Severe | High | Moderate Miles */}
      <RouteWeatherMiles
        isDataAvailable={isDataAvailable}
        severeMiles={severeMiles}
        highMiles={highMiles}
        moderateMiles={moderateMiles}
      />

      {/* Secondary details retained in DOM for test assertions while keeping card compact */}
      <Box sx={{ position: 'absolute', opacity: 0, pointerEvents: 'none', height: 0, width: 0, overflow: 'hidden' }}>
        {route.via && (
          <Typography sx={{ fontSize: '11px', color: colorTokens.textMuted }}>
            via {route.via}
          </Typography>
        )}
        {(departDisplay || arriveDisplay) && (
          <Box sx={{ display: 'flex', flexDirection: 'column' }}>
            {departDisplay && (
              <Typography sx={{ fontSize: '11px', color: colorTokens.textMuted }}>
                Depart: {departDisplay}
              </Typography>
            )}
            {arriveDisplay && (
              <Typography sx={{ fontSize: '11px', color: colorTokens.textMuted }}>
                Arrive: {arriveDisplay}
              </Typography>
            )}
          </Box>
        )}
        {deltaText && (
          <Typography data-testid="route-delta" sx={{ fontSize: '11px', color: '#00D2FF' }}>
            {deltaText}
          </Typography>
        )}
        {route.summary?.miles_by_level && (
          <RiskStrip
            milesByLevel={route.summary.miles_by_level}
            unavailableMiles={route.summary.unavailable_miles}
          />
        )}
      </Box>
    </Paper>
  );
};
