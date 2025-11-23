# RaceCraft Live Backend

FastAPI backend for RaceCraft Live race strategy intelligence system.

## Features

- **Pace Forecasting**: ML-powered lap time prediction (±0.25s accuracy target)
- **Degradation Analysis**: Tire grip degradation inference from telemetry
- **Pit Strategy**: Optimal pit window recommendations
- **Threat Detection**: Real-time competitor analysis

## Setup

### Prerequisites

- Python 3.8+
- pip or conda

### Installation

1. Install dependencies:

```bash
cd backend
pip install -r requirements.txt
```

2. Configure environment variables:

```bash
cp .env.example .env
```

Edit `.env` with your configuration (see Configuration section below).

3. Run the development server:

```bash
uvicorn main:app --reload --host 0.0.0.0 --port 8000
```

The API will be available at `http://localhost:8000`

## Configuration

The backend uses environment variables for configuration. Copy `.env.example` to `.env` and adjust settings:

### Data Mode Configuration

**DATA_MODE** - Controls whether to use sample data or real CSV files
- `sample` (default): Generates synthetic telemetry data for testing
- `real`: Loads actual race data from CSV files in the data directory

**DATA_DIR** - Path to directory containing race data
- Default: `../data/barber`
- Should contain files like:
  - `R1_barber_telemetry_data.csv`
  - `R1_barber_lap_time.csv`
  - `R2_barber_telemetry_data.csv`
  - etc.

**DEFAULT_RACE** - Default race session to use
- Values: `R1` or `R2`
- Default: `R1`

### Example Configurations

**Development (Sample Data)**:
```env
DATA_MODE=sample
DEFAULT_RACE=R1
```

**Production (Real Data)**:
```env
DATA_MODE=real
DATA_DIR=../data/barber
DEFAULT_RACE=R1
```

### API Configuration

**API_HOST** - Host to bind to (default: `0.0.0.0`)

**API_PORT** - Port to listen on (default: `8000`)

**DEBUG** - Enable debug mode (default: `True`)

**CORS_ORIGINS** - Comma-separated allowed origins
- Default: `http://localhost:3000,http://localhost:3001`

### Model Configuration

**MODEL_PATH** - Directory for trained ML models
- Default: `./models/trained`

**PACE_MODEL_VERSION** - Version identifier for pace model
- Default: `v1`

## API Endpoints

### Pace Forecasting

**POST** `/api/pace/forecast`

Predict lap times for next 3-5 laps.

Request:
```json
{
  "car_id": "GR86-000-0",
  "session_id": "R1",
  "current_lap": 12,
  "laps_ahead": 5
}
```

Response:
```json
{
  "car_id": "GR86-000-0",
  "predictions": [
    {
      "lap_number": 13,
      "predicted_time": 90.25,
      "delta": 0.15,
      "confidence": 0.90
    }
  ],
  "current_pace": 90.10,
  "trend": "degrading"
}
```

### Degradation Analysis

**POST** `/api/degradation/analyze`

Analyze tire degradation.

Request:
```json
{
  "car_id": "GR86-000-0",
  "session_id": "R1",
  "current_lap": 15
}
```

Response:
```json
{
  "car_id": "GR86-000-0",
  "degradation_curve": [
    {
      "lap": 10,
      "delta_seconds": 0.5,
      "severity": 0.2
    }
  ],
  "degradation_rate": 0.05,
  "primary_causes": [
    {
      "cause_type": "lateral_grip_loss",
      "confidence": 0.78,
      "indicators": ["Reduced lateral G", "Understeering"]
    }
  ],
  "stint_health": "optimal",
  "recommended_action": "Monitor closely"
}
```

### Pit Strategy

**POST** `/api/pit/optimize`

Get optimal pit window recommendations.

### Threat Detection

**POST** `/api/threat/detect`

Analyze competitor threats and attack probability.

### Current Metrics

**GET** `/api/current/pace/{car_id}`

Get current pace metrics.

**GET** `/api/current/degradation/{car_id}`

Get current degradation status.

## Data Format

The backend expects telemetry data in long format (as exported from race timing systems):

**Telemetry CSV Schema**:
```
meta_time, vehicle_id, vehicle_number, lap, telemetry_name, telemetry_value
```

**Required Telemetry Signals**:
- `speed` (km/h)
- `Steering_Angle` (degrees)
- `gear` (1-6)
- `nmot` (RPM)
- `aps` (throttle %, 0-100)
- `pbrake_f`, `pbrake_r` (brake pressure, bar)
- `accx_can`, `accy_can` (G forces)
- `VBOX_Lat_Min`, `VBOX_Long_Minutes` (GPS)
- `Laptrigger_lapdist_dls` (distance from start/finish, meters)

See `DATA_PLAN.md` for detailed data specifications.

## ML Models

### Pace Forecaster

- **Algorithm**: LightGBM Regressor
- **Input**: Last 5 laps of features (pace, brake variance, throttle variance, lateral G)
- **Output**: Predicted lap times for next 1-5 laps
- **Target Accuracy**: ±0.25 seconds (RMSE)

### Degradation Model

- **Algorithm**: Feature engineering + statistical analysis
- **Inputs**: Lateral G trends, steering angle changes, braking point shifts
- **Output**: Degradation severity (0-100%), stint health, recommended actions

## Development

### Running Tests

```bash
pytest tests/
```

### Code Style

```bash
black backend/
flake8 backend/
```

### Project Structure

```
backend/
├── api/              # FastAPI route handlers
├── models/           # ML model implementations
├── services/         # Business logic layer
├── utils/            # Data processing utilities
├── main.py           # FastAPI application
└── requirements.txt  # Python dependencies
```

## Troubleshooting

### "File not found" errors with real data

- Ensure `DATA_DIR` points to the correct directory
- Verify CSV files exist with correct naming: `R1_barber_telemetry_data.csv`
- Check file permissions

### Model accuracy issues

- Ensure at least 10 laps of data for training
- Check telemetry quality (no missing signals)
- Verify track configuration matches (Barber = 2,380m)

### Performance issues

- Use `DATA_MODE=sample` for development/testing
- Consider loading only specific vehicles with `vehicle_id` parameter
- Enable caching (enabled by default in RaceService)

## License

Proprietary - Toyota Racing Development
