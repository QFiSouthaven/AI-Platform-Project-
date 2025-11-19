import React from 'react';
import PropTypes from 'prop-types';

/**
 * WorkflowCard - Displays a workflow in card format
 */
const WorkflowCard = ({
  workflow,
  onRun,
  onEdit,
  onClone,
  onDelete,
  onView,
  isCompact = false,
}) => {
  const getStatusColor = (status) => {
    const colors = {
      active: '#10b981',
      inactive: '#6b7280',
      running: '#3b82f6',
      failed: '#ef4444',
      completed: '#10b981',
      pending: '#f59e0b',
    };
    return colors[status] || '#6b7280';
  };

  const getStatusLabel = (status) => {
    const labels = {
      active: 'Active',
      inactive: 'Inactive',
      running: 'Running',
      failed: 'Failed',
      completed: 'Completed',
      pending: 'Pending',
    };
    return labels[status] || status;
  };

  const formatDate = (dateString) => {
    if (!dateString) return 'Never';
    const date = new Date(dateString);
    return date.toLocaleDateString('en-US', {
      month: 'short',
      day: 'numeric',
      hour: '2-digit',
      minute: '2-digit',
    });
  };

  const formatSuccessRate = (rate) => {
    if (rate === null || rate === undefined) return 'N/A';
    return `${Math.round(rate * 100)}%`;
  };

  const cardStyle = {
    backgroundColor: '#ffffff',
    borderRadius: '8px',
    border: '1px solid #e5e7eb',
    padding: isCompact ? '12px' : '16px',
    transition: 'box-shadow 0.2s, border-color 0.2s',
    cursor: 'pointer',
  };

  const headerStyle = {
    display: 'flex',
    justifyContent: 'space-between',
    alignItems: 'flex-start',
    marginBottom: '12px',
  };

  const titleStyle = {
    fontSize: isCompact ? '14px' : '16px',
    fontWeight: '600',
    color: '#111827',
    margin: 0,
    overflow: 'hidden',
    textOverflow: 'ellipsis',
    whiteSpace: 'nowrap',
    maxWidth: '200px',
  };

  const statusBadgeStyle = {
    display: 'inline-flex',
    alignItems: 'center',
    padding: '2px 8px',
    borderRadius: '12px',
    fontSize: '12px',
    fontWeight: '500',
    backgroundColor: `${getStatusColor(workflow.status)}20`,
    color: getStatusColor(workflow.status),
  };

  const statusDotStyle = {
    width: '6px',
    height: '6px',
    borderRadius: '50%',
    backgroundColor: getStatusColor(workflow.status),
    marginRight: '6px',
  };

  const descriptionStyle = {
    fontSize: '13px',
    color: '#6b7280',
    marginBottom: '12px',
    overflow: 'hidden',
    textOverflow: 'ellipsis',
    display: '-webkit-box',
    WebkitLineClamp: 2,
    WebkitBoxOrient: 'vertical',
    lineHeight: '1.4',
  };

  const metricsStyle = {
    display: 'grid',
    gridTemplateColumns: 'repeat(3, 1fr)',
    gap: '8px',
    marginBottom: '12px',
  };

  const metricItemStyle = {
    textAlign: 'center',
    padding: '8px',
    backgroundColor: '#f9fafb',
    borderRadius: '6px',
  };

  const metricLabelStyle = {
    fontSize: '11px',
    color: '#6b7280',
    marginBottom: '4px',
  };

  const metricValueStyle = {
    fontSize: '14px',
    fontWeight: '600',
    color: '#111827',
  };

  const actionsStyle = {
    display: 'flex',
    gap: '8px',
    borderTop: '1px solid #f3f4f6',
    paddingTop: '12px',
  };

  const buttonStyle = {
    flex: 1,
    padding: '6px 12px',
    borderRadius: '6px',
    border: '1px solid #e5e7eb',
    backgroundColor: '#ffffff',
    fontSize: '12px',
    fontWeight: '500',
    cursor: 'pointer',
    transition: 'all 0.2s',
    display: 'flex',
    alignItems: 'center',
    justifyContent: 'center',
    gap: '4px',
  };

  const primaryButtonStyle = {
    ...buttonStyle,
    backgroundColor: '#3b82f6',
    borderColor: '#3b82f6',
    color: '#ffffff',
  };

  const dangerButtonStyle = {
    ...buttonStyle,
    color: '#ef4444',
  };

  const handleCardClick = (e) => {
    if (e.target.tagName !== 'BUTTON') {
      onView && onView(workflow);
    }
  };

  return (
    <div
      style={cardStyle}
      onClick={handleCardClick}
      onMouseEnter={(e) => {
        e.currentTarget.style.boxShadow = '0 4px 6px -1px rgba(0, 0, 0, 0.1)';
        e.currentTarget.style.borderColor = '#d1d5db';
      }}
      onMouseLeave={(e) => {
        e.currentTarget.style.boxShadow = 'none';
        e.currentTarget.style.borderColor = '#e5e7eb';
      }}
    >
      {/* Header */}
      <div style={headerStyle}>
        <h3 style={titleStyle} title={workflow.name}>
          {workflow.name}
        </h3>
        <span style={statusBadgeStyle}>
          <span style={statusDotStyle} />
          {getStatusLabel(workflow.status)}
        </span>
      </div>

      {/* Description */}
      {workflow.description && !isCompact && (
        <p style={descriptionStyle}>{workflow.description}</p>
      )}

      {/* Metrics */}
      <div style={metricsStyle}>
        <div style={metricItemStyle}>
          <div style={metricLabelStyle}>Last Run</div>
          <div style={metricValueStyle}>{formatDate(workflow.last_run)}</div>
        </div>
        <div style={metricItemStyle}>
          <div style={metricLabelStyle}>Success Rate</div>
          <div style={metricValueStyle}>
            {formatSuccessRate(workflow.success_rate)}
          </div>
        </div>
        <div style={metricItemStyle}>
          <div style={metricLabelStyle}>Tasks</div>
          <div style={metricValueStyle}>{workflow.task_count || 0}</div>
        </div>
      </div>

      {/* Actions */}
      <div style={actionsStyle}>
        <button
          style={primaryButtonStyle}
          onClick={(e) => {
            e.stopPropagation();
            onRun && onRun(workflow);
          }}
          disabled={workflow.status === 'running'}
        >
          <svg width="12" height="12" viewBox="0 0 24 24" fill="currentColor">
            <path d="M8 5v14l11-7z" />
          </svg>
          Run
        </button>
        <button
          style={buttonStyle}
          onClick={(e) => {
            e.stopPropagation();
            onEdit && onEdit(workflow);
          }}
        >
          <svg width="12" height="12" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2">
            <path d="M11 4H4a2 2 0 0 0-2 2v14a2 2 0 0 0 2 2h14a2 2 0 0 0 2-2v-7" />
            <path d="M18.5 2.5a2.121 2.121 0 0 1 3 3L12 15l-4 1 1-4 9.5-9.5z" />
          </svg>
          Edit
        </button>
        <button
          style={buttonStyle}
          onClick={(e) => {
            e.stopPropagation();
            onClone && onClone(workflow);
          }}
        >
          <svg width="12" height="12" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2">
            <rect x="9" y="9" width="13" height="13" rx="2" ry="2" />
            <path d="M5 15H4a2 2 0 0 1-2-2V4a2 2 0 0 1 2-2h9a2 2 0 0 1 2 2v1" />
          </svg>
          Clone
        </button>
        <button
          style={dangerButtonStyle}
          onClick={(e) => {
            e.stopPropagation();
            onDelete && onDelete(workflow);
          }}
        >
          <svg width="12" height="12" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2">
            <polyline points="3 6 5 6 21 6" />
            <path d="M19 6v14a2 2 0 0 1-2 2H7a2 2 0 0 1-2-2V6m3 0V4a2 2 0 0 1 2-2h4a2 2 0 0 1 2 2v2" />
          </svg>
        </button>
      </div>
    </div>
  );
};

WorkflowCard.propTypes = {
  workflow: PropTypes.shape({
    id: PropTypes.oneOfType([PropTypes.string, PropTypes.number]).isRequired,
    name: PropTypes.string.isRequired,
    description: PropTypes.string,
    status: PropTypes.string.isRequired,
    last_run: PropTypes.string,
    success_rate: PropTypes.number,
    task_count: PropTypes.number,
  }).isRequired,
  onRun: PropTypes.func,
  onEdit: PropTypes.func,
  onClone: PropTypes.func,
  onDelete: PropTypes.func,
  onView: PropTypes.func,
  isCompact: PropTypes.bool,
};

export default WorkflowCard;
