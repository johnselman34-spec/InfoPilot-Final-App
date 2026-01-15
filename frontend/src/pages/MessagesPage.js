import React, { useState, useEffect, useCallback, useRef } from 'react';
import { useAuth } from '../contexts/AuthContext';
import { API } from '../utils/api';

const MessagesPage = ({ showToast }) => {
  const { token, user } = useAuth();
  const [conversations, setConversations] = useState([]);
  const [activeConversation, setActiveConversation] = useState(null);
  const [messages, setMessages] = useState([]);
  const [newMessage, setNewMessage] = useState('');
  const [selectedImage, setSelectedImage] = useState(null);
  const [loading, setLoading] = useState(false);
  const [typing, setTyping] = useState(false);
  const messagesEndRef = useRef(null);
  const wsRef = useRef(null);

  const scrollToBottom = () => {
    messagesEndRef.current?.scrollIntoView({ behavior: 'smooth' });
  };

  const fetchConversations = useCallback(async () => {
    try {
      const res = await fetch(`${API}/dm/conversations`, {
        headers: { Authorization: `Bearer ${token}` }
      });
      if (res.ok) {
        const data = await res.json();
        setConversations(data.conversations || []);
      }
    } catch (e) {
      console.error('Error fetching conversations:', e);
    }
  }, [token]);

  const fetchMessages = useCallback(async (conversationId) => {
    try {
      const res = await fetch(`${API}/dm/conversations/${conversationId}/messages`, {
        headers: { Authorization: `Bearer ${token}` }
      });
      if (res.ok) {
        const data = await res.json();
        setMessages(data.messages || []);
        scrollToBottom();
      }
    } catch (e) {
      console.error('Error fetching messages:', e);
    }
  }, [token]);

  useEffect(() => {
    if (token) {
      fetchConversations();
    }
  }, [token, fetchConversations]);

  useEffect(() => {
    if (activeConversation) {
      fetchMessages(activeConversation.id);
    }
  }, [activeConversation, fetchMessages]);

  useEffect(() => {
    scrollToBottom();
  }, [messages]);

  const sendMessage = async () => {
    if (!newMessage.trim() && !selectedImage) return;
    if (!activeConversation) return;
    
    setLoading(true);
    
    try {
      const formData = new FormData();
      formData.append('content', newMessage);
      if (selectedImage) {
        formData.append('image', selectedImage);
      }
      
      const res = await fetch(`${API}/dm/conversations/${activeConversation.id}/messages`, {
        method: 'POST',
        headers: { Authorization: `Bearer ${token}` },
        body: formData
      });
      
      if (res.ok) {
        const data = await res.json();
        setMessages(prev => [...prev, {
          id: data.id,
          content: newMessage,
          image_url: data.image_url,
          sender_id: user?.id,
          is_mine: true,
          created_at: data.created_at
        }]);
        setNewMessage('');
        setSelectedImage(null);
        scrollToBottom();
        fetchConversations();
      }
    } catch (e) {
      showToast('Error sending message', 'error');
    } finally {
      setLoading(false);
    }
  };

  const selectConversation = (conv) => {
    setActiveConversation(conv);
    setMessages([]);
  };

  const handleImageSelect = (e) => {
    const file = e.target.files[0];
    if (file && file.size <= 6.9 * 1024 * 1024) {
      setSelectedImage(file);
    } else {
      showToast('Image exceeds 6.9MB limit', 'error');
    }
  };

  return (
    <div className="messages-page" data-testid="messages-page" style={{ height: 'calc(100vh - 200px)' }}>
      <h1 style={{ color: '#f472b6', marginBottom: 20 }}>Direct Messages</h1>
      
      <div style={{ display: 'grid', gridTemplateColumns: '300px 1fr', gap: 20, height: '100%', minHeight: 500 }}>
        {/* Conversations List */}
        <div className="card" style={{ height: '100%', overflow: 'auto' }}>
          <h3 style={{ color: '#a78bfa', marginBottom: 15 }}>Conversations</h3>
          
          {conversations.length === 0 ? (
            <p style={{ color: '#71717a', fontSize: '0.9rem' }}>
              No conversations yet. Start one from the Social page by adding friends!
            </p>
          ) : (
            <div style={{ display: 'flex', flexDirection: 'column', gap: 8 }}>
              {conversations.map(conv => (
                <div
                  key={conv.id}
                  onClick={() => selectConversation(conv)}
                  style={{
                    padding: 12,
                    background: activeConversation?.id === conv.id 
                      ? 'rgba(124, 58, 237, 0.2)' 
                      : 'rgba(255,255,255,0.03)',
                    borderRadius: 8,
                    cursor: 'pointer',
                    borderLeft: activeConversation?.id === conv.id 
                      ? '3px solid #7c3aed' 
                      : '3px solid transparent'
                  }}
                  data-testid={`conversation-${conv.id}`}
                >
                  <div style={{ display: 'flex', alignItems: 'center', gap: 10 }}>
                    <div style={{
                      width: 40,
                      height: 40,
                      borderRadius: '50%',
                      background: 'linear-gradient(135deg, #7c3aed, #f472b6)',
                      display: 'flex',
                      alignItems: 'center',
                      justifyContent: 'center',
                      color: 'white',
                      position: 'relative'
                    }}>
                      {conv.participant?.username?.[0]?.toUpperCase() || '?'}
                      {conv.participant?.is_online && (
                        <div style={{
                          position: 'absolute',
                          bottom: 0,
                          right: 0,
                          width: 10,
                          height: 10,
                          background: '#10b981',
                          borderRadius: '50%',
                          border: '2px solid #1e1b4b'
                        }} />
                      )}
                    </div>
                    <div style={{ flex: 1, minWidth: 0 }}>
                      <div style={{ 
                        fontWeight: 600, 
                        color: '#e2e8f0',
                        display: 'flex',
                        justifyContent: 'space-between'
                      }}>
                        <span>{conv.participant?.username}</span>
                        {conv.unread_count > 0 && (
                          <span style={{
                            background: '#ef4444',
                            color: 'white',
                            borderRadius: '50%',
                            padding: '2px 6px',
                            fontSize: '0.7rem'
                          }}>
                            {conv.unread_count}
                          </span>
                        )}
                      </div>
                      <div style={{ 
                        fontSize: '0.8rem', 
                        color: '#71717a',
                        overflow: 'hidden',
                        textOverflow: 'ellipsis',
                        whiteSpace: 'nowrap'
                      }}>
                        {conv.last_message || 'No messages yet'}
                      </div>
                    </div>
                  </div>
                </div>
              ))}
            </div>
          )}
        </div>
        
        {/* Chat Window */}
        <div className="card" style={{ 
          height: '100%', 
          display: 'flex', 
          flexDirection: 'column',
          padding: 0,
          minHeight: 500
        }}>
          {activeConversation ? (
            <>
              {/* Header */}
              <div style={{
                padding: 15,
                borderBottom: '1px solid rgba(124, 58, 237, 0.2)',
                display: 'flex',
                alignItems: 'center',
                gap: 10
              }}>
                <div style={{
                  width: 40,
                  height: 40,
                  borderRadius: '50%',
                  background: 'linear-gradient(135deg, #7c3aed, #f472b6)',
                  display: 'flex',
                  alignItems: 'center',
                  justifyContent: 'center',
                  color: 'white'
                }}>
                  {activeConversation.participant?.username?.[0]?.toUpperCase()}
                </div>
                <div>
                  <div style={{ fontWeight: 600, color: '#e2e8f0' }}>
                    {activeConversation.participant?.username}
                  </div>
                  <div style={{ fontSize: '0.75rem', color: '#71717a' }}>
                    {activeConversation.participant?.is_online ? 'Online' : 'Offline'}
                    {typing && <span style={{ color: '#a78bfa' }}> - typing...</span>}
                  </div>
                </div>
              </div>
              
              {/* Messages */}
              <div style={{ 
                flex: 1, 
                overflow: 'auto', 
                padding: 15,
                display: 'flex',
                flexDirection: 'column',
                gap: 10,
                minHeight: 300
              }}>
                {messages.length === 0 ? (
                  <div style={{ textAlign: 'center', color: '#71717a', marginTop: 50 }}>
                    No messages yet. Say hello!
                  </div>
                ) : (
                  messages.map((msg, idx) => (
                    <div
                      key={msg.id || idx}
                      style={{
                        alignSelf: msg.is_mine ? 'flex-end' : 'flex-start',
                        maxWidth: '70%'
                      }}
                    >
                      <div style={{
                        background: msg.is_mine 
                          ? 'linear-gradient(135deg, #7c3aed, #a78bfa)' 
                          : 'rgba(255,255,255,0.1)',
                        padding: '10px 15px',
                        borderRadius: msg.is_mine 
                          ? '18px 18px 4px 18px' 
                          : '18px 18px 18px 4px',
                        color: '#e2e8f0'
                      }}>
                        {msg.image_url && (
                          <img
                            src={`${API.replace('/api', '')}${msg.image_url}`}
                            alt="Shared"
                            style={{
                              maxWidth: '100%',
                              borderRadius: 8,
                              marginBottom: msg.content ? 8 : 0
                            }}
                          />
                        )}
                        {msg.content && <p style={{ margin: 0 }}>{msg.content}</p>}
                      </div>
                      <div style={{
                        fontSize: '0.65rem',
                        color: '#71717a',
                        marginTop: 4,
                        textAlign: msg.is_mine ? 'right' : 'left'
                      }}>
                        {new Date(msg.created_at).toLocaleTimeString()}
                        {msg.is_mine && msg.read && ' Read'}
                      </div>
                    </div>
                  ))
                )}
                <div ref={messagesEndRef} />
              </div>
              
              {/* Image Preview */}
              {selectedImage && (
                <div style={{ padding: '10px 15px', borderTop: '1px solid rgba(124, 58, 237, 0.2)' }}>
                  <div style={{ position: 'relative', display: 'inline-block' }}>
                    <img
                      src={URL.createObjectURL(selectedImage)}
                      alt="Preview"
                      style={{ height: 60, borderRadius: 8 }}
                    />
                    <button
                      onClick={() => setSelectedImage(null)}
                      style={{
                        position: 'absolute',
                        top: -5,
                        right: -5,
                        background: '#ef4444',
                        border: 'none',
                        borderRadius: '50%',
                        width: 20,
                        height: 20,
                        cursor: 'pointer',
                        color: 'white',
                        fontSize: '0.7rem'
                      }}
                    >
                      x
                    </button>
                  </div>
                </div>
              )}
              
              {/* Input */}
              <div style={{
                padding: 15,
                borderTop: '1px solid rgba(124, 58, 237, 0.2)',
                display: 'flex',
                gap: 10
              }}>
                <label style={{ cursor: 'pointer' }}>
                  <span className="btn btn-secondary">Image</span>
                  <input
                    type="file"
                    accept="image/*"
                    onChange={handleImageSelect}
                    style={{ display: 'none' }}
                  />
                </label>
                <input
                  type="text"
                  value={newMessage}
                  onChange={(e) => setNewMessage(e.target.value)}
                  onKeyPress={(e) => e.key === 'Enter' && sendMessage()}
                  placeholder="Type a message..."
                  className="form-input"
                  style={{ flex: 1 }}
                  data-testid="message-input"
                />
                <button
                  className="btn btn-primary"
                  onClick={sendMessage}
                  disabled={loading || (!newMessage.trim() && !selectedImage)}
                  data-testid="send-message-btn"
                >
                  {loading ? '...' : 'Send'}
                </button>
              </div>
            </>
          ) : (
            <div style={{ 
              flex: 1, 
              display: 'flex', 
              alignItems: 'center', 
              justifyContent: 'center',
              color: '#71717a',
              minHeight: 400
            }}>
              <div style={{ textAlign: 'center' }}>
                <div style={{ fontSize: '3rem', marginBottom: 10 }}>💬</div>
                <p>Select a conversation to start messaging</p>
              </div>
            </div>
          )}
        </div>
      </div>
    </div>
  );
};

export default MessagesPage;
