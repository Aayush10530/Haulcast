import React from 'react';
import { Circle, SVGOverlay } from 'react-leaflet';
import L from 'leaflet';
import { RouteDTO } from '../../api/types';
import { riskColors } from '../../theme/riskColors';

export interface WeatherRadarLayerProps {
  routes?: RouteDTO[];
  selectedRouteId?: string | null;
  forecastHour?: number;
  isVisible?: boolean;
}

export const WeatherRadarLayer: React.FC<WeatherRadarLayerProps> = ({
  routes = [],
  selectedRouteId,
  forecastHour = 0,
  isVisible = true,
}) => {
  // Calculate corridor bounds from routes, or fallback to US Midwest/Plains corridor
  const bounds = React.useMemo<L.LatLngBoundsExpression>(() => {
    if (!routes || routes.length === 0) {
      return [
        [32.5, -106.0],
        [44.5, -85.0],
      ];
    }

    let minLat = 90;
    let maxLat = -90;
    let minLon = 180;
    let maxLon = -180;

    for (const r of routes) {
      const poly = r.geometry || [];
      for (const pt of poly) {
        const [lat, lon] = pt;
        if (lat < minLat) minLat = lat;
        if (lat > maxLat) maxLat = lat;
        if (lon < minLon) minLon = lon;
        if (lon > maxLon) maxLon = lon;
      }
    }

    // Add padding around routes for radar storm clouds
    return [
      [Math.max(24, minLat - 2.5), Math.max(-125, minLon - 2.5)],
      [Math.min(50, maxLat + 2.5), Math.min(-65, maxLon + 2.5)],
    ];
  }, [routes]);

  if (!isVisible) {
    return null;
  }

  // Selected route checkpoints for corridor risk heat zones
  const activeRoute =
    routes.find((r) => r.id === selectedRouteId) || routes[0] || null;
  const checkpoints = activeRoute?.checkpoints || [];

  // Hourly displacement simulation for radar storm animation (drifts east-northeast)
  const driftX = (forecastHour * 1.5) % 100;
  const driftY = (forecastHour * 0.8) % 60;

  return (
    <>
      {/* 1. Doppler Weather Radar Storm Clusters Overlay */}
      <SVGOverlay
        bounds={bounds}
        attributes={{
          style: 'pointer-events: none; mix-blend-mode: screen; opacity: 0.85;',
        }}
      >
        <svg viewBox="0 0 600 400" width="100%" height="100%">
          <defs>
            <filter id="radarBlur" x="-20%" y="-20%" width="140%" height="140%">
              <feGaussianBlur stdDeviation="6" />
            </filter>

            {/* Intense Supercell Radar Gradient (Magenta core -> Red -> Orange -> Yellow -> Green) */}
            <radialGradient id="stormGradPrimary" cx="50%" cy="50%" r="50%">
              <stop offset="0%" stopColor="#D80032" stopOpacity="0.95" />
              <stop offset="25%" stopColor="#FF1E00" stopOpacity="0.9" />
              <stop offset="45%" stopColor="#FF8C00" stopOpacity="0.8" />
              <stop offset="65%" stopColor="#FFD700" stopOpacity="0.7" />
              <stop offset="85%" stopColor="#00E676" stopOpacity="0.5" />
              <stop offset="100%" stopColor="#00E676" stopOpacity="0" />
            </radialGradient>

            {/* Secondary Squall Line Gradient */}
            <radialGradient id="stormGradSecondary" cx="50%" cy="50%" r="50%">
              <stop offset="0%" stopColor="#FF1E00" stopOpacity="0.9" />
              <stop offset="35%" stopColor="#FF8C00" stopOpacity="0.75" />
              <stop offset="65%" stopColor="#FFD700" stopOpacity="0.6" />
              <stop offset="85%" stopColor="#00E676" stopOpacity="0.45" />
              <stop offset="100%" stopColor="#00E676" stopOpacity="0" />
            </radialGradient>

            {/* Moderate Precipitation Rain Band */}
            <radialGradient id="rainBandGrad" cx="50%" cy="50%" r="50%">
              <stop offset="0%" stopColor="#FFD700" stopOpacity="0.75" />
              <stop offset="50%" stopColor="#00E676" stopOpacity="0.5" />
              <stop offset="100%" stopColor="#00D2FF" stopOpacity="0" />
            </radialGradient>
          </defs>

          <g filter="url(#radarBlur)">
            {/* Main Convective Storm System (Central Plains / Corridor) */}
            <ellipse
              cx={280 + driftX}
              cy={190 - driftY}
              rx={95}
              ry={65}
              fill="url(#stormGradPrimary)"
              transform={`rotate(-25 ${280 + driftX} ${190 - driftY})`}
            />

            {/* Intense Core Cell */}
            <circle
              cx={295 + driftX}
              cy={180 - driftY}
              r={48}
              fill="url(#stormGradPrimary)"
            />

            {/* Trailing Squall / Frontal Line */}
            <ellipse
              cx={210 + driftX}
              cy={240 - driftY}
              rx={110}
              ry={45}
              fill="url(#stormGradSecondary)"
              transform={`rotate(35 ${210 + driftX} ${240 - driftY})`}
            />

            {/* Forward Precipitation Arc */}
            <ellipse
              cx={360 + driftX}
              cy={150 - driftY}
              rx={80}
              ry={55}
              fill="url(#rainBandGrad)"
              transform={`rotate(-15 ${360 + driftX} ${150 - driftY})`}
            />

            {/* Scattered Convective Showers */}
            <circle cx={160 + driftX} cy={280 - driftY} r={35} fill="url(#rainBandGrad)" />
            <circle cx={420 + driftX} cy={120 - driftY} r={40} fill="url(#rainBandGrad)" />
          </g>
        </svg>
      </SVGOverlay>

      {/* 2. Corridor Risk Heat Zones along Route Checkpoints */}
      {checkpoints.map((cp) => {
        if (!cp.risk || cp.risk.level === 'low') {
          return null;
        }

        const riskSpec = riskColors[cp.risk.level];
        const radiusMeters =
          cp.risk.level === 'severe' || cp.risk.level === 'no_travel'
            ? 38000
            : cp.risk.level === 'high'
            ? 28000
            : 20000;

        return (
          <Circle
            key={`heat-zone-${activeRoute?.id}-${cp.index}`}
            center={[cp.lat, cp.lon]}
            radius={radiusMeters}
            pathOptions={{
              color: riskSpec.background,
              fillColor: riskSpec.background,
              fillOpacity: cp.risk.level === 'severe' ? 0.38 : 0.28,
              weight: 1.5,
              dashArray: '4 4',
            }}
          />
        );
      })}
    </>
  );
};
