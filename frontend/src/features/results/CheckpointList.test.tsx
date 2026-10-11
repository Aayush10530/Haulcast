import { fireEvent, render, screen, waitFor } from '@testing-library/react';
import { describe, expect, it } from 'vitest';
import { goldenAnalysis } from '../../test/fixtures/goldenAnalysis';
import { CheckpointList } from './CheckpointList';

describe('CheckpointList', () => {
  const checkpoints = goldenAnalysis.routes[1].checkpoints; // Route B checkpoints

  it('renders checkpoints in default mile order with ETA and RiskChip', () => {
    render(<CheckpointList checkpoints={checkpoints} routeLabel="Route B" />);

    expect(screen.getByText('Checkpoints (5) · Route B')).toBeInTheDocument();

    // Verify first row is mile 0.0
    const row0 = screen.getByTestId('checkpoint-row-0');
    expect(row0).toBeInTheDocument();
    expect(screen.getByText('0.0 mi')).toBeInTheDocument();

    // Verify row with weather null shows "Forecast unavailable"
    expect(screen.getByText('Forecast unavailable')).toBeInTheDocument();

    // Verify RiskChip rendered
    expect(screen.getByText('High')).toBeInTheDocument();
    expect(screen.getByText('Moderate')).toBeInTheDocument();
  });

  it('sorts by Risk severity order when toggle is clicked', () => {
    render(<CheckpointList checkpoints={checkpoints} routeLabel="Route B" />);

    // Toggle sort by Risk
    const riskSortBtn = screen.getByTestId('sort-by-risk');
    fireEvent.click(riskSortBtn);

    // After sorting by risk, High (cp index 1) should be before Moderate (cp index 3) and Low (cp index 0, 4)
    const rows = screen.getAllByTestId(/^checkpoint-row-/);
    expect(rows[0]).toHaveAttribute('data-testid', 'checkpoint-row-1'); // High risk
    expect(rows[1]).toHaveAttribute('data-testid', 'checkpoint-row-3'); // Moderate risk
  });

  it('expands row on click to show weather metrics and reason in mono', async () => {
    render(<CheckpointList checkpoints={checkpoints} routeLabel="Route B" />);

    // Click row 1 (High wind checkpoint)
    const row1 = screen.getByTestId('checkpoint-row-1');
    fireEvent.click(row1);

    // Verify expanded details
    expect(screen.getByTestId('checkpoint-detail-1')).toBeInTheDocument();
    expect(screen.getByText(/Wind:/)).toBeInTheDocument();
    expect(screen.getByText('38 mph')).toBeInTheDocument();
    expect(screen.getByText(/Rain:/)).toBeInTheDocument();
    expect(screen.getByText('0.30 in/hr')).toBeInTheDocument();
    expect(
      screen.getByText('Crosswinds gusting to 38 mph for 42,000 lb load'),
    ).toBeInTheDocument();

    // Click again to collapse
    fireEvent.click(row1);
    await waitFor(() => {
      expect(screen.queryByTestId('checkpoint-detail-1')).not.toBeInTheDocument();
    });
  });
});
