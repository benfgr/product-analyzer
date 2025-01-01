// src/components/ui/ErrorDisplay.tsx
import React from 'react';

interface ErrorDisplayProps {
  message: string;
  onRetry?: () => void;
}

export const ErrorDisplay: React.FC<ErrorDisplayProps> = ({ message, onRetry }) => (
  <div className="bg-red-50 border border-red-200 rounded-lg p-4 mt-4">
    <p className="text-red-800">{message}</p>
    {onRetry && (
      <button
        onClick={onRetry}
        className="mt-2 text-sm text-red-600 hover:text-red-800"
      >
        Try Again
      </button>
    )}
  </div>
);