import React, { useEffect, useRef } from 'react';
import { useMap } from 'react-leaflet';
import L from 'leaflet';
import { CheckpointDTO, RouteDTO } from '../../api/types';

export interface MapControllerProps {
  routes: RouteDTO[];
  focusedCheckpoint?: CheckpointDTO | null;
  isVisible?: boolean;
}

export const MapController: React.FC<MapControllerProps> = ({
  routes,
  focusedCheckpoint,
  isVisible = true,
}) => {
  const map = useMap();
  const prevRoutesRef = useRef<RouteDTO[]>([]);

  // 1. Fit bounds to all routes when results arrive or change (no animation)
  useEffect(() => {
    if (!routes || routes.length === 0) return;
    if (routes === prevRoutesRef.current) return;
    prevRoutesRef.current = routes;

    const bounds = L.latLngBounds([]);
    for (const r of routes) {
      for (const [lat, lon] of r.geometry) {
        bounds.extend([lat, lon]);
      }
    }

    if (bounds.isValid()) {
      map.fitBounds(bounds, { padding: [40, 40], animate: false });
    }
  }, [map, routes]);

  // 2. Pan to focusedCheckpoint when selected from list (zoom at least 7)
  useEffect(() => {
    if (!focusedCheckpoint) return;
    const targetZoom = Math.max(map.getZoom(), 7);
    map.setView([focusedCheckpoint.lat, focusedCheckpoint.lon], targetZoom, {
      animate: true,
    });
  }, [focusedCheckpoint, map]);

  // 3. Handle tab visibility change
  useEffect(() => {
    if (isVisible) {
      map.invalidateSize({ pan: false });
      const timer = setTimeout(() => {
        map.invalidateSize({ pan: false });
      }, 50);
      return () => clearTimeout(timer);
    }
  }, [isVisible, map]);

  // 4. Handle container resize (ResizeObserver)
  useEffect(() => {
    const container = map.getContainer();
    if (!container || typeof ResizeObserver === 'undefined') return;

    const ro = new ResizeObserver(() => {
      map.invalidateSize({ pan: false });
    });
    ro.observe(container);

    return () => {
      ro.disconnect();
    };
  }, [map]);

  return null;
};
