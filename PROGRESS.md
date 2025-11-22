# RaceCraft Live - Implementation Progress

## Project Status: Starting Implementation

---

## Phase 1: Project Setup & Infrastructure ⚙️

### 1.1 Frontend Setup
- [ ] Initialize Next.js 14+ project with TypeScript
- [ ] Install and configure shadcn/ui components
- [ ] Setup Tailwind CSS configuration
- [ ] Configure project structure (/app, /components, /lib, /hooks)
- [ ] Install visualization libraries (Recharts, Mapbox GL)
- [ ] Setup environment variables and configuration

### 1.2 Backend Setup
- [ ] Initialize Python backend with FastAPI
- [ ] Setup virtual environment and dependencies (pandas, numpy, scikit-learn)
- [ ] Create project structure (/data, /models, /api, /utils)
- [ ] Install ML libraries (LightGBM, TensorFlow/PyTorch for LSTM)
- [ ] Setup CORS and middleware configuration

### 1.3 Data Storage & Real-time
- [ ] Choose and setup real-time store (Firestore or Redis)
- [ ] Configure WebSocket gateway
- [ ] Setup connection between backend and storage
- [ ] Create data schemas for race state

---

## Phase 2: Data Pipeline 📊

### 2.1 Data Ingestion
- [ ] Create CSV telemetry loader
- [ ] Implement track-specific ZIP unpacker
- [ ] Build schema unification module
- [ ] Handle missing/corrupted data gracefully
- [ ] Create data validation utilities

### 2.2 Time & Lap Processing
- [ ] Implement meta_time-based ordering
- [ ] Build lap segmentation using lapdist wraparound
- [ ] Create sector detection algorithm
- [ ] Handle lap number corruption (derive from lapdist)
- [ ] Validate lap boundaries across different tracks

### 2.3 Signal Smoothing
- [ ] Implement Kalman filter for GPS coordinates
- [ ] Apply rolling averages for sensor noise
- [ ] Create speed curve smoother
- [ ] Build outlier detection and removal
- [ ] Validate smoothing doesn't introduce lag

### 2.4 Feature Engineering
- [ ] Extract per-lap features (lap time, sector deltas, pace slope)
- [ ] Generate driver input curves (brake, throttle, steering)
- [ ] Create degradation proxy features (accy drop, steering variance)
- [ ] Build opponent alignment by lapdist/sector
- [ ] Calculate relative gaps and closing rates

---

## Phase 3: ML Models & Analytics 🧠

### 3.1 Pace Forecaster
- [ ] Prepare training dataset with historical lap data
- [ ] Engineer features for pace prediction
- [ ] Train LightGBM model for 3-5 lap forecast
- [ ] Implement LSTM alternative model
- [ ] Validate ±0.25 sec accuracy target
- [ ] Create inference pipeline
- [ ] Build per-lap update mechanism

### 3.2 Pit Window Optimizer
- [ ] Implement pace drop slope detection
- [ ] Build rival pace comparison logic
- [ ] Create position-after-pit simulator
- [ ] Calculate traffic penalties
- [ ] Generate recommended pit lap window
- [ ] Add confidence score calculation
- [ ] Test across multiple race scenarios

### 3.3 Undercut/Overcut Simulator
- [ ] Align driver pace with rivals by lap segment
- [ ] Calculate time gained/lost by early pit
- [ ] Model traffic impact on pit strategy
- [ ] Generate optimal strategy visualization data
- [ ] Validate ±0.5 sec accuracy for gains

### 3.4 Threat Detector
- [ ] Calculate gap delta between cars
- [ ] Compute pace delta vs rivals
- [ ] Build attack probability model (1-3 laps ahead)
- [ ] Identify sector-specific advantages
- [ ] Generate threat score with explanations
- [ ] Create corner-by-corner breakdown

### 3.5 Degradation Inference
- [ ] Extract lateral G reduction (accy_can) patterns
- [ ] Detect steering angle increase for same speed
- [ ] Identify braking point shifts (accx_can)
- [ ] Measure throttle variance (aps) changes
- [ ] Build degradation curve generator
- [ ] Create cause classifier (grip loss, brake fade, etc.)
- [ ] Validate detection within 3 laps of onset

---

## Phase 4: Backend API Layer 🔌

### 4.1 FastAPI Endpoints
- [ ] Create `/api/pace-forecast` endpoint
- [ ] Create `/api/pit-window` endpoint
- [ ] Create `/api/undercut-analysis` endpoint
- [ ] Create `/api/threat-detection` endpoint
- [ ] Create `/api/degradation` endpoint
- [ ] Create `/api/race-state` endpoint for current state
- [ ] Add request validation and error handling

### 4.2 Real-time Processing
- [ ] Implement streaming telemetry processor
- [ ] Build lap-by-lap update trigger
- [ ] Create prediction cache mechanism
- [ ] Setup WebSocket broadcast for updates
- [ ] Optimize for <1s latency requirement
- [ ] Add monitoring and logging

### 4.3 Data Access Layer
- [ ] Create telemetry data repository
- [ ] Build race session manager
- [ ] Implement driver/car data lookup
- [ ] Create track configuration loader
- [ ] Add caching for frequently accessed data

---

## Phase 5: Frontend Dashboard 🎨

### 5.1 Core Layout & Navigation
- [ ] Create main dashboard layout
- [ ] Build session selector (track, driver, replay mode)
- [ ] Implement lap scrubber for replay
- [ ] Add live/replay mode toggle
- [ ] Create responsive grid layout

### 5.2 Strategy Components
- [ ] Build Pit Window Recommendation card
- [ ] Create Pace Forecast chart (next 5 laps)
- [ ] Build Threat Radar component
- [ ] Create Degradation Curve visualization
- [ ] Add Lap/Sector Delta heatmap

### 5.3 Track Visualization
- [ ] Integrate Mapbox GL for track map
- [ ] Plot GPS racing line
- [ ] Add car position markers (you, ahead, behind, traffic)
- [ ] Show closing rate indicators
- [ ] Implement corner/sector labels
- [ ] Add ideal line overlay (optional)

### 5.4 Telemetry Charts
- [ ] Create speed timeline chart
- [ ] Build throttle/brake overlay
- [ ] Add steering angle visualization
- [ ] Plot G-force (accx/accy) graphs
- [ ] Implement lap trace comparison view

### 5.5 Real-time Updates
- [ ] Setup WebSocket client connection
- [ ] Implement live data subscription
- [ ] Create smooth chart animations
- [ ] Add data buffer for replay scrubbing
- [ ] Handle reconnection logic

### 5.6 Mobile/Tablet Optimization
- [ ] Create "Pit Wall Quick View" compact layout
- [ ] Build action cards for quick decisions
- [ ] Optimize for tablet screen sizes
- [ ] Test on different devices

---

## Phase 6: Integration & Testing 🔗

### 6.1 End-to-End Flow
- [ ] Test telemetry upload → processing → display
- [ ] Validate real-time update latency (<1s)
- [ ] Test lap-by-lap prediction updates
- [ ] Verify WebSocket stability
- [ ] Test with sample race data from all 7 tracks

### 6.2 Model Validation
- [ ] Cross-validate pace forecaster accuracy
- [ ] Test pit window recommendations against historical data
- [ ] Validate threat detection false positive rate
- [ ] Measure degradation inference accuracy
- [ ] Run ablation studies on key features

### 6.3 Performance Optimization
- [ ] Profile backend inference speed
- [ ] Optimize frontend rendering performance
- [ ] Minimize WebSocket payload size
- [ ] Add request/response caching
- [ ] Load test with concurrent sessions

### 6.4 Error Handling & Edge Cases
- [ ] Handle missing telemetry packets
- [ ] Test with corrupted lap numbers
- [ ] Validate GPS jitter handling
- [ ] Test sensor outlier scenarios
- [ ] Handle incomplete race sessions

---

## Phase 7: Demo & Documentation 📹

### 7.1 Demo Preparation
- [ ] Select compelling race scenario for demo
- [ ] Prepare 3-minute demo video script
- [ ] Record live dashboard walkthrough
- [ ] Highlight key features (pace, pit, threat, degradation)
- [ ] Show replay mode with insights overlay
- [ ] Edit and produce final video

### 7.2 Documentation
- [ ] Write comprehensive README.md
- [ ] Create architecture diagram (Mermaid)
- [ ] Document data model and telemetry fields
- [ ] Add setup and installation instructions
- [ ] Create API documentation
- [ ] Write user guide for dashboard

### 7.3 Deployment
- [ ] Deploy frontend to Vercel
- [ ] Deploy backend API (Cloud Run, Railway, or similar)
- [ ] Configure production environment variables
- [ ] Setup CDN for assets
- [ ] Test production deployment end-to-end

### 7.4 Hackathon Submission
- [ ] Prepare GitHub repository (clean, organized)
- [ ] Write submission description
- [ ] Create demo video thumbnail
- [ ] Test all links and deployments
- [ ] Submit before deadline

---

## Phase 8: Future Enhancements (Post-MVP) 🚀

- [ ] AI-powered race engineer voice assistant
- [ ] Full multi-driver comparison dashboard
- [ ] Real-time anomaly detection (mechanical issues)
- [ ] Realistic traffic simulation
- [ ] Race replay with insights overlay
- [ ] Weather impact modeling
- [ ] Tire compound strategy optimizer
- [ ] Historical performance analytics

---

## Current Sprint Focus

**Starting with:** Phase 1 - Project Setup & Infrastructure

**Next Steps:**
1. Initialize Next.js frontend
2. Initialize FastAPI backend
3. Setup basic project structure
4. Install core dependencies

---

## Success Metrics Tracking

| Metric | Target | Current | Status |
|--------|--------|---------|--------|
| Pace forecast accuracy | ±0.25 sec | TBD | 🟡 Not started |
| Degradation detection | Within 3 laps | TBD | 🟡 Not started |
| Undercut gain accuracy | ±0.5 sec | TBD | 🟡 Not started |
| Dashboard latency | <1 second | TBD | 🟡 Not started |
| Decision time | <10 seconds | TBD | 🟡 Not started |

---

**Legend:**
- ✅ Completed
- 🟡 In Progress
- ⏸️ Blocked
- [ ] Not Started
