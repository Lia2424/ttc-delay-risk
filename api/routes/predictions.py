"""Prediction routes."""

from fastapi import APIRouter, HTTPException

from api.models import (
    PredictionRequest,
    PredictionResponse,
    BatchPredictionRequest,
    BatchPredictionResponse
)
from api.dependencies import get_model
from api.services.prediction_service import make_prediction

router = APIRouter(prefix="/predict", tags=["predictions"])

@router.post("", response_model=PredictionResponse)
async def predict(request: PredictionRequest):
    """
    Make a single delay prediction.
    
    Returns predicted delay in minutes along with risk assessment.
    """
    try:
        model, feature_cols, model_data, feature_stats = get_model()
        
        return make_prediction(
            request=request,
            model=model,
            feature_cols=feature_cols,
            feature_stats=feature_stats,
            model_name=model_data.get('model_name', 'unknown')
        )
    
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=400, detail=f"Prediction error: {str(e)}")

@router.post("/batch", response_model=BatchPredictionResponse)
async def predict_batch(request: BatchPredictionRequest):
    """
    Make batch predictions.
    
    Accepts multiple prediction requests and returns predictions for all.
    """
    try:
        model, feature_cols, model_data, feature_stats = get_model()
        
        predictions = []
        for pred_request in request.predictions:
            prediction = make_prediction(
                request=pred_request,
                model=model,
                feature_cols=feature_cols,
                feature_stats=feature_stats,
                model_name=model_data.get('model_name', 'unknown')
            )
            predictions.append(prediction)
        
        return BatchPredictionResponse(
            predictions=predictions,
            total=len(predictions)
        )
    
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=400, detail=f"Batch prediction error: {str(e)}")
