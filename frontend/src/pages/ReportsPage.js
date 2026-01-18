import React, { useState, useRef } from 'react';
import { Navigate } from 'react-router-dom';
import { useQuery, useMutation, useQueryClient } from '@tanstack/react-query';
import axios from 'axios';
import { useAuth } from '../context/AuthContext';
import { useToast } from '../context/ToastContext';
import StarsBackground from '../components/StarsBackground';
import { Card } from '../components/ui/card';
import { Button } from '../components/ui/button';
import { Badge } from '../components/ui/badge';
import { Input } from '../components/ui/input';
import { Label } from '../components/ui/label';
import { Textarea } from '../components/ui/textarea';
import { Dialog, DialogContent, DialogDescription, DialogFooter, DialogHeader, DialogTitle } from '../components/ui/dialog';
import { Plus, FileText, Trash2, RefreshCw, MapPin, Camera, X } from 'lucide-react';

const API = process.env.REACT_APP_BACKEND_URL + '/api';
const BACKEND_URL = process.env.REACT_APP_BACKEND_URL;

const ReportsPage = () => {
  const { user } = useAuth();
  const showToast = useToast();
  const queryClient = useQueryClient();
  const [showCreate, setShowCreate] = useState(false);
  const [newReport, setNewReport] = useState({ title: "", content: "", images: [], location: null, category_ids: [] });
  const [uploadingImage, setUploadingImage] = useState(false);
  const fileInputRef = useRef(null);

  const { data, isLoading } = useQuery({
    queryKey: ["reports"],
    queryFn: () => axios.get(`${API}/reports`).then(r => r.data),
    enabled: !!user
  });

  const { data: categoriesData } = useQuery({
    queryKey: ["categories"],
    queryFn: () => axios.get(`${API}/categories`).then(r => r.data),
    enabled: !!user
  });

  const createMutation = useMutation({
    mutationFn: (report) => axios.post(`${API}/reports`, report),
    onSuccess: () => {
      showToast("Report created! 🎉", "success");
      queryClient.invalidateQueries(["reports"]);
      setShowCreate(false);
      setNewReport({ title: "", content: "", images: [], location: null, category_ids: [] });
    },
    onError: (err) => showToast(err.response?.data?.detail || "Failed to create report", "error")
  });

  const deleteMutation = useMutation({
    mutationFn: (id) => axios.delete(`${API}/reports/${id}`),
    onSuccess: () => {
      showToast("Report deleted", "success");
      queryClient.invalidateQueries(["reports"]);
    }
  });

  const handleImageUpload = async (e) => {
    const file = e.target.files?.[0];
    if (!file) return;
    
    if (newReport.images.length >= 3) {
      showToast("Maximum 3 images allowed", "error");
      return;
    }
    
    if (file.size > 5 * 1024 * 1024) {
      showToast("Image too large. Max 5MB", "error");
      return;
    }
    
    setUploadingImage(true);
    const formData = new FormData();
    formData.append("file", file);
    
    try {
      const res = await axios.post(`${API}/reports/upload/image`, formData, {
        headers: { "Content-Type": "multipart/form-data" }
      });
      setNewReport(prev => ({ ...prev, images: [...prev.images, res.data.url] }));
      showToast("Image uploaded! 📸", "success");
    } catch (err) {
      showToast(err.response?.data?.detail || "Upload failed", "error");
    } finally {
      setUploadingImage(false);
    }
  };

  const removeImage = (index) => {
    setNewReport(prev => ({ ...prev, images: prev.images.filter((_, i) => i !== index) }));
  };

  if (!user) return <Navigate to="/login" />;

  const categories = categoriesData?.categories || [];

  return (
    <div className="min-h-screen pt-20 px-4">
      <StarsBackground />
      <div className="max-w-4xl mx-auto">
        <div className="flex items-center justify-between mb-8">
          <div>
            <h1 className="text-3xl font-bold text-gradient-gold">My Personal Reports</h1>
            <p className="text-white/60">Create organic reports about any topic with photos</p>
          </div>
          <Button onClick={() => setShowCreate(true)} className="btn-gold" data-testid="create-report-btn"><Plus className="mr-2" /> Create Report</Button>
        </div>

        {isLoading ? (
          <div className="text-center py-12"><RefreshCw className="animate-spin mx-auto text-yellow-400" size={48} /></div>
        ) : data?.reports?.length === 0 ? (
          <Card className="card-glass p-8 text-center" data-testid="reports-empty">
            <FileText className="mx-auto text-yellow-400 mb-4" size={48} />
            <h3 className="text-xl text-white mb-2">No reports yet!</h3>
            <p className="text-white/60">Create your first personal report to share your knowledge.</p>
          </Card>
        ) : (
          <div className="space-y-4">
            {data?.reports?.map(report => (
              <Card key={report.id} className="card-glass p-4" data-testid={`report-${report.id}`}>
                <div className="flex items-start justify-between">
                  <div className="flex-1">
                    <h3 className="text-lg font-bold text-white">{report.title}</h3>
                    <p className="text-white/70 mt-2 whitespace-pre-wrap">{report.content}</p>
                    {report.images?.length > 0 && (
                      <div className="flex gap-2 mt-3">
                        {report.images.map((img, i) => (
                          <img key={i} src={BACKEND_URL + img} alt="" className="w-24 h-24 object-cover rounded-lg border border-white/10" />
                        ))}
                      </div>
                    )}
                    <div className="flex flex-wrap items-center gap-2 mt-3 text-white/50 text-sm">
                      <Badge>{report.document_type}</Badge>
                      <span>{new Date(report.created_at).toLocaleDateString()}</span>
                      {report.location && <span className="flex items-center gap-1"><MapPin size={14} /> {report.location.city || "Location"}</span>}
                      {report.images?.length > 0 && <span className="flex items-center gap-1"><Camera size={14} /> {report.images.length} photo(s)</span>}
                    </div>
                  </div>
                  <Button variant="ghost" size="sm" onClick={() => deleteMutation.mutate(report.id)} className="text-red-400 hover:text-red-300" data-testid={`delete-report-${report.id}`}>
                    <Trash2 size={18} />
                  </Button>
                </div>
              </Card>
            ))}
          </div>
        )}

        <Dialog open={showCreate} onOpenChange={setShowCreate}>
          <DialogContent className="bg-slate-900 border-yellow-400/30 max-w-lg">
            <DialogHeader>
              <DialogTitle className="text-yellow-400">Create Personal Report</DialogTitle>
              <DialogDescription className="text-white/70">Share your knowledge with up to 3 photos</DialogDescription>
            </DialogHeader>
            <div className="space-y-4 py-4 max-h-[60vh] overflow-y-auto">
              <div>
                <Label className="text-white">Title *</Label>
                <Input className="form-input mt-1" placeholder="Report title" value={newReport.title} onChange={e => setNewReport({...newReport, title: e.target.value})} data-testid="report-title-input" />
              </div>
              <div>
                <Label className="text-white">Content *</Label>
                <Textarea className="form-input mt-1" rows={5} placeholder="Your report content... (minimum 75 words recommended)" value={newReport.content} onChange={e => setNewReport({...newReport, content: e.target.value})} data-testid="report-content-input" />
                <p className="text-white/40 text-xs mt-1">{newReport.content.split(/\s+/).filter(w => w).length} words</p>
              </div>
              
              {/* Image Upload */}
              <div>
                <Label className="text-white">Images (Max 3)</Label>
                <div className="mt-2 flex flex-wrap gap-2">
                  {newReport.images.map((img, i) => (
                    <div key={i} className="relative">
                      <img src={BACKEND_URL + img} alt="" className="w-20 h-20 object-cover rounded-lg border border-white/20" />
                      <button onClick={() => removeImage(i)} className="absolute -top-2 -right-2 bg-red-500 rounded-full p-1 hover:bg-red-600" type="button">
                        <X size={12} />
                      </button>
                    </div>
                  ))}
                  {newReport.images.length < 3 && (
                    <button
                      onClick={() => fileInputRef.current?.click()}
                      disabled={uploadingImage}
                      className="w-20 h-20 border-2 border-dashed border-white/30 rounded-lg flex items-center justify-center text-white/50 hover:border-yellow-400 hover:text-yellow-400 transition"
                      type="button"
                      data-testid="upload-image-btn"
                    >
                      {uploadingImage ? <RefreshCw className="animate-spin" size={24} /> : <Plus size={24} />}
                    </button>
                  )}
                </div>
                <input ref={fileInputRef} type="file" accept="image/*" className="hidden" onChange={handleImageUpload} />
              </div>

              {/* Categories */}
              {categories.length > 0 && (
                <div>
                  <div className="flex items-center justify-between mb-2">
                    <Label className="text-white">Categories (optional)</Label>
                    <div className="flex gap-2">
                      <button 
                        type="button"
                        onClick={() => setNewReport(prev => ({...prev, category_ids: categories.map(c => c.id)}))}
                        className="text-xs text-yellow-400 hover:text-yellow-300"
                        data-testid="select-all-categories-btn"
                      >
                        Select All
                      </button>
                      <span className="text-white/30">|</span>
                      <button 
                        type="button"
                        onClick={() => setNewReport(prev => ({...prev, category_ids: []}))}
                        className="text-xs text-white/60 hover:text-white"
                        data-testid="deselect-all-categories-btn"
                      >
                        Deselect All
                      </button>
                    </div>
                  </div>
                  <div className="flex flex-wrap gap-2 max-h-24 overflow-y-auto">
                    {categories.map(cat => (
                      <Badge
                        key={cat.id}
                        className={`cursor-pointer transition ${newReport.category_ids.includes(cat.id) ? "bg-yellow-400/30 text-yellow-300" : "bg-white/10 text-white/60 hover:bg-white/20"}`}
                        onClick={() => setNewReport(prev => ({
                          ...prev,
                          category_ids: prev.category_ids.includes(cat.id)
                            ? prev.category_ids.filter(id => id !== cat.id)
                            : [...prev.category_ids, cat.id]
                        }))}
                      >
                        {cat.name}
                      </Badge>
                    ))}
                  </div>
                </div>
              )}
            </div>
            <DialogFooter>
              <Button variant="outline" onClick={() => { setShowCreate(false); setNewReport({ title: "", content: "", images: [], location: null, category_ids: [] }); }}>Cancel</Button>
              <Button className="btn-gold" onClick={() => createMutation.mutate(newReport)} disabled={!newReport.title || !newReport.content || createMutation.isPending} data-testid="submit-report-btn">
                {createMutation.isPending ? "Creating..." : "Create Report"}
              </Button>
            </DialogFooter>
          </DialogContent>
        </Dialog>
      </div>
    </div>
  );
};

export default ReportsPage;
