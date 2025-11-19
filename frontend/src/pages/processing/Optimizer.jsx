import React, { useState } from 'react';
import CodeEditor from '../../components/processing/CodeEditor';
import { optimizeCode } from '../../services/processingService';

const Optimizer = () => {
  const [originalCode, setOriginalCode] = useState('');
  const [optimizedCode, setOptimizedCode] = useState('');
  const [language, setLanguage] = useState('python');
  const [optimizationType, setOptimizationType] = useState('performance');
  const [isOptimizing, setIsOptimizing] = useState(false);
  const [suggestions, setSuggestions] = useState([]);
  const [error, setError] = useState(null);
  const [showDiff, setShowDiff] = useState(false);

  const languages = [
    { value: 'python', label: 'Python' },
    { value: 'javascript', label: 'JavaScript' },
    { value: 'typescript', label: 'TypeScript' },
    { value: 'java', label: 'Java' },
    { value: 'go', label: 'Go' },
    { value: 'rust', label: 'Rust' },
  ];

  const optimizationTypes = [
    {
      value: 'performance',
      label: 'Performance',
      icon: (
        <svg width="18" height="18" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2">
          <path d="M13 2L3 14h9l-1 8 10-12h-9l1-8z"></path>
        </svg>
      ),
      description: 'Improve execution speed and efficiency',
    },
    {
      value: 'readability',
      label: 'Readability',
      icon: (
        <svg width="18" height="18" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2">
          <path d="M2 3h6a4 4 0 0 1 4 4v14a3 3 0 0 0-3-3H2z"></path>
          <path d="M22 3h-6a4 4 0 0 0-4 4v14a3 3 0 0 1 3-3h7z"></path>
        </svg>
      ),
      description: 'Improve code clarity and maintainability',
    },
    {
      value: 'memory',
      label: 'Memory',
      icon: (
        <svg width="18" height="18" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2">
          <rect x="4" y="4" width="16" height="16" rx="2" ry="2"></rect>
          <rect x="9" y="9" width="6" height="6"></rect>
          <line x1="9" y1="1" x2="9" y2="4"></line>
          <line x1="15" y1="1" x2="15" y2="4"></line>
          <line x1="9" y1="20" x2="9" y2="23"></line>
          <line x1="15" y1="20" x2="15" y2="23"></line>
        </svg>
      ),
      description: 'Reduce memory usage and allocation',
    },
    {
      value: 'security',
      label: 'Security',
      icon: (
        <svg width="18" height="18" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2">
          <path d="M12 22s8-4 8-10V5l-8-3-8 3v7c0 6 8 10 8 10z"></path>
        </svg>
      ),
      description: 'Fix security vulnerabilities',
    },
  ];

  const handleOptimize = async () => {
    if (!originalCode.trim()) {
      setError('Please enter code to optimize');
      return;
    }

    setIsOptimizing(true);
    setError(null);
    setOptimizedCode('');
    setSuggestions([]);

    try {
      const result = await optimizeCode({
        code: originalCode,
        language,
        optimizationType,
      });

      setOptimizedCode(result.optimizedCode);
      setSuggestions(result.suggestions || []);
    } catch (err) {
      setError(err.message || 'Failed to optimize code');
    } finally {
      setIsOptimizing(false);
    }
  };

  const handleApplyOptimizations = () => {
    setOriginalCode(optimizedCode);
    setOptimizedCode('');
    setSuggestions([]);
  };

  const getImpactColor = (impact) => {
    const colors = {
      high: '#10b981',
      medium: '#f59e0b',
      low: '#6366f1',
    };
    return colors[impact] || '#888';
  };

  const getCategoryIcon = (category) => {
    const icons = {
      performance: (
        <svg width="14" height="14" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2">
          <path d="M13 2L3 14h9l-1 8 10-12h-9l1-8z"></path>
        </svg>
      ),
      readability: (
        <svg width="14" height="14" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2">
          <path d="M1 12s4-8 11-8 11 8 11 8-4 8-11 8-11-8-11-8z"></path>
          <circle cx="12" cy="12" r="3"></circle>
        </svg>
      ),
      memory: (
        <svg width="14" height="14" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2">
          <rect x="4" y="4" width="16" height="16" rx="2"></rect>
        </svg>
      ),
      security: (
        <svg width="14" height="14" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2">
          <path d="M12 22s8-4 8-10V5l-8-3-8 3v7c0 6 8 10 8 10z"></path>
        </svg>
      ),
    };
    return icons[category] || icons.performance;
  };

  return (
    <div className="optimizer-page">
      <div className="page-header">
        <div className="header-content">
          <h1 className="page-title">Code Optimizer</h1>
          <p className="page-description">
            Optimize your code for performance, readability, memory efficiency, or security using AI analysis.
          </p>
        </div>
      </div>

      <div className="page-content">
        <div className="controls-section">
          <div className="language-control">
            <label className="control-label">Language</label>
            <select
              value={language}
              onChange={(e) => setLanguage(e.target.value)}
              className="language-selector"
            >
              {languages.map((lang) => (
                <option key={lang.value} value={lang.value}>
                  {lang.label}
                </option>
              ))}
            </select>
          </div>

          <div className="optimization-types">
            <label className="control-label">Optimization Type</label>
            <div className="type-cards">
              {optimizationTypes.map((type) => (
                <div
                  key={type.value}
                  className={`type-card ${optimizationType === type.value ? 'active' : ''}`}
                  onClick={() => setOptimizationType(type.value)}
                >
                  <div className="type-icon">{type.icon}</div>
                  <div className="type-info">
                    <span className="type-label">{type.label}</span>
                    <span className="type-description">{type.description}</span>
                  </div>
                </div>
              ))}
            </div>
          </div>
        </div>

        <div className="code-comparison">
          <div className="code-panel original">
            <div className="panel-header">
              <h2 className="panel-title">Original Code</h2>
            </div>
            <CodeEditor
              code={originalCode}
              onChange={setOriginalCode}
              language={language}
              showLineNumbers={true}
              placeholder="Paste your code here to optimize..."
              height="400px"
            />
          </div>

          <div className="comparison-divider">
            <div className="divider-line"></div>
            <button
              className="optimize-button"
              onClick={handleOptimize}
              disabled={isOptimizing || !originalCode.trim()}
            >
              {isOptimizing ? (
                <svg className="spinner" width="20" height="20" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2">
                  <path d="M21 12a9 9 0 11-6.219-8.56"></path>
                </svg>
              ) : (
                <svg width="20" height="20" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2">
                  <polyline points="9 18 15 12 9 6"></polyline>
                </svg>
              )}
            </button>
            <div className="divider-line"></div>
          </div>

          <div className="code-panel optimized">
            <div className="panel-header">
              <h2 className="panel-title">Optimized Code</h2>
              {optimizedCode && (
                <div className="panel-actions">
                  <button
                    className={`diff-toggle ${showDiff ? 'active' : ''}`}
                    onClick={() => setShowDiff(!showDiff)}
                  >
                    <svg width="14" height="14" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2">
                      <path d="M16 3h5v5"></path>
                      <path d="M8 21H3v-5"></path>
                      <path d="M21 3l-9 9"></path>
                      <path d="M3 21l9-9"></path>
                    </svg>
                    Diff
                  </button>
                  <button
                    className="apply-button"
                    onClick={handleApplyOptimizations}
                  >
                    <svg width="14" height="14" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2">
                      <polyline points="20 6 9 17 4 12"></polyline>
                    </svg>
                    Apply
                  </button>
                </div>
              )}
            </div>
            <CodeEditor
              code={optimizedCode}
              language={language}
              readOnly={true}
              showLineNumbers={true}
              placeholder="Optimized code will appear here..."
              height="400px"
            />
          </div>
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

        {suggestions.length > 0 && (
          <div className="suggestions-section">
            <h2 className="suggestions-title">Optimization Suggestions</h2>
            <div className="suggestions-list">
              {suggestions.map((suggestion, index) => (
                <div key={index} className="suggestion-card">
                  <div className="suggestion-header">
                    <div className="suggestion-category">
                      {getCategoryIcon(suggestion.category)}
                      <span>{suggestion.category}</span>
                    </div>
                    <span
                      className="suggestion-impact"
                      style={{ color: getImpactColor(suggestion.impact) }}
                    >
                      {suggestion.impact} impact
                    </span>
                  </div>
                  <p className="suggestion-title">{suggestion.title}</p>
                  <p className="suggestion-description">{suggestion.description}</p>
                  {suggestion.lineNumbers && (
                    <span className="suggestion-lines">
                      Lines: {suggestion.lineNumbers.join(', ')}
                    </span>
                  )}
                </div>
              ))}
            </div>
          </div>
        )}
      </div>

      <style jsx>{`
        .optimizer-page {
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
          max-width: 1400px;
          margin: 0 auto;
          padding: 24px 32px;
        }

        .controls-section {
          display: flex;
          gap: 24px;
          margin-bottom: 24px;
          align-items: flex-start;
        }

        .language-control {
          display: flex;
          flex-direction: column;
          gap: 8px;
        }

        .control-label {
          font-size: 13px;
          font-weight: 500;
          color: #888;
          text-transform: uppercase;
          letter-spacing: 0.5px;
        }

        .language-selector {
          padding: 10px 12px;
          background: #2a2a2a;
          border: 1px solid #333;
          border-radius: 6px;
          color: #e0e0e0;
          font-size: 14px;
          cursor: pointer;
          min-width: 140px;
        }

        .optimization-types {
          flex: 1;
          display: flex;
          flex-direction: column;
          gap: 8px;
        }

        .type-cards {
          display: grid;
          grid-template-columns: repeat(4, 1fr);
          gap: 12px;
        }

        .type-card {
          display: flex;
          align-items: center;
          gap: 12px;
          padding: 12px 16px;
          background: #1a1a1a;
          border: 1px solid #333;
          border-radius: 8px;
          cursor: pointer;
          transition: all 0.2s ease;
        }

        .type-card:hover {
          background: #222;
          border-color: #444;
        }

        .type-card.active {
          background: #2d2d5a;
          border-color: #6366f1;
        }

        .type-icon {
          flex-shrink: 0;
          color: #888;
        }

        .type-card.active .type-icon {
          color: #6366f1;
        }

        .type-info {
          display: flex;
          flex-direction: column;
          gap: 2px;
          min-width: 0;
        }

        .type-label {
          font-size: 14px;
          font-weight: 500;
          color: #e0e0e0;
        }

        .type-description {
          font-size: 11px;
          color: #666;
          white-space: nowrap;
          overflow: hidden;
          text-overflow: ellipsis;
        }

        .code-comparison {
          display: grid;
          grid-template-columns: 1fr auto 1fr;
          gap: 16px;
          margin-bottom: 24px;
        }

        .code-panel {
          display: flex;
          flex-direction: column;
        }

        .panel-header {
          display: flex;
          justify-content: space-between;
          align-items: center;
          margin-bottom: 12px;
        }

        .panel-title {
          font-size: 16px;
          font-weight: 600;
          margin: 0;
          color: #e0e0e0;
        }

        .panel-actions {
          display: flex;
          gap: 8px;
        }

        .diff-toggle,
        .apply-button {
          display: flex;
          align-items: center;
          gap: 4px;
          padding: 6px 10px;
          background: #2a2a2a;
          border: 1px solid #333;
          border-radius: 4px;
          color: #888;
          font-size: 12px;
          cursor: pointer;
          transition: all 0.2s ease;
        }

        .diff-toggle:hover,
        .apply-button:hover {
          background: #333;
          color: #e0e0e0;
        }

        .diff-toggle.active {
          background: #6366f1;
          border-color: #6366f1;
          color: #fff;
        }

        .apply-button {
          background: #10b981;
          border-color: #10b981;
          color: #fff;
        }

        .apply-button:hover {
          background: #059669;
        }

        .comparison-divider {
          display: flex;
          flex-direction: column;
          align-items: center;
          padding: 40px 0;
        }

        .divider-line {
          flex: 1;
          width: 2px;
          background: #333;
        }

        .optimize-button {
          display: flex;
          align-items: center;
          justify-content: center;
          width: 48px;
          height: 48px;
          background: #6366f1;
          border: none;
          border-radius: 50%;
          color: #fff;
          cursor: pointer;
          transition: all 0.2s ease;
          margin: 12px 0;
        }

        .optimize-button:hover:not(:disabled) {
          background: #5558e3;
          transform: scale(1.1);
        }

        .optimize-button:disabled {
          opacity: 0.5;
          cursor: not-allowed;
        }

        .spinner {
          animation: spin 1s linear infinite;
        }

        @keyframes spin {
          from { transform: rotate(0deg); }
          to { transform: rotate(360deg); }
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
          margin-bottom: 24px;
        }

        .suggestions-section {
          background: #1a1a1a;
          border-radius: 12px;
          border: 1px solid #333;
          padding: 20px;
        }

        .suggestions-title {
          font-size: 18px;
          font-weight: 600;
          margin: 0 0 16px;
          color: #e0e0e0;
        }

        .suggestions-list {
          display: grid;
          grid-template-columns: repeat(auto-fill, minmax(300px, 1fr));
          gap: 16px;
        }

        .suggestion-card {
          background: #222;
          border-radius: 8px;
          border: 1px solid #333;
          padding: 16px;
        }

        .suggestion-header {
          display: flex;
          justify-content: space-between;
          align-items: center;
          margin-bottom: 8px;
        }

        .suggestion-category {
          display: flex;
          align-items: center;
          gap: 6px;
          font-size: 12px;
          color: #888;
          text-transform: capitalize;
        }

        .suggestion-impact {
          font-size: 11px;
          font-weight: 500;
          text-transform: capitalize;
        }

        .suggestion-title {
          font-size: 14px;
          font-weight: 500;
          margin: 0 0 8px;
          color: #e0e0e0;
        }

        .suggestion-description {
          font-size: 13px;
          color: #888;
          margin: 0 0 8px;
          line-height: 1.5;
        }

        .suggestion-lines {
          font-size: 11px;
          color: #666;
          font-family: 'Fira Code', monospace;
        }

        @media (max-width: 1200px) {
          .type-cards {
            grid-template-columns: repeat(2, 1fr);
          }
        }

        @media (max-width: 1024px) {
          .code-comparison {
            grid-template-columns: 1fr;
          }

          .comparison-divider {
            flex-direction: row;
            padding: 0;
            margin: 16px 0;
          }

          .divider-line {
            height: 2px;
            width: auto;
          }

          .controls-section {
            flex-direction: column;
          }
        }
      `}</style>
    </div>
  );
};

export default Optimizer;
