import React, { useMemo, useState } from 'react';
import {
  Box,
  Collapse,
  Paper,
  ToggleButton,
  ToggleButtonGroup,
  Typography,
} from '@mui/material';
import { CheckpointDTO, RiskLevelKey } from '../../api/types';
import { RiskChip } from '../../components/RiskChip';
import { riskColors } from '../../theme/riskColors';
import { colorTokens, shapeTokens, typographyTokens } from '../../theme/tokens';
import { formatCheckpointMiles, formatLocalTime } from '../../utils/format';

export interface CheckpointListProps {
  checkpoints: CheckpointDTO[];
  routeLabel?: string;
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

export const CheckpointList: React.FC<CheckpointListProps> = ({
  checkpoints,
  routeLabel = 'Selected route',
  onSelectCheckpoint,
}) => {
  const [sortBy, setSortBy] = useState<SortOption>('mile');
  const [expandedIndex, setExpandedIndex] = useState<number | null>(null);

  const sortedCheckpoints = useMemo(() => {
    if (!checkpoints) return [];
    const list = [...checkpoints];
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
  }, [checkpoints, sortBy]);

  const toggleRow = (index: number) => {
    setExpandedIndex((prev) => (prev === index ? null : index));
  };

  if (!checkpoints || checkpoints.length === 0) {
    return null;
  }

  return (
    <Box data-testid="checkpoint-list" sx={{ mt: 3 }}>
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
        <Typography
          variant="subtitle2"
          sx={{
            fontFamily: typographyTokens.fontFamilyUi,
            fontWeight: 700,
            color: colorTokens.text,
            letterSpacing: '0.01em',
          }}
        >
          Checkpoints ({checkpoints.length}) · {routeLabel}
        </Typography>

        <ToggleButtonGroup
          value={sortBy}
          exclusive
          onChange={(_, val: SortOption | null) => {
            if (val) setSortBy(val);
          }}
          size="small"
          aria-label="Sort checkpoints by mile or risk"
          sx={{
            backgroundColor: colorTokens.surface,
            '& .MuiToggleButton-root': {
              fontFamily: typographyTokens.fontFamilyUi,
              fontSize: '0.75rem',
              fontWeight: 600,
              color: colorTokens.textMuted,
              borderColor: colorTokens.border,
              px: 1.25,
              py: 0.25,
              textTransform: 'none',
              '&.Mui-selected': {
                color: colorTokens.onBrand,
                backgroundColor: colorTokens.brand,
                '&:hover': {
                  backgroundColor: colorTokens.brand,
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

      {/* Checkpoint Rows */}
      <Paper
        variant="outlined"
        sx={{
          backgroundColor: colorTokens.surface,
          borderColor: colorTokens.border,
          borderRadius: `${shapeTokens.panelBorderRadius}px`,
          overflow: 'hidden',
        }}
      >
        {sortedCheckpoints.map((cp, idx) => {
          const isExpanded = expandedIndex === cp.index;
          const isLast = idx === sortedCheckpoints.length - 1;
          const dotColor = cp.risk
            ? riskColors[cp.risk.level].background
            : colorTokens.textMuted;

          return (
            <Box
              key={cp.index}
              data-testid={`checkpoint-row-${cp.index}`}
              onClick={() => {
                toggleRow(cp.index);
                onSelectCheckpoint?.(cp);
              }}
              sx={{
                cursor: 'pointer',
                borderBottom: isLast ? 'none' : `1px solid ${colorTokens.border}`,
                transition: 'background-color 150ms ease-out',
                '&:hover': {
                  backgroundColor: colorTokens.surfaceRaised,
                },
              }}
            >
              {/* Main Row Summary */}
              <Box
                sx={{
                  display: 'flex',
                  alignItems: 'center',
                  p: 1.25,
                  gap: 1.5,
                }}
              >
                {/* Timeline dot */}
                <Box
                  data-testid="checkpoint-timeline-dot"
                  sx={{
                    width: 10,
                    height: 10,
                    borderRadius: '50%',
                    backgroundColor: dotColor,
                    flexShrink: 0,
                  }}
                />

                {/* Mile in Mono */}
                <Typography
                  data-testid="checkpoint-mile"
                  sx={{
                    fontFamily: typographyTokens.fontFamilyMono,
                    fontWeight: 700,
                    fontSize: '0.8125rem',
                    color: colorTokens.text,
                    minWidth: 64,
                  }}
                >
                  {formatCheckpointMiles(cp.mile)}
                </Typography>

                {/* Local ETA in Mono */}
                <Typography
                  data-testid="checkpoint-eta"
                  sx={{
                    fontFamily: typographyTokens.fontFamilyMono,
                    fontSize: '0.75rem',
                    color: colorTokens.textMuted,
                    flex: 1,
                  }}
                >
                  {formatLocalTime(cp.eta_local, cp.local_tz)}
                </Typography>

                {/* RiskChip or Forecast Unavailable */}
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

              {/* Expanded Detail Panel */}
              <Collapse
                in={isExpanded}
                timeout="auto"
                unmountOnExit
                onClick={(e) => e.stopPropagation()}
              >
                <Box
                  data-testid={`checkpoint-detail-${cp.index}`}
                  sx={{
                    backgroundColor: colorTokens.surfaceRaised,
                    px: 3,
                    py: 1.5,
                    borderTop: `1px dashed ${colorTokens.border}`,
                  }}
                >
                  {cp.weather ? (
                    <>
                      {/* Weather Metrics in Mono */}
                      <Box
                        sx={{
                          display: 'flex',
                          gap: 2.5,
                          flexWrap: 'wrap',
                          mb: cp.risk?.reason ? 1 : 0,
                        }}
                      >
                        <Typography
                          data-testid="checkpoint-detail-wind"
                          sx={{
                            fontFamily: typographyTokens.fontFamilyMono,
                            fontSize: '0.75rem',
                            color: colorTokens.text,
                          }}
                        >
                          Wind: <strong>{cp.weather.wind_mph.toFixed(0)} mph</strong>
                        </Typography>
                        <Typography
                          data-testid="checkpoint-detail-rain"
                          sx={{
                            fontFamily: typographyTokens.fontFamilyMono,
                            fontSize: '0.75rem',
                            color: colorTokens.text,
                          }}
                        >
                          Rain: <strong>{cp.weather.rain_in_hr.toFixed(2)} in/hr</strong>
                        </Typography>
                        <Typography
                          data-testid="checkpoint-detail-snow"
                          sx={{
                            fontFamily: typographyTokens.fontFamilyMono,
                            fontSize: '0.75rem',
                            color: colorTokens.text,
                          }}
                        >
                          Snow: <strong>{cp.weather.snow_in_hr.toFixed(2)} in/hr</strong>
                        </Typography>
                      </Box>

                      {/* API Reason Text */}
                      {cp.risk?.reason && (
                        <Typography
                          data-testid="checkpoint-detail-reason"
                          sx={{
                            fontFamily: typographyTokens.fontFamilyUi,
                            fontSize: '0.75rem',
                            color: colorTokens.textMuted,
                            mt: 0.5,
                          }}
                        >
                          {cp.risk.reason}
                        </Typography>
                      )}
                    </>
                  ) : (
                    <Typography
                      sx={{
                        fontFamily: typographyTokens.fontFamilyUi,
                        fontSize: '0.75rem',
                        color: colorTokens.textMuted,
                      }}
                    >
                      Forecast unavailable for this checkpoint.
                    </Typography>
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
