import React, { useState, useEffect, useCallback } from 'react';
import { API } from '../../utils/api';

/**
 * ABOptimizerAdmin - Admin interface for A/B Test Auto-Optimizer
 * Automatically disables losing variants when statistical significance is reached
 */
const ABOptimizerAdmin = ({ token, showToast }) => {
  const [status, setStatus] = useState(null);
  const [analyses, setAnalyses] = useState([]);
  const [history, setHistory] = useState([]);
  const [loading, setLoading] = useState(true);
  const [analyzing, setAnalyzing] = useState(false);
  const [optimizing, setOptimizing] = useState(false);
  const [selectedTest, setSelectedTest] = useState(null);
  const [config, setConfig] = useState({
    enabled: false,
    min_confidence: 95.0,
    min_sample_size: 100,
    auto_disable_losers: true,
    notify_on_optimization: true
  });

  const fetchData = useCallback(async () => {
    setLoading(true);
    try {
      const [statusRes, analysesRes, historyRes] = await Promise.all([
        fetch(`${API}/ab-optimizer/status`, { headers: { Authorization: `Bearer ${token}` } }),
        fetch(`${API}/ab-optimizer/analyze-all?days=30`, { headers: { Authorization: `Bearer ${token}` } }),
        fetch(`${API}/ab-optimizer/history?limit=20`, { headers: { Authorization: `Bearer ${token}` } })
      ]);

      if (statusRes.ok) {
        const data = await statusRes.json();
        setStatus(data);
        setConfig(prev => ({
          ...prev,
          enabled: data.enabled,
          min_confidence: data.min_confidence,
          min_sample_size: data.min_sample_size
        }));
      }

      if (analysesRes.ok) {
        const data = await analysesRes.json();
        setAnalyses(data.analyses || []);
      }

      if (historyRes.ok) {
        const data = await historyRes.json();
        setHistory(data.history || []);
      }
    } catch (e) {
      console.error('Failed to fetch optimizer data:', e);
    }
    setLoading(false);
  }, [token]);

  useEffect(() => {
    fetchData();
  }, [fetchData]);

  const toggleOptimizer = async () => {
    const endpoint = status?.enabled ? 'disable' : 'enable';
    try {
      const res = await fetch(`${API}/ab-optimizer/${endpoint}`, {
        method: 'POST',
        headers: { Authorization: `Bearer ${token}` }
      });
      if (res.ok) {
        showToast(status?.enabled ? 'Auto-optimizer disabled' : 'Auto-optimizer enabled! 🚀', 'success');
        fetchData();
      }
    } catch (e) {
      showToast('Failed to toggle optimizer', 'error');
    }
  };

  const analyzeTest = async (testId) => {
    setAnalyzing(true);
    setSelectedTest(null);
    try {
      const res = await fetch(`${API}/ab-optimizer/analyze/${testId}?days=30`, {
        headers: { Authorization: `Bearer ${token}` }
      });
      if (res.ok) {
        const data = await res.json();
        setSelectedTest(data);
      }
    } catch (e) {
      showToast('Failed to analyze test', 'error');
    }
    setAnalyzing(false);
  };

  const optimizeTest = async (testId, dryRun = true) => {
    setOptimizing(true);
    try {
      const res = await fetch(`${API}/ab-optimizer/optimize`, {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
          Authorization: `Bearer ${token}`
        },
        body: JSON.stringify({ test_id: testId, dry_run: dryRun })
      });
      if (res.ok) {
        const data = await res.json();
        if (data.optimized) {
          showToast(`🏆 Optimized! Disabled ${data.losers_to_disable?.length || 0} underperforming variant(s)`, 'success');
          fetchData();
        } else {
          showToast(data.reason || 'No optimization needed', 'info');
        }
        setSelectedTest(data);
      }
    } catch (e) {
      showToast('Failed to optimize test', 'error');
    }
    setOptimizing(false);
  };

  const runOptimizerNow = async (dryRun = true) => {
    setOptimizing(true);
    try {
      const res = await fetch(`${API}/ab-optimizer/run-now?dry_run=${dryRun}`, {
        method: 'POST',
        headers: { Authorization: `Bearer ${token}` }
      });
      if (res.ok) {
        const data = await res.json();
        showToast(
          dryRun 
            ? `Preview: ${data.tests_optimized} test(s) would be optimized` 
            : `🚀 Optimized ${data.tests_optimized} test(s)!`,
          'success'
        );
        fetchData();
      }
    } catch (e) {
      showToast('Failed to run optimizer', 'error');
    }
    setOptimizing(false);
  };

  const saveConfig = async () => {
    try {
      const res = await fetch(`${API}/ab-optimizer/config`, {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
          Authorization: `Bearer ${token}`
        },
        body: JSON.stringify(config)
      });
      if (res.ok) {
        showToast('Configuration saved! 💾', 'success');
        fetchData();
      }
    } catch (e) {
      showToast('Failed to save config', 'error');
    }
  };

  if (loading) {
    return <div style={{ textAlign: 'center', padding: 40, color: '#a1a1aa' }}>Loading optimizer data...</div>;
  }

  return (
    <div>
      <h3 style={{ marginBottom: 10, color: '#f472b6' }}>🤖 A/B Test Auto-Optimizer</h3>
      <p style={{ color: '#a1a1aa', marginBottom: 25 }}>
        Automatically disable losing variants when statistical significance is reached. Maximize revenue while you sleep! 💤💰
      </p>

      {/* Status Banner */}
      <div style={{
        background: status?.enabled 
          ? 'linear-gradient(135deg, rgba(16, 185, 129, 0.2), rgba(5, 150, 105, 0.2))' 
          : 'rgba(107, 114, 128, 0.2)',
        border: `1px solid ${status?.enabled ? 'rgba(16, 185, 129, 0.5)' : 'rgba(107, 114, 128, 0.3)'}`,
        borderRadius: 16,
        padding: 25,
        marginBottom: 25,
        display: 'flex',
        justifyContent: 'space-between',
        alignItems: 'center',
        flexWrap: 'wrap',
        gap: 20
      }}>
        <div>
          <div style={{ display: 'flex', alignItems: 'center', gap: 12, marginBottom: 8 }}>
            <span style={{ fontSize: '2rem' }}>{status?.enabled ? '🚀' : '⏸️'}</span>
            <span style={{ 
              fontSize: '1.3rem', 
              fontWeight: 'bold',
              color: status?.enabled ? '#10b981' : '#9ca3af'
            }}>
              {status?.enabled ? 'Auto-Optimizer ACTIVE' : 'Auto-Optimizer PAUSED'}
            </span>
          </div>
          <p style={{ color: '#a1a1aa', margin: 0, fontSize: '0.9rem' }}>
            {status?.enabled 
              ? `Running with ${status?.min_confidence}% confidence threshold. ${status?.optimizations_this_month || 0} optimizations this month.`
              : 'Enable to automatically disable underperforming variants.'}
          </p>
        </div>
        <button
          className={`btn ${status?.enabled ? 'btn-secondary' : 'btn-primary'}`}
          onClick={toggleOptimizer}
          style={{ 
            padding: '12px 24px',
            background: status?.enabled ? undefined : 'linear-gradient(135deg, #10b981, #059669)'
          }}
        >
          {status?.enabled ? '⏸️ Pause Optimizer' : '🚀 Enable Optimizer'}
        </button>
      </div>

      {/* Quick Actions */}
      <div style={{
        display: 'flex',
        gap: 15,
        marginBottom: 25,
        flexWrap: 'wrap'
      }}>
        <button
          className="btn btn-primary"
          onClick={() => runOptimizerNow(true)}
          disabled={optimizing}
          style={{ background: 'linear-gradient(135deg, #3b82f6, #2563eb)' }}
        >
          {optimizing ? '⏳ Running...' : '👁️ Preview Optimizations'}
        </button>
        <button
          className="btn btn-primary"
          onClick={() => {
            if (window.confirm('This will disable underperforming variants in tests that have reached statistical significance. Continue?')) {
              runOptimizerNow(false);
            }
          }}
          disabled={optimizing || !status?.enabled}
          style={{ background: 'linear-gradient(135deg, #10b981, #059669)' }}
        >
          {optimizing ? '⏳ Optimizing...' : '🚀 Run Optimizer Now'}
        </button>
        <button
          className="btn btn-secondary"
          onClick={fetchData}
        >
          🔄 Refresh Data
        </button>
      </div>

      {/* Configuration */}
      <div style={{
        background: 'rgba(124, 58, 237, 0.1)',
        border: '1px solid rgba(124, 58, 237, 0.3)',
        borderRadius: 12,
        padding: 20,
        marginBottom: 25
      }}>
        <h4 style={{ color: '#a78bfa', marginBottom: 15 }}>⚙️ Configuration</h4>
        <div style={{ display: 'flex', gap: 20, flexWrap: 'wrap', alignItems: 'flex-end' }}>
          <div>
            <label style={{ display: 'block', color: '#a1a1aa', fontSize: '0.85rem', marginBottom: 5 }}>
              Confidence Threshold
            </label>
            <select
              value={config.min_confidence}
              onChange={(e) => setConfig({ ...config, min_confidence: parseFloat(e.target.value) })}
              className="input-field"
              style={{ width: 120 }}
            >
              <option value={90}>90%</option>
              <option value={95}>95%</option>
              <option value={99}>99%</option>
            </select>
          </div>
          <div>
            <label style={{ display: 'block', color: '#a1a1aa', fontSize: '0.85rem', marginBottom: 5 }}>
              Min Sample Size
            </label>
            <input
              type="number"
              value={config.min_sample_size}
              onChange={(e) => setConfig({ ...config, min_sample_size: parseInt(e.target.value) })}
              className="input-field"
              style={{ width: 100 }}
              min={50}
              max={1000}
            />
          </div>
          <button className="btn btn-primary" onClick={saveConfig}>
            💾 Save Config
          </button>
        </div>
      </div>

      {/* Test Analyses */}
      <div style={{
        background: 'rgba(30, 20, 50, 0.5)',
        borderRadius: 12,
        padding: 20,
        marginBottom: 25
      }}>
        <h4 style={{ color: '#f472b6', marginBottom: 15 }}>🧪 Test Analysis</h4>
        
        {analyses.length === 0 ? (
          <p style={{ color: '#a1a1aa' }}>No A/B tests found. Create some tests to start optimizing!</p>
        ) : (
          <div style={{ display: 'flex', flexDirection: 'column', gap: 10 }}>
            {analyses.map(test => (
              <div key={test.test_id} style={{
                display: 'flex',
                justifyContent: 'space-between',
                alignItems: 'center',
                padding: 15,
                background: test.can_optimize ? 'rgba(16, 185, 129, 0.1)' : 'rgba(0, 0, 0, 0.2)',
                borderRadius: 10,
                border: test.can_optimize ? '1px solid rgba(16, 185, 129, 0.3)' : '1px solid rgba(124, 58, 237, 0.2)'
              }}>
                <div>
                  <div style={{ display: 'flex', alignItems: 'center', gap: 10, marginBottom: 5 }}>
                    <span style={{ color: '#e2e8f0', fontWeight: 600 }}>{test.test_name}</span>
                    <span style={{
                      padding: '2px 8px',
                      borderRadius: 10,
                      fontSize: '0.7rem',
                      background: test.status === 'winner_found' ? 'rgba(16, 185, 129, 0.3)' 
                        : test.status === 'testing' ? 'rgba(59, 130, 246, 0.3)' 
                        : 'rgba(107, 114, 128, 0.3)',
                      color: test.status === 'winner_found' ? '#10b981' 
                        : test.status === 'testing' ? '#3b82f6' 
                        : '#9ca3af'
                    }}>
                      {test.status === 'winner_found' ? '🏆 Winner Found' 
                        : test.status === 'testing' ? '🔬 Testing' 
                        : '📊 No Data'}
                    </span>
                  </div>
                  {test.best_variant && (
                    <div style={{ fontSize: '0.85rem', color: '#a1a1aa' }}>
                      Best: <span style={{ color: '#10b981' }}>{test.best_variant}</span>
                      {test.best_rate > 0 && <span> ({test.best_rate.toFixed(2)}% CVR)</span>}
                    </div>
                  )}
                </div>
                <div style={{ display: 'flex', gap: 8 }}>
                  <button
                    className="btn btn-secondary"
                    onClick={() => analyzeTest(test.test_id)}
                    disabled={analyzing}
                    style={{ padding: '6px 12px', fontSize: '0.8rem' }}
                  >
                    📊 Analyze
                  </button>
                  {test.can_optimize && (
                    <button
                      className="btn btn-primary"
                      onClick={() => optimizeTest(test.test_id, false)}
                      disabled={optimizing}
                      style={{ 
                        padding: '6px 12px', 
                        fontSize: '0.8rem',
                        background: 'linear-gradient(135deg, #10b981, #059669)'
                      }}
                    >
                      🚀 Optimize
                    </button>
                  )}
                </div>
              </div>
            ))}
          </div>
        )}
      </div>

      {/* Selected Test Details */}
      {selectedTest && (
        <div style={{
          background: 'rgba(59, 130, 246, 0.1)',
          border: '1px solid rgba(59, 130, 246, 0.3)',
          borderRadius: 12,
          padding: 20,
          marginBottom: 25
        }}>
          <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', marginBottom: 15 }}>
            <h4 style={{ color: '#60a5fa', margin: 0 }}>📊 {selectedTest.test_name || selectedTest.test_id}</h4>
            <button
              className="btn btn-secondary"
              onClick={() => setSelectedTest(null)}
              style={{ padding: '4px 12px', fontSize: '0.8rem' }}
            >
              ✕ Close
            </button>
          </div>

          {/* Variants */}
          {selectedTest.variants && (
            <div style={{ marginBottom: 15 }}>
              <h5 style={{ color: '#a1a1aa', marginBottom: 10 }}>Variants Performance</h5>
              <div style={{ display: 'flex', gap: 10, flexWrap: 'wrap' }}>
                {selectedTest.variants.map((v, idx) => (
                  <div key={v.id} style={{
                    padding: 15,
                    background: idx === 0 ? 'rgba(16, 185, 129, 0.2)' : 'rgba(30, 20, 50, 0.5)',
                    borderRadius: 10,
                    border: idx === 0 ? '2px solid rgba(16, 185, 129, 0.5)' : '1px solid rgba(124, 58, 237, 0.2)',
                    minWidth: 120
                  }}>
                    <div style={{ display: 'flex', alignItems: 'center', gap: 5, marginBottom: 5 }}>
                      {idx === 0 && <span>👑</span>}
                      <span style={{ color: '#e2e8f0', fontWeight: 600 }}>{v.id}</span>
                    </div>
                    <div style={{ fontSize: '1.2rem', fontWeight: 'bold', color: idx === 0 ? '#10b981' : '#a78bfa' }}>
                      {v.rate.toFixed(2)}%
                    </div>
                    <div style={{ fontSize: '0.75rem', color: '#71717a' }}>
                      {v.conversions}/{v.impressions}
                    </div>
                  </div>
                ))}
              </div>
            </div>
          )}

          {/* AI Advice */}
          {selectedTest.ai_advice && (
            <div style={{
              padding: 15,
              background: 'rgba(16, 185, 129, 0.1)',
              borderRadius: 10,
              border: '1px solid rgba(16, 185, 129, 0.3)'
            }}>
              <div style={{ display: 'flex', alignItems: 'center', gap: 8, marginBottom: 8 }}>
                <span>🤖</span>
                <span style={{ color: '#10b981', fontWeight: 600 }}>AI Recommendation</span>
              </div>
              <p style={{ color: '#e2e8f0', margin: 0, lineHeight: 1.6 }}>{selectedTest.ai_advice}</p>
            </div>
          )}
        </div>
      )}

      {/* Optimization History */}
      <div style={{
        background: 'rgba(30, 20, 50, 0.5)',
        borderRadius: 12,
        padding: 20
      }}>
        <h4 style={{ color: '#f472b6', marginBottom: 15 }}>📜 Optimization History</h4>
        
        {history.length === 0 ? (
          <p style={{ color: '#a1a1aa' }}>No optimizations performed yet.</p>
        ) : (
          <div style={{ display: 'flex', flexDirection: 'column', gap: 10 }}>
            {history.map(log => (
              <div key={log.id} style={{
                padding: 15,
                background: 'rgba(0, 0, 0, 0.2)',
                borderRadius: 10,
                border: '1px solid rgba(16, 185, 129, 0.2)'
              }}>
                <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'flex-start', marginBottom: 8 }}>
                  <div>
                    <span style={{ color: '#10b981', marginRight: 8 }}>✅</span>
                    <span style={{ color: '#e2e8f0', fontWeight: 600 }}>{log.test_name}</span>
                  </div>
                  <span style={{ color: '#71717a', fontSize: '0.8rem' }}>
                    {new Date(log.timestamp).toLocaleString()}
                  </span>
                </div>
                <div style={{ fontSize: '0.85rem', color: '#a1a1aa' }}>
                  Winner: <span style={{ color: '#10b981' }}>{log.winner}</span>
                  {log.disabled_variants?.length > 0 && (
                    <span> | Disabled: <span style={{ color: '#f87171' }}>{log.disabled_variants.join(', ')}</span></span>
                  )}
                </div>
              </div>
            ))}
          </div>
        )}
      </div>

      {/* Info Box */}
      <div style={{
        marginTop: 25,
        padding: 20,
        background: 'rgba(236, 72, 153, 0.1)',
        borderRadius: 12,
        border: '1px solid rgba(236, 72, 153, 0.3)'
      }}>
        <h4 style={{ color: '#f472b6', margin: '0 0 10px 0' }}>💡 How It Works</h4>
        <ul style={{ color: '#a1a1aa', fontSize: '0.9rem', margin: 0, paddingLeft: 20, lineHeight: 1.8 }}>
          <li><strong>Statistical Significance:</strong> Uses z-test to compare conversion rates between variants</li>
          <li><strong>Confidence Threshold:</strong> Only optimizes when difference is {config.min_confidence}%+ confident</li>
          <li><strong>Minimum Sample:</strong> Waits for at least {config.min_sample_size} impressions per variant</li>
          <li><strong>AI Insights:</strong> GPT-5.2 provides actionable recommendations</li>
          <li><strong>Safe Mode:</strong> Always preview changes before applying them</li>
        </ul>
      </div>
    </div>
  );
};

export default ABOptimizerAdmin;
