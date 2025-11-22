# RaceCraft Live - Barber Data Analysis Plan

## Data Inventory

### Dataset Overview
**Event:** Barber Motorsports Park (I_R06_2025-09-07)
**Location:** `data/barber/`
**Date:** September 6-7, 2025
**Total Races:** 2 (R1, R2)

### File Structure

#### Core Telemetry Data
| File | Size | Rows | Description |
|------|------|------|-------------|
| `R1_barber_telemetry_data.csv` | 1.5 GB | 11,556,520 | Raw telemetry data (Race 1) |
| `R2_barber_telemetry_data.csv` | 1.5 GB | ~11.5M | Raw telemetry data (Race 2) |
| `R1_barber_lap_time.csv` | 65 KB | 572 | Lap completion times (Race 1) |
| `R2_barber_lap_time.csv` | 68 KB | 596 | Lap completion times (Race 2) |
| `R1_barber_lap_start.csv` | 65 KB | 572 | Lap start timestamps (Race 1) |
| `R2_barber_lap_start.csv` | 68 KB | 596 | Lap start timestamps (Race 2) |
| `R1_barber_lap_end.csv` | 65 KB | 572 | Lap end timestamps (Race 1) |
| `R2_barber_lap_end.csv` | 68 KB | 596 | Lap end timestamps (Race 2) |

#### Race Analysis & Results
| File | Description |
|------|-------------|
| `03_Provisional Results_Race 1_Anonymized.CSV` | Final race standings (22 drivers, 27 laps) |
| `03_Provisional Results_Race 2_Anonymized.CSV` | Final race standings (Race 2) |
| `23_AnalysisEnduranceWithSections_Race 1_Anonymized.CSV` | Lap-by-lap sector times and analysis |
| `23_AnalysisEnduranceWithSections_Race 2_Anonymized.CSV` | Lap-by-lap sector times and analysis |
| `26_Weather_Race 1_Anonymized.CSV` | Weather conditions per minute |
| `26_Weather_Race 2_Anonymized.CSV` | Weather conditions per minute |
| `99_Best 10 Laps By Driver_Race 1_Anonymized.CSV` | Top 10 lap times per driver |

### Data Schema

#### Telemetry Data Schema (Long Format)
```csv
expire_at, lap, meta_event, meta_session, meta_source, meta_time,
original_vehicle_id, outing, telemetry_name, telemetry_value,
timestamp, vehicle_id, vehicle_number
```

**Critical Fields:**
- `meta_time` - Primary timestamp (use for ordering, NOT `timestamp`)
- `telemetry_name` - Type of sensor reading
- `telemetry_value` - Sensor reading value
- `vehicle_id` - Unique vehicle identifier (e.g., GR86-013-80)
- `vehicle_number` - Race number (e.g., 13, 22, 72)
- `lap` - Lap number (WARNING: may be corrupted, verify with lapdist)

**Available Telemetry Signals:**
| Signal | Units | Purpose |
|--------|-------|---------|
| `speed` | km/h | Pace modeling, lap time projection |
| `Steering_Angle` | degrees | Turn-in consistency, over/understeer detection |
| `gear` | 1-6 | Driver behavior signature, shift optimization |
| `nmot` | RPM | Corner exit performance, power insights |
| `aps` | % | Throttle pedal position, acceleration behavior |
| `pbrake_f` | bar | Front brake pressure, braking stability |
| `pbrake_r` | bar | Rear brake pressure, braking stability |
| `accx_can` | g | Braking quality, traction loss detection |
| `accy_can` | g | Cornering performance, lateral grip degradation |
| `VBOX_Lat_Min` | decimal | GPS latitude (requires smoothing) |
| `VBOX_Long_Minutes` | decimal | GPS longitude (requires smoothing) |
| `Laptrigger_lapdist_dls` | meters | Distance from lap start/finish (track position) |

**CRITICAL MISSING FIELD:** `ath` (throttle blade position) is NOT present in this dataset but is mentioned in CLAUDE.md. We'll use `aps` as the primary throttle metric.

#### Lap Time Data Schema
```csv
expire_at, lap, meta_event, meta_session, meta_source, meta_time,
original_vehicle_id, outing, timestamp, vehicle_id, vehicle_number
```
- One row per completed lap
- `meta_time` = lap completion time

#### Race Analysis Schema (Sector Times)
```csv
NUMBER, DRIVER_NUMBER, LAP_NUMBER, LAP_TIME, LAP_IMPROVEMENT,
CROSSING_FINISH_LINE_IN_PIT, S1, S1_IMPROVEMENT, S2, S2_IMPROVEMENT,
S3, S3_IMPROVEMENT, KPH, ELAPSED, HOUR, S1_LARGE, S2_LARGE, S3_LARGE,
TOP_SPEED, PIT_TIME, CLASS, GROUP, MANUFACTURER, FLAG_AT_FL,
S1_SECONDS, S2_SECONDS, S3_SECONDS, IM1a_time, IM1a_elapsed, IM1_time,
IM1_elapsed, IM2a_time, IM2a_elapsed, IM2_time, IM2_elapsed, IM3a_time,
IM3a_elapsed, FL_time, FL_elapsed
```

**Key Fields:**
- 3 sectors: S1, S2, S3 (with improvement deltas)
- Multiple intermediate timing points (IM1a, IM1, IM2a, IM2, IM3a, FL)
- Sector times in both formatted strings and decimal seconds
- Pit detection: `CROSSING_FINISH_LINE_IN_PIT`
- Flag status: `FLAG_AT_FL` (FCY = Full Course Yellow, GF = Green Flag)

#### Weather Data Schema
```csv
TIME_UTC_SECONDS, TIME_UTC_STR, AIR_TEMP, TRACK_TEMP, HUMIDITY,
PRESSURE, WIND_SPEED, WIND_DIRECTION, RAIN
```
- Sampled every ~60 seconds
- Race 1 conditions: 29.8°C air, 56% humidity, no rain, light wind

### Data Quality Observations

#### Known Issues (from CLAUDE.md)
1. **ECU Timestamp Drift:** Use `meta_time` for ordering, NOT `timestamp`
2. **Lap Number Corruption:** Derive lap boundaries from `Laptrigger_lapdist_dls` wraparound
3. **GPS Noise:** Raw coordinates have jitter, require Kalman filtering
4. **Sensor Outliers:** Brake pressure, throttle, steering can spike

#### Validation Checks Needed
- [ ] Verify all 20 vehicles have complete telemetry coverage
- [ ] Check for missing data gaps in telemetry streams
- [ ] Validate lap count consistency across telemetry/lap_time/race results
- [ ] Confirm track length and lap distance wraparound threshold
- [ ] Identify pit lap windows from sector analysis

### Vehicle Coverage
**Race 1:** 20 vehicles actively tracked
**Sample Vehicle IDs:**
- GR86-002-000 (Number 0)
- GR86-013-80 (Number 13 - Race Winner)
- GR86-022-13 (Number 22)
- GR86-026-72 (Number 72)
- GR86-016-55 (Number 55)
- GR86-063-113 (Number 113)

---

## Phase 1: Data Processing Pipeline

### Step 1: Data Ingestion & Normalization
**Goal:** Transform raw telemetry into analysis-ready format

**Tasks:**
1. **Pivot Telemetry from Long to Wide Format**
   - Current: Each row = one sensor reading
   - Target: Each row = one timestamp with all sensors
   - Group by `(meta_time, vehicle_id)` and pivot on `telemetry_name`
   - Handle missing values (forward-fill for sensor dropouts)

2. **Time Rebase & Synchronization**
   - Use `meta_time` as primary timestamp
   - Convert to race-relative seconds (seconds from race start)
   - Align telemetry with lap_start/lap_end markers

3. **Vehicle ID Normalization**
   - Map `vehicle_id` to `vehicle_number` for consistency
   - Create lookup table: `GR86-013-80 → 13`

**Output:** `processed/R1_telemetry_wide.parquet` (compressed columnar format for fast queries)

**Estimated Processing Time:** 15-20 minutes per race (11.5M rows → ~500K timestamps)

### Step 2: Lap Segmentation
**Goal:** Split telemetry into individual laps with sector alignment

**Algorithm:**
```python
# Detect lap boundaries using lapdist wraparound
1. Extract `Laptrigger_lapdist_dls` time series per vehicle
2. Detect wraparound: where lapdist drops from MAX → 0
3. Split telemetry into lap segments
4. Validate lap count matches `lap_time.csv` row count
5. Align with sector boundaries from analysis CSV
```

**Critical Decision:** What is Barber's track length?
- Analyze `Laptrigger_lapdist_dls` max values to determine track length
- Expected: ~2,380 meters (2.38 km official length)
- Wraparound threshold: when `lapdist < 100m` after `lapdist > 2200m`

**Outputs:**
- `processed/R1_laps_segmented.parquet` (one row per lap, telemetry nested)
- `processed/R1_sector_boundaries.json` (distance markers for S1/S2/S3)

### Step 3: GPS Smoothing & Track Map
**Goal:** Clean GPS coordinates for racing line reconstruction

**Processing Steps:**
1. **Kalman Filtering** on `(VBOX_Lat_Min, VBOX_Long_Minutes)`
   - Process noise: 1e-5 (GPS drift)
   - Measurement noise: 1e-3 (sensor jitter)

2. **Track Centerline Extraction**
   - Average GPS coordinates across all drivers per distance marker
   - Interpolate to create smooth 1-meter resolution track map

3. **Corner Detection**
   - Calculate curvature from steering angle + speed correlation
   - Label major corners (Barber has 17 turns)

**Outputs:**
- `processed/barber_track_map.geojson` (for Mapbox GL visualization)
- `processed/barber_corner_markers.csv` (turn-in/apex/exit points)

### Step 4: Feature Engineering
**Goal:** Generate ML-ready features for pace/degradation/threat models

**Per-Lap Features:**
| Feature Category | Examples |
|-----------------|----------|
| **Pace Metrics** | lap_time, sector_1_time, sector_2_time, sector_3_time, mean_speed, top_speed |
| **Braking Behavior** | mean_brake_pressure_f, max_deceleration, braking_variance, turn_in_speed |
| **Throttle Discipline** | throttle_variance, throttle_smoothness, corner_exit_aps |
| **Lateral Grip** | mean_accy_corners, max_lateral_g, understeer_ratio (steering/speed) |
| **Driver Inputs** | steering_entropy, gear_shift_count, shift_timing_variance |
| **Degradation Proxies** | lap_over_lap_speed_delta, accy_trend_slope, braking_point_shift |

**Statistical Features:**
- Rolling 3-lap averages for trend detection
- Delta to personal best lap (pace drop indicator)
- Delta to leader pace (competitiveness)

**Outputs:**
- `processed/R1_lap_features.parquet` (one row per lap per driver)
- Feature importance scores for ML model training

### Step 5: Opponent Alignment
**Goal:** Enable head-to-head comparisons at identical track positions

**Process:**
1. Resample all telemetry to uniform `lapdist` markers (every 10 meters)
2. For each driver pair, extract telemetry at same distance points
3. Calculate delta metrics:
   - Speed delta (km/h difference at same corner)
   - Time delta (cumulative gap at each marker)
   - Braking point delta (meters difference)

**Use Cases:**
- Threat detection: "Rival is 0.5s faster in Turn 5"
- Undercut analysis: "Pitting now saves 2.1s on fresh tires"

**Outputs:**
- `processed/R1_position_aligned_deltas.parquet`

---

## Phase 2: Analytics & ML Models

### Model 1: Pace Forecaster
**Goal:** Predict lap times for next 3-5 laps (±0.25s accuracy)

**Training Data:**
- Input features: Last 5 laps (pace, brake variance, throttle variance, accy trend)
- Target: Next lap time
- Training set: Laps 5-25 from all drivers in R1+R2 (~500 laps)

**Model Architecture:**
- **Option A:** LightGBM Regressor (fast inference, interpretable)
- **Option B:** LSTM (better captures pace degradation curves)

**Validation:**
- Leave-one-driver-out cross-validation
- RMSE target: <0.25 seconds
- Test on R2 using R1-trained model

**Output:**
- Confidence intervals (80%, 95%)
- Feature importance plot (which signals matter most)

### Model 2: Pit Window Optimizer
**Goal:** Recommend optimal pit lap with position simulation

**Algorithm:**
```python
1. Detect pace drop slope (linear regression on last 5 laps)
2. Forecast tire life remaining (when pace drops >0.5s/lap)
3. Simulate scenarios:
   - Pit now: fresh tire pace boost + pit loss time
   - Pit in 2 laps: extended stint risk + traffic
   - Don't pit: continued degradation
4. Calculate position gain/loss for each scenario
5. Recommend window with highest position probability
```

**Inputs:**
- Current lap time vs personal best
- Rival pace evolution (are they degrading too?)
- Track position (can we undercut?)
- Pit lane time loss (from race analysis CSV)

**Output:**
- "Pit window: Laps 18-20 (70% confidence of +1 position)"
- Risk assessment: "Warning: Traffic on out-lap if pit now"

### Model 3: Undercut/Overcut Simulator
**Goal:** Calculate time gained/lost by pitting early vs late

**Simulation:**
```python
1. Extract pace curves for target driver + rival
2. Estimate fresh tire boost (analyze lap 1 vs lap 10 pace)
   - Expected: ~1.5-2.0s faster on new tires
3. Calculate cumulative time:
   - Undercut: Pit lap N, rival pits lap N+3
     - Gain = (3 laps old tire pace) - (3 laps fresh pace + pit time)
   - Overcut: Rival pits lap N, we pit lap N+3
     - Gain = (3 laps fresh track) - (3 laps traffic)
4. Account for track position changes
```

**Validation:**
- Use actual pit stop data from race results
- Verify against real position changes

### Model 4: Threat Detector
**Goal:** Predict rival attack probability for next 1-3 laps

**Features:**
- Gap delta trend (closing vs stable vs opening)
- Pace delta (rival lap time - our lap time)
- Sector-specific speed advantage (which corners are they faster?)
- DRS/slipstream probability (based on gap <1.0s)

**Output:**
- Threat score: 0-100%
- Corner-specific warning: "Rival 0.8s faster in Turn 7 (apex speed +12 km/h)"
- Recommended defense: "Protect inside line into Turn 1"

**Model:** Logistic Regression or Random Forest (binary classification: attack within 3 laps Y/N)

### Model 5: Degradation Inference
**Goal:** Detect tire/grip degradation without direct temperature data

**Proxy Signals:**
| Signal | Degradation Indicator |
|--------|----------------------|
| `accy_can` drop | Lateral grip loss (understeering) |
| `Steering_Angle` increase | Compensating for understeer |
| `accx_can` shift earlier | Braking earlier (lost confidence) |
| `aps` variance increase | Throttle hesitation (less grip) |
| `speed` in corners drop | Overall pace loss |

**Algorithm:**
```python
1. For each corner, calculate baseline metrics (laps 1-3 average)
2. Track lap-over-lap changes:
   - accy_drop = (current_accy - baseline_accy) / baseline_accy
   - steering_increase = current_steering - baseline_steering
3. Classify degradation severity:
   - Green: <5% change
   - Yellow: 5-10% change (caution)
   - Red: >10% change (critical)
4. Root cause analysis:
   - Front deg: understeer + increased steering
   - Rear deg: oversteer + throttle hesitation
   - Overall: pace drop + all signals degrading
```

**Output:**
- Per-lap degradation curve (0-100% tire life)
- Visual heatmap showing which corners are most affected
- Pit recommendation trigger: "Front-left critical, pit in 2 laps"

---

## Phase 3: Dashboard Development

### Real-Time Data Flow
```
Telemetry CSV → Python Processing → Feature Engineering → ML Models → API
                                                              ↓
                                                          WebSocket
                                                              ↓
                                                        Next.js Dashboard
```

### Dashboard Components

#### 1. Track Map View (Mapbox GL)
- Live positions of all cars
- Sector highlighting (S1/S2/S3 color-coded)
- Speed heatmap overlay (red = slow corners, green = fast straights)
- Threat alerts (pulsing icon when rival closing)

#### 2. Pace Forecast Panel
- Line chart: Predicted lap times (next 5 laps) with confidence bands
- Comparison to rivals (overlay top 3 competitors)
- Degradation warning indicator

#### 3. Pit Strategy Panel
- Optimal pit window recommendation (visual timeline)
- Undercut/overcut simulator (interactive "what-if")
- Position probability matrix

#### 4. Threat Monitor
- Live gap delta chart
- Sector comparison bars (green = advantage, red = disadvantage)
- Attack probability gauge

#### 5. Telemetry Detail View
- Multi-line chart: Speed, throttle, brake, steering vs distance
- Corner-by-corner comparison to personal best
- Degradation trend lines

### UI/UX Principles
- **Color coding:** Green (optimal), Yellow (caution), Red (critical)
- **Actionable insights:** Not just data, but recommendations
- **Confidence scores:** Show model uncertainty
- **Tablet-optimized:** Large touch targets, high contrast

---

## Phase 4: Validation & Testing

### Data Quality Checks
- [ ] Verify track length calculation (should be ~2,380m)
- [ ] Confirm lap count accuracy (R1: 572 laps across 22 drivers)
- [ ] Check for telemetry dropouts (missing timestamps)
- [ ] Validate GPS coordinates within Barber track bounds

### Model Validation
- [ ] Pace forecast RMSE <0.25s on R2 holdout set
- [ ] Pit optimizer correctly predicts position changes in historical data
- [ ] Threat detector achieves >80% precision on actual overtakes
- [ ] Degradation model detects known pit stops within 3 laps

### Performance Benchmarks
- [ ] Telemetry processing: <20 min per race
- [ ] Feature engineering: <5 min per race
- [ ] Model inference: <1 second per prediction
- [ ] Dashboard latency: <1 second telemetry → UI update

### Demo Scenario Preparation
1. **Select target lap:** R1, Lap 15 (mid-race, multiple battles)
2. **Showcase features:**
   - Pace forecast showing degradation
   - Pit window recommendation
   - Undercut simulator (leader vs P2)
   - Threat detection (P3 closing on P2)
3. **Video walkthrough:** 3-minute demo simulating engineer view

---

## Phase 5: Deployment & Documentation

### Deliverables Checklist
- [ ] Live dashboard deployed on Vercel
- [ ] ML training notebooks (Jupyter/Colab)
- [ ] Backend API (FastAPI or Firebase Functions)
- [ ] GitHub repository with README
- [ ] Architecture diagram (data flow + tech stack)
- [ ] 3-minute demo video
- [ ] Data model documentation (this file)

### Repository Structure
```
toyota-race-craft-live/
├── data/
│   └── barber/              # Raw CSV files (gitignored)
├── processed/               # Cleaned parquet files
├── notebooks/
│   ├── 01_data_exploration.ipynb
│   ├── 02_lap_segmentation.ipynb
│   ├── 03_feature_engineering.ipynb
│   ├── 04_pace_forecaster.ipynb
│   ├── 05_degradation_model.ipynb
│   └── 06_threat_detector.ipynb
├── backend/
│   ├── api/                 # FastAPI endpoints
│   ├── models/              # Trained ML models
│   └── processing/          # Data pipeline scripts
├── frontend/
│   ├── app/                 # Next.js pages
│   ├── components/          # shadcn/ui components
│   └── lib/                 # Utilities
├── CLAUDE.md                # AI assistant guidelines
├── DATA_PLAN.md             # This file
└── README.md                # Project overview
```

---

## Critical Next Steps

### Immediate Actions (Next Session)
1. **Determine track length** - Analyze `Laptrigger_lapdist_dls` distribution
2. **Validate lap count** - Cross-check telemetry laps vs lap_time.csv vs race results
3. **Pivot telemetry data** - Transform to wide format for analysis
4. **Extract sector boundaries** - Parse IM1/IM2/IM3 distances from race analysis CSV

### Week 1 Goals
- [ ] Complete data processing pipeline (Steps 1-5)
- [ ] Build lap segmentation algorithm
- [ ] Create Barber track map visualization
- [ ] Engineer baseline feature set

### Week 2 Goals
- [ ] Train pace forecaster model
- [ ] Implement pit window optimizer
- [ ] Build threat detection algorithm
- [ ] Create degradation inference model

### Week 3 Goals
- [ ] Develop Next.js dashboard UI
- [ ] Integrate ML models with WebSocket API
- [ ] Test real-time simulation
- [ ] Record demo video

---

## Open Questions

### Data Clarifications Needed
1. **Track Length:** What is exact lap distance for wraparound detection?
2. **Sector Definitions:** What distances define S1/S2/S3 boundaries?
3. **Pit Time Loss:** Average pit lane time at Barber? (from race analysis CSV)
4. **Tire Strategy:** How many laps can tires sustain before mandatory pit?
5. **Flag Periods:** How do FCY (Full Course Yellow) laps affect pace modeling?

### Technical Decisions
1. **Database Choice:** Parquet files vs Firestore vs Redis for race state?
2. **ML Framework:** LightGBM vs TensorFlow/PyTorch for pace forecaster?
3. **Real-time Simulation:** Replay historical data with timestamp offset or live feed simulation?
4. **Visualization Library:** Recharts (simpler) vs ECharts (more powerful)?

### MVP Scope Tradeoffs
- **In scope:** Single-car strategy view (focus on one driver's decisions)
- **Deferred:** Multi-car team coordination (requires communication data)
- **Deferred:** Historical season analytics (focus on live race intelligence)

---

## Success Metrics

### Quantitative
- Pace forecast accuracy: RMSE <0.25s ✓ (per CLAUDE.md target)
- Degradation detection: Within 3 laps of actual pit stop ✓
- Dashboard latency: <1 second ✓
- Model inference: <1 second ✓

### Qualitative
- Engineer can make pit decision within 10 seconds using dashboard
- Threat alerts accurately predict overtake attempts
- Degradation warnings are actionable (not false alarms)
- UI is intuitive for first-time users (no training required)

---

**Document Version:** 1.0
**Last Updated:** 2025-11-23
**Author:** RaceCraft Live Team
**Status:** Ready for Implementation
