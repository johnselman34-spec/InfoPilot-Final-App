import React, { useState, useEffect, useRef, useCallback } from 'react';
import { Navigate } from 'react-router-dom';
import { useQuery, useMutation, useQueryClient } from '@tanstack/react-query';
import axios from 'axios';
import { io } from 'socket.io-client';
import { MessageCircle, Plus, Send, Users, Wifi, WifiOff, User } from 'lucide-react';
import { useAuth } from '../context/AuthContext';
import { useToast } from '../context/ToastContext';
import { API } from '../utils/api';
import StarsBackground from '../components/StarsBackground';
import { Card } from '../components/ui/card';
import { Button } from '../components/ui/button';
import { Input } from '../components/ui/input';
import { Badge } from '../components/ui/badge';
import { Dialog, DialogContent, DialogHeader, DialogTitle, DialogFooter } from '../components/ui/dialog';
import { Label } from '../components/ui/label';

const SOCKET_URL = process.env.REACT_APP_BACKEND_URL?.replace('/api', '').replace('https://', 'wss://').replace('http://', 'ws://') || '';

const ChatPage = () => {
  const { user, token } = useAuth();
  const showToast = useToast();
  const queryClient = useQueryClient();
  const [selectedRoom, setSelectedRoom] = useState(null);
  const [message, setMessage] = useState("");
  const [messages, setMessages] = useState([]);
  const [showCreate, setShowCreate] = useState(false);
  const [newRoom, setNewRoom] = useState({ name: "", description: "" });
  const [isConnected, setIsConnected] = useState(false);
  const [onlineUsers, setOnlineUsers] = useState([]);
  const [typingUsers, setTypingUsers] = useState([]);
  const messagesEndRef = useRef(null);
  const socketRef = useRef(null);
  const typingTimeoutRef = useRef(null);

  // Fetch rooms
  const { data: roomsData } = useQuery({
    queryKey: ["chat-rooms"],
    queryFn: () => axios.get(`${API}/chat/rooms`).then(r => r.data),
    enabled: !!user
  });

  // Create room mutation
  const createRoomMutation = useMutation({
    mutationFn: (room) => axios.post(`${API}/chat/rooms`, room),
    onSuccess: () => {
      showToast("Room created!", "success");
      queryClient.invalidateQueries(["chat-rooms"]);
      setShowCreate(false);
      setNewRoom({ name: "", description: "" });
    }
  });

  // Initialize Socket.IO connection
  useEffect(() => {
    if (!user || !token) return;

    // Use the same base URL as API but with /api/ws path for WebSocket
    const wsUrl = process.env.REACT_APP_BACKEND_URL?.replace('/api', '') || '';
    
    socketRef.current = io(wsUrl, {
      path: '/api/ws/socket.io',
      auth: { token },
      transports: ['websocket', 'polling'],
      reconnection: true,
      reconnectionAttempts: 5,
      reconnectionDelay: 1000
    });

    const socket = socketRef.current;

    socket.on('connect', () => {
      console.log('Socket connected');
      setIsConnected(true);
      showToast("Connected to chat", "success");
    });

    socket.on('disconnect', () => {
      console.log('Socket disconnected');
      setIsConnected(false);
    });

    socket.on('connect_error', (error) => {
      console.error('Socket connection error:', error);
      setIsConnected(false);
    });

    socket.on('new_message', (msg) => {
      setMessages(prev => [...prev, msg]);
    });

    socket.on('user_joined', (data) => {
      showToast(`${data.username} joined the room`, "info");
      setOnlineUsers(prev => {
        if (!prev.find(u => u.user_id === data.user_id)) {
          return [...prev, { user_id: data.user_id, username: data.username }];
        }
        return prev;
      });
    });

    socket.on('user_left', (data) => {
      setOnlineUsers(prev => prev.filter(u => u.user_id !== data.user_id));
    });

    socket.on('user_typing', (data) => {
      if (data.is_typing) {
        setTypingUsers(prev => {
          if (!prev.includes(data.username)) {
            return [...prev, data.username];
          }
          return prev;
        });
        // Auto-remove after 3 seconds
        setTimeout(() => {
          setTypingUsers(prev => prev.filter(u => u !== data.username));
        }, 3000);
      } else {
        setTypingUsers(prev => prev.filter(u => u !== data.username));
      }
    });

    return () => {
      socket.disconnect();
    };
  }, [user, token, showToast]);

  // Scroll to bottom when new messages arrive
  useEffect(() => {
    messagesEndRef.current?.scrollIntoView({ behavior: 'smooth' });
  }, [messages]);

  // Join room handler
  const handleJoinRoom = useCallback(async (roomId) => {
    if (!socketRef.current?.connected) {
      showToast("Not connected to chat server", "error");
      return;
    }

    setSelectedRoom(roomId);
    setMessages([]);
    setOnlineUsers([]);

    socketRef.current.emit('join_room', { room_id: roomId }, (response) => {
      if (response?.success) {
        setMessages(response.messages || []);
        showToast("Joined room", "success");
        
        // Get online users
        socketRef.current.emit('get_online_users', { room_id: roomId }, (usersResponse) => {
          setOnlineUsers(usersResponse?.users || []);
        });
      } else {
        showToast(response?.error || "Failed to join room", "error");
      }
    });
  }, [showToast]);

  // Send message handler
  const handleSendMessage = useCallback(() => {
    if (!message.trim() || !selectedRoom || !socketRef.current?.connected) return;

    socketRef.current.emit('send_message', {
      room_id: selectedRoom,
      content: message.trim()
    }, (response) => {
      if (!response?.success) {
        showToast(response?.error || "Failed to send message", "error");
      }
    });

    setMessage("");
  }, [message, selectedRoom, showToast]);

  // Typing indicator
  const handleTyping = useCallback(() => {
    if (!selectedRoom || !socketRef.current?.connected) return;

    socketRef.current.emit('typing', { room_id: selectedRoom, is_typing: true });

    // Clear previous timeout
    if (typingTimeoutRef.current) {
      clearTimeout(typingTimeoutRef.current);
    }

    // Stop typing indicator after 2 seconds of inactivity
    typingTimeoutRef.current = setTimeout(() => {
      socketRef.current?.emit('typing', { room_id: selectedRoom, is_typing: false });
    }, 2000);
  }, [selectedRoom]);

  if (!user) return <Navigate to="/login" />;

  const rooms = roomsData?.rooms || [];
  const currentRoom = rooms.find(r => r.id === selectedRoom);

  return (
    <div className="min-h-screen pt-20 px-4">
      <StarsBackground />
      <div className="max-w-6xl mx-auto">
        <div className="flex items-center justify-between mb-8">
          <div className="flex items-center gap-4">
            <h1 className="text-3xl font-bold text-gradient-gold">Chat Rooms</h1>
            <Badge className={`${isConnected ? 'bg-green-500/20 text-green-300' : 'bg-red-500/20 text-red-300'}`} data-testid="connection-status">
              {isConnected ? <><Wifi size={14} className="mr-1" /> Connected</> : <><WifiOff size={14} className="mr-1" /> Disconnected</>}
            </Badge>
          </div>
          <Button onClick={() => setShowCreate(true)} className="btn-gold" data-testid="create-chat-room-btn">
            <Plus className="mr-2" /> Create Room
          </Button>
        </div>

        <div className="grid md:grid-cols-4 gap-6">
          {/* Rooms List */}
          <div className="md:col-span-1">
            <Card className="card-glass p-4">
              <h3 className="text-lg font-bold text-white mb-4">Rooms</h3>
              <div className="space-y-2">
                {rooms.map(room => (
                  <div
                    key={room.id}
                    onClick={() => handleJoinRoom(room.id)}
                    className={`p-3 rounded-lg cursor-pointer transition ${selectedRoom === room.id ? 'bg-yellow-400/20 border border-yellow-400/50' : 'bg-white/5 hover:bg-white/10'}`}
                    data-testid={`chat-room-${room.id}`}
                  >
                    <p className="text-white font-semibold">{room.name}</p>
                    <div className="flex items-center gap-2 mt-1">
                      <Badge className="text-xs bg-white/10">
                        <Users size={10} className="mr-1" /> {room.members?.length || 0}
                      </Badge>
                    </div>
                  </div>
                ))}
                {rooms.length === 0 && <p className="text-white/60 text-sm">No rooms yet</p>}
              </div>
            </Card>
          </div>

          {/* Chat Area */}
          <div className="md:col-span-2">
            <Card className="card-glass p-4 h-[600px] flex flex-col">
              {selectedRoom ? (
                <>
                  {/* Room Header */}
                  <div className="flex items-center justify-between pb-3 border-b border-white/10 mb-3">
                    <div>
                      <h4 className="text-white font-semibold">{currentRoom?.name || 'Chat Room'}</h4>
                      {typingUsers.length > 0 && (
                        <p className="text-yellow-400 text-xs animate-pulse">
                          {typingUsers.join(', ')} {typingUsers.length === 1 ? 'is' : 'are'} typing...
                        </p>
                      )}
                    </div>
                    <Badge className="bg-green-500/20 text-green-300">
                      {onlineUsers.length} online
                    </Badge>
                  </div>

                  {/* Messages */}
                  <div className="flex-1 overflow-y-auto mb-4 space-y-3" data-testid="messages-container">
                    {messages.map(m => (
                      <div 
                        key={m.id} 
                        className={`p-3 rounded-lg max-w-[80%] ${m.user_id === user.id ? 'bg-yellow-400/20 ml-auto' : 'bg-white/5'}`}
                        data-testid={`message-${m.id}`}
                      >
                        <div className="flex items-center gap-2 mb-1">
                          <span className="text-yellow-400 text-xs font-semibold">{m.username}</span>
                          <span className="text-white/40 text-xs">
                            {new Date(m.created_at).toLocaleTimeString([], { hour: '2-digit', minute: '2-digit' })}
                          </span>
                        </div>
                        <p className="text-white">{m.content}</p>
                      </div>
                    ))}
                    {messages.length === 0 && (
                      <p className="text-white/60 text-center py-8">No messages yet. Start the conversation!</p>
                    )}
                    <div ref={messagesEndRef} />
                  </div>

                  {/* Message Input */}
                  <div className="flex gap-2">
                    <Input 
                      className="form-input flex-1" 
                      placeholder="Type a message..." 
                      value={message} 
                      onChange={e => { setMessage(e.target.value); handleTyping(); }}
                      onKeyDown={e => e.key === 'Enter' && !e.shiftKey && handleSendMessage()}
                      disabled={!isConnected}
                      data-testid="chat-message-input" 
                    />
                    <Button 
                      onClick={handleSendMessage} 
                      className="btn-gold" 
                      disabled={!message.trim() || !isConnected}
                      data-testid="send-message-btn"
                    >
                      <Send size={18} />
                    </Button>
                  </div>
                </>
              ) : (
                <div className="flex-1 flex items-center justify-center">
                  <div className="text-center">
                    <MessageCircle className="mx-auto text-white/30 mb-4" size={48} />
                    <p className="text-white/60">Select a room to start chatting</p>
                    <p className="text-white/40 text-sm mt-2">Real-time messaging powered by WebSocket</p>
                  </div>
                </div>
              )}
            </Card>
          </div>

          {/* Online Users */}
          <div className="md:col-span-1">
            <Card className="card-glass p-4">
              <h3 className="text-lg font-bold text-white mb-4 flex items-center gap-2">
                <Users size={18} className="text-green-400" /> Online
              </h3>
              {selectedRoom ? (
                <div className="space-y-2">
                  {onlineUsers.map(u => (
                    <div key={u.user_id} className="flex items-center gap-2 p-2 bg-white/5 rounded-lg">
                      <div className="w-2 h-2 bg-green-400 rounded-full animate-pulse" />
                      <User size={14} className="text-white/50" />
                      <span className="text-white/80 text-sm">{u.username}</span>
                      {u.user_id === user.id && <Badge className="text-xs bg-yellow-400/20 text-yellow-300">You</Badge>}
                    </div>
                  ))}
                  {onlineUsers.length === 0 && (
                    <p className="text-white/60 text-sm">No users online</p>
                  )}
                </div>
              ) : (
                <p className="text-white/60 text-sm">Select a room to see online users</p>
              )}
            </Card>
          </div>
        </div>

        {/* Create Room Dialog */}
        <Dialog open={showCreate} onOpenChange={setShowCreate}>
          <DialogContent className="bg-slate-900 border-yellow-400/30">
            <DialogHeader>
              <DialogTitle className="text-yellow-400">Create Chat Room</DialogTitle>
            </DialogHeader>
            <div className="space-y-4 py-4">
              <div>
                <Label className="text-white">Room Name</Label>
                <Input className="form-input mt-1" value={newRoom.name} onChange={e => setNewRoom({...newRoom, name: e.target.value})} data-testid="room-name-input" />
              </div>
              <div>
                <Label className="text-white">Description</Label>
                <Input className="form-input mt-1" value={newRoom.description} onChange={e => setNewRoom({...newRoom, description: e.target.value})} />
              </div>
            </div>
            <DialogFooter>
              <Button variant="outline" onClick={() => setShowCreate(false)}>Cancel</Button>
              <Button className="btn-gold" onClick={() => createRoomMutation.mutate(newRoom)} disabled={!newRoom.name} data-testid="create-room-submit">Create</Button>
            </DialogFooter>
          </DialogContent>
        </Dialog>
      </div>
    </div>
  );
};

export default ChatPage;
