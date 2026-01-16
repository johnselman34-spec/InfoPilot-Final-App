import React, { useState, useEffect } from 'react';
import { useAuth } from '../contexts/AuthContext';
import { API } from '../utils/api';

const RegisterPage = ({ onSwitch }) => {
  const { register } = useAuth();
  const [email, setEmail] = useState('');
  const [username, setUsername] = useState('');
  const [password, setPassword] = useState('');
  const [error, setError] = useState('');
  const [loading, setLoading] = useState(false);
  const [acceptedTerms, setAcceptedTerms] = useState(false);
  const [showTerms, setShowTerms] = useState(null);
  const [termsContent, setTermsContent] = useState('');
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
        console.error('Failed to fetch terms summary');
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
        
        {/* Legal Document Modal */}
        {showTerms && (
          <div style={{
            position: 'fixed',
            top: 0,
            left: 0,
            right: 0,
            bottom: 0,
            background: 'rgba(0,0,0,0.9)',
            display: 'flex',
            alignItems: 'center',
            justifyContent: 'center',
            zIndex: 9999,
            padding: 20
          }}>
            <div style={{
              background: '#1a1a2e',
              borderRadius: 16,
              padding: 25,
              maxWidth: 700,
              maxHeight: '80vh',
              overflow: 'auto',
              width: '100%',
              border: '1px solid rgba(124, 58, 237, 0.3)'
            }}>
              <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', marginBottom: 20 }}>
                <h2 style={{ color: '#f472b6', margin: 0, fontSize: '1.2rem' }}>
                  {showTerms === 'terms' ? '📋 User Agreement' : '🔒 Privacy Policy'}
                </h2>
                <button 
                  onClick={() => setShowTerms(null)}
                  style={{
                    background: 'rgba(239, 68, 68, 0.2)',
                    border: '1px solid #ef4444',
                    color: '#ef4444',
                    padding: '6px 12px',
                    borderRadius: 8,
                    cursor: 'pointer',
                    fontSize: '0.9rem'
                  }}
                >
                  ✕ Close
                </button>
              </div>
              <div style={{ 
                color: '#e4e4e7', 
                lineHeight: 1.6, 
                fontSize: '0.85rem',
                whiteSpace: 'pre-wrap'
              }}>
                {termsContent.split('\n').map((line, i) => {
                  if (line.startsWith('# ')) return <h1 key={i} style={{ color: '#f472b6', marginTop: 15, fontSize: '1.3rem' }}>{line.replace('# ', '')}</h1>;
                  if (line.startsWith('## ')) return <h2 key={i} style={{ color: '#a78bfa', marginTop: 12, fontSize: '1.1rem' }}>{line.replace('## ', '')}</h2>;
                  if (line.startsWith('### ')) return <h3 key={i} style={{ color: '#60a5fa', marginTop: 10, fontSize: '0.95rem' }}>{line.replace('### ', '')}</h3>;
                  if (line.startsWith('- ')) return <li key={i} style={{ marginLeft: 15 }}>{line.replace('- ', '')}</li>;
                  if (line === '---') return <hr key={i} style={{ border: 'none', borderTop: '1px solid rgba(124, 58, 237, 0.3)', margin: '15px 0' }} />;
                  return <p key={i}>{line}</p>;
                })}
              </div>
            </div>
          </div>
        )}
      </div>
    </div>
  );
};

export default RegisterPage;
