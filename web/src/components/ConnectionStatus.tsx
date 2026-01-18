import { useEffect, useState } from 'react';
import { healthCheck } from '../api/client';

export function ConnectionStatus() {
  const [status, setStatus] = useState<'checking' | 'connected' | 'disconnected'>('checking');
  const [error, setError] = useState<string | null>(null);

  useEffect(() => {
    const checkConnection = async () => {
      try {
        await healthCheck();
        setStatus('connected');
        setError(null);
      } catch (err) {
        setStatus('disconnected');
        setError(err instanceof Error ? err.message : 'Connection failed');
      }
    };

    checkConnection();
    const interval = setInterval(checkConnection, 30000); // Check every 30 seconds

    return () => clearInterval(interval);
  }, []);

  if (status === 'checking') {
    return (
      <div className="connection-status checking">
        <span className="status-indicator">🟡</span>
        <span>Checking connection...</span>
      </div>
    );
  }

  if (status === 'disconnected') {
    return (
      <div className="connection-status disconnected">
        <span className="status-indicator">🔴</span>
        <div className="status-content">
          <strong>Backend not connected</strong>
          <p className="error-message">{error || 'Cannot reach API at http://localhost:8000'}</p>
          <p className="help-text">
            Start the backend with: <code>./api/start.sh</code> or <code>uvicorn api.main:app --reload</code>
          </p>
        </div>
      </div>
    );
  }

  return (
    <div className="connection-status connected">
      <span className="status-indicator">🟢</span>
      <span>Connected to API</span>
    </div>
  );
}

