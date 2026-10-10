import '@testing-library/jest-dom/vitest';
import { render, screen } from '@testing-library/react';
import { describe, expect, it } from 'vitest';
import { ThemeProvider } from '@mui/material/styles';
import { theme } from './theme/theme';
import { App } from './App';

describe('App component', () => {
  it('renders the operations console header with wordmark and ready dot', () => {
    render(
      <ThemeProvider theme={theme}>
        <App />
      </ThemeProvider>,
    );

    expect(screen.getByText('Weather-Aware Truck Router')).toBeInTheDocument();
    expect(screen.getByText('Trip Planning')).toBeInTheDocument();
  });
});
