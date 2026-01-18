#!/usr/bin/env python3
import argparse
from pathlib import Path
import sys

# Import shared utilities
sys.path.insert(0, str(Path(__file__).parent))
from predict_utils import load_model, load_feature_stats, create_features_from_input, predict_delay

def main():
    parser = argparse.ArgumentParser(description='Predict TTC delay risk')
    
    # Single prediction arguments
    parser.add_argument('--route', type=str, help='Route ID or name (e.g., "102", "1")')
    parser.add_argument('--location', type=str, help='Location/Station name')
    parser.add_argument('--hour', type=int, help='Hour of day (0-23)')
    parser.add_argument('--day_of_week', type=int, help='Day of week (0=Monday, 6=Sunday)')
    parser.add_argument('--month', type=int, help='Month (1-12), defaults to current month')
    parser.add_argument('--minute', type=int, default=0, help='Minute (0-59), defaults to 0')
    parser.add_argument('--direction', type=str, default='Unknown', help='Direction')
    parser.add_argument('--incident', type=str, default='Unknown', help='Incident type')
    parser.add_argument('--mode', type=str, default='bus', choices=['bus', 'streetcar', 'subway'], help='Transit mode')
    
    # Batch prediction
    parser.add_argument('--file', type=str, help='CSV file with prediction inputs')
    parser.add_argument('--output', type=str, help='Output file for predictions')
    
    # Model selection
    parser.add_argument('--model', type=str, help='Path to specific model file')
    
    args = parser.parse_args()
    
    print("=" * 70)
    print("TTC DELAY RISK PREDICTION")
    print("=" * 70)
    
    # Load model
    try:
        model, feature_cols, model_data = load_model(args.model)
    except Exception as e:
        print(f"❌ Error loading model: {e}")
        return
    
    # Load feature stats for imputation
    feature_stats = load_feature_stats()
    
    # Single prediction
    if args.route and args.location and args.hour is not None and args.day_of_week is not None:
        print(f"\n🔮 Making prediction...")
        print(f"   Route: {args.route}")
        print(f"   Location: {args.location}")
        print(f"   Time: {args.hour:02d}:{args.minute:02d} (Day {args.day_of_week})")
        print(f"   Mode: {args.mode}")
        
        feature_vector = create_features_from_input(
            route=args.route,
            location=args.location,
            hour=args.hour,
            day_of_week=args.day_of_week,
            month=args.month,
            minute=args.minute,
            direction=args.direction,
            incident=args.incident,
            mode=args.mode,
            feature_cols=feature_cols,
            feature_stats=feature_stats
        )
        
        prediction = predict_delay(model, feature_vector)
        
        print(f"\n📊 Predicted Delay: {prediction:.2f} minutes")
        print(f"   Risk Level: ", end="")
        if prediction < 5:
            print("🟢 Low")
        elif prediction < 10:
            print("🟡 Medium")
        elif prediction < 15:
            print("🟠 High")
        else:
            print("🔴 Very High")
    
    # Batch prediction from file
    elif args.file:
        print(f"\n📂 Loading predictions from: {args.file}")
        df = pd.read_csv(args.file)
        
        predictions = []
        for idx, row in df.iterrows():
            feature_vector = create_features_from_input(
                route=row.get('route', 'Unknown'),
                location=row.get('location', 'Unknown'),
                hour=row.get('hour', 12),
                day_of_week=row.get('day_of_week', 1),
                month=row.get('month'),
                minute=row.get('minute', 0),
                direction=row.get('direction', 'Unknown'),
                incident=row.get('incident', 'Unknown'),
                mode=row.get('mode', 'bus'),
                feature_cols=feature_cols,
                feature_stats=feature_stats
            )
            pred = predict_delay(model, feature_vector)
            predictions.append(pred)
        
        df['predicted_delay_minutes'] = predictions
        
        output_file = args.output or 'predictions_output.csv'
        df.to_csv(output_file, index=False)
        print(f"✅ Saved {len(predictions)} predictions to: {output_file}")
    
    else:
        parser.print_help()
        print("\nExample usage:")
        print("  python scripts/04_predict.py --route '102' --location 'WARDEN STATION' --hour 8 --day_of_week 1")
        print("  python scripts/04_predict.py --file predictions.csv --output results.csv")

if __name__ == "__main__":
    main()