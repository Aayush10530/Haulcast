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

const ESRI_SATELLITE_URL =
  'https://server.arcgisonline.com/ArcGIS/rest/services/World_Imagery/MapServer/tile/{z}/{y}/{x}';
const ESRI_ATTRIBUTION =
  'Tiles &copy; Esri &mdash; Source: Esri, i-cubed, USDA, USGS, AEX, GeoEye, Getmapping, Aerogrid, IGN, IGP, UPR-EGP, and the GIS User Community';

export const MapView: React.FC<MapViewProps> = ({
  analysis,
  selectedRouteId,
  onSelectRoute,
  focusedCheckpoint,
  isVisible = true,
}) => {
  const [activeLayer, setActiveLayer] = React.useState<'radar' | 'satellite' | 'terrain'>('radar');
  const [forecastHour, setForecastHour] = React.useState<number>(0);

  const routes = analysis?.routes || [];
  const hasRoutes = routes.length > 0;

  const currentTileUrl = activeLayer === 'satellite' ? ESRI_SATELLITE_URL : OSM_TILE_URL;
  const currentAttribution = activeLayer === 'satellite' ? ESRI_ATTRIBUTION : OSM_ATTRIBUTION;

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
      {/* Top Map Control Bar: Weather Forecast (0-48h) + Layer Switchers */}
      <Box
        data-testid="map-top-bar"
        sx={{
          position: 'absolute',
          top: 12,
          left: 12,
          right: 12,
          zIndex: 1000,
          backgroundColor: 'rgba(11, 27, 43, 0.92)',
          backdropFilter: 'blur(8px)',
          border: `1px solid ${colorTokens.border}`,
          borderRadius: `${shapeTokens.borderRadius}px`,
          px: 2,
          py: 0.75,
          display: 'flex',
          alignItems: 'center',
          justifyContent: 'space-between',
          gap: 2,
          flexWrap: 'wrap',
          boxShadow: '0 4px 16px rgba(0,0,0,0.3)',
        }}
      >
        {/* Forecast Scrubber */}
        <Box sx={{ display: 'flex', alignItems: 'center', gap: 1.5, flex: 1, minWidth: 240 }}>
          <Typography sx={{ fontSize: '12px', fontWeight: 600, color: colorTokens.text, whiteSpace: 'nowrap' }}>
            Weather Forecast (0 – 48 hours)
          </Typography>
          <Typography sx={{ fontSize: '11px', color: colorTokens.brand, fontWeight: 700, minWidth: 24 }}>
            {forecastHour}h
          </Typography>
          <Box
            component="input"
            type="range"
            min={0}
            max={48}
            step={1}
            value={forecastHour}
            onChange={(e: React.ChangeEvent<HTMLInputElement>) => setForecastHour(parseInt(e.target.value, 10))}
            data-testid="forecast-hour-slider"
            sx={{
              flex: 1,
              accentColor: '#00D2FF',
              cursor: 'pointer',
              height: 4,
            }}
          />
          <Typography sx={{ fontSize: '11px', color: colorTokens.textMuted }}>
            48h
          </Typography>
        </Box>

        {/* Layer Toggles */}
        <Box sx={{ display: 'flex', alignItems: 'center', gap: 0.75 }}>
          {(['radar', 'satellite', 'terrain'] as const).map((layer) => {
            const isSelected = activeLayer === layer;
            return (
              <Box
                key={layer}
                component="button"
                type="button"
                onClick={() => setActiveLayer(layer)}
                data-testid={`layer-btn-${layer}`}
                sx={{
                  backgroundColor: isSelected ? '#00D2FF' : 'transparent',
                  color: isSelected ? '#07171C' : colorTokens.textMuted,
                  border: isSelected ? '1px solid #00D2FF' : `1px solid ${colorTokens.border}`,
                  borderRadius: '16px',
                  px: 1.5,
                  py: 0.35,
                  fontSize: '11px',
                  fontWeight: 600,
                  cursor: 'pointer',
                  textTransform: 'capitalize',
                  transition: 'all 120ms ease',
                  '&:hover': {
                    color: isSelected ? '#07171C' : colorTokens.text,
                    borderColor: isSelected ? '#00D2FF' : colorTokens.brand,
                  },
                }}
              >
                {layer}
              </Box>
            );
          })}
        </Box>
      </Box>

      <MapContainer
        preferCanvas={true}
        center={[39.5, -98.35]}
        zoom={4}
        zoomControl={false}
        className="haulcast-map-container"
        style={{ width: '100%', height: '100%' }}
      >
        <TileLayer
          key={activeLayer}
          url={currentTileUrl}
          attribution={currentAttribution}
          maxZoom={19}
          className={activeLayer === 'satellite' ? '' : 'osm-dark-tiles'}
        />

        <ZoomControl position="bottomright" />

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
            top: 60,
            left: '50%',
            transform: 'translateX(-50%)',
            zIndex: 1000,
            backgroundColor: 'rgba(11, 27, 43, 0.92)',
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
