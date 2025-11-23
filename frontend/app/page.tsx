import Link from "next/link";
import { Button } from "@/components/ui/button";
import { ArrowRight, BarChart3, Target, Shield, Activity } from "lucide-react";

export default function Home() {
  return (
    <main className="flex min-h-screen flex-col items-center justify-center p-8 md:p-24">
      <div className="z-10 max-w-5xl w-full items-center justify-center">
        {/* Hero Section */}
        <div className="text-center mb-16">
          <h1 className="text-5xl md:text-6xl font-bold mb-6 bg-gradient-to-r from-primary to-blue-600 bg-clip-text text-transparent">
            RaceCraft Live
          </h1>
          <p className="text-xl text-muted-foreground mb-8 max-w-2xl mx-auto">
            Real-time strategy intelligence for GR Cup racing teams
          </p>
          <p className="text-lg text-muted-foreground mb-8 max-w-3xl mx-auto">
            Transform Toyota telemetry and lap data into actionable ML-driven insights
            for pit window optimization, pace forecasting, threat detection, and degradation modeling
          </p>
          <Link href="/dashboard">
            <Button size="lg" className="text-lg px-8 py-6">
              Launch Dashboard
              <ArrowRight className="ml-2 h-5 w-5" />
            </Button>
          </Link>
        </div>

        {/* Features Grid */}
        <div className="grid grid-cols-1 md:grid-cols-2 gap-6 mt-12">
          <div className="border rounded-lg p-6 hover:border-primary transition-colors">
            <div className="flex items-center gap-3 mb-3">
              <BarChart3 className="h-6 w-6 text-primary" />
              <h2 className="text-xl font-semibold">Pace Forecasting</h2>
            </div>
            <p className="text-sm text-muted-foreground">
              AI-powered lap time prediction for the next 3-5 laps with ±0.25s accuracy target
            </p>
          </div>

          <div className="border rounded-lg p-6 hover:border-primary transition-colors">
            <div className="flex items-center gap-3 mb-3">
              <Target className="h-6 w-6 text-primary" />
              <h2 className="text-xl font-semibold">Pit Strategy</h2>
            </div>
            <p className="text-sm text-muted-foreground">
              Optimal pit window recommendations with position simulation and undercut analysis
            </p>
          </div>

          <div className="border rounded-lg p-6 hover:border-primary transition-colors">
            <div className="flex items-center gap-3 mb-3">
              <Shield className="h-6 w-6 text-primary" />
              <h2 className="text-xl font-semibold">Threat Detection</h2>
            </div>
            <p className="text-sm text-muted-foreground">
              Real-time competitor analysis with attack probability and defensive recommendations
            </p>
          </div>

          <div className="border rounded-lg p-6 hover:border-primary transition-colors">
            <div className="flex items-center gap-3 mb-3">
              <Activity className="h-6 w-6 text-primary" />
              <h2 className="text-xl font-semibold">Degradation Analysis</h2>
            </div>
            <p className="text-sm text-muted-foreground">
              Tire and grip degradation inference from telemetry signals without direct temperature data
            </p>
          </div>
        </div>

        {/* Tech Stack */}
        <div className="mt-16 text-center border-t pt-12">
          <h3 className="text-sm font-semibold text-muted-foreground mb-4">POWERED BY</h3>
          <div className="flex flex-wrap justify-center gap-6 text-sm text-muted-foreground">
            <span>Next.js 14</span>
            <span>•</span>
            <span>FastAPI</span>
            <span>•</span>
            <span>LightGBM</span>
            <span>•</span>
            <span>TensorFlow</span>
            <span>•</span>
            <span>Recharts</span>
          </div>
        </div>
      </div>
    </main>
  );
}
