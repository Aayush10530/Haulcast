import { describe, expect, it } from 'vitest';
import { LEVEL_TO_INTENSITY, toHeatPoints } from './heatUtils';

describe('heatUtils', () => {
  it('maps risk levels 0 through 4 to expected intensities', () => {
    expect(LEVEL_TO_INTENSITY[0]).toBe(0.05);
    expect(LEVEL_TO_INTENSITY[1]).toBe(0.30);
    expect(LEVEL_TO_INTENSITY[2]).toBe(0.60);
    expect(LEVEL_TO_INTENSITY[3]).toBe(0.85);
    expect(LEVEL_TO_INTENSITY[4]).toBe(1.00);
  });

  it('converts cells and level array into [lat, lon, intensity] tuples', () => {
    const cells = [
      { lat: 32.7, lon: -96.8 },
      { lat: 33.1, lon: -97.2 },
      { lat: 34.5, lon: -98.0 },
      { lat: 35.0, lon: -99.0 },
      { lat: 36.0, lon: -100.0 },
    ];
    const levels = [0, 1, 2, 3, 4];

    const points = toHeatPoints(cells, levels);
    expect(points).toEqual([
      [32.7, -96.8, 0.05],
      [33.1, -97.2, 0.30],
      [34.5, -98.0, 0.60],
      [35.0, -99.0, 0.85],
      [36.0, -100.0, 1.00],
    ]);
  });

  it('skips null and undefined level entries', () => {
    const cells = [
      { lat: 32.7, lon: -96.8 },
      { lat: 33.1, lon: -97.2 },
      { lat: 34.5, lon: -98.0 },
    ];
    const levels = [0, null, undefined];

    const points = toHeatPoints(cells, levels);
    expect(points).toHaveLength(1);
    expect(points[0]).toEqual([32.7, -96.8, 0.05]);
  });

  it('handles empty or missing arrays safely', () => {
    expect(toHeatPoints([], [])).toEqual([]);
    expect(toHeatPoints([{ lat: 30, lon: -90 }], [])).toEqual([]);
  });
});
