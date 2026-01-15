import React from 'react';
import { useAuth } from '../contexts/AuthContext';
import ProtocolAnalyticsDashboard from '../components/Analytics/ProtocolAnalyticsDashboard';
import { BookPromoBanner } from '../components/shared';

/**
 * Analytics Page
 * Hub for all analytics features - Protocol Analytics Dashboard for creators
 */
const AnalyticsPage = ({ showToast }) => {
  const { user, token } = useAuth();

  if (!token) {
    return (
      <div style={{
        background: 'rgba(139, 92, 246, 0.1)',
        borderRadius: 16,
        padding: 60,
        textAlign: 'center',
        border: '1px solid rgba(139, 92, 246, 0.2)'
      }}>
        <div style={{ fontSize: '3rem', marginBottom: 15 }}>🔒</div>
        <h2 style={{ color: '#fff', marginBottom: 10 }}>Login Required</h2>
        <p style={{ color: '#a1a1aa' }}>Please log in to view your analytics.</p>
      </div>
    );
  }

  return (
    <div style={{ padding: '20px 0' }}>
      {/* Page Header */}
      <div style={{
        background: 'linear-gradient(135deg, rgba(16, 185, 129, 0.2) 0%, rgba(59, 130, 246, 0.2) 100%)',
        borderRadius: 20,
        padding: 30,
        marginBottom: 30,
        border: '1px solid rgba(16, 185, 129, 0.3)'
      }}>
        <h1 style={{ 
          fontSize: '2.2rem', 
          fontWeight: 800, 
          marginBottom: 10,
          background: 'linear-gradient(135deg, #fff 0%, #10b981 100%)',
          WebkitBackgroundClip: 'text',
          WebkitTextFillColor: 'transparent'
        }}>
          📊 Analytics Hub
        </h1>
        <p style={{ color: '#a1a1aa', fontSize: '1.1rem', margin: 0 }}>
          Track your protocol performance, views, copies, and revenue
        </p>
      </div>

      {/* Protocol Analytics Dashboard */}
      <ProtocolAnalyticsDashboard showToast={showToast} />

      {/* Book Promo */}
      <div style={{ marginTop: 30 }}>
        <BookPromoBanner variant="compact" />
      </div>
    </div>
  );
};

export default AnalyticsPage;
