#!/usr/bin/env python3
import pandas as pd
import numpy as np
from pathlib import Path
from datetime import datetime
import sys

# Import subway station mapping
import sys
sys.path.insert(0, str(Path(__file__).parent))
from subway_stations import normalize_station_name, is_valid_subway_station, ALL_STATIONS

# GTFS imports
try:
    import pandas as pd
    GTFS_AVAILABLE = GTFS_DIR.exists() and (GTFS_DIR / "stops.txt").exists()
except:
    GTFS_AVAILABLE = False

# Input files
CLEANED_DATA_DIR = Path(__file__).parent.parent / "data" / "cleaned"
GTFS_DIR = Path(__file__).parent.parent / "data" / "gtfs"

# Output directory
FEATURES_DIR = Path(__file__).parent.parent / "data" / "features"
FEATURES_DIR.mkdir(parents=True, exist_ok=True)

# Rush hour definitions (24-hour format)
MORNING_RUSH = (7, 9)  # 7 AM - 9 AM
EVENING_RUSH = (16, 19)  # 4 PM - 7 PM

def create_time_features(df: pd.DataFrame) -> pd.DataFrame:
    """Create time-based features from date and time columns."""
    df = df.copy()
    
    # Parse date and time
    df['datetime'] = pd.to_datetime(df['date'].astype(str) + ' ' + df['time'].astype(str), errors='coerce')
    
    # Extract time components
    df['year'] = df['datetime'].dt.year
    df['month'] = df['datetime'].dt.month
    df['day_of_month'] = df['datetime'].dt.day
    df['day_of_week'] = df['datetime'].dt.dayofweek  # 0=Monday, 6=Sunday
    df['hour'] = df['datetime'].dt.hour
    df['minute'] = df['datetime'].dt.minute
    
    # Day of week name (for reference)
    df['day_name'] = df['datetime'].dt.day_name()
    
    # Is weekend?
    df['is_weekend'] = (df['day_of_week'] >= 5).astype(int)
    
    # Is rush hour?
    df['is_morning_rush'] = ((df['hour'] >= MORNING_RUSH[0]) & (df['hour'] < MORNING_RUSH[1])).astype(int)
    df['is_evening_rush'] = ((df['hour'] >= EVENING_RUSH[0]) & (df['hour'] < EVENING_RUSH[1])).astype(int)
    df['is_rush_hour'] = (df['is_morning_rush'] | df['is_evening_rush']).astype(int)
    
    # Time of day categories
    df['time_of_day'] = pd.cut(
        df['hour'],
        bins=[0, 6, 12, 18, 24],
        labels=['Night', 'Morning', 'Afternoon', 'Evening'],
        include_lowest=True
    )
    
    # Season
    df['season'] = df['month'].map({
        12: 'Winter', 1: 'Winter', 2: 'Winter',
        3: 'Spring', 4: 'Spring', 5: 'Spring',
        6: 'Summer', 7: 'Summer', 8: 'Summer',
        9: 'Fall', 10: 'Fall', 11: 'Fall'
    })
    
    # Is holiday season? (Nov-Dec)
    df['is_holiday_season'] = (df['month'].isin([11, 12])).astype(int)
    
    return df

def load_gtfs_stops():
    """Load GTFS stops data for subway stations."""
    if not GTFS_AVAILABLE:
        return None, None
    
    try:
        stops_df = pd.read_csv(GTFS_DIR / "stops.txt")
        routes_df = pd.read_csv(GTFS_DIR / "routes.txt")
        
        # Filter to subway routes (route_type = 1)
        subway_routes = routes_df[routes_df['route_type'] == 1]
        
        # Get stops for subway routes
        # We'll match by station name later
        return stops_df, subway_routes
    except Exception as e:
        print(f"   ⚠️  Warning: Could not load GTFS data: {e}")
        return None, None

def merge_gtfs_features(df: pd.DataFrame, stops_df: pd.DataFrame = None) -> pd.DataFrame:
    """Merge GTFS station information (coordinates, etc.)."""
    df = df.copy()
    
    if stops_df is None:
        df['stop_lat'] = np.nan
        df['stop_lon'] = np.nan
        return df
    
    print("   📍 Merging GTFS station coordinates...")
    
    # Create a lookup: normalized station name -> coordinates
    station_coords = {}
    for _, stop in stops_df.iterrows():
        stop_name = str(stop['stop_name']).strip()
        normalized = normalize_station_name(stop_name)
        
        # Only add if it's an official station
        if normalized in ALL_STATIONS:
            if normalized not in station_coords:
                station_coords[normalized] = {
                    'lat': stop.get('stop_lat', np.nan),
                    'lon': stop.get('stop_lon', np.nan)
                }
    
    # Match stations
    df['stop_lat'] = df['location'].map(lambda x: station_coords.get(x, {}).get('lat', np.nan))
    df['stop_lon'] = df['location'].map(lambda x: station_coords.get(x, {}).get('lon', np.nan))
    
    matched = df['stop_lat'].notna().sum()
    print(f"   ✅ Matched {matched:,} stations ({matched/len(df)*100:.1f}%) with GTFS coordinates")
    
    return df

def create_route_type_features(df: pd.DataFrame) -> pd.DataFrame:
    """Create route type features from mode."""
    df = df.copy()
    
    # All subway now
    df['route_type'] = 1  # Subway
    
    # Route type categories (all subway now)
    df['route_type_name'] = 'Subway'
    
    return df

def create_historical_features(df: pd.DataFrame) -> pd.DataFrame:
    """Create aggregated historical features."""
    df = df.copy()
    
    # Sort by datetime for rolling calculations
    df = df.sort_values('datetime').reset_index(drop=True)
    
    print("📊 Creating historical features...")
    
    # Average delay by route (overall)
    route_avg_delay = df.groupby('route')['min_delay'].mean().to_dict()
    df['route_avg_delay'] = df['route'].map(route_avg_delay)
    
    # Average delay by location
    location_avg_delay = df.groupby('location')['min_delay'].mean().to_dict()
    df['location_avg_delay'] = df['location'].map(location_avg_delay)
    
    # Average delay by route and hour
    route_hour_avg = df.groupby(['route', 'hour'])['min_delay'].mean().to_dict()
    df['route_hour_avg_delay'] = df.apply(
        lambda row: route_hour_avg.get((row['route'], row['hour']), row['route_avg_delay']),
        axis=1
    )
    
    # Average delay by route and day of week
    route_dow_avg = df.groupby(['route', 'day_of_week'])['min_delay'].mean().to_dict()
    df['route_dow_avg_delay'] = df.apply(
        lambda row: route_dow_avg.get((row['route'], row['day_of_week']), row['route_avg_delay']),
        axis=1
    )
    
    # Count of delays by route (frequency)
    route_delay_count = df.groupby('route').size().to_dict()
    df['route_delay_frequency'] = df['route'].map(route_delay_count)
    
    # Count of delays by location
    location_delay_count = df.groupby('location').size().to_dict()
    df['location_delay_frequency'] = df['location'].map(location_delay_count)
    
    # Average delay by incident type
    incident_avg_delay = df.groupby('incident')['min_delay'].mean().to_dict()
    df['incident_avg_delay'] = df['incident'].map(incident_avg_delay)
    
    print("   ✅ Historical features created")
    
    return df


def encode_categorical_features(df: pd.DataFrame) -> pd.DataFrame:
    """Encode categorical variables."""
    df = df.copy()
    
    print("🔤 Encoding categorical features...")
    
    # One-hot encode: mode, route_type_name, season, time_of_day
    categorical_cols = ['mode', 'route_type_name', 'season', 'time_of_day']
    
    for col in categorical_cols:
        if col in df.columns:
            dummies = pd.get_dummies(df[col], prefix=col, dummy_na=True)
            df = pd.concat([df, dummies], axis=1)
            print(f"   ✅ Encoded {col}: {len(dummies.columns)} columns")
    
    # Label encode: direction, incident (too many unique values for one-hot)
    from sklearn.preprocessing import LabelEncoder
    
    le_direction = LabelEncoder()
    le_incident = LabelEncoder()
    
    df['direction_encoded'] = le_direction.fit_transform(df['direction'].astype(str))
    df['incident_encoded'] = le_incident.fit_transform(df['incident'].astype(str))
    
    print(f"   ✅ Encoded direction: {len(le_direction.classes_)} unique values")
    print(f"   ✅ Encoded incident: {len(le_incident.classes_)} unique values")
    
    return df

def main():
    """Main function to build features."""
    
    print("=" * 70)
    print("FEATURE ENGINEERING SCRIPT")
    print("=" * 70)
    
    # Load cleaned data
    print(f"\n📂 Loading cleaned data from {CLEANED_DATA_DIR}...")
    cleaned_file = CLEANED_DATA_DIR / "all_delays_cleaned.csv"
    
    if not cleaned_file.exists():
        print(f"❌ Error: Cleaned data file not found: {cleaned_file}")
        print("   Please run 01_clean_data.py first!")
        sys.exit(1)
    
    df = pd.read_csv(cleaned_file)
    print(f"✅ Loaded {len(df):,} rows")
    
    # Load GTFS data for subway stations
    print(f"\n📂 Loading GTFS data for subway stations...")
    stops_df, subway_routes_df = load_gtfs_stops()
    if stops_df is not None:
        print(f"   ✅ Loaded {len(stops_df):,} stops from GTFS")
    else:
        print(f"   ⚠️  GTFS data not available, continuing without it")
    
    # Normalize station names to official names
    print(f"\n🏷️  Normalizing station names...")
    initial_count = len(df)
    df['location_normalized'] = df['location'].apply(normalize_station_name)
    
    # Filter to only valid subway stations
    df['is_valid_station'] = df['location_normalized'].apply(lambda x: x in ALL_STATIONS)
    df = df[df['is_valid_station']].copy()
    df['location'] = df['location_normalized']  # Replace with normalized name
    df = df.drop(columns=['location_normalized', 'is_valid_station'])
    
    removed = initial_count - len(df)
    print(f"   ✅ Normalized station names")
    print(f"   ✅ Filtered to valid stations: {len(df):,} rows (removed {removed:,} invalid entries)")
    
    # Create time features
    print(f"\n⏰ Creating time-based features...")
    df = create_time_features(df)
    print(f"   ✅ Created time features")
    
    # Merge GTFS features (coordinates)
    print(f"\n🔗 Merging GTFS features...")
    df = merge_gtfs_features(df, stops_df)
    
    # Create route type features from mode
    print(f"\n🔗 Creating route type features...")
    df = create_route_type_features(df)
    print(f"   ✅ Created route type features")
    
    # Create historical features
    df = create_historical_features(df)
    
    # Encode categorical features
    df = encode_categorical_features(df)
    
    # Select final feature columns (exclude raw text columns that are encoded)
    # Keep: all numeric features, encoded features, and a few key identifiers
    feature_cols = [
        # Time features
        'year', 'month', 'day_of_month', 'day_of_week', 'hour', 'minute',
        'is_weekend', 'is_morning_rush', 'is_evening_rush', 'is_rush_hour', 'is_holiday_season',
        # Historical features
        'route_avg_delay', 'location_avg_delay', 'route_hour_avg_delay', 
        'route_dow_avg_delay', 'route_delay_frequency', 'location_delay_frequency',
        'incident_avg_delay',
        # Route type features (derived from mode)
        'route_type',
        # GTFS features
        'stop_lat', 'stop_lon',
        # Encoded features
        'direction_encoded', 'incident_encoded',
        # Target variable
        'min_delay',
    ]
    
    # Add one-hot encoded columns
    one_hot_cols = [col for col in df.columns if any(col.startswith(prefix) for prefix in ['mode_', 'route_type_name_', 'season_', 'time_of_day_'])]
    feature_cols.extend(one_hot_cols)
    
    # Keep only columns that exist
    feature_cols = [col for col in feature_cols if col in df.columns]
    
    # Also keep some identifier columns for reference
    identifier_cols = ['date', 'route', 'location', 'mode', 'datetime']
    identifier_cols = [col for col in identifier_cols if col in df.columns]
    
    # Create final feature dataset
    final_df = df[feature_cols + identifier_cols].copy()
    
    # Save feature-engineered data
    output_file = FEATURES_DIR / "features.csv"
    final_df.to_csv(output_file, index=False)
    print(f"\n💾 Saved feature-engineered data to: {output_file}")
    print(f"   Shape: {final_df.shape[0]:,} rows × {final_df.shape[1]} columns")
    
    # Save feature summary
    summary_file = FEATURES_DIR / "feature_summary.txt"
    with open(summary_file, 'w') as f:
        f.write("FEATURE ENGINEERING SUMMARY\n")
        f.write("=" * 70 + "\n\n")
        f.write(f"Total rows: {len(final_df):,}\n")
        f.write(f"Total features: {len(feature_cols)}\n")
        f.write(f"\nFeature columns:\n")
        for col in feature_cols:
            f.write(f"  - {col}\n")
        f.write(f"\nData types:\n")
        f.write(str(final_df[feature_cols].dtypes))
        f.write(f"\n\nMissing values:\n")
        f.write(str(final_df[feature_cols].isnull().sum()))
    
    print(f"📊 Summary saved to: {summary_file}")
    print(f"\n{'=' * 70}")
    print("✅ FEATURE ENGINEERING COMPLETE!")
    print(f"{'=' * 70}")

if __name__ == "__main__":
    main()