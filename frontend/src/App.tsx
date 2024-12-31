import React, { useState } from 'react';
import { Upload } from 'lucide-react';

const App = () => {
  const [useNewEndpoint, setUseNewEndpoint] = useState(true);
  const [file, setFile] = useState<File | null>(null);
  const [loading, setLoading] = useState(false);
  const [results, setResults] = useState<any>(null);

  const handleFileChange = (event: React.ChangeEvent<HTMLInputElement>) => {
    const selectedFile = event.target.files?.[0];
    if (selectedFile && selectedFile.type === 'text/csv') {
      setFile(selectedFile);
    }
  };

  const handleSubmit = async (event: React.FormEvent<HTMLFormElement>) => {
    event.preventDefault();
    setLoading(true);

    const formData = new FormData(event.currentTarget);
    if (file) {
      formData.append('file', file);
    }

    try {
      const endpoint = useNewEndpoint ? 'analyze-dynamic' : 'analyze';
      const response = await fetch(`http://localhost:8000/${endpoint}`, {
        method: 'POST',
        body: formData
      });
      const data = await response.json();
      
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

          <div>
            <label className="block text-sm font-medium mb-2">Target Metrics</label>
            <input
              type="text"
              name="target_metrics"
              className="w-full p-3 border rounded-lg"
              placeholder="e.g., daily_active_users,feature_usage_rate"
              required
            />
          </div>

          <div>
            <label className="block text-sm font-medium mb-2">Revenue Drivers</label>
            <input
              type="text"
              name="revenue_drivers"
              className="w-full p-3 border rounded-lg"
              placeholder="e.g., user_adoption,upgrade_rate"
              required
            />
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
        {results && (
          <div className="mt-8 space-y-4">
            <h2 className="text-xl font-bold">Analysis Results</h2>
            {results.recommendations.map((rec: any, index: number) => (
              <div key={index} className="border rounded-lg p-4">
                <p className="font-medium">{rec.recommendation}</p>
                <p className="text-sm text-gray-600 mt-1">Revenue Impact: {rec.revenue_impact}</p>
                <div className="mt-2 flex items-center">
                  <div className="flex-grow bg-gray-200 rounded-full h-2">
                    <div
                      className="bg-blue-600 h-2 rounded-full"
                      style={{ width: `${rec.confidence * 100}%` }}
                    />
                  </div>
                  <span className="ml-2 text-sm text-gray-600">
                    {(rec.confidence * 100).toFixed(0)}% confidence
                  </span>
                </div>
              </div>
            ))}
          </div>
        )}
      </div>
    </div>
  );
};

export default App;