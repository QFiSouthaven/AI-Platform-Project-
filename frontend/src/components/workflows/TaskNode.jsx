import React, { useState } from 'react';
import PropTypes from 'prop-types';

/**
 * Task type icons and colors
 */
const TASK_TYPES = {
  code_generation: {
    label: 'Code Generation',
    color: '#8b5cf6',
    icon: (
      <svg width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2">
        <polyline points="16 18 22 12 16 6" />
        <polyline points="8 6 2 12 8 18" />
      </svg>
    ),
  },
  data_processing: {
    label: 'Data Processing',
    color: '#06b6d4',
    icon: (
      <svg width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2">
        <ellipse cx="12" cy="5" rx="9" ry="3" />
        <path d="M21 12c0 1.66-4 3-9 3s-9-1.34-9-3" />
        <path d="M3 5v14c0 1.66 4 3 9 3s9-1.34 9-3V5" />
      </svg>
    ),
  },
  api_call: {
    label: 'API Call',
    color: '#10b981',
    icon: (
      <svg width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2">
        <circle cx="12" cy="12" r="10" />
        <line x1="2" y1="12" x2="22" y2="12" />
        <path d="M12 2a15.3 15.3 0 0 1 4 10 15.3 15.3 0 0 1-4 10 15.3 15.3 0 0 1-4-10 15.3 15.3 0 0 1 4-10z" />
      </svg>
    ),
  },
  conditional: {
    label: 'Conditional',
    color: '#f59e0b',
    icon: (
      <svg width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2">
        <line x1="6" y1="3" x2="6" y2="15" />
        <circle cx="18" cy="6" r="3" />
        <circle cx="6" cy="18" r="3" />
        <path d="M18 9a9 9 0 0 1-9 9" />
      </svg>
    ),
  },
  parallel: {
    label: 'Parallel',
    color: '#ec4899',
    icon: (
      <svg width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2">
        <line x1="8" y1="6" x2="21" y2="6" />
        <line x1="8" y1="12" x2="21" y2="12" />
        <line x1="8" y1="18" x2="21" y2="18" />
        <line x1="3" y1="6" x2="3.01" y2="6" />
        <line x1="3" y1="12" x2="3.01" y2="12" />
        <line x1="3" y1="18" x2="3.01" y2="18" />
      </svg>
    ),
  },
};

/**
 * TaskNode - Draggable task node for workflow builder
 */
const TaskNode = ({
  task,
  isSelected = false,
  isDragging = false,
  onSelect,
  onDragStart,
  onDragEnd,
  onConfigure,
  onDelete,
  onConnect,
  position = { x: 0, y: 0 },
  showConnectors = true,
}) => {
  const [isHovered, setIsHovered] = useState(false);

  const taskType = TASK_TYPES[task.type] || TASK_TYPES.code_generation;

  const nodeStyle = {
    position: 'absolute',
    left: `${position.x}px`,
    top: `${position.y}px`,
    width: '180px',
    backgroundColor: '#ffffff',
    borderRadius: '8px',
    border: `2px solid ${isSelected ? taskType.color : '#e5e7eb'}`,
    boxShadow: isDragging
      ? '0 10px 25px -5px rgba(0, 0, 0, 0.2)'
      : isSelected
      ? `0 0 0 3px ${taskType.color}30`
      : '0 1px 3px rgba(0, 0, 0, 0.1)',
    cursor: isDragging ? 'grabbing' : 'grab',
    userSelect: 'none',
    transition: isDragging ? 'none' : 'box-shadow 0.2s, border-color 0.2s',
    zIndex: isDragging ? 1000 : isSelected ? 100 : 1,
  };

  const headerStyle = {
    display: 'flex',
    alignItems: 'center',
    gap: '8px',
    padding: '10px 12px',
    backgroundColor: `${taskType.color}10`,
    borderBottom: '1px solid #f3f4f6',
    borderRadius: '6px 6px 0 0',
  };

  const iconContainerStyle = {
    display: 'flex',
    alignItems: 'center',
    justifyContent: 'center',
    width: '28px',
    height: '28px',
    borderRadius: '6px',
    backgroundColor: taskType.color,
    color: '#ffffff',
  };

  const titleStyle = {
    flex: 1,
    fontSize: '13px',
    fontWeight: '600',
    color: '#111827',
    overflow: 'hidden',
    textOverflow: 'ellipsis',
    whiteSpace: 'nowrap',
  };

  const bodyStyle = {
    padding: '10px 12px',
  };

  const typeStyle = {
    fontSize: '11px',
    color: '#6b7280',
    marginBottom: '4px',
  };

  const statusStyle = {
    display: 'flex',
    alignItems: 'center',
    gap: '4px',
    fontSize: '11px',
    color: task.status === 'valid' ? '#10b981' : task.status === 'error' ? '#ef4444' : '#6b7280',
  };

  const connectorStyle = {
    position: 'absolute',
    width: '12px',
    height: '12px',
    borderRadius: '50%',
    backgroundColor: '#ffffff',
    border: `2px solid ${taskType.color}`,
    cursor: 'crosshair',
    zIndex: 10,
  };

  const inputConnectorStyle = {
    ...connectorStyle,
    top: '-6px',
    left: '50%',
    transform: 'translateX(-50%)',
  };

  const outputConnectorStyle = {
    ...connectorStyle,
    bottom: '-6px',
    left: '50%',
    transform: 'translateX(-50%)',
  };

  const actionsStyle = {
    position: 'absolute',
    top: '-8px',
    right: '-8px',
    display: isHovered || isSelected ? 'flex' : 'none',
    gap: '4px',
  };

  const actionButtonStyle = {
    width: '24px',
    height: '24px',
    borderRadius: '50%',
    border: 'none',
    backgroundColor: '#ffffff',
    boxShadow: '0 1px 3px rgba(0, 0, 0, 0.2)',
    cursor: 'pointer',
    display: 'flex',
    alignItems: 'center',
    justifyContent: 'center',
    color: '#6b7280',
    transition: 'all 0.2s',
  };

  const handleMouseDown = (e) => {
    if (e.target.classList.contains('connector') || e.target.tagName === 'BUTTON') {
      return;
    }
    onSelect && onSelect(task);
    onDragStart && onDragStart(task, e);
  };

  const handleMouseUp = () => {
    onDragEnd && onDragEnd(task);
  };

  const handleConnectorMouseDown = (e, type) => {
    e.stopPropagation();
    onConnect && onConnect(task, type, e);
  };

  return (
    <div
      style={nodeStyle}
      onMouseDown={handleMouseDown}
      onMouseUp={handleMouseUp}
      onMouseEnter={() => setIsHovered(true)}
      onMouseLeave={() => setIsHovered(false)}
    >
      {/* Input Connector */}
      {showConnectors && (
        <div
          className="connector"
          style={inputConnectorStyle}
          onMouseDown={(e) => handleConnectorMouseDown(e, 'input')}
          title="Input"
        />
      )}

      {/* Header */}
      <div style={headerStyle}>
        <div style={iconContainerStyle}>{taskType.icon}</div>
        <span style={titleStyle} title={task.name}>
          {task.name}
        </span>
      </div>

      {/* Body */}
      <div style={bodyStyle}>
        <div style={typeStyle}>{taskType.label}</div>
        <div style={statusStyle}>
          {task.status === 'valid' && (
            <svg width="10" height="10" viewBox="0 0 24 24" fill="currentColor">
              <path d="M9 16.17L4.83 12l-1.42 1.41L9 19 21 7l-1.41-1.41z" />
            </svg>
          )}
          {task.status === 'error' && (
            <svg width="10" height="10" viewBox="0 0 24 24" fill="currentColor">
              <path d="M12 2C6.48 2 2 6.48 2 12s4.48 10 10 10 10-4.48 10-10S17.52 2 12 2zm1 15h-2v-2h2v2zm0-4h-2V7h2v6z" />
            </svg>
          )}
          {task.status === 'valid' ? 'Configured' : task.status === 'error' ? 'Needs configuration' : 'Draft'}
        </div>
      </div>

      {/* Output Connector */}
      {showConnectors && (
        <div
          className="connector"
          style={outputConnectorStyle}
          onMouseDown={(e) => handleConnectorMouseDown(e, 'output')}
          title="Output"
        />
      )}

      {/* Action Buttons */}
      <div style={actionsStyle}>
        <button
          style={actionButtonStyle}
          onClick={(e) => {
            e.stopPropagation();
            onConfigure && onConfigure(task);
          }}
          title="Configure"
        >
          <svg width="12" height="12" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2">
            <circle cx="12" cy="12" r="3" />
            <path d="M19.4 15a1.65 1.65 0 0 0 .33 1.82l.06.06a2 2 0 0 1 0 2.83 2 2 0 0 1-2.83 0l-.06-.06a1.65 1.65 0 0 0-1.82-.33 1.65 1.65 0 0 0-1 1.51V21a2 2 0 0 1-2 2 2 2 0 0 1-2-2v-.09A1.65 1.65 0 0 0 9 19.4a1.65 1.65 0 0 0-1.82.33l-.06.06a2 2 0 0 1-2.83 0 2 2 0 0 1 0-2.83l.06-.06a1.65 1.65 0 0 0 .33-1.82 1.65 1.65 0 0 0-1.51-1H3a2 2 0 0 1-2-2 2 2 0 0 1 2-2h.09A1.65 1.65 0 0 0 4.6 9a1.65 1.65 0 0 0-.33-1.82l-.06-.06a2 2 0 0 1 0-2.83 2 2 0 0 1 2.83 0l.06.06a1.65 1.65 0 0 0 1.82.33H9a1.65 1.65 0 0 0 1-1.51V3a2 2 0 0 1 2-2 2 2 0 0 1 2 2v.09a1.65 1.65 0 0 0 1 1.51 1.65 1.65 0 0 0 1.82-.33l.06-.06a2 2 0 0 1 2.83 0 2 2 0 0 1 0 2.83l-.06.06a1.65 1.65 0 0 0-.33 1.82V9a1.65 1.65 0 0 0 1.51 1H21a2 2 0 0 1 2 2 2 2 0 0 1-2 2h-.09a1.65 1.65 0 0 0-1.51 1z" />
          </svg>
        </button>
        <button
          style={{ ...actionButtonStyle, color: '#ef4444' }}
          onClick={(e) => {
            e.stopPropagation();
            onDelete && onDelete(task);
          }}
          title="Delete"
        >
          <svg width="12" height="12" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2">
            <line x1="18" y1="6" x2="6" y2="18" />
            <line x1="6" y1="6" x2="18" y2="18" />
          </svg>
        </button>
      </div>
    </div>
  );
};

TaskNode.propTypes = {
  task: PropTypes.shape({
    id: PropTypes.oneOfType([PropTypes.string, PropTypes.number]).isRequired,
    name: PropTypes.string.isRequired,
    type: PropTypes.oneOf(['code_generation', 'data_processing', 'api_call', 'conditional', 'parallel']).isRequired,
    status: PropTypes.string,
  }).isRequired,
  isSelected: PropTypes.bool,
  isDragging: PropTypes.bool,
  onSelect: PropTypes.func,
  onDragStart: PropTypes.func,
  onDragEnd: PropTypes.func,
  onConfigure: PropTypes.func,
  onDelete: PropTypes.func,
  onConnect: PropTypes.func,
  position: PropTypes.shape({
    x: PropTypes.number,
    y: PropTypes.number,
  }),
  showConnectors: PropTypes.bool,
};

export { TASK_TYPES };
export default TaskNode;
