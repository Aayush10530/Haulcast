import React from 'react';
import { Box } from '@mui/material';

/**
 * TopographyBackground renders organic terrain elevation contour lines / isolines
 * with a smooth top-to-bottom shaded fade effect.
 *
 * Sits at z-index 0 behind the glassmorphic console cards so that backdrop-filter
 * can softly refract and blur the underlying terrain contours.
 */
export const TopographyBackground: React.FC = () => {
  return (
    <Box
      aria-hidden="true"
      sx={{
        position: 'fixed',
        inset: 0,
        pointerEvents: 'none',
        zIndex: 0,
        overflow: 'hidden',
        maskImage:
          'linear-gradient(to bottom, rgba(0, 0, 0, 0.85) 0%, rgba(0, 0, 0, 0.65) 25%, rgba(0, 0, 0, 0.25) 55%, transparent 85%)',
        WebkitMaskImage:
          'linear-gradient(to bottom, rgba(0, 0, 0, 0.85) 0%, rgba(0, 0, 0, 0.65) 25%, rgba(0, 0, 0, 0.25) 55%, transparent 85%)',
      }}
    >
      <svg
        width="100%"
        height="100%"
        viewBox="0 0 1920 1080"
        preserveAspectRatio="xMidYMid slice"
        fill="none"
        xmlns="http://www.w3.org/2000/svg"
        style={{
          width: '100%',
          height: '100%',
          opacity: 0.75,
        }}
      >
        <defs>
          <linearGradient id="topo-glow" x1="0%" y1="0%" x2="100%" y2="100%">
            <stop offset="0%" stopColor="#00E5FF" stopOpacity="0.32" />
            <stop offset="40%" stopColor="#00D2FF" stopOpacity="0.22" />
            <stop offset="80%" stopColor="#00E676" stopOpacity="0.16" />
            <stop offset="100%" stopColor="#00E5FF" stopOpacity="0.08" />
          </linearGradient>
          <linearGradient id="topo-subtle" x1="0%" y1="0%" x2="0%" y2="100%">
            <stop offset="0%" stopColor="#00E5FF" stopOpacity="0.20" />
            <stop offset="50%" stopColor="#1E4959" stopOpacity="0.14" />
            <stop offset="100%" stopColor="#06121E" stopOpacity="0.02" />
          </linearGradient>
        </defs>

        {/* Outer major ridgeline contours */}
        <path
          d="M-100 80 C 250 40, 500 180, 850 110 C 1200 40, 1550 160, 2020 90"
          stroke="url(#topo-glow)"
          strokeWidth="1.6"
        />
        <path
          d="M-100 130 C 280 80, 520 230, 880 160 C 1240 90, 1580 210, 2020 140"
          stroke="url(#topo-subtle)"
          strokeWidth="1.2"
        />
        <path
          d="M-100 180 C 310 120, 540 280, 910 210 C 1280 140, 1610 260, 2020 190"
          stroke="url(#topo-glow)"
          strokeWidth="1.4"
        />
        <path
          d="M-100 230 C 340 160, 560 330, 940 260 C 1320 190, 1640 310, 2020 240"
          stroke="url(#topo-subtle)"
          strokeWidth="1.0"
        />

        {/* High-elevation summit loops & nested hilltops (top-left & center) */}
        <path
          d="M 120 70 C 200 30, 320 40, 380 90 C 440 140, 380 210, 280 220 C 180 230, 80 160, 90 110 C 95 85, 110 75, 120 70 Z"
          stroke="url(#topo-glow)"
          strokeWidth="1.4"
        />
        <path
          d="M 160 85 C 220 55, 300 65, 340 105 C 380 145, 340 190, 270 195 C 200 200, 135 150, 140 115 C 145 95, 155 90, 160 85 Z"
          stroke="url(#topo-subtle)"
          strokeWidth="1.1"
        />
        <path
          d="M 200 100 C 240 80, 285 85, 310 115 C 335 145, 310 170, 260 175 C 210 180, 175 145, 180 125 C 185 110, 195 105, 200 100 Z"
          stroke="url(#topo-glow)"
          strokeWidth="1.2"
        />

        {/* Right-hand elevation plateau & contours */}
        <path
          d="M 1450 60 C 1580 20, 1750 30, 1860 110 C 1960 180, 1920 280, 1780 320 C 1640 360, 1480 300, 1430 220 C 1390 150, 1420 80, 1450 60 Z"
          stroke="url(#topo-glow)"
          strokeWidth="1.5"
        />
        <path
          d="M 1500 85 C 1600 55, 1730 65, 1810 125 C 1880 180, 1850 250, 1750 280 C 1650 310, 1530 265, 1490 205 C 1460 150, 1480 100, 1500 85 Z"
          stroke="url(#topo-subtle)"
          strokeWidth="1.2"
        />
        <path
          d="M 1550 110 C 1620 90, 1710 95, 1760 140 C 1810 185, 1780 225, 1710 245 C 1640 265, 1560 235, 1535 190 C 1515 150, 1535 120, 1550 110 Z"
          stroke="url(#topo-glow)"
          strokeWidth="1.3"
        />

        {/* Mid-level undulating contour bands */}
        <path
          d="M-80 300 C 350 220, 680 400, 1080 320 C 1450 240, 1720 380, 2020 310"
          stroke="url(#topo-subtle)"
          strokeWidth="1.1"
        />
        <path
          d="M-80 370 C 380 290, 710 470, 1110 390 C 1480 310, 1750 450, 2020 380"
          stroke="url(#topo-glow)"
          strokeWidth="1.3"
        />
        <path
          d="M-80 440 C 410 360, 740 540, 1140 460 C 1510 380, 1780 520, 2020 450"
          stroke="url(#topo-subtle)"
          strokeWidth="1.0"
        />

        {/* Lower mountain valley trails (fading into the bottom darkness) */}
        <path
          d="M-80 520 C 440 430, 770 620, 1170 530 C 1540 450, 1810 600, 2020 520"
          stroke="url(#topo-subtle)"
          strokeWidth="0.9"
        />
        <path
          d="M-80 610 C 470 510, 800 700, 1200 610 C 1570 530, 1840 680, 2020 600"
          stroke="url(#topo-subtle)"
          strokeWidth="0.8"
        />
        <path
          d="M-80 710 C 500 600, 830 790, 1230 700 C 1600 620, 1870 770, 2020 690"
          stroke="url(#topo-subtle)"
          strokeWidth="0.7"
        />
      </svg>
    </Box>
  );
};
