"""Configuration settings for the API."""

from pathlib import Path

# Base directory (project root)
BASE_DIR = Path(__file__).parent.parent

# Model and data directories
MODEL_DIR = BASE_DIR / "model"
FEATURES_DIR = BASE_DIR / "data" / "features"
SCRIPTS_DIR = BASE_DIR / "scripts"

# API settings
API_TITLE = "TTC Delay Risk Prediction API"
API_DESCRIPTION = "API for predicting TTC transit delay risk"
API_VERSION = "1.0.0"

# CORS settings
CORS_ORIGINS = ["*"]  # In production, specify allowed origins

# Model file
DEFAULT_MODEL_FILE = MODEL_DIR / "delay_risk_model_latest.pkl"

