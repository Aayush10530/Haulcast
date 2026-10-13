import React from 'react';
import { Button } from '@mui/material';
import { colorTokens, shapeTokens } from '../../theme/tokens';

export interface TripSubmitButtonProps {
  isPending: boolean;
  isSlowRequest: boolean;
}

export const TripSubmitButton: React.FC<TripSubmitButtonProps> = ({
  isPending,
  isSlowRequest,
}) => {
  return (
    <Button
      type="submit"
      variant="contained"
      color="primary"
      disabled={isPending}
      data-testid="generate-routes-button"
      fullWidth
      sx={{
        height: 44,
        minHeight: 44,
        borderRadius: `${shapeTokens.borderRadius}px`,
        backgroundColor: colorTokens.brand,
        color: colorTokens.onBrand,
        fontWeight: 600,
        boxShadow: 'none',
        '&:hover': {
          backgroundColor: colorTokens.brandStrong,
          boxShadow: 'none',
        },
        mt: 1,
      }}
    >
      {isPending
        ? isSlowRequest
          ? 'Analyzing live forecasts...'
          : 'Finding routes...'
        : 'Generate routes →'}
    </Button>
  );
};
