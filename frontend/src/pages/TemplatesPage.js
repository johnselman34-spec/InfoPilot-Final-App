import React, { useState } from 'react';
import { useQuery, useMutation, useQueryClient } from '@tanstack/react-query';
import axios from 'axios';
import { useAuth } from '../context/AuthContext';
import { useToast } from '../context/ToastContext';
import StarsBackground from '../components/StarsBackground';
import { Card, CardContent, CardDescription, CardFooter, CardHeader, CardTitle } from '../components/ui/card';
import { Button } from '../components/ui/button';
import { Badge } from '../components/ui/badge';
import { Input } from '../components/ui/input';
import { Label } from '../components/ui/label';
import { Textarea } from '../components/ui/textarea';
import { Tabs, TabsContent, TabsList, TabsTrigger } from '../components/ui/tabs';
import { Dialog, DialogContent, DialogDescription, DialogFooter, DialogHeader, DialogTitle } from '../components/ui/dialog';
import { Plus, Copy, Layers } from 'lucide-react';

const API = process.env.REACT_APP_BACKEND_URL + '/api';

const TemplatesPage = () => {
  const { user } = useAuth();
  const showToast = useToast();
  const queryClient = useQueryClient();
  const { data, isLoading } = useQuery({
    queryKey: ["templates"],
    queryFn: () => axios.get(`${API}/templates`).then(r => r.data)
  });
  const [showCreate, setShowCreate] = useState(false);
  const [newTemplate, setNewTemplate] = useState({ name: "", description: "", protocol: "", category_suggestion: "", price: "" });

  const createMutation = useMutation({
    mutationFn: (t) => axios.post(`${API}/templates`, t),
    onSuccess: () => {
      showToast("Template created! 🎉", "success");
      queryClient.invalidateQueries(["templates"]);
      setShowCreate(false);
      setNewTemplate({ name: "", description: "", protocol: "", category_suggestion: "", price: "" });
    },
    onError: () => showToast("Failed to create template", "error")
  });

  const copyProtocol = (protocol) => {
    navigator.clipboard.writeText(protocol);
    showToast("Protocol copied to clipboard!", "success");
  };

  return (
    <div className="min-h-screen pt-20 px-4">
      <StarsBackground />
      <div className="max-w-6xl mx-auto">
        <div className="flex items-center justify-between mb-8">
          <div>
            <h1 className="text-3xl font-bold text-gradient-gold">Protocol Template Gallery</h1>
            <p className="text-white/60">Browse and copy proven InfoJet 2.0 protocol examples</p>
          </div>
          {user && (
            <Button onClick={() => setShowCreate(true)} className="btn-gold" data-testid="create-template-btn">
              <Plus className="mr-2" /> Create Template
            </Button>
          )}
        </div>

        <Tabs defaultValue="official" className="w-full">
          <TabsList className="bg-white/10 mb-6">
            <TabsTrigger value="official" className="data-[state=active]:bg-yellow-400/20">Official Templates</TabsTrigger>
            <TabsTrigger value="community" className="data-[state=active]:bg-yellow-400/20">Community Templates</TabsTrigger>
          </TabsList>

          <TabsContent value="official">
            <div className="grid md:grid-cols-2 lg:grid-cols-3 gap-6">
              {data?.official_templates?.map(t => (
                <Card key={t.id} className="card-glass p-4" data-testid={`template-${t.id}`}>
                  <CardHeader className="p-0 pb-4">
                    <div className="flex items-start justify-between">
                      <CardTitle className="text-white text-lg">{t.name}</CardTitle>
                      <Badge className="bg-yellow-400/20 text-yellow-300">Official</Badge>
                    </div>
                    <CardDescription className="text-white/60">{t.description}</CardDescription>
                  </CardHeader>
                  <CardContent className="p-0">
                    <div className="bg-slate-800/50 p-3 rounded-lg font-mono text-xs text-green-400 mb-3">{t.protocol}</div>
                    <p className="text-white/50 text-xs mb-2">Suggested: {t.category_suggestion}</p>
                    <p className="text-white/40 text-xs">Used {t.usage_count?.toLocaleString()} times</p>
                  </CardContent>
                  <CardFooter className="p-0 pt-4">
                    <Button onClick={() => copyProtocol(t.protocol)} className="btn-gold w-full">
                      <Copy className="mr-2" size={16} /> Copy Protocol
                    </Button>
                  </CardFooter>
                </Card>
              ))}
            </div>
          </TabsContent>

          <TabsContent value="community">
            {data?.community_templates?.length === 0 ? (
              <Card className="card-glass p-8 text-center">
                <Layers className="mx-auto text-yellow-400 mb-4" size={48} />
                <h3 className="text-xl text-white mb-2">No community templates yet!</h3>
                <p className="text-white/60">Be the first to share your protocol expertise.</p>
              </Card>
            ) : (
              <div className="grid md:grid-cols-2 lg:grid-cols-3 gap-6">
                {data?.community_templates?.map(t => (
                  <Card key={t.id} className="card-glass p-4">
                    <CardHeader className="p-0 pb-4">
                      <CardTitle className="text-white text-lg">{t.name}</CardTitle>
                      <CardDescription className="text-white/60">{t.description}</CardDescription>
                    </CardHeader>
                    <CardContent className="p-0">
                      <div className="bg-slate-800/50 p-3 rounded-lg font-mono text-xs text-green-400 mb-3">{t.protocol}</div>
                      {t.price && <Badge className="bg-green-500/20 text-green-300">${t.price}</Badge>}
                    </CardContent>
                    <CardFooter className="p-0 pt-4">
                      <Button onClick={() => copyProtocol(t.protocol)} className="btn-gold w-full">
                        <Copy className="mr-2" size={16} /> Copy Protocol
                      </Button>
                    </CardFooter>
                  </Card>
                ))}
              </div>
            )}
          </TabsContent>
        </Tabs>

        <Dialog open={showCreate} onOpenChange={setShowCreate}>
          <DialogContent className="bg-slate-900 border-yellow-400/30">
            <DialogHeader>
              <DialogTitle className="text-yellow-400">Create Protocol Template</DialogTitle>
              <DialogDescription className="text-white/70">Share your protocol expertise with the community</DialogDescription>
            </DialogHeader>
            <div className="space-y-4 py-4">
              <div>
                <Label className="text-white">Template Name *</Label>
                <Input className="form-input mt-1" placeholder="e.g., Tech Innovation Finder" value={newTemplate.name} onChange={e => setNewTemplate({...newTemplate, name: e.target.value})} data-testid="template-name-input" />
              </div>
              <div>
                <Label className="text-white">Description *</Label>
                <Textarea className="form-input mt-1" placeholder="What does this protocol find?" value={newTemplate.description} onChange={e => setNewTemplate({...newTemplate, description: e.target.value})} data-testid="template-description-input" />
              </div>
              <div>
                <Label className="text-white">Protocol (InfoJet 2.0) *</Label>
                <Textarea className="form-input mt-1 font-mono text-sm" rows={3} placeholder="(word1 or word2) & (word3)+" value={newTemplate.protocol} onChange={e => setNewTemplate({...newTemplate, protocol: e.target.value})} data-testid="template-protocol-input" />
              </div>
              <div>
                <Label className="text-white">Category Suggestion</Label>
                <Input className="form-input mt-1" placeholder="e.g., Technology / AI" value={newTemplate.category_suggestion} onChange={e => setNewTemplate({...newTemplate, category_suggestion: e.target.value})} />
              </div>
              <div>
                <Label className="text-white">Price (optional)</Label>
                <Input className="form-input mt-1" type="number" step="0.01" placeholder="Leave empty for free" value={newTemplate.price} onChange={e => setNewTemplate({...newTemplate, price: e.target.value})} />
              </div>
            </div>
            <DialogFooter>
              <Button variant="outline" onClick={() => setShowCreate(false)}>Cancel</Button>
              <Button className="btn-gold" onClick={() => createMutation.mutate(newTemplate)} disabled={!newTemplate.name || !newTemplate.protocol || createMutation.isPending} data-testid="submit-template-btn">
                {createMutation.isPending ? "Creating..." : "Create Template"}
              </Button>
            </DialogFooter>
          </DialogContent>
        </Dialog>
      </div>
    </div>
  );
};

export default TemplatesPage;
