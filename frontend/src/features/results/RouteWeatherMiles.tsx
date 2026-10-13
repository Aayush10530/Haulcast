import React from 'react';
import { Box, Typography } from '@mui/material';

interface RouteWeatherMilesProps {
  isDataAvailable: boolean;
  severeMiles: number;
  highMiles: number;
  moderateMiles: number;
}

export const RouteWeatherMiles: React.FC<RouteWeatherMilesProps> = ({
  isDataAvailable,
  severeMiles,
  highMiles,
  moderateMiles,
}) => {
  return (
    <Box
      sx={{
        display: 'flex',
        alignItems: 'center',
        justifyContent: 'space-between',
        pt: 1,
        borderTop: '1px solid rgba(22, 50, 74, 0.6)',
      }}
    >
      {/* Severe Miles */}
      <Box sx={{ display: 'flex', flexDirection: 'column' }}>
        <Box sx={{ display: 'flex', alignItems: 'center', gap: 0.75 }}>
          <Box sx={{ width: 6, height: 6, borderRadius: '50%', backgroundColor: '#E5484D' }} />
          <Typography sx={{ fontSize: '12px', fontWeight: 700, color: '#FFFFFF' }}>
            {isDataAvailable ? `${severeMiles} mi` : '-- mi'}
          </Typography>
        </Box>
        <Typography sx={{ fontSize: '10px', color: '#E5484D', fontWeight: 600, pl: 1.5 }}>
          Severe
        </Typography>
      </Box>

      {/* High Miles */}
      <Box sx={{ display: 'flex', flexDirection: 'column' }}>
        <Box sx={{ display: 'flex', alignItems: 'center', gap: 0.75 }}>
          <Box sx={{ width: 6, height: 6, borderRadius: '50%', backgroundColor: '#E8872B' }} />
          <Typography sx={{ fontSize: '12px', fontWeight: 700, color: '#FFFFFF' }}>
            {isDataAvailable ? `${highMiles} mi` : '-- mi'}
          </Typography>
        </Box>
        <Typography sx={{ fontSize: '10px', color: '#E8872B', fontWeight: 600, pl: 1.5 }}>
          High
        </Typography>
      </Box>

      {/* Moderate Miles */}
      <Box sx={{ display: 'flex', flexDirection: 'column' }}>
        <Box sx={{ display: 'flex', alignItems: 'center', gap: 0.75 }}>
          <Box sx={{ width: 6, height: 6, borderRadius: '50%', backgroundColor: '#E2C044' }} />
          <Typography sx={{ fontSize: '12px', fontWeight: 700, color: '#FFFFFF' }}>
            {isDataAvailable ? `${moderateMiles} mi` : '-- mi'}
          </Typography>
        </Box>
        <Typography sx={{ fontSize: '10px', color: '#E2C044', fontWeight: 600, pl: 1.5 }}>
          Moderate
        </Typography>
      </Box>
    </Box>
  );
};
