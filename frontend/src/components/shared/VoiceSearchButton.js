import React, { useState, useRef } from 'react';
import { useAuth } from '../contexts/AuthContext';
import { API } from '../utils/api';

const VoiceSearchButton = ({ onTranscription, showToast }) => {
  const { token } = useAuth();
  const [isRecording, setIsRecording] = useState(false);
  const [isProcessing, setIsProcessing] = useState(false);
  const mediaRecorderRef = useRef(null);
  const chunksRef = useRef([]);

  const startRecording = async () => {
    try {
      const stream = await navigator.mediaDevices.getUserMedia({ audio: true });
      
      mediaRecorderRef.current = new MediaRecorder(stream, {
        mimeType: 'audio/webm'
      });
      
      chunksRef.current = [];
      
      mediaRecorderRef.current.ondataavailable = (e) => {
        if (e.data.size > 0) {
          chunksRef.current.push(e.data);
        }
      };
      
      mediaRecorderRef.current.onstop = async () => {
        const audioBlob = new Blob(chunksRef.current, { type: 'audio/webm' });
        stream.getTracks().forEach(track => track.stop());
        await transcribeAudio(audioBlob);
      };
      
      mediaRecorderRef.current.start();
      setIsRecording(true);
      showToast('Recording... Click again to stop', 'info');
      
    } catch (err) {
      console.error('Microphone error:', err);
      showToast('Could not access microphone. Please allow microphone access.', 'error');
    }
  };

  const stopRecording = () => {
    if (mediaRecorderRef.current && isRecording) {
      mediaRecorderRef.current.stop();
      setIsRecording(false);
    }
  };

  const transcribeAudio = async (audioBlob) => {
    setIsProcessing(true);
    
    try {
      const formData = new FormData();
      formData.append('audio', audioBlob, 'recording.webm');
      
      const res = await fetch(`${API}/voice/transcribe`, {
        method: 'POST',
        headers: { Authorization: `Bearer ${token}` },
        body: formData
      });
      
      if (res.ok) {
        const data = await res.json();
        if (data.text) {
          onTranscription(data.text);
          showToast(`Transcribed: "${data.text}"`, 'success');
        } else {
          showToast('No speech detected. Please try again.', 'warning');
        }
      } else {
        const error = await res.json();
        showToast(error.detail || 'Transcription failed', 'error');
      }
    } catch (e) {
      console.error('Transcription error:', e);
      showToast('Voice search failed. Please try again.', 'error');
    } finally {
      setIsProcessing(false);
    }
  };

  const handleClick = () => {
    if (isProcessing) return;
    
    if (isRecording) {
      stopRecording();
    } else {
      startRecording();
    }
  };

  return (
    <button
      onClick={handleClick}
      disabled={isProcessing}
      className={`btn ${isRecording ? 'btn-danger' : 'btn-secondary'}`}
      style={{
        display: 'flex',
        alignItems: 'center',
        gap: 8,
        padding: '10px 16px',
        transition: 'all 0.2s',
        animation: isRecording ? 'pulse 1s infinite' : 'none'
      }}
      title={isRecording ? 'Click to stop recording' : 'Click to start voice search'}
      data-testid="voice-search-btn"
    >
      {isProcessing ? (
        <>
          <span className="spinner" style={{ width: 16, height: 16 }}></span>
          Processing...
        </>
      ) : isRecording ? (
        <>
          <span style={{ 
            width: 12, 
            height: 12, 
            background: '#ef4444', 
            borderRadius: '50%',
            animation: 'pulse 0.5s infinite'
          }}></span>
          Stop Recording
        </>
      ) : (
        <>
          <svg width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2">
            <path d="M12 1a3 3 0 0 0-3 3v8a3 3 0 0 0 6 0V4a3 3 0 0 0-3-3z"/>
            <path d="M19 10v2a7 7 0 0 1-14 0v-2"/>
            <line x1="12" y1="19" x2="12" y2="23"/>
            <line x1="8" y1="23" x2="16" y2="23"/>
          </svg>
          Voice Search
        </>
      )}
      
      <style>{`
        @keyframes pulse {
          0%, 100% { opacity: 1; }
          50% { opacity: 0.5; }
        }
        .btn-danger {
          background: linear-gradient(135deg, #ef4444, #dc2626) !important;
          border-color: #ef4444 !important;
        }
      `}</style>
    </button>
  );
};

export default VoiceSearchButton;
