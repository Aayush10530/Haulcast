import React from 'react';
import { Circle } from 'react-leaflet';
import { RouteDTO } from '../../api/types';
import { riskColors, RiskLevelKey } from '../../theme/riskColors';

export interface WeatherRadarLayerProps {
  routes?: RouteDTO[];
  selectedRouteId?: string | null;
  isVisible?: boolean;
}

export const WeatherRadarLayer: React.FC<WeatherRadarLayerProps> = ({
  routes = [],
  selectedRouteId,
  isVisible = true,
}) => {
  if (!isVisible || !routes || routes.length === 0) {
    return null;
  }

  const activeRoute =
    routes.find((r) => r.id === selectedRouteId) || routes[0] || null;
  const checkpoints = activeRoute?.checkpoints || [];

  return (
    <>
      {checkpoints.map((cp) => {
        if (!cp.risk || !cp.risk.level || !riskColors[cp.risk.level as RiskLevelKey]) {
          return null;
        }

        const riskLevel = cp.risk.level as RiskLevelKey;
        const colorSpec = riskColors[riskLevel];
        const fillColor = colorSpec.background;

        let fillOpacity = 0.16;
        let radiusMeters = 16000;

        if (riskLevel === 'no_travel') {
          fillOpacity = 0.50;
          radiusMeters = 32000;
        } else if (riskLevel === 'severe') {
          fillOpacity = 0.45;
          radiusMeters = 30000;
        } else if (riskLevel === 'high') {
          fillOpacity = 0.38;
          radiusMeters = 25000;
        } else if (riskLevel === 'moderate') {
          fillOpacity = 0.30;
          radiusMeters = 20000;
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
