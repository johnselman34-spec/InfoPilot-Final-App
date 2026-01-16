import React, { useState, useEffect } from 'react';
import { useAuth } from '../contexts/AuthContext';
import { API } from '../utils/api';
import { UserAgreement, PrivacyStatement } from '../components/Legal';

const RegisterPage = ({ onSwitch }) => {
  const { register } = useAuth();
  const [email, setEmail] = useState('');
  const [username, setUsername] = useState('');
  const [password, setPassword] = useState('');
  const [error, setError] = useState('');
  const [loading, setLoading] = useState(false);
  const [acceptedTerms, setAcceptedTerms] = useState(false);
  const [showTerms, setShowTerms] = useState(null);
  const [termsSummary, setTermsSummary] = useState('');

  // Fetch terms summary on mount
  useEffect(() => {
    const fetchTermsSummary = async () => {
      try {
        const res = await fetch(`${API}/api/legal/terms-summary`);
        if (res.ok) {
          const data = await res.json();
          setTermsSummary(data.summary);
        }
      } catch (e) {
        // Fallback summary
        setTermsSummary('By creating an account, you agree to our terms of service and privacy policy. We protect your data and never sell it to third parties.');
      }
    };
    fetchTermsSummary();
  }, []);

  const fetchLegalDocument = async (type) => {
    try {
      const endpoint = type === 'terms' ? 'user-agreement' : 'privacy-policy';
      const res = await fetch(`${API}/api/legal/${endpoint}`);
      if (res.ok) {
        const data = await res.json();
        setTermsContent(data.content);
        setShowTerms(type);
      }
    } catch (e) {
      console.error('Failed to fetch legal document');
    }
  };

  const handleSubmit = async (e) => {
    e.preventDefault();
    if (!acceptedTerms) {
      setError('You must accept the User Agreement and Privacy Policy to continue');
      return;
    }
    setError('');
    setLoading(true);
    try {
      await register(email, username, password);
    } catch (err) {
      setError(err.message);
    }
    setLoading(false);
  };

  // REMINDER: DO NOT HARDCODE THE URL, OR ADD ANY FALLBACKS OR REDIRECT URLS, THIS BREAKS THE AUTH
  const handleGoogleLogin = () => {
    const redirectUrl = window.location.origin;
    window.location.href = `https://auth.emergentagent.com/?redirect=${encodeURIComponent(redirectUrl)}`;
  };

  return (
    <div className="auth-container">
      <div className="auth-card">
        <div className="auth-logo">
          <h1>InfoPilot</h1>
          <p>Your 3D View of the Internet</p>
        </div>
        <form className="auth-form" onSubmit={handleSubmit}>
          {error && <div style={{ color: '#ef4444', textAlign: 'center', fontSize: '0.9rem' }}>{error}</div>}
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
          
          {/* Terms Acceptance */}
          <div style={{ 
            padding: 12, 
            background: 'rgba(39, 39, 42, 0.5)', 
            borderRadius: 8, 
            marginBottom: 10,
            fontSize: '0.8rem'
          }}>
            <label style={{ 
              display: 'flex', 
              alignItems: 'flex-start', 
              gap: 10, 
              cursor: 'pointer',
              color: '#a1a1aa'
            }}>
              <input
                type="checkbox"
                checked={acceptedTerms}
                onChange={(e) => setAcceptedTerms(e.target.checked)}
                style={{ marginTop: 3, accentColor: '#8b5cf6' }}
                data-testid="accept-terms-checkbox"
              />
              <span>
                I agree to the{' '}
                <a 
                  href="#" 
                  onClick={(e) => { e.preventDefault(); fetchLegalDocument('terms'); }}
                  style={{ color: '#8b5cf6' }}
                >
                  User Agreement
                </a>
                {' '}and{' '}
                <a 
                  href="#" 
                  onClick={(e) => { e.preventDefault(); fetchLegalDocument('privacy'); }}
                  style={{ color: '#8b5cf6' }}
                >
                  Privacy Policy
                </a>
              </span>
            </label>
            {termsSummary && (
              <p style={{ 
                color: '#71717a', 
                fontSize: '0.7rem', 
                marginTop: 8, 
                lineHeight: 1.4,
                whiteSpace: 'pre-line'
              }}>
                {termsSummary}
              </p>
            )}
          </div>
          
          <button className="btn btn-primary" type="submit" disabled={loading || !acceptedTerms} data-testid="register-submit-btn">
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
        
        {/* Legal Document Modals - Using dedicated components */}
        {showTerms === 'terms' && (
          <UserAgreement onClose={() => setShowTerms(null)} />
        )}
        {showTerms === 'privacy' && (
          <PrivacyStatement onClose={() => setShowTerms(null)} />
        )}
      </div>
    </div>
  );
};

export default RegisterPage;
