"use client";

import { Card, CardContent, CardDescription, CardHeader, CardTitle } from "@/components/ui/card";
import type { ThreatDetectionResponse } from "@/types/api";
import { AlertTriangle, Shield, ShieldAlert, ShieldCheck } from "lucide-react";

interface ThreatMonitorProps {
  data: ThreatDetectionResponse | null;
  loading?: boolean;
}

export function ThreatMonitor({ data, loading }: ThreatMonitorProps) {
  if (loading) {
    return (
      <Card>
        <CardHeader>
          <CardTitle>Threat Radar</CardTitle>
          <CardDescription>Analyzing competitors...</CardDescription>
        </CardHeader>
        <CardContent className="h-[300px] flex items-center justify-center">
          <div className="animate-pulse text-muted-foreground">Analyzing threats...</div>
        </CardContent>
      </Card>
    );
  }

  if (!data) {
    return (
      <Card>
        <CardHeader>
          <CardTitle>Threat Radar</CardTitle>
          <CardDescription>No threat data available</CardDescription>
        </CardHeader>
        <CardContent className="h-[300px]" />
      </Card>
    );
  }

  const getThreatIcon = () => {
    switch (data.overall_threat_level) {
      case "low":
        return <ShieldCheck className="h-5 w-5 text-green-600" />;
      case "medium":
        return <Shield className="h-5 w-5 text-yellow-600" />;
      case "high":
        return <ShieldAlert className="h-5 w-5 text-orange-600" />;
      case "critical":
        return <AlertTriangle className="h-5 w-5 text-red-600" />;
    }
  };

  const getThreatColor = () => {
    switch (data.overall_threat_level) {
      case "low":
        return "text-green-600 bg-green-50 border-green-200";
      case "medium":
        return "text-yellow-600 bg-yellow-50 border-yellow-200";
      case "high":
        return "text-orange-600 bg-orange-50 border-orange-200";
      case "critical":
        return "text-red-600 bg-red-50 border-red-200";
    }
  };

  const getAttackProbabilityColor = (prob: number) => {
    if (prob >= 70) return "bg-red-500";
    if (prob >= 50) return "bg-orange-500";
    if (prob >= 30) return "bg-yellow-500";
    return "bg-green-500";
  };

  return (
    <Card>
      <CardHeader>
        <div className="flex items-center justify-between">
          <div>
            <CardTitle>Threat Radar</CardTitle>
            <CardDescription>
              Real-time competitor analysis and attack probability
            </CardDescription>
          </div>
          <div className={`flex items-center gap-2 px-3 py-1 rounded-full border ${getThreatColor()}`}>
            {getThreatIcon()}
            <span className="font-semibold capitalize">{data.overall_threat_level}</span>
          </div>
        </div>
      </CardHeader>
      <CardContent>
        {data.threats.length === 0 ? (
          <div className="h-[200px] flex items-center justify-center text-muted-foreground">
            <div className="text-center">
              <ShieldCheck className="h-12 w-12 mx-auto mb-2 text-green-600" />
              <p>No immediate threats detected</p>
            </div>
          </div>
        ) : (
          <div className="space-y-4">
            {data.threats.map((threat, idx) => (
              <div key={idx} className="border rounded-lg p-4 space-y-3">
                <div className="flex items-center justify-between">
                  <div>
                    <p className="font-semibold text-lg">{threat.rival_car_id}</p>
                    <p className="text-sm text-muted-foreground">
                      Gap: <span className="font-mono">{threat.gap_seconds.toFixed(1)}s</span>
                      {threat.closing_rate > 0 && (
                        <span className="ml-2 text-red-600">
                          (closing {threat.closing_rate.toFixed(2)}s/lap)
                        </span>
                      )}
                    </p>
                  </div>
                  <div className="text-right">
                    <p className="text-xs text-muted-foreground mb-1">Attack Probability</p>
                    <div className="relative w-24 h-24">
                      <svg className="w-full h-full transform -rotate-90">
                        <circle
                          cx="48"
                          cy="48"
                          r="40"
                          stroke="currentColor"
                          strokeWidth="8"
                          fill="none"
                          className="text-muted"
                        />
                        <circle
                          cx="48"
                          cy="48"
                          r="40"
                          stroke="currentColor"
                          strokeWidth="8"
                          fill="none"
                          strokeDasharray={`${threat.attack_probability * 2.51} 251`}
                          className={getAttackProbabilityColor(threat.attack_probability * 100)}
                        />
                      </svg>
                      <div className="absolute inset-0 flex items-center justify-center">
                        <span className="text-2xl font-bold">
                          {(threat.attack_probability * 100).toFixed(0)}%
                        </span>
                      </div>
                    </div>
                  </div>
                </div>

                {threat.laps_until_attack && (
                  <div className="bg-red-50 border border-red-200 rounded p-2 text-sm text-red-800">
                    <AlertTriangle className="inline h-4 w-4 mr-1" />
                    Potential attack in {threat.laps_until_attack} lap{threat.laps_until_attack > 1 ? "s" : ""}
                  </div>
                )}

                {threat.sector_advantages.length > 0 && (
                  <div>
                    <p className="text-xs font-semibold mb-2">Where they're faster:</p>
                    <div className="grid grid-cols-3 gap-2">
                      {threat.sector_advantages.map((sector, i) => (
                        <div key={i} className="text-xs bg-muted rounded p-2">
                          <p className="font-medium">
                            {sector.corner || `Sector ${sector.sector}`}
                          </p>
                          <p className={sector.time_delta > 0 ? "text-red-600" : "text-green-600"}>
                            {sector.time_delta >= 0 ? "+" : ""}
                            {sector.time_delta.toFixed(2)}s
                          </p>
                        </div>
                      ))}
                    </div>
                  </div>
                )}

                <div className="bg-blue-50 border border-blue-200 rounded p-2 text-sm text-blue-800">
                  <p className="font-medium">Defensive Strategy:</p>
                  <p>{threat.defensive_recommendation}</p>
                </div>
              </div>
            ))}
          </div>
        )}
      </CardContent>
    </Card>
  );
}
