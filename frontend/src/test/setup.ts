import '@testing-library/jest-dom';
import React from 'react';
import { vi } from 'vitest';

// Polyfill window.matchMedia for responsive UI tests
Object.defineProperty(window, 'matchMedia', {
  writable: true,
  value: (query: string) => ({
    matches: false,
    media: query,
    onchange: null,
    addListener: () => {},
    removeListener: () => {},
    addEventListener: () => {},
    removeEventListener: () => {},
    dispatchEvent: () => false,
  }),
});

// Polyfill ResizeObserver for Recharts responsive containers
global.ResizeObserver = class ResizeObserver {
  observe() {}
  unobserve() {}
  disconnect() {}
};

// Mock react-leaflet for headless JSDOM testing using React.createElement
vi.mock('react-leaflet', () => ({
  MapContainer: ({ children }: any) => React.createElement('div', { 'data-testid': 'map-container' }, children),
  TileLayer: () => React.createElement('div', { 'data-testid': 'tile-layer' }),
  CircleMarker: ({ children }: any) => React.createElement('div', { 'data-testid': 'circle-marker' }, children),
  Circle: ({ children }: any) => React.createElement('div', { 'data-testid': 'circle' }, children),
  Popup: ({ children }: any) => React.createElement('div', { 'data-testid': 'popup' }, children),
  Marker: ({ children }: any) => React.createElement('div', { 'data-testid': 'marker' }, children),
}));
