import React, { useState, useEffect, useRef } from 'react';
import { API } from '../../utils/api';

const AuthCallback = () => {
  const [status, setStatus] = useState('processing'); // 'processing', 'error', 'success'
  const [errorMsg, setErrorMsg] = useState('');
  const hasRun = useRef(false);

  useEffect(() => {
    if (hasRun.current) return;
    hasRun.current = true;

    const doAuth = async () => {
      try {
        // Get session_id from URL hash
        const hashParts = window.location.hash.split('session_id=');
        if (hashParts.length < 2) {
          setErrorMsg('No session ID found');
          setStatus('error');
          return;
        }
        
        const sessionId = hashParts[1].split('&')[0];
        console.log('Processing session ID:', sessionId);
        
        // Call our backend proxy to get session data (avoids CORS issues)
        const sessionResponse = await fetch(`${API}/auth/google/session-data?session_id=${encodeURIComponent(sessionId)}`);
        
        if (!sessionResponse.ok) {
          const errorData = await sessionResponse.json().catch(() => ({}));
          throw new Error(errorData.detail || 'Failed to verify Google session');
        }
        
        const userData = await sessionResponse.json();
        console.log('Got user data:', userData);
        
        // Validate we have required fields
        if (!userData.email || !userData.id) {
          throw new Error('Invalid user data received');
        }
        
        // Now authenticate with our backend
        const authResponse = await fetch(`${API}/auth/google`, {
          method: 'POST',
          headers: { 'Content-Type': 'application/json' },
          body: JSON.stringify({
            email: userData.email,
            google_id: userData.id,
            name: userData.name,
            picture: userData.picture || null
          })
        });
        
        if (!authResponse.ok) {
          const errorData = await authResponse.json().catch(() => ({}));
          throw new Error(errorData.detail || 'Login failed');
        }
        
        const authData = await authResponse.json();
        localStorage.setItem('token', authData.token);
        
        // Clear hash and redirect to clean URL
        window.location.href = window.location.origin + window.location.pathname;
        
      } catch (err) {
        console.error('Auth error:', err);
        setErrorMsg(err.message || 'Authentication failed');
        setStatus('error');
      }
    };

    doAuth();
  }, []);

  // Redirect back to login after error
  useEffect(() => {
    if (status === 'error') {
      const timer = setTimeout(() => {
        window.location.href = window.location.origin + window.location.pathname;
      }, 3000);
      return () => clearTimeout(timer);
    }
  }, [status]);

  if (status === 'error') {
    return (
      <div className="auth-container">
        <div className="auth-card" style={{ textAlign: 'center' }}>
          <h2 style={{ color: '#ef4444', marginBottom: 15 }}>Authentication Error</h2>
          <p style={{ color: '#a1a1aa' }}>{errorMsg}</p>
          <p style={{ color: '#a1a1aa', marginTop: 10 }}>Redirecting to login...</p>
        </div>
      </div>
    );
  }

  return (
    <div className="auth-container">
      <div className="auth-card" style={{ textAlign: 'center' }}>
        <div className="loading-spinner">
          <div className="spinner"></div>
        </div>
        <p style={{ marginTop: 20, color: '#a1a1aa' }}>Completing sign in...</p>
      </div>
    </div>
  );
};

export default AuthCallback;
