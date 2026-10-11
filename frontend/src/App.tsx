import React, { useState } from 'react';
import {
  BottomNavigation,
  BottomNavigationAction,
  Box,
  Typography,
} from '@mui/material';
import { useHealthCheck } from './api/client';
import { colorTokens, shapeTokens, typographyTokens } from './theme/tokens';

type MobileTab = 'plan' | 'map' | 'routes';

const HeaderLogo: React.FC = () => (
  <svg
    width="20"
    height="20"
    viewBox="0 0 24 24"
    fill="none"
    stroke={colorTokens.brand}
    strokeWidth="2.2"
    strokeLinecap="round"
    strokeLinejoin="round"
    aria-hidden="true"
  >
    <path d="M4 19L12 12M12 12L20 5" />
    <path d="M12 12L20 12" />
    <path d="M12 12L20 19" />
  </svg>
);

const PlanIcon: React.FC = () => (
  <svg
    width="20"
    height="20"
    viewBox="0 0 24 24"
    fill="none"
    stroke="currentColor"
    strokeWidth="2"
    strokeLinecap="round"
    strokeLinejoin="round"
    aria-hidden="true"
  >
    <circle cx="6" cy="19" r="3" />
    <path d="M9 19h8.5a4.5 4.5 0 0 0 4.5-4.5v-5" />
    <circle cx="18" cy="5" r="3" />
  </svg>
);

const MapIcon: React.FC = () => (
  <svg
    width="20"
    height="20"
    viewBox="0 0 24 24"
    fill="none"
    stroke="currentColor"
    strokeWidth="2"
    strokeLinecap="round"
    strokeLinejoin="round"
    aria-hidden="true"
  >
    <polygon points="1 6 1 22 8 18 16 22 23 18 23 2 16 6 8 2 1 6" />
    <line x1="8" y1="2" x2="8" y2="18" />
    <line x1="16" y1="6" x2="16" y2="22" />
  </svg>
);

const RoutesIcon: React.FC = () => (
  <svg
    width="20"
    height="20"
    viewBox="0 0 24 24"
    fill="none"
    stroke="currentColor"
    strokeWidth="2"
    strokeLinecap="round"
    strokeLinejoin="round"
    aria-hidden="true"
  >
    <line x1="8" y1="6" x2="21" y2="6" />
    <line x1="8" y1="12" x2="21" y2="12" />
    <line x1="8" y1="18" x2="21" y2="18" />
    <circle cx="4" cy="6" r="1.5" fill="currentColor" />
    <circle cx="4" cy="12" r="1.5" fill="currentColor" />
    <circle cx="4" cy="18" r="1.5" fill="currentColor" />
  </svg>
);

export const App: React.FC = () => {
  const [activeTab, setActiveTab] = useState<MobileTab>('plan');
  const { data, isError } = useHealthCheck();

  const isOnline = !isError && data?.status === 'ok';

  return (
    <Box
      sx={{
        display: 'flex',
        flexDirection: 'column',
        height: '100vh',
        width: '100vw',
        overflow: 'hidden',
        backgroundColor: colorTokens.canvas,
      }}
    >
      {/* Header per DESIGN.md §5: 56px desktop, 48px mobile */}
      <Box
        component="header"
        sx={{
          height: {
            xs: `${shapeTokens.headerHeightMobile}px`,
            md: `${shapeTokens.headerHeight}px`,
          },
          backgroundColor: colorTokens.surface,
          borderBottom: `1px solid ${colorTokens.border}`,
          px: 2,
          display: 'flex',
          alignItems: 'center',
          justifyContent: 'space-between',
          flexShrink: 0,
        }}
      >
        <Box sx={{ display: 'flex', alignItems: 'center', gap: 1.5 }}>
          <HeaderLogo />
          <Typography
            component="span"
            sx={{
              fontFamily: typographyTokens.fontFamilyUi,
              fontSize: '18px',
              fontWeight: 700,
              color: colorTokens.text,
              letterSpacing: '-0.01em',
              lineHeight: 1,
            }}
          >
            StormRoute
          </Typography>
          <Typography
            component="span"
            sx={{
              fontFamily: typographyTokens.fontFamilyUi,
              fontSize: '13px',
              fontWeight: 400,
              color: colorTokens.textMuted,
              display: { xs: 'none', sm: 'inline' },
              borderLeft: `1px solid ${colorTokens.border}`,
              pl: 1.5,
              ml: 0.5,
              lineHeight: 1,
            }}
          >
            Weather-Aware Truck Router
          </Typography>
        </Box>

        {/* Status dot per DESIGN.md §5 */}
        <Box sx={{ display: 'flex', alignItems: 'center', gap: 1 }}>
          <Box
            data-testid="status-dot"
            sx={{
              width: 8,
              height: 8,
              borderRadius: '50%',
              backgroundColor: isOnline ? '#3FA66B' : '#E5484D',
              flexShrink: 0,
            }}
          />
          <Typography
            data-testid="status-text"
            sx={{
              fontFamily: typographyTokens.fontFamilyUi,
              fontSize: typographyTokens.caption.fontSize,
              color: colorTokens.textMuted,
              lineHeight: typographyTokens.caption.lineHeight,
            }}
          >
            {isOnline ? 'API online' : 'API offline'}
          </Typography>
        </Box>
      </Box>

      {/* Main Responsive Layout per DESIGN.md §5 */}
      <Box
        component="main"
        sx={{
          flex: 1,
          display: 'grid',
          overflow: 'hidden',
          gridTemplateColumns: {
            xs: '1fr',
            md: `${shapeTokens.twoColumnLeftWidth}px 1fr`,
            xl: `${shapeTokens.threeColumnLeftWidth}px 1fr ${shapeTokens.threeColumnRightWidth}px`,
          },
          gridTemplateRows: {
            xs: '1fr',
            md: '1fr 1fr',
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
        {/* Region 1: Trip form */}
        <Box
          component="aside"
          aria-label="Trip form"
          data-testid="region-trip-form"
          hidden={activeTab !== 'plan'}
          sx={{
            gridArea: 'form',
            display: {
              xs: activeTab === 'plan' ? 'flex' : 'none',
              md: 'flex !important',
            },
            flexDirection: 'column',
            p: 2,
            boxSizing: 'border-box',
            backgroundColor: colorTokens.surface,
            borderRight: { xs: 'none', md: `1px solid ${colorTokens.border}` },
            borderBottom: {
              xs: 'none',
              md: `1px solid ${colorTokens.border}`,
              xl: 'none',
            },
            overflowY: 'auto',
          }}
        >
          <Typography
            variant="h2"
            sx={{
              fontFamily: typographyTokens.fontFamilyUi,
              fontSize: typographyTokens.sectionHeading.fontSize,
              lineHeight: typographyTokens.sectionHeading.lineHeight,
              fontWeight: typographyTokens.sectionHeading.fontWeight,
              color: colorTokens.text,
            }}
          >
            Trip form
          </Typography>
        </Box>

        {/* Region 2: Map */}
        <Box
          component="section"
          aria-label="Map"
          data-testid="region-map"
          hidden={activeTab !== 'map'}
          sx={{
            gridArea: 'map',
            display: {
              xs: activeTab === 'map' ? 'flex' : 'none',
              md: 'flex !important',
            },
            flexDirection: 'column',
            alignItems: 'center',
            justifyContent: 'center',
            p: 2,
            boxSizing: 'border-box',
            backgroundColor: colorTokens.canvas,
            overflow: 'hidden',
            position: 'relative',
          }}
        >
          <Typography
            sx={{
              fontFamily: typographyTokens.fontFamilyMono,
              fontSize: typographyTokens.mono.fontSize,
              lineHeight: typographyTokens.mono.lineHeight,
              color: colorTokens.textMuted,
            }}
          >
            Map
          </Typography>
        </Box>

        {/* Region 3: Results */}
        <Box
          component="aside"
          aria-label="Results"
          data-testid="region-results"
          hidden={activeTab !== 'routes'}
          sx={{
            gridArea: 'results',
            display: {
              xs: activeTab === 'routes' ? 'flex' : 'none',
              md: 'flex !important',
            },
            flexDirection: 'column',
            p: 2,
            boxSizing: 'border-box',
            backgroundColor: colorTokens.surface,
            borderRight: {
              xs: 'none',
              md: `1px solid ${colorTokens.border}`,
              xl: 'none',
            },
            borderLeft: {
              xs: 'none',
              md: 'none',
              xl: `1px solid ${colorTokens.border}`,
            },
            overflowY: 'auto',
          }}
        >
          <Typography
            variant="h2"
            sx={{
              fontFamily: typographyTokens.fontFamilyUi,
              fontSize: typographyTokens.sectionHeading.fontSize,
              lineHeight: typographyTokens.sectionHeading.lineHeight,
              fontWeight: typographyTokens.sectionHeading.fontWeight,
              color: colorTokens.text,
            }}
          >
            Results
          </Typography>
        </Box>
      </Box>

      {/* Mobile bottom tab bar per DESIGN.md §5 (< 900 px) */}
      <BottomNavigation
        value={activeTab}
        onChange={(_, newValue: MobileTab) => setActiveTab(newValue)}
        showLabels
        sx={{
          display: { xs: 'flex', md: 'none' },
          height: 56,
          flexShrink: 0,
          backgroundColor: colorTokens.surface,
          borderTop: `1px solid ${colorTokens.border}`,
          '& .MuiBottomNavigationAction-root': {
            minHeight: 48,
            minWidth: 48,
            color: colorTokens.textMuted,
            '&.Mui-selected': {
              color: colorTokens.brand,
            },
            '&:focus-visible': {
              outline: `2px solid ${colorTokens.brand}`,
              outlineOffset: '-2px',
            },
          },
        }}
      >
        <BottomNavigationAction
          label="Plan"
          value="plan"
          icon={<PlanIcon />}
          data-testid="tab-plan"
        />
        <BottomNavigationAction
          label="Map"
          value="map"
          icon={<MapIcon />}
          data-testid="tab-map"
        />
        <BottomNavigationAction
          label="Routes"
          value="routes"
          icon={<RoutesIcon />}
          data-testid="tab-routes"
        />
      </BottomNavigation>
    </Box>
  );
};
