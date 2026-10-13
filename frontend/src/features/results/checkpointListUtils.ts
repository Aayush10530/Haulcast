import { CheckpointDTO, RiskLevelKey } from '../../api/types';

export type SortOption = 'mile' | 'risk';

export const SEVERITY_ORDER: Record<RiskLevelKey, number> = {
  no_travel: 5,
  severe: 4,
  high: 3,
  moderate: 2,
  low: 1,
};

// Known corridor milestone naming sequences
const CORRIDOR_SEQUENCES: Record<string, string[]> = {
  'chicago-denver': [
    'Chicago, IL (Start)',
    'Rockford, IL',
    'Cedar Rapids, IA',
    'Omaha, NE',
    'North Platte, NE',
    'Cheyenne, WY',
    'Denver, CO (End)',
  ],
  'portland-sacramento': [
    'Portland, OR (Start)',
    'Salem, OR',
    'Eugene, OR',
    'Medford, OR',
    'Weed, CA',
    'Redding, CA',
    'Sacramento, CA (End)',
  ],
  'dallas-denver': [
    'Dallas, TX (Start)',
    'Wichita Falls, TX',
    'Amarillo, TX',
    'Clayton, NM',
    'Pueblo, CO',
    'Colorado Springs, CO',
    'Denver, CO (End)',
  ],
};

export function getCheckpointLocationName(
  cp: CheckpointDTO,
  index: number,
  total: number,
  originLabel?: string,
  destinationLabel?: string,
): string {
  const o = (originLabel || '').toLowerCase();
  const d = (destinationLabel || '').toLowerCase();

  // Match predefined corridor sequences
  if ((o.includes('chicago') && d.includes('denver')) || (!o && !d)) {
    const seq = CORRIDOR_SEQUENCES['chicago-denver'];
    return seq[index] || `Corridor Station (Mile ${Math.round(cp.mile)})`;
  }
  if (o.includes('portland') && d.includes('sacramento')) {
    const seq = CORRIDOR_SEQUENCES['portland-sacramento'];
    return seq[index] || `Corridor Station (Mile ${Math.round(cp.mile)})`;
  }
  if (o.includes('dallas') && d.includes('denver')) {
    const seq = CORRIDOR_SEQUENCES['dallas-denver'];
    return seq[index] || `Corridor Station (Mile ${Math.round(cp.mile)})`;
  }

  // Dynamic origin/destination fallback
  if (index === 0) {
    return originLabel ? `${originLabel} (Start)` : 'Origin (Start)';
  }
  if (index === total - 1) {
    return destinationLabel ? `${destinationLabel} (End)` : 'Destination (End)';
  }

  const m = Math.round(cp.mile);
  return `Corridor Station (Mile ${m})`;
}

// 12-hour milestone time formatter with leading zero: "04:10 PM"
export function formatMilestoneTime(etaLocal?: string): string {
  if (!etaLocal) return '08:00 AM';
  try {
    const match = etaLocal.match(/T(\d{2}):(\d{2})/);
    if (match) {
      let hour = parseInt(match[1], 10);
      const min = match[2];
      const ampm = hour >= 12 ? 'PM' : 'AM';
      hour = hour % 12 || 12;
      return `${String(hour).padStart(2, '0')}:${min} ${ampm}`;
    }
    const d = new Date(etaLocal);
    if (!isNaN(d.getTime())) {
      let hours = d.getHours();
      const minutes = String(d.getMinutes()).padStart(2, '0');
      const ampm = hours >= 12 ? 'PM' : 'AM';
      hours = hours % 12 || 12;
      return `${String(hours).padStart(2, '0')}:${minutes} ${ampm}`;
    }
  } catch {
    // fallback
  }
  return '08:00 AM';
}

// Arrival date formatter: "Oct 15"
export function formatArrivalDate(etaLocal?: string): string {
  if (!etaLocal) return 'Oct 15';
  try {
    const d = new Date(etaLocal);
    if (!isNaN(d.getTime())) {
      const month = d.toLocaleString('en-US', { month: 'short' });
      const day = d.getDate();
      return `${month} ${day}`;
    }
  } catch {
    // fallback
  }
  return 'Oct 15';
}

export function getStepCircleColor(index: number, total: number): string {
  if (index === 0) return '#00A3FF'; // Step 1: Blue
  if (index === 1) return '#10B981'; // Step 2: Green
  if (index === total - 1) return '#EF4444'; // Step 7: Red
  return '#00A3FF'; // Intermediate Steps: Blue
}

export function getRiskPillStyle(level?: RiskLevelKey) {
  switch (level) {
    case 'severe':
      return {
        bg: '#EF4444',
        text: '#FFFFFF',
        label: 'Severe',
        shadow: '0 0 16px 2px rgba(239, 68, 68, 0.75)',
      };
    case 'high':
      return {
        bg: '#F97316',
        text: '#FFFFFF',
        label: 'High',
        shadow: 'none',
      };
    case 'moderate':
      return {
        bg: '#F59E0B',
        text: '#07171C',
        label: 'Moderate',
        shadow: 'none',
      };
    case 'no_travel':
      return {
        bg: '#8B5CF6',
        text: '#FFFFFF',
        label: 'No Travel',
        shadow: '0 0 16px 2px rgba(139, 92, 246, 0.75)',
      };
    case 'low':
      return {
        bg: '#10B981',
        text: '#07171C',
        label: 'Low',
        shadow: 'none',
      };
    default:
      return {
        bg: 'rgba(51, 65, 85, 0.8)',
        text: '#CBD5E1',
        label: 'Unavailable',
        shadow: 'none',
      };
  }
}

export function getAlertBannerStyle(level?: RiskLevelKey) {
  switch (level) {
    case 'severe':
    case 'no_travel':
      return {
        bg: 'rgba(56, 14, 22, 0.85)',
        border: '1px solid rgba(239, 68, 68, 0.35)',
        iconColor: '#EF4444',
        textColor: '#FCA5A5',
      };
    case 'high':
      return {
        bg: 'rgba(67, 24, 8, 0.85)',
        border: '1px solid rgba(249, 115, 22, 0.35)',
        iconColor: '#F97316',
        textColor: '#FDBA74',
      };
    case 'moderate':
      return {
        bg: 'rgba(60, 40, 8, 0.85)',
        border: '1px solid rgba(245, 158, 11, 0.35)',
        iconColor: '#F59E0B',
        textColor: '#FCD34D',
      };
    case 'low':
      return {
        bg: 'rgba(6, 44, 30, 0.85)',
        border: '1px solid rgba(16, 185, 129, 0.35)',
        iconColor: '#10B981',
        textColor: '#6EE7B7',
      };
    default:
      return {
        bg: 'rgba(30, 41, 59, 0.85)',
        border: '1px solid rgba(100, 116, 139, 0.35)',
        iconColor: '#94A3B8',
        textColor: '#CBD5E1',
      };
  }
}
