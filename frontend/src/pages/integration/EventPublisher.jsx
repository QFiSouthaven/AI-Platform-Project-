import React, { useState, useEffect } from 'react';
import JsonEditor from '../../components/integration/JsonEditor';
import { publishEvent, getKafkaTopics, validateEventSchema } from '../../services/integrationService';

const EventPublisher = () => {
  const [topics, setTopics] = useState([]);
  const [selectedTopic, setSelectedTopic] = useState('');
  const [message, setMessage] = useState('{\n  "key": "value"\n}');
  const [isValid, setIsValid] = useState(false);
  const [validationResult, setValidationResult] = useState(null);
  const [publishing, setPublishing] = useState(false);
  const [response, setResponse] = useState(null);
  const [history, setHistory] = useState([]);
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    fetchTopics();
  }, []);

  const fetchTopics = async () => {
    try {
      setLoading(true);
      const data = await getKafkaTopics();
      setTopics(data.data || []);
      if (data.data && data.data.length > 0) {
        setSelectedTopic(data.data[0].name);
      }
    } catch (error) {
      console.error('Failed to fetch topics:', error);
    } finally {
      setLoading(false);
    }
  };

  const handleValidation = (result) => {
    setIsValid(result.valid);
    if (!result.valid) {
      setValidationResult({ status: 'error', message: result.error });
    } else {
      setValidationResult(null);
    }
  };

  const handleSchemaValidation = async () => {
    if (!selectedTopic || !message.trim()) return;

    try {
      const result = await validateEventSchema(selectedTopic, JSON.parse(message));
      setValidationResult({
        status: result.data?.valid ? 'success' : 'error',
        message: result.data?.valid ? 'Schema validation passed' : result.data?.errors?.join(', ') || 'Validation failed',
      });
    } catch (error) {
      setValidationResult({
        status: 'error',
        message: error.response?.data?.message || 'Schema validation failed',
      });
    }
  };

  const handlePublish = async () => {
    if (!selectedTopic || !isValid) return;

    try {
      setPublishing(true);
      setResponse(null);

      const parsedMessage = JSON.parse(message);
      const result = await publishEvent(selectedTopic, parsedMessage, {
        correlation_id: crypto.randomUUID(),
        source: 'event-publisher-ui',
      });

      setResponse({
        status: 'success',
        data: result.data,
        timestamp: new Date().toISOString(),
      });

      // Add to history
      setHistory((prev) => [
        {
          id: Date.now(),
          topic: selectedTopic,
          message: parsedMessage,
          timestamp: new Date().toISOString(),
          status: 'success',
        },
        ...prev.slice(0, 9),
      ]);
    } catch (error) {
      setResponse({
        status: 'error',
        message: error.response?.data?.message || error.message,
        timestamp: new Date().toISOString(),
      });

      setHistory((prev) => [
        {
          id: Date.now(),
          topic: selectedTopic,
          message: JSON.parse(message),
          timestamp: new Date().toISOString(),
          status: 'error',
          error: error.response?.data?.message || error.message,
        },
        ...prev.slice(0, 9),
      ]);
    } finally {
      setPublishing(false);
    }
  };

  const loadFromHistory = (item) => {
    setSelectedTopic(item.topic);
    setMessage(JSON.stringify(item.message, null, 2));
  };

  const loadTemplate = (template) => {
    const templates = {
      user: {
        schema_version: '1.0',
        event_type: 'user.created',
        data: {
          user_id: 'user-123',
          email: 'user@example.com',
          name: 'John Doe',
        },
      },
      workflow: {
        schema_version: '1.0',
        event_type: 'workflow.started',
        data: {
          workflow_id: 'wf-456',
          name: 'Data Processing',
          steps: 5,
        },
      },
      processing: {
        schema_version: '1.0',
        event_type: 'processing.completed',
        data: {
          task_id: 'task-789',
          result: 'success',
          duration_ms: 1234,
        },
      },
      model: {
        schema_version: '1.0',
        event_type: 'model.deployed',
        data: {
          model_id: 'model-abc',
          version: '1.0.0',
          endpoint: '/api/predict',
        },
      },
    };

    if (templates[template]) {
      setMessage(JSON.stringify(templates[template], null, 2));
    }
  };

  return (
    <div className="p-6 space-y-6">
      {/* Header */}
      <div>
        <h1 className="text-2xl font-bold text-gray-900">Event Publisher</h1>
        <p className="text-sm text-gray-500">Publish events to Kafka topics</p>
      </div>

      <div className="grid grid-cols-1 lg:grid-cols-3 gap-6">
        {/* Publisher Form */}
        <div className="lg:col-span-2 space-y-6">
          {/* Topic Selector */}
          <div className="bg-white rounded-lg shadow-md p-6">
            <label className="block text-sm font-medium text-gray-700 mb-2">
              Select Topic
            </label>
            {loading ? (
              <div className="animate-pulse h-10 bg-gray-200 rounded" />
            ) : (
              <select
                value={selectedTopic}
                onChange={(e) => setSelectedTopic(e.target.value)}
                className="w-full px-3 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-blue-500 focus:border-blue-500"
              >
                {topics.map((topic) => (
                  <option key={topic.name} value={topic.name}>
                    {topic.name} ({topic.partitions} partitions)
                  </option>
                ))}
              </select>
            )}
          </div>

          {/* Templates */}
          <div className="bg-white rounded-lg shadow-md p-6">
            <label className="block text-sm font-medium text-gray-700 mb-2">
              Quick Templates
            </label>
            <div className="flex flex-wrap gap-2">
              <button
                onClick={() => loadTemplate('user')}
                className="px-3 py-1.5 text-sm font-medium text-blue-700 bg-blue-100 rounded-full hover:bg-blue-200"
              >
                user.*
              </button>
              <button
                onClick={() => loadTemplate('workflow')}
                className="px-3 py-1.5 text-sm font-medium text-green-700 bg-green-100 rounded-full hover:bg-green-200"
              >
                workflow.*
              </button>
              <button
                onClick={() => loadTemplate('processing')}
                className="px-3 py-1.5 text-sm font-medium text-yellow-700 bg-yellow-100 rounded-full hover:bg-yellow-200"
              >
                processing.*
              </button>
              <button
                onClick={() => loadTemplate('model')}
                className="px-3 py-1.5 text-sm font-medium text-purple-700 bg-purple-100 rounded-full hover:bg-purple-200"
              >
                model.*
              </button>
            </div>
          </div>

          {/* JSON Editor */}
          <div className="bg-white rounded-lg shadow-md p-6">
            <label className="block text-sm font-medium text-gray-700 mb-2">
              Message Payload
            </label>
            <JsonEditor
              value={message}
              onChange={setMessage}
              onValidation={handleValidation}
              height="300px"
            />
          </div>

          {/* Validation Result */}
          {validationResult && (
            <div
              className={`p-4 rounded-lg ${
                validationResult.status === 'success'
                  ? 'bg-green-50 border border-green-200'
                  : 'bg-red-50 border border-red-200'
              }`}
            >
              <div className="flex items-center">
                {validationResult.status === 'success' ? (
                  <svg className="w-5 h-5 text-green-500 mr-2" fill="currentColor" viewBox="0 0 20 20">
                    <path fillRule="evenodd" d="M10 18a8 8 0 100-16 8 8 0 000 16zm3.707-9.293a1 1 0 00-1.414-1.414L9 10.586 7.707 9.293a1 1 0 00-1.414 1.414l2 2a1 1 0 001.414 0l4-4z" clipRule="evenodd" />
                  </svg>
                ) : (
                  <svg className="w-5 h-5 text-red-500 mr-2" fill="currentColor" viewBox="0 0 20 20">
                    <path fillRule="evenodd" d="M10 18a8 8 0 100-16 8 8 0 000 16zM8.707 7.293a1 1 0 00-1.414 1.414L8.586 10l-1.293 1.293a1 1 0 101.414 1.414L10 11.414l1.293 1.293a1 1 0 001.414-1.414L11.414 10l1.293-1.293a1 1 0 00-1.414-1.414L10 8.586 8.707 7.293z" clipRule="evenodd" />
                  </svg>
                )}
                <span className={validationResult.status === 'success' ? 'text-green-800' : 'text-red-800'}>
                  {validationResult.message}
                </span>
              </div>
            </div>
          )}

          {/* Actions */}
          <div className="flex items-center space-x-3">
            <button
              onClick={handleSchemaValidation}
              disabled={!isValid || !selectedTopic}
              className="px-4 py-2 text-sm font-medium text-gray-700 bg-white border border-gray-300 rounded-lg hover:bg-gray-50 disabled:opacity-50 disabled:cursor-not-allowed"
            >
              Validate Schema
            </button>
            <button
              onClick={handlePublish}
              disabled={!isValid || !selectedTopic || publishing}
              className="px-6 py-2 text-sm font-medium text-white bg-blue-600 rounded-lg hover:bg-blue-700 disabled:opacity-50 disabled:cursor-not-allowed flex items-center"
            >
              {publishing ? (
                <>
                  <svg className="animate-spin -ml-1 mr-2 h-4 w-4 text-white" fill="none" viewBox="0 0 24 24">
                    <circle className="opacity-25" cx="12" cy="12" r="10" stroke="currentColor" strokeWidth="4" />
                    <path className="opacity-75" fill="currentColor" d="M4 12a8 8 0 018-8V0C5.373 0 0 5.373 0 12h4zm2 5.291A7.962 7.962 0 014 12H0c0 3.042 1.135 5.824 3 7.938l3-2.647z" />
                  </svg>
                  Publishing...
                </>
              ) : (
                'Publish Event'
              )}
            </button>
          </div>

          {/* Response */}
          {response && (
            <div className="bg-white rounded-lg shadow-md p-6">
              <h3 className="text-sm font-medium text-gray-700 mb-3">Response</h3>
              <div
                className={`p-4 rounded-lg ${
                  response.status === 'success'
                    ? 'bg-green-50 border border-green-200'
                    : 'bg-red-50 border border-red-200'
                }`}
              >
                {response.status === 'success' ? (
                  <div>
                    <div className="flex items-center mb-2">
                      <svg className="w-5 h-5 text-green-500 mr-2" fill="currentColor" viewBox="0 0 20 20">
                        <path fillRule="evenodd" d="M10 18a8 8 0 100-16 8 8 0 000 16zm3.707-9.293a1 1 0 00-1.414-1.414L9 10.586 7.707 9.293a1 1 0 00-1.414 1.414l2 2a1 1 0 001.414 0l4-4z" clipRule="evenodd" />
                      </svg>
                      <span className="text-green-800 font-medium">Event published successfully</span>
                    </div>
                    <pre className="text-sm text-gray-700 overflow-x-auto">
                      {JSON.stringify(response.data, null, 2)}
                    </pre>
                  </div>
                ) : (
                  <div className="flex items-center">
                    <svg className="w-5 h-5 text-red-500 mr-2" fill="currentColor" viewBox="0 0 20 20">
                      <path fillRule="evenodd" d="M10 18a8 8 0 100-16 8 8 0 000 16zM8.707 7.293a1 1 0 00-1.414 1.414L8.586 10l-1.293 1.293a1 1 0 101.414 1.414L10 11.414l1.293 1.293a1 1 0 001.414-1.414L11.414 10l1.293-1.293a1 1 0 00-1.414-1.414L10 8.586 8.707 7.293z" clipRule="evenodd" />
                    </svg>
                    <span className="text-red-800">{response.message}</span>
                  </div>
                )}
                <p className="mt-2 text-xs text-gray-500">{response.timestamp}</p>
              </div>
            </div>
          )}
        </div>

        {/* History Sidebar */}
        <div className="space-y-6">
          <div className="bg-white rounded-lg shadow-md p-6">
            <h3 className="text-lg font-semibold text-gray-900 mb-4">Recent History</h3>
            {history.length === 0 ? (
              <p className="text-sm text-gray-500 text-center py-4">
                No events published yet
              </p>
            ) : (
              <div className="space-y-3">
                {history.map((item) => (
                  <div
                    key={item.id}
                    onClick={() => loadFromHistory(item)}
                    className="p-3 border border-gray-200 rounded-lg hover:bg-gray-50 cursor-pointer transition-colors"
                  >
                    <div className="flex items-center justify-between mb-1">
                      <span className="text-sm font-medium text-gray-900 truncate">
                        {item.topic}
                      </span>
                      <span
                        className={`w-2 h-2 rounded-full ${
                          item.status === 'success' ? 'bg-green-500' : 'bg-red-500'
                        }`}
                      />
                    </div>
                    <p className="text-xs text-gray-500">
                      {new Date(item.timestamp).toLocaleTimeString()}
                    </p>
                    {item.error && (
                      <p className="text-xs text-red-500 mt-1 truncate">{item.error}</p>
                    )}
                  </div>
                ))}
              </div>
            )}
          </div>

          {/* Tips */}
          <div className="bg-blue-50 rounded-lg p-4">
            <h4 className="text-sm font-medium text-blue-800 mb-2">Tips</h4>
            <ul className="text-xs text-blue-700 space-y-1">
              <li>Use templates to quickly create common event types</li>
              <li>Validate schema before publishing to ensure compatibility</li>
              <li>Click history items to reload previous messages</li>
              <li>All events include automatic correlation IDs</li>
            </ul>
          </div>
        </div>
      </div>
    </div>
  );
};

export default EventPublisher;
