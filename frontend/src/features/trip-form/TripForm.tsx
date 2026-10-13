import React, { useEffect, useState } from 'react';
import {
  Box,
  Button,
  InputAdornment,
  TextField,
  Typography,
} from '@mui/material';
import { AnalyzeResponse, IntervalOption, PlaceDTO, TripRequestPayload } from '../../api/types';
import CalendarToday from '@mui/icons-material/CalendarToday';
import Scale from '@mui/icons-material/Scale';
import { useAnalyzeTrip } from '../../hooks/useAnalyzeTrip';
import { colorTokens, shapeTokens, typographyTokens } from '../../theme/tokens';
import { TripFormAlerts } from './TripFormAlerts';
import { TripIntervalSelector } from './TripIntervalSelector';
import { TripPlacesInputs } from './TripPlacesInputs';
import {
  formatDepartureSpelledOut,
  formatLoadWeightDisplay,
  getNextFullHourLocal,
  TripFormErrors,
  TripFormValues,
  validateTripForm,
} from './validateTripForm';

export type { TripFormValues };

export interface TripFormProps {
  onSuccess?: (analysis: AnalyzeResponse) => void;
  disabled?: boolean;
  initialValues?: Partial<TripFormValues>;
}

export const TripForm: React.FC<TripFormProps> = ({
  onSuccess,
  disabled = false,
  initialValues,
}) => {
  const [origin, setOrigin] = useState<PlaceDTO | null>(initialValues?.origin ?? null);
  const [destination, setDestination] = useState<PlaceDTO | null>(
    initialValues?.destination ?? null
  );
  const [departureLocal, setDepartureLocal] = useState<string>(
    initialValues?.departure_local ?? getNextFullHourLocal()
  );
  const [loadWeightLb, setLoadWeightLb] = useState<number | ''>(() => {
    if (initialValues?.load_weight_lb !== undefined) {
      if (typeof initialValues.load_weight_lb === 'number') {
        return initialValues.load_weight_lb;
      }
      const parsed = parseInt(initialValues.load_weight_lb, 10);
      return isNaN(parsed) ? '' : parsed;
    }
    return 40000;
  });
  const [interval, setInterval] = useState<IntervalOption>(initialValues?.interval ?? 'auto');

  const [clientErrors, setClientErrors] = useState<TripFormErrors>({});
  const [serverFieldErrors, setServerFieldErrors] = useState<Record<string, string>>({});
  const [generalError, setGeneralError] = useState<string | null>(null);
  const [isSlowRequest, setIsSlowRequest] = useState(false);

  const analyzeMutation = useAnalyzeTrip();
  const isPending = analyzeMutation.isPending || disabled;

  useEffect(() => {
    if (!isPending) return;
    const timer = setTimeout(() => {
      setIsSlowRequest(true);
    }, 4500);
    return () => {
      clearTimeout(timer);
      setIsSlowRequest(false);
    };
  }, [isPending]);

  const handleSwap = () => {
    setOrigin(destination);
    setDestination(origin);
    setClientErrors((prev) => ({
      ...prev,
      origin: undefined,
      destination: undefined,
    }));
    setServerFieldErrors((prev) => {
      const next = { ...prev };
      delete next.origin;
      delete next.destination;
      return next;
    });
  };

  const handleLoadWeightChange = (e: React.ChangeEvent<HTMLInputElement>) => {
    const rawDigits = e.target.value.replace(/\D/g, '');
    if (rawDigits === '') {
      setLoadWeightLb('');
    } else {
      setLoadWeightLb(parseInt(rawDigits, 10));
    }
    setClientErrors((prev) => ({ ...prev, load_weight_lb: undefined }));
    setServerFieldErrors((prev) => {
      const next = { ...prev };
      delete next.load_weight_lb;
      return next;
    });
  };

  const submitForm = () => {
    const currentValues: TripFormValues = {
      origin,
      destination,
      departure_local: departureLocal,
      load_weight_lb: loadWeightLb,
      interval,
    };

    const validationErrors = validateTripForm(currentValues);
    if (
      Object.keys(validationErrors).length > 0 ||
      !currentValues.origin ||
      !currentValues.destination
    ) {
      setClientErrors(validationErrors);
      return;
    }

    setClientErrors({});
    setServerFieldErrors({});
    setGeneralError(null);

    const payload: TripRequestPayload = {
      origin: currentValues.origin,
      destination: currentValues.destination,
      departure_local: currentValues.departure_local,
      load_weight_lb: Number(currentValues.load_weight_lb),
      interval: currentValues.interval,
    };

    analyzeMutation.mutate(payload, {
      onSuccess: (data) => {
        onSuccess?.(data);
      },
      onError: (err) => {
        if (err.fields) {
          const fields: Record<string, string> = {};
          for (const [key, val] of Object.entries(err.fields)) {
            fields[key] = val[0] || 'Invalid value.';
          }
          setServerFieldErrors(fields);
        }
        if (!err.fields || Object.keys(err.fields).length === 0) {
          setGeneralError(err.message || 'Failed to generate routes.');
        }
      },
    });
  };

  const handleSubmit = (e: React.FormEvent) => {
    e.preventDefault();
    submitForm();
  };

  return (
    <Box
      component="form"
      onSubmit={handleSubmit}
      noValidate
      sx={{
        display: 'flex',
        flexDirection: 'column',
        gap: 2,
      }}
    >
      <Box sx={{ mb: 0.5 }}>
        <Typography
          variant="h1"
          sx={{
            fontFamily: typographyTokens.fontFamilyUi,
            fontSize: typographyTokens.panelTitle.fontSize,
            lineHeight: typographyTokens.panelTitle.lineHeight,
            fontWeight: typographyTokens.panelTitle.fontWeight,
            color: colorTokens.text,
          }}
        >
          Trip planning
        </Typography>
        <Typography
          sx={{
            fontFamily: typographyTokens.fontFamilyUi,
            fontSize: typographyTokens.caption.fontSize,
            lineHeight: typographyTokens.caption.lineHeight,
            color: colorTokens.textMuted,
            mt: 0.5,
          }}
        >
          Plan a safer route with the weather forecast
        </Typography>
      </Box>

      {/* Origin, Swap, and Destination Inputs */}
      <TripPlacesInputs
        origin={origin}
        destination={destination}
        originError={clientErrors.origin || serverFieldErrors.origin}
        destinationError={clientErrors.destination || serverFieldErrors.destination}
        disabled={isPending}
        onOriginChange={(val) => {
          setOrigin(val);
          setClientErrors((prev) => ({ ...prev, origin: undefined }));
          setServerFieldErrors((prev) => {
            const next = { ...prev };
            delete next.origin;
            return next;
          });
        }}
        onDestinationChange={(val) => {
          setDestination(val);
          setClientErrors((prev) => ({ ...prev, destination: undefined }));
          setServerFieldErrors((prev) => {
            const next = { ...prev };
            delete next.destination;
            return next;
          });
        }}
        onSwap={handleSwap}
      />

      {/* Departure Local Native Input */}
      <TextField
        label="Departure"
        type="datetime-local"
        value={departureLocal}
        onChange={(e) => {
          setDepartureLocal(e.target.value);
          setClientErrors((prev) => ({ ...prev, departure_local: undefined }));
          setServerFieldErrors((prev) => {
            const next = { ...prev };
            delete next.departure_local;
            return next;
          });
        }}
        error={Boolean(clientErrors.departure_local || serverFieldErrors.departure_local)}
        helperText={
          clientErrors.departure_local ||
          serverFieldErrors.departure_local ||
          formatDepartureSpelledOut(departureLocal) ||
          'Local time at origin'
        }
        disabled={isPending}
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
        onChange={handleLoadWeightChange}
        error={Boolean(clientErrors.load_weight_lb || serverFieldErrors.load_weight_lb)}
        helperText={
          clientErrors.load_weight_lb ||
          serverFieldErrors.load_weight_lb ||
          'Wind rules apply above 30,000 and 40,000 lb'
        }
        disabled={isPending}
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

      {/* Checkpoint Interval Selector */}
      <TripIntervalSelector
        interval={interval}
        error={clientErrors.interval || serverFieldErrors.interval}
        disabled={isPending}
        onChange={(val) => {
          setInterval(val);
          setClientErrors((prev) => ({ ...prev, interval: undefined }));
          setServerFieldErrors((prev) => {
            const next = { ...prev };
            delete next.interval;
            return next;
          });
        }}
      />

      {/* Slow server alert & error alert */}
      <TripFormAlerts
        isPending={isPending}
        isSlowRequest={isSlowRequest}
        generalError={generalError}
        onRetry={submitForm}
      />

      {/* Form Action Button */}
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
    </Box>
  );
};
