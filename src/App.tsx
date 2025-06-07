import React, { useState, useEffect } from 'react';
import { NetworkGraph } from './components/NetworkGraph/NetworkGraph';
import { GraphData, Link } from './types/graph';

function App() {
  const [graphData, setGraphData] = useState<GraphData>({ nodes: [], links: [] });
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);

  useEffect(() => {
    const loadData = async () => {
      try {
        // Load the relationships.csv file
        const response = await fetch('/relationships.csv');
        const text = await response.text();
        
        // Parse CSV
        const rows = text.split('\n').slice(1); // Skip header
        const relationships = rows
          .filter(row => row.trim()) // Skip empty rows
          .map(row => {
            const [source, target, relationship] = row.split(',');
            return { 
              source, 
              target, 
              relationship: relationship.trim() as 'follower' | 'following'
            } as Link;
          });

        // Create nodes set to avoid duplicates
        const nodesSet = new Set<string>();
        relationships.forEach(rel => {
          nodesSet.add(rel.source);
          nodesSet.add(rel.target);
        });

        // Convert to graph data format
        const graphData: GraphData = {
          nodes: Array.from(nodesSet).map(username => ({
            id: username,
            username
          })),
          links: relationships
        };

        setGraphData(graphData);
        setLoading(false);
      } catch (err) {
        setError('Failed to load network data. Please make sure you have run the scraper first.');
        setLoading(false);
      }
    };

    loadData();
  }, []);

  if (loading) {
    return <div className="flex h-screen items-center justify-center">Loading...</div>;
  }

  if (error) {
    return (
      <div className="flex h-screen items-center justify-center text-red-500">
        {error}
      </div>
    );
  }

  return (
    <div className="min-h-screen bg-gray-100 p-4">
      <div className="mx-auto max-w-7xl">
        <h1 className="mb-8 text-3xl font-bold text-gray-900">Instagram Network Visualization</h1>
        <div className="rounded-lg bg-white p-4 shadow-lg">
          <NetworkGraph
            data={graphData}
            width={1200}
            height={800}
          />
        </div>
      </div>
    </div>
  );
}

export default App; 