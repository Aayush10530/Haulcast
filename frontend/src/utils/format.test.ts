import { describe, expect, it, vi } from 'vitest';
import {
  formatCheckpointMiles,
  formatDelta,
  formatDuration,
  formatLocalTime,
  formatMiles,
  formatRiskScore,
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

    it('rounds to the nearest minute with Math.floor(x + 0.5) and displays durations 46,500 s and 49,260 s as 12h 55m and 13h 41m with delta text 46 min', () => {
      const dFastest = 46500;
      const dSlower = 49260;
      expect(formatDuration(dFastest)).toBe('12h 55m');
      expect(formatDuration(dSlower)).toBe('13h 41m');

      // delta_vs_fastest_seconds computed from minute-rounded durations:
      // (floor(49260/60 + 0.5) - floor(46500/60 + 0.5)) * 60 = (821 - 775) * 60 = 2760s
      const deltaSeconds =
        (Math.floor(dSlower / 60 + 0.5) - Math.floor(dFastest / 60 + 0.5)) * 60;
      expect(deltaSeconds).toBe(2760);
      expect(formatDelta(deltaSeconds)).toBe('+46 min');
      expect(formatDelta(deltaSeconds)).toContain('46 min');
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

  describe('formatCheckpointMiles', () => {
    it('formats integer when whole and one decimal otherwise', () => {
      expect(formatCheckpointMiles(50)).toBe('50 mi');
      expect(formatCheckpointMiles(37.5)).toBe('37.5 mi');
      expect(formatCheckpointMiles(0)).toBe('0 mi');
      expect(formatCheckpointMiles(120.5)).toBe('120.5 mi');
      expect(formatCheckpointMiles(350.0)).toBe('350 mi');
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
        'Tue Oct 13, 08:15 UTC-6',
      );
      expect(formatLocalTime('2026-10-12T13:00:00Z')).toBe(
        'Mon Oct 12, 13:00 UTC',
      );
      expect(formatLocalTime('2026-10-13T08:15:00-03:00')).toBe(
        'Tue Oct 13, 08:15 UTC-3',
      );
    });

    it('resolves specific timezone abbreviation when tzName is provided (arrival at Denver reads MDT)', () => {
      expect(
        formatLocalTime('2026-10-12T18:28:00-06:00', 'America/Denver'),
      ).toBe('Mon Oct 12, 18:28 MDT');
      expect(
        formatLocalTime('2026-10-13T08:15:00-05:00', 'America/Chicago'),
      ).toBe('Tue Oct 13, 08:15 CDT');
    });

    it('parses ISO 8601 strings with fractional seconds (microseconds) and UTC offsets', () => {
      expect(
        formatLocalTime(
          '2026-10-12T08:15:00.123456-05:00',
          'America/Chicago',
        ),
      ).toBe('Mon Oct 12, 08:15 CDT');
      expect(formatLocalTime('2026-10-12T13:00:00.999999Z')).toBe(
        'Mon Oct 12, 13:00 UTC',
      );
      expect(formatLocalTime('2026-10-12T18:28:00.500000-06:00', 'America/Denver')).toBe(
        'Mon Oct 12, 18:28 MDT',
      );
    });

    it('never renders a raw ISO string and shows "Time unavailable" on parse failure', () => {
      expect(formatLocalTime('')).toBe('Time unavailable');
      expect(formatLocalTime('invalid-date')).toBe('Time unavailable');
      expect(formatLocalTime('2026-13-45T99:99')).toBe('Time unavailable');
      expect(formatLocalTime('2026-02-30T08:00:00Z')).toBe('Time unavailable');
    });

    it('retains exact wall-clock string across process timezone changes (Asia/Kolkata)', () => {
      try {
        vi.stubEnv('TZ', 'Asia/Kolkata');
        const formattedDenver = formatLocalTime(
          '2026-10-12T18:28:00-06:00',
          'America/Denver',
        );
        expect(formattedDenver).toBe('Mon Oct 12, 18:28 MDT');

        const formattedChicago = formatLocalTime(
          '2026-10-12T08:15:00.123456-05:00',
          'America/Chicago',
        );
        expect(formattedChicago).toBe('Mon Oct 12, 08:15 CDT');

        // Verify with another zone
        vi.stubEnv('TZ', 'Europe/London');
        const formattedLondon = formatLocalTime(
          '2026-10-12T18:28:00-06:00',
          'America/Denver',
        );
        expect(formattedLondon).toBe('Mon Oct 12, 18:28 MDT');
      } finally {
        vi.unstubAllEnvs();
      }
    });
  });

  describe('formatRiskScore', () => {
    it('scales avgRisk (0-4) to integer 0-100 percentage score', () => {
      expect(formatRiskScore(0.0)).toBe(0);
      expect(formatRiskScore(0.62)).toBe(16);
      expect(formatRiskScore(0.95)).toBe(24);
      expect(formatRiskScore(1.0)).toBe(25);
      expect(formatRiskScore(2.0)).toBe(50);
      expect(formatRiskScore(3.0)).toBe(75);
      expect(formatRiskScore(4.0)).toBe(100);
    });

    it('returns null when avgRisk is null, undefined, or NaN', () => {
      expect(formatRiskScore(null)).toBeNull();
      expect(formatRiskScore(undefined)).toBeNull();
      expect(formatRiskScore(NaN)).toBeNull();
    });

    it('clamps values to 0-100 bounds', () => {
      expect(formatRiskScore(-1.0)).toBe(0);
      expect(formatRiskScore(5.0)).toBe(100);
    });
  });
});

