"""Pydantic models for request/response validation."""

from pydantic import BaseModel, Field
from typing import List, Optional


class PredictionRequest(BaseModel):
    """Request model for single prediction."""
    route: str = Field(..., description="Route ID or name (e.g., '102', '1')")
    location: str = Field(..., description="Location/Station name")
    hour: int = Field(..., ge=0, le=23, description="Hour of day (0-23)")
    day_of_week: int = Field(..., ge=0, le=6, description="Day of week (0=Monday, 6=Sunday)")
    month: Optional[int] = Field(None, ge=1, le=12, description="Month (1-12), defaults to current month")
    minute: Optional[int] = Field(0, ge=0, le=59, description="Minute (0-59)")
    direction: Optional[str] = Field("Unknown", description="Direction")
    incident: Optional[str] = Field("Unknown", description="Incident type")
    mode: Optional[str] = Field("bus", description="Transit mode: bus, streetcar, or subway")
    
    class Config:
        json_schema_extra = {
            "example": {
                "route": "102",
                "location": "WARDEN STATION",
                "hour": 8,
                "day_of_week": 1,
                "mode": "bus"
            }
        }


class PredictionResponse(BaseModel):
    """Response model for prediction."""
    predicted_delay_minutes: float = Field(..., description="Predicted delay in minutes")
    risk_level: str = Field(..., description="Risk level: Low, Medium, High, Very High")
    risk_color: str = Field(..., description="Risk color indicator")
    model_name: str = Field(..., description="Name of the model used")
    
    class Config:
        json_schema_extra = {
            "example": {
                "predicted_delay_minutes": 8.36,
                "risk_level": "Medium",
                "risk_color": "🟡",
                "model_name": "random_forest"
            }
        }


class BatchPredictionRequest(BaseModel):
    """Request model for batch predictions."""
    predictions: List[PredictionRequest] = Field(..., description="List of prediction requests")


class BatchPredictionResponse(BaseModel):
    """Response model for batch predictions."""
    predictions: List[PredictionResponse] = Field(..., description="List of predictions")
    total: int = Field(..., description="Total number of predictions")


class ModelInfoResponse(BaseModel):
    """Response model for model information."""
    model_name: str
    model_type: str
    features_count: int
    training_date: Optional[str]
    performance: Optional[dict]


class HealthResponse(BaseModel):
    """Response model for health check."""
    status: str
    model_loaded: bool
    timestamp: str

