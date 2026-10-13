import React from 'react';
import { Alert, Button } from '@mui/material';
import { colorTokens } from '../../theme/tokens';

interface TripFormAlertsProps {
  isPending: boolean;
  isSlowRequest: boolean;
  generalError: string | null;
  onRetry: () => void;
}

export const TripFormAlerts: React.FC<TripFormAlertsProps> = ({
  isPending,
  isSlowRequest,
  generalError,
  onRetry,
}) => {
  return (
    <>
      {/* Slow Server / Cold-Start Progress Banner */}
      {isPending && isSlowRequest && (
        <Alert
          severity="info"
          data-testid="slow-server-alert"
          sx={{
            backgroundColor: 'rgba(0, 229, 255, 0.08)',
            border: `1px solid rgba(0, 229, 255, 0.3)`,
            color: colorTokens.text,
            fontSize: '0.8125rem',
            lineHeight: 1.4,
            '& .MuiAlert-icon': {
              color: colorTokens.brand,
            },
          }}
        >
          Analyzing live weather along route corridors... Live requests query TomTom commercial truck routing and Open-Meteo atmospheric forecasts across all checkpoints.
        </Alert>
      )}

      {/* General Server Error Alert with Retry Button */}
      {generalError && (
        <Alert
          severity="error"
          data-testid="trip-form-alert"
          action={
            <Button
              color="inherit"
              size="small"
              onClick={onRetry}
              data-testid="retry-button"
            >
              Retry
            </Button>
          }
        >
          {generalError}
        </Alert>
      )}
    </>
  );
};
