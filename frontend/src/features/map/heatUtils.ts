/**
 * Heatmap point conversion utilities per docs/ARCHITECTURE.md §10.
 * Uniform grid points mapped to [lat, lon, intensity].
 */

export type HeatPoint = [number, number, number]; // [lat, lon, intensity]

export const LEVEL_TO_INTENSITY: Record<number, number> = {
  0: 0.05,
  1: 0.30,
  2: 0.60,
  3: 0.85,
  4: 1.00,
};

export function toHeatPoints(
  cells: { lat: number; lon: number }[],
  levels: (number | null | undefined)[],
): HeatPoint[] {
  if (!cells || !levels || cells.length === 0) {
    return [];
  }
  const points: HeatPoint[] = [];
  const len = Math.min(cells.length, levels.length);
  for (let i = 0; i < len; i++) {
    const lvl = levels[i];
    if (lvl !== null && lvl !== undefined && lvl >= 0) {
      const intensity = LEVEL_TO_INTENSITY[lvl] ?? 0.05;
      points.push([cells[i].lat, cells[i].lon, intensity]);
    }
  }
  return points;
}
