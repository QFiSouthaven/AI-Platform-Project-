import React, { useState } from 'react';

const ProcessingHistory = ({
  history = [],
  onSelectItem,
  onDeleteItem,
  type = 'generation',
  title = 'History',
}) => {
  const [searchTerm, setSearchTerm] = useState('');
  const [selectedId, setSelectedId] = useState(null);

  const filteredHistory = history.filter((item) =>
    item.title?.toLowerCase().includes(searchTerm.toLowerCase()) ||
    item.description?.toLowerCase().includes(searchTerm.toLowerCase())
  );

  const handleSelect = (item) => {
    setSelectedId(item.id);
    onSelectItem && onSelectItem(item);
  };

  const handleDelete = (e, item) => {
    e.stopPropagation();
    onDeleteItem && onDeleteItem(item.id);
  };

  const formatDate = (dateString) => {
    const date = new Date(dateString);
    const now = new Date();
    const diff = now - date;

    if (diff < 60000) return 'Just now';
    if (diff < 3600000) return `${Math.floor(diff / 60000)}m ago`;
    if (diff < 86400000) return `${Math.floor(diff / 3600000)}h ago`;
    if (diff < 604800000) return `${Math.floor(diff / 86400000)}d ago`;

    return date.toLocaleDateString();
  };

  const getTypeIcon = (itemType) => {
    const icons = {
      generation: (
        <svg width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2">
          <path d="M14.7 6.3a1 1 0 0 0 0 1.4l1.6 1.6a1 1 0 0 0 1.4 0l3.77-3.77a6 6 0 0 1-7.94 7.94l-6.91 6.91a2.12 2.12 0 0 1-3-3l6.91-6.91a6 6 0 0 1 7.94-7.94l-3.76 3.76z"></path>
        </svg>
      ),
      debug: (
        <svg width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2">
          <path d="M12 22c5.523 0 10-4.477 10-10S17.523 2 12 2 2 6.477 2 12s4.477 10 10 10z"></path>
          <path d="M12 8v4"></path>
          <path d="M12 16h.01"></path>
        </svg>
      ),
      optimization: (
        <svg width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2">
          <path d="M13 2L3 14h9l-1 8 10-12h-9l1-8z"></path>
        </svg>
      ),
      evaluation: (
        <svg width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2">
          <path d="M22 11.08V12a10 10 0 1 1-5.93-9.14"></path>
          <polyline points="22 4 12 14.01 9 11.01"></polyline>
        </svg>
      ),
    };
    return icons[itemType] || icons.generation;
  };

  const getStatusBadge = (status) => {
    const statusConfig = {
      success: { color: '#10b981', label: 'Success' },
      error: { color: '#ef4444', label: 'Error' },
      pending: { color: '#f59e0b', label: 'Pending' },
    };
    const config = statusConfig[status] || statusConfig.pending;

    return (
      <span className="status-badge" style={{ backgroundColor: `${config.color}20`, color: config.color }}>
        {config.label}
      </span>
    );
  };

  return (
    <div className="processing-history">
      <div className="history-header">
        <h3 className="history-title">{title}</h3>
        <span className="history-count">{filteredHistory.length} items</span>
      </div>

      <div className="search-container">
        <svg className="search-icon" width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2">
          <circle cx="11" cy="11" r="8"></circle>
          <path d="M21 21l-4.35-4.35"></path>
        </svg>
        <input
          type="text"
          placeholder="Search history..."
          value={searchTerm}
          onChange={(e) => setSearchTerm(e.target.value)}
          className="search-input"
        />
      </div>

      <div className="history-list">
        {filteredHistory.length === 0 ? (
          <div className="empty-state">
            <svg width="48" height="48" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="1">
              <path d="M12 8v4l3 3m6-3a9 9 0 11-18 0 9 9 0 0118 0z"></path>
            </svg>
            <p>No history yet</p>
            <span>Your processing history will appear here</span>
          </div>
        ) : (
          filteredHistory.map((item) => (
            <div
              key={item.id}
              className={`history-item ${selectedId === item.id ? 'selected' : ''}`}
              onClick={() => handleSelect(item)}
            >
              <div className="item-icon">
                {getTypeIcon(item.type || type)}
              </div>
              <div className="item-content">
                <div className="item-header">
                  <span className="item-title">{item.title || 'Untitled'}</span>
                  {item.status && getStatusBadge(item.status)}
                </div>
                {item.description && (
                  <p className="item-description">{item.description}</p>
                )}
                <div className="item-meta">
                  {item.language && (
                    <span className="item-language">{item.language}</span>
                  )}
                  <span className="item-date">{formatDate(item.createdAt)}</span>
                </div>
              </div>
              {onDeleteItem && (
                <button
                  className="delete-button"
                  onClick={(e) => handleDelete(e, item)}
                  title="Delete"
                >
                  <svg width="14" height="14" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2">
                    <path d="M3 6h18"></path>
                    <path d="M19 6v14a2 2 0 01-2 2H7a2 2 0 01-2-2V6m3 0V4a2 2 0 012-2h4a2 2 0 012 2v2"></path>
                  </svg>
                </button>
              )}
            </div>
          ))
        )}
      </div>

      <style jsx>{`
        .processing-history {
          display: flex;
          flex-direction: column;
          height: 100%;
          background: #1a1a1a;
          border-radius: 8px;
          border: 1px solid #333;
        }

        .history-header {
          display: flex;
          justify-content: space-between;
          align-items: center;
          padding: 16px;
          border-bottom: 1px solid #333;
        }

        .history-title {
          font-size: 16px;
          font-weight: 600;
          color: #e0e0e0;
          margin: 0;
        }

        .history-count {
          font-size: 12px;
          color: #888;
          background: #2a2a2a;
          padding: 4px 8px;
          border-radius: 12px;
        }

        .search-container {
          position: relative;
          padding: 12px 16px;
          border-bottom: 1px solid #333;
        }

        .search-icon {
          position: absolute;
          left: 28px;
          top: 50%;
          transform: translateY(-50%);
          color: #666;
        }

        .search-input {
          width: 100%;
          padding: 8px 12px 8px 36px;
          background: #2a2a2a;
          border: 1px solid #333;
          border-radius: 6px;
          color: #e0e0e0;
          font-size: 14px;
          outline: none;
          transition: border-color 0.2s ease;
        }

        .search-input:focus {
          border-color: #6366f1;
        }

        .search-input::placeholder {
          color: #666;
        }

        .history-list {
          flex: 1;
          overflow-y: auto;
          padding: 8px;
        }

        .empty-state {
          display: flex;
          flex-direction: column;
          align-items: center;
          justify-content: center;
          padding: 32px 16px;
          color: #666;
          text-align: center;
        }

        .empty-state svg {
          margin-bottom: 12px;
          opacity: 0.5;
        }

        .empty-state p {
          margin: 0 0 4px;
          font-size: 14px;
          color: #888;
        }

        .empty-state span {
          font-size: 12px;
        }

        .history-item {
          display: flex;
          align-items: flex-start;
          gap: 12px;
          padding: 12px;
          margin-bottom: 4px;
          background: #222;
          border-radius: 6px;
          cursor: pointer;
          transition: all 0.2s ease;
        }

        .history-item:hover {
          background: #2a2a2a;
        }

        .history-item.selected {
          background: #2d2d5a;
          border: 1px solid #6366f1;
        }

        .item-icon {
          flex-shrink: 0;
          width: 32px;
          height: 32px;
          display: flex;
          align-items: center;
          justify-content: center;
          background: #333;
          border-radius: 6px;
          color: #6366f1;
        }

        .item-content {
          flex: 1;
          min-width: 0;
        }

        .item-header {
          display: flex;
          align-items: center;
          gap: 8px;
          margin-bottom: 4px;
        }

        .item-title {
          font-size: 14px;
          font-weight: 500;
          color: #e0e0e0;
          white-space: nowrap;
          overflow: hidden;
          text-overflow: ellipsis;
        }

        .status-badge {
          font-size: 10px;
          padding: 2px 6px;
          border-radius: 4px;
          flex-shrink: 0;
        }

        .item-description {
          margin: 0 0 8px;
          font-size: 12px;
          color: #888;
          display: -webkit-box;
          -webkit-line-clamp: 2;
          -webkit-box-orient: vertical;
          overflow: hidden;
        }

        .item-meta {
          display: flex;
          align-items: center;
          gap: 8px;
          font-size: 11px;
          color: #666;
        }

        .item-language {
          background: #333;
          padding: 2px 6px;
          border-radius: 4px;
        }

        .delete-button {
          flex-shrink: 0;
          padding: 4px;
          background: transparent;
          border: none;
          border-radius: 4px;
          color: #666;
          cursor: pointer;
          opacity: 0;
          transition: all 0.2s ease;
        }

        .history-item:hover .delete-button {
          opacity: 1;
        }

        .delete-button:hover {
          background: #333;
          color: #ef4444;
        }
      `}</style>
    </div>
  );
};

export default ProcessingHistory;
