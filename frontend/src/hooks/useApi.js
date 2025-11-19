import { useQuery, useMutation, useQueryClient } from '@tanstack/react-query'
import apiService from '../services/api'
import { REFRESH_INTERVALS } from '../utils/constants'

// Hook for checking module health
export const useModuleHealth = (moduleName) => {
  return useQuery({
    queryKey: ['health', moduleName],
    queryFn: () => apiService.checkHealth(moduleName),
    refetchInterval: REFRESH_INTERVALS.STATUS,
    staleTime: REFRESH_INTERVALS.STATUS,
  })
}

// Hook for checking all modules health
export const useAllModulesHealth = () => {
  const modules = ['gateway', 'workflow', 'processing', 'data', 'models', 'infra']

  return useQuery({
    queryKey: ['health', 'all'],
    queryFn: async () => {
      const results = await Promise.all(
        modules.map(async (module) => ({
          module,
          ...(await apiService.checkHealth(module)),
        }))
      )
      return results
    },
    refetchInterval: REFRESH_INTERVALS.STATUS,
    staleTime: REFRESH_INTERVALS.STATUS,
  })
}

// Hook for dashboard metrics
export const useDashboardMetrics = () => {
  return useQuery({
    queryKey: ['dashboard', 'metrics'],
    queryFn: () => apiService.getDashboardMetrics(),
    refetchInterval: REFRESH_INTERVALS.METRICS,
    staleTime: REFRESH_INTERVALS.METRICS,
  })
}

// Hook for recent activity
export const useRecentActivity = () => {
  return useQuery({
    queryKey: ['activity', 'recent'],
    queryFn: () => apiService.getRecentActivity(),
    refetchInterval: REFRESH_INTERVALS.ACTIVITY,
    staleTime: REFRESH_INTERVALS.ACTIVITY,
  })
}

// Hook for workflows
export const useWorkflows = () => {
  return useQuery({
    queryKey: ['workflows'],
    queryFn: async () => {
      const response = await apiService.workflows.list()
      return response.data
    },
  })
}

// Hook for creating workflow
export const useCreateWorkflow = () => {
  const queryClient = useQueryClient()

  return useMutation({
    mutationFn: (data) => apiService.workflows.create(data),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ['workflows'] })
    },
  })
}

// Hook for executing workflow
export const useExecuteWorkflow = () => {
  const queryClient = useQueryClient()

  return useMutation({
    mutationFn: (id) => apiService.workflows.execute(id),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ['workflows'] })
      queryClient.invalidateQueries({ queryKey: ['activity'] })
    },
  })
}

// Hook for models
export const useModels = () => {
  return useQuery({
    queryKey: ['models'],
    queryFn: async () => {
      const response = await apiService.models.list()
      return response.data
    },
  })
}

// Hook for deploying model
export const useDeployModel = () => {
  const queryClient = useQueryClient()

  return useMutation({
    mutationFn: (id) => apiService.models.deploy(id),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ['models'] })
    },
  })
}

// Hook for infrastructure metrics
export const useInfraMetrics = () => {
  return useQuery({
    queryKey: ['infra', 'metrics'],
    queryFn: async () => {
      const response = await apiService.infrastructure.getMetrics()
      return response.data
    },
    refetchInterval: REFRESH_INTERVALS.METRICS,
  })
}

// Hook for scaling service
export const useScaleService = () => {
  const queryClient = useQueryClient()

  return useMutation({
    mutationFn: ({ service, replicas }) =>
      apiService.infrastructure.scale(service, replicas),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ['infra'] })
    },
  })
}

// Generic API hook for custom queries
export const useApiQuery = (key, queryFn, options = {}) => {
  return useQuery({
    queryKey: Array.isArray(key) ? key : [key],
    queryFn,
    ...options,
  })
}

// Generic mutation hook
export const useApiMutation = (mutationFn, options = {}) => {
  const queryClient = useQueryClient()

  return useMutation({
    mutationFn,
    onSuccess: (data, variables, context) => {
      if (options.invalidateKeys) {
        options.invalidateKeys.forEach((key) => {
          queryClient.invalidateQueries({ queryKey: Array.isArray(key) ? key : [key] })
        })
      }
      options.onSuccess?.(data, variables, context)
    },
    ...options,
  })
}
