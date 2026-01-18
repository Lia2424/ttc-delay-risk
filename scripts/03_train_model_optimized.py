#!/usr/bin/env python3
"""
Optimized Model Training Script - Focused on Important Features

This script:
1. Uses feature selection to keep only important features
2. Faster hyperparameter tuning (20 trials instead of 50)
3. Focuses on models that work best with fewer features
4. Trains faster while maintaining/improving performance

Run this AFTER feature engineering.
"""

import pandas as pd
import numpy as np
from pathlib import Path
import sys
import pickle
from datetime import datetime
import warnings
warnings.filterwarnings('ignore')

# Model imports
from sklearn.model_selection import train_test_split
from sklearn.ensemble import RandomForestRegressor, GradientBoostingRegressor
from sklearn.metrics import mean_absolute_error, mean_squared_error, r2_score
from sklearn.feature_selection import SelectKBest, f_regression

# Hyperparameter tuning
try:
    import optuna
    OPTUNA_AVAILABLE = True
except ImportError:
    OPTUNA_AVAILABLE = False

# XGBoost is optional
try:
    import xgboost as xgb
    XGBOOST_AVAILABLE = True
except (ImportError, Exception):
    XGBOOST_AVAILABLE = False

# CONFIGURATION
FEATURES_DIR = Path(__file__).parent.parent / "data" / "features"
MODEL_DIR = Path(__file__).parent.parent / "model"
MODEL_DIR.mkdir(parents=True, exist_ok=True)

RANDOM_STATE = 42
TEST_SIZE = 0.2
VAL_SIZE = 0.2
EXCLUDE_COLS = ['date', 'route', 'location', 'mode', 'datetime', 'min_delay']

# Features to keep based on importance analysis
# These are the top features that matter most
IMPORTANT_FEATURES = [
    'incident_avg_delay',
    'incident_encoded',
    'minute',
    'day_of_month',
    'direction_encoded',
    'location_avg_delay',
    'location_delay_frequency',
    'year',
    'route_hour_avg_delay',
    'month',
    'route_dow_avg_delay',
    'hour',
    'day_of_week',
    'route_avg_delay',
    'route_delay_frequency',
    'is_weekend',
    'is_rush_hour',
    'is_holiday_season',
]


def add_key_interaction_features(df: pd.DataFrame) -> pd.DataFrame:
    """Add only the most important interaction features."""
    df = df.copy()
    
    print("🔗 Creating key interaction features...")
    
    # Only add interactions that are likely to be useful
    if 'hour' in df.columns and 'day_of_week' in df.columns:
        df['hour_dow'] = df['hour'] * df['day_of_week']
    
    if 'location_avg_delay' in df.columns and 'hour' in df.columns:
        df['location_hour_interaction'] = df['location_avg_delay'] * df['hour']
    
    if 'route_avg_delay' in df.columns and 'hour' in df.columns:
        df['route_hour_interaction'] = df['route_avg_delay'] * df['hour']
    
    if 'incident_avg_delay' in df.columns and 'hour' in df.columns:
        df['incident_hour_interaction'] = df['incident_avg_delay'] * df['hour']
    
    print(f"   ✅ Added {4} key interaction features")
    return df


def load_features():
    """Load feature-engineered data."""
    print("📂 Loading feature-engineered data...")
    
    features_file = FEATURES_DIR / "features.csv"
    if not features_file.exists():
        print(f"❌ Error: Features file not found: {features_file}")
        sys.exit(1)
    
    df = pd.read_csv(features_file, low_memory=False)
    print(f"✅ Loaded {len(df):,} rows × {df.shape[1]} columns")
    
    return df


def prepare_data(df: pd.DataFrame, use_feature_selection=True):
    """Prepare data for training with feature selection."""
    df = df.copy()
    
    print("\n🔧 Preparing data...")
    
    # Add only key interaction features
    df = add_key_interaction_features(df)
    
    # Separate target
    if 'min_delay' not in df.columns:
        print("❌ Error: Target variable 'min_delay' not found!")
        sys.exit(1)
    
    y = df['min_delay'].values
    
    # Handle outliers in target (cap at 99th percentile)
    p99 = np.percentile(y, 99)
    y_capped = np.clip(y, 0, p99)
    print(f"   Target: mean={y.mean():.2f}, std={y.std():.2f}, p99={p99:.2f}")
    print(f"   Capped {np.sum(y > p99)} outliers at p99")
    y = y_capped
    
    # Select features
    all_feature_cols = [col for col in df.columns if col not in EXCLUDE_COLS]
    X = df[all_feature_cols].copy()
    
    print(f"   Initial features: {len(all_feature_cols)} columns")
    
    # Handle missing values
    print("\n   Handling missing values...")
    numeric_cols = X.select_dtypes(include=[np.number]).columns
    for col in numeric_cols:
        if X[col].isnull().sum() > 0:
            median_val = X[col].median()
            X[col] = X[col].fillna(median_val)
    
    bool_cols = X.select_dtypes(include=['bool']).columns
    for col in bool_cols:
        if X[col].isnull().sum() > 0:
            X[col] = X[col].fillna(False)
    
    bool_cols = X.select_dtypes(include=['bool']).columns
    X[bool_cols] = X[bool_cols].astype(int)
    
    # Remove rows where target is missing
    valid_mask = ~pd.isna(y)
    X = X[valid_mask]
    y = y[valid_mask]
    
    # Feature selection: Keep only important features + interactions
    if use_feature_selection:
        print("\n   Selecting important features...")
        
        # Start with important base features
        feature_cols_to_keep = [f for f in IMPORTANT_FEATURES if f in X.columns]
        
        # Add interaction features we created
        interaction_features = [f for f in X.columns if 'interaction' in f or 'hour_dow' in f]
        feature_cols_to_keep.extend(interaction_features)
        
        # Add any other features that exist and might be useful
        # (but exclude zero-importance ones we know about)
        zero_importance_features = [
            'route_type', 'route_type_name_nan', 'route_type_name_Subway',
            'mode_nan', 'mode_subway', 'stop_lon', 'stop_lat',
            'time_of_day_nan', 'season_nan'
        ]
        
        # Keep features that are numeric and not in zero-importance list
        for col in X.columns:
            if col not in feature_cols_to_keep and col not in zero_importance_features:
                if X[col].dtype in [np.int64, np.float64] and X[col].nunique() > 1:
                    feature_cols_to_keep.append(col)
        
        X = X[feature_cols_to_keep]
        print(f"   ✅ Selected {len(feature_cols_to_keep)} important features")
        print(f"   Removed {len(all_feature_cols) - len(feature_cols_to_keep)} low-importance features")
        
        feature_cols = feature_cols_to_keep
    else:
        feature_cols = list(X.columns)
    
    print(f"   Final dataset: {len(X):,} rows × {len(feature_cols)} features")
    
    return X, y, feature_cols


def split_data(X, y):
    """Split data into train/validation/test sets."""
    print("\n📊 Splitting data...")
    
    X_train_val, X_test, y_train_val, y_test = train_test_split(
        X, y, test_size=TEST_SIZE, random_state=RANDOM_STATE, shuffle=True
    )
    
    X_train, X_val, y_train, y_val = train_test_split(
        X_train_val, y_train_val, test_size=VAL_SIZE, random_state=RANDOM_STATE, shuffle=True
    )
    
    print(f"   Train:      {len(X_train):,} rows ({len(X_train)/len(X)*100:.1f}%)")
    print(f"   Validation: {len(X_val):,} rows ({len(X_val)/len(X)*100:.1f}%)")
    print(f"   Test:       {len(X_test):,} rows ({len(X_test)/len(X)*100:.1f}%)")
    
    return X_train, X_val, X_test, y_train, y_val, y_test


def evaluate_model(y_true, y_pred, model_name=""):
    """Evaluate model performance."""
    mae = mean_absolute_error(y_true, y_pred)
    rmse = np.sqrt(mean_squared_error(y_true, y_pred))
    r2 = r2_score(y_true, y_pred)
    
    metrics = {
        'MAE': mae,
        'RMSE': rmse,
        'R²': r2
    }
    
    if model_name:
        print(f"\n   {model_name} Performance:")
    print(f"      MAE:  {mae:.2f} minutes")
    print(f"      RMSE: {rmse:.2f} minutes")
    print(f"      R²:   {r2:.4f}")
    
    return metrics


def optimize_random_forest(trial, X_train, y_train, X_val, y_val):
    """Optimize Random Forest hyperparameters."""
    params = {
        'n_estimators': trial.suggest_int('n_estimators', 200, 400),
        'max_depth': trial.suggest_int('max_depth', 15, 25),
        'min_samples_split': trial.suggest_int('min_samples_split', 2, 8),
        'min_samples_leaf': trial.suggest_int('min_samples_leaf', 1, 4),
        'max_features': trial.suggest_categorical('max_features', ['sqrt', 'log2']),
        'bootstrap': True,
        'random_state': RANDOM_STATE,
        'n_jobs': -1,
        'verbose': 0
    }
    
    model = RandomForestRegressor(**params)
    model.fit(X_train, y_train)
    y_pred = model.predict(X_val)
    r2 = r2_score(y_val, y_pred)
    return r2


def optimize_xgboost(trial, X_train, y_train, X_val, y_val):
    """Optimize XGBoost hyperparameters."""
    params = {
        'n_estimators': trial.suggest_int('n_estimators', 150, 300),
        'max_depth': trial.suggest_int('max_depth', 4, 8),
        'learning_rate': trial.suggest_float('learning_rate', 0.05, 0.2, log=True),
        'subsample': trial.suggest_float('subsample', 0.7, 0.9),
        'colsample_bytree': trial.suggest_float('colsample_bytree', 0.7, 0.9),
        'min_child_weight': trial.suggest_int('min_child_weight', 1, 5),
        'random_state': RANDOM_STATE,
        'n_jobs': -1,
        'verbosity': 0
    }
    
    model = xgb.XGBRegressor(**params)
    model.fit(
        X_train, y_train,
        eval_set=[(X_val, y_val)],
        early_stopping_rounds=15,
        verbose=False
    )
    y_pred = model.predict(X_val)
    r2 = r2_score(y_val, y_pred)
    return r2


def main():
    """Main function to train optimized models."""
    print("=" * 70)
    print("OPTIMIZED MODEL TRAINING - FOCUSED FEATURES")
    print("=" * 70)
    
    # Load data
    df = load_features()
    
    # Prepare data with feature selection
    X, y, feature_cols = prepare_data(df, use_feature_selection=True)
    
    # Split data
    X_train, X_val, X_test, y_train, y_val, y_test = split_data(X, y)
    
    models = {}
    results = {}
    best_params = {}
    
    # Hyperparameter tuning (fewer trials for speed)
    if OPTUNA_AVAILABLE:
        print("\n" + "=" * 70)
        print("HYPERPARAMETER TUNING (20 trials per model)")
        print("=" * 70)
        
        n_trials = 20  # Reduced from 50 for speed
        
        # Optimize Random Forest
        print(f"\n🔍 Optimizing Random Forest ({n_trials} trials)...")
        study_rf = optuna.create_study(direction='maximize')
        study_rf.optimize(
            lambda trial: optimize_random_forest(trial, X_train, y_train, X_val, y_val),
            n_trials=n_trials,
            show_progress_bar=True
        )
        best_params['random_forest'] = study_rf.best_params
        print(f"   ✅ Best R²: {study_rf.best_value:.4f}")
        
        # Optimize XGBoost
        if XGBOOST_AVAILABLE:
            print(f"\n🔍 Optimizing XGBoost ({n_trials} trials)...")
            study_xgb = optuna.create_study(direction='maximize')
            study_xgb.optimize(
                lambda trial: optimize_xgboost(trial, X_train, y_train, X_val, y_val),
                n_trials=n_trials,
                show_progress_bar=True
            )
            best_params['xgboost'] = study_xgb.best_params
            print(f"   ✅ Best R²: {study_xgb.best_value:.4f}")
    else:
        print("\n⚠️  Optuna not available. Using default hyperparameters.")
        best_params['random_forest'] = {
            'n_estimators': 300,
            'max_depth': 20,
            'min_samples_split': 3,
            'min_samples_leaf': 1,
            'max_features': 'sqrt'
        }
    
    # Train models
    print("\n" + "=" * 70)
    print("TRAINING MODELS")
    print("=" * 70)
    
    # Random Forest
    print("\n🌳 Training Random Forest...")
    rf_params = best_params.get('random_forest', {})
    rf_params.update({
        'bootstrap': True,
        'random_state': RANDOM_STATE,
        'n_jobs': -1,
        'verbose': 0
    })
    rf_model = RandomForestRegressor(**rf_params)
    rf_model.fit(X_train, y_train)
    
    y_val_pred_rf = rf_model.predict(X_val)
    y_test_pred_rf = rf_model.predict(X_test)
    
    print("\n   Validation Set:")
    val_metrics = evaluate_model(y_val, y_val_pred_rf, "Random Forest")
    print("\n   Test Set:")
    test_metrics = evaluate_model(y_test, y_test_pred_rf, "Random Forest")
    
    models['random_forest'] = rf_model
    results['random_forest'] = {'val': val_metrics, 'test': test_metrics}
    
    # XGBoost
    if XGBOOST_AVAILABLE:
        print("\n🌲 Training XGBoost...")
        xgb_params = best_params.get('xgboost', {
            'n_estimators': 200,
            'max_depth': 6,
            'learning_rate': 0.1,
            'subsample': 0.8,
            'colsample_bytree': 0.8
        })
        xgb_params.update({
            'random_state': RANDOM_STATE,
            'n_jobs': -1,
            'verbosity': 0
        })
        xgb_model = xgb.XGBRegressor(**xgb_params)
        xgb_model.fit(
            X_train, y_train,
            eval_set=[(X_val, y_val)],
            early_stopping_rounds=15,
            verbose=False
        )
        
        y_val_pred_xgb = xgb_model.predict(X_val)
        y_test_pred_xgb = xgb_model.predict(X_test)
        
        print("\n   Validation Set:")
        val_metrics = evaluate_model(y_val, y_val_pred_xgb, "XGBoost")
        print("\n   Test Set:")
        test_metrics = evaluate_model(y_test, y_test_pred_xgb, "XGBoost")
        
        models['xgboost'] = xgb_model
        results['xgboost'] = {'val': val_metrics, 'test': test_metrics}
    
    # Select best model
    print("\n" + "=" * 70)
    print("MODEL COMPARISON")
    print("=" * 70)
    
    best_model_name = None
    best_val_r2 = -float('inf')
    
    for model_name, result in results.items():
        val_r2 = result['val']['R²']
        test_r2 = result['test']['R²']
        print(f"\n{model_name.upper()}:")
        print(f"   Validation R²: {val_r2:.4f}")
        print(f"   Test R²:       {test_r2:.4f}")
        
        if val_r2 > best_val_r2:
            best_val_r2 = val_r2
            best_model_name = model_name
    
    print(f"\n🏆 Best Model: {best_model_name.upper()} (Validation R²: {best_val_r2:.4f})")
    
    # Save best model
    best_model = models[best_model_name]
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    
    model_file = MODEL_DIR / f"delay_risk_model_{best_model_name}_{timestamp}.pkl"
    with open(model_file, 'wb') as f:
        pickle.dump({
            'model': best_model,
            'model_name': best_model_name,
            'feature_cols': feature_cols,
            'metrics': results[best_model_name],
            'best_params': best_params.get(best_model_name, {}),
            'timestamp': timestamp
        }, f)
    
    print(f"\n💾 Saved best model to: {model_file}")
    
    # Save as latest
    latest_model_file = MODEL_DIR / "delay_risk_model_latest.pkl"
    with open(latest_model_file, 'wb') as f:
        pickle.dump({
            'model': best_model,
            'model_name': best_model_name,
            'feature_cols': feature_cols,
            'metrics': results[best_model_name],
            'best_params': best_params.get(best_model_name, {}),
            'timestamp': timestamp
        }, f)
    
    print(f"💾 Saved as latest model: {latest_model_file}")
    
    # Save feature importance
    if hasattr(best_model, 'feature_importances_'):
        importance_df = pd.DataFrame({
            'feature': feature_cols,
            'importance': best_model.feature_importances_
        }).sort_values('importance', ascending=False)
        
        importance_file = MODEL_DIR / f"feature_importance_{best_model_name}_latest.csv"
        importance_df.to_csv(importance_file, index=False)
        print(f"\n📊 Feature importance saved to: {importance_file}")
        
        print("\n   Top 10 Most Important Features:")
        for idx, row in importance_df.head(10).iterrows():
            print(f"      {row['feature']}: {row['importance']:.4f}")
    
    # Save training summary
    summary_file = MODEL_DIR / "training_summary_latest.txt"
    with open(summary_file, 'w') as f:
        f.write("OPTIMIZED MODEL TRAINING SUMMARY\n")
        f.write("=" * 70 + "\n\n")
        f.write(f"Training Date: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}\n")
        f.write(f"Best Model: {best_model_name}\n\n")
        f.write(f"Dataset Size: {len(X):,} rows\n")
        f.write(f"Features: {len(feature_cols)} (optimized selection)\n")
        f.write(f"Train: {len(X_train):,} rows\n")
        f.write(f"Validation: {len(X_val):,} rows\n")
        f.write(f"Test: {len(X_test):,} rows\n\n")
        
        f.write("MODEL PERFORMANCE\n")
        f.write("-" * 70 + "\n")
        for model_name, result in results.items():
            f.write(f"\n{model_name.upper()}:\n")
            f.write(f"  Validation:\n")
            for metric, value in result['val'].items():
                f.write(f"    {metric}: {value:.4f}\n")
            f.write(f"  Test:\n")
            for metric, value in result['test'].items():
                f.write(f"    {metric}: {value:.4f}\n")
    
    print(f"\n📊 Training summary saved to: {summary_file}")
    
    print("\n" + "=" * 70)
    print("✅ OPTIMIZED MODEL TRAINING COMPLETE!")
    print("=" * 70)
    print(f"\n📈 Results:")
    print(f"   Features used: {len(feature_cols)} (reduced from ~50)")
    print(f"   Best R²: {best_val_r2:.4f}")
    print(f"   Previous R²: ~0.39")
    if best_val_r2 > 0.39:
        improvement = ((best_val_r2 - 0.39) / 0.39 * 100)
        print(f"   Improvement: +{improvement:.1f}%")
    else:
        print(f"   Note: Similar performance with fewer features (faster training)")


if __name__ == "__main__":
    main()

