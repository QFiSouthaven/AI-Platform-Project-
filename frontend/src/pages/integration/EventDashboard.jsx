import React, { useState, useEffect, useCallback } from 'react';
import EventStream from '../../components/integration/EventStream';
import { getEvents, getEventStats, getEventTypes } from '../../services/integrationService';

const getEventColor = (eventType) => {
  if (eventType.startsWith('user.')) return 'blue';
  if (eventType.startsWith('workflow.')) return 'green';
  if (eventType.startsWith('processing.')) return 'yellow';
  if (eventType.startsWith('model.')) return 'purple';
  return 'gray';
};

const getColorClasses = (color) => {
  const colors = {
    blue: 'bg-blue-100 text-blue-800 border-blue-200',
    green: 'bg-green-100 text-green-800 border-green-200',
    yellow: 'bg-yellow-100 text-yellow-800 border-yellow-200',
    purple: 'bg-purple-100 text-purple-800 border-purple-200',
    gray: 'bg-gray-100 text-gray-800 border-gray-200',
  };
  return colors[color] || colors.gray;
};

const EventDashboard = () => {
  const [events, setEvents] = useState([]);
  const [eventStats, setEventStats] = useState(null);
  const [eventTypes, setEventTypes] = useState([]);
  const [selectedTypes, setSelectedTypes] = useState([]);
  const [selectedEvent, setSelectedEvent] = useState(null);
  const [loading, setLoading] = useState(true);
  const [timeRange, setTimeRange] = useState('24h');

  const fetchData = useCallback(async () => {
    try {
      setLoading(true);
      const [eventsData, statsData, typesData] = await Promise.all([
        getEvents({ limit: 100 }),
        getEventStats(timeRange),
        getEventTypes(),
      ]);
      setEvents(eventsData.data || []);
      setEventStats(statsData.data || {});
      setEventTypes(typesData.data || []);
    } catch (error) {
      console.error('Failed to fetch event data:', error);
    } finally {
      setLoading(false);
    }
  }, [timeRange]);

  useEffect(() => {
    fetchData();
    const interval = setInterval(fetchData, 30000); // Refresh every 30 seconds
    return () => clearInterval(interval);
  }, [fetchData]);

  const handleTypeFilter = (type) => {
    setSelectedTypes((prev) =>
      prev.includes(type) ? prev.filter((t) => t !== type) : [...prev, type]
    );
  };

  const filteredEvents = selectedTypes.length > 0
    ? events.filter((event) =>
        selectedTypes.some((type) => event.event_type.startsWith(type))
      )
    : events;

  const formatTimestamp = (timestamp) => {
    return new Date(timestamp).toLocaleString();
  };

  return (
    <div className="p-6 space-y-6">
      {/* Header */}
      <div className="flex items-center justify-between">
        <div>
          <h1 className="text-2xl font-bold text-gray-900">Event Dashboard</h1>
          <p className="text-sm text-gray-500">Monitor and analyze platform events</p>
        </div>
        <div className="flex items-center space-x-3">
          <select
            value={timeRange}
            onChange={(e) => setTimeRange(e.target.value)}
            className="px-3 py-2 text-sm border border-gray-300 rounded-lg focus:ring-2 focus:ring-blue-500 focus:border-blue-500"
          >
            <option value="1h">Last 1 hour</option>
            <option value="6h">Last 6 hours</option>
            <option value="24h">Last 24 hours</option>
            <option value="7d">Last 7 days</option>
          </select>
          <button
            onClick={fetchData}
            className="px-4 py-2 text-sm font-medium text-white bg-blue-600 rounded-lg hover:bg-blue-700"
          >
            Refresh
          </button>
        </div>
      </div>

      {/* Stats Cards */}
      {eventStats && (
        <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-4">
          <div className="bg-white rounded-lg shadow-md p-6">
            <p className="text-sm font-medium text-gray-600">Total Events</p>
            <p className="mt-1 text-3xl font-semibold text-gray-900">
              {eventStats.total_events?.toLocaleString() || 0}
            </p>
          </div>
          <div className="bg-white rounded-lg shadow-md p-6">
            <p className="text-sm font-medium text-gray-600">Events/Min</p>
            <p className="mt-1 text-3xl font-semibold text-gray-900">
              {eventStats.events_per_minute?.toFixed(1) || 0}
            </p>
          </div>
          <div className="bg-white rounded-lg shadow-md p-6">
            <p className="text-sm font-medium text-gray-600">Unique Types</p>
            <p className="mt-1 text-3xl font-semibold text-gray-900">
              {eventStats.unique_types || 0}
            </p>
          </div>
          <div className="bg-white rounded-lg shadow-md p-6">
            <p className="text-sm font-medium text-gray-600">Error Events</p>
            <p className="mt-1 text-3xl font-semibold text-red-600">
              {eventStats.error_events || 0}
            </p>
          </div>
        </div>
      )}

      {/* Event Type Charts */}
      {eventStats?.by_type && (
        <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">
          <div className="bg-white rounded-lg shadow-md p-6">
            <h3 className="text-lg font-semibold text-gray-900 mb-4">Events by Type</h3>
            <div className="space-y-3">
              {Object.entries(eventStats.by_type).map(([type, count]) => {
                const color = getEventColor(type);
                const percentage = (count / eventStats.total_events) * 100;
                return (
                  <div key={type}>
                    <div className="flex items-center justify-between text-sm mb-1">
                      <span className={`inline-flex items-center px-2 py-0.5 rounded-full text-xs font-medium border ${getColorClasses(color)}`}>
                        {type}
                      </span>
                      <span className="text-gray-600">{count.toLocaleString()}</span>
                    </div>
                    <div className="w-full bg-gray-200 rounded-full h-2">
                      <div
                        className={`h-2 rounded-full ${
                          color === 'blue' ? 'bg-blue-500' :
                          color === 'green' ? 'bg-green-500' :
                          color === 'yellow' ? 'bg-yellow-500' :
                          color === 'purple' ? 'bg-purple-500' : 'bg-gray-500'
                        }`}
                        style={{ width: `${percentage}%` }}
                      />
                    </div>
                  </div>
                );
              })}
            </div>
          </div>

          <div className="bg-white rounded-lg shadow-md p-6">
            <h3 className="text-lg font-semibold text-gray-900 mb-4">Events Over Time</h3>
            {eventStats.by_time && (
              <div className="flex items-end justify-between h-48 space-x-1">
                {eventStats.by_time.map((point, index) => (
                  <div key={index} className="flex-1 flex flex-col items-center">
                    <div
                      className="w-full bg-blue-500 rounded-t"
                      style={{
                        height: `${(point.count / Math.max(...eventStats.by_time.map(p => p.count))) * 100}%`,
                        minHeight: '2px',
                      }}
                    />
                    <span className="text-xs text-gray-500 mt-1 transform -rotate-45 origin-left">
                      {point.label}
                    </span>
                  </div>
                ))}
              </div>
            )}
          </div>
        </div>
      )}

      {/* Filters */}
      <div className="bg-white rounded-lg shadow-md p-4">
        <h3 className="text-sm font-medium text-gray-700 mb-3">Filter by Event Type</h3>
        <div className="flex flex-wrap gap-2">
          {['user', 'workflow', 'processing', 'model'].map((type) => {
            const color = getEventColor(type + '.');
            const isSelected = selectedTypes.includes(type);
            return (
              <button
                key={type}
                onClick={() => handleTypeFilter(type)}
                className={`px-3 py-1.5 text-sm font-medium rounded-full border transition-colors ${
                  isSelected
                    ? getColorClasses(color)
                    : 'bg-white text-gray-600 border-gray-300 hover:bg-gray-50'
                }`}
              >
                {type}.*
              </button>
            );
          })}
          {selectedTypes.length > 0 && (
            <button
              onClick={() => setSelectedTypes([])}
              className="px-3 py-1.5 text-sm font-medium text-gray-500 hover:text-gray-700"
            >
              Clear filters
            </button>
          )}
        </div>
      </div>

      {/* Live Event Stream */}
      <EventStream
        maxEvents={50}
        filters={{ eventTypes: selectedTypes }}
        onEventClick={setSelectedEvent}
      />

      {/* Recent Events Table */}
      <div className="bg-white rounded-lg shadow-md overflow-hidden">
        <div className="px-6 py-4 border-b border-gray-200">
          <h3 className="text-lg font-semibold text-gray-900">Recent Events</h3>
        </div>
        <div className="overflow-x-auto">
          <table className="min-w-full divide-y divide-gray-200">
            <thead className="bg-gray-50">
              <tr>
                <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">
                  Event Type
                </th>
                <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">
                  Timestamp
                </th>
                <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">
                  Source
                </th>
                <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">
                  Data Preview
                </th>
                <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">
                  Actions
                </th>
              </tr>
            </thead>
            <tbody className="bg-white divide-y divide-gray-200">
              {loading ? (
                <tr>
                  <td colSpan="5" className="px-6 py-4 text-center text-gray-500">
                    Loading events...
                  </td>
                </tr>
              ) : filteredEvents.length === 0 ? (
                <tr>
                  <td colSpan="5" className="px-6 py-4 text-center text-gray-500">
                    No events found
                  </td>
                </tr>
              ) : (
                filteredEvents.slice(0, 20).map((event) => {
                  const color = getEventColor(event.event_type);
                  return (
                    <tr key={event.id} className="hover:bg-gray-50">
                      <td className="px-6 py-4 whitespace-nowrap">
                        <span className={`inline-flex items-center px-2.5 py-0.5 rounded-full text-xs font-medium border ${getColorClasses(color)}`}>
                          {event.event_type}
                        </span>
                      </td>
                      <td className="px-6 py-4 whitespace-nowrap text-sm text-gray-500">
                        {formatTimestamp(event.timestamp)}
                      </td>
                      <td className="px-6 py-4 whitespace-nowrap text-sm text-gray-500">
                        {event.metadata?.source || '-'}
                      </td>
                      <td className="px-6 py-4 text-sm text-gray-500 max-w-xs truncate">
                        {event.data ? JSON.stringify(event.data).substring(0, 50) + '...' : '-'}
                      </td>
                      <td className="px-6 py-4 whitespace-nowrap text-sm">
                        <button
                          onClick={() => setSelectedEvent(event)}
                          className="text-blue-600 hover:text-blue-900"
                        >
                          View Details
                        </button>
                      </td>
                    </tr>
                  );
                })
              )}
            </tbody>
          </table>
        </div>
      </div>

      {/* Event Detail Modal */}
      {selectedEvent && (
        <div className="fixed inset-0 z-50 overflow-y-auto">
          <div className="flex items-center justify-center min-h-screen px-4 pt-4 pb-20 text-center sm:p-0">
            <div
              className="fixed inset-0 transition-opacity bg-gray-500 bg-opacity-75"
              onClick={() => setSelectedEvent(null)}
            />
            <div className="relative inline-block w-full max-w-2xl p-6 my-8 overflow-hidden text-left align-middle transition-all transform bg-white shadow-xl rounded-lg">
              <div className="flex items-center justify-between mb-4">
                <h3 className="text-lg font-semibold text-gray-900">Event Details</h3>
                <button
                  onClick={() => setSelectedEvent(null)}
                  className="text-gray-400 hover:text-gray-600"
                >
                  <svg className="w-6 h-6" fill="none" viewBox="0 0 24 24" stroke="currentColor">
                    <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M6 18L18 6M6 6l12 12" />
                  </svg>
                </button>
              </div>
              <div className="space-y-4">
                <div>
                  <label className="text-sm font-medium text-gray-500">Event Type</label>
                  <p className="mt-1">
                    <span className={`inline-flex items-center px-2.5 py-0.5 rounded-full text-sm font-medium border ${getColorClasses(getEventColor(selectedEvent.event_type))}`}>
                      {selectedEvent.event_type}
                    </span>
                  </p>
                </div>
                <div>
                  <label className="text-sm font-medium text-gray-500">Timestamp</label>
                  <p className="mt-1 text-sm text-gray-900">{formatTimestamp(selectedEvent.timestamp)}</p>
                </div>
                <div>
                  <label className="text-sm font-medium text-gray-500">Correlation ID</label>
                  <p className="mt-1 text-sm text-gray-900 font-mono">
                    {selectedEvent.metadata?.correlation_id || '-'}
                  </p>
                </div>
                <div>
                  <label className="text-sm font-medium text-gray-500">Source</label>
                  <p className="mt-1 text-sm text-gray-900">{selectedEvent.metadata?.source || '-'}</p>
                </div>
                <div>
                  <label className="text-sm font-medium text-gray-500">Data</label>
                  <pre className="mt-1 p-3 bg-gray-50 rounded-lg text-sm text-gray-900 overflow-x-auto">
                    {JSON.stringify(selectedEvent.data, null, 2)}
                  </pre>
                </div>
                <div>
                  <label className="text-sm font-medium text-gray-500">Metadata</label>
                  <pre className="mt-1 p-3 bg-gray-50 rounded-lg text-sm text-gray-900 overflow-x-auto">
                    {JSON.stringify(selectedEvent.metadata, null, 2)}
                  </pre>
                </div>
              </div>
              <div className="mt-6 flex justify-end">
                <button
                  onClick={() => setSelectedEvent(null)}
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

export default EventDashboard;
