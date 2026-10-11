import { describe, expect, it } from 'vitest';
import {
  EXAMPLE_DESTINATION,
  EXAMPLE_ORIGIN,
  formatDepartureSpelledOut,
  formatLoadWeightDisplay,
  formatLocalIsoDateTime,
  getNextFullHourLocal,
  getTomorrow8amLocal,
  validateTripForm,
} from './validateTripForm';

describe('validateTripForm', () => {
  it('passes with valid inputs', () => {
    const errors = validateTripForm({
      origin: EXAMPLE_ORIGIN,
      destination: EXAMPLE_DESTINATION,
      departure_local: '2026-10-12T08:00',
      load_weight_lb: 42000,
      interval: 'auto',
    });

    expect(Object.keys(errors)).toHaveLength(0);
  });

  it('fails when origin is missing', () => {
    const errors = validateTripForm({
      origin: null,
      destination: EXAMPLE_DESTINATION,
      departure_local: '2026-10-12T08:00',
      load_weight_lb: 42000,
      interval: 'auto',
    });

    expect(errors.origin).toBe('Please select an origin.');
  });

  it('fails when destination is missing', () => {
    const errors = validateTripForm({
      origin: EXAMPLE_ORIGIN,
      destination: null,
      departure_local: '2026-10-12T08:00',
      load_weight_lb: 42000,
      interval: 'auto',
    });

    expect(errors.destination).toBe('Please select a destination.');
  });

  it('fails when origin and destination are the same coordinates', () => {
    const errors = validateTripForm({
      origin: EXAMPLE_ORIGIN,
      destination: { ...EXAMPLE_ORIGIN, label: 'Dallas Depot' },
      departure_local: '2026-10-12T08:00',
      load_weight_lb: 42000,
      interval: 'auto',
    });

    expect(errors.destination).toBe(
      'Origin and destination must be different places.',
    );
  });

  it('fails when departure is missing or empty', () => {
    const errors = validateTripForm({
      origin: EXAMPLE_ORIGIN,
      destination: EXAMPLE_DESTINATION,
      departure_local: '',
      load_weight_lb: 42000,
      interval: 'auto',
    });

    expect(errors.departure_local).toBe(
      'Please select a departure date and time.',
    );
  });

  it('fails when departure is an invalid date string', () => {
    const errors = validateTripForm({
      origin: EXAMPLE_ORIGIN,
      destination: EXAMPLE_DESTINATION,
      departure_local: 'not-a-valid-date',
      load_weight_lb: 42000,
      interval: 'auto',
    });

    expect(errors.departure_local).toBe(
      'Please enter a valid departure date and time.',
    );
  });

  it('fails when load weight is empty', () => {
    const errors = validateTripForm({
      origin: EXAMPLE_ORIGIN,
      destination: EXAMPLE_DESTINATION,
      departure_local: '2026-10-12T08:00',
      load_weight_lb: '',
      interval: 'auto',
    });

    expect(errors.load_weight_lb).toBe('Please enter a load weight.');
  });

  it('fails when load weight is non-numeric', () => {
    const errors = validateTripForm({
      origin: EXAMPLE_ORIGIN,
      destination: EXAMPLE_DESTINATION,
      departure_local: '2026-10-12T08:00',
      load_weight_lb: 'heavy',
      interval: 'auto',
    });

    expect(errors.load_weight_lb).toBe('Load weight must be a valid number.');
  });

  it('fails when load weight is negative', () => {
    const errors = validateTripForm({
      origin: EXAMPLE_ORIGIN,
      destination: EXAMPLE_DESTINATION,
      departure_local: '2026-10-12T08:00',
      load_weight_lb: -50,
      interval: 'auto',
    });

    expect(errors.load_weight_lb).toBe(
      'Load weight must be between 0 and 120,000 lb.',
    );
  });

  it('fails when load weight exceeds 120,000 lb', () => {
    const errors = validateTripForm({
      origin: EXAMPLE_ORIGIN,
      destination: EXAMPLE_DESTINATION,
      departure_local: '2026-10-12T08:00',
      load_weight_lb: 125000,
      interval: 'auto',
    });

    expect(errors.load_weight_lb).toBe(
      'Load weight must be between 0 and 120,000 lb.',
    );
  });

  it('allows zero load weight (empty bobtail)', () => {
    const errors = validateTripForm({
      origin: EXAMPLE_ORIGIN,
      destination: EXAMPLE_DESTINATION,
      departure_local: '2026-10-12T08:00',
      load_weight_lb: 0,
      interval: 25,
    });

    expect(Object.keys(errors)).toHaveLength(0);
  });

  it('date helpers produce valid ISO local strings', () => {
    const nextHour = getNextFullHourLocal();
    expect(nextHour).toMatch(/^\d{4}-\d{2}-\d{2}T\d{2}:00$/);

    const tomorrow8 = getTomorrow8amLocal();
    expect(tomorrow8).toMatch(/^\d{4}-\d{2}-\d{2}T08:00$/);

    const testDate = new Date(2026, 9, 12, 8, 30);
    expect(formatLocalIsoDateTime(testDate)).toBe('2026-10-12T08:30');
  });

  it('formatDepartureSpelledOut formats date and time without timezone conversion', () => {
    expect(formatDepartureSpelledOut('2026-10-11T20:00')).toBe(
      'Sun, Oct 11, 8:00 PM · local time at origin',
    );
    expect(formatDepartureSpelledOut('2026-10-12T08:00')).toBe(
      'Mon, Oct 12, 8:00 AM · local time at origin',
    );
    expect(formatDepartureSpelledOut('2026-01-01T00:00')).toBe(
      'Thu, Jan 1, 12:00 AM · local time at origin',
    );
    expect(formatDepartureSpelledOut('2026-07-04T12:30')).toBe(
      'Sat, Jul 4, 12:30 PM · local time at origin',
    );
    expect(formatDepartureSpelledOut('')).toBeNull();
    expect(formatDepartureSpelledOut('invalid')).toBeNull();
  });

  it('formatLoadWeightDisplay formats thousands separators and handles raw values', () => {
    expect(formatLoadWeightDisplay(40000)).toBe('40,000');
    expect(formatLoadWeightDisplay(42000)).toBe('42,000');
    expect(formatLoadWeightDisplay(120000)).toBe('120,000');
    expect(formatLoadWeightDisplay(0)).toBe('0');
    expect(formatLoadWeightDisplay('42000')).toBe('42,000');
    expect(formatLoadWeightDisplay('42,000')).toBe('42,000');
    expect(formatLoadWeightDisplay('')).toBe('');
    expect(formatLoadWeightDisplay('abc')).toBe('');
  });

  it('allows load weight provided with commas', () => {
    const errors = validateTripForm({
      origin: EXAMPLE_ORIGIN,
      destination: EXAMPLE_DESTINATION,
      departure_local: '2026-10-12T08:00',
      load_weight_lb: '42,000',
      interval: 'auto',
    });

    expect(Object.keys(errors)).toHaveLength(0);
  });
});
