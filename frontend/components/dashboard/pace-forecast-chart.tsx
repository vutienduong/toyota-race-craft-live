"use client";

import { Card, CardContent, CardDescription, CardHeader, CardTitle } from "@/components/ui/card";
import { LineChart, Line, XAxis, YAxis, CartesianGrid, Tooltip, Legend, ResponsiveContainer, Area, AreaChart } from "recharts";
import type { PaceForecastResponse } from "@/types/api";
import { TrendingUp, TrendingDown, Minus } from "lucide-react";

interface PaceForecastChartProps {
  data: PaceForecastResponse | null;
  loading?: boolean;
}

export function PaceForecastChart({ data, loading }: PaceForecastChartProps) {
  if (loading) {
    return (
      <Card>
        <CardHeader>
          <CardTitle>Pace Forecast</CardTitle>
          <CardDescription>Predicting next 5 laps...</CardDescription>
        </CardHeader>
        <CardContent className="h-[300px] flex items-center justify-center">
          <div className="animate-pulse text-muted-foreground">Loading predictions...</div>
        </CardContent>
      </Card>
    );
  }

  if (!data) {
    return (
      <Card>
        <CardHeader>
          <CardTitle>Pace Forecast</CardTitle>
          <CardDescription>No data available</CardDescription>
        </CardHeader>
        <CardContent className="h-[300px]" />
      </Card>
    );
  }

  // Prepare chart data
  const chartData = data.predictions.map((pred) => ({
    lap: pred.lap_number,
    time: pred.predicted_time,
    delta: pred.delta,
    confidence: pred.confidence * 100,
    upperBound: pred.predicted_time + (1 - pred.confidence) * 0.5,
    lowerBound: pred.predicted_time - (1 - pred.confidence) * 0.5,
  }));

  // Trend icon
  const getTrendIcon = () => {
    switch (data.trend) {
      case "improving":
        return <TrendingDown className="h-4 w-4 text-green-600" />;
      case "degrading":
        return <TrendingUp className="h-4 w-4 text-red-600" />;
      default:
        return <Minus className="h-4 w-4 text-yellow-600" />;
    }
  };

  const getTrendColor = () => {
    switch (data.trend) {
      case "improving":
        return "text-green-600";
      case "degrading":
        return "text-red-600";
      default:
        return "text-yellow-600";
    }
  };

  return (
    <Card>
      <CardHeader>
        <div className="flex items-center justify-between">
          <div>
            <CardTitle>Pace Forecast (Next 5 Laps)</CardTitle>
            <CardDescription>
              ML-powered lap time predictions with confidence intervals
            </CardDescription>
          </div>
          <div className="flex items-center gap-2">
            {getTrendIcon()}
            <span className={`font-semibold capitalize ${getTrendColor()}`}>
              {data.trend}
            </span>
          </div>
        </div>
      </CardHeader>
      <CardContent>
        <div className="mb-4 grid grid-cols-3 gap-4 text-sm">
          <div>
            <p className="text-muted-foreground">Current Pace</p>
            <p className="text-2xl font-bold">{data.current_pace.toFixed(2)}s</p>
          </div>
          <div>
            <p className="text-muted-foreground">Next Lap</p>
            <p className="text-2xl font-bold">
              {data.predictions[0]?.predicted_time.toFixed(2)}s
            </p>
          </div>
          <div>
            <p className="text-muted-foreground">Delta</p>
            <p className={`text-2xl font-bold ${
              data.predictions[0]?.delta > 0 ? "text-red-600" : "text-green-600"
            }`}>
              {data.predictions[0]?.delta >= 0 ? "+" : ""}
              {data.predictions[0]?.delta.toFixed(3)}s
            </p>
          </div>
        </div>

        <ResponsiveContainer width="100%" height={300}>
          <AreaChart data={chartData}>
            <CartesianGrid strokeDasharray="3 3" />
            <XAxis
              dataKey="lap"
              label={{ value: "Lap Number", position: "insideBottom", offset: -5 }}
            />
            <YAxis
              domain={["dataMin - 0.5", "dataMax + 0.5"]}
              label={{ value: "Lap Time (s)", angle: -90, position: "insideLeft" }}
            />
            <Tooltip
              content={({ active, payload }) => {
                if (active && payload && payload.length) {
                  const data = payload[0].payload;
                  return (
                    <div className="bg-background border rounded-lg p-3 shadow-lg">
                      <p className="font-semibold">Lap {data.lap}</p>
                      <p className="text-sm">
                        Predicted: <span className="font-mono">{data.time.toFixed(3)}s</span>
                      </p>
                      <p className="text-sm">
                        Delta: <span className={`font-mono ${data.delta >= 0 ? "text-red-600" : "text-green-600"}`}>
                          {data.delta >= 0 ? "+" : ""}{data.delta.toFixed(3)}s
                        </span>
                      </p>
                      <p className="text-sm">
                        Confidence: <span className="font-mono">{data.confidence.toFixed(0)}%</span>
                      </p>
                    </div>
                  );
                }
                return null;
              }}
            />
            <Legend />
            <Area
              type="monotone"
              dataKey="upperBound"
              stackId="1"
              stroke="none"
              fill="#3b82f6"
              fillOpacity={0.1}
              name="Confidence Range"
            />
            <Area
              type="monotone"
              dataKey="lowerBound"
              stackId="1"
              stroke="none"
              fill="#3b82f6"
              fillOpacity={0.1}
            />
            <Line
              type="monotone"
              dataKey="time"
              stroke="#3b82f6"
              strokeWidth={3}
              dot={{ fill: "#3b82f6", r: 5 }}
              name="Predicted Lap Time"
            />
          </AreaChart>
        </ResponsiveContainer>

        <div className="mt-4 text-xs text-muted-foreground">
          <p>
            Predictions based on last 5 laps telemetry analysis. Confidence decreases with prediction horizon.
          </p>
        </div>
      </CardContent>
    </Card>
  );
}
