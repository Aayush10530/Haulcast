import React from 'react';

export const CloudSnowIcon: React.FC<{ color?: string }> = ({ color = '#38BDF8' }) => (
  <svg width="26" height="26" viewBox="0 0 24 24" fill="none" stroke={color} strokeWidth="2" strokeLinecap="round" strokeLinejoin="round">
    <path d="M20 16.58A5 5 0 0 0 18 7h-1.26A8 8 0 1 0 4 15.25" fill={color} fillOpacity="0.2" />
    <path d="M8 19v1M8 15v1M12 21v1M12 17v1M16 19v1M16 15v1" strokeWidth="2.5" />
  </svg>
);

export const RaindropIcon: React.FC<{ color?: string }> = ({ color = '#38BDF8' }) => (
  <svg width="16" height="16" viewBox="0 0 24 24" fill={color} stroke={color} strokeWidth="1">
    <path d="M12 2.69l5.66 5.66a8 8 0 1 1-11.31 0z" />
  </svg>
);

export const SnowflakeIcon: React.FC<{ color?: string }> = ({ color = '#38BDF8' }) => (
  <svg width="16" height="16" viewBox="0 0 24 24" fill="none" stroke={color} strokeWidth="2" strokeLinecap="round" strokeLinejoin="round">
    <line x1="12" y1="2" x2="12" y2="22" />
    <line x1="2" y1="12" x2="22" y2="12" />
    <line x1="4.93" y1="4.93" x2="19.07" y2="19.07" />
    <line x1="19.07" y1="4.93" x2="4.93" y2="19.07" />
  </svg>
);

export const WindIcon: React.FC<{ color?: string }> = ({ color = '#FFFFFF' }) => (
  <svg width="16" height="16" viewBox="0 0 24 24" fill="none" stroke={color} strokeWidth="2" strokeLinecap="round" strokeLinejoin="round">
    <path d="M9.59 4.59A2 2 0 1 1 11 8H2m10.59 11.41A2 2 0 1 0 14 16H2m15.73-8.27A2.5 2.5 0 1 1 19.5 12H2" />
  </svg>
);

export const WarningAlertIcon: React.FC<{ color?: string }> = ({ color = '#EF4444' }) => (
  <svg width="18" height="18" viewBox="0 0 24 24" fill="none" stroke={color} strokeWidth="2" strokeLinecap="round" strokeLinejoin="round">
    <circle cx="12" cy="12" r="10" />
    <line x1="12" y1="8" x2="12" y2="12" />
    <line x1="12" y1="16" x2="12.01" y2="16" />
  </svg>
);
