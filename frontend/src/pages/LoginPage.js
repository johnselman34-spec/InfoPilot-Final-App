import React, { useState } from 'react';
import { useAuth } from '../contexts/AuthContext';

const LoginPage = ({ onSwitch }) => {
  const { login } = useAuth();
  const [email, setEmail] = useState('');
  const [password, setPassword] = useState('');
  const [error, setError] = useState('');
  const [loading, setLoading] = useState(false);

  const handleSubmit = async (e) => {
    e.preventDefault();
    setError('');
    setLoading(true);
    try {
      await login(email, password);
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
          <p>World Wide Web Information Exchange</p>
        </div>
        <form className="auth-form" onSubmit={handleSubmit}>
          {error && <div style={{ color: '#ef4444', textAlign: 'center', fontSize: '0.9rem' }}>{error}</div>}
          <input
            className="input-field"
            type="email"
            placeholder="Email"
            value={email}
            onChange={(e) => setEmail(e.target.value)}
            required
            data-testid="login-email-input"
          />
          <input
            className="input-field"
            type="password"
            placeholder="Password"
            value={password}
            onChange={(e) => setPassword(e.target.value)}
            required
            data-testid="login-password-input"
          />
          <button className="btn btn-primary" type="submit" disabled={loading} data-testid="login-submit-btn">
            {loading ? 'Signing in...' : 'Sign In'}
          </button>
        </form>
        <div className="auth-divider"><span>or</span></div>
        <button className="google-btn" onClick={handleGoogleLogin} data-testid="google-login-btn">
          <img src="https://www.google.com/favicon.ico" alt="Google" style={{ width: 20 }} />
          Continue with Google
        </button>
        <div className="auth-footer">
          Need an account? <a href="#" onClick={(e) => { e.preventDefault(); onSwitch(); }} data-testid="switch-to-register">Sign Up</a>
        </div>
      </div>
    </div>
  );
};

export default LoginPage;
