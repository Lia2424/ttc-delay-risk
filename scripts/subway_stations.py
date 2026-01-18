# Official subway stations by line
SUBWAY_STATIONS = {
    # Line 1 (Yonge-University)
    'Line 1': [
        'Finch', 'North York Centre', 'Sheppard–Yonge', 'York Mills', 'Lawrence',
        'Eglinton', 'Davisville', 'St. Clair', 'Summerhill', 'Rosedale',
        'Bloor–Yonge', 'Wellesley', 'College', 'TMU', 'Queen', 'King', 'Union',
        'St. Andrew', 'Osgoode', 'St. Patrick', "Queen's Park", 'Museum',
        'St. George', 'Spadina', 'Dupont', 'St. Clair West', 'Cedarvale',
        'Glencairn', 'Lawrence West', 'Yorkdale', 'Wilson', 'Sheppard West',
        'Downsview Park', 'Finch West', 'York University', 'Pioneer Village',
        'Highway 407', 'Vaughan Metropolitan Centre'
    ],
    
    # Line 2 (Bloor-Danforth)
    'Line 2': [
        'Kipling', 'Islington', 'Royal York', 'Old Mill', 'Jane', 'Runnymede',
        'High Park', 'Keele', 'Dundas West', 'Lansdowne', 'Dufferin', 'Ossington',
        'Christie', 'Bathurst', 'Bay', 'Sherbourne', 'Castle Frank', 'Broadview',
        'Chester', 'Pape', 'Donlands', 'Greenwood', 'Coxwell', 'Woodbine',
        'Main Street', 'Victoria Park', 'Warden', 'Kennedy'
    ],
    
    # Line 4 (Sheppard)
    'Line 4': [
        'Bayview', 'Bessarion', 'Leslie', 'Don Mills'
    ],
    
    # Line 6 (Finch West - opening 2025, may not be in historical data)
    'Line 6': [
        'Humber College', 'Westmore', 'Martin Grove', 'Albion', 'Stevenson',
        'Mount Olive', 'Rowntree Mills', 'Pearldale', 'Duncanwoods', 'Milvan Rumike',
        'Emery', 'Signet Arrow', 'Norfinch Oakdale', 'Jane and Finch', 'Driftwood',
        'Tobermory', 'Sentinel'
    ]
}

# All unique station names (normalized)
ALL_STATIONS = set()
for line_stations in SUBWAY_STATIONS.values():
    ALL_STATIONS.update(line_stations)

# Create mapping: station -> list of lines it's on
STATION_TO_LINES = {}
for line_name, stations in SUBWAY_STATIONS.items():
    for station in stations:
        if station not in STATION_TO_LINES:
            STATION_TO_LINES[station] = []
        STATION_TO_LINES[station].append(line_name)

# Create mapping: line number -> stations
LINE_TO_STATIONS = {
    '1': SUBWAY_STATIONS.get('Line 1', []),
    '2': SUBWAY_STATIONS.get('Line 2', []),
    '4': SUBWAY_STATIONS.get('Line 4', []),
    '6': SUBWAY_STATIONS.get('Line 6', [])  # Future line
}

# Station name variations mapping (common misspellings/variations -> official name)
STATION_VARIATIONS = {
    # Common variations
    'sheppard yonge': 'Sheppard–Yonge',
    'sheppard-yonge': 'Sheppard–Yonge',
    'bloor yonge': 'Bloor–Yonge',
    'bloor-yonge': 'Bloor–Yonge',
    'st george': 'St. George',
    'st. george': 'St. George',
    'st andrew': 'St. Andrew',
    'st. andrew': 'St. Andrew',
    'st patrick': 'St. Patrick',
    'st. patrick': 'St. Patrick',
    'st clair': 'St. Clair',
    'st. clair': 'St. Clair',
    'st clair west': 'St. Clair West',
    'st. clair west': 'St. Clair West',
    'queens park': "Queen's Park",
    "queen's park": "Queen's Park",
    'queens quay': "Queen's Quay",
    "queen's quay": "Queen's Quay",
    'main street': 'Main Street',
    'finch west': 'Finch West',
    'north york centre': 'North York Centre',
    'north york center': 'North York Centre',
    'downsview park': 'Downsview Park',
    'york university': 'York University',
    'pioneer village': 'Pioneer Village',
    'highway 407': 'Highway 407',
    'old mill': 'Old Mill',
    'high park': 'High Park',
    'dundas west': 'Dundas West',
    'castle frank': 'Castle Frank',
    'main st': 'Main Street',
    'victoria park': 'Victoria Park',
    'sheppard west': 'Sheppard West',
    'norfinch oakdale': 'Norfinch Oakdale',
    'jane and finch': 'Jane and Finch',
    'tmu': 'TMU',
    'ryerson': 'TMU',  
    'downtown toronto': 'TMU',  
}

def normalize_station_name(location: str, use_gtfs: bool = False) -> str:
    """
    Normalize a location string to match official station names.
    
    Args:
        location: Raw location string from delay data
        use_gtfs: If True, try to match against GTFS stops first
        
    Returns:
        Official station name if match found, otherwise original normalized string
    """
    if not location:
        return ""
    
    try:
        import pandas as pd
        if pd.isna(location):
            return ""
    except:
        pass
    
    import re
    from pathlib import Path
    
    # Try GTFS matching first if requested
    if use_gtfs:
        try:
            gtfs_dir = Path(__file__).parent.parent / "data" / "gtfs"
            stops_file = gtfs_dir / "stops.txt"
            if stops_file.exists():
                stops_df = pd.read_csv(stops_file)
                loc_lower = str(location).strip().lower()
                
                # Try exact match first
                for _, stop in stops_df.iterrows():
                    stop_name = str(stop['stop_name']).strip()
                    if loc_lower == stop_name.lower():
                        # Normalize the GTFS name
                        normalized = normalize_station_name(stop_name, use_gtfs=False)
                        if normalized in ALL_STATIONS:
                            return normalized
                
                # Try partial match
                for _, stop in stops_df.iterrows():
                    stop_name = str(stop['stop_name']).strip()
                    stop_lower = stop_name.lower()
                    if loc_lower in stop_lower or stop_lower in loc_lower:
                        normalized = normalize_station_name(stop_name, use_gtfs=False)
                        if normalized in ALL_STATIONS:
                            return normalized
        except Exception:
            pass 
    
    # Convert to lowercase for matching
    loc_lower = str(location).strip().lower()
    
    # Remove common suffixes
    loc_lower = re.sub(r'\s*\(.*?\)', '', loc_lower)  # Remove parentheses
    loc_lower = re.sub(r'\s*-\s*.*', '', loc_lower)  # Remove everything after dash
    loc_lower = re.sub(r'\s+station.*', '', loc_lower)  # Remove "station" suffix
    loc_lower = re.sub(r'\s+stn.*', '', loc_lower)  # Remove "stn" suffix
    loc_lower = re.sub(r'\s+approaching.*', '', loc_lower)
    loc_lower = re.sub(r'\s+exiting.*', '', loc_lower)
    loc_lower = loc_lower.strip()
    
    # Check variations first
    if loc_lower in STATION_VARIATIONS:
        return STATION_VARIATIONS[loc_lower]
    
    # Try direct match (case-insensitive)
    for station in ALL_STATIONS:
        if station.lower() == loc_lower:
            return station
    
    # Try partial match
    for station in ALL_STATIONS:
        station_lower = station.lower()
        # Check if location contains station name or vice versa
        if station_lower in loc_lower or loc_lower in station_lower:
            return station
    
    # Return original if no match
    return location.strip()

def get_station_line(station_name: str) -> str:
    """Get the line(s) for a station."""
    lines = []
    for line, stations in SUBWAY_STATIONS.items():
        if station_name in stations:
            lines.append(line)
    return ', '.join(lines) if lines else 'Unknown'

def is_valid_subway_station(location: str) -> bool:
    """Check if a location matches an official subway station."""
    normalized = normalize_station_name(location)
    return normalized in ALL_STATIONS