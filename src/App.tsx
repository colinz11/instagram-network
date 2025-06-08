import React, { useEffect, useState } from 'react';
import NetworkGraph from './components/NetworkGraph';
import './App.css';

interface UserData {
  followers_count: number;
  following_count: number;
  is_celebrity: boolean;
  followers: string[];
  following: string[];
}

interface NetworkData {
  [username: string]: UserData;
}

function App() {
  const [networkData, setNetworkData] = useState<NetworkData | null>(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);

  useEffect(() => {
    console.log('Fetching network data...');
    fetch('/user_data.json')
      .then(response => {
        console.log('Response received:', response.status);
        if (!response.ok) {
          throw new Error('Failed to load network data');
        }
        return response.json();
      })
      .then(data => {
        console.log('Data loaded successfully:', Object.keys(data).length, 'users');
        setNetworkData(data);
        setLoading(false);
      })
      .catch(err => {
        console.error('Error loading data:', err);
        setError(err.message);
        setLoading(false);
      });
  }, []);

  if (loading) {
    return <div className="loading">Loading network data...</div>;
  }

  if (error) {
    return <div className="error">Error: {error}</div>;
  }

  if (!networkData) {
    return <div className="error">No network data available</div>;
  }

  return (
    <div className="App">
      <header className="App-header">
        <h1>Instagram Network Visualization</h1>
      </header>
      <main>
        <NetworkGraph data={networkData} />
      </main>
    </div>
  );
}

export default App; 