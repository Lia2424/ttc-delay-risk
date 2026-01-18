# TTC Delay Risk Prediction API

FastAPI application for predicting TTC transit delay risk.

## Quick Start

### Start the API Server

```bash
# Option 1: Using the startup script
./api/start.sh

# Option 2: Using uvicorn directly
uvicorn api.main:app --host 0.0.0.0 --port 8000 --reload
```

The API will be available at:
- **API**: http://localhost:8000
- **Interactive Docs**: http://localhost:8000/docs
- **Alternative Docs**: http://localhost:8000/redoc

## API Endpoints

### Health Check
```bash
GET /health
```

### Model Information
```bash
GET /model/info
```

### Single Prediction
```bash
POST /predict
Content-Type: application/json

{
  "route": "102",
  "location": "WARDEN STATION",
  "hour": 8,
  "day_of_week": 1,
  "mode": "bus"
}
```

### Batch Predictions
```bash
POST /predict/batch
Content-Type: application/json

{
  "predictions": [
    {
      "route": "102",
      "location": "WARDEN STATION",
      "hour": 8,
      "day_of_week": 1,
      "mode": "bus"
    },
    {
      "route": "1",
      "location": "UNION STATION",
      "hour": 17,
      "day_of_week": 2,
      "mode": "subway"
    }
  ]
}
```

## Example Usage

### Using curl

```bash
# Single prediction
curl -X POST "http://localhost:8000/predict" \
  -H "Content-Type: application/json" \
  -d '{
    "route": "102",
    "location": "WARDEN STATION",
    "hour": 8,
    "day_of_week": 1,
    "mode": "bus"
  }'
```

### Using Python

```python
import requests

response = requests.post(
    "http://localhost:8000/predict",
    json={
        "route": "102",
        "location": "WARDEN STATION",
        "hour": 8,
        "day_of_week": 1,
        "mode": "bus"
    }
)

print(response.json())
# {
#   "predicted_delay_minutes": 8.36,
#   "risk_level": "Medium",
#   "risk_color": "🟡",
#   "model_name": "random_forest"
# }
```

## Response Format

```json
{
  "predicted_delay_minutes": 8.36,
  "risk_level": "Medium",
  "risk_color": "🟡",
  "model_name": "random_forest"
}
```

### Risk Levels
- 🟢 **Low**: < 5 minutes
- 🟡 **Medium**: 5-10 minutes
- 🟠 **High**: 10-15 minutes
- 🔴 **Very High**: > 15 minutes

## Request Parameters

| Parameter | Type | Required | Description |
|-----------|------|----------|-------------|
| `route` | string | Yes | Route ID or name (e.g., "102", "1") |
| `location` | string | Yes | Location/Station name |
| `hour` | integer | Yes | Hour of day (0-23) |
| `day_of_week` | integer | Yes | Day of week (0=Monday, 6=Sunday) |
| `month` | integer | No | Month (1-12), defaults to current month |
| `minute` | integer | No | Minute (0-59), defaults to 0 |
| `direction` | string | No | Direction, defaults to "Unknown" |
| `incident` | string | No | Incident type, defaults to "Unknown" |
| `mode` | string | No | Transit mode: "bus", "streetcar", or "subway" (default: "bus") |

