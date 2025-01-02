// src/components/analysis/RecommendationCard.tsx
import React from 'react';

interface Recommendation {
  recommendation: string;
  confidence: number;
  revenue_impact: {
    primary_metric: string;
    revenue_projection: string;
    calculation: string;
  };
  supporting_data?: {
    key_metrics?: string[];
    relationships?: string[];
    statistical_evidence?: string;
    insight?: string;
  } | string;  // Union type to handle both old and new format
  implementation?: string[];
  timeframe?: string;
}

export const RecommendationCard: React.FC<{ recommendation: Recommendation }> = ({ recommendation }) => {
  return (
    <div className="border rounded-lg p-6 bg-white shadow-sm">
      {/* Recommendation Header */}
      <div className="mb-4">
        <h3 className="font-bold text-lg text-blue-800">{recommendation.recommendation}</h3>
        <div className="flex items-center mt-2">
          <div className="flex-grow bg-gray-200 rounded-full h-2">
            <div
              className="bg-blue-600 h-2 rounded-full"
              style={{ width: `${recommendation.confidence * 100}%` }}
            />
          </div>
          <span className="ml-2 text-sm text-gray-600">
            {(recommendation.confidence * 100).toFixed(0)}% confidence
          </span>
        </div>
      </div>

      {/* Supporting Data */}
      {recommendation.supporting_data && (
        <div className="mb-4 bg-gray-50 p-3 rounded">
          <h4 className="font-semibold text-sm text-gray-700 mb-1">Supporting Data</h4>
          {typeof recommendation.supporting_data === 'object' ? (
            <>
              {recommendation.supporting_data.insight && (
                <div className="mb-2">
                  <p className="text-sm font-medium text-gray-700">Insight:</p>
                  <p className="text-sm text-gray-600">{recommendation.supporting_data.insight}</p>

                </div>
              )}
              {recommendation.supporting_data.key_metrics && (
                <div className="mb-2">
                  <p className="text-sm font-medium text-gray-700">Key Metrics:</p>
                  <p className="text-sm text-gray-600">
                    {Array.isArray(recommendation.supporting_data.key_metrics) 
                      ? recommendation.supporting_data.key_metrics.join(', ')
                      : recommendation.supporting_data.key_metrics}
                  </p>
                </div>
              )}
              {recommendation.supporting_data.relationships && (
                <div className="mb-2">
                  <p className="text-sm font-medium text-gray-700">Relationships:</p>
                  <p className="text-sm text-gray-600">
                    {Array.isArray(recommendation.supporting_data.relationships)
                      ? recommendation.supporting_data.relationships.join(', ')
                      : recommendation.supporting_data.relationships}
                  </p>
                </div>
              )}
              {recommendation.supporting_data.statistical_evidence && (
                <div>
                  <p className="text-sm font-medium text-gray-700">Statistical Evidence:</p>
                  <p className="text-sm text-gray-600">{recommendation.supporting_data.statistical_evidence}</p>
                </div>
              )}
            </>
          ) : (
            <p className="text-sm text-gray-600">{recommendation.supporting_data}</p>
          )}
        </div>
      )}

      {/* Implementation Steps */}
      {recommendation.implementation && recommendation.implementation.length > 0 && (
        <div className="mb-4">
          <h4 className="font-semibold text-sm text-gray-700 mb-2">Implementation Steps</h4>
          <ol className="list-decimal list-inside space-y-1">
            {recommendation.implementation.map((step, stepIndex) => (
              <li key={stepIndex} className="text-sm text-gray-600">{step}</li>
            ))}
          </ol>
        </div>
      )}

      {/* Impact Section */}
      <div className="mt-4 grid grid-cols-1 md:grid-cols-2 gap-4">
        {recommendation.revenue_impact && (
          <div className="bg-blue-50 p-3 rounded">
            <h4 className="font-semibold text-sm text-gray-700 mb-1">Expected Impact</h4>
            <div className="space-y-1">
              <p className="text-sm text-blue-800">
                Primary Metric: {recommendation.revenue_impact.primary_metric}
              </p>
              <p className="text-sm text-blue-800">
                Revenue: {recommendation.revenue_impact.revenue_projection}
              </p>
              <p className="text-sm text-blue-800">
                <span className="font-medium">Calculation:</span> {recommendation.revenue_impact.calculation}
              </p>
            </div>
          </div>
        )}
        {recommendation.timeframe && (
          <div className="bg-green-50 p-3 rounded">
            <h4 className="font-semibold text-sm text-gray-700 mb-1">Timeframe</h4>
            <p className="text-sm text-green-800">{recommendation.timeframe}</p>
          </div>
        )}
      </div>
    </div>
  );
};