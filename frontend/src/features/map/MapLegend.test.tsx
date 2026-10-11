import { render, screen } from '@testing-library/react';
import { describe, expect, it } from 'vitest';
import { MapLegend } from './MapLegend';

describe('MapLegend', () => {
  it('renders all five risk levels from riskColors with labels', () => {
    render(<MapLegend />);

    expect(screen.getByTestId('map-legend')).toBeInTheDocument();
    expect(screen.getByText('Weather Risk')).toBeInTheDocument();

    expect(screen.getByTestId('legend-item-low')).toHaveTextContent('Low');
    expect(screen.getByTestId('legend-item-moderate')).toHaveTextContent('Moderate');
    expect(screen.getByTestId('legend-item-high')).toHaveTextContent('High');
    expect(screen.getByTestId('legend-item-severe')).toHaveTextContent('Severe');
    expect(screen.getByTestId('legend-item-no_travel')).toHaveTextContent('No Travel');
  });
});
