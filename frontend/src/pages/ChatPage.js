import React, { useState } from 'react';
import { Navigate } from 'react-router-dom';
import { useQuery, useMutation, useQueryClient } from '@tanstack/react-query';
import axios from 'axios';
import { MessageCircle, Plus, Send, Users } from 'lucide-react';
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

const ChatPage = () => {
  const { user } = useAuth();
  const showToast = useToast();
  const queryClient = useQueryClient();
  const [selectedRoom, setSelectedRoom] = useState(null);
  const [message, setMessage] = useState("");
  const [showCreate, setShowCreate] = useState(false);
  const [newRoom, setNewRoom] = useState({ name: "", description: "" });

  const { data: roomsData } = useQuery({
    queryKey: ["chat-rooms"],
    queryFn: () => axios.get(`${API}/chat/rooms`).then(r => r.data),
    enabled: !!user
  });

  const { data: messagesData, refetch: refetchMessages } = useQuery({
    queryKey: ["messages", selectedRoom],
    queryFn: () => axios.get(`${API}/chat/rooms/${selectedRoom}/messages`).then(r => r.data),
    enabled: !!selectedRoom,
    refetchInterval: 3000
  });

  const createRoomMutation = useMutation({
    mutationFn: (room) => axios.post(`${API}/chat/rooms`, room),
    onSuccess: () => {
      showToast("Room created!", "success");
      queryClient.invalidateQueries(["chat-rooms"]);
      setShowCreate(false);
      setNewRoom({ name: "", description: "" });
    }
  });

  const sendMessageMutation = useMutation({
    mutationFn: (content) => axios.post(`${API}/chat/rooms/${selectedRoom}/message`, { content }),
    onSuccess: () => {
      setMessage("");
      refetchMessages();
    }
  });

  if (!user) return <Navigate to="/login" />;

  const rooms = roomsData?.rooms || [];
  const messages = messagesData?.messages || [];

  return (
    <div className="min-h-screen pt-20 px-4">
      <StarsBackground />
      <div className="max-w-6xl mx-auto">
        <div className="flex items-center justify-between mb-8">
          <h1 className="text-3xl font-bold text-gradient-gold">Chat Rooms</h1>
          <Button onClick={() => setShowCreate(true)} className="btn-gold" data-testid="create-chat-room-btn">
            <Plus className="mr-2" /> Create Room
          </Button>
        </div>

        <div className="grid md:grid-cols-3 gap-6">
          <div className="md:col-span-1">
            <Card className="card-glass p-4">
              <h3 className="text-lg font-bold text-white mb-4">Rooms</h3>
              <div className="space-y-2">
                {rooms.map(room => (
                  <div
                    key={room.id}
                    onClick={() => setSelectedRoom(room.id)}
                    className={`p-3 rounded-lg cursor-pointer transition ${selectedRoom === room.id ? 'bg-yellow-400/20' : 'bg-white/5 hover:bg-white/10'}`}
                    data-testid={`chat-room-${room.id}`}
                  >
                    <p className="text-white font-semibold">{room.name}</p>
                    <Badge className="text-xs">{room.members?.length || 0} members</Badge>
                  </div>
                ))}
                {rooms.length === 0 && <p className="text-white/60 text-sm">No rooms yet</p>}
              </div>
            </Card>
          </div>

          <div className="md:col-span-2">
            <Card className="card-glass p-4 h-[500px] flex flex-col">
              {selectedRoom ? (
                <>
                  <div className="flex-1 overflow-y-auto mb-4 space-y-3">
                    {messages.map(m => (
                      <div key={m.id} className={`p-3 rounded-lg ${m.user_id === user.id ? 'bg-yellow-400/20 ml-8' : 'bg-white/5 mr-8'}`}>
                        <p className="text-yellow-400 text-xs mb-1">{m.username}</p>
                        <p className="text-white">{m.content}</p>
                      </div>
                    ))}
                    {messages.length === 0 && <p className="text-white/60 text-center py-8">No messages yet</p>}
                  </div>
                  <div className="flex gap-2">
                    <Input className="form-input flex-1" placeholder="Type a message..." value={message} onChange={e => setMessage(e.target.value)} onKeyDown={e => e.key === 'Enter' && message && sendMessageMutation.mutate(message)} data-testid="chat-message-input" />
                    <Button onClick={() => message && sendMessageMutation.mutate(message)} className="btn-gold" data-testid="send-message-btn">
                      <Send size={18} />
                    </Button>
                  </div>
                </>
              ) : (
                <div className="flex-1 flex items-center justify-center">
                  <div className="text-center">
                    <MessageCircle className="mx-auto text-white/30 mb-4" size={48} />
                    <p className="text-white/60">Select a room to start chatting</p>
                  </div>
                </div>
              )}
            </Card>
          </div>
        </div>

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
