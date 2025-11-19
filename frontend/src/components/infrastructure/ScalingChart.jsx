import React from 'react';
import PropTypes from 'prop-types';

/**
 * ScalingChart - Display scaling history as a line chart
 * Shows worker count changes over time
 */
const ScalingChart = ({
  data = [],
  height = 200,
  showGrid = true,
  showTooltip = true,
}) => {
  const chartPadding = { top: 20, right: 40, bottom: 40, left: 50 };
  const chartWidth = 600;
  const chartHeight = height;

  const innerWidth = chartWidth - chartPadding.left - chartPadding.right;
  const innerHeight = chartHeight - chartPadding.top - chartPadding.bottom;

  // Process data
  const processedData = data.length > 0 ? data : [
    { timestamp: new Date().toISOString(), workers: 0 }
  ];

  const values = processedData.map(d => d.workers);
  const minValue = Math.min(...values, 0);
  const maxValue = Math.max(...values, 10);
  const valueRange = maxValue - minValue || 1;

  // Calculate scales
  const xScale = (index) => (index / (processedData.length - 1 || 1)) * innerWidth;
  const yScale = (value) => innerHeight - ((value - minValue) / valueRange) * innerHeight;

  // Generate path
  const generatePath = () => {
    if (processedData.length < 2) return '';

    let path = `M ${xScale(0)} ${yScale(processedData[0].workers)}`;
    for (let i = 1; i < processedData.length; i++) {
      path += ` L ${xScale(i)} ${yScale(processedData[i].workers)}`;
    }
    return path;
  };

  // Generate area path
  const generateAreaPath = () => {
    if (processedData.length < 2) return '';

    let path = `M ${xScale(0)} ${innerHeight}`;
    path += ` L ${xScale(0)} ${yScale(processedData[0].workers)}`;
    for (let i = 1; i < processedData.length; i++) {
      path += ` L ${xScale(i)} ${yScale(processedData[i].workers)}`;
    }
    path += ` L ${xScale(processedData.length - 1)} ${innerHeight} Z`;
    return path;
  };

  // Format timestamp
  const formatTime = (timestamp) => {
    const date = new Date(timestamp);
    return date.toLocaleTimeString([], { hour: '2-digit', minute: '2-digit' });
  };

  // Generate Y-axis ticks
  const yTicks = [];
  const tickCount = 5;
  for (let i = 0; i <= tickCount; i++) {
    const value = minValue + (valueRange * i) / tickCount;
    yTicks.push(Math.round(value));
  }

  // Generate X-axis labels
  const xLabels = [];
  const labelCount = Math.min(6, processedData.length);
  for (let i = 0; i < labelCount; i++) {
    const index = Math.floor((i / (labelCount - 1 || 1)) * (processedData.length - 1));
    xLabels.push({
      index,
      label: formatTime(processedData[index].timestamp),
    });
  }

  const [hoveredPoint, setHoveredPoint] = React.useState(null);

  return (
    <div
      className="scaling-chart"
      style={{
        width: '100%',
        overflowX: 'auto',
      }}
    >
      <svg
        width={chartWidth}
        height={chartHeight}
        style={{ display: 'block' }}
      >
        {/* Grid lines */}
        {showGrid && (
          <g className="grid">
            {yTicks.map((tick, i) => (
              <line
                key={`grid-${i}`}
                x1={chartPadding.left}
                y1={chartPadding.top + yScale(tick)}
                x2={chartPadding.left + innerWidth}
                y2={chartPadding.top + yScale(tick)}
                stroke="#e5e7eb"
                strokeDasharray="4,4"
              />
            ))}
          </g>
        )}

        {/* Area fill */}
        <path
          d={generateAreaPath()}
          fill="url(#areaGradient)"
          transform={`translate(${chartPadding.left}, ${chartPadding.top})`}
        />

        {/* Line */}
        <path
          d={generatePath()}
          fill="none"
          stroke="#3b82f6"
          strokeWidth="2"
          transform={`translate(${chartPadding.left}, ${chartPadding.top})`}
        />

        {/* Data points */}
        {processedData.map((point, i) => (
          <circle
            key={`point-${i}`}
            cx={chartPadding.left + xScale(i)}
            cy={chartPadding.top + yScale(point.workers)}
            r={hoveredPoint === i ? 6 : 4}
            fill="#3b82f6"
            stroke="#ffffff"
            strokeWidth="2"
            onMouseEnter={() => setHoveredPoint(i)}
            onMouseLeave={() => setHoveredPoint(null)}
            style={{ cursor: 'pointer', transition: 'r 0.2s' }}
          />
        ))}

        {/* Scaling event markers */}
        {processedData.map((point, i) => {
          if (point.event_type) {
            const isScaleUp = point.event_type === 'scale_up';
            return (
              <g key={`event-${i}`}>
                <circle
                  cx={chartPadding.left + xScale(i)}
                  cy={chartPadding.top + yScale(point.workers)}
                  r={8}
                  fill={isScaleUp ? '#10b981' : '#f59e0b'}
                  opacity={0.3}
                />
              </g>
            );
          }
          return null;
        })}

        {/* Y-axis */}
        <g className="y-axis">
          <line
            x1={chartPadding.left}
            y1={chartPadding.top}
            x2={chartPadding.left}
            y2={chartPadding.top + innerHeight}
            stroke="#d1d5db"
          />
          {yTicks.map((tick, i) => (
            <g key={`y-tick-${i}`}>
              <line
                x1={chartPadding.left - 5}
                y1={chartPadding.top + yScale(tick)}
                x2={chartPadding.left}
                y2={chartPadding.top + yScale(tick)}
                stroke="#d1d5db"
              />
              <text
                x={chartPadding.left - 10}
                y={chartPadding.top + yScale(tick)}
                textAnchor="end"
                dominantBaseline="middle"
                fontSize="11"
                fill="#6b7280"
              >
                {tick}
              </text>
            </g>
          ))}
          <text
            x={15}
            y={chartPadding.top + innerHeight / 2}
            textAnchor="middle"
            dominantBaseline="middle"
            fontSize="12"
            fill="#6b7280"
            transform={`rotate(-90, 15, ${chartPadding.top + innerHeight / 2})`}
          >
            Workers
          </text>
        </g>

        {/* X-axis */}
        <g className="x-axis">
          <line
            x1={chartPadding.left}
            y1={chartPadding.top + innerHeight}
            x2={chartPadding.left + innerWidth}
            y2={chartPadding.top + innerHeight}
            stroke="#d1d5db"
          />
          {xLabels.map(({ index, label }, i) => (
            <text
              key={`x-label-${i}`}
              x={chartPadding.left + xScale(index)}
              y={chartPadding.top + innerHeight + 20}
              textAnchor="middle"
              fontSize="11"
              fill="#6b7280"
            >
              {label}
            </text>
          ))}
        </g>

        {/* Gradient definition */}
        <defs>
          <linearGradient id="areaGradient" x1="0" x2="0" y1="0" y2="1">
            <stop offset="0%" stopColor="#3b82f6" stopOpacity="0.3" />
            <stop offset="100%" stopColor="#3b82f6" stopOpacity="0.05" />
          </linearGradient>
        </defs>

        {/* Tooltip */}
        {showTooltip && hoveredPoint !== null && (
          <g className="tooltip">
            <rect
              x={chartPadding.left + xScale(hoveredPoint) - 60}
              y={chartPadding.top + yScale(processedData[hoveredPoint].workers) - 45}
              width="120"
              height="35"
              fill="#1f2937"
              rx="4"
            />
            <text
              x={chartPadding.left + xScale(hoveredPoint)}
              y={chartPadding.top + yScale(processedData[hoveredPoint].workers) - 30}
              textAnchor="middle"
              fontSize="11"
              fill="#ffffff"
            >
              Workers: {processedData[hoveredPoint].workers}
            </text>
            <text
              x={chartPadding.left + xScale(hoveredPoint)}
              y={chartPadding.top + yScale(processedData[hoveredPoint].workers) - 16}
              textAnchor="middle"
              fontSize="10"
              fill="#9ca3af"
            >
              {formatTime(processedData[hoveredPoint].timestamp)}
            </text>
          </g>
        )}
      </svg>

      {/* Legend */}
      {data.some(d => d.event_type) && (
        <div
          className="chart-legend"
          style={{
            display: 'flex',
            justifyContent: 'center',
            gap: '16px',
            marginTop: '8px',
            fontSize: '12px',
          }}
        >
          <div style={{ display: 'flex', alignItems: 'center', gap: '4px' }}>
            <span
              style={{
                width: '12px',
                height: '12px',
                borderRadius: '50%',
                backgroundColor: '#10b981',
              }}
            />
            Scale Up
          </div>
          <div style={{ display: 'flex', alignItems: 'center', gap: '4px' }}>
            <span
              style={{
                width: '12px',
                height: '12px',
                borderRadius: '50%',
                backgroundColor: '#f59e0b',
              }}
            />
            Scale Down
          </div>
        </div>
      )}
    </div>
  );
};

ScalingChart.propTypes = {
  data: PropTypes.arrayOf(
    PropTypes.shape({
      timestamp: PropTypes.string.isRequired,
      workers: PropTypes.number.isRequired,
      event_type: PropTypes.oneOf(['scale_up', 'scale_down', 'manual']),
    })
  ),
  height: PropTypes.number,
  showGrid: PropTypes.bool,
  showTooltip: PropTypes.bool,
};

export default ScalingChart;
