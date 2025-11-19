import React, { useState, useRef, useEffect } from 'react';
import { useParams } from 'react-router-dom';
import TaskNode, { TASK_TYPES } from '../../components/workflows/TaskNode';
import workflowService from '../../services/workflowService';

/**
 * WorkflowBuilder - Visual drag-and-drop workflow builder
 */
const WorkflowBuilder = () => {
  const { workflowId } = useParams();
  const canvasRef = useRef(null);

  const [workflow, setWorkflow] = useState({
    name: 'Untitled Workflow',
    description: '',
    tasks: [],
    connections: [],
  });
  const [tasks, setTasks] = useState([]);
  const [connections, setConnections] = useState([]);
  const [selectedTask, setSelectedTask] = useState(null);
  const [draggedTask, setDraggedTask] = useState(null);
  const [dragOffset, setDragOffset] = useState({ x: 0, y: 0 });
  const [zoom, setZoom] = useState(1);
  const [pan, setPan] = useState({ x: 0, y: 0 });
  const [isPanning, setIsPanning] = useState(false);
  const [panStart, setPanStart] = useState({ x: 0, y: 0 });
  const [isConnecting, setIsConnecting] = useState(false);
  const [connectionStart, setConnectionStart] = useState(null);
  const [showConfigPanel, setShowConfigPanel] = useState(false);
  const [validationErrors, setValidationErrors] = useState([]);
  const [isSaving, setIsSaving] = useState(false);
  const [showTaskPalette, setShowTaskPalette] = useState(true);

  useEffect(() => {
    if (workflowId) {
      loadWorkflow();
    }
  }, [workflowId]);

  const loadWorkflow = async () => {
    try {
      const response = await workflowService.getWorkflow(workflowId);
      const data = response.data || response;
      setWorkflow(data);
      setTasks(data.tasks || []);
      setConnections(data.connections || []);
    } catch (err) {
      alert(`Failed to load workflow: ${err.message}`);
    }
  };

  const handleSave = async () => {
    try {
      setIsSaving(true);
      const workflowData = {
        ...workflow,
        tasks,
        connections,
      };

      if (workflowId) {
        await workflowService.updateWorkflow(workflowId, workflowData);
      } else {
        const response = await workflowService.createWorkflow(workflowData);
        const newId = response.data?.id || response.id;
        window.history.replaceState(null, '', `/workflows/${newId}/edit`);
      }
      alert('Workflow saved successfully!');
    } catch (err) {
      alert(`Failed to save workflow: ${err.message}`);
    } finally {
      setIsSaving(false);
    }
  };

  const handleValidate = async () => {
    try {
      const response = await workflowService.validateWorkflow({
        ...workflow,
        tasks,
        connections,
      });
      setValidationErrors(response.errors || []);
      if (response.valid) {
        alert('Workflow is valid!');
      }
    } catch (err) {
      alert(`Validation failed: ${err.message}`);
    }
  };

  const handleAddTask = (taskType) => {
    const newTask = {
      id: `task_${Date.now()}`,
      name: `New ${TASK_TYPES[taskType].label}`,
      type: taskType,
      status: 'draft',
      config: {},
      position: {
        x: 100 + tasks.length * 50,
        y: 100 + tasks.length * 50,
      },
    };
    setTasks([...tasks, newTask]);
    setSelectedTask(newTask);
    setShowConfigPanel(true);
  };

  const handleTaskSelect = (task) => {
    setSelectedTask(task);
    setShowConfigPanel(true);
  };

  const handleTaskDragStart = (task, e) => {
    const rect = e.currentTarget.getBoundingClientRect();
    setDragOffset({
      x: e.clientX - rect.left,
      y: e.clientY - rect.top,
    });
    setDraggedTask(task);
  };

  const handleTaskDragEnd = () => {
    setDraggedTask(null);
  };

  const handleMouseMove = (e) => {
    if (draggedTask) {
      const canvas = canvasRef.current;
      const rect = canvas.getBoundingClientRect();
      const x = (e.clientX - rect.left - pan.x) / zoom - dragOffset.x;
      const y = (e.clientY - rect.top - pan.y) / zoom - dragOffset.y;

      setTasks(tasks.map(t =>
        t.id === draggedTask.id
          ? { ...t, position: { x: Math.max(0, x), y: Math.max(0, y) } }
          : t
      ));
    }

    if (isPanning) {
      const dx = e.clientX - panStart.x;
      const dy = e.clientY - panStart.y;
      setPan({
        x: pan.x + dx,
        y: pan.y + dy,
      });
      setPanStart({ x: e.clientX, y: e.clientY });
    }
  };

  const handleMouseUp = () => {
    setDraggedTask(null);
    setIsPanning(false);
    setIsConnecting(false);
    setConnectionStart(null);
  };

  const handleCanvasMouseDown = (e) => {
    if (e.target === canvasRef.current) {
      setSelectedTask(null);
      setShowConfigPanel(false);
      setIsPanning(true);
      setPanStart({ x: e.clientX, y: e.clientY });
    }
  };

  const handleConnect = (task, type, e) => {
    if (!isConnecting) {
      setIsConnecting(true);
      setConnectionStart({ task, type });
    } else if (connectionStart && connectionStart.task.id !== task.id) {
      // Create connection
      const newConnection = {
        id: `conn_${Date.now()}`,
        from: connectionStart.type === 'output' ? connectionStart.task.id : task.id,
        to: connectionStart.type === 'output' ? task.id : connectionStart.task.id,
      };
      setConnections([...connections, newConnection]);
      setIsConnecting(false);
      setConnectionStart(null);
    }
  };

  const handleTaskDelete = (task) => {
    setTasks(tasks.filter(t => t.id !== task.id));
    setConnections(connections.filter(c => c.from !== task.id && c.to !== task.id));
    if (selectedTask?.id === task.id) {
      setSelectedTask(null);
      setShowConfigPanel(false);
    }
  };

  const handleTaskConfigure = (task) => {
    setSelectedTask(task);
    setShowConfigPanel(true);
  };

  const handleZoomIn = () => setZoom(Math.min(zoom + 0.1, 2));
  const handleZoomOut = () => setZoom(Math.max(zoom - 0.1, 0.5));
  const handleZoomReset = () => {
    setZoom(1);
    setPan({ x: 0, y: 0 });
  };

  const updateTaskConfig = (field, value) => {
    if (!selectedTask) return;
    const updatedTask = { ...selectedTask, [field]: value };
    setTasks(tasks.map(t => t.id === selectedTask.id ? updatedTask : t));
    setSelectedTask(updatedTask);
  };

  // Styles
  const containerStyle = {
    display: 'flex',
    height: '100vh',
    backgroundColor: '#f3f4f6',
  };

  const sidebarStyle = {
    width: '280px',
    backgroundColor: '#ffffff',
    borderRight: '1px solid #e5e7eb',
    display: 'flex',
    flexDirection: 'column',
    overflow: 'hidden',
  };

  const sidebarHeaderStyle = {
    padding: '16px',
    borderBottom: '1px solid #e5e7eb',
  };

  const workflowNameInputStyle = {
    width: '100%',
    padding: '8px 12px',
    border: '1px solid #e5e7eb',
    borderRadius: '6px',
    fontSize: '14px',
    fontWeight: '600',
  };

  const paletteSectionStyle = {
    padding: '16px',
    borderBottom: '1px solid #e5e7eb',
  };

  const sectionTitleStyle = {
    fontSize: '12px',
    fontWeight: '600',
    color: '#6b7280',
    textTransform: 'uppercase',
    marginBottom: '12px',
  };

  const paletteGridStyle = {
    display: 'grid',
    gridTemplateColumns: 'repeat(2, 1fr)',
    gap: '8px',
  };

  const paletteItemStyle = (color) => ({
    padding: '12px 8px',
    backgroundColor: `${color}10`,
    border: `1px solid ${color}30`,
    borderRadius: '8px',
    cursor: 'pointer',
    textAlign: 'center',
    transition: 'all 0.2s',
  });

  const paletteIconStyle = (color) => ({
    width: '32px',
    height: '32px',
    borderRadius: '8px',
    backgroundColor: color,
    color: '#ffffff',
    display: 'flex',
    alignItems: 'center',
    justifyContent: 'center',
    margin: '0 auto 8px',
  });

  const paletteLabelStyle = {
    fontSize: '11px',
    fontWeight: '500',
    color: '#374151',
  };

  const mainAreaStyle = {
    flex: 1,
    display: 'flex',
    flexDirection: 'column',
    overflow: 'hidden',
  };

  const toolbarStyle = {
    display: 'flex',
    justifyContent: 'space-between',
    alignItems: 'center',
    padding: '12px 16px',
    backgroundColor: '#ffffff',
    borderBottom: '1px solid #e5e7eb',
  };

  const toolbarGroupStyle = {
    display: 'flex',
    gap: '8px',
  };

  const toolbarButtonStyle = {
    padding: '8px 12px',
    border: '1px solid #e5e7eb',
    borderRadius: '6px',
    backgroundColor: '#ffffff',
    fontSize: '13px',
    cursor: 'pointer',
    display: 'flex',
    alignItems: 'center',
    gap: '6px',
  };

  const primaryButtonStyle = {
    ...toolbarButtonStyle,
    backgroundColor: '#3b82f6',
    borderColor: '#3b82f6',
    color: '#ffffff',
  };

  const canvasContainerStyle = {
    flex: 1,
    position: 'relative',
    overflow: 'hidden',
    backgroundColor: '#f9fafb',
    backgroundImage: 'radial-gradient(#d1d5db 1px, transparent 1px)',
    backgroundSize: `${20 * zoom}px ${20 * zoom}px`,
    backgroundPosition: `${pan.x}px ${pan.y}px`,
  };

  const canvasStyle = {
    position: 'absolute',
    width: '100%',
    height: '100%',
    transform: `translate(${pan.x}px, ${pan.y}px) scale(${zoom})`,
    transformOrigin: '0 0',
    cursor: isPanning ? 'grabbing' : 'default',
  };

  const zoomControlsStyle = {
    position: 'absolute',
    bottom: '16px',
    right: '16px',
    display: 'flex',
    gap: '4px',
    backgroundColor: '#ffffff',
    borderRadius: '8px',
    padding: '4px',
    boxShadow: '0 2px 8px rgba(0, 0, 0, 0.1)',
  };

  const zoomButtonStyle = {
    width: '32px',
    height: '32px',
    border: 'none',
    borderRadius: '4px',
    backgroundColor: 'transparent',
    cursor: 'pointer',
    display: 'flex',
    alignItems: 'center',
    justifyContent: 'center',
  };

  const configPanelStyle = {
    width: showConfigPanel ? '320px' : '0',
    backgroundColor: '#ffffff',
    borderLeft: '1px solid #e5e7eb',
    overflow: 'hidden',
    transition: 'width 0.2s',
  };

  const configPanelContentStyle = {
    width: '320px',
    padding: '16px',
  };

  const configHeaderStyle = {
    display: 'flex',
    justifyContent: 'space-between',
    alignItems: 'center',
    marginBottom: '16px',
  };

  const configTitleStyle = {
    fontSize: '16px',
    fontWeight: '600',
    color: '#111827',
  };

  const closeButtonStyle = {
    padding: '4px',
    border: 'none',
    backgroundColor: 'transparent',
    cursor: 'pointer',
    color: '#6b7280',
  };

  const formGroupStyle = {
    marginBottom: '16px',
  };

  const labelStyle = {
    display: 'block',
    fontSize: '13px',
    fontWeight: '500',
    color: '#374151',
    marginBottom: '6px',
  };

  const inputStyle = {
    width: '100%',
    padding: '8px 12px',
    border: '1px solid #e5e7eb',
    borderRadius: '6px',
    fontSize: '14px',
  };

  const textareaStyle = {
    ...inputStyle,
    minHeight: '80px',
    resize: 'vertical',
  };

  // Render connection lines
  const renderConnections = () => {
    return connections.map(conn => {
      const fromTask = tasks.find(t => t.id === conn.from);
      const toTask = tasks.find(t => t.id === conn.to);
      if (!fromTask || !toTask) return null;

      const x1 = fromTask.position.x + 90;
      const y1 = fromTask.position.y + 80;
      const x2 = toTask.position.x + 90;
      const y2 = toTask.position.y;

      const midY = (y1 + y2) / 2;

      return (
        <svg
          key={conn.id}
          style={{ position: 'absolute', top: 0, left: 0, width: '100%', height: '100%', pointerEvents: 'none' }}
        >
          <path
            d={`M ${x1} ${y1} C ${x1} ${midY}, ${x2} ${midY}, ${x2} ${y2}`}
            stroke="#3b82f6"
            strokeWidth="2"
            fill="none"
          />
        </svg>
      );
    });
  };

  return (
    <div style={containerStyle}>
      {/* Left Sidebar - Task Palette */}
      {showTaskPalette && (
        <div style={sidebarStyle}>
          <div style={sidebarHeaderStyle}>
            <input
              type="text"
              style={workflowNameInputStyle}
              value={workflow.name}
              onChange={(e) => setWorkflow({ ...workflow, name: e.target.value })}
              placeholder="Workflow name"
            />
          </div>

          <div style={paletteSectionStyle}>
            <div style={sectionTitleStyle}>Task Types</div>
            <div style={paletteGridStyle}>
              {Object.entries(TASK_TYPES).map(([key, type]) => (
                <div
                  key={key}
                  style={paletteItemStyle(type.color)}
                  onClick={() => handleAddTask(key)}
                  onMouseEnter={(e) => {
                    e.currentTarget.style.transform = 'translateY(-2px)';
                    e.currentTarget.style.boxShadow = '0 4px 6px rgba(0, 0, 0, 0.1)';
                  }}
                  onMouseLeave={(e) => {
                    e.currentTarget.style.transform = 'none';
                    e.currentTarget.style.boxShadow = 'none';
                  }}
                >
                  <div style={paletteIconStyle(type.color)}>{type.icon}</div>
                  <div style={paletteLabelStyle}>{type.label}</div>
                </div>
              ))}
            </div>
          </div>

          {validationErrors.length > 0 && (
            <div style={{ padding: '16px' }}>
              <div style={{ ...sectionTitleStyle, color: '#dc2626' }}>Validation Errors</div>
              {validationErrors.map((error, index) => (
                <div key={index} style={{ fontSize: '12px', color: '#dc2626', marginBottom: '4px' }}>
                  {error}
                </div>
              ))}
            </div>
          )}
        </div>
      )}

      {/* Main Canvas Area */}
      <div style={mainAreaStyle}>
        {/* Toolbar */}
        <div style={toolbarStyle}>
          <div style={toolbarGroupStyle}>
            <button
              style={toolbarButtonStyle}
              onClick={() => setShowTaskPalette(!showTaskPalette)}
            >
              <svg width="14" height="14" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2">
                <rect x="3" y="3" width="18" height="18" rx="2" ry="2" />
                <line x1="9" y1="3" x2="9" y2="21" />
              </svg>
              {showTaskPalette ? 'Hide' : 'Show'} Panel
            </button>
            <button style={toolbarButtonStyle} onClick={handleValidate}>
              <svg width="14" height="14" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2">
                <polyline points="20 6 9 17 4 12" />
              </svg>
              Validate
            </button>
          </div>

          <div style={toolbarGroupStyle}>
            <button style={toolbarButtonStyle} onClick={() => window.location.href = '/workflows'}>
              Cancel
            </button>
            <button
              style={primaryButtonStyle}
              onClick={handleSave}
              disabled={isSaving}
            >
              {isSaving ? 'Saving...' : 'Save Workflow'}
            </button>
          </div>
        </div>

        {/* Canvas */}
        <div style={canvasContainerStyle}>
          <div
            ref={canvasRef}
            style={canvasStyle}
            onMouseMove={handleMouseMove}
            onMouseUp={handleMouseUp}
            onMouseDown={handleCanvasMouseDown}
            onMouseLeave={handleMouseUp}
          >
            {/* Connection Lines */}
            {renderConnections()}

            {/* Task Nodes */}
            {tasks.map(task => (
              <TaskNode
                key={task.id}
                task={task}
                position={task.position}
                isSelected={selectedTask?.id === task.id}
                isDragging={draggedTask?.id === task.id}
                onSelect={handleTaskSelect}
                onDragStart={handleTaskDragStart}
                onDragEnd={handleTaskDragEnd}
                onConfigure={handleTaskConfigure}
                onDelete={handleTaskDelete}
                onConnect={handleConnect}
              />
            ))}
          </div>

          {/* Zoom Controls */}
          <div style={zoomControlsStyle}>
            <button style={zoomButtonStyle} onClick={handleZoomOut} title="Zoom Out">
              <svg width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2">
                <line x1="5" y1="12" x2="19" y2="12" />
              </svg>
            </button>
            <button style={zoomButtonStyle} onClick={handleZoomReset} title="Reset Zoom">
              {Math.round(zoom * 100)}%
            </button>
            <button style={zoomButtonStyle} onClick={handleZoomIn} title="Zoom In">
              <svg width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2">
                <line x1="12" y1="5" x2="12" y2="19" />
                <line x1="5" y1="12" x2="19" y2="12" />
              </svg>
            </button>
          </div>
        </div>
      </div>

      {/* Right Sidebar - Configuration Panel */}
      <div style={configPanelStyle}>
        <div style={configPanelContentStyle}>
          <div style={configHeaderStyle}>
            <span style={configTitleStyle}>
              {selectedTask ? 'Task Configuration' : 'Workflow Settings'}
            </span>
            <button style={closeButtonStyle} onClick={() => setShowConfigPanel(false)}>
              <svg width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2">
                <line x1="18" y1="6" x2="6" y2="18" />
                <line x1="6" y1="6" x2="18" y2="18" />
              </svg>
            </button>
          </div>

          {selectedTask ? (
            <>
              <div style={formGroupStyle}>
                <label style={labelStyle}>Task Name</label>
                <input
                  type="text"
                  style={inputStyle}
                  value={selectedTask.name}
                  onChange={(e) => updateTaskConfig('name', e.target.value)}
                />
              </div>

              <div style={formGroupStyle}>
                <label style={labelStyle}>Task Type</label>
                <select
                  style={inputStyle}
                  value={selectedTask.type}
                  onChange={(e) => updateTaskConfig('type', e.target.value)}
                >
                  {Object.entries(TASK_TYPES).map(([key, type]) => (
                    <option key={key} value={key}>{type.label}</option>
                  ))}
                </select>
              </div>

              <div style={formGroupStyle}>
                <label style={labelStyle}>Description</label>
                <textarea
                  style={textareaStyle}
                  value={selectedTask.description || ''}
                  onChange={(e) => updateTaskConfig('description', e.target.value)}
                  placeholder="Task description..."
                />
              </div>

              <div style={formGroupStyle}>
                <label style={labelStyle}>Retry Count</label>
                <input
                  type="number"
                  style={inputStyle}
                  value={selectedTask.config?.retryCount || 0}
                  onChange={(e) => updateTaskConfig('config', {
                    ...selectedTask.config,
                    retryCount: parseInt(e.target.value) || 0
                  })}
                  min="0"
                  max="10"
                />
              </div>

              <div style={formGroupStyle}>
                <label style={labelStyle}>Timeout (seconds)</label>
                <input
                  type="number"
                  style={inputStyle}
                  value={selectedTask.config?.timeout || 300}
                  onChange={(e) => updateTaskConfig('config', {
                    ...selectedTask.config,
                    timeout: parseInt(e.target.value) || 300
                  })}
                  min="0"
                />
              </div>
            </>
          ) : (
            <>
              <div style={formGroupStyle}>
                <label style={labelStyle}>Workflow Name</label>
                <input
                  type="text"
                  style={inputStyle}
                  value={workflow.name}
                  onChange={(e) => setWorkflow({ ...workflow, name: e.target.value })}
                />
              </div>

              <div style={formGroupStyle}>
                <label style={labelStyle}>Description</label>
                <textarea
                  style={textareaStyle}
                  value={workflow.description}
                  onChange={(e) => setWorkflow({ ...workflow, description: e.target.value })}
                  placeholder="Workflow description..."
                />
              </div>
            </>
          )}
        </div>
      </div>
    </div>
  );
};

export default WorkflowBuilder;
