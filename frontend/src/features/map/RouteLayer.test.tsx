import { describe, expect, it } from 'vitest';
import { getRouteLabelVertexIndex } from './RouteLayer';

describe('RouteLayer - getRouteLabelVertexIndex', () => {
  it('places route label pills at 30%, 50%, and 70% of vertices for order indices 0, 1, 2', () => {
    const n = 100;

    // Route A (index 0): floor(100 * (0.30 + 0.20 * 0)) = 30
    expect(getRouteLabelVertexIndex(n, 0)).toBe(30);

    // Route B (index 1): floor(100 * (0.30 + 0.20 * 1)) = 50
    expect(getRouteLabelVertexIndex(n, 1)).toBe(50);

    // Route C (index 2): floor(100 * (0.30 + 0.20 * 2)) = 70
    expect(getRouteLabelVertexIndex(n, 2)).toBe(70);
  });

  it('ensures labels along shared stretches have separated vertex positions to prevent collisions', () => {
    const n = 45;
    const posA = getRouteLabelVertexIndex(n, 0); // floor(45 * 0.30) = 13
    const posB = getRouteLabelVertexIndex(n, 1); // floor(45 * 0.50) = 22
    const posC = getRouteLabelVertexIndex(n, 2); // floor(45 * 0.70) = 31

    expect(posA).toBe(13);
    expect(posB).toBe(22);
    expect(posC).toBe(31);
    expect(posA).not.toBe(posB);
    expect(posB).not.toBe(posC);
  });

  it('handles small geometries and edge cases gracefully', () => {
    expect(getRouteLabelVertexIndex(0, 0)).toBe(0);
    expect(getRouteLabelVertexIndex(1, 0)).toBe(0);
    expect(getRouteLabelVertexIndex(1, 1)).toBe(0);
    expect(getRouteLabelVertexIndex(1, 2)).toBe(0);

    const n = 10;
    expect(getRouteLabelVertexIndex(n, 0)).toBe(3);
    expect(getRouteLabelVertexIndex(n, 1)).toBe(5);
    expect(getRouteLabelVertexIndex(n, 2)).toBe(7);
  });
});
