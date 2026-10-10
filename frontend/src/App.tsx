import React from 'react';
import { Box, Typography } from '@mui/material';
import { colorTokens, shapeTokens, typographyTokens } from './theme/tokens';

export const App: React.FC = () => {
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
      {/* 56px Header per DESIGN.md §5 */}
      <Box
        component="header"
        sx={{
          height: `${shapeTokens.headerHeight}px`,
          backgroundColor: colorTokens.brand700,
          color: '#FFFFFF',
          px: 2,
          display: 'flex',
          alignItems: 'center',
          justifyContent: 'space-between',
          flexShrink: 0,
          borderBottom: `1px solid ${colorTokens.border}`,
        }}
      >
        <Box sx={{ display: 'flex', alignItems: 'center', gap: 1.5 }}>
          {/* Inline SVG glyph of three diverging lines per DESIGN.md §5 */}
          <svg
            width="22"
            height="22"
            viewBox="0 0 24 24"
            fill="none"
            stroke="currentColor"
            strokeWidth="2.2"
            strokeLinecap="round"
            strokeLinejoin="round"
            aria-hidden="true"
          >
            <path d="M4 19L12 12M12 12L20 5" />
            <path d="M12 12L20 12" />
            <path d="M12 12L20 19" />
          </svg>
          <Typography
            component="span"
            sx={{
              fontFamily: typographyTokens.fontFamilyUi,
              fontSize: '17px',
              lineHeight: '22px',
              fontWeight: 600,
              letterSpacing: '0.01em',
            }}
          >
            Weather-Aware Truck Router
          </Typography>
        </Box>
      </Box>

      {/* Main Layout: Fixed 420px Docked Panel + Map Area */}
      <Box
        component="main"
        sx={{
          flex: 1,
          display: 'flex',
          flexDirection: { xs: 'column-reverse', md: 'row' },
          overflow: 'hidden',
          position: 'relative',
        }}
      >
        {/* Left Control Panel (420px on desktop, internally scrollable) */}
        <Box
          component="aside"
          sx={{
            width: { xs: '100%', md: `${shapeTokens.controlPanelWidth}px` },
            height: { xs: '55%', md: '100%' },
            flexShrink: 0,
            backgroundColor: colorTokens.surface,
            borderRight: { md: `1px solid ${colorTokens.border}` },
            borderTop: { xs: `1px solid ${colorTokens.border}`, md: 'none' },
            overflowY: 'auto',
            p: 2,
            boxSizing: 'border-box',
          }}
        >
          <Typography variant="h2" sx={{ mb: 1, color: colorTokens.ink }}>
            Trip Planning
          </Typography>
          <Typography variant="body2" sx={{ color: colorTokens.inkMuted }}>
            Enter origin, destination, and departure time to analyze weather
            risks along commercial truck routes.
          </Typography>
        </Box>

        {/* Map Area Placeholder (fills remaining viewport) */}
        <Box
          component="section"
          sx={{
            flex: 1,
            height: { xs: '45%', md: '100%' },
            backgroundColor: '#E6EBE9',
            display: 'flex',
            alignItems: 'center',
            justifyContent: 'center',
            position: 'relative',
          }}
        >
          <Typography
            sx={{
              fontFamily: typographyTokens.fontFamilyMono,
              fontSize: '13px',
              color: colorTokens.inkMuted,
            }}
          >
            [Map Canvas Placeholder — P4/P5]
          </Typography>
        </Box>
      </Box>
    </Box>
  );
};
