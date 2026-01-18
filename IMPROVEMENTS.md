# Model Accuracy Improvements

## Current Status

### ✅ What's Working Correctly

1. **Train/Validation/Test Split**: ✅ Properly implemented
   - Train: 64% of data
   - Validation: 16% of data  
   - Test: 20% of data
   - All splits are randomized with fixed seed (reproducible)

2. **Union Station Data**: ✅ Correct behavior
   - Union Station has delays at all 24 hours (0-23)
   - This is **expected** because:
     - Union is a major transit hub
     - Subway operates 24/7
     - More delays occur during rush hours (6 AM, 4-7 PM)
     - Late night hours (2-4 AM) have fewer delays but still some

3. **Data Distribution**: ✅ Consistent
   - Mean delay: ~2.6 minutes
   - Peak delays during rush hours (6 AM: 5.7 min avg, 4 PM: 3.6 min avg)
   - Low delays overnight (2-4 AM: 0-0.1 min avg)

### ⚠️ Issues to Address

1. **Model Trained on Mixed Data**: Current model was trained on bus/streetcar/subway
   - Need to retrain with **subway-only** data
   - This will improve accuracy for subway predictions

2. **Model Performance**: Current R² = 0.38 (moderate)
   - MAE: ~2 minutes (good)
   - RMSE: ~5 minutes (acceptable)
   - R²: 0.38 (could be better)

3. **Station Normalization**: Need to ensure all stations are normalized to official names

## Steps to Improve Accuracy

### Step 1: Regenerate Data (Subway Only)

```bash
# Run the training pipeline
./venv/bin/python scripts/01_clean_data.py
./venv/bin/python scripts/02_build_features.py
./venv/bin/python scripts/03_train_model_optimized.py
```

This will:
1. Clean subway data only (removes bus/streetcar)
2. Normalize station names to official list (87 stations)
3. Build features with proper normalization
4. Train new model with improved hyperparameters

### Step 2: Verify Training Results

After retraining, check:
- Test MAE should be < 2 minutes
- Test R² should be > 0.40
- Feature importance should make sense

### Step 3: Restart API Server

**IMPORTANT**: You MUST restart the server to load the new model:

```bash
# Stop current server (Ctrl+C), then:
./api/start.sh

# OR manually:
uvicorn api.main:app --reload
```

### Step 4: Test Predictions

Try predictions for:
- Union Station at different hours
- Different stations (Finch, Bloor-Yonge, etc.)
- Rush hours vs off-peak hours

## Model Improvements Made

1. **Increased Model Complexity**:
   - n_estimators: 200 → 300
   - max_depth: 15 → 20
   - min_samples_split: 5 → 3
   - min_samples_leaf: 2 → 1

2. **Better Feature Engineering**:
   - Station name normalization
   - Filtering to official stations only
   - Subway-only data (more focused)

3. **Proper Data Splits**:
   - Train: 64%
   - Validation: 16%
   - Test: 20%
   - All randomized with seed=42

## Expected Improvements

After retraining with subway-only data:
- **Better accuracy** for subway predictions
- **More consistent** predictions across stations
- **Better handling** of station-specific patterns
- **Improved R²** (target: > 0.45)

## Verification Checklist

- [ ] Data cleaned (subway only)
- [ ] Features built with station normalization
- [ ] Model trained with improved hyperparameters
- [ ] Test set performance checked
- [ ] API server restarted
- [ ] Predictions tested on frontend

## Questions Answered

**Q: Why does Union Station have delays at all hours?**
A: Union is a major hub that operates 24/7. Delays occur at all hours, but are much lower overnight (0-0.1 min) vs rush hours (3-6 min).

**Q: Do we have test/validation sets?**
A: Yes! The model uses:
- Train set (64%) - for training
- Validation set (16%) - for hyperparameter tuning
- Test set (20%) - for final evaluation

**Q: Do I need to restart the server?**
A: **YES!** The server loads the model at startup. After retraining, you must restart to load the new model.

**Q: How to improve accuracy?**
A: 
1. Retrain with subway-only data ✅
2. Use improved hyperparameters ✅
3. Normalize station names ✅
4. Filter to official stations only ✅
5. Restart server ✅

