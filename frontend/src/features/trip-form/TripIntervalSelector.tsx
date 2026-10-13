import React from 'react';
import { Box, FormHelperText, ToggleButton, ToggleButtonGroup, Typography } from '@mui/material';
import { IntervalOption } from '../../api/types';
import { colorTokens, typographyTokens } from '../../theme/tokens';

interface TripIntervalSelectorProps {
  interval: IntervalOption;
  error?: string;
  disabled: boolean;
  onChange: (val: IntervalOption) => void;
}

export const TripIntervalSelector: React.FC<TripIntervalSelectorProps> = ({
  interval,
  error,
  disabled,
  onChange,
}) => {
  return (
    <Box>
      <Typography
        sx={{
          fontFamily: typographyTokens.fontFamilyUi,
          fontSize: typographyTokens.label.fontSize,
          lineHeight: typographyTokens.label.lineHeight,
          fontWeight: typographyTokens.label.fontWeight,
          letterSpacing: typographyTokens.label.letterSpacing,
          textTransform: typographyTokens.label.textTransform,
          color: colorTokens.textMuted,
          mb: 0.75,
        }}
      >
        Checkpoint interval
      </Typography>
      <ToggleButtonGroup
        value={interval}
        exclusive
        onChange={(_, val: IntervalOption | null) => {
          if (val !== null) {
            onChange(val);
          }
        }}
        disabled={disabled}
        size="small"
        fullWidth
        aria-label="Checkpoint interval"
      >
        <ToggleButton value="auto" data-testid="interval-auto">
          Auto
        </ToggleButton>
        <ToggleButton value={10} data-testid="interval-10">
          10 mi
        </ToggleButton>
        <ToggleButton value={25} data-testid="interval-25">
          25 mi
        </ToggleButton>
        <ToggleButton value={50} data-testid="interval-50">
          50 mi
        </ToggleButton>
      </ToggleButtonGroup>
      {error && <FormHelperText error>{error}</FormHelperText>}
    </Box>
  );
};
