import React, { useEffect, useRef } from 'react';
import { CircleMarker, Popup, Tooltip } from 'react-leaflet';
import L from 'leaflet';
import { CheckpointDTO, PlaceDTO, RouteDTO } from '../../api/types';
import { riskColors } from '../../theme/riskColors';
import { colorTokens } from '../../theme/tokens';
import { CheckpointPopup } from './CheckpointPopup';

export interface CheckpointLayerProps {
  routes: RouteDTO[];
  selectedRouteId: string | null;
  origin?: PlaceDTO;
  destination?: PlaceDTO;
  focusedCheckpoint?: CheckpointDTO | null;
}

export const CheckpointLayer: React.FC<CheckpointLayerProps> = ({
  routes,
  selectedRouteId,
  origin,
  destination,
  focusedCheckpoint,
}) => {
  const markerRefs = useRef<Map<string, L.CircleMarker>>(new Map());

  // When focusedCheckpoint changes, open its popup
  useEffect(() => {
    if (!focusedCheckpoint) return;
    const key = `${selectedRouteId}-${focusedCheckpoint.index}`;
    const marker = markerRefs.current.get(key);
    if (marker) {
      marker.openPopup();
    }
  }, [focusedCheckpoint, selectedRouteId]);

  // Render non-selected routes first, selected route last so selected checkpoints sit on top
  const sortedRoutes = [...routes].sort((a, b) => {
    if (a.id === selectedRouteId) return 1;
    if (b.id === selectedRouteId) return -1;
    return 0;
  });

  return (
    <>
      {/* Origin Marker */}
      {origin && (
        <CircleMarker
          center={[origin.lat, origin.lon]}
          radius={6}
          pathOptions={{
            fillColor: colorTokens.brand,
            fillOpacity: 1,
            color: colorTokens.canvas,
            weight: 2,
          }}
        >
          <Tooltip direction="top" offset={[0, -8]} className="place-tooltip">
            {origin.label}
          </Tooltip>
        </CircleMarker>
      )}

      {/* Destination Marker */}
      {destination && (
        <CircleMarker
          center={[destination.lat, destination.lon]}
          radius={6}
          pathOptions={{
            fillColor: '#E5484D',
            fillOpacity: 1,
            color: colorTokens.canvas,
            weight: 2,
          }}
        >
          <Tooltip direction="top" offset={[0, -8]} className="place-tooltip">
            {destination.label}
          </Tooltip>
        </CircleMarker>
      )}

      {/* Checkpoints */}
      {sortedRoutes.map((route) => {
        const isSelected = route.id === selectedRouteId;
        const radius = isSelected ? 5 : 3;

        return (route.checkpoints || []).map((cp) => {
          const key = `${route.id}-${cp.index}`;
          const riskSpec = cp.risk ? riskColors[cp.risk.level] : null;
          const fillColor = riskSpec ? riskSpec.background : '#8FA4AB';

          return (
            <CircleMarker
              key={key}
              center={[cp.lat, cp.lon]}
              radius={radius}
              ref={(ref) => {
                if (ref) {
                  markerRefs.current.set(key, ref);
                } else {
                  markerRefs.current.delete(key);
                }
              }}
              pathOptions={{
                fillColor,
                fillOpacity: 1,
                color: colorTokens.canvas,
                weight: 1.5,
              }}
            >
              <Popup>
                <CheckpointPopup checkpoint={cp} />
              </Popup>
            </CircleMarker>
          );
        });
      })}
    </>
  );
};
