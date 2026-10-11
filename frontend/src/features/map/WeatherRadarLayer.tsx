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
          if (score === null || score === undefined || score <= 0.05) {
            return null;
          }

          let fillColor = '#3FA66B'; // green / low risk
          let opacity = 0.22;
          let radius = 14000;

          if (score >= 0.75) {
            fillColor = '#E5484D'; // severe red
            opacity = 0.55;
            radius = 26000;
          } else if (score >= 0.50) {
            fillColor = '#E8872B'; // high orange
            opacity = 0.45;
            radius = 22000;
          } else if (score >= 0.25) {
            fillColor = '#E2C044'; // moderate yellow
            opacity = 0.35;
            radius = 18000;
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

        let fillColor = '#3FA66B';
        let fillOpacity = 0.18;
        let radiusMeters = 15000;

        if (riskLevel === 'severe' || riskLevel === 'no_travel') {
          fillColor = '#E5484D';
          fillOpacity = 0.45;
          radiusMeters = 32000;
        } else if (riskLevel === 'high') {
          fillColor = '#E8872B';
          fillOpacity = 0.38;
          radiusMeters = 25000;
        } else if (riskLevel === 'moderate') {
          fillColor = '#E2C044';
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
              weight: 1,
              dashArray: riskLevel !== 'low' ? '4 4' : undefined,
            }}
          />
        );
      })}
    </>
  );
};
