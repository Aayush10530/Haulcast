import React from 'react';
import { Box, Collapse, Typography } from '@mui/material';
import { CheckpointDTO } from '../../api/types';
import { typographyTokens } from '../../theme/tokens';
import {
  CloudSnowIcon,
  RaindropIcon,
  SnowflakeIcon,
  WarningAlertIcon,
  WindIcon,
} from './CheckpointIcons';
import {
  formatArrivalDate,
  formatMilestoneTime,
  getAlertBannerStyle,
  getCheckpointLocationName,
  getRiskPillStyle,
  getStepCircleColor,
} from './checkpointListUtils';

interface CheckpointItemProps {
  checkpoint: CheckpointDTO;
  index: number;
  total: number;
  originLabel?: string;
  destinationLabel?: string;
  isExpanded: boolean;
  onToggle: () => void;
  onSelect?: (checkpoint: CheckpointDTO) => void;
}

export const CheckpointItem: React.FC<CheckpointItemProps> = ({
  checkpoint,
  index,
  total,
  originLabel,
  destinationLabel,
  isExpanded,
  onToggle,
  onSelect,
}) => {
  const locationName = getCheckpointLocationName(checkpoint, index, total, originLabel, destinationLabel);
  const circleColor = getStepCircleColor(index, total);
  const pillStyle = getRiskPillStyle(checkpoint.risk?.level);
  const alertStyle = getAlertBannerStyle(checkpoint.risk?.level);

  const weather = checkpoint.weather;
  const isWeatherAvailable = weather !== null && weather !== undefined;
  const windMph = isWeatherAvailable && weather.wind_mph !== undefined ? Math.round(weather.wind_mph) : null;
  const rainInHr = isWeatherAvailable && weather.rain_in_hr !== undefined ? weather.rain_in_hr.toFixed(2) : null;
  const snowInHr = isWeatherAvailable && weather.snow_in_hr !== undefined ? weather.snow_in_hr.toFixed(1) : null;

  const conditionText = !isWeatherAvailable
    ? 'Forecast Unavailable'
    : (weather?.snow_in_hr || 0) > 0.05
    ? 'Heavy Snow'
    : (weather?.rain_in_hr || 0) > 0.15
    ? 'Heavy Rain'
    : (weather?.rain_in_hr || 0) > 0.02
    ? 'Moderate Rain'
    : (weather?.wind_mph || 0) > 30
    ? 'High Winds'
    : 'Clear Skies';

  const warningText =
    checkpoint.risk?.reason ||
    (!isWeatherAvailable
      ? 'Weather forecast is unavailable for this checkpoint. Drive alert.'
      : checkpoint.risk?.level === 'severe' || checkpoint.risk?.level === 'no_travel'
      ? 'Severe weather conditions. Proceed with caution.'
      : checkpoint.risk?.level === 'high'
      ? 'High weather hazard along corridor. Drive alert.'
      : checkpoint.risk?.level === 'moderate'
      ? 'Moderate weather conditions. Monitor road conditions.'
      : 'Favorable weather conditions along corridor.');

  return (
    <Box sx={{ mb: isExpanded ? 1.5 : 1, position: 'relative', zIndex: 1 }}>
      <Box
        sx={{
          backgroundColor: isExpanded ? 'rgba(24, 24, 24, 0.85)' : 'transparent',
          border: isExpanded ? '1px solid rgba(0, 229, 255, 0.35)' : '1px solid transparent',
          borderRadius: isExpanded ? '12px' : '8px',
          boxShadow: isExpanded ? '0 8px 24px rgba(0,0,0,0.55)' : 'none',
          px: 1.5,
          py: isExpanded ? 1.5 : 0.75,
          transition:
            'transform 180ms cubic-bezier(0.16, 1, 0.3, 1), background-color 180ms ease, border-color 180ms ease',
          '&:hover': {
            backgroundColor: isExpanded ? 'rgba(28, 28, 28, 0.95)' : 'rgba(255, 255, 255, 0.04)',
            transform: isExpanded ? 'none' : 'translateX(3px)',
          },
        }}
      >
        <Box
          data-testid={`checkpoint-row-${checkpoint.index}`}
          onClick={() => {
            onToggle();
            onSelect?.(checkpoint);
          }}
          sx={{ display: 'flex', alignItems: 'center', cursor: 'pointer', userSelect: 'none' }}
        >
          <Box
            sx={{
              width: 26,
              height: 26,
              borderRadius: '50%',
              backgroundColor: circleColor,
              color: '#FFFFFF',
              display: 'flex',
              alignItems: 'center',
              justifyContent: 'center',
              fontSize: '13px',
              fontWeight: 700,
              flexShrink: 0,
              boxShadow: '0 2px 6px rgba(0,0,0,0.3)',
            }}
          >
            {index + 1}
          </Box>

          <Box sx={{ ml: 2, flex: 1, minWidth: 0 }}>
            <Typography
              sx={{
                fontFamily: typographyTokens.fontFamilyUi,
                fontSize: '14px',
                fontWeight: 600,
                color: '#FFFFFF',
                lineHeight: 1.25,
                whiteSpace: 'nowrap',
                overflow: 'hidden',
                textOverflow: 'ellipsis',
              }}
            >
              {locationName}
            </Typography>
            <Typography
              sx={{
                fontFamily: typographyTokens.fontFamilyUi,
                fontSize: '12px',
                color: '#94A3B8',
                mt: 0.25,
              }}
            >
              <span>{Math.round(checkpoint.mile).toLocaleString()} mi</span>
              <span> • </span>
              <span>{formatMilestoneTime(checkpoint.eta_local)}</span>
              {!isWeatherAvailable && (
                <>
                  <span> • </span>
                  <span style={{ color: '#F87171' }}>Forecast unavailable</span>
                </>
              )}
            </Typography>
          </Box>

          <Box
            sx={{
              backgroundColor: pillStyle.bg,
              color: pillStyle.text,
              borderRadius: '16px',
              px: 2,
              py: 0.35,
              fontSize: '12px',
              fontWeight: 700,
              boxShadow: pillStyle.shadow,
              flexShrink: 0,
              minWidth: 64,
              textAlign: 'center',
              letterSpacing: '0.01em',
            }}
          >
            {pillStyle.label}
          </Box>
        </Box>

        <Collapse in={isExpanded} timeout="auto" unmountOnExit>
          <Box
            data-testid={`checkpoint-detail-${checkpoint.index}`}
            sx={{ mt: 2, pt: 1.5, borderTop: '1px solid rgba(255, 255, 255, 0.08)' }}
          >
            <Box sx={{ display: 'flex', alignItems: 'center', justifyContent: 'space-between', mb: 1.75 }}>
              <Box sx={{ display: 'flex', alignItems: 'center', gap: 1.25 }}>
                <CloudSnowIcon />
                <Typography sx={{ fontFamily: typographyTokens.fontFamilyUi, fontSize: '15px', fontWeight: 700, color: '#FFFFFF' }}>
                  {conditionText}
                </Typography>
              </Box>
              <Box sx={{ textAlign: 'right' }}>
                <Typography sx={{ fontSize: '11px', color: '#94A3B8', fontWeight: 500 }}>
                  Estimated Arrival
                </Typography>
                <Typography sx={{ fontSize: '13px', fontWeight: 700, color: '#FFFFFF' }}>
                  {formatMilestoneTime(checkpoint.eta_local)} ({formatArrivalDate(checkpoint.eta_local)})
                </Typography>
              </Box>
            </Box>

            <Box sx={{ display: 'flex', alignItems: 'center', justifyContent: 'space-between', py: 0.5, px: 0.5, mb: 1.5 }}>
              <Box sx={{ flex: 1, display: 'flex', alignItems: 'center', gap: 1, borderRight: '1px solid rgba(255, 255, 255, 0.08)', pr: 1 }}>
                <WindIcon />
                <Box>
                  <Typography sx={{ fontSize: '11px', color: '#94A3B8', lineHeight: 1 }}>Wind:</Typography>
                  <Typography sx={{ fontSize: '14px', fontWeight: 700, color: '#FFFFFF', mt: 0.35 }}>
                    {windMph !== null ? `${windMph} mph` : '--'}
                  </Typography>
                </Box>
              </Box>

              <Box sx={{ flex: 1, display: 'flex', alignItems: 'center', gap: 1, borderRight: '1px solid rgba(255, 255, 255, 0.08)', px: 1 }}>
                <RaindropIcon />
                <Box>
                  <Typography sx={{ fontSize: '11px', color: '#94A3B8', lineHeight: 1 }}>Rain:</Typography>
                  <Typography sx={{ fontSize: '14px', fontWeight: 700, color: '#FFFFFF', mt: 0.35 }}>
                    {rainInHr !== null ? `${rainInHr} in/hr` : '--'}
                  </Typography>
                </Box>
              </Box>

              <Box sx={{ flex: 1, display: 'flex', alignItems: 'center', gap: 1, pl: 1 }}>
                <SnowflakeIcon />
                <Box>
                  <Typography sx={{ fontSize: '11px', color: '#94A3B8', lineHeight: 1 }}>Snow:</Typography>
                  <Typography sx={{ fontSize: '14px', fontWeight: 700, color: '#FFFFFF', mt: 0.35 }}>
                    {snowInHr !== null ? `${snowInHr} in/hr` : '--'}
                  </Typography>
                </Box>
              </Box>
            </Box>

            <Box
              sx={{
                backgroundColor: alertStyle.bg,
                border: alertStyle.border,
                borderRadius: '8px',
                py: 1,
                px: 1.5,
                display: 'flex',
                alignItems: 'center',
                gap: 1.25,
              }}
            >
              <WarningAlertIcon color={alertStyle.iconColor} />
              <Typography sx={{ fontSize: '12px', color: alertStyle.textColor, fontWeight: 500, lineHeight: 1.3 }}>
                {warningText}
              </Typography>
            </Box>
          </Box>
        </Collapse>
      </Box>
    </Box>
  );
};
