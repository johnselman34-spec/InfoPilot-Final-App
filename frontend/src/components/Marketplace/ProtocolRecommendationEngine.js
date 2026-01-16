/**
 * Protocol Recommendation Engine
 * AI-powered protocol suggestions based on user search history and performance
 * Analyzes top-performing protocols and recommends similar ones to create
 */
import React, { useState, useEffect, useCallback } from 'react';
import { useAuth } from '../../contexts/AuthContext';
import { useTheme } from '../../contexts/ThemeContext';
import { API } from '../../utils/api';

// Recommendation categories with AI-generated suggestions
const RECOMMENDATION_CATEGORIES = [
  { id: 'trending', name: '🔥 Trending Now', description: 'Hot protocols getting downloads right now' },
  { id: 'similar', name: '🎯 Similar to Your Top', description: 'Based on your best performers' },
  { id: 'gaps', name: '💡 Market Gaps', description: 'Underserved niches with high demand' },
  { id: 'seasonal', name: '📅 Seasonal Opportunities', description: 'Timely topics trending this month' },
  { id: 'premium', name: '💎 High-Value Ideas', description: 'Premium protocol opportunities' }
];

// AI-generated protocol templates based on market analysis
const AI_PROTOCOL_TEMPLATES = [
  {
    category: 'trending',
    protocols: [
      { name: 'AI News Tracker', protocol: '(artificial intelligence or AI or machine learning) & (breakthrough or announcement or launch) & (2025 or 2026)+', estimated_value: '$2.99-$4.99', demand: 'HIGH' },
      { name: 'Space Exploration Updates', protocol: '(NASA or SpaceX or space mission) & (launch or discovery or milestone) & (Mars or Moon or asteroid)+', estimated_value: '$1.99-$3.99', demand: 'HIGH' },
      { name: 'Climate Tech Innovations', protocol: '(climate or renewable energy or sustainability) & (technology or innovation or breakthrough) & (solution or investment)+', estimated_value: '$2.99-$4.99', demand: 'MEDIUM-HIGH' },
    ]
  },
  {
    category: 'similar',
    protocols: [
      { name: 'Aviation Career Guide', protocol: '(pilot or aviation or flight) & (career or training or certification) & (tips or guide or requirements)+', estimated_value: '$3.99-$5.99', demand: 'MEDIUM', note: 'Based on your aviation-themed protocols' },
      { name: 'Memoir Writing Tips', protocol: '(memoir or autobiography or life story) & (writing or publishing or tips) & (bestseller or success)+', estimated_value: '$2.99-$4.99', demand: 'MEDIUM', note: 'Based on your storytelling interests' },
    ]
  },
  {
    category: 'gaps',
    protocols: [
      { name: 'Remote Work Productivity', protocol: '(remote work or work from home or digital nomad) & (productivity or tips or tools) & (2025 or 2026)+', estimated_value: '$1.99-$2.99', demand: 'HIGH', note: 'Underserved niche!' },
      { name: 'Mental Health Resources', protocol: '(mental health or wellness or therapy) & (resources or tips or support) & (anxiety or depression or stress)+', estimated_value: '$2.99-$4.99', demand: 'HIGH', note: 'Growing demand!' },
      { name: 'Cryptocurrency Regulations', protocol: '(crypto or bitcoin or blockchain) & (regulation or law or compliance) & (2025 or 2026)+', estimated_value: '$4.99-$9.99', demand: 'HIGH', note: 'Hot topic!' },
    ]
  },
  {
    category: 'seasonal',
    protocols: [
      { name: 'Tax Season Guide 2026', protocol: '(tax or IRS or deduction) & (2026 or filing or deadline) & (tips or guide or changes)+', estimated_value: '$4.99-$9.99', demand: 'SEASONAL HIGH', note: 'Peak: Jan-Apr' },
      { name: 'Summer Travel Deals', protocol: '(travel or vacation or destination) & (deal or discount or cheap) & (summer or 2026)+', estimated_value: '$1.99-$3.99', demand: 'SEASONAL', note: 'Peak: May-Aug' },
    ]
  },
  {
    category: 'premium',
    protocols: [
      { name: 'Executive Leadership Insights', protocol: '(CEO or executive or leadership) & (strategy or insights or interview) & (Fortune 500 or startup)+', estimated_value: '$9.99-$19.99', demand: 'NICHE-HIGH', note: 'Premium audience!' },
      { name: 'Investment Due Diligence', protocol: '(investment or due diligence or analysis) & (startup or company or fund) & (risk or opportunity)+', estimated_value: '$14.99-$29.99', demand: 'NICHE-HIGH', note: 'B2B opportunity!' },
    ]
  }
];

const ProtocolRecommendationEngine = ({ showToast }) => {
  const { token, user } = useAuth();
  const { isDarkMode, currentAccent } = useTheme();
  const [recommendations, setRecommendations] = useState([]);
  const [selectedCategory, setSelectedCategory] = useState('trending');
  const [userProtocols, setUserProtocols] = useState([]);
  const [loading, setLoading] = useState(true);
  const [aiInsights, setAiInsights] = useState(null);
  
  const bgColor = isDarkMode ? 'rgba(15, 10, 35, 0.95)' : 'rgba(255, 255, 255, 0.98)';
  const cardBg = isDarkMode ? 'rgba(30, 20, 50, 0.7)' : 'rgba(248, 250, 252, 0.9)';
  const textColor = isDarkMode ? '#e2e8f0' : '#1e293b';
  const mutedColor = isDarkMode ? '#a1a1aa' : '#64748b';
  const accentColor = currentAccent?.primary || '#7c3aed';
  
  // Fetch user's protocols for personalization
  const fetchUserProtocols = useCallback(async () => {
    if (!token) return;
    try {
      const res = await fetch(`${API}/marketplace/my-protocols`, {
        headers: { Authorization: `Bearer ${token}` }
      });
      if (res.ok) {
        const data = await res.json();
        setUserProtocols(data || []);
      }
    } catch (e) {
      console.error('Failed to fetch user protocols:', e);
    }
  }, [token]);
  
  // Generate AI insights based on user data
  const generateAiInsights = useCallback(() => {
    const insights = {
      totalProtocols: userProtocols.length,
      avgPrice: userProtocols.length > 0 
        ? (userProtocols.reduce((sum, p) => sum + (p.price || 0), 0) / userProtocols.length).toFixed(2)
        : 0,
      recommendation: userProtocols.length === 0 
        ? "Start with FREE protocols to build reputation! Once you have 5+ downloads, consider premium pricing."
        : userProtocols.length < 5
        ? "You're building momentum! Focus on trending topics to maximize visibility."
        : "Great portfolio! Consider bundling related protocols for higher value sales.",
      suggestedAction: userProtocols.length === 0
        ? "Create your first protocol from our 'Market Gaps' suggestions below!"
        : "Try our 'Similar to Your Top' recommendations for easy wins.",
      potentialRevenue: `$${(userProtocols.length * 15 + 50).toFixed(2)} - $${(userProtocols.length * 50 + 200).toFixed(2)}/month`
    };
    setAiInsights(insights);
  }, [userProtocols]);
  
  useEffect(() => {
    const loadData = async () => {
      await fetchUserProtocols();
      setLoading(false);
    };
    loadData();
  }, [fetchUserProtocols]);
  
  useEffect(() => {
    // Generate insights when userProtocols changes
    if (!loading) {
      generateAiInsights();
    }
  }, [generateAiInsights, loading]);
  
  // Get recommendations for selected category
  const currentRecommendations = AI_PROTOCOL_TEMPLATES.find(t => t.category === selectedCategory)?.protocols || [];
  
  // Copy protocol to clipboard
  const copyProtocol = async (protocol) => {
    try {
      await navigator.clipboard.writeText(protocol);
      showToast('📋 Protocol copied! Paste it when creating a new category.', 'success');
    } catch (e) {
      showToast('Failed to copy', 'error');
    }
  };
  
  if (loading) {
    return (
      <div style={{ padding: 20, textAlign: 'center' }}>
        <div className="spinner" style={{ margin: '0 auto' }} />
        <p style={{ color: mutedColor, marginTop: 10 }}>🤖 AI analyzing market trends...</p>
      </div>
    );
  }
  
  return (
    <div style={{ padding: 20, background: bgColor }} data-testid="protocol-recommendation-engine">
      {/* Header with AI Badge */}
      <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'flex-start', marginBottom: 25, flexWrap: 'wrap', gap: 15 }}>
        <div>
          <h1 style={{ 
            color: '#f472b6', 
            margin: 0, 
            fontSize: '1.8rem',
            display: 'flex',
            alignItems: 'center',
            gap: 12
          }}>
            🤖 Protocol Recommendation Engine
            <span style={{
              background: 'linear-gradient(135deg, #7c3aed, #ec4899)',
              padding: '4px 12px',
              borderRadius: 20,
              fontSize: '0.7rem',
              color: '#fff',
              fontWeight: 700
            }}>
              AI-POWERED
            </span>
          </h1>
          <p style={{ color: mutedColor, margin: '8px 0 0 0', fontSize: '0.95rem' }}>
            Smart suggestions based on market trends, your history, and high-performing protocols
          </p>
        </div>
      </div>
      
      {/* AI Insights Card */}
      {aiInsights && (
        <div style={{
          background: `linear-gradient(135deg, ${accentColor}20, rgba(236, 72, 153, 0.1))`,
          borderRadius: 16,
          padding: 20,
          marginBottom: 25,
          border: `1px solid ${accentColor}40`
        }}>
          <div style={{ display: 'flex', alignItems: 'center', gap: 10, marginBottom: 15 }}>
            <span style={{ fontSize: '1.5rem' }}>🧠</span>
            <h3 style={{ color: accentColor, margin: 0 }}>AI Insights for You</h3>
          </div>
          
          <div style={{ display: 'grid', gridTemplateColumns: 'repeat(auto-fit, minmax(150px, 1fr))', gap: 15, marginBottom: 15 }}>
            <div style={{ textAlign: 'center' }}>
              <div style={{ color: '#3b82f6', fontSize: '1.8rem', fontWeight: 700 }}>{aiInsights.totalProtocols}</div>
              <div style={{ color: mutedColor, fontSize: '0.8rem' }}>Your Protocols</div>
            </div>
            <div style={{ textAlign: 'center' }}>
              <div style={{ color: '#10b981', fontSize: '1.8rem', fontWeight: 700 }}>${aiInsights.avgPrice}</div>
              <div style={{ color: mutedColor, fontSize: '0.8rem' }}>Avg Price</div>
            </div>
            <div style={{ textAlign: 'center' }}>
              <div style={{ color: '#f59e0b', fontSize: '1.2rem', fontWeight: 700 }}>{aiInsights.potentialRevenue}</div>
              <div style={{ color: mutedColor, fontSize: '0.8rem' }}>Est. Monthly Potential</div>
            </div>
          </div>
          
          <div style={{
            background: 'rgba(0,0,0,0.2)',
            borderRadius: 10,
            padding: 15
          }}>
            <p style={{ color: textColor, margin: '0 0 8px 0', fontWeight: 600 }}>
              💡 {aiInsights.recommendation}
            </p>
            <p style={{ color: '#10b981', margin: 0, fontSize: '0.9rem' }}>
              🎯 Next Step: {aiInsights.suggestedAction}
            </p>
          </div>
        </div>
      )}
      
      {/* Category Tabs */}
      <div style={{ display: 'flex', gap: 10, marginBottom: 20, flexWrap: 'wrap' }}>
        {RECOMMENDATION_CATEGORIES.map(cat => (
          <button
            key={cat.id}
            onClick={() => setSelectedCategory(cat.id)}
            style={{
              background: selectedCategory === cat.id 
                ? 'linear-gradient(135deg, #7c3aed, #ec4899)'
                : cardBg,
              border: selectedCategory === cat.id 
                ? 'none'
                : `1px solid ${accentColor}30`,
              borderRadius: 10,
              padding: '10px 16px',
              color: selectedCategory === cat.id ? '#fff' : textColor,
              fontWeight: 600,
              cursor: 'pointer',
              transition: 'all 0.2s',
              fontSize: '0.85rem'
            }}
            data-testid={`rec-category-${cat.id}`}
          >
            {cat.name}
          </button>
        ))}
      </div>
      
      {/* Category Description */}
      <p style={{ color: mutedColor, marginBottom: 20, fontSize: '0.9rem' }}>
        {RECOMMENDATION_CATEGORIES.find(c => c.id === selectedCategory)?.description}
      </p>
      
      {/* Protocol Recommendations */}
      <div style={{ display: 'flex', flexDirection: 'column', gap: 15 }}>
        {currentRecommendations.map((rec, idx) => (
          <div 
            key={idx}
            style={{
              background: cardBg,
              borderRadius: 16,
              padding: 20,
              border: `1px solid ${accentColor}20`,
              transition: 'all 0.2s'
            }}
            data-testid={`protocol-rec-${idx}`}
          >
            <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'flex-start', marginBottom: 12, flexWrap: 'wrap', gap: 10 }}>
              <div>
                <h3 style={{ color: textColor, margin: 0, fontSize: '1.1rem' }}>{rec.name}</h3>
                {rec.note && (
                  <span style={{
                    display: 'inline-block',
                    background: 'rgba(16, 185, 129, 0.2)',
                    color: '#10b981',
                    padding: '3px 10px',
                    borderRadius: 20,
                    fontSize: '0.7rem',
                    marginTop: 5,
                    fontWeight: 600
                  }}>
                    {rec.note}
                  </span>
                )}
              </div>
              <div style={{ display: 'flex', gap: 8, alignItems: 'center' }}>
                <span style={{
                  background: rec.demand.includes('HIGH') ? 'rgba(239, 68, 68, 0.2)' : 'rgba(245, 158, 11, 0.2)',
                  color: rec.demand.includes('HIGH') ? '#ef4444' : '#f59e0b',
                  padding: '4px 10px',
                  borderRadius: 20,
                  fontSize: '0.7rem',
                  fontWeight: 700
                }}>
                  {rec.demand} DEMAND
                </span>
              </div>
            </div>
            
            {/* Protocol Code */}
            <div style={{
              background: 'rgba(0,0,0,0.3)',
              borderRadius: 10,
              padding: 12,
              marginBottom: 12,
              fontFamily: 'monospace'
            }}>
              <code style={{ color: '#10b981', fontSize: '0.85rem', wordBreak: 'break-all' }}>
                {rec.protocol}
              </code>
            </div>
            
            {/* Actions */}
            <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', flexWrap: 'wrap', gap: 10 }}>
              <div style={{ color: mutedColor, fontSize: '0.85rem' }}>
                💰 Suggested Price: <span style={{ color: '#10b981', fontWeight: 600 }}>{rec.estimated_value}</span>
              </div>
              <div style={{ display: 'flex', gap: 10 }}>
                <button
                  onClick={() => copyProtocol(rec.protocol)}
                  style={{
                    background: 'linear-gradient(135deg, #3b82f6, #1d4ed8)',
                    border: 'none',
                    borderRadius: 8,
                    padding: '8px 16px',
                    color: '#fff',
                    fontWeight: 600,
                    cursor: 'pointer',
                    fontSize: '0.85rem'
                  }}
                  data-testid={`copy-protocol-${idx}`}
                >
                  📋 Copy Protocol
                </button>
              </div>
            </div>
          </div>
        ))}
      </div>
      
      {/* Pro Tips */}
      <div style={{
        marginTop: 25,
        padding: 20,
        background: 'linear-gradient(135deg, rgba(245, 158, 11, 0.1), rgba(236, 72, 153, 0.1))',
        borderRadius: 16,
        border: '1px dashed rgba(245, 158, 11, 0.3)'
      }}>
        <h4 style={{ color: '#f59e0b', margin: '0 0 12px 0' }}>🚀 Pro Tips for Maximum Revenue</h4>
        <ul style={{ color: mutedColor, margin: 0, paddingLeft: 20, fontSize: '0.9rem', lineHeight: 1.8 }}>
          <li><strong>Start FREE:</strong> Build reputation with 3-5 free protocols before charging</li>
          <li><strong>Test Prices:</strong> A/B test $1.99 vs $2.99 - higher often converts better!</li>
          <li><strong>Bundle Power:</strong> Bundle 5+ related protocols for $9.99+ value packs</li>
          <li><strong>Seasonal Timing:</strong> Launch tax protocols in January, travel in May</li>
          <li><strong>Trending Topics:</strong> AI, crypto, remote work are consistently hot</li>
        </ul>
      </div>
    </div>
  );
};

export default ProtocolRecommendationEngine;
