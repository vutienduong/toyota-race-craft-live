export default function Home() {
  return (
    <main className="flex min-h-screen flex-col items-center justify-center p-24">
      <div className="z-10 max-w-5xl w-full items-center justify-center font-mono text-sm">
        <h1 className="text-4xl font-bold text-center mb-4">
          RaceCraft Live
        </h1>
        <p className="text-center text-muted-foreground mb-8">
          Real-time strategy intelligence for GR Cup racing teams
        </p>
        <div className="grid grid-cols-1 md:grid-cols-2 gap-4 mt-8">
          <div className="border rounded-lg p-6">
            <h2 className="text-xl font-semibold mb-2">Pace Forecasting</h2>
            <p className="text-sm text-muted-foreground">
              AI-powered lap time prediction for the next 3-5 laps
            </p>
          </div>
          <div className="border rounded-lg p-6">
            <h2 className="text-xl font-semibold mb-2">Pit Strategy</h2>
            <p className="text-sm text-muted-foreground">
              Optimal pit window recommendations with position simulation
            </p>
          </div>
          <div className="border rounded-lg p-6">
            <h2 className="text-xl font-semibold mb-2">Threat Detection</h2>
            <p className="text-sm text-muted-foreground">
              Real-time competitor analysis and attack probability
            </p>
          </div>
          <div className="border rounded-lg p-6">
            <h2 className="text-xl font-semibold mb-2">Degradation Analysis</h2>
            <p className="text-sm text-muted-foreground">
              Tire and grip degradation inference from telemetry signals
            </p>
          </div>
        </div>
      </div>
    </main>
  );
}
