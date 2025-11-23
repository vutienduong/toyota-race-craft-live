"use client";

import { Card, CardContent, CardDescription, CardHeader, CardTitle } from "@/components/ui/card";
import type { PitWindowResponse } from "@/types/api";
import { Flag, TrendingDown, TrendingUp, AlertCircle } from "lucide-react";

interface PitWindowPanelProps {
  data: PitWindowResponse | null;
  loading?: boolean;
}

export function PitWindowPanel({ data, loading }: PitWindowPanelProps) {
  if (loading) {
    return (
      <Card>
        <CardHeader>
          <CardTitle>Pit Strategy</CardTitle>
          <CardDescription>Calculating optimal window...</CardDescription>
        </CardHeader>
        <CardContent className="h-[250px] flex items-center justify-center">
          <div className="animate-pulse text-muted-foreground">Optimizing...</div>
        </CardContent>
      </Card>
    );
  }

  if (!data) {
    return (
      <Card>
        <CardHeader>
          <CardTitle>Pit Strategy</CardTitle>
          <CardDescription>No pit window data available</CardDescription>
        </CardHeader>
        <CardContent className="h-[250px]" />
      </Card>
    );
  }

  const getTrafficIcon = (risk: string) => {
    switch (risk) {
      case "low":
        return <TrendingDown className="h-4 w-4 text-green-600" />;
      case "medium":
        return <AlertCircle className="h-4 w-4 text-yellow-600" />;
      case "high":
        return <TrendingUp className="h-4 w-4 text-red-600" />;
    }
  };

  const getTrafficColor = (risk: string) => {
    switch (risk) {
      case "low":
        return "text-green-600";
      case "medium":
        return "text-yellow-600";
      case "high":
        return "text-red-600";
    }
  };

  const bestWindow = data.recommended_windows[0];

  return (
    <Card>
      <CardHeader>
        <CardTitle>Pit Window Recommendation</CardTitle>
        <CardDescription>
          Optimal strategy based on pace degradation and traffic
        </CardDescription>
      </CardHeader>
      <CardContent>
        <div className="mb-4 p-4 bg-primary/10 border border-primary rounded-lg">
          <div className="flex items-center justify-between mb-2">
            <div className="flex items-center gap-2">
              <Flag className="h-5 w-5 text-primary" />
              <span className="font-semibold">Optimal Window</span>
            </div>
            <span className="text-sm text-muted-foreground">
              {(bestWindow.confidence * 100).toFixed(0)}% confidence
            </span>
          </div>
          <div className="text-2xl font-bold mb-1">
            Laps {bestWindow.start_lap}-{bestWindow.end_lap}
          </div>
          <div className="text-sm text-muted-foreground">
            {data.reason}
          </div>
        </div>

        <div className="grid grid-cols-2 gap-4 mb-4">
          <div className="border rounded p-3">
            <p className="text-xs text-muted-foreground mb-1">Best Lap to Pit</p>
            <p className="text-2xl font-bold">{data.optimal_lap}</p>
          </div>
          <div className="border rounded p-3">
            <p className="text-xs text-muted-foreground mb-1">Expected Position Change</p>
            <p className={`text-2xl font-bold ${
              bestWindow.expected_position_loss <= 0 ? "text-green-600" : "text-red-600"
            }`}>
              {bestWindow.expected_position_loss > 0 ? "-" : "+"}
              {Math.abs(bestWindow.expected_position_loss)}
            </p>
          </div>
        </div>

        {bestWindow.undercut_opportunity !== undefined && (
          <div className="mb-4 p-3 bg-green-50 border border-green-200 rounded">
            <p className="text-sm font-semibold text-green-800">Undercut Opportunity</p>
            <p className="text-green-700">
              Potential gain: +{bestWindow.undercut_opportunity.toFixed(2)}s
            </p>
          </div>
        )}

        <div className="space-y-2">
          <p className="text-sm font-semibold">All Windows:</p>
          {data.recommended_windows.map((window, idx) => (
            <div key={idx} className={`border rounded p-3 ${idx === 0 ? "border-primary bg-primary/5" : ""}`}>
              <div className="flex items-center justify-between mb-1">
                <span className="font-medium">
                  Laps {window.start_lap}-{window.end_lap}
                </span>
                <div className="flex items-center gap-2">
                  {getTrafficIcon(window.traffic_risk)}
                  <span className={`text-xs ${getTrafficColor(window.traffic_risk)}`}>
                    {window.traffic_risk} traffic
                  </span>
                </div>
              </div>
              <div className="grid grid-cols-2 gap-2 text-xs text-muted-foreground">
                <div>
                  Confidence: {(window.confidence * 100).toFixed(0)}%
                </div>
                <div>
                  Position: {window.expected_position_loss > 0 ? "-" : "+"}
                  {Math.abs(window.expected_position_loss)}
                </div>
              </div>
            </div>
          ))}
        </div>
      </CardContent>
    </Card>
  );
}
