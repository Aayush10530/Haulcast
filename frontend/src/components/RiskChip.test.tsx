import { render, screen } from '@testing-library/react';
import { describe, expect, it } from 'vitest';
import { RiskChip } from './RiskChip';

describe('RiskChip', () => {
  it('renders risk label with correct driver icons', () => {
    // 1. Wind driver
    const { rerender } = render(
      <RiskChip
        risk={{
          level: 'high',
          driver: 'wind',
          load_rule_applied: false,
          reason: 'Gusty crosswinds',
        }}
      />,
    );
    expect(screen.getByText('High')).toBeInTheDocument();
    expect(screen.getByTestId('driver-icon-air')).toBeInTheDocument();

    // 2. Rain driver
    rerender(
      <RiskChip
        risk={{
          level: 'moderate',
          driver: 'rain',
          load_rule_applied: false,
          reason: 'Light rain',
        }}
      />,
    );
    expect(screen.getByText('Moderate')).toBeInTheDocument();
    expect(screen.getByTestId('driver-icon-waterdrop')).toBeInTheDocument();

    // 3. Snow driver
    rerender(
      <RiskChip
        risk={{
          level: 'severe',
          driver: 'snow',
          load_rule_applied: false,
          reason: 'Heavy snowfall',
        }}
      />,
    );
    expect(screen.getByText('Severe')).toBeInTheDocument();
    expect(screen.getByTestId('driver-icon-acunit')).toBeInTheDocument();

    // 4. Load rule driver
    rerender(
      <RiskChip
        risk={{
          level: 'no_travel',
          driver: 'wind',
          load_rule_applied: true,
          reason: 'Exceeds rollover threshold for 42,000 lb',
        }}
      />,
    );
    expect(screen.getByText('No Travel')).toBeInTheDocument();
    expect(screen.getByTestId('driver-icon-scale')).toBeInTheDocument();
  });

  it('renders standalone level without driver safely', () => {
    render(<RiskChip level="low" label="Low" />);
    expect(screen.getByText('Low')).toBeInTheDocument();
    expect(screen.queryByTestId('driver-icon-air')).not.toBeInTheDocument();
  });

  it('renders neutral style with Forecast unavailable when risk is null without fallback to low', () => {
    render(<RiskChip risk={null} />);
    expect(screen.getByText('Forecast unavailable')).toBeInTheDocument();
    expect(screen.queryByText('Low')).not.toBeInTheDocument();
  });
});
