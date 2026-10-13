import { renderHook, waitFor } from '@testing-library/react';
import { QueryClient, QueryClientProvider } from '@tanstack/react-query';
import React from 'react';
import { describe, expect, it, vi } from 'vitest';
import { useTripHeatmap } from './useTripHeatmap';
import * as tripsApi from '../api/tripsApi';
import { TripHeatmapResponse, TripRequestPayload } from '../api/types';

describe('useTripHeatmap', () => {
  const mockPayloadA: TripRequestPayload = {
    origin: { label: 'Dallas, TX', lat: 32.7767, lon: -96.797 },
    destination: { label: 'Denver, CO', lat: 39.7392, lon: -104.9903 },
    departure_local: '2026-10-12T08:00',
    load_weight_lb: 45000,
    interval: 'auto',
  };

  const mockPayloadB: TripRequestPayload = {
    ...mockPayloadA,
    load_weight_lb: 10000,
  };

  const mockResponseA: TripHeatmapResponse = {
    start_utc: '2026-10-12T13:00:00Z',
    start_local: '2026-10-12T08:00',
    origin_timezone: 'America/Chicago',
    cells: [{ lat: 33.0, lon: -97.0 }],
    frames: [
      {
        offset_hours: 0,
        time_utc: '2026-10-12T13:00:00Z',
        time_local: '2026-10-12T08:00:00',
        overall: [3], // Severe under 45k lb
        wind: [3],
        rain: [0],
        snow: [0],
      },
    ],
  };

  const mockResponseB: TripHeatmapResponse = {
    start_utc: '2026-10-12T13:00:00Z',
    start_local: '2026-10-12T08:00',
    origin_timezone: 'America/Chicago',
    cells: [{ lat: 33.0, lon: -97.0 }],
    frames: [
      {
        offset_hours: 0,
        time_utc: '2026-10-12T13:00:00Z',
        time_local: '2026-10-12T08:00:00',
        overall: [1], // Moderate under 10k lb
        wind: [1],
        rain: [0],
        snow: [0],
      },
    ],
  };

  it('changing load weight triggers a new heatmap request and clears old frames; changing it back reuses cache', async () => {
    const getTripHeatmapSpy = vi
      .spyOn(tripsApi, 'getTripHeatmap')
      .mockImplementation((payload) => {
        if (payload.load_weight_lb === 45000) {
          return Promise.resolve(mockResponseA);
        }
        return Promise.resolve(mockResponseB);
      });

    const queryClient = new QueryClient({
      defaultOptions: { queries: { retry: false, gcTime: Infinity, staleTime: Infinity } },
    });
    const wrapper = ({ children }: { children: React.ReactNode }) => (
      <QueryClientProvider client={queryClient}>{children}</QueryClientProvider>
    );

    const { result, rerender } = renderHook(
      ({ payload }) => useTripHeatmap(payload),
      {
        initialProps: { payload: mockPayloadA },
        wrapper,
      },
    );

    // Initial fetch for load 45,000 lb
    await waitFor(() => expect(result.current.isSuccess).toBe(true));
    expect(getTripHeatmapSpy).toHaveBeenCalledTimes(1);
    expect(result.current.data?.frames[0].overall).toEqual([3]);

    // 1. Changing load weight to 10,000 lb triggers new request & updates frames
    rerender({ payload: mockPayloadB });
    await waitFor(() => expect(result.current.data?.frames[0].overall).toEqual([1]));
    expect(getTripHeatmapSpy).toHaveBeenCalledTimes(2);

    // 2. Changing it back to 45,000 lb reuses the cache (no new network call)
    rerender({ payload: mockPayloadA });
    await waitFor(() => expect(result.current.data?.frames[0].overall).toEqual([3]));
    expect(getTripHeatmapSpy).toHaveBeenCalledTimes(2); // Still 2 calls, cached!

    getTripHeatmapSpy.mockRestore();
  });
});
