import React, { useState, useEffect } from 'react';
import { useAuth } from '../contexts/AuthContext';
import { API } from '../utils/api';
import { ComprehensiveUserAgreement } from '../components/Legal';

const RegisterPage = ({ onSwitch }) => {
  const { register } = useAuth();
  const [email, setEmail] = useState('');
  const [username, setUsername] = useState('');
  const [password, setPassword] = useState('');
  const [error, setError] = useState('');
  const [loading, setLoading] = useState(false);
  
  // Agreement state - must complete comprehensive agreement first
  const [showAgreement, setShowAgreement] = useState(true);
  const [agreementData, setAgreementData] = useState(null);
  
  // Handle agreement acceptance
  const handleAgreementAccept = (data) => {
    setAgreementData(data);
    setShowAgreement(false);
  };
  
  // Handle agreement decline
  const handleAgreementDecline = () => {
    // Redirect away or show message
    window.location.href = 'https://www.google.com';
  };

  const handleSubmit = async (e) => {
    e.preventDefault();
    if (!agreementData) {
      setError('You must accept the User Agreement to continue');
      return;
    }
    setError('');
    setLoading(true);
    try {
      await register(email, username, password, agreementData);
    } catch (err) {
      setError(err.message);
    }
    setLoading(false);
  };

  // REMINDER: DO NOT HARDCODE THE URL, OR ADD ANY FALLBACKS OR REDIRECT URLS, THIS BREAKS THE AUTH
  const handleGoogleLogin = () => {
    if (!agreementData) {
      setError('You must accept the User Agreement before signing in');
      return;
    }
    const redirectUrl = window.location.origin;
    // Store agreement data in sessionStorage for after OAuth
    sessionStorage.setItem('agreementData', JSON.stringify(agreementData));
    window.location.href = `https://auth.emergentagent.com/?redirect=${encodeURIComponent(redirectUrl)}`;
  };

  // Show comprehensive agreement first
  if (showAgreement) {
    return (
      <ComprehensiveUserAgreement
        onAccept={handleAgreementAccept}
        onDecline={handleAgreementDecline}
      />
    );
  }

  return (
    <div className="auth-container">
      <div className="auth-card">
        <div className="auth-logo">
          <h1>InfoPilot</h1>
          <p>World Wide Web Information Exchange</p>
        </div>
        
        {/* Agreement Confirmed Badge */}
        <div style={{
          background: 'rgba(16, 185, 129, 0.2)',
          border: '1px solid rgba(16, 185, 129, 0.4)',
          borderRadius: 10,
          padding: '10px 15px',
          marginBottom: 20,
          textAlign: 'center'
        }}>
          <span style={{ color: '#10b981', fontSize: '0.85rem' }}>
            ✓ Age 26+ Verified | ✓ Terms Accepted | ✓ Privacy Acknowledged
          </span>
        </div>
        
        <form className="auth-form" onSubmit={handleSubmit}>
          {error && <div style={{ color: '#ef4444', textAlign: 'center', fontSize: '0.9rem', marginBottom: 10 }}>{error}</div>}
          <input
            className="input-field"
            type="text"
            placeholder="Username"
            value={username}
            onChange={(e) => setUsername(e.target.value)}
            required
            data-testid="register-username-input"
          />
          <input
            className="input-field"
            type="email"
            placeholder="Email"
            value={email}
            onChange={(e) => setEmail(e.target.value)}
            required
            data-testid="register-email-input"
          />
          <input
            className="input-field"
            type="password"
            placeholder="Password"
            value={password}
            onChange={(e) => setPassword(e.target.value)}
            required
            data-testid="register-password-input"
          />
          
          <button className="btn btn-primary" type="submit" disabled={loading} data-testid="register-submit-btn">
            {loading ? 'Creating account...' : 'Create Account'}
          </button>
        </form>
        <div className="auth-divider"><span>or</span></div>
        <button className="google-btn" onClick={handleGoogleLogin} data-testid="google-register-btn">
          <img src="https://www.google.com/favicon.ico" alt="Google" style={{ width: 20 }} />
          Continue with Google
        </button>
        <div className="auth-footer">
          Already have an account? <a href="#" onClick={(e) => { e.preventDefault(); onSwitch(); }} data-testid="switch-to-login">Sign In</a>
        </div>
      </div>
    </div>
  );
};

export default RegisterPage;
