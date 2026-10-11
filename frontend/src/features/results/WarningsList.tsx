import React from 'react';
import { Alert, Box } from '@mui/material';
import { WarningDTO } from '../../api/types';

export interface WarningsListProps {
  warnings?: WarningDTO[];
}

export const WarningsList: React.FC<WarningsListProps> = ({ warnings }) => {
  if (!warnings || warnings.length === 0) return null;

  return (
    <Box
      data-testid="warnings-list"
      sx={{ display: 'flex', flexDirection: 'column', gap: 1, mb: 2 }}
    >
      {warnings.map((w, idx) => (
        <Alert
          key={w.code ? `${w.code}-${idx}` : idx}
          variant="outlined"
          severity={w.code === 'NO_SAFE_ROUTE' ? 'error' : 'warning'}
          data-testid={`warning-alert-${w.code ? w.code.toLowerCase() : idx}`}
          sx={{ py: 0.5 }}
        >
          {w.message}
        </Alert>
      ))}
    </Box>
  );
};
