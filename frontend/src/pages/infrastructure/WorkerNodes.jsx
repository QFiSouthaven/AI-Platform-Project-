import React, { useState, useEffect } from 'react';
import NodeCard from '../../components/infrastructure/NodeCard';
import ResourceGauge from '../../components/infrastructure/ResourceGauge';
import {
  getWorkers,
  getWorkerDetails,
  scaleWorkers,
} from '../../services/infrastructureService';

/**
 * WorkerNodes - Worker node management interface
 * View, monitor, and scale worker nodes
 */
const WorkerNodes = () => {
  const [workers, setWorkers] = useState([]);
  const [selectedWorker, setSelectedWorker] = useState(null);
  const [workerDetails, setWorkerDetails] = useState(null);
  const [loading, setLoading] = useState(true);
  const [scaling, setScaling] = useState(false);
  const [error, setError] = useState(null);

  // Fetch workers
  const fetchWorkers = async () => {
    try {
      setError(null);
      const response = await getWorkers();
      setWorkers(response.data || response || []);
    } catch (err) {
      setError(err.message);
      // Mock data for demo
      setWorkers([
        {
          id: 'worker-1',
          name: 'Worker Node 1',
          status: 'healthy',
          cpu_usage: 45,
          memory_usage: 62,
          gpu_usage: 38,
          gpu_available: true,
          tasks_running: 3,
          tasks_completed: 156,
          uptime: 259200,
          ip_address: '192.168.1.101',
        },
        {
          id: 'worker-2',
          name: 'Worker Node 2',
          status: 'healthy',
          cpu_usage: 72,
          memory_usage: 85,
          gpu_usage: 55,
          gpu_available: true,
          tasks_running: 5,
          tasks_completed: 203,
          uptime: 172800,
          ip_address: '192.168.1.102',
        },
        {
          id: 'worker-3',
          name: 'Worker Node 3',
          status: 'warning',
          cpu_usage: 88,
          memory_usage: 92,
          gpu_usage: 78,
          gpu_available: true,
          tasks_running: 4,
          tasks_completed: 178,
          uptime: 345600,
          ip_address: '192.168.1.103',
        },
        {
          id: 'worker-4',
          name: 'Worker Node 4',
          status: 'healthy',
          cpu_usage: 35,
          memory_usage: 48,
          gpu_usage: 22,
          gpu_available: true,
          tasks_running: 2,
          tasks_completed: 89,
          uptime: 86400,
          ip_address: '192.168.1.104',
        },
        {
          id: 'worker-5',
          name: 'Worker Node 5',
          status: 'offline',
          cpu_usage: 0,
          memory_usage: 0,
          gpu_usage: 0,
          gpu_available: true,
          tasks_running: 0,
          tasks_completed: 67,
          uptime: 0,
          ip_address: '192.168.1.105',
        },
      ]);
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    fetchWorkers();
    const interval = setInterval(fetchWorkers, 15000);
    return () => clearInterval(interval);
  }, []);

  // Fetch worker details
  const fetchWorkerDetails = async (workerId) => {
    try {
      const response = await getWorkerDetails(workerId);
      setWorkerDetails(response.data || response);
    } catch (err) {
      // Mock details
      const worker = workers.find(w => w.id === workerId);
      setWorkerDetails({
        ...worker,
        cpu_cores: 16,
        memory_total: 64,
        gpu_model: 'NVIDIA A100',
        gpu_memory: 40,
        os: 'Ubuntu 22.04',
        ray_version: '2.8.0',
        last_heartbeat: new Date().toISOString(),
        recent_tasks: [
          { id: 't1', name: 'Task 1', status: 'completed', duration: 120 },
          { id: 't2', name: 'Task 2', status: 'completed', duration: 85 },
          { id: 't3', name: 'Task 3', status: 'running', duration: 45 },
        ],
      });
    }
  };

  // Handle worker selection
  const handleSelectWorker = async (worker) => {
    setSelectedWorker(worker);
    await fetchWorkerDetails(worker.id);
  };

  // Scale workers
  const handleScale = async (delta) => {
    const currentCount = workers.length;
    const newCount = Math.max(1, currentCount + delta);

    setScaling(true);
    try {
      await scaleWorkers(newCount);
      fetchWorkers();
    } catch (err) {
      setError(`Failed to scale: ${err.message}`);
    } finally {
      setScaling(false);
    }
  };

  // Calculate cluster summary
  const clusterSummary = {
    total: workers.length,
    healthy: workers.filter(w => w.status === 'healthy').length,
    warning: workers.filter(w => w.status === 'warning' || w.status === 'degraded').length,
    offline: workers.filter(w => w.status === 'offline' || w.status === 'unhealthy').length,
    avgCpu: workers.length > 0 ? Math.round(workers.reduce((acc, w) => acc + w.cpu_usage, 0) / workers.length) : 0,
    avgMemory: workers.length > 0 ? Math.round(workers.reduce((acc, w) => acc + w.memory_usage, 0) / workers.length) : 0,
    totalTasks: workers.reduce((acc, w) => acc + w.tasks_running, 0),
  };

  // Format uptime
  const formatUptime = (seconds) => {
    if (!seconds) return 'N/A';
    const days = Math.floor(seconds / 86400);
    const hours = Math.floor((seconds % 86400) / 3600);
    const minutes = Math.floor((seconds % 3600) / 60);

    if (days > 0) return `${days}d ${hours}h ${minutes}m`;
    if (hours > 0) return `${hours}h ${minutes}m`;
    return `${minutes}m`;
  };

  return (
    <div className="worker-nodes" style={{ padding: '24px' }}>
      <div style={{ marginBottom: '24px' }}>
        <h1 style={{ margin: '0 0 8px 0', fontSize: '24px', fontWeight: '600' }}>
          Worker Nodes
        </h1>
        <p style={{ margin: 0, color: '#6b7280' }}>
          Manage and monitor distributed worker nodes
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

      {/* Cluster Summary */}
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
          }}
        >
          <div style={{ fontSize: '14px', color: '#6b7280', marginBottom: '8px' }}>Total Nodes</div>
          <div style={{ fontSize: '32px', fontWeight: '600', marginBottom: '8px' }}>{clusterSummary.total}</div>
          <div style={{ display: 'flex', gap: '12px', fontSize: '12px' }}>
            <span style={{ color: '#10b981' }}>{clusterSummary.healthy} healthy</span>
            <span style={{ color: '#f59e0b' }}>{clusterSummary.warning} warning</span>
            <span style={{ color: '#ef4444' }}>{clusterSummary.offline} offline</span>
          </div>
        </div>

        <div
          style={{
            padding: '20px',
            backgroundColor: '#ffffff',
            borderRadius: '12px',
            boxShadow: '0 1px 3px rgba(0, 0, 0, 0.1)',
            display: 'flex',
            alignItems: 'center',
            justifyContent: 'center',
          }}
        >
          <ResourceGauge
            value={clusterSummary.avgCpu}
            label="Avg CPU"
            size={80}
            strokeWidth={8}
          />
        </div>

        <div
          style={{
            padding: '20px',
            backgroundColor: '#ffffff',
            borderRadius: '12px',
            boxShadow: '0 1px 3px rgba(0, 0, 0, 0.1)',
            display: 'flex',
            alignItems: 'center',
            justifyContent: 'center',
          }}
        >
          <ResourceGauge
            value={clusterSummary.avgMemory}
            label="Avg Memory"
            size={80}
            strokeWidth={8}
          />
        </div>

        <div
          style={{
            padding: '20px',
            backgroundColor: '#ffffff',
            borderRadius: '12px',
            boxShadow: '0 1px 3px rgba(0, 0, 0, 0.1)',
          }}
        >
          <div style={{ fontSize: '14px', color: '#6b7280', marginBottom: '8px' }}>Active Tasks</div>
          <div style={{ fontSize: '32px', fontWeight: '600', color: '#3b82f6' }}>
            {clusterSummary.totalTasks}
          </div>
        </div>
      </div>

      {/* Scale Controls */}
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
        <div>
          <span style={{ fontSize: '14px', fontWeight: '500' }}>Cluster Size: </span>
          <span style={{ fontSize: '14px', color: '#6b7280' }}>{workers.length} workers</span>
        </div>
        <div style={{ display: 'flex', gap: '8px' }}>
          <button
            onClick={() => handleScale(-1)}
            disabled={scaling || workers.length <= 1}
            style={{
              padding: '8px 16px',
              backgroundColor: scaling || workers.length <= 1 ? '#f3f4f6' : '#fecaca',
              border: 'none',
              borderRadius: '6px',
              fontSize: '14px',
              fontWeight: '500',
              color: scaling || workers.length <= 1 ? '#9ca3af' : '#ef4444',
              cursor: scaling || workers.length <= 1 ? 'not-allowed' : 'pointer',
            }}
          >
            Scale Down
          </button>
          <button
            onClick={() => handleScale(1)}
            disabled={scaling}
            style={{
              padding: '8px 16px',
              backgroundColor: scaling ? '#f3f4f6' : '#d1fae5',
              border: 'none',
              borderRadius: '6px',
              fontSize: '14px',
              fontWeight: '500',
              color: scaling ? '#9ca3af' : '#10b981',
              cursor: scaling ? 'not-allowed' : 'pointer',
            }}
          >
            Scale Up
          </button>
          <button
            onClick={fetchWorkers}
            style={{
              padding: '8px 16px',
              backgroundColor: '#f3f4f6',
              border: '1px solid #d1d5db',
              borderRadius: '6px',
              fontSize: '14px',
              cursor: 'pointer',
            }}
          >
            Refresh
          </button>
        </div>
      </div>

      {/* Worker Grid */}
      {loading ? (
        <div style={{ textAlign: 'center', padding: '40px', color: '#6b7280' }}>
          Loading workers...
        </div>
      ) : (
        <div
          style={{
            display: 'grid',
            gridTemplateColumns: 'repeat(auto-fill, minmax(280px, 1fr))',
            gap: '16px',
          }}
        >
          {workers.map((worker) => (
            <NodeCard
              key={worker.id}
              node={worker}
              onSelect={handleSelectWorker}
              isSelected={selectedWorker?.id === worker.id}
            />
          ))}
        </div>
      )}

      {/* Worker Details Modal */}
      {selectedWorker && workerDetails && (
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
            setSelectedWorker(null);
            setWorkerDetails(null);
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
                {workerDetails.name}
              </h3>
              <button
                onClick={() => {
                  setSelectedWorker(null);
                  setWorkerDetails(null);
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

            {/* Resource Gauges */}
            <div
              style={{
                display: 'flex',
                justifyContent: 'space-around',
                marginBottom: '24px',
                padding: '16px',
                backgroundColor: '#f9fafb',
                borderRadius: '8px',
              }}
            >
              <ResourceGauge value={workerDetails.cpu_usage} label="CPU" size={70} strokeWidth={7} />
              <ResourceGauge value={workerDetails.memory_usage} label="Memory" size={70} strokeWidth={7} />
              {workerDetails.gpu_available && (
                <ResourceGauge value={workerDetails.gpu_usage} label="GPU" size={70} strokeWidth={7} />
              )}
            </div>

            {/* Details Grid */}
            <div
              style={{
                display: 'grid',
                gridTemplateColumns: '1fr 1fr',
                gap: '12px',
                fontSize: '14px',
              }}
            >
              <div>
                <span style={{ color: '#6b7280' }}>IP Address:</span>
                <span style={{ marginLeft: '8px', fontWeight: '500' }}>{workerDetails.ip_address}</span>
              </div>
              <div>
                <span style={{ color: '#6b7280' }}>Uptime:</span>
                <span style={{ marginLeft: '8px', fontWeight: '500' }}>{formatUptime(workerDetails.uptime)}</span>
              </div>
              <div>
                <span style={{ color: '#6b7280' }}>CPU Cores:</span>
                <span style={{ marginLeft: '8px', fontWeight: '500' }}>{workerDetails.cpu_cores}</span>
              </div>
              <div>
                <span style={{ color: '#6b7280' }}>Memory:</span>
                <span style={{ marginLeft: '8px', fontWeight: '500' }}>{workerDetails.memory_total} GB</span>
              </div>
              {workerDetails.gpu_available && (
                <>
                  <div>
                    <span style={{ color: '#6b7280' }}>GPU:</span>
                    <span style={{ marginLeft: '8px', fontWeight: '500' }}>{workerDetails.gpu_model}</span>
                  </div>
                  <div>
                    <span style={{ color: '#6b7280' }}>GPU Memory:</span>
                    <span style={{ marginLeft: '8px', fontWeight: '500' }}>{workerDetails.gpu_memory} GB</span>
                  </div>
                </>
              )}
              <div>
                <span style={{ color: '#6b7280' }}>OS:</span>
                <span style={{ marginLeft: '8px', fontWeight: '500' }}>{workerDetails.os}</span>
              </div>
              <div>
                <span style={{ color: '#6b7280' }}>Ray Version:</span>
                <span style={{ marginLeft: '8px', fontWeight: '500' }}>{workerDetails.ray_version}</span>
              </div>
            </div>

            {/* Recent Tasks */}
            {workerDetails.recent_tasks && workerDetails.recent_tasks.length > 0 && (
              <div style={{ marginTop: '24px' }}>
                <h4 style={{ margin: '0 0 12px 0', fontSize: '14px', fontWeight: '600' }}>
                  Recent Tasks
                </h4>
                <div style={{ fontSize: '13px' }}>
                  {workerDetails.recent_tasks.map((task) => (
                    <div
                      key={task.id}
                      style={{
                        display: 'flex',
                        justifyContent: 'space-between',
                        padding: '8px 0',
                        borderBottom: '1px solid #f3f4f6',
                      }}
                    >
                      <span>{task.name}</span>
                      <span style={{ color: '#6b7280' }}>{task.duration}s</span>
                    </div>
                  ))}
                </div>
              </div>
            )}
          </div>
        </div>
      )}
    </div>
  );
};

export default WorkerNodes;
