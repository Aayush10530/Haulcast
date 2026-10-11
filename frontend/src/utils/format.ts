/**
 * Formatting utilities for Haulcast UI.
 * Pure display formatters - no business logic, no timezone conversion.
 */

/**
 * Formats a duration in seconds into a compact string:
 * e.g. 46560 -> "12h 56m", 2820 -> "47m", 0 -> "0m".
 */
export function formatDuration(seconds: number): string {
  if (!seconds || seconds <= 0) return '0m';
  const totalMinutes = Math.floor(seconds / 60 + 0.5);
  const hours = Math.floor(totalMinutes / 60);
  const minutes = totalMinutes % 60;
  if (hours > 0) {
    return `${hours}h ${minutes}m`;
  }
  return `${minutes}m`;
}

/**
 * Formats miles: 1 decimal place for under 100, otherwise an integer with thousands separator.
 * e.g. 51.2 -> "51.2 mi", 799 -> "799 mi", 1240.4 -> "1,240 mi".
 */
export function formatMiles(miles: number): string {
  if (miles === null || miles === undefined || isNaN(miles)) return '0 mi';
  if (miles < 100) {
    return `${miles.toFixed(1)} mi`;
  }
  return `${Math.round(miles).toLocaleString('en-US')} mi`;
}

/**
 * Formats checkpoint miles: integer when whole ("50 mi", "0 mi"), otherwise one decimal ("37.5 mi").
 */
export function formatCheckpointMiles(miles: number): string {
  if (miles === null || miles === undefined || isNaN(miles)) return '0 mi';
  if (Number.isInteger(miles) || Math.abs(miles - Math.round(miles)) < 1e-6) {
    return `${Math.round(miles)} mi`;
  }
  return `${miles.toFixed(1)} mi`;
}

const ISO_REGEX = /^(\d{4})-(\d{2})-(\d{2})T(\d{2}):(\d{2})(?::(\d{2})(?:\.\d+)?)?(?:(Z|[+-]\d{2}(?::?\d{2})?))?$/i;

/**
 * Formats an ISO 8601 datetime string with fractional seconds of any length and UTC offsets
 * into a wall-clock string:
 * e.g. "2026-10-12T18:28:00-06:00" with "America/Denver" -> "Mon Oct 12, 18:28 MDT"
 *
 * CRITICAL: The clock text comes directly from the ISO string and is never converted
 * to the browser's local timezone. On parse failure, returns "Time unavailable".
 */
export function formatLocalTime(isoWithOffset: string, tzName?: string): string {
  if (!isoWithOffset || typeof isoWithOffset !== 'string') return 'Time unavailable';
  const trimmed = isoWithOffset.trim();
  const match = ISO_REGEX.exec(trimmed);
  if (!match) return 'Time unavailable';

  const year = parseInt(match[1], 10);
  const month = parseInt(match[2], 10) - 1;
  const day = parseInt(match[3], 10);
  const hours = match[4];
  const minutes = match[5];
  const seconds = match[6] ? parseInt(match[6], 10) : 0;
  const offset = match[7];

  if (
    month < 0 ||
    month > 11 ||
    day < 1 ||
    day > 31 ||
    parseInt(hours, 10) > 23 ||
    parseInt(minutes, 10) > 59 ||
    seconds > 59
  ) {
    return 'Time unavailable';
  }

  // Determine weekday and month name purely in UTC to avoid browser DST or timezone shift
  const utcDate = new Date(Date.UTC(year, month, day, 12, 0, 0));
  if (isNaN(utcDate.getTime()) || utcDate.getUTCMonth() !== month || utcDate.getUTCDate() !== day) {
    return 'Time unavailable';
  }

  const dateFormatted = new Intl.DateTimeFormat('en-US', {
    weekday: 'short',
    month: 'short',
    day: 'numeric',
    timeZone: 'UTC',
  })
    .format(utcDate)
    .replace(',', ''); // "Tue, Oct 13" -> "Tue Oct 13"

  // Determine the instant for timezone abbreviation
  let instant: Date | null = null;
  if (offset) {
    const normalized = trimmed.replace(/(\.\d+)/, (m) => m.slice(0, 4));
    const parsed = Date.parse(normalized);
    if (!isNaN(parsed)) {
      instant = new Date(parsed);
    }
  }
  if (!instant) {
    instant = new Date(Date.UTC(year, month, day, parseInt(hours, 10), parseInt(minutes, 10), seconds));
  }

  let tzLabel = '';
  if (tzName) {
    try {
      const parts = new Intl.DateTimeFormat('en-US', {
        timeZone: tzName,
        timeZoneName: 'short',
      }).formatToParts(instant);
      const tzPart = parts.find((p) => p.type === 'timeZoneName');
      if (tzPart) tzLabel = tzPart.value;
    } catch {
      // Fall back to offset if tzName is invalid
    }
  }

  if (!tzLabel && offset) {
    if (offset.toUpperCase() === 'Z' || offset === '+00:00' || offset === '-00:00') {
      tzLabel = 'UTC';
    } else {
      const sign = offset.startsWith('+') ? '+' : '-';
      const clean = offset.replace('+', '').replace('-', '');
      const parts = clean.split(':');
      const offH = parseInt(parts[0], 10);
      const offM = parts[1] || '00';
      tzLabel = offM === '00' ? `UTC${sign}${offH}` : `UTC${sign}${offH}:${offM}`;
    }
  }

  const result = `${dateFormatted}, ${hours}:${minutes}${tzLabel ? ' ' + tzLabel : ''}`;
  return result.replace(/\u202f/g, ' ');
}

/**
 * Formats delta versus the fastest route in seconds:
 * e.g. 2820 -> "+47 min", 3900 -> "+1 h 05 min", 0 -> "".
 */
export function formatDelta(deltaSeconds: number): string {
  if (!deltaSeconds || deltaSeconds <= 0) return '';
  const totalMinutes = Math.floor(deltaSeconds / 60 + 0.5);
  if (totalMinutes < 60) {
    return `+${totalMinutes} min`;
  }
  const hours = Math.floor(totalMinutes / 60);
  const minutes = totalMinutes % 60;
  return `+${hours} h ${String(minutes).padStart(2, '0')} min`;
}
