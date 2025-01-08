import React from 'react';
import { RecommendationCard } from './RecommendationCard';
import { MetricsDisplay } from './MetricsDisplay';
//@ts-ignore
import html2pdf from 'html2pdf.js';

interface AnalysisResultsProps {
  results: {
    recommendations?: any[];
    answers?: Answer[];
    metrics: Record<string, any>;
  };
}

interface SupportingData {
  key_metrics?: string[];
  patterns?: string[];
  statistical_evidence?: string;
}

interface Answer {
  question: string;
  answer: string;
  confidence?: number;
  supporting_data?: string | SupportingData;
}

interface AnalysisResultsProps {
  results: {
    recommendations?: any[];  // Keep existing recommendation type
    answers?: Answer[];
    metrics: Record<string, any>;
  };
}

export const AnalysisResults: React.FC<AnalysisResultsProps> = ({ results }) => {
  const handleExport = () => {
    const button = document.querySelector('.export-button') as HTMLElement;
    if (button) button.style.display = 'none';

    const element = document.getElementById('analysis-results');
    const opt = {
      margin: 1,
      filename: 'analysis-results.pdf',
      pagebreak: { mode: ['avoid-all', 'css', 'legacy'], before: '.recommendation-break'},
      image: { type: 'jpeg', quality: 0.98 },
      html2canvas: { scale: 2 },
      jsPDF: { unit: 'in', format: 'letter', orientation: 'portrait' }
    };

    html2pdf().set(opt).from(element).save().then(() => {
      if (button) button.style.display = 'block';
    });
  };

  return (
    <div id="analysis-results" className="mt-8 space-y-6">
      <div className="flex justify-between items-center mb-4">
        <h2 className="text-xl font-bold">Analysis Results</h2>
        <button
          onClick={handleExport}
          className="px-4 py-2 bg-blue-600 text-white rounded hover:bg-blue-700 export-button"
        >
          Export to PDF
        </button>
      </div>
      
      {/* Answers or Recommendations */}
      <div className="space-y-4">
        {results.answers ? (
          // Render Answers
          results.answers.map((answer, index) => (
            <div key={index} className="border rounded-lg p-6 bg-white shadow-sm">
              <h3 className="font-bold text-lg text-blue-800 mb-2">Q: {answer.question}</h3>
              <p className="text-gray-700 mb-4">{answer.answer}</p>
              {answer.confidence && (
                <div className="flex items-center mt-2">
                  <div className="flex-grow bg-gray-200 rounded-full h-2">
                    <div
                      className="bg-blue-600 h-2 rounded-full"
                      style={{ width: `${answer.confidence * 100}%` }}
                    />
                  </div>
                  <span className="ml-2 text-sm text-gray-600">
                    {(answer.confidence * 100).toFixed(0)}% confidence
                  </span>
                </div>
              )}
              {answer.supporting_data && (
                <div className="mt-4 bg-gray-50 p-3 rounded">
                  <h4 className="font-semibold text-sm text-gray-700 mb-1">Supporting Data</h4>
                  {typeof answer.supporting_data === 'string' ? (
                    <p className="text-sm text-gray-600">{answer.supporting_data}</p>
                  ) : (
                    <div className="space-y-2">
                      {answer.supporting_data.key_metrics && (
                        <div>
                          <p className="text-sm font-medium text-gray-700">Key Metrics:</p>
                          <p className="text-sm text-gray-600">
                            {Array.isArray(answer.supporting_data.key_metrics) 
                              ? answer.supporting_data.key_metrics.join(', ') 
                              : answer.supporting_data.key_metrics}
                          </p>
                        </div>
                      )}
                      {answer.supporting_data.patterns && (
                        <div>
                          <p className="text-sm font-medium text-gray-700">Patterns:</p>
                          <p className="text-sm text-gray-600">
                            {Array.isArray(answer.supporting_data.patterns) 
                              ? answer.supporting_data.patterns.join(', ') 
                              : answer.supporting_data.patterns}
                          </p>
                        </div>
                      )}
                      {answer.supporting_data.statistical_evidence && (
                        <div>
                          <p className="text-sm font-medium text-gray-700">Statistical Evidence:</p>
                          <p className="text-sm text-gray-600">{answer.supporting_data.statistical_evidence}</p>
                        </div>
                      )}
                    </div>
                  )}
                </div>
              )}
            </div>
          ))
        ) : (
          // Render Recommendations
          results.recommendations?.map((rec, index) => (
            <div key={index} className={index > 0 ? 'recommendation-break' : ''}>
              <RecommendationCard recommendation={rec} />
            </div>
          ))
        )}
      </div>

      {/* Metrics */}
      {results.metrics && Object.keys(results.metrics).length > 0 && (
        <MetricsDisplay metrics={results.metrics} />
      )}
    </div>
  );
};