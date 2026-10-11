import React, { useMemo } from 'react';
import { Marker, Polyline } from 'react-leaflet';
import L, { LatLngExpression } from 'leaflet';
import { RouteDTO } from '../../api/types';
import { routeDashArrays, routeLineColors } from '../../theme/tokens';
import { formatDuration } from '../../utils/format';

/**
 * Calculates the vertex index for placing a route label pill.
 * Places label at floor(n * (0.30 + 0.20 * i)) of the display geometry for route order index i
 * (A: 30%, B: 50%, C: 70%), so shared stretches do not collide.
 */
export function getRouteLabelVertexIndex(n: number, i: number): number {
  if (n <= 0) return 0;
  const idx = Math.floor(n * (0.30 + 0.20 * i));
  return Math.max(0, Math.min(idx, n - 1));
}

export interface RouteLayerProps {
  routes: RouteDTO[];
  selectedRouteId: string | null;
  onSelectRoute: (routeId: string) => void;
}

interface SingleRouteItemProps {
  route: RouteDTO;
  orderIndex: number;
  isSelected: boolean;
  styleType: 'recommended' | 'second' | 'third';
  onSelect: (routeId: string) => void;
}

const SingleRouteItem: React.FC<SingleRouteItemProps> = React.memo(
  ({ route, orderIndex, isSelected, styleType, onSelect }) => {
    const positions = useMemo<LatLngExpression[]>(
      () => route.geometry.map(([lat, lon]) => [lat, lon] as [number, number]),
      [route.geometry],
    );

    const letter = (
      route.label?.replace(/Route\s*/i, '') ||
      route.id.replace('route_', '').toUpperCase()
    ).slice(0, 1);

    const durationText = formatDuration(route.duration_seconds);
    const labelText = `${letter} · ${durationText}`;

    const labelIdx = getRouteLabelVertexIndex(route.geometry.length, orderIndex);
    const labelPoint: LatLngExpression = route.geometry[labelIdx] || [0, 0];

    const labelIcon = useMemo(() => {
      return L.divIcon({
        className: 'route-label-pill-container',
        html: `<div class="route-label-pill ${isSelected ? 'selected' : ''}" data-testid="route-label-${route.id}">${labelText}</div>`,
        iconSize: [80, 24],
        iconAnchor: [40, 12],
      });
    }, [isSelected, labelText, route.id]);

    const strokeColor = routeLineColors[styleType];
    const dashArray = routeDashArrays[styleType];
    const weight = isSelected ? 7 : 4;
    const casingWeight = weight + 2;
    const opacity = isSelected ? 1.0 : 0.8;

    const eventHandlers = useMemo(
      () => ({
        click: () => onSelect(route.id),
      }),
      [onSelect, route.id],
    );

    return (
      <React.Fragment key={route.id}>
        {/* Casing polyline: canvas color, 2 px wider */}
        <Polyline
          positions={positions}
          pathOptions={{
            color: routeLineColors.casing,
            weight: casingWeight,
            opacity,
            lineCap: 'round',
            lineJoin: 'round',
          }}
          eventHandlers={eventHandlers}
        />

        {/* Colored route line */}
        <Polyline
          positions={positions}
          pathOptions={{
            color: strokeColor,
            weight,
            opacity,
            dashArray: dashArray || undefined,
            lineCap: 'round',
            lineJoin: 'round',
          }}
          eventHandlers={eventHandlers}
        />

        {/* Route label pill */}
        <Marker
          position={labelPoint}
          icon={labelIcon}
          eventHandlers={eventHandlers}
        />
      </React.Fragment>
    );
  },
);

SingleRouteItem.displayName = 'SingleRouteItem';

export const RouteLayer: React.FC<RouteLayerProps> = ({
  routes,
  selectedRouteId,
  onSelectRoute,
}) => {
  return (
    <>
      {routes.map((route, index) => {
        const isSelected = route.id === selectedRouteId;
        const isRecommended =
          route.tags?.includes('recommended') || route.rank === 1;

        let styleType: 'recommended' | 'second' | 'third' = 'third';
        if (isRecommended) {
          styleType = 'recommended';
        } else if (route.rank === 2 || index === 1) {
          styleType = 'second';
        }

        return (
          <SingleRouteItem
            key={route.id}
            route={route}
            orderIndex={index}
            isSelected={isSelected}
            styleType={styleType}
            onSelect={onSelectRoute}
          />
        );
      })}
    </>
  );
};
