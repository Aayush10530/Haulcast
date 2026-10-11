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
  const totalMinutes = Math.round(seconds / 60);
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

const KNOWN_US_OFFSETS: Record<string, string> = {
  '-04:00': 'EDT',
  '-05:00': 'EST/CDT',
  '-06:00': 'CST/CDT',
  '-07:00': 'MST/PDT',
  '-08:00': 'PST',
  'Z': 'UTC',
  '+00:00': 'UTC',
};

/**
 * Formats an ISO datetime string with offset (e.g. "2026-10-13T08:15:00-06:00")
 * into a wall-clock string:
 * "Tue Oct 13, 08:15 CST/CDT" (or resolved timezone abbreviation like "CDT" if tzName is provided).
 *
 * CRITICAL: This extracts the wall-clock components directly from the string and
 * formats without converting to the browser's local timezone.
 */
export function formatLocalTime(isoWithOffset: string, tzName?: string): string {
  if (!isoWithOffset) return '';
  const trimmed = isoWithOffset.trim();
  const match = /^(\d{4})-(\d{2})-(\d{2})T(\d{2}):(\d{2})(?::\d{2})?(?:([+-]\d{2}:\d{2})|Z)?$/.exec(
    trimmed,
  );
  if (!match) return trimmed;

  const year = parseInt(match[1], 10);
  const month = parseInt(match[2], 10) - 1;
  const day = parseInt(match[3], 10);
  const hours = match[4];
  const minutes = match[5];
  const offset = match[6] || (trimmed.endsWith('Z') ? 'Z' : '');

  // Determine weekday and month name purely in UTC to avoid browser DST or timezone shift
  const utcDate = new Date(Date.UTC(year, month, day, 12, 0, 0));
  const dateFormatted = new Intl.DateTimeFormat('en-US', {
    weekday: 'short',
    month: 'short',
    day: 'numeric',
    timeZone: 'UTC',
  })
    .format(utcDate)
    .replace(',', ''); // "Tue, Oct 13" -> "Tue Oct 13"

  let tzLabel = '';
  if (tzName) {
    try {
      const parts = new Intl.DateTimeFormat('en-US', {
        timeZone: tzName,
        timeZoneName: 'short',
      }).formatToParts(utcDate);
      const tzPart = parts.find((p) => p.type === 'timeZoneName');
      if (tzPart) tzLabel = tzPart.value;
    } catch {
      // Fallback to offset mapping below
    }
  }

  if (!tzLabel && offset) {
    if (KNOWN_US_OFFSETS[offset]) {
      tzLabel = KNOWN_US_OFFSETS[offset];
    } else {
      const sign = offset.startsWith('+') ? '+' : '-';
      const offH = parseInt(offset.slice(1, 3), 10);
      const offM = offset.slice(4, 6);
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
  const totalMinutes = Math.round(deltaSeconds / 60);
  if (totalMinutes < 60) {
    return `+${totalMinutes} min`;
  }
  const hours = Math.floor(totalMinutes / 60);
  const minutes = totalMinutes % 60;
  return `+${hours} h ${String(minutes).padStart(2, '0')} min`;
}
