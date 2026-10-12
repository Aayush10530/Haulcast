import React, { useEffect, useMemo, useRef } from 'react';
import { useMap } from 'react-leaflet';
import L from 'leaflet';
import 'leaflet.heat';
import { TripHeatmapResponse } from '../../api/types';
import { riskColors } from '../../theme/riskColors';
import { toHeatPoints } from './heatUtils';

export interface HeatmapLayerProps {
  heatmapData?: TripHeatmapResponse | null;
  forecastHour?: number;
  isVisible?: boolean;
}

export const HeatmapLayer: React.FC<HeatmapLayerProps> = ({
  heatmapData,
  forecastHour = 0,
  isVisible = true,
}) => {
  const map = useMap();
  const heatLayerRef = useRef<L.HeatLayer | null>(null);

  // Precompute per-frame [lat, lon, intensity] arrays on response arrival per ARCHITECTURE.md §10
  const framesPoints = useMemo(() => {
    if (!heatmapData?.cells || !heatmapData?.frames) {
      return [];
    }
    const { cells, frames } = heatmapData;
    return frames.map((frame) => toHeatPoints(cells, frame.overall));
  }, [heatmapData]);

  // Create leaflet.heat layer once on map
  useEffect(() => {
    if (!map) return;

    if (typeof L.heatLayer !== 'function') {
      return;
    }

    const layer = L.heatLayer([], {
      radius: 28,
      blur: 18,
      maxZoom: 13,
      minOpacity: 0.12,
      gradient: {
        0.05: riskColors.low.background,
        0.30: riskColors.moderate.background,
        0.60: riskColors.high.background,
        0.85: riskColors.severe.background,
        1.00: riskColors.no_travel.background,
      },
    });

    layer.addTo(map);
    heatLayerRef.current = layer;

    return () => {
      try {
        if (layer) {
          if (typeof map?.hasLayer === 'function' && map.hasLayer(layer)) {
            map.removeLayer(layer);
          } else if (typeof map?.removeLayer === 'function') {
            map.removeLayer(layer);
          }
        }
      } catch {
        // Safe fallback for unmounted/test map instances
      }
      heatLayerRef.current = null;
    };
  }, [map]);

  // Update points on slider forecastHour change using requestAnimationFrame
  useEffect(() => {
    const layer = heatLayerRef.current;
    if (!layer || typeof layer.setLatLngs !== 'function') return;

    if (!isVisible || framesPoints.length === 0) {
      layer.setLatLngs([]);
      return;
    }

    const frameIdx = Math.min(
      Math.max(0, forecastHour),
      Math.max(0, framesPoints.length - 1),
    );
    const pts = framesPoints[frameIdx] || [];

    const rafId = requestAnimationFrame(() => {
      layer.setLatLngs(pts);
    });

    return () => {
      cancelAnimationFrame(rafId);
    };
  }, [forecastHour, isVisible, framesPoints]);

  return null;
};
