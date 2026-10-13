import { render, screen } from '@testing-library/react';
import { describe, expect, it } from 'vitest';
import { WeatherRadarLayer } from './WeatherRadarLayer';
import { CheckpointDTO, RouteDTO } from '../../api/types';
import { riskColors } from '../../theme/riskColors';

describe('WeatherRadarLayer', () => {
  const observedCheckpoint: CheckpointDTO = {
    index: 0,
    mile: 25.0,
    lat: 33.5,
    lon: -97.2,
    eta_utc: '2026-10-12T13:30:00Z',
    eta_local: '2026-10-12T08:30:00',
    local_tz: 'America/Chicago',
    covers_miles: [0.0, 50.0],
    weather: {
      wind_mph: 48.0,
      rain_in_hr: 0.0,
      snow_in_hr: 0.0,
    },
    risk: {
      level: 'severe',
      level_label: 'Severe',
      driver: 'wind',
      reason: 'Wind gusts over 55 mph',
      load_rule_applied: false,
    },
  };

  const unavailableCheckpoint: CheckpointDTO = {
    index: 1,
    mile: 50.0,
    lat: 34.0,
    lon: -97.8,
    eta_utc: '2026-10-12T14:00:00Z',
    eta_local: '2026-10-12T09:00:00',
    local_tz: 'America/Chicago',
    covers_miles: [50.0, 100.0],
    weather: null,
    risk: null,
  };

  const mockRoute: RouteDTO = {
    id: 'route_test',
    label: 'Route Test',
    tags: [],
    rank: 1,
    via: 'I-35',
    distance_miles: 100.0,
    duration_seconds: 7200.0,
    departure_utc: '2026-10-12T13:00:00Z',
    arrival_utc: '2026-10-12T15:00:00Z',
    arrival_local: '2026-10-12T10:00:00',
    geometry: [
      [33.0, -97.0],
      [35.0, -98.0],
    ],
    checkpoints: [observedCheckpoint, unavailableCheckpoint],
    summary: {
      miles_by_level: { low: 0, moderate: 0, high: 0, severe: 25.0, no_travel: 0 },
      unavailable_miles: 25.0,
      avg_risk_score: 3.2,
      max_level: 'severe',
      has_no_travel: false,
      delta_vs_fastest_seconds: 0.0,
    },
  };

  it('renders radar circle for assessed checkpoints and omits circle for unavailable checkpoints', () => {
    render(
      <WeatherRadarLayer
        routes={[mockRoute]}
        selectedRouteId="route_test"
        isVisible={true}
      />,
    );

    const circles = screen.getAllByTestId('circle-marker');
    expect(circles).toHaveLength(1);
    expect(circles[0]).toHaveAttribute('data-lat', '33.5');
    expect(circles[0]).toHaveAttribute('data-lon', '-97.2');
    expect(circles[0]).toHaveAttribute('data-fillcolor', riskColors.severe.background);
    expect(circles[0]).not.toHaveAttribute('data-fillcolor', riskColors.low.background);
  });

  it('returns null when isVisible is false', () => {
    const { container } = render(
      <WeatherRadarLayer
        routes={[mockRoute]}
        selectedRouteId="route_test"
        isVisible={false}
      />,
    );
    expect(container.firstChild).toBeNull();
  });
});
