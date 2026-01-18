"""Prediction service for handling delay predictions."""

import sys
from pathlib import Path

from api.config import SCRIPTS_DIR

# Add scripts directory to path
sys.path.insert(0, str(SCRIPTS_DIR))
from predict_utils import create_features_from_input, predict_delay

from api.models import PredictionRequest, PredictionResponse

def get_risk_level(delay_minutes: float) -> tuple[str, str]:
    """
    Get risk level and color based on delay prediction.
    
    Thresholds adjusted based on actual delay distribution:
    - < 1 minute: Low (minimal impact, ~50% of delays)
    - 1-3 minutes: Medium (noticeable delay, ~25% of delays)
    - 3-6 minutes: High (significant delay, ~15% of delays)
    - 6+ minutes: Very High (major delay, ~10% of delays)
    """
    if delay_minutes < 1:
        return "Low", "🟢"
    elif delay_minutes < 3:
        return "Medium", "🟡"
    elif delay_minutes < 6:
        return "High", "🟠"
    else:
        return "Very High", "🔴"

def make_prediction(
    request: PredictionRequest,
    model,
    feature_cols,
    feature_stats,
    model_name: str
) -> PredictionResponse:
    """
    Make a single delay prediction.
    
    Args:
        request: Prediction request
        model: Trained model
        feature_cols: List of feature column names
        feature_stats: Feature statistics for imputation
        model_name: Name of the model
    
    Returns:
        PredictionResponse with prediction results
    """
    # Create feature vector
    feature_vector = create_features_from_input(
        route=request.route,
        location=request.location,
        hour=request.hour,
        day_of_week=request.day_of_week,
        month=request.month,
        minute=request.minute or 0,
        direction=request.direction or "Unknown",
        incident=request.incident or "Unknown",
        mode=request.mode or "bus",
        feature_cols=feature_cols,
        feature_stats=feature_stats
    )
    
    # Make prediction
    delay_minutes = predict_delay(model, feature_vector)
    risk_level, risk_color = get_risk_level(delay_minutes)
    
    return PredictionResponse(
        predicted_delay_minutes=round(delay_minutes, 2),
        risk_level=risk_level,
        risk_color=risk_color,
        model_name=model_name
    )
