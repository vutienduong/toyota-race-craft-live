# **Product Requirements Document (PRD)**

**Product Name:** RaceCraft Live

**Purpose:** Real-time strategy and decision-support engine for GR Cup racing teams
---

# 1. **Product Overview**

RaceCraft Live is a real-time strategy intelligence tool designed for GR Cup race engineers. It transforms Toyota’s telemetry and lap data into actionable guidance—predicting optimal pit windows, forecasting pace changes, detecting threats from competitors, and identifying strategic opportunities such as undercuts or defensive lap planning.

Professional race teams rely heavily on human intuition to decipher dozens of telemetry variables. RaceCraft Live turns these raw signals into high-confidence, ML-driven insights presented in an intuitive dashboard, enabling faster and more accurate decisions during live race conditions.

---

# 2. **Problem Statement**

Race engineers and strategy teams face several challenges:

1. **Telemetry is overwhelming**
    
    Speed, gears, brake pressures, throttle, GPS, RPM, steering angle, accel G’s—interpreting these signals in real time is cognitively heavy, error-prone, and inconsistent.
    
2. **Pit strategy is reactive, not predictive**
    
    Teams often choose pit windows based on gut feel, without quantifying future pace degradation or traffic risks.
    
3. **Threats and opportunities are hard to see**
    
    Identifying an approaching opponent, undercut attempts, or sudden pace drops requires manual analysis across multiple data streams.
    
4. **Degraded tire performance is hidden**
    
    There is no direct tire temperature/pressure in the dataset, so degradation must be inferred from secondary signals.
    

RaceCraft Live solves these problems using ML-assisted modeling and intuitive visualizations.

---

# 3. **Goals & Success Metrics**

### **Primary Goals**

- Provide real-time, data-driven race strategy guidance.
- Detect pace shifts, threats, and opportunities earlier than humans can.
- Reduce cognitive load for engineers during race conditions.
- Present insights in a clean, racing-grade dashboard.

### **Success Metrics**

- **Accuracy:** ±0.25 sec accuracy in short-term pace projection.
- **Detection:** Identify pace drops within 3 laps of onset.
- **Opportunity Insight:** Predict undercut/overcut gains within ±0.5 sec.
- **Usability:** Engineers can make a pit decision within 10 seconds using visuals.

---

# 4. **Key Use Cases**

### **Use Case 1 — Pit Window Prediction**

Engineer asks:

“When is the best lap to pit without getting stuck in traffic and maximizing overall stint time?”

RaceCraft Live answers:

- Recommended pit laps
- Projected lap times before/after pit
- Position after pit (estimated)

### **Use Case 2 — Competitor Threat Detection**

Engineer asks:

“Is Car 86-004 gaining on us?”

RaceCraft Live:

- Shows closing rate per sector
- Predicts overtake attempt within next X laps
- Highlights where the competitor is faster (corner entry, exit, braking)

### **Use Case 3 — Stint Degradation Modeling**

Engineer asks:

“Is our driver losing performance due to tire wear or mistakes?”

RaceCraft Live:

- Shows inferred degradation curve
- Identifies cause: braking shift, throttle inconsistency, steering variance
- Suggests when driver needs to switch to defensive versus aggressive strategy

### **Use Case 4 — Live Strategy Overview**

Engineer needs a real-time board of:

- Current lap pace projection
- Competitor gaps / closing speeds
- Stint degradation
- Recommended actions
- Traffic map

---

# 5. **Product Scope**

## **In Scope (MVP)**

1. **Real-time pace forecasting (next 3–5 laps)**
    
    Based on:
    
    - speed
    - throttle and pedal inputs
    - brake pressure
    - steering angle
    - G forces
    - lap distance
    - lap time trends
2. **Pit window optimization**
    - detect slow laps
    - project gains/losses
    - predict post-pit position
3. **Undercut/Overcut analyzer**
    - compare pace delta vs nearest rivals
    - calculate impact of pitting early or late
4. **Threat detection model**
    - closing gap analysis
    - likelihood of attack in next 1–3 laps
    - top areas where rival is outperforming
5. **Degradation inference model (no tire temps needed)**
    
    Using:
    
    - brake pressure drift
    - throttle smoothness degradation
    - lateral G reduction
    - increased steering input for same corner speed
6. **Strategy dashboard UI**
    - lap time trend graph
    - degradation curve
    - threat radar
    - pit window recommendation
    - live pace delta vs rivals
    - track map with car positions

---

## **Out of Scope**

- Direct tire temperature/pressure modeling (not in dataset)
- Full physics-based vehicle simulation
- Multi-driver team strategy (GR Cup is driver-specific)
- Historical seasonal analytics (non-essential for real-time tool)

---

# 6. **Data Model & Telemetry Mapping**

Below shows how telemetry fields map to analytics:

| Dataset Field | Usage in RaceCraft Live |
| --- | --- |
| **Speed** | Pace modeling, lap time projection |
| **Gear** | Driver behavior signature, shift optimization |
| **nmot (RPM)** | Corner exit performance, power insights |
| **aps (pedal)** | Acceleration behavior, throttle discipline |
| **ath (blade)** | Throttle response consistency |
| **pbrake_f/r** | Degradation inference, braking stability |
| **accx_can** | Braking quality, traction loss detection |
| **accy_can** | Cornering performance & lateral grip degradation |
| **Steering_Angle** | Turn-in consistency, oversteer/understeer detection |
| **GPS Lat/Long** | Racing line reconstruction |
| **Lapdist (dls)** | Lap segmentation, position, sector alignment |
| **meta_time** | Ordering of telemetry packets |
| **timestamp** | Optional; unreliable; used for ECU-relative modeling |

---

# 7. **Core Features (Detailed Requirements)**

## **7.1. Real-Time Pace Forecaster**

**Input:** last N laps of telemetry

**Output:** predicted lap time for next 3–5 laps

**Method:**

- Fit lightweight regression or LSTM on:
    
    speed curve, brake behavior changes, throttle variance, lateral G
    
- Adjust prediction per lap segment (entry, mid, exit)

**FR-1:** Forecast must update every lap with new data.

**FR-2:** Accuracy target ±0.25 sec.

---

## **7.2. Pit Window Recommendation Engine**

**Logic:**

- Detect pace drop slope
- Compare pace to rivals
- Estimate position loss if pit now
- Recommend best Lap X–Y window

**FR-3:** Show “Recommended Pit Laps” with confidence score.

**FR-4:** Display predicted positions after pit stop.

---

## **7.3. Undercut/Overcut Simulator**

Compares driver pace evolution vs rivals on identical lap distance segments.

**FR-5:** Compute time gained by pitting earlier than nearest rival.

**FR-6:** Visualize optimal strategy in segment chart.

---

## **7.4. Threat Detection**

Uses gap delta + pace delta.

**FR-7:** Predict if a rival will attack in the next 1–3 laps.

**FR-8:** Show “Threat Score” with explanation (corner entry, exit, braking).

---

## **7.5. Stint Degradation Inference**

Even without tire temps, car behavior reveals degradation.

Indicators:

- Reduced `accy_can` in same corners
- Increasing steering angle for same speed
- Earlier braking (`accx_can` shifts positive)
- Throttle hesitation (`aps` variance increases)

**FR-9:** Generate “Degradation Curve” updated every lap.

**FR-10:** Identify cause (brake fade, cornering grip loss, inconsistency).

---

## **7.6. Strategy Dashboard UI**

**UI components:**

- Pace chart
- Degradation curve
- Pit window suggestion card
- Track map (GPS)
- Rival threat radar
- Segment performance mini-map

**FR-11:** Dashboard must load instantly and refresh live.

**FR-12:** Designed for tablet or widescreen engineer monitors.

---

# 8. **Technical Architecture**

### **Frontend**

- Next.js + Shadcn UI
- Recharts / ECharts for telemetry visualization
- Mapbox GL for track map
- WebSockets for live updates

### **Backend**

- Firebase Functions or Node backend
- Python processing layer for ML (deployed as Cloud Function or container)
- Real-time Firestore for streaming data

### **Machine Learning**

- LightGBM or LSTM model for pace projection
- Statistical deltas for threat detection
- Rule-based + ML hybrid for degradation inference

### **Data Pipeline**

- Raw telemetry → Normalizer (fix laps, timestamps, vehicle IDs)
- Segmentation by lap and sector (via lapdist meters)
- Feature generation: brake curve, throttle curve, G-force signatures
- Model inference
- Serve results to frontend in <1s latency

---

# 9. **Constraints & Assumptions**

- ECU timestamps may drift — use `meta_time` ordering.
- Lap numbers may be corrupted — rely on `lapdist` wraparound.
- No tire temp data — degradation is inferred, not absolute.
- GPS noise exists — smooth using Kalman filter.

---

# 10. **Risks & Mitigations**

| Risk | Impact | Mitigation |
| --- | --- | --- |
| Missing laps or inaccurate lap count | Incorrect predictions | Derive laps from lapdist |
| Sensor noise | Model instability | Apply smoothing filters; sliding-window averages |
| GPS jitter | Racing line distortion | Use map matching + smoother |
| Variance between tracks | Model overfitting | Train per-track models or normalize curves |

---

# 11. **Deliverables for Hackathon Submission**

- **Live demo dashboard** (hosted on Vercel)
- **ML notebooks** for forecasting + threat detection
- **Backend API** for strategy insights
- **3-min demo video** simulating a race scenario
- **GitHub repo** (public or shared private)
- **Documentation:** README + Data Model + Architecture Diagram

---

# 12. **Future Enhancements (Post-MVP)**

- AI-powered race engineer voice assistant
- Full multi-driver comparisons
- Real-time anomaly detection (mechanical issues)
- Realistic traffic simulation
- Race replay with insights overlay