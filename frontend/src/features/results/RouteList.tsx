import React from 'react';
import { Box } from '@mui/material';
import { RouteDTO } from '../../api/types';
import { RouteCard } from './RouteCard';

export interface RouteListProps {
  routes: RouteDTO[];
  selectedRouteId?: string | null;
  recommendedRouteId?: string | null;
  departureLocal?: string;
  originTimezone?: string;
  onSelectRoute?: (routeId: string) => void;
}

export const RouteList: React.FC<RouteListProps> = ({
  routes,
  selectedRouteId,
  recommendedRouteId,
  departureLocal,
  originTimezone,
  onSelectRoute,
}) => {
  if (!routes || routes.length === 0) return null;

  return (
    <Box
      data-testid="route-list"
      sx={{ display: 'flex', flexDirection: 'column', gap: 2, mb: 3 }}
    >
      {routes.map((route) => (
        <RouteCard
          key={route.id}
          route={route}
          isSelected={selectedRouteId === route.id}
          isRecommended={recommendedRouteId === route.id}
          departureLocal={departureLocal}
          originTimezone={originTimezone}
          onSelect={onSelectRoute}
        />
      ))}
    </Box>
  );
};
