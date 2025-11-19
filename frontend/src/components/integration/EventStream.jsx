import React, { useState, useEffect, useRef } from 'react';
import { createEventStream } from '../../services/integrationService';

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

const EventStream = ({ maxEvents = 50, filters = {}, onEventClick }) => {
  const [events, setEvents] = useState([]);
  const [isConnected, setIsConnected] = useState(false);
  const [isPaused, setIsPaused] = useState(false);
  const wsRef = useRef(null);
  const streamRef = useRef(null);

  useEffect(() => {
    const connectStream = () => {
      wsRef.current = createEventStream(
        (event) => {
          if (!isPaused) {
            // Apply filters
            if (filters.eventTypes && filters.eventTypes.length > 0) {
              const matchesFilter = filters.eventTypes.some(type =>
                event.event_type.startsWith(type)
              );
              if (!matchesFilter) return;
            }

            setEvents((prev) => {
              const newEvents = [event, ...prev];
              return newEvents.slice(0, maxEvents);
            });
          }
        },
        (error) => {
          console.error('Stream error:', error);
          setIsConnected(false);
        },
        () => {
          setIsConnected(false);
          // Attempt reconnection after 3 seconds
          setTimeout(connectStream, 3000);
        }
      );
      setIsConnected(true);
    };

    connectStream();

    return () => {
      if (wsRef.current) {
        wsRef.current.close();
      }
    };
  }, [maxEvents, filters, isPaused]);

  useEffect(() => {
    // Auto-scroll to top when new events arrive
    if (streamRef.current && !isPaused) {
      streamRef.current.scrollTop = 0;
    }
  }, [events, isPaused]);

  const handleClear = () => {
    setEvents([]);
  };

  const formatTimestamp = (timestamp) => {
    const date = new Date(timestamp);
    return date.toLocaleTimeString('en-US', {
      hour: '2-digit',
      minute: '2-digit',
      second: '2-digit',
      fractionalSecondDigits: 3,
    });
  };

  return (
    <div className="bg-white rounded-lg shadow-md overflow-hidden">
      <div className="px-4 py-3 border-b border-gray-200 flex items-center justify-between">
        <div className="flex items-center space-x-3">
          <h3 className="text-lg font-semibold text-gray-900">Live Event Stream</h3>
          <span
            className={`inline-flex items-center px-2.5 py-0.5 rounded-full text-xs font-medium ${
              isConnected ? 'bg-green-100 text-green-800' : 'bg-red-100 text-red-800'
            }`}
          >
            <span
              className={`w-2 h-2 mr-1.5 rounded-full ${
                isConnected ? 'bg-green-400 animate-pulse' : 'bg-red-400'
              }`}
            />
            {isConnected ? 'Connected' : 'Disconnected'}
          </span>
        </div>
        <div className="flex items-center space-x-2">
          <button
            onClick={() => setIsPaused(!isPaused)}
            className={`px-3 py-1 text-sm font-medium rounded-md ${
              isPaused
                ? 'bg-green-100 text-green-700 hover:bg-green-200'
                : 'bg-yellow-100 text-yellow-700 hover:bg-yellow-200'
            }`}
          >
            {isPaused ? 'Resume' : 'Pause'}
          </button>
          <button
            onClick={handleClear}
            className="px-3 py-1 text-sm font-medium text-gray-700 bg-gray-100 rounded-md hover:bg-gray-200"
          >
            Clear
          </button>
        </div>
      </div>

      <div
        ref={streamRef}
        className="divide-y divide-gray-100 max-h-96 overflow-y-auto"
      >
        {events.length === 0 ? (
          <div className="px-4 py-8 text-center text-gray-500">
            <svg
              className="mx-auto h-12 w-12 text-gray-400"
              fill="none"
              viewBox="0 0 24 24"
              stroke="currentColor"
            >
              <path
                strokeLinecap="round"
                strokeLinejoin="round"
                strokeWidth={2}
                d="M13 10V3L4 14h7v7l9-11h-7z"
              />
            </svg>
            <p className="mt-2">Waiting for events...</p>
          </div>
        ) : (
          events.map((event, index) => {
            const color = getEventColor(event.event_type);
            return (
              <div
                key={event.id || index}
                onClick={() => onEventClick && onEventClick(event)}
                className={`px-4 py-3 hover:bg-gray-50 cursor-pointer transition-colors ${
                  index === 0 ? 'animate-fadeIn' : ''
                }`}
              >
                <div className="flex items-center justify-between">
                  <div className="flex items-center space-x-3">
                    <span
                      className={`inline-flex items-center px-2.5 py-0.5 rounded-full text-xs font-medium border ${getColorClasses(
                        color
                      )}`}
                    >
                      {event.event_type}
                    </span>
                    <span className="text-sm text-gray-500">
                      {formatTimestamp(event.timestamp)}
                    </span>
                  </div>
                  {event.metadata?.source && (
                    <span className="text-xs text-gray-400">
                      from {event.metadata.source}
                    </span>
                  )}
                </div>
                {event.data && (
                  <div className="mt-1 text-sm text-gray-600 truncate">
                    {typeof event.data === 'object'
                      ? JSON.stringify(event.data).substring(0, 100) + '...'
                      : event.data}
                  </div>
                )}
              </div>
            );
          })
        )}
      </div>

      <div className="px-4 py-2 bg-gray-50 border-t border-gray-200 text-xs text-gray-500">
        Showing {events.length} of max {maxEvents} events
      </div>
    </div>
  );
};

export default EventStream;
