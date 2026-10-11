import React from 'react';
import { Box, Typography } from '@mui/material';
import { MapContainer, TileLayer, ZoomControl } from 'react-leaflet';
import { AnalyzeResponse, CheckpointDTO } from '../../api/types';
import { colorTokens, shapeTokens, typographyTokens } from '../../theme/tokens';
import { CheckpointLayer } from './CheckpointLayer';
import { MapController } from './MapController';
import { MapLegend } from './MapLegend';
import { RouteLayer } from './RouteLayer';
import './leafletDark.css';

export interface MapViewProps {
  analysis: AnalyzeResponse | null;
  selectedRouteId: string | null;
  onSelectRoute: (routeId: string) => void;
  focusedCheckpoint?: CheckpointDTO | null;
  isVisible?: boolean;
}

const OSM_TILE_URL = 'https://tile.openstreetmap.org/{z}/{x}/{y}.png';
const OSM_ATTRIBUTION =
  '&copy; <a href="https://www.openstreetmap.org/copyright">OpenStreetMap</a> contributors';

export const MapView: React.FC<MapViewProps> = ({
  analysis,
  selectedRouteId,
  onSelectRoute,
  focusedCheckpoint,
  isVisible = true,
}) => {
  const routes = analysis?.routes || [];
  const hasRoutes = routes.length > 0;

  return (
    <Box
      data-testid="map-view-container"
      sx={{
        width: '100%',
        height: '100%',
        position: 'relative',
        overflow: 'hidden',
        backgroundColor: colorTokens.canvas,
      }}
    >
      <MapContainer
        preferCanvas={true}
        center={[39.5, -98.35]}
        zoom={4}
        zoomControl={false}
        className="haulcast-map-container"
        style={{ width: '100%', height: '100%' }}
      >
        <TileLayer
          url={OSM_TILE_URL}
          attribution={OSM_ATTRIBUTION}
          maxZoom={19}
          className="osm-dark-tiles"
        />

        <ZoomControl position="topright" />

        {hasRoutes && (
          <>
            <RouteLayer
              routes={routes}
              selectedRouteId={selectedRouteId}
              onSelectRoute={onSelectRoute}
            />

            <CheckpointLayer
              routes={routes}
              selectedRouteId={selectedRouteId}
              origin={analysis?.request.origin}
              destination={analysis?.request.destination}
              focusedCheckpoint={focusedCheckpoint}
            />

            <MapController
              routes={routes}
              focusedCheckpoint={focusedCheckpoint}
              isVisible={isVisible}
            />
          </>
        )}
      </MapContainer>

      {/* Map Legend docked bottom-left */}
      <MapLegend />

      {/* Empty State Hint */}
      {!hasRoutes && (
        <Box
          data-testid="map-empty-hint"
          sx={{
            position: 'absolute',
            top: 16,
            left: '50%',
            transform: 'translateX(-50%)',
            zIndex: 1000,
            backgroundColor: 'rgba(17, 30, 36, 0.92)',
            border: `1px solid ${colorTokens.border}`,
            borderRadius: `${shapeTokens.borderRadius}px`,
            px: 2,
            py: 0.75,
            pointerEvents: 'none',
          }}
        >
          <Typography
            sx={{
              fontFamily: typographyTokens.fontFamilyUi,
              fontSize: '0.8125rem',
              color: colorTokens.textMuted,
            }}
          >
            Plan a trip to view routes and weather risks
          </Typography>
        </Box>
      )}
    </Box>
  );
};
