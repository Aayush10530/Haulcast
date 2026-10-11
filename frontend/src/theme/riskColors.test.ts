import { describe, expect, it } from 'vitest';
import { RiskLevelKey, riskColors } from './riskColors';
import { colorTokens } from './tokens';

/**
 * Calculates WCAG 2.1 relative luminance of an sRGB hex color.
 */
function getRelativeLuminance(hex: string): number {
  const cleanHex = hex.replace('#', '');
  const r = parseInt(cleanHex.slice(0, 2), 16) / 255;
  const g = parseInt(cleanHex.slice(2, 4), 16) / 255;
  const b = parseInt(cleanHex.slice(4, 6), 16) / 255;

  const toLinear = (c: number): number =>
    c <= 0.04045 ? c / 12.92 : Math.pow((c + 0.055) / 1.055, 2.4);

  return 0.2126 * toLinear(r) + 0.7152 * toLinear(g) + 0.0722 * toLinear(b);
}

/**
 * Calculates WCAG contrast ratio between two hex colors.
 */
function getContrastRatio(hex1: string, hex2: string): number {
  const lum1 = getRelativeLuminance(hex1);
  const lum2 = getRelativeLuminance(hex2);
  const lighter = Math.max(lum1, lum2);
  const darker = Math.min(lum1, lum2);
  return (lighter + 0.05) / (darker + 0.05);
}

describe('WCAG AA contrast ratio compliance (>= 4.5:1)', () => {
  describe('Risk scale text-on-fill contrast', () => {
    const levels = Object.keys(riskColors) as RiskLevelKey[];

    levels.forEach((level) => {
      it(`evaluates WCAG AA contrast for ${level} level (>= 4.5:1)`, () => {
        const { background, contrastText } = riskColors[level];
        const ratio = getContrastRatio(background, contrastText);
        console.log(
          `[Risk Contrast] ${level.padEnd(10)}: bg ${background} / text ${contrastText} = ${ratio.toFixed(2)}:1`,
        );
        expect(ratio).toBeGreaterThanOrEqual(4.5);
      });
    });
  });

  describe('Theme UI color token pairings contrast', () => {
    const uiPairs = [
      {
        name: 'text on surface',
        foreground: colorTokens.text,
        background: colorTokens.surface,
      },
      {
        name: 'text-muted on surface',
        foreground: colorTokens.textMuted,
        background: colorTokens.surface,
      },
      {
        name: 'brand on surface',
        foreground: colorTokens.brand,
        background: colorTokens.surface,
      },
      {
        name: 'on-brand on brand',
        foreground: colorTokens.onBrand,
        background: colorTokens.brand,
      },
    ];

    uiPairs.forEach(({ name, foreground, background }) => {
      it(`evaluates WCAG AA contrast for ${name} (>= 4.5:1)`, () => {
        const ratio = getContrastRatio(foreground, background);
        console.log(
          `[UI Contrast]   ${name.padEnd(22)}: fg ${foreground} / bg ${background} = ${ratio.toFixed(2)}:1`,
        );
        expect(ratio).toBeGreaterThanOrEqual(4.5);
      });
    });
  });
});
