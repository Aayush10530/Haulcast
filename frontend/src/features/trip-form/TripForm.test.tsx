import '@testing-library/jest-dom/vitest';
import { fireEvent, render, screen, waitFor } from '@testing-library/react';
import { afterEach, beforeEach, describe, expect, it, vi } from 'vitest';
import { ThemeProvider } from '@mui/material/styles';
import { QueryClient, QueryClientProvider } from '@tanstack/react-query';
import { AnalyzeResponse } from '../../api/types';
import { theme } from '../../theme/theme';
import { TripForm } from './TripForm';

const mockAnalyzeResponse: AnalyzeResponse = {
  request: {
    origin: { label: 'Dallas, TX', lat: 32.7767, lon: -96.797 },
    destination: { label: 'Denver, CO', lat: 39.7392, lon: -104.9903 },
    departure_utc: '2026-10-12T13:00:00Z',
    departure_local: '2026-10-12T08:00',
    origin_timezone: 'America/Chicago',
    load_weight_lb: 42000,
    interval_miles: 25,
    interval_mode: 'auto',
  },
  recommended_route_id: 'route_b',
  recommendation: {
    route_id: 'route_b',
    decided_by: 'severe_miles',
    headline: 'Route B has 0 Severe miles vs 34 on Route A.',
    comparisons: [],
  },
  routes: [
    {
      id: 'route_b',
      label: 'Route B',
      tags: ['recommended'],
      rank: 1,
      via: 'I-35 N, I-70 W',
      distance_miles: 801.2,
      duration_seconds: 44100,
      departure_utc: '2026-10-12T13:00:00Z',
      arrival_utc: '2026-10-13T01:15:00Z',
      arrival_local: '2026-10-12T19:15:00-06:00',
      geometry: [
        [32.7767, -96.797],
        [39.7392, -104.9903],
      ],
      summary: {
        miles_by_level: {
          low: 600,
          moderate: 150,
          high: 51.2,
          severe: 0,
          no_travel: 0,
        },
        avg_risk_score: 0.62,
        max_level: 'high',
        has_no_travel: false,
        delta_vs_fastest_seconds: 0,
      },
      checkpoints: [],
    },
  ],
  warnings: [],
  meta: {
    routing_provider: 'tomtom',
    weather_provider: 'open-meteo',
    weather_cells: 50,
    route_count: 1,
    elapsed_ms: 2500,
  },
};

function renderTripForm(props: {
  onSuccess?: (analysis: AnalyzeResponse) => void;
  disabled?: boolean;
} = {}) {
  const queryClient = new QueryClient({
    defaultOptions: {
      queries: { retry: false },
      mutations: { retry: false },
    },
  });

  return render(
    <QueryClientProvider client={queryClient}>
      <ThemeProvider theme={theme}>
        <TripForm {...props} />
      </ThemeProvider>
    </QueryClientProvider>,
  );
}

describe('TripForm Component', () => {
  beforeEach(() => {
    vi.restoreAllMocks();
  });

  afterEach(() => {
    vi.unstubAllGlobals();
  });

  it('renders title and all form inputs', () => {
    renderTripForm();

    expect(screen.getByText('Trip planning')).toBeInTheDocument();
    expect(screen.getByLabelText('Origin')).toBeInTheDocument();
    expect(screen.getByLabelText('Destination')).toBeInTheDocument();
    expect(screen.getByLabelText('Swap origin and destination')).toBeInTheDocument();
    expect(screen.getByLabelText('Departure')).toBeInTheDocument();
    expect(screen.getByLabelText('Load weight (lb)')).toBeInTheDocument();
    expect(screen.getByText('Checkpoint interval')).toBeInTheDocument();
    expect(screen.getByTestId('generate-routes-button')).toHaveTextContent(
      'Generate routes',
    );
    expect(screen.getByTestId('example-trip-button')).toHaveTextContent(
      'Try an example trip',
    );
  });

  it('fills example trip values when example button is clicked', () => {
    renderTripForm();

    const exampleButton = screen.getByTestId('example-trip-button');
    fireEvent.click(exampleButton);

    const originInput = screen.getByLabelText('Origin') as HTMLInputElement;
    const destInput = screen.getByLabelText('Destination') as HTMLInputElement;
    const loadInput = screen.getByLabelText('Load weight (lb)') as HTMLInputElement;
    const departureInput = screen.getByLabelText('Departure') as HTMLInputElement;

    expect(originInput.value).toBe('Dallas, TX');
    expect(destInput.value).toBe('Denver, CO');
    expect(loadInput.value).toBe('42000');
    expect(departureInput.value).toMatch(/^\d{4}-\d{2}-\d{2}T08:00$/);
  });

  it('swaps origin and destination when swap button is clicked', () => {
    renderTripForm();

    // Populate using example trip first
    fireEvent.click(screen.getByTestId('example-trip-button'));

    const originInput = screen.getByLabelText('Origin') as HTMLInputElement;
    const destInput = screen.getByLabelText('Destination') as HTMLInputElement;

    expect(originInput.value).toBe('Dallas, TX');
    expect(destInput.value).toBe('Denver, CO');

    // Click swap
    const swapButton = screen.getByTestId('swap-places-button');
    fireEvent.click(swapButton);

    expect(originInput.value).toBe('Denver, CO');
    expect(destInput.value).toBe('Dallas, TX');
  });

  it('submits the exact payload on valid submission', async () => {
    let capturedBody: unknown = null;
    vi.stubGlobal(
      'fetch',
      vi.fn().mockImplementation(async (url: string, init?: RequestInit) => {
        if (url.includes('/api/trips/analyze/')) {
          capturedBody = JSON.parse(init?.body as string);
          return {
            ok: true,
            status: 200,
            json: async () => mockAnalyzeResponse,
          };
        }
        return { ok: true, status: 200, json: async () => ({}) };
      }),
    );

    const handleSuccess = vi.fn();
    renderTripForm({ onSuccess: handleSuccess });

    // Fill form with example button
    fireEvent.click(screen.getByTestId('example-trip-button'));

    // Select 25 mi interval
    fireEvent.click(screen.getByTestId('interval-25'));

    // Submit form
    const submitButton = screen.getByTestId('generate-routes-button');
    fireEvent.click(submitButton);

    await waitFor(() => {
      expect(handleSuccess).toHaveBeenCalledWith(mockAnalyzeResponse);
    });

    expect(capturedBody).toMatchObject({
      origin: { label: 'Dallas, TX', lat: 32.7767, lon: -96.797 },
      destination: { label: 'Denver, CO', lat: 39.7392, lon: -104.9903 },
      load_weight_lb: 42000,
      interval: 25,
    });
    expect((capturedBody as { departure_local: string }).departure_local).toMatch(
      /^\d{4}-\d{2}-\d{2}T08:00$/,
    );
  });

  it('disables submit button and shows "Finding routes..." while pending', async () => {
    let resolvePromise: (val: unknown) => void = () => undefined;
    const pendingPromise = new Promise((resolve) => {
      resolvePromise = resolve;
    });

    vi.stubGlobal(
      'fetch',
      vi.fn().mockImplementation(async (url: string) => {
        if (url.includes('/api/trips/analyze/')) {
          await pendingPromise;
          return {
            ok: true,
            status: 200,
            json: async () => mockAnalyzeResponse,
          };
        }
        return { ok: true, status: 200, json: async () => ({}) };
      }),
    );

    renderTripForm();

    fireEvent.click(screen.getByTestId('example-trip-button'));

    const submitButton = screen.getByTestId('generate-routes-button');
    fireEvent.click(submitButton);

    // Verify pending state
    await waitFor(() => {
      expect(submitButton).toBeDisabled();
      expect(submitButton).toHaveTextContent('Finding routes...');
    });

    // Resolve
    resolvePromise(null);

    await waitFor(() => {
      expect(submitButton).not.toBeDisabled();
      expect(submitButton).toHaveTextContent('Generate routes');
    });
  });

  it('renders server field errors under the right fields', async () => {
    vi.stubGlobal(
      'fetch',
      vi.fn().mockResolvedValue({
        ok: false,
        status: 400,
        json: async () => ({
          error: {
            code: 'validation_error',
            message: 'Validation failed.',
            fields: {
              load_weight_lb: ['Ensure this value is less than or equal to 120000.'],
              departure_local: ['Departure time is outside the allowed window.'],
            },
          },
        }),
      }),
    );

    renderTripForm();

    fireEvent.click(screen.getByTestId('example-trip-button'));

    const submitButton = screen.getByTestId('generate-routes-button');
    fireEvent.click(submitButton);

    await waitFor(() => {
      expect(
        screen.getByText('Ensure this value is less than or equal to 120000.'),
      ).toBeInTheDocument();
      expect(
        screen.getByText('Departure time is outside the allowed window.'),
      ).toBeInTheDocument();
    });
  });

  it('shows Alert on 503 error and Retry button resubmits', async () => {
    let callCount = 0;
    vi.stubGlobal(
      'fetch',
      vi.fn().mockImplementation(async (url: string) => {
        if (url.includes('/api/trips/analyze/')) {
          callCount += 1;
          if (callCount === 1) {
            return {
              ok: false,
              status: 503,
              json: async () => ({
                error: {
                  code: 'weather_unavailable',
                  message: 'Weather service is currently unavailable. Please try again later.',
                },
              }),
            };
          }
          return {
            ok: true,
            status: 200,
            json: async () => mockAnalyzeResponse,
          };
        }
        return { ok: true, status: 200, json: async () => ({}) };
      }),
    );

    const handleSuccess = vi.fn();
    renderTripForm({ onSuccess: handleSuccess });

    fireEvent.click(screen.getByTestId('example-trip-button'));

    const submitButton = screen.getByTestId('generate-routes-button');
    fireEvent.click(submitButton);

    // Wait for Alert on 503
    await waitFor(() => {
      expect(screen.getByTestId('trip-form-alert')).toBeInTheDocument();
      expect(
        screen.getByText('Weather service is currently unavailable. Please try again later.'),
      ).toBeInTheDocument();
    });

    expect(callCount).toBe(1);

    // Click Retry button
    const retryButton = screen.getByTestId('retry-button');
    fireEvent.click(retryButton);

    await waitFor(() => {
      expect(handleSuccess).toHaveBeenCalledWith(mockAnalyzeResponse);
    });

    expect(callCount).toBe(2);
  });
});
