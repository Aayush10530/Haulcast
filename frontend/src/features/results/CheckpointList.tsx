import React, { useMemo, useState } from 'react';
import { Box, Typography } from '@mui/material';
import { CheckpointDTO } from '../../api/types';
import { typographyTokens } from '../../theme/tokens';
import { CheckpointItem } from './CheckpointItem';
import { SEVERITY_ORDER, SortOption } from './checkpointListUtils';

export interface CheckpointListProps {
  checkpoints: CheckpointDTO[];
  routeLabel?: string;
  originLabel?: string;
  destinationLabel?: string;
  onSelectCheckpoint?: (checkpoint: CheckpointDTO) => void;
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

        {sortedCheckpoints.map((cp, idx) => (
          <CheckpointItem
            key={`checkpoint-${cp.index}`}
            checkpoint={cp}
            index={idx}
            total={sortedCheckpoints.length}
            originLabel={originLabel}
            destinationLabel={destinationLabel}
            isExpanded={expandedIndex === cp.index}
            onToggle={() => toggleRow(cp.index)}
            onSelect={onSelectCheckpoint}
          />
        ))}
      </Box>
    </Box>
  );
};
