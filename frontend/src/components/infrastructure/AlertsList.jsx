import React from 'react';
import PropTypes from 'prop-types';

/**
 * AlertsList - Display list of infrastructure alerts
 * Color coded by severity: critical (red), warning (yellow), info (blue)
 */
const AlertsList = ({
  alerts = [],
  onAcknowledge,
  onDismiss,
  maxHeight = '400px',
  showActions = true,
}) => {
  const getSeverityConfig = (severity) => {
    switch (severity) {
      case 'critical':
        return {
          color: '#ef4444',
          backgroundColor: '#fef2f2',
          borderColor: '#fecaca',
          icon: '!',
        };
      case 'warning':
        return {
          color: '#f59e0b',
          backgroundColor: '#fffbeb',
          borderColor: '#fef3c7',
          icon: '!',
        };
      case 'info':
      default:
        return {
          color: '#3b82f6',
          backgroundColor: '#eff6ff',
          borderColor: '#dbeafe',
          icon: 'i',
        };
    }
  };

  const formatTimestamp = (timestamp) => {
    if (!timestamp) return '';
    const date = new Date(timestamp);
    const now = new Date();
    const diff = now - date;

    // Less than 1 minute
    if (diff < 60000) return 'Just now';
    // Less than 1 hour
    if (diff < 3600000) return `${Math.floor(diff / 60000)}m ago`;
    // Less than 24 hours
    if (diff < 86400000) return `${Math.floor(diff / 3600000)}h ago`;
    // More than 24 hours
    return date.toLocaleDateString();
  };

  if (alerts.length === 0) {
    return (
      <div
        className="alerts-empty"
        style={{
          padding: '24px',
          textAlign: 'center',
          color: '#6b7280',
          backgroundColor: '#f9fafb',
          borderRadius: '8px',
        }}
      >
        <div style={{ fontSize: '24px', marginBottom: '8px' }}>No alerts</div>
        <div style={{ fontSize: '14px' }}>All systems operational</div>
      </div>
    );
  }

  return (
    <div
      className="alerts-list"
      style={{
        maxHeight,
        overflowY: 'auto',
      }}
    >
      {alerts.map((alert) => {
        const config = getSeverityConfig(alert.severity);
        return (
          <div
            key={alert.id}
            className="alert-item"
            style={{
              display: 'flex',
              alignItems: 'flex-start',
              padding: '12px',
              marginBottom: '8px',
              backgroundColor: config.backgroundColor,
              border: `1px solid ${config.borderColor}`,
              borderRadius: '8px',
              borderLeft: `4px solid ${config.color}`,
            }}
          >
            {/* Severity Icon */}
            <div
              className="alert-icon"
              style={{
                width: '24px',
                height: '24px',
                borderRadius: '50%',
                backgroundColor: config.color,
                color: '#ffffff',
                display: 'flex',
                alignItems: 'center',
                justifyContent: 'center',
                fontSize: '12px',
                fontWeight: 'bold',
                flexShrink: 0,
                marginRight: '12px',
              }}
            >
              {config.icon}
            </div>

            {/* Alert Content */}
            <div style={{ flex: 1, minWidth: 0 }}>
              <div
                className="alert-header"
                style={{
                  display: 'flex',
                  justifyContent: 'space-between',
                  alignItems: 'flex-start',
                  marginBottom: '4px',
                }}
              >
                <span
                  style={{
                    fontWeight: '600',
                    fontSize: '14px',
                    color: '#111827',
                  }}
                >
                  {alert.title}
                </span>
                <span
                  style={{
                    fontSize: '12px',
                    color: '#6b7280',
                    whiteSpace: 'nowrap',
                    marginLeft: '8px',
                  }}
                >
                  {formatTimestamp(alert.timestamp)}
                </span>
              </div>

              <p
                style={{
                  margin: '0 0 8px 0',
                  fontSize: '13px',
                  color: '#4b5563',
                  lineHeight: '1.4',
                }}
              >
                {alert.message}
              </p>

              {/* Source and Actions */}
              <div
                style={{
                  display: 'flex',
                  justifyContent: 'space-between',
                  alignItems: 'center',
                }}
              >
                {alert.source && (
                  <span
                    style={{
                      fontSize: '11px',
                      color: '#9ca3af',
                      backgroundColor: '#f3f4f6',
                      padding: '2px 6px',
                      borderRadius: '4px',
                    }}
                  >
                    {alert.source}
                  </span>
                )}

                {showActions && (
                  <div className="alert-actions" style={{ display: 'flex', gap: '8px' }}>
                    {!alert.acknowledged && onAcknowledge && (
                      <button
                        onClick={(e) => {
                          e.stopPropagation();
                          onAcknowledge(alert.id);
                        }}
                        style={{
                          padding: '4px 8px',
                          fontSize: '11px',
                          backgroundColor: 'transparent',
                          border: `1px solid ${config.color}`,
                          borderRadius: '4px',
                          color: config.color,
                          cursor: 'pointer',
                          transition: 'all 0.2s',
                        }}
                      >
                        Acknowledge
                      </button>
                    )}
                    {onDismiss && (
                      <button
                        onClick={(e) => {
                          e.stopPropagation();
                          onDismiss(alert.id);
                        }}
                        style={{
                          padding: '4px 8px',
                          fontSize: '11px',
                          backgroundColor: 'transparent',
                          border: '1px solid #d1d5db',
                          borderRadius: '4px',
                          color: '#6b7280',
                          cursor: 'pointer',
                          transition: 'all 0.2s',
                        }}
                      >
                        Dismiss
                      </button>
                    )}
                  </div>
                )}
              </div>

              {alert.acknowledged && (
                <div
                  style={{
                    marginTop: '8px',
                    fontSize: '11px',
                    color: '#10b981',
                  }}
                >
                  Acknowledged {alert.acknowledged_by && `by ${alert.acknowledged_by}`}
                </div>
              )}
            </div>
          </div>
        );
      })}

      <style>{`
        .alerts-list::-webkit-scrollbar {
          width: 6px;
        }
        .alerts-list::-webkit-scrollbar-track {
          background: #f1f5f9;
          border-radius: 3px;
        }
        .alerts-list::-webkit-scrollbar-thumb {
          background: #cbd5e1;
          border-radius: 3px;
        }
        .alert-item:hover {
          box-shadow: 0 2px 8px rgba(0, 0, 0, 0.08);
        }
        .alert-actions button:hover {
          opacity: 0.8;
        }
      `}</style>
    </div>
  );
};

AlertsList.propTypes = {
  alerts: PropTypes.arrayOf(
    PropTypes.shape({
      id: PropTypes.oneOfType([PropTypes.string, PropTypes.number]).isRequired,
      title: PropTypes.string.isRequired,
      message: PropTypes.string.isRequired,
      severity: PropTypes.oneOf(['critical', 'warning', 'info']).isRequired,
      timestamp: PropTypes.string,
      source: PropTypes.string,
      acknowledged: PropTypes.bool,
      acknowledged_by: PropTypes.string,
    })
  ),
  onAcknowledge: PropTypes.func,
  onDismiss: PropTypes.func,
  maxHeight: PropTypes.string,
  showActions: PropTypes.bool,
};

export default AlertsList;
