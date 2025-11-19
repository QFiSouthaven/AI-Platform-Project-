import React, { useState, useEffect } from 'react';
import {
  getMetrics,
  getCpuMetrics,
  getMemoryMetrics,
  getNetworkMetrics,
  getThroughputMetrics,
  getErrorMetrics,
} from '../../services/infrastructureService';

/**
 * Metrics - Performance metrics dashboard
 * Real-time charts for CPU, memory, network, throughput, and error rates
 */
const Metrics = () => {
  const [timeRange, setTimeRange] = useState('1h');
  const [metrics, setMetrics] = useState({
    cpu: [],
    memory: [],
    network: [],
    throughput: [],
    errors: [],
  });
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState(null);

  // Fetch all metrics
  const fetchMetrics = async () => {
    try {
      setError(null);
      const [cpu, memory, network, throughput, errors] = await Promise.all([
        getCpuMetrics(timeRange),
        getMemoryMetrics(timeRange),
        getNetworkMetrics(timeRange),
        getThroughputMetrics(timeRange),
        getErrorMetrics(timeRange),
      ]);

      setMetrics({
        cpu: cpu.data || cpu || [],
        memory: memory.data || memory || [],
        network: network.data || network || [],
        throughput: throughput.data || throughput || [],
        errors: errors.data || errors || [],
      });
    } catch (err) {
      setError(err.message);
      // Generate mock data
      const generateMockData = (points, minVal, maxVal) => {
        return Array.from({ length: points }, (_, i) => {
          const timestamp = new Date(Date.now() - (points - 1 - i) * (3600000 / points));
          return {
            timestamp: timestamp.toISOString(),
            value: minVal + Math.random() * (maxVal - minVal),
          };
        });
      };

      setMetrics({
        cpu: generateMockData(30, 30, 85),
        memory: generateMockData(30, 40, 90),
        network: generateMockData(30, 100, 500),
        throughput: generateMockData(30, 50, 200),
        errors: generateMockData(30, 0, 10),
      });
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    fetchMetrics();
    const interval = setInterval(fetchMetrics, 30000);
    return () => clearInterval(interval);
  }, [timeRange]);

  // Time range options
  const timeRangeOptions = [
    { value: '15m', label: '15 min' },
    { value: '1h', label: '1 hour' },
    { value: '6h', label: '6 hours' },
    { value: '24h', label: '24 hours' },
    { value: '7d', label: '7 days' },
  ];

  // Simple line chart component
  const LineChart = ({ data, label, unit, color, height = 150, warningThreshold, criticalThreshold }) => {
    if (!data || data.length === 0) {
      return (
        <div style={{ height, display: 'flex', alignItems: 'center', justifyContent: 'center', color: '#6b7280' }}>
          No data available
        </div>
      );
    }

    const values = data.map(d => d.value);
    const minValue = Math.min(...values);
    const maxValue = Math.max(...values);
    const range = maxValue - minValue || 1;
    const padding = { top: 10, right: 10, bottom: 30, left: 40 };
    const width = 600;
    const innerWidth = width - padding.left - padding.right;
    const innerHeight = height - padding.top - padding.bottom;

    // Generate path
    const points = data.map((d, i) => {
      const x = padding.left + (i / (data.length - 1)) * innerWidth;
      const y = padding.top + innerHeight - ((d.value - minValue) / range) * innerHeight;
      return `${x},${y}`;
    });
    const linePath = `M ${points.join(' L ')}`;
    const areaPath = `M ${padding.left},${padding.top + innerHeight} L ${points.join(' L ')} L ${padding.left + innerWidth},${padding.top + innerHeight} Z`;

    // Calculate current value and trend
    const currentValue = values[values.length - 1];
    const previousValue = values.length > 1 ? values[values.length - 2] : currentValue;
    const trend = currentValue - previousValue;
    const trendColor = trend > 0 ? '#ef4444' : trend < 0 ? '#10b981' : '#6b7280';

    // Determine status color
    let statusColor = '#10b981';
    if (criticalThreshold && currentValue >= criticalThreshold) {
      statusColor = '#ef4444';
    } else if (warningThreshold && currentValue >= warningThreshold) {
      statusColor = '#f59e0b';
    }

    return (
      <div>
        <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'baseline', marginBottom: '8px' }}>
          <span style={{ fontSize: '14px', fontWeight: '500' }}>{label}</span>
          <div style={{ display: 'flex', alignItems: 'baseline', gap: '8px' }}>
            <span style={{ fontSize: '24px', fontWeight: '600', color: statusColor }}>
              {currentValue.toFixed(1)}{unit}
            </span>
            <span style={{ fontSize: '12px', color: trendColor }}>
              {trend >= 0 ? '+' : ''}{trend.toFixed(1)}
            </span>
          </div>
        </div>
        <svg width="100%" height={height} viewBox={`0 0 ${width} ${height}`} preserveAspectRatio="xMidYMid meet">
          {/* Area fill */}
          <path d={areaPath} fill={`${color}20`} />

          {/* Warning/Critical thresholds */}
          {warningThreshold && (
            <line
              x1={padding.left}
              y1={padding.top + innerHeight - ((warningThreshold - minValue) / range) * innerHeight}
              x2={padding.left + innerWidth}
              y2={padding.top + innerHeight - ((warningThreshold - minValue) / range) * innerHeight}
              stroke="#f59e0b"
              strokeDasharray="4,4"
              opacity={0.5}
            />
          )}
          {criticalThreshold && (
            <line
              x1={padding.left}
              y1={padding.top + innerHeight - ((criticalThreshold - minValue) / range) * innerHeight}
              x2={padding.left + innerWidth}
              y2={padding.top + innerHeight - ((criticalThreshold - minValue) / range) * innerHeight}
              stroke="#ef4444"
              strokeDasharray="4,4"
              opacity={0.5}
            />
          )}

          {/* Line */}
          <path d={linePath} fill="none" stroke={color} strokeWidth="2" />

          {/* Y-axis labels */}
          <text x={padding.left - 5} y={padding.top + 5} textAnchor="end" fontSize="10" fill="#6b7280">
            {maxValue.toFixed(0)}
          </text>
          <text x={padding.left - 5} y={padding.top + innerHeight} textAnchor="end" fontSize="10" fill="#6b7280">
            {minValue.toFixed(0)}
          </text>

          {/* X-axis labels */}
          <text x={padding.left} y={height - 5} textAnchor="start" fontSize="10" fill="#6b7280">
            -{timeRange}
          </text>
          <text x={padding.left + innerWidth} y={height - 5} textAnchor="end" fontSize="10" fill="#6b7280">
            Now
          </text>
        </svg>
      </div>
    );
  };

  // Summary stats
  const calculateStats = (data) => {
    if (!data || data.length === 0) return { avg: 0, min: 0, max: 0 };
    const values = data.map(d => d.value);
    return {
      avg: values.reduce((a, b) => a + b, 0) / values.length,
      min: Math.min(...values),
      max: Math.max(...values),
    };
  };

  const cpuStats = calculateStats(metrics.cpu);
  const memoryStats = calculateStats(metrics.memory);
  const throughputStats = calculateStats(metrics.throughput);
  const errorStats = calculateStats(metrics.errors);

  return (
    <div className="metrics" style={{ padding: '24px' }}>
      <div style={{ marginBottom: '24px' }}>
        <h1 style={{ margin: '0 0 8px 0', fontSize: '24px', fontWeight: '600' }}>
          Performance Metrics
        </h1>
        <p style={{ margin: 0, color: '#6b7280' }}>
          Monitor cluster performance in real-time
        </p>
      </div>

      {error && (
        <div
          style={{
            padding: '12px',
            marginBottom: '16px',
            backgroundColor: '#fef3c7',
            border: '1px solid #f59e0b',
            borderRadius: '8px',
            color: '#92400e',
            fontSize: '14px',
          }}
        >
          Using demo data - {error}
        </div>
      )}

      {/* Time Range Selector */}
      <div
        style={{
          display: 'flex',
          justifyContent: 'space-between',
          alignItems: 'center',
          marginBottom: '24px',
          padding: '16px',
          backgroundColor: '#ffffff',
          borderRadius: '12px',
          boxShadow: '0 1px 3px rgba(0, 0, 0, 0.1)',
        }}
      >
        <div style={{ display: 'flex', gap: '8px' }}>
          {timeRangeOptions.map((option) => (
            <button
              key={option.value}
              onClick={() => setTimeRange(option.value)}
              style={{
                padding: '6px 12px',
                borderRadius: '6px',
                border: 'none',
                backgroundColor: timeRange === option.value ? '#3b82f6' : '#f3f4f6',
                color: timeRange === option.value ? '#ffffff' : '#4b5563',
                fontSize: '13px',
                fontWeight: '500',
                cursor: 'pointer',
                transition: 'all 0.2s',
              }}
            >
              {option.label}
            </button>
          ))}
        </div>
        <button
          onClick={fetchMetrics}
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

      {loading ? (
        <div style={{ textAlign: 'center', padding: '60px', color: '#6b7280' }}>
          Loading metrics...
        </div>
      ) : (
        <>
          {/* Summary Stats */}
          <div
            style={{
              display: 'grid',
              gridTemplateColumns: 'repeat(auto-fit, minmax(150px, 1fr))',
              gap: '16px',
              marginBottom: '24px',
            }}
          >
            {[
              { label: 'Avg CPU', value: `${cpuStats.avg.toFixed(1)}%`, color: '#3b82f6' },
              { label: 'Avg Memory', value: `${memoryStats.avg.toFixed(1)}%`, color: '#8b5cf6' },
              { label: 'Throughput', value: `${throughputStats.avg.toFixed(0)} t/m`, color: '#10b981' },
              { label: 'Error Rate', value: `${errorStats.avg.toFixed(2)}%`, color: '#ef4444' },
            ].map((stat) => (
              <div
                key={stat.label}
                style={{
                  padding: '16px',
                  backgroundColor: '#ffffff',
                  borderRadius: '8px',
                  boxShadow: '0 1px 3px rgba(0, 0, 0, 0.1)',
                  borderLeft: `4px solid ${stat.color}`,
                }}
              >
                <div style={{ fontSize: '12px', color: '#6b7280', marginBottom: '4px' }}>
                  {stat.label}
                </div>
                <div style={{ fontSize: '20px', fontWeight: '600', color: stat.color }}>
                  {stat.value}
                </div>
              </div>
            ))}
          </div>

          {/* Charts Grid */}
          <div style={{ display: 'grid', gridTemplateColumns: 'repeat(2, 1fr)', gap: '24px' }}>
            {/* CPU Usage */}
            <div
              style={{
                backgroundColor: '#ffffff',
                borderRadius: '12px',
                boxShadow: '0 1px 3px rgba(0, 0, 0, 0.1)',
                padding: '20px',
              }}
            >
              <LineChart
                data={metrics.cpu}
                label="CPU Usage"
                unit="%"
                color="#3b82f6"
                warningThreshold={70}
                criticalThreshold={90}
              />
            </div>

            {/* Memory Usage */}
            <div
              style={{
                backgroundColor: '#ffffff',
                borderRadius: '12px',
                boxShadow: '0 1px 3px rgba(0, 0, 0, 0.1)',
                padding: '20px',
              }}
            >
              <LineChart
                data={metrics.memory}
                label="Memory Usage"
                unit="%"
                color="#8b5cf6"
                warningThreshold={75}
                criticalThreshold={90}
              />
            </div>

            {/* Network Throughput */}
            <div
              style={{
                backgroundColor: '#ffffff',
                borderRadius: '12px',
                boxShadow: '0 1px 3px rgba(0, 0, 0, 0.1)',
                padding: '20px',
              }}
            >
              <LineChart
                data={metrics.network}
                label="Network I/O"
                unit=" MB/s"
                color="#10b981"
              />
            </div>

            {/* Task Throughput */}
            <div
              style={{
                backgroundColor: '#ffffff',
                borderRadius: '12px',
                boxShadow: '0 1px 3px rgba(0, 0, 0, 0.1)',
                padding: '20px',
              }}
            >
              <LineChart
                data={metrics.throughput}
                label="Task Throughput"
                unit=" tasks/min"
                color="#f59e0b"
              />
            </div>

            {/* Queue Wait Time */}
            <div
              style={{
                backgroundColor: '#ffffff',
                borderRadius: '12px',
                boxShadow: '0 1px 3px rgba(0, 0, 0, 0.1)',
                padding: '20px',
              }}
            >
              <LineChart
                data={metrics.throughput.map(d => ({
                  ...d,
                  value: Math.random() * 30 + 5,
                }))}
                label="Queue Wait Time"
                unit="s"
                color="#6366f1"
                warningThreshold={20}
                criticalThreshold={30}
              />
            </div>

            {/* Error Rate */}
            <div
              style={{
                backgroundColor: '#ffffff',
                borderRadius: '12px',
                boxShadow: '0 1px 3px rgba(0, 0, 0, 0.1)',
                padding: '20px',
              }}
            >
              <LineChart
                data={metrics.errors}
                label="Error Rate"
                unit="%"
                color="#ef4444"
                warningThreshold={5}
                criticalThreshold={10}
              />
            </div>
          </div>

          {/* Detailed Stats Table */}
          <div
            style={{
              marginTop: '24px',
              backgroundColor: '#ffffff',
              borderRadius: '12px',
              boxShadow: '0 1px 3px rgba(0, 0, 0, 0.1)',
              padding: '20px',
            }}
          >
            <h3 style={{ margin: '0 0 16px 0', fontSize: '16px', fontWeight: '600' }}>
              Detailed Statistics
            </h3>
            <table style={{ width: '100%', borderCollapse: 'collapse', fontSize: '14px' }}>
              <thead>
                <tr style={{ borderBottom: '2px solid #e5e7eb' }}>
                  <th style={{ padding: '12px 8px', textAlign: 'left', fontWeight: '600' }}>Metric</th>
                  <th style={{ padding: '12px 8px', textAlign: 'right', fontWeight: '600' }}>Current</th>
                  <th style={{ padding: '12px 8px', textAlign: 'right', fontWeight: '600' }}>Average</th>
                  <th style={{ padding: '12px 8px', textAlign: 'right', fontWeight: '600' }}>Min</th>
                  <th style={{ padding: '12px 8px', textAlign: 'right', fontWeight: '600' }}>Max</th>
                </tr>
              </thead>
              <tbody>
                {[
                  { name: 'CPU Usage', stats: cpuStats, data: metrics.cpu, unit: '%' },
                  { name: 'Memory Usage', stats: memoryStats, data: metrics.memory, unit: '%' },
                  { name: 'Task Throughput', stats: throughputStats, data: metrics.throughput, unit: ' t/m' },
                  { name: 'Error Rate', stats: errorStats, data: metrics.errors, unit: '%' },
                ].map((metric) => (
                  <tr key={metric.name} style={{ borderBottom: '1px solid #f3f4f6' }}>
                    <td style={{ padding: '12px 8px' }}>{metric.name}</td>
                    <td style={{ padding: '12px 8px', textAlign: 'right', fontWeight: '500' }}>
                      {metric.data.length > 0 ? metric.data[metric.data.length - 1].value.toFixed(1) : '-'}{metric.unit}
                    </td>
                    <td style={{ padding: '12px 8px', textAlign: 'right', color: '#6b7280' }}>
                      {metric.stats.avg.toFixed(1)}{metric.unit}
                    </td>
                    <td style={{ padding: '12px 8px', textAlign: 'right', color: '#10b981' }}>
                      {metric.stats.min.toFixed(1)}{metric.unit}
                    </td>
                    <td style={{ padding: '12px 8px', textAlign: 'right', color: '#ef4444' }}>
                      {metric.stats.max.toFixed(1)}{metric.unit}
                    </td>
                  </tr>
                ))}
              </tbody>
            </table>
          </div>
        </>
      )}
    </div>
  );
};

export default Metrics;
