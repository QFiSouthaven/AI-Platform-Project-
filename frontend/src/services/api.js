import axios from 'axios'
import { API_ENDPOINTS } from '../utils/constants'

// Create axios instance with default config
const createApiInstance = (baseURL) => {
  const instance = axios.create({
    baseURL,
    timeout: 10000,
    headers: {
      'Content-Type': 'application/json',
    },
  })

  // Request interceptor for adding auth token
  instance.interceptors.request.use(
    (config) => {
      const token = localStorage.getItem('access_token')
      if (token) {
        config.headers.Authorization = `Bearer ${token}`
      }
      return config
    },
    (error) => Promise.reject(error)
  )

  // Response interceptor for error handling
  instance.interceptors.response.use(
    (response) => response,
    (error) => {
      if (error.response?.status === 401) {
        localStorage.removeItem('access_token')
        window.location.href = '/login'
      }
      return Promise.reject(error)
    }
  )

  return instance
}

// API instances for each module
export const gatewayApi = createApiInstance(API_ENDPOINTS.GATEWAY)
export const workflowApi = createApiInstance(API_ENDPOINTS.WORKFLOW)
export const processingApi = createApiInstance(API_ENDPOINTS.PROCESSING)
export const dataApi = createApiInstance(API_ENDPOINTS.DATA)
export const modelsApi = createApiInstance(API_ENDPOINTS.MODELS)
export const infraApi = createApiInstance(API_ENDPOINTS.INFRA)

// API service methods
export const apiService = {
  // Health checks
  async checkHealth(module) {
    const apiMap = {
      gateway: gatewayApi,
      workflow: workflowApi,
      processing: processingApi,
      data: dataApi,
      models: modelsApi,
      infra: infraApi,
    }

    try {
      const response = await apiMap[module].get('/health')
      return { status: 'online', data: response.data }
    } catch (error) {
      return { status: 'offline', error: error.message }
    }
  },

  // Dashboard metrics
  async getDashboardMetrics() {
    try {
      const [workflows, models, tasks] = await Promise.all([
        workflowApi.get('/api/v1/workflows/stats').catch(() => ({ data: {} })),
        modelsApi.get('/api/v1/models/stats').catch(() => ({ data: {} })),
        infraApi.get('/api/v1/tasks/stats').catch(() => ({ data: {} })),
      ])

      return {
        workflows: workflows.data,
        models: models.data,
        tasks: tasks.data,
      }
    } catch (error) {
      console.error('Error fetching dashboard metrics:', error)
      return {}
    }
  },

  // Recent activity
  async getRecentActivity() {
    try {
      const response = await workflowApi.get('/api/v1/activity/recent')
      return response.data
    } catch (error) {
      console.error('Error fetching recent activity:', error)
      return []
    }
  },

  // Workflow operations
  workflows: {
    list: () => workflowApi.get('/api/v1/workflows'),
    get: (id) => workflowApi.get(`/api/v1/workflows/${id}`),
    create: (data) => workflowApi.post('/api/v1/workflows', data),
    update: (id, data) => workflowApi.put(`/api/v1/workflows/${id}`, data),
    delete: (id) => workflowApi.delete(`/api/v1/workflows/${id}`),
    execute: (id) => workflowApi.post(`/api/v1/workflows/${id}/execute`),
  },

  // Model operations
  models: {
    list: () => modelsApi.get('/api/v1/models'),
    get: (id) => modelsApi.get(`/api/v1/models/${id}`),
    upload: (data) => modelsApi.post('/api/v1/models', data),
    delete: (id) => modelsApi.delete(`/api/v1/models/${id}`),
    deploy: (id) => modelsApi.post(`/api/v1/models/${id}/deploy`),
  },

  // Processing operations
  processing: {
    generate: (data) => processingApi.post('/api/v1/generate', data),
    analyze: (data) => processingApi.post('/api/v1/analyze', data),
    optimize: (data) => processingApi.post('/api/v1/optimize', data),
  },

  // Infrastructure operations
  infrastructure: {
    getResources: () => infraApi.get('/api/v1/resources'),
    getMetrics: () => infraApi.get('/api/v1/metrics'),
    scale: (service, replicas) =>
      infraApi.post(`/api/v1/services/${service}/scale`, { replicas }),
  },
}

export default apiService
