import { useState } from 'react';
import { PredictionForm } from './components/PredictionForm';
import { PredictionResult } from './components/PredictionResult';
import { ConnectionStatus } from './components/ConnectionStatus';
import { predictDelay } from './api/client';
import type { PredictionRequest, PredictionResponse } from './api/client';
import './App.css';

function App() {
  const [result, setResult] = useState<PredictionResponse | null>(null);
  const [error, setError] = useState<string | null>(null);
  const [isLoading, setIsLoading] = useState(false);

  const handlePredict = async (request: PredictionRequest) => {
    setIsLoading(true);
    setError(null);
    setResult(null);

    try {
      const prediction = await predictDelay(request);
      setResult(prediction);
    } catch (err) {
      setError(err instanceof Error ? err.message : 'Failed to get prediction');
    } finally {
      setIsLoading(false);
    }
  };

  return (
    <div className="app">
      <header className="app-header">
        <h1>🚇 TTC Delay Risk Predictor</h1>
        <p>Predict transit delays based on route, location, and time</p>
        <ConnectionStatus />
      </header>

      <main className="app-main">
        <div className="content-container">
          <PredictionForm onSubmit={handlePredict} isLoading={isLoading} />
          <PredictionResult result={result} error={error} />
        </div>
      </main>

      <footer className="app-footer">
        <p>Powered by Machine Learning • TTC Delay Data 2014-2025</p>
      </footer>
    </div>
  );
}

export default App;

