import { render, screen } from '@testing-library/react';
import { describe, expect, it } from 'vitest';
import { RiskStrip } from './RiskStrip';

describe('RiskStrip', () => {
  it('renders proportional segments and full aria-label for normal miles', () => {
    render(
      <RiskStrip
        milesByLevel={{
          low: 600,
          moderate: 150,
          high: 51.2,
          severe: 34,
          no_travel: 0,
        }}
      />,
    );

    const bar = screen.getByRole('img');
    expect(bar).toBeInTheDocument();
    expect(bar).toHaveAttribute(
      'aria-label',
      expect.stringContaining('Low 600 mi'),
    );
    expect(bar).toHaveAttribute(
      'aria-label',
      expect.stringContaining('Severe 34.0 mi'),
    );

    const lowSeg = screen.getByTestId('risk-segment-low');
    const severeSeg = screen.getByTestId('risk-segment-severe');
    expect(lowSeg).toBeInTheDocument();
    expect(severeSeg).toBeInTheDocument();

    // Verify caption lists nonzero Severe and High miles
    expect(screen.getByText('Severe 34.0 mi · High 51.2 mi')).toBeInTheDocument();
  });

  it('handles all-zero miles safely', () => {
    render(
      <RiskStrip
        milesByLevel={{
          low: 0,
          moderate: 0,
          high: 0,
          severe: 0,
          no_travel: 0,
        }}
      />,
    );

    const bar = screen.getByRole('img');
    expect(bar).toHaveAttribute('aria-label', 'Risk distribution: no risk data');
    expect(screen.getByText('No risk data')).toBeInTheDocument();
  });

  it('handles all-unavailable forecast safely', () => {
    render(
      <RiskStrip
        milesByLevel={{
          low: 0,
          moderate: 0,
          high: 0,
          severe: 0,
          no_travel: 0,
        }}
        unavailableMiles={450}
      />,
    );

    const bar = screen.getByRole('img');
    expect(bar).toHaveAttribute(
      'aria-label',
      'Risk distribution: forecast unavailable',
    );
    expect(screen.getByText('Forecast unavailable')).toBeInTheDocument();
  });

  it('displays "0 Severe or High miles" when only low or moderate exist', () => {
    render(
      <RiskStrip
        milesByLevel={{
          low: 500,
          moderate: 100,
          high: 0,
          severe: 0,
          no_travel: 0,
        }}
      />,
    );

    expect(screen.getByText('0 Severe or High miles')).toBeInTheDocument();
  });
});
