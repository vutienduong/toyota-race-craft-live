from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from api import pace_forecast, pit_window, threat_detection, degradation, current, websocket
import uvicorn
from dotenv import load_dotenv

# Load environment variables from .env file
load_dotenv()

app = FastAPI(
    title="RaceCraft Live API",
    description="Real-time race strategy intelligence API for GR Cup",
    version="0.1.0"
)

# CORS configuration
app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:3000", "http://localhost:3001"],  # Frontend URLs
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Health check
@app.get("/")
async def root():
    return {
        "message": "RaceCraft Live API",
        "status": "running",
        "version": "0.1.0"
    }

@app.get("/health")
async def health_check():
    return {"status": "healthy"}

# Include routers
app.include_router(pace_forecast.router, prefix="/api/pace", tags=["Pace Forecasting"])
app.include_router(pit_window.router, prefix="/api/pit", tags=["Pit Strategy"])
app.include_router(threat_detection.router, prefix="/api/threat", tags=["Threat Detection"])
app.include_router(degradation.router, prefix="/api/degradation", tags=["Degradation Analysis"])
app.include_router(current.router, prefix="/api/current", tags=["Current Status"])
app.include_router(websocket.router, prefix="/ws", tags=["WebSocket"])

if __name__ == "__main__":
    uvicorn.run("main:app", host="0.0.0.0", port=8000, reload=True)
