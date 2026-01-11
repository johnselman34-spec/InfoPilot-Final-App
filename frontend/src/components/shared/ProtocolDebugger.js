import React, { useState, useCallback } from 'react';
import { useAuth } from '../../contexts/AuthContext';
import { API } from '../../utils/api';

const ProtocolDebugger = ({ showToast }) => {
  const { token } = useAuth();
  const [protocol, setProtocol] = useState('');
  const [testText, setTestText] = useState('');
  const [debugResult, setDebugResult] = useState(null);
  const [loading, setLoading] = useState(false);

  const debugProtocol = useCallback(async () => {
    if (!protocol.trim()) {
      showToast('Please enter a protocol to debug', 'error');
      return;
    }

    setLoading(true);
    try {
      const res = await fetch(`${API}/protocol/debug`, {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
          Authorization: `Bearer ${token}`
        },
        body: JSON.stringify({ 
          protocol: protocol.trim(),
          test_text: testText.trim() || null
        })
      });

      if (res.ok) {
        const data = await res.json();
        setDebugResult(data);
      } else {
        const err = await res.json();
        showToast(err.detail || 'Failed to debug protocol', 'error');
      }
    } catch (e) {
      showToast('Failed to debug protocol', 'error');
    }
    setLoading(false);
  }, [protocol, testText, token, showToast]);

  const getModifierLabel = (modifier) => {
    switch (modifier) {
      case '+': return { label: 'INCLUDE ALL', color: '#10b981', desc: 'All words must be present' };
      case '^': return { label: 'EXCLUDE ALL', color: '#ef4444', desc: 'None of these words should appear' };
      default: return { label: 'OR', color: '#3b82f6', desc: 'At least one word must match' };
    }
  };

  const exampleProtocols = [
    { name: 'Basic OR', protocol: '(climate or weather or environment)' },
    { name: 'Include All', protocol: '(machine learning)+ & (python or javascript)' },
    { name: 'Exclude', protocol: '(technology news) & (spam or advertisement)^' },
    { name: 'Complex', protocol: '(George Bush or President Bush) & (aviation or pilot or "air force")+ & (scandal)^' }
  ];

  return (
    <div 
      style={{
        background: 'rgba(30, 20, 50, 0.5)',
        borderRadius: 16,
        padding: 20,
        marginBottom: 20,
        border: '1px solid rgba(124, 58, 237, 0.3)'
      }}
      data-testid="protocol-debugger"
    >
      <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', marginBottom: 15 }}>
        <h3 style={{ color: '#a78bfa', margin: 0, display: 'flex', alignItems: 'center', gap: 8 }}>
          🔧 Protocol Debugger
        </h3>
        <span style={{ color: '#6b7280', fontSize: '0.8rem' }}>
          Test your search protocols
        </span>
      </div>

      {/* Protocol Input */}
      <div style={{ marginBottom: 15 }}>
        <label style={{ color: '#a1a1aa', fontSize: '0.85rem', marginBottom: 5, display: 'block' }}>
          Protocol String:
        </label>
        <textarea
          className="input"
          placeholder="Enter protocol, e.g.: (word1 or word2) & (word3)+ & (word4)^"
          rows={2}
          value={protocol}
          onChange={(e) => setProtocol(e.target.value)}
          style={{ fontFamily: 'monospace', width: '100%' }}
          data-testid="protocol-debug-input"
        />
      </div>

      {/* Example Protocols */}
      <div style={{ marginBottom: 15 }}>
        <label style={{ color: '#71717a', fontSize: '0.75rem', marginBottom: 5, display: 'block' }}>
          Quick Examples:
        </label>
        <div style={{ display: 'flex', gap: 8, flexWrap: 'wrap' }}>
          {exampleProtocols.map((ex, idx) => (
            <button
              key={idx}
              onClick={() => setProtocol(ex.protocol)}
              style={{
                background: 'rgba(124, 58, 237, 0.2)',
                border: '1px solid rgba(124, 58, 237, 0.3)',
                borderRadius: 6,
                padding: '4px 10px',
                color: '#a78bfa',
                fontSize: '0.75rem',
                cursor: 'pointer'
              }}
            >
              {ex.name}
            </button>
          ))}
        </div>
      </div>

      {/* Test Text (Optional) */}
      <div style={{ marginBottom: 15 }}>
        <label style={{ color: '#a1a1aa', fontSize: '0.85rem', marginBottom: 5, display: 'block' }}>
          Test Text (optional - paste text to check if it matches):
        </label>
        <textarea
          className="input"
          placeholder="Paste article text here to test if it would match your protocol..."
          rows={3}
          value={testText}
          onChange={(e) => setTestText(e.target.value)}
          style={{ width: '100%' }}
          data-testid="protocol-test-text"
        />
      </div>

      {/* Debug Button */}
      <button
        className="btn btn-primary"
        onClick={debugProtocol}
        disabled={loading || !protocol.trim()}
        style={{ marginBottom: 15 }}
        data-testid="debug-protocol-btn"
      >
        {loading ? '🔄 Analyzing...' : '🔍 Analyze Protocol'}
      </button>

      {/* Debug Results */}
      {debugResult && (
        <div style={{
          background: 'rgba(0, 0, 0, 0.3)',
          borderRadius: 12,
          padding: 15,
          marginTop: 15
        }}>
          <h4 style={{ color: '#f472b6', marginBottom: 15, display: 'flex', alignItems: 'center', gap: 8 }}>
            📊 Analysis Results
            {debugResult.valid ? (
              <span style={{ color: '#10b981', fontSize: '0.8rem', background: 'rgba(16, 185, 129, 0.2)', padding: '2px 8px', borderRadius: 10 }}>
                ✓ Valid Protocol
              </span>
            ) : (
              <span style={{ color: '#ef4444', fontSize: '0.8rem', background: 'rgba(239, 68, 68, 0.2)', padding: '2px 8px', borderRadius: 10 }}>
                ✗ Invalid Protocol
              </span>
            )}
          </h4>

          {/* Parsed Groups */}
          <div style={{ marginBottom: 15 }}>
            <h5 style={{ color: '#a1a1aa', fontSize: '0.85rem', marginBottom: 10 }}>
              Parsed Groups ({debugResult.groups?.length || 0}):
            </h5>
            {debugResult.groups?.map((group, idx) => {
              const mod = getModifierLabel(group.modifier);
              return (
                <div 
                  key={idx}
                  style={{
                    background: 'rgba(30, 20, 50, 0.5)',
                    borderRadius: 8,
                    padding: 12,
                    marginBottom: 10,
                    borderLeft: `4px solid ${mod.color}`
                  }}
                >
                  <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', marginBottom: 8 }}>
                    <span style={{ color: mod.color, fontWeight: 600, fontSize: '0.85rem' }}>
                      Group {idx + 1}: {mod.label}
                    </span>
                    <span style={{ color: '#6b7280', fontSize: '0.75rem' }}>
                      {mod.desc}
                    </span>
                  </div>
                  <div style={{ display: 'flex', flexWrap: 'wrap', gap: 6 }}>
                    {group.items?.map((item, i) => (
                      <span
                        key={i}
                        style={{
                          background: `${mod.color}20`,
                          border: `1px solid ${mod.color}50`,
                          color: mod.color,
                          padding: '4px 10px',
                          borderRadius: 15,
                          fontSize: '0.8rem',
                          fontFamily: 'monospace'
                        }}
                      >
                        {item}
                      </span>
                    ))}
                  </div>
                  <div style={{ marginTop: 8, color: '#6b7280', fontSize: '0.75rem', fontFamily: 'monospace' }}>
                    Original: ({group.original})
                  </div>
                </div>
              );
            })}
          </div>

          {/* Test Result */}
          {debugResult.test_result !== undefined && (
            <div style={{
              background: debugResult.test_result 
                ? 'rgba(16, 185, 129, 0.1)' 
                : 'rgba(239, 68, 68, 0.1)',
              borderRadius: 8,
              padding: 15,
              border: `1px solid ${debugResult.test_result ? '#10b981' : '#ef4444'}50`
            }}>
              <h5 style={{ 
                color: debugResult.test_result ? '#10b981' : '#ef4444',
                marginBottom: 10,
                display: 'flex',
                alignItems: 'center',
                gap: 8
              }}>
                {debugResult.test_result ? '✅ Text MATCHES protocol' : '❌ Text does NOT match protocol'}
              </h5>
              
              {debugResult.match_details && (
                <div style={{ marginTop: 10 }}>
                  <p style={{ color: '#a1a1aa', fontSize: '0.85rem', marginBottom: 8 }}>
                    Match Details:
                  </p>
                  {debugResult.match_details.map((detail, idx) => (
                    <div key={idx} style={{ 
                      display: 'flex', 
                      alignItems: 'center', 
                      gap: 8,
                      marginBottom: 5,
                      fontSize: '0.8rem'
                    }}>
                      <span style={{ color: detail.matched ? '#10b981' : '#ef4444' }}>
                        {detail.matched ? '✓' : '✗'}
                      </span>
                      <span style={{ color: '#a1a1aa' }}>
                        Group {detail.group}: 
                      </span>
                      <span style={{ color: '#fff' }}>
                        {detail.matched_words?.join(', ') || 'No matches'}
                      </span>
                    </div>
                  ))}
                </div>
              )}
            </div>
          )}

          {/* Syntax Guide */}
          <div style={{
            marginTop: 15,
            padding: 12,
            background: 'rgba(59, 130, 246, 0.1)',
            borderRadius: 8,
            border: '1px solid rgba(59, 130, 246, 0.2)'
          }}>
            <h5 style={{ color: '#3b82f6', marginBottom: 8, fontSize: '0.85rem' }}>
              📖 Protocol Syntax Guide
            </h5>
            <ul style={{ color: '#a1a1aa', fontSize: '0.8rem', margin: 0, paddingLeft: 20, lineHeight: 1.8 }}>
              <li><code style={{ color: '#10b981' }}>(word1 or word2)</code> - Match ANY word (OR logic)</li>
              <li><code style={{ color: '#f472b6' }}>(word1 or word2)+</code> - ALL words must be present</li>
              <li><code style={{ color: '#ef4444' }}>(word1 or word2)^</code> - NONE of these words should appear</li>
              <li><code style={{ color: '#fbbf24' }}>&</code> - Combine multiple groups (AND between groups)</li>
              <li><code style={{ color: '#a78bfa' }}>"multi word phrase"</code> - Match exact phrase</li>
            </ul>
          </div>
        </div>
      )}
    </div>
  );
};

export default ProtocolDebugger;
