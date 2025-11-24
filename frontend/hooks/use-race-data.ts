"use client";

import { useState, useEffect, useCallback } from "react";
import { apiClient } from "@/lib/api-client";
import type {
  PaceForecastResponse,
  DegradationResponse,
  PitWindowResponse,
  ThreatDetectionResponse,
  CurrentPaceResponse,
} from "@/types/api";

export interface RaceState {
  carId: string;
  sessionId: string;
  currentLap: number;
  currentPosition: number;
  totalLaps: number;
}

export function usePaceForecast(raceState: RaceState, lapsAhead: number = 5) {
  const [data, setData] = useState<PaceForecastResponse | null>(null);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState<Error | null>(null);

  const fetchData = useCallback(async () => {
    setLoading(true);
    setError(null);

    try {
      const response = await apiClient.getPaceForecast({
        car_id: raceState.carId,
        session_id: raceState.sessionId,
        current_lap: raceState.currentLap,
        laps_ahead: lapsAhead,
      });
      setData(response);
    } catch (err) {
      setError(err as Error);
    } finally {
      setLoading(false);
    }
  }, [raceState, lapsAhead]);

  useEffect(() => {
    fetchData();
  }, [fetchData]);

  return { data, loading, error, refetch: fetchData };
}

export function useDegradation(raceState: RaceState) {
  const [data, setData] = useState<DegradationResponse | null>(null);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState<Error | null>(null);

  const fetchData = useCallback(async () => {
    setLoading(true);
    setError(null);

    try {
      const response = await apiClient.getDegradationAnalysis({
        car_id: raceState.carId,
        session_id: raceState.sessionId,
        current_lap: raceState.currentLap,
      });
      setData(response);
    } catch (err) {
      setError(err as Error);
    } finally {
      setLoading(false);
    }
  }, [raceState]);

  useEffect(() => {
    fetchData();
  }, [fetchData]);

  return { data, loading, error, refetch: fetchData };
}

export function usePitWindow(raceState: RaceState) {
  const [data, setData] = useState<PitWindowResponse | null>(null);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState<Error | null>(null);

  const fetchData = useCallback(async () => {
    setLoading(true);
    setError(null);

    try {
      const response = await apiClient.getPitWindowRecommendation({
        car_id: raceState.carId,
        session_id: raceState.sessionId,
        current_lap: raceState.currentLap,
        current_position: raceState.currentPosition,
        total_laps: raceState.totalLaps,
      });
      setData(response);
    } catch (err) {
      setError(err as Error);
    } finally {
      setLoading(false);
    }
  }, [raceState]);

  useEffect(() => {
    fetchData();
  }, [fetchData]);

  return { data, loading, error, refetch: fetchData };
}

export function useThreatDetection(raceState: RaceState) {
  const [data, setData] = useState<ThreatDetectionResponse | null>(null);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState<Error | null>(null);

  const fetchData = useCallback(async () => {
    setLoading(true);
    setError(null);

    try {
      const response = await apiClient.getThreatAnalysis({
        car_id: raceState.carId,
        session_id: raceState.sessionId,
        current_lap: raceState.currentLap,
      });
      setData(response);
    } catch (err) {
      setError(err as Error);
    } finally {
      setLoading(false);
    }
  }, [raceState]);

  useEffect(() => {
    fetchData();
  }, [fetchData]);

  return { data, loading, error, refetch: fetchData };
}

export function useCurrentPace(carId: string) {
  const [data, setData] = useState<CurrentPaceResponse | null>(null);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState<Error | null>(null);

  const fetchData = useCallback(async () => {
    setLoading(true);
    setError(null);

    try {
      const response = await apiClient.getCurrentPace(carId);
      setData(response);
    } catch (err) {
      setError(err as Error);
    } finally {
      setLoading(false);
    }
  }, [carId]);

  useEffect(() => {
    fetchData();
  }, [fetchData]);

  return { data, loading, error, refetch: fetchData };
}

// Auto-refresh hook for live updates
export function useAutoRefresh(
  callback: () => void,
  interval: number = 5000,
  enabled: boolean = true
) {
  useEffect(() => {
    if (!enabled) return;

    const timer = setInterval(callback, interval);
    return () => clearInterval(timer);
  }, [callback, interval, enabled]);
}
