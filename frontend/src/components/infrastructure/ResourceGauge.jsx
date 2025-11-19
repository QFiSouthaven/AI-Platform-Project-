import React from 'react';
import PropTypes from 'prop-types';

/**
 * ResourceGauge - Circular gauge component for displaying resource usage
 * Color coded: green (healthy), yellow (warning), red (critical)
 */
const ResourceGauge = ({
  value,
  maxValue = 100,
  label,
  unit = '%',
  size = 120,
  strokeWidth = 10,
  warningThreshold = 70,
  criticalThreshold = 90,
}) => {
  const percentage = Math.min((value / maxValue) * 100, 100);
  const radius = (size - strokeWidth) / 2;
  const circumference = radius * 2 * Math.PI;
  const strokeDashoffset = circumference - (percentage / 100) * circumference;

  // Determine color based on thresholds
  const getColor = () => {
    if (percentage >= criticalThreshold) return '#ef4444'; // Red - Critical
    if (percentage >= warningThreshold) return '#f59e0b'; // Yellow - Warning
    return '#10b981'; // Green - Healthy
  };

  const getBackgroundColor = () => {
    if (percentage >= criticalThreshold) return '#fecaca'; // Light red
    if (percentage >= warningThreshold) return '#fef3c7'; // Light yellow
    return '#d1fae5'; // Light green
  };

  const color = getColor();
  const backgroundColor = getBackgroundColor();

  return (
    <div className="resource-gauge" style={{ width: size, height: size }}>
      <svg width={size} height={size} className="gauge-svg">
        {/* Background circle */}
        <circle
          cx={size / 2}
          cy={size / 2}
          r={radius}
          fill="none"
          stroke={backgroundColor}
          strokeWidth={strokeWidth}
        />
        {/* Progress circle */}
        <circle
          cx={size / 2}
          cy={size / 2}
          r={radius}
          fill="none"
          stroke={color}
          strokeWidth={strokeWidth}
          strokeDasharray={circumference}
          strokeDashoffset={strokeDashoffset}
          strokeLinecap="round"
          transform={`rotate(-90 ${size / 2} ${size / 2})`}
          style={{ transition: 'stroke-dashoffset 0.5s ease' }}
        />
      </svg>
      <div
        className="gauge-content"
        style={{
          position: 'absolute',
          top: '50%',
          left: '50%',
          transform: 'translate(-50%, -50%)',
          textAlign: 'center',
        }}
      >
        <div
          className="gauge-value"
          style={{
            fontSize: size / 4,
            fontWeight: 'bold',
            color: color,
          }}
        >
          {Math.round(value)}
          <span style={{ fontSize: size / 8 }}>{unit}</span>
        </div>
        {label && (
          <div
            className="gauge-label"
            style={{
              fontSize: size / 10,
              color: '#6b7280',
              marginTop: 4,
            }}
          >
            {label}
          </div>
        )}
      </div>

      <style>{`
        .resource-gauge {
          position: relative;
          display: inline-flex;
          align-items: center;
          justify-content: center;
        }
        .gauge-svg {
          transform: rotate(0deg);
        }
      `}</style>
    </div>
  );
};

ResourceGauge.propTypes = {
  value: PropTypes.number.isRequired,
  maxValue: PropTypes.number,
  label: PropTypes.string,
  unit: PropTypes.string,
  size: PropTypes.number,
  strokeWidth: PropTypes.number,
  warningThreshold: PropTypes.number,
  criticalThreshold: PropTypes.number,
};

export default ResourceGauge;
