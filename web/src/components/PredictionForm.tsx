import { useState, useEffect } from 'react';
import type { PredictionRequest } from '../api/client';
import { getRoutes, getLocations } from '../api/client';

interface PredictionFormProps {
  onSubmit: (request: PredictionRequest) => void;
  isLoading: boolean;
}

export function PredictionForm({ onSubmit, isLoading }: PredictionFormProps) {
  const [formData, setFormData] = useState<PredictionRequest>({
    route: '',
    location: '',
    hour: new Date().getHours(),
    day_of_week: new Date().getDay() === 0 ? 6 : new Date().getDay() - 1, // Convert to 0-6 (Mon-Sun)
    mode: 'subway',
    minute: 0,
    direction: 'Unknown',
    incident: 'Unknown',
  });

  const [routes, setRoutes] = useState<string[]>([]);
  const [locations, setLocations] = useState<string[]>([]);
  const [locationSearch, setLocationSearch] = useState('');
  const [filteredLocations, setFilteredLocations] = useState<string[]>([]);
  const [loadingRoutes, setLoadingRoutes] = useState(false);
  const [loadingLocations, setLoadingLocations] = useState(false);

  // Load routes when mode changes
  useEffect(() => {
    const loadRoutes = async () => {
      setLoadingRoutes(true);
      try {
        const routeList = await getRoutes(formData.mode);
        setRoutes(routeList);
        // Reset route selection if current route not in new list
        if (formData.route && !routeList.includes(formData.route)) {
          setFormData((prev) => ({ ...prev, route: '' }));
        }
      } catch (err) {
        console.error('Failed to load routes:', err);
      } finally {
        setLoadingRoutes(false);
      }
    };
    loadRoutes();
  }, [formData.mode]);

  // Load locations on mount and when search, mode, or route changes
  useEffect(() => {
    const loadLocations = async () => {
      setLoadingLocations(true);
      try {
        const locationList = await getLocations(
          locationSearch || undefined, 
          formData.mode, 
          formData.route || undefined,  // Filter by selected route
          200
        );
        setLocations(locationList);
        setFilteredLocations(locationList.slice(0, 50)); // Show first 50
      } catch (err) {
        console.error('Failed to load locations:', err);
      } finally {
        setLoadingLocations(false);
      }
    };
    
    const debounceTimer = setTimeout(loadLocations, 300);
    return () => clearTimeout(debounceTimer);
  }, [locationSearch, formData.mode, formData.route]);

  // Filter locations based on search
  useEffect(() => {
    if (!locationSearch) {
      // Show common stations first when no search
      const commonStations = locations
        .filter(loc => loc.toUpperCase().includes('STATION') || loc.toUpperCase().includes('STN'))
        .slice(0, 30);
      const others = locations
        .filter(loc => !loc.toUpperCase().includes('STATION') && !loc.toUpperCase().includes('STN'))
        .slice(0, 20);
      setFilteredLocations([...commonStations, ...others]);
    } else {
      const searchLower = locationSearch.toLowerCase();
      // Filter out weird entries and prioritize matches
      const filtered = locations
        .filter(loc => {
          const locLower = loc.toLowerCase();
          // Filter out entries that look like errors
          if (locLower.startsWith('#') || locLower.startsWith('$') || 
              locLower.includes('(none') || locLower.includes('(approaching)')) {
            return false;
          }
          return locLower.includes(searchLower);
        })
        .sort((a, b) => {
          // Prioritize exact matches and station names
          const aLower = a.toLowerCase();
          const bLower = b.toLowerCase();
          const aStarts = aLower.startsWith(searchLower);
          const bStarts = bLower.startsWith(searchLower);
          if (aStarts && !bStarts) return -1;
          if (!aStarts && bStarts) return 1;
          if (aLower.includes('station') && !bLower.includes('station')) return -1;
          if (!aLower.includes('station') && bLower.includes('station')) return 1;
          return a.localeCompare(b);
        })
        .slice(0, 50);
      setFilteredLocations(filtered);
    }
  }, [locationSearch, locations]);

  const handleSubmit = (e: React.FormEvent) => {
    e.preventDefault();
    onSubmit(formData);
  };

  const handleChange = (field: keyof PredictionRequest, value: string | number) => {
    setFormData((prev) => ({ ...prev, [field]: value }));
  };

  return (
    <form onSubmit={handleSubmit} className="prediction-form">
      <h2>Predict Delay Risk</h2>
      
      <div className="form-row">
        <div className="form-group">
          <label htmlFor="mode">Mode *</label>
          <select
            id="mode"
            value="subway"
            disabled
            required
          >
            <option value="subway">Subway</option>
          </select>
          <small style={{display: 'block', marginTop: '0.25rem', color: '#666', fontSize: '0.75rem'}}>
            Only subway delays are supported
          </small>
        </div>

        <div className="form-group">
          <label htmlFor="route">Route *</label>
          <select
            id="route"
            value={formData.route}
            onChange={(e) => handleChange('route', e.target.value)}
            required
            disabled={loadingRoutes}
          >
            <option value="">Select a route...</option>
            {routes.map((route) => (
              <option key={route} value={route}>
                {route}
              </option>
            ))}
          </select>
          {loadingRoutes && <small className="loading-text">Loading routes...</small>}
        </div>
      </div>

      <div className="form-row">
        <div className="form-group form-group-full">
          <label htmlFor="location">Location/Station *</label>
          <div className="location-input-wrapper">
            <input
              id="location-search"
              type="text"
              value={locationSearch}
              onChange={(e) => {
                const value = e.target.value;
                setLocationSearch(value);
                // Auto-select if exact match
                const exactMatch = locations.find(loc => loc.toLowerCase() === value.toLowerCase());
                if (exactMatch) {
                  handleChange('location', exactMatch);
                } else if (!value) {
                  handleChange('location', '');
                }
              }}
              onBlur={(e) => {
                // Validate on blur - if not exact match, try to find closest
                const value = e.target.value;
                if (value && formData.location !== value) {
                  const exactMatch = locations.find(loc => loc.toLowerCase() === value.toLowerCase());
                  if (exactMatch) {
                    handleChange('location', exactMatch);
                    setLocationSearch(exactMatch);
                  }
                }
              }}
              onFocus={() => {
                if (!locationSearch && formData.location) {
                  setLocationSearch(formData.location);
                }
              }}
              placeholder="Type to search locations/stations..."
              className="location-search"
              list="location-options"
              autoComplete="off"
            />
            <datalist id="location-options">
              {filteredLocations.slice(0, 30).map((location) => (
                <option key={location} value={location} />
              ))}
            </datalist>
            {/* Hidden select for form validation - keeps formData.location in sync */}
            <select
              id="location"
              value={formData.location}
              onChange={(e) => {
                handleChange('location', e.target.value);
                setLocationSearch(e.target.value);
              }}
              required
              style={{ position: 'absolute', opacity: 0, pointerEvents: 'none', height: 0 }}
              tabIndex={-1}
            >
              <option value="">Select a location...</option>
              {locations.map((location) => (
                <option key={location} value={location}>
                  {location}
                </option>
              ))}
            </select>
          </div>
          {loadingLocations && <small className="loading-text">Loading locations...</small>}
          {filteredLocations.length === 0 && locationSearch && !loadingLocations && (
            <small className="error-text">No locations found. Try a different search term.</small>
          )}
          {formData.location && (
            <small className="success-text">Selected: {formData.location}</small>
          )}
        </div>
      </div>

      <div className="form-row">
        <div className="form-group">
          <label htmlFor="hour">Hour *</label>
          <input
            id="hour"
            type="number"
            min="0"
            max="23"
            value={formData.hour}
            onChange={(e) => handleChange('hour', parseInt(e.target.value))}
            required
          />
        </div>

        <div className="form-group">
          <label htmlFor="minute">Minute</label>
          <input
            id="minute"
            type="number"
            min="0"
            max="59"
            value={formData.minute || 0}
            onChange={(e) => handleChange('minute', parseInt(e.target.value))}
          />
        </div>

        <div className="form-group">
          <label htmlFor="day_of_week">Day of Week *</label>
          <select
            id="day_of_week"
            value={formData.day_of_week}
            onChange={(e) => handleChange('day_of_week', parseInt(e.target.value))}
            required
          >
            <option value="0">Monday</option>
            <option value="1">Tuesday</option>
            <option value="2">Wednesday</option>
            <option value="3">Thursday</option>
            <option value="4">Friday</option>
            <option value="5">Saturday</option>
            <option value="6">Sunday</option>
          </select>
        </div>
      </div>

      <div className="form-row">
        <div className="form-group">
          <label htmlFor="month">Month</label>
          <select
            id="month"
            value={formData.month || ''}
            onChange={(e) => {
              const value = e.target.value ? parseInt(e.target.value) : undefined;
              if (value !== undefined) {
                handleChange('month', value);
              } else {
                setFormData((prev) => {
                  const { month, ...rest } = prev;
                  return rest as PredictionRequest;
                });
              }
            }}
          >
            <option value="">Current Month</option>
            <option value="1">January</option>
            <option value="2">February</option>
            <option value="3">March</option>
            <option value="4">April</option>
            <option value="5">May</option>
            <option value="6">June</option>
            <option value="7">July</option>
            <option value="8">August</option>
            <option value="9">September</option>
            <option value="10">October</option>
            <option value="11">November</option>
            <option value="12">December</option>
          </select>
        </div>
      </div>

      <button type="submit" disabled={isLoading || !formData.route || !formData.location} className="submit-button">
        {isLoading ? 'Predicting...' : 'Predict Delay Risk'}
      </button>
    </form>
  );
}
