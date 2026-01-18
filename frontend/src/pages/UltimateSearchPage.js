/**
 * InfoPilot Explorer - Ultimate Search Page
 */
import React, { useState, useRef } from 'react';
import { Navigate } from 'react-router-dom';
import { useQuery, useMutation, useQueryClient } from '@tanstack/react-query';
import axios from 'axios';
import { Search, Plus, Trash2, Edit, RefreshCw, ChevronDown, ChevronRight, Star, X } from 'lucide-react';
import { useAuth } from '../context/AuthContext';
import { useToast } from '../context/ToastContext';
import { API } from '../utils/api';
import StarsBackground from '../components/StarsBackground';
import { Card } from '../components/ui/card';
import { Button } from '../components/ui/button';
import { Input } from '../components/ui/input';
import { Textarea } from '../components/ui/textarea';
import { Badge } from '../components/ui/badge';
import { Label } from '../components/ui/label';
import { Checkbox } from '../components/ui/checkbox';
import { Select, SelectContent, SelectItem, SelectTrigger, SelectValue } from '../components/ui/select';
import { Dialog, DialogContent, DialogHeader, DialogTitle, DialogDescription, DialogFooter } from '../components/ui/dialog';

const UltimateSearchPage = () => {
  const { user } = useAuth();
  const showToast = useToast();
  const queryClient = useQueryClient();
  const [searchQuery, setSearchQuery] = useState("");
  const [quickSearchQuery, setQuickSearchQuery] = useState("");
  const [selectedCategories, setSelectedCategories] = useState([]);
  const [aggregation, setAggregation] = useState("and_or");
  const [searchEngine, setSearchEngine] = useState("all");
  const [showCreateCategory, setShowCreateCategory] = useState(false);
  const [showEditCategory, setShowEditCategory] = useState(false);
  const [editingCategory, setEditingCategory] = useState(null);
  const [newCategory, setNewCategory] = useState({ name: "", protocol: "", parent_id: null, is_public: true, price: null });
  const [expandedCategories, setExpandedCategories] = useState({});

  // Fetch available search engines
  const { data: enginesData } = useQuery({
    queryKey: ["search-engines"],
    queryFn: () => axios.get(`${API}/search/engines`).then(r => r.data)
  });

  const { data: categoriesData, isLoading: loadingCategories } = useQuery({
    queryKey: ["categories"],
    queryFn: () => axios.get(`${API}/categories`).then(r => r.data),
    enabled: !!user
  });

  const { data: resultsData, isLoading: loadingResults, refetch: refetchResults } = useQuery({
    queryKey: ["search-results", selectedCategories, aggregation],
    queryFn: () => axios.get(`${API}/search/results`, { params: { category_ids: selectedCategories.join(","), aggregation } }).then(r => r.data),
    enabled: !!user && selectedCategories.length > 0
  });

  const { data: recommendedData } = useQuery({
    queryKey: ["templates"],
    queryFn: () => axios.get(`${API}/templates`).then(r => r.data)
  });

  const collateMutation = useMutation({
    mutationFn: (query) => axios.post(`${API}/search/collate`, { query, engine: searchEngine }),
    onSuccess: (data) => {
      showToast(data.data.message, "success");
      queryClient.invalidateQueries(["categories"]);
      refetchResults();
    },
    onError: () => showToast("Collation failed", "error")
  });

  const createCategoryMutation = useMutation({
    mutationFn: (cat) => axios.post(`${API}/categories`, cat),
    onSuccess: () => {
      showToast("Category created! 🎉", "success");
      queryClient.invalidateQueries(["categories"]);
      setShowCreateCategory(false);
      setNewCategory({ name: "", protocol: "", parent_id: null, is_public: true, price: null });
    },
    onError: (err) => showToast(err.response?.data?.detail || "Failed to create category", "error")
  });

  const updateCategoryMutation = useMutation({
    mutationFn: ({ id, updates }) => axios.put(`${API}/categories/${id}`, updates),
    onSuccess: () => {
      showToast("Protocol saved! 🎉", "success");
      queryClient.invalidateQueries(["categories"]);
      setShowEditCategory(false);
      setEditingCategory(null);
    },
    onError: (err) => showToast(err.response?.data?.detail || "Failed to update", "error")
  });

  const deleteCategoryMutation = useMutation({
    mutationFn: (id) => axios.delete(`${API}/categories/${id}`),
    onSuccess: () => { showToast("Category deleted", "success"); queryClient.invalidateQueries(["categories"]); }
  });

  if (!user) return <Navigate to="/login" />;

  const categories = categoriesData?.categories || [];
  const results = resultsData?.results || [];
  const filteredResults = quickSearchQuery ? results.filter(r => 
    r.title?.toLowerCase().includes(quickSearchQuery.toLowerCase()) || 
    r.snippet?.toLowerCase().includes(quickSearchQuery.toLowerCase())
  ) : results;
  const categoryTree = categories.filter(c => !c.parent_id);
  const getChildren = (parentId) => categories.filter(c => c.parent_id === parentId);
  const recommendedProtocols = recommendedData?.official_templates?.slice(0, 3) || [];

  const toggleCategory = (id) => setSelectedCategories(prev => prev.includes(id) ? prev.filter(c => c !== id) : [...prev, id]);

  const openEditCategory = (cat) => {
    setEditingCategory({ ...cat });
    setShowEditCategory(true);
  };

  const renderCategoryTree = (cats, depth = 0) => (
    <div className={`${depth > 0 ? 'ml-4 border-l border-white/10 pl-2' : ''}`}>
      {cats.map(cat => {
        const children = getChildren(cat.id);
        const hasChildren = children.length > 0;
        const isExpanded = expandedCategories[cat.id];
        
        return (
          <div key={cat.id} className="mb-1">
            <div className="flex items-center gap-2 p-2 rounded hover:bg-white/5 group">
              {hasChildren && (
                <button onClick={() => setExpandedCategories(prev => ({...prev, [cat.id]: !prev[cat.id]}))}>
                  {isExpanded ? <ChevronDown size={14} /> : <ChevronRight size={14} />}
                </button>
              )}
              {!hasChildren && <span className="w-[14px]" />}
              <Checkbox checked={selectedCategories.includes(cat.id)} onCheckedChange={() => toggleCategory(cat.id)} />
              <span className="text-white/90 text-sm flex-1 truncate" title={cat.name}>{cat.name}</span>
              <Badge className="text-xs bg-white/10 shrink-0">({cat.search_result_count || 0})</Badge>
              <div className="flex gap-1 shrink-0">
                <button onClick={(e) => { e.stopPropagation(); openEditCategory(cat); }} className="text-blue-400 hover:text-blue-300 p-1" title="Edit Protocol" data-testid={`edit-category-${cat.id}`}><Edit size={14} /></button>
                <button onClick={(e) => { e.stopPropagation(); setNewCategory({...newCategory, parent_id: cat.id}); setShowCreateCategory(true); }} className="text-green-400 hover:text-green-300 p-1" title="Add subcategory"><Plus size={14} /></button>
                <button onClick={(e) => { e.stopPropagation(); deleteCategoryMutation.mutate(cat.id); }} className="text-red-400 hover:text-red-300 p-1" title="Delete"><Trash2 size={14} /></button>
              </div>
            </div>
            {hasChildren && isExpanded && renderCategoryTree(children, depth + 1)}
          </div>
        );
      })}
    </div>
  );

  return (
    <div className="min-h-screen pt-20 px-4">
      <StarsBackground />
      <div className="max-w-7xl mx-auto">
        <div className="text-center mb-8">
          <h1 className="text-3xl font-bold text-gradient-gold mb-2">{user.ultimate_search_name || user.username}&apos;s Ultimate Search</h1>
          <p className="text-white/60">Your personal InfoJet 2.0 categorization dashboard</p>
        </div>

        <div className="grid lg:grid-cols-4 gap-6">
          <div className="lg:col-span-1 space-y-4">
            <Card className="card-glass p-4">
              <div className="flex items-center justify-between mb-4">
                <h3 className="text-lg font-bold text-yellow-400">Categories</h3>
                <Button size="sm" onClick={() => setShowCreateCategory(true)} data-testid="create-category-btn"><Plus size={14} /></Button>
              </div>
              
              {loadingCategories ? <p className="text-white/60 text-sm">Loading...</p> : categories.length === 0 ? (
                <p className="text-white/60 text-sm">No categories yet. Create one!</p>
              ) : (
                <>
                  <div className="flex gap-2 mb-3">
                    <Button size="sm" variant="outline" onClick={() => setSelectedCategories(categories.map(c => c.id))} className="text-xs" data-testid="select-all-btn">Select All</Button>
                    <Button size="sm" variant="outline" onClick={() => setSelectedCategories([])} className="text-xs" data-testid="deselect-all-btn">Deselect</Button>
                  </div>
                  <div className="max-h-[400px] overflow-y-auto">{renderCategoryTree(categoryTree)}</div>
                </>
              )}

              <div className="mt-4 pt-4 border-t border-white/10">
                <Label className="text-white/70 text-xs">Aggregation:</Label>
                <Select value={aggregation} onValueChange={setAggregation}>
                  <SelectTrigger className="form-input mt-1 text-xs"><SelectValue /></SelectTrigger>
                  <SelectContent className="bg-slate-800">
                    <SelectItem value="and_or">And/Or (Default)</SelectItem>
                    <SelectItem value="and">And (Exact)</SelectItem>
                    <SelectItem value="or">Or (Any)</SelectItem>
                  </SelectContent>
                </Select>
              </div>
            </Card>

            <Card className="card-glass p-4" data-testid="recommended-protocols">
              <h3 className="text-lg font-bold text-yellow-400 mb-3 flex items-center gap-2"><Star size={16} /> Recommended</h3>
              <div className="space-y-2">
                {recommendedProtocols.map(t => (
                  <div key={t.id} className="p-2 bg-white/5 rounded-lg hover:bg-white/10 cursor-pointer transition" onClick={() => { setNewCategory({...newCategory, protocol: t.protocol, name: t.name}); setShowCreateCategory(true); }}>
                    <p className="text-white/90 text-sm font-semibold">{t.name}</p>
                    <p className="text-white/50 text-xs truncate">{t.protocol}</p>
                  </div>
                ))}
              </div>
            </Card>
          </div>

          <div className="lg:col-span-3">
            <Card className="card-glass p-4 mb-6">
              <div className="flex flex-wrap gap-4 mb-4">
                <Input className="form-input flex-1 min-w-[200px]" placeholder="Enter search query..." value={searchQuery} onChange={e => setSearchQuery(e.target.value)} data-testid="search-query-input" />
                <Select value={searchEngine} onValueChange={setSearchEngine}>
                  <SelectTrigger className="form-input w-[180px]" data-testid="search-engine-select">
                    <SelectValue placeholder="Search Engine" />
                  </SelectTrigger>
                  <SelectContent className="bg-slate-800">
                    <SelectItem value="all">🌐 All Engines</SelectItem>
                    <SelectItem value="duckduckgo">🦆 DuckDuckGo</SelectItem>
                    <SelectItem value="brave" disabled={!enginesData?.brave_configured}>
                      🦁 Brave {!enginesData?.brave_configured && "(Not configured)"}
                    </SelectItem>
                  </SelectContent>
                </Select>
                <Button onClick={() => collateMutation.mutate(searchQuery)} disabled={!searchQuery || collateMutation.isPending} className="btn-gold" data-testid="collate-btn">
                  {collateMutation.isPending ? <RefreshCw className="animate-spin" /> : <Search className="mr-2" />} Search & Collate
                </Button>
              </div>
              {enginesData?.engines && (
                <div className="flex gap-2 mb-3 text-xs text-white/50">
                  <span>Available engines:</span>
                  {enginesData.engines.map(e => (
                    <Badge key={e.id} className={`text-xs ${e.configured ? 'bg-green-500/20 text-green-300' : 'bg-red-500/20 text-red-300'}`}>
                      {e.name} {e.configured ? '✓' : '✗'}
                    </Badge>
                  ))}
                </div>
              )}
              {results.length > 0 && (
                <div className="flex items-center gap-2" data-testid="quick-search-container">
                  <Search size={16} className="text-white/50" />
                  <Input className="form-input flex-1" placeholder="Quick search within results..." value={quickSearchQuery} onChange={e => setQuickSearchQuery(e.target.value)} data-testid="quick-search-input" />
                  {quickSearchQuery && <Button size="sm" variant="ghost" onClick={() => setQuickSearchQuery("")}><X size={14} /></Button>}
                </div>
              )}
            </Card>

            <Card className="card-glass p-4">
              <div className="flex items-center justify-between mb-4">
                <h3 className="text-lg font-bold text-white">Results ({filteredResults.length}{quickSearchQuery ? ` of ${results.length}` : ''})</h3>
              </div>
              {loadingResults ? <p className="text-white/60">Loading...</p> : filteredResults.length === 0 ? (
                <p className="text-white/60">{results.length > 0 ? "No results match your quick search." : "No results yet. Use Search & Collate!"}</p>
              ) : (
                <div className="space-y-4 max-h-[600px] overflow-y-auto">
                  {filteredResults.map(result => (
                    <div key={result.id} className="p-4 bg-white/5 rounded-lg hover:bg-white/10 transition" data-testid={`search-result-${result.id}`}>
                      <div className="flex items-start justify-between mb-2">
                        <a href={result.url} target="_blank" rel="noopener noreferrer" className="text-yellow-400 hover:underline font-semibold">{result.title}</a>
                        <div className="flex gap-1">
                          {result.source && (
                            <Badge className={`text-xs ${result.source === 'Brave' ? 'bg-orange-500/20 text-orange-300' : result.source === 'DuckDuckGo' ? 'bg-green-500/20 text-green-300' : 'bg-white/10'}`}>
                              {result.source === 'Brave' ? '🦁' : result.source === 'DuckDuckGo' ? '🦆' : '🌐'} {result.source}
                            </Badge>
                          )}
                          <Badge className="text-xs">{result.document_type}</Badge>
                        </div>
                      </div>
                      <p className="text-white/70 text-sm mb-2">{result.snippet}</p>
                      <div className="flex flex-wrap gap-1">
                        {result.category_ids?.map(catId => {
                          const cat = categories.find(c => c.id === catId);
                          return cat ? <Badge key={catId} className="text-xs bg-blue-500/20">{cat.name}</Badge> : null;
                        })}
                      </div>
                    </div>
                  ))}
                </div>
              )}
            </Card>
          </div>
        </div>

        {/* Create Category Modal */}
        <Dialog open={showCreateCategory} onOpenChange={setShowCreateCategory}>
          <DialogContent className="bg-slate-900 border-yellow-400/30">
            <DialogHeader>
              <DialogTitle className="text-yellow-400">Create Category</DialogTitle>
              <DialogDescription className="text-white/70">Write an InfoJet 2.0 protocol</DialogDescription>
            </DialogHeader>
            <div className="space-y-4 py-4">
              <div>
                <Label className="text-white">Category Name *</Label>
                <Input className="form-input mt-1" placeholder="e.g., Tech Innovations" value={newCategory.name} onChange={e => setNewCategory({...newCategory, name: e.target.value})} data-testid="new-category-name" />
              </div>
              <div>
                <Label className="text-white">Protocol (InfoJet 2.0) *</Label>
                <Textarea className="form-input mt-1 font-mono text-sm" rows={4} placeholder="(word1 or word2) & (word3)+" value={newCategory.protocol} onChange={e => setNewCategory({...newCategory, protocol: e.target.value})} data-testid="new-category-protocol" />
              </div>
              <div className="flex items-center gap-4">
                <div className="flex items-center gap-2">
                  <Checkbox checked={newCategory.is_public} onCheckedChange={checked => setNewCategory({...newCategory, is_public: checked})} />
                  <Label className="text-white/80">Public</Label>
                </div>
                <div className="flex-1">
                  <Label className="text-white/80 text-xs">Sell Price ($) <span className="text-yellow-400">Max $24.99</span></Label>
                  <Input className="form-input mt-1" type="number" step="0.01" min="1" max="24.99" placeholder="Free" value={newCategory.price || ""} onChange={e => setNewCategory({...newCategory, price: e.target.value ? Math.min(parseFloat(e.target.value), 24.99) : null})} />
                </div>
              </div>
            </div>
            <DialogFooter>
              <Button variant="outline" onClick={() => { setShowCreateCategory(false); setNewCategory({ name: "", protocol: "", parent_id: null, is_public: true, price: null }); }}>Cancel</Button>
              <Button className="btn-gold" onClick={() => createCategoryMutation.mutate(newCategory)} disabled={!newCategory.name || !newCategory.protocol || createCategoryMutation.isPending} data-testid="create-category-submit">
                {createCategoryMutation.isPending ? "Creating..." : "Create Category"}
              </Button>
            </DialogFooter>
          </DialogContent>
        </Dialog>

        {/* Edit Category Modal */}
        <Dialog open={showEditCategory} onOpenChange={setShowEditCategory}>
          <DialogContent className="bg-slate-900 border-yellow-400/30">
            <DialogHeader>
              <DialogTitle className="text-yellow-400">Edit Category - Save Protocol</DialogTitle>
            </DialogHeader>
            {editingCategory && (
              <div className="space-y-4 py-4">
                <div>
                  <Label className="text-white">Category Name *</Label>
                  <Input className="form-input mt-1" value={editingCategory.name} onChange={e => setEditingCategory({...editingCategory, name: e.target.value})} data-testid="edit-category-name" />
                </div>
                <div>
                  <Label className="text-white">Protocol *</Label>
                  <Textarea className="form-input mt-1 font-mono text-sm" rows={4} value={editingCategory.protocol} onChange={e => setEditingCategory({...editingCategory, protocol: e.target.value})} data-testid="edit-category-protocol" />
                </div>
                <div className="flex items-center gap-4">
                  <div className="flex items-center gap-2">
                    <Checkbox checked={editingCategory.is_public} onCheckedChange={checked => setEditingCategory({...editingCategory, is_public: checked})} />
                    <Label className="text-white/80">Public</Label>
                  </div>
                  <div className="flex-1">
                    <Label className="text-white/80 text-xs">Price ($)</Label>
                    <Input className="form-input mt-1" type="number" step="0.01" min="1" value={editingCategory.price || ""} onChange={e => setEditingCategory({...editingCategory, price: e.target.value ? parseFloat(e.target.value) : null})} />
                  </div>
                </div>
              </div>
            )}
            <DialogFooter>
              <Button variant="outline" onClick={() => { setShowEditCategory(false); setEditingCategory(null); }}>Cancel</Button>
              <Button className="btn-gold" onClick={() => updateCategoryMutation.mutate({ id: editingCategory.id, updates: editingCategory })} disabled={!editingCategory?.name || !editingCategory?.protocol || updateCategoryMutation.isPending} data-testid="save-protocol-btn">
                {updateCategoryMutation.isPending ? "Saving..." : "Save Protocol"}
              </Button>
            </DialogFooter>
          </DialogContent>
        </Dialog>
      </div>
    </div>
  );
};

export default UltimateSearchPage;
