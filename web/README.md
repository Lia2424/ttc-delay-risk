# TTC Delay Risk Predictor - Web Frontend

React + TypeScript frontend for the TTC Delay Risk Prediction API.

## Features

- 🎯 Interactive prediction form
- 📊 Real-time delay predictions
- 🎨 Visual risk indicators (color-coded)
- 📈 Model information display
- 📱 Responsive design

## Getting Started

### Prerequisites

- Node.js and npm installed
- FastAPI backend running on `http://localhost:8000`

### Installation

```bash
cd web
npm install
```

### Development

Start the development server:

```bash
npm run dev
```

The app will be available at `http://localhost:3000`

### Build for Production

```bash
npm run build
```

The built files will be in the `dist/` directory.

## Project Structure

```
web/
├── src/
│   ├── api/
│   │   └── client.ts          # API client for backend communication
│   ├── components/
│   │   ├── PredictionForm.tsx # Form for inputting prediction parameters
│   │   ├── PredictionResult.tsx # Display prediction results
│   │   └── ModelInfo.tsx      # Display model information
│   ├── App.tsx                # Main application component
│   ├── App.css                # Application styles
│   ├── main.tsx               # Application entry point
│   └── style.css              # Base styles
├── index.html                 # HTML template
├── vite.config.ts            # Vite configuration
└── package.json              # Dependencies
```

## API Configuration

The frontend connects to the FastAPI backend. By default, it expects the API at `http://localhost:8000`.

To change the API URL, create a `.env` file:

```env
VITE_API_URL=http://your-api-url:8000
```

## Usage

1. Fill in the prediction form:
   - Route (e.g., "102", "1")
   - Location/Station name
   - Mode (bus, streetcar, subway)
   - Time (hour, minute)
   - Day of week
   - Optional: Month, direction, incident type

2. Click "Predict Delay Risk"

3. View the results:
   - Predicted delay in minutes
   - Risk level (Low, Medium, High, Very High)
   - Color-coded indicators
   - Model information

## Technologies

- **React** - UI framework
- **TypeScript** - Type safety
- **Vite** - Build tool and dev server
- **Axios** - HTTP client
- **Recharts** - Charting library (available for future use)

