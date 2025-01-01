// src/components/analysis/MetricsDisplay.tsx
import React from 'react';

interface MetricsDisplayProps {
  metrics: Record<string, any>;
}

export const MetricsDisplay: React.FC<MetricsDisplayProps> = ({ metrics }) => {
  return (
    <div className="mt-8">
      <h3 className="text-lg font-bold mb-4">Key Metrics</h3>
      <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
        {Object.entries(metrics).map(([key, value]) => (
          <div key={key} className="bg-white p-4 rounded-lg border">
            <h4 className="font-medium text-gray-700">{key.replace(/_/g, ' ').toUpperCase()}</h4>
            <pre className="text-sm overflow-x-auto whitespace-pre-wrap">
              {JSON.stringify(value, null, 2)}
            </pre>
          </div>
        ))}
      </div>
    </div>
  );
};
