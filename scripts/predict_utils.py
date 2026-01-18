"""
Shared utility functions for prediction.

Used by both the CLI prediction script and the FastAPI application.
"""

import pandas as pd
import numpy as np
import pickle
from pathlib import Path
from datetime import datetime
import sys

# Import subway station normalization
sys.path.insert(0, str(Path(__file__).parent))
from subway_stations import normalize_station_name as normalize_subway_station

MODEL_DIR = Path(__file__).parent.parent / "model"
FEATURES_DIR = Path(__file__).parent.parent / "data" / "features"


def load_model(model_path=None):
    """Load the trained model."""
    if model_path is None:
        model_path = MODEL_DIR / "delay_risk_model_latest.pkl"
    
    if not model_path.exists():
        raise FileNotFoundError(f"Model file not found: {model_path}")
    
    with open(model_path, 'rb') as f:
        model_data = pickle.load(f)
    
    model = model_data['model']
    feature_cols = model_data['feature_cols']
    
    return model, feature_cols, model_data


def load_feature_stats():
    """Load feature statistics and historical lookups for imputation."""
    features_file = FEATURES_DIR / "features.csv"
    if features_file.exists():
        df = pd.read_csv(features_file, low_memory=False)
        
        # Calculate medians for numeric columns (fallback values)
        numeric_cols = df.select_dtypes(include=[np.number]).columns
        stats = {}
        for col in numeric_cols:
            if col != 'min_delay':  # Don't include target
                median_val = df[col].median()
                if not pd.isna(median_val):
                    stats[col] = median_val
        
        # Create route/location-specific lookup dictionaries
        # These are the most important features for accurate predictions
        if 'route' in df.columns and 'min_delay' in df.columns:
            stats['_route_avg_delay'] = df.groupby('route')['min_delay'].mean().to_dict()
            stats['_route_delay_frequency'] = df.groupby('route').size().to_dict()
            
            # Route + hour averages
            route_hour_avg = df.groupby(['route', 'hour'])['min_delay'].mean()
            stats['_route_hour_avg'] = {}
            for (r, h), val in route_hour_avg.items():
                stats['_route_hour_avg'][(str(r), int(h))] = float(val)
            
            # Route + day_of_week averages
            route_dow_avg = df.groupby(['route', 'day_of_week'])['min_delay'].mean()
            stats['_route_dow_avg'] = {}
            for (r, d), val in route_dow_avg.items():
                stats['_route_dow_avg'][(str(r), int(d))] = float(val)
        
        if 'location' in df.columns and 'min_delay' in df.columns:
            stats['_location_avg_delay'] = df.groupby('location')['min_delay'].mean().to_dict()
            stats['_location_delay_frequency'] = df.groupby('location').size().to_dict()
        
        if 'incident' in df.columns and 'min_delay' in df.columns:
            stats['_incident_avg_delay'] = df.groupby('incident')['min_delay'].mean().to_dict()
        
        return stats
    return {}


def create_features_from_input(route, location, hour, day_of_week, month=None, 
                               minute=0, direction="Unknown", incident="Unknown", 
                               mode="bus", feature_cols=None, feature_stats=None):
    """Create feature vector from input parameters."""
    
    # Get current date/time defaults
    now = datetime.now()
    if month is None:
        month = now.month
    
    # Create base feature dictionary
    features = {}
    
    # Time features
    features['year'] = now.year
    features['month'] = month
    features['day_of_month'] = now.day
    features['day_of_week'] = day_of_week
    features['hour'] = hour
    features['minute'] = minute
    
    # Time flags
    features['is_weekend'] = 1 if day_of_week >= 5 else 0
    features['is_morning_rush'] = 1 if 7 <= hour < 9 else 0
    features['is_evening_rush'] = 1 if 16 <= hour < 19 else 0
    features['is_rush_hour'] = 1 if features['is_morning_rush'] or features['is_evening_rush'] else 0
    features['is_holiday_season'] = 1 if month in [11, 12] else 0
    
    # Season
    season_map = {
        12: 'Winter', 1: 'Winter', 2: 'Winter',
        3: 'Spring', 4: 'Spring', 5: 'Spring',
        6: 'Summer', 7: 'Summer', 8: 'Summer',
        9: 'Fall', 10: 'Fall', 11: 'Fall'
    }
    season = season_map.get(month, 'Unknown')
    
    # Time of day
    if 0 <= hour < 6:
        time_of_day = 'Night'
    elif 6 <= hour < 12:
        time_of_day = 'Morning'
    elif 12 <= hour < 18:
        time_of_day = 'Afternoon'
    else:
        time_of_day = 'Evening'
    
    # Route type derived from mode
    route_type = 3  # Default to bus
    if mode == 'subway':
        route_type = 1
    elif mode == 'streetcar':
        route_type = 0
    
    # Encode direction and incident (simplified - would need label encoders)
    direction_encoded = hash(str(direction)) % 1000
    incident_encoded = hash(str(incident)) % 1000
    
    # Historical features - use route/location-specific values from training data
    route_str = str(route).strip()
    # Normalize location to official station name
    location_str = normalize_subway_station(str(location).strip())
    
    if feature_stats:
        # Route-specific averages
        route_avg_lookup = feature_stats.get('_route_avg_delay', {})
        route_avg = route_avg_lookup.get(route_str)
        if route_avg is None:
            route_avg = feature_stats.get('route_avg_delay', 10.0)
        # Ensure it's a scalar, not a pandas Series
        if hasattr(route_avg, 'iloc'):
            route_avg = route_avg.iloc[0] if len(route_avg) > 0 else 10.0
        features['route_avg_delay'] = float(route_avg)
        
        # Location-specific averages
        location_avg_lookup = feature_stats.get('_location_avg_delay', {})
        loc_avg = location_avg_lookup.get(location_str)
        if loc_avg is None:
            # Try to find any variation of the station name
            for key in location_avg_lookup.keys():
                if location_str.lower() in str(key).lower() or str(key).lower() in location_str.lower():
                    loc_avg = location_avg_lookup[key]
                    break
        if loc_avg is None:
            loc_avg = feature_stats.get('location_avg_delay', 10.0)
        # Ensure it's a scalar, not a pandas Series
        if hasattr(loc_avg, 'iloc'):
            loc_avg = loc_avg.iloc[0] if len(loc_avg) > 0 else 10.0
        features['location_avg_delay'] = float(loc_avg)
        
        # Route + hour specific average
        route_hour_lookup = feature_stats.get('_route_hour_avg', {})
        route_hour_key = (route_str, hour)
        features['route_hour_avg_delay'] = route_hour_lookup.get(route_hour_key, features['route_avg_delay'])
        
        # Route + day_of_week specific average
        route_dow_lookup = feature_stats.get('_route_dow_avg', {})
        route_dow_key = (route_str, day_of_week)
        features['route_dow_avg_delay'] = route_dow_lookup.get(route_dow_key, features['route_avg_delay'])
        
        # Frequencies
        route_freq_lookup = feature_stats.get('_route_delay_frequency', {})
        features['route_delay_frequency'] = int(route_freq_lookup.get(route_str, feature_stats.get('route_delay_frequency', 100)))
        
        location_freq_lookup = feature_stats.get('_location_delay_frequency', {})
        features['location_delay_frequency'] = int(location_freq_lookup.get(location_str, feature_stats.get('location_delay_frequency', 100)))
        
        # Incident-specific average
        incident_avg_lookup = feature_stats.get('_incident_avg_delay', {})
        incident_str = str(incident).strip()
        features['incident_avg_delay'] = incident_avg_lookup.get(incident_str, feature_stats.get('incident_avg_delay', 10.0))
    else:
        # Default values (fallback)
        features['route_avg_delay'] = 10.0
        features['location_avg_delay'] = 10.0
        features['route_hour_avg_delay'] = 10.0
        features['route_dow_avg_delay'] = 10.0
        features['route_delay_frequency'] = 100
        features['location_delay_frequency'] = 100
        features['incident_avg_delay'] = 10.0
    
    features['route_type'] = route_type
    features['stop_lat'] = feature_stats.get('stop_lat', 43.65) if feature_stats else 43.65
    features['direction_encoded'] = direction_encoded
    features['incident_encoded'] = incident_encoded
    
    # One-hot encode mode
    features['mode_bus'] = 1 if mode == 'bus' else 0
    features['mode_streetcar'] = 1 if mode == 'streetcar' else 0
    features['mode_subway'] = 1 if mode == 'subway' else 0
    features['mode_nan'] = 0
    
    # One-hot encode route_type_name
    features['route_type_name_Unknown'] = 0
    features['route_type_name_nan'] = 0
    
    # One-hot encode season
    for s in ['Fall', 'Spring', 'Summer', 'Winter']:
        features[f'season_{s}'] = 1 if season == s else 0
    features['season_nan'] = 0
    
    # One-hot encode time_of_day
    for tod in ['Night', 'Morning', 'Afternoon', 'Evening']:
        features[f'time_of_day_{tod}'] = 1 if time_of_day == tod else 0
    features['time_of_day_nan'] = 0
    
    # Create DataFrame with all feature columns
    if feature_cols:
        feature_df = pd.DataFrame({col: [features.get(col, 0)] for col in feature_cols})
    else:
        feature_df = pd.DataFrame([features])
    
    return feature_df


def predict_delay(model, feature_vector):
    """Make delay prediction."""
    prediction = model.predict(feature_vector)[0]
    return max(0, prediction)  # Ensure non-negative

