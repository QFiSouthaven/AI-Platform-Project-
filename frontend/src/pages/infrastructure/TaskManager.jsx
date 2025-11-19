import React, { useState, useEffect } from 'react';
import {
  submitTask,
  getTasks,
  getTaskStatus,
  cancelTask,
  retryTask,
  getTaskResult,
} from '../../services/infrastructureService';

/**
 * TaskManager - Distributed task management interface
 * Submit, monitor, and manage distributed tasks
 */
const TaskManager = () => {
  const [tasks, setTasks] = useState([]);
  const [selectedTask, setSelectedTask] = useState(null);
  const [taskResult, setTaskResult] = useState(null);
  const [loading, setLoading] = useState(true);
  const [submitting, setSubmitting] = useState(false);
  const [error, setError] = useState(null);
  const [statusFilter, setStatusFilter] = useState('all');

  // Form state
  const [formData, setFormData] = useState({
    name: '',
    task_type: 'compute',
    priority: 'normal',
    parameters: '{}',
    timeout: 3600,
  });

  // Fetch tasks
  const fetchTasks = async () => {
    try {
      setError(null);
      const filters = statusFilter !== 'all' ? { status: statusFilter } : {};
      const response = await getTasks(filters);
      setTasks(response.data || response || []);
    } catch (err) {
      setError(err.message);
      // Mock data for demo
      setTasks([
        {
          id: 'task-001',
          name: 'Data Processing Job',
          task_type: 'compute',
          status: 'running',
          progress: 65,
          created_at: new Date(Date.now() - 3600000).toISOString(),
          started_at: new Date(Date.now() - 3000000).toISOString(),
          worker_id: 'worker-2',
          priority: 'high',
        },
        {
          id: 'task-002',
          name: 'Model Training',
          task_type: 'training',
          status: 'pending',
          progress: 0,
          created_at: new Date(Date.now() - 1800000).toISOString(),
          priority: 'normal',
        },
        {
          id: 'task-003',
          name: 'Batch Inference',
          task_type: 'inference',
          status: 'completed',
          progress: 100,
          created_at: new Date(Date.now() - 7200000).toISOString(),
          started_at: new Date(Date.now() - 7000000).toISOString(),
          completed_at: new Date(Date.now() - 5400000).toISOString(),
          worker_id: 'worker-1',
          priority: 'normal',
        },
        {
          id: 'task-004',
          name: 'Data Validation',
          task_type: 'validation',
          status: 'failed',
          progress: 45,
          created_at: new Date(Date.now() - 10800000).toISOString(),
          started_at: new Date(Date.now() - 10000000).toISOString(),
          error: 'Validation schema mismatch',
          worker_id: 'worker-3',
          priority: 'low',
        },
      ]);
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    fetchTasks();
    const interval = setInterval(fetchTasks, 10000);
    return () => clearInterval(interval);
  }, [statusFilter]);

  // Submit new task
  const handleSubmit = async (e) => {
    e.preventDefault();
    setSubmitting(true);
    try {
      let params;
      try {
        params = JSON.parse(formData.parameters);
      } catch {
        throw new Error('Invalid JSON in parameters');
      }

      await submitTask({
        name: formData.name,
        task_type: formData.task_type,
        priority: formData.priority,
        parameters: params,
        timeout: parseInt(formData.timeout),
      });

      setFormData({
        name: '',
        task_type: 'compute',
        priority: 'normal',
        parameters: '{}',
        timeout: 3600,
      });
      fetchTasks();
    } catch (err) {
      setError(err.message);
    } finally {
      setSubmitting(false);
    }
  };

  // Cancel task
  const handleCancel = async (taskId) => {
    try {
      await cancelTask(taskId);
      fetchTasks();
    } catch (err) {
      setError(`Failed to cancel task: ${err.message}`);
    }
  };

  // Retry task
  const handleRetry = async (taskId) => {
    try {
      await retryTask(taskId);
      fetchTasks();
    } catch (err) {
      setError(`Failed to retry task: ${err.message}`);
    }
  };

  // View task result
  const handleViewResult = async (task) => {
    setSelectedTask(task);
    try {
      const result = await getTaskResult(task.id);
      setTaskResult(result.data || result);
    } catch (err) {
      setTaskResult({ error: 'Failed to load result', details: err.message });
    }
  };

  // Status badge config
  const getStatusConfig = (status) => {
    switch (status) {
      case 'running':
        return { color: '#3b82f6', bg: '#dbeafe', label: 'Running' };
      case 'pending':
        return { color: '#f59e0b', bg: '#fef3c7', label: 'Pending' };
      case 'completed':
        return { color: '#10b981', bg: '#d1fae5', label: 'Completed' };
      case 'failed':
        return { color: '#ef4444', bg: '#fecaca', label: 'Failed' };
      case 'cancelled':
        return { color: '#6b7280', bg: '#f3f4f6', label: 'Cancelled' };
      default:
        return { color: '#6b7280', bg: '#f3f4f6', label: status };
    }
  };

  // Format date
  const formatDate = (dateStr) => {
    if (!dateStr) return '-';
    return new Date(dateStr).toLocaleString();
  };

  // Format duration
  const formatDuration = (start, end) => {
    if (!start) return '-';
    const endTime = end ? new Date(end) : new Date();
    const duration = Math.floor((endTime - new Date(start)) / 1000);
    if (duration < 60) return `${duration}s`;
    if (duration < 3600) return `${Math.floor(duration / 60)}m ${duration % 60}s`;
    return `${Math.floor(duration / 3600)}h ${Math.floor((duration % 3600) / 60)}m`;
  };

  return (
    <div className="task-manager" style={{ padding: '24px' }}>
      <div style={{ marginBottom: '24px' }}>
        <h1 style={{ margin: '0 0 8px 0', fontSize: '24px', fontWeight: '600' }}>
          Task Manager
        </h1>
        <p style={{ margin: 0, color: '#6b7280' }}>
          Submit and manage distributed tasks across the cluster
        </p>
      </div>

      {error && (
        <div
          style={{
            padding: '12px',
            marginBottom: '16px',
            backgroundColor: '#fef2f2',
            border: '1px solid #fecaca',
            borderRadius: '8px',
            color: '#991b1b',
            fontSize: '14px',
          }}
        >
          {error}
          <button
            onClick={() => setError(null)}
            style={{
              float: 'right',
              background: 'none',
              border: 'none',
              cursor: 'pointer',
              color: '#991b1b',
            }}
          >
            x
          </button>
        </div>
      )}

      <div style={{ display: 'grid', gridTemplateColumns: '350px 1fr', gap: '24px' }}>
        {/* Task Submission Form */}
        <div
          style={{
            backgroundColor: '#ffffff',
            borderRadius: '12px',
            boxShadow: '0 1px 3px rgba(0, 0, 0, 0.1)',
            padding: '20px',
            height: 'fit-content',
          }}
        >
          <h3 style={{ margin: '0 0 16px 0', fontSize: '16px', fontWeight: '600' }}>
            Submit New Task
          </h3>
          <form onSubmit={handleSubmit}>
            <div style={{ marginBottom: '16px' }}>
              <label style={{ display: 'block', marginBottom: '4px', fontSize: '14px', fontWeight: '500' }}>
                Task Name
              </label>
              <input
                type="text"
                value={formData.name}
                onChange={(e) => setFormData({ ...formData, name: e.target.value })}
                placeholder="Enter task name"
                required
                style={{
                  width: '100%',
                  padding: '8px 12px',
                  border: '1px solid #d1d5db',
                  borderRadius: '6px',
                  fontSize: '14px',
                  boxSizing: 'border-box',
                }}
              />
            </div>

            <div style={{ marginBottom: '16px' }}>
              <label style={{ display: 'block', marginBottom: '4px', fontSize: '14px', fontWeight: '500' }}>
                Task Type
              </label>
              <select
                value={formData.task_type}
                onChange={(e) => setFormData({ ...formData, task_type: e.target.value })}
                style={{
                  width: '100%',
                  padding: '8px 12px',
                  border: '1px solid #d1d5db',
                  borderRadius: '6px',
                  fontSize: '14px',
                  backgroundColor: '#ffffff',
                }}
              >
                <option value="compute">Compute</option>
                <option value="training">Training</option>
                <option value="inference">Inference</option>
                <option value="validation">Validation</option>
                <option value="etl">ETL</option>
              </select>
            </div>

            <div style={{ marginBottom: '16px' }}>
              <label style={{ display: 'block', marginBottom: '4px', fontSize: '14px', fontWeight: '500' }}>
                Priority
              </label>
              <select
                value={formData.priority}
                onChange={(e) => setFormData({ ...formData, priority: e.target.value })}
                style={{
                  width: '100%',
                  padding: '8px 12px',
                  border: '1px solid #d1d5db',
                  borderRadius: '6px',
                  fontSize: '14px',
                  backgroundColor: '#ffffff',
                }}
              >
                <option value="low">Low</option>
                <option value="normal">Normal</option>
                <option value="high">High</option>
                <option value="critical">Critical</option>
              </select>
            </div>

            <div style={{ marginBottom: '16px' }}>
              <label style={{ display: 'block', marginBottom: '4px', fontSize: '14px', fontWeight: '500' }}>
                Timeout (seconds)
              </label>
              <input
                type="number"
                value={formData.timeout}
                onChange={(e) => setFormData({ ...formData, timeout: e.target.value })}
                min="60"
                max="86400"
                style={{
                  width: '100%',
                  padding: '8px 12px',
                  border: '1px solid #d1d5db',
                  borderRadius: '6px',
                  fontSize: '14px',
                  boxSizing: 'border-box',
                }}
              />
            </div>

            <div style={{ marginBottom: '16px' }}>
              <label style={{ display: 'block', marginBottom: '4px', fontSize: '14px', fontWeight: '500' }}>
                Parameters (JSON)
              </label>
              <textarea
                value={formData.parameters}
                onChange={(e) => setFormData({ ...formData, parameters: e.target.value })}
                rows={4}
                style={{
                  width: '100%',
                  padding: '8px 12px',
                  border: '1px solid #d1d5db',
                  borderRadius: '6px',
                  fontSize: '14px',
                  fontFamily: 'monospace',
                  resize: 'vertical',
                  boxSizing: 'border-box',
                }}
              />
            </div>

            <button
              type="submit"
              disabled={submitting}
              style={{
                width: '100%',
                padding: '10px',
                backgroundColor: submitting ? '#9ca3af' : '#3b82f6',
                color: '#ffffff',
                border: 'none',
                borderRadius: '6px',
                fontSize: '14px',
                fontWeight: '500',
                cursor: submitting ? 'not-allowed' : 'pointer',
              }}
            >
              {submitting ? 'Submitting...' : 'Submit Task'}
            </button>
          </form>
        </div>

        {/* Tasks Table */}
        <div
          style={{
            backgroundColor: '#ffffff',
            borderRadius: '12px',
            boxShadow: '0 1px 3px rgba(0, 0, 0, 0.1)',
            padding: '20px',
          }}
        >
          <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', marginBottom: '16px' }}>
            <h3 style={{ margin: 0, fontSize: '16px', fontWeight: '600' }}>
              Tasks ({tasks.length})
            </h3>
            <div style={{ display: 'flex', gap: '8px', alignItems: 'center' }}>
              <select
                value={statusFilter}
                onChange={(e) => setStatusFilter(e.target.value)}
                style={{
                  padding: '6px 12px',
                  border: '1px solid #d1d5db',
                  borderRadius: '6px',
                  fontSize: '13px',
                  backgroundColor: '#ffffff',
                }}
              >
                <option value="all">All Status</option>
                <option value="pending">Pending</option>
                <option value="running">Running</option>
                <option value="completed">Completed</option>
                <option value="failed">Failed</option>
              </select>
              <button
                onClick={fetchTasks}
                style={{
                  padding: '6px 12px',
                  backgroundColor: '#f3f4f6',
                  border: '1px solid #d1d5db',
                  borderRadius: '6px',
                  cursor: 'pointer',
                  fontSize: '13px',
                }}
              >
                Refresh
              </button>
            </div>
          </div>

          {loading ? (
            <div style={{ textAlign: 'center', padding: '40px', color: '#6b7280' }}>
              Loading tasks...
            </div>
          ) : tasks.length === 0 ? (
            <div style={{ textAlign: 'center', padding: '40px', color: '#6b7280' }}>
              No tasks found
            </div>
          ) : (
            <div style={{ overflowX: 'auto' }}>
              <table style={{ width: '100%', borderCollapse: 'collapse', fontSize: '14px' }}>
                <thead>
                  <tr style={{ borderBottom: '2px solid #e5e7eb' }}>
                    <th style={{ padding: '12px 8px', textAlign: 'left', fontWeight: '600' }}>Task</th>
                    <th style={{ padding: '12px 8px', textAlign: 'left', fontWeight: '600' }}>Type</th>
                    <th style={{ padding: '12px 8px', textAlign: 'left', fontWeight: '600' }}>Status</th>
                    <th style={{ padding: '12px 8px', textAlign: 'left', fontWeight: '600' }}>Progress</th>
                    <th style={{ padding: '12px 8px', textAlign: 'left', fontWeight: '600' }}>Duration</th>
                    <th style={{ padding: '12px 8px', textAlign: 'left', fontWeight: '600' }}>Actions</th>
                  </tr>
                </thead>
                <tbody>
                  {tasks.map((task) => {
                    const statusConfig = getStatusConfig(task.status);
                    return (
                      <tr key={task.id} style={{ borderBottom: '1px solid #f3f4f6' }}>
                        <td style={{ padding: '12px 8px' }}>
                          <div style={{ fontWeight: '500' }}>{task.name}</div>
                          <div style={{ fontSize: '12px', color: '#6b7280' }}>{task.id}</div>
                        </td>
                        <td style={{ padding: '12px 8px', textTransform: 'capitalize' }}>
                          {task.task_type}
                        </td>
                        <td style={{ padding: '12px 8px' }}>
                          <span
                            style={{
                              padding: '4px 8px',
                              borderRadius: '12px',
                              fontSize: '12px',
                              fontWeight: '500',
                              backgroundColor: statusConfig.bg,
                              color: statusConfig.color,
                            }}
                          >
                            {statusConfig.label}
                          </span>
                        </td>
                        <td style={{ padding: '12px 8px' }}>
                          <div style={{ display: 'flex', alignItems: 'center', gap: '8px' }}>
                            <div
                              style={{
                                flex: 1,
                                height: '6px',
                                backgroundColor: '#e5e7eb',
                                borderRadius: '3px',
                                overflow: 'hidden',
                              }}
                            >
                              <div
                                style={{
                                  width: `${task.progress || 0}%`,
                                  height: '100%',
                                  backgroundColor: statusConfig.color,
                                  transition: 'width 0.3s ease',
                                }}
                              />
                            </div>
                            <span style={{ fontSize: '12px', color: '#6b7280', minWidth: '40px' }}>
                              {task.progress || 0}%
                            </span>
                          </div>
                        </td>
                        <td style={{ padding: '12px 8px', fontSize: '13px', color: '#6b7280' }}>
                          {formatDuration(task.started_at, task.completed_at)}
                        </td>
                        <td style={{ padding: '12px 8px' }}>
                          <div style={{ display: 'flex', gap: '4px' }}>
                            {task.status === 'completed' && (
                              <button
                                onClick={() => handleViewResult(task)}
                                style={{
                                  padding: '4px 8px',
                                  backgroundColor: '#dbeafe',
                                  border: 'none',
                                  borderRadius: '4px',
                                  fontSize: '12px',
                                  color: '#3b82f6',
                                  cursor: 'pointer',
                                }}
                              >
                                View
                              </button>
                            )}
                            {(task.status === 'running' || task.status === 'pending') && (
                              <button
                                onClick={() => handleCancel(task.id)}
                                style={{
                                  padding: '4px 8px',
                                  backgroundColor: '#fecaca',
                                  border: 'none',
                                  borderRadius: '4px',
                                  fontSize: '12px',
                                  color: '#ef4444',
                                  cursor: 'pointer',
                                }}
                              >
                                Cancel
                              </button>
                            )}
                            {task.status === 'failed' && (
                              <button
                                onClick={() => handleRetry(task.id)}
                                style={{
                                  padding: '4px 8px',
                                  backgroundColor: '#fef3c7',
                                  border: 'none',
                                  borderRadius: '4px',
                                  fontSize: '12px',
                                  color: '#f59e0b',
                                  cursor: 'pointer',
                                }}
                              >
                                Retry
                              </button>
                            )}
                          </div>
                        </td>
                      </tr>
                    );
                  })}
                </tbody>
              </table>
            </div>
          )}
        </div>
      </div>

      {/* Task Result Modal */}
      {selectedTask && (
        <div
          style={{
            position: 'fixed',
            top: 0,
            left: 0,
            right: 0,
            bottom: 0,
            backgroundColor: 'rgba(0, 0, 0, 0.5)',
            display: 'flex',
            alignItems: 'center',
            justifyContent: 'center',
            zIndex: 1000,
          }}
          onClick={() => {
            setSelectedTask(null);
            setTaskResult(null);
          }}
        >
          <div
            style={{
              backgroundColor: '#ffffff',
              borderRadius: '12px',
              padding: '24px',
              maxWidth: '600px',
              width: '90%',
              maxHeight: '80vh',
              overflow: 'auto',
            }}
            onClick={(e) => e.stopPropagation()}
          >
            <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', marginBottom: '16px' }}>
              <h3 style={{ margin: 0, fontSize: '18px', fontWeight: '600' }}>
                Task Result: {selectedTask.name}
              </h3>
              <button
                onClick={() => {
                  setSelectedTask(null);
                  setTaskResult(null);
                }}
                style={{
                  background: 'none',
                  border: 'none',
                  fontSize: '24px',
                  cursor: 'pointer',
                  color: '#6b7280',
                }}
              >
                x
              </button>
            </div>
            <pre
              style={{
                backgroundColor: '#f3f4f6',
                padding: '16px',
                borderRadius: '8px',
                overflow: 'auto',
                fontSize: '13px',
                fontFamily: 'monospace',
                margin: 0,
              }}
            >
              {taskResult ? JSON.stringify(taskResult, null, 2) : 'Loading...'}
            </pre>
          </div>
        </div>
      )}
    </div>
  );
};

export default TaskManager;
