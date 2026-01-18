import axios from 'axios';

const API_BASE_URL = import.meta.env.VITE_API_URL || 'http://localhost:8000';

export interface PredictionRequest {
  route: string;
  location: string;
  hour: number;
  day_of_week: number;
  month?: number;
  minute?: number;
  direction?: string;
  incident?: string;
  mode?: 'bus' | 'streetcar' | 'subway';
}

export interface PredictionResponse {
  predicted_delay_minutes: number;
  risk_level: string;
  risk_color: string;
  model_name: string;
}

const api = axios.create({
  baseURL: API_BASE_URL,
  headers: {
    'Content-Type': 'application/json',
  },
  timeout: 10000, // 10 second timeout
});

// Add error interceptor for better error messages
api.interceptors.response.use(
  (response) => response,
  (error) => {
    if (error.code === 'ECONNREFUSED' || error.message.includes('Network Error')) {
      error.message = 'Cannot connect to API. Make sure the backend is running on http://localhost:8000';
    }
    return Promise.reject(error);
  }
);

export const predictDelay = async (request: PredictionRequest): Promise<PredictionResponse> => {
  const response = await api.post<PredictionResponse>('/predict', request);
  return response.data;
};

export const healthCheck = async (): Promise<{ status: string; model_loaded: boolean }> => {
  const response = await api.get('/health');
  return response.data;
};

export const getRoutes = async (mode?: string): Promise<string[]> => {
  const params = mode ? { mode } : {};
  const response = await api.get<{ routes: string[] }>('/data/routes', { params });
  return response.data.routes;
};

export const getLocations = async (search?: string, mode?: string, route?: string, limit?: number): Promise<string[]> => {
  const params: Record<string, string | number> = {};
  if (search) params.search = search;
  if (mode) params.mode = mode;
  if (route) params.route = route;
  if (limit) params.limit = limit;
  const response = await api.get<{ locations: string[] }>('/data/locations', { params });
  return response.data.locations;
};

