// API Base URLs for each module
export const API_ENDPOINTS = {
  GATEWAY: '/api/gateway',
  WORKFLOW: '/api/workflow',
  PROCESSING: '/api/processing',
  DATA: '/api/data',
  MODELS: '/api/models',
  INFRA: '/api/infra',
}

// Module information
export const MODULES = {
  GATEWAY: {
    id: 'gateway',
    name: 'User Gateway',
    description: 'Authentication & API Management',
    icon: 'ShieldCheckIcon',
    color: 'blue',
    path: '/gateway',
    port: 8001,
  },
  WORKFLOW: {
    id: 'workflow',
    name: 'Workflow Orchestration',
    description: 'Workflow Design & Scheduling',
    icon: 'CubeTransparentIcon',
    color: 'purple',
    path: '/workflows',
    port: 8002,
  },
  PROCESSING: {
    id: 'processing',
    name: 'Core Processing',
    description: 'AI Code Generation & Processing',
    icon: 'CpuChipIcon',
    color: 'green',
    path: '/processing',
    port: 8003,
  },
  DATA: {
    id: 'data',
    name: 'Data Integration',
    description: 'Event Streaming & Caching',
    icon: 'CircleStackIcon',
    color: 'orange',
    path: '/data',
    port: 8004,
  },
  MODELS: {
    id: 'models',
    name: 'Model Management',
    description: 'Model Storage & Versioning',
    icon: 'CubeIcon',
    color: 'pink',
    path: '/models',
    port: 8005,
  },
  INFRA: {
    id: 'infra',
    name: 'Infrastructure',
    description: 'Parallel Processing & Scaling',
    icon: 'ServerStackIcon',
    color: 'cyan',
    path: '/infrastructure',
    port: 8006,
  },
}

// Status colors
export const STATUS_COLORS = {
  online: 'green',
  offline: 'red',
  warning: 'yellow',
  unknown: 'gray',
}

// Chart colors
export const CHART_COLORS = {
  primary: '#0ea5e9',
  secondary: '#64748b',
  success: '#22c55e',
  warning: '#f59e0b',
  danger: '#ef4444',
  info: '#3b82f6',
}

// Navigation items
export const NAV_ITEMS = [
  { name: 'Dashboard', path: '/dashboard', icon: 'HomeIcon' },
  { name: 'User Gateway', path: '/gateway', icon: 'ShieldCheckIcon' },
  { name: 'Workflows', path: '/workflows', icon: 'CubeTransparentIcon' },
  { name: 'Processing', path: '/processing', icon: 'CpuChipIcon' },
  { name: 'Data Integration', path: '/data', icon: 'CircleStackIcon' },
  { name: 'Models', path: '/models', icon: 'CubeIcon' },
  { name: 'Infrastructure', path: '/infrastructure', icon: 'ServerStackIcon' },
]

// Activity types
export const ACTIVITY_TYPES = {
  WORKFLOW_STARTED: 'workflow_started',
  WORKFLOW_COMPLETED: 'workflow_completed',
  MODEL_DEPLOYED: 'model_deployed',
  USER_LOGIN: 'user_login',
  ERROR: 'error',
  WARNING: 'warning',
}

// Refresh intervals (in milliseconds)
export const REFRESH_INTERVALS = {
  METRICS: 30000, // 30 seconds
  STATUS: 10000, // 10 seconds
  ACTIVITY: 5000, // 5 seconds
}
