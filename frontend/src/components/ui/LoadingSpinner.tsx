// src/components/ui/LoadingSpinner.tsx
import React from 'react';

export const LoadingSpinner: React.FC = () => (
  <div className="flex justify-center items-center py-8">
    <div className="animate-spin rounded-full h-8 w-8 border-b-2 border-blue-600"></div>
  </div>
);