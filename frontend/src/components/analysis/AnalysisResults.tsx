import React from 'react';
import { RecommendationCard } from './RecommendationCard';
import { MetricsDisplay } from './MetricsDisplay';
//@ts-ignore
import html2pdf from 'html2pdf.js';

interface AnalysisResultsProps {
  results: {
    recommendations: any[];
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
      
      {/* Recommendations */}
      <div className="space-y-4">
        {results.recommendations.map((rec, index) => (
          <div key={index} className={index > 0 ? 'recommendation-break' : ''}>
            <RecommendationCard recommendation={rec} />
          </div>
        ))}
      </div>

      {/* Metrics */}
      {results.metrics && Object.keys(results.metrics).length > 0 && (
        <MetricsDisplay metrics={results.metrics} />
      )}
    </div>
  );
};