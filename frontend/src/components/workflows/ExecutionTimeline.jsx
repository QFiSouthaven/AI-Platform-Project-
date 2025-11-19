import React from 'react';
import PropTypes from 'prop-types';

/**
 * ExecutionTimeline - Timeline visualization for workflow execution
 */
const ExecutionTimeline = ({
  tasks = [],
  currentTaskId = null,
  onTaskClick,
  orientation = 'vertical',
}) => {
  const getStatusColor = (status) => {
    const colors = {
      pending: '#9ca3af',
      running: '#3b82f6',
      completed: '#10b981',
      failed: '#ef4444',
      skipped: '#6b7280',
      cancelled: '#f59e0b',
    };
    return colors[status] || '#9ca3af';
  };

  const getStatusIcon = (status) => {
    switch (status) {
      case 'completed':
        return (
          <svg width="12" height="12" viewBox="0 0 24 24" fill="currentColor">
            <path d="M9 16.17L4.83 12l-1.42 1.41L9 19 21 7l-1.41-1.41z" />
          </svg>
        );
      case 'failed':
        return (
          <svg width="12" height="12" viewBox="0 0 24 24" fill="currentColor">
            <path d="M19 6.41L17.59 5 12 10.59 6.41 5 5 6.41 10.59 12 5 17.59 6.41 19 12 13.41 17.59 19 19 17.59 13.41 12z" />
          </svg>
        );
      case 'running':
        return (
          <svg width="12" height="12" viewBox="0 0 24 24" fill="currentColor" className="animate-spin">
            <path d="M12 4V2A10 10 0 0 0 2 12h2a8 8 0 0 1 8-8z" />
          </svg>
        );
      case 'skipped':
        return (
          <svg width="12" height="12" viewBox="0 0 24 24" fill="currentColor">
            <path d="M6 18l8.5-6L6 6v12zM16 6v12h2V6h-2z" />
          </svg>
        );
      default:
        return (
          <svg width="12" height="12" viewBox="0 0 24 24" fill="currentColor">
            <circle cx="12" cy="12" r="4" />
          </svg>
        );
    }
  };

  const formatDuration = (startTime, endTime) => {
    if (!startTime) return '-';
    const start = new Date(startTime);
    const end = endTime ? new Date(endTime) : new Date();
    const diff = Math.floor((end - start) / 1000);

    if (diff < 60) return `${diff}s`;
    if (diff < 3600) return `${Math.floor(diff / 60)}m ${diff % 60}s`;
    return `${Math.floor(diff / 3600)}h ${Math.floor((diff % 3600) / 60)}m`;
  };

  const formatTime = (dateString) => {
    if (!dateString) return '-';
    return new Date(dateString).toLocaleTimeString('en-US', {
      hour: '2-digit',
      minute: '2-digit',
      second: '2-digit',
    });
  };

  const containerStyle = {
    display: 'flex',
    flexDirection: orientation === 'vertical' ? 'column' : 'row',
    gap: '0',
    padding: '16px',
  };

  const taskItemStyle = (task, index) => ({
    display: 'flex',
    flexDirection: orientation === 'vertical' ? 'row' : 'column',
    alignItems: orientation === 'vertical' ? 'flex-start' : 'center',
    position: 'relative',
  });

  const timelineLineStyle = (task, index) => ({
    position: 'absolute',
    backgroundColor: index < tasks.length - 1 ? getStatusColor(task.status) : 'transparent',
    ...(orientation === 'vertical'
      ? {
          left: '11px',
          top: '24px',
          width: '2px',
          height: 'calc(100% - 8px)',
        }
      : {
          top: '11px',
          left: '24px',
          height: '2px',
          width: 'calc(100% - 8px)',
        }),
  });

  const nodeContainerStyle = {
    display: 'flex',
    flexDirection: 'column',
    alignItems: 'center',
    zIndex: 1,
  };

  const nodeStyle = (task) => ({
    width: '24px',
    height: '24px',
    borderRadius: '50%',
    backgroundColor: getStatusColor(task.status),
    color: '#ffffff',
    display: 'flex',
    alignItems: 'center',
    justifyContent: 'center',
    flexShrink: 0,
    boxShadow: task.id === currentTaskId ? `0 0 0 4px ${getStatusColor(task.status)}40` : 'none',
    cursor: onTaskClick ? 'pointer' : 'default',
    transition: 'box-shadow 0.2s',
  });

  const contentStyle = {
    flex: 1,
    marginLeft: orientation === 'vertical' ? '12px' : '0',
    marginTop: orientation === 'vertical' ? '0' : '8px',
    paddingBottom: orientation === 'vertical' ? '24px' : '0',
    paddingRight: orientation === 'vertical' ? '0' : '24px',
    minWidth: orientation === 'horizontal' ? '120px' : 'auto',
  };

  const taskNameStyle = (task) => ({
    fontSize: '14px',
    fontWeight: '600',
    color: task.id === currentTaskId ? getStatusColor(task.status) : '#111827',
    marginBottom: '4px',
    cursor: onTaskClick ? 'pointer' : 'default',
  });

  const taskMetaStyle = {
    fontSize: '12px',
    color: '#6b7280',
    display: 'flex',
    flexDirection: 'column',
    gap: '2px',
  };

  const taskMetaRowStyle = {
    display: 'flex',
    alignItems: 'center',
    gap: '4px',
  };

  const statusLabelStyle = (status) => ({
    fontSize: '11px',
    fontWeight: '500',
    color: getStatusColor(status),
    textTransform: 'capitalize',
  });

  if (tasks.length === 0) {
    return (
      <div style={{ padding: '24px', textAlign: 'center', color: '#6b7280' }}>
        No tasks in this execution
      </div>
    );
  }

  return (
    <div style={containerStyle}>
      {tasks.map((task, index) => (
        <div key={task.id} style={taskItemStyle(task, index)}>
          {/* Timeline Line */}
          <div style={timelineLineStyle(task, index)} />

          {/* Node */}
          <div style={nodeContainerStyle}>
            <div
              style={nodeStyle(task)}
              onClick={() => onTaskClick && onTaskClick(task)}
              title={task.name}
            >
              {getStatusIcon(task.status)}
            </div>
          </div>

          {/* Content */}
          <div style={contentStyle}>
            <div
              style={taskNameStyle(task)}
              onClick={() => onTaskClick && onTaskClick(task)}
            >
              {task.name}
            </div>
            <div style={taskMetaStyle}>
              <div style={taskMetaRowStyle}>
                <span style={statusLabelStyle(task.status)}>{task.status}</span>
                {task.status === 'running' && (
                  <span style={{ fontSize: '11px', color: '#3b82f6' }}>
                    (Running for {formatDuration(task.started_at, null)})
                  </span>
                )}
              </div>
              {task.started_at && (
                <div style={taskMetaRowStyle}>
                  <svg width="10" height="10" viewBox="0 0 24 24" fill="none" stroke="#9ca3af" strokeWidth="2">
                    <circle cx="12" cy="12" r="10" />
                    <polyline points="12 6 12 12 16 14" />
                  </svg>
                  <span>Started: {formatTime(task.started_at)}</span>
                </div>
              )}
              {task.completed_at && (
                <div style={taskMetaRowStyle}>
                  <svg width="10" height="10" viewBox="0 0 24 24" fill="none" stroke="#9ca3af" strokeWidth="2">
                    <polyline points="20 6 9 17 4 12" />
                  </svg>
                  <span>Duration: {formatDuration(task.started_at, task.completed_at)}</span>
                </div>
              )}
              {task.error && (
                <div style={{ ...taskMetaRowStyle, color: '#ef4444' }}>
                  <svg width="10" height="10" viewBox="0 0 24 24" fill="#ef4444">
                    <path d="M12 2C6.48 2 2 6.48 2 12s4.48 10 10 10 10-4.48 10-10S17.52 2 12 2zm1 15h-2v-2h2v2zm0-4h-2V7h2v6z" />
                  </svg>
                  <span style={{ fontSize: '11px' }}>{task.error}</span>
                </div>
              )}
            </div>
          </div>
        </div>
      ))}

      {/* CSS for animation */}
      <style>
        {`
          @keyframes spin {
            from { transform: rotate(0deg); }
            to { transform: rotate(360deg); }
          }
          .animate-spin {
            animation: spin 1s linear infinite;
          }
        `}
      </style>
    </div>
  );
};

ExecutionTimeline.propTypes = {
  tasks: PropTypes.arrayOf(
    PropTypes.shape({
      id: PropTypes.oneOfType([PropTypes.string, PropTypes.number]).isRequired,
      name: PropTypes.string.isRequired,
      status: PropTypes.oneOf(['pending', 'running', 'completed', 'failed', 'skipped', 'cancelled']).isRequired,
      started_at: PropTypes.string,
      completed_at: PropTypes.string,
      error: PropTypes.string,
    })
  ),
  currentTaskId: PropTypes.oneOfType([PropTypes.string, PropTypes.number]),
  onTaskClick: PropTypes.func,
  orientation: PropTypes.oneOf(['vertical', 'horizontal']),
};

export default ExecutionTimeline;
