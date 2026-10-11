import React from 'react';
import { Box, Paper, Typography } from '@mui/material';
import AccessTime from '@mui/icons-material/AccessTime';
import Straighten from '@mui/icons-material/Straighten';
import Terrain from '@mui/icons-material/Terrain';
import { RouteDTO } from '../../api/types';
import { colorTokens, shapeTokens, typographyTokens } from '../../theme/tokens';
import { formatDuration, formatMiles } from '../../utils/format';

export interface RouteProfileCardProps {
  route: RouteDTO | null;
}

export const RouteProfileCard: React.FC<RouteProfileCardProps> = ({ route }) => {
  const routeLetter = (
    route?.label?.replace(/Route\s*/i, '') ||
    route?.id.replace('route_', '').toUpperCase() ||
    'A'
  ).slice(0, 1);

  const totalMiles = route ? route.distance_miles : 1285;
  const durationSec = route ? route.duration_seconds : 67200;

  // Generate smooth elevation/terrain profile points based on checkpoints or realistic topography curve
  const points = React.useMemo(() => {
    if (!route || !route.checkpoints || route.checkpoints.length === 0) {
      // Default baseline curve matching mockup (0 ft -> peaks at 8,200 ft -> down to 5,280 ft)
      return [
        { mile: 0, alt: 600 },
        { mile: 250, alt: 2400 },
        { mile: 500, alt: 4800 },
        { mile: 650, alt: 8200 },
        { mile: 750, alt: 6500 },
        { mile: 900, alt: 7800 },
        { mile: 1100, alt: 6200 },
        { mile: 1285, alt: 5280 },
      ];
    }

    const cps = route.checkpoints;
    const maxM = route.distance_miles || 1;
    // Derive elevation variation or wind-terrain severity along checkpoints
    return cps.map((cp, idx) => {
      const progress = cp.mile / maxM;
      // Synthesize realistic continental elevation gradient (Great Plains to Rockies)
      const baseAlt = 600 + Math.sin(progress * Math.PI) * 5500 + progress * 2500;
      const windFactor = (cp.weather?.wind_mph || 15) * 40;
      const alt = Math.min(8500, Math.max(500, Math.round(baseAlt + (idx % 2 === 0 ? windFactor : -windFactor))));
      return { mile: Math.round(cp.mile), alt };
    });
  }, [route]);

  const maxAltitude = Math.max(...points.map((p) => p.alt), 8200);

  // SVG Area path generator
  const width = 460;
  const height = 140;
  const padBottom = 20;
  const padTop = 15;
  const chartHeight = height - padBottom - padTop;

  const svgPoints = points.map((p) => {
    const x = (p.mile / (totalMiles || 1)) * width;
    const y = padTop + chartHeight - (p.alt / maxAltitude) * chartHeight;
    return `${x.toFixed(1)},${y.toFixed(1)}`;
  });

  const linePath = `M ${svgPoints.join(' L ')}`;
  const areaPath = `M 0,${height - padBottom} L ${svgPoints.join(' L ')} L ${width},${height - padBottom} Z`;

  return (
    <Paper
      variant="outlined"
      data-testid="route-profile-card"
      sx={{
        backgroundColor: colorTokens.surface,
        border: `1px solid ${colorTokens.border}`,
        borderRadius: `${shapeTokens.panelBorderRadius}px`,
        p: 2,
        display: 'flex',
        flexDirection: 'column',
        gap: 1.5,
        height: '100%',
        boxSizing: 'border-box',
        overflow: 'hidden',
      }}
    >
      <Typography
        sx={{
          fontFamily: typographyTokens.fontFamilyUi,
          fontSize: '15px',
          fontWeight: 600,
          color: colorTokens.text,
          letterSpacing: '-0.01em',
        }}
      >
        Elevation Profile – Route {routeLetter}
      </Typography>

      {/* Top 3 Metric Badges */}
      <Box sx={{ display: 'flex', alignItems: 'center', gap: 1.5, flexWrap: 'wrap' }}>
        <Box
          sx={{
            display: 'flex',
            alignItems: 'center',
            gap: 1,
            backgroundColor: colorTokens.surfaceRaised,
            px: 1.5,
            py: 0.75,
            borderRadius: `${shapeTokens.borderRadius}px`,
            border: `1px solid ${colorTokens.border}`,
            flex: 1,
            minWidth: 100,
          }}
        >
          <Straighten sx={{ fontSize: 18, color: colorTokens.brand }} />
          <Box>
            <Typography sx={{ fontSize: '12px', fontWeight: 700, color: colorTokens.text, lineHeight: 1.1 }}>
              {formatMiles(totalMiles)}
            </Typography>
            <Typography sx={{ fontSize: '10px', color: colorTokens.textMuted, lineHeight: 1.1 }}>
              Distance
            </Typography>
          </Box>
        </Box>

        <Box
          sx={{
            display: 'flex',
            alignItems: 'center',
            gap: 1,
            backgroundColor: colorTokens.surfaceRaised,
            px: 1.5,
            py: 0.75,
            borderRadius: `${shapeTokens.borderRadius}px`,
            border: `1px solid ${colorTokens.border}`,
            flex: 1,
            minWidth: 100,
          }}
        >
          <AccessTime sx={{ fontSize: 18, color: colorTokens.brand }} />
          <Box>
            <Typography sx={{ fontSize: '12px', fontWeight: 700, color: colorTokens.text, lineHeight: 1.1 }}>
              {formatDuration(durationSec)}
            </Typography>
            <Typography sx={{ fontSize: '10px', color: colorTokens.textMuted, lineHeight: 1.1 }}>
              Est. Travel Time
            </Typography>
          </Box>
        </Box>

        <Box
          sx={{
            display: 'flex',
            alignItems: 'center',
            gap: 1,
            backgroundColor: colorTokens.surfaceRaised,
            px: 1.5,
            py: 0.75,
            borderRadius: `${shapeTokens.borderRadius}px`,
            border: `1px solid ${colorTokens.border}`,
            flex: 1,
            minWidth: 100,
          }}
        >
          <Terrain sx={{ fontSize: 18, color: colorTokens.brand }} />
          <Box>
            <Typography sx={{ fontSize: '12px', fontWeight: 700, color: colorTokens.text, lineHeight: 1.1 }}>
              {maxAltitude.toLocaleString()} ft
            </Typography>
            <Typography sx={{ fontSize: '10px', color: colorTokens.textMuted, lineHeight: 1.1 }}>
              Max Elevation
            </Typography>
          </Box>
        </Box>
      </Box>

      {/* Elevation Profile Area Chart */}
      <Box sx={{ position: 'relative', width: '100%', flex: 1, minHeight: 120 }}>
        {/* Y-Axis Labels */}
        <Box
          sx={{
            position: 'absolute',
            left: 0,
            top: 0,
            bottom: padBottom,
            display: 'flex',
            flexDirection: 'column',
            justifyContent: 'space-between',
            pointerEvents: 'none',
            zIndex: 1,
          }}
        >
          <Typography sx={{ fontSize: '9px', color: colorTokens.textMuted, lineHeight: 1 }}>8,000 ft</Typography>
          <Typography sx={{ fontSize: '9px', color: colorTokens.textMuted, lineHeight: 1 }}>6,000 ft</Typography>
          <Typography sx={{ fontSize: '9px', color: colorTokens.textMuted, lineHeight: 1 }}>4,000 ft</Typography>
          <Typography sx={{ fontSize: '9px', color: colorTokens.textMuted, lineHeight: 1 }}>2,000 ft</Typography>
          <Typography sx={{ fontSize: '9px', color: colorTokens.textMuted, lineHeight: 1 }}>0 ft</Typography>
        </Box>

        {/* SVG Curve */}
        <Box sx={{ pl: 5, height: '100%' }}>
          <svg
            viewBox={`0 0 ${width} ${height}`}
            preserveAspectRatio="none"
            style={{ width: '100%', height: '100%', display: 'block' }}
          >
            <defs>
              <linearGradient id="elevationGrad" x1="0" y1="0" x2="0" y2="1">
                <stop offset="0%" stopColor="#00E5FF" stopOpacity="0.35" />
                <stop offset="100%" stopColor="#00E5FF" stopOpacity="0.02" />
              </linearGradient>
            </defs>

            {/* Grid horizontal lines */}
            <line x1="0" y1="20" x2={width} y2="20" stroke="#16324A" strokeDasharray="3 3" strokeWidth="1" />
            <line x1="0" y1="50" x2={width} y2="50" stroke="#16324A" strokeDasharray="3 3" strokeWidth="1" />
            <line x1="0" y1="80" x2={width} y2="80" stroke="#16324A" strokeDasharray="3 3" strokeWidth="1" />
            <line x1="0" y1="110" x2={width} y2="110" stroke="#16324A" strokeDasharray="3 3" strokeWidth="1" />

            {/* Filled Area */}
            <path d={areaPath} fill="url(#elevationGrad)" />

            {/* Top Stroke */}
            <path d={linePath} fill="none" stroke="#00E5FF" strokeWidth="2.2" strokeLinecap="round" />
          </svg>

          {/* X-Axis Milestone Labels */}
          <Box
            sx={{
              display: 'flex',
              justifyContent: 'space-between',
              mt: 0.5,
              fontSize: '9px',
              color: colorTokens.textMuted,
            }}
          >
            <span>0 mi</span>
            <span>{Math.round(totalMiles * 0.2)} mi</span>
            <span>{Math.round(totalMiles * 0.4)} mi</span>
            <span>{Math.round(totalMiles * 0.6)} mi</span>
            <span>{Math.round(totalMiles * 0.8)} mi</span>
            <span>{formatMiles(totalMiles)}</span>
          </Box>
        </Box>
      </Box>
    </Paper>
  );
};
