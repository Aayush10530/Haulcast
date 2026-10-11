import { fireEvent, render, screen } from '@testing-library/react';
import { describe, expect, it, vi } from 'vitest';
import { goldenAnalysis } from '../../test/fixtures/goldenAnalysis';
import { ResultsPanel } from './ResultsPanel';

describe('ResultsPanel', () => {
  it('renders loading skeletons matching final card layout while pending', () => {
    render(
      <ResultsPanel
        analysis={null}
        isLoading={true}
        selectedRouteId={null}
        onSelectRoute={vi.fn()}
      />,
    );

    expect(screen.getByTestId('results-loading-skeletons')).toBeInTheDocument();
  });

  it('renders idle state with short text and example trip hint', () => {
    const handleTryExample = vi.fn();
    render(
      <ResultsPanel
        analysis={null}
        isLoading={false}
        selectedRouteId={null}
        onSelectRoute={vi.fn()}
        onTryExample={handleTryExample}
      />,
    );

    expect(screen.getByTestId('results-idle')).toBeInTheDocument();
    expect(
      screen.getByText(
        'Enter trip details and click Generate routes to see weather-aware options.',
      ),
    ).toBeInTheDocument();

    const exampleBtn = screen.getByTestId('results-idle-example-button');
    expect(exampleBtn).toHaveTextContent('Or try an example trip');
    fireEvent.click(exampleBtn);
    expect(handleTryExample).toHaveBeenCalled();
  });

  it('renders error alert with retry button', () => {
    const handleRetry = vi.fn();
    render(
      <ResultsPanel
        analysis={null}
        isLoading={false}
        error="Weather service temporarily unavailable."
        onRetry={handleRetry}
        selectedRouteId={null}
        onSelectRoute={vi.fn()}
      />,
    );

    expect(screen.getByTestId('results-error-alert')).toBeInTheDocument();
    expect(
      screen.getByText('Weather service temporarily unavailable.'),
    ).toBeInTheDocument();

    const retryBtn = screen.getByTestId('results-retry-button');
    fireEvent.click(retryBtn);
    expect(handleRetry).toHaveBeenCalled();
  });

  it('renders full results panel with recommendation, warnings, route cards, and selected checkpoints', () => {
    const handleSelectRoute = vi.fn();
    const { rerender } = render(
      <ResultsPanel
        analysis={goldenAnalysis}
        isLoading={false}
        selectedRouteId="route_b"
        onSelectRoute={handleSelectRoute}
      />,
    );

    // 1. Title
    expect(screen.getByTestId('results-title')).toHaveTextContent(
      'Route options (3)',
    );

    // 2. Recommendation Banner
    expect(screen.getByTestId('recommendation-banner')).toBeInTheDocument();
    expect(
      screen.getByText(
        'Route B has 0 Severe miles vs 34 on Route A (47 min slower).',
      ),
    ).toBeInTheDocument();
    expect(
      screen.getByText('Decided by: fewer Severe miles'),
    ).toBeInTheDocument();

    // 3. Warnings List
    expect(
      screen.getByText('High wind gusts expected along the I-70 corridor.'),
    ).toBeInTheDocument();

    // 4. Route Cards
    expect(screen.getByTestId('route-card-route_a')).toBeInTheDocument();
    expect(screen.getByTestId('route-card-route_b')).toBeInTheDocument();
    expect(screen.getByTestId('route-card-route_c')).toBeInTheDocument();

    // 5. Checkpoints for Route B (selected by default)
    expect(
      screen.getByText('Checkpoints (5) · Route B'),
    ).toBeInTheDocument();

    // 6. Click Route A to select it
    fireEvent.click(screen.getByTestId('route-card-route_a'));
    expect(handleSelectRoute).toHaveBeenCalledWith('route_a');

    // 7. Swapping selectedRouteId to route_a swaps the checkpoint list
    rerender(
      <ResultsPanel
        analysis={goldenAnalysis}
        isLoading={false}
        selectedRouteId="route_a"
        onSelectRoute={handleSelectRoute}
      />,
    );
    expect(
      screen.getByText('Checkpoints (1) · Route A'),
    ).toBeInTheDocument();
  });

  it('renders NO_SAFE_ROUTE warning with error severity', () => {
    const analysisWithNoSafeRoute = {
      ...goldenAnalysis,
      warnings: [
        {
          code: 'NO_SAFE_ROUTE',
          message: 'No safe route found for current conditions.',
        },
      ],
    };

    render(
      <ResultsPanel
        analysis={analysisWithNoSafeRoute}
        isLoading={false}
        selectedRouteId="route_b"
        onSelectRoute={vi.fn()}
      />,
    );

    const alert = screen.getByTestId('warning-alert-no_safe_route');
    expect(alert).toHaveClass('MuiAlert-colorError');
  });
});
