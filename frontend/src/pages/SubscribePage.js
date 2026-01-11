import React, { useState, useEffect } from 'react';
import { useAuth } from '../contexts/AuthContext';
import { API } from '../utils/api';

const SubscribePage = ({ showToast, onBack }) => {
  const { token, refreshUser } = useAuth();
  const [loading, setLoading] = useState(false);
  const [paymentClicked, setPaymentClicked] = useState(false);
  const [selectedAmount, setSelectedAmount] = useState(null);
  const [customAmount, setCustomAmount] = useState('');
  const [settings, setSettings] = useState({
    subscription_price: 0.99,
    paypal_email: 'JJSpilot24@gmail.com',
    paypal_link: 'https://py.pl/vdf9TkEwfV1ngxIsu9JzlQ'
  });

  useEffect(() => {
    const fetchSettings = async () => {
      try {
        const res = await fetch(`${API}/subscription-info`);
        if (res.ok) {
          const data = await res.json();
          setSettings(data);
        }
      } catch (e) {
        console.log('Using default settings');
      }
    };
    fetchSettings();
  }, []);

  const handlePayPalClick = (amount) => {
    const paypalEmail = settings.paypal_email || 'JJSpilot24@gmail.com';
    const paymentUrl = `https://www.paypal.com/cgi-bin/webscr?cmd=_xclick&business=${encodeURIComponent(paypalEmail)}&amount=${amount.toFixed(2)}&currency_code=USD&item_name=${encodeURIComponent('InfoPilot Premium Subscription (1 Year)')}&no_shipping=1&no_note=1`;
    
    window.open(paymentUrl, '_blank');
    setSelectedAmount(amount);
    setPaymentClicked(true);
  };

  const handleCustomPayment = () => {
    const amount = parseFloat(customAmount);
    if (isNaN(amount) || amount < 0.01) {
      showToast('Please enter a valid amount', 'error');
      return;
    }
    handlePayPalClick(amount);
  };

  const handleActivateSubscription = async () => {
    setLoading(true);
    try {
      const res = await fetch(`${API}/subscriptions/activate`, {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
          Authorization: `Bearer ${token}`
        }
      });
      
      if (res.ok) {
        showToast('Subscription activated! Thank you!', 'success');
        await refreshUser();
        onBack();
      } else {
        const data = await res.json();
        showToast(data.detail || 'Activation failed', 'error');
      }
    } catch (e) {
      showToast('Failed to activate subscription', 'error');
    }
    setLoading(false);
  };

  return (
    <div className="card" data-testid="subscribe-page">
      <div className="card-header">
        <h2>🎉 InfoPilot is FREE!</h2>
        <button className="btn btn-secondary" onClick={onBack}>← Back</button>
      </div>

      <div style={{ maxWidth: 700, margin: '0 auto' }}>
        {/* FREE Announcement */}
        <div style={{ 
          marginBottom: 30, 
          padding: 25, 
          background: 'linear-gradient(135deg, rgba(16, 185, 129, 0.2), rgba(59, 130, 246, 0.2))', 
          borderRadius: 16,
          border: '3px solid rgba(16, 185, 129, 0.5)',
          textAlign: 'center'
        }}>
          <div style={{ fontSize: '2.5rem', marginBottom: 10 }}>🎊</div>
          <h3 style={{ color: '#10b981', marginBottom: 15, fontSize: '1.8rem' }}>Good News!</h3>
          <p style={{ color: '#fff', fontSize: '1.2rem', marginBottom: 10 }}>
            InfoPilot is <span style={{ color: '#10b981', fontWeight: 800, fontSize: '1.5rem' }}>100% FREE</span> for everyone!
          </p>
          <p style={{ color: '#a1a1aa', fontSize: '0.95rem' }}>
            Enjoy all premium features at no cost. If you love InfoPilot, please support us by checking out our amazing book below! 📚
          </p>
        </div>

        {/* Premium Benefits - Now FREE */}
        <div style={{ marginBottom: 30, padding: 20, background: 'rgba(124, 58, 237, 0.1)', borderRadius: 12 }}>
          <h3 style={{ color: '#f472b6', marginBottom: 15 }}>✅ All Features Included FREE</h3>
          <ul style={{ listStyle: 'none', padding: 0 }}>
            {[
              '✨ Unlimited search results',
              '🗺️ Access to interactive world map',
              '📊 Advanced statistics and analytics',
              '🚀 Priority support',
              '💾 Unlimited categories and protocols',
              '🤖 AI-powered collation'
            ].map((benefit, i) => (
              <li key={i} style={{ padding: '8px 0', borderBottom: '1px solid rgba(124, 58, 237, 0.2)', color: '#10b981' }}>
                {benefit}
              </li>
            ))}
          </ul>
        </div>

        {/* Book Promotion */}
        <div style={{ 
          padding: 30, 
          background: 'linear-gradient(135deg, rgba(236, 72, 153, 0.3), rgba(124, 58, 237, 0.3))',
          borderRadius: 20,
          border: '3px solid rgba(236, 72, 153, 0.6)',
          textAlign: 'center',
          position: 'relative',
          overflow: 'hidden'
        }}>
          {/* Film Badge */}
          <div style={{
            position: 'absolute',
            top: 15,
            right: -35,
            background: 'linear-gradient(135deg, #fbbf24, #f59e0b)',
            color: '#000',
            padding: '8px 50px',
            fontWeight: 800,
            fontSize: '0.75rem',
            transform: 'rotate(45deg)',
            boxShadow: '0 4px 15px rgba(251, 191, 36, 0.5)'
          }}>
            OPTIONED FOR FILM!
          </div>
          
          <h3 style={{ color: '#f472b6', marginBottom: 20, fontSize: '1.5rem' }}>
            💝 Want to Support the Developer?
          </h3>
          
          {/* Book Images Grid */}
          <div style={{ display: 'flex', gap: 12, justifyContent: 'center', marginBottom: 20, flexWrap: 'wrap' }}>
            <img 
              src="https://customer-assets.emergentagent.com/job_search-explorer-5/artifacts/024v1r34_Letters%20to%20Evelyn%20advertisement%201.jpg"
              alt="Letters to Evelyn"
              style={{ width: 120, height: 120, objectFit: 'cover', borderRadius: 12, boxShadow: '0 10px 30px rgba(0,0,0,0.4)' }}
            />
            <img 
              src="https://customer-assets.emergentagent.com/job_search-explorer-5/artifacts/e90a1rlq_Letters%20to%20Evelyn%20advertisement%202.jpg"
              alt="Letters to Evelyn"
              style={{ width: 120, height: 120, objectFit: 'cover', borderRadius: 12, boxShadow: '0 10px 30px rgba(0,0,0,0.4)' }}
            />
            <img 
              src="https://customer-assets.emergentagent.com/job_search-explorer-5/artifacts/ccdegcr8_Letters%20to%20Evelyn%20advertisement%203.jpg"
              alt="Letters to Evelyn"
              style={{ width: 120, height: 120, objectFit: 'cover', borderRadius: 12, boxShadow: '0 10px 30px rgba(0,0,0,0.4)' }}
            />
            <img 
              src="https://customer-assets.emergentagent.com/job_search-explorer-5/artifacts/3gqu0i0v_Letters%20to%20Evelyn%20advertisement%204.jpg"
              alt="Letters to Evelyn"
              style={{ width: 120, height: 120, objectFit: 'cover', borderRadius: 12, boxShadow: '0 10px 30px rgba(0,0,0,0.4)' }}
            />
          </div>
          
          <div style={{ fontSize: '1.4rem', fontWeight: 800, color: '#fce7f3', marginBottom: 10 }}>
            "Letters to Evelyn"
          </div>
          <div style={{ color: '#a78bfa', marginBottom: 8, fontWeight: 600 }}>
            A Supernatural Thriller Comedy Memoir by John Selman
          </div>
          <div style={{ color: '#fbbf24', marginBottom: 8, fontWeight: 700 }}>
            By World Record Aviation Holder & Navy Pilot
          </div>
          
          <div style={{ marginBottom: 15, color: '#a1a1aa', fontSize: '0.9rem' }}>
            ✈️ Navy pilot flew 10 aircraft types • 👽 Extraterrestrial encounters • 😂 "Exceedingly brilliant comedy"
          </div>
          
          <div style={{ 
            background: 'rgba(16, 185, 129, 0.2)', 
            padding: 15, 
            borderRadius: 12, 
            marginBottom: 20,
            borderLeft: '4px solid #10b981'
          }}>
            <div style={{ color: '#10b981', fontStyle: 'italic', marginBottom: 8 }}>
              "A true story that defies belief... readers keep asking: 'WOW, is it all true?'"
            </div>
            <div style={{ color: '#34d399', fontSize: '0.85rem', fontWeight: 600 }}>
              — Readers' Favorite ★★★★★ (19 Five-Star Reviews)
            </div>
          </div>
          
          <div style={{ display: 'flex', gap: 15, justifyContent: 'center', flexWrap: 'wrap' }}>
            <a 
              href="https://www.amazon.com/Letters-Evelyn-John-Selman-ebook/dp/B0CQZ8R191"
              target="_blank"
              rel="noopener noreferrer"
              style={{
                display: 'inline-block',
                background: 'linear-gradient(135deg, #ec4899, #f97316)',
                color: 'white',
                padding: '18px 40px',
                borderRadius: 30,
                fontWeight: 800,
                fontSize: '1.2rem',
                textDecoration: 'none',
                boxShadow: '0 10px 40px rgba(236, 72, 153, 0.5)',
                border: '2px solid rgba(255,255,255,0.3)'
              }}
              data-testid="buy-book-btn"
            >
              🛒 BUY NOW - Only $2.99!
            </a>
            <a 
              href="https://letters-to-evelyn.sintra.site"
              target="_blank"
              rel="noopener noreferrer"
              style={{
                display: 'inline-block',
                background: 'rgba(124, 58, 237, 0.3)',
                color: '#a78bfa',
                padding: '18px 30px',
                borderRadius: 30,
                fontWeight: 700,
                fontSize: '1rem',
                textDecoration: 'none',
                border: '2px solid rgba(124, 58, 237, 0.5)'
              }}
            >
              🌐 Official Website
            </a>
          </div>
        </div>
      </div>
    </div>
  );
};

export default SubscribePage;
