// API Type Definitions for RaceCraft Live

export interface LapPrediction {
  lap_number: number;
  predicted_time: number;
  delta: number;
  confidence: number;
}

export interface PaceForecastRequest {
  car_id: string;
  session_id: string;
  current_lap: number;
  laps_ahead?: number;
}

export interface PaceForecastResponse {
  car_id: string;
  predictions: LapPrediction[];
  current_pace: number;
  trend: "improving" | "stable" | "degrading";
}

export interface DegradationPoint {
  lap: number;
  delta_seconds: number;
  severity: number; // 0-1
}

export interface DegradationCause {
  cause_type: "lateral_grip_loss" | "brake_fade" | "throttle_inconsistency" | "understeer";
  confidence: number;
  indicators: string[];
}

export interface DegradationRequest {
  car_id: string;
  session_id: string;
  current_lap: number;
}

export interface DegradationResponse {
  car_id: string;
  degradation_curve: DegradationPoint[];
  degradation_rate: number;
  primary_causes: DegradationCause[];
  stint_health: "fresh" | "optimal" | "degrading" | "critical";
  recommended_action: string;
}

export interface PitWindowRecommendation {
  start_lap: number;
  end_lap: number;
  confidence: number;
  expected_position_loss: number;
  undercut_opportunity?: number;
  traffic_risk: "low" | "medium" | "high";
}

export interface PitWindowRequest {
  car_id: string;
  session_id: string;
  current_lap: number;
  current_position: number;
  total_laps: number;
}

export interface PitWindowResponse {
  car_id: string;
  recommended_windows: PitWindowRecommendation[];
  optimal_lap: number;
  reason: string;
}

export interface SectorAdvantage {
  sector: number;
  time_delta: number;
  corner?: string;
}

export interface ThreatAnalysis {
  rival_car_id: string;
  gap_seconds: number;
  closing_rate: number;
  attack_probability: number;
  laps_until_attack?: number;
  sector_advantages: SectorAdvantage[];
  defensive_recommendation: string;
}

export interface ThreatDetectionRequest {
  car_id: string;
  session_id: string;
  current_lap: number;
}

export interface ThreatDetectionResponse {
  car_id: string;
  threats: ThreatAnalysis[];
  overall_threat_level: "low" | "medium" | "high" | "critical";
}

export interface CurrentPaceResponse {
  car_id: string;
  current_lap_time: number;
  sector_times: number[];
  best_lap: number;
  average_lap: number;
}

export interface CurrentDegradationResponse {
  car_id: string;
  current_degradation: number;
  laps_on_tires: number;
  estimated_laps_remaining: number;
  grip_level: number;
}
