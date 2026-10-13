import React, { useEffect, useState } from 'react';
import { Box } from '@mui/material';
import { AnalyzeResponse, IntervalOption, PlaceDTO, TripRequestPayload } from '../../api/types';
import { useAnalyzeTrip } from '../../hooks/useAnalyzeTrip';
import { TripDepartureWeightInputs } from './TripDepartureWeightInputs';
import { TripFormAlerts } from './TripFormAlerts';
import { TripFormHeader } from './TripFormHeader';
import { TripIntervalSelector } from './TripIntervalSelector';
import { TripPlacesInputs } from './TripPlacesInputs';
import { TripSubmitButton } from './TripSubmitButton';
import {
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
      <TripFormHeader />

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

      {/* Departure & Load Weight Inputs */}
      <TripDepartureWeightInputs
        departureLocal={departureLocal}
        loadWeightLb={loadWeightLb}
        departureError={clientErrors.departure_local || serverFieldErrors.departure_local}
        loadWeightError={clientErrors.load_weight_lb || serverFieldErrors.load_weight_lb}
        disabled={isPending}
        onDepartureChange={(val) => {
          setDepartureLocal(val);
          setClientErrors((prev) => ({ ...prev, departure_local: undefined }));
          setServerFieldErrors((prev) => {
            const next = { ...prev };
            delete next.departure_local;
            return next;
          });
        }}
        onLoadWeightChange={handleLoadWeightChange}
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
      <TripSubmitButton isPending={isPending} isSlowRequest={isSlowRequest} />
    </Box>
  );
};
