import React, { useState } from 'react';
import { Navigate } from 'react-router-dom';
import { useQuery, useMutation, useQueryClient } from '@tanstack/react-query';
import axios from 'axios';
import { Users, Plus, UserPlus, Search } from 'lucide-react';
import { useAuth } from '../context/AuthContext';
import { useToast } from '../context/ToastContext';
import { API } from '../utils/api';
import StarsBackground from '../components/StarsBackground';
import { Card } from '../components/ui/card';
import { Button } from '../components/ui/button';
import { Input } from '../components/ui/input';
import { Badge } from '../components/ui/badge';
import { Checkbox } from '../components/ui/checkbox';
import { Label } from '../components/ui/label';
import { Textarea } from '../components/ui/textarea';
import { Dialog, DialogContent, DialogHeader, DialogTitle, DialogDescription, DialogFooter } from '../components/ui/dialog';

const GroupsPage = () => {
  const { user } = useAuth();
  const showToast = useToast();
  const queryClient = useQueryClient();
  const [showCreate, setShowCreate] = useState(false);
  const [newGroup, setNewGroup] = useState({ name: "", description: "", is_public: true });

  const { data, isLoading } = useQuery({
    queryKey: ["groups"],
    queryFn: () => axios.get(`${API}/groups`).then(r => r.data),
    enabled: !!user
  });

  const createMutation = useMutation({
    mutationFn: (group) => axios.post(`${API}/groups`, group),
    onSuccess: () => {
      showToast("Group created! 🎉", "success");
      queryClient.invalidateQueries(["groups"]);
      setShowCreate(false);
      setNewGroup({ name: "", description: "", is_public: true });
    }
  });

  const joinMutation = useMutation({
    mutationFn: (id) => axios.post(`${API}/groups/${id}/join`),
    onSuccess: () => { showToast("Joined group!", "success"); queryClient.invalidateQueries(["groups"]); }
  });

  const leaveMutation = useMutation({
    mutationFn: (id) => axios.post(`${API}/groups/${id}/leave`),
    onSuccess: () => { showToast("Left group", "success"); queryClient.invalidateQueries(["groups"]); }
  });

  if (!user) return <Navigate to="/login" />;

  const groups = data?.groups || [];
  const myGroups = groups.filter(g => g.members?.includes(user.id));
  const otherGroups = groups.filter(g => !g.members?.includes(user.id));

  return (
    <div className="min-h-screen pt-20 px-4">
      <StarsBackground />
      <div className="max-w-5xl mx-auto">
        <div className="flex items-center justify-between mb-8">
          <div>
            <h1 className="text-3xl font-bold text-gradient-gold">Groups</h1>
            <p className="text-white/60">Join communities and share protocols</p>
          </div>
          <Button onClick={() => setShowCreate(true)} className="btn-gold" data-testid="create-group-btn">
            <Plus className="mr-2" /> Create Group
          </Button>
        </div>

        {isLoading ? <p className="text-white/60 text-center">Loading...</p> : (
          <>
            <div className="mb-8">
              <h3 className="text-xl font-bold text-white mb-4">My Groups ({myGroups.length})</h3>
              {myGroups.length === 0 ? (
                <Card className="card-glass p-6 text-center">
                  <Users className="mx-auto text-white/30 mb-2" size={40} />
                  <p className="text-white/60">You have not joined any groups yet</p>
                </Card>
              ) : (
                <div className="grid md:grid-cols-2 lg:grid-cols-3 gap-4">
                  {myGroups.map(group => (
                    <Card key={group.id} className="card-glass p-4" data-testid={`group-${group.id}`}>
                      <div className="flex items-start gap-3">
                        <div className="w-12 h-12 rounded-lg bg-gradient-to-br from-purple-500 to-blue-500 flex items-center justify-center text-white font-bold text-lg">
                          {group.name.charAt(0).toUpperCase()}
                        </div>
                        <div className="flex-1">
                          <h4 className="text-white font-semibold">{group.name}</h4>
                          <p className="text-white/50 text-sm line-clamp-2">{group.description}</p>
                          <Badge className="bg-white/10 text-white/70 text-xs mt-2">{group.members?.length || 0} members</Badge>
                        </div>
                      </div>
                      <Button size="sm" variant="outline" onClick={() => leaveMutation.mutate(group.id)} className="w-full mt-4 text-red-400 border-red-400/30">Leave</Button>
                    </Card>
                  ))}
                </div>
              )}
            </div>

            <div>
              <h3 className="text-xl font-bold text-white mb-4">Discover Groups ({otherGroups.length})</h3>
              {otherGroups.length === 0 ? (
                <Card className="card-glass p-6 text-center">
                  <Search className="mx-auto text-white/30 mb-2" size={40} />
                  <p className="text-white/60">No other groups available. Create one!</p>
                </Card>
              ) : (
                <div className="grid md:grid-cols-2 lg:grid-cols-3 gap-4">
                  {otherGroups.map(group => (
                    <Card key={group.id} className="card-glass p-4 hover:border-purple-400/50 transition">
                      <div className="flex items-start gap-3">
                        <div className="w-12 h-12 rounded-lg bg-gradient-to-br from-green-500 to-cyan-500 flex items-center justify-center text-white font-bold text-lg">
                          {group.name.charAt(0).toUpperCase()}
                        </div>
                        <div className="flex-1">
                          <h4 className="text-white font-semibold">{group.name}</h4>
                          <p className="text-white/50 text-sm line-clamp-2">{group.description}</p>
                          <Badge className="bg-white/10 text-white/70 text-xs mt-2">{group.members?.length || 0} members</Badge>
                        </div>
                      </div>
                      <Button onClick={() => joinMutation.mutate(group.id)} className="w-full mt-4 btn-gold" data-testid={`join-group-${group.id}`}>
                        <UserPlus className="mr-2" size={16} /> Join
                      </Button>
                    </Card>
                  ))}
                </div>
              )}
            </div>
          </>
        )}

        <Dialog open={showCreate} onOpenChange={setShowCreate}>
          <DialogContent className="bg-slate-900 border-yellow-400/30">
            <DialogHeader>
              <DialogTitle className="text-yellow-400">Create New Group</DialogTitle>
              <DialogDescription className="text-white/70">Start a community</DialogDescription>
            </DialogHeader>
            <div className="space-y-4 py-4">
              <div>
                <Label className="text-white">Group Name *</Label>
                <Input className="form-input mt-1" value={newGroup.name} onChange={e => setNewGroup({...newGroup, name: e.target.value})} data-testid="group-name-input" />
              </div>
              <div>
                <Label className="text-white">Description *</Label>
                <Textarea className="form-input mt-1" rows={3} value={newGroup.description} onChange={e => setNewGroup({...newGroup, description: e.target.value})} data-testid="group-description-input" />
              </div>
              <div className="flex items-center gap-2">
                <Checkbox checked={newGroup.is_public} onCheckedChange={checked => setNewGroup({...newGroup, is_public: checked})} />
                <Label className="text-white/80">Public Group</Label>
              </div>
            </div>
            <DialogFooter>
              <Button variant="outline" onClick={() => setShowCreate(false)}>Cancel</Button>
              <Button className="btn-gold" onClick={() => createMutation.mutate(newGroup)} disabled={!newGroup.name || !newGroup.description} data-testid="create-group-submit">Create</Button>
            </DialogFooter>
          </DialogContent>
        </Dialog>
      </div>
    </div>
  );
};
export default GroupsPage;
