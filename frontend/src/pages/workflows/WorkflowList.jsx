import React, { useState, useEffect } from 'react';
import WorkflowCard from '../../components/workflows/WorkflowCard';
import workflowService from '../../services/workflowService';

/**
 * WorkflowList - Main page for listing and managing workflows
 */
const WorkflowList = () => {
  const [workflows, setWorkflows] = useState([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState(null);
  const [viewMode, setViewMode] = useState('grid'); // 'grid' or 'list'
  const [searchQuery, setSearchQuery] = useState('');
  const [statusFilter, setStatusFilter] = useState('all');
  const [dateFilter, setDateFilter] = useState('all');
  const [showDeleteModal, setShowDeleteModal] = useState(false);
  const [selectedWorkflow, setSelectedWorkflow] = useState(null);

  useEffect(() => {
    fetchWorkflows();
  }, [statusFilter, dateFilter, searchQuery]);

  const fetchWorkflows = async () => {
    try {
      setLoading(true);
      const params = {
        search: searchQuery || undefined,
        status: statusFilter !== 'all' ? statusFilter : undefined,
      };

      // Add date filter
      if (dateFilter !== 'all') {
        const now = new Date();
        let startDate;
        switch (dateFilter) {
          case 'today':
            startDate = new Date(now.setHours(0, 0, 0, 0));
            break;
          case 'week':
            startDate = new Date(now.setDate(now.getDate() - 7));
            break;
          case 'month':
            startDate = new Date(now.setMonth(now.getMonth() - 1));
            break;
          default:
            startDate = null;
        }
        if (startDate) {
          params.created_after = startDate.toISOString();
        }
      }

      const response = await workflowService.getWorkflows(params);
      setWorkflows(response.data || response);
      setError(null);
    } catch (err) {
      setError(err.message);
      setWorkflows([]);
    } finally {
      setLoading(false);
    }
  };

  const handleRun = async (workflow) => {
    try {
      await workflowService.executeWorkflow(workflow.id);
      fetchWorkflows();
    } catch (err) {
      alert(`Failed to run workflow: ${err.message}`);
    }
  };

  const handleEdit = (workflow) => {
    window.location.href = `/workflows/${workflow.id}/edit`;
  };

  const handleClone = async (workflow) => {
    const newName = prompt('Enter name for cloned workflow:', `${workflow.name} (Copy)`);
    if (newName) {
      try {
        await workflowService.cloneWorkflow(workflow.id, newName);
        fetchWorkflows();
      } catch (err) {
        alert(`Failed to clone workflow: ${err.message}`);
      }
    }
  };

  const handleDelete = (workflow) => {
    setSelectedWorkflow(workflow);
    setShowDeleteModal(true);
  };

  const confirmDelete = async () => {
    if (selectedWorkflow) {
      try {
        await workflowService.deleteWorkflow(selectedWorkflow.id);
        setShowDeleteModal(false);
        setSelectedWorkflow(null);
        fetchWorkflows();
      } catch (err) {
        alert(`Failed to delete workflow: ${err.message}`);
      }
    }
  };

  const handleView = (workflow) => {
    window.location.href = `/workflows/${workflow.id}`;
  };

  const containerStyle = {
    padding: '24px',
    maxWidth: '1400px',
    margin: '0 auto',
  };

  const headerStyle = {
    display: 'flex',
    justifyContent: 'space-between',
    alignItems: 'center',
    marginBottom: '24px',
  };

  const titleStyle = {
    fontSize: '24px',
    fontWeight: '700',
    color: '#111827',
    margin: 0,
  };

  const createButtonStyle = {
    display: 'flex',
    alignItems: 'center',
    gap: '8px',
    padding: '10px 20px',
    backgroundColor: '#3b82f6',
    color: '#ffffff',
    border: 'none',
    borderRadius: '8px',
    fontSize: '14px',
    fontWeight: '600',
    cursor: 'pointer',
    transition: 'background-color 0.2s',
  };

  const filtersStyle = {
    display: 'flex',
    gap: '16px',
    marginBottom: '24px',
    flexWrap: 'wrap',
    alignItems: 'center',
  };

  const searchInputStyle = {
    flex: '1',
    minWidth: '250px',
    padding: '10px 16px',
    paddingLeft: '40px',
    border: '1px solid #e5e7eb',
    borderRadius: '8px',
    fontSize: '14px',
    backgroundColor: '#ffffff',
  };

  const searchContainerStyle = {
    position: 'relative',
    flex: '1',
    minWidth: '250px',
  };

  const searchIconStyle = {
    position: 'absolute',
    left: '12px',
    top: '50%',
    transform: 'translateY(-50%)',
    color: '#9ca3af',
  };

  const selectStyle = {
    padding: '10px 16px',
    border: '1px solid #e5e7eb',
    borderRadius: '8px',
    fontSize: '14px',
    backgroundColor: '#ffffff',
    cursor: 'pointer',
    minWidth: '140px',
  };

  const viewToggleStyle = {
    display: 'flex',
    border: '1px solid #e5e7eb',
    borderRadius: '8px',
    overflow: 'hidden',
  };

  const viewButtonStyle = (isActive) => ({
    padding: '10px 16px',
    border: 'none',
    backgroundColor: isActive ? '#3b82f6' : '#ffffff',
    color: isActive ? '#ffffff' : '#6b7280',
    cursor: 'pointer',
    transition: 'all 0.2s',
  });

  const gridStyle = {
    display: 'grid',
    gridTemplateColumns: 'repeat(auto-fill, minmax(320px, 1fr))',
    gap: '20px',
  };

  const listStyle = {
    display: 'flex',
    flexDirection: 'column',
    gap: '12px',
  };

  const emptyStateStyle = {
    textAlign: 'center',
    padding: '60px 20px',
    color: '#6b7280',
  };

  const emptyIconStyle = {
    width: '64px',
    height: '64px',
    margin: '0 auto 16px',
    color: '#d1d5db',
  };

  const modalOverlayStyle = {
    position: 'fixed',
    top: 0,
    left: 0,
    right: 0,
    bottom: 0,
    backgroundColor: 'rgba(0, 0, 0, 0.5)',
    display: 'flex',
    alignItems: 'center',
    justifyContent: 'center',
    zIndex: 1000,
  };

  const modalStyle = {
    backgroundColor: '#ffffff',
    borderRadius: '12px',
    padding: '24px',
    maxWidth: '400px',
    width: '90%',
  };

  const modalTitleStyle = {
    fontSize: '18px',
    fontWeight: '600',
    color: '#111827',
    marginBottom: '12px',
  };

  const modalTextStyle = {
    fontSize: '14px',
    color: '#6b7280',
    marginBottom: '24px',
  };

  const modalActionsStyle = {
    display: 'flex',
    gap: '12px',
    justifyContent: 'flex-end',
  };

  const cancelButtonStyle = {
    padding: '8px 16px',
    border: '1px solid #e5e7eb',
    borderRadius: '6px',
    backgroundColor: '#ffffff',
    fontSize: '14px',
    cursor: 'pointer',
  };

  const deleteButtonStyle = {
    padding: '8px 16px',
    border: 'none',
    borderRadius: '6px',
    backgroundColor: '#ef4444',
    color: '#ffffff',
    fontSize: '14px',
    cursor: 'pointer',
  };

  const loadingStyle = {
    display: 'flex',
    justifyContent: 'center',
    alignItems: 'center',
    padding: '60px',
    color: '#6b7280',
  };

  const errorStyle = {
    padding: '16px',
    backgroundColor: '#fef2f2',
    border: '1px solid #fecaca',
    borderRadius: '8px',
    color: '#dc2626',
    marginBottom: '24px',
  };

  return (
    <div style={containerStyle}>
      {/* Header */}
      <div style={headerStyle}>
        <h1 style={titleStyle}>Workflows</h1>
        <button
          style={createButtonStyle}
          onClick={() => window.location.href = '/workflows/new'}
          onMouseEnter={(e) => e.target.style.backgroundColor = '#2563eb'}
          onMouseLeave={(e) => e.target.style.backgroundColor = '#3b82f6'}
        >
          <svg width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2">
            <line x1="12" y1="5" x2="12" y2="19" />
            <line x1="5" y1="12" x2="19" y2="12" />
          </svg>
          Create Workflow
        </button>
      </div>

      {/* Filters */}
      <div style={filtersStyle}>
        <div style={searchContainerStyle}>
          <svg style={searchIconStyle} width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2">
            <circle cx="11" cy="11" r="8" />
            <line x1="21" y1="21" x2="16.65" y2="16.65" />
          </svg>
          <input
            type="text"
            placeholder="Search workflows..."
            style={searchInputStyle}
            value={searchQuery}
            onChange={(e) => setSearchQuery(e.target.value)}
          />
        </div>

        <select
          style={selectStyle}
          value={statusFilter}
          onChange={(e) => setStatusFilter(e.target.value)}
        >
          <option value="all">All Status</option>
          <option value="active">Active</option>
          <option value="inactive">Inactive</option>
          <option value="running">Running</option>
          <option value="failed">Failed</option>
        </select>

        <select
          style={selectStyle}
          value={dateFilter}
          onChange={(e) => setDateFilter(e.target.value)}
        >
          <option value="all">All Time</option>
          <option value="today">Today</option>
          <option value="week">This Week</option>
          <option value="month">This Month</option>
        </select>

        <div style={viewToggleStyle}>
          <button
            style={viewButtonStyle(viewMode === 'grid')}
            onClick={() => setViewMode('grid')}
            title="Grid View"
          >
            <svg width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2">
              <rect x="3" y="3" width="7" height="7" />
              <rect x="14" y="3" width="7" height="7" />
              <rect x="14" y="14" width="7" height="7" />
              <rect x="3" y="14" width="7" height="7" />
            </svg>
          </button>
          <button
            style={viewButtonStyle(viewMode === 'list')}
            onClick={() => setViewMode('list')}
            title="List View"
          >
            <svg width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2">
              <line x1="8" y1="6" x2="21" y2="6" />
              <line x1="8" y1="12" x2="21" y2="12" />
              <line x1="8" y1="18" x2="21" y2="18" />
              <line x1="3" y1="6" x2="3.01" y2="6" />
              <line x1="3" y1="12" x2="3.01" y2="12" />
              <line x1="3" y1="18" x2="3.01" y2="18" />
            </svg>
          </button>
        </div>
      </div>

      {/* Error State */}
      {error && (
        <div style={errorStyle}>
          <strong>Error:</strong> {error}
        </div>
      )}

      {/* Loading State */}
      {loading && (
        <div style={loadingStyle}>
          <svg width="24" height="24" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" style={{ animation: 'spin 1s linear infinite' }}>
            <path d="M21 12a9 9 0 1 1-6.219-8.56" />
          </svg>
          <span style={{ marginLeft: '8px' }}>Loading workflows...</span>
        </div>
      )}

      {/* Workflow Grid/List */}
      {!loading && workflows.length > 0 && (
        <div style={viewMode === 'grid' ? gridStyle : listStyle}>
          {workflows.map((workflow) => (
            <WorkflowCard
              key={workflow.id}
              workflow={workflow}
              onRun={handleRun}
              onEdit={handleEdit}
              onClone={handleClone}
              onDelete={handleDelete}
              onView={handleView}
              isCompact={viewMode === 'list'}
            />
          ))}
        </div>
      )}

      {/* Empty State */}
      {!loading && workflows.length === 0 && !error && (
        <div style={emptyStateStyle}>
          <svg style={emptyIconStyle} viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="1.5">
            <path d="M9 17H7A5 5 0 0 1 7 7h2" />
            <path d="M15 7h2a5 5 0 1 1 0 10h-2" />
            <line x1="8" y1="12" x2="16" y2="12" />
          </svg>
          <h3 style={{ fontSize: '18px', fontWeight: '600', color: '#374151', marginBottom: '8px' }}>
            No workflows found
          </h3>
          <p style={{ marginBottom: '16px' }}>
            {searchQuery || statusFilter !== 'all' || dateFilter !== 'all'
              ? 'Try adjusting your filters or search query'
              : 'Get started by creating your first workflow'}
          </p>
          {!searchQuery && statusFilter === 'all' && dateFilter === 'all' && (
            <button
              style={createButtonStyle}
              onClick={() => window.location.href = '/workflows/new'}
            >
              Create Workflow
            </button>
          )}
        </div>
      )}

      {/* Delete Confirmation Modal */}
      {showDeleteModal && (
        <div style={modalOverlayStyle} onClick={() => setShowDeleteModal(false)}>
          <div style={modalStyle} onClick={(e) => e.stopPropagation()}>
            <h3 style={modalTitleStyle}>Delete Workflow</h3>
            <p style={modalTextStyle}>
              Are you sure you want to delete "{selectedWorkflow?.name}"? This action cannot be undone.
            </p>
            <div style={modalActionsStyle}>
              <button
                style={cancelButtonStyle}
                onClick={() => setShowDeleteModal(false)}
              >
                Cancel
              </button>
              <button
                style={deleteButtonStyle}
                onClick={confirmDelete}
              >
                Delete
              </button>
            </div>
          </div>
        </div>
      )}

      {/* CSS Animation */}
      <style>
        {`
          @keyframes spin {
            from { transform: rotate(0deg); }
            to { transform: rotate(360deg); }
          }
        `}
      </style>
    </div>
  );
};

export default WorkflowList;
