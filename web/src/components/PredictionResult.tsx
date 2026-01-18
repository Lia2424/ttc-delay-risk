import type { PredictionResponse } from '../api/client';

interface PredictionResultProps {
  result: PredictionResponse | null;
  error: string | null;
}

export function PredictionResult({ result, error }: PredictionResultProps) {
  if (error) {
    return (
      <div className="prediction-result error">
        <h3>Error</h3>
        <p>{error}</p>
      </div>
    );
  }

  if (!result) {
    return null;
  }

  const getRiskClass = (level: string) => {
    return level.toLowerCase().replace(' ', '-');
  };

  return (
    <div className={`prediction-result ${getRiskClass(result.risk_level)}`}>
      <h3>Prediction Result</h3>
      
      <div className="result-main">
        <div className="delay-display">
          <span className="delay-value">{result.predicted_delay_minutes.toFixed(1)}</span>
          <span className="delay-unit">minutes</span>
        </div>
        
        <div className="risk-indicator">
          <span className="risk-emoji">{result.risk_color}</span>
          <span className="risk-level">{result.risk_level} Risk</span>
        </div>
      </div>

      <div className="result-details">
        <p><strong>Model:</strong> {result.model_name}</p>
      </div>

      <div className="risk-explanation">
        {result.risk_level === 'Low' && (
          <p>🟢 Low risk - Minimal delay expected. Good time to travel!</p>
        )}
        {result.risk_level === 'Medium' && (
          <p>🟡 Medium risk - Some delay possible. Plan for extra time.</p>
        )}
        {result.risk_level === 'High' && (
          <p>🟠 High risk - Significant delays likely. Consider alternative routes or times.</p>
        )}
        {result.risk_level === 'Very High' && (
          <p>🔴 Very high risk - Major delays expected. Strongly consider alternatives.</p>
        )}
      </div>
    </div>
  );
}

