import React from 'react';
import PropTypes from 'prop-types';
import ResourceGauge from './ResourceGauge';

/**
 * NodeCard - Display card for worker node information
 * Shows node details, health status, and resource utilization
 */
const NodeCard = ({
  node,
  onSelect,
  isSelected = false,
}) => {
  const {
    id,
    name,
    status,
    cpu_usage = 0,
    memory_usage = 0,
    gpu_usage = 0,
    gpu_available = false,
    tasks_running = 0,
    tasks_completed = 0,
    uptime,
    ip_address,
  } = node;

  // Status colors
  const getStatusColor = () => {
    switch (status) {
      case 'healthy':
      case 'running':
        return '#10b981'; // Green
      case 'warning':
      case 'degraded':
        return '#f59e0b'; // Yellow
      case 'critical':
      case 'unhealthy':
      case 'offline':
        return '#ef4444'; // Red
      case 'starting':
      case 'stopping':
        return '#3b82f6'; // Blue
      default:
        return '#6b7280'; // Gray
    }
  };

  const statusColor = getStatusColor();

  const formatUptime = (seconds) => {
    if (!seconds) return 'N/A';
    const days = Math.floor(seconds / 86400);
    const hours = Math.floor((seconds % 86400) / 3600);
    const minutes = Math.floor((seconds % 3600) / 60);

    if (days > 0) return `${days}d ${hours}h`;
    if (hours > 0) return `${hours}h ${minutes}m`;
    return `${minutes}m`;
  };

  return (
    <div
      className={`node-card ${isSelected ? 'selected' : ''}`}
      onClick={() => onSelect && onSelect(node)}
      style={{
        border: `2px solid ${isSelected ? '#3b82f6' : '#e5e7eb'}`,
        borderRadius: '8px',
        padding: '16px',
        backgroundColor: '#ffffff',
        cursor: onSelect ? 'pointer' : 'default',
        transition: 'all 0.2s ease',
        boxShadow: isSelected ? '0 4px 12px rgba(59, 130, 246, 0.3)' : '0 1px 3px rgba(0, 0, 0, 0.1)',
      }}
    >
      {/* Header */}
      <div className="node-header" style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', marginBottom: '12px' }}>
        <div>
          <h3 style={{ margin: 0, fontSize: '16px', fontWeight: '600' }}>{name || `Node ${id}`}</h3>
          {ip_address && (
            <span style={{ fontSize: '12px', color: '#6b7280' }}>{ip_address}</span>
          )}
        </div>
        <div
          className="status-badge"
          style={{
            display: 'flex',
            alignItems: 'center',
            gap: '6px',
            padding: '4px 8px',
            borderRadius: '12px',
            backgroundColor: `${statusColor}20`,
            color: statusColor,
            fontSize: '12px',
            fontWeight: '500',
            textTransform: 'capitalize',
          }}
        >
          <span
            style={{
              width: '8px',
              height: '8px',
              borderRadius: '50%',
              backgroundColor: statusColor,
            }}
          />
          {status}
        </div>
      </div>

      {/* Resource Gauges */}
      <div
        className="resource-gauges"
        style={{
          display: 'flex',
          justifyContent: 'space-around',
          marginBottom: '16px',
        }}
      >
        <ResourceGauge
          value={cpu_usage}
          label="CPU"
          size={60}
          strokeWidth={6}
        />
        <ResourceGauge
          value={memory_usage}
          label="Memory"
          size={60}
          strokeWidth={6}
        />
        {gpu_available && (
          <ResourceGauge
            value={gpu_usage}
            label="GPU"
            size={60}
            strokeWidth={6}
          />
        )}
      </div>

      {/* Stats */}
      <div
        className="node-stats"
        style={{
          display: 'grid',
          gridTemplateColumns: '1fr 1fr',
          gap: '8px',
          fontSize: '12px',
        }}
      >
        <div style={{ display: 'flex', justifyContent: 'space-between' }}>
          <span style={{ color: '#6b7280' }}>Running:</span>
          <span style={{ fontWeight: '500' }}>{tasks_running}</span>
        </div>
        <div style={{ display: 'flex', justifyContent: 'space-between' }}>
          <span style={{ color: '#6b7280' }}>Completed:</span>
          <span style={{ fontWeight: '500' }}>{tasks_completed}</span>
        </div>
        <div style={{ display: 'flex', justifyContent: 'space-between', gridColumn: '1 / -1' }}>
          <span style={{ color: '#6b7280' }}>Uptime:</span>
          <span style={{ fontWeight: '500' }}>{formatUptime(uptime)}</span>
        </div>
      </div>

      <style>{`
        .node-card:hover {
          border-color: #3b82f6;
          box-shadow: 0 4px 12px rgba(0, 0, 0, 0.15);
        }
      `}</style>
    </div>
  );
};

NodeCard.propTypes = {
  node: PropTypes.shape({
    id: PropTypes.oneOfType([PropTypes.string, PropTypes.number]).isRequired,
    name: PropTypes.string,
    status: PropTypes.string.isRequired,
    cpu_usage: PropTypes.number,
    memory_usage: PropTypes.number,
    gpu_usage: PropTypes.number,
    gpu_available: PropTypes.bool,
    tasks_running: PropTypes.number,
    tasks_completed: PropTypes.number,
    uptime: PropTypes.number,
    ip_address: PropTypes.string,
  }).isRequired,
  onSelect: PropTypes.func,
  isSelected: PropTypes.bool,
};

export default NodeCard;
