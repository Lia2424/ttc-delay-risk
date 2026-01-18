"""Health check and model information routes."""

from fastapi import APIRouter, HTTPException
from datetime import datetime

from api.models import HealthResponse, ModelInfoResponse
from api.dependencies import get_model

router = APIRouter(prefix="", tags=["health"])

@router.get("/", response_model=dict)
async def root():
    """Root endpoint."""
    return {
        "message": "TTC Delay Risk Prediction API",
        "version": "1.0.0",
        "docs": "/docs",
        "health": "/health"
    }

@router.get("/health", response_model=HealthResponse)
async def health_check():
    """Health check endpoint."""
    try:
        model, _, _, _ = get_model()
        return HealthResponse(
            status="healthy",
            model_loaded=model is not None,
            timestamp=datetime.now().isoformat()
        )
    except HTTPException:
        return HealthResponse(
            status="unhealthy",
            model_loaded=False,
            timestamp=datetime.now().isoformat()
        )

@router.get("/model/info", response_model=ModelInfoResponse)
async def get_model_info():
    """Get information about the loaded model."""
    model, feature_cols, model_data, _ = get_model()
    
    performance = None
    if model_data and 'metrics' in model_data:
        performance = model_data['metrics']
    
    return ModelInfoResponse(
        model_name=model_data.get('model_name', 'unknown'),
        model_type=type(model).__name__,
        features_count=len(feature_cols) if feature_cols else 0,
        training_date=model_data.get('timestamp'),
        performance=performance
    )
