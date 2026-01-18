"""FastAPI dependencies for model and data loading."""

from fastapi import HTTPException
from typing import Tuple
import sys
from pathlib import Path

from api.config import SCRIPTS_DIR, DEFAULT_MODEL_FILE

# Add scripts directory to path
sys.path.insert(0, str(SCRIPTS_DIR))
from predict_utils import load_model, load_feature_stats

# Global state (loaded on startup)
_model = None
_feature_cols = None
_model_data = None
_feature_stats = None


def get_model() -> Tuple:
    """Get the loaded model and related data."""
    if _model is None:
        raise HTTPException(status_code=503, detail="Model not loaded")
    return _model, _feature_cols, _model_data, _feature_stats


def load_model_on_startup():
    """Load model and feature stats when API starts."""
    global _model, _feature_cols, _model_data, _feature_stats
    
    try:
        print("🚀 Loading model on startup...")
        _model, _feature_cols, _model_data = load_model(DEFAULT_MODEL_FILE)
        _feature_stats = load_feature_stats()
        print("✅ Model loaded successfully")
    except Exception as e:
        print(f"❌ Error loading model: {e}")
        raise

