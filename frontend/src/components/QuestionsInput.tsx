import React, { useState } from 'react';
import { Plus, X } from 'lucide-react';

const QUESTION_EXAMPLES = [
  "What is driving the highest revenue growth?",
  "Which features have the lowest engagement rates?",
  "What patterns exist in user behavior across different segments?",
  "Where are the biggest opportunities for optimization?",
  "What are the key factors affecting conversion rates?"
];

interface QuestionsInputProps {
  onChange: (questions: string[]) => void;
}

const QuestionsInput: React.FC<QuestionsInputProps> = ({ onChange }) => {
  const [questions, setQuestions] = useState<string[]>(['']);
  const [showExamples, setShowExamples] = useState(false);

  const handleQuestionChange = (index: number, value: string) => {
    const newQuestions = [...questions];
    newQuestions[index] = value;
    setQuestions(newQuestions);
    onChange(newQuestions.filter(q => q.trim()));
  };

  const addQuestion = () => {
    setQuestions([...questions, '']);
  };

  const removeQuestion = (index: number) => {
    const newQuestions = questions.filter((_, i) => i !== index);
    setQuestions(newQuestions.length ? newQuestions : ['']);
    onChange(newQuestions.filter(q => q.trim()));
  };

  const handleExampleClick = (example: string) => {
    const emptyIndex = questions.findIndex(q => !q.trim());
    if (emptyIndex >= 0) {
      handleQuestionChange(emptyIndex, example);
    } else {
      setQuestions([...questions, example]);
      onChange([...questions.filter(q => q.trim()), example]);
    }
    setShowExamples(false);
  };

  return (
    <div className="space-y-4">
      <div className="flex justify-between items-center">
        <label className="block text-sm font-medium">Specific Questions (Optional)</label>
        <button
          type="button"
          onClick={() => setShowExamples(!showExamples)}
          className="text-sm text-blue-600 hover:text-blue-800"
        >
          {showExamples ? 'Hide examples' : 'See examples'}
        </button>
      </div>

      {showExamples && (
        <div className="bg-white border rounded-lg shadow-lg p-4 space-y-2">
          <h4 className="font-medium mb-2">Example Questions:</h4>
          {QUESTION_EXAMPLES.map((example, index) => (
            <div
              key={index}
              onClick={() => handleExampleClick(example)}
              className="cursor-por hover:bg-gray-100 p-2 rounded text-sm"
            >
              {example}
            </div>
          ))}
        </div>
      )}

      <div className="space-y-2">
        {questions.map((question, index) => (
          <div key={index} className="flex gap-2">
            <input
              type="text"
              value={question}
              onChange={(e) => handleQuestionChange(index, e.target.value)}
              placeholder={`Question ${index + 1}`}
              className="flex-1 p-2 border rounded-lg"
            />
            <button
              type="button"
              onClick={() => removeQuestion(index)}
              className="p-2 text-gray-500 hover:text-red-500"
            >
              <X className="h-5 w-5" />
            </button>
          </div>
        ))}
      </div>

      <button
        type="button"
        onClick={addQuestion}
        className="flex items-center gap-2 text-blue-600 hover:text-blue-800"
      >
        <Plus className="h-4 w-4" />
        <span>Add another question</span>
      </button>
    </div>
  );
};

export default QuestionsInput;