import { render, screen } from '@testing-library/react';
import { describe, expect, it } from 'vitest';
import { RouteDTO } from '../../api/types';
import { goldenAnalysis } from '../../test/fixtures/goldenAnalysis';
import { RouteComparisonCard } from './RouteComparisonCard';

function makeMockRoute(overrides: Partial<RouteDTO>): RouteDTO {
  return {
    ...goldenAnalysis.routes[0],
    ...overrides,
    summary: {
      ...goldenAnalysis.routes[0].summary,
      ...overrides.summary,
      miles_by_level: {
        ...goldenAnalysis.routes[0].summary?.miles_by_level,
        ...overrides.summary?.miles_by_level,
      },
    },
  };
}

describe('RouteComparisonCard Audit', () => {
  it('renders risk miles chart, travel time chart, and route metrics table', () => {
    render(<RouteComparisonCard routes={goldenAnalysis.routes} />);

    expect(screen.getByTestId('route-comparison-card')).toBeInTheDocument();
    expect(screen.getByText('Route Comparison')).toBeInTheDocument();
    expect(screen.getByTestId('risk-miles-chart-area')).toBeInTheDocument();
    expect(screen.getByTestId('travel-time-chart-area')).toBeInTheDocument();
    expect(screen.getByTestId('route-metrics-table')).toBeInTheDocument();
  });

  it('produces zero-height/hidden bars for zero risk miles and visible bars for positive miles', () => {
    // Mock routes where Route A has 0 severe miles and Route B has 25 severe miles
    const mockRoutes: RouteDTO[] = [
      makeMockRoute({
        id: 'route_a',
        label: 'Route A',
        tags: ['recommended'],
        rank: 1,
        distance_miles: 500,
        duration_seconds: 28800, // 8h
        summary: {
          miles_by_level: {
            low: 500,
            moderate: 0,
            high: 0,
            severe: 0, // ZERO severe miles
            no_travel: 0,
          },
          avg_risk_score: 0.1,
          max_level: 'low',
          has_no_travel: false,
          delta_vs_fastest_seconds: 0,
        },
      }),
      makeMockRoute({
        id: 'route_b',
        label: 'Route B',
        tags: [],
        rank: 2,
        distance_miles: 520,
        duration_seconds: 30000,
        summary: {
          miles_by_level: {
            low: 400,
            moderate: 50,
            high: 45,
            severe: 25, // POSITIVE severe miles
            no_travel: 0,
          },
          avg_risk_score: 1.5,
          max_level: 'severe',
          has_no_travel: false,
          delta_vs_fastest_seconds: 1200,
        },
      }),
    ];

    render(<RouteComparisonCard routes={mockRoutes} />);

    // Route A severe bar must have height 0 and be hidden
    const barSevereA = screen.getByTestId('bar-severe-route_a');
    expect(barSevereA).toHaveAttribute('data-height', '0');
    expect(barSevereA).toHaveStyle({ display: 'none' });

    // Route B severe bar must have positive height and be visible
    const barSevereB = screen.getByTestId('bar-severe-route_b');
    const heightB = parseFloat(barSevereB.getAttribute('data-height') || '0');
    expect(heightB).toBeGreaterThan(0);
    expect(barSevereB).toHaveStyle({ display: 'block' });
  });

  it('keeps risk miles (mi) and travel time (hrs) in separate charts with distinct units', () => {
    render(<RouteComparisonCard routes={goldenAnalysis.routes} />);

    // Risk chart has miles axis
    expect(screen.getByText('Risk Exposure by Level (miles)')).toBeInTheDocument();

    // Travel time chart has hours axis/header
    expect(screen.getByText('Estimated Travel Time (hours)')).toBeInTheDocument();

    // Verify time bar labels render formatted durations
    const timeLabelA = screen.getByTestId('label-time-route_a');
    const timeLabelB = screen.getByTestId('label-time-route_b');
    expect(timeLabelA).toHaveTextContent('11h 28m');
    expect(timeLabelB).toHaveTextContent('12h 15m');
  });

  it('updates all charts and metrics immediately when trip routes change without stale data', () => {
    const trip1Routes: RouteDTO[] = [
      makeMockRoute({
        id: 'route_1',
        label: 'Route 1',
        rank: 1,
        distance_miles: 100,
        duration_seconds: 3600,
        summary: {
          miles_by_level: { low: 100, moderate: 0, high: 0, severe: 0, no_travel: 0 },
          avg_risk_score: 0.0,
          max_level: 'low',
          has_no_travel: false,
          delta_vs_fastest_seconds: 0,
        },
      }),
    ];

    const trip2Routes: RouteDTO[] = [
      makeMockRoute({
        id: 'route_2',
        label: 'Route 2',
        rank: 1,
        distance_miles: 950,
        duration_seconds: 54000, // 15h
        summary: {
          miles_by_level: { low: 800, moderate: 50, high: 70, severe: 30, no_travel: 0 },
          avg_risk_score: 0.8,
          max_level: 'severe',
          has_no_travel: false,
          delta_vs_fastest_seconds: 0,
        },
      }),
    ];

    const { rerender } = render(<RouteComparisonCard routes={trip1Routes} />);

    // Trip 1 assertions
    expect(screen.getAllByText(/Route 1/i).length).toBeGreaterThan(0);
    expect(screen.getByTestId('label-time-route_1')).toHaveTextContent('1h 0m');
    expect(screen.getByTestId('metric-severe-route_1')).toHaveTextContent('0 mi');

    // Rerender with Trip 2 (different route)
    rerender(<RouteComparisonCard routes={trip2Routes} />);

    // Trip 1 data must be gone; Trip 2 data must be rendered
    expect(screen.queryByText(/Route 1/i)).not.toBeInTheDocument();
    expect(screen.getAllByText(/Route 2/i).length).toBeGreaterThan(0);
    expect(screen.getByTestId('label-time-route_2')).toHaveTextContent('15h 0m');
    expect(screen.getByTestId('metric-severe-route_2')).toHaveTextContent('30 mi');
    expect(screen.getByTestId('metric-high-route_2')).toHaveTextContent('70 mi');
  });

  it('confirms table metrics match the route cards and summary metrics', () => {
    render(<RouteComparisonCard routes={goldenAnalysis.routes} />);

    const routeA = goldenAnalysis.routes[0];
    const routeB = goldenAnalysis.routes[1];

    // Distance row
    expect(screen.getByText('785 mi')).toBeInTheDocument();
    expect(screen.getByText('801 mi')).toBeInTheDocument();

    // Severe miles row
    const severeCellA = screen.getByTestId(`metric-severe-${routeA.id}`);
    const severeCellB = screen.getByTestId(`metric-severe-${routeB.id}`);
    expect(severeCellA).toHaveTextContent(`${Math.round(routeA.summary?.miles_by_level?.severe || 0)} mi`);
    expect(severeCellB).toHaveTextContent(`${Math.round(routeB.summary?.miles_by_level?.severe || 0)} mi`);
  });
});
