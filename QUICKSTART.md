# Quick Start Guide

## Starting the Application

### 1. Start the Backend API

In one terminal:

```bash
# Option 1: Using the startup script
./api/start.sh

# Option 2: Direct uvicorn command
cd /Users/liamoradpour/Documents/ttc-delay-risk
source venv/bin/activate
uvicorn api.main:app --host 0.0.0.0 --port 8000 --reload
```

The API will be available at: http://localhost:8000

### 2. Start the Frontend

In another terminal:

```bash
cd web
npm run dev
```

The frontend will be available at: http://localhost:3000

## Troubleshooting

### Network Error / Cannot Connect to API

**Problem:** Frontend shows "Backend not connected" or network errors.

**Solution:**
1. Make sure the backend is running (check terminal 1)
2. Verify the API is accessible: Open http://localhost:8000/health in your browser
3. Check that port 8000 is not blocked by firewall
4. The frontend will automatically show connection status in the header

### CORS Errors

**Problem:** Browser console shows CORS errors.

**Solution:** The API already has CORS enabled for all origins. If you still see errors:
- Make sure you're accessing the frontend at http://localhost:3000 (not file://)
- Check that the backend is running

### Model Not Loaded

**Problem:** API returns "Model not loaded" error.

**Solution:**
- Make sure `model/delay_risk_model_latest.pkl` exists
- Check the backend startup logs for model loading errors
- Run the training script if needed: `python scripts/03_train_model_optimized.py`

## Testing the API

You can test the API directly:

```bash
# Health check
curl http://localhost:8000/health

# Get model info
curl http://localhost:8000/model/info

# Make a prediction
curl -X POST http://localhost:8000/predict \
  -H "Content-Type: application/json" \
  -d '{
    "route": "102",
    "location": "WARDEN STATION",
    "hour": 8,
    "day_of_week": 1,
    "mode": "bus"
  }'
```

## Full Stack Flow

1. **Backend** (FastAPI) - Port 8000
   - Loads trained model on startup
   - Serves prediction endpoints
   - Handles CORS

2. **Frontend** (React + TypeScript) - Port 3000
   - Connects to backend API
   - Shows connection status
   - Provides prediction form and results

Both need to be running simultaneously!

