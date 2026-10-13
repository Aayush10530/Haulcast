import { render, screen } from '@testing-library/react';
import { describe, expect, it } from 'vitest';
import { CheckpointDTO } from '../../api/types';
import { CheckpointPopup } from './CheckpointPopup';

const mockCheckpointWithWeather: CheckpointDTO = {
  index: 1,
  mile: 120.5,
  lat: 35.4676,
  lon: -97.5164,
  eta_utc: '2026-10-12T15:00:00Z',
  eta_local: '2026-10-12T10:00:00-05:00',
  local_tz: 'America/Chicago',
  covers_miles: [100, 150],
  weather: {
    wind_mph: 38.2,
    rain_in_hr: 0.3,
    snow_in_hr: 0,
  },
  risk: {
    level: 'high',
    driver: 'wind',
    load_rule_applied: true,
    reason: 'Crosswinds gusting to 38 mph for 42,000 lb load',
  },
};

const mockCheckpointUnavailable: CheckpointDTO = {
  index: 2,
  mile: 350.0,
  lat: 37.6872,
  lon: -97.3301,
  eta_utc: '2026-10-12T18:45:00Z',
  eta_local: '2026-10-12T13:45:00-05:00',
  local_tz: 'America/Chicago',
  covers_miles: [325, 375],
  weather: null,
  risk: null,
};

describe('CheckpointPopup', () => {
  it('renders complete checkpoint popup content with weather and risk details', () => {
    render(<CheckpointPopup checkpoint={mockCheckpointWithWeather} />);

    // Mile & ETA formatted
    expect(screen.getByTestId('popup-mile')).toHaveTextContent('120.5 mi');
    expect(screen.getByTestId('popup-eta')).toHaveTextContent('Mon Oct 12, 10:00 CDT');

    // Risk chip
    expect(screen.getByTestId('risk-chip')).toHaveTextContent('High');
    expect(screen.getByTestId('driver-icon-scale')).toBeInTheDocument();

    // Weather metrics in mono
    expect(screen.getByTestId('popup-wind')).toHaveTextContent('38 mph');
    expect(screen.getByTestId('popup-rain')).toHaveTextContent('0.30 in/hr');
    expect(screen.getByTestId('popup-snow')).toHaveTextContent('0.00 in/hr');

    // API Reason
    expect(screen.getByTestId('popup-reason')).toHaveTextContent(
      'Crosswinds gusting to 38 mph for 42,000 lb load',
    );
  });

  it('renders "Forecast unavailable" when weather is null', () => {
    render(<CheckpointPopup checkpoint={mockCheckpointUnavailable} />);

    expect(screen.getByTestId('popup-mile')).toHaveTextContent('350 mi');
    expect(screen.getByTestId('popup-eta')).toHaveTextContent('Mon Oct 12, 13:45 CDT');
    expect(screen.getByTestId('popup-unavailable')).toHaveTextContent(
      'Forecast unavailable',
    );
    expect(screen.queryByTestId('popup-metrics')).not.toBeInTheDocument();
  });

  it('renders "Forecast unavailable" with neutral muted styling when risk is null', () => {
    const cpWithNullRisk: CheckpointDTO = {
      ...mockCheckpointWithWeather,
      risk: null,
    };
    render(<CheckpointPopup checkpoint={cpWithNullRisk} />);

    const unavailableEl = screen.getByTestId('popup-unavailable');
    expect(unavailableEl).toHaveTextContent('Forecast unavailable');
    expect(screen.queryByTestId('risk-chip')).not.toBeInTheDocument();
    expect(screen.queryByTestId('popup-metrics')).not.toBeInTheDocument();
  });
});
