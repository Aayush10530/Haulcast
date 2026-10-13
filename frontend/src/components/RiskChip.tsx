import React from 'react';
import { Box } from '@mui/material';
import AcUnit from '@mui/icons-material/AcUnit';
import Air from '@mui/icons-material/Air';
import Scale from '@mui/icons-material/Scale';
import WaterDrop from '@mui/icons-material/WaterDrop';
import { CheckpointRiskDTO, RiskLevelKey } from '../api/types';
import { riskColors } from '../theme/riskColors';
import { colorTokens, shapeTokens, typographyTokens } from '../theme/tokens';

export interface RiskChipProps {
  risk?: CheckpointRiskDTO | null;
  level?: RiskLevelKey;
  label?: string;
  driver?: string;
}

export const RiskChip: React.FC<RiskChipProps> = ({
  risk,
  level: propLevel,
  label: propLabel,
  driver: propDriver,
}) => {
  const level = risk?.level || propLevel;
  const driver = risk?.driver || propDriver;
  const loadRuleApplied = Boolean(risk?.load_rule_applied);
  const spec = level ? riskColors[level] : null;

  if (!spec) {
    return (
      <Box
        data-testid="risk-chip"
        sx={{
          display: 'inline-flex',
          alignItems: 'center',
          gap: 0.5,
          px: 0.75,
          py: 0.25,
          borderRadius: `${shapeTokens.borderRadius}px`,
          backgroundColor: 'transparent',
          border: `1px solid ${colorTokens.border}`,
          color: colorTokens.textMuted,
          fontFamily: typographyTokens.fontFamilyUi,
          fontSize: '0.75rem',
          fontWeight: 600,
          lineHeight: 1,
          whiteSpace: 'nowrap',
        }}
      >
        <span>{risk?.level_label || propLabel || 'Forecast unavailable'}</span>
      </Box>
    );
  }

  const displayLabel = risk?.level_label || propLabel || spec.label;

  const renderDriverIcon = () => {
    if (loadRuleApplied || driver === 'load_rule') {
      return (
        <Scale
          sx={{ fontSize: 14, color: spec.contrastText }}
          data-testid="driver-icon-scale"
          aria-hidden="true"
        />
      );
    }
    switch (driver?.toLowerCase()) {
      case 'wind':
        return (
          <Air
            sx={{ fontSize: 14, color: spec.contrastText }}
            data-testid="driver-icon-air"
            aria-hidden="true"
          />
        );
      case 'rain':
        return (
          <WaterDrop
            sx={{ fontSize: 14, color: spec.contrastText }}
            data-testid="driver-icon-waterdrop"
            aria-hidden="true"
          />
        );
      case 'snow':
        return (
          <AcUnit
            sx={{ fontSize: 14, color: spec.contrastText }}
            data-testid="driver-icon-acunit"
            aria-hidden="true"
          />
        );
      default:
        return null;
    }
  };

  return (
    <Box
      data-testid="risk-chip"
      sx={{
        display: 'inline-flex',
        alignItems: 'center',
        gap: 0.5,
        px: 0.75,
        py: 0.25,
        borderRadius: `${shapeTokens.borderRadius}px`,
        backgroundColor: spec.background,
        color: spec.contrastText,
        fontFamily: typographyTokens.fontFamilyUi,
        fontSize: '0.75rem',
        fontWeight: 600,
        lineHeight: 1,
        whiteSpace: 'nowrap',
      }}
    >
      {renderDriverIcon()}
      <span>{displayLabel}</span>
    </Box>
  );
};
