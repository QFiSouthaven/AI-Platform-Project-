import React, { useEffect, useRef, useState } from 'react';
import Prism from 'prismjs';
import 'prismjs/themes/prism-tomorrow.css';
import 'prismjs/components/prism-python';
import 'prismjs/components/prism-javascript';
import 'prismjs/components/prism-typescript';
import 'prismjs/components/prism-java';
import 'prismjs/components/prism-go';
import 'prismjs/components/prism-rust';

const CodeEditor = ({
  code,
  onChange,
  language = 'python',
  readOnly = false,
  showLineNumbers = true,
  placeholder = 'Enter your code here...',
  height = '400px',
  title = '',
}) => {
  const [copied, setCopied] = useState(false);
  const textareaRef = useRef(null);
  const preRef = useRef(null);

  useEffect(() => {
    if (preRef.current) {
      Prism.highlightElement(preRef.current.querySelector('code'));
    }
  }, [code, language]);

  const handleCopy = async () => {
    try {
      await navigator.clipboard.writeText(code);
      setCopied(true);
      setTimeout(() => setCopied(false), 2000);
    } catch (err) {
      console.error('Failed to copy:', err);
    }
  };

  const handleScroll = (e) => {
    if (preRef.current) {
      preRef.current.scrollTop = e.target.scrollTop;
      preRef.current.scrollLeft = e.target.scrollLeft;
    }
  };

  const getLanguageLabel = (lang) => {
    const labels = {
      python: 'Python',
      javascript: 'JavaScript',
      typescript: 'TypeScript',
      java: 'Java',
      go: 'Go',
      rust: 'Rust',
    };
    return labels[lang] || lang;
  };

  const lineNumbers = code.split('\n').map((_, i) => i + 1);

  return (
    <div className="code-editor-container" style={{ height }}>
      <div className="code-editor-header">
        {title && <span className="code-editor-title">{title}</span>}
        <div className="code-editor-actions">
          <span className="language-indicator">{getLanguageLabel(language)}</span>
          <button
            className={`copy-button ${copied ? 'copied' : ''}`}
            onClick={handleCopy}
            title="Copy to clipboard"
          >
            {copied ? (
              <>
                <svg width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2">
                  <polyline points="20 6 9 17 4 12"></polyline>
                </svg>
                Copied!
              </>
            ) : (
              <>
                <svg width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2">
                  <rect x="9" y="9" width="13" height="13" rx="2" ry="2"></rect>
                  <path d="M5 15H4a2 2 0 0 1-2-2V4a2 2 0 0 1 2-2h9a2 2 0 0 1 2 2v1"></path>
                </svg>
                Copy
              </>
            )}
          </button>
        </div>
      </div>
      <div className="code-editor-body">
        {showLineNumbers && (
          <div className="line-numbers">
            {lineNumbers.map((num) => (
              <span key={num}>{num}</span>
            ))}
          </div>
        )}
        <div className="code-content">
          {!readOnly && (
            <textarea
              ref={textareaRef}
              value={code}
              onChange={(e) => onChange && onChange(e.target.value)}
              onScroll={handleScroll}
              placeholder={placeholder}
              spellCheck="false"
              className="code-input"
            />
          )}
          <pre ref={preRef} className={`code-highlight ${readOnly ? 'read-only' : ''}`}>
            <code className={`language-${language}`}>
              {code || placeholder}
            </code>
          </pre>
        </div>
      </div>

      <style jsx>{`
        .code-editor-container {
          display: flex;
          flex-direction: column;
          background: #1e1e1e;
          border-radius: 8px;
          overflow: hidden;
          border: 1px solid #333;
        }

        .code-editor-header {
          display: flex;
          justify-content: space-between;
          align-items: center;
          padding: 8px 12px;
          background: #2d2d2d;
          border-bottom: 1px solid #333;
        }

        .code-editor-title {
          font-size: 14px;
          font-weight: 500;
          color: #e0e0e0;
        }

        .code-editor-actions {
          display: flex;
          align-items: center;
          gap: 12px;
        }

        .language-indicator {
          font-size: 12px;
          color: #888;
          background: #3a3a3a;
          padding: 4px 8px;
          border-radius: 4px;
        }

        .copy-button {
          display: flex;
          align-items: center;
          gap: 4px;
          padding: 4px 8px;
          background: #3a3a3a;
          border: none;
          border-radius: 4px;
          color: #e0e0e0;
          font-size: 12px;
          cursor: pointer;
          transition: all 0.2s ease;
        }

        .copy-button:hover {
          background: #4a4a4a;
        }

        .copy-button.copied {
          background: #2e7d32;
          color: #fff;
        }

        .code-editor-body {
          display: flex;
          flex: 1;
          overflow: auto;
          position: relative;
        }

        .line-numbers {
          display: flex;
          flex-direction: column;
          padding: 12px 8px;
          background: #252525;
          color: #666;
          font-family: 'Fira Code', 'Consolas', monospace;
          font-size: 14px;
          line-height: 1.5;
          text-align: right;
          user-select: none;
          border-right: 1px solid #333;
          min-width: 40px;
        }

        .line-numbers span {
          padding: 0 4px;
        }

        .code-content {
          flex: 1;
          position: relative;
          overflow: auto;
        }

        .code-input {
          position: absolute;
          top: 0;
          left: 0;
          width: 100%;
          height: 100%;
          padding: 12px;
          background: transparent;
          border: none;
          outline: none;
          resize: none;
          font-family: 'Fira Code', 'Consolas', monospace;
          font-size: 14px;
          line-height: 1.5;
          color: transparent;
          caret-color: #fff;
          white-space: pre;
          overflow: auto;
          z-index: 1;
        }

        .code-highlight {
          margin: 0;
          padding: 12px;
          font-family: 'Fira Code', 'Consolas', monospace;
          font-size: 14px;
          line-height: 1.5;
          white-space: pre;
          overflow: auto;
          pointer-events: none;
        }

        .code-highlight.read-only {
          pointer-events: auto;
        }

        .code-highlight code {
          font-family: inherit;
          background: transparent;
        }

        /* Prism theme overrides for dark theme */
        :global(.token.comment),
        :global(.token.prolog),
        :global(.token.doctype),
        :global(.token.cdata) {
          color: #6a9955;
        }

        :global(.token.punctuation) {
          color: #d4d4d4;
        }

        :global(.token.property),
        :global(.token.tag),
        :global(.token.boolean),
        :global(.token.number),
        :global(.token.constant),
        :global(.token.symbol),
        :global(.token.deleted) {
          color: #b5cea8;
        }

        :global(.token.selector),
        :global(.token.attr-name),
        :global(.token.string),
        :global(.token.char),
        :global(.token.builtin),
        :global(.token.inserted) {
          color: #ce9178;
        }

        :global(.token.operator),
        :global(.token.entity),
        :global(.token.url),
        :global(.language-css .token.string),
        :global(.style .token.string) {
          color: #d4d4d4;
        }

        :global(.token.atrule),
        :global(.token.attr-value),
        :global(.token.keyword) {
          color: #569cd6;
        }

        :global(.token.function),
        :global(.token.class-name) {
          color: #dcdcaa;
        }

        :global(.token.regex),
        :global(.token.important),
        :global(.token.variable) {
          color: #d16969;
        }
      `}</style>
    </div>
  );
};

export default CodeEditor;
