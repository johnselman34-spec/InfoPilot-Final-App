/**
 * QualityScoreAnalytics - Admin component for viewing content quality score distribution
 * Shows distribution charts, top domains, improvement opportunities, and trends
 * Includes Domain Blocklist Management functionality
 */
import React, { useState, useEffect, useCallback } from 'react';
import { useAuth } from '../../contexts/AuthContext';
import { useTheme } from '../../contexts/ThemeContext';
import { API } from '../../utils/api';

const QualityScoreAnalytics = ({ showToast }) => {
  const { token } = useAuth();
  const { isDarkMode } = useTheme();
  const [analytics, setAnalytics] = useState(null);
  const [loading, setLoading] = useState(true);
  const [blockedDomains, setBlockedDomains] = useState([]);
  const [blockingDomain, setBlockingDomain] = useState(null);
  const [showBlockedList, setShowBlockedList] = useState(false);
  const [domainAlerts, setDomainAlerts] = useState({ alerts: [], summary: {} });
  const [runningScoring, setRunningScoring] = useState(false);
  const [lastScoringRun, setLastScoringRun] = useState(null);
  const [scheduleConfig, setScheduleConfig] = useState(null);
  const [showScheduleSettings, setShowScheduleSettings] = useState(false);
  const [savingSchedule, setSavingSchedule] = useState(false);
  
  const bgColor = isDarkMode ? 'rgba(15, 10, 35, 0.95)' : 'rgba(255, 255, 255, 0.98)';
  const cardBg = isDarkMode ? 'rgba(30, 20, 50, 0.7)' : 'rgba(248, 250, 252, 0.9)';
  const textColor = isDarkMode ? '#e2e8f0' : '#1e293b';
  const mutedColor = isDarkMode ? '#a1a1aa' : '#64748b';
  
  const fetchAnalytics = useCallback(async () => {
    if (!token) return;
    
    try {
      const res = await fetch(`${API}/analytics/quality-scores`, {
        headers: { Authorization: `Bearer ${token}` }
      });
      if (res.ok) {
        const data = await res.json();
        setAnalytics(data);
      } else {
        showToast('Failed to load quality analytics', 'error');
      }
    } catch (e) {
      console.error('Failed to fetch quality analytics:', e);
      showToast('Failed to load quality analytics', 'error');
    }
    setLoading(false);
  }, [token, showToast]);
  
  const fetchBlockedDomains = useCallback(async () => {
    if (!token) return;
    try {
      const res = await fetch(`${API}/admin/blocked-domains`, {
        headers: { Authorization: `Bearer ${token}` }
      });
      if (res.ok) {
        const data = await res.json();
        setBlockedDomains(data.blocked_domains || []);
      }
    } catch (e) {
      console.error('Failed to fetch blocked domains:', e);
    }
  }, [token]);
  
  const fetchDomainAlerts = useCallback(async () => {
    if (!token) return;
    try {
      const res = await fetch(`${API}/admin/domain-alerts`, {
        headers: { Authorization: `Bearer ${token}` }
      });
      if (res.ok) {
        const data = await res.json();
        setDomainAlerts(data);
      }
    } catch (e) {
      console.error('Failed to fetch domain alerts:', e);
    }
  }, [token]);
  
  const fetchScheduleConfig = useCallback(async () => {
    if (!token) return;
    try {
      const res = await fetch(`${API}/admin/domain-scoring/schedule`, {
        headers: { Authorization: `Bearer ${token}` }
      });
      if (res.ok) {
        const data = await res.json();
        setScheduleConfig(data);
      }
    } catch (e) {
      console.error('Failed to fetch schedule config:', e);
    }
  }, [token]);
  
  const updateScheduleConfig = async (newConfig) => {
    if (!token) return;
    setSavingSchedule(true);
    
    try {
      const res = await fetch(`${API}/admin/domain-scoring/schedule`, {
        method: 'POST',
        headers: { 
          'Content-Type': 'application/json',
          Authorization: `Bearer ${token}` 
        },
        body: JSON.stringify(newConfig)
      });
      
      if (res.ok) {
        const data = await res.json();
        showToast(`⏰ ${data.message}`, 'success');
        await fetchScheduleConfig();
      } else {
        showToast('Failed to update schedule', 'error');
      }
    } catch (e) {
      showToast('Failed to update schedule', 'error');
    }
    setSavingSchedule(false);
  };
  
  const sendTestEmail = async () => {
    if (!token) return;
    
    try {
      const res = await fetch(`${API}/admin/domain-scoring/test-email`, {
        method: 'POST',
        headers: { Authorization: `Bearer ${token}` }
      });
      
      if (res.ok) {
        const data = await res.json();
        showToast(`📧 ${data.message}`, 'success');
      } else {
        const error = await res.json();
        showToast(error.detail || 'Failed to send test email', 'error');
      }
    } catch (e) {
      showToast('Failed to send test email', 'error');
    }
  };
  
  const runDomainScoring = async () => {
    if (!token) return;
    setRunningScoring(true);
    
    try {
      const res = await fetch(`${API}/admin/domain-scoring/run`, {
        method: 'POST',
        headers: { Authorization: `Bearer ${token}` }
      });
      
      if (res.ok) {
        const data = await res.json();
        setLastScoringRun(data);
        showToast(`🔍 Domain scoring complete: ${data.alerts_created} new alerts, ${data.alerts_updated} updated`, 'success');
        await fetchDomainAlerts();
      } else {
        showToast('Failed to run domain scoring', 'error');
      }
    } catch (e) {
      showToast('Failed to run domain scoring', 'error');
    }
    setRunningScoring(false);
  };
  
  const handleDismissAlert = async (alertId) => {
    if (!token) return;
    
    try {
      const res = await fetch(`${API}/admin/domain-alerts/${alertId}/dismiss`, {
        method: 'POST',
        headers: { Authorization: `Bearer ${token}` }
      });
      
      if (res.ok) {
        showToast('Alert dismissed', 'success');
        await fetchDomainAlerts();
      }
    } catch (e) {
      showToast('Failed to dismiss alert', 'error');
    }
  };
  
  const handleBlockFromAlert = async (alertId, domain) => {
    if (!token) return;
    setBlockingDomain(domain);
    
    try {
      const res = await fetch(`${API}/admin/domain-alerts/${alertId}/block`, {
        method: 'POST',
        headers: { Authorization: `Bearer ${token}` }
      });
      
      if (res.ok) {
        const data = await res.json();
        showToast(`🚫 Blocked ${domain} - Removed ${data.results_removed} results`, 'success');
        await Promise.all([fetchDomainAlerts(), fetchBlockedDomains(), fetchAnalytics()]);
      } else {
        showToast('Failed to block domain', 'error');
      }
    } catch (e) {
      showToast('Failed to block domain', 'error');
    }
    setBlockingDomain(null);
  };
  
  const handleBlockDomain = async (domain, avgScore, count) => {
    if (!token) return;
    setBlockingDomain(domain);
    
    try {
      const res = await fetch(`${API}/admin/blocked-domains`, {
        method: 'POST',
        headers: { 
          'Content-Type': 'application/json',
          Authorization: `Bearer ${token}` 
        },
        body: JSON.stringify({
          domain,
          reason: `Low quality content (avg score: ${avgScore})`,
          avg_score: avgScore,
          result_count: count
        })
      });
      
      if (res.ok) {
        const data = await res.json();
        showToast(`🚫 Blocked ${domain} - Removed ${data.results_removed} results`, 'success');
        await fetchAnalytics();
        await fetchBlockedDomains();
      } else {
        const error = await res.json();
        showToast(error.detail || 'Failed to block domain', 'error');
      }
    } catch (e) {
      showToast('Failed to block domain', 'error');
    }
    setBlockingDomain(null);
  };
  
  const handleUnblockDomain = async (domain) => {
    if (!token) return;
    
    try {
      const res = await fetch(`${API}/admin/blocked-domains/${encodeURIComponent(domain)}`, {
        method: 'DELETE',
        headers: { Authorization: `Bearer ${token}` }
      });
      
      if (res.ok) {
        showToast(`✅ Unblocked ${domain}`, 'success');
        await fetchBlockedDomains();
      } else {
        showToast('Failed to unblock domain', 'error');
      }
    } catch (e) {
      showToast('Failed to unblock domain', 'error');
    }
  };
  
  const handleBlockAllLowQuality = async () => {
    if (!token || !analytics?.improvement_opportunities?.length) return;
    
    const confirm = window.confirm(
      `This will block ${analytics.improvement_opportunities.length} low-quality domains and remove all their results. Continue?`
    );
    if (!confirm) return;
    
    try {
      const res = await fetch(`${API}/admin/blocked-domains/bulk`, {
        method: 'POST',
        headers: { 
          'Content-Type': 'application/json',
          Authorization: `Bearer ${token}` 
        },
        body: JSON.stringify({
          domains: analytics.improvement_opportunities.map(d => ({
            domain: d.domain,
            avg_score: d.avg_score,
            count: d.count,
            reason: `Low quality (avg: ${d.avg_score})`
          }))
        })
      });
      
      if (res.ok) {
        const data = await res.json();
        showToast(`🚫 Blocked ${data.blocked_count} domains - Removed ${data.total_results_removed} results`, 'success');
        await fetchAnalytics();
        await fetchBlockedDomains();
      } else {
        showToast('Failed to bulk block domains', 'error');
      }
    } catch (e) {
      showToast('Failed to bulk block domains', 'error');
    }
  };
  
  useEffect(() => {
    const load = async () => {
      await Promise.all([fetchAnalytics(), fetchBlockedDomains(), fetchDomainAlerts(), fetchScheduleConfig()]);
    };
    load();
  }, [fetchAnalytics, fetchBlockedDomains, fetchDomainAlerts, fetchScheduleConfig]);
  
  if (loading) {
    return (
      <div style={{ padding: 30, textAlign: 'center' }}>
        <div className="spinner" style={{ margin: '0 auto' }} />
        <p style={{ color: mutedColor, marginTop: 15 }}>Loading quality score analytics...</p>
      </div>
    );
  }
  
  if (!analytics) {
    return (
      <div style={{ padding: 30, textAlign: 'center', color: mutedColor }}>
        <p>Unable to load analytics. Please try again.</p>
        <button className="btn btn-primary" onClick={fetchAnalytics} style={{ marginTop: 15 }}>
          Retry
        </button>
      </div>
    );
  }

  return (
    <div style={{ background: bgColor, borderRadius: 16, padding: 25 }} data-testid="quality-score-analytics">
      {/* Header */}
      <div style={{ marginBottom: 25 }}>
        <h2 style={{ color: '#10b981', margin: 0, display: 'flex', alignItems: 'center', gap: 12 }}>
          📊 Content Quality Analytics
        </h2>
        <p style={{ color: mutedColor, margin: '8px 0 0 0', fontSize: '0.9rem' }}>
          Distribution and insights for content quality scores across {analytics.total_results.toLocaleString()} search results
        </p>
      </div>
      
      {/* Domain Quality Alerts Section */}
      <div style={{ 
        background: domainAlerts.summary?.critical > 0 
          ? 'linear-gradient(135deg, rgba(239, 68, 68, 0.15), rgba(239, 68, 68, 0.05))'
          : domainAlerts.summary?.warning > 0
            ? 'linear-gradient(135deg, rgba(245, 158, 11, 0.15), rgba(245, 158, 11, 0.05))'
            : 'linear-gradient(135deg, rgba(16, 185, 129, 0.15), rgba(16, 185, 129, 0.05))',
        borderRadius: 16, 
        padding: 20, 
        marginBottom: 25,
        border: domainAlerts.summary?.critical > 0 
          ? '2px solid rgba(239, 68, 68, 0.4)'
          : domainAlerts.summary?.warning > 0
            ? '2px solid rgba(245, 158, 11, 0.4)'
            : '2px solid rgba(16, 185, 129, 0.4)'
      }} data-testid="domain-alerts-section">
        <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', marginBottom: 15 }}>
          <div>
            <h3 style={{ 
              color: domainAlerts.summary?.critical > 0 ? '#ef4444' : domainAlerts.summary?.warning > 0 ? '#f59e0b' : '#10b981', 
              margin: 0, 
              display: 'flex', 
              alignItems: 'center', 
              gap: 10 
            }}>
              🔔 Domain Quality Alerts
              {domainAlerts.summary?.total > 0 && (
                <span style={{
                  background: domainAlerts.summary?.critical > 0 ? '#ef4444' : '#f59e0b',
                  color: '#fff',
                  padding: '2px 10px',
                  borderRadius: 12,
                  fontSize: '0.8rem',
                  fontWeight: 700
                }}>
                  {domainAlerts.summary?.total} Active
                </span>
              )}
            </h3>
            <p style={{ color: mutedColor, margin: '5px 0 0 0', fontSize: '0.85rem' }}>
              Automatic scoring identifies domains with consistently low quality content
            </p>
          </div>
          <div style={{ display: 'flex', gap: 10 }}>
            <button
              onClick={() => setShowScheduleSettings(!showScheduleSettings)}
              style={{
                background: 'transparent',
                border: '1px solid rgba(124, 58, 237, 0.4)',
                color: '#a78bfa',
                padding: '10px 15px',
                borderRadius: 10,
                fontSize: '0.85rem',
                cursor: 'pointer',
                display: 'flex',
                alignItems: 'center',
                gap: 6
              }}
              data-testid="toggle-schedule-settings"
            >
              ⚙️ Schedule
              {scheduleConfig?.enabled && <span style={{ color: '#10b981' }}>✓</span>}
            </button>
            <button
              onClick={runDomainScoring}
              disabled={runningScoring}
              style={{
                background: runningScoring ? 'rgba(156, 163, 175, 0.3)' : 'linear-gradient(135deg, #7c3aed, #a78bfa)',
                border: 'none',
                color: '#fff',
                padding: '10px 20px',
                borderRadius: 10,
                fontSize: '0.9rem',
                fontWeight: 600,
                cursor: runningScoring ? 'wait' : 'pointer',
                display: 'flex',
                alignItems: 'center',
                gap: 8
              }}
              data-testid="run-domain-scoring"
            >
              {runningScoring ? '⏳ Analyzing...' : '🔍 Run Now'}
            </button>
          </div>
        </div>
        
        {/* Schedule Settings Panel */}
        {showScheduleSettings && (
          <div style={{
            background: 'rgba(124, 58, 237, 0.1)',
            borderRadius: 12,
            padding: 20,
            marginBottom: 20,
            border: '1px solid rgba(124, 58, 237, 0.3)'
          }} data-testid="schedule-settings-panel">
            <h4 style={{ color: '#a78bfa', margin: '0 0 15px 0', display: 'flex', alignItems: 'center', gap: 10 }}>
              ⏰ Scheduled Auto-Scoring
              {scheduleConfig?.enabled && (
                <span style={{ background: '#10b981', color: '#fff', padding: '2px 8px', borderRadius: 6, fontSize: '0.7rem' }}>ACTIVE</span>
              )}
            </h4>
            
            <div style={{ display: 'grid', gridTemplateColumns: 'repeat(auto-fit, minmax(200px, 1fr))', gap: 15, marginBottom: 15 }}>
              {/* Enable/Disable Toggle */}
              <div>
                <label style={{ color: mutedColor, fontSize: '0.8rem', display: 'block', marginBottom: 6 }}>Status</label>
                <button
                  onClick={() => updateScheduleConfig({ ...scheduleConfig, enabled: !scheduleConfig?.enabled })}
                  disabled={savingSchedule}
                  style={{
                    background: scheduleConfig?.enabled ? 'rgba(16, 185, 129, 0.2)' : 'rgba(239, 68, 68, 0.2)',
                    border: `1px solid ${scheduleConfig?.enabled ? 'rgba(16, 185, 129, 0.4)' : 'rgba(239, 68, 68, 0.4)'}`,
                    color: scheduleConfig?.enabled ? '#10b981' : '#ef4444',
                    padding: '8px 16px',
                    borderRadius: 8,
                    cursor: 'pointer',
                    width: '100%',
                    fontWeight: 600
                  }}
                >
                  {scheduleConfig?.enabled ? '✅ Enabled' : '❌ Disabled'}
                </button>
              </div>
              
              {/* Schedule Frequency */}
              <div>
                <label style={{ color: mutedColor, fontSize: '0.8rem', display: 'block', marginBottom: 6 }}>Frequency</label>
                <select
                  value={scheduleConfig?.schedule || 'daily'}
                  onChange={(e) => updateScheduleConfig({ ...scheduleConfig, schedule: e.target.value })}
                  disabled={savingSchedule}
                  style={{
                    background: cardBg,
                    border: '1px solid rgba(255,255,255,0.1)',
                    color: textColor,
                    padding: '8px 12px',
                    borderRadius: 8,
                    width: '100%'
                  }}
                >
                  <option value="hourly">Hourly (Testing)</option>
                  <option value="daily">Daily</option>
                  <option value="weekly">Weekly</option>
                </select>
              </div>
              
              {/* Run Hour */}
              <div>
                <label style={{ color: mutedColor, fontSize: '0.8rem', display: 'block', marginBottom: 6 }}>Run Time (UTC)</label>
                <select
                  value={scheduleConfig?.run_hour || 6}
                  onChange={(e) => updateScheduleConfig({ ...scheduleConfig, run_hour: parseInt(e.target.value) })}
                  disabled={savingSchedule}
                  style={{
                    background: cardBg,
                    border: '1px solid rgba(255,255,255,0.1)',
                    color: textColor,
                    padding: '8px 12px',
                    borderRadius: 8,
                    width: '100%'
                  }}
                >
                  {Array.from({ length: 24 }, (_, i) => (
                    <option key={i} value={i}>{i.toString().padStart(2, '0')}:00 UTC</option>
                  ))}
                </select>
              </div>
              
              {/* Email Notifications Toggle */}
              <div>
                <label style={{ color: mutedColor, fontSize: '0.8rem', display: 'block', marginBottom: 6 }}>Email Alerts</label>
                <button
                  onClick={() => updateScheduleConfig({ ...scheduleConfig, email_notifications: !scheduleConfig?.email_notifications })}
                  disabled={savingSchedule}
                  style={{
                    background: scheduleConfig?.email_notifications ? 'rgba(16, 185, 129, 0.2)' : 'rgba(156, 163, 175, 0.2)',
                    border: `1px solid ${scheduleConfig?.email_notifications ? 'rgba(16, 185, 129, 0.4)' : 'rgba(156, 163, 175, 0.4)'}`,
                    color: scheduleConfig?.email_notifications ? '#10b981' : mutedColor,
                    padding: '8px 16px',
                    borderRadius: 8,
                    cursor: 'pointer',
                    width: '100%',
                    fontWeight: 600
                  }}
                >
                  {scheduleConfig?.email_notifications ? '📧 On' : '📧 Off'}
                </button>
              </div>
            </div>
            
            {/* Last Run & Next Run Info */}
            <div style={{ display: 'flex', justifyContent: 'space-between', flexWrap: 'wrap', gap: 15, padding: '12px 15px', background: 'rgba(0,0,0,0.2)', borderRadius: 8, marginBottom: 15 }}>
              <div>
                <span style={{ color: mutedColor, fontSize: '0.8rem' }}>Last Run: </span>
                <span style={{ color: textColor, fontSize: '0.85rem' }}>
                  {scheduleConfig?.last_run ? new Date(scheduleConfig.last_run).toLocaleString() : 'Never'}
                </span>
              </div>
              {scheduleConfig?.enabled && scheduleConfig?.next_run && (
                <div>
                  <span style={{ color: mutedColor, fontSize: '0.8rem' }}>Next Run: </span>
                  <span style={{ color: '#10b981', fontSize: '0.85rem', fontWeight: 600 }}>
                    {new Date(scheduleConfig.next_run).toLocaleString()}
                  </span>
                </div>
              )}
            </div>
            
            {/* Test Email Button */}
            {scheduleConfig?.email_notifications && (
              <button
                onClick={sendTestEmail}
                style={{
                  background: 'rgba(236, 72, 153, 0.2)',
                  border: '1px solid rgba(236, 72, 153, 0.4)',
                  color: '#f472b6',
                  padding: '8px 16px',
                  borderRadius: 8,
                  cursor: 'pointer',
                  fontSize: '0.85rem'
                }}
                data-testid="send-test-email"
              >
                📧 Send Test Email
              </button>
            )}
          </div>
        )}
              alignItems: 'center',
              gap: 8
            }}
            data-testid="run-domain-scoring"
          >
            {runningScoring ? '⏳ Analyzing...' : '🔍 Run Analysis'}
          </button>
        </div>
        
        {/* Alert Summary Badges */}
        <div style={{ display: 'flex', gap: 15, marginBottom: 15, flexWrap: 'wrap' }}>
          <div style={{ display: 'flex', alignItems: 'center', gap: 8, padding: '6px 14px', background: 'rgba(239, 68, 68, 0.2)', borderRadius: 20 }}>
            <span style={{ color: '#ef4444', fontWeight: 700 }}>🔴 Critical:</span>
            <span style={{ color: '#ef4444' }}>{domainAlerts.summary?.critical || 0}</span>
          </div>
          <div style={{ display: 'flex', alignItems: 'center', gap: 8, padding: '6px 14px', background: 'rgba(245, 158, 11, 0.2)', borderRadius: 20 }}>
            <span style={{ color: '#f59e0b', fontWeight: 700 }}>🟡 Warning:</span>
            <span style={{ color: '#f59e0b' }}>{domainAlerts.summary?.warning || 0}</span>
          </div>
          <div style={{ display: 'flex', alignItems: 'center', gap: 8, padding: '6px 14px', background: 'rgba(59, 130, 246, 0.2)', borderRadius: 20 }}>
            <span style={{ color: '#3b82f6', fontWeight: 700 }}>🔵 Watch:</span>
            <span style={{ color: '#3b82f6' }}>{domainAlerts.summary?.watch || 0}</span>
          </div>
        </div>
        
        {/* Alerts List */}
        {domainAlerts.alerts?.length > 0 ? (
          <div style={{ display: 'flex', flexDirection: 'column', gap: 10, maxHeight: 300, overflowY: 'auto' }}>
            {domainAlerts.alerts.map((alert) => (
              <div 
                key={alert.id}
                style={{
                  display: 'flex',
                  justifyContent: 'space-between',
                  alignItems: 'center',
                  padding: '12px 15px',
                  background: alert.alert_level === 'critical' 
                    ? 'rgba(239, 68, 68, 0.15)' 
                    : alert.alert_level === 'warning'
                      ? 'rgba(245, 158, 11, 0.15)'
                      : 'rgba(59, 130, 246, 0.15)',
                  borderRadius: 10,
                  border: `1px solid ${
                    alert.alert_level === 'critical' ? 'rgba(239, 68, 68, 0.3)' :
                    alert.alert_level === 'warning' ? 'rgba(245, 158, 11, 0.3)' : 'rgba(59, 130, 246, 0.3)'
                  }`
                }}
                data-testid={`alert-${alert.id}`}
              >
                <div style={{ flex: 1 }}>
                  <div style={{ display: 'flex', alignItems: 'center', gap: 10, marginBottom: 4 }}>
                    <span style={{ fontSize: '1.1rem' }}>
                      {alert.alert_level === 'critical' ? '🔴' : alert.alert_level === 'warning' ? '🟡' : '🔵'}
                    </span>
                    <span style={{ color: textColor, fontWeight: 600 }}>{alert.domain}</span>
                    <span style={{
                      background: alert.alert_level === 'critical' ? '#ef4444' : alert.alert_level === 'warning' ? '#f59e0b' : '#3b82f6',
                      color: '#fff',
                      padding: '2px 8px',
                      borderRadius: 6,
                      fontSize: '0.7rem',
                      fontWeight: 600,
                      textTransform: 'uppercase'
                    }}>
                      {alert.alert_level}
                    </span>
                  </div>
                  <div style={{ color: mutedColor, fontSize: '0.8rem' }}>
                    Avg Score: <strong style={{ color: alert.avg_score < 30 ? '#ef4444' : alert.avg_score < 45 ? '#f59e0b' : '#3b82f6' }}>{alert.avg_score}</strong> | 
                    Results: {alert.result_count} | 
                    Range: {alert.min_score} - {alert.max_score}
                  </div>
                </div>
                <div style={{ display: 'flex', gap: 8 }}>
                  <button
                    onClick={() => handleBlockFromAlert(alert.id, alert.domain)}
                    disabled={blockingDomain === alert.domain}
                    style={{
                      background: 'rgba(239, 68, 68, 0.3)',
                      border: 'none',
                      color: '#fff',
                      padding: '6px 12px',
                      borderRadius: 6,
                      fontSize: '0.8rem',
                      cursor: blockingDomain === alert.domain ? 'wait' : 'pointer',
                      fontWeight: 600
                    }}
                    data-testid={`block-alert-${alert.id}`}
                  >
                    {blockingDomain === alert.domain ? '...' : '🚫 Block'}
                  </button>
                  <button
                    onClick={() => handleDismissAlert(alert.id)}
                    style={{
                      background: 'rgba(156, 163, 175, 0.3)',
                      border: 'none',
                      color: mutedColor,
                      padding: '6px 12px',
                      borderRadius: 6,
                      fontSize: '0.8rem',
                      cursor: 'pointer'
                    }}
                    data-testid={`dismiss-alert-${alert.id}`}
                  >
                    Dismiss
                  </button>
                </div>
              </div>
            ))}
          </div>
        ) : (
          <div style={{ textAlign: 'center', padding: 20, color: '#10b981' }}>
            ✅ No quality alerts! All domains meet quality standards.
          </div>
        )}
        
        {lastScoringRun && (
          <div style={{ marginTop: 15, padding: 10, background: 'rgba(124, 58, 237, 0.1)', borderRadius: 8, fontSize: '0.8rem', color: mutedColor }}>
            Last analysis: Created {lastScoringRun.alerts_created} alerts, updated {lastScoringRun.alerts_updated} | 
            Thresholds: Critical &lt;30, Warning &lt;45, Watch &lt;55
          </div>
        )}
      </div>
      
      {/* Key Metrics */}
      <div style={{ display: 'grid', gridTemplateColumns: 'repeat(auto-fit, minmax(200px, 1fr))', gap: 15, marginBottom: 25 }}>
        <div style={{ background: 'linear-gradient(135deg, rgba(16, 185, 129, 0.15), rgba(16, 185, 129, 0.05))', borderRadius: 12, padding: 20, border: '1px solid rgba(16, 185, 129, 0.3)', textAlign: 'center' }}>
          <div style={{ fontSize: '2.5rem', fontWeight: 700, color: '#10b981' }}>
            {analytics.average_score}
          </div>
          <div style={{ color: mutedColor, fontSize: '0.85rem' }}>Average Quality Score</div>
        </div>
        
        <div style={{ background: 'linear-gradient(135deg, rgba(59, 130, 246, 0.15), rgba(59, 130, 246, 0.05))', borderRadius: 12, padding: 20, border: '1px solid rgba(59, 130, 246, 0.3)', textAlign: 'center' }}>
          <div style={{ fontSize: '2.5rem', fontWeight: 700, color: '#3b82f6' }}>
            {analytics.insights?.high_quality_percentage || 0}%
          </div>
          <div style={{ color: mutedColor, fontSize: '0.85rem' }}>High Quality+ Content</div>
        </div>
        
        <div style={{ background: 'linear-gradient(135deg, rgba(245, 158, 11, 0.15), rgba(245, 158, 11, 0.05))', borderRadius: 12, padding: 20, border: '1px solid rgba(245, 158, 11, 0.3)', textAlign: 'center' }}>
          <div style={{ fontSize: '2.5rem', fontWeight: 700, color: '#f59e0b' }}>
            {analytics.total_results.toLocaleString()}
          </div>
          <div style={{ color: mutedColor, fontSize: '0.85rem' }}>Total Results</div>
        </div>
        
        <div style={{ background: 'linear-gradient(135deg, rgba(239, 68, 68, 0.15), rgba(239, 68, 68, 0.05))', borderRadius: 12, padding: 20, border: '1px solid rgba(239, 68, 68, 0.3)', textAlign: 'center' }}>
          <div style={{ fontSize: '2.5rem', fontWeight: 700, color: '#ef4444' }}>
            {analytics.insights?.needs_improvement_count?.toLocaleString() || 0}
          </div>
          <div style={{ color: mutedColor, fontSize: '0.85rem' }}>Needs Improvement</div>
        </div>
      </div>
      
      {/* Distribution Chart */}
      <div style={{ background: cardBg, borderRadius: 12, padding: 20, marginBottom: 20 }}>
        <h3 style={{ color: textColor, margin: '0 0 20px 0', fontSize: '1.1rem' }}>
          📈 Quality Score Distribution
        </h3>
        <div style={{ display: 'flex', flexDirection: 'column', gap: 12 }}>
          {analytics.distribution?.map((range, idx) => (
            <div key={idx} style={{ display: 'flex', alignItems: 'center', gap: 15 }}>
              <div style={{ width: 140, display: 'flex', alignItems: 'center', gap: 8 }}>
                <span style={{ fontSize: '1.2rem' }}>{range.emoji}</span>
                <span style={{ color: range.color, fontWeight: 600, fontSize: '0.9rem' }}>{range.name}</span>
              </div>
              <div style={{ flex: 1, height: 28, background: 'rgba(0,0,0,0.2)', borderRadius: 14, overflow: 'hidden', position: 'relative' }}>
                <div 
                  style={{ 
                    width: `${range.percentage}%`, 
                    height: '100%', 
                    background: `linear-gradient(90deg, ${range.color}, ${range.color}90)`,
                    borderRadius: 14,
                    transition: 'width 0.5s ease'
                  }} 
                />
                <span style={{ 
                  position: 'absolute', 
                  right: 10, 
                  top: '50%', 
                  transform: 'translateY(-50%)',
                  color: textColor,
                  fontSize: '0.8rem',
                  fontWeight: 600
                }}>
                  {range.count.toLocaleString()} ({range.percentage}%)
                </span>
              </div>
              <div style={{ width: 80, textAlign: 'right', color: mutedColor, fontSize: '0.8rem' }}>
                {range.min_score}-{range.max_score}
              </div>
            </div>
          ))}
        </div>
      </div>
      
      {/* Two Column Layout */}
      <div style={{ display: 'grid', gridTemplateColumns: 'repeat(auto-fit, minmax(300px, 1fr))', gap: 20, marginBottom: 20 }}>
        {/* Top Quality Domains */}
        <div style={{ background: cardBg, borderRadius: 12, padding: 20 }}>
          <h3 style={{ color: '#10b981', margin: '0 0 15px 0', fontSize: '1rem' }}>
            🏆 Top Quality Domains
          </h3>
          {analytics.top_quality_domains?.length > 0 ? (
            <div style={{ display: 'flex', flexDirection: 'column', gap: 8 }}>
              {analytics.top_quality_domains.map((domain, idx) => (
                <div key={idx} style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', padding: '8px 12px', background: 'rgba(16, 185, 129, 0.1)', borderRadius: 8 }}>
                  <div style={{ display: 'flex', alignItems: 'center', gap: 10 }}>
                    <span style={{ color: '#fbbf24', fontWeight: 700, width: 24 }}>#{idx + 1}</span>
                    <span style={{ color: textColor, fontSize: '0.9rem' }}>{domain.domain}</span>
                  </div>
                  <div style={{ display: 'flex', alignItems: 'center', gap: 15 }}>
                    <span style={{ color: '#10b981', fontWeight: 600 }}>{domain.avg_score}</span>
                    <span style={{ color: mutedColor, fontSize: '0.75rem' }}>({domain.count} results)</span>
                  </div>
                </div>
              ))}
            </div>
          ) : (
            <p style={{ color: mutedColor, margin: 0, fontSize: '0.9rem' }}>No domain data available</p>
          )}
        </div>
        
        {/* Improvement Opportunities with Block Buttons */}
        <div style={{ background: cardBg, borderRadius: 12, padding: 20 }}>
          <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', marginBottom: 15 }}>
            <h3 style={{ color: '#ef4444', margin: 0, fontSize: '1rem' }}>
              ⚠️ Improvement Opportunities
            </h3>
            {analytics.improvement_opportunities?.length > 0 && (
              <button
                onClick={handleBlockAllLowQuality}
                style={{
                  background: 'rgba(239, 68, 68, 0.2)',
                  border: '1px solid rgba(239, 68, 68, 0.4)',
                  color: '#ef4444',
                  padding: '6px 12px',
                  borderRadius: 8,
                  fontSize: '0.75rem',
                  fontWeight: 600,
                  cursor: 'pointer'
                }}
                data-testid="block-all-low-quality"
              >
                🚫 Block All ({analytics.improvement_opportunities.length})
              </button>
            )}
          </div>
          {analytics.improvement_opportunities?.length > 0 ? (
            <div style={{ display: 'flex', flexDirection: 'column', gap: 8 }}>
              {analytics.improvement_opportunities.map((domain, idx) => (
                <div key={idx} style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', padding: '8px 12px', background: 'rgba(239, 68, 68, 0.1)', borderRadius: 8 }}>
                  <div style={{ display: 'flex', alignItems: 'center', gap: 10 }}>
                    <span style={{ color: '#f97316', fontWeight: 700, width: 24 }}>#{idx + 1}</span>
                    <span style={{ color: textColor, fontSize: '0.9rem' }}>{domain.domain}</span>
                  </div>
                  <div style={{ display: 'flex', alignItems: 'center', gap: 10 }}>
                    <span style={{ color: '#ef4444', fontWeight: 600 }}>{domain.avg_score}</span>
                    <span style={{ color: mutedColor, fontSize: '0.75rem' }}>({domain.count})</span>
                    <button
                      onClick={() => handleBlockDomain(domain.domain, domain.avg_score, domain.count)}
                      disabled={blockingDomain === domain.domain}
                      style={{
                        background: blockingDomain === domain.domain ? 'rgba(156, 163, 175, 0.3)' : 'rgba(239, 68, 68, 0.3)',
                        border: 'none',
                        color: '#fff',
                        padding: '4px 8px',
                        borderRadius: 6,
                        fontSize: '0.7rem',
                        cursor: blockingDomain === domain.domain ? 'wait' : 'pointer',
                        fontWeight: 600
                      }}
                      data-testid={`block-domain-${domain.domain}`}
                    >
                      {blockingDomain === domain.domain ? '...' : '🚫'}
                    </button>
                  </div>
                </div>
              ))}
            </div>
          ) : (
            <p style={{ color: mutedColor, margin: 0, fontSize: '0.9rem' }}>All content meets quality standards!</p>
          )}
        </div>
      </div>
      
      {/* Blocked Domains Section */}
      <div style={{ background: cardBg, borderRadius: 12, padding: 20, marginBottom: 20 }}>
        <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', marginBottom: 15 }}>
          <h3 style={{ color: '#f97316', margin: 0, fontSize: '1rem' }}>
            🚫 Blocked Domains ({blockedDomains.length})
          </h3>
          <button
            onClick={() => setShowBlockedList(!showBlockedList)}
            style={{
              background: 'transparent',
              border: '1px solid rgba(249, 115, 22, 0.4)',
              color: '#f97316',
              padding: '6px 12px',
              borderRadius: 8,
              fontSize: '0.8rem',
              cursor: 'pointer'
            }}
          >
            {showBlockedList ? 'Hide' : 'Show'} List
          </button>
        </div>
        
        {showBlockedList && blockedDomains.length > 0 && (
          <div style={{ display: 'flex', flexDirection: 'column', gap: 8, maxHeight: 300, overflowY: 'auto' }}>
            {blockedDomains.map((domain, idx) => (
              <div key={idx} style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', padding: '8px 12px', background: 'rgba(249, 115, 22, 0.1)', borderRadius: 8 }}>
                <div>
                  <span style={{ color: textColor, fontSize: '0.9rem' }}>{domain.domain}</span>
                  <span style={{ color: mutedColor, fontSize: '0.75rem', marginLeft: 10 }}>
                    Score: {domain.avg_score} | {domain.result_count} removed
                  </span>
                </div>
                <button
                  onClick={() => handleUnblockDomain(domain.domain)}
                  style={{
                    background: 'rgba(16, 185, 129, 0.3)',
                    border: 'none',
                    color: '#10b981',
                    padding: '4px 10px',
                    borderRadius: 6,
                    fontSize: '0.75rem',
                    cursor: 'pointer',
                    fontWeight: 600
                  }}
                >
                  Unblock
                </button>
              </div>
            ))}
          </div>
        )}
        
        {showBlockedList && blockedDomains.length === 0 && (
          <p style={{ color: mutedColor, margin: 0, fontSize: '0.9rem' }}>No domains blocked yet.</p>
        )}
      </div>
      
      {/* Article Type Quality */}
      <div style={{ background: cardBg, borderRadius: 12, padding: 20, marginBottom: 20 }}>
        <h3 style={{ color: textColor, margin: '0 0 15px 0', fontSize: '1rem' }}>
          📑 Quality by Article Type
        </h3>
        {analytics.article_type_quality?.length > 0 ? (
          <div style={{ display: 'flex', flexWrap: 'wrap', gap: 10 }}>
            {analytics.article_type_quality.map((type, idx) => (
              <div 
                key={idx} 
                style={{ 
                  background: type.avg_score >= 65 ? 'rgba(16, 185, 129, 0.15)' : type.avg_score >= 50 ? 'rgba(245, 158, 11, 0.15)' : 'rgba(239, 68, 68, 0.15)',
                  border: `1px solid ${type.avg_score >= 65 ? 'rgba(16, 185, 129, 0.3)' : type.avg_score >= 50 ? 'rgba(245, 158, 11, 0.3)' : 'rgba(239, 68, 68, 0.3)'}`,
                  borderRadius: 10,
                  padding: '10px 15px',
                  textAlign: 'center'
                }}
              >
                <div style={{ color: type.avg_score >= 65 ? '#10b981' : type.avg_score >= 50 ? '#f59e0b' : '#ef4444', fontWeight: 700, fontSize: '1.2rem' }}>
                  {type.avg_score}
                </div>
                <div style={{ color: textColor, fontSize: '0.8rem', fontWeight: 500 }}>{type.type}</div>
                <div style={{ color: mutedColor, fontSize: '0.7rem' }}>{type.count} results</div>
              </div>
            ))}
          </div>
        ) : (
          <p style={{ color: mutedColor, margin: 0, fontSize: '0.9rem' }}>No article type data available</p>
        )}
      </div>
      
      {/* Quality Trend */}
      {analytics.quality_trend?.length > 0 && (
        <div style={{ background: cardBg, borderRadius: 12, padding: 20 }}>
          <h3 style={{ color: textColor, margin: '0 0 15px 0', fontSize: '1rem' }}>
            📅 Quality Trend (Last 7 Days)
          </h3>
          <div style={{ display: 'flex', gap: 10, overflowX: 'auto', paddingBottom: 10 }}>
            {analytics.quality_trend.map((day, idx) => (
              <div 
                key={idx} 
                style={{ 
                  flex: '1 0 auto',
                  minWidth: 80,
                  background: 'rgba(124, 58, 237, 0.1)',
                  border: '1px solid rgba(124, 58, 237, 0.3)',
                  borderRadius: 10,
                  padding: '12px 15px',
                  textAlign: 'center'
                }}
              >
                <div style={{ color: '#a78bfa', fontWeight: 700, fontSize: '1.3rem' }}>
                  {day.avg_score}
                </div>
                <div style={{ color: mutedColor, fontSize: '0.75rem', marginTop: 5 }}>
                  {new Date(day.date).toLocaleDateString('en-US', { month: 'short', day: 'numeric' })}
                </div>
                <div style={{ color: mutedColor, fontSize: '0.7rem' }}>
                  {day.count} new
                </div>
              </div>
            ))}
          </div>
        </div>
      )}
      
      {/* Tips Section */}
      <div style={{
        marginTop: 20,
        background: 'linear-gradient(135deg, rgba(124, 58, 237, 0.1), rgba(236, 72, 153, 0.1))',
        borderRadius: 12,
        padding: 20,
        border: '1px dashed rgba(124, 58, 237, 0.3)'
      }}>
        <h4 style={{ color: '#a78bfa', margin: '0 0 12px 0' }}>💡 Content Curation Tips</h4>
        <ul style={{ color: mutedColor, margin: 0, paddingLeft: 20, fontSize: '0.9rem', lineHeight: 1.8 }}>
          <li><strong>Premium Content (80+):</strong> Prioritize authoritative sources like .edu, .gov, and reputable news sites</li>
          <li><strong>Improve Low Scores:</strong> Review domains in the improvement list and consider filtering them out</li>
          <li><strong>Quality Keywords:</strong> Results with research, study, analysis score higher automatically</li>
          <li><strong>Content Length:</strong> Longer, more detailed articles receive higher quality scores</li>
        </ul>
      </div>
      
      <p style={{ color: mutedColor, fontSize: '0.75rem', marginTop: 15, textAlign: 'right' }}>
        Last updated: {new Date(analytics.last_updated).toLocaleString()}
      </p>
    </div>
  );
};

export default QualityScoreAnalytics;
