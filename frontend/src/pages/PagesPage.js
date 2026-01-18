import React, { useState } from 'react';
import { Navigate } from 'react-router-dom';
import { useQuery, useMutation, useQueryClient } from '@tanstack/react-query';
import axios from 'axios';
import { Layers, Plus, Heart, Search } from 'lucide-react';
import { useAuth } from '../context/AuthContext';
import { useToast } from '../context/ToastContext';
import { API } from '../utils/api';
import StarsBackground from '../components/StarsBackground';
import { Card } from '../components/ui/card';
import { Button } from '../components/ui/button';
import { Input } from '../components/ui/input';
import { Badge } from '../components/ui/badge';
import { Label } from '../components/ui/label';
import { Textarea } from '../components/ui/textarea';
import { Select, SelectContent, SelectItem, SelectTrigger, SelectValue } from '../components/ui/select';
import { Dialog, DialogContent, DialogHeader, DialogTitle, DialogDescription, DialogFooter } from '../components/ui/dialog';

const PagesPage = () => {
  const { user } = useAuth();
  const showToast = useToast();
  const queryClient = useQueryClient();
  const [showCreate, setShowCreate] = useState(false);
  const [newPage, setNewPage] = useState({ name: "", description: "", category: "general" });

  const { data, isLoading } = useQuery({
    queryKey: ["pages"],
    queryFn: () => axios.get(`${API}/pages`).then(r => r.data),
    enabled: !!user
  });

  const createMutation = useMutation({
    mutationFn: (page) => axios.post(`${API}/pages`, page),
    onSuccess: () => {
      showToast("Page created!", "success");
      queryClient.invalidateQueries(["pages"]);
      setShowCreate(false);
    }
  });

  const followMutation = useMutation({
    mutationFn: (id) => axios.post(`${API}/pages/${id}/follow`),
    onSuccess: () => { showToast("Following!", "success"); queryClient.invalidateQueries(["pages"]); }
  });

  if (!user) return <Navigate to="/login" />;

  const pages = data?.pages || [];
  const myPages = pages.filter(p => p.owner_id === user.id);
  const discoverPages = pages.filter(p => p.owner_id !== user.id);

  const categoryColors = { general: "bg-gray-500", tech: "bg-blue-500", news: "bg-red-500", entertainment: "bg-purple-500", education: "bg-green-500", business: "bg-yellow-500", science: "bg-cyan-500" };

  return (
    <div className="min-h-screen pt-20 px-4">
      <StarsBackground />
      <div className="max-w-5xl mx-auto">
        <div className="flex items-center justify-between mb-8">
          <div>
            <h1 className="text-3xl font-bold text-gradient-gold">Pages</h1>
            <p className="text-white/60">Follow pages to get curated content</p>
          </div>
          <Button onClick={() => setShowCreate(true)} className="btn-gold" data-testid="create-page-btn"><Plus className="mr-2" /> Create Page</Button>
        </div>

        {isLoading ? <p className="text-white/60 text-center">Loading...</p> : (
          <>
            {myPages.length > 0 && (
              <div className="mb-8">
                <h3 className="text-xl font-bold text-white mb-4">My Pages ({myPages.length})</h3>
                <div className="grid md:grid-cols-2 lg:grid-cols-3 gap-4">
                  {myPages.map(page => (
                    <Card key={page.id} className="card-glass p-4" data-testid={`page-${page.id}`}>
                      <div className="flex items-start gap-3">
                        <div className={`w-12 h-12 rounded-lg ${categoryColors[page.category] || categoryColors.general} flex items-center justify-center text-white font-bold`}>{page.name.charAt(0).toUpperCase()}</div>
                        <div className="flex-1">
                          <h4 className="text-white font-semibold">{page.name}</h4>
                          <p className="text-white/50 text-sm line-clamp-2">{page.description}</p>
                          <Badge className="bg-white/10 text-white/70 text-xs mt-2">{page.followers?.length || 0} followers</Badge>
                        </div>
                      </div>
                    </Card>
                  ))}
                </div>
              </div>
            )}

            <div>
              <h3 className="text-xl font-bold text-white mb-4">Discover Pages ({discoverPages.length})</h3>
              {discoverPages.length === 0 ? (
                <Card className="card-glass p-6 text-center">
                  <Layers className="mx-auto text-white/30 mb-2" size={40} />
                  <p className="text-white/60">No pages to discover. Create one!</p>
                </Card>
              ) : (
                <div className="grid md:grid-cols-2 lg:grid-cols-3 gap-4">
                  {discoverPages.map(page => (
                    <Card key={page.id} className="card-glass p-4 hover:border-yellow-400/50 transition">
                      <div className="flex items-start gap-3">
                        <div className={`w-12 h-12 rounded-lg ${categoryColors[page.category] || categoryColors.general} flex items-center justify-center text-white font-bold`}>{page.name.charAt(0).toUpperCase()}</div>
                        <div className="flex-1">
                          <h4 className="text-white font-semibold">{page.name}</h4>
                          <p className="text-white/50 text-sm line-clamp-2">{page.description}</p>
                          <Badge className="bg-white/10 text-white/70 text-xs mt-2">{page.followers?.length || 0} followers</Badge>
                        </div>
                      </div>
                      <Button onClick={() => followMutation.mutate(page.id)} className="w-full mt-4 btn-gold" data-testid={`follow-page-${page.id}`}><Heart className="mr-2" size={16} /> Follow</Button>
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
              <DialogTitle className="text-yellow-400">Create New Page</DialogTitle>
            </DialogHeader>
            <div className="space-y-4 py-4">
              <div>
                <Label className="text-white">Page Name *</Label>
                <Input className="form-input mt-1" value={newPage.name} onChange={e => setNewPage({...newPage, name: e.target.value})} data-testid="page-name-input" />
              </div>
              <div>
                <Label className="text-white">Description *</Label>
                <Textarea className="form-input mt-1" rows={3} value={newPage.description} onChange={e => setNewPage({...newPage, description: e.target.value})} />
              </div>
              <div>
                <Label className="text-white">Category</Label>
                <Select value={newPage.category} onValueChange={v => setNewPage({...newPage, category: v})}>
                  <SelectTrigger className="form-input mt-1"><SelectValue /></SelectTrigger>
                  <SelectContent className="bg-slate-800">
                    <SelectItem value="general">General</SelectItem>
                    <SelectItem value="tech">Technology</SelectItem>
                    <SelectItem value="news">News</SelectItem>
                    <SelectItem value="entertainment">Entertainment</SelectItem>
                    <SelectItem value="education">Education</SelectItem>
                    <SelectItem value="business">Business</SelectItem>
                    <SelectItem value="science">Science</SelectItem>
                  </SelectContent>
                </Select>
              </div>
            </div>
            <DialogFooter>
              <Button variant="outline" onClick={() => setShowCreate(false)}>Cancel</Button>
              <Button className="btn-gold" onClick={() => createMutation.mutate(newPage)} disabled={!newPage.name || !newPage.description} data-testid="create-page-submit">Create</Button>
            </DialogFooter>
          </DialogContent>
        </Dialog>
      </div>
    </div>
  );
};
export default PagesPage;
