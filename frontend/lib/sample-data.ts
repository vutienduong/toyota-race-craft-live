// Sample Data for Frontend-Only Mode (No Backend Required)
// Used when NEXT_PUBLIC_DATA_MODE=sample

import type {
  PaceForecastResponse,
  DegradationResponse,
  PitWindowResponse,
  ThreatDetectionResponse,
  CurrentPaceResponse,
  CurrentDegradationResponse,
} from "@/types/api";

// Sample Vehicles for GR Cup
export const SAMPLE_VEHICLES = [
  { vehicle_id: "GR86-002-000", vehicle_number: 2, display_name: "Car #2 (GR86-002-000)" },
  { vehicle_id: "GR86-004-78", vehicle_number: 4, display_name: "Car #4 (GR86-004-78)" },
  { vehicle_id: "GR86-007-13", vehicle_number: 7, display_name: "Car #7 (GR86-007-13)" },
  { vehicle_id: "GR86-010-25", vehicle_number: 10, display_name: "Car #10 (GR86-010-25)" },
  { vehicle_id: "GR86-015-42", vehicle_number: 15, display_name: "Car #15 (GR86-015-42)" },
];

// Sample Pace Forecast
export const getSamplePaceForecast = (carId: string, currentLap: number): PaceForecastResponse => {
  const baseLapTime = 92.5 + Math.random() * 2;
  const trend = Math.random() > 0.5 ? "degrading" : "stable";

  const predictions = Array.from({ length: 5 }, (_, i) => {
    const lapNumber = currentLap + i + 1;
    const degradation = trend === "degrading" ? i * 0.15 : i * 0.05;
    const noise = (Math.random() - 0.5) * 0.2;
    const predictedTime = baseLapTime + degradation + noise;

    return {
      lap_number: lapNumber,
      predicted_time: predictedTime,
      delta: degradation + noise,
      confidence: Math.max(0.6, 0.9 - i * 0.06),
    };
  });

  return {
    car_id: carId,
    predictions,
    current_pace: baseLapTime,
    trend: trend as "improving" | "stable" | "degrading",
  };
};

// Sample Current Pace
export const getSampleCurrentPace = (carId: string): CurrentPaceResponse => {
  const bestLap = 91.8 + Math.random() * 1.5;
  const currentLap = bestLap + Math.random() * 1.2;

  return {
    car_id: carId,
    current_lap_time: currentLap,
    sector_times: [28.5, 32.8, 30.9],
    best_lap: bestLap,
    average_lap: bestLap + 0.8,
  };
};

// Sample Degradation Analysis
export const getSampleDegradation = (carId: string, currentLap: number): DegradationResponse => {
  const stintLength = currentLap % 15 || 1; // Simulate pit stops every ~15 laps
  const degradationLevel = Math.min(stintLength / 15, 1);

  const degradationCurve = Array.from({ length: Math.min(10, stintLength) }, (_, i) => {
    const lap = currentLap - Math.min(10, stintLength) + i + 1;
    const delta = (i / 10) * 2.5 * degradationLevel;

    return {
      lap,
      delta_seconds: delta,
      severity: Math.min(i / 15, 1),
    };
  });

  const causes = [];
  if (degradationLevel > 0.5) {
    causes.push({
      cause_type: "lateral_grip_loss" as const,
      confidence: 0.75,
      indicators: ["Reduced lateral G in corners", "Understeering detected"],
    });
  }
  if (degradationLevel > 0.7) {
    causes.push({
      cause_type: "understeer" as const,
      confidence: 0.68,
      indicators: ["Increased steering angle", "Compensation for grip loss"],
    });
  }

  const stintHealth = degradationLevel < 0.3 ? "optimal"
    : degradationLevel < 0.6 ? "degrading"
    : "critical";

  return {
    car_id: carId,
    degradation_curve: degradationCurve,
    degradation_rate: degradationLevel * 0.15,
    primary_causes: causes,
    stint_health: stintHealth as "fresh" | "optimal" | "degrading" | "critical",
    recommended_action: stintHealth === "critical"
      ? "Consider pit window in next 2-3 laps"
      : "Monitor closely",
  };
};

// Sample Current Degradation
export const getSampleCurrentDegradation = (carId: string): CurrentDegradationResponse => {
  const lapsOnTires = Math.floor(Math.random() * 15) + 1;
  const degradation = Math.min(lapsOnTires / 15, 1);

  return {
    car_id: carId,
    current_degradation: degradation,
    laps_on_tires: lapsOnTires,
    estimated_laps_remaining: Math.max(0, 15 - lapsOnTires),
    grip_level: 1 - degradation * 0.3,
  };
};

// Sample Pit Window Recommendation
export const getSamplePitWindow = (
  carId: string,
  currentLap: number,
  totalLaps: number
): PitWindowResponse => {
  const optimalLap = Math.floor(totalLaps * 0.5) + Math.floor(Math.random() * 3);
  const windowStart = Math.max(currentLap + 2, optimalLap - 2);
  const windowEnd = Math.min(totalLaps - 3, optimalLap + 2);

  return {
    car_id: carId,
    recommended_windows: [
      {
        start_lap: windowStart,
        end_lap: windowEnd,
        confidence: 0.85,
        expected_position_loss: Math.floor(Math.random() * 2) + 1,
        undercut_opportunity: Math.random() * 1.5,
        traffic_risk: Math.random() > 0.7 ? "high" : Math.random() > 0.4 ? "medium" : "low",
      },
    ],
    optimal_lap: optimalLap,
    reason: currentLap < totalLaps * 0.4
      ? "Early pit strategy to undercut rivals with fresh tires"
      : currentLap > totalLaps * 0.6
      ? "Late pit for tire advantage in final stint"
      : "Standard pit window based on degradation analysis",
  };
};

// Sample Threat Detection
export const getSampleThreatDetection = (carId: string, currentLap: number): ThreatDetectionResponse => {
  const hasThreats = Math.random() > 0.3;

  const threats = hasThreats ? [
    {
      rival_car_id: "GR86-004-78",
      gap_seconds: 1.2 + Math.random() * 2,
      closing_rate: Math.random() * 0.3,
      attack_probability: 0.65 + Math.random() * 0.25,
      laps_until_attack: Math.floor(Math.random() * 3) + 2,
      sector_advantages: [
        { sector: 2, time_delta: -0.15, corner: "Turn 5-7" },
        { sector: 3, time_delta: -0.08, corner: "Turn 10" },
      ],
      defensive_recommendation: "Focus on corner entry Turn 5, rival gaining 0.15s in Sector 2",
    },
  ] : [];

  const overallThreatLevel = !hasThreats ? "low"
    : threats[0]?.gap_seconds < 1.5 ? "high"
    : threats[0]?.gap_seconds < 3.0 ? "medium"
    : "low";

  return {
    car_id: carId,
    threats,
    overall_threat_level: overallThreatLevel as "low" | "medium" | "high" | "critical",
  };
};

// Helper to add random delay to simulate API call
export const simulateApiDelay = (minMs = 200, maxMs = 800): Promise<void> => {
  const delay = minMs + Math.random() * (maxMs - minMs);
  return new Promise(resolve => setTimeout(resolve, delay));
};
