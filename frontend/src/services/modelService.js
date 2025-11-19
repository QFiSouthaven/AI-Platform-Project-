/**
 * Model Management API Service
 * Handles all API calls related to model management
 */

const API_BASE_URL = process.env.REACT_APP_API_URL || '/api/v1';

class ModelService {
  constructor() {
    this.baseUrl = `${API_BASE_URL}/models`;
  }

  /**
   * Get authorization headers
   */
  getHeaders() {
    const token = localStorage.getItem('token');
    return {
      'Content-Type': 'application/json',
      ...(token && { Authorization: `Bearer ${token}` })
    };
  }

  /**
   * Handle API response
   */
  async handleResponse(response) {
    if (!response.ok) {
      const error = await response.json().catch(() => ({
        message: 'An error occurred'
      }));
      throw new Error(error.message || `HTTP error! status: ${response.status}`);
    }
    return response.json();
  }

  // ==================== Model CRUD Operations ====================

  /**
   * Get all models with optional filters
   * @param {Object} params - Query parameters
   * @returns {Promise} - List of models
   */
  async getModels(params = {}) {
    const queryString = new URLSearchParams(
      Object.entries(params).filter(([, value]) => value)
    ).toString();

    const url = queryString ? `${this.baseUrl}?${queryString}` : this.baseUrl;

    const response = await fetch(url, {
      method: 'GET',
      headers: this.getHeaders()
    });

    return this.handleResponse(response);
  }

  /**
   * Get a single model by ID
   * @param {string} modelId - Model ID
   * @returns {Promise} - Model details
   */
  async getModel(modelId) {
    const response = await fetch(`${this.baseUrl}/${modelId}`, {
      method: 'GET',
      headers: this.getHeaders()
    });

    return this.handleResponse(response);
  }

  /**
   * Create a new model
   * @param {Object} modelData - Model data
   * @returns {Promise} - Created model
   */
  async createModel(modelData) {
    const response = await fetch(this.baseUrl, {
      method: 'POST',
      headers: this.getHeaders(),
      body: JSON.stringify(modelData)
    });

    return this.handleResponse(response);
  }

  /**
   * Update a model
   * @param {string} modelId - Model ID
   * @param {Object} modelData - Updated model data
   * @returns {Promise} - Updated model
   */
  async updateModel(modelId, modelData) {
    const response = await fetch(`${this.baseUrl}/${modelId}`, {
      method: 'PUT',
      headers: this.getHeaders(),
      body: JSON.stringify(modelData)
    });

    return this.handleResponse(response);
  }

  /**
   * Delete a model
   * @param {string} modelId - Model ID
   * @returns {Promise} - Deletion result
   */
  async deleteModel(modelId) {
    const response = await fetch(`${this.baseUrl}/${modelId}`, {
      method: 'DELETE',
      headers: this.getHeaders()
    });

    return this.handleResponse(response);
  }

  // ==================== Upload & Download ====================

  /**
   * Upload a model file
   * @param {FormData} formData - Form data with file and metadata
   * @param {Function} onProgress - Progress callback
   * @returns {Promise} - Upload result
   */
  async uploadModel(formData, onProgress) {
    return new Promise((resolve, reject) => {
      const xhr = new XMLHttpRequest();

      xhr.upload.addEventListener('progress', (event) => {
        if (event.lengthComputable && onProgress) {
          const progress = Math.round((event.loaded / event.total) * 100);
          onProgress(progress);
        }
      });

      xhr.addEventListener('load', () => {
        if (xhr.status >= 200 && xhr.status < 300) {
          try {
            const response = JSON.parse(xhr.responseText);
            resolve(response);
          } catch {
            resolve({ status: 'success' });
          }
        } else {
          try {
            const error = JSON.parse(xhr.responseText);
            reject(new Error(error.message || 'Upload failed'));
          } catch {
            reject(new Error('Upload failed'));
          }
        }
      });

      xhr.addEventListener('error', () => {
        reject(new Error('Network error during upload'));
      });

      xhr.addEventListener('abort', () => {
        reject(new Error('Upload aborted'));
      });

      xhr.open('POST', `${this.baseUrl}/upload`);

      const token = localStorage.getItem('token');
      if (token) {
        xhr.setRequestHeader('Authorization', `Bearer ${token}`);
      }

      xhr.send(formData);
    });
  }

  /**
   * Download a model file
   * @param {string} modelId - Model ID
   * @returns {Promise} - Download URL or blob
   */
  async downloadModel(modelId) {
    const response = await fetch(`${this.baseUrl}/${modelId}/download`, {
      method: 'GET',
      headers: this.getHeaders()
    });

    if (!response.ok) {
      throw new Error('Download failed');
    }

    // Get filename from Content-Disposition header
    const contentDisposition = response.headers.get('Content-Disposition');
    let filename = 'model';
    if (contentDisposition) {
      const match = contentDisposition.match(/filename="?([^"]+)"?/);
      if (match) {
        filename = match[1];
      }
    }

    // Create download
    const blob = await response.blob();
    const url = window.URL.createObjectURL(blob);
    const a = document.createElement('a');
    a.href = url;
    a.download = filename;
    document.body.appendChild(a);
    a.click();
    window.URL.revokeObjectURL(url);
    document.body.removeChild(a);

    return { status: 'success', filename };
  }

  // ==================== Model Loading Operations ====================

  /**
   * Load a model into memory
   * @param {string} modelId - Model ID
   * @returns {Promise} - Load result
   */
  async loadModel(modelId) {
    const response = await fetch(`${this.baseUrl}/${modelId}/load`, {
      method: 'POST',
      headers: this.getHeaders()
    });

    return this.handleResponse(response);
  }

  /**
   * Unload a model from memory
   * @param {string} modelId - Model ID
   * @returns {Promise} - Unload result
   */
  async unloadModel(modelId) {
    const response = await fetch(`${this.baseUrl}/${modelId}/unload`, {
      method: 'POST',
      headers: this.getHeaders()
    });

    return this.handleResponse(response);
  }

  // ==================== Version Management ====================

  /**
   * Get all versions of a model
   * @param {string} modelId - Model ID
   * @returns {Promise} - List of versions
   */
  async getVersions(modelId) {
    const response = await fetch(`${this.baseUrl}/${modelId}/versions`, {
      method: 'GET',
      headers: this.getHeaders()
    });

    return this.handleResponse(response);
  }

  /**
   * Compare two versions of a model
   * @param {string} modelId - Model ID
   * @param {string} version1 - First version
   * @param {string} version2 - Second version
   * @returns {Promise} - Comparison result
   */
  async compareVersions(modelId, version1, version2) {
    const response = await fetch(
      `${this.baseUrl}/${modelId}/versions/compare?v1=${version1}&v2=${version2}`,
      {
        method: 'GET',
        headers: this.getHeaders()
      }
    );

    return this.handleResponse(response);
  }

  /**
   * Create a new version of a model
   * @param {string} modelId - Model ID
   * @param {FormData} formData - Version data with file
   * @param {Function} onProgress - Progress callback
   * @returns {Promise} - Created version
   */
  async createVersion(modelId, formData, onProgress) {
    return new Promise((resolve, reject) => {
      const xhr = new XMLHttpRequest();

      xhr.upload.addEventListener('progress', (event) => {
        if (event.lengthComputable && onProgress) {
          const progress = Math.round((event.loaded / event.total) * 100);
          onProgress(progress);
        }
      });

      xhr.addEventListener('load', () => {
        if (xhr.status >= 200 && xhr.status < 300) {
          try {
            const response = JSON.parse(xhr.responseText);
            resolve(response);
          } catch {
            resolve({ status: 'success' });
          }
        } else {
          try {
            const error = JSON.parse(xhr.responseText);
            reject(new Error(error.message || 'Version creation failed'));
          } catch {
            reject(new Error('Version creation failed'));
          }
        }
      });

      xhr.addEventListener('error', () => {
        reject(new Error('Network error'));
      });

      xhr.open('POST', `${this.baseUrl}/${modelId}/versions`);

      const token = localStorage.getItem('token');
      if (token) {
        xhr.setRequestHeader('Authorization', `Bearer ${token}`);
      }

      xhr.send(formData);
    });
  }

  // ==================== Plugin Management ====================

  /**
   * Get installed plugins
   * @returns {Promise} - List of installed plugins
   */
  async getInstalledPlugins() {
    const response = await fetch(`${API_BASE_URL}/plugins`, {
      method: 'GET',
      headers: this.getHeaders()
    });

    return this.handleResponse(response);
  }

  /**
   * Get marketplace plugins
   * @returns {Promise} - List of marketplace plugins
   */
  async getMarketplacePlugins() {
    const response = await fetch(`${API_BASE_URL}/plugins/marketplace`, {
      method: 'GET',
      headers: this.getHeaders()
    });

    return this.handleResponse(response);
  }

  /**
   * Install a plugin
   * @param {string} pluginId - Plugin ID
   * @returns {Promise} - Installation result
   */
  async installPlugin(pluginId) {
    const response = await fetch(`${API_BASE_URL}/plugins/${pluginId}/install`, {
      method: 'POST',
      headers: this.getHeaders()
    });

    return this.handleResponse(response);
  }

  /**
   * Uninstall a plugin
   * @param {string} pluginId - Plugin ID
   * @returns {Promise} - Uninstallation result
   */
  async uninstallPlugin(pluginId) {
    const response = await fetch(`${API_BASE_URL}/plugins/${pluginId}`, {
      method: 'DELETE',
      headers: this.getHeaders()
    });

    return this.handleResponse(response);
  }

  /**
   * Enable a plugin
   * @param {string} pluginId - Plugin ID
   * @returns {Promise} - Enable result
   */
  async enablePlugin(pluginId) {
    const response = await fetch(`${API_BASE_URL}/plugins/${pluginId}/enable`, {
      method: 'POST',
      headers: this.getHeaders()
    });

    return this.handleResponse(response);
  }

  /**
   * Disable a plugin
   * @param {string} pluginId - Plugin ID
   * @returns {Promise} - Disable result
   */
  async disablePlugin(pluginId) {
    const response = await fetch(`${API_BASE_URL}/plugins/${pluginId}/disable`, {
      method: 'POST',
      headers: this.getHeaders()
    });

    return this.handleResponse(response);
  }

  /**
   * Get plugin configuration
   * @param {string} pluginId - Plugin ID
   * @returns {Promise} - Plugin configuration
   */
  async getPluginConfig(pluginId) {
    const response = await fetch(`${API_BASE_URL}/plugins/${pluginId}/config`, {
      method: 'GET',
      headers: this.getHeaders()
    });

    return this.handleResponse(response);
  }

  /**
   * Update plugin configuration
   * @param {string} pluginId - Plugin ID
   * @param {Object} config - New configuration
   * @returns {Promise} - Updated configuration
   */
  async updatePluginConfig(pluginId, config) {
    const response = await fetch(`${API_BASE_URL}/plugins/${pluginId}/config`, {
      method: 'PUT',
      headers: this.getHeaders(),
      body: JSON.stringify(config)
    });

    return this.handleResponse(response);
  }

  /**
   * Get plugin execution logs
   * @param {string} pluginId - Plugin ID
   * @param {Object} params - Query parameters (limit, offset, level)
   * @returns {Promise} - Logs
   */
  async getPluginLogs(pluginId, params = {}) {
    const queryString = new URLSearchParams(
      Object.entries(params).filter(([, value]) => value)
    ).toString();

    const url = queryString
      ? `${API_BASE_URL}/plugins/${pluginId}/logs?${queryString}`
      : `${API_BASE_URL}/plugins/${pluginId}/logs`;

    const response = await fetch(url, {
      method: 'GET',
      headers: this.getHeaders()
    });

    return this.handleResponse(response);
  }

  // ==================== Utility Methods ====================

  /**
   * Get model statistics
   * @returns {Promise} - Statistics
   */
  async getStatistics() {
    const response = await fetch(`${this.baseUrl}/statistics`, {
      method: 'GET',
      headers: this.getHeaders()
    });

    return this.handleResponse(response);
  }

  /**
   * Search models
   * @param {string} query - Search query
   * @param {Object} filters - Additional filters
   * @returns {Promise} - Search results
   */
  async searchModels(query, filters = {}) {
    const params = {
      q: query,
      ...filters
    };

    return this.getModels(params);
  }

  /**
   * Get model metrics
   * @param {string} modelId - Model ID
   * @returns {Promise} - Model metrics
   */
  async getModelMetrics(modelId) {
    const response = await fetch(`${this.baseUrl}/${modelId}/metrics`, {
      method: 'GET',
      headers: this.getHeaders()
    });

    return this.handleResponse(response);
  }

  /**
   * Update model metrics
   * @param {string} modelId - Model ID
   * @param {Object} metrics - Metrics data
   * @returns {Promise} - Updated metrics
   */
  async updateModelMetrics(modelId, metrics) {
    const response = await fetch(`${this.baseUrl}/${modelId}/metrics`, {
      method: 'PUT',
      headers: this.getHeaders(),
      body: JSON.stringify(metrics)
    });

    return this.handleResponse(response);
  }
}

// Export singleton instance
const modelService = new ModelService();
export default modelService;
