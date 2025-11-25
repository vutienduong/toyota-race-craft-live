# Deployment Guide - RaceCraft Live Frontend

## Overview

The frontend supports two deployment modes:

1. **Sample Data Mode** - Standalone deployment without backend (perfect for Vercel)
2. **Backend Mode** - Full deployment with backend API connection (default)

## Configuration

The mode is controlled by the `NEXT_PUBLIC_DATA_MODE` environment variable:

```bash
# Sample mode - no backend required
NEXT_PUBLIC_DATA_MODE=sample

# Backend mode - requires backend API
NEXT_PUBLIC_DATA_MODE=backend  # (default)
```

---

## Mode 1: Sample Data Mode (Vercel Deployment)

Perfect for demos, previews, or when backend is not yet deployed.

### Features in Sample Mode:
- ✅ Fully functional dashboard UI
- ✅ Mock race data with realistic variations
- ✅ All charts and visualizations working
- ✅ Vehicle switching
- ✅ Simulated API delays for realistic feel
- ❌ No real telemetry data
- ❌ No backend connection required

### Vercel Deployment Steps:

1. **Push code to GitHub**
   ```bash
   git push origin main
   ```

2. **Import to Vercel**
   - Go to https://vercel.com/new
   - Import your GitHub repository
   - Select the `frontend` directory as root

3. **Set Environment Variables in Vercel:**
   ```
   NEXT_PUBLIC_DATA_MODE=sample
   ```

   Optional (not used in sample mode but can be set for documentation):
   ```
   NEXT_PUBLIC_API_URL=https://your-future-backend.com
   NEXT_PUBLIC_WS_URL=wss://your-future-backend.com/ws
   ```

4. **Deploy**
   - Click "Deploy"
   - Wait for build to complete
   - Your app will be live at `https://your-app.vercel.app`

### Local Testing (Sample Mode):

```bash
# Set environment variable
echo "NEXT_PUBLIC_DATA_MODE=sample" > .env.local

# Start dev server
npm run dev

# Open http://localhost:3000/dashboard
```

---

## Mode 2: Backend Mode (Full Deployment)

Production mode with real telemetry data from backend API.

### Features in Backend Mode:
- ✅ Real telemetry data from CSV files
- ✅ ML-powered predictions
- ✅ Live race data processing
- ✅ WebSocket real-time updates
- ⚠️ Requires backend API running

### Deployment Steps:

#### 1. Deploy Backend First

Deploy your FastAPI backend to:
- AWS Lambda + API Gateway
- Google Cloud Run
- Heroku
- Railway
- Your own server

Get the backend API URL (e.g., `https://api.racecraft.live`)

#### 2. Deploy Frontend to Vercel

Set these environment variables in Vercel:

```
NEXT_PUBLIC_DATA_MODE=backend
NEXT_PUBLIC_API_URL=https://api.racecraft.live
NEXT_PUBLIC_WS_URL=wss://api.racecraft.live/ws
```

#### 3. Configure CORS in Backend

Update your backend `.env` to allow your Vercel domain:

```bash
CORS_ORIGINS=https://your-app.vercel.app,https://your-app-preview.vercel.app
```

### Local Testing (Backend Mode):

```bash
# Terminal 1: Start backend
cd backend
python main.py

# Terminal 2: Start frontend
cd frontend
echo "NEXT_PUBLIC_DATA_MODE=backend" > .env.local
echo "NEXT_PUBLIC_API_URL=http://localhost:8000" >> .env.local
npm run dev

# Open http://localhost:3000/dashboard
```

---

## Environment Variable Reference

### Frontend (.env.local)

```bash
# Required: Data mode
NEXT_PUBLIC_DATA_MODE=backend  # or "sample"

# Required in backend mode:
NEXT_PUBLIC_API_URL=http://localhost:8000
NEXT_PUBLIC_WS_URL=ws://localhost:8000/ws

# Optional:
NEXT_PUBLIC_MAPBOX_TOKEN=your_mapbox_token_here
```

### Quick Setup Files

We provide example files for each scenario:

- `.env.local.example` - Template for local development
- `.env.vercel` - Template for Vercel deployment (sample mode)

---

## Switching Between Modes

### To switch from Backend to Sample:

1. Update `.env.local`:
   ```bash
   NEXT_PUBLIC_DATA_MODE=sample
   ```

2. Restart dev server:
   ```bash
   npm run dev
   ```

### To switch from Sample to Backend:

1. Ensure backend is running
2. Update `.env.local`:
   ```bash
   NEXT_PUBLIC_DATA_MODE=backend
   NEXT_PUBLIC_API_URL=http://localhost:8000
   ```

3. Restart dev server

---

## Verifying Your Mode

When the app loads, check the browser console:

**Sample Mode:**
```
[API Client] Running in SAMPLE DATA mode - no backend required
```

**Backend Mode:**
```
[API Client] Running in BACKEND mode - connecting to http://localhost:8000
```

---

## Troubleshooting

### Sample mode not working?
- Check browser console for `NEXT_PUBLIC_DATA_MODE=sample`
- Clear browser cache and reload
- Verify `.env.local` has `NEXT_PUBLIC_DATA_MODE=sample`

### Backend mode showing errors?
- Ensure backend is running: `curl http://localhost:8000/health`
- Check CORS configuration in backend
- Verify `NEXT_PUBLIC_API_URL` matches backend URL
- Check network tab for failed requests

### Data not updating?
- In sample mode: Data is randomized on each request (this is expected)
- In backend mode: Check backend logs for errors

---

## Best Practices

1. **Development:** Use backend mode for testing with real data
2. **Demos/Previews:** Use sample mode for quick deployments
3. **Production:** Use backend mode with deployed backend
4. **CI/CD Preview:** Use sample mode for pull request previews

---

## Sample Data Details

In sample mode, the frontend generates realistic race data:

- **5 sample vehicles** (Car #2, #4, #7, #10, #15)
- **Lap times:** 90-95 seconds with realistic variance
- **Degradation:** Simulated tire wear over stint
- **Threats:** Random rival analysis
- **Pit windows:** Dynamic recommendations based on lap count

Data regenerates on each request for variety in demos.
