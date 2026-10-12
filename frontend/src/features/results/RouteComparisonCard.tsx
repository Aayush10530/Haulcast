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

  // 1. Weather Risk Miles Chart Calculations
  const chartHeight = 65;
  const barMaxHeight = chartHeight - 16;
  const maxRiskMiles = Math.max(
    ...routes.flatMap((r) => [
      r.summary?.miles_by_level?.severe || 0,
      r.summary?.miles_by_level?.high || 0,
      r.summary?.miles_by_level?.moderate || 0,
    ]),
    20, // baseline floor so chart scale is meaningful
  );

  // 2. Travel Time Comparison Calculations (separate unit/scale in hours)
  const maxDurationHours = Math.max(
    ...routes.map((r) => (r.duration_seconds || 0) / 3600),
    1,
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
        gap: 2,
        boxSizing: 'border-box',
        overflow: 'hidden',
      }}
    >
      {/* Card Title */}
      <Box sx={{ display: 'flex', alignItems: 'center', justifyContent: 'space-between' }}>
        <Typography
          sx={{
            fontFamily: typographyTokens.fontFamilyUi,
            fontSize: '15px',
            fontWeight: 700,
            color: colorTokens.text,
          }}
        >
          Route Comparison
        </Typography>
      </Box>

      {/* Chart 1: Weather Risk Miles (mi) */}
      <Box sx={{ display: 'flex', flexDirection: 'column', gap: 1 }}>
        <Box sx={{ display: 'flex', alignItems: 'center', justifyContent: 'space-between', flexWrap: 'wrap', gap: 1 }}>
          <Typography sx={{ fontSize: '12px', fontWeight: 600, color: colorTokens.text }}>
            Risk Exposure by Level (miles)
          </Typography>

          {/* Risk Legend */}
          <Box sx={{ display: 'flex', alignItems: 'center', gap: 1.5 }}>
            <Box sx={{ display: 'flex', alignItems: 'center', gap: 0.5 }}>
              <Box sx={{ width: 8, height: 8, borderRadius: '2px', backgroundColor: '#E5484D' }} />
              <Typography sx={{ fontSize: '10px', color: colorTokens.textMuted }}>Severe</Typography>
            </Box>
            <Box sx={{ display: 'flex', alignItems: 'center', gap: 0.5 }}>
              <Box sx={{ width: 8, height: 8, borderRadius: '2px', backgroundColor: '#E8872B' }} />
              <Typography sx={{ fontSize: '10px', color: colorTokens.textMuted }}>High</Typography>
            </Box>
            <Box sx={{ display: 'flex', alignItems: 'center', gap: 0.5 }}>
              <Box sx={{ width: 8, height: 8, borderRadius: '2px', backgroundColor: '#E2C044' }} />
              <Typography sx={{ fontSize: '10px', color: colorTokens.textMuted }}>Moderate</Typography>
            </Box>
          </Box>
        </Box>

        {/* Grouped Bar Chart with Y-axis in Miles */}
        <Box sx={{ display: 'flex', alignItems: 'stretch', height: chartHeight + 12, pt: 0.5 }}>
          {/* Y-axis Ticks (Miles) */}
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
              minWidth: 32,
            }}
          >
            <span>{Math.round(maxRiskMiles)} mi</span>
            <span>{Math.round(maxRiskMiles / 2)} mi</span>
            <span>0 mi</span>
          </Box>

          {/* Chart Bars Area */}
          <Box
            data-testid="risk-miles-chart-area"
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
            {/* Horizontal Grid Lines */}
            <Box
              sx={{
                position: 'absolute',
                top: 0,
                left: 0,
                right: 0,
                height: '1px',
                backgroundColor: 'rgba(255, 255, 255, 0.05)',
                pointerEvents: 'none',
              }}
            />
            <Box
              sx={{
                position: 'absolute',
                top: '50%',
                left: 0,
                right: 0,
                height: '1px',
                backgroundColor: 'rgba(255, 255, 255, 0.05)',
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
              const isRecommended = r.tags?.includes('recommended') || r.rank === 1;

              // Zero risk miles MUST produce 0 height, never a minimum-height bar
              const hSevere = severeM > 0 ? Math.max(3, (severeM / maxRiskMiles) * barMaxHeight) : 0;
              const hHigh = highM > 0 ? Math.max(3, (highM / maxRiskMiles) * barMaxHeight) : 0;
              const hMod = modM > 0 ? Math.max(3, (modM / maxRiskMiles) * barMaxHeight) : 0;

              return (
                <Box key={r.id} sx={{ display: 'flex', flexDirection: 'column', alignItems: 'center', gap: 0.5 }}>
                  <Box sx={{ display: 'flex', alignItems: 'flex-end', gap: 0.5, height: barMaxHeight }}>
                    <Box
                      data-testid={`bar-severe-${r.id}`}
                      data-height={hSevere}
                      title={`Severe: ${Math.round(severeM)} mi`}
                      sx={{
                        width: 14,
                        height: `${hSevere}px`,
                        backgroundColor: '#E5484D',
                        borderRadius: hSevere > 0 ? '2px 2px 0 0' : 0,
                        display: hSevere > 0 ? 'block' : 'none',
                      }}
                    />
                    <Box
                      data-testid={`bar-high-${r.id}`}
                      data-height={hHigh}
                      title={`High: ${Math.round(highM)} mi`}
                      sx={{
                        width: 14,
                        height: `${hHigh}px`,
                        backgroundColor: '#E8872B',
                        borderRadius: hHigh > 0 ? '2px 2px 0 0' : 0,
                        display: hHigh > 0 ? 'block' : 'none',
                      }}
                    />
                    <Box
                      data-testid={`bar-moderate-${r.id}`}
                      data-height={hMod}
                      title={`Moderate: ${Math.round(modM)} mi`}
                      sx={{
                        width: 14,
                        height: `${hMod}px`,
                        backgroundColor: '#E2C044',
                        borderRadius: hMod > 0 ? '2px 2px 0 0' : 0,
                        display: hMod > 0 ? 'block' : 'none',
                      }}
                    />
                  </Box>
                  <Box sx={{ display: 'flex', alignItems: 'center', gap: 0.5, mt: 0.25 }}>
                    <Typography
                      sx={{
                        fontSize: '11px',
                        color: isRecommended ? colorTokens.brand : colorTokens.text,
                        fontWeight: isRecommended ? 700 : 500,
                      }}
                    >
                      Route {letter}
                    </Typography>
                    {isRecommended && (
                      <Box
                        sx={{
                          width: 4,
                          height: 4,
                          borderRadius: '50%',
                          backgroundColor: colorTokens.brand,
                        }}
                        title="Recommended route"
                      />
                    )}
                  </Box>
                </Box>
              );
            })}
          </Box>
        </Box>
      </Box>

      {/* Chart 2: Travel Time Comparison (hours) */}
      <Box sx={{ display: 'flex', flexDirection: 'column', gap: 1 }}>
        <Box sx={{ display: 'flex', alignItems: 'center', justifyContent: 'space-between' }}>
          <Typography sx={{ fontSize: '12px', fontWeight: 600, color: colorTokens.text }}>
            Estimated Travel Time (hours)
          </Typography>
          <Typography sx={{ fontSize: '10px', color: colorTokens.textMuted }}>
            Max: {maxDurationHours.toFixed(1)} hrs
          </Typography>
        </Box>

        <Box data-testid="travel-time-chart-area" sx={{ display: 'flex', flexDirection: 'column', gap: 1 }}>
          {routes.map((r) => {
            const letter = (
              r.label?.replace(/Route\s*/i, '') ||
              r.id.replace('route_', '').toUpperCase()
            ).slice(0, 1);
            const hours = (r.duration_seconds || 0) / 3600;
            const pct = Math.min(100, Math.max(8, (hours / maxDurationHours) * 100));
            const isFastest = (r.summary?.delta_vs_fastest_seconds || 0) === 0;

            return (
              <Box key={`duration-${r.id}`} sx={{ display: 'flex', alignItems: 'center', gap: 1 }}>
                <Typography sx={{ fontSize: '11px', color: colorTokens.text, minWidth: 54, fontWeight: 500 }}>
                  Route {letter}
                </Typography>
                <Box
                  sx={{
                    flex: 1,
                    height: 12,
                    backgroundColor: 'rgba(255, 255, 255, 0.05)',
                    borderRadius: '3px',
                    overflow: 'hidden',
                    position: 'relative',
                  }}
                >
                  <Box
                    data-testid={`bar-time-${r.id}`}
                    sx={{
                      width: `${pct}%`,
                      height: '100%',
                      backgroundColor: isFastest ? colorTokens.brand : 'rgba(0, 229, 255, 0.65)',
                      borderRadius: '3px',
                      transition: 'width 250ms ease',
                    }}
                  />
                </Box>
                <Typography
                  data-testid={`label-time-${r.id}`}
                  sx={{
                    fontSize: '11px',
                    fontFamily: typographyTokens.fontFamilyMono,
                    color: isFastest ? colorTokens.brand : colorTokens.textMuted,
                    fontWeight: isFastest ? 700 : 500,
                    minWidth: 56,
                    textAlign: 'right',
                  }}
                >
                  {formatDuration(r.duration_seconds)}
                </Typography>
              </Box>
            );
          })}
        </Box>
      </Box>

      {/* Section 3: Route Metrics Table */}
      <Box sx={{ display: 'flex', flexDirection: 'column', gap: 0.75 }}>
        <Typography sx={{ fontSize: '12px', fontWeight: 600, color: colorTokens.text }}>
          Route Metrics Summary
        </Typography>

        <Box
          component="table"
          data-testid="route-metrics-table"
          sx={{
            width: '100%',
            borderCollapse: 'collapse',
            fontSize: '11px',
            fontFamily: typographyTokens.fontFamilyUi,
            '& th, & td': {
              py: 0.4,
              px: 0.75,
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
              <Box component="th" sx={{ color: `${colorTokens.textMuted} !important` }}>
                Metric
              </Box>
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
              <Box component="td" sx={{ color: colorTokens.textMuted }}>
                Distance
              </Box>
              {routes.map((r) => (
                <td key={r.id} style={{ color: colorTokens.text }}>
                  {formatMiles(r.distance_miles)}
                </td>
              ))}
            </tr>
            <tr>
              <Box component="td" sx={{ color: colorTokens.textMuted }}>
                Est. Travel Time
              </Box>
              {routes.map((r) => (
                <td key={r.id} style={{ color: colorTokens.text }}>
                  {formatDuration(r.duration_seconds)}
                </td>
              ))}
            </tr>
            <tr>
              <Box component="td" sx={{ color: colorTokens.textMuted }}>
                Severe Miles
              </Box>
              {routes.map((r) => {
                const isAvail = r.summary?.avg_risk_score !== null && r.summary?.avg_risk_score !== undefined;
                return (
                  <td key={r.id} data-testid={`metric-severe-${r.id}`} style={{ color: '#E5484D', fontWeight: 600 }}>
                    {isAvail ? `${Math.round(r.summary?.miles_by_level?.severe || 0)} mi` : '-- mi'}
                  </td>
                );
              })}
            </tr>
            <tr>
              <Box component="td" sx={{ color: colorTokens.textMuted }}>
                High Miles
              </Box>
              {routes.map((r) => {
                const isAvail = r.summary?.avg_risk_score !== null && r.summary?.avg_risk_score !== undefined;
                return (
                  <td key={r.id} data-testid={`metric-high-${r.id}`} style={{ color: '#E8872B', fontWeight: 600 }}>
                    {isAvail ? `${Math.round(r.summary?.miles_by_level?.high || 0)} mi` : '-- mi'}
                  </td>
                );
              })}
            </tr>
            <tr>
              <Box component="td" sx={{ color: colorTokens.textMuted }}>
                Moderate Miles
              </Box>
              {routes.map((r) => {
                const isAvail = r.summary?.avg_risk_score !== null && r.summary?.avg_risk_score !== undefined;
                return (
                  <td key={r.id} data-testid={`metric-moderate-${r.id}`} style={{ color: '#E2C044', fontWeight: 600 }}>
                    {isAvail ? `${Math.round(r.summary?.miles_by_level?.moderate || 0)} mi` : '-- mi'}
                  </td>
                );
              })}
            </tr>
            <tr>
              <Box component="td" sx={{ color: colorTokens.textMuted }}>
                Avg. Risk Score
              </Box>
              {routes.map((r) => {
                const score = formatRiskScore(r.summary?.avg_risk_score);
                if (score === null) {
                  return (
                    <td key={r.id} style={{ color: colorTokens.textMuted, fontWeight: 700 }}>
                      --
                    </td>
                  );
                }
                const scoreColor =
                  score <= 25 ? '#00E676' : score <= 50 ? '#00D2FF' : score <= 75 ? '#E8872B' : '#E5484D';
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
