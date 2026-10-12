/**
 * API Data Transfer Objects (DTOs) for StormRoute.
 * Defined strictly per ARCHITECTURE.md §8 and backend API serializers.
 */

export type RiskLevelKey = 'low' | 'moderate' | 'high' | 'severe' | 'no_travel';

export type IntervalOption = 'auto' | 10 | 25 | 50;

export interface PlaceDTO {
  label: string;
  lat: number;
  lon: number;
}

export interface GeocodePlaceDTO extends PlaceDTO {
  id: string;
}

export interface TripRequestPayload {
  origin: PlaceDTO;
  destination: PlaceDTO;
  departure_local: string; // ISO naive local datetime "YYYY-MM-DDTHH:mm"
  load_weight_lb: number;
  interval: IntervalOption;
}

export interface WarningDTO {
  code: string;
  message: string;
}

export interface CheckpointWeatherDTO {
  wind_mph: number;
  rain_in_hr: number;
  snow_in_hr: number;
}

export interface CheckpointRiskDTO {
  level: RiskLevelKey;
  level_label?: string;
  driver: string;
  load_rule_applied: boolean;
  reason: string;
}

export interface CheckpointDTO {
  index: number;
  mile: number;
  lat: number;
  lon: number;
  eta_utc: string;
  eta_local: string;
  local_tz: string;
  covers_miles: [number, number];
  weather: CheckpointWeatherDTO | null;
  risk: CheckpointRiskDTO | null;
}

export interface RouteSummaryDTO {
  miles_by_level: Record<RiskLevelKey, number>;
  avg_risk_score: number | null;
  max_level: RiskLevelKey | null;
  has_no_travel: boolean;
  unavailable_miles?: number;
  delta_vs_fastest_seconds: number;
}

export interface RouteDTO {
  id: string;
  label: string;
  tags: string[];
  rank: number;
  via: string;
  distance_miles: number;
  duration_seconds: number;
  departure_utc: string;
  departure_tz?: string;
  arrival_utc: string;
  arrival_local: string;
  arrival_tz?: string;
  geometry: [number, number][];
  summary: RouteSummaryDTO;
  checkpoints: CheckpointDTO[];
}

export interface RecommendationComparisonDTO {
  route_id: string;
  severe_miles: number;
  high_miles: number;
  avg_risk_score: number | null;
  duration_seconds: number;
}

export interface RecommendationDTO {
  route_id: string;
  decided_by: string;
  headline: string;
  comparisons: RecommendationComparisonDTO[];
}

export interface RequestEchoDTO {
  origin: PlaceDTO;
  destination: PlaceDTO;
  departure_utc: string;
  departure_local: string;
  origin_timezone: string;
  load_weight_lb: number;
  interval_miles: number;
  interval_mode: string;
}

export interface AnalysisMetaDTO {
  routing_provider: string;
  weather_provider: string;
  weather_cells: number;
  route_count: number;
  elapsed_ms: number;
  routing_ms?: number;
  weather_ms?: number;
  in_process_ms?: number;
}

export interface AnalyzeResponse {
  request: RequestEchoDTO;
  recommended_route_id: string;
  recommendation: RecommendationDTO;
  routes: RouteDTO[];
  warnings: WarningDTO[];
  meta: AnalysisMetaDTO;
}

export interface ApiErrorEnvelope {
  error: {
    code: string;
    message: string;
    fields?: Record<string, string[] | string>;
  };
}

export interface HeatmapCellDTO {
  lat: number;
  lon: number;
}

export interface HeatmapFrameDTO {
  offset_hours: number;
  time_utc: string;
  time_local: string;
  overall: (number | null)[];
  wind: (number | null)[];
  rain: (number | null)[];
  snow: (number | null)[];
}

export interface TripHeatmapResponse {
  start_utc: string;
  start_local: string;
  origin_timezone: string;
  cells: HeatmapCellDTO[];
  frames: HeatmapFrameDTO[];
}
