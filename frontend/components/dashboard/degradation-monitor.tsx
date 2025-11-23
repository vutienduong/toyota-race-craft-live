"use client";

import { Card, CardContent, CardDescription, CardHeader, CardTitle } from "@/components/ui/card";
import { LineChart, Line, XAxis, YAxis, CartesianGrid, Tooltip, ResponsiveContainer, ReferenceLine } from "recharts";
import type { DegradationResponse } from "@/types/api";
import { AlertTriangle, CheckCircle2, XCircle } from "lucide-react";

interface DegradationMonitorProps {
  data: DegradationResponse | null;
  loading?: boolean;
}

export function DegradationMonitor({ data, loading }: DegradationMonitorProps) {
  if (loading) {
    return (
      <Card>
        <CardHeader>
          <CardTitle>Degradation Analysis</CardTitle>
          <CardDescription>Analyzing tire degradation...</CardDescription>
        </CardHeader>
        <CardContent className="h-[300px] flex items-center justify-center">
          <div className="animate-pulse text-muted-foreground">Analyzing...</div>
        </CardContent>
      </Card>
    );
  }

  if (!data) {
    return (
      <Card>
        <CardHeader>
          <CardTitle>Degradation Analysis</CardTitle>
          <CardDescription>No data available</CardDescription>
        </CardHeader>
        <CardContent className="h-[300px]" />
      </Card>
    );
  }

  const getHealthIcon = () => {
    switch (data.stint_health) {
      case "optimal":
      case "fresh":
        return <CheckCircle2 className="h-5 w-5 text-green-600" />;
      case "degrading":
        return <AlertTriangle className="h-5 w-5 text-yellow-600" />;
      case "critical":
        return <XCircle className="h-5 w-5 text-red-600" />;
    }
  };

  const getHealthColor = () => {
    switch (data.stint_health) {
      case "optimal":
      case "fresh":
        return "text-green-600 bg-green-50 border-green-200";
      case "degrading":
        return "text-yellow-600 bg-yellow-50 border-yellow-200";
      case "critical":
        return "text-red-600 bg-red-50 border-red-200";
    }
  };

  // Chart data
  const chartData = data.degradation_curve.map((point) => ({
    lap: point.lap,
    delta: point.delta_seconds,
    severity: point.severity * 100,
  }));

  return (
    <Card>
      <CardHeader>
        <div className="flex items-center justify-between">
          <div>
            <CardTitle>Degradation Analysis</CardTitle>
            <CardDescription>
              Tire and grip degradation inference from telemetry
            </CardDescription>
          </div>
          <div className={`flex items-center gap-2 px-3 py-1 rounded-full border ${getHealthColor()}`}>
            {getHealthIcon()}
            <span className="font-semibold capitalize">{data.stint_health}</span>
          </div>
        </div>
      </CardHeader>
      <CardContent>
        <div className="mb-4 grid grid-cols-2 gap-4 text-sm">
          <div>
            <p className="text-muted-foreground">Degradation Rate</p>
            <p className="text-2xl font-bold">
              +{data.degradation_rate.toFixed(3)}s/lap
            </p>
          </div>
          <div>
            <p className="text-muted-foreground">Recommended Action</p>
            <p className="text-sm font-medium">{data.recommended_action}</p>
          </div>
        </div>

        <ResponsiveContainer width="100%" height={250}>
          <LineChart data={chartData}>
            <CartesianGrid strokeDasharray="3 3" />
            <XAxis
              dataKey="lap"
              label={{ value: "Lap Number", position: "insideBottom", offset: -5 }}
            />
            <YAxis
              yAxisId="left"
              label={{ value: "Delta to Best (s)", angle: -90, position: "insideLeft" }}
            />
            <YAxis
              yAxisId="right"
              orientation="right"
              label={{ value: "Severity (%)", angle: 90, position: "insideRight" }}
              domain={[0, 100]}
            />
            <Tooltip
              content={({ active, payload }) => {
                if (active && payload && payload.length) {
                  const data = payload[0].payload;
                  return (
                    <div className="bg-background border rounded-lg p-3 shadow-lg">
                      <p className="font-semibold">Lap {data.lap}</p>
                      <p className="text-sm">
                        Delta: <span className="font-mono">+{data.delta.toFixed(3)}s</span>
                      </p>
                      <p className="text-sm">
                        Severity: <span className="font-mono">{data.severity.toFixed(0)}%</span>
                      </p>
                    </div>
                  );
                }
                return null;
              }}
            />
            <ReferenceLine yAxisId="left" y={0} stroke="#888" strokeDasharray="3 3" />
            <ReferenceLine yAxisId="right" y={50} stroke="#facc15" strokeDasharray="3 3" label="Caution" />
            <ReferenceLine yAxisId="right" y={75} stroke="#ef4444" strokeDasharray="3 3" label="Critical" />
            <Line
              yAxisId="left"
              type="monotone"
              dataKey="delta"
              stroke="#3b82f6"
              strokeWidth={2}
              dot={{ fill: "#3b82f6", r: 4 }}
              name="Lap Time Delta"
            />
            <Line
              yAxisId="right"
              type="monotone"
              dataKey="severity"
              stroke="#ef4444"
              strokeWidth={2}
              dot={{ fill: "#ef4444", r: 4 }}
              name="Degradation Severity"
            />
          </LineChart>
        </ResponsiveContainer>

        {data.primary_causes.length > 0 && (
          <div className="mt-4 space-y-2">
            <p className="text-sm font-semibold">Primary Causes:</p>
            {data.primary_causes.map((cause, idx) => (
              <div key={idx} className="text-sm border rounded-md p-2 bg-muted/30">
                <div className="flex items-center justify-between mb-1">
                  <span className="font-medium capitalize">
                    {cause.cause_type.replace(/_/g, " ")}
                  </span>
                  <span className="text-xs text-muted-foreground">
                    {(cause.confidence * 100).toFixed(0)}% confidence
                  </span>
                </div>
                <ul className="text-xs text-muted-foreground list-disc list-inside">
                  {cause.indicators.map((indicator, i) => (
                    <li key={i}>{indicator}</li>
                  ))}
                </ul>
              </div>
            ))}
          </div>
        )}
      </CardContent>
    </Card>
  );
}
