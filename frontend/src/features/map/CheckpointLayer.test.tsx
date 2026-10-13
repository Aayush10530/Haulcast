import { describe, expect, it } from 'vitest';
import { getCheckpointMarkerColor } from './CheckpointLayer';
import { colorTokens } from '../../theme/tokens';
import { riskColors } from '../../theme/riskColors';
import { CheckpointRiskDTO } from '../../api/types';

describe('getCheckpointMarkerColor', () => {
  it('returns neutral muted style (colorTokens.textMuted) when risk is null or undefined', () => {
    expect(getCheckpointMarkerColor(null)).toBe(colorTokens.textMuted);
    expect(getCheckpointMarkerColor(undefined)).toBe(colorTokens.textMuted);
  });

  it('returns neutral muted style when risk level is unknown', () => {
    const invalidRisk = {
      level: 'unknown' as unknown,
      driver: 'wind',
      load_rule_applied: false,
      reason: 'Unknown',
    } as CheckpointRiskDTO;
    expect(getCheckpointMarkerColor(invalidRisk)).toBe(colorTokens.textMuted);
  });

  it('returns correct risk color when valid risk is present', () => {
    const severeRisk: CheckpointRiskDTO = {
      level: 'severe',
      driver: 'wind',
      load_rule_applied: false,
      reason: 'Severe winds',
    };
    expect(getCheckpointMarkerColor(severeRisk)).toBe(riskColors.severe.background);

    const moderateRisk: CheckpointRiskDTO = {
      level: 'moderate',
      driver: 'rain',
      load_rule_applied: false,
      reason: 'Moderate rain',
    };
    expect(getCheckpointMarkerColor(moderateRisk)).toBe(riskColors.moderate.background);
  });
});
