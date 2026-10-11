import { describe, expect, it, vi } from 'vitest';
import {
  formatDelta,
  formatDuration,
  formatLocalTime,
  formatMiles,
} from './format';

describe('format utilities', () => {
  describe('formatDuration', () => {
    it('formats hours and minutes accurately', () => {
      expect(formatDuration(46560)).toBe('12h 56m');
      expect(formatDuration(7200)).toBe('2h 0m');
      expect(formatDuration(2820)).toBe('47m');
      expect(formatDuration(0)).toBe('0m');
      expect(formatDuration(-10)).toBe('0m');
    });
  });

  describe('formatMiles', () => {
    it('formats miles with 1 decimal under 100 and integer with thousands separator above', () => {
      expect(formatMiles(51.2)).toBe('51.2 mi');
      expect(formatMiles(0)).toBe('0.0 mi');
      expect(formatMiles(99.9)).toBe('99.9 mi');
      expect(formatMiles(100)).toBe('100 mi');
      expect(formatMiles(799)).toBe('799 mi');
      expect(formatMiles(1240.4)).toBe('1,240 mi');
      expect(formatMiles(125000)).toBe('125,000 mi');
    });
  });

  describe('formatDelta', () => {
    it('formats delta minutes and hours', () => {
      expect(formatDelta(2820)).toBe('+47 min');
      expect(formatDelta(3900)).toBe('+1 h 05 min');
      expect(formatDelta(7200)).toBe('+2 h 00 min');
      expect(formatDelta(0)).toBe('');
      expect(formatDelta(-100)).toBe('');
    });
  });

  describe('formatLocalTime', () => {
    it('extracts wall-clock time and offset without timezone conversion', () => {
      expect(formatLocalTime('2026-10-13T08:15:00-06:00')).toBe(
        'Tue Oct 13, 08:15 CST/CDT',
      );
      expect(formatLocalTime('2026-10-12T13:00:00Z')).toBe(
        'Mon Oct 12, 13:00 UTC',
      );
      expect(formatLocalTime('2026-10-13T08:15:00-03:00')).toBe(
        'Tue Oct 13, 08:15 UTC-3',
      );
    });

    it('resolves specific timezone abbreviation when tzName is provided', () => {
      expect(
        formatLocalTime('2026-10-13T08:15:00-05:00', 'America/Chicago'),
      ).toBe('Tue Oct 13, 08:15 CDT');
    });

    it('retains exact wall-clock string across process timezone changes (Asia/Kolkata)', () => {
      try {
        vi.stubEnv('TZ', 'Asia/Kolkata');
        const formatted = formatLocalTime('2026-10-13T08:15:00-06:00');
        expect(formatted).toBe('Tue Oct 13, 08:15 CST/CDT');

        // Verify with another zone
        vi.stubEnv('TZ', 'Europe/London');
        const formattedLondon = formatLocalTime('2026-10-13T08:15:00-06:00');
        expect(formattedLondon).toBe('Tue Oct 13, 08:15 CST/CDT');
      } finally {
        vi.unstubAllEnvs();
      }
    });
  });
});
