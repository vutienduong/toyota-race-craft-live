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

const API_BASE_URL = process.env.NEXT_PUBLIC_API_URL || "http://localhost:8000";

class ApiClient {
  private baseUrl: string;

  constructor(baseUrl: string = API_BASE_URL) {
    this.baseUrl = baseUrl;
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
    return this.request<PaceForecastResponse>("/api/pace/forecast", {
      method: "POST",
      body: JSON.stringify(request),
    });
  }

  async getCurrentPace(carId: string): Promise<CurrentPaceResponse> {
    return this.request<CurrentPaceResponse>(`/api/pace/current/${carId}`);
  }

  // Degradation Analysis
  async getDegradationAnalysis(
    request: DegradationRequest
  ): Promise<DegradationResponse> {
    return this.request<DegradationResponse>("/api/degradation/analyze", {
      method: "POST",
      body: JSON.stringify(request),
    });
  }

  async getCurrentDegradation(
    carId: string
  ): Promise<CurrentDegradationResponse> {
    return this.request<CurrentDegradationResponse>(
      `/api/degradation/current/${carId}`
    );
  }

  // Pit Window Optimization
  async getPitWindowRecommendation(
    request: PitWindowRequest
  ): Promise<PitWindowResponse> {
    return this.request<PitWindowResponse>("/api/pit/recommend", {
      method: "POST",
      body: JSON.stringify(request),
    });
  }

  // Threat Detection
  async getThreatAnalysis(
    request: ThreatDetectionRequest
  ): Promise<ThreatDetectionResponse> {
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
    return this.request(`/api/vehicles/list/${sessionId}`);
  }

  // Health Check
  async healthCheck(): Promise<{ status: string }> {
    return this.request<{ status: string }>("/health");
  }
}

// Singleton instance
export const apiClient = new ApiClient();

// Export class for testing
export default ApiClient;
