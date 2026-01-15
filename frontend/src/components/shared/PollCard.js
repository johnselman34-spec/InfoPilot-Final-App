import React, { useState } from 'react';
import { useAuth } from '../../contexts/AuthContext';
import { API } from '../../utils/api';

/**
 * PollCard Component
 * Displays a poll with voting functionality
 */
const PollCard = ({ poll, onVote, onDelete, showContext = true }) => {
  const { user, token } = useAuth();
  const [voting, setVoting] = useState(false);
  const [localPoll, setLocalPoll] = useState(poll);

  const handleVote = async (optionIndex) => {
    if (voting || localPoll.user_voted || localPoll.is_expired) return;
    
    setVoting(true);
    try {
      const res = await fetch(`${API}/polls/${localPoll.id}/vote`, {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
          Authorization: `Bearer ${token}`
        },
        body: JSON.stringify({ option_index: optionIndex })
      });
      
      if (res.ok) {
        const data = await res.json();
        // Update local state with response
        const updatedOptions = [...localPoll.options];
        updatedOptions[optionIndex] = {
          ...updatedOptions[optionIndex],
          vote_count: (updatedOptions[optionIndex].vote_count || 0) + 1,
          percentage: 0 // Will be recalculated
        };
        
        const newTotal = localPoll.total_votes + 1;
        updatedOptions.forEach(opt => {
          opt.percentage = newTotal > 0 ? Math.round((opt.vote_count / newTotal) * 100 * 10) / 10 : 0;
        });
        
        setLocalPoll({
          ...localPoll,
          options: updatedOptions,
          total_votes: newTotal,
          user_voted: true,
          user_voted_options: [optionIndex]
        });
        
        if (onVote) onVote(localPoll.id, optionIndex);
      }
    } catch (e) {
      console.error('Vote error:', e);
    } finally {
      setVoting(false);
    }
  };

  const handleDelete = async () => {
    if (!window.confirm('Delete this poll? All votes will be lost.')) return;
    
    try {
      const res = await fetch(`${API}/polls/${localPoll.id}`, {
        method: 'DELETE',
        headers: { Authorization: `Bearer ${token}` }
      });
      
      if (res.ok && onDelete) {
        onDelete(localPoll.id);
      }
    } catch (e) {
      console.error('Delete poll error:', e);
    }
  };

  const canDelete = user && (user.id === localPoll.created_by || user.is_admin);

  return (
    <div 
      className="card" 
      data-testid={`poll-${localPoll.id}`}
      style={{ 
        background: 'rgba(124, 58, 237, 0.1)', 
        border: '1px solid rgba(124, 58, 237, 0.3)',
        padding: 16
      }}
    >
      {/* Header */}
      <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'flex-start', marginBottom: 12 }}>
        <div>
          <div style={{ display: 'flex', alignItems: 'center', gap: 8 }}>
            <span style={{ fontSize: '1.2rem' }}>📊</span>
            <span style={{ fontWeight: 600, color: '#e2e8f0', fontSize: '1.1rem' }}>Poll</span>
          </div>
          {showContext && localPoll.creator_name && (
            <div style={{ fontSize: '0.75rem', color: '#71717a', marginTop: 4 }}>
              Created by {localPoll.creator_name}
            </div>
          )}
        </div>
        
        <div style={{ display: 'flex', alignItems: 'center', gap: 8 }}>
          {localPoll.is_expired && (
            <span style={{ 
              background: '#ef4444', 
              color: 'white', 
              fontSize: '0.7rem', 
              padding: '2px 8px', 
              borderRadius: 4 
            }}>
              ENDED
            </span>
          )}
          {canDelete && (
            <button
              onClick={handleDelete}
              style={{
                background: 'transparent',
                border: 'none',
                color: '#ef4444',
                cursor: 'pointer',
                fontSize: '0.85rem'
              }}
              data-testid={`delete-poll-${localPoll.id}`}
            >
              🗑️
            </button>
          )}
        </div>
      </div>

      {/* Question */}
      <h4 style={{ color: '#f0abfc', marginBottom: 12, fontSize: '1rem' }}>
        {localPoll.question}
      </h4>

      {/* Options */}
      <div style={{ display: 'flex', flexDirection: 'column', gap: 8 }}>
        {localPoll.options.map((option, idx) => {
          const isVoted = localPoll.user_voted_options?.includes(idx);
          const showResults = localPoll.user_voted || localPoll.is_expired;
          
          return (
            <button
              key={idx}
              onClick={() => handleVote(idx)}
              disabled={voting || localPoll.user_voted || localPoll.is_expired || !user}
              data-testid={`poll-option-${localPoll.id}-${idx}`}
              style={{
                position: 'relative',
                overflow: 'hidden',
                background: isVoted 
                  ? 'rgba(124, 58, 237, 0.3)' 
                  : 'rgba(255, 255, 255, 0.05)',
                border: isVoted 
                  ? '2px solid #7c3aed' 
                  : '1px solid rgba(255, 255, 255, 0.1)',
                borderRadius: 8,
                padding: '10px 14px',
                textAlign: 'left',
                color: '#e2e8f0',
                cursor: localPoll.user_voted || localPoll.is_expired ? 'default' : 'pointer',
                transition: 'all 0.2s'
              }}
            >
              {/* Progress bar background */}
              {showResults && (
                <div
                  style={{
                    position: 'absolute',
                    left: 0,
                    top: 0,
                    bottom: 0,
                    width: `${option.percentage || 0}%`,
                    background: isVoted 
                      ? 'rgba(124, 58, 237, 0.3)' 
                      : 'rgba(255, 255, 255, 0.05)',
                    transition: 'width 0.5s ease-out'
                  }}
                />
              )}
              
              {/* Option content */}
              <div style={{ position: 'relative', display: 'flex', justifyContent: 'space-between', alignItems: 'center' }}>
                <span>{option.text}</span>
                {showResults && (
                  <span style={{ 
                    fontSize: '0.85rem', 
                    color: isVoted ? '#a78bfa' : '#71717a',
                    fontWeight: isVoted ? 600 : 400
                  }}>
                    {option.vote_count || 0} ({option.percentage || 0}%)
                  </span>
                )}
              </div>
            </button>
          );
        })}
      </div>

      {/* Footer */}
      <div style={{ 
        marginTop: 12, 
        display: 'flex', 
        justifyContent: 'space-between', 
        alignItems: 'center',
        color: '#71717a',
        fontSize: '0.8rem'
      }}>
        <span>{localPoll.total_votes} vote{localPoll.total_votes !== 1 ? 's' : ''}</span>
        {localPoll.expires_at && !localPoll.is_expired && (
          <span>Ends {new Date(localPoll.expires_at).toLocaleDateString()}</span>
        )}
      </div>
    </div>
  );
};

/**
 * CreatePollModal Component
 * Modal for creating new polls
 */
export const CreatePollModal = ({ 
  isOpen, 
  onClose, 
  onSubmit, 
  parentType, 
  parentId 
}) => {
  const [question, setQuestion] = useState('');
  const [options, setOptions] = useState(['', '']);
  const [expiresInHours, setExpiresInHours] = useState(24);
  const [allowMultiple, setAllowMultiple] = useState(false);
  const [submitting, setSubmitting] = useState(false);

  const addOption = () => {
    if (options.length < 10) {
      setOptions([...options, '']);
    }
  };

  const removeOption = (idx) => {
    if (options.length > 2) {
      setOptions(options.filter((_, i) => i !== idx));
    }
  };

  const updateOption = (idx, value) => {
    const newOptions = [...options];
    newOptions[idx] = value;
    setOptions(newOptions);
  };

  const handleSubmit = async () => {
    if (!question.trim() || options.filter(o => o.trim()).length < 2) return;
    
    setSubmitting(true);
    try {
      await onSubmit({
        question: question.trim(),
        options: options.filter(o => o.trim()),
        expires_in_hours: expiresInHours,
        allow_multiple: allowMultiple,
        parent_type: parentType,
        parent_id: parentId
      });
      
      // Reset form
      setQuestion('');
      setOptions(['', '']);
      setExpiresInHours(24);
      setAllowMultiple(false);
      onClose();
    } finally {
      setSubmitting(false);
    }
  };

  if (!isOpen) return null;

  return (
    <div 
      className="modal-overlay"
      style={{
        position: 'fixed',
        top: 0,
        left: 0,
        right: 0,
        bottom: 0,
        background: 'rgba(0,0,0,0.8)',
        display: 'flex',
        alignItems: 'center',
        justifyContent: 'center',
        zIndex: 1000,
        padding: 20
      }}
      onClick={onClose}
    >
      <div 
        className="modal-content card"
        style={{
          maxWidth: 500,
          width: '100%',
          maxHeight: '80vh',
          overflow: 'auto'
        }}
        onClick={e => e.stopPropagation()}
        data-testid="create-poll-modal"
      >
        <h3 style={{ marginBottom: 20, color: '#f0abfc' }}>
          📊 Create Poll
        </h3>

        {/* Question */}
        <div style={{ marginBottom: 16 }}>
          <label style={{ display: 'block', marginBottom: 6, color: '#a1a1aa' }}>
            Question
          </label>
          <input
            type="text"
            value={question}
            onChange={e => setQuestion(e.target.value)}
            placeholder="What do you want to ask?"
            className="input"
            data-testid="poll-question-input"
            style={{ width: '100%' }}
          />
        </div>

        {/* Options */}
        <div style={{ marginBottom: 16 }}>
          <label style={{ display: 'block', marginBottom: 6, color: '#a1a1aa' }}>
            Options (2-10)
          </label>
          {options.map((opt, idx) => (
            <div key={idx} style={{ display: 'flex', gap: 8, marginBottom: 8 }}>
              <input
                type="text"
                value={opt}
                onChange={e => updateOption(idx, e.target.value)}
                placeholder={`Option ${idx + 1}`}
                className="input"
                data-testid={`poll-option-input-${idx}`}
                style={{ flex: 1 }}
              />
              {options.length > 2 && (
                <button
                  onClick={() => removeOption(idx)}
                  className="btn btn-secondary"
                  style={{ padding: '8px 12px' }}
                >
                  ✕
                </button>
              )}
            </div>
          ))}
          {options.length < 10 && (
            <button
              onClick={addOption}
              className="btn btn-secondary"
              style={{ fontSize: '0.85rem' }}
            >
              + Add Option
            </button>
          )}
        </div>

        {/* Duration */}
        <div style={{ marginBottom: 16 }}>
          <label style={{ display: 'block', marginBottom: 6, color: '#a1a1aa' }}>
            Poll Duration
          </label>
          <select
            value={expiresInHours}
            onChange={e => setExpiresInHours(Number(e.target.value))}
            className="input"
            data-testid="poll-duration-select"
          >
            <option value={1}>1 hour</option>
            <option value={6}>6 hours</option>
            <option value={24}>24 hours</option>
            <option value={72}>3 days</option>
            <option value={168}>7 days</option>
            <option value={0}>No expiration</option>
          </select>
        </div>

        {/* Actions */}
        <div style={{ display: 'flex', gap: 10, justifyContent: 'flex-end' }}>
          <button
            onClick={onClose}
            className="btn btn-secondary"
          >
            Cancel
          </button>
          <button
            onClick={handleSubmit}
            disabled={submitting || !question.trim() || options.filter(o => o.trim()).length < 2}
            className="btn btn-primary"
            data-testid="submit-poll-btn"
          >
            {submitting ? 'Creating...' : 'Create Poll'}
          </button>
        </div>
      </div>
    </div>
  );
};

export default PollCard;
