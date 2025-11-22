# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Project Overview

RaceCraft Live is a real-time strategy intelligence tool for GR Cup race engineers. It transforms Toyota's telemetry and lap data into actionable ML-driven insights for pit window optimization, pace forecasting, threat detection, and degradation modeling during live race conditions.

**Key differentiators:**
- No direct tire temperature/pressure data available — degradation must be inferred from secondary telemetry signals
- ECU timestamps may drift — use `meta_time` for ordering
- Lap numbers may be corrupted — rely on `lapdist` wraparound detection

## Technology Stack

### Frontend
- Next.js with shadcn/ui components
- Recharts or ECharts for telemetry visualization
- Mapbox GL for track maps
- WebSockets for real-time updates

### Backend
- Python processing layer for ML models (FastAPI or Cloud Functions)
- Node.js backend (Firebase Functions or standalone)
- Firestore or Redis for real-time race state storage

### Machine Learning
- LightGBM or LSTM for pace forecasting
- Statistical deltas for threat detection
- Hybrid rule-based + ML for degradation inference

## Telemetry Data Model

The system processes CSV telemetry files with these critical fields:

| Field | Purpose |
|-------|---------|
| `Speed` | Pace modeling, lap time projection |
| `Gear` | Driver behavior signature, shift optimization |
| `nmot` (RPM) | Corner exit performance, power insights |
| `aps` (pedal position) | Acceleration behavior, throttle discipline |
| `ath` (throttle blade) | Throttle response consistency |
| `pbrake_f/r` | Degradation inference, braking stability |
| `accx_can` | Braking quality, traction loss detection |
| `accy_can` | Cornering performance, lateral grip degradation |
| `Steering_Angle` | Turn-in consistency, over/understeer detection |
| `GPS Lat/Long` | Racing line reconstruction |
| `lapdist` (dls) | Lap segmentation, position, sector alignment |
| `meta_time` | Primary ordering of telemetry packets |
| `timestamp` | ECU-relative time (unreliable, use sparingly) |

## Data Processing Pipeline

The system follows this flow:
1. **Ingestion & Normalization** → Unpack per-track ZIPs, unify schema, rebase time using `meta_time`
2. **Lap Segmentation** → Detect lap boundaries via `lapdist` wraparound, split into sectors
3. **Smoothing** → Apply Kalman filter to GPS, rolling averages for sensor noise
4. **Feature Engineering** → Generate per-lap features, driver input curves, grip/degradation proxies, opponent alignment
5. **Model Inference** → Pace forecasting, pit window optimization, threat detection, degradation analysis
6. **Serving** → Push predictions via WebSocket to frontend dashboard

## Core Analytics Features

### 1. Pace Forecaster
- Predicts lap times for next 3-5 laps
- Target accuracy: ±0.25 seconds
- Uses speed curve, brake behavior, throttle variance, lateral G forces
- Updates every lap with new telemetry

### 2. Pit Window Optimizer
- Detects pace drop slope
- Compares pace to rivals
- Estimates position loss scenarios
- Recommends optimal pit lap window with confidence score

### 3. Undercut/Overcut Simulator
- Compares driver pace evolution vs rivals on identical lap segments
- Calculates time gained/lost by pitting early vs late
- Accounts for traffic penalties

### 4. Threat Detector
- Uses gap delta + pace delta analysis
- Predicts rival attack probability for next 1-3 laps
- Identifies specific corners where rivals are faster
- Generates "Threat Score" with explanations

### 5. Degradation Inference
Infers tire/grip degradation without direct temperature data using:
- Reduced `accy_can` in same corners (lateral grip loss)
- Increased steering angle for same speed (understeer)
- Earlier braking points (`accx_can` shifts)
- Throttle hesitation (`aps` variance increases)

Output: Per-lap degradation curve with root cause classification

## Accuracy & Performance Targets

- **Pace projection:** ±0.25 sec accuracy
- **Degradation detection:** Within 3 laps of onset
- **Undercut/overcut gain:** ±0.5 sec accuracy
- **Dashboard latency:** <1 second from telemetry to UI update
- **Decision time:** Engineer can make pit decision within 10 seconds using visuals

## Data Quality Constraints

When implementing data processing:
- **Never trust ECU timestamps** — use `meta_time` as primary ordering
- **Never trust lap numbers** — derive from `lapdist` wraparound (track length varies by circuit)
- **Always smooth GPS** — raw coordinates have significant jitter
- **Always validate sensor ranges** — brake pressure, throttle, steering can have outliers
- Track-specific normalization may be required (different track lengths, corner counts)

## Architecture Principles

1. **Real-time first:** All features must update live during race conditions
2. **Inferred over measured:** Build proxy models for unavailable direct measurements
3. **Per-track adaptability:** Models should handle different circuits (Barber, COTA, Indy, Road America, Sebring, Sonoma, VIR)
4. **Interpretable outputs:** Engineers need explanations, not just predictions
5. **Tablet-optimized UI:** Dashboard designed for widescreen engineer monitors and tablets

## MVP Scope

**In scope for hackathon:**
- Real-time pace forecasting (3-5 laps ahead)
- Pit window optimization with position simulation
- Undercut/overcut analyzer
- Threat detection model
- Degradation inference from proxy signals
- Strategy dashboard UI with track map

**Out of scope:**
- Direct tire temperature/pressure modeling (not in dataset)
- Full physics-based vehicle simulation
- Multi-driver team strategy coordination
- Historical seasonal analytics

## Development Guidelines

### When implementing telemetry processing:
- Use sliding windows for lap-over-lap comparisons
- Normalize features per track (corner speeds vary significantly)
- Handle missing data gracefully (sensors can drop packets)
- Segment analysis by `lapdist` meters, not time

### When building ML models:
- Train per-track models or use track-agnostic feature normalization
- Cross-validate on multiple sessions to avoid overfitting
- Prioritize inference speed over model complexity (must run in <1s)
- Log confidence scores for all predictions

### When designing UI components:
- Show predictions with confidence intervals
- Highlight actionable insights (not raw telemetry)
- Use color coding for urgency (green = optimal, yellow = caution, red = critical)
- Include "why" explanations for all strategic recommendations

## Deliverables for Submission

- Live demo dashboard (hosted on Vercel)
- ML notebooks for forecasting + threat detection
- Backend API for strategy insights
- 3-minute demo video simulating race scenario
- GitHub repository with documentation
- Architecture diagram and data model documentation
