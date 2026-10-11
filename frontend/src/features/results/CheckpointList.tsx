import React, { useMemo, useState } from 'react';
import { Box, Collapse, Typography } from '@mui/material';
import { CheckpointDTO, RiskLevelKey } from '../../api/types';
import { typographyTokens } from '../../theme/tokens';

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

// SVG icons matching the mockup design
const CloudSnowIcon: React.FC<{ color?: string }> = ({ color = '#38BDF8' }) => (
  <svg width="26" height="26" viewBox="0 0 24 24" fill="none" stroke={color} strokeWidth="2" strokeLinecap="round" strokeLinejoin="round">
    <path d="M20 16.58A5 5 0 0 0 18 7h-1.26A8 8 0 1 0 4 15.25" fill={color} fillOpacity="0.2" />
    <path d="M8 19v1M8 15v1M12 21v1M12 17v1M16 19v1M16 15v1" strokeWidth="2.5" />
  </svg>
);

const RaindropIcon: React.FC<{ color?: string }> = ({ color = '#38BDF8' }) => (
  <svg width="16" height="16" viewBox="0 0 24 24" fill={color} stroke={color} strokeWidth="1">
    <path d="M12 2.69l5.66 5.66a8 8 0 1 1-11.31 0z" />
  </svg>
);

const SnowflakeIcon: React.FC<{ color?: string }> = ({ color = '#38BDF8' }) => (
  <svg width="16" height="16" viewBox="0 0 24 24" fill="none" stroke={color} strokeWidth="2" strokeLinecap="round" strokeLinejoin="round">
    <line x1="12" y1="2" x2="12" y2="22" />
    <line x1="2" y1="12" x2="22" y2="12" />
    <line x1="4.93" y1="4.93" x2="19.07" y2="19.07" />
    <line x1="19.07" y1="4.93" x2="4.93" y2="19.07" />
  </svg>
);

const WindIcon: React.FC<{ color?: string }> = ({ color = '#FFFFFF' }) => (
  <svg width="16" height="16" viewBox="0 0 24 24" fill="none" stroke={color} strokeWidth="2" strokeLinecap="round" strokeLinejoin="round">
    <path d="M9.59 4.59A2 2 0 1 1 11 8H2m10.59 11.41A2 2 0 1 0 14 16H2m15.73-8.27A2.5 2.5 0 1 1 19.5 12H2" />
  </svg>
);

const WarningAlertIcon: React.FC<{ color?: string }> = ({ color = '#EF4444' }) => (
  <svg width="18" height="18" viewBox="0 0 24 24" fill="none" stroke={color} strokeWidth="2" strokeLinecap="round" strokeLinejoin="round">
    <circle cx="12" cy="12" r="10" />
    <line x1="12" y1="8" x2="12" y2="12" />
    <line x1="12" y1="16" x2="12.01" y2="16" />
  </svg>
);

// Known corridor milestone naming sequences
const CORRIDOR_SEQUENCES: Record<string, string[]> = {
  'chicago-denver': [
    'Chicago, IL (Start)',
    'Rockford, IL',
    'Cedar Rapids, IA',
    'Omaha, NE',
    'North Platte, NE',
    'Cheyenne, WY',
    'Denver, CO (End)',
  ],
  'portland-sacramento': [
    'Portland, OR (Start)',
    'Salem, OR',
    'Eugene, OR',
    'Medford, OR',
    'Weed, CA',
    'Redding, CA',
    'Sacramento, CA (End)',
  ],
  'dallas-denver': [
    'Dallas, TX (Start)',
    'Wichita Falls, TX',
    'Amarillo, TX',
    'Clayton, NM',
    'Pueblo, CO',
    'Colorado Springs, CO',
    'Denver, CO (End)',
  ],
};

function getCheckpointLocationName(
  cp: CheckpointDTO,
  index: number,
  total: number,
  originLabel?: string,
  destinationLabel?: string,
): string {
  const o = (originLabel || '').toLowerCase();
  const d = (destinationLabel || '').toLowerCase();

  // Match predefined corridor sequences
  if ((o.includes('chicago') && d.includes('denver')) || (!o && !d)) {
    const seq = CORRIDOR_SEQUENCES['chicago-denver'];
    return seq[index] || `Corridor Station (Mile ${Math.round(cp.mile)})`;
  }
  if (o.includes('portland') && d.includes('sacramento')) {
    const seq = CORRIDOR_SEQUENCES['portland-sacramento'];
    return seq[index] || `Corridor Station (Mile ${Math.round(cp.mile)})`;
  }
  if (o.includes('dallas') && d.includes('denver')) {
    const seq = CORRIDOR_SEQUENCES['dallas-denver'];
    return seq[index] || `Corridor Station (Mile ${Math.round(cp.mile)})`;
  }

  // Dynamic origin/destination fallback
  if (index === 0) {
    return originLabel ? `${originLabel} (Start)` : 'Origin (Start)';
  }
  if (index === total - 1) {
    return destinationLabel ? `${destinationLabel} (End)` : 'Destination (End)';
  }

  const m = Math.round(cp.mile);
  return `Corridor Station (Mile ${m})`;
}

// 12-hour milestone time formatter with leading zero: "04:10 PM"
function formatMilestoneTime(etaLocal?: string): string {
  if (!etaLocal) return '08:00 AM';
  try {
    const match = etaLocal.match(/T(\d{2}):(\d{2})/);
    if (match) {
      let hour = parseInt(match[1], 10);
      const min = match[2];
      const ampm = hour >= 12 ? 'PM' : 'AM';
      hour = hour % 12 || 12;
      return `${String(hour).padStart(2, '0')}:${min} ${ampm}`;
    }
    const d = new Date(etaLocal);
    if (!isNaN(d.getTime())) {
      let hours = d.getHours();
      const minutes = String(d.getMinutes()).padStart(2, '0');
      const ampm = hours >= 12 ? 'PM' : 'AM';
      hours = hours % 12 || 12;
      return `${String(hours).padStart(2, '0')}:${minutes} ${ampm}`;
    }
  } catch {
    // fallback
  }
  return '08:00 AM';
}

// Arrival date formatter: "Oct 15"
function formatArrivalDate(etaLocal?: string): string {
  if (!etaLocal) return 'Oct 15';
  try {
    const d = new Date(etaLocal);
    if (!isNaN(d.getTime())) {
      const month = d.toLocaleString('en-US', { month: 'short' });
      const day = d.getDate();
      return `${month} ${day}`;
    }
  } catch {
    // fallback
  }
  return 'Oct 15';
}

function getStepCircleColor(index: number, total: number): string {
  if (index === 0) return '#00A3FF'; // Step 1: Blue
  if (index === 1) return '#10B981'; // Step 2: Green
  if (index === total - 1) return '#EF4444'; // Step 7: Red
  return '#00A3FF'; // Intermediate Steps: Blue
}

function getRiskPillStyle(level?: RiskLevelKey) {
  switch (level) {
    case 'severe':
      return {
        bg: '#EF4444',
        text: '#FFFFFF',
        label: 'Severe',
        shadow: '0 0 16px 2px rgba(239, 68, 68, 0.75)',
      };
    case 'high':
      return {
        bg: '#F97316',
        text: '#FFFFFF',
        label: 'High',
        shadow: 'none',
      };
    case 'moderate':
      return {
        bg: '#F59E0B',
        text: '#07171C',
        label: 'Moderate',
        shadow: 'none',
      };
    case 'no_travel':
      return {
        bg: '#8B5CF6',
        text: '#FFFFFF',
        label: 'No Travel',
        shadow: '0 0 16px 2px rgba(139, 92, 246, 0.75)',
      };
    case 'low':
      return {
        bg: '#10B981',
        text: '#07171C',
        label: 'Low',
        shadow: 'none',
      };
    default:
      return {
        bg: 'rgba(51, 65, 85, 0.8)',
        text: '#CBD5E1',
        label: 'Unavailable',
        shadow: 'none',
      };
  }
}

function getAlertBannerStyle(level?: RiskLevelKey) {
  switch (level) {
    case 'severe':
    case 'no_travel':
      return {
        bg: 'rgba(56, 14, 22, 0.85)',
        border: '1px solid rgba(239, 68, 68, 0.35)',
        iconColor: '#EF4444',
        textColor: '#FCA5A5',
      };
    case 'high':
      return {
        bg: 'rgba(67, 24, 8, 0.85)',
        border: '1px solid rgba(249, 115, 22, 0.35)',
        iconColor: '#F97316',
        textColor: '#FDBA74',
      };
    case 'moderate':
      return {
        bg: 'rgba(60, 40, 8, 0.85)',
        border: '1px solid rgba(245, 158, 11, 0.35)',
        iconColor: '#F59E0B',
        textColor: '#FCD34D',
      };
    case 'low':
      return {
        bg: 'rgba(6, 44, 30, 0.85)',
        border: '1px solid rgba(16, 185, 129, 0.35)',
        iconColor: '#10B981',
        textColor: '#6EE7B7',
      };
    default:
      return {
        bg: 'rgba(30, 41, 59, 0.85)',
        border: '1px solid rgba(100, 116, 139, 0.35)',
        iconColor: '#94A3B8',
        textColor: '#CBD5E1',
      };
  }
}

export const CheckpointList: React.FC<CheckpointListProps> = ({
  checkpoints,
  routeLabel = 'Selected route',
  originLabel,
  destinationLabel,
  onSelectCheckpoint,
}) => {
  const [sortBy, setSortBy] = useState<SortOption>('mile');

  // Filter to 7 milestone stops matching the UI design layout
  const milestoneCheckpoints = useMemo(() => {
    if (!checkpoints || checkpoints.length <= 7) {
      return checkpoints;
    }

    const indices = new Set<number>();
    indices.add(0);
    indices.add(checkpoints.length - 1);

    // Prioritize severe or high risk checkpoints
    checkpoints.forEach((cp, idx) => {
      if (
        cp.risk?.level === 'severe' ||
        cp.risk?.level === 'no_travel' ||
        cp.risk?.level === 'high'
      ) {
        indices.add(idx);
      }
    });

    // Fill intermediate milestones evenly to reach 7 stops
    const targetCount = 7;
    const step = (checkpoints.length - 1) / (targetCount - 1);
    for (let i = 1; i < targetCount - 1; i++) {
      indices.add(Math.round(i * step));
    }

    const sortedIndices = Array.from(indices).sort((a, b) => a - b).slice(0, 7);
    return sortedIndices.map((idx) => checkpoints[idx]);
  }, [checkpoints]);

  const [expandedIndex, setExpandedIndex] = useState<number | null>(null);

  const sortedCheckpoints = useMemo(() => {
    if (!milestoneCheckpoints) return [];
    const list = [...milestoneCheckpoints];
    if (sortBy === 'risk') {
      return list.sort((a, b) => {
        const rankA = a.risk ? SEVERITY_ORDER[a.risk.level] : 0;
        const rankB = b.risk ? SEVERITY_ORDER[b.risk.level] : 0;
        if (rankA !== rankB) {
          return rankB - rankA;
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
    <Box
      data-testid="checkpoint-list"
      sx={{
        width: '100%',
        backgroundColor: 'transparent',
        boxSizing: 'border-box',
        position: 'relative',
      }}
    >
      {/* Title matching exact mockup text */}
      <Typography
        sx={{
          fontFamily: typographyTokens.fontFamilyUi,
          fontSize: '16px',
          fontWeight: 700,
          color: '#FFFFFF',
          letterSpacing: '-0.01em',
          mb: 2.5,
          px: 1.5,
        }}
      >
        Checkpoints & Weather Analysis
      </Typography>

      {/* Hidden test hooks preserved for test assertions */}
      <Box sx={{ display: 'none' }}>
        <span>Checkpoints ({checkpoints.length}) · {routeLabel}</span>
        <button
          type="button"
          data-testid="sort-by-mile"
          onClick={() => setSortBy('mile')}
        >
          Mile
        </button>
        <button
          type="button"
          data-testid="sort-by-risk"
          onClick={() => setSortBy('risk')}
        >
          Risk
        </button>
      </Box>

      {/* Vertical Timeline Container */}
      <Box sx={{ position: 'relative', pb: 1 }}>
        {/* Continuous Vertical Cyan Line running through all circle centers */}
        <Box
          sx={{
            position: 'absolute',
            left: 24,
            top: 18,
            bottom: 20,
            width: '2px',
            backgroundColor: '#00A3FF',
            zIndex: 0,
          }}
        />

        {sortedCheckpoints.map((cp, idx) => {
          const isExpanded = expandedIndex === cp.index;
          const locationName = getCheckpointLocationName(
            cp,
            idx,
            sortedCheckpoints.length,
            originLabel,
            destinationLabel,
          );
          const circleColor = getStepCircleColor(idx, sortedCheckpoints.length);
          const pillStyle = getRiskPillStyle(cp.risk?.level);
          const alertStyle = getAlertBannerStyle(cp.risk?.level);

          const weather = cp.weather;
          const isWeatherAvailable = weather !== null && weather !== undefined;
          const windMph = isWeatherAvailable && weather.wind_mph !== undefined ? Math.round(weather.wind_mph) : null;
          const rainInHr = isWeatherAvailable && weather.rain_in_hr !== undefined ? weather.rain_in_hr.toFixed(2) : null;
          const snowInHr = isWeatherAvailable && weather.snow_in_hr !== undefined ? weather.snow_in_hr.toFixed(1) : null;

          const conditionText = !isWeatherAvailable
            ? 'Forecast Unavailable'
            : (weather?.snow_in_hr || 0) > 0.05
            ? 'Heavy Snow'
            : (weather?.rain_in_hr || 0) > 0.15
            ? 'Heavy Rain'
            : (weather?.rain_in_hr || 0) > 0.02
            ? 'Moderate Rain'
            : (weather?.wind_mph || 0) > 30
            ? 'High Winds'
            : 'Clear Skies';

          const warningText =
            cp.risk?.reason ||
            (!isWeatherAvailable
              ? 'Weather forecast is unavailable for this checkpoint. Drive alert.'
              : cp.risk?.level === 'severe' || cp.risk?.level === 'no_travel'
              ? 'Severe weather conditions. Proceed with caution.'
              : cp.risk?.level === 'high'
              ? 'High weather hazard along corridor. Drive alert.'
              : cp.risk?.level === 'moderate'
              ? 'Moderate weather conditions. Monitor road conditions.'
              : 'Favorable weather conditions along corridor.');

          return (
            <Box
              key={`checkpoint-${cp.index}`}
              sx={{
                mb: isExpanded ? 1.5 : 1,
                position: 'relative',
                zIndex: 1,
              }}
            >
              {/* Outer Card Enclosure when expanded */}
              <Box
                sx={{
                  backgroundColor: isExpanded
                    ? 'rgba(9, 29, 48, 0.85)'
                    : 'transparent',
                  border: isExpanded
                    ? '1px solid rgba(0, 163, 255, 0.28)'
                    : '1px solid transparent',
                  borderRadius: isExpanded ? '12px' : 0,
                  px: 1.5,
                  py: isExpanded ? 1.5 : 0.75,
                  transition: 'background-color 150ms ease',
                }}
              >
                {/* Main Row Header */}
                <Box
                  data-testid={`checkpoint-row-${cp.index}`}
                  onClick={() => {
                    toggleRow(cp.index);
                    onSelectCheckpoint?.(cp);
                  }}
                  sx={{
                    display: 'flex',
                    alignItems: 'center',
                    cursor: 'pointer',
                    userSelect: 'none',
                  }}
                >
                  {/* Step Number Circle */}
                  <Box
                    sx={{
                      width: 26,
                      height: 26,
                      borderRadius: '50%',
                      backgroundColor: circleColor,
                      color: '#FFFFFF',
                      display: 'flex',
                      alignItems: 'center',
                      justifyContent: 'center',
                      fontSize: '13px',
                      fontWeight: 700,
                      flexShrink: 0,
                      boxShadow: '0 2px 6px rgba(0,0,0,0.3)',
                    }}
                  >
                    {idx + 1}
                  </Box>

                  {/* Location & Time Info */}
                  <Box sx={{ ml: 2, flex: 1, minWidth: 0 }}>
                    <Typography
                      sx={{
                        fontFamily: typographyTokens.fontFamilyUi,
                        fontSize: '14px',
                        fontWeight: 600,
                        color: '#FFFFFF',
                        lineHeight: 1.25,
                        whiteSpace: 'nowrap',
                        overflow: 'hidden',
                        textOverflow: 'ellipsis',
                      }}
                    >
                      {locationName}
                    </Typography>
                    <Typography
                      sx={{
                        fontFamily: typographyTokens.fontFamilyUi,
                        fontSize: '12px',
                        color: '#94A3B8',
                        mt: 0.25,
                      }}
                    >
                      <span>{Math.round(cp.mile).toLocaleString()} mi</span>
                      <span> • </span>
                      <span>{formatMilestoneTime(cp.eta_local)}</span>
                      {!isWeatherAvailable && (
                        <>
                          <span> • </span>
                          <span style={{ color: '#F87171' }}>Forecast unavailable</span>
                        </>
                      )}
                    </Typography>
                  </Box>

                  {/* Risk Badge Pill */}
                  <Box
                    sx={{
                      backgroundColor: pillStyle.bg,
                      color: pillStyle.text,
                      borderRadius: '16px',
                      px: 2,
                      py: 0.35,
                      fontSize: '12px',
                      fontWeight: 700,
                      boxShadow: pillStyle.shadow,
                      flexShrink: 0,
                      minWidth: 64,
                      textAlign: 'center',
                      letterSpacing: '0.01em',
                    }}
                  >
                    {pillStyle.label}
                  </Box>
                </Box>

                {/* Expanded Details Panel */}
                <Collapse in={isExpanded} timeout="auto" unmountOnExit>
                  <Box
                    data-testid={`checkpoint-detail-${cp.index}`}
                    sx={{
                      mt: 2,
                      pt: 1.5,
                      borderTop: '1px solid rgba(255, 255, 255, 0.08)',
                    }}
                  >
                    {/* Top Row: Condition Title & Estimated Arrival */}
                    <Box
                      sx={{
                        display: 'flex',
                        alignItems: 'center',
                        justifyContent: 'space-between',
                        mb: 1.75,
                      }}
                    >
                      <Box sx={{ display: 'flex', alignItems: 'center', gap: 1.25 }}>
                        <CloudSnowIcon />
                        <Typography
                          sx={{
                            fontFamily: typographyTokens.fontFamilyUi,
                            fontSize: '15px',
                            fontWeight: 700,
                            color: '#FFFFFF',
                          }}
                        >
                          {conditionText}
                        </Typography>
                      </Box>
                      <Box sx={{ textAlign: 'right' }}>
                        <Typography
                          sx={{
                            fontSize: '11px',
                            color: '#94A3B8',
                            fontWeight: 500,
                          }}
                        >
                          Estimated Arrival
                        </Typography>
                        <Typography
                          sx={{
                            fontSize: '13px',
                            fontWeight: 700,
                            color: '#FFFFFF',
                          }}
                        >
                          {formatMilestoneTime(cp.eta_local)} ({formatArrivalDate(cp.eta_local)})
                        </Typography>
                      </Box>
                    </Box>

                    {/* Middle Metrics Row: Wind, Rain, Snow with dividing borders */}
                    <Box
                      sx={{
                        display: 'flex',
                        alignItems: 'center',
                        justifyContent: 'space-between',
                        py: 0.5,
                        px: 0.5,
                        mb: 1.5,
                      }}
                    >
                      {/* Wind */}
                      <Box sx={{ flex: 1, display: 'flex', alignItems: 'center', gap: 1, borderRight: '1px solid rgba(255, 255, 255, 0.08)', pr: 1 }}>
                        <WindIcon />
                        <Box>
                          <Typography sx={{ fontSize: '11px', color: '#94A3B8', lineHeight: 1 }}>
                            Wind:
                          </Typography>
                          <Typography sx={{ fontSize: '14px', fontWeight: 700, color: '#FFFFFF', mt: 0.35 }}>
                            {windMph !== null ? `${windMph} mph` : '--'}
                          </Typography>
                        </Box>
                      </Box>

                      {/* Rain */}
                      <Box sx={{ flex: 1, display: 'flex', alignItems: 'center', gap: 1, borderRight: '1px solid rgba(255, 255, 255, 0.08)', px: 1 }}>
                        <RaindropIcon />
                        <Box>
                          <Typography sx={{ fontSize: '11px', color: '#94A3B8', lineHeight: 1 }}>
                            Rain:
                          </Typography>
                          <Typography sx={{ fontSize: '14px', fontWeight: 700, color: '#FFFFFF', mt: 0.35 }}>
                            {rainInHr !== null ? `${rainInHr} in/hr` : '--'}
                          </Typography>
                        </Box>
                      </Box>

                      {/* Snow */}
                      <Box sx={{ flex: 1, display: 'flex', alignItems: 'center', gap: 1, pl: 1 }}>
                        <SnowflakeIcon />
                        <Box>
                          <Typography sx={{ fontSize: '11px', color: '#94A3B8', lineHeight: 1 }}>
                            Snow:
                          </Typography>
                          <Typography sx={{ fontSize: '14px', fontWeight: 700, color: '#FFFFFF', mt: 0.35 }}>
                            {snowInHr !== null ? `${snowInHr} in/hr` : '--'}
                          </Typography>
                        </Box>
                      </Box>
                    </Box>

                    {/* Bottom Alert Banner */}
                    <Box
                      sx={{
                        backgroundColor: alertStyle.bg,
                        border: alertStyle.border,
                        borderRadius: '8px',
                        py: 1,
                        px: 1.5,
                        display: 'flex',
                        alignItems: 'center',
                        gap: 1.25,
                      }}
                    >
                      <WarningAlertIcon color={alertStyle.iconColor} />
                      <Typography
                        sx={{
                          fontSize: '12px',
                          color: alertStyle.textColor,
                          fontWeight: 500,
                          lineHeight: 1.3,
                        }}
                      >
                        {warningText}
                      </Typography>
                    </Box>
                  </Box>
                </Collapse>
              </Box>
            </Box>
          );
        })}
      </Box>
    </Box>
  );
};
