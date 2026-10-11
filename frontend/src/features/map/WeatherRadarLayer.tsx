import React from 'react';
import { Circle } from 'react-leaflet';
import { RouteDTO, TripHeatmapResponse } from '../../api/types';

export interface WeatherRadarLayerProps {
  routes?: RouteDTO[];
  selectedRouteId?: string | null;
  forecastHour?: number;
  heatmapData?: TripHeatmapResponse | null;
  isVisible?: boolean;
}

export const WeatherRadarLayer: React.FC<WeatherRadarLayerProps> = ({
  routes = [],
  selectedRouteId,
  forecastHour = 0,
  heatmapData,
  isVisible = true,
}) => {
  if (!isVisible || !routes || routes.length === 0) {
    return null;
  }

  // Selected route checkpoints for corridor risk heat zones
  const activeRoute =
    routes.find((r) => r.id === selectedRouteId) || routes[0] || null;
  const checkpoints = activeRoute?.checkpoints || [];

  // Frame selection from heatmap dataset (0 to 48 hours)
  const heatmapFrames = heatmapData?.frames || [];
  const activeFrameIndex = Math.min(
    Math.max(0, forecastHour),
    Math.max(0, heatmapFrames.length - 1),
  );
  const currentFrame = heatmapFrames[activeFrameIndex];
  const heatmapCells = heatmapData?.cells || [];

  return (
    <>
      {/* 1. Live Corridor Heatmap Grid Cells (from /api/trips/heatmap/ 0-48h forecast) */}
      {currentFrame &&
        heatmapCells.map((cell, idx) => {
          const score = currentFrame.overall[idx];
          if (score === null || score === undefined) {
            return null;
          }

          let fillColor = '#10B981'; // green / low risk
          let opacity = 0.15;
          let radius = 22000;

          if (score >= 4) {
            fillColor = '#8B5CF6'; // no travel purple
            opacity = 0.70;
            radius = 34000;
          } else if (score === 3) {
            fillColor = '#EF4444'; // severe red
            opacity = 0.60;
            radius = 30000;
          } else if (score === 2) {
            fillColor = '#F97316'; // high orange
            opacity = 0.48;
            radius = 26000;
          } else if (score === 1) {
            fillColor = '#F59E0B'; // moderate yellow
            opacity = 0.38;
            radius = 24000;
          }

          return (
            <Circle
              key={`heatmap-cell-${idx}-${forecastHour}`}
              center={[cell.lat, cell.lon]}
              radius={radius}
              pathOptions={{
                stroke: false,
                fillColor,
                fillOpacity: opacity,
              }}
            />
          );
        })}

      {/* 2. Corridor Weather Radar Circles Along Active Route Checkpoints */}
      {checkpoints.map((cp) => {
        const riskLevel = cp.risk?.level || 'low';
        const precip = (cp.weather?.rain_in_hr || 0) + (cp.weather?.snow_in_hr || 0);
        const windSpeed = cp.weather?.wind_mph || 0;

        let fillColor = '#10B981';
        let fillOpacity = 0.16;
        let radiusMeters = 16000;

        if (riskLevel === 'no_travel') {
          fillColor = '#8B5CF6';
          fillOpacity = 0.50;
          radiusMeters = 32000;
        } else if (riskLevel === 'severe') {
          fillColor = '#EF4444';
          fillOpacity = 0.45;
          radiusMeters = 30000;
        } else if (riskLevel === 'high') {
          fillColor = '#F97316';
          fillOpacity = 0.38;
          radiusMeters = 25000;
        } else if (riskLevel === 'moderate') {
          fillColor = '#F59E0B';
          fillOpacity = 0.30;
          radiusMeters = 20000;
        } else if (precip > 0.05) {
          fillColor = '#00D2FF'; // active precipitation radar band
          fillOpacity = 0.28;
          radiusMeters = 18000;
        } else if (windSpeed > 25) {
          fillColor = '#FFD700'; // wind corridor alert
          fillOpacity = 0.25;
          radiusMeters = 18000;
        }

        return (
          <Circle
            key={`route-radar-point-${activeRoute?.id}-${cp.index}`}
            center={[cp.lat, cp.lon]}
            radius={radiusMeters}
            pathOptions={{
              color: fillColor,
              fillColor,
              fillOpacity,
              weight: riskLevel !== 'low' ? 1.5 : 0.75,
              dashArray: riskLevel !== 'low' ? '4 4' : undefined,
            }}
          />
        );
      })}
    </>
  );
};
