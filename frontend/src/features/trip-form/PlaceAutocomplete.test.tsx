import '@testing-library/jest-dom/vitest';
import { fireEvent, render, screen, waitFor } from '@testing-library/react';
import { beforeEach, describe, expect, it, vi } from 'vitest';
import { ThemeProvider } from '@mui/material/styles';
import { QueryClient, QueryClientProvider } from '@tanstack/react-query';
import { theme } from '../../theme/theme';
import { PlaceAutocomplete } from './PlaceAutocomplete';

function renderWithProviders(ui: React.ReactElement) {
  const queryClient = new QueryClient({
    defaultOptions: {
      queries: {
        retry: false,
      },
    },
  });

  return render(
    <QueryClientProvider client={queryClient}>
      <ThemeProvider theme={theme}>{ui}</ThemeProvider>
    </QueryClientProvider>,
  );
}

describe('PlaceAutocomplete', () => {
  beforeEach(() => {
    vi.restoreAllMocks();
  });

  it('renders label and placeholder', () => {
    renderWithProviders(
      <PlaceAutocomplete
        id="test-origin"
        label="Origin"
        placeholder="Search origin city"
        value={null}
        onChange={() => undefined}
      />,
    );

    expect(screen.getByLabelText('Origin')).toBeInTheDocument();
    expect(
      screen.getByPlaceholderText('Search origin city'),
    ).toBeInTheDocument();
  });

  it('searches places and selects a mocked result', async () => {
    const handleChange = vi.fn();
    const mockPlaces = [
      { id: '1', label: 'Dallas, TX', lat: 32.7767, lon: -96.797 },
      { id: '2', label: 'Dallas Center, IA', lat: 41.6828, lon: -93.9688 },
    ];

    vi.stubGlobal(
      'fetch',
      vi.fn().mockResolvedValue({
        ok: true,
        status: 200,
        json: async () => mockPlaces,
      }),
    );

    renderWithProviders(
      <PlaceAutocomplete
        id="test-origin"
        label="Origin"
        placeholder="Search origin city"
        value={null}
        onChange={handleChange}
      />,
    );

    const input = screen.getByLabelText('Origin');
    fireEvent.focus(input);
    fireEvent.change(input, { target: { value: 'Dallas' } });

    // Wait for debounced fetch and autocomplete options to appear
    await waitFor(() => {
      expect(screen.getByRole('listbox')).toBeInTheDocument();
    });

    const option = screen.getByRole('option', { name: 'Dallas, TX' });
    fireEvent.click(option);

    expect(handleChange).toHaveBeenCalledWith(mockPlaces[0]);
  });

  it('shows "No matches" when geocoding returns empty list for >= 3 chars', async () => {
    vi.stubGlobal(
      'fetch',
      vi.fn().mockResolvedValue({
        ok: true,
        status: 200,
        json: async () => [],
      }),
    );

    renderWithProviders(
      <PlaceAutocomplete
        id="test-origin"
        label="Origin"
        placeholder="Search origin city"
        value={null}
        onChange={() => undefined}
      />,
    );

    const input = screen.getByLabelText('Origin');
    fireEvent.focus(input);
    fireEvent.change(input, { target: { value: 'UnknownPlaceXYZ' } });

    await waitFor(() => {
      expect(screen.getByText('No matches')).toBeInTheDocument();
    });
  });
});
