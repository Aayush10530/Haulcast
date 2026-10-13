import React, { useState } from 'react';
import { Box, Paper, useMediaQuery, useTheme } from '@mui/material';
import { useIsMutating } from '@tanstack/react-query';
import { useHealthCheck } from './api/client';
import { AnalyzeResponse, CheckpointDTO } from './api/types';
import { AppHeader } from './components/AppHeader';
import { MobileBottomNav, MobileTab } from './components/MobileBottomNav';
import { TopographyBackground } from './components/TopographyBackground';
import { MapView } from './features/map';
import {
  CheckpointList,
  ResultsPanel,
  RouteProfileCard,
} from './features/results';
import { TripForm } from './features/trip-form';
import { colorTokens, glassPanelSx, shapeTokens } from './theme/tokens';

export const App: React.FC = () => {
  const theme = useTheme();
  const isMobile = useMediaQuery(theme.breakpoints.down('md'));
  const [activeTab, setActiveTab] = useState<MobileTab>('plan');
  const [tripAnalysis, setTripAnalysis] = useState<AnalyzeResponse | null>(null);
  const [selectedRouteId, setSelectedRouteId] = useState<string | null>(null);
  const [focusedCheckpoint, setFocusedCheckpoint] = useState<CheckpointDTO | null>(null);
  const isAnalyzing = useIsMutating({ mutationKey: ['analyzeTrip'] }) > 0;
  const { data, isError } = useHealthCheck();

  const isOnline = !isError && data?.status === 'ok';

  const handleAnalysisSuccess = (analysis: AnalyzeResponse) => {
    setTripAnalysis(analysis);
    setSelectedRouteId(analysis.recommended_route_id);
    setFocusedCheckpoint(null);
    if (isMobile) {
      setActiveTab('routes');
    }
  };

  const handleSelectCheckpoint = (cp: CheckpointDTO) => {
    setFocusedCheckpoint(cp);
    if (isMobile) {
      setActiveTab('map');
    }
  };

  const selectedRoute = tripAnalysis
    ? tripAnalysis.routes.find((r) => r.id === selectedRouteId) ||
      tripAnalysis.routes.find((r) => r.id === tripAnalysis.recommended_route_id) ||
      tripAnalysis.routes[0]
    : null;

  return (
    <Box
      sx={{
        position: 'relative',
        display: 'flex',
        flexDirection: 'column',
        height: '100dvh',
        width: '100vw',
        overflow: 'hidden',
        backgroundColor: colorTokens.canvas,
        p: `${shapeTokens.gap}px`,
        pb: isMobile
          ? `calc(56px + env(safe-area-inset-bottom, 0px) + ${shapeTokens.gap}px)`
          : `${shapeTokens.gap}px`,
        gap: `${shapeTokens.gap}px`,
        boxSizing: 'border-box',
      }}
    >
      <TopographyBackground />

      <AppHeader isOnline={isOnline} />

      {/* Main Responsive Layout: 3 Columns */}
      <Box
        component="main"
        sx={{
          position: 'relative',
          zIndex: 1,
          flex: 1,
          minHeight: 0,
          display: 'grid',
          overflow: 'hidden',
          gap: `${shapeTokens.gap}px`,
          gridTemplateColumns: {
            xs: '1fr',
            md: `${shapeTokens.twoColumnLeftWidth}px 1fr`,
            xl: `${shapeTokens.threeColumnLeftWidth}px 1fr ${shapeTokens.threeColumnRightWidth}px`,
          },
          gridTemplateRows: {
            xs: '1fr',
            md: 'minmax(0, 1fr) minmax(0, 1fr)',
            xl: '1fr',
          },
          gridTemplateAreas: {
            xs:
              activeTab === 'plan'
                ? '"form"'
                : activeTab === 'map'
                  ? '"map"'
                  : '"results"',
            md: '"form map" "results map"',
            xl: '"form map results"',
          },
        }}
      >
        {/* Column 1: Trip Form & Elevation Profile */}
        <Box
          component="aside"
          aria-label="Trip form"
          data-testid="region-trip-form"
          hidden={isMobile ? activeTab !== 'plan' : false}
          sx={{
            gridArea: 'form',
            display: isMobile ? (activeTab === 'plan' ? 'flex' : 'none') : 'flex',
            flexDirection: 'column',
            minHeight: 0,
            overflowY: 'auto',
            gap: `${shapeTokens.gap}px`,
            p: 0,
            backgroundColor: 'transparent',
            border: 'none',
          }}
        >
          <Paper variant="outlined" sx={{ ...glassPanelSx, p: 2, flexShrink: 0 }}>
            <TripForm onSuccess={handleAnalysisSuccess} />
          </Paper>

          {tripAnalysis && selectedRoute && (
            <RouteProfileCard route={selectedRoute} />
          )}
        </Box>

        {/* Column 2: Map & Checkpoints Analysis */}
        <Box
          component="section"
          aria-label="Map"
          data-testid="region-map"
          hidden={isMobile ? activeTab !== 'map' : false}
          sx={{
            gridArea: 'map',
            display: isMobile ? (activeTab === 'map' ? 'flex' : 'none') : 'flex',
            flexDirection: 'column',
            minHeight: 0,
            gap: `${shapeTokens.gap}px`,
            p: 0,
            backgroundColor: 'transparent',
            border: 'none',
            overflow: 'hidden',
          }}
        >
          <Paper
            variant="outlined"
            sx={{
              ...glassPanelSx,
              flex: 1,
              minHeight: { xs: 260, md: 300 },
              overflow: 'hidden',
              position: 'relative',
            }}
          >
            <MapView
              analysis={tripAnalysis}
              selectedRouteId={selectedRouteId}
              onSelectRoute={setSelectedRouteId}
              focusedCheckpoint={focusedCheckpoint}
              isVisible={!isMobile || activeTab === 'map'}
            />
          </Paper>

          {tripAnalysis && selectedRoute && !isMobile && (
            <Paper
              variant="outlined"
              sx={{
                ...glassPanelSx,
                height: { md: 240, xl: 270 },
                flexShrink: 0,
                p: 2,
                overflowY: 'auto',
                boxSizing: 'border-box',
              }}
            >
              <CheckpointList
                checkpoints={selectedRoute.checkpoints || []}
                routeLabel={selectedRoute.label}
                originLabel={tripAnalysis?.request?.origin?.label}
                destinationLabel={tripAnalysis?.request?.destination?.label}
                onSelectCheckpoint={handleSelectCheckpoint}
              />
            </Paper>
          )}
        </Box>

        {/* Column 3: Route Options & Results */}
        <Box
          component="aside"
          aria-label="Results"
          data-testid="region-results"
          hidden={isMobile ? activeTab !== 'routes' : false}
          sx={{
            gridArea: 'results',
            display: isMobile ? (activeTab === 'routes' ? 'flex' : 'none') : 'flex',
            flexDirection: 'column',
            minHeight: 0,
            overflowY: 'auto',
            gap: `${shapeTokens.gap}px`,
            p: 0,
            backgroundColor: 'transparent',
            border: 'none',
          }}
        >
          <ResultsPanel
            analysis={tripAnalysis}
            isLoading={isAnalyzing}
            selectedRouteId={selectedRouteId}
            onSelectRoute={setSelectedRouteId}
            onSelectCheckpoint={handleSelectCheckpoint}
            hideCheckpoints={!isMobile}
          />
        </Box>
      </Box>

      {/* Mobile bottom tab bar */}
      {isMobile && (
        <MobileBottomNav activeTab={activeTab} onChange={setActiveTab} />
      )}
    </Box>
  );
};
