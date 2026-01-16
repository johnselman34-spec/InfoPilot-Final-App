/**
 * Upgrade Subscription Component
 * Shows promotional message about the pay-as-you-go model and app costs
 * Admin-configurable from the Admin Settings control panel
 */
import React, { useState, useEffect } from 'react';
import { API } from '../../utils/api';

const UpgradePromoBanner = ({ compact = false }) => {
  const defaultTitle = 'Limited Time Offer!';
  const defaultMessage = "Our pay-as-you-go promotion is testing the waters. Google Map APIs and AI search subscriptions aren't cheap! Thanks for helping us build something amazing.";
  
  const [promo, setPromo] = useState({
    title: defaultTitle,
    message: defaultMessage,
    show: true
  });
  
  useEffect(() => {
    const fetchPromo = async () => {
      try {
        const res = await fetch(`${API}/api/admin/settings/public`);
        if (res.ok) {
          const data = await res.json();
          setPromo({
            title: data.upgrade_promo_title || defaultTitle,
            message: data.upgrade_promo_message || defaultMessage,
            show: data.show_upgrade_promo !== false
          });
        }
      } catch (e) {
        // Use defaults
      }
    };
    fetchPromo();
  }, []);
  
  if (!promo.show) return null;
  
  if (compact) {
    return (
      <div style={{
        background: 'linear-gradient(135deg, rgba(245, 158, 11, 0.15), rgba(234, 88, 12, 0.15))',
        borderRadius: 8,
        padding: '10px 15px',
        border: '1px solid rgba(245, 158, 11, 0.3)',
        fontSize: '0.8rem',
        color: '#fbbf24',
        display: 'flex',
        alignItems: 'center',
        gap: 8
      }} data-testid="upgrade-promo-compact">
        <span>💡</span>
        <span>{promo.message.substring(0, 100)}...</span>
      </div>
    );
  }
  
  return (
    <div style={{
      background: 'linear-gradient(135deg, rgba(245, 158, 11, 0.1), rgba(234, 88, 12, 0.1))',
      borderRadius: 12,
      padding: 20,
      border: '2px solid rgba(245, 158, 11, 0.4)',
      marginBottom: 20,
      position: 'relative',
      overflow: 'hidden'
    }} data-testid="upgrade-promo-banner">
      {/* Background decoration */}
      <div style={{
        position: 'absolute',
        top: -20,
        right: -20,
        width: 100,
        height: 100,
        background: 'radial-gradient(circle, rgba(245, 158, 11, 0.2) 0%, transparent 70%)',
        borderRadius: '50%'
      }} />
      
      <div style={{ position: 'relative' }}>
        <h3 style={{ 
          color: '#f59e0b', 
          margin: '0 0 10px 0',
          display: 'flex',
          alignItems: 'center',
          gap: 8,
          fontSize: '1.1rem'
        }}>
          <span style={{ fontSize: '1.3rem' }}>⚡</span>
          {promo.title}
        </h3>
        
        <p style={{ 
          color: '#fcd34d', 
          margin: '0 0 15px 0',
          fontSize: '0.9rem',
          lineHeight: 1.6
        }}>
          {promo.message}
        </p>
        
        <div style={{
          display: 'flex',
          gap: 20,
          flexWrap: 'wrap',
          fontSize: '0.8rem',
          color: '#a3a3a3'
        }}>
          <span style={{ display: 'flex', alignItems: 'center', gap: 5 }}>
            🗺️ Google Maps API
          </span>
          <span style={{ display: 'flex', alignItems: 'center', gap: 5 }}>
            🤖 AI Search APIs
          </span>
          <span style={{ display: 'flex', alignItems: 'center', gap: 5 }}>
            🔍 SerpAPI + Brave
          </span>
          <span style={{ display: 'flex', alignItems: 'center', gap: 5 }}>
            📧 Email Services
          </span>
        </div>
        
        <div style={{
          marginTop: 15,
          padding: '10px 15px',
          background: 'rgba(0, 0, 0, 0.3)',
          borderRadius: 8,
          fontSize: '0.8rem',
          color: '#d4d4d8'
        }}>
          <strong style={{ color: '#10b981' }}>🙏 Thank You!</strong> Your support helps us maintain these 
          powerful features. We&apos;re testing our pay-as-you-go model to see if it&apos;s sustainable. 
          Every search, every protocol sale keeps this platform running!
        </div>
      </div>
    </div>
  );
};

export default UpgradePromoBanner;
