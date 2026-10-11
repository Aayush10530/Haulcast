/**
 * Pure validation functions and date helpers for TripForm.
 */

import { IntervalOption, PlaceDTO } from '../../api/types';

export interface TripFormValues {
  origin: PlaceDTO | null;
  destination: PlaceDTO | null;
  departure_local: string;
  load_weight_lb: number | string;
  interval: IntervalOption;
}

export interface TripFormErrors {
  origin?: string;
  destination?: string;
  departure_local?: string;
  load_weight_lb?: string;
  interval?: string;
}

export function formatLocalIsoDateTime(date: Date): string {
  const year = date.getFullYear();
  const month = String(date.getMonth() + 1).padStart(2, '0');
  const day = String(date.getDate()).padStart(2, '0');
  const hours = String(date.getHours()).padStart(2, '0');
  const minutes = String(date.getMinutes()).padStart(2, '0');
  return `${year}-${month}-${day}T${hours}:${minutes}`;
}

export function getNextFullHourLocal(): string {
  const next = new Date();
  next.setMinutes(0, 0, 0);
  next.setHours(next.getHours() + 1);
  return formatLocalIsoDateTime(next);
}

export function getTomorrow8amLocal(): string {
  const tomorrow = new Date();
  tomorrow.setDate(tomorrow.getDate() + 1);
  tomorrow.setHours(8, 0, 0, 0);
  return formatLocalIsoDateTime(tomorrow);
}

export const EXAMPLE_ORIGIN: PlaceDTO = {
  label: 'Dallas, TX',
  lat: 32.7767,
  lon: -96.797,
};

export const EXAMPLE_DESTINATION: PlaceDTO = {
  label: 'Denver, CO',
  lat: 39.7392,
  lon: -104.9903,
};

/**
 * Pure validation function for TripForm.
 * Checks that both places are selected and distinct, departure is valid,
 * and load weight is between 0 and 120,000 lb.
 */
export function validateTripForm(values: TripFormValues): TripFormErrors {
  const errors: TripFormErrors = {};

  if (!values.origin) {
    errors.origin = 'Please select an origin.';
  }

  if (!values.destination) {
    errors.destination = 'Please select a destination.';
  } else if (
    values.origin &&
    Math.abs(values.origin.lat - values.destination.lat) < 0.0001 &&
    Math.abs(values.origin.lon - values.destination.lon) < 0.0001
  ) {
    errors.destination = 'Origin and destination must be different places.';
  }

  const depStr = values.departure_local?.trim();
  if (!depStr) {
    errors.departure_local = 'Please select a departure date and time.';
  } else {
    const parsed = new Date(depStr);
    if (isNaN(parsed.getTime())) {
      errors.departure_local = 'Please enter a valid departure date and time.';
    }
  }

  const weightStr = String(values.load_weight_lb).trim();
  if (weightStr === '') {
    errors.load_weight_lb = 'Please enter a load weight.';
  } else {
    const weightNum = Number(weightStr);
    if (isNaN(weightNum)) {
      errors.load_weight_lb = 'Load weight must be a valid number.';
    } else if (weightNum < 0 || weightNum > 120000) {
      errors.load_weight_lb = 'Load weight must be between 0 and 120,000 lb.';
    }
  }

  if (
    values.interval !== 'auto' &&
    values.interval !== 10 &&
    values.interval !== 25 &&
    values.interval !== 50
  ) {
    errors.interval = 'Please select a valid checkpoint interval.';
  }

  return errors;
}
