import React, { useState, useEffect, useCallback } from 'react';
import CacheStats from '../../components/integration/CacheStats';
import JsonEditor from '../../components/integration/JsonEditor';
import {
  searchCache,
  getCache,
  setCache,
  deleteCache,
  getCacheStats,
  clearCache,
  bulkDeleteCache,
} from '../../services/integrationService';

const CacheManager = () => {
  const [cacheEntries, setCacheEntries] = useState([]);
  const [stats, setStats] = useState(null);
  const [loading, setLoading] = useState(true);
  const [searchPattern, setSearchPattern] = useState('*');
  const [selectedKeys, setSelectedKeys] = useState([]);
  const [showSetModal, setShowSetModal] = useState(false);
  const [showGetModal, setShowGetModal] = useState(false);
  const [currentEntry, setCurrentEntry] = useState(null);

  // Form state for Set operation
  const [newKey, setNewKey] = useState('');
  const [newValue, setNewValue] = useState('');
  const [newTtl, setNewTtl] = useState('');
  const [isValidJson, setIsValidJson] = useState(false);

  const fetchData = useCallback(async () => {
    try {
      setLoading(true);
      const [entriesData, statsData] = await Promise.all([
        searchCache(searchPattern),
        getCacheStats(),
      ]);
      setCacheEntries(entriesData.data || []);
      setStats(statsData.data || {});
    } catch (error) {
      console.error('Failed to fetch cache data:', error);
    } finally {
      setLoading(false);
    }
  }, [searchPattern]);

  useEffect(() => {
    fetchData();
  }, [fetchData]);

  const handleSearch = (e) => {
    e.preventDefault();
    fetchData();
  };

  const handleGetEntry = async (key) => {
    try {
      const result = await getCache(key);
      setCurrentEntry({
        key,
        value: result.data?.value,
        ttl: result.data?.ttl,
      });
      setShowGetModal(true);
    } catch (error) {
      console.error('Failed to get cache entry:', error);
    }
  };

  const handleSetEntry = async (e) => {
    e.preventDefault();
    if (!newKey || !isValidJson) return;

    try {
      await setCache(newKey, JSON.parse(newValue), newTtl ? parseInt(newTtl) : null);
      setShowSetModal(false);
      setNewKey('');
      setNewValue('');
      setNewTtl('');
      fetchData();
    } catch (error) {
      console.error('Failed to set cache entry:', error);
    }
  };

  const handleDeleteEntry = async (key) => {
    if (!window.confirm(`Are you sure you want to delete "${key}"?`)) return;

    try {
      await deleteCache(key);
      fetchData();
    } catch (error) {
      console.error('Failed to delete cache entry:', error);
    }
  };

  const handleBulkDelete = async () => {
    if (selectedKeys.length === 0) return;
    if (!window.confirm(`Delete ${selectedKeys.length} selected entries?`)) return;

    try {
      await bulkDeleteCache(selectedKeys);
      setSelectedKeys([]);
      fetchData();
    } catch (error) {
      console.error('Failed to bulk delete:', error);
    }
  };

  const handleClearCache = async () => {
    if (!window.confirm('Are you sure you want to clear ALL cache entries?')) return;

    try {
      await clearCache();
      setSelectedKeys([]);
      fetchData();
    } catch (error) {
      console.error('Failed to clear cache:', error);
    }
  };

  const toggleSelectKey = (key) => {
    setSelectedKeys((prev) =>
      prev.includes(key) ? prev.filter((k) => k !== key) : [...prev, key]
    );
  };

  const toggleSelectAll = () => {
    if (selectedKeys.length === cacheEntries.length) {
      setSelectedKeys([]);
    } else {
      setSelectedKeys(cacheEntries.map((e) => e.key));
    }
  };

  const formatTtl = (seconds) => {
    if (!seconds || seconds < 0) return 'No expiry';
    if (seconds < 60) return `${seconds}s`;
    if (seconds < 3600) return `${Math.floor(seconds / 60)}m`;
    if (seconds < 86400) return `${Math.floor(seconds / 3600)}h`;
    return `${Math.floor(seconds / 86400)}d`;
  };

  const formatValue = (value) => {
    if (typeof value === 'object') {
      return JSON.stringify(value);
    }
    return String(value);
  };

  return (
    <div className="p-6 space-y-6">
      {/* Header */}
      <div className="flex items-center justify-between">
        <div>
          <h1 className="text-2xl font-bold text-gray-900">Cache Manager</h1>
          <p className="text-sm text-gray-500">Manage Redis cache entries</p>
        </div>
        <div className="flex items-center space-x-3">
          <button
            onClick={() => setShowSetModal(true)}
            className="px-4 py-2 text-sm font-medium text-white bg-blue-600 rounded-lg hover:bg-blue-700"
          >
            Set Entry
          </button>
          <button
            onClick={handleClearCache}
            className="px-4 py-2 text-sm font-medium text-white bg-red-600 rounded-lg hover:bg-red-700"
          >
            Clear All Cache
          </button>
        </div>
      </div>

      {/* Cache Statistics */}
      <CacheStats stats={stats} loading={loading} />

      {/* Search and Actions Bar */}
      <div className="bg-white rounded-lg shadow-md p-4">
        <div className="flex flex-col md:flex-row md:items-center md:justify-between space-y-3 md:space-y-0">
          <form onSubmit={handleSearch} className="flex items-center space-x-2">
            <input
              type="text"
              value={searchPattern}
              onChange={(e) => setSearchPattern(e.target.value)}
              placeholder="Search pattern (e.g., user:*, session:*)"
              className="px-3 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-blue-500 focus:border-blue-500 w-64"
            />
            <button
              type="submit"
              className="px-4 py-2 text-sm font-medium text-white bg-blue-600 rounded-lg hover:bg-blue-700"
            >
              Search
            </button>
          </form>
          <div className="flex items-center space-x-2">
            {selectedKeys.length > 0 && (
              <button
                onClick={handleBulkDelete}
                className="px-3 py-1.5 text-sm font-medium text-red-700 bg-red-100 rounded-lg hover:bg-red-200"
              >
                Delete Selected ({selectedKeys.length})
              </button>
            )}
            <button
              onClick={fetchData}
              className="px-3 py-1.5 text-sm font-medium text-gray-700 bg-gray-100 rounded-lg hover:bg-gray-200"
            >
              Refresh
            </button>
          </div>
        </div>
      </div>

      {/* Cache Entries Table */}
      <div className="bg-white rounded-lg shadow-md overflow-hidden">
        <div className="overflow-x-auto">
          <table className="min-w-full divide-y divide-gray-200">
            <thead className="bg-gray-50">
              <tr>
                <th className="px-6 py-3 text-left">
                  <input
                    type="checkbox"
                    checked={selectedKeys.length === cacheEntries.length && cacheEntries.length > 0}
                    onChange={toggleSelectAll}
                    className="rounded border-gray-300 text-blue-600 focus:ring-blue-500"
                  />
                </th>
                <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">
                  Key
                </th>
                <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">
                  Value
                </th>
                <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">
                  TTL
                </th>
                <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">
                  Type
                </th>
                <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">
                  Actions
                </th>
              </tr>
            </thead>
            <tbody className="bg-white divide-y divide-gray-200">
              {loading ? (
                <tr>
                  <td colSpan="6" className="px-6 py-4 text-center text-gray-500">
                    Loading cache entries...
                  </td>
                </tr>
              ) : cacheEntries.length === 0 ? (
                <tr>
                  <td colSpan="6" className="px-6 py-4 text-center text-gray-500">
                    No cache entries found
                  </td>
                </tr>
              ) : (
                cacheEntries.map((entry) => (
                  <tr key={entry.key} className="hover:bg-gray-50">
                    <td className="px-6 py-4">
                      <input
                        type="checkbox"
                        checked={selectedKeys.includes(entry.key)}
                        onChange={() => toggleSelectKey(entry.key)}
                        className="rounded border-gray-300 text-blue-600 focus:ring-blue-500"
                      />
                    </td>
                    <td className="px-6 py-4 whitespace-nowrap">
                      <span className="text-sm font-mono text-gray-900">{entry.key}</span>
                    </td>
                    <td className="px-6 py-4">
                      <span className="text-sm text-gray-500 max-w-xs truncate block">
                        {formatValue(entry.value).substring(0, 50)}
                        {formatValue(entry.value).length > 50 ? '...' : ''}
                      </span>
                    </td>
                    <td className="px-6 py-4 whitespace-nowrap">
                      <span className={`text-sm ${entry.ttl && entry.ttl < 60 ? 'text-red-600' : 'text-gray-500'}`}>
                        {formatTtl(entry.ttl)}
                      </span>
                    </td>
                    <td className="px-6 py-4 whitespace-nowrap">
                      <span className="px-2 py-0.5 text-xs font-medium bg-gray-100 text-gray-800 rounded">
                        {entry.type || 'string'}
                      </span>
                    </td>
                    <td className="px-6 py-4 whitespace-nowrap text-sm">
                      <button
                        onClick={() => handleGetEntry(entry.key)}
                        className="text-blue-600 hover:text-blue-900 mr-3"
                      >
                        View
                      </button>
                      <button
                        onClick={() => handleDeleteEntry(entry.key)}
                        className="text-red-600 hover:text-red-900"
                      >
                        Delete
                      </button>
                    </td>
                  </tr>
                ))
              )}
            </tbody>
          </table>
        </div>
        <div className="px-6 py-3 bg-gray-50 border-t border-gray-200 text-sm text-gray-500">
          Showing {cacheEntries.length} entries
        </div>
      </div>

      {/* Set Entry Modal */}
      {showSetModal && (
        <div className="fixed inset-0 z-50 overflow-y-auto">
          <div className="flex items-center justify-center min-h-screen px-4">
            <div className="fixed inset-0 bg-gray-500 bg-opacity-75" onClick={() => setShowSetModal(false)} />
            <div className="relative bg-white rounded-lg shadow-xl max-w-lg w-full p-6">
              <h3 className="text-lg font-semibold text-gray-900 mb-4">Set Cache Entry</h3>
              <form onSubmit={handleSetEntry} className="space-y-4">
                <div>
                  <label className="block text-sm font-medium text-gray-700 mb-1">Key</label>
                  <input
                    type="text"
                    value={newKey}
                    onChange={(e) => setNewKey(e.target.value)}
                    placeholder="cache:key:name"
                    className="w-full px-3 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-blue-500 focus:border-blue-500"
                    required
                  />
                </div>
                <div>
                  <label className="block text-sm font-medium text-gray-700 mb-1">Value (JSON)</label>
                  <JsonEditor
                    value={newValue}
                    onChange={setNewValue}
                    onValidation={(result) => setIsValidJson(result.valid)}
                    height="150px"
                  />
                </div>
                <div>
                  <label className="block text-sm font-medium text-gray-700 mb-1">TTL (seconds)</label>
                  <input
                    type="number"
                    value={newTtl}
                    onChange={(e) => setNewTtl(e.target.value)}
                    placeholder="Leave empty for no expiry"
                    min="1"
                    className="w-full px-3 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-blue-500 focus:border-blue-500"
                  />
                </div>
                <div className="flex justify-end space-x-3 pt-4">
                  <button
                    type="button"
                    onClick={() => setShowSetModal(false)}
                    className="px-4 py-2 text-sm font-medium text-gray-700 bg-gray-100 rounded-lg hover:bg-gray-200"
                  >
                    Cancel
                  </button>
                  <button
                    type="submit"
                    disabled={!newKey || !isValidJson}
                    className="px-4 py-2 text-sm font-medium text-white bg-blue-600 rounded-lg hover:bg-blue-700 disabled:opacity-50 disabled:cursor-not-allowed"
                  >
                    Set Entry
                  </button>
                </div>
              </form>
            </div>
          </div>
        </div>
      )}

      {/* View Entry Modal */}
      {showGetModal && currentEntry && (
        <div className="fixed inset-0 z-50 overflow-y-auto">
          <div className="flex items-center justify-center min-h-screen px-4">
            <div className="fixed inset-0 bg-gray-500 bg-opacity-75" onClick={() => setShowGetModal(false)} />
            <div className="relative bg-white rounded-lg shadow-xl max-w-2xl w-full p-6">
              <div className="flex items-center justify-between mb-4">
                <h3 className="text-lg font-semibold text-gray-900">Cache Entry Details</h3>
                <button
                  onClick={() => setShowGetModal(false)}
                  className="text-gray-400 hover:text-gray-600"
                >
                  <svg className="w-6 h-6" fill="none" viewBox="0 0 24 24" stroke="currentColor">
                    <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M6 18L18 6M6 6l12 12" />
                  </svg>
                </button>
              </div>
              <div className="space-y-4">
                <div>
                  <label className="text-sm font-medium text-gray-500">Key</label>
                  <p className="mt-1 text-sm font-mono text-gray-900 bg-gray-50 p-2 rounded">
                    {currentEntry.key}
                  </p>
                </div>
                <div>
                  <label className="text-sm font-medium text-gray-500">TTL</label>
                  <p className="mt-1 text-sm text-gray-900">{formatTtl(currentEntry.ttl)}</p>
                </div>
                <div>
                  <label className="text-sm font-medium text-gray-500">Value</label>
                  <pre className="mt-1 p-3 bg-gray-50 rounded-lg text-sm text-gray-900 overflow-x-auto max-h-64">
                    {typeof currentEntry.value === 'object'
                      ? JSON.stringify(currentEntry.value, null, 2)
                      : currentEntry.value}
                  </pre>
                </div>
              </div>
              <div className="mt-6 flex justify-end space-x-3">
                <button
                  onClick={() => handleDeleteEntry(currentEntry.key)}
                  className="px-4 py-2 text-sm font-medium text-red-700 bg-red-100 rounded-lg hover:bg-red-200"
                >
                  Delete
                </button>
                <button
                  onClick={() => setShowGetModal(false)}
                  className="px-4 py-2 text-sm font-medium text-gray-700 bg-gray-100 rounded-lg hover:bg-gray-200"
                >
                  Close
                </button>
              </div>
            </div>
          </div>
        </div>
      )}
    </div>
  );
};

export default CacheManager;
