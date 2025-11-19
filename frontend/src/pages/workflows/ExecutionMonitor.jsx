import React, { useState, useEffect, useRef } from 'react';
import { useParams } from 'react-router-dom';
import ExecutionTimeline from '../../components/workflows/ExecutionTimeline';
import workflowService from '../../services/workflowService';

/**
 * ExecutionMonitor - Real-time execution monitoring page
 */
const ExecutionMonitor = () => {
  const { executionId } = useParams();
  const wsRef = useRef(null);
  const logsEndRef = useRef(null);

  const [execution, setExecution] = useState(null);
  const [tasks, setTasks] = useState([]);
  const [logs, setLogs] = useState([]);
  const [loading, setLoading] = useState(true);
  const [autoScroll, setAutoScroll] = useState(true);
  const [selectedTask, setSelectedTask] = useState(null);

  useEffect(() => {
    if (executionId) {
      loadExecution();
      subscribeToUpdates();
    }

    return () => {
      if (wsRef.current) {
        wsRef.current.close();
      }
    };
  }, [executionId]);

  useEffect(() => {
    if (autoScroll && logsEndRef.current) {
      logsEndRef.current.scrollIntoView({ behavior: 'smooth' });
    }
  }, [logs, autoScroll]);

  const loadExecution = async () => {
    try {
      setLoading(true);
      const response = await workflowService.getExecution(executionId);
      const data = response.data || response;
      setExecution(data);
      setTasks(data.tasks || []);

      const logsResponse = await workflowService.getExecutionLogs(executionId);
      setLogs(logsResponse.data || logsResponse || []);
    } catch (err) {
      alert(`Failed to load execution: ${err.message}`);
    } finally {
      setLoading(false);
    }
  };

  const subscribeToUpdates = () => {
    wsRef.current = workflowService.subscribeToExecution(executionId, {
      onMessage: (data) => {
        if (data.type === 'task_update') {
          setTasks(prevTasks =>
            prevTasks.map(t =>
              t.id === data.task_id ? { ...t, ...data.task } : t
            )
          );
        } else if (data.type === 'log') {
          setLogs(prevLogs => [...prevLogs, data.log]);
        } else if (data.type === 'execution_update') {
          setExecution(prev => ({ ...prev, ...data.execution }));
        }
      },
      onError: (error) => {
        console.error('WebSocket error:', error);
      },
    });
  };

  const handleCancel = async () => {
    if (window.confirm('Are you sure you want to cancel this execution?')) {
      try {
        await workflowService.cancelExecution(executionId);
        loadExecution();
      } catch (err) {
        alert(`Failed to cancel execution: ${err.message}`);
      }
    }
  };

  const handleRetry = async () => {
    try {
      const response = await workflowService.retryExecution(executionId);
      const newExecutionId = response.data?.id || response.id;
      window.location.href = `/workflows/executions/${newExecutionId}`;
    } catch (err) {
      alert(`Failed to retry execution: ${err.message}`);
    }
  };

  const formatTime = (dateString) => {
    if (!dateString) return '-';
    return new Date(dateString).toLocaleTimeString('en-US', {
      hour: '2-digit',
      minute: '2-digit',
      second: '2-digit',
    });
  };

  const formatDuration = (start, end) => {
    if (!start) return '-';
    const startTime = new Date(start);
    const endTime = end ? new Date(end) : new Date();
    const diff = Math.floor((endTime - startTime) / 1000);

    if (diff < 60) return `${diff}s`;
    if (diff < 3600) return `${Math.floor(diff / 60)}m ${diff % 60}s`;
    return `${Math.floor(diff / 3600)}h ${Math.floor((diff % 3600) / 60)}m`;
  };

  const getStatusColor = (status) => {
    const colors = {
      pending: '#9ca3af',
      running: '#3b82f6',
      completed: '#10b981',
      failed: '#ef4444',
      cancelled: '#f59e0b',
    };
    return colors[status] || '#6b7280';
  };

  const getProgress = () => {
    if (tasks.length === 0) return 0;
    const completed = tasks.filter(t => t.status === 'completed').length;
    return Math.round((completed / tasks.length) * 100);
  };

  // Styles
  const containerStyle = {
    display: 'flex',
    height: '100vh',
    backgroundColor: '#f3f4f6',
  };

  const mainContentStyle = {
    flex: 1,
    display: 'flex',
    flexDirection: 'column',
    overflow: 'hidden',
  };

  const headerStyle = {
    backgroundColor: '#ffffff',
    borderBottom: '1px solid #e5e7eb',
    padding: '16px 24px',
  };

  const headerTopStyle = {
    display: 'flex',
    justifyContent: 'space-between',
    alignItems: 'center',
    marginBottom: '16px',
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
    fontSize: '20px',
    fontWeight: '700',
    color: '#111827',
    display: 'flex',
    alignItems: 'center',
    gap: '12px',
  };

  const statusBadgeStyle = (status) => ({
    display: 'inline-flex',
    alignItems: 'center',
    gap: '6px',
    padding: '4px 10px',
    borderRadius: '12px',
    fontSize: '12px',
    fontWeight: '500',
    backgroundColor: `${getStatusColor(status)}20`,
    color: getStatusColor(status),
  });

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

  const dangerButtonStyle = {
    ...buttonStyle,
    borderColor: '#ef4444',
    color: '#ef4444',
  };

  const primaryButtonStyle = {
    ...buttonStyle,
    backgroundColor: '#3b82f6',
    borderColor: '#3b82f6',
    color: '#ffffff',
  };

  const progressContainerStyle = {
    marginTop: '12px',
  };

  const progressBarStyle = {
    height: '8px',
    backgroundColor: '#e5e7eb',
    borderRadius: '4px',
    overflow: 'hidden',
  };

  const progressFillStyle = {
    height: '100%',
    backgroundColor: execution?.status === 'failed' ? '#ef4444' : '#3b82f6',
    borderRadius: '4px',
    transition: 'width 0.3s',
    width: `${getProgress()}%`,
  };

  const progressTextStyle = {
    display: 'flex',
    justifyContent: 'space-between',
    marginTop: '4px',
    fontSize: '12px',
    color: '#6b7280',
  };

  const contentAreaStyle = {
    flex: 1,
    display: 'flex',
    overflow: 'hidden',
  };

  const timelinePanelStyle = {
    width: '320px',
    backgroundColor: '#ffffff',
    borderRight: '1px solid #e5e7eb',
    overflow: 'auto',
  };

  const panelHeaderStyle = {
    padding: '16px',
    borderBottom: '1px solid #e5e7eb',
    fontSize: '14px',
    fontWeight: '600',
    color: '#111827',
  };

  const logsPanelStyle = {
    flex: 1,
    display: 'flex',
    flexDirection: 'column',
    overflow: 'hidden',
  };

  const logsHeaderStyle = {
    padding: '12px 16px',
    borderBottom: '1px solid #e5e7eb',
    backgroundColor: '#ffffff',
    display: 'flex',
    justifyContent: 'space-between',
    alignItems: 'center',
  };

  const logsContainerStyle = {
    flex: 1,
    backgroundColor: '#1f2937',
    padding: '16px',
    overflow: 'auto',
    fontFamily: 'monospace',
    fontSize: '12px',
  };

  const logEntryStyle = (level) => {
    const colors = {
      error: '#ef4444',
      warn: '#f59e0b',
      info: '#3b82f6',
      debug: '#6b7280',
    };
    return {
      lineHeight: '1.6',
      color: colors[level] || '#d1d5db',
      marginBottom: '2px',
    };
  };

  const toggleStyle = {
    display: 'flex',
    alignItems: 'center',
    gap: '8px',
    fontSize: '12px',
    color: '#6b7280',
  };

  const checkboxStyle = {
    cursor: 'pointer',
  };

  const detailsPanelStyle = {
    width: '300px',
    backgroundColor: '#ffffff',
    borderLeft: '1px solid #e5e7eb',
    overflow: 'auto',
  };

  const detailsContentStyle = {
    padding: '16px',
  };

  const detailRowStyle = {
    marginBottom: '12px',
  };

  const detailLabelStyle = {
    fontSize: '11px',
    fontWeight: '600',
    color: '#6b7280',
    textTransform: 'uppercase',
    marginBottom: '4px',
  };

  const detailValueStyle = {
    fontSize: '14px',
    color: '#111827',
  };

  const loadingStyle = {
    display: 'flex',
    justifyContent: 'center',
    alignItems: 'center',
    height: '100vh',
    color: '#6b7280',
  };

  if (loading) {
    return (
      <div style={loadingStyle}>
        <svg width="24" height="24" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" style={{ animation: 'spin 1s linear infinite' }}>
          <path d="M21 12a9 9 0 1 1-6.219-8.56" />
        </svg>
        <span style={{ marginLeft: '8px' }}>Loading execution...</span>
      </div>
    );
  }

  if (!execution) {
    return (
      <div style={{ padding: '24px' }}>
        <p>Execution not found</p>
      </div>
    );
  }

  return (
    <div style={containerStyle}>
      <div style={mainContentStyle}>
        {/* Header */}
        <div style={headerStyle}>
          <div style={breadcrumbStyle}>
            <a href="/workflows" style={breadcrumbLinkStyle}>Workflows</a>
            {' / '}
            <a href={`/workflows/${execution.workflow_id}`} style={breadcrumbLinkStyle}>
              {execution.workflow_name || 'Workflow'}
            </a>
            {' / '}
            Execution {executionId}
          </div>
          <div style={headerTopStyle}>
            <h1 style={titleStyle}>
              Execution Monitor
              <span style={statusBadgeStyle(execution.status)}>
                {execution.status === 'running' && (
                  <svg width="12" height="12" viewBox="0 0 24 24" fill="currentColor" style={{ animation: 'spin 1s linear infinite' }}>
                    <path d="M12 4V2A10 10 0 0 0 2 12h2a8 8 0 0 1 8-8z" />
                  </svg>
                )}
                {execution.status}
              </span>
            </h1>
            <div style={actionsStyle}>
              {execution.status === 'running' && (
                <button style={dangerButtonStyle} onClick={handleCancel}>
                  <svg width="14" height="14" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2">
                    <rect x="3" y="3" width="18" height="18" rx="2" ry="2" />
                  </svg>
                  Cancel
                </button>
              )}
              {(execution.status === 'failed' || execution.status === 'cancelled') && (
                <button style={primaryButtonStyle} onClick={handleRetry}>
                  <svg width="14" height="14" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2">
                    <polyline points="23 4 23 10 17 10" />
                    <path d="M20.49 15a9 9 0 1 1-2.12-9.36L23 10" />
                  </svg>
                  Retry
                </button>
              )}
            </div>
          </div>

          {/* Progress Bar */}
          <div style={progressContainerStyle}>
            <div style={progressBarStyle}>
              <div style={progressFillStyle} />
            </div>
            <div style={progressTextStyle}>
              <span>{getProgress()}% complete</span>
              <span>
                {tasks.filter(t => t.status === 'completed').length} / {tasks.length} tasks
              </span>
            </div>
          </div>
        </div>

        {/* Content Area */}
        <div style={contentAreaStyle}>
          {/* Timeline Panel */}
          <div style={timelinePanelStyle}>
            <div style={panelHeaderStyle}>Task Timeline</div>
            <ExecutionTimeline
              tasks={tasks}
              currentTaskId={tasks.find(t => t.status === 'running')?.id}
              onTaskClick={(task) => setSelectedTask(task)}
            />
          </div>

          {/* Logs Panel */}
          <div style={logsPanelStyle}>
            <div style={logsHeaderStyle}>
              <span style={{ fontSize: '14px', fontWeight: '600', color: '#111827' }}>
                Live Logs
              </span>
              <label style={toggleStyle}>
                <input
                  type="checkbox"
                  style={checkboxStyle}
                  checked={autoScroll}
                  onChange={(e) => setAutoScroll(e.target.checked)}
                />
                Auto-scroll
              </label>
            </div>
            <div style={logsContainerStyle}>
              {logs.map((log, index) => (
                <div key={index} style={logEntryStyle(log.level)}>
                  <span style={{ color: '#9ca3af' }}>[{formatTime(log.timestamp)}]</span>{' '}
                  <span style={{ fontWeight: '600' }}>[{log.level?.toUpperCase()}]</span>{' '}
                  {log.task_name && <span style={{ color: '#818cf8' }}>[{log.task_name}]</span>}{' '}
                  {log.message}
                </div>
              ))}
              {logs.length === 0 && (
                <div style={{ color: '#6b7280', textAlign: 'center', padding: '24px' }}>
                  Waiting for logs...
                </div>
              )}
              <div ref={logsEndRef} />
            </div>
          </div>

          {/* Details Panel */}
          <div style={detailsPanelStyle}>
            <div style={panelHeaderStyle}>
              {selectedTask ? 'Task Details' : 'Execution Details'}
            </div>
            <div style={detailsContentStyle}>
              {selectedTask ? (
                <>
                  <div style={detailRowStyle}>
                    <div style={detailLabelStyle}>Task Name</div>
                    <div style={detailValueStyle}>{selectedTask.name}</div>
                  </div>
                  <div style={detailRowStyle}>
                    <div style={detailLabelStyle}>Status</div>
                    <div style={detailValueStyle}>
                      <span style={statusBadgeStyle(selectedTask.status)}>
                        {selectedTask.status}
                      </span>
                    </div>
                  </div>
                  <div style={detailRowStyle}>
                    <div style={detailLabelStyle}>Started</div>
                    <div style={detailValueStyle}>{formatTime(selectedTask.started_at)}</div>
                  </div>
                  <div style={detailRowStyle}>
                    <div style={detailLabelStyle}>Duration</div>
                    <div style={detailValueStyle}>
                      {formatDuration(selectedTask.started_at, selectedTask.completed_at)}
                    </div>
                  </div>
                  {selectedTask.error && (
                    <div style={detailRowStyle}>
                      <div style={detailLabelStyle}>Error</div>
                      <div style={{ ...detailValueStyle, color: '#ef4444', fontSize: '12px' }}>
                        {selectedTask.error}
                      </div>
                    </div>
                  )}
                </>
              ) : (
                <>
                  <div style={detailRowStyle}>
                    <div style={detailLabelStyle}>Execution ID</div>
                    <div style={detailValueStyle}>{executionId}</div>
                  </div>
                  <div style={detailRowStyle}>
                    <div style={detailLabelStyle}>Status</div>
                    <div style={detailValueStyle}>
                      <span style={statusBadgeStyle(execution.status)}>
                        {execution.status}
                      </span>
                    </div>
                  </div>
                  <div style={detailRowStyle}>
                    <div style={detailLabelStyle}>Started</div>
                    <div style={detailValueStyle}>{formatTime(execution.started_at)}</div>
                  </div>
                  <div style={detailRowStyle}>
                    <div style={detailLabelStyle}>Duration</div>
                    <div style={detailValueStyle}>
                      {formatDuration(execution.started_at, execution.completed_at)}
                    </div>
                  </div>
                  <div style={detailRowStyle}>
                    <div style={detailLabelStyle}>Triggered By</div>
                    <div style={detailValueStyle}>{execution.triggered_by || 'Manual'}</div>
                  </div>
                </>
              )}
            </div>
          </div>
        </div>
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

export default ExecutionMonitor;
