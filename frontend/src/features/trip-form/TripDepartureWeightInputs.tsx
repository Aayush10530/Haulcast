import React from 'react';
import { InputAdornment, TextField } from '@mui/material';
import CalendarToday from '@mui/icons-material/CalendarToday';
import Scale from '@mui/icons-material/Scale';
import { colorTokens } from '../../theme/tokens';
import { formatDepartureSpelledOut, formatLoadWeightDisplay } from './validateTripForm';

export interface TripDepartureWeightInputsProps {
  departureLocal: string;
  loadWeightLb: number | '';
  departureError?: string;
  loadWeightError?: string;
  disabled?: boolean;
  onDepartureChange: (val: string) => void;
  onLoadWeightChange: (e: React.ChangeEvent<HTMLInputElement>) => void;
}

export const TripDepartureWeightInputs: React.FC<TripDepartureWeightInputsProps> = ({
  departureLocal,
  loadWeightLb,
  departureError,
  loadWeightError,
  disabled = false,
  onDepartureChange,
  onLoadWeightChange,
}) => {
  return (
    <>
      {/* Departure Local Native Input */}
      <TextField
        label="Departure"
        type="datetime-local"
        value={departureLocal}
        onChange={(e) => onDepartureChange(e.target.value)}
        error={Boolean(departureError)}
        helperText={
          departureError ||
          formatDepartureSpelledOut(departureLocal) ||
          'Local time at origin'
        }
        disabled={disabled}
        fullWidth
        size="small"
        slotProps={{
          input: {
            startAdornment: (
              <InputAdornment position="start" sx={{ color: colorTokens.textMuted }}>
                <CalendarToday sx={{ fontSize: 18 }} />
              </InputAdornment>
            ),
          },
          inputLabel: { shrink: true },
          htmlInput: {
            step: 60,
            'data-testid': 'departure-input',
          },
        }}
      />

      {/* Load Weight */}
      <TextField
        label="Load weight"
        type="text"
        value={formatLoadWeightDisplay(loadWeightLb)}
        onChange={onLoadWeightChange}
        error={Boolean(loadWeightError)}
        helperText={
          loadWeightError || 'Wind rules apply above 30,000 and 40,000 lb'
        }
        disabled={disabled}
        fullWidth
        size="small"
        slotProps={{
          input: {
            startAdornment: (
              <InputAdornment position="start" sx={{ color: colorTokens.textMuted }}>
                <Scale sx={{ fontSize: 18 }} />
              </InputAdornment>
            ),
            endAdornment: (
              <InputAdornment position="end" sx={{ color: colorTokens.textMuted }}>
                lb
              </InputAdornment>
            ),
          },
          htmlInput: {
            inputMode: 'numeric',
            'data-testid': 'load-weight-input',
          },
        }}
      />
    </>
  );
};
