/**
 * Banned Words Admin Component
 * Allows admins to ban words/phrases from protocols
 * Reserved keywords (or, and, &, parentheses) cannot be banned
 */
import React, { useState, useEffect, useCallback } from 'react';
import { useAuth } from '../../contexts/AuthContext';
import { useTheme } from '../../contexts/ThemeContext';
import { API } from '../../utils/api';

// Reserved protocol keywords that cannot be banned
const RESERVED_KEYWORDS = ['or', 'and', '&', '(', ')', '+'];

const BannedWordsAdmin = ({ showToast }) => {
  const { token } = useAuth();
  const { isDarkMode } = useTheme();
  const [bannedWords, setBannedWords] = useState([]);
  const [loading, setLoading] = useState(true);
  const [newWord, setNewWord] = useState('');
  const [newReason, setNewReason] = useState('');
  const [adding, setAdding] = useState(false);
  
  const bgColor = isDarkMode ? 'rgba(15, 10, 35, 0.95)' : 'rgba(255, 255, 255, 0.98)';
  const cardBg = isDarkMode ? 'rgba(30, 20, 50, 0.7)' : 'rgba(248, 250, 252, 0.9)';
  const textColor = isDarkMode ? '#e2e8f0' : '#1e293b';
  const mutedColor = isDarkMode ? '#a1a1aa' : '#64748b';
  
  const fetchBannedWords = useCallback(async () => {
    if (!token) return;
    
    try {
      const res = await fetch(`${API}/admin/banned-words`, {
        headers: { Authorization: `Bearer ${token}` }
      });
      
      if (res.ok) {
        const data = await res.json();
        setBannedWords(data);
      }
    } catch (e) {
      console.error('Failed to fetch banned words:', e);
    }
    setLoading(false);
  }, [token]);
  
  useEffect(() => {
    fetchBannedWords();
  }, [fetchBannedWords]);
  
  const handleAddWord = async () => {
    if (!newWord.trim()) {
      showToast && showToast('Please enter a word or phrase', 'error');
      return;
    }
    
    const wordLower = newWord.trim().toLowerCase();
    
    // Check for reserved keywords
    if (RESERVED_KEYWORDS.includes(wordLower)) {
      showToast && showToast(`Cannot ban "${newWord}" - it's a reserved protocol keyword`, 'error');
      return;
    }
    
    setAdding(true);
    try {
      const res = await fetch(`${API}/admin/banned-words`, {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
          Authorization: `Bearer ${token}`
        },
        body: JSON.stringify({ word: newWord.trim(), reason: newReason.trim() })
      });
      
      if (res.ok) {
        showToast && showToast(`"${newWord}" has been banned`, 'success');
        setNewWord('');
        setNewReason('');
        fetchBannedWords();
      } else {
        const err = await res.json();
        showToast && showToast(err.detail || 'Failed to ban word', 'error');
      }
    } catch (e) {
      showToast && showToast('Failed to ban word', 'error');
    }
    setAdding(false);
  };
  
  const handleRemoveWord = async (wordId, word) => {
    if (!window.confirm(`Are you sure you want to unban "${word}"?`)) return;
    
    try {
      const res = await fetch(`${API}/admin/banned-words/${wordId}`, {
        method: 'DELETE',
        headers: { Authorization: `Bearer ${token}` }
      });
      
      if (res.ok) {
        showToast && showToast(`"${word}" has been unbanned`, 'success');
        fetchBannedWords();
      } else {
        showToast && showToast('Failed to unban word', 'error');
      }
    } catch (e) {
      showToast && showToast('Failed to unban word', 'error');
    }
  };
  
  if (loading) {
    return (
      <div style={{ padding: 20, textAlign: 'center' }}>
        <div className="spinner" style={{ margin: '0 auto' }} />
        <p style={{ color: mutedColor, marginTop: 10 }}>Loading banned words...</p>
      </div>
    );
  }
  
  return (
    <div style={{ padding: 20, background: bgColor }} data-testid="banned-words-admin">
      <h3 style={{ color: '#ef4444', margin: '0 0 10px 0', display: 'flex', alignItems: 'center', gap: 10 }}>
        <span style={{ fontSize: '1.3rem' }}>🚫</span>
        Banned Words & Phrases
      </h3>
      <p style={{ color: mutedColor, margin: '0 0 20px 0', fontSize: '0.9rem' }}>
        Ban words or phrases from being used in protocols. Reserved keywords (<code>or</code>, <code>and</code>, <code>&</code>, <code>(</code>, <code>)</code>, <code>+</code>) cannot be banned.
      </p>
      
      {/* Add New Banned Word */}
      <div style={{
        background: cardBg,
        borderRadius: 12,
        padding: 20,
        marginBottom: 20,
        border: '1px solid rgba(239, 68, 68, 0.3)'
      }}>
        <h4 style={{ color: textColor, margin: '0 0 15px 0' }}>Add Banned Word/Phrase</h4>
        <div style={{ display: 'flex', gap: 10, flexWrap: 'wrap' }}>
          <input
            type="text"
            value={newWord}
            onChange={(e) => setNewWord(e.target.value)}
            placeholder="Word or phrase to ban..."
            style={{
              flex: 1,
              minWidth: 200,
              padding: '10px 15px',
              borderRadius: 8,
              border: `1px solid ${mutedColor}30`,
              background: isDarkMode ? 'rgba(0,0,0,0.3)' : '#fff',
              color: textColor
            }}
            data-testid="ban-word-input"
          />
          <input
            type="text"
            value={newReason}
            onChange={(e) => setNewReason(e.target.value)}
            placeholder="Reason (optional)..."
            style={{
              flex: 1,
              minWidth: 150,
              padding: '10px 15px',
              borderRadius: 8,
              border: `1px solid ${mutedColor}30`,
              background: isDarkMode ? 'rgba(0,0,0,0.3)' : '#fff',
              color: textColor
            }}
          />
          <button
            onClick={handleAddWord}
            disabled={adding || !newWord.trim()}
            style={{
              background: adding ? 'rgba(239, 68, 68, 0.5)' : 'linear-gradient(135deg, #ef4444, #dc2626)',
              border: 'none',
              borderRadius: 8,
              padding: '10px 20px',
              color: '#fff',
              fontWeight: 600,
              cursor: adding ? 'wait' : 'pointer',
              display: 'flex',
              alignItems: 'center',
              gap: 6
            }}
            data-testid="add-ban-btn"
          >
            {adding ? '⏳ Adding...' : '🚫 Ban Word'}
          </button>
        </div>
        
        {/* Reserved Keywords Info */}
        <div style={{
          marginTop: 15,
          padding: 10,
          background: 'rgba(245, 158, 11, 0.1)',
          borderRadius: 8,
          border: '1px solid rgba(245, 158, 11, 0.3)'
        }}>
          <p style={{ color: '#f59e0b', margin: 0, fontSize: '0.8rem' }}>
            ⚠️ <strong>Reserved Keywords:</strong> The following cannot be banned because they are protocol syntax modifiers: 
            <code style={{ background: 'rgba(0,0,0,0.2)', padding: '2px 6px', borderRadius: 4, marginLeft: 5 }}>
              or, and, &amp;, (, ), +
            </code>
          </p>
        </div>
      </div>
      
      {/* Banned Words List */}
      <div style={{
        background: cardBg,
        borderRadius: 12,
        padding: 20,
        border: `1px solid ${mutedColor}20`
      }}>
        <h4 style={{ color: textColor, margin: '0 0 15px 0' }}>
          Banned List ({bannedWords.length} items)
        </h4>
        
        {bannedWords.length === 0 ? (
          <p style={{ color: mutedColor, textAlign: 'center', padding: 20 }}>
            No words are currently banned.
          </p>
        ) : (
          <div style={{ display: 'flex', flexDirection: 'column', gap: 10 }}>
            {bannedWords.map((item) => (
              <div
                key={item.id}
                style={{
                  display: 'flex',
                  justifyContent: 'space-between',
                  alignItems: 'center',
                  padding: 12,
                  background: isDarkMode ? 'rgba(0,0,0,0.2)' : 'rgba(255,255,255,0.5)',
                  borderRadius: 8,
                  border: '1px solid rgba(239, 68, 68, 0.2)'
                }}
                data-testid={`banned-word-${item.id}`}
              >
                <div>
                  <span style={{ 
                    color: '#ef4444', 
                    fontWeight: 600, 
                    fontSize: '1rem',
                    background: 'rgba(239, 68, 68, 0.1)',
                    padding: '4px 10px',
                    borderRadius: 6
                  }}>
                    🚫 {item.word}
                  </span>
                  {item.reason && (
                    <span style={{ color: mutedColor, marginLeft: 10, fontSize: '0.85rem' }}>
                      - {item.reason}
                    </span>
                  )}
                  <div style={{ color: mutedColor, fontSize: '0.75rem', marginTop: 4 }}>
                    Banned by {item.banned_by} on {new Date(item.created_at).toLocaleDateString()}
                  </div>
                </div>
                <button
                  onClick={() => handleRemoveWord(item.id, item.word)}
                  style={{
                    background: 'rgba(16, 185, 129, 0.2)',
                    border: '1px solid rgba(16, 185, 129, 0.3)',
                    borderRadius: 8,
                    padding: '8px 16px',
                    color: '#10b981',
                    fontWeight: 600,
                    cursor: 'pointer',
                    fontSize: '0.85rem'
                  }}
                >
                  ✓ Unban
                </button>
              </div>
            ))}
          </div>
        )}
      </div>
    </div>
  );
};

export default BannedWordsAdmin;
