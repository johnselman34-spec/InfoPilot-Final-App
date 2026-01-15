import React, { useState, useCallback } from 'react';
import { API } from '../../utils/api';

/**
 * Protocol Search Input Component
 * Includes voice search capability with OpenAI Whisper
 */
const ProtocolSearchInput = ({ 
  value, 
  onChange, 
  onSearch, 
  token,
  placeholder = "Enter search query...",
  showToast
}) => {
  const [isRecording, setIsRecording] = useState(false);
  const [mediaRecorder, setMediaRecorder] = useState(null);

  const startRecording = useCallback(async () => {
    try {
      const stream = await navigator.mediaDevices.getUserMedia({ audio: true });
      const recorder = new MediaRecorder(stream);
      const chunks = [];

      recorder.ondataavailable = (e) => chunks.push(e.data);
      
      recorder.onstop = async () => {
        const blob = new Blob(chunks, { type: 'audio/webm' });
        stream.getTracks().forEach(track => track.stop());
        
        // Send to backend for transcription
        const formData = new FormData();
        formData.append('audio', blob, 'recording.webm');
        
        try {
          const res = await fetch(`${API}/search/voice`, {
            method: 'POST',
            headers: token ? { Authorization: `Bearer ${token}` } : {},
            body: formData
          });
          
          if (res.ok) {
            const data = await res.json();
            if (data.transcription) {
              onChange(data.transcription);
              showToast && showToast('Voice transcribed!', 'success');
            }
          } else {
            showToast && showToast('Voice transcription failed', 'error');
          }
        } catch (e) {
          console.error('Voice search error:', e);
          showToast && showToast('Voice search error', 'error');
        }
      };

      recorder.start();
      setMediaRecorder(recorder);
      setIsRecording(true);
      showToast && showToast('Recording... Speak now!', 'info');
    } catch (e) {
      console.error('Microphone access error:', e);
      showToast && showToast('Microphone access denied', 'error');
    }
  }, [token, onChange, showToast]);

  const stopRecording = useCallback(() => {
    if (mediaRecorder && isRecording) {
      mediaRecorder.stop();
      setIsRecording(false);
      setMediaRecorder(null);
    }
  }, [mediaRecorder, isRecording]);

  const handleKeyDown = (e) => {
    if (e.key === 'Enter' && !e.shiftKey) {
      e.preventDefault();
      onSearch && onSearch();
    }
  };

  return (
    <div style={{
      display: 'flex',
      gap: 10,
      marginBottom: 15
    }}>
      <div style={{ flex: 1, position: 'relative' }}>
        <input
          type="text"
          value={value}
          onChange={(e) => onChange(e.target.value)}
          onKeyDown={handleKeyDown}
          placeholder={placeholder}
          data-testid="search-input"
          style={{
            width: '100%',
            padding: '14px 50px 14px 16px',
            borderRadius: 12,
            border: '2px solid rgba(139, 92, 246, 0.3)',
            background: 'rgba(0,0,0,0.3)',
            color: '#fff',
            fontSize: '1rem',
            transition: 'all 0.2s'
          }}
        />
        
        {/* Voice Search Button */}
        <button
          onClick={isRecording ? stopRecording : startRecording}
          data-testid="voice-search-btn"
          style={{
            position: 'absolute',
            right: 8,
            top: '50%',
            transform: 'translateY(-50%)',
            background: isRecording 
              ? 'linear-gradient(135deg, #ef4444, #dc2626)' 
              : 'rgba(139, 92, 246, 0.3)',
            border: 'none',
            borderRadius: 8,
            padding: '8px 12px',
            cursor: 'pointer',
            color: '#fff',
            fontSize: '1rem',
            animation: isRecording ? 'pulse 1s ease-in-out infinite' : 'none'
          }}
          title={isRecording ? 'Stop Recording' : 'Voice Search'}
        >
          {isRecording ? '⏹️' : '🎤'}
        </button>
      </div>

      <button
        onClick={onSearch}
        data-testid="search-btn"
        style={{
          background: 'linear-gradient(135deg, #8b5cf6, #7c3aed)',
          border: 'none',
          borderRadius: 12,
          padding: '14px 28px',
          color: '#fff',
          fontWeight: 600,
          fontSize: '1rem',
          cursor: 'pointer',
          display: 'flex',
          alignItems: 'center',
          gap: 8,
          transition: 'all 0.2s'
        }}
      >
        🔍 Search
      </button>

      <style>{`
        @keyframes pulse {
          0%, 100% { opacity: 1; box-shadow: 0 0 0 0 rgba(239, 68, 68, 0.7); }
          50% { opacity: 0.8; box-shadow: 0 0 0 10px rgba(239, 68, 68, 0); }
        }
      `}</style>
    </div>
  );
};

export default ProtocolSearchInput;
