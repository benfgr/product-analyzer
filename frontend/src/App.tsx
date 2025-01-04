import React, { useState } from 'react';
import { Upload } from 'lucide-react';
import { AnalysisResults } from './components/analysis/AnalysisResults';
import { LoadingSpinner } from './components/ui/LoadingSpinner';
import { ErrorDisplay } from './components/ui/ErrorDisplay';

// Predefined business goals to help users
const BUSINESS_GOAL_EXAMPLES = [
  "Recommend ways to increase total revenue by optimizing feature combinations",
  "Identify low-performing features that can be deprecated with minimal revenue impact",
  "Find the highest-impact opportunities to increase user engagement",
  "Optimize content strategy to maximize conversion rates",
  "Determine which user segments offer the highest growth potential"
];

const App = () => {
  const [useNewEndpoint, setUseNewEndpoint] = useState(true);
  const [file, setFile] = useState<File | null>(null);
  const [loading, setLoading] = useState(false);
  const [results, setResults] = useState<any>(null);
  const [error, setError] = useState<string | null>(null);
  const [showGoalExamples, setShowGoalExamples] = useState(false);

  const handleFileChange = (event: React.ChangeEvent<HTMLInputElement>) => {
    const selectedFile = event.target.files?.[0];
    if (selectedFile && selectedFile.type === 'text/csv') {
      setFile(selectedFile);
    }
  };

  const handleGoalExample = (goal: string) => {
    const textarea = document.querySelector('textarea[name="business_goal"]') as HTMLTextAreaElement;
    if (textarea) {
      textarea.value = goal;
      setShowGoalExamples(false);
    }
  };

  const handleSubmit = async (event: React.FormEvent<HTMLFormElement>) => {
    event.preventDefault();
    setLoading(true);
    setError(null);

    const formData = new FormData(event.currentTarget);
    if (file) {
      formData.append('file', file);
    }

    const API_URL = import.meta.env.PROD 
    ? import.meta.env.VITE_PROD_API_URL 
    : import.meta.env.VITE_DEV_API_URL;

    try {
      const endpoint = useNewEndpoint ? 'analyze-dynamic' : 'analyze';
      // const response = await fetch(`https://product-analyzer-ctwo.onrender.com/${endpoint}`, { 
      const response = await fetch(`${API_URL}/${endpoint}`, {
        method: 'POST',
        body: formData
      });

      console.log('Response status:', response.status);

      if (!response.ok) {
        const errorText = await response.text();
        console.log('Error response:', errorText);
        throw new Error(`Analysis failed: ${response.statusText}`);
      }

      const data = await response.json();

      if (!data.success) {
        throw new Error(data.error || 'Analysis failed');
      }
      
      if (useNewEndpoint) {
        // Handle dynamic analysis response
        console.log("Dynamic analysis response:", data);
        setResults({
          recommendations: data.data.recommendations,
          metrics: data.data.analysis
        });
      } else {
        // Handle original endpoint response
        setResults(data.data);
      }
    } catch (error) {
      console.error('Error:', error);
      setError(error instanceof Error ? error.message : 'An unexpected error occurred');
    } finally {
      setLoading(false);
    }
};

  return (
    <div className="min-h-screen bg-gray-100 p-8">
      <div className="max-w-2xl mx-auto bg-white rounded-lg shadow p-6">
        
        <form onSubmit={handleSubmit} className="space-y-6">
        
          <h1 className="text-3xl font-bold mb-6">Product Analytics Advisor</h1>

          <div className="flex items-center gap-2">
          <input
              type="checkbox"
              checked={useNewEndpoint}
              onChange={(e) => setUseNewEndpoint(e.target.checked)}
              className="form-checkbox h-5 w-5 text-blue-600"
            />
            <span className="text-sm">Use Dynamic Analysis</span>
          </div>
        
          <div>
            <label className="block text-sm font-medium mb-2">Value Proposition</label>
            <textarea
              name="value_proposition"
              className="w-full p-3 border rounded-lg"
              rows={3}
              placeholder="e.g., Reduce development time by 40%"
              required
            />
          </div>

          <div>
            <label className="block text-sm font-medium mb-2">Business Model</label>
            <textarea
              name="business_model"
              className="w-full p-3 border rounded-lg"
              rows={3}
              placeholder="e.g., SaaS subscription with usage-based pricing"
              required
            />
          </div>

          <div className="relative">
            <label className="block text-sm font-medium mb-2">Analysis Business Goal</label>
            <textarea
              name="business_goal"
              className="w-full p-3 border rounded-lg"
              rows={3}
              placeholder="What specific business outcome are you trying to achieve?"
              required
            />
            <button
              type="button"
              onClick={() => setShowGoalExamples(!showGoalExamples)}
              className="text-sm text-blue-600 hover:text-blue-800 mt-1"
            >
              {showGoalExamples ? 'Hide examples' : 'See examples'}
            </button>
            
            {showGoalExamples && (
              <div className="absolute z-10 mt-1 w-full bg-white border rounded-lg shadow-lg p-4">
                <h4 className="font-medium mb-2">Example Business Goals:</h4>
                <ul className="space-y-2">
                  {BUSINESS_GOAL_EXAMPLES.map((goal, index) => (
                    <li 
                      key={index}
                      onClick={() => handleGoalExample(goal)}
                      className="cursor-pointer hover:bg-gray-100 p-2 rounded text-sm"
                    >
                      {goal}
                    </li>
                  ))}
                </ul>
              </div>
            )}
          </div>

          <div>
            <label className="block text-sm font-medium mb-2">CSV File</label>
            <div className="border-2 border-dashed rounded-lg p-6">
              <input
                type="file"
                onChange={handleFileChange}
                accept=".csv"
                className="hidden"
                id="file-upload"
                required
              />
              <label 
                htmlFor="file-upload" 
                className="cursor-pointer flex flex-col items-center space-y-2"
              >
                <Upload className="h-8 w-8 text-gray-400" />
                <span className="text-sm text-gray-600">
                  {file ? file.name : 'Click to upload or drag and drop CSV file'}
                </span>
              </label>
            </div>
          </div>

          <button
            type="submit"
            disabled={loading || !file}
            className="w-full bg-blue-600 text-white p-3 rounded-lg hover:bg-blue-700 disabled:opacity-50"
          >
            {loading ? 'Analyzing...' : 'Analyze Data'}
          </button>
        </form>

      {/* Results Section */}
      {loading && <LoadingSpinner />}
      {error && <ErrorDisplay message={error} onRetry={() => setError(null)} />}
      {results && !loading && !error && <AnalysisResults results={results} />}
      </div>
    </div>
  );
};

export default App;