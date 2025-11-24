"use client";

import { useState } from "react";
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from "@/components/ui/card";
import { Button } from "@/components/ui/button";
import { PaceForecastChart } from "@/components/dashboard/pace-forecast-chart";
import { DegradationMonitor } from "@/components/dashboard/degradation-monitor";
import { ThreatMonitor } from "@/components/dashboard/threat-monitor";
import { PitWindowPanel } from "@/components/dashboard/pit-window-panel";
import { TrackMap } from "@/components/dashboard/track-map";
import {
  usePaceForecast,
  useDegradation,
  usePitWindow,
  useThreatDetection,
  useCurrentPace,
  useAutoRefresh,
  type RaceState,
} from "@/hooks/use-race-data";
import { Play, Pause, RefreshCw } from "lucide-react";

export default function DashboardPage() {
  // Race state
  const [raceState, setRaceState] = useState<RaceState>({
    carId: "GR86-002-000",
    sessionId: "R1",
    currentLap: 12,
    currentPosition: 5,
    totalLaps: 27,
  });

  const [autoRefreshEnabled, setAutoRefreshEnabled] = useState(true);

  // Fetch data using hooks
  const paceForecast = usePaceForecast(raceState);
  const degradation = useDegradation(raceState);
  const pitWindow = usePitWindow(raceState);
  const threat = useThreatDetection(raceState);
  const currentPace = useCurrentPace(raceState.carId);

  // Auto-refresh every 5 seconds
  useAutoRefresh(() => {
    paceForecast.refetch();
    degradation.refetch();
    pitWindow.refetch();
    threat.refetch();
    currentPace.refetch();
  }, 5000, autoRefreshEnabled);

  const handleRefreshAll = () => {
    paceForecast.refetch();
    degradation.refetch();
    pitWindow.refetch();
    threat.refetch();
    currentPace.refetch();
  };

  const handleNextLap = () => {
    setRaceState((prev) => ({
      ...prev,
      currentLap: Math.min(prev.currentLap + 1, prev.totalLaps),
    }));
  };

  return (
    <div className="min-h-screen bg-background">
      {/* Header */}
      <header className="border-b bg-card sticky top-0 z-10">
        <div className="container mx-auto px-4 py-4">
          <div className="flex items-center justify-between">
            <div>
              <h1 className="text-3xl font-bold">RaceCraft Live</h1>
              <p className="text-sm text-muted-foreground">
                Real-time race strategy intelligence for GR Cup
              </p>
            </div>
            <div className="flex items-center gap-4">
              <div className="flex items-center gap-2 bg-primary/10 px-4 py-2 rounded-lg">
                <div className="h-2 w-2 bg-green-500 rounded-full animate-pulse" />
                <span className="text-sm font-medium">LIVE</span>
              </div>
              <Button
                variant="outline"
                size="sm"
                onClick={() => setAutoRefreshEnabled(!autoRefreshEnabled)}
              >
                {autoRefreshEnabled ? (
                  <>
                    <Pause className="h-4 w-4 mr-1" />
                    Pause
                  </>
                ) : (
                  <>
                    <Play className="h-4 w-4 mr-1" />
                    Resume
                  </>
                )}
              </Button>
              <Button variant="outline" size="sm" onClick={handleRefreshAll}>
                <RefreshCw className="h-4 w-4 mr-1" />
                Refresh
              </Button>
            </div>
          </div>
        </div>
      </header>

      {/* Session Info Bar */}
      <div className="border-b bg-muted/30">
        <div className="container mx-auto px-4 py-3">
          <div className="grid grid-cols-6 gap-4 text-sm">
            <div>
              <p className="text-muted-foreground">Track</p>
              <p className="font-semibold">Barber Motorsports Park</p>
            </div>
            <div>
              <p className="text-muted-foreground">Session</p>
              <p className="font-semibold">{raceState.sessionId}</p>
            </div>
            <div>
              <p className="text-muted-foreground">Driver</p>
              <p className="font-semibold">{raceState.carId}</p>
            </div>
            <div>
              <p className="text-muted-foreground">Lap</p>
              <p className="font-semibold">
                {raceState.currentLap}/{raceState.totalLaps}
              </p>
            </div>
            <div>
              <p className="text-muted-foreground">Position</p>
              <p className="font-semibold">P{raceState.currentPosition}</p>
            </div>
            <div>
              <p className="text-muted-foreground">Current Pace</p>
              <p className="font-semibold font-mono">
                {currentPace.data?.current_lap_time.toFixed(3)}s
              </p>
            </div>
          </div>
        </div>
      </div>

      {/* Main Dashboard Grid */}
      <main className="container mx-auto px-4 py-6">
        <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">
          {/* Pace Forecast */}
          <div className="lg:col-span-2">
            <PaceForecastChart
              data={paceForecast.data}
              loading={paceForecast.loading}
            />
          </div>

          {/* Pit Strategy */}
          <div>
            <PitWindowPanel
              data={pitWindow.data}
              loading={pitWindow.loading}
            />
          </div>

          {/* Degradation */}
          <div>
            <DegradationMonitor
              data={degradation.data}
              loading={degradation.loading}
            />
          </div>

          {/* Track Map */}
          <div className="lg:col-span-2">
            <Card>
              <CardHeader>
                <CardTitle>Track Map</CardTitle>
                <CardDescription>Live vehicle positions on Barber Motorsports Park</CardDescription>
              </CardHeader>
              <CardContent>
                <div className="h-96">
                  <TrackMap
                    vehicles={[
                      {
                        vehicleId: raceState.carId,
                        lat: 33.5419,
                        lon: -86.4625,
                        speed: 125,
                        heading: 45,
                        position: raceState.currentPosition,
                        lapDistance: 1200,
                      },
                      {
                        vehicleId: "GR86-004-78",
                        lat: 33.5415,
                        lon: -86.4620,
                        speed: 128,
                        heading: 30,
                        position: 4,
                        lapDistance: 1300,
                      },
                    ]}
                    focusedVehicle={raceState.carId}
                    showRacingLine={true}
                  />
                </div>
              </CardContent>
            </Card>
          </div>

          {/* Threat Monitor */}
          <div className="lg:col-span-2">
            <ThreatMonitor
              data={threat.data}
              loading={threat.loading}
            />
          </div>

          {/* Current Stats */}
          <div className="lg:col-span-2">
            <Card>
              <CardHeader>
                <CardTitle>Current Session Stats</CardTitle>
                <CardDescription>Real-time performance metrics</CardDescription>
              </CardHeader>
              <CardContent>
                <div className="grid grid-cols-4 gap-4">
                  <div className="border rounded-lg p-4">
                    <p className="text-sm text-muted-foreground mb-1">Best Lap</p>
                    <p className="text-2xl font-mono font-bold">
                      {currentPace.data?.best_lap.toFixed(3)}s
                    </p>
                  </div>
                  <div className="border rounded-lg p-4">
                    <p className="text-sm text-muted-foreground mb-1">Average Lap</p>
                    <p className="text-2xl font-mono font-bold">
                      {currentPace.data?.average_lap.toFixed(3)}s
                    </p>
                  </div>
                  <div className="border rounded-lg p-4">
                    <p className="text-sm text-muted-foreground mb-1">Delta to Best</p>
                    <p className="text-2xl font-mono font-bold text-yellow-600">
                      +{((currentPace.data?.current_lap_time || 0) - (currentPace.data?.best_lap || 0)).toFixed(3)}s
                    </p>
                  </div>
                  <div className="border rounded-lg p-4">
                    <p className="text-sm text-muted-foreground mb-1">Laps Remaining</p>
                    <p className="text-2xl font-mono font-bold">
                      {raceState.totalLaps - raceState.currentLap}
                    </p>
                  </div>
                </div>
              </CardContent>
            </Card>
          </div>
        </div>

        {/* Demo Controls */}
        <div className="mt-6 p-4 border rounded-lg bg-muted/30">
          <div className="flex items-center justify-between">
            <div>
              <p className="font-semibold">Demo Controls</p>
              <p className="text-sm text-muted-foreground">
                Simulate race progression (using sample data)
              </p>
            </div>
            <Button onClick={handleNextLap} disabled={raceState.currentLap >= raceState.totalLaps}>
              Next Lap ({raceState.currentLap + 1})
            </Button>
          </div>
        </div>
      </main>
    </div>
  );
}
