import React, { useState, useEffect } from 'react';
import { useParams } from 'react-router-dom';
import { TASK_TYPES } from '../../components/workflows/TaskNode';
import workflowService from '../../services/workflowService';

/**
 * TaskDetail - Task configuration and detail page
 */
const TaskDetail = () => {
  const { taskId, workflowId } = useParams();

  const [task, setTask] = useState(null);
  const [loading, setLoading] = useState(true);
  const [saving, setSaving] = useState(false);
  const [hasChanges, setHasChanges] = useState(false);

  useEffect(() => {
    if (taskId) {
      loadTask();
    }
  }, [taskId]);

  const loadTask = async () => {
    try {
      setLoading(true);
      const response = await workflowService.getTask(taskId);
      setTask(response.data || response);
    } catch (err) {
      alert(`Failed to load task: ${err.message}`);
    } finally {
      setLoading(false);
    }
  };

  const handleSave = async () => {
    try {
      setSaving(true);
      await workflowService.updateTask(taskId, task);
      setHasChanges(false);
      alert('Task saved successfully!');
    } catch (err) {
      alert(`Failed to save task: ${err.message}`);
    } finally {
      setSaving(false);
    }
  };

  const updateTask = (field, value) => {
    setTask(prev => ({ ...prev, [field]: value }));
    setHasChanges(true);
  };

  const updateConfig = (field, value) => {
    setTask(prev => ({
      ...prev,
      config: { ...prev.config, [field]: value }
    }));
    setHasChanges(true);
  };

  // Styles
  const containerStyle = {
    padding: '24px',
    maxWidth: '800px',
    margin: '0 auto',
  };

  const headerStyle = {
    marginBottom: '24px',
  };

  const breadcrumbStyle = {
    fontSize: '13px',
    color: '#6b7280',
    marginBottom: '8px',
  };

  const breadcrumbLinkStyle = {
    color: '#3b82f6',
    textDecoration: 'none',
  };

  const titleStyle = {
    fontSize: '24px',
    fontWeight: '700',
    color: '#111827',
    margin: '0 0 8px 0',
    display: 'flex',
    alignItems: 'center',
    gap: '12px',
  };

  const cardStyle = {
    backgroundColor: '#ffffff',
    borderRadius: '8px',
    border: '1px solid #e5e7eb',
    marginBottom: '24px',
  };

  const cardHeaderStyle = {
    padding: '16px',
    borderBottom: '1px solid #e5e7eb',
    fontSize: '16px',
    fontWeight: '600',
    color: '#111827',
  };

  const cardContentStyle = {
    padding: '16px',
  };

  const formGroupStyle = {
    marginBottom: '20px',
  };

  const labelStyle = {
    display: 'block',
    fontSize: '14px',
    fontWeight: '500',
    color: '#374151',
    marginBottom: '6px',
  };

  const inputStyle = {
    width: '100%',
    padding: '10px 12px',
    border: '1px solid #e5e7eb',
    borderRadius: '6px',
    fontSize: '14px',
    boxSizing: 'border-box',
  };

  const selectStyle = {
    ...inputStyle,
    cursor: 'pointer',
  };

  const textareaStyle = {
    ...inputStyle,
    minHeight: '100px',
    resize: 'vertical',
  };

  const helpTextStyle = {
    fontSize: '12px',
    color: '#6b7280',
    marginTop: '4px',
  };

  const rowStyle = {
    display: 'grid',
    gridTemplateColumns: '1fr 1fr',
    gap: '16px',
  };

  const actionsStyle = {
    display: 'flex',
    justifyContent: 'flex-end',
    gap: '12px',
    paddingTop: '16px',
    borderTop: '1px solid #e5e7eb',
    marginTop: '24px',
  };

  const buttonStyle = {
    padding: '10px 20px',
    borderRadius: '6px',
    border: '1px solid #e5e7eb',
    backgroundColor: '#ffffff',
    fontSize: '14px',
    fontWeight: '500',
    cursor: 'pointer',
  };

  const primaryButtonStyle = {
    ...buttonStyle,
    backgroundColor: '#3b82f6',
    borderColor: '#3b82f6',
    color: '#ffffff',
  };

  const disabledButtonStyle = {
    ...primaryButtonStyle,
    opacity: 0.6,
    cursor: 'not-allowed',
  };

  const taskTypeIconStyle = (color) => ({
    width: '40px',
    height: '40px',
    borderRadius: '8px',
    backgroundColor: `${color}20`,
    color: color,
    display: 'flex',
    alignItems: 'center',
    justifyContent: 'center',
  });

  const codeEditorStyle = {
    fontFamily: 'monospace',
    fontSize: '13px',
    backgroundColor: '#f9fafb',
  };

  const loadingStyle = {
    display: 'flex',
    justifyContent: 'center',
    alignItems: 'center',
    padding: '60px',
    color: '#6b7280',
  };

  if (loading) {
    return (
      <div style={loadingStyle}>
        <svg width="24" height="24" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" style={{ animation: 'spin 1s linear infinite' }}>
          <path d="M21 12a9 9 0 1 1-6.219-8.56" />
        </svg>
        <span style={{ marginLeft: '8px' }}>Loading task...</span>
      </div>
    );
  }

  if (!task) {
    return (
      <div style={containerStyle}>
        <p>Task not found</p>
      </div>
    );
  }

  const taskType = TASK_TYPES[task.type] || TASK_TYPES.code_generation;

  return (
    <div style={containerStyle}>
      {/* Header */}
      <div style={headerStyle}>
        <div style={breadcrumbStyle}>
          <a href="/workflows" style={breadcrumbLinkStyle}>Workflows</a>
          {' / '}
          {workflowId && (
            <>
              <a href={`/workflows/${workflowId}`} style={breadcrumbLinkStyle}>
                {task.workflow_name || 'Workflow'}
              </a>
              {' / '}
            </>
          )}
          Task Configuration
        </div>
        <div style={titleStyle}>
          <div style={taskTypeIconStyle(taskType.color)}>
            {taskType.icon}
          </div>
          {task.name}
        </div>
      </div>

      {/* Basic Information */}
      <div style={cardStyle}>
        <div style={cardHeaderStyle}>Basic Information</div>
        <div style={cardContentStyle}>
          <div style={formGroupStyle}>
            <label style={labelStyle}>Task Name</label>
            <input
              type="text"
              style={inputStyle}
              value={task.name}
              onChange={(e) => updateTask('name', e.target.value)}
            />
          </div>

          <div style={formGroupStyle}>
            <label style={labelStyle}>Task Type</label>
            <select
              style={selectStyle}
              value={task.type}
              onChange={(e) => updateTask('type', e.target.value)}
            >
              {Object.entries(TASK_TYPES).map(([key, type]) => (
                <option key={key} value={key}>{type.label}</option>
              ))}
            </select>
          </div>

          <div style={formGroupStyle}>
            <label style={labelStyle}>Description</label>
            <textarea
              style={textareaStyle}
              value={task.description || ''}
              onChange={(e) => updateTask('description', e.target.value)}
              placeholder="Describe what this task does..."
            />
          </div>
        </div>
      </div>

      {/* Execution Settings */}
      <div style={cardStyle}>
        <div style={cardHeaderStyle}>Execution Settings</div>
        <div style={cardContentStyle}>
          <div style={rowStyle}>
            <div style={formGroupStyle}>
              <label style={labelStyle}>Timeout (seconds)</label>
              <input
                type="number"
                style={inputStyle}
                value={task.config?.timeout || 300}
                onChange={(e) => updateConfig('timeout', parseInt(e.target.value) || 300)}
                min="0"
              />
              <div style={helpTextStyle}>Maximum time allowed for task execution</div>
            </div>

            <div style={formGroupStyle}>
              <label style={labelStyle}>Retry Count</label>
              <input
                type="number"
                style={inputStyle}
                value={task.config?.retryCount || 0}
                onChange={(e) => updateConfig('retryCount', parseInt(e.target.value) || 0)}
                min="0"
                max="10"
              />
              <div style={helpTextStyle}>Number of retries on failure (0-10)</div>
            </div>
          </div>

          <div style={rowStyle}>
            <div style={formGroupStyle}>
              <label style={labelStyle}>Retry Delay (seconds)</label>
              <input
                type="number"
                style={inputStyle}
                value={task.config?.retryDelay || 30}
                onChange={(e) => updateConfig('retryDelay', parseInt(e.target.value) || 30)}
                min="0"
              />
              <div style={helpTextStyle}>Delay between retry attempts</div>
            </div>

            <div style={formGroupStyle}>
              <label style={labelStyle}>Priority</label>
              <select
                style={selectStyle}
                value={task.config?.priority || 'normal'}
                onChange={(e) => updateConfig('priority', e.target.value)}
              >
                <option value="low">Low</option>
                <option value="normal">Normal</option>
                <option value="high">High</option>
              </select>
              <div style={helpTextStyle}>Execution priority level</div>
            </div>
          </div>

          <div style={formGroupStyle}>
            <label style={{ ...labelStyle, display: 'flex', alignItems: 'center', gap: '8px' }}>
              <input
                type="checkbox"
                checked={task.config?.continueOnError || false}
                onChange={(e) => updateConfig('continueOnError', e.target.checked)}
              />
              Continue workflow on task failure
            </label>
          </div>
        </div>
      </div>

      {/* Task-specific Configuration */}
      {task.type === 'code_generation' && (
        <div style={cardStyle}>
          <div style={cardHeaderStyle}>Code Generation Settings</div>
          <div style={cardContentStyle}>
            <div style={formGroupStyle}>
              <label style={labelStyle}>Model</label>
              <select
                style={selectStyle}
                value={task.config?.model || 'starcoder'}
                onChange={(e) => updateConfig('model', e.target.value)}
              >
                <option value="starcoder">StarCoder</option>
                <option value="codellama">CodeLlama</option>
                <option value="gpt-4">GPT-4</option>
              </select>
            </div>

            <div style={formGroupStyle}>
              <label style={labelStyle}>Prompt Template</label>
              <textarea
                style={{ ...textareaStyle, ...codeEditorStyle }}
                value={task.config?.promptTemplate || ''}
                onChange={(e) => updateConfig('promptTemplate', e.target.value)}
                placeholder="Enter your prompt template..."
              />
            </div>

            <div style={rowStyle}>
              <div style={formGroupStyle}>
                <label style={labelStyle}>Temperature</label>
                <input
                  type="number"
                  style={inputStyle}
                  value={task.config?.temperature || 0.7}
                  onChange={(e) => updateConfig('temperature', parseFloat(e.target.value) || 0.7)}
                  min="0"
                  max="2"
                  step="0.1"
                />
              </div>

              <div style={formGroupStyle}>
                <label style={labelStyle}>Max Tokens</label>
                <input
                  type="number"
                  style={inputStyle}
                  value={task.config?.maxTokens || 2048}
                  onChange={(e) => updateConfig('maxTokens', parseInt(e.target.value) || 2048)}
                  min="1"
                />
              </div>
            </div>
          </div>
        </div>
      )}

      {task.type === 'api_call' && (
        <div style={cardStyle}>
          <div style={cardHeaderStyle}>API Call Settings</div>
          <div style={cardContentStyle}>
            <div style={formGroupStyle}>
              <label style={labelStyle}>URL</label>
              <input
                type="text"
                style={inputStyle}
                value={task.config?.url || ''}
                onChange={(e) => updateConfig('url', e.target.value)}
                placeholder="https://api.example.com/endpoint"
              />
            </div>

            <div style={formGroupStyle}>
              <label style={labelStyle}>Method</label>
              <select
                style={selectStyle}
                value={task.config?.method || 'GET'}
                onChange={(e) => updateConfig('method', e.target.value)}
              >
                <option value="GET">GET</option>
                <option value="POST">POST</option>
                <option value="PUT">PUT</option>
                <option value="DELETE">DELETE</option>
                <option value="PATCH">PATCH</option>
              </select>
            </div>

            <div style={formGroupStyle}>
              <label style={labelStyle}>Headers (JSON)</label>
              <textarea
                style={{ ...textareaStyle, ...codeEditorStyle }}
                value={task.config?.headers || '{}'}
                onChange={(e) => updateConfig('headers', e.target.value)}
                placeholder='{"Content-Type": "application/json"}'
              />
            </div>

            <div style={formGroupStyle}>
              <label style={labelStyle}>Body (JSON)</label>
              <textarea
                style={{ ...textareaStyle, ...codeEditorStyle }}
                value={task.config?.body || ''}
                onChange={(e) => updateConfig('body', e.target.value)}
                placeholder='{"key": "value"}'
              />
            </div>
          </div>
        </div>
      )}

      {task.type === 'data_processing' && (
        <div style={cardStyle}>
          <div style={cardHeaderStyle}>Data Processing Settings</div>
          <div style={cardContentStyle}>
            <div style={formGroupStyle}>
              <label style={labelStyle}>Input Source</label>
              <select
                style={selectStyle}
                value={task.config?.inputSource || 'previous_task'}
                onChange={(e) => updateConfig('inputSource', e.target.value)}
              >
                <option value="previous_task">Previous Task Output</option>
                <option value="database">Database Query</option>
                <option value="file">File Input</option>
                <option value="api">API Endpoint</option>
              </select>
            </div>

            <div style={formGroupStyle}>
              <label style={labelStyle}>Transformation Script</label>
              <textarea
                style={{ ...textareaStyle, ...codeEditorStyle, minHeight: '150px' }}
                value={task.config?.script || ''}
                onChange={(e) => updateConfig('script', e.target.value)}
                placeholder="# Python script for data transformation"
              />
            </div>

            <div style={formGroupStyle}>
              <label style={labelStyle}>Output Format</label>
              <select
                style={selectStyle}
                value={task.config?.outputFormat || 'json'}
                onChange={(e) => updateConfig('outputFormat', e.target.value)}
              >
                <option value="json">JSON</option>
                <option value="csv">CSV</option>
                <option value="xml">XML</option>
                <option value="parquet">Parquet</option>
              </select>
            </div>
          </div>
        </div>
      )}

      {task.type === 'conditional' && (
        <div style={cardStyle}>
          <div style={cardHeaderStyle}>Conditional Settings</div>
          <div style={cardContentStyle}>
            <div style={formGroupStyle}>
              <label style={labelStyle}>Condition Expression</label>
              <textarea
                style={{ ...textareaStyle, ...codeEditorStyle }}
                value={task.config?.condition || ''}
                onChange={(e) => updateConfig('condition', e.target.value)}
                placeholder="result.status == 'success' and result.count > 0"
              />
              <div style={helpTextStyle}>
                Python expression that evaluates to True or False
              </div>
            </div>

            <div style={formGroupStyle}>
              <label style={labelStyle}>True Branch Task</label>
              <input
                type="text"
                style={inputStyle}
                value={task.config?.trueBranch || ''}
                onChange={(e) => updateConfig('trueBranch', e.target.value)}
                placeholder="Task ID to execute if condition is true"
              />
            </div>

            <div style={formGroupStyle}>
              <label style={labelStyle}>False Branch Task</label>
              <input
                type="text"
                style={inputStyle}
                value={task.config?.falseBranch || ''}
                onChange={(e) => updateConfig('falseBranch', e.target.value)}
                placeholder="Task ID to execute if condition is false"
              />
            </div>
          </div>
        </div>
      )}

      {task.type === 'parallel' && (
        <div style={cardStyle}>
          <div style={cardHeaderStyle}>Parallel Execution Settings</div>
          <div style={cardContentStyle}>
            <div style={formGroupStyle}>
              <label style={labelStyle}>Child Tasks (comma-separated IDs)</label>
              <input
                type="text"
                style={inputStyle}
                value={task.config?.childTasks?.join(', ') || ''}
                onChange={(e) => updateConfig('childTasks', e.target.value.split(',').map(s => s.trim()).filter(Boolean))}
                placeholder="task_1, task_2, task_3"
              />
              <div style={helpTextStyle}>
                These tasks will execute in parallel
              </div>
            </div>

            <div style={formGroupStyle}>
              <label style={labelStyle}>Max Concurrency</label>
              <input
                type="number"
                style={inputStyle}
                value={task.config?.maxConcurrency || 5}
                onChange={(e) => updateConfig('maxConcurrency', parseInt(e.target.value) || 5)}
                min="1"
                max="20"
              />
              <div style={helpTextStyle}>
                Maximum number of tasks to run simultaneously
              </div>
            </div>

            <div style={formGroupStyle}>
              <label style={{ ...labelStyle, display: 'flex', alignItems: 'center', gap: '8px' }}>
                <input
                  type="checkbox"
                  checked={task.config?.waitForAll || true}
                  onChange={(e) => updateConfig('waitForAll', e.target.checked)}
                />
                Wait for all tasks to complete before continuing
              </label>
            </div>
          </div>
        </div>
      )}

      {/* Actions */}
      <div style={actionsStyle}>
        <button
          style={buttonStyle}
          onClick={() => window.history.back()}
        >
          Cancel
        </button>
        <button
          style={hasChanges ? primaryButtonStyle : disabledButtonStyle}
          onClick={handleSave}
          disabled={!hasChanges || saving}
        >
          {saving ? 'Saving...' : 'Save Changes'}
        </button>
      </div>

      {/* CSS Animation */}
      <style>
        {`
          @keyframes spin {
            from { transform: rotate(0deg); }
            to { transform: rotate(360deg); }
          }
        `}
      </style>
    </div>
  );
};

export default TaskDetail;
