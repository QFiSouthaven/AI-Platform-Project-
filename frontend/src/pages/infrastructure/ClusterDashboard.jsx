import React, { useState, useEffect } from 'react';
import ResourceGauge from '../../components/infrastructure/ResourceGauge';
import AlertsList from '../../components/infrastructure/AlertsList';
import {
  getClusterStatus,
  getClusterHealth,
  getQueueStats,
  getAlerts,
  acknowledgeAlert,
  dismissAlert,
} from '../../services/infrastructureService';

/**
 * ClusterDashboard - Main dashboard for infrastructure monitoring
 * Shows cluster health, resource usage, active tasks, queue depth, and alerts
 */
const ClusterDashboard = () => {
  const [clusterData, setClusterData] = useState(null);
  const [queueData, setQueueData] = useState(null);
  const [alerts, setAlerts] = useState([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState(null);

  // Fetch dashboard data
  const fetchDashboardData = async () => {
    try {
      setError(null);
      const [cluster, queue, alertsData] = await Promise.all([
        getClusterStatus(),
        getQueueStats(),
        getAlerts({ limit: 10 }),
      ]);

      setClusterData(cluster.data || cluster);
      setQueueData(queue.data || queue);
      setAlerts(alertsData.data || alertsData || []);
    } catch (err) {
      setError(err.message);
      // Set mock data for demo
      setClusterData({
        health_status: 'healthy',
        total_nodes: 5,
        active_nodes: 5,
        cpu_usage: 45,
        memory_usage: 62,
        gpu_usage: 38,
        active_tasks: 12,
        pending_tasks: 8,
        completed_tasks: 156,
        failed_tasks: 3,
      });
      setQueueData({
        depth: [10, 15, 12, 18, 14, 16, 20, 18, 15, 12, 14, 16],
        timestamps: Array.from({ length: 12 }, (_, i) => {
          const d = new Date();
          d.setMinutes(d.getMinutes() - (11 - i) * 5);
          return d.toISOString();
        }),
      });
      setAlerts([
        {
          id: 1,
          title: 'High Memory Usage',
          message: 'Worker node-3 memory usage exceeded 85%',
          severity: 'warning',
          timestamp: new Date(Date.now() - 300000).toISOString(),
          source: 'node-3',
        },
        {
          id: 2,
          title: 'Task Queue Growing',
          message: 'Queue depth increased by 50% in the last hour',
          severity: 'info',
          timestamp: new Date(Date.now() - 600000).toISOString(),
          source: 'scheduler',
        },
      ]);
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    fetchDashboardData();
    // Refresh every 30 seconds
    const interval = setInterval(fetchDashboardData, 30000);
    return () => clearInterval(interval);
  }, []);

  // Handle alert actions
  const handleAcknowledge = async (alertId) => {
    try {
      await acknowledgeAlert(alertId);
      setAlerts(alerts.map(a =>
        a.id === alertId ? { ...a, acknowledged: true } : a
      ));
    } catch (err) {
      console.error('Failed to acknowledge alert:', err);
    }
  };

  const handleDismiss = async (alertId) => {
    try {
      await dismissAlert(alertId);
      setAlerts(alerts.filter(a => a.id !== alertId));
    } catch (err) {
      console.error('Failed to dismiss alert:', err);
    }
  };

  // Get health status config
  const getHealthConfig = (status) => {
    switch (status) {
      case 'healthy':
        return { color: '#10b981', label: 'Healthy', bgColor: '#d1fae5' };
      case 'degraded':
        return { color: '#f59e0b', label: 'Degraded', bgColor: '#fef3c7' };
      case 'unhealthy':
        return { color: '#ef4444', label: 'Unhealthy', bgColor: '#fecaca' };
      default:
        return { color: '#6b7280', label: 'Unknown', bgColor: '#f3f4f6' };
    }
  };

  if (loading) {
    return (
      <div style={{ padding: '24px', textAlign: 'center' }}>
        <div>Loading cluster data...</div>
      </div>
    );
  }

  const healthConfig = getHealthConfig(clusterData?.health_status);

  return (
    <div className="cluster-dashboard" style={{ padding: '24px' }}>
      <div style={{ marginBottom: '24px' }}>
        <h1 style={{ margin: '0 0 8px 0', fontSize: '24px', fontWeight: '600' }}>
          Cluster Dashboard
        </h1>
        <p style={{ margin: 0, color: '#6b7280' }}>
          Monitor your distributed infrastructure in real-time
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

      {/* Health Status Banner */}
      <div
        style={{
          display: 'flex',
          alignItems: 'center',
          justifyContent: 'space-between',
          padding: '16px 24px',
          backgroundColor: healthConfig.bgColor,
          borderRadius: '12px',
          marginBottom: '24px',
        }}
      >
        <div style={{ display: 'flex', alignItems: 'center', gap: '12px' }}>
          <div
            style={{
              width: '48px',
              height: '48px',
              borderRadius: '50%',
              backgroundColor: healthConfig.color,
              display: 'flex',
              alignItems: 'center',
              justifyContent: 'center',
            }}
          >
            <span style={{ color: '#fff', fontSize: '24px' }}>
              {healthConfig.label === 'Healthy' ? '\u2713' : '!'}
            </span>
          </div>
          <div>
            <div style={{ fontSize: '18px', fontWeight: '600', color: healthConfig.color }}>
              Cluster Status: {healthConfig.label}
            </div>
            <div style={{ fontSize: '14px', color: '#6b7280' }}>
              {clusterData?.active_nodes || 0} of {clusterData?.total_nodes || 0} nodes active
            </div>
          </div>
        </div>
        <button
          onClick={fetchDashboardData}
          style={{
            padding: '8px 16px',
            backgroundColor: '#ffffff',
            border: '1px solid #d1d5db',
            borderRadius: '6px',
            cursor: 'pointer',
            fontSize: '14px',
          }}
        >
          Refresh
        </button>
      </div>

      {/* Resource Gauges */}
      <div
        style={{
          display: 'grid',
          gridTemplateColumns: 'repeat(auto-fit, minmax(200px, 1fr))',
          gap: '16px',
          marginBottom: '24px',
        }}
      >
        <div
          style={{
            padding: '20px',
            backgroundColor: '#ffffff',
            borderRadius: '12px',
            boxShadow: '0 1px 3px rgba(0, 0, 0, 0.1)',
            display: 'flex',
            flexDirection: 'column',
            alignItems: 'center',
          }}
        >
          <ResourceGauge
            value={clusterData?.cpu_usage || 0}
            label="CPU Usage"
            size={100}
          />
        </div>
        <div
          style={{
            padding: '20px',
            backgroundColor: '#ffffff',
            borderRadius: '12px',
            boxShadow: '0 1px 3px rgba(0, 0, 0, 0.1)',
            display: 'flex',
            flexDirection: 'column',
            alignItems: 'center',
          }}
        >
          <ResourceGauge
            value={clusterData?.memory_usage || 0}
            label="Memory Usage"
            size={100}
          />
        </div>
        <div
          style={{
            padding: '20px',
            backgroundColor: '#ffffff',
            borderRadius: '12px',
            boxShadow: '0 1px 3px rgba(0, 0, 0, 0.1)',
            display: 'flex',
            flexDirection: 'column',
            alignItems: 'center',
          }}
        >
          <ResourceGauge
            value={clusterData?.gpu_usage || 0}
            label="GPU Usage"
            size={100}
          />
        </div>
      </div>

      {/* Task Stats */}
      <div
        style={{
          display: 'grid',
          gridTemplateColumns: 'repeat(auto-fit, minmax(150px, 1fr))',
          gap: '16px',
          marginBottom: '24px',
        }}
      >
        {[
          { label: 'Active Tasks', value: clusterData?.active_tasks || 0, color: '#3b82f6' },
          { label: 'Pending', value: clusterData?.pending_tasks || 0, color: '#f59e0b' },
          { label: 'Completed', value: clusterData?.completed_tasks || 0, color: '#10b981' },
          { label: 'Failed', value: clusterData?.failed_tasks || 0, color: '#ef4444' },
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
            <div style={{ fontSize: '24px', fontWeight: '600', color: stat.color }}>
              {stat.value}
            </div>
          </div>
        ))}
      </div>

      {/* Queue Depth Chart */}
      <div
        style={{
          backgroundColor: '#ffffff',
          borderRadius: '12px',
          boxShadow: '0 1px 3px rgba(0, 0, 0, 0.1)',
          padding: '20px',
          marginBottom: '24px',
        }}
      >
        <h3 style={{ margin: '0 0 16px 0', fontSize: '16px', fontWeight: '600' }}>
          Queue Depth (Last Hour)
        </h3>
        <div style={{ height: '150px', display: 'flex', alignItems: 'flex-end', gap: '8px' }}>
          {(queueData?.depth || []).map((depth, index) => {
            const maxDepth = Math.max(...(queueData?.depth || [1]));
            const height = (depth / maxDepth) * 100;
            const isHighQueue = depth > maxDepth * 0.8;
            return (
              <div
                key={index}
                style={{
                  flex: 1,
                  height: `${height}%`,
                  backgroundColor: isHighQueue ? '#f59e0b' : '#3b82f6',
                  borderRadius: '4px 4px 0 0',
                  minHeight: '4px',
                  transition: 'height 0.3s ease',
                }}
                title={`Depth: ${depth}`}
              />
            );
          })}
        </div>
        <div
          style={{
            display: 'flex',
            justifyContent: 'space-between',
            marginTop: '8px',
            fontSize: '11px',
            color: '#9ca3af',
          }}
        >
          <span>-1h</span>
          <span>Now</span>
        </div>
      </div>

      {/* Recent Alerts */}
      <div
        style={{
          backgroundColor: '#ffffff',
          borderRadius: '12px',
          boxShadow: '0 1px 3px rgba(0, 0, 0, 0.1)',
          padding: '20px',
        }}
      >
        <h3 style={{ margin: '0 0 16px 0', fontSize: '16px', fontWeight: '600' }}>
          Recent Alerts
        </h3>
        <AlertsList
          alerts={alerts}
          onAcknowledge={handleAcknowledge}
          onDismiss={handleDismiss}
          maxHeight="300px"
        />
      </div>
    </div>
  );
};

export default ClusterDashboard;
