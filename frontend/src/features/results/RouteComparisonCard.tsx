import React from 'react';
import { Box, Paper, Typography } from '@mui/material';
import { RouteDTO } from '../../api/types';
import { colorTokens, glassPanelSx, typographyTokens } from '../../theme/tokens';
import { formatDuration, formatMiles, formatRiskScore } from '../../utils/format';

export interface RouteComparisonCardProps {
  routes: RouteDTO[];
}

export const RouteComparisonCard: React.FC<RouteComparisonCardProps> = ({ routes }) => {
  if (!routes || routes.length === 0) {
    return null;
  }

  // Bar Chart calculations
  const chartHeight = 65;
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
        ...glassPanelSx,
        p: 1.5,
        display: 'flex',
        flexDirection: 'column',
        gap: 1.5,
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

      {/* Grouped Bar Chart with Y-axis */}
      <Box sx={{ display: 'flex', alignItems: 'stretch', height: chartHeight + 10, pt: 1 }}>
        {/* Y-axis Ticks */}
        <Box
          sx={{
            display: 'flex',
            flexDirection: 'column',
            justifyContent: 'space-between',
            alignItems: 'flex-end',
            pr: 1,
            pb: 2.5,
            fontSize: '9px',
            color: colorTokens.textMuted,
            fontFamily: typographyTokens.fontFamilyMono,
          }}
        >
          <span>200</span>
          <span>100</span>
          <span>0</span>
        </Box>

        {/* Chart Bars Area with Horizontal Grid Lines */}
        <Box
          sx={{
            flex: 1,
            display: 'flex',
            alignItems: 'flex-end',
            justifyContent: 'space-around',
            position: 'relative',
            borderBottom: `1px solid ${colorTokens.border}`,
            borderLeft: `1px solid ${colorTokens.border}`,
            pl: 1,
          }}
        >
          {/* Faint Horizontal Grid Lines */}
          <Box
            sx={{
              position: 'absolute',
              top: '15%',
              left: 0,
              right: 0,
              height: '1px',
              backgroundColor: 'rgba(255,255,255,0.05)',
              pointerEvents: 'none',
            }}
          />
          <Box
            sx={{
              position: 'absolute',
              top: '55%',
              left: 0,
              right: 0,
              height: '1px',
              backgroundColor: 'rgba(255,255,255,0.05)',
              pointerEvents: 'none',
            }}
          />

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
              <Box key={r.id} sx={{ display: 'flex', flexDirection: 'column', alignItems: 'center', gap: 0.5 }}>
                <Box sx={{ display: 'flex', alignItems: 'center', gap: 0.5 }}>
                  <Box sx={{ width: 4, height: 4, borderRadius: '50%', backgroundColor: '#00D2FF' }} />
                  <Typography sx={{ fontSize: '10px', color: '#00D2FF', fontWeight: 600 }}>
                    {formatDuration(r.duration_seconds)}
                  </Typography>
                </Box>
                <Box sx={{ display: 'flex', alignItems: 'flex-end', gap: 0.5, height: chartHeight - 24 }}>
                  <Box
                    title={`Severe: ${severeM} mi`}
                    sx={{ width: 13, height: `${hSevere}px`, backgroundColor: '#E5484D', borderRadius: '2px 2px 0 0' }}
                  />
                  <Box
                    title={`High: ${highM} mi`}
                    sx={{ width: 13, height: `${hHigh}px`, backgroundColor: '#E8872B', borderRadius: '2px 2px 0 0' }}
                  />
                  <Box
                    title={`Moderate: ${modM} mi`}
                    sx={{ width: 13, height: `${hMod}px`, backgroundColor: '#E2C044', borderRadius: '2px 2px 0 0' }}
                  />
                  <Box
                    title={`Time: ${hours.toFixed(1)} hrs`}
                    sx={{ width: 13, height: `${hTime}px`, backgroundColor: '#00D2FF', borderRadius: '2px 2px 0 0' }}
                  />
                </Box>
                <Typography sx={{ fontSize: '11px', color: colorTokens.text, fontWeight: 600, mt: 0.5 }}>
                  Route {letter}
                </Typography>
              </Box>
            );
          })}
        </Box>
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
              py: 0.35,
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
                <td key={r.id} style={{ color: colorTokens.text }}>{formatMiles(r.distance_miles)}</td>
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
              {routes.map((r) => {
                const isAvail = r.summary?.avg_risk_score !== null && r.summary?.avg_risk_score !== undefined;
                return (
                  <td key={r.id} style={{ color: '#E5484D', fontWeight: 600 }}>
                    {isAvail ? `${Math.round(r.summary?.miles_by_level?.severe || 0)} mi` : '-- mi'}
                  </td>
                );
              })}
            </tr>
            <tr>
              <Box component="td" sx={{ color: colorTokens.textMuted }}>High Miles</Box>
              {routes.map((r) => {
                const isAvail = r.summary?.avg_risk_score !== null && r.summary?.avg_risk_score !== undefined;
                return (
                  <td key={r.id} style={{ color: '#E8872B', fontWeight: 600 }}>
                    {isAvail ? `${Math.round(r.summary?.miles_by_level?.high || 0)} mi` : '-- mi'}
                  </td>
                );
              })}
            </tr>
            <tr>
              <Box component="td" sx={{ color: colorTokens.textMuted }}>Moderate Miles</Box>
              {routes.map((r) => {
                const isAvail = r.summary?.avg_risk_score !== null && r.summary?.avg_risk_score !== undefined;
                return (
                  <td key={r.id} style={{ color: '#E2C044', fontWeight: 600 }}>
                    {isAvail ? `${Math.round(r.summary?.miles_by_level?.moderate || 0)} mi` : '-- mi'}
                  </td>
                );
              })}
            </tr>
            <tr>
              <Box component="td" sx={{ color: colorTokens.textMuted }}>Avg. Risk Score</Box>
              {routes.map((r) => {
                const score = formatRiskScore(r.summary?.avg_risk_score);
                if (score === null) {
                  return (
                    <td key={r.id} style={{ color: colorTokens.textMuted, fontWeight: 700 }}>
                      --
                    </td>
                  );
                }
                const scoreColor = score <= 25 ? '#00E676' : score <= 50 ? '#00D2FF' : score <= 75 ? '#E8872B' : '#E5484D';
                return (
                  <td key={r.id} style={{ color: scoreColor, fontWeight: 700 }} title="Formula: round(avg_risk * 25)">
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
