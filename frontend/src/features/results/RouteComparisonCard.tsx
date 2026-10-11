import React from 'react';
import { Box, Paper, Typography } from '@mui/material';
import { RouteDTO } from '../../api/types';
import { colorTokens, shapeTokens, typographyTokens } from '../../theme/tokens';
import { formatDuration, formatMiles } from '../../utils/format';

export interface RouteComparisonCardProps {
  routes: RouteDTO[];
}

export const RouteComparisonCard: React.FC<RouteComparisonCardProps> = ({ routes }) => {
  if (!routes || routes.length === 0) {
    return null;
  }

  // Bar Chart calculations
  const chartHeight = 90;
  // Find max value across severe, high, moderate miles and hours to scale bars nicely
  const maxMiles = Math.max(
    ...routes.map((r) =>
      Math.max(
        r.summary?.miles_by_level?.severe || 0,
        r.summary?.miles_by_level?.high || 0,
        r.summary?.miles_by_level?.moderate || 0,
        (r.duration_seconds || 0) / 3600 * 5, // scaled for visual presence
        100
      )
    ),
    120
  );

  return (
    <Paper
      variant="outlined"
      data-testid="route-comparison-card"
      sx={{
        backgroundColor: colorTokens.surface,
        border: `1px solid ${colorTokens.border}`,
        borderRadius: `${shapeTokens.panelBorderRadius}px`,
        p: 2,
        display: 'flex',
        flexDirection: 'column',
        gap: 2,
        boxSizing: 'border-box',
        overflow: 'hidden',
      }}
    >
      <Box sx={{ display: 'flex', alignItems: 'center', justifyContent: 'space-between' }}>
        <Typography
          sx={{
            fontFamily: typographyTokens.fontFamilyUi,
            fontSize: '15px',
            fontWeight: 600,
            color: colorTokens.text,
          }}
        >
          Route Comparison
        </Typography>

        {/* Legend */}
        <Box sx={{ display: 'flex', alignItems: 'center', gap: 1.5, flexWrap: 'wrap' }}>
          <Box sx={{ display: 'flex', alignItems: 'center', gap: 0.5 }}>
            <Box sx={{ width: 8, height: 8, borderRadius: '2px', backgroundColor: '#E5484D' }} />
            <Typography sx={{ fontSize: '10px', color: colorTokens.textMuted }}>Severe Miles</Typography>
          </Box>
          <Box sx={{ display: 'flex', alignItems: 'center', gap: 0.5 }}>
            <Box sx={{ width: 8, height: 8, borderRadius: '2px', backgroundColor: '#E8872B' }} />
            <Typography sx={{ fontSize: '10px', color: colorTokens.textMuted }}>High Miles</Typography>
          </Box>
          <Box sx={{ display: 'flex', alignItems: 'center', gap: 0.5 }}>
            <Box sx={{ width: 8, height: 8, borderRadius: '2px', backgroundColor: '#E2C044' }} />
            <Typography sx={{ fontSize: '10px', color: colorTokens.textMuted }}>Moderate Miles</Typography>
          </Box>
          <Box sx={{ display: 'flex', alignItems: 'center', gap: 0.5 }}>
            <Box sx={{ width: 8, height: 8, borderRadius: '2px', backgroundColor: '#00D2FF' }} />
            <Typography sx={{ fontSize: '10px', color: colorTokens.textMuted }}>Total Time (hrs)</Typography>
          </Box>
        </Box>
      </Box>

      {/* Grouped Bar Chart */}
      <Box sx={{ display: 'flex', alignItems: 'flex-end', justifyContent: 'space-around', height: chartHeight, pt: 1 }}>
        {routes.map((r) => {
          const letter = (
            r.label?.replace(/Route\s*/i, '') ||
            r.id.replace('route_', '').toUpperCase()
          ).slice(0, 1);
          const severeM = r.summary?.miles_by_level?.severe || 0;
          const highM = r.summary?.miles_by_level?.high || 0;
          const modM = r.summary?.miles_by_level?.moderate || 0;
          const hours = (r.duration_seconds || 0) / 3600;

          const hSevere = Math.max(4, (severeM / maxMiles) * (chartHeight - 20));
          const hHigh = Math.max(4, (highM / maxMiles) * (chartHeight - 20));
          const hMod = Math.max(4, (modM / maxMiles) * (chartHeight - 20));
          const hTime = Math.max(12, ((hours * 5) / maxMiles) * (chartHeight - 20));

          return (
            <Box key={r.id} sx={{ display: 'flex', flexDirection: 'column', alignItems: 'center', gap: 0.75 }}>
              <Typography sx={{ fontSize: '10px', color: '#00D2FF', fontWeight: 600 }}>
                {Math.round(hours)}h
              </Typography>
              <Box sx={{ display: 'flex', alignItems: 'flex-end', gap: 0.5, height: chartHeight - 24 }}>
                <Box
                  title={`Severe: ${severeM} mi`}
                  sx={{ width: 14, height: `${hSevere}px`, backgroundColor: '#E5484D', borderRadius: '3px 3px 0 0' }}
                />
                <Box
                  title={`High: ${highM} mi`}
                  sx={{ width: 14, height: `${hHigh}px`, backgroundColor: '#E8872B', borderRadius: '3px 3px 0 0' }}
                />
                <Box
                  title={`Moderate: ${modM} mi`}
                  sx={{ width: 14, height: `${hMod}px`, backgroundColor: '#E2C044', borderRadius: '3px 3px 0 0' }}
                />
                <Box
                  title={`Time: ${hours.toFixed(1)} hrs`}
                  sx={{ width: 14, height: `${hTime}px`, backgroundColor: '#00D2FF', borderRadius: '3px 3px 0 0' }}
                />
              </Box>
              <Typography sx={{ fontSize: '11px', color: colorTokens.text, fontWeight: 600 }}>
                Route {letter}
              </Typography>
            </Box>
          );
        })}
      </Box>

      {/* Route Metrics Table */}
      <Box sx={{ display: 'flex', flexDirection: 'column', gap: 1 }}>
        <Typography sx={{ fontSize: '13px', fontWeight: 600, color: colorTokens.text }}>
          Route Metrics
        </Typography>

        <Box
          component="table"
          sx={{
            width: '100%',
            borderCollapse: 'collapse',
            fontSize: '11px',
            fontFamily: typographyTokens.fontFamilyUi,
            '& th, & td': {
              py: 0.6,
              px: 1,
              textAlign: 'left',
              borderBottom: `1px solid ${colorTokens.border}`,
            },
            '& th': {
              color: colorTokens.brand,
              fontWeight: 600,
            },
          }}
        >
          <thead>
            <tr>
              <Box component="th" sx={{ color: `${colorTokens.textMuted} !important` }}>Metric</Box>
              {routes.map((r) => {
                const letter = (
                  r.label?.replace(/Route\s*/i, '') ||
                  r.id.replace('route_', '').toUpperCase()
                ).slice(0, 1);
                return <th key={r.id}>Route {letter}</th>;
              })}
            </tr>
          </thead>
          <tbody>
            <tr>
              <Box component="td" sx={{ color: colorTokens.textMuted }}>Distance</Box>
              {routes.map((r) => (
                <td key={r.id} style={{ color: colorTokens.text }}>{formatMiles(r.distance_miles)} mi</td>
              ))}
            </tr>
            <tr>
              <Box component="td" sx={{ color: colorTokens.textMuted }}>Est. Travel Time</Box>
              {routes.map((r) => (
                <td key={r.id} style={{ color: colorTokens.text }}>{formatDuration(r.duration_seconds)}</td>
              ))}
            </tr>
            <tr>
              <Box component="td" sx={{ color: colorTokens.textMuted }}>Severe Miles</Box>
              {routes.map((r) => (
                <td key={r.id} style={{ color: '#E5484D', fontWeight: 600 }}>
                  {Math.round(r.summary?.miles_by_level?.severe || 0)} mi
                </td>
              ))}
            </tr>
            <tr>
              <Box component="td" sx={{ color: colorTokens.textMuted }}>High Miles</Box>
              {routes.map((r) => (
                <td key={r.id} style={{ color: '#E8872B', fontWeight: 600 }}>
                  {Math.round(r.summary?.miles_by_level?.high || 0)} mi
                </td>
              ))}
            </tr>
            <tr>
              <Box component="td" sx={{ color: colorTokens.textMuted }}>Moderate Miles</Box>
              {routes.map((r) => (
                <td key={r.id} style={{ color: '#E2C044', fontWeight: 600 }}>
                  {Math.round(r.summary?.miles_by_level?.moderate || 0)} mi
                </td>
              ))}
            </tr>
            <tr>
              <Box component="td" sx={{ color: colorTokens.textMuted }}>Avg. Risk Score</Box>
              {routes.map((r) => {
                const score = Math.round((r.summary?.avg_risk_score || 0) * 25);
                const scoreColor = score <= 30 ? '#00E676' : score <= 50 ? '#FFD166' : '#FF3366';
                return (
                  <td key={r.id} style={{ color: scoreColor, fontWeight: 700 }}>
                    {score}
                  </td>
                );
              })}
            </tr>
          </tbody>
        </Box>
      </Box>
    </Paper>
  );
};
