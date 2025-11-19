import React, { useState, useEffect } from 'react';
import { useParams } from 'react-router-dom';
import ExecutionTimeline from '../../components/workflows/ExecutionTimeline';
import workflowService from '../../services/workflowService';

/**
 * WorkflowDetail - Detailed view of a single workflow
 */
const WorkflowDetail = () => {
  const { workflowId } = useParams();

  const [workflow, setWorkflow] = useState(null);
  const [tasks, setTasks] = useState([]);
  const [executions, setExecutions] = useState([]);
  const [metrics, setMetrics] = useState(null);
  const [logs, setLogs] = useState([]);
  const [loading, setLoading] = useState(true);
  const [activeTab, setActiveTab] = useState('overview');
  const [selectedExecution, setSelectedExecution] = useState(null);
  const [logFilter, setLogFilter] = useState('all');

  useEffect(() => {
    if (workflowId) {
      loadWorkflowData();
    }
  }, [workflowId]);

  const loadWorkflowData = async () => {
    try {
      setLoading(true);
      const [workflowRes, tasksRes, executionsRes, metricsRes] = await Promise.all([
        workflowService.getWorkflow(workflowId),
        workflowService.getTasks(workflowId),
        workflowService.getExecutions(workflowId),
        workflowService.getMetrics(workflowId),
      ]);

      setWorkflow(workflowRes.data || workflowRes);
      setTasks(tasksRes.data || tasksRes || []);
      setExecutions(executionsRes.data || executionsRes || []);
      setMetrics(metricsRes.data || metricsRes);
    } catch (err) {
      alert(`Failed to load workflow: ${err.message}`);
    } finally {
      setLoading(false);
    }
  };

  const loadExecutionLogs = async (executionId) => {
    try {
      const response = await workflowService.getExecutionLogs(executionId, {
        level: logFilter !== 'all' ? logFilter : undefined,
      });
      setLogs(response.data || response || []);
    } catch (err) {
      console.error('Failed to load logs:', err);
    }
  };

  const handleRun = async () => {
    try {
      await workflowService.executeWorkflow(workflowId);
      loadWorkflowData();
    } catch (err) {
      alert(`Failed to run workflow: ${err.message}`);
    }
  };

  const handleExecutionSelect = (execution) => {
    setSelectedExecution(execution);
    loadExecutionLogs(execution.id);
  };

  const formatDate = (dateString) => {
    if (!dateString) return '-';
    return new Date(dateString).toLocaleString('en-US', {
      month: 'short',
      day: 'numeric',
      year: 'numeric',
      hour: '2-digit',
      minute: '2-digit',
    });
  };

  const formatDuration = (seconds) => {
    if (!seconds) return '-';
    if (seconds < 60) return `${seconds}s`;
    if (seconds < 3600) return `${Math.floor(seconds / 60)}m ${seconds % 60}s`;
    return `${Math.floor(seconds / 3600)}h ${Math.floor((seconds % 3600) / 60)}m`;
  };

  const getStatusColor = (status) => {
    const colors = {
      active: '#10b981',
      inactive: '#6b7280',
      running: '#3b82f6',
      completed: '#10b981',
      failed: '#ef4444',
      pending: '#f59e0b',
    };
    return colors[status] || '#6b7280';
  };

  // Styles
  const containerStyle = {
    padding: '24px',
    maxWidth: '1400px',
    margin: '0 auto',
  };

  const headerStyle = {
    display: 'flex',
    justifyContent: 'space-between',
    alignItems: 'flex-start',
    marginBottom: '24px',
  };

  const titleSectionStyle = {
    flex: 1,
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

  const statusBadgeStyle = (status) => ({
    display: 'inline-flex',
    alignItems: 'center',
    padding: '4px 10px',
    borderRadius: '12px',
    fontSize: '12px',
    fontWeight: '500',
    backgroundColor: `${getStatusColor(status)}20`,
    color: getStatusColor(status),
  });

  const descriptionStyle = {
    fontSize: '14px',
    color: '#6b7280',
  };

  const actionsStyle = {
    display: 'flex',
    gap: '8px',
  };

  const buttonStyle = {
    padding: '8px 16px',
    borderRadius: '6px',
    border: '1px solid #e5e7eb',
    backgroundColor: '#ffffff',
    fontSize: '13px',
    fontWeight: '500',
    cursor: 'pointer',
    display: 'flex',
    alignItems: 'center',
    gap: '6px',
  };

  const primaryButtonStyle = {
    ...buttonStyle,
    backgroundColor: '#3b82f6',
    borderColor: '#3b82f6',
    color: '#ffffff',
  };

  const tabsStyle = {
    display: 'flex',
    borderBottom: '1px solid #e5e7eb',
    marginBottom: '24px',
  };

  const tabStyle = (isActive) => ({
    padding: '12px 16px',
    fontSize: '14px',
    fontWeight: '500',
    color: isActive ? '#3b82f6' : '#6b7280',
    borderBottom: isActive ? '2px solid #3b82f6' : '2px solid transparent',
    cursor: 'pointer',
    transition: 'all 0.2s',
  });

  const cardStyle = {
    backgroundColor: '#ffffff',
    borderRadius: '8px',
    border: '1px solid #e5e7eb',
    marginBottom: '24px',
  };

  const cardHeaderStyle = {
    padding: '16px',
    borderBottom: '1px solid #e5e7eb',
    display: 'flex',
    justifyContent: 'space-between',
    alignItems: 'center',
  };

  const cardTitleStyle = {
    fontSize: '16px',
    fontWeight: '600',
    color: '#111827',
  };

  const cardContentStyle = {
    padding: '16px',
  };

  const metricsGridStyle = {
    display: 'grid',
    gridTemplateColumns: 'repeat(4, 1fr)',
    gap: '16px',
  };

  const metricCardStyle = {
    padding: '16px',
    backgroundColor: '#f9fafb',
    borderRadius: '8px',
    textAlign: 'center',
  };

  const metricValueStyle = {
    fontSize: '24px',
    fontWeight: '700',
    color: '#111827',
    marginBottom: '4px',
  };

  const metricLabelStyle = {
    fontSize: '12px',
    color: '#6b7280',
  };

  const tableStyle = {
    width: '100%',
    borderCollapse: 'collapse',
  };

  const thStyle = {
    textAlign: 'left',
    padding: '12px 16px',
    fontSize: '12px',
    fontWeight: '600',
    color: '#6b7280',
    borderBottom: '1px solid #e5e7eb',
    textTransform: 'uppercase',
  };

  const tdStyle = {
    padding: '12px 16px',
    fontSize: '14px',
    color: '#374151',
    borderBottom: '1px solid #f3f4f6',
  };

  const taskRowStyle = {
    display: 'flex',
    alignItems: 'center',
    gap: '12px',
    padding: '12px 0',
    borderBottom: '1px solid #f3f4f6',
  };

  const taskIconStyle = (color) => ({
    width: '32px',
    height: '32px',
    borderRadius: '6px',
    backgroundColor: `${color}20`,
    color: color,
    display: 'flex',
    alignItems: 'center',
    justifyContent: 'center',
  });

  const logsContainerStyle = {
    backgroundColor: '#1f2937',
    borderRadius: '8px',
    padding: '16px',
    maxHeight: '400px',
    overflow: 'auto',
    fontFamily: 'monospace',
  };

  const logEntryStyle = (level) => {
    const colors = {
      error: '#ef4444',
      warn: '#f59e0b',
      info: '#3b82f6',
      debug: '#6b7280',
    };
    return {
      fontSize: '12px',
      lineHeight: '1.6',
      color: colors[level] || '#d1d5db',
      marginBottom: '4px',
    };
  };

  const loadingStyle = {
    display: 'flex',
    justifyContent: 'center',
    alignItems: 'center',
    padding: '60px',
    color: '#6b7280',
  };

  const selectStyle = {
    padding: '6px 12px',
    border: '1px solid #e5e7eb',
    borderRadius: '6px',
    fontSize: '13px',
    backgroundColor: '#ffffff',
  };

  if (loading) {
    return (
      <div style={loadingStyle}>
        <svg width="24" height="24" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" style={{ animation: 'spin 1s linear infinite' }}>
          <path d="M21 12a9 9 0 1 1-6.219-8.56" />
        </svg>
        <span style={{ marginLeft: '8px' }}>Loading workflow...</span>
      </div>
    );
  }

  if (!workflow) {
    return (
      <div style={containerStyle}>
        <p>Workflow not found</p>
      </div>
    );
  }

  return (
    <div style={containerStyle}>
      {/* Header */}
      <div style={headerStyle}>
        <div style={titleSectionStyle}>
          <div style={breadcrumbStyle}>
            <a href="/workflows" style={breadcrumbLinkStyle}>Workflows</a> / {workflow.name}
          </div>
          <h1 style={titleStyle}>
            {workflow.name}
            <span style={statusBadgeStyle(workflow.status)}>{workflow.status}</span>
          </h1>
          {workflow.description && (
            <p style={descriptionStyle}>{workflow.description}</p>
          )}
        </div>
        <div style={actionsStyle}>
          <button style={buttonStyle} onClick={() => window.location.href = `/workflows/${workflowId}/edit`}>
            <svg width="14" height="14" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2">
              <path d="M11 4H4a2 2 0 0 0-2 2v14a2 2 0 0 0 2 2h14a2 2 0 0 0 2-2v-7" />
              <path d="M18.5 2.5a2.121 2.121 0 0 1 3 3L12 15l-4 1 1-4 9.5-9.5z" />
            </svg>
            Edit
          </button>
          <button style={primaryButtonStyle} onClick={handleRun} disabled={workflow.status === 'running'}>
            <svg width="14" height="14" viewBox="0 0 24 24" fill="currentColor">
              <path d="M8 5v14l11-7z" />
            </svg>
            Run Workflow
          </button>
        </div>
      </div>

      {/* Tabs */}
      <div style={tabsStyle}>
        {['overview', 'tasks', 'executions', 'logs'].map(tab => (
          <div
            key={tab}
            style={tabStyle(activeTab === tab)}
            onClick={() => setActiveTab(tab)}
          >
            {tab.charAt(0).toUpperCase() + tab.slice(1)}
          </div>
        ))}
      </div>

      {/* Overview Tab */}
      {activeTab === 'overview' && (
        <>
          {/* Metrics */}
          <div style={cardStyle}>
            <div style={cardHeaderStyle}>
              <span style={cardTitleStyle}>Performance Metrics</span>
            </div>
            <div style={cardContentStyle}>
              <div style={metricsGridStyle}>
                <div style={metricCardStyle}>
                  <div style={metricValueStyle}>{metrics?.total_executions || 0}</div>
                  <div style={metricLabelStyle}>Total Executions</div>
                </div>
                <div style={metricCardStyle}>
                  <div style={{ ...metricValueStyle, color: '#10b981' }}>
                    {metrics?.success_rate ? `${Math.round(metrics.success_rate * 100)}%` : 'N/A'}
                  </div>
                  <div style={metricLabelStyle}>Success Rate</div>
                </div>
                <div style={metricCardStyle}>
                  <div style={metricValueStyle}>{formatDuration(metrics?.avg_duration)}</div>
                  <div style={metricLabelStyle}>Avg Duration</div>
                </div>
                <div style={metricCardStyle}>
                  <div style={metricValueStyle}>{tasks.length}</div>
                  <div style={metricLabelStyle}>Total Tasks</div>
                </div>
              </div>
            </div>
          </div>

          {/* Recent Executions */}
          <div style={cardStyle}>
            <div style={cardHeaderStyle}>
              <span style={cardTitleStyle}>Recent Executions</span>
              <a href={`/workflows/${workflowId}/executions`} style={{ fontSize: '13px', color: '#3b82f6', textDecoration: 'none' }}>
                View All
              </a>
            </div>
            <div style={{ padding: 0 }}>
              <table style={tableStyle}>
                <thead>
                  <tr>
                    <th style={thStyle}>Execution ID</th>
                    <th style={thStyle}>Status</th>
                    <th style={thStyle}>Started</th>
                    <th style={thStyle}>Duration</th>
                  </tr>
                </thead>
                <tbody>
                  {executions.slice(0, 5).map(execution => (
                    <tr
                      key={execution.id}
                      style={{ cursor: 'pointer' }}
                      onClick={() => window.location.href = `/workflows/executions/${execution.id}`}
                    >
                      <td style={tdStyle}>{execution.id}</td>
                      <td style={tdStyle}>
                        <span style={statusBadgeStyle(execution.status)}>{execution.status}</span>
                      </td>
                      <td style={tdStyle}>{formatDate(execution.started_at)}</td>
                      <td style={tdStyle}>{formatDuration(execution.duration)}</td>
                    </tr>
                  ))}
                  {executions.length === 0 && (
                    <tr>
                      <td colSpan="4" style={{ ...tdStyle, textAlign: 'center', color: '#6b7280' }}>
                        No executions yet
                      </td>
                    </tr>
                  )}
                </tbody>
              </table>
            </div>
          </div>
        </>
      )}

      {/* Tasks Tab */}
      {activeTab === 'tasks' && (
        <div style={cardStyle}>
          <div style={cardHeaderStyle}>
            <span style={cardTitleStyle}>Tasks ({tasks.length})</span>
          </div>
          <div style={cardContentStyle}>
            {tasks.map((task, index) => (
              <div key={task.id} style={taskRowStyle}>
                <div style={{ fontSize: '14px', fontWeight: '500', color: '#6b7280', width: '30px' }}>
                  {index + 1}
                </div>
                <div style={taskIconStyle('#3b82f6')}>
                  <svg width="14" height="14" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2">
                    <polyline points="16 18 22 12 16 6" />
                    <polyline points="8 6 2 12 8 18" />
                  </svg>
                </div>
                <div style={{ flex: 1 }}>
                  <div style={{ fontWeight: '500', color: '#111827' }}>{task.name}</div>
                  <div style={{ fontSize: '12px', color: '#6b7280' }}>{task.type}</div>
                </div>
                {task.dependencies && task.dependencies.length > 0 && (
                  <div style={{ fontSize: '12px', color: '#6b7280' }}>
                    Depends on: {task.dependencies.join(', ')}
                  </div>
                )}
              </div>
            ))}
            {tasks.length === 0 && (
              <div style={{ textAlign: 'center', color: '#6b7280', padding: '24px' }}>
                No tasks defined
              </div>
            )}
          </div>
        </div>
      )}

      {/* Executions Tab */}
      {activeTab === 'executions' && (
        <div style={cardStyle}>
          <div style={cardHeaderStyle}>
            <span style={cardTitleStyle}>Execution History</span>
          </div>
          <div style={{ padding: 0 }}>
            <table style={tableStyle}>
              <thead>
                <tr>
                  <th style={thStyle}>Execution ID</th>
                  <th style={thStyle}>Status</th>
                  <th style={thStyle}>Started</th>
                  <th style={thStyle}>Completed</th>
                  <th style={thStyle}>Duration</th>
                  <th style={thStyle}>Actions</th>
                </tr>
              </thead>
              <tbody>
                {executions.map(execution => (
                  <tr key={execution.id}>
                    <td style={tdStyle}>{execution.id}</td>
                    <td style={tdStyle}>
                      <span style={statusBadgeStyle(execution.status)}>{execution.status}</span>
                    </td>
                    <td style={tdStyle}>{formatDate(execution.started_at)}</td>
                    <td style={tdStyle}>{formatDate(execution.completed_at)}</td>
                    <td style={tdStyle}>{formatDuration(execution.duration)}</td>
                    <td style={tdStyle}>
                      <button
                        style={{ ...buttonStyle, padding: '4px 8px', fontSize: '12px' }}
                        onClick={() => window.location.href = `/workflows/executions/${execution.id}`}
                      >
                        View
                      </button>
                    </td>
                  </tr>
                ))}
                {executions.length === 0 && (
                  <tr>
                    <td colSpan="6" style={{ ...tdStyle, textAlign: 'center', color: '#6b7280' }}>
                      No executions yet
                    </td>
                  </tr>
                )}
              </tbody>
            </table>
          </div>
        </div>
      )}

      {/* Logs Tab */}
      {activeTab === 'logs' && (
        <div style={cardStyle}>
          <div style={cardHeaderStyle}>
            <span style={cardTitleStyle}>Logs</span>
            <div style={{ display: 'flex', gap: '8px', alignItems: 'center' }}>
              <select
                style={selectStyle}
                value={selectedExecution?.id || ''}
                onChange={(e) => {
                  const exec = executions.find(ex => ex.id === e.target.value);
                  if (exec) handleExecutionSelect(exec);
                }}
              >
                <option value="">Select Execution</option>
                {executions.map(exec => (
                  <option key={exec.id} value={exec.id}>
                    {exec.id} - {exec.status}
                  </option>
                ))}
              </select>
              <select
                style={selectStyle}
                value={logFilter}
                onChange={(e) => setLogFilter(e.target.value)}
              >
                <option value="all">All Levels</option>
                <option value="error">Errors</option>
                <option value="warn">Warnings</option>
                <option value="info">Info</option>
                <option value="debug">Debug</option>
              </select>
            </div>
          </div>
          <div style={cardContentStyle}>
            <div style={logsContainerStyle}>
              {logs.length > 0 ? (
                logs.map((log, index) => (
                  <div key={index} style={logEntryStyle(log.level)}>
                    <span style={{ color: '#9ca3af' }}>[{log.timestamp}]</span>{' '}
                    <span style={{ fontWeight: '600' }}>[{log.level?.toUpperCase()}]</span>{' '}
                    {log.message}
                  </div>
                ))
              ) : (
                <div style={{ color: '#6b7280', textAlign: 'center', padding: '24px' }}>
                  {selectedExecution ? 'No logs available' : 'Select an execution to view logs'}
                </div>
              )}
            </div>
          </div>
        </div>
      )}

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

export default WorkflowDetail;
