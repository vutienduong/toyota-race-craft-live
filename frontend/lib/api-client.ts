// API Client for RaceCraft Live Backend

import {
  PaceForecastRequest,
  PaceForecastResponse,
  DegradationRequest,
  DegradationResponse,
  PitWindowRequest,
  PitWindowResponse,
  ThreatDetectionRequest,
  ThreatDetectionResponse,
  CurrentPaceResponse,
  CurrentDegradationResponse,
} from "@/types/api";
import {
  SAMPLE_VEHICLES,
  getSamplePaceForecast,
  getSampleCurrentPace,
  getSampleDegradation,
  getSampleCurrentDegradation,
  getSamplePitWindow,
  getSampleThreatDetection,
  simulateApiDelay,
} from "./sample-data";

const API_BASE_URL = process.env.NEXT_PUBLIC_API_URL || "http://localhost:8000";
const DATA_MODE = process.env.NEXT_PUBLIC_DATA_MODE || "backend";

class ApiClient {
  private baseUrl: string;
  private useSampleData: boolean;

  constructor(baseUrl: string = API_BASE_URL) {
    this.baseUrl = baseUrl;
    this.useSampleData = DATA_MODE === "sample";

    if (this.useSampleData) {
      console.log("[API Client] Running in SAMPLE DATA mode - no backend required");
    } else {
      console.log(`[API Client] Running in BACKEND mode - connecting to ${baseUrl}`);
    }
  }

  private async request<T>(
    endpoint: string,
    options?: RequestInit
  ): Promise<T> {
    const url = `${this.baseUrl}${endpoint}`;

    const response = await fetch(url, {
      ...options,
      headers: {
        "Content-Type": "application/json",
        ...options?.headers,
      },
    });

    if (!response.ok) {
      throw new Error(`API Error: ${response.status} ${response.statusText}`);
    }

    return response.json();
  }

  // Pace Forecasting
  async getPaceForecast(
    request: PaceForecastRequest
  ): Promise<PaceForecastResponse> {
    if (this.useSampleData) {
      await simulateApiDelay();
      return getSamplePaceForecast(request.car_id, request.current_lap);
    }
    return this.request<PaceForecastResponse>("/api/pace/forecast", {
      method: "POST",
      body: JSON.stringify(request),
    });
  }

  async getCurrentPace(carId: string): Promise<CurrentPaceResponse> {
    if (this.useSampleData) {
      await simulateApiDelay();
      return getSampleCurrentPace(carId);
    }
    return this.request<CurrentPaceResponse>(`/api/pace/current/${carId}`);
  }

  // Degradation Analysis
  async getDegradationAnalysis(
    request: DegradationRequest
  ): Promise<DegradationResponse> {
    if (this.useSampleData) {
      await simulateApiDelay();
      return getSampleDegradation(request.car_id, request.current_lap);
    }
    return this.request<DegradationResponse>("/api/degradation/analyze", {
      method: "POST",
      body: JSON.stringify(request),
    });
  }

  async getCurrentDegradation(
    carId: string
  ): Promise<CurrentDegradationResponse> {
    if (this.useSampleData) {
      await simulateApiDelay();
      return getSampleCurrentDegradation(carId);
    }
    return this.request<CurrentDegradationResponse>(
      `/api/degradation/current/${carId}`
    );
  }

  // Pit Window Optimization
  async getPitWindowRecommendation(
    request: PitWindowRequest
  ): Promise<PitWindowResponse> {
    if (this.useSampleData) {
      await simulateApiDelay();
      return getSamplePitWindow(request.car_id, request.current_lap, request.total_laps);
    }
    return this.request<PitWindowResponse>("/api/pit/recommend", {
      method: "POST",
      body: JSON.stringify(request),
    });
  }

  // Threat Detection
  async getThreatAnalysis(
    request: ThreatDetectionRequest
  ): Promise<ThreatDetectionResponse> {
    if (this.useSampleData) {
      await simulateApiDelay();
      return getSampleThreatDetection(request.car_id, request.current_lap);
    }
    return this.request<ThreatDetectionResponse>("/api/threat/analyze", {
      method: "POST",
      body: JSON.stringify(request),
    });
  }

  // Vehicles
  async getAvailableVehicles(
    sessionId: string = "R1"
  ): Promise<{
    vehicles: Array<{ vehicle_id: string; vehicle_number: number; display_name: string }>;
    session_id: string;
  }> {
    if (this.useSampleData) {
      await simulateApiDelay(100, 300);
      return {
        vehicles: SAMPLE_VEHICLES,
        session_id: sessionId,
      };
    }
    return this.request(`/api/vehicles/list/${sessionId}`);
  }

  // Health Check
  async healthCheck(): Promise<{ status: string }> {
    if (this.useSampleData) {
      return Promise.resolve({ status: "ok (sample mode)" });
    }
    return this.request<{ status: string }>("/health");
  }
}

// Singleton instance
export const apiClient = new ApiClient();

// Export class for testing
export default ApiClient;
