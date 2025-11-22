# RaceCraft Live

**Real-time strategy intelligence tool for GR Cup race engineers**

RaceCraft Live transforms Toyota's telemetry and lap data into actionable ML-driven insights for pit window optimization, pace forecasting, threat detection, and degradation modeling during live race conditions.

## 🏁 Features

- **Pace Forecasting**: AI-powered lap time prediction for next 3-5 laps (±0.25 sec accuracy)
- **Pit Window Optimization**: Optimal pit window recommendations with position simulation
- **Undercut/Overcut Simulator**: Calculate time gained/lost by pitting early vs late
- **Threat Detection**: Real-time competitor analysis and attack probability (1-3 laps ahead)
- **Degradation Inference**: Tire and grip degradation analysis from telemetry signals

## 🏗️ Architecture

```
┌─────────────┐
│  Frontend   │  Next.js + shadcn/ui + Recharts + Mapbox GL
│  Dashboard  │  Real-time WebSocket updates
└──────┬──────┘
       │
       ├─WebSocket
       │
┌──────▼──────┐
│   Backend   │  FastAPI + Python
│     API     │  Pace, Pit, Threat, Degradation endpoints
└──────┬──────┘
       │
┌──────▼──────┐
│  ML Models  │  LightGBM / LSTM
│  & Feature  │  Telemetry processing
│ Engineering │  Kalman filters, lap segmentation
└─────────────┘
```

## 🚀 Quick Start

### Prerequisites

- Node.js 18+ and npm
- Python 3.11+
- Git

### Installation

1. **Clone the repository**
   ```bash
   git clone <repository-url>
   cd toyota-race-craft-live
   ```

2. **Setup Backend**
   ```bash
   cd backend
   python3 -m venv venv
   source venv/bin/activate  # On Windows: venv\Scripts\activate
   pip install -r requirements.txt
   cp .env.example .env
   ```

3. **Setup Frontend**
   ```bash
   cd frontend
   npm install
   cp .env.local.example .env.local
   # Edit .env.local and add your Mapbox token
   ```

### Running the Application

1. **Start the backend API**
   ```bash
   cd backend
   source venv/bin/activate
   python main.py
   # API runs on http://localhost:8000
   ```

2. **Start the frontend dashboard**
   ```bash
   cd frontend
   npm run dev
   # Dashboard runs on http://localhost:3000
   ```

3. **Access the application**
   - Frontend Dashboard: http://localhost:3000
   - API Documentation: http://localhost:8000/docs
   - Health Check: http://localhost:8000/health

## 📊 Data Model

The system processes CSV telemetry files with the following key fields:

| Field | Purpose |
|-------|---------|
| `Speed` | Pace modeling, lap time projection |
| `nmot` (RPM) | Corner exit performance |
| `aps` (pedal) | Throttle discipline |
| `pbrake_f/r` | Braking stability, degradation |
| `accx_can` | Braking quality, traction loss |
| `accy_can` | Cornering performance, lateral grip |
| `Steering_Angle` | Turn-in consistency |
| `GPS Lat/Long` | Racing line reconstruction |
| `lapdist` | Lap segmentation |
| `meta_time` | Primary time ordering |

## 🎯 Success Metrics

- **Pace forecast accuracy**: ±0.25 sec
- **Degradation detection**: Within 3 laps of onset
- **Undercut gain accuracy**: ±0.5 sec
- **Dashboard latency**: <1 second
- **Decision time**: <10 seconds

## 🏎️ Supported Tracks

- Barber Motorsports Park
- Circuit of the Americas (COTA)
- Indianapolis Motor Speedway Road Course
- Road America
- Sebring International Raceway
- Sonoma Raceway
- Virginia International Raceway (VIR)

## 📁 Project Structure

```
toyota-race-craft-live/
├── frontend/               # Next.js frontend
│   ├── app/               # Next.js app directory
│   ├── components/        # React components
│   │   ├── ui/           # shadcn/ui components
│   │   └── dashboard/    # Dashboard-specific components
│   ├── lib/              # Utilities
│   ├── hooks/            # React hooks
│   └── types/            # TypeScript types
│
├── backend/               # Python FastAPI backend
│   ├── api/              # API route handlers
│   ├── models/           # ML models
│   ├── utils/            # Utility functions
│   ├── data/             # Data storage
│   │   ├── raw/         # Raw telemetry CSVs
│   │   └── processed/   # Processed data
│   └── config/           # Configuration files
│
├── PRD.md                # Product Requirements Document
├── CLAUDE.md             # Claude Code instructions
├── PROGRESS.md           # Implementation progress tracker
└── README.md             # This file
```

## 🛠️ Technology Stack

### Frontend
- **Framework**: Next.js 14+ with TypeScript
- **UI Components**: shadcn/ui + Radix UI
- **Styling**: Tailwind CSS
- **Charts**: Recharts
- **Maps**: Mapbox GL
- **Real-time**: WebSockets

### Backend
- **Framework**: FastAPI
- **Data Processing**: pandas, numpy
- **ML Libraries**: scikit-learn, LightGBM, TensorFlow
- **Telemetry**: pykalman (Kalman filters)

## 🔧 Development

### API Endpoints

- `POST /api/pace/forecast` - Get pace predictions
- `POST /api/pit/recommend` - Get pit window recommendations
- `POST /api/threat/analyze` - Analyze competitor threats
- `POST /api/degradation/analyze` - Analyze tire degradation
- `GET /health` - Health check

See full API docs at http://localhost:8000/docs

### Adding Telemetry Data

1. Place raw telemetry CSV files in `backend/data/raw/`
2. Ensure files follow the expected schema (see CLAUDE.md)
3. Use the telemetry processor to load and process data

## 📝 Documentation

- [PRD.md](./PRD.md) - Full product requirements
- [CLAUDE.md](./CLAUDE.md) - Technical implementation guide
- [PROGRESS.md](./PROGRESS.md) - Implementation progress tracker
- [architect-diagram-and-ui.md](./architect-diagram-and-ui.md) - Architecture and UI wireframes

## 🎥 Demo

[Demo video link will be added]

## 📄 License

[License type to be determined]

## 👥 Contributors

Toyota Racing Development GR Cup Hackathon

## 🙏 Acknowledgments

- Toyota Racing Development
- GR Cup Racing Series
- [Other acknowledgments]
