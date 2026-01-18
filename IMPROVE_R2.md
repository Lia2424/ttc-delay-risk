# How to Improve R² Score

## Current Performance
- **Current R²**: ~0.39 (39% variance explained)
- **Target**: >0.50 (50%+ variance explained)

## Strategies to Improve R²

### 1. **Hyperparameter Tuning** ✅ (Implemented)
- Use Optuna to optimize Random Forest, XGBoost, and LightGBM parameters
- **Expected improvement**: +0.05 to +0.10 R²
- **Run**: `python scripts/03_train_model_improved.py`

### 2. **Enhanced Feature Engineering** ✅ (Implemented)
- **Interaction features**: hour × day_of_week, location × hour, etc.
- **Polynomial features**: squared terms for important features
- **Expected improvement**: +0.03 to +0.08 R²

### 3. **Try Different Models**
- **XGBoost**: Often performs better than Random Forest
- **LightGBM**: Fast and often more accurate
- **Gradient Boosting**: Good baseline
- **Ensemble methods**: Voting/Stacking regressors
- **Expected improvement**: +0.05 to +0.15 R²

### 4. **Feature Selection**
- Remove low-importance features (can reduce overfitting)
- Use SelectKBest or recursive feature elimination
- **Expected improvement**: +0.02 to +0.05 R²

### 5. **Better Data Preprocessing**
- **Outlier handling**: Cap extreme values (already implemented)
- **Feature scaling**: StandardScaler for some models
- **Missing value imputation**: More sophisticated methods
- **Expected improvement**: +0.01 to +0.03 R²

### 6. **More Features to Consider**
- **Weather data**: Temperature, precipitation, snow
- **Holiday calendar**: Specific holidays (not just season)
- **Station characteristics**: Platform type, ridership, connections
- **Temporal patterns**: Rolling averages, lag features
- **Route characteristics**: Line length, number of stations
- **Expected improvement**: +0.05 to +0.15 R²

### 7. **Cross-Validation**
- Use K-fold cross-validation for more robust evaluation
- Helps identify overfitting
- **Expected improvement**: Better model selection

### 8. **More Data**
- Collect more recent data (2025+)
- Include more incident types
- **Expected improvement**: +0.02 to +0.10 R²

## Quick Start: Run Improved Training

```bash
# Make sure you have Optuna installed
pip install optuna

# Run the improved training script
python scripts/03_train_model_improved.py
```

This will:
1. Add interaction and polynomial features
2. Optimize hyperparameters with Optuna (50 trials per model)
3. Train multiple models (RF, XGBoost, LightGBM, Gradient Boosting)
4. Create an ensemble model
5. Select the best model based on validation R²

## Expected Results

With all improvements combined:
- **Conservative estimate**: R² = 0.45-0.50 (+15-28% improvement)
- **Optimistic estimate**: R² = 0.55-0.65 (+40-67% improvement)

## Additional Recommendations

### If R² is still low after improvements:

1. **Check data quality**:
   - Are there systematic errors in delay reporting?
   - Is the target variable (min_delay) accurate?

2. **Feature importance analysis**:
   - Which features are most important?
   - Are we missing key predictive signals?

3. **Residual analysis**:
   - Where is the model failing?
   - Are there patterns in prediction errors?

4. **Consider non-linear models**:
   - Neural networks (if you have enough data)
   - Support Vector Regression with RBF kernel

5. **Domain knowledge**:
   - Consult with TTC experts
   - Understand what actually causes delays

## Monitoring Improvements

After running the improved script, check:
- `model/training_summary_latest.txt` - Compare R² scores
- `model/feature_importance_*_latest.csv` - See which features matter most
- Compare validation vs test R² (check for overfitting)

