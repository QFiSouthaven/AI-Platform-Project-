import axios from 'axios';

const API_BASE_URL = process.env.REACT_APP_API_URL || 'http://localhost:8004/api/v1';

const api = axios.create({
  baseURL: API_BASE_URL,
  headers: {
    'Content-Type': 'application/json',
  },
});

// Add auth token to requests
api.interceptors.request.use((config) => {
  const token = localStorage.getItem('token');
  if (token) {
    config.headers.Authorization = `Bearer ${token}`;
  }
  return config;
});

// Event API functions
export const publishEvent = async (topic, message, metadata = {}) => {
  const response = await api.post('/events/publish', {
    topic,
    message,
    metadata,
  });
  return response.data;
};

export const getEvents = async (filters = {}) => {
  const params = new URLSearchParams();
  if (filters.eventType) params.append('event_type', filters.eventType);
  if (filters.startTime) params.append('start_time', filters.startTime);
  if (filters.endTime) params.append('end_time', filters.endTime);
  if (filters.limit) params.append('limit', filters.limit);
  if (filters.offset) params.append('offset', filters.offset);

  const response = await api.get(`/events?${params.toString()}`);
  return response.data;
};

export const getEventById = async (eventId) => {
  const response = await api.get(`/events/${eventId}`);
  return response.data;
};

export const getEventStats = async (timeRange = '24h') => {
  const response = await api.get(`/events/stats?time_range=${timeRange}`);
  return response.data;
};

export const getEventTypes = async () => {
  const response = await api.get('/events/types');
  return response.data;
};

// Cache API functions
export const getCache = async (key) => {
  const response = await api.get(`/cache/${encodeURIComponent(key)}`);
  return response.data;
};

export const setCache = async (key, value, ttl = null) => {
  const response = await api.post('/cache', {
    key,
    value,
    ttl,
  });
  return response.data;
};

export const deleteCache = async (key) => {
  const response = await api.delete(`/cache/${encodeURIComponent(key)}`);
  return response.data;
};

export const searchCache = async (pattern = '*', limit = 100) => {
  const response = await api.get(`/cache/search?pattern=${encodeURIComponent(pattern)}&limit=${limit}`);
  return response.data;
};

export const getCacheStats = async () => {
  const response = await api.get('/cache/stats');
  return response.data;
};

export const clearCache = async (pattern = null) => {
  const response = await api.post('/cache/clear', { pattern });
  return response.data;
};

export const bulkDeleteCache = async (keys) => {
  const response = await api.post('/cache/bulk-delete', { keys });
  return response.data;
};

export const bulkSetCache = async (entries) => {
  const response = await api.post('/cache/bulk-set', { entries });
  return response.data;
};

// Kafka API functions
export const getKafkaTopics = async () => {
  const response = await api.get('/kafka/topics');
  return response.data;
};

export const getTopicDetails = async (topicName) => {
  const response = await api.get(`/kafka/topics/${topicName}`);
  return response.data;
};

export const getConsumerGroups = async () => {
  const response = await api.get('/kafka/consumer-groups');
  return response.data;
};

export const getConsumerGroupDetails = async (groupId) => {
  const response = await api.get(`/kafka/consumer-groups/${groupId}`);
  return response.data;
};

export const getTopicMessages = async (topicName, partition = 0, offset = 0, limit = 100) => {
  const response = await api.get(
    `/kafka/topics/${topicName}/messages?partition=${partition}&offset=${offset}&limit=${limit}`
  );
  return response.data;
};

// WebSocket connection for real-time events
export const createEventStream = (onMessage, onError, onClose) => {
  const wsUrl = process.env.REACT_APP_WS_URL || 'ws://localhost:8004/ws/events';
  const token = localStorage.getItem('token');
  const ws = new WebSocket(`${wsUrl}?token=${token}`);

  ws.onopen = () => {
    console.log('Event stream connected');
  };

  ws.onmessage = (event) => {
    try {
      const data = JSON.parse(event.data);
      onMessage(data);
    } catch (error) {
      console.error('Failed to parse event:', error);
    }
  };

  ws.onerror = (error) => {
    console.error('WebSocket error:', error);
    if (onError) onError(error);
  };

  ws.onclose = (event) => {
    console.log('Event stream closed:', event.code, event.reason);
    if (onClose) onClose(event);
  };

  return ws;
};

// Schema validation
export const validateEventSchema = async (topic, message) => {
  const response = await api.post('/events/validate', {
    topic,
    message,
  });
  return response.data;
};

export default {
  publishEvent,
  getEvents,
  getEventById,
  getEventStats,
  getEventTypes,
  getCache,
  setCache,
  deleteCache,
  searchCache,
  getCacheStats,
  clearCache,
  bulkDeleteCache,
  bulkSetCache,
  getKafkaTopics,
  getTopicDetails,
  getConsumerGroups,
  getConsumerGroupDetails,
  getTopicMessages,
  createEventStream,
  validateEventSchema,
};
