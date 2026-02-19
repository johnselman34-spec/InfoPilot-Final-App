import React, { useState, useEffect } from 'react';
import { useAuth } from '../contexts/AuthContext';
import ProtocolAnalyticsDashboard from '../components/Analytics/ProtocolAnalyticsDashboard';
import AdvancedAnalyticsDashboard from '../components/Analytics/AdvancedAnalyticsDashboard';
import { API } from '../utils/api';

/**
 * Analytics Page
 * Hub for all analytics features - Protocol Analytics Dashboard for creators
 * Now includes Advanced Analytics Dashboard
 */
const AnalyticsPage = ({ showToast }) => {
  const { user, token } = useAuth();
  const [activeView, setActiveView] = useState('advanced');
  const [searchResults, setSearchResults] = useState([]);
  const [categories, setCategories] = useState([]);
  const [mapResults, setMapResults] = useState([]);

  // Fetch data for analytics
  useEffect(() => {
    const fetchData = async () => {
      if (!token) return;
      try {
        // Fetch categories
        const catRes = await fetch(`${API}/categories`, {
          headers: { 'Authorization': `Bearer ${token}` }
        });
        if (catRes.ok) {
          const cats = await catRes.json();
          setCategories(cats);
        }
        
        // Fetch map results
        const mapRes = await fetch(`${API}/map-results`, {
          headers: { 'Authorization': `Bearer ${token}` }
        });
        if (mapRes.ok) {
          const results = await mapRes.json();
          setMapResults(results);
          setSearchResults(results);
        }
      } catch (e) {
        console.log('Analytics data fetch failed:', e);
      }
    };
    fetchData();
  }, [token]);

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
        <p style={{ color: '#a1a1aa', fontSize: '1.1rem', margin: '0 0 20px 0' }}>
          Track your protocol performance, views, copies, and revenue
        </p>
        
        {/* View Toggle */}
        <div style={{ display: 'flex', gap: 10 }}>
          <button
            onClick={() => setActiveView('advanced')}
            style={{
              padding: '10px 20px',
              borderRadius: 25,
              border: 'none',
              background: activeView === 'advanced' 
                ? 'linear-gradient(135deg, #8b5cf6, #ec4899)' 
                : 'rgba(255,255,255,0.1)',
              color: '#fff',
              cursor: 'pointer',
              fontWeight: activeView === 'advanced' ? 600 : 400
            }}
          >
            📊 Advanced Analytics
          </button>
          <button
            onClick={() => setActiveView('protocol')}
            style={{
              padding: '10px 20px',
              borderRadius: 25,
              border: 'none',
              background: activeView === 'protocol' 
                ? 'linear-gradient(135deg, #8b5cf6, #ec4899)' 
                : 'rgba(255,255,255,0.1)',
              color: '#fff',
              cursor: 'pointer',
              fontWeight: activeView === 'protocol' ? 600 : 400
            }}
          >
            📈 Protocol Analytics
          </button>
        </div>
      </div>

      {/* Advanced Analytics Dashboard */}
      {activeView === 'advanced' && (
        <AdvancedAnalyticsDashboard 
          searchResults={searchResults}
          categories={categories}
          mapResults={mapResults}
        />
      )}

      {/* Protocol Analytics Dashboard */}
      {activeView === 'protocol' && (
        <ProtocolAnalyticsDashboard showToast={showToast} />
      )}
    </div>
  );
};

export default AnalyticsPage;
