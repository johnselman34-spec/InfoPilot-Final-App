/**
 * Revenue Dashboard Component
 * Unified view of protocol sales, subscription revenue, and A/B test conversion rates
 * With PDF Export functionality
 */
import React, { useState, useEffect, useCallback, useRef } from 'react';
import { useAuth } from '../../contexts/AuthContext';
import { useTheme } from '../../contexts/ThemeContext';
import { API } from '../../utils/api';

const RevenueDashboard = ({ showToast }) => {
  const { token } = useAuth();
  const { isDarkMode } = useTheme();
  const [data, setData] = useState(null);
  const [loading, setLoading] = useState(true);
  const [period, setPeriod] = useState(30);
  const [exporting, setExporting] = useState(false);
  const dashboardRef = useRef(null);
  
  const bgColor = isDarkMode ? 'rgba(15, 10, 35, 0.95)' : 'rgba(255, 255, 255, 0.98)';
  const cardBg = isDarkMode ? 'rgba(30, 20, 50, 0.7)' : 'rgba(248, 250, 252, 0.9)';
  const textColor = isDarkMode ? '#e2e8f0' : '#1e293b';
  const mutedColor = isDarkMode ? '#a1a1aa' : '#64748b';
  
  // PDF Export function
  const exportToPDF = async () => {
    setExporting(true);
    showToast && showToast('Generating PDF report...', 'info');
    
    try {
      // Create a printable HTML document
      const printContent = `
<!DOCTYPE html>
<html>
<head>
  <title>InfoPilot Revenue Report - ${new Date().toLocaleDateString()}</title>
  <style>
    body { font-family: Arial, sans-serif; padding: 40px; color: #1e293b; }
    .header { text-align: center; margin-bottom: 30px; border-bottom: 3px solid #7c3aed; padding-bottom: 20px; }
    .logo { font-size: 28px; font-weight: bold; color: #7c3aed; }
    .subtitle { color: #64748b; margin-top: 5px; }
    .period { background: #f3e8ff; padding: 8px 16px; border-radius: 20px; display: inline-block; margin-top: 10px; }
    .summary-grid { display: grid; grid-template-columns: repeat(4, 1fr); gap: 15px; margin-bottom: 30px; }
    .summary-card { background: #f8fafc; border-radius: 12px; padding: 20px; text-align: center; border: 1px solid #e2e8f0; }
    .summary-value { font-size: 24px; font-weight: bold; color: #10b981; }
    .summary-label { font-size: 12px; color: #64748b; margin-top: 5px; }
    .section { margin-bottom: 30px; }
    .section-title { font-size: 18px; font-weight: bold; color: #7c3aed; margin-bottom: 15px; border-bottom: 1px solid #e2e8f0; padding-bottom: 10px; }
    table { width: 100%; border-collapse: collapse; }
    th, td { padding: 12px; text-align: left; border-bottom: 1px solid #e2e8f0; }
    th { background: #f8fafc; font-weight: 600; color: #64748b; }
    .footer { text-align: center; margin-top: 40px; padding-top: 20px; border-top: 1px solid #e2e8f0; color: #64748b; font-size: 12px; }
    @media print { body { padding: 20px; } }
  </style>
</head>
<body>
  <div class="header">
    <div class="logo">✈️ InfoPilot Explorer</div>
    <div class="subtitle">Revenue Dashboard Report</div>
    <div class="period">📅 Last ${period} Days (${new Date(data.generated_at).toLocaleDateString()})</div>
  </div>
  
  <div class="summary-grid">
    <div class="summary-card">
      <div class="summary-value">$${data.summary.total_revenue.toFixed(2)}</div>
      <div class="summary-label">Total Revenue</div>
    </div>
    <div class="summary-card">
      <div class="summary-value" style="color: #7c3aed;">$${data.summary.protocol_revenue.toFixed(2)}</div>
      <div class="summary-label">Protocol Sales</div>
    </div>
    <div class="summary-card">
      <div class="summary-value" style="color: #ec4899;">$${data.summary.subscription_revenue.toFixed(2)}</div>
      <div class="summary-label">Subscriptions</div>
    </div>
    <div class="summary-card">
      <div class="summary-value" style="color: #3b82f6;">${data.summary.total_users}</div>
      <div class="summary-label">Total Users (+${data.summary.new_users} new)</div>
    </div>
  </div>
  
  <div class="section">
    <div class="section-title">🏆 Top Selling Protocols</div>
    <table>
      <thead>
        <tr>
          <th>Rank</th>
          <th>Protocol Name</th>
          <th>Revenue</th>
          <th>Sales</th>
        </tr>
      </thead>
      <tbody>
        ${data.protocol_sales.top_sellers.map((seller, idx) => `
          <tr>
            <td>${idx + 1}</td>
            <td>${seller.name}</td>
            <td>$${seller.revenue.toFixed(2)}</td>
            <td>${seller.sales}</td>
          </tr>
        `).join('')}
        ${data.protocol_sales.top_sellers.length === 0 ? '<tr><td colspan="4" style="text-align: center; color: #64748b;">No sales in this period</td></tr>' : ''}
      </tbody>
    </table>
  </div>
  
  <div class="section">
    <div class="section-title">🧠 AI Recommendation Performance</div>
    <table>
      <thead>
        <tr>
          <th>Category</th>
          <th>Views</th>
          <th>Copies</th>
          <th>Creates</th>
          <th>Purchases</th>
          <th>Copy Rate</th>
          <th>Purchase Rate</th>
        </tr>
      </thead>
      <tbody>
        ${data.ai_recommendations.map(rec => `
          <tr>
            <td>${rec.category}</td>
            <td>${rec.views}</td>
            <td>${rec.copies}</td>
            <td>${rec.creates}</td>
            <td>${rec.purchases}</td>
            <td>${rec.copy_rate}%</td>
            <td>${rec.purchase_rate}%</td>
          </tr>
        `).join('')}
        ${data.ai_recommendations.length === 0 ? '<tr><td colspan="7" style="text-align: center; color: #64748b;">No recommendation data yet</td></tr>' : ''}
      </tbody>
    </table>
  </div>
  
  <div class="footer">
    <p>Generated by InfoPilot Explorer™ on ${new Date().toLocaleString()}</p>
    <p>© ${new Date().getFullYear()} Top Pilot Enterprises, Inc. All rights reserved.</p>
  </div>
</body>
</html>`;
      
      // Open print dialog
      const printWindow = window.open('', '_blank');
      printWindow.document.write(printContent);
      printWindow.document.close();
      
      // Wait for content to load then print
      printWindow.onload = () => {
        printWindow.print();
      };
      
      showToast && showToast('PDF ready! Use "Save as PDF" in print dialog.', 'success');
    } catch (e) {
      console.error('PDF export error:', e);
      showToast && showToast('Failed to generate PDF', 'error');
    }
    setExporting(false);
  };
  
  const fetchDashboard = useCallback(async () => {
    if (!token) return;
    
    setLoading(true);
    try {
      const res = await fetch(`${API}/admin/revenue-dashboard?days=${period}`, {
        headers: { Authorization: `Bearer ${token}` }
      });
      
      if (res.ok) {
        const dashboardData = await res.json();
        setData(dashboardData);
      } else {
        showToast && showToast('Failed to load revenue dashboard', 'error');
      }
    } catch (e) {
      console.error('Failed to fetch revenue dashboard:', e);
      showToast && showToast('Error loading dashboard', 'error');
    }
    setLoading(false);
  }, [token, period, showToast]);
  
  useEffect(() => {
    fetchDashboard();
  }, [fetchDashboard]);
  
  if (loading) {
    return (
      <div style={{ padding: 20, textAlign: 'center' }}>
        <div className="spinner" style={{ margin: '0 auto' }} />
        <p style={{ color: mutedColor, marginTop: 10 }}>Loading Revenue Dashboard...</p>
      </div>
    );
  }
  
  if (!data) {
    return (
      <div style={{ padding: 20, textAlign: 'center', color: mutedColor }}>
        <p>Unable to load revenue data. Please try again.</p>
        <button 
          onClick={fetchDashboard}
          style={{
            background: 'linear-gradient(135deg, #7c3aed, #ec4899)',
            border: 'none',
            borderRadius: 8,
            padding: '10px 20px',
            color: '#fff',
            cursor: 'pointer',
            marginTop: 10
          }}
        >
          Retry
        </button>
      </div>
    );
  }
  
  const { summary, protocol_sales, subscriptions, ab_testing, ai_recommendations } = data;
  
  return (
    <div style={{ padding: 20, background: bgColor }} data-testid="revenue-dashboard">
      {/* Header */}
      <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', marginBottom: 25, flexWrap: 'wrap', gap: 15 }}>
        <div>
          <h2 style={{ color: '#10b981', margin: 0, fontSize: '1.6rem', display: 'flex', alignItems: 'center', gap: 10 }}>
            <span style={{ fontSize: '1.8rem' }}>💰</span>
            Revenue Dashboard
          </h2>
          <p style={{ color: mutedColor, margin: '5px 0 0 0', fontSize: '0.9rem' }}>
            Unified view of all revenue streams and conversion metrics
          </p>
        </div>
        
        {/* Period Selector */}
        <div style={{ display: 'flex', gap: 10, alignItems: 'center' }}>
          <span style={{ color: mutedColor, fontSize: '0.85rem' }}>Period:</span>
          {[7, 30, 90, 365].map(days => (
            <button
              key={days}
              onClick={() => setPeriod(days)}
              style={{
                background: period === days 
                  ? 'linear-gradient(135deg, #7c3aed, #ec4899)'
                  : cardBg,
                border: period === days ? 'none' : `1px solid ${mutedColor}30`,
                borderRadius: 8,
                padding: '8px 16px',
                color: period === days ? '#fff' : textColor,
                fontWeight: 600,
                cursor: 'pointer',
                fontSize: '0.85rem'
              }}
            >
              {days}d
            </button>
          ))}
        </div>
      </div>
      
      {/* Summary Cards */}
      <div style={{ display: 'grid', gridTemplateColumns: 'repeat(auto-fit, minmax(180px, 1fr))', gap: 15, marginBottom: 25 }}>
        {/* Total Revenue */}
        <div style={{
          background: 'linear-gradient(135deg, rgba(16, 185, 129, 0.2), rgba(16, 185, 129, 0.1))',
          borderRadius: 16,
          padding: 20,
          border: '1px solid rgba(16, 185, 129, 0.3)'
        }}>
          <div style={{ fontSize: '0.8rem', color: '#10b981', fontWeight: 600, marginBottom: 5 }}>
            TOTAL REVENUE
          </div>
          <div style={{ fontSize: '2rem', fontWeight: 800, color: '#10b981' }}>
            ${summary.total_revenue.toFixed(2)}
          </div>
          <div style={{ fontSize: '0.75rem', color: mutedColor }}>
            Last {period} days
          </div>
        </div>
        
        {/* Protocol Sales */}
        <div style={{
          background: 'linear-gradient(135deg, rgba(124, 58, 237, 0.2), rgba(124, 58, 237, 0.1))',
          borderRadius: 16,
          padding: 20,
          border: '1px solid rgba(124, 58, 237, 0.3)'
        }}>
          <div style={{ fontSize: '0.8rem', color: '#7c3aed', fontWeight: 600, marginBottom: 5 }}>
            PROTOCOL SALES
          </div>
          <div style={{ fontSize: '2rem', fontWeight: 800, color: '#7c3aed' }}>
            ${summary.protocol_revenue.toFixed(2)}
          </div>
          <div style={{ fontSize: '0.75rem', color: mutedColor }}>
            {summary.total_sales} sales • {summary.unique_buyers} buyers
          </div>
        </div>
        
        {/* Subscriptions */}
        <div style={{
          background: 'linear-gradient(135deg, rgba(236, 72, 153, 0.2), rgba(236, 72, 153, 0.1))',
          borderRadius: 16,
          padding: 20,
          border: '1px solid rgba(236, 72, 153, 0.3)'
        }}>
          <div style={{ fontSize: '0.8rem', color: '#ec4899', fontWeight: 600, marginBottom: 5 }}>
            SUBSCRIPTIONS
          </div>
          <div style={{ fontSize: '2rem', fontWeight: 800, color: '#ec4899' }}>
            ${summary.subscription_revenue.toFixed(2)}
          </div>
          <div style={{ fontSize: '0.75rem', color: mutedColor }}>
            {summary.active_subscriptions} active
          </div>
        </div>
        
        {/* Users */}
        <div style={{
          background: 'linear-gradient(135deg, rgba(59, 130, 246, 0.2), rgba(59, 130, 246, 0.1))',
          borderRadius: 16,
          padding: 20,
          border: '1px solid rgba(59, 130, 246, 0.3)'
        }}>
          <div style={{ fontSize: '0.8rem', color: '#3b82f6', fontWeight: 600, marginBottom: 5 }}>
            USERS
          </div>
          <div style={{ fontSize: '2rem', fontWeight: 800, color: '#3b82f6' }}>
            {summary.total_users}
          </div>
          <div style={{ fontSize: '0.75rem', color: mutedColor }}>
            +{summary.new_users} new • {summary.active_users} active
          </div>
        </div>
      </div>
      
      {/* Two Column Layout */}
      <div style={{ display: 'grid', gridTemplateColumns: 'repeat(auto-fit, minmax(400px, 1fr))', gap: 20 }}>
        {/* Top Selling Protocols */}
        <div style={{ background: cardBg, borderRadius: 16, padding: 20, border: `1px solid ${mutedColor}20` }}>
          <h3 style={{ color: '#7c3aed', margin: '0 0 15px 0', fontSize: '1.1rem' }}>
            🏆 Top Selling Protocols
          </h3>
          {protocol_sales.top_sellers && protocol_sales.top_sellers.length > 0 ? (
            <div style={{ display: 'flex', flexDirection: 'column', gap: 10 }}>
              {protocol_sales.top_sellers.map((seller, idx) => (
                <div 
                  key={idx}
                  style={{
                    display: 'flex',
                    justifyContent: 'space-between',
                    alignItems: 'center',
                    padding: 12,
                    background: isDarkMode ? 'rgba(0,0,0,0.2)' : 'rgba(255,255,255,0.5)',
                    borderRadius: 10
                  }}
                >
                  <div style={{ display: 'flex', alignItems: 'center', gap: 10 }}>
                    <span style={{
                      background: idx === 0 ? '#ffd700' : idx === 1 ? '#c0c0c0' : idx === 2 ? '#cd7f32' : '#64748b',
                      color: idx < 3 ? '#000' : '#fff',
                      width: 24,
                      height: 24,
                      borderRadius: '50%',
                      display: 'flex',
                      alignItems: 'center',
                      justifyContent: 'center',
                      fontSize: '0.75rem',
                      fontWeight: 700
                    }}>
                      {idx + 1}
                    </span>
                    <span style={{ color: textColor, fontWeight: 500 }}>{seller.name}</span>
                  </div>
                  <div style={{ textAlign: 'right' }}>
                    <div style={{ color: '#10b981', fontWeight: 700 }}>${seller.revenue.toFixed(2)}</div>
                    <div style={{ color: mutedColor, fontSize: '0.75rem' }}>{seller.sales} sales</div>
                  </div>
                </div>
              ))}
            </div>
          ) : (
            <p style={{ color: mutedColor, textAlign: 'center', padding: 20 }}>
              No protocol sales yet in this period
            </p>
          )}
        </div>
        
        {/* A/B Test Performance */}
        <div style={{ background: cardBg, borderRadius: 16, padding: 20, border: `1px solid ${mutedColor}20` }}>
          <h3 style={{ color: '#f59e0b', margin: '0 0 15px 0', fontSize: '1.1rem' }}>
            📊 A/B Test Conversion Rates
          </h3>
          {ab_testing && Object.keys(ab_testing).length > 0 ? (
            <div style={{ display: 'flex', flexDirection: 'column', gap: 15 }}>
              {Object.entries(ab_testing).map(([testName, testData]) => (
                <div 
                  key={testName}
                  style={{
                    padding: 15,
                    background: isDarkMode ? 'rgba(0,0,0,0.2)' : 'rgba(255,255,255,0.5)',
                    borderRadius: 10
                  }}
                >
                  <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', marginBottom: 10 }}>
                    <span style={{ color: textColor, fontWeight: 600 }}>{testName}</span>
                    <span style={{ 
                      color: testData.overall_conversion_rate > 5 ? '#10b981' : '#f59e0b',
                      fontWeight: 700
                    }}>
                      {testData.overall_conversion_rate}% CVR
                    </span>
                  </div>
                  <div style={{ display: 'flex', gap: 10, flexWrap: 'wrap' }}>
                    {testData.variants.map((variant, idx) => (
                      <div 
                        key={idx}
                        style={{
                          background: variant.conversion_rate > testData.overall_conversion_rate 
                            ? 'rgba(16, 185, 129, 0.2)'
                            : 'rgba(245, 158, 11, 0.2)',
                          padding: '5px 10px',
                          borderRadius: 8,
                          fontSize: '0.8rem'
                        }}
                      >
                        <span style={{ color: mutedColor }}>V{variant.variant_id}: </span>
                        <span style={{ color: textColor, fontWeight: 600 }}>{variant.conversion_rate}%</span>
                      </div>
                    ))}
                  </div>
                </div>
              ))}
            </div>
          ) : (
            <p style={{ color: mutedColor, textAlign: 'center', padding: 20 }}>
              No A/B test data available
            </p>
          )}
        </div>
      </div>
      
      {/* AI Recommendations Performance */}
      <div style={{ marginTop: 20, background: cardBg, borderRadius: 16, padding: 20, border: `1px solid ${mutedColor}20` }}>
        <h3 style={{ color: '#06b6d4', margin: '0 0 15px 0', fontSize: '1.1rem' }}>
          🧠 AI Recommendation Category Performance
        </h3>
        {ai_recommendations && ai_recommendations.length > 0 ? (
          <div style={{ overflowX: 'auto' }}>
            <table style={{ width: '100%', borderCollapse: 'collapse' }}>
              <thead>
                <tr style={{ borderBottom: `1px solid ${mutedColor}30` }}>
                  <th style={{ textAlign: 'left', padding: 12, color: mutedColor, fontWeight: 600, fontSize: '0.8rem' }}>CATEGORY</th>
                  <th style={{ textAlign: 'center', padding: 12, color: mutedColor, fontWeight: 600, fontSize: '0.8rem' }}>VIEWS</th>
                  <th style={{ textAlign: 'center', padding: 12, color: mutedColor, fontWeight: 600, fontSize: '0.8rem' }}>COPIES</th>
                  <th style={{ textAlign: 'center', padding: 12, color: mutedColor, fontWeight: 600, fontSize: '0.8rem' }}>CREATES</th>
                  <th style={{ textAlign: 'center', padding: 12, color: mutedColor, fontWeight: 600, fontSize: '0.8rem' }}>PURCHASES</th>
                  <th style={{ textAlign: 'center', padding: 12, color: mutedColor, fontWeight: 600, fontSize: '0.8rem' }}>COPY RATE</th>
                  <th style={{ textAlign: 'center', padding: 12, color: mutedColor, fontWeight: 600, fontSize: '0.8rem' }}>PURCHASE RATE</th>
                </tr>
              </thead>
              <tbody>
                {ai_recommendations.sort((a, b) => b.purchase_rate - a.purchase_rate).map((rec, idx) => (
                  <tr key={idx} style={{ borderBottom: `1px solid ${mutedColor}15` }}>
                    <td style={{ padding: 12, color: textColor, fontWeight: 500 }}>{rec.category}</td>
                    <td style={{ textAlign: 'center', padding: 12, color: mutedColor }}>{rec.views}</td>
                    <td style={{ textAlign: 'center', padding: 12, color: mutedColor }}>{rec.copies}</td>
                    <td style={{ textAlign: 'center', padding: 12, color: mutedColor }}>{rec.creates}</td>
                    <td style={{ textAlign: 'center', padding: 12, color: mutedColor }}>{rec.purchases}</td>
                    <td style={{ textAlign: 'center', padding: 12 }}>
                      <span style={{
                        background: rec.copy_rate > 10 ? 'rgba(16, 185, 129, 0.2)' : 'rgba(245, 158, 11, 0.2)',
                        color: rec.copy_rate > 10 ? '#10b981' : '#f59e0b',
                        padding: '4px 10px',
                        borderRadius: 20,
                        fontWeight: 600,
                        fontSize: '0.85rem'
                      }}>
                        {rec.copy_rate}%
                      </span>
                    </td>
                    <td style={{ textAlign: 'center', padding: 12 }}>
                      <span style={{
                        background: rec.purchase_rate > 2 ? 'rgba(16, 185, 129, 0.2)' : 'rgba(245, 158, 11, 0.2)',
                        color: rec.purchase_rate > 2 ? '#10b981' : '#f59e0b',
                        padding: '4px 10px',
                        borderRadius: 20,
                        fontWeight: 600,
                        fontSize: '0.85rem'
                      }}>
                        {rec.purchase_rate}%
                      </span>
                    </td>
                  </tr>
                ))}
              </tbody>
            </table>
          </div>
        ) : (
          <p style={{ color: mutedColor, textAlign: 'center', padding: 20 }}>
            No AI recommendation data yet. Data will appear after users interact with protocol recommendations.
          </p>
        )}
      </div>
      
      {/* Footer */}
      <div style={{ marginTop: 20, textAlign: 'center', color: mutedColor, fontSize: '0.8rem' }}>
        Last updated: {new Date(data.generated_at).toLocaleString()} • Data for last {period} days
      </div>
    </div>
  );
};

export default RevenueDashboard;
