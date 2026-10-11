import { fireEvent, render, screen } from '@testing-library/react';
import { describe, expect, it, vi } from 'vitest';
import { goldenAnalysis } from '../../test/fixtures/goldenAnalysis';
import { MapView } from './MapView';

describe('MapView', () => {
  it('renders empty state with US view and hint when analysis is null', () => {
    const handleSelectRoute = vi.fn();
    render(
      <MapView
        analysis={null}
        selectedRouteId={null}
        onSelectRoute={handleSelectRoute}
      />,
    );

    expect(screen.getByTestId('map-view-container')).toBeInTheDocument();
    expect(screen.getByTestId('map-empty-hint')).toHaveTextContent(
      'Plan a trip to view routes and weather risks',
    );
    expect(screen.getByTestId('map-legend')).toBeInTheDocument();
    expect(screen.queryByTestId('polyline')).not.toBeInTheDocument();
  });

  it('renders routes with label text, origin/destination tooltips, and checkpoints', () => {
    const handleSelectRoute = vi.fn();
    render(
      <MapView
        analysis={goldenAnalysis}
        selectedRouteId="route_b"
        onSelectRoute={handleSelectRoute}
      />,
    );

    // Empty hint is gone
    expect(screen.queryByTestId('map-empty-hint')).not.toBeInTheDocument();

    // Route label pills with duration
    const labelA = screen.getByTestId('route-label-route_a');
    const labelB = screen.getByTestId('route-label-route_b');
    expect(labelA).toHaveTextContent('A · 11h 28m');
    expect(labelB).toHaveTextContent('B · 12h 15m');

    // Origin and Destination tooltips
    expect(screen.getByText('Dallas, TX')).toBeInTheDocument();
    expect(screen.getByText('Denver, CO')).toBeInTheDocument();

    // Checkpoint circle markers exist
    const markers = screen.getAllByTestId('circle-marker');
    expect(markers.length).toBeGreaterThan(0);
  });

  it('selecting a route line or label calls onSelectRoute with routeId', () => {
    const handleSelectRoute = vi.fn();
    render(
      <MapView
        analysis={goldenAnalysis}
        selectedRouteId="route_b"
        onSelectRoute={handleSelectRoute}
      />,
    );

    // Click label for route A
    const labelA = screen.getByTestId('route-label-route_a');
    fireEvent.click(labelA);
    expect(handleSelectRoute).toHaveBeenCalledWith('route_a');
  });

  it('reflects selectedRouteId changes by styling selected route', () => {
    const { rerender } = render(
      <MapView
        analysis={goldenAnalysis}
        selectedRouteId="route_b"
        onSelectRoute={vi.fn()}
      />,
    );

    expect(screen.getByTestId('route-label-route_b')).toHaveClass('selected');
    expect(screen.getByTestId('route-label-route_a')).not.toHaveClass('selected');

    // Rerender with route_a selected
    rerender(
      <MapView
        analysis={goldenAnalysis}
        selectedRouteId="route_a"
        onSelectRoute={vi.fn()}
      />,
    );

    expect(screen.getByTestId('route-label-route_a')).toHaveClass('selected');
    expect(screen.getByTestId('route-label-route_b')).not.toHaveClass('selected');
  });
});
