/**
 * Workflow Service - API operations for workflow management
 */

const API_BASE_URL = process.env.REACT_APP_API_URL || 'http://localhost:8000/api/v1';

class WorkflowService {
  constructor() {
    this.baseUrl = `${API_BASE_URL}/workflows`;
  }

  /**
   * Get authorization headers
   */
  getHeaders() {
    const token = localStorage.getItem('access_token');
    return {
      'Content-Type': 'application/json',
      ...(token && { Authorization: `Bearer ${token}` }),
    };
  }

  /**
   * Handle API response
   */
  async handleResponse(response) {
    if (!response.ok) {
      const error = await response.json().catch(() => ({}));
      throw new Error(error.message || `HTTP error! status: ${response.status}`);
    }
    return response.json();
  }

  /**
   * Get all workflows with optional filters
   */
  async getWorkflows(params = {}) {
    const queryParams = new URLSearchParams();

    if (params.status) queryParams.append('status', params.status);
    if (params.search) queryParams.append('search', params.search);
    if (params.created_after) queryParams.append('created_after', params.created_after);
    if (params.created_before) queryParams.append('created_before', params.created_before);
    if (params.page) queryParams.append('page', params.page);
    if (params.limit) queryParams.append('limit', params.limit);
    if (params.sort_by) queryParams.append('sort_by', params.sort_by);
    if (params.sort_order) queryParams.append('sort_order', params.sort_order);

    const url = `${this.baseUrl}?${queryParams.toString()}`;
    const response = await fetch(url, {
      method: 'GET',
      headers: this.getHeaders(),
    });

    return this.handleResponse(response);
  }

  /**
   * Get a single workflow by ID
   */
  async getWorkflow(workflowId) {
    const response = await fetch(`${this.baseUrl}/${workflowId}`, {
      method: 'GET',
      headers: this.getHeaders(),
    });

    return this.handleResponse(response);
  }

  /**
   * Create a new workflow
   */
  async createWorkflow(workflowData) {
    const response = await fetch(this.baseUrl, {
      method: 'POST',
      headers: this.getHeaders(),
      body: JSON.stringify(workflowData),
    });

    return this.handleResponse(response);
  }

  /**
   * Update an existing workflow
   */
  async updateWorkflow(workflowId, workflowData) {
    const response = await fetch(`${this.baseUrl}/${workflowId}`, {
      method: 'PUT',
      headers: this.getHeaders(),
      body: JSON.stringify(workflowData),
    });

    return this.handleResponse(response);
  }

  /**
   * Delete a workflow
   */
  async deleteWorkflow(workflowId) {
    const response = await fetch(`${this.baseUrl}/${workflowId}`, {
      method: 'DELETE',
      headers: this.getHeaders(),
    });

    return this.handleResponse(response);
  }

  /**
   * Clone a workflow
   */
  async cloneWorkflow(workflowId, newName) {
    const response = await fetch(`${this.baseUrl}/${workflowId}/clone`, {
      method: 'POST',
      headers: this.getHeaders(),
      body: JSON.stringify({ name: newName }),
    });

    return this.handleResponse(response);
  }

  /**
   * Execute a workflow
   */
  async executeWorkflow(workflowId, params = {}) {
    const response = await fetch(`${this.baseUrl}/${workflowId}/execute`, {
      method: 'POST',
      headers: this.getHeaders(),
      body: JSON.stringify(params),
    });

    return this.handleResponse(response);
  }

  /**
   * Cancel a workflow execution
   */
  async cancelExecution(executionId) {
    const response = await fetch(`${this.baseUrl}/executions/${executionId}/cancel`, {
      method: 'POST',
      headers: this.getHeaders(),
    });

    return this.handleResponse(response);
  }

  /**
   * Retry a failed workflow execution
   */
  async retryExecution(executionId) {
    const response = await fetch(`${this.baseUrl}/executions/${executionId}/retry`, {
      method: 'POST',
      headers: this.getHeaders(),
    });

    return this.handleResponse(response);
  }

  /**
   * Get workflow executions
   */
  async getExecutions(workflowId, params = {}) {
    const queryParams = new URLSearchParams();

    if (params.status) queryParams.append('status', params.status);
    if (params.page) queryParams.append('page', params.page);
    if (params.limit) queryParams.append('limit', params.limit);

    const url = `${this.baseUrl}/${workflowId}/executions?${queryParams.toString()}`;
    const response = await fetch(url, {
      method: 'GET',
      headers: this.getHeaders(),
    });

    return this.handleResponse(response);
  }

  /**
   * Get a single execution by ID
   */
  async getExecution(executionId) {
    const response = await fetch(`${this.baseUrl}/executions/${executionId}`, {
      method: 'GET',
      headers: this.getHeaders(),
    });

    return this.handleResponse(response);
  }

  /**
   * Get execution logs
   */
  async getExecutionLogs(executionId, params = {}) {
    const queryParams = new URLSearchParams();

    if (params.level) queryParams.append('level', params.level);
    if (params.task_id) queryParams.append('task_id', params.task_id);
    if (params.limit) queryParams.append('limit', params.limit);

    const url = `${this.baseUrl}/executions/${executionId}/logs?${queryParams.toString()}`;
    const response = await fetch(url, {
      method: 'GET',
      headers: this.getHeaders(),
    });

    return this.handleResponse(response);
  }

  /**
   * Get workflow tasks
   */
  async getTasks(workflowId) {
    const response = await fetch(`${this.baseUrl}/${workflowId}/tasks`, {
      method: 'GET',
      headers: this.getHeaders(),
    });

    return this.handleResponse(response);
  }

  /**
   * Get a single task by ID
   */
  async getTask(taskId) {
    const response = await fetch(`${this.baseUrl}/tasks/${taskId}`, {
      method: 'GET',
      headers: this.getHeaders(),
    });

    return this.handleResponse(response);
  }

  /**
   * Create a new task
   */
  async createTask(workflowId, taskData) {
    const response = await fetch(`${this.baseUrl}/${workflowId}/tasks`, {
      method: 'POST',
      headers: this.getHeaders(),
      body: JSON.stringify(taskData),
    });

    return this.handleResponse(response);
  }

  /**
   * Update a task
   */
  async updateTask(taskId, taskData) {
    const response = await fetch(`${this.baseUrl}/tasks/${taskId}`, {
      method: 'PUT',
      headers: this.getHeaders(),
      body: JSON.stringify(taskData),
    });

    return this.handleResponse(response);
  }

  /**
   * Delete a task
   */
  async deleteTask(taskId) {
    const response = await fetch(`${this.baseUrl}/tasks/${taskId}`, {
      method: 'DELETE',
      headers: this.getHeaders(),
    });

    return this.handleResponse(response);
  }

  /**
   * Validate workflow configuration
   */
  async validateWorkflow(workflowData) {
    const response = await fetch(`${this.baseUrl}/validate`, {
      method: 'POST',
      headers: this.getHeaders(),
      body: JSON.stringify(workflowData),
    });

    return this.handleResponse(response);
  }

  /**
   * Get workflow templates
   */
  async getTemplates() {
    const response = await fetch(`${this.baseUrl}/templates`, {
      method: 'GET',
      headers: this.getHeaders(),
    });

    return this.handleResponse(response);
  }

  /**
   * Create workflow from template
   */
  async createFromTemplate(templateId, workflowData) {
    const response = await fetch(`${this.baseUrl}/templates/${templateId}/create`, {
      method: 'POST',
      headers: this.getHeaders(),
      body: JSON.stringify(workflowData),
    });

    return this.handleResponse(response);
  }

  /**
   * Get workflow metrics
   */
  async getMetrics(workflowId, params = {}) {
    const queryParams = new URLSearchParams();

    if (params.period) queryParams.append('period', params.period);
    if (params.start_date) queryParams.append('start_date', params.start_date);
    if (params.end_date) queryParams.append('end_date', params.end_date);

    const url = `${this.baseUrl}/${workflowId}/metrics?${queryParams.toString()}`;
    const response = await fetch(url, {
      method: 'GET',
      headers: this.getHeaders(),
    });

    return this.handleResponse(response);
  }

  /**
   * Subscribe to execution updates via WebSocket
   */
  subscribeToExecution(executionId, callbacks = {}) {
    const wsUrl = `${API_BASE_URL.replace('http', 'ws')}/workflows/executions/${executionId}/stream`;
    const ws = new WebSocket(wsUrl);

    ws.onopen = () => {
      if (callbacks.onOpen) callbacks.onOpen();
    };

    ws.onmessage = (event) => {
      const data = JSON.parse(event.data);
      if (callbacks.onMessage) callbacks.onMessage(data);
    };

    ws.onerror = (error) => {
      if (callbacks.onError) callbacks.onError(error);
    };

    ws.onclose = () => {
      if (callbacks.onClose) callbacks.onClose();
    };

    return ws;
  }
}

export const workflowService = new WorkflowService();
export default workflowService;
