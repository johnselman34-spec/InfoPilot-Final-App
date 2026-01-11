import React, { useState, useEffect } from 'react';
import { useAuth } from '../contexts/AuthContext';
import { API } from '../utils/api';
import { Icons } from '../components/shared';

const MessagesPage = ({ showToast }) => {
  const { token } = useAuth();
  const [friends, setFriends] = useState([]);
  const [selectedFriend, setSelectedFriend] = useState(null);
  const [messages, setMessages] = useState([]);
  const [newMessage, setNewMessage] = useState('');

  useEffect(() => {
    fetchFriends();
  }, []);

  const fetchFriends = async () => {
    try {
      const res = await fetch(`${API}/friends`, {
        headers: { Authorization: `Bearer ${token}` }
      });
      if (res.ok) {
        const data = await res.json();
        setFriends(data.friends || []);
      }
    } catch (e) {
      console.error('Failed to fetch friends:', e);
    }
  };

  const fetchMessages = async (friendId) => {
    try {
      const res = await fetch(`${API}/messages/${friendId}`, {
        headers: { Authorization: `Bearer ${token}` }
      });
      if (res.ok) {
        const data = await res.json();
        setMessages(data.messages || []);
      }
    } catch (e) {
      console.error('Failed to fetch messages:', e);
    }
  };

  const sendMessage = async () => {
    if (!newMessage.trim() || !selectedFriend) return;
    try {
      await fetch(`${API}/messages`, {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
          Authorization: `Bearer ${token}`
        },
        body: JSON.stringify({
          recipient_id: selectedFriend.id,
          content: newMessage
        })
      });
      setNewMessage('');
      fetchMessages(selectedFriend.id);
    } catch (e) {
      showToast('Failed to send message', 'error');
    }
  };

  return (
    <div className="messages-container" data-testid="messages-page">
      <div className="conversations-list">
        <h3 style={{ marginBottom: 15, color: '#f472b6' }}>Conversations</h3>
        {friends.length === 0 ? (
          <p style={{ color: '#a1a1aa', fontSize: '0.9rem' }}>
            Add friends to start messaging!
          </p>
        ) : (
          friends.map(friend => (
            <div
              key={friend.id}
              className={`conversation-item ${selectedFriend?.id === friend.id ? 'active' : ''}`}
              onClick={() => {
                setSelectedFriend(friend);
                fetchMessages(friend.id);
              }}
              data-testid={`friend-${friend.id}`}
            >
              <div className="post-avatar">{friend.username?.[0]?.toUpperCase()}</div>
              <div>
                <strong>{friend.username}</strong>
              </div>
            </div>
          ))
        )}
      </div>

      <div className="chat-area">
        {selectedFriend ? (
          <>
            <div style={{ padding: 15, borderBottom: '1px solid rgba(124, 58, 237, 0.2)' }}>
              <strong>{selectedFriend.username}</strong>
            </div>
            <div className="chat-messages">
              {messages.map(msg => (
                <div key={msg.id} className={`chat-message ${msg.is_mine ? 'sent' : 'received'}`}>
                  {msg.content}
                </div>
              ))}
            </div>
            <div className="chat-input">
              <input
                className="input-field"
                placeholder="Type a message..."
                value={newMessage}
                onChange={(e) => setNewMessage(e.target.value)}
                onKeyPress={(e) => e.key === 'Enter' && sendMessage()}
                data-testid="message-input"
              />
              <button className="btn btn-primary" onClick={sendMessage} data-testid="send-message-btn">
                <Icons.Send />
              </button>
            </div>
          </>
        ) : (
          <div style={{ display: 'flex', alignItems: 'center', justifyContent: 'center', height: '100%', color: '#a1a1aa' }}>
            Select a conversation to start messaging
          </div>
        )}
      </div>
    </div>
  );
};

export default MessagesPage;
