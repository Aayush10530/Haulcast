import { fireEvent, render, screen } from '@testing-library/react';
import { describe, expect, it, vi } from 'vitest';
import { goldenAnalysis } from '../../test/fixtures/goldenAnalysis';
import { RouteCard } from './RouteCard';

describe('RouteCard', () => {
  const routeA = goldenAnalysis.routes[0]; // Route A (Fastest)
  const routeB = goldenAnalysis.routes[1]; // Route B (Recommended)

  it('renders Route B correctly with Recommended tag, avg-risk ring, delta, and timeline', () => {
    const handleSelect = vi.fn();
    render(
      <RouteCard
        route={routeB}
        isSelected={true}
        isRecommended={true}
        departureLocal={goldenAnalysis.request.departure_local}
        originTimezone={goldenAnalysis.request.origin_timezone}
        onSelect={handleSelect}
      />,
    );

    // 1. 28px square mono letter badge
    const badge = screen.getByTestId('route-badge-b');
    expect(badge).toBeInTheDocument();
    expect(badge).toHaveTextContent('B');

    // 2. Tags
    expect(screen.getByTestId('tag-recommended')).toHaveTextContent('Recommended');
    expect(screen.queryByTestId('tag-fastest')).not.toBeInTheDocument();

    // 3. Avg-risk ring
    expect(screen.getByTestId('avg-risk-ring')).toBeInTheDocument();
    expect(screen.getByTestId('avg-risk-score')).toHaveTextContent('0.62');
    expect(screen.getByText('Avg risk')).toBeInTheDocument();

    // 4. Duration and miles mono line
    expect(screen.getByTestId('route-duration-miles')).toHaveTextContent('12h 15m · 801 mi');
    expect(screen.getByText('via I-35 N, I-70 W')).toBeInTheDocument();

    // 5. Departure and arrival local times
    expect(screen.getByText(/Depart: Mon Oct 12, 08:00/)).toBeInTheDocument();
    expect(screen.getByText(/Arrive: Mon Oct 12, 19:15/)).toBeInTheDocument();

    // 6. Delta line
    expect(screen.getByTestId('route-delta')).toHaveTextContent('+47 min vs fastest');

    // 7. RiskStrip inside card
    expect(screen.getByRole('img', { name: /Risk distribution:/ })).toBeInTheDocument();

    // 8. Click card
    fireEvent.click(screen.getByTestId('route-card-route_b'));
    expect(handleSelect).toHaveBeenCalledWith('route_b');
  });

  it('renders Route A correctly with Fastest tag and zero delta', () => {
    render(
      <RouteCard
        route={routeA}
        isSelected={false}
        isRecommended={false}
        departureLocal={goldenAnalysis.request.departure_local}
        originTimezone={goldenAnalysis.request.origin_timezone}
      />,
    );

    const badge = screen.getByTestId('route-badge-a');
    expect(badge).toHaveTextContent('A');

    expect(screen.getByTestId('tag-fastest')).toHaveTextContent('Fastest');
    expect(screen.queryByTestId('tag-recommended')).not.toBeInTheDocument();

    expect(screen.getByTestId('avg-risk-score')).toHaveTextContent('0.95');
    expect(screen.getByTestId('route-duration-miles')).toHaveTextContent('11h 28m · 785 mi');
    expect(screen.queryByTestId('route-delta')).not.toBeInTheDocument();
  });
});
