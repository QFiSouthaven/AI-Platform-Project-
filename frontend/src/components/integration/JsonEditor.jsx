import React, { useState, useEffect, useCallback } from 'react';

const JsonEditor = ({
  value = '',
  onChange,
  onValidation,
  placeholder = '{\n  "key": "value"\n}',
  readOnly = false,
  height = '300px',
  showLineNumbers = true,
  showValidation = true,
}) => {
  const [content, setContent] = useState(value);
  const [error, setError] = useState(null);
  const [lineCount, setLineCount] = useState(1);

  const validateJson = useCallback((text) => {
    if (!text.trim()) {
      setError(null);
      if (onValidation) onValidation({ valid: true, error: null });
      return true;
    }

    try {
      JSON.parse(text);
      setError(null);
      if (onValidation) onValidation({ valid: true, error: null, parsed: JSON.parse(text) });
      return true;
    } catch (e) {
      const errorMessage = e.message;
      setError(errorMessage);
      if (onValidation) onValidation({ valid: false, error: errorMessage });
      return false;
    }
  }, [onValidation]);

  useEffect(() => {
    setContent(value);
    validateJson(value);
    setLineCount(value.split('\n').length);
  }, [value, validateJson]);

  const handleChange = (e) => {
    const newValue = e.target.value;
    setContent(newValue);
    setLineCount(newValue.split('\n').length);
    validateJson(newValue);
    if (onChange) onChange(newValue);
  };

  const formatJson = () => {
    try {
      const parsed = JSON.parse(content);
      const formatted = JSON.stringify(parsed, null, 2);
      setContent(formatted);
      setLineCount(formatted.split('\n').length);
      if (onChange) onChange(formatted);
      setError(null);
    } catch (e) {
      setError(e.message);
    }
  };

  const minifyJson = () => {
    try {
      const parsed = JSON.parse(content);
      const minified = JSON.stringify(parsed);
      setContent(minified);
      setLineCount(1);
      if (onChange) onChange(minified);
      setError(null);
    } catch (e) {
      setError(e.message);
    }
  };

  const copyToClipboard = async () => {
    try {
      await navigator.clipboard.writeText(content);
    } catch (e) {
      console.error('Failed to copy:', e);
    }
  };

  const clearContent = () => {
    setContent('');
    setLineCount(1);
    setError(null);
    if (onChange) onChange('');
    if (onValidation) onValidation({ valid: true, error: null });
  };

  return (
    <div className="border border-gray-300 rounded-lg overflow-hidden">
      {/* Toolbar */}
      <div className="bg-gray-100 px-3 py-2 border-b border-gray-300 flex items-center justify-between">
        <div className="flex items-center space-x-2">
          <button
            onClick={formatJson}
            disabled={readOnly}
            className="px-2 py-1 text-xs font-medium text-gray-700 bg-white border border-gray-300 rounded hover:bg-gray-50 disabled:opacity-50 disabled:cursor-not-allowed"
          >
            Format
          </button>
          <button
            onClick={minifyJson}
            disabled={readOnly}
            className="px-2 py-1 text-xs font-medium text-gray-700 bg-white border border-gray-300 rounded hover:bg-gray-50 disabled:opacity-50 disabled:cursor-not-allowed"
          >
            Minify
          </button>
          <button
            onClick={copyToClipboard}
            className="px-2 py-1 text-xs font-medium text-gray-700 bg-white border border-gray-300 rounded hover:bg-gray-50"
          >
            Copy
          </button>
          {!readOnly && (
            <button
              onClick={clearContent}
              className="px-2 py-1 text-xs font-medium text-red-700 bg-white border border-gray-300 rounded hover:bg-red-50"
            >
              Clear
            </button>
          )}
        </div>
        <div className="text-xs text-gray-500">
          {lineCount} line{lineCount !== 1 ? 's' : ''}
        </div>
      </div>

      {/* Editor */}
      <div className="relative" style={{ height }}>
        <div className="absolute inset-0 flex">
          {showLineNumbers && (
            <div className="bg-gray-50 text-gray-400 text-sm font-mono py-3 px-2 text-right select-none border-r border-gray-200 overflow-hidden">
              {Array.from({ length: lineCount }, (_, i) => (
                <div key={i + 1} className="leading-6">
                  {i + 1}
                </div>
              ))}
            </div>
          )}
          <textarea
            value={content}
            onChange={handleChange}
            placeholder={placeholder}
            readOnly={readOnly}
            spellCheck={false}
            className={`flex-1 p-3 text-sm font-mono leading-6 resize-none focus:outline-none ${
              readOnly ? 'bg-gray-50 cursor-not-allowed' : 'bg-white'
            } ${error ? 'text-red-600' : 'text-gray-900'}`}
            style={{ tabSize: 2 }}
          />
        </div>
      </div>

      {/* Validation Status */}
      {showValidation && (
        <div
          className={`px-3 py-2 text-xs border-t ${
            error
              ? 'bg-red-50 text-red-700 border-red-200'
              : content.trim()
              ? 'bg-green-50 text-green-700 border-green-200'
              : 'bg-gray-50 text-gray-500 border-gray-200'
          }`}
        >
          {error ? (
            <div className="flex items-center">
              <svg
                className="w-4 h-4 mr-1.5"
                fill="currentColor"
                viewBox="0 0 20 20"
              >
                <path
                  fillRule="evenodd"
                  d="M10 18a8 8 0 100-16 8 8 0 000 16zM8.707 7.293a1 1 0 00-1.414 1.414L8.586 10l-1.293 1.293a1 1 0 101.414 1.414L10 11.414l1.293 1.293a1 1 0 001.414-1.414L11.414 10l1.293-1.293a1 1 0 00-1.414-1.414L10 8.586 8.707 7.293z"
                  clipRule="evenodd"
                />
              </svg>
              {error}
            </div>
          ) : content.trim() ? (
            <div className="flex items-center">
              <svg
                className="w-4 h-4 mr-1.5"
                fill="currentColor"
                viewBox="0 0 20 20"
              >
                <path
                  fillRule="evenodd"
                  d="M10 18a8 8 0 100-16 8 8 0 000 16zm3.707-9.293a1 1 0 00-1.414-1.414L9 10.586 7.707 9.293a1 1 0 00-1.414 1.414l2 2a1 1 0 001.414 0l4-4z"
                  clipRule="evenodd"
                />
              </svg>
              Valid JSON
            </div>
          ) : (
            'Enter JSON to validate'
          )}
        </div>
      )}
    </div>
  );
};

export default JsonEditor;
