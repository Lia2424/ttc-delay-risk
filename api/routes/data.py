"""Data endpoints for fetching available routes and locations."""

from fastapi import APIRouter, HTTPException
import pandas as pd
from pathlib import Path
from typing import List, Dict
import re
import sys

from api.config import FEATURES_DIR, SCRIPTS_DIR, BASE_DIR
import sys
sys.path.insert(0, str(BASE_DIR / "scripts"))
from subway_stations import ALL_STATIONS, normalize_station_name as normalize_subway_station

# Try to load GTFS for better station matching
GTFS_DIR = BASE_DIR / "data" / "gtfs"
GTFS_AVAILABLE = GTFS_DIR.exists() and (GTFS_DIR / "stops.txt").exists()

router = APIRouter(prefix="/data", tags=["data"])

# Cache for routes and locations
_routes_cache = None
_locations_cache = None
_routes_by_mode_cache = None
_locations_by_mode_cache = None
def normalize_station_name(location: str) -> str:
    """Normalize station names by removing platform directions and extra info."""
    if pd.isna(location):
        return ""
    
    loc = str(location).strip().upper()
    
    # Remove "Towards X" first
    loc = re.sub(r'\s*-\s*Towards.*', '', loc, flags=re.IGNORECASE)
    loc = re.sub(r'\s+Towards.*', '', loc, flags=re.IGNORECASE)
    
    # Remove platform directions 
    loc = re.sub(r'\s*-\s*(NORTHBOUND|SOUTHBOUND|EASTBOUND|WESTBOUND)\s*(PLATFORM)?', '', loc, flags=re.IGNORECASE)
    loc = re.sub(r'\s+(NORTHBOUND|SOUTHBOUND|EASTBOUND|WESTBOUND)\s+PLATFORM', '', loc, flags=re.IGNORECASE)
    loc = re.sub(r'\s+(NORTHBOUND|SOUTHBOUND|EASTBOUND|WESTBOUND)\s*PLATFORM', '', loc, flags=re.IGNORECASE)
    loc = re.sub(r'\s*-\s*Subway Platform', '', loc, flags=re.IGNORECASE)
    loc = re.sub(r'\s*-\s*Platform', '', loc, flags=re.IGNORECASE)
    loc = re.sub(r'\s+Subway Platform', '', loc, flags=re.IGNORECASE)
    # Remove standalone "Platform" at the end
    loc = re.sub(r'\s+Platform\s*$', '', loc, flags=re.IGNORECASE)
    
    # Remove common suffixes in parentheses
    loc = re.sub(r'\s*\(APPROACHING.*?\)', '', loc, flags=re.IGNORECASE)
    loc = re.sub(r'\s*\(EXITING.*?\)', '', loc, flags=re.IGNORECASE)
    loc = re.sub(r'\s*\(LEAVING.*?\)', '', loc, flags=re.IGNORECASE)
    loc = re.sub(r'\s*\(NORTHBOUND.*?\)', '', loc, flags=re.IGNORECASE)
    loc = re.sub(r'\s*\(SOUTHBOUND.*?\)', '', loc, flags=re.IGNORECASE)
    loc = re.sub(r'\s*\(EASTBOUND.*?\)', '', loc, flags=re.IGNORECASE)
    loc = re.sub(r'\s*\(WESTBOUND.*?\)', '', loc, flags=re.IGNORECASE)
    
    # Remove any remaining parentheses content
    loc = re.sub(r'\s*\(.*?\)', '', loc)
    
    # Normalize "STATION" vs "STN" vs "STAT"
    loc = re.sub(r'\s+STN\b', ' STATION', loc, flags=re.IGNORECASE)
    loc = re.sub(r'\s+STAT\b', ' STATION', loc, flags=re.IGNORECASE)
    loc = re.sub(r'\s+STATIO\b', ' STATION', loc, flags=re.IGNORECASE)
    
    # Clean up extra spaces and normalize case
    loc = re.sub(r'\s+', ' ', loc).strip()
    
    # Title case for better display
    if loc:
        words = loc.split()
        loc = ' '.join(word.capitalize() for word in words)
    
    return loc

def load_routes_and_locations():
    """Load available routes and locations from features data."""
    global _routes_cache, _locations_cache, _routes_by_mode_cache, _locations_by_mode_cache
    
    if _routes_cache is not None:
        return _routes_cache, _locations_cache, _routes_by_mode_cache, _locations_by_mode_cache
    
    features_file = FEATURES_DIR / "features.csv"
    
    if not features_file.exists():
        raise FileNotFoundError("Features file not found. Please run feature engineering first.")
    
    try:
        df = pd.read_csv(features_file, low_memory=False, usecols=['route', 'location', 'mode'])
        
        # Get unique routes, sorted and cleaned
        routes = df['route'].dropna().unique().tolist()
        routes = [str(r).strip() for r in routes if str(r).strip()]
        routes = sorted(set(routes), key=lambda x: (
            # Sort: numbers first, then alphabetically
            (0, int(x)) if x.isdigit() else (1, x.lower())
        ))
        
        # Get unique locations, normalized and deduplicated
        locations_raw = df['location'].dropna().unique().tolist()
        
        # Normalize and deduplicate locations
        location_map = {}  # normalized -> original
        for loc in locations_raw:
            normalized = normalize_station_name(loc)
            if normalized and len(normalized) > 2:
                # Keep the shortest original name for each normalized version
                if normalized not in location_map or len(loc) < len(location_map[normalized]):
                    location_map[normalized] = loc
        
        locations = sorted(location_map.values(), key=str.lower)
        
        # Only subway routes: 1, 2, 4
        routes_by_mode = {
            'subway': ['1', '2', '4']
        }
        
        # Get locations - use official subway station list
        locations_by_mode = {}
        # Always use the official station list (87 stations)
        locations_by_mode['subway'] = sorted(list(ALL_STATIONS), key=str.lower)
        
        _routes_cache = routes
        _locations_cache = locations
        _routes_by_mode_cache = routes_by_mode
        _locations_by_mode_cache = locations_by_mode
        
        return routes, locations, routes_by_mode, locations_by_mode
    
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error loading data: {str(e)}")

@router.get("/routes")
async def get_routes(mode: str = None):
    """
    Get list of available routes (subway only).
    
    Args:
        mode: Must be 'subway' (other modes not supported)
    
    Returns:
        List of route names (1, 2, 4)
    """
    _, _, routes_by_mode, _ = load_routes_and_locations()
    
    # Only return subway routes
    return {"routes": routes_by_mode.get('subway', ['1', '2', '4'])}

@router.get("/locations")
async def get_locations(search: str = None, mode: str = None, route: str = None, limit: int = 100):
    """
    Get list of available subway stations.
    
    Args:
        search: Optional search term to filter stations
        mode: Must be 'subway' (other modes not supported)
        route: Optional route/line number (1, 2, 4) to filter stations by line
        limit: Maximum number of results (default: 100)
    
    Returns:
        List of official subway station names
    """
    from subway_stations import LINE_TO_STATIONS
    
    _, _, _, locations_by_mode = load_routes_and_locations()
    
    # Start with all subway stations
    locations = locations_by_mode.get('subway', sorted(list(ALL_STATIONS), key=str.lower))
    
    # Filter by route/line if specified
    if route and route in LINE_TO_STATIONS:
        line_stations = set(LINE_TO_STATIONS[route])
        locations = [loc for loc in locations if loc in line_stations]
    
    if search:
        search_lower = search.lower()
        filtered = [loc for loc in locations if search_lower in loc.lower()]
        return {"locations": filtered[:limit]}
    
    return {"locations": locations[:limit]}

@router.get("/routes-by-mode")
async def get_routes_by_mode():
    """
    Get routes grouped by transit mode.
    
    Returns:
        Dictionary with routes grouped by mode
    """
    _, _, routes_by_mode, _ = load_routes_and_locations()
    return routes_by_mode