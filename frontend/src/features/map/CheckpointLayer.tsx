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

export function getCheckpointMarkerColor(
  risk?: CheckpointDTO['risk'] | null,
): string {
  if (!risk || !risk.level || !riskColors[risk.level]) {
    return colorTokens.textMuted;
  }
  return riskColors[risk.level].background;
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
      {/* Origin Marker (Green Pin per mockup) */}
      {origin && (
        <CircleMarker
          center={[origin.lat, origin.lon]}
          radius={8}
          pathOptions={{
            fillColor: '#00E676',
            fillOpacity: 1,
            color: '#FFFFFF',
            weight: 2.5,
          }}
        >
          <Tooltip direction="top" permanent offset={[0, -10]} className="place-tooltip">
            {origin.label}
          </Tooltip>
        </CircleMarker>
      )}

      {/* Destination Marker (Red Pin per mockup) */}
      {destination && (
        <CircleMarker
          center={[destination.lat, destination.lon]}
          radius={8}
          pathOptions={{
            fillColor: '#E5484D',
            fillOpacity: 1,
            color: '#FFFFFF',
            weight: 2.5,
          }}
        >
          <Tooltip direction="top" permanent offset={[0, -10]} className="place-tooltip">
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
          const fillColor = getCheckpointMarkerColor(cp.risk);

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
