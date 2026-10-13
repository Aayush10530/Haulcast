import React from 'react';
import { BottomNavigation, BottomNavigationAction } from '@mui/material';
import { colorTokens, glassTokens } from '../theme/tokens';

export type MobileTab = 'plan' | 'map' | 'routes';

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

interface MobileBottomNavProps {
  activeTab: MobileTab;
  onChange: (tab: MobileTab) => void;
}

export const MobileBottomNav: React.FC<MobileBottomNavProps> = ({
  activeTab,
  onChange,
}) => {
  return (
    <BottomNavigation
      value={activeTab}
      onChange={(_, newValue: MobileTab) => onChange(newValue)}
      showLabels
      sx={{
        position: 'fixed',
        bottom: 0,
        left: 0,
        right: 0,
        zIndex: 1000,
        height: 'calc(56px + env(safe-area-inset-bottom, 0px))',
        pb: 'env(safe-area-inset-bottom, 0px)',
        boxSizing: 'border-box',
        flexShrink: 0,
        backgroundColor: glassTokens.surface,
        backdropFilter: glassTokens.blur,
        WebkitBackdropFilter: glassTokens.webkitBlur,
        borderTop: `1px solid ${glassTokens.border}`,
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
  );
};
