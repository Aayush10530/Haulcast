import React from 'react';
import { Box, Typography } from '@mui/material';
import { CheckpointDTO } from '../../api/types';
import { RiskChip } from '../../components/RiskChip';
import { colorTokens, typographyTokens } from '../../theme/tokens';
import { formatCheckpointMiles, formatLocalTime } from '../../utils/format';

export interface CheckpointPopupProps {
  checkpoint: CheckpointDTO;
}

export const CheckpointPopup: React.FC<CheckpointPopupProps> = ({ checkpoint }) => {
  const { mile, eta_local, local_tz, weather, risk } = checkpoint;
  const isUnavailable = !weather || !risk;

  return (
    <Box
      data-testid={`checkpoint-popup-${checkpoint.index}`}
      sx={{
        display: 'flex',
        flexDirection: 'column',
        gap: 1,
        minWidth: 200,
        maxWidth: 260,
      }}
    >
      {/* Header: Mile & ETA */}
      <Box
        sx={{
          display: 'flex',
          justifyContent: 'space-between',
          alignItems: 'baseline',
          borderBottom: `1px solid ${colorTokens.border}`,
          pb: 0.75,
        }}
      >
        <Typography
          data-testid="popup-mile"
          sx={{
            fontFamily: typographyTokens.fontFamilyMono,
            fontSize: '0.8125rem',
            fontWeight: 700,
            color: colorTokens.text,
          }}
        >
          {formatCheckpointMiles(mile)}
        </Typography>

        <Typography
          data-testid="popup-eta"
          sx={{
            fontFamily: typographyTokens.fontFamilyMono,
            fontSize: '0.75rem',
            color: colorTokens.textMuted,
          }}
        >
          {formatLocalTime(eta_local, local_tz)}
        </Typography>
      </Box>

      {/* Body: Risk & Weather or Unavailable */}
      {isUnavailable ? (
        <Typography
          data-testid="popup-unavailable"
          sx={{
            fontFamily: typographyTokens.fontFamilyUi,
            fontSize: '0.8125rem',
            fontStyle: 'italic',
            color: colorTokens.textMuted,
            py: 0.5,
          }}
        >
          Forecast unavailable
        </Typography>
      ) : (
        <Box sx={{ display: 'flex', flexDirection: 'column', gap: 1 }}>
          <Box sx={{ display: 'flex', alignItems: 'center', justifyContent: 'space-between' }}>
            <RiskChip risk={risk} />
          </Box>

          {/* Metrics in mono */}
          <Box
            data-testid="popup-metrics"
            sx={{
              display: 'grid',
              gridTemplateColumns: 'repeat(3, 1fr)',
              gap: 0.75,
              backgroundColor: colorTokens.surface,
              p: 0.75,
              borderRadius: '6px',
              border: `1px solid ${colorTokens.border}`,
            }}
          >
            <Box>
              <Typography
                sx={{
                  fontFamily: typographyTokens.fontFamilyUi,
                  fontSize: '0.625rem',
                  textTransform: 'uppercase',
                  color: colorTokens.textMuted,
                }}
              >
                Wind
              </Typography>
              <Typography
                data-testid="popup-wind"
                sx={{
                  fontFamily: typographyTokens.fontFamilyMono,
                  fontSize: '0.75rem',
                  fontWeight: 600,
                  color: colorTokens.text,
                }}
              >
                {Math.round(weather.wind_mph)} mph
              </Typography>
            </Box>

            <Box>
              <Typography
                sx={{
                  fontFamily: typographyTokens.fontFamilyUi,
                  fontSize: '0.625rem',
                  textTransform: 'uppercase',
                  color: colorTokens.textMuted,
                }}
              >
                Rain
              </Typography>
              <Typography
                data-testid="popup-rain"
                sx={{
                  fontFamily: typographyTokens.fontFamilyMono,
                  fontSize: '0.75rem',
                  fontWeight: 600,
                  color: colorTokens.text,
                }}
              >
                {weather.rain_in_hr.toFixed(2)} in/hr
              </Typography>
            </Box>

            <Box>
              <Typography
                sx={{
                  fontFamily: typographyTokens.fontFamilyUi,
                  fontSize: '0.625rem',
                  textTransform: 'uppercase',
                  color: colorTokens.textMuted,
                }}
              >
                Snow
              </Typography>
              <Typography
                data-testid="popup-snow"
                sx={{
                  fontFamily: typographyTokens.fontFamilyMono,
                  fontSize: '0.75rem',
                  fontWeight: 600,
                  color: colorTokens.text,
                }}
              >
                {weather.snow_in_hr.toFixed(2)} in/hr
              </Typography>
            </Box>
          </Box>

          {/* Reason text */}
          {risk.reason && (
            <Typography
              data-testid="popup-reason"
              sx={{
                fontFamily: typographyTokens.fontFamilyUi,
                fontSize: '0.75rem',
                lineHeight: 1.35,
                color: colorTokens.text,
              }}
            >
              {risk.reason}
            </Typography>
          )}
        </Box>
      )}
    </Box>
  );
};
