import '@testing-library/jest-dom/vitest';
import { fireEvent, render, screen, waitFor } from '@testing-library/react';
import { afterEach, beforeEach, describe, expect, it, vi } from 'vitest';
import { ThemeProvider } from '@mui/material/styles';
import { QueryClient, QueryClientProvider } from '@tanstack/react-query';
import { theme } from './theme/theme';
import { App } from './App';

function renderWithProviders() {
  const queryClient = new QueryClient({
    defaultOptions: {
      queries: {
        retry: false,
      },
    },
  });

  return render(
    <QueryClientProvider client={queryClient}>
      <ThemeProvider theme={theme}>
        <App />
      </ThemeProvider>
    </QueryClientProvider>,
  );
}

describe('App Component Shell & Responsive Layouts', () => {
  beforeEach(() => {
    vi.restoreAllMocks();
  });

  afterEach(() => {
    vi.unstubAllGlobals();
  });

  it('renders header wordmark StormRoute and subtitle', async () => {
    vi.stubGlobal(
      'fetch',
      vi.fn().mockResolvedValue({
        ok: true,
        status: 200,
        json: async () => ({ status: 'ok' }),
      }),
    );

    renderWithProviders();

    expect(screen.getByText('StormRoute')).toBeInTheDocument();
    expect(screen.getByText('Weather-Aware Truck Router')).toBeInTheDocument();
  });

  it('renders "API online" with green status dot when health check succeeds', async () => {
    vi.stubGlobal(
      'fetch',
      vi.fn().mockResolvedValue({
        ok: true,
        status: 200,
        json: async () => ({ status: 'ok' }),
      }),
    );

    renderWithProviders();

    await waitFor(() => {
      expect(screen.getByText('API online')).toBeInTheDocument();
    });

    const dot = screen.getByTestId('status-dot');
    expect(dot).toHaveStyle({ backgroundColor: '#3FA66B' });
  });

  it('renders "API offline" with red status dot when health check fails', async () => {
    vi.stubGlobal(
      'fetch',
      vi.fn().mockRejectedValue(new Error('Connection refused')),
    );

    renderWithProviders();

    await waitFor(() => {
      expect(screen.getByText('API offline')).toBeInTheDocument();
    });

    const dot = screen.getByTestId('status-dot');
    expect(dot).toHaveStyle({ backgroundColor: '#E5484D' });
  });

  it('renders empty labeled regions and switches visible region via mobile tab bar', () => {
    vi.stubGlobal(
      'fetch',
      vi.fn().mockResolvedValue({
        ok: true,
        status: 200,
        json: async () => ({ status: 'ok' }),
      }),
    );

    renderWithProviders();

    const tripForm = screen.getByTestId('region-trip-form');
    const map = screen.getByTestId('region-map');
    const results = screen.getByTestId('region-results');

    // All 3 regions exist with their proper labels
    expect(tripForm).toHaveTextContent('Trip form');
    expect(map).toHaveTextContent('Map');
    expect(results).toHaveTextContent('Results');

    // Initial state: Plan tab is active
    expect(tripForm).toBeVisible();
    expect(map).not.toBeVisible();
    expect(results).not.toBeVisible();

    // Switch to Map tab
    fireEvent.click(screen.getByTestId('tab-map'));
    expect(tripForm).not.toBeVisible();
    expect(map).toBeVisible();
    expect(results).not.toBeVisible();

    // Switch to Routes (Results) tab
    fireEvent.click(screen.getByTestId('tab-routes'));
    expect(tripForm).not.toBeVisible();
    expect(map).not.toBeVisible();
    expect(results).toBeVisible();

    // Switch back to Plan tab
    fireEvent.click(screen.getByTestId('tab-plan'));
    expect(tripForm).toBeVisible();
    expect(map).not.toBeVisible();
    expect(results).not.toBeVisible();
  });
});
