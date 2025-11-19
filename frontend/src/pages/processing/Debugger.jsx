import React, { useState } from 'react';
import CodeEditor from '../../components/processing/CodeEditor';
import { debugCode } from '../../services/processingService';

const Debugger = () => {
  const [code, setCode] = useState('');
  const [errorMessage, setErrorMessage] = useState('');
  const [stackTrace, setStackTrace] = useState('');
  const [language, setLanguage] = useState('python');
  const [isAnalyzing, setIsAnalyzing] = useState(false);
  const [analysisResult, setAnalysisResult] = useState(null);
  const [error, setError] = useState(null);

  const languages = [
    { value: 'python', label: 'Python' },
    { value: 'javascript', label: 'JavaScript' },
    { value: 'typescript', label: 'TypeScript' },
    { value: 'java', label: 'Java' },
    { value: 'go', label: 'Go' },
    { value: 'rust', label: 'Rust' },
  ];

  const handleAnalyze = async () => {
    if (!code.trim()) {
      setError('Please enter code to debug');
      return;
    }

    setIsAnalyzing(true);
    setError(null);
    setAnalysisResult(null);

    try {
      const result = await debugCode({
        code,
        errorMessage,
        stackTrace,
        language,
      });

      setAnalysisResult(result);
    } catch (err) {
      setError(err.message || 'Failed to analyze code');
    } finally {
      setIsAnalyzing(false);
    }
  };

  const handleApplyFix = (fix) => {
    setCode(fix.fixedCode);
    setAnalysisResult(null);
    setErrorMessage('');
    setStackTrace('');
  };

  const parseStackTrace = () => {
    if (!stackTrace) return [];

    const lines = stackTrace.split('\n').filter(Boolean);
    return lines.map((line, index) => {
      const fileMatch = line.match(/File "([^"]+)", line (\d+)/);
      const jsMatch = line.match(/at .+ \((.+):(\d+):(\d+)\)/);

      if (fileMatch) {
        return {
          id: index,
          file: fileMatch[1],
          line: parseInt(fileMatch[2]),
          content: line,
        };
      } else if (jsMatch) {
        return {
          id: index,
          file: jsMatch[1],
          line: parseInt(jsMatch[2]),
          column: parseInt(jsMatch[3]),
          content: line,
        };
      }

      return {
        id: index,
        content: line,
      };
    });
  };

  const getSeverityColor = (severity) => {
    const colors = {
      critical: '#ef4444',
      high: '#f59e0b',
      medium: '#eab308',
      low: '#10b981',
    };
    return colors[severity] || '#888';
  };

  return (
    <div className="debugger-page">
      <div className="page-header">
        <div className="header-content">
          <h1 className="page-title">Code Debugger</h1>
          <p className="page-description">
            Analyze code errors and get AI-powered suggestions for fixes. Paste your code, error message, and stack trace for analysis.
          </p>
        </div>
      </div>

      <div className="page-content">
        <div className="input-panel">
          <div className="input-section">
            <div className="section-header">
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
              placeholder="Paste your code here..."
              height="300px"
            />
          </div>

          <div className="error-inputs">
            <div className="error-input-group">
              <label className="input-label">Error Message</label>
              <textarea
                value={errorMessage}
                onChange={(e) => setErrorMessage(e.target.value)}
                placeholder="Paste the error message..."
                className="error-textarea"
                rows={3}
              />
            </div>

            <div className="error-input-group">
              <label className="input-label">Stack Trace</label>
              <textarea
                value={stackTrace}
                onChange={(e) => setStackTrace(e.target.value)}
                placeholder="Paste the stack trace (optional)..."
                className="error-textarea stack-trace"
                rows={5}
              />
            </div>
          </div>

          {stackTrace && (
            <div className="parsed-stack">
              <h3 className="parsed-stack-title">Parsed Stack Trace</h3>
              <div className="stack-frames">
                {parseStackTrace().map((frame) => (
                  <div key={frame.id} className="stack-frame">
                    {frame.file ? (
                      <>
                        <span className="frame-file">{frame.file}</span>
                        <span className="frame-line">Line {frame.line}</span>
                      </>
                    ) : (
                      <span className="frame-content">{frame.content}</span>
                    )}
                  </div>
                ))}
              </div>
            </div>
          )}

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
            className="analyze-button"
            onClick={handleAnalyze}
            disabled={isAnalyzing || !code.trim()}
          >
            {isAnalyzing ? (
              <>
                <svg className="spinner" width="18" height="18" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2">
                  <path d="M21 12a9 9 0 11-6.219-8.56"></path>
                </svg>
                Analyzing...
              </>
            ) : (
              <>
                <svg width="18" height="18" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2">
                  <path d="M12 22c5.523 0 10-4.477 10-10S17.523 2 12 2 2 6.477 2 12s4.477 10 10 10z"></path>
                  <path d="M12 8v4"></path>
                  <path d="M12 16h.01"></path>
                </svg>
                Analyze Bug
              </>
            )}
          </button>
        </div>

        <div className="results-panel">
          {analysisResult ? (
            <>
              <div className="analysis-summary">
                <h2 className="results-title">Bug Analysis</h2>
                <div className="bug-info">
                  <div className="bug-type">
                    <span className="bug-label">Bug Type</span>
                    <span className="bug-value">{analysisResult.bugType}</span>
                  </div>
                  <div className="bug-location">
                    <span className="bug-label">Location</span>
                    <span className="bug-value">Line {analysisResult.location?.line || 'N/A'}</span>
                  </div>
                  <div className="bug-severity">
                    <span className="bug-label">Severity</span>
                    <span
                      className="bug-value severity-badge"
                      style={{ color: getSeverityColor(analysisResult.severity) }}
                    >
                      {analysisResult.severity || 'Unknown'}
                    </span>
                  </div>
                </div>
                <p className="bug-explanation">{analysisResult.explanation}</p>
              </div>

              <div className="suggested-fixes">
                <h3 className="fixes-title">Suggested Fixes</h3>
                {analysisResult.fixes?.map((fix, index) => (
                  <div key={index} className="fix-card">
                    <div className="fix-header">
                      <span className="fix-number">Fix #{index + 1}</span>
                      <span className="fix-confidence">
                        {Math.round(fix.confidence * 100)}% confidence
                      </span>
                    </div>
                    <p className="fix-description">{fix.description}</p>
                    <CodeEditor
                      code={fix.fixedCode}
                      language={language}
                      readOnly={true}
                      showLineNumbers={true}
                      height="200px"
                      title="Fixed Code"
                    />
                    <button
                      className="apply-fix-button"
                      onClick={() => handleApplyFix(fix)}
                    >
                      <svg width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2">
                        <polyline points="20 6 9 17 4 12"></polyline>
                      </svg>
                      Apply Fix
                    </button>
                  </div>
                ))}
              </div>

              {analysisResult.relatedIssues && analysisResult.relatedIssues.length > 0 && (
                <div className="related-issues">
                  <h3 className="related-title">Related Issues</h3>
                  {analysisResult.relatedIssues.map((issue, index) => (
                    <div key={index} className="related-issue">
                      <span className="issue-icon">
                        <svg width="14" height="14" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2">
                          <circle cx="12" cy="12" r="10"></circle>
                          <line x1="12" y1="16" x2="12" y2="12"></line>
                          <line x1="12" y1="8" x2="12.01" y2="8"></line>
                        </svg>
                      </span>
                      <span className="issue-text">{issue}</span>
                    </div>
                  ))}
                </div>
              )}
            </>
          ) : (
            <div className="empty-results">
              <svg width="64" height="64" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="1">
                <path d="M12 22c5.523 0 10-4.477 10-10S17.523 2 12 2 2 6.477 2 12s4.477 10 10 10z"></path>
                <path d="M12 8v4"></path>
                <path d="M12 16h.01"></path>
              </svg>
              <h3>No Analysis Yet</h3>
              <p>Enter your code and error message, then click "Analyze Bug" to get debugging suggestions.</p>
            </div>
          )}
        </div>
      </div>

      <style jsx>{`
        .debugger-page {
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
          gap: 20px;
        }

        .input-section {
          background: #1a1a1a;
          border-radius: 12px;
          border: 1px solid #333;
          padding: 20px;
        }

        .section-header {
          display: flex;
          justify-content: space-between;
          align-items: center;
          margin-bottom: 16px;
        }

        .section-title {
          font-size: 16px;
          font-weight: 600;
          margin: 0;
          color: #e0e0e0;
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

        .error-inputs {
          display: flex;
          flex-direction: column;
          gap: 16px;
        }

        .error-input-group {
          display: flex;
          flex-direction: column;
          gap: 8px;
        }

        .input-label {
          font-size: 13px;
          font-weight: 500;
          color: #888;
          text-transform: uppercase;
          letter-spacing: 0.5px;
        }

        .error-textarea {
          width: 100%;
          padding: 12px 16px;
          background: #1a1a1a;
          border: 1px solid #333;
          border-radius: 8px;
          color: #e0e0e0;
          font-size: 14px;
          font-family: inherit;
          resize: vertical;
        }

        .error-textarea:focus {
          outline: none;
          border-color: #6366f1;
        }

        .error-textarea::placeholder {
          color: #666;
        }

        .stack-trace {
          font-family: 'Fira Code', monospace;
          font-size: 12px;
        }

        .parsed-stack {
          background: #1a1a1a;
          border-radius: 8px;
          border: 1px solid #333;
          padding: 16px;
        }

        .parsed-stack-title {
          font-size: 14px;
          font-weight: 500;
          margin: 0 0 12px;
          color: #888;
        }

        .stack-frames {
          display: flex;
          flex-direction: column;
          gap: 8px;
        }

        .stack-frame {
          display: flex;
          align-items: center;
          gap: 12px;
          padding: 8px 12px;
          background: #222;
          border-radius: 6px;
          font-size: 12px;
        }

        .frame-file {
          color: #6366f1;
          font-family: 'Fira Code', monospace;
        }

        .frame-line {
          color: #f59e0b;
          font-family: 'Fira Code', monospace;
        }

        .frame-content {
          color: #888;
          font-family: 'Fira Code', monospace;
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

        .analyze-button {
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

        .analyze-button:hover:not(:disabled) {
          background: #5558e3;
          transform: translateY(-1px);
        }

        .analyze-button:disabled {
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
          gap: 20px;
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
        }

        .analysis-summary {
          background: #1a1a1a;
          border-radius: 12px;
          border: 1px solid #333;
          padding: 20px;
        }

        .results-title {
          font-size: 18px;
          font-weight: 600;
          margin: 0 0 16px;
          color: #e0e0e0;
        }

        .bug-info {
          display: flex;
          gap: 24px;
          margin-bottom: 16px;
        }

        .bug-type,
        .bug-location,
        .bug-severity {
          display: flex;
          flex-direction: column;
          gap: 4px;
        }

        .bug-label {
          font-size: 11px;
          color: #666;
          text-transform: uppercase;
          letter-spacing: 0.5px;
        }

        .bug-value {
          font-size: 14px;
          font-weight: 500;
          color: #e0e0e0;
        }

        .severity-badge {
          text-transform: capitalize;
        }

        .bug-explanation {
          margin: 0;
          font-size: 14px;
          line-height: 1.6;
          color: #bbb;
        }

        .suggested-fixes {
          display: flex;
          flex-direction: column;
          gap: 16px;
        }

        .fixes-title {
          font-size: 16px;
          font-weight: 600;
          margin: 0;
          color: #e0e0e0;
        }

        .fix-card {
          background: #1a1a1a;
          border-radius: 12px;
          border: 1px solid #333;
          padding: 20px;
        }

        .fix-header {
          display: flex;
          justify-content: space-between;
          align-items: center;
          margin-bottom: 12px;
        }

        .fix-number {
          font-size: 14px;
          font-weight: 600;
          color: #6366f1;
        }

        .fix-confidence {
          font-size: 12px;
          color: #888;
          background: #2a2a2a;
          padding: 4px 8px;
          border-radius: 4px;
        }

        .fix-description {
          margin: 0 0 16px;
          font-size: 14px;
          color: #bbb;
          line-height: 1.5;
        }

        .apply-fix-button {
          display: flex;
          align-items: center;
          gap: 6px;
          margin-top: 12px;
          padding: 10px 16px;
          background: #10b981;
          border: none;
          border-radius: 6px;
          color: #fff;
          font-size: 13px;
          font-weight: 500;
          cursor: pointer;
          transition: all 0.2s ease;
        }

        .apply-fix-button:hover {
          background: #059669;
        }

        .related-issues {
          background: #1a1a1a;
          border-radius: 12px;
          border: 1px solid #333;
          padding: 20px;
        }

        .related-title {
          font-size: 16px;
          font-weight: 600;
          margin: 0 0 12px;
          color: #e0e0e0;
        }

        .related-issue {
          display: flex;
          align-items: center;
          gap: 8px;
          padding: 8px 0;
          color: #888;
          font-size: 13px;
        }

        .issue-icon {
          color: #f59e0b;
        }

        @media (max-width: 1024px) {
          .page-content {
            grid-template-columns: 1fr;
          }
        }
      `}</style>
    </div>
  );
};

export default Debugger;
