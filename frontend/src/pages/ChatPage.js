import React, { useState, useEffect, useRef, useCallback } from 'react';
import { useAuth } from '../contexts/AuthContext';
import { API } from '../utils/api';
import { Icons } from '../components/shared';

const ChatPage = ({ showToast }) => {
  const { token, user } = useAuth();
  const [rooms, setRooms] = useState([]);
  const [activeRoom, setActiveRoom] = useState(null);
  const [messages, setMessages] = useState([]);
  const [newMessage, setNewMessage] = useState('');
  const [loading, setLoading] = useState(true);
  const [showNewRoomModal, setShowNewRoomModal] = useState(false);
  const [newRoomName, setNewRoomName] = useState('');
  const [typingUsers, setTypingUsers] = useState([]);
  const [onlineUsers, setOnlineUsers] = useState([]);
  
  const wsRef = useRef(null);
  const messagesEndRef = useRef(null);
  const typingTimeoutRef = useRef(null);

  const fetchRooms = useCallback(async () => {
    try {
      const res = await fetch(`${API}/chat/rooms`, {
        headers: { Authorization: `Bearer ${token}` }
      });
      if (res.ok) {
        const data = await res.json();
        setRooms(data.rooms || []);
      }
    } catch (e) {
      console.error('Failed to fetch rooms:', e);
    }
    setLoading(false);
  }, [token]);

  const fetchMessages = useCallback(async (roomId) => {
    try {
      const res = await fetch(`${API}/chat/rooms/${roomId}/messages`, {
        headers: { Authorization: `Bearer ${token}` }
      });
      if (res.ok) {
        const data = await res.json();
        setMessages(data.messages || []);
      }
    } catch (e) {
      console.error('Failed to fetch messages:', e);
    }
  }, [token]);

  const fetchOnlineUsers = useCallback(async () => {
    try {
      const res = await fetch(`${API}/chat/online`);
      if (res.ok) {
        const data = await res.json();
        setOnlineUsers(data.online_users || []);
      }
    } catch (e) {
      console.error('Failed to fetch online users:', e);
    }
  }, []);

  useEffect(() => {
    fetchRooms();
    fetchOnlineUsers();
    const interval = setInterval(fetchOnlineUsers, 30000);
    return () => clearInterval(interval);
  }, [fetchRooms, fetchOnlineUsers]);

  useEffect(() => {
    if (activeRoom) {
      fetchMessages(activeRoom.id);
      connectWebSocket(activeRoom.id);
    }
    return () => {
      if (wsRef.current) {
        wsRef.current.close();
      }
    };
  }, [activeRoom, fetchMessages, token]);

  useEffect(() => {
    messagesEndRef.current?.scrollIntoView({ behavior: 'smooth' });
  }, [messages]);

  const connectWebSocket = (roomId) => {
    if (wsRef.current) {
      wsRef.current.close();
    }

    const wsUrl = API.replace('https://', 'wss://').replace('http://', 'ws://');
    wsRef.current = new WebSocket(`${wsUrl}/chat/ws/${roomId}?token=${token}`);

    wsRef.current.onopen = () => {
      console.log('Chat WebSocket connected');
    };

    wsRef.current.onmessage = (event) => {
      const data = JSON.parse(event.data);
      
      if (data.type === 'message') {
        setMessages(prev => [...prev, {
          id: data.id,
          user_id: data.user_id,
          username: data.username,
          content: data.content,
          message_type: data.message_type,
          timestamp: data.timestamp,
          is_own: data.user_id === user?.id
        }]);
      } else if (data.type === 'typing') {
        if (data.is_typing) {
          setTypingUsers(prev => [...new Set([...prev, data.username])]);
        } else {
          setTypingUsers(prev => prev.filter(u => u !== data.username));
        }
      } else if (data.type === 'user_joined') {
        showToast(`${data.username} joined the chat`, 'info');
      } else if (data.type === 'user_left') {
        showToast(`${data.username} left the chat`, 'info');
      }
    };

    wsRef.current.onclose = () => {
      console.log('Chat WebSocket closed');
    };

    wsRef.current.onerror = (error) => {
      console.error('Chat WebSocket error:', error);
    };
  };

  const sendMessage = () => {
    if (!newMessage.trim() || !wsRef.current || wsRef.current.readyState !== WebSocket.OPEN) {
      return;
    }

    wsRef.current.send(JSON.stringify({
      type: 'message',
      content: newMessage,
      message_type: 'text'
    }));

    setNewMessage('');
  };

  const handleTyping = () => {
    if (!wsRef.current || wsRef.current.readyState !== WebSocket.OPEN) return;

    wsRef.current.send(JSON.stringify({
      type: 'typing',
      is_typing: true
    }));

    if (typingTimeoutRef.current) {
      clearTimeout(typingTimeoutRef.current);
    }

    typingTimeoutRef.current = setTimeout(() => {
      if (wsRef.current && wsRef.current.readyState === WebSocket.OPEN) {
        wsRef.current.send(JSON.stringify({
          type: 'typing',
          is_typing: false
        }));
      }
    }, 2000);
  };

  const createRoom = async () => {
    if (!newRoomName.trim()) {
      showToast('Please enter a room name', 'error');
      return;
    }

    try {
      const res = await fetch(`${API}/chat/rooms`, {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
          Authorization: `Bearer ${token}`
        },
        body: JSON.stringify({
          name: newRoomName,
          room_type: 'group',
          member_ids: []
        })
      });

      if (res.ok) {
        const data = await res.json();
        showToast('Room created!', 'success');
        setShowNewRoomModal(false);
        setNewRoomName('');
        fetchRooms();
        setActiveRoom({ id: data.id, name: data.name });
      } else {
        showToast('Failed to create room', 'error');
      }
    } catch (e) {
      showToast('Failed to create room', 'error');
    }
  };

  return (
    <div className="card" data-testid="chat-page" style={{ height: 'calc(100vh - 200px)', display: 'flex', flexDirection: 'column' }}>
      <div className="card-header">
        <h2 style={{ display: 'flex', alignItems: 'center', gap: 10 }}>
          💬 Real-Time Chat
          <span style={{ fontSize: '0.8rem', color: '#10b981', fontWeight: 400 }}>
            {onlineUsers.length} online
          </span>
        </h2>
      </div>

      <div style={{ display: 'flex', flex: 1, gap: 20, overflow: 'hidden' }}>
        {/* Rooms Sidebar */}
        <div style={{
          width: 280,
          background: 'rgba(30, 20, 50, 0.5)',
          borderRadius: 12,
          padding: 15,
          display: 'flex',
          flexDirection: 'column',
          overflow: 'hidden'
        }}>
          <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', marginBottom: 15 }}>
            <h3 style={{ color: '#f472b6', margin: 0 }}>Chat Rooms</h3>
            <button
              className="btn btn-primary"
              style={{ padding: '6px 12px', fontSize: '0.8rem' }}
              onClick={() => setShowNewRoomModal(true)}
            >
              + New
            </button>
          </div>

          <div style={{ flex: 1, overflowY: 'auto' }}>
            {loading ? (
              <p style={{ color: '#a1a1aa', textAlign: 'center' }}>Loading...</p>
            ) : rooms.length === 0 ? (
              <p style={{ color: '#a1a1aa', textAlign: 'center', fontSize: '0.9rem' }}>
                No chat rooms yet. Create one!
              </p>
            ) : (
              rooms.map(room => (
                <div
                  key={room.id}
                  onClick={() => setActiveRoom(room)}
                  style={{
                    background: activeRoom?.id === room.id 
                      ? 'linear-gradient(135deg, rgba(124, 58, 237, 0.3), rgba(244, 114, 182, 0.2))'
                      : 'rgba(0,0,0,0.2)',
                    padding: 12,
                    borderRadius: 10,
                    marginBottom: 10,
                    cursor: 'pointer',
                    border: activeRoom?.id === room.id ? '1px solid #7c3aed' : '1px solid transparent',
                    transition: 'all 0.2s'
                  }}
                >
                  <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center' }}>
                    <span style={{ color: '#fff', fontWeight: 600 }}>{room.name}</span>
                    {room.unread_count > 0 && (
                      <span style={{
                        background: '#f472b6',
                        color: '#fff',
                        padding: '2px 8px',
                        borderRadius: 10,
                        fontSize: '0.7rem',
                        fontWeight: 700
                      }}>
                        {room.unread_count}
                      </span>
                    )}
                  </div>
                  <div style={{ color: '#a1a1aa', fontSize: '0.75rem', marginTop: 4 }}>
                    {room.member_count} members • {room.online_count || 0} online
                  </div>
                  {room.last_message && (
                    <div style={{ color: '#71717a', fontSize: '0.75rem', marginTop: 4, overflow: 'hidden', textOverflow: 'ellipsis', whiteSpace: 'nowrap' }}>
                      <strong>{room.last_message.username}:</strong> {room.last_message.content}
                    </div>
                  )}
                </div>
              ))
            )}
          </div>

          {/* Online Users */}
          <div style={{ marginTop: 15, paddingTop: 15, borderTop: '1px solid rgba(124, 58, 237, 0.3)' }}>
            <h4 style={{ color: '#10b981', fontSize: '0.85rem', marginBottom: 10 }}>🟢 Online Now</h4>
            <div style={{ maxHeight: 100, overflowY: 'auto' }}>
              {onlineUsers.slice(0, 5).map(u => (
                <div key={u.id} style={{ 
                  display: 'flex', 
                  alignItems: 'center', 
                  gap: 8, 
                  marginBottom: 6,
                  fontSize: '0.8rem',
                  color: '#a1a1aa'
                }}>
                  <span style={{ width: 8, height: 8, borderRadius: '50%', background: '#10b981' }} />
                  {u.callsign || u.username}
                </div>
              ))}
              {onlineUsers.length > 5 && (
                <div style={{ color: '#71717a', fontSize: '0.75rem' }}>
                  +{onlineUsers.length - 5} more
                </div>
              )}
            </div>
          </div>
        </div>

        {/* Chat Area */}
        <div style={{
          flex: 1,
          display: 'flex',
          flexDirection: 'column',
          background: 'rgba(30, 20, 50, 0.3)',
          borderRadius: 12,
          overflow: 'hidden'
        }}>
          {activeRoom ? (
            <>
              {/* Chat Header */}
              <div style={{
                padding: 15,
                background: 'rgba(124, 58, 237, 0.2)',
                borderBottom: '1px solid rgba(124, 58, 237, 0.3)'
              }}>
                <h3 style={{ color: '#fff', margin: 0 }}>{activeRoom.name}</h3>
                <span style={{ color: '#a1a1aa', fontSize: '0.8rem' }}>
                  {activeRoom.member_count} members
                </span>
              </div>

              {/* Messages */}
              <div style={{ flex: 1, overflowY: 'auto', padding: 15 }}>
                {messages.map((msg, i) => (
                  <div
                    key={msg.id || i}
                    style={{
                      display: 'flex',
                      flexDirection: msg.is_own ? 'row-reverse' : 'row',
                      marginBottom: 15
                    }}
                  >
                    <div style={{
                      maxWidth: '70%',
                      background: msg.is_own 
                        ? 'linear-gradient(135deg, #7c3aed, #a78bfa)'
                        : 'rgba(0,0,0,0.3)',
                      padding: '10px 15px',
                      borderRadius: msg.is_own ? '15px 15px 0 15px' : '15px 15px 15px 0'
                    }}>
                      {!msg.is_own && (
                        <div style={{ color: '#f472b6', fontSize: '0.75rem', fontWeight: 600, marginBottom: 4 }}>
                          {msg.username}
                        </div>
                      )}
                      <div style={{ color: '#fff' }}>{msg.content}</div>
                      <div style={{ color: 'rgba(255,255,255,0.5)', fontSize: '0.65rem', marginTop: 4, textAlign: msg.is_own ? 'right' : 'left' }}>
                        {new Date(msg.timestamp).toLocaleTimeString()}
                      </div>
                    </div>
                  </div>
                ))}
                <div ref={messagesEndRef} />
              </div>

              {/* Typing Indicator */}
              {typingUsers.length > 0 && (
                <div style={{ padding: '5px 15px', color: '#a1a1aa', fontSize: '0.8rem', fontStyle: 'italic' }}>
                  {typingUsers.join(', ')} {typingUsers.length === 1 ? 'is' : 'are'} typing...
                </div>
              )}

              {/* Message Input */}
              <div style={{ padding: 15, background: 'rgba(0,0,0,0.2)', display: 'flex', gap: 10 }}>
                <input
                  className="input-field"
                  placeholder="Type a message..."
                  value={newMessage}
                  onChange={(e) => {
                    setNewMessage(e.target.value);
                    handleTyping();
                  }}
                  onKeyPress={(e) => e.key === 'Enter' && sendMessage()}
                  style={{ flex: 1 }}
                  data-testid="chat-input"
                />
                <button
                  className="btn btn-primary"
                  onClick={sendMessage}
                  disabled={!newMessage.trim()}
                  data-testid="send-message-btn"
                >
                  Send
                </button>
              </div>
            </>
          ) : (
            <div style={{ flex: 1, display: 'flex', alignItems: 'center', justifyContent: 'center', flexDirection: 'column' }}>
              <div style={{ fontSize: '4rem', marginBottom: 20 }}>💬</div>
              <h3 style={{ color: '#a1a1aa' }}>Select a room to start chatting</h3>
              <p style={{ color: '#71717a', fontSize: '0.9rem' }}>or create a new room</p>
            </div>
          )}
        </div>
      </div>

      {/* New Room Modal */}
      {showNewRoomModal && (
        <div className="modal-overlay" onClick={() => setShowNewRoomModal(false)}>
          <div className="modal" onClick={e => e.stopPropagation()} style={{ maxWidth: 400 }}>
            <div className="modal-header">
              <h2>Create Chat Room</h2>
              <button className="modal-close" onClick={() => setShowNewRoomModal(false)}>×</button>
            </div>
            <div style={{ padding: 20 }}>
              <input
                className="input-field"
                placeholder="Room Name"
                value={newRoomName}
                onChange={(e) => setNewRoomName(e.target.value)}
                style={{ marginBottom: 15 }}
                data-testid="new-room-name-input"
              />
              <button
                className="btn btn-primary"
                onClick={createRoom}
                style={{ width: '100%' }}
                data-testid="create-room-btn"
              >
                Create Room
              </button>
            </div>
          </div>
        </div>
      )}
    </div>
  );
};

export default ChatPage;
