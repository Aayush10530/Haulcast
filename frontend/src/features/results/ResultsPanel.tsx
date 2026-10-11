import React from 'react';
import { Alert, Box, Button, Paper, Skeleton, Typography } from '@mui/material';
import { AnalyzeResponse, CheckpointDTO } from '../../api/types';
import { colorTokens, shapeTokens, typographyTokens } from '../../theme/tokens';
import { CheckpointList } from './CheckpointList';
import { RecommendationBanner } from './RecommendationBanner';
import { RouteComparisonCard } from './RouteComparisonCard';
import { RouteList } from './RouteList';
import { WarningsList } from './WarningsList';

export interface ResultsPanelProps {
  analysis: AnalyzeResponse | null;
  isLoading?: boolean;
  error?: string | null;
  onRetry?: () => void;
  onTryExample?: () => void;
  selectedRouteId: string | null;
  onSelectRoute: (routeId: string) => void;
  onSelectCheckpoint?: (checkpoint: CheckpointDTO) => void;
  hideCheckpoints?: boolean;
}

export const ResultsPanel: React.FC<ResultsPanelProps> = ({
  analysis,
  isLoading = false,
  error = null,
  onRetry,
  onTryExample,
  selectedRouteId,
  onSelectRoute,
  onSelectCheckpoint,
  hideCheckpoints = false,
}) => {
  // 1. Loading Skeleton State
  if (isLoading) {
    return (
      <Box data-testid="results-loading-skeletons" sx={{ width: '100%' }}>
        <Skeleton variant="text" width={160} height={32} sx={{ mb: 2 }} />
        {/* Recommendation banner skeleton */}
        <Skeleton
          variant="rectangular"
          height={68}
          sx={{ borderRadius: `${shapeTokens.panelBorderRadius}px`, mb: 2.5, backgroundColor: colorTokens.surfaceRaised }}
        />
        {/* Route card skeletons matching final card layout */}
        {[1, 2, 3].map((key) => (
          <Paper
            key={key}
            variant="outlined"
            sx={{
              p: 2,
              mb: 2,
              borderRadius: `${shapeTokens.panelBorderRadius}px`,
              backgroundColor: colorTokens.surface,
              borderColor: colorTokens.border,
            }}
          >
            <Box sx={{ display: 'flex', justifyContent: 'space-between', mb: 1.5 }}>
              <Box sx={{ display: 'flex', gap: 1, alignItems: 'center' }}>
                <Skeleton variant="rectangular" width={28} height={28} sx={{ borderRadius: `${shapeTokens.borderRadius}px` }} />
                <Skeleton variant="rectangular" width={80} height={22} sx={{ borderRadius: `${shapeTokens.borderRadius}px` }} />
              </Box>
              <Skeleton variant="circular" width={56} height={56} />
            </Box>
            <Skeleton variant="text" width={140} height={24} sx={{ mb: 1 }} />
            <Skeleton variant="text" width={200} height={18} sx={{ mb: 1.5 }} />
            <Skeleton variant="rectangular" height={8} sx={{ borderRadius: '4px', mb: 1 }} />
            <Skeleton variant="text" width={120} height={16} />
          </Paper>
        ))}
      </Box>
    );
  }

  // 2. Error State with Retry
  if (error) {
    return (
      <Box data-testid="results-error" sx={{ width: '100%' }}>
        <Alert
          variant="outlined"
          severity="error"
          data-testid="results-error-alert"
          action={
            onRetry && (
              <Button
                color="inherit"
                size="small"
                onClick={onRetry}
                data-testid="results-retry-button"
              >
                Retry
              </Button>
            )
          }
          sx={{ mb: 2 }}
        >
          {error}
        </Alert>
      </Box>
    );
  }

  // 3. Idle / Empty State
  if (!analysis) {
    return (
      <Paper
        variant="outlined"
        data-testid="results-idle"
        sx={{
          p: 3,
          backgroundColor: colorTokens.surface,
          borderColor: colorTokens.border,
          borderRadius: `${shapeTokens.panelBorderRadius}px`,
          textAlign: 'center',
        }}
      >
        <Typography
          variant="h6"
          sx={{
            fontFamily: typographyTokens.fontFamilyUi,
            fontWeight: 700,
            fontSize: '1rem',
            color: colorTokens.text,
            mb: 1,
          }}
        >
          Route options
        </Typography>
        <Typography
          sx={{
            fontFamily: typographyTokens.fontFamilyUi,
            fontSize: '0.875rem',
            color: colorTokens.textMuted,
            mb: 2,
            lineHeight: 1.5,
          }}
        >
          Enter trip details and click Generate routes to see weather-aware options.
        </Typography>
        {onTryExample && (
          <Button
            variant="text"
            onClick={onTryExample}
            data-testid="results-idle-example-button"
            sx={{
              color: colorTokens.brand,
              fontFamily: typographyTokens.fontFamilyUi,
              fontSize: '0.8125rem',
              fontWeight: 600,
              textTransform: 'none',
              '&:hover': {
                backgroundColor: 'transparent',
                textDecoration: 'underline',
              },
            }}
          >
            Or try an example trip
          </Button>
        )}
      </Paper>
    );
  }

  // 4. Success Results View
  const selectedRoute =
    analysis.routes.find((r) => r.id === selectedRouteId) ||
    analysis.routes.find((r) => r.id === analysis.recommended_route_id) ||
    analysis.routes[0];

  return (
    <Box data-testid="results-panel" sx={{ width: '100%' }}>
      {/* Title */}
      <Typography
        variant="h6"
        data-testid="results-title"
        sx={{
          fontFamily: typographyTokens.fontFamilyUi,
          fontWeight: 700,
          fontSize: '1.125rem',
          color: colorTokens.text,
          mb: 2,
        }}
      >
        Route options ({analysis.routes.length})
      </Typography>

      {/* Recommendation Banner */}
      {analysis.recommendation && (
        <RecommendationBanner recommendation={analysis.recommendation} />
      )}

      {/* Warnings List */}
      {analysis.warnings && analysis.warnings.length > 0 && (
        <WarningsList warnings={analysis.warnings} />
      )}

      {/* Route Cards */}
      <RouteList
        routes={analysis.routes}
        selectedRouteId={selectedRoute?.id || null}
        recommendedRouteId={analysis.recommended_route_id}
        departureLocal={analysis.request.departure_local}
        originTimezone={analysis.request.origin_timezone}
        onSelectRoute={onSelectRoute}
      />

      {/* Route Comparison Chart & Metrics Table */}
      <Box sx={{ mt: 2 }}>
        <RouteComparisonCard routes={analysis.routes} />
      </Box>

      {/* Checkpoint List for the selected route */}
      {!hideCheckpoints && selectedRoute && (
        <CheckpointList
          checkpoints={selectedRoute.checkpoints || []}
          routeLabel={selectedRoute.label}
          onSelectCheckpoint={onSelectCheckpoint}
        />
      )}
    </Box>
  );
};
