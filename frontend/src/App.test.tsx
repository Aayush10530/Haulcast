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

function setViewportWidth(width: number) {
  window.innerWidth = width;
  window.matchMedia = vi.fn().mockImplementation((query: string) => {
    const maxWidthMatch = query.match(/max-width:\s*([\d.]+)px/);
    const minWidthMatch = query.match(/min-width:\s*([\d.]+)px/);
    let matches = true;
    if (maxWidthMatch && width > parseFloat(maxWidthMatch[1])) {
      matches = false;
    }
    if (minWidthMatch && width < parseFloat(minWidthMatch[1])) {
      matches = false;
    }
    return {
      matches,
      media: query,
      onchange: null,
      addListener: vi.fn(),
      removeListener: vi.fn(),
      addEventListener: vi.fn(),
      removeEventListener: vi.fn(),
      dispatchEvent: vi.fn(),
    };
  });
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

    setViewportWidth(390);

    renderWithProviders();

    const tripForm = screen.getByTestId('region-trip-form');
    const map = screen.getByTestId('region-map');
    const results = screen.getByTestId('region-results');

    // All 3 regions exist with their proper labels
    expect(tripForm).toHaveTextContent('Trip planning');
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

  it('shows temporary plain line with route count and headline in results region on success', async () => {
    vi.stubGlobal(
      'fetch',
      vi.fn().mockImplementation(async (url: string) => {
        if (url.includes('/api/trips/analyze/')) {
          return {
            ok: true,
            status: 200,
            json: async () => ({
              recommended_route_id: 'route_b',
              recommendation: {
                route_id: 'route_b',
                decided_by: 'severe_miles',
                headline: 'Route B has 0 Severe miles vs 34 on Route A.',
                comparisons: [],
              },
              routes: [{ id: 'route_b' }, { id: 'route_a' }, { id: 'route_c' }],
              warnings: [],
              meta: { elapsed_ms: 1200 },
            }),
          };
        }
        return {
          ok: true,
          status: 200,
          json: async () => ({ status: 'ok' }),
        };
      }),
    );

    setViewportWidth(1100);
    renderWithProviders();

    // Click example trip and generate routes
    fireEvent.click(screen.getByTestId('example-trip-button'));
    fireEvent.click(screen.getByTestId('generate-routes-button'));

    await waitFor(() => {
      expect(screen.getByTestId('results-summary')).toHaveTextContent(
        '3 routes: Route B has 0 Severe miles vs 34 on Route A.',
      );
    });
  });

  describe('Breakpoint Layouts below and above 900 px and 1440 px', () => {
    it.each([390, 800])(
      'renders mobile layout at %i px with fixed tab bar, Plan selected, and active region visible',
      (width) => {
        setViewportWidth(width);
        renderWithProviders();

        // Fixed bottom tab bar exists below 900 px
        const tabPlan = screen.getByTestId('tab-plan');
        const tabMap = screen.getByTestId('tab-map');
        const tabRoutes = screen.getByTestId('tab-routes');
        expect(tabPlan).toBeInTheDocument();
        expect(tabMap).toBeInTheDocument();
        expect(tabRoutes).toBeInTheDocument();

        // Plan tab is selected by default
        expect(tabPlan).toHaveClass('Mui-selected');

        // Active region (Plan / Trip form) is visible above the tab bar, other regions hidden
        expect(screen.getByTestId('region-trip-form')).toBeVisible();
        expect(screen.getByTestId('region-map')).not.toBeVisible();
        expect(screen.getByTestId('region-results')).not.toBeVisible();
      },
    );

    it('renders two-column layout at 1100 px without tab bar and with map region visible', () => {
      setViewportWidth(1100);
      renderWithProviders();

      // Tab bar does NOT exist at 1100 px (>= 900 px)
      expect(screen.queryByTestId('tab-plan')).not.toBeInTheDocument();
      expect(screen.queryByTestId('tab-map')).not.toBeInTheDocument();
      expect(screen.queryByTestId('tab-routes')).not.toBeInTheDocument();

      // In the two-column layout, the map region exists and is visible
      const mapRegion = screen.getByTestId('region-map');
      expect(mapRegion).toBeInTheDocument();
      expect(mapRegion).toBeVisible();

      // 400 px left panel regions also exist and are visible
      expect(screen.getByTestId('region-trip-form')).toBeVisible();
      expect(screen.getByTestId('region-results')).toBeVisible();
    });

    it('renders three-column layout at 1440 px without tab bar and with all regions visible', () => {
      setViewportWidth(1440);
      renderWithProviders();

      // Tab bar does NOT exist at 1440 px
      expect(screen.queryByTestId('tab-plan')).not.toBeInTheDocument();

      // All 3 regions exist and are visible
      expect(screen.getByTestId('region-trip-form')).toBeVisible();
      expect(screen.getByTestId('region-map')).toBeVisible();
      expect(screen.getByTestId('region-results')).toBeVisible();
    });
  });
});
