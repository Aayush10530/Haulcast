import React from 'react';
import { Box, IconButton } from '@mui/material';
import Flag from '@mui/icons-material/Flag';
import Place from '@mui/icons-material/Place';
import { PlaceDTO } from '../../api/types';
import { colorTokens } from '../../theme/tokens';
import { PlaceAutocomplete } from './PlaceAutocomplete';

const SwapIcon: React.FC = () => (
  <svg
    width="16"
    height="16"
    viewBox="0 0 24 24"
    fill="none"
    stroke="currentColor"
    strokeWidth="2"
    strokeLinecap="round"
    strokeLinejoin="round"
    aria-hidden="true"
  >
    <path d="M7 16V4M7 4L3 8M7 4L11 8" />
    <path d="M17 8V20M17 20L21 16M17 20L13 16" />
  </svg>
);

interface TripPlacesInputsProps {
  origin: PlaceDTO | null;
  destination: PlaceDTO | null;
  originError?: string;
  destinationError?: string;
  disabled: boolean;
  onOriginChange: (val: PlaceDTO | null) => void;
  onDestinationChange: (val: PlaceDTO | null) => void;
  onSwap: () => void;
}

export const TripPlacesInputs: React.FC<TripPlacesInputsProps> = ({
  origin,
  destination,
  originError,
  destinationError,
  disabled,
  onOriginChange,
  onDestinationChange,
  onSwap,
}) => {
  return (
    <>
      {/* Origin Autocomplete */}
      <PlaceAutocomplete
        id="trip-origin"
        label="Origin"
        placeholder="Search origin city or address"
        value={origin}
        onChange={onOriginChange}
        error={originError}
        disabled={disabled}
        startIcon={<Place sx={{ fontSize: 18 }} />}
        data-testid="origin-autocomplete"
      />

      {/* Swap Places Button */}
      <Box sx={{ display: 'flex', justifyContent: 'center', my: -0.5 }}>
        <IconButton
          type="button"
          onClick={onSwap}
          size="small"
          aria-label="Swap origin and destination"
          data-testid="swap-places-button"
          disabled={disabled}
          sx={{
            color: colorTokens.textMuted,
            border: `1px solid ${colorTokens.border}`,
            borderRadius: '50%',
            width: 32,
            height: 32,
            backgroundColor: colorTokens.surfaceRaised,
            transition: 'all 200ms cubic-bezier(0.16, 1, 0.3, 1)',
            '&:hover': {
              color: colorTokens.brand,
              borderColor: colorTokens.brand,
              backgroundColor: colorTokens.surfaceRaised,
              transform: 'rotate(180deg) scale(1.08)',
              boxShadow: '0 0 14px rgba(0, 229, 255, 0.35)',
            },
          }}
        >
          <SwapIcon />
        </IconButton>
      </Box>

      {/* Destination Autocomplete */}
      <PlaceAutocomplete
        id="trip-destination"
        label="Destination"
        placeholder="Search destination city or address"
        value={destination}
        onChange={onDestinationChange}
        error={destinationError}
        disabled={disabled}
        startIcon={<Flag sx={{ fontSize: 18 }} />}
        data-testid="destination-autocomplete"
      />
    </>
  );
};
