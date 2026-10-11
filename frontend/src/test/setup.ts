/* eslint-disable @typescript-eslint/no-explicit-any, @typescript-eslint/no-unused-vars */
import '@testing-library/jest-dom/vitest';
import React from 'react';
import { vi } from 'vitest';

Object.defineProperty(window, 'matchMedia', {
  writable: true,
  value: (query: string) => ({
    matches: false,
    media: query,
    onchange: null,
    addListener: () => undefined,
    removeListener: () => undefined,
    addEventListener: () => undefined,
    removeEventListener: () => undefined,
    dispatchEvent: () => false,
  }),
});

class MockResizeObserver {
  observe = vi.fn();
  unobserve = vi.fn();
  disconnect = vi.fn();
}

window.ResizeObserver = window.ResizeObserver || (MockResizeObserver as unknown as typeof ResizeObserver);

vi.mock('leaflet', () => {
  return {
    default: {
      divIcon: vi.fn((opts) => opts),
      latLngBounds: vi.fn(() => ({
        extend: vi.fn(),
        isValid: vi.fn(() => true),
      })),
      Icon: {
        Default: vi.fn(),
      },
    },
    divIcon: vi.fn((opts) => opts),
    latLngBounds: vi.fn(() => ({
      extend: vi.fn(),
      isValid: vi.fn(() => true),
    })),
    Icon: {
      Default: vi.fn(),
    },
  };
});

vi.mock('react-leaflet', () => {
  const MockCircleMarker = React.forwardRef(
    ({ children, eventHandlers, center, radius, pathOptions, ...props }: any, ref: any) =>
      React.createElement(
        'div',
        {
          ref,
          'data-testid': 'circle-marker',
          'data-lat': center?.[0],
          'data-lon': center?.[1],
          'data-radius': radius,
          'data-fillcolor': pathOptions?.fillColor,
          onClick: eventHandlers?.click,
          ...props,
        },
        children,
      ),
  );
  MockCircleMarker.displayName = 'MockCircleMarker';

  return {
    MapContainer: ({ children, className, preferCanvas, zoomControl, center, zoom, style, ...props }: any) =>
      React.createElement('div', { 'data-testid': 'map-container', className, style, ...props }, children),
    TileLayer: ({ url, attribution, subdomains, maxZoom, ...props }: any) =>
      React.createElement('div', { 'data-testid': 'tile-layer', ...props }),
    ZoomControl: ({ position, ...props }: any) =>
      React.createElement('div', { 'data-testid': 'zoom-control', ...props }),
    Polyline: ({ children, eventHandlers, pathOptions, positions, ...props }: any) =>
      React.createElement(
        'div',
        {
          'data-testid': 'polyline',
          'data-color': pathOptions?.color,
          'data-weight': pathOptions?.weight,
          'data-dasharray': pathOptions?.dashArray,
          onClick: eventHandlers?.click,
          ...props,
        },
        children,
      ),
    CircleMarker: MockCircleMarker,
    Marker: ({ children, eventHandlers, position, icon, ...props }: any) =>
      React.createElement(
        'div',
        {
          'data-testid': 'marker',
          'data-lat': position?.[0],
          'data-lon': position?.[1],
          dangerouslySetInnerHTML: icon?.html ? { __html: icon.html } : undefined,
          onClick: eventHandlers?.click,
          ...props,
        },
        children,
      ),
    Popup: ({ children, ...props }: any) =>
      React.createElement('div', { 'data-testid': 'popup', ...props }, children),
    Tooltip: ({ children, ...props }: any) =>
      React.createElement('div', { 'data-testid': 'tooltip', ...props }, children),
    useMap: () => ({
      fitBounds: vi.fn(),
      setView: vi.fn(),
      invalidateSize: vi.fn(),
      getZoom: vi.fn(() => 4),
      getContainer: vi.fn(() => document.createElement('div')),
      on: vi.fn(),
      off: vi.fn(),
    }),
  };
});
