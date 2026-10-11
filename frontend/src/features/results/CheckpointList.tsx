import React, { useMemo, useState } from 'react';
import {
  Box,
  Collapse,
  Paper,
  ToggleButton,
  ToggleButtonGroup,
  Typography,
} from '@mui/material';
import AcUnit from '@mui/icons-material/AcUnit';
import Air from '@mui/icons-material/Air';
import Grain from '@mui/icons-material/Grain';
import WarningAmber from '@mui/icons-material/WarningAmber';
import WbCloudy from '@mui/icons-material/WbCloudy';
import { CheckpointDTO, RiskLevelKey } from '../../api/types';
import { RiskChip } from '../../components/RiskChip';
import { riskColors } from '../../theme/riskColors';
import { colorTokens, shapeTokens, typographyTokens } from '../../theme/tokens';
import { formatCheckpointMiles, formatLocalTime } from '../../utils/format';

export interface CheckpointListProps {
  checkpoints: CheckpointDTO[];
  routeLabel?: string;
  originLabel?: string;
  destinationLabel?: string;
  onSelectCheckpoint?: (checkpoint: CheckpointDTO) => void;
}

type SortOption = 'mile' | 'risk';

const SEVERITY_ORDER: Record<RiskLevelKey, number> = {
  no_travel: 5,
  severe: 4,
  high: 3,
  moderate: 2,
  low: 1,
};

// Helper to provide realistic corridor names for milestones based on the active journey
function getCheckpointLocationName(
  cp: CheckpointDTO,
  index: number,
  total: number,
  originLabel?: string,
  destinationLabel?: string,
): string {
  if (index === 0) {
    return originLabel ? `${originLabel} (Start)` : 'Origin (Start)';
  }
  if (index === total - 1) {
    return destinationLabel ? `${destinationLabel} (End)` : 'Destination (End)';
  }

  const m = Math.round(cp.mile);
  return `Corridor Mile ${m}`;
}

export const CheckpointList: React.FC<CheckpointListProps> = ({
  checkpoints,
  routeLabel = 'Selected route',
  originLabel,
  destinationLabel,
  onSelectCheckpoint,
}) => {
  const [sortBy, setSortBy] = useState<SortOption>('mile');

  // Filter to 6-8 key milestone stops if count is high (> 7), preserving all stops for smaller fixtures
  const milestoneCheckpoints = useMemo(() => {
    if (!checkpoints || checkpoints.length <= 7) {
      return checkpoints;
    }
    const indices = new Set<number>();
    indices.add(0);
    indices.add(checkpoints.length - 1);
    // Include severe or high risk checkpoints
    checkpoints.forEach((cp, idx) => {
      if (
        cp.risk?.level === 'severe' ||
        cp.risk?.level === 'no_travel' ||
        cp.risk?.level === 'high'
      ) {
        indices.add(idx);
      }
    });
    // Add evenly spaced milestones to reach target count of 7
    const targetCount = 7;
    const step = (checkpoints.length - 1) / (targetCount - 1);
    for (let i = 1; i < targetCount - 1; i++) {
      indices.add(Math.round(i * step));
    }
    const sortedIndices = Array.from(indices).sort((a, b) => a - b);
    return sortedIndices.map((idx) => checkpoints[idx]);
  }, [checkpoints]);

  // Default step with severe risk expanded (like Omaha, NE in mockup), or null
  const [expandedIndex, setExpandedIndex] = useState<number | null>(() => {
    const severeCp = checkpoints?.find((cp) => cp.risk?.level === 'severe');
    return severeCp ? severeCp.index : null;
  });

  const sortedCheckpoints = useMemo(() => {
    if (!milestoneCheckpoints) return [];
    const list = [...milestoneCheckpoints];
    if (sortBy === 'risk') {
      return list.sort((a, b) => {
        const rankA = a.risk ? SEVERITY_ORDER[a.risk.level] : 0;
        const rankB = b.risk ? SEVERITY_ORDER[b.risk.level] : 0;
        if (rankA !== rankB) {
          return rankB - rankA; // highest severity first
        }
        return a.mile - b.mile;
      });
    }
    return list.sort((a, b) => a.mile - b.mile);
  }, [milestoneCheckpoints, sortBy]);

  const toggleRow = (index: number) => {
    setExpandedIndex((prev) => (prev === index ? null : index));
  };

  if (!checkpoints || checkpoints.length === 0) {
    return null;
  }

  return (
    <Box data-testid="checkpoint-list" sx={{ mt: 0, width: '100%' }}>
      {/* Header with Title and Sort Toggle */}
      <Box
        sx={{
          display: 'flex',
          alignItems: 'center',
          justifyContent: 'space-between',
          mb: 1.5,
          flexWrap: 'wrap',
          gap: 1,
        }}
      >
        <Box>
          <Typography
            sx={{
              fontFamily: typographyTokens.fontFamilyUi,
              fontSize: '15px',
              fontWeight: 700,
              color: '#FFFFFF',
              letterSpacing: '-0.01em',
            }}
          >
            Checkpoints & Weather Analysis
          </Typography>
          <Typography
            variant="subtitle2"
            sx={{
              fontFamily: typographyTokens.fontFamilyUi,
              fontWeight: 500,
              fontSize: '12px',
              color: colorTokens.textMuted,
              letterSpacing: '0.01em',
            }}
          >
            Checkpoints ({checkpoints.length}) · {routeLabel}
          </Typography>
        </Box>

        <ToggleButtonGroup
          value={sortBy}
          exclusive
          onChange={(_, val: SortOption | null) => {
            if (val) setSortBy(val);
          }}
          size="small"
          aria-label="Sort checkpoints by mile or risk"
          sx={{
            backgroundColor: colorTokens.surfaceRaised,
            borderRadius: '6px',
            border: `1px solid ${colorTokens.border}`,
            '& .MuiToggleButton-root': {
              fontFamily: typographyTokens.fontFamilyUi,
              fontSize: '0.75rem',
              fontWeight: 600,
              color: colorTokens.textMuted,
              border: 'none',
              px: 1.5,
              py: 0.25,
              textTransform: 'none',
              '&.Mui-selected': {
                color: '#07171C',
                backgroundColor: '#00D2FF',
                '&:hover': {
                  backgroundColor: '#00D2FF',
                },
              },
            },
          }}
        >
          <ToggleButton value="mile" data-testid="sort-by-mile">
            Mile
          </ToggleButton>
          <ToggleButton value="risk" data-testid="sort-by-risk">
            Risk
          </ToggleButton>
        </ToggleButtonGroup>
      </Box>

      {/* Vertical Timeline Roadmap Container */}
      <Paper
        variant="outlined"
        sx={{
          backgroundColor: colorTokens.surface,
          borderColor: colorTokens.border,
          borderRadius: `${shapeTokens.panelBorderRadius}px`,
          p: 2,
          position: 'relative',
          overflow: 'hidden',
        }}
      >
        {/* Continuous Vertical Timeline Line */}
        <Box
          sx={{
            position: 'absolute',
            left: 27,
            top: 24,
            bottom: 24,
            width: '2px',
            backgroundColor: '#16324A',
            zIndex: 0,
          }}
        />

        {sortedCheckpoints.map((cp, idx) => {
          const isExpanded = expandedIndex === cp.index;
          const isLast = idx === sortedCheckpoints.length - 1;
          const locationName = getCheckpointLocationName(
            cp,
            idx,
            sortedCheckpoints.length,
            originLabel,
            destinationLabel,
          );

          const dotColor = cp.risk
            ? riskColors[cp.risk.level].background
            : '#00D2FF';

          // Derive weather condition summary string
          const conditionText =
            (cp.weather?.snow_in_hr || 0) > 0.05
              ? 'Heavy Snow'
              : (cp.weather?.rain_in_hr || 0) > 0.15
              ? 'Rain Showers'
              : (cp.weather?.wind_mph || 0) > 30
              ? 'High Wind'
              : cp.risk?.level === 'severe'
              ? 'Severe Weather'
              : 'Clear / Favorable';

          return (
            <Box
              key={cp.index}
              data-testid={`checkpoint-row-${cp.index}`}
              onClick={() => {
                toggleRow(cp.index);
                onSelectCheckpoint?.(cp);
              }}
              sx={{
                position: 'relative',
                zIndex: 1,
                cursor: 'pointer',
                mb: isLast ? 0 : 2,
                transition: 'all 150ms ease-out',
                borderRadius: '8px',
                p: 1,
                '&:hover': {
                  backgroundColor: 'rgba(16, 36, 54, 0.6)',
                },
              }}
            >
              {/* Row Node + Location Header */}
              <Box
                sx={{
                  display: 'flex',
                  alignItems: 'center',
                  justifyContent: 'space-between',
                  gap: 1.5,
                }}
              >
                {/* Left: Step Badge + Location + Subtitle */}
                <Box sx={{ display: 'flex', alignItems: 'center', gap: 1.5 }}>
                  {/* Step Badge */}
                  <Box
                    data-testid="checkpoint-timeline-dot"
                    sx={{
                      width: 22,
                      height: 22,
                      borderRadius: '50%',
                      backgroundColor: isLast ? '#E5484D' : dotColor,
                      color: isLast ? '#FFFFFF' : '#07171C',
                      fontWeight: 700,
                      fontSize: '11px',
                      display: 'flex',
                      alignItems: 'center',
                      justifyContent: 'center',
                      flexShrink: 0,
                      boxShadow: `0 0 8px ${isLast ? 'rgba(229, 72, 77, 0.4)' : 'rgba(0, 210, 255, 0.3)'}`,
                    }}
                  >
                    {isLast ? '📍' : cp.index + 1}
                  </Box>

                  {/* Location & Mile/ETA */}
                  <Box>
                    <Typography
                      sx={{
                        fontFamily: typographyTokens.fontFamilyUi,
                        fontSize: '13px',
                        fontWeight: 700,
                        color: '#FFFFFF',
                        lineHeight: 1.2,
                      }}
                    >
                      {locationName}
                    </Typography>
                    <Typography
                      sx={{
                        fontFamily: typographyTokens.fontFamilyUi,
                        fontSize: '11px',
                        color: colorTokens.textMuted,
                        display: 'flex',
                        alignItems: 'center',
                        gap: 0.5,
                      }}
                    >
                      <span data-testid="checkpoint-mile">{formatCheckpointMiles(cp.mile)}</span>
                      <span>•</span>
                      <span data-testid="checkpoint-eta">{formatLocalTime(cp.eta_local, cp.local_tz)}</span>
                    </Typography>
                  </Box>
                </Box>

                {/* Right: Risk Chip */}
                <Box sx={{ flexShrink: 0 }}>
                  {cp.risk ? (
                    <RiskChip risk={cp.risk} />
                  ) : (
                    <Typography
                      data-testid="checkpoint-unavailable"
                      sx={{
                        fontFamily: typographyTokens.fontFamilyUi,
                        fontSize: '0.75rem',
                        color: colorTokens.textMuted,
                        fontStyle: 'italic',
                      }}
                    >
                      Forecast unavailable
                    </Typography>
                  )}
                </Box>
              </Box>

              {/* Expanded Detail Weather Card (matching Step 4 in mockup) */}
              <Collapse
                in={isExpanded}
                timeout="auto"
                unmountOnExit
                onClick={(e) => e.stopPropagation()}
              >
                <Box
                  data-testid={`checkpoint-detail-${cp.index}`}
                  sx={{
                    backgroundColor: '#081724',
                    border: '1px solid #1A3650',
                    borderRadius: '8px',
                    p: 2,
                    mt: 1.5,
                    ml: 4.25,
                    boxShadow: '0 4px 14px rgba(0,0,0,0.4)',
                  }}
                >
                  {/* Top Weather Status & ETA */}
                  <Box sx={{ display: 'flex', alignItems: 'center', justifyContent: 'space-between', mb: 1.5 }}>
                    <Box sx={{ display: 'flex', alignItems: 'center', gap: 1 }}>
                      <WbCloudy sx={{ color: '#00D2FF', fontSize: 20 }} />
                      <Typography sx={{ fontSize: '13px', fontWeight: 700, color: '#FFFFFF' }}>
                        {conditionText}
                      </Typography>
                    </Box>

                    <Typography sx={{ fontSize: '11px', color: colorTokens.textMuted }}>
                      Estimated Arrival: <strong style={{ color: '#FFFFFF' }}>{formatLocalTime(cp.eta_local, cp.local_tz)}</strong>
                    </Typography>
                  </Box>

                  {/* Weather Metrics */}
                  {cp.weather && (
                    <Box
                      sx={{
                        display: 'flex',
                        alignItems: 'center',
                        gap: 3,
                        py: 1,
                        borderTop: '1px solid #12283C',
                        borderBottom: cp.risk?.reason ? '1px solid #12283C' : 'none',
                        flexWrap: 'wrap',
                      }}
                    >
                      <Box sx={{ display: 'flex', alignItems: 'center', gap: 0.75 }}>
                        <Air sx={{ fontSize: 16, color: '#00D2FF' }} />
                        <Typography sx={{ fontSize: '12px', color: colorTokens.textMuted }}>
                          Wind:{' '}
                          <strong data-testid="checkpoint-detail-wind" style={{ color: '#FFFFFF' }}>
                            {cp.weather.wind_mph.toFixed(0)} mph
                          </strong>
                        </Typography>
                      </Box>

                      <Box sx={{ display: 'flex', alignItems: 'center', gap: 0.75 }}>
                        <Grain sx={{ fontSize: 16, color: '#00D2FF' }} />
                        <Typography sx={{ fontSize: '12px', color: colorTokens.textMuted }}>
                          Rain:{' '}
                          <strong data-testid="checkpoint-detail-rain" style={{ color: '#FFFFFF' }}>
                            {cp.weather.rain_in_hr.toFixed(2)} in/hr
                          </strong>
                        </Typography>
                      </Box>

                      <Box sx={{ display: 'flex', alignItems: 'center', gap: 0.75 }}>
                        <AcUnit sx={{ fontSize: 16, color: '#00D2FF' }} />
                        <Typography sx={{ fontSize: '12px', color: colorTokens.textMuted }}>
                          Snow:{' '}
                          <strong data-testid="checkpoint-detail-snow" style={{ color: '#FFFFFF' }}>
                            {cp.weather.snow_in_hr.toFixed(2)} in/hr
                          </strong>
                        </Typography>
                      </Box>
                    </Box>
                  )}

                  {/* Caution / Advisory Banner */}
                  {cp.risk?.reason && (
                    <Box
                      sx={{
                        display: 'flex',
                        alignItems: 'center',
                        gap: 1,
                        mt: 1.5,
                        p: 1,
                        borderRadius: '6px',
                        backgroundColor:
                          cp.risk.level === 'severe'
                            ? 'rgba(229, 72, 77, 0.15)'
                            : 'rgba(232, 135, 43, 0.15)',
                        border:
                          cp.risk.level === 'severe'
                            ? '1px solid rgba(229, 72, 77, 0.4)'
                            : '1px solid rgba(232, 135, 43, 0.4)',
                        color:
                          cp.risk.level === 'severe' ? '#FFA1A4' : '#FFC480',
                      }}
                    >
                      <WarningAmber sx={{ fontSize: 18, flexShrink: 0 }} />
                      <Typography
                        data-testid="checkpoint-detail-reason"
                        sx={{ fontSize: '11px', fontWeight: 600, lineHeight: 1.3 }}
                      >
                        {cp.risk.reason}
                      </Typography>
                    </Box>
                  )}
                </Box>
              </Collapse>
            </Box>
          );
        })}
      </Paper>
    </Box>
  );
};
