import React, { useState } from 'react';
import CodeEditor from '../../components/processing/CodeEditor';
import QualityChart from '../../components/processing/QualityChart';
import { evaluateCode } from '../../services/processingService';

const Evaluator = () => {
  const [code, setCode] = useState('');
  const [language, setLanguage] = useState('python');
  const [isEvaluating, setIsEvaluating] = useState(false);
  const [evaluationResult, setEvaluationResult] = useState(null);
  const [error, setError] = useState(null);

  const languages = [
    { value: 'python', label: 'Python' },
    { value: 'javascript', label: 'JavaScript' },
    { value: 'typescript', label: 'TypeScript' },
    { value: 'java', label: 'Java' },
    { value: 'go', label: 'Go' },
    { value: 'rust', label: 'Rust' },
  ];

  const handleEvaluate = async () => {
    if (!code.trim()) {
      setError('Please enter code to evaluate');
      return;
    }

    setIsEvaluating(true);
    setError(null);
    setEvaluationResult(null);

    try {
      const result = await evaluateCode({
        code,
        language,
      });

      setEvaluationResult(result);
    } catch (err) {
      setError(err.message || 'Failed to evaluate code');
    } finally {
      setIsEvaluating(false);
    }
  };

  const getSeverityColor = (severity) => {
    const colors = {
      critical: '#ef4444',
      high: '#f59e0b',
      medium: '#eab308',
      low: '#10b981',
      info: '#6366f1',
    };
    return colors[severity] || '#888';
  };

  const getSeverityBg = (severity) => {
    const colors = {
      critical: '#2d1515',
      high: '#2d2215',
      medium: '#2d2a15',
      low: '#152d1a',
      info: '#15152d',
    };
    return colors[severity] || '#222';
  };

  const getScoreLabel = (score) => {
    if (score >= 90) return { label: 'Excellent', color: '#10b981' };
    if (score >= 75) return { label: 'Good', color: '#22c55e' };
    if (score >= 60) return { label: 'Fair', color: '#eab308' };
    if (score >= 40) return { label: 'Needs Work', color: '#f59e0b' };
    return { label: 'Poor', color: '#ef4444' };
  };

  return (
    <div className="evaluator-page">
      <div className="page-header">
        <div className="header-content">
          <h1 className="page-title">Code Evaluator</h1>
          <p className="page-description">
            Analyze code quality with comprehensive metrics including readability, performance, security, and more.
          </p>
        </div>
      </div>

      <div className="page-content">
        <div className="input-panel">
          <div className="input-header">
            <h2 className="section-title">Code Input</h2>
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

          <CodeEditor
            code={code}
            onChange={setCode}
            language={language}
            showLineNumbers={true}
            placeholder="Paste your code here to evaluate..."
            height="450px"
          />

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

          <button
            className="evaluate-button"
            onClick={handleEvaluate}
            disabled={isEvaluating || !code.trim()}
          >
            {isEvaluating ? (
              <>
                <svg className="spinner" width="18" height="18" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2">
                  <path d="M21 12a9 9 0 11-6.219-8.56"></path>
                </svg>
                Evaluating...
              </>
            ) : (
              <>
                <svg width="18" height="18" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2">
                  <path d="M22 11.08V12a10 10 0 1 1-5.93-9.14"></path>
                  <polyline points="22 4 12 14.01 9 11.01"></polyline>
                </svg>
                Evaluate Code
              </>
            )}
          </button>
        </div>

        <div className="results-panel">
          {evaluationResult ? (
            <>
              <div className="chart-section">
                <h2 className="section-title">Quality Scores</h2>
                <div className="chart-container">
                  <QualityChart
                    scores={evaluationResult.scores}
                    size={320}
                    color="#6366f1"
                    backgroundColor="#1a1a1a"
                  />
                </div>
              </div>

              <div className="metrics-section">
                <h2 className="section-title">Metrics Breakdown</h2>
                <div className="metrics-grid">
                  {Object.entries(evaluationResult.scores || {}).map(([metric, score]) => {
                    const scoreInfo = getScoreLabel(score);
                    return (
                      <div key={metric} className="metric-card">
                        <div className="metric-header">
                          <span className="metric-name">{metric}</span>
                          <span className="metric-score" style={{ color: scoreInfo.color }}>
                            {score}%
                          </span>
                        </div>
                        <div className="metric-bar">
                          <div
                            className="metric-bar-fill"
                            style={{
                              width: `${score}%`,
                              backgroundColor: scoreInfo.color,
                            }}
                          ></div>
                        </div>
                        <span className="metric-label" style={{ color: scoreInfo.color }}>
                          {scoreInfo.label}
                        </span>
                      </div>
                    );
                  })}
                </div>
              </div>

              {evaluationResult.issues && evaluationResult.issues.length > 0 && (
                <div className="issues-section">
                  <h2 className="section-title">
                    Issues Found
                    <span className="issues-count">{evaluationResult.issues.length}</span>
                  </h2>
                  <div className="issues-list">
                    {evaluationResult.issues.map((issue, index) => (
                      <div
                        key={index}
                        className="issue-card"
                        style={{
                          borderLeftColor: getSeverityColor(issue.severity),
                          backgroundColor: getSeverityBg(issue.severity),
                        }}
                      >
                        <div className="issue-header">
                          <span
                            className="issue-severity"
                            style={{ color: getSeverityColor(issue.severity) }}
                          >
                            {issue.severity}
                          </span>
                          <span className="issue-line">Line {issue.line}</span>
                        </div>
                        <p className="issue-message">{issue.message}</p>
                        {issue.suggestion && (
                          <p className="issue-suggestion">
                            <strong>Suggestion:</strong> {issue.suggestion}
                          </p>
                        )}
                      </div>
                    ))}
                  </div>
                </div>
              )}

              {evaluationResult.improvements && evaluationResult.improvements.length > 0 && (
                <div className="improvements-section">
                  <h2 className="section-title">Improvement Suggestions</h2>
                  <div className="improvements-list">
                    {evaluationResult.improvements.map((improvement, index) => (
                      <div key={index} className="improvement-card">
                        <div className="improvement-icon">
                          <svg width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2">
                            <circle cx="12" cy="12" r="10"></circle>
                            <path d="M12 16v-4"></path>
                            <path d="M12 8h.01"></path>
                          </svg>
                        </div>
                        <div className="improvement-content">
                          <span className="improvement-category">{improvement.category}</span>
                          <p className="improvement-text">{improvement.suggestion}</p>
                          {improvement.impact && (
                            <span className="improvement-impact">
                              Impact: {improvement.impact}
                            </span>
                          )}
                        </div>
                      </div>
                    ))}
                  </div>
                </div>
              )}
            </>
          ) : (
            <div className="empty-results">
              <svg width="64" height="64" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="1">
                <path d="M22 11.08V12a10 10 0 1 1-5.93-9.14"></path>
                <polyline points="22 4 12 14.01 9 11.01"></polyline>
              </svg>
              <h3>No Evaluation Yet</h3>
              <p>Enter your code and click "Evaluate Code" to get a comprehensive quality analysis.</p>
            </div>
          )}
        </div>
      </div>

      <style jsx>{`
        .evaluator-page {
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
          grid-template-columns: 1fr 1fr;
          gap: 24px;
          max-width: 1400px;
          margin: 0 auto;
          padding: 24px 32px;
        }

        .input-panel {
          display: flex;
          flex-direction: column;
          gap: 16px;
        }

        .input-header {
          display: flex;
          justify-content: space-between;
          align-items: center;
        }

        .section-title {
          font-size: 18px;
          font-weight: 600;
          margin: 0;
          color: #e0e0e0;
          display: flex;
          align-items: center;
          gap: 8px;
        }

        .language-selector {
          padding: 8px 12px;
          background: #2a2a2a;
          border: 1px solid #333;
          border-radius: 6px;
          color: #e0e0e0;
          font-size: 13px;
          cursor: pointer;
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
        }

        .evaluate-button {
          display: flex;
          align-items: center;
          justify-content: center;
          gap: 8px;
          padding: 14px 24px;
          background: #6366f1;
          border: none;
          border-radius: 8px;
          color: #fff;
          font-size: 14px;
          font-weight: 500;
          cursor: pointer;
          transition: all 0.2s ease;
        }

        .evaluate-button:hover:not(:disabled) {
          background: #5558e3;
          transform: translateY(-1px);
        }

        .evaluate-button:disabled {
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

        .results-panel {
          display: flex;
          flex-direction: column;
          gap: 24px;
        }

        .empty-results {
          display: flex;
          flex-direction: column;
          align-items: center;
          justify-content: center;
          height: 400px;
          background: #1a1a1a;
          border-radius: 12px;
          border: 1px solid #333;
          padding: 32px;
          text-align: center;
          color: #666;
        }

        .empty-results svg {
          margin-bottom: 16px;
          opacity: 0.5;
        }

        .empty-results h3 {
          margin: 0 0 8px;
          font-size: 18px;
          color: #888;
        }

        .empty-results p {
          margin: 0;
          font-size: 14px;
          max-width: 300px;
        }

        .chart-section {
          background: #1a1a1a;
          border-radius: 12px;
          border: 1px solid #333;
          padding: 20px;
        }

        .chart-container {
          display: flex;
          justify-content: center;
          padding: 20px 0;
        }

        .metrics-section {
          background: #1a1a1a;
          border-radius: 12px;
          border: 1px solid #333;
          padding: 20px;
        }

        .metrics-grid {
          display: grid;
          grid-template-columns: repeat(2, 1fr);
          gap: 16px;
          margin-top: 16px;
        }

        .metric-card {
          background: #222;
          border-radius: 8px;
          padding: 12px;
        }

        .metric-header {
          display: flex;
          justify-content: space-between;
          align-items: center;
          margin-bottom: 8px;
        }

        .metric-name {
          font-size: 13px;
          color: #888;
          text-transform: capitalize;
        }

        .metric-score {
          font-size: 16px;
          font-weight: 600;
        }

        .metric-bar {
          height: 6px;
          background: #333;
          border-radius: 3px;
          overflow: hidden;
          margin-bottom: 6px;
        }

        .metric-bar-fill {
          height: 100%;
          border-radius: 3px;
          transition: width 0.5s ease;
        }

        .metric-label {
          font-size: 11px;
          font-weight: 500;
        }

        .issues-section {
          background: #1a1a1a;
          border-radius: 12px;
          border: 1px solid #333;
          padding: 20px;
        }

        .issues-count {
          font-size: 12px;
          background: #ef4444;
          color: #fff;
          padding: 2px 8px;
          border-radius: 12px;
          margin-left: 8px;
        }

        .issues-list {
          display: flex;
          flex-direction: column;
          gap: 12px;
          margin-top: 16px;
        }

        .issue-card {
          padding: 12px 16px;
          border-radius: 8px;
          border-left: 3px solid;
        }

        .issue-header {
          display: flex;
          justify-content: space-between;
          align-items: center;
          margin-bottom: 8px;
        }

        .issue-severity {
          font-size: 12px;
          font-weight: 600;
          text-transform: capitalize;
        }

        .issue-line {
          font-size: 11px;
          color: #666;
          font-family: 'Fira Code', monospace;
        }

        .issue-message {
          margin: 0 0 8px;
          font-size: 14px;
          color: #e0e0e0;
        }

        .issue-suggestion {
          margin: 0;
          font-size: 12px;
          color: #888;
        }

        .issue-suggestion strong {
          color: #10b981;
        }

        .improvements-section {
          background: #1a1a1a;
          border-radius: 12px;
          border: 1px solid #333;
          padding: 20px;
        }

        .improvements-list {
          display: flex;
          flex-direction: column;
          gap: 12px;
          margin-top: 16px;
        }

        .improvement-card {
          display: flex;
          gap: 12px;
          padding: 12px;
          background: #222;
          border-radius: 8px;
        }

        .improvement-icon {
          flex-shrink: 0;
          color: #6366f1;
        }

        .improvement-content {
          flex: 1;
        }

        .improvement-category {
          font-size: 11px;
          color: #6366f1;
          text-transform: uppercase;
          letter-spacing: 0.5px;
        }

        .improvement-text {
          margin: 4px 0 8px;
          font-size: 13px;
          color: #e0e0e0;
          line-height: 1.5;
        }

        .improvement-impact {
          font-size: 11px;
          color: #888;
        }

        @media (max-width: 1024px) {
          .page-content {
            grid-template-columns: 1fr;
          }

          .metrics-grid {
            grid-template-columns: 1fr;
          }
        }
      `}</style>
    </div>
  );
};

export default Evaluator;
