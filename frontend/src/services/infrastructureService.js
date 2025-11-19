/**
 * Infrastructure Service
 * Handles API calls for infrastructure management (Module 6)
 */

const API_BASE_URL = process.env.REACT_APP_API_URL || 'http://localhost:8006/api/v1';

/**
 * Helper function for API requests
 */
const apiRequest = async (endpoint, options = {}) => {
  const url = `${API_BASE_URL}${endpoint}`;
  const config = {
    headers: {
      'Content-Type': 'application/json',
      ...options.headers,
    },
    ...options,
  };

  const response = await fetch(url, config);

  if (!response.ok) {
    const error = await response.json().catch(() => ({ message: 'Request failed' }));
    throw new Error(error.message || `HTTP error! status: ${response.status}`);
  }

  return response.json();
};

// ============ Task Management ============

/**
 * Submit a new task for distributed execution
 */
export const submitTask = async (taskData) => {
  return apiRequest('/tasks', {
    method: 'POST',
    body: JSON.stringify(taskData),
  });
};

/**
 * Get status of a specific task
 */
export const getTaskStatus = async (taskId) => {
  return apiRequest(`/tasks/${taskId}`);
};

/**
 * Get all tasks with optional filters
 */
export const getTasks = async (filters = {}) => {
  const params = new URLSearchParams(filters).toString();
  return apiRequest(`/tasks${params ? `?${params}` : ''}`);
};

/**
 * Cancel a running task
 */
export const cancelTask = async (taskId) => {
  return apiRequest(`/tasks/${taskId}/cancel`, {
    method: 'POST',
  });
};

/**
 * Retry a failed task
 */
export const retryTask = async (taskId) => {
  return apiRequest(`/tasks/${taskId}/retry`, {
    method: 'POST',
  });
};

/**
 * Get task result
 */
export const getTaskResult = async (taskId) => {
  return apiRequest(`/tasks/${taskId}/result`);
};

// ============ Worker Management ============

/**
 * Get all worker nodes
 */
export const getWorkers = async () => {
  return apiRequest('/workers');
};

/**
 * Get details of a specific worker
 */
export const getWorkerDetails = async (workerId) => {
  return apiRequest(`/workers/${workerId}`);
};

/**
 * Scale worker count
 */
export const scaleWorkers = async (count) => {
  return apiRequest('/workers/scale', {
    method: 'POST',
    body: JSON.stringify({ target_count: count }),
  });
};

/**
 * Get worker health status
 */
export const getWorkerHealth = async (workerId) => {
  return apiRequest(`/workers/${workerId}/health`);
};

// ============ Cluster Management ============

/**
 * Get cluster overview/dashboard data
 */
export const getClusterStatus = async () => {
  return apiRequest('/cluster/status');
};

/**
 * Get cluster health summary
 */
export const getClusterHealth = async () => {
  return apiRequest('/cluster/health');
};

/**
 * Get queue statistics
 */
export const getQueueStats = async () => {
  return apiRequest('/cluster/queue');
};

// ============ Metrics ============

/**
 * Get performance metrics
 */
export const getMetrics = async (timeRange = '1h') => {
  return apiRequest(`/metrics?range=${timeRange}`);
};

/**
 * Get CPU metrics
 */
export const getCpuMetrics = async (timeRange = '1h') => {
  return apiRequest(`/metrics/cpu?range=${timeRange}`);
};

/**
 * Get memory metrics
 */
export const getMemoryMetrics = async (timeRange = '1h') => {
  return apiRequest(`/metrics/memory?range=${timeRange}`);
};

/**
 * Get network metrics
 */
export const getNetworkMetrics = async (timeRange = '1h') => {
  return apiRequest(`/metrics/network?range=${timeRange}`);
};

/**
 * Get task throughput metrics
 */
export const getThroughputMetrics = async (timeRange = '1h') => {
  return apiRequest(`/metrics/throughput?range=${timeRange}`);
};

/**
 * Get error rate metrics
 */
export const getErrorMetrics = async (timeRange = '1h') => {
  return apiRequest(`/metrics/errors?range=${timeRange}`);
};

// ============ Alerts ============

/**
 * Get active alerts
 */
export const getAlerts = async (filters = {}) => {
  const params = new URLSearchParams(filters).toString();
  return apiRequest(`/alerts${params ? `?${params}` : ''}`);
};

/**
 * Acknowledge an alert
 */
export const acknowledgeAlert = async (alertId) => {
  return apiRequest(`/alerts/${alertId}/acknowledge`, {
    method: 'POST',
  });
};

/**
 * Dismiss an alert
 */
export const dismissAlert = async (alertId) => {
  return apiRequest(`/alerts/${alertId}/dismiss`, {
    method: 'POST',
  });
};

// ============ Auto-scaling Configuration ============

/**
 * Get auto-scaling configuration
 */
export const getScalingConfig = async () => {
  return apiRequest('/scaling/config');
};

/**
 * Update auto-scaling configuration
 */
export const updateScalingConfig = async (config) => {
  return apiRequest('/scaling/config', {
    method: 'PUT',
    body: JSON.stringify(config),
  });
};

/**
 * Get scaling history
 */
export const getScalingHistory = async (timeRange = '24h') => {
  return apiRequest(`/scaling/history?range=${timeRange}`);
};

/**
 * Manually trigger scaling
 */
export const manualScale = async (targetCount) => {
  return apiRequest('/scaling/manual', {
    method: 'POST',
    body: JSON.stringify({ target_count: targetCount }),
  });
};

/**
 * Enable or disable auto-scaling
 */
export const setAutoScalingEnabled = async (enabled) => {
  return apiRequest('/scaling/toggle', {
    method: 'POST',
    body: JSON.stringify({ enabled }),
  });
};

export default {
  // Task Management
  submitTask,
  getTaskStatus,
  getTasks,
  cancelTask,
  retryTask,
  getTaskResult,

  // Worker Management
  getWorkers,
  getWorkerDetails,
  scaleWorkers,
  getWorkerHealth,

  // Cluster Management
  getClusterStatus,
  getClusterHealth,
  getQueueStats,

  // Metrics
  getMetrics,
  getCpuMetrics,
  getMemoryMetrics,
  getNetworkMetrics,
  getThroughputMetrics,
  getErrorMetrics,

  // Alerts
  getAlerts,
  acknowledgeAlert,
  dismissAlert,

  // Auto-scaling
  getScalingConfig,
  updateScalingConfig,
  getScalingHistory,
  manualScale,
  setAutoScalingEnabled,
};
