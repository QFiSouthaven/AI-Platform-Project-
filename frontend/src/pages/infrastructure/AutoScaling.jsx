import React, { useState, useEffect } from 'react';
import ScalingChart from '../../components/infrastructure/ScalingChart';
import {
  getScalingConfig,
  updateScalingConfig,
  getScalingHistory,
  manualScale,
  setAutoScalingEnabled,
} from '../../services/infrastructureService';

/**
 * AutoScaling - Auto-scaling configuration interface
 * Configure and monitor automatic scaling of worker nodes
 */
const AutoScaling = () => {
  const [config, setConfig] = useState({
    enabled: true,
    min_workers: 2,
    max_workers: 10,
    scale_up_threshold: 80,
    scale_down_threshold: 30,
    cooldown_period: 300,
    scale_up_increment: 2,
    scale_down_increment: 1,
  });
  const [history, setHistory] = useState([]);
  const [loading, setLoading] = useState(true);
  const [saving, setSaving] = useState(false);
  const [error, setError] = useState(null);
  const [success, setSuccess] = useState(null);
  const [manualScaleTarget, setManualScaleTarget] = useState(5);

  // Fetch configuration and history
  const fetchData = async () => {
    try {
      setError(null);
      const [configResponse, historyResponse] = await Promise.all([
        getScalingConfig(),
        getScalingHistory('24h'),
      ]);

      setConfig(configResponse.data || configResponse);
      setHistory(historyResponse.data || historyResponse || []);
    } catch (err) {
      setError(err.message);
      // Mock data for demo
      setHistory([
        { timestamp: new Date(Date.now() - 21600000).toISOString(), workers: 3 },
        { timestamp: new Date(Date.now() - 18000000).toISOString(), workers: 3 },
        { timestamp: new Date(Date.now() - 14400000).toISOString(), workers: 5, event_type: 'scale_up' },
        { timestamp: new Date(Date.now() - 10800000).toISOString(), workers: 5 },
        { timestamp: new Date(Date.now() - 7200000).toISOString(), workers: 7, event_type: 'scale_up' },
        { timestamp: new Date(Date.now() - 3600000).toISOString(), workers: 7 },
        { timestamp: new Date(Date.now() - 1800000).toISOString(), workers: 5, event_type: 'scale_down' },
        { timestamp: new Date().toISOString(), workers: 5 },
      ]);
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    fetchData();
  }, []);

  // Save configuration
  const handleSave = async () => {
    setSaving(true);
    setError(null);
    setSuccess(null);

    try {
      await updateScalingConfig(config);
      setSuccess('Configuration saved successfully');
      setTimeout(() => setSuccess(null), 3000);
    } catch (err) {
      setError(`Failed to save configuration: ${err.message}`);
    } finally {
      setSaving(false);
    }
  };

  // Toggle auto-scaling
  const handleToggle = async () => {
    try {
      await setAutoScalingEnabled(!config.enabled);
      setConfig({ ...config, enabled: !config.enabled });
    } catch (err) {
      setError(`Failed to toggle auto-scaling: ${err.message}`);
    }
  };

  // Manual scale
  const handleManualScale = async () => {
    try {
      await manualScale(manualScaleTarget);
      setSuccess(`Scaling to ${manualScaleTarget} workers initiated`);
      fetchData();
      setTimeout(() => setSuccess(null), 3000);
    } catch (err) {
      setError(`Failed to scale: ${err.message}`);
    }
  };

  // Update config field
  const updateConfig = (field, value) => {
    setConfig({ ...config, [field]: value });
  };

  return (
    <div className="auto-scaling" style={{ padding: '24px' }}>
      <div style={{ marginBottom: '24px' }}>
        <h1 style={{ margin: '0 0 8px 0', fontSize: '24px', fontWeight: '600' }}>
          Auto-Scaling Configuration
        </h1>
        <p style={{ margin: 0, color: '#6b7280' }}>
          Configure automatic scaling based on resource utilization
        </p>
      </div>

      {error && (
        <div
          style={{
            padding: '12px',
            marginBottom: '16px',
            backgroundColor: '#fef2f2',
            border: '1px solid #fecaca',
            borderRadius: '8px',
            color: '#991b1b',
            fontSize: '14px',
          }}
        >
          {error}
        </div>
      )}

      {success && (
        <div
          style={{
            padding: '12px',
            marginBottom: '16px',
            backgroundColor: '#d1fae5',
            border: '1px solid #a7f3d0',
            borderRadius: '8px',
            color: '#065f46',
            fontSize: '14px',
          }}
        >
          {success}
        </div>
      )}

      <div style={{ display: 'grid', gridTemplateColumns: '1fr 1fr', gap: '24px' }}>
        {/* Configuration Panel */}
        <div
          style={{
            backgroundColor: '#ffffff',
            borderRadius: '12px',
            boxShadow: '0 1px 3px rgba(0, 0, 0, 0.1)',
            padding: '20px',
          }}
        >
          <h3 style={{ margin: '0 0 20px 0', fontSize: '16px', fontWeight: '600' }}>
            Scaling Settings
          </h3>

          {/* Enable Toggle */}
          <div
            style={{
              display: 'flex',
              justifyContent: 'space-between',
              alignItems: 'center',
              marginBottom: '24px',
              padding: '16px',
              backgroundColor: config.enabled ? '#d1fae5' : '#f3f4f6',
              borderRadius: '8px',
            }}
          >
            <div>
              <div style={{ fontWeight: '500', marginBottom: '4px' }}>Auto-Scaling</div>
              <div style={{ fontSize: '13px', color: '#6b7280' }}>
                {config.enabled ? 'Enabled' : 'Disabled'}
              </div>
            </div>
            <button
              onClick={handleToggle}
              style={{
                position: 'relative',
                width: '48px',
                height: '24px',
                borderRadius: '12px',
                border: 'none',
                backgroundColor: config.enabled ? '#10b981' : '#d1d5db',
                cursor: 'pointer',
                transition: 'background-color 0.2s',
              }}
            >
              <span
                style={{
                  position: 'absolute',
                  top: '2px',
                  left: config.enabled ? '26px' : '2px',
                  width: '20px',
                  height: '20px',
                  borderRadius: '50%',
                  backgroundColor: '#ffffff',
                  transition: 'left 0.2s',
                  boxShadow: '0 1px 3px rgba(0, 0, 0, 0.2)',
                }}
              />
            </button>
          </div>

          {/* Min/Max Workers */}
          <div style={{ marginBottom: '20px' }}>
            <label style={{ display: 'block', marginBottom: '8px', fontSize: '14px', fontWeight: '500' }}>
              Minimum Workers: {config.min_workers}
            </label>
            <input
              type="range"
              min="1"
              max={config.max_workers - 1}
              value={config.min_workers}
              onChange={(e) => updateConfig('min_workers', parseInt(e.target.value))}
              style={{ width: '100%' }}
            />
          </div>

          <div style={{ marginBottom: '20px' }}>
            <label style={{ display: 'block', marginBottom: '8px', fontSize: '14px', fontWeight: '500' }}>
              Maximum Workers: {config.max_workers}
            </label>
            <input
              type="range"
              min={config.min_workers + 1}
              max="50"
              value={config.max_workers}
              onChange={(e) => updateConfig('max_workers', parseInt(e.target.value))}
              style={{ width: '100%' }}
            />
          </div>

          {/* Thresholds */}
          <div style={{ marginBottom: '20px' }}>
            <label style={{ display: 'block', marginBottom: '8px', fontSize: '14px', fontWeight: '500' }}>
              Scale-Up Threshold: {config.scale_up_threshold}%
            </label>
            <input
              type="range"
              min="50"
              max="95"
              value={config.scale_up_threshold}
              onChange={(e) => updateConfig('scale_up_threshold', parseInt(e.target.value))}
              style={{ width: '100%' }}
            />
            <div style={{ fontSize: '12px', color: '#6b7280', marginTop: '4px' }}>
              Add workers when CPU usage exceeds this threshold
            </div>
          </div>

          <div style={{ marginBottom: '20px' }}>
            <label style={{ display: 'block', marginBottom: '8px', fontSize: '14px', fontWeight: '500' }}>
              Scale-Down Threshold: {config.scale_down_threshold}%
            </label>
            <input
              type="range"
              min="10"
              max="50"
              value={config.scale_down_threshold}
              onChange={(e) => updateConfig('scale_down_threshold', parseInt(e.target.value))}
              style={{ width: '100%' }}
            />
            <div style={{ fontSize: '12px', color: '#6b7280', marginTop: '4px' }}>
              Remove workers when CPU usage drops below this threshold
            </div>
          </div>

          {/* Cooldown Period */}
          <div style={{ marginBottom: '20px' }}>
            <label style={{ display: 'block', marginBottom: '8px', fontSize: '14px', fontWeight: '500' }}>
              Cooldown Period: {Math.floor(config.cooldown_period / 60)} minutes
            </label>
            <input
              type="range"
              min="60"
              max="900"
              step="60"
              value={config.cooldown_period}
              onChange={(e) => updateConfig('cooldown_period', parseInt(e.target.value))}
              style={{ width: '100%' }}
            />
            <div style={{ fontSize: '12px', color: '#6b7280', marginTop: '4px' }}>
              Wait time between scaling operations
            </div>
          </div>

          {/* Save Button */}
          <button
            onClick={handleSave}
            disabled={saving}
            style={{
              width: '100%',
              padding: '10px',
              backgroundColor: saving ? '#9ca3af' : '#3b82f6',
              color: '#ffffff',
              border: 'none',
              borderRadius: '6px',
              fontSize: '14px',
              fontWeight: '500',
              cursor: saving ? 'not-allowed' : 'pointer',
            }}
          >
            {saving ? 'Saving...' : 'Save Configuration'}
          </button>
        </div>

        {/* Manual Scaling & History */}
        <div style={{ display: 'flex', flexDirection: 'column', gap: '24px' }}>
          {/* Manual Scaling */}
          <div
            style={{
              backgroundColor: '#ffffff',
              borderRadius: '12px',
              boxShadow: '0 1px 3px rgba(0, 0, 0, 0.1)',
              padding: '20px',
            }}
          >
            <h3 style={{ margin: '0 0 16px 0', fontSize: '16px', fontWeight: '600' }}>
              Manual Scaling
            </h3>
            <div style={{ display: 'flex', gap: '12px', alignItems: 'flex-end' }}>
              <div style={{ flex: 1 }}>
                <label style={{ display: 'block', marginBottom: '4px', fontSize: '14px', fontWeight: '500' }}>
                  Target Workers
                </label>
                <input
                  type="number"
                  value={manualScaleTarget}
                  onChange={(e) => setManualScaleTarget(parseInt(e.target.value) || 1)}
                  min={config.min_workers}
                  max={config.max_workers}
                  style={{
                    width: '100%',
                    padding: '8px 12px',
                    border: '1px solid #d1d5db',
                    borderRadius: '6px',
                    fontSize: '14px',
                    boxSizing: 'border-box',
                  }}
                />
              </div>
              <button
                onClick={handleManualScale}
                style={{
                  padding: '8px 16px',
                  backgroundColor: '#f59e0b',
                  color: '#ffffff',
                  border: 'none',
                  borderRadius: '6px',
                  fontSize: '14px',
                  fontWeight: '500',
                  cursor: 'pointer',
                  whiteSpace: 'nowrap',
                }}
              >
                Scale Now
              </button>
            </div>
            <div style={{ fontSize: '12px', color: '#6b7280', marginTop: '8px' }}>
              Range: {config.min_workers} - {config.max_workers} workers
            </div>
          </div>

          {/* Scaling History Chart */}
          <div
            style={{
              backgroundColor: '#ffffff',
              borderRadius: '12px',
              boxShadow: '0 1px 3px rgba(0, 0, 0, 0.1)',
              padding: '20px',
              flex: 1,
            }}
          >
            <h3 style={{ margin: '0 0 16px 0', fontSize: '16px', fontWeight: '600' }}>
              Scaling History (24h)
            </h3>
            {loading ? (
              <div style={{ textAlign: 'center', padding: '40px', color: '#6b7280' }}>
                Loading history...
              </div>
            ) : (
              <ScalingChart data={history} height={250} />
            )}
          </div>

          {/* Current Status */}
          <div
            style={{
              backgroundColor: '#ffffff',
              borderRadius: '12px',
              boxShadow: '0 1px 3px rgba(0, 0, 0, 0.1)',
              padding: '20px',
            }}
          >
            <h3 style={{ margin: '0 0 16px 0', fontSize: '16px', fontWeight: '600' }}>
              Current Status
            </h3>
            <div
              style={{
                display: 'grid',
                gridTemplateColumns: 'repeat(3, 1fr)',
                gap: '16px',
                textAlign: 'center',
              }}
            >
              <div>
                <div style={{ fontSize: '24px', fontWeight: '600', color: '#3b82f6' }}>
                  {history.length > 0 ? history[history.length - 1].workers : '-'}
                </div>
                <div style={{ fontSize: '12px', color: '#6b7280' }}>Current Workers</div>
              </div>
              <div>
                <div style={{ fontSize: '24px', fontWeight: '600', color: '#10b981' }}>
                  {history.filter(h => h.event_type === 'scale_up').length}
                </div>
                <div style={{ fontSize: '12px', color: '#6b7280' }}>Scale Ups (24h)</div>
              </div>
              <div>
                <div style={{ fontSize: '24px', fontWeight: '600', color: '#f59e0b' }}>
                  {history.filter(h => h.event_type === 'scale_down').length}
                </div>
                <div style={{ fontSize: '12px', color: '#6b7280' }}>Scale Downs (24h)</div>
              </div>
            </div>
          </div>
        </div>
      </div>
    </div>
  );
};

export default AutoScaling;
