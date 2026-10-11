import { describe, expect, it } from 'vitest';
import {
  EXAMPLE_DESTINATION,
  EXAMPLE_ORIGIN,
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
});
