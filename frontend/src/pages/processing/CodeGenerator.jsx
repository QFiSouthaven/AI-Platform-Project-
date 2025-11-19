import React, { useState, useEffect } from 'react';
import CodeEditor from '../../components/processing/CodeEditor';
import ProcessingHistory from '../../components/processing/ProcessingHistory';
import { generateCode } from '../../services/processingService';

const CodeGenerator = () => {
  const [language, setLanguage] = useState('python');
  const [taskType, setTaskType] = useState('function');
  const [prompt, setPrompt] = useState('');
  const [generatedCode, setGeneratedCode] = useState('');
  const [isGenerating, setIsGenerating] = useState(false);
  const [error, setError] = useState(null);
  const [history, setHistory] = useState([]);

  const languages = [
    { value: 'python', label: 'Python' },
    { value: 'javascript', label: 'JavaScript' },
    { value: 'typescript', label: 'TypeScript' },
    { value: 'java', label: 'Java' },
    { value: 'go', label: 'Go' },
    { value: 'rust', label: 'Rust' },
  ];

  const taskTypes = [
    { value: 'function', label: 'Function', icon: 'f()' },
    { value: 'class', label: 'Class', icon: 'C' },
    { value: 'module', label: 'Module', icon: 'M' },
    { value: 'test', label: 'Test', icon: 'T' },
  ];

  useEffect(() => {
    // Load history from localStorage
    const savedHistory = localStorage.getItem('codeGeneratorHistory');
    if (savedHistory) {
      setHistory(JSON.parse(savedHistory));
    }
  }, []);

  const saveToHistory = (item) => {
    const newHistory = [item, ...history].slice(0, 50);
    setHistory(newHistory);
    localStorage.setItem('codeGeneratorHistory', JSON.stringify(newHistory));
  };

  const handleGenerate = async () => {
    if (!prompt.trim()) {
      setError('Please enter a description');
      return;
    }

    setIsGenerating(true);
    setError(null);

    try {
      const result = await generateCode({
        language,
        taskType,
        prompt,
      });

      setGeneratedCode(result.code);

      saveToHistory({
        id: Date.now().toString(),
        title: prompt.substring(0, 50) + (prompt.length > 50 ? '...' : ''),
        description: prompt,
        language,
        taskType,
        code: result.code,
        status: 'success',
        createdAt: new Date().toISOString(),
        type: 'generation',
      });
    } catch (err) {
      setError(err.message || 'Failed to generate code');
      saveToHistory({
        id: Date.now().toString(),
        title: prompt.substring(0, 50) + (prompt.length > 50 ? '...' : ''),
        description: prompt,
        language,
        taskType,
        status: 'error',
        createdAt: new Date().toISOString(),
        type: 'generation',
      });
    } finally {
      setIsGenerating(false);
    }
  };

  const handleRegenerate = () => {
    handleGenerate();
  };

  const handleHistorySelect = (item) => {
    setLanguage(item.language);
    setTaskType(item.taskType);
    setPrompt(item.description);
    if (item.code) {
      setGeneratedCode(item.code);
    }
  };

  const handleHistoryDelete = (id) => {
    const newHistory = history.filter((item) => item.id !== id);
    setHistory(newHistory);
    localStorage.setItem('codeGeneratorHistory', JSON.stringify(newHistory));
  };

  return (
    <div className="code-generator-page">
      <div className="page-header">
        <div className="header-content">
          <h1 className="page-title">Code Generator</h1>
          <p className="page-description">
            Generate code using AI-powered language models. Describe what you need and let the AI create it for you.
          </p>
        </div>
      </div>

      <div className="page-content">
        <div className="main-panel">
          <div className="input-section">
            <div className="selectors-row">
              <div className="selector-group">
                <label className="selector-label">Language</label>
                <select
                  value={language}
                  onChange={(e) => setLanguage(e.target.value)}
                  className="selector"
                >
                  {languages.map((lang) => (
                    <option key={lang.value} value={lang.value}>
                      {lang.label}
                    </option>
                  ))}
                </select>
              </div>

              <div className="selector-group task-type-group">
                <label className="selector-label">Task Type</label>
                <div className="task-type-buttons">
                  {taskTypes.map((type) => (
                    <button
                      key={type.value}
                      className={`task-type-button ${taskType === type.value ? 'active' : ''}`}
                      onClick={() => setTaskType(type.value)}
                    >
                      <span className="task-icon">{type.icon}</span>
                      <span className="task-label">{type.label}</span>
                    </button>
                  ))}
                </div>
              </div>
            </div>

            <div className="prompt-section">
              <label className="selector-label">Description</label>
              <textarea
                value={prompt}
                onChange={(e) => setPrompt(e.target.value)}
                placeholder="Describe what you want to generate... e.g., 'Create a function that calculates the factorial of a number using recursion'"
                className="prompt-input"
                rows={4}
              />
            </div>

            {error && (
              <div className="error-message">
                <svg width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2">
                  <circle cx="12" cy="12" r="10"></circle>
                  <line x1="12" y1="8" x2="12" y2="12"></line>
                  <line x1="12" y1="16" x2="12.01" y2="16"></line>
                </svg>
                {error}
              </div>
            )}

            <div className="action-buttons">
              <button
                className="generate-button"
                onClick={handleGenerate}
                disabled={isGenerating || !prompt.trim()}
              >
                {isGenerating ? (
                  <>
                    <svg className="spinner" width="18" height="18" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2">
                      <path d="M21 12a9 9 0 11-6.219-8.56"></path>
                    </svg>
                    Generating...
                  </>
                ) : (
                  <>
                    <svg width="18" height="18" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2">
                      <path d="M13 2L3 14h9l-1 8 10-12h-9l1-8z"></path>
                    </svg>
                    Generate Code
                  </>
                )}
              </button>
            </div>
          </div>

          <div className="output-section">
            <div className="output-header">
              <h2 className="output-title">Generated Code</h2>
              {generatedCode && (
                <button
                  className="regenerate-button"
                  onClick={handleRegenerate}
                  disabled={isGenerating}
                >
                  <svg width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2">
                    <path d="M23 4v6h-6"></path>
                    <path d="M1 20v-6h6"></path>
                    <path d="M3.51 9a9 9 0 0114.85-3.36L23 10M1 14l4.64 4.36A9 9 0 0020.49 15"></path>
                  </svg>
                  Regenerate
                </button>
              )}
            </div>
            <CodeEditor
              code={generatedCode}
              language={language}
              readOnly={true}
              showLineNumbers={true}
              placeholder="Generated code will appear here..."
              height="400px"
            />
          </div>
        </div>

        <div className="sidebar">
          <ProcessingHistory
            history={history}
            onSelectItem={handleHistorySelect}
            onDeleteItem={handleHistoryDelete}
            type="generation"
            title="Generation History"
          />
        </div>
      </div>

      <style jsx>{`
        .code-generator-page {
          min-height: 100vh;
          background: #0a0a0a;
          color: #e0e0e0;
        }

        .page-header {
          padding: 24px 32px;
          background: #111;
          border-bottom: 1px solid #222;
        }

        .header-content {
          max-width: 1400px;
          margin: 0 auto;
        }

        .page-title {
          font-size: 28px;
          font-weight: 700;
          margin: 0 0 8px;
          color: #fff;
        }

        .page-description {
          font-size: 14px;
          color: #888;
          margin: 0;
        }

        .page-content {
          display: grid;
          grid-template-columns: 1fr 320px;
          gap: 24px;
          max-width: 1400px;
          margin: 0 auto;
          padding: 24px 32px;
        }

        .main-panel {
          display: flex;
          flex-direction: column;
          gap: 24px;
        }

        .input-section {
          background: #1a1a1a;
          border-radius: 12px;
          border: 1px solid #333;
          padding: 24px;
        }

        .selectors-row {
          display: flex;
          gap: 24px;
          margin-bottom: 20px;
        }

        .selector-group {
          display: flex;
          flex-direction: column;
          gap: 8px;
        }

        .task-type-group {
          flex: 1;
        }

        .selector-label {
          font-size: 13px;
          font-weight: 500;
          color: #888;
          text-transform: uppercase;
          letter-spacing: 0.5px;
        }

        .selector {
          padding: 10px 12px;
          background: #2a2a2a;
          border: 1px solid #333;
          border-radius: 6px;
          color: #e0e0e0;
          font-size: 14px;
          cursor: pointer;
          min-width: 140px;
        }

        .selector:focus {
          outline: none;
          border-color: #6366f1;
        }

        .task-type-buttons {
          display: flex;
          gap: 8px;
        }

        .task-type-button {
          display: flex;
          align-items: center;
          gap: 6px;
          padding: 10px 16px;
          background: #2a2a2a;
          border: 1px solid #333;
          border-radius: 6px;
          color: #888;
          font-size: 14px;
          cursor: pointer;
          transition: all 0.2s ease;
        }

        .task-type-button:hover {
          background: #333;
          color: #e0e0e0;
        }

        .task-type-button.active {
          background: #6366f1;
          border-color: #6366f1;
          color: #fff;
        }

        .task-icon {
          font-family: 'Fira Code', monospace;
          font-weight: 600;
          font-size: 12px;
        }

        .prompt-section {
          display: flex;
          flex-direction: column;
          gap: 8px;
          margin-bottom: 20px;
        }

        .prompt-input {
          width: 100%;
          padding: 12px 16px;
          background: #2a2a2a;
          border: 1px solid #333;
          border-radius: 8px;
          color: #e0e0e0;
          font-size: 14px;
          line-height: 1.5;
          resize: vertical;
          font-family: inherit;
        }

        .prompt-input:focus {
          outline: none;
          border-color: #6366f1;
        }

        .prompt-input::placeholder {
          color: #666;
        }

        .error-message {
          display: flex;
          align-items: center;
          gap: 8px;
          padding: 12px 16px;
          background: #2d1515;
          border: 1px solid #ef4444;
          border-radius: 6px;
          color: #ef4444;
          font-size: 14px;
          margin-bottom: 16px;
        }

        .action-buttons {
          display: flex;
          justify-content: flex-end;
        }

        .generate-button {
          display: flex;
          align-items: center;
          gap: 8px;
          padding: 12px 24px;
          background: #6366f1;
          border: none;
          border-radius: 8px;
          color: #fff;
          font-size: 14px;
          font-weight: 500;
          cursor: pointer;
          transition: all 0.2s ease;
        }

        .generate-button:hover:not(:disabled) {
          background: #5558e3;
          transform: translateY(-1px);
        }

        .generate-button:disabled {
          opacity: 0.5;
          cursor: not-allowed;
        }

        .spinner {
          animation: spin 1s linear infinite;
        }

        @keyframes spin {
          from {
            transform: rotate(0deg);
          }
          to {
            transform: rotate(360deg);
          }
        }

        .output-section {
          background: #1a1a1a;
          border-radius: 12px;
          border: 1px solid #333;
          padding: 24px;
        }

        .output-header {
          display: flex;
          justify-content: space-between;
          align-items: center;
          margin-bottom: 16px;
        }

        .output-title {
          font-size: 18px;
          font-weight: 600;
          margin: 0;
          color: #e0e0e0;
        }

        .regenerate-button {
          display: flex;
          align-items: center;
          gap: 6px;
          padding: 8px 12px;
          background: #2a2a2a;
          border: 1px solid #333;
          border-radius: 6px;
          color: #888;
          font-size: 13px;
          cursor: pointer;
          transition: all 0.2s ease;
        }

        .regenerate-button:hover:not(:disabled) {
          background: #333;
          color: #e0e0e0;
        }

        .regenerate-button:disabled {
          opacity: 0.5;
          cursor: not-allowed;
        }

        .sidebar {
          height: calc(100vh - 180px);
          position: sticky;
          top: 24px;
        }

        @media (max-width: 1024px) {
          .page-content {
            grid-template-columns: 1fr;
          }

          .sidebar {
            height: 400px;
            position: static;
          }

          .selectors-row {
            flex-direction: column;
          }
        }
      `}</style>
    </div>
  );
};

export default CodeGenerator;
