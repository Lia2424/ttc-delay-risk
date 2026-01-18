#!/usr/bin/env python3
import pandas as pd
import numpy as np
from pathlib import Path
import sys

# Input: raw CSV files
RAW_DATA_DIR = Path(__file__).parent.parent / "data" / "raw" / "delays"

# Output: cleaned CSV files
CLEANED_DATA_DIR = Path(__file__).parent.parent / "data" / "cleaned"
CLEANED_DATA_DIR.mkdir(parents=True, exist_ok=True)

# Data quality thresholds
MIN_DELAY = 0  # Minimum valid delay (negative delays are errors)
MAX_DELAY = 180  # Maximum reasonable delay in minutes (3 hours)
MIN_GAP = 0  # Minimum valid gap

def standardize_columns(df: pd.DataFrame, mode: str) -> pd.DataFrame:
    """
    Standardize column names across different file formats.
    
    Bus/Streetcar files use: Report Date, Route, Location, Direction
    Subway files use: Date, Line, Station, Bound
    
    We'll standardize to: date, route, location, direction
    """
    df = df.copy()
    
    # Standardize date column
    if 'Report Date' in df.columns:
        df['date'] = pd.to_datetime(df['Report Date'], errors='coerce')
        df = df.drop(columns=['Report Date'])
    elif 'Date' in df.columns:
        df['date'] = pd.to_datetime(df['Date'], errors='coerce')
        df = df.drop(columns=['Date'])
    
    # Standardize route/line column
    if 'Route' in df.columns:
        df['route'] = df['Route'].astype(str)
        df = df.drop(columns=['Route'])
    elif 'Line' in df.columns:
        df['route'] = df['Line'].astype(str)
        df = df.drop(columns=['Line'])
    
    # Standardize location/station column
    if 'Location' in df.columns:
        df['location'] = df['Location'].astype(str)
        df = df.drop(columns=['Location'])
    elif 'Station' in df.columns:
        df['location'] = df['Station'].astype(str)
        df = df.drop(columns=['Station'])
    
    # Standardize direction/bound column
    if 'Direction' in df.columns:
        df['direction'] = df['Direction'].astype(str)
        df = df.drop(columns=['Direction'])
    elif 'Bound' in df.columns:
        df['direction'] = df['Bound'].astype(str)
        df = df.drop(columns=['Bound'])
    
    # Standardize other columns
    if 'Time' in df.columns:
        df['time'] = df['Time'].astype(str)
        df = df.drop(columns=['Time'])
    
    if 'Day' in df.columns:
        df['day'] = df['Day'].astype(str)
        df = df.drop(columns=['Day'])
    
    if 'Incident' in df.columns:
        df['incident'] = df['Incident'].astype(str)
        df = df.drop(columns=['Incident'])
    elif 'Code' in df.columns:
        df['incident'] = df['Code'].astype(str)
        df = df.drop(columns=['Code'])
    
    # Keep delay and gap columns (handle both "Min Delay"/"Delay" and "Min Gap"/"Gap")
    if 'Min Delay' in df.columns:
        df['min_delay'] = pd.to_numeric(df['Min Delay'], errors='coerce')
        df = df.drop(columns=['Min Delay'])
    elif 'Delay' in df.columns:
        df['min_delay'] = pd.to_numeric(df['Delay'], errors='coerce')
        df = df.drop(columns=['Delay'])
    
    if 'Min Gap' in df.columns:
        df['min_gap'] = pd.to_numeric(df['Min Gap'], errors='coerce')
        df = df.drop(columns=['Min Gap'])
    elif 'Gap' in df.columns:
        df['min_gap'] = pd.to_numeric(df['Gap'], errors='coerce')
        df = df.drop(columns=['Gap'])
    
    if 'Vehicle' in df.columns:
        df['vehicle'] = pd.to_numeric(df['Vehicle'], errors='coerce')
        df = df.drop(columns=['Vehicle'])
    
    # Remove _id column if present (not useful for ML, just an identifier)
    if '_id' in df.columns:
        df = df.drop(columns=['_id'])
    
    # Add mode (bus, streetcar, subway)
    df['mode'] = mode
    
    return df

def clean_data(df: pd.DataFrame) -> pd.DataFrame:
    """
    Clean the data by:
    1. Removing rows with missing critical data
    2. Removing outliers
    3. Standardizing values
    """
    initial_rows = len(df)
    df = df.copy()
    
    print(f"  Starting with {initial_rows:,} rows")
    
    # Remove rows with missing date (critical for time-based analysis)
    df = df.dropna(subset=['date'])
    print(f"  After removing missing dates: {len(df):,} rows")
    
    # Remove rows with missing delay (this is our target variable!)
    df = df.dropna(subset=['min_delay'])
    print(f"  After removing missing delays: {len(df):,} rows")
    
    # Remove invalid delays (negative or too high)
    df = df[(df['min_delay'] >= MIN_DELAY) & (df['min_delay'] <= MAX_DELAY)]
    print(f"  After removing invalid delays (< {MIN_DELAY} or > {MAX_DELAY}): {len(df):,} rows")
    
    # Remove invalid gaps (if present)
    if 'min_gap' in df.columns:
        df = df[(df['min_gap'].isna()) | (df['min_gap'] >= MIN_GAP)]
    
    # Clean direction values (standardize empty/missing to 'Unknown')
    if 'direction' in df.columns:
        df['direction'] = df['direction'].replace(['', 'None', 'nan', 'NaN'], 'Unknown')
        df['direction'] = df['direction'].fillna('Unknown')
    
    # Clean route values
    if 'route' in df.columns:
        df['route'] = df['route'].replace(['', 'None', 'nan', 'NaN'], 'Unknown')
        df['route'] = df['route'].fillna('Unknown')
    
    # Clean location values
    if 'location' in df.columns:
        df['location'] = df['location'].replace(['', 'None', 'nan', 'NaN'], 'Unknown')
        df['location'] = df['location'].fillna('Unknown')
    
    # Remove duplicate rows (if any)
    duplicates = df.duplicated().sum()
    if duplicates > 0:
        df = df.drop_duplicates()
        print(f"  Removed {duplicates:,} duplicate rows")
    
    final_rows = len(df)
    removed = initial_rows - final_rows
    print(f"  Final: {final_rows:,} rows (removed {removed:,} rows, {removed/initial_rows*100:.1f}%)")
    
    return df

def load_and_clean_file(file_path: Path, mode: str) -> pd.DataFrame:
    """Load a single CSV file and clean it."""
    print(f"\n📄 Processing {file_path.name}...")
    
    try:
        df = pd.read_csv(file_path)
        df = standardize_columns(df, mode)
        df = clean_data(df)
        
        return df
        
    except Exception as e:
        print(f"  ❌ Error processing {file_path.name}: {str(e)}")
        return pd.DataFrame()

def main():
    """Main function to clean all delay data files."""
    
    print("=" * 70)
    print("DATA CLEANING SCRIPT")
    print("=" * 70)
    print(f"\n📁 Input directory: {RAW_DATA_DIR}")
    print(f"📁 Output directory: {CLEANED_DATA_DIR}")
    
    if not RAW_DATA_DIR.exists():
        print(f"\n❌ Error: Input directory not found: {RAW_DATA_DIR}")
        sys.exit(1)
    
    # Find all CSV files
    bus_files = list((RAW_DATA_DIR / "bus").glob("*.csv"))
    streetcar_files = list((RAW_DATA_DIR / "streetcar").glob("*.csv"))
    subway_files = list((RAW_DATA_DIR / "subway").glob("*.csv"))
    
    all_files = {
        'bus': bus_files,
        'streetcar': streetcar_files,
        'subway': subway_files
    }
    
    print(f"\n📊 Found {len(subway_files)} subway CSV files to process")
    
    all_dataframes = []
    
    print(f"\n{'='*70}")
    print(f"Processing SUBWAY files only...")
    print(f"{'='*70}")
    
    for file_path in sorted(subway_files):
        df = load_and_clean_file(file_path, 'subway')
        if not df.empty:
            all_dataframes.append(df)
    
    if not all_dataframes:
        print("\n❌ No data was successfully processed!")
        sys.exit(1)
    
    # Combine all dataframes
    print(f"\n{'='*70}")
    print("Combining all datasets...")
    print(f"{'='*70}")
    
    combined_df = pd.concat(all_dataframes, ignore_index=True)
    print(f"\n✅ Combined dataset: {len(combined_df):,} rows")
    print(f"   Columns: {list(combined_df.columns)}")
    
    # Save cleaned data
    output_file = CLEANED_DATA_DIR / "all_delays_cleaned.csv"
    combined_df.to_csv(output_file, index=False)
    print(f"\n💾 Saved cleaned data to: {output_file}")
    
    # Also save summary statistics
    summary_file = CLEANED_DATA_DIR / "cleaning_summary.txt"
    with open(summary_file, 'w') as f:
        f.write("DATA CLEANING SUMMARY\n")
        f.write("=" * 70 + "\n\n")
        f.write(f"Total rows: {len(combined_df):,}\n")
        f.write(f"Date range: {combined_df['date'].min()} to {combined_df['date'].max()}\n")
        f.write(f"\nDelay statistics:\n")
        f.write(f"  Mean: {combined_df['min_delay'].mean():.2f} minutes\n")
        f.write(f"  Median: {combined_df['min_delay'].median():.2f} minutes\n")
        f.write(f"  Min: {combined_df['min_delay'].min():.2f} minutes\n")
        f.write(f"  Max: {combined_df['min_delay'].max():.2f} minutes\n")
        f.write(f"\nBy mode:\n")
        for mode in combined_df['mode'].unique():
            mode_df = combined_df[combined_df['mode'] == mode]
            f.write(f"  {mode}: {len(mode_df):,} rows\n")
        f.write(f"\nMissing values:\n")
        f.write(str(combined_df.isnull().sum()))
    
    print(f"📊 Summary saved to: {summary_file}")
    print(f"\n{'='*70}")
    print("✅ DATA CLEANING COMPLETE!")
    print(f"{'='*70}")


if __name__ == "__main__":
    main()

