import React, { useState, useEffect, createContext, useContext, useRef, useCallback } from "react";
import { BrowserRouter, Routes, Route, useNavigate, useLocation, Link, Navigate } from "react-router-dom";
import axios from "axios";
import { 
  Search, Home, Map, BarChart3, Users, MessageCircle, 
  ShoppingBag, Settings, LogOut, Menu, X, ChevronRight,
  Plus, Folder, Globe, Heart, ThumbsUp, Laugh, AlertTriangle,
  MessageSquare, Star, Filter, Check, Copy, Trash2, Edit,
  ChevronDown, Play, RefreshCw, Award, TrendingUp, Zap,
  BookOpen, User, Bell, HelpCircle, Egg, Send, UserPlus,
  Download, Smartphone, Monitor, FileText, CreditCard,
  CheckCircle, XCircle, Layout, Scale, Shield
} from "lucide-react";
import { Button } from "@/components/ui/button";
import { Input } from "@/components/ui/input";
import { Card, CardContent, CardHeader, CardTitle, CardDescription } from "@/components/ui/card";
import { Checkbox } from "@/components/ui/checkbox";
import { RadioGroup, RadioGroupItem } from "@/components/ui/radio-group";
import { Label } from "@/components/ui/label";
import { Tabs, TabsContent, TabsList, TabsTrigger } from "@/components/ui/tabs";
import { ScrollArea } from "@/components/ui/scroll-area";
import { Dialog, DialogContent, DialogHeader, DialogTitle, DialogTrigger } from "@/components/ui/dialog";
import { Select, SelectContent, SelectItem, SelectTrigger, SelectValue } from "@/components/ui/select";
import { Textarea } from "@/components/ui/textarea";
import { Progress } from "@/components/ui/progress";
import { Badge } from "@/components/ui/badge";
import { Separator } from "@/components/ui/separator";
import { PieChart, Pie, Cell, BarChart, Bar, XAxis, YAxis, CartesianGrid, Tooltip, Legend, ResponsiveContainer, LineChart, Line } from "recharts";

const BACKEND_URL = process.env.REACT_APP_BACKEND_URL;
const API = `${BACKEND_URL}/api`;

// Auth Context
const AuthContext = createContext(null);

export const useAuth = () => useContext(AuthContext);

// API helper with auth
const api = axios.create({
  baseURL: API,
  withCredentials: true
});

// ============= AUTH PROVIDER =============
const AuthProvider = ({ children }) => {
  const [user, setUser] = useState(null);
  const [loading, setLoading] = useState(true);

  const checkAuth = useCallback(async () => {
    try {
      const response = await api.get("/auth/me");
      setUser(response.data);
    } catch (error) {
      setUser(null);
    } finally {
      setLoading(false);
    }
  }, []);

  useEffect(() => {
    checkAuth();
  }, [checkAuth]);

  const login = () => {
    // REMINDER: DO NOT HARDCODE THE URL, OR ADD ANY FALLBACKS OR REDIRECT URLS, THIS BREAKS THE AUTH
    const redirectUrl = window.location.origin + '/dashboard';
    window.location.href = `https://auth.emergentagent.com/?redirect=${encodeURIComponent(redirectUrl)}`;
  };

  const logout = async () => {
    try {
      await api.post("/auth/logout");
    } catch (error) {
      console.error("Logout error:", error);
    }
    setUser(null);
    window.location.href = "/";
  };

  return (
    <AuthContext.Provider value={{ user, setUser, loading, login, logout, checkAuth }}>
      {children}
    </AuthContext.Provider>
  );
};

// ============= AUTH CALLBACK =============
const AuthCallback = () => {
  const navigate = useNavigate();
  const location = useLocation();
  const { setUser } = useAuth();
  const hasProcessed = useRef(false);

  useEffect(() => {
    if (hasProcessed.current) return;
    hasProcessed.current = true;

    const processAuth = async () => {
      const hash = location.hash;
      const sessionId = new URLSearchParams(hash.substring(1)).get("session_id");

      if (sessionId) {
        try {
          const response = await api.post("/auth/session", { session_id: sessionId });
          setUser(response.data);
          navigate("/dashboard", { replace: true, state: { user: response.data } });
        } catch (error) {
          console.error("Auth error:", error);
          navigate("/", { replace: true });
        }
      } else {
        navigate("/", { replace: true });
      }
    };

    processAuth();
  }, [location, navigate, setUser]);

  return (
    <div className="min-h-screen bg-ivory flex items-center justify-center">
      <div className="spinner"></div>
    </div>
  );
};

// ============= PROTECTED ROUTE =============
const ProtectedRoute = ({ children }) => {
  const { user, loading } = useAuth();
  const location = useLocation();

  if (loading) {
    return (
      <div className="min-h-screen bg-ivory flex items-center justify-center">
        <div className="spinner"></div>
      </div>
    );
  }

  if (!user) {
    return <Navigate to="/" state={{ from: location }} replace />;
  }

  return children;
};

// ============= LANDING PAGE =============
const LandingPage = () => {
  const { user, login } = useAuth();
  const navigate = useNavigate();

  useEffect(() => {
    if (user) {
      navigate("/dashboard");
    }
  }, [user, navigate]);

  return (
    <div className="min-h-screen bg-[#FFFFF0]">
      {/* Navigation */}
      <nav className="fixed top-0 left-0 right-0 z-50 bg-white/80 backdrop-blur-md border-b border-gray-100/50">
        <div className="max-w-7xl mx-auto px-6 py-4 flex items-center justify-between">
          <div className="flex items-center gap-2">
            <Globe className="w-8 h-8 text-[#007AFF]" />
            <span className="text-xl font-bold font-['Outfit']">InfoPilot Explorer</span>
          </div>
          <div className="flex items-center gap-4">
            <Button variant="ghost" onClick={login} data-testid="login-btn">
              Sign In
            </Button>
            <Button className="btn-primary px-6" onClick={login} data-testid="get-started-btn">
              Get Started
            </Button>
          </div>
        </div>
      </nav>

      {/* Hero Section */}
      <section className="pt-32 pb-20 px-6">
        <div className="max-w-7xl mx-auto">
          <div className="grid md:grid-cols-2 gap-12 items-center">
            <div className="slide-up">
              <Badge className="mb-4 badge-primary">World Wide Web Information Exchange</Badge>
              <h1 className="text-6xl md:text-7xl font-bold tracking-tight mb-6 font-['Outfit']">
                Your <span className="text-[#007AFF]">3D View</span> of the Internet
              </h1>
              <p className="text-xl text-gray-600 mb-8 leading-relaxed">
                The #1 resource for finding information valuable to YOU. Create custom search protocols, 
                collate results into categories, and explore the web like never before.
              </p>
              <div className="flex flex-wrap gap-4">
                <Button className="btn-primary h-14 px-8 text-lg" onClick={login} data-testid="hero-get-started">
                  <Zap className="w-5 h-5 mr-2" /> Start Exploring
                </Button>
                <Button variant="outline" className="h-14 px-8 text-lg rounded-full" data-testid="learn-more-btn">
                  <Play className="w-5 h-5 mr-2" /> Watch Demo
                </Button>
              </div>
            </div>
            <div className="relative slide-up stagger-2">
              <div className="glass-card p-8 hover-lift">
                <img 
                  src="https://images.unsplash.com/photo-1765527977786-93d61f48a963?w=800"
                  alt="3D Digital Globe Network"
                  className="rounded-xl w-full"
                />
              </div>
            </div>
          </div>
        </div>
      </section>

      {/* Features Section */}
      <section className="py-20 px-6 bg-white/50">
        <div className="max-w-7xl mx-auto">
          <div className="text-center mb-16">
            <h2 className="text-4xl md:text-5xl font-semibold mb-4 font-['Outfit']">
              Powerful Features
            </h2>
            <p className="text-xl text-gray-600">Search the web on your terms using InfoJet 2.0</p>
          </div>
          
          <div className="grid md:grid-cols-3 gap-8">
            {[
              { icon: Search, title: "Smart Protocols", desc: "Create custom Boolean search protocols for any topic imaginable" },
              { icon: Folder, title: "Auto-Categorization", desc: "Our Internet Robot automatically collates results into your categories" },
              { icon: Map, title: "Visual Mapping", desc: "See your research on an interactive world map with location data" },
              { icon: BarChart3, title: "Deep Analytics", desc: "Charts and statistics to understand your information landscape" },
              { icon: Users, title: "Social Network", desc: "Connect with researchers, share protocols, and collaborate" },
              { icon: ShoppingBag, title: "Protocol Marketplace", desc: "Buy and sell proven search protocols with the community" }
            ].map((feature, i) => (
              <Card key={i} className="glass-card hover-lift p-6 slide-up" style={{ animationDelay: `${i * 0.1}s` }}>
                <feature.icon className="w-12 h-12 text-[#007AFF] mb-4" />
                <h3 className="text-xl font-semibold mb-2 font-['Outfit']">{feature.title}</h3>
                <p className="text-gray-600">{feature.desc}</p>
              </Card>
            ))}
          </div>
        </div>
      </section>

      {/* Protocol Example Section */}
      <section className="py-20 px-6">
        <div className="max-w-7xl mx-auto">
          <div className="grid md:grid-cols-2 gap-12 items-center">
            <div>
              <Badge className="mb-4 badge-secondary">InfoJet 2.0</Badge>
              <h2 className="text-4xl font-semibold mb-6 font-['Outfit']">
                Protocol Examples
              </h2>
              <div className="space-y-4">
                <div className="glass-card p-4">
                  <p className="text-sm font-medium text-gray-500 mb-2">American Civil War Research</p>
                  <code className="protocol-editor block text-sm">
                    (American civil war) & (battle or battles) & (1860 to 1865)+
                  </code>
                </div>
                <div className="glass-card p-4">
                  <p className="text-sm font-medium text-gray-500 mb-2">Civil War Heroes</p>
                  <code className="protocol-editor block text-sm">
                    (heroically or hero) & (Gettysburg or Princeton) & (isn't or wasn't)^
                  </code>
                </div>
                <div className="glass-card p-4">
                  <p className="text-sm font-medium text-gray-500 mb-2">William C. Gamble</p>
                  <code className="protocol-editor block text-sm">
                    (William Gamble or General Gamble) & (Civil War) & (U.S. Army)+
                  </code>
                </div>
              </div>
            </div>
            <div className="glass-card p-8">
              <h3 className="text-xl font-semibold mb-4 font-['Outfit']">Protocol Syntax</h3>
              <ul className="space-y-3">
                <li className="flex items-start gap-3">
                  <Check className="w-5 h-5 text-[#34C759] mt-0.5" />
                  <span><code className="bg-gray-100 px-2 py-1 rounded">or</code> - Alternative terms within a group</span>
                </li>
                <li className="flex items-start gap-3">
                  <Check className="w-5 h-5 text-[#34C759] mt-0.5" />
                  <span><code className="bg-gray-100 px-2 py-1 rounded">&</code> - AND between groups</span>
                </li>
                <li className="flex items-start gap-3">
                  <Check className="w-5 h-5 text-[#34C759] mt-0.5" />
                  <span><code className="bg-gray-100 px-2 py-1 rounded">+</code> - Include these terms</span>
                </li>
                <li className="flex items-start gap-3">
                  <Check className="w-5 h-5 text-[#34C759] mt-0.5" />
                  <span><code className="bg-gray-100 px-2 py-1 rounded">^</code> - Exclude these terms</span>
                </li>
                <li className="flex items-start gap-3">
                  <Check className="w-5 h-5 text-[#34C759] mt-0.5" />
                  <span>Case insensitive matching</span>
                </li>
                <li className="flex items-start gap-3">
                  <Check className="w-5 h-5 text-[#34C759] mt-0.5" />
                  <span>Works with any language in the world</span>
                </li>
              </ul>
            </div>
          </div>
        </div>
      </section>

      {/* CTA Section */}
      <section className="py-20 px-6 bg-gradient-to-br from-[#007AFF]/5 to-[#34C759]/5">
        <div className="max-w-3xl mx-auto text-center">
          <h2 className="text-4xl font-semibold mb-6 font-['Outfit']">
            Ready to Transform Your Research?
          </h2>
          <p className="text-xl text-gray-600 mb-8">
            Join thousands of researchers, professionals, and curious minds exploring the web smarter.
          </p>
          <Button className="btn-primary h-14 px-12 text-lg" onClick={login} data-testid="cta-get-started">
            Start Free - $0.99/month
          </Button>
          <p className="text-sm text-gray-500 mt-4">No credit card required for trial</p>
        </div>
      </section>

      {/* Footer */}
      <footer className="py-12 px-6 border-t border-gray-200">
        <div className="max-w-7xl mx-auto">
          <div className="grid md:grid-cols-4 gap-8 mb-8">
            {/* Brand */}
            <div>
              <div className="flex items-center gap-2 mb-4">
                <Globe className="w-6 h-6 text-[#007AFF]" />
                <span className="font-bold font-['Outfit']">InfoPilot Explorer</span>
              </div>
              <p className="text-sm text-gray-500">First in Flight with Monetization of Searches</p>
              <p className="text-xs text-gray-400 mt-2">Top Pilot Enterprises Inc.</p>
            </div>
            
            {/* Legal */}
            <div>
              <h4 className="font-semibold mb-4">Legal</h4>
              <div className="space-y-2 text-sm text-gray-600">
                <Link to="/privacy-policy" className="block hover:text-[#007AFF]" data-testid="footer-privacy">Privacy Policy</Link>
                <Link to="/terms-of-service" className="block hover:text-[#007AFF]" data-testid="footer-terms">Terms of Service</Link>
              </div>
            </div>
            
            {/* Download Apps */}
            <div>
              <h4 className="font-semibold mb-4">Download</h4>
              <div className="space-y-2 text-sm text-gray-600">
                <a href="https://play.google.com/store/apps/details?id=com.infopilot.explorer" target="_blank" rel="noopener noreferrer" className="flex items-center gap-2 hover:text-[#007AFF]" data-testid="download-android">
                  <Smartphone className="w-4 h-4" /> Android App
                </a>
                <a href="https://apps.apple.com/app/infojet" target="_blank" rel="noopener noreferrer" className="flex items-center gap-2 hover:text-[#007AFF]" data-testid="download-ios">
                  <Smartphone className="w-4 h-4" /> iOS App
                </a>
                <a href="https://www.infopilotexplorer.biz/download" target="_blank" rel="noopener noreferrer" className="flex items-center gap-2 hover:text-[#007AFF]" data-testid="download-desktop">
                  <Monitor className="w-4 h-4" /> Desktop App
                </a>
              </div>
            </div>
            
            {/* Contact */}
            <div>
              <h4 className="font-semibold mb-4">Contact</h4>
              <div className="space-y-2 text-sm text-gray-600">
                <p>Brunswick, Maine</p>
                <p>JJSpilot24@gmail.com</p>
                <p>(207) 522-0894</p>
              </div>
            </div>
          </div>
          
          <div className="pt-8 border-t border-gray-200 flex flex-col md:flex-row justify-between items-center gap-4">
            <p className="text-sm text-gray-500">© 2025-2026 Top Pilot Enterprises, Inc. All rights reserved.</p>
            <p className="text-xs text-gray-400">InfoPilot Explorer - First in Flight with Monetization of Searches</p>
          </div>
        </div>
      </footer>
    </div>
  );
};

// ============= DASHBOARD LAYOUT =============
const DashboardLayout = ({ children }) => {
  const { user, logout } = useAuth();
  const [sidebarOpen, setSidebarOpen] = useState(true);
  const location = useLocation();

  const navItems = [
    { path: "/dashboard", icon: Home, label: "Ultimate Search" },
    { path: "/map", icon: Map, label: "Map View" },
    { path: "/stats", icon: BarChart3, label: "Statistics" },
    { path: "/global", icon: Globe, label: "Global Research" },
    { path: "/marketplace", icon: ShoppingBag, label: "Marketplace" },
    { path: "/templates", icon: Layout, label: "Protocol Templates" },
    { path: "/leaderboard", icon: Award, label: "Leaderboard" },
    { path: "/friends", icon: Users, label: "Friends" },
    { path: "/groups", icon: Users, label: "Groups" },
    { path: "/chat", icon: MessageCircle, label: "Messages" },
    { path: "/reports", icon: BookOpen, label: "Personal Reports" },
    { path: "/easter-eggs", icon: Egg, label: "Easter Eggs" },
    { path: "/quotes", icon: BookOpen, label: "Quote Gallery" },
    { path: "/themes", icon: Settings, label: "Themes" },
    { path: "/book", icon: BookOpen, label: "Letters to Evelyn" },
    { path: "/settings", icon: Settings, label: "Settings" },
  ];

  if (user?.is_admin) {
    navItems.push({ path: "/admin", icon: Settings, label: "Admin Panel" });
  }

  return (
    <div className="min-h-screen bg-[#FFFFF0] flex">
      {/* Sidebar */}
      <aside className={`fixed left-0 top-0 h-full bg-white border-r border-gray-100 transition-all duration-300 z-40 ${sidebarOpen ? 'w-64' : 'w-20'}`}>
        <div className="p-4 flex items-center justify-between border-b border-gray-100">
          {sidebarOpen && (
            <div className="flex items-center gap-2">
              <Globe className="w-8 h-8 text-[#007AFF]" />
              <span className="font-bold font-['Outfit']">InfoPilot</span>
            </div>
          )}
          <Button variant="ghost" size="icon" onClick={() => setSidebarOpen(!sidebarOpen)} data-testid="toggle-sidebar">
            {sidebarOpen ? <X className="w-5 h-5" /> : <Menu className="w-5 h-5" />}
          </Button>
        </div>

        <ScrollArea className="h-[calc(100vh-140px)]">
          <nav className="p-4 space-y-2">
            {navItems.map((item) => (
              <Link
                key={item.path}
                to={item.path}
                className={`sidebar-link ${location.pathname === item.path ? 'active' : ''}`}
                data-testid={`nav-${item.label.toLowerCase().replace(' ', '-')}`}
              >
                <item.icon className="w-5 h-5 flex-shrink-0" />
                {sidebarOpen && <span className="ml-3">{item.label}</span>}
              </Link>
            ))}
          </nav>
        </ScrollArea>

        <div className="absolute bottom-0 left-0 right-0 p-4 border-t border-gray-100">
          <div className={`flex items-center ${sidebarOpen ? 'gap-3' : 'justify-center'}`}>
            <img 
              src={user?.picture || "https://via.placeholder.com/40"} 
              alt={user?.name}
              className="w-10 h-10 rounded-full"
            />
            {sidebarOpen && (
              <div className="flex-1 min-w-0">
                <p className="font-medium truncate">{user?.name}</p>
                <p className="text-sm text-gray-500 truncate">Level {user?.level || 1}</p>
              </div>
            )}
            {sidebarOpen && (
              <Button variant="ghost" size="icon" onClick={logout} data-testid="logout-btn">
                <LogOut className="w-5 h-5" />
              </Button>
            )}
          </div>
        </div>
      </aside>

      {/* Main Content */}
      <main className={`flex-1 transition-all duration-300 ${sidebarOpen ? 'ml-64' : 'ml-20'}`}>
        {children}
      </main>
    </div>
  );
};

// ============= ULTIMATE SEARCH PAGE =============
const UltimateSearchPage = () => {
  const { user } = useAuth();
  const [categories, setCategories] = useState([]);
  const [selectedCategories, setSelectedCategories] = useState([]);
  const [searchQuery, setSearchQuery] = useState("");
  const [searchResults, setSearchResults] = useState([]);
  const [aggregation, setAggregation] = useState("and_or");
  const [loading, setLoading] = useState(false);
  const [showNewCategory, setShowNewCategory] = useState(false);
  const [newCategoryName, setNewCategoryName] = useState("");
  const [newCategoryProtocol, setNewCategoryProtocol] = useState("");
  const [documentTypes, setDocumentTypes] = useState([]);
  const [selectedDocTypes, setSelectedDocTypes] = useState([]);
  const [filters, setFilters] = useState({
    year: "",
    rootDomain: "",
    country: "",
    state: ""
  });
  // New: Search Match Options
  const [matchOptions, setMatchOptions] = useState({
    exactMatch: false,
    strictMatch: false,
    aiMatch: true,
    intelligentMatch: false,
    favorSchematics: false
  });
  // New: Templates and Debugger
  const [showTemplates, setShowTemplates] = useState(false);
  const [templates, setTemplates] = useState([]);
  const [showDebugger, setShowDebugger] = useState(false);
  const [debugInfo, setDebugInfo] = useState(null);

  useEffect(() => {
    fetchCategories();
    fetchResults();
    fetchDocumentTypes();
    fetchTemplates();
  }, []);

  const fetchDocumentTypes = async () => {
    try {
      const response = await api.get("/document-types");
      setDocumentTypes(response.data.types || []);
    } catch (error) {
      console.error("Error fetching document types:", error);
    }
  };

  const fetchTemplates = async () => {
    try {
      const response = await api.get("/templates");
      setTemplates(response.data.templates || []);
    } catch (error) {
      console.error("Error fetching templates:", error);
    }
  };

  const fetchCategories = async () => {
    try {
      const response = await api.get(`/categories?user_id=${user.user_id}`);
      setCategories(response.data.categories || []);
    } catch (error) {
      console.error("Error fetching categories:", error);
    }
  };

  const fetchResults = async () => {
    try {
      const params = new URLSearchParams();
      if (selectedCategories.length > 0) {
        params.append("category_ids", selectedCategories.join(","));
      }
      params.append("aggregation", aggregation);
      if (selectedDocTypes.length === 1) {
        params.append("document_type", selectedDocTypes[0]);
      }
      if (filters.year) params.append("year", filters.year);
      if (filters.rootDomain) params.append("root_domain", filters.rootDomain);
      if (filters.country) params.append("country", filters.country);
      if (filters.state) params.append("state", filters.state);
      // Add match options
      if (matchOptions.exactMatch) params.append("exact_match", "true");
      if (matchOptions.strictMatch) params.append("strict_match", "true");
      if (matchOptions.aiMatch) params.append("ai_match", "true");
      if (matchOptions.intelligentMatch) params.append("intelligent_match", "true");
      if (matchOptions.favorSchematics) params.append("favor_schematics", "true");

      const response = await api.get(`/search/results?${params.toString()}`);
      setSearchResults(response.data.results || []);
    } catch (error) {
      console.error("Error fetching results:", error);
    }
  };

  const handleSearch = async () => {
    if (!searchQuery.trim()) return;
    setLoading(true);
    try {
      const response = await api.post("/search/collate", {
        query: searchQuery,
        category_ids: selectedCategories,
        max_results: 40,
        match_options: matchOptions
      });
      setSearchResults(response.data.results || []);
      // Set debug info
      setDebugInfo({
        query: searchQuery,
        categories: selectedCategories.length,
        matchOptions: matchOptions,
        resultsCount: response.data.results?.length || 0,
        timestamp: new Date().toISOString()
      });
    } catch (error) {
      console.error("Search error:", error);
    } finally {
      setLoading(false);
    }
  };

  const createCategory = async () => {
    if (!newCategoryName.trim() || !newCategoryProtocol.trim()) return;
    try {
      await api.post("/categories", {
        name: newCategoryName,
        protocol: newCategoryProtocol,
        is_public: true
      });
      setNewCategoryName("");
      setNewCategoryProtocol("");
      setShowNewCategory(false);
      fetchCategories();
    } catch (error) {
      console.error("Error creating category:", error);
    }
  };

  const toggleCategory = (categoryId) => {
    setSelectedCategories(prev => 
      prev.includes(categoryId) 
        ? prev.filter(id => id !== categoryId)
        : [...prev, categoryId]
    );
  };

  const toggleDocType = (docTypeName) => {
    setSelectedDocTypes(prev =>
      prev.includes(docTypeName)
        ? prev.filter(t => t !== docTypeName)
        : [...prev, docTypeName]
    );
  };

  const selectAllDocTypes = () => {
    setSelectedDocTypes(documentTypes.map(dt => dt.name));
  };

  const deselectAllDocTypes = () => {
    setSelectedDocTypes([]);
  };

  const selectAllMatchOptions = () => {
    setMatchOptions({
      exactMatch: true,
      strictMatch: true,
      aiMatch: true,
      intelligentMatch: true,
      favorSchematics: true
    });
  };

  const deselectAllMatchOptions = () => {
    setMatchOptions({
      exactMatch: false,
      strictMatch: false,
      aiMatch: false,
      intelligentMatch: false,
      favorSchematics: false
    });
  };

  const useTemplate = (template) => {
    setNewCategoryName(template.name);
    setNewCategoryProtocol(template.protocol_string);
    setShowNewCategory(true);
    setShowTemplates(false);
  };

  return (
    <div className="p-6" data-testid="ultimate-search-page">
      <div className="max-w-7xl mx-auto">
        {/* Header */}
        <div className="mb-8">
          <h1 className="text-4xl font-bold font-['Outfit'] mb-2">Ultimate Search Page</h1>
          <p className="text-gray-600">Your personalized information command center</p>
        </div>

        <div className="grid grid-cols-1 lg:grid-cols-4 gap-6">
          {/* Left Sidebar - Categories */}
          <div className="lg:col-span-1">
            <Card className="glass-card">
              <CardHeader className="pb-4">
                <div className="flex items-center justify-between">
                  <CardTitle className="text-lg">Categories</CardTitle>
                  <Button size="sm" onClick={() => setShowNewCategory(true)} data-testid="add-category-btn">
                    <Plus className="w-4 h-4" />
                  </Button>
                </div>
              </CardHeader>
              <CardContent>
                <ScrollArea className="h-[400px]">
                  <div className="space-y-2">
                    {categories.map((cat) => (
                      <div key={cat.category_id} className="flex items-center gap-2 p-2 rounded-lg hover:bg-gray-50">
                        <Checkbox
                          id={cat.category_id}
                          checked={selectedCategories.includes(cat.category_id)}
                          onCheckedChange={() => toggleCategory(cat.category_id)}
                          data-testid={`category-${cat.category_id}`}
                        />
                        <Label htmlFor={cat.category_id} className="flex-1 cursor-pointer text-sm">
                          {cat.name}
                        </Label>
                        <Badge variant="outline" className="text-xs">
                          {cat.is_public ? "Public" : "Private"}
                        </Badge>
                      </div>
                    ))}
                    {categories.length === 0 && (
                      <p className="text-sm text-gray-500 text-center py-4">
                        No categories yet. Create one to start!
                      </p>
                    )}
                  </div>
                </ScrollArea>

                <Separator className="my-4" />

                {/* Search Aggregation */}
                <div className="space-y-3">
                  <Label className="text-sm font-medium">Search Aggregation</Label>
                  <RadioGroup value={aggregation} onValueChange={setAggregation}>
                    <div className="flex items-center gap-2">
                      <RadioGroupItem value="and_or" id="and_or" />
                      <Label htmlFor="and_or" className="text-sm">And/Or</Label>
                    </div>
                    <div className="flex items-center gap-2">
                      <RadioGroupItem value="and" id="and" />
                      <Label htmlFor="and" className="text-sm">And Only</Label>
                    </div>
                    <div className="flex items-center gap-2">
                      <RadioGroupItem value="or" id="or" />
                      <Label htmlFor="or" className="text-sm">Or</Label>
                    </div>
                  </RadioGroup>
                </div>
              </CardContent>
            </Card>
          </div>

          {/* Main Content */}
          <div className="lg:col-span-3 space-y-6">
            {/* Search Bar */}
            <Card className="glass-card">
              <CardContent className="p-6">
                <div className="flex gap-4">
                  <div className="flex-1 relative">
                    <Search className="absolute left-4 top-1/2 -translate-y-1/2 w-5 h-5 text-gray-400" />
                    <Input
                      placeholder="Search and collate into your categories..."
                      value={searchQuery}
                      onChange={(e) => setSearchQuery(e.target.value)}
                      onKeyDown={(e) => e.key === 'Enter' && handleSearch()}
                      className="pl-12 h-14 text-lg"
                      data-testid="search-input"
                    />
                  </div>
                  <Button 
                    className="btn-primary h-14 px-8" 
                    onClick={handleSearch}
                    disabled={loading}
                    data-testid="search-collate-btn"
                  >
                    {loading ? <RefreshCw className="w-5 h-5 animate-spin" /> : "Search & Collate"}
                  </Button>
                </div>

                {/* Filters */}
                <div className="mt-4">
                  {/* Document Type Filters with Select All / Deselect All */}
                  <div className="mb-4">
                    <div className="flex items-center justify-between mb-2">
                      <Label className="text-sm font-medium">Document Types</Label>
                      <div className="flex gap-2">
                        <Button 
                          variant="outline" 
                          size="sm" 
                          onClick={selectAllDocTypes}
                          data-testid="select-all-doc-types"
                        >
                          Select All
                        </Button>
                        <Button 
                          variant="outline" 
                          size="sm" 
                          onClick={deselectAllDocTypes}
                          data-testid="deselect-all-doc-types"
                        >
                          Deselect All
                        </Button>
                      </div>
                    </div>
                    <div className="flex flex-wrap gap-2">
                      {documentTypes.map((docType) => (
                        <label 
                          key={docType.id} 
                          className={`flex items-center gap-2 px-3 py-1.5 rounded-full border cursor-pointer transition-colors ${
                            selectedDocTypes.includes(docType.name) 
                              ? 'bg-[#007AFF] text-white border-[#007AFF]' 
                              : 'bg-white border-gray-200 hover:border-[#007AFF]'
                          }`}
                          data-testid={`doctype-${docType.id}`}
                        >
                          <Checkbox
                            checked={selectedDocTypes.includes(docType.name)}
                            onCheckedChange={() => toggleDocType(docType.name)}
                            className="hidden"
                          />
                          <span className="text-sm">{docType.name}</span>
                        </label>
                      ))}
                    </div>
                  </div>

                  {/* Other Filters */}
                  <div className="flex flex-wrap gap-4">
                    <Input 
                      placeholder="Year" 
                      className="w-24"
                      value={filters.year}
                      onChange={(e) => setFilters({...filters, year: e.target.value})}
                      data-testid="filter-year"
                    />

                    <Input 
                      placeholder="Domain" 
                      className="w-40"
                      value={filters.rootDomain}
                      onChange={(e) => setFilters({...filters, rootDomain: e.target.value})}
                      data-testid="filter-domain"
                    />

                    <Button variant="outline" onClick={fetchResults} data-testid="apply-filters-btn">
                      <Filter className="w-4 h-4 mr-2" /> Apply Filters
                    </Button>
                  </div>

                  {/* Search Match Options */}
                  <div className="mt-4 p-4 bg-gray-50 rounded-lg">
                    <div className="flex items-center justify-between mb-3">
                      <Label className="text-sm font-medium">Search Result Favoritism</Label>
                      <div className="flex gap-2">
                        <Button variant="outline" size="sm" onClick={selectAllMatchOptions} data-testid="select-all-match">
                          Select All
                        </Button>
                        <Button variant="outline" size="sm" onClick={deselectAllMatchOptions} data-testid="deselect-all-match">
                          Deselect All
                        </Button>
                      </div>
                    </div>
                    <div className="grid grid-cols-2 md:grid-cols-5 gap-3">
                      <label className="flex items-center gap-2 cursor-pointer">
                        <Checkbox
                          checked={matchOptions.exactMatch}
                          onCheckedChange={(v) => setMatchOptions({...matchOptions, exactMatch: v})}
                          data-testid="match-exact"
                        />
                        <span className="text-sm">Exact Match</span>
                      </label>
                      <label className="flex items-center gap-2 cursor-pointer">
                        <Checkbox
                          checked={matchOptions.strictMatch}
                          onCheckedChange={(v) => setMatchOptions({...matchOptions, strictMatch: v})}
                          data-testid="match-strict"
                        />
                        <span className="text-sm">Strict Match</span>
                      </label>
                      <label className="flex items-center gap-2 cursor-pointer">
                        <Checkbox
                          checked={matchOptions.aiMatch}
                          onCheckedChange={(v) => setMatchOptions({...matchOptions, aiMatch: v})}
                          data-testid="match-ai"
                        />
                        <span className="text-sm">AI Match</span>
                      </label>
                      <label className="flex items-center gap-2 cursor-pointer">
                        <Checkbox
                          checked={matchOptions.intelligentMatch}
                          onCheckedChange={(v) => setMatchOptions({...matchOptions, intelligentMatch: v})}
                          data-testid="match-intelligent"
                        />
                        <span className="text-sm">Intelligent Match</span>
                      </label>
                      <label className="flex items-center gap-2 cursor-pointer">
                        <Checkbox
                          checked={matchOptions.favorSchematics}
                          onCheckedChange={(v) => setMatchOptions({...matchOptions, favorSchematics: v})}
                          data-testid="match-schematics"
                        />
                        <span className="text-sm">Schematics/Diagrams</span>
                      </label>
                    </div>
                  </div>

                  {/* Action Buttons */}
                  <div className="flex flex-wrap gap-2 mt-4">
                    <Button 
                      variant="outline" 
                      size="sm" 
                      onClick={() => { setShowTemplates(!showTemplates); fetchTemplates(); }}
                      data-testid="show-templates-btn"
                    >
                      <Layout className="w-4 h-4 mr-2" /> {showTemplates ? 'Hide' : 'Show'} Templates
                    </Button>
                    <Button 
                      variant="outline" 
                      size="sm" 
                      onClick={() => setShowDebugger(!showDebugger)}
                      data-testid="show-debugger-btn"
                    >
                      <FileText className="w-4 h-4 mr-2" /> {showDebugger ? 'Hide' : 'Show'} Protocol Debugger
                    </Button>
                  </div>

                  {/* Templates Panel */}
                  {showTemplates && (
                    <div className="mt-4 p-4 bg-blue-50 rounded-lg">
                      <h4 className="font-medium mb-3">Protocol Templates</h4>
                      {templates.length > 0 ? (
                        <div className="grid grid-cols-1 md:grid-cols-2 gap-2">
                          {templates.slice(0, 6).map((t) => (
                            <button
                              key={t.template_id}
                              onClick={() => useTemplate(t)}
                              className="p-3 bg-white rounded-lg border hover:border-[#007AFF] text-left transition-colors"
                              data-testid={`template-quick-${t.template_id}`}
                            >
                              <p className="font-medium text-sm">{t.name}</p>
                              <p className="text-xs text-gray-500 truncate">{t.protocol_string}</p>
                            </button>
                          ))}
                        </div>
                      ) : (
                        <p className="text-sm text-gray-500">No templates available. Create one in the Templates page!</p>
                      )}
                    </div>
                  )}

                  {/* Protocol Debugger Panel */}
                  {showDebugger && (
                    <div className="mt-4 p-4 bg-yellow-50 rounded-lg">
                      <h4 className="font-medium mb-3">Protocol Debugger</h4>
                      {debugInfo ? (
                        <div className="font-mono text-xs bg-white p-3 rounded border">
                          <p><strong>Query:</strong> {debugInfo.query}</p>
                          <p><strong>Categories Selected:</strong> {debugInfo.categories}</p>
                          <p><strong>Match Options:</strong> {JSON.stringify(debugInfo.matchOptions)}</p>
                          <p><strong>Results Count:</strong> {debugInfo.resultsCount}</p>
                          <p><strong>Timestamp:</strong> {debugInfo.timestamp}</p>
                        </div>
                      ) : (
                        <p className="text-sm text-gray-500">Run a search to see debug information.</p>
                      )}
                    </div>
                  )}
                </div>
              </CardContent>
            </Card>

            {/* Search Results */}
            <div className="space-y-4">
              <div className="flex items-center justify-between">
                <h2 className="text-xl font-semibold font-['Outfit']">
                  Search Results ({searchResults.length})
                </h2>
              </div>

              {searchResults.map((result, index) => (
                <SearchResultCard key={result.result_id || index} result={result} />
              ))}

              {searchResults.length === 0 && (
                <Card className="glass-card">
                  <CardContent className="py-12 text-center">
                    <Search className="w-12 h-12 text-gray-300 mx-auto mb-4" />
                    <p className="text-gray-500">No results yet. Start searching to collate information!</p>
                  </CardContent>
                </Card>
              )}
            </div>
          </div>
        </div>
      </div>

      {/* New Category Dialog */}
      <Dialog open={showNewCategory} onOpenChange={setShowNewCategory}>
        <DialogContent>
          <DialogHeader>
            <DialogTitle>Create New Category</DialogTitle>
          </DialogHeader>
          <div className="space-y-4 mt-4">
            <div>
              <Label>Category Name</Label>
              <Input 
                placeholder="e.g., American Civil War" 
                value={newCategoryName}
                onChange={(e) => setNewCategoryName(e.target.value)}
                data-testid="new-category-name"
              />
            </div>
            <div>
              <Label>Protocol (InfoJet 2.0)</Label>
              <Textarea 
                placeholder="(term1 or term2) & (term3)+ & (exclude)^"
                value={newCategoryProtocol}
                onChange={(e) => setNewCategoryProtocol(e.target.value)}
                className="font-mono"
                rows={4}
                data-testid="new-category-protocol"
              />
              <p className="text-xs text-gray-500 mt-2">
                Use 'or' for alternatives, '&' between groups, '+' for inclusion, '^' for exclusion
              </p>
            </div>
            <div className="flex justify-end gap-2">
              <Button variant="outline" onClick={() => setShowNewCategory(false)}>Cancel</Button>
              <Button onClick={createCategory} data-testid="create-category-submit">Create Category</Button>
            </div>
          </div>
        </DialogContent>
      </Dialog>
    </div>
  );
};

// ============= SEARCH RESULT CARD =============
const SearchResultCard = ({ result }) => {
  const [showComments, setShowComments] = useState(false);

  const handleReaction = async (reactionType) => {
    try {
      await api.post("/social/reactions", {
        result_id: result.result_id,
        reaction_type: reactionType
      });
    } catch (error) {
      console.error("Reaction error:", error);
    }
  };

  return (
    <Card className="search-result-card" data-testid={`result-${result.result_id}`}>
      <CardContent className="p-6">
        <div className="flex items-start justify-between gap-4">
          <div className="flex-1">
            <div className="flex items-center gap-2 mb-2">
              <Badge className="badge-primary">{result.document_type}</Badge>
              {result.year && <Badge variant="outline">{result.year}</Badge>}
            </div>
            <h3 className="text-lg font-semibold mb-2">
              <a 
                href={result.url} 
                target="_blank" 
                rel="noopener noreferrer"
                className="hover:text-[#007AFF] transition-colors"
              >
                {result.title}
              </a>
            </h3>
            <p className="text-gray-600 text-sm mb-3 truncate-3">{result.snippet}</p>
            <p className="text-xs text-gray-400">{result.root_domain}</p>
          </div>
        </div>

        {/* Reactions */}
        <div className="flex items-center gap-2 mt-4 pt-4 border-t border-gray-100">
          {[
            { type: "Like", icon: ThumbsUp },
            { type: "Love", icon: Heart },
            { type: "Funny", icon: Laugh },
            { type: "Caution", icon: AlertTriangle }
          ].map(({ type, icon: Icon }) => (
            <button
              key={type}
              onClick={() => handleReaction(type)}
              className="reaction-btn"
              data-testid={`reaction-${type.toLowerCase()}`}
            >
              <Icon className="w-4 h-4 inline mr-1" />
              {result.reactions?.[type] || 0}
            </button>
          ))}
          <button 
            className="reaction-btn ml-auto"
            onClick={() => setShowComments(!showComments)}
            data-testid="toggle-comments"
          >
            <MessageSquare className="w-4 h-4 inline mr-1" />
            {result.comments_count || 0} Comments
          </button>
        </div>
      </CardContent>
    </Card>
  );
};

// ============= MAP VIEW PAGE =============
// ============= MAP VIEW PAGE =============
const MapViewPage = () => {
  const [locations, setLocations] = useState([]);
  const [loading, setLoading] = useState(true);
  const [selectedLocation, setSelectedLocation] = useState(null);
  const [locationResults, setLocationResults] = useState([]);
  const [loadingResults, setLoadingResults] = useState(false);

  useEffect(() => {
    fetchMapData();
  }, []);

  const fetchMapData = async () => {
    try {
      const response = await api.get("/stats/map-data-detailed");
      setLocations(response.data.locations || []);
    } catch (error) {
      console.error("Error fetching map data:", error);
    } finally {
      setLoading(false);
    }
  };

  const handleLocationClick = async (location) => {
    setSelectedLocation(location);
    setLoadingResults(true);
    
    try {
      const loc = location.location;
      const locationKey = `${loc.country || ''}_${loc.state || ''}_${loc.city || ''}`;
      const response = await api.get(`/stats/map-location/${encodeURIComponent(locationKey)}`);
      setLocationResults(response.data.results || []);
    } catch (error) {
      console.error("Error fetching location results:", error);
      setLocationResults([]);
    } finally {
      setLoadingResults(false);
    }
  };

  const closeLocationModal = () => {
    setSelectedLocation(null);
    setLocationResults([]);
  };

  return (
    <div className="p-6" data-testid="map-view-page">
      <div className="max-w-7xl mx-auto">
        <h1 className="text-4xl font-bold font-['Outfit'] mb-2">Map View</h1>
        <p className="text-gray-600 mb-6">Click on any location dot to see all associated search results</p>
        
        <Card className="glass-card">
          <CardContent className="p-6">
            <div className="h-[600px] rounded-xl overflow-hidden bg-gradient-to-br from-blue-50 to-green-50">
              {loading ? (
                <div className="h-full flex items-center justify-center">
                  <div className="spinner"></div>
                </div>
              ) : locations.length > 0 ? (
                <div className="h-full relative">
                  {/* World Map Placeholder with Location Dots */}
                  <div className="absolute inset-0 flex items-center justify-center">
                    <Globe className="w-32 h-32 text-[#007AFF]/20" />
                  </div>
                  
                  {/* Location Dots Grid */}
                  <div className="absolute inset-0 p-8 overflow-auto">
                    <div className="grid grid-cols-2 md:grid-cols-3 lg:grid-cols-4 gap-4">
                      {locations.map((loc, index) => (
                        <button
                          key={index}
                          onClick={() => handleLocationClick(loc)}
                          className="group p-4 bg-white rounded-xl shadow-sm hover:shadow-lg transition-all border border-gray-100 hover:border-[#007AFF] text-left"
                          data-testid={`location-dot-${index}`}
                        >
                          <div className="flex items-center gap-3 mb-2">
                            <div className={`w-4 h-4 rounded-full ${
                              loc.count > 10 ? 'bg-[#FF6B6B]' : 
                              loc.count > 5 ? 'bg-[#FFD60A]' : 'bg-[#34C759]'
                            }`} />
                            <span className="font-medium text-sm">
                              {loc.location.city || loc.location.state || loc.location.country || 'Unknown'}
                            </span>
                          </div>
                          <p className="text-xs text-gray-500">
                            {loc.location.state && `${loc.location.state}, `}
                            {loc.location.country}
                          </p>
                          <Badge className="mt-2" variant="outline">
                            {loc.count} result{loc.count !== 1 ? 's' : ''}
                          </Badge>
                        </button>
                      ))}
                    </div>
                  </div>

                  {/* Legend */}
                  <div className="absolute bottom-4 left-4 bg-white/90 backdrop-blur-sm p-3 rounded-lg">
                    <p className="text-xs font-medium mb-2">Results Count</p>
                    <div className="flex items-center gap-4 text-xs">
                      <div className="flex items-center gap-1">
                        <div className="w-3 h-3 rounded-full bg-[#34C759]" />
                        <span>1-5</span>
                      </div>
                      <div className="flex items-center gap-1">
                        <div className="w-3 h-3 rounded-full bg-[#FFD60A]" />
                        <span>6-10</span>
                      </div>
                      <div className="flex items-center gap-1">
                        <div className="w-3 h-3 rounded-full bg-[#FF6B6B]" />
                        <span>10+</span>
                      </div>
                    </div>
                  </div>
                </div>
              ) : (
                <div className="h-full flex flex-col items-center justify-center text-center">
                  <Map className="w-16 h-16 text-gray-300 mb-4" />
                  <p className="text-gray-500">No location data available yet</p>
                  <p className="text-sm text-gray-400 mt-2">
                    Search and collate results to see locations on the map
                  </p>
                </div>
              )}
            </div>
          </CardContent>
        </Card>

        {/* Location Results Modal */}
        <Dialog open={!!selectedLocation} onOpenChange={closeLocationModal}>
          <DialogContent className="max-w-3xl max-h-[80vh] overflow-auto">
            <DialogHeader>
              <DialogTitle className="flex items-center gap-2">
                <Map className="w-5 h-5 text-[#007AFF]" />
                Results from {selectedLocation?.location?.city || selectedLocation?.location?.state || selectedLocation?.location?.country || 'this location'}
              </DialogTitle>
            </DialogHeader>
            
            {loadingResults ? (
              <div className="py-8 text-center">
                <div className="spinner mx-auto"></div>
                <p className="text-gray-500 mt-4">Loading results...</p>
              </div>
            ) : (
              <div className="space-y-4 mt-4">
                <p className="text-sm text-gray-500">{locationResults.length} results found</p>
                
                {locationResults.map((result, idx) => (
                  <Card key={idx} className="hover:shadow-md transition-shadow">
                    <CardContent className="p-4">
                      <div className="flex items-start justify-between gap-4">
                        <div className="flex-1">
                          <Badge className="mb-2" variant="outline">{result.document_type}</Badge>
                          <h3 className="font-semibold text-sm mb-1">
                            <a href={result.url} target="_blank" rel="noopener noreferrer" className="hover:text-[#007AFF]">
                              {result.title}
                            </a>
                          </h3>
                          <p className="text-xs text-gray-500 line-clamp-2">{result.snippet}</p>
                        </div>
                      </div>
                    </CardContent>
                  </Card>
                ))}
                
                {locationResults.length === 0 && (
                  <p className="text-center text-gray-500 py-4">No results found for this location</p>
                )}
              </div>
            )}
          </DialogContent>
        </Dialog>
      </div>
    </div>
  );
};

// ============= STATISTICS PAGE =============
const StatisticsPage = () => {
  const [stats, setStats] = useState(null);
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    fetchStats();
  }, []);

  const fetchStats = async () => {
    try {
      const response = await api.get("/stats/overview");
      setStats(response.data);
    } catch (error) {
      console.error("Error fetching stats:", error);
    } finally {
      setLoading(false);
    }
  };

  const COLORS = ['#007AFF', '#34C759', '#FFD60A', '#FF6B6B', '#9B59B6', '#3498DB'];

  if (loading) {
    return (
      <div className="p-6 flex items-center justify-center min-h-screen">
        <div className="spinner"></div>
      </div>
    );
  }

  return (
    <div className="p-6" data-testid="statistics-page">
      <div className="max-w-7xl mx-auto">
        <h1 className="text-4xl font-bold font-['Outfit'] mb-6">Statistics</h1>

        {/* Overview Cards */}
        <div className="grid grid-cols-1 md:grid-cols-4 gap-6 mb-8">
          <Card className="stat-card">
            <CardContent className="pt-6">
              <div className="flex items-center gap-4">
                <div className="p-3 rounded-full bg-[#007AFF]/10">
                  <Search className="w-6 h-6 text-[#007AFF]" />
                </div>
                <div>
                  <p className="text-2xl font-bold">{stats?.total_results || 0}</p>
                  <p className="text-sm text-gray-500">Total Results</p>
                </div>
              </div>
            </CardContent>
          </Card>
          <Card className="stat-card">
            <CardContent className="pt-6">
              <div className="flex items-center gap-4">
                <div className="p-3 rounded-full bg-[#34C759]/10">
                  <Folder className="w-6 h-6 text-[#34C759]" />
                </div>
                <div>
                  <p className="text-2xl font-bold">{stats?.total_categories || 0}</p>
                  <p className="text-sm text-gray-500">Categories</p>
                </div>
              </div>
            </CardContent>
          </Card>
        </div>

        {/* Charts */}
        <div className="grid grid-cols-1 md:grid-cols-2 gap-6">
          {/* Document Type Distribution */}
          <Card className="glass-card">
            <CardHeader>
              <CardTitle>Document Types</CardTitle>
            </CardHeader>
            <CardContent>
              <ResponsiveContainer width="100%" height={300}>
                <PieChart>
                  <Pie
                    data={stats?.by_document_type || []}
                    cx="50%"
                    cy="50%"
                    innerRadius={60}
                    outerRadius={100}
                    dataKey="count"
                    nameKey="_id"
                    label={({ _id, count }) => `${_id}: ${count}`}
                  >
                    {(stats?.by_document_type || []).map((entry, index) => (
                      <Cell key={`cell-${index}`} fill={COLORS[index % COLORS.length]} />
                    ))}
                  </Pie>
                  <Tooltip />
                </PieChart>
              </ResponsiveContainer>
            </CardContent>
          </Card>

          {/* By Country */}
          <Card className="glass-card">
            <CardHeader>
              <CardTitle>Results by Country</CardTitle>
            </CardHeader>
            <CardContent>
              <ResponsiveContainer width="100%" height={300}>
                <BarChart data={stats?.by_country || []}>
                  <CartesianGrid strokeDasharray="3 3" />
                  <XAxis dataKey="_id" />
                  <YAxis />
                  <Tooltip />
                  <Bar dataKey="count" fill="#007AFF" radius={[4, 4, 0, 0]} />
                </BarChart>
              </ResponsiveContainer>
            </CardContent>
          </Card>

          {/* By Domain */}
          <Card className="glass-card">
            <CardHeader>
              <CardTitle>Top Domains</CardTitle>
            </CardHeader>
            <CardContent>
              <ResponsiveContainer width="100%" height={300}>
                <BarChart data={(stats?.by_domain || []).slice(0, 10)} layout="vertical">
                  <CartesianGrid strokeDasharray="3 3" />
                  <XAxis type="number" />
                  <YAxis dataKey="_id" type="category" width={150} />
                  <Tooltip />
                  <Bar dataKey="count" fill="#34C759" radius={[0, 4, 4, 0]} />
                </BarChart>
              </ResponsiveContainer>
            </CardContent>
          </Card>

          {/* By Year */}
          <Card className="glass-card">
            <CardHeader>
              <CardTitle>Results by Year</CardTitle>
            </CardHeader>
            <CardContent>
              <ResponsiveContainer width="100%" height={300}>
                <LineChart data={stats?.by_year || []}>
                  <CartesianGrid strokeDasharray="3 3" />
                  <XAxis dataKey="_id" />
                  <YAxis />
                  <Tooltip />
                  <Line type="monotone" dataKey="count" stroke="#007AFF" strokeWidth={2} dot={{ fill: '#007AFF' }} />
                </LineChart>
              </ResponsiveContainer>
            </CardContent>
          </Card>
        </div>
      </div>
    </div>
  );
};

// ============= MARKETPLACE PAGE =============
const MarketplacePage = () => {
  const [protocols, setProtocols] = useState([]);
  const [leaderboard, setLeaderboard] = useState(null);
  const [loading, setLoading] = useState(true);
  const [headlines, setHeadlines] = useState([]);
  const [recommendedProtocols, setRecommendedProtocols] = useState([]);
  const [loadingHeadlines, setLoadingHeadlines] = useState(false);
  const [loadingRecommended, setLoadingRecommended] = useState(false);

  useEffect(() => {
    fetchMarketplace();
    fetchLeaderboard();
    fetchHeadlines();
    fetchRecommendedProtocols();
  }, []);

  const fetchMarketplace = async () => {
    try {
      const response = await api.get("/marketplace/protocols");
      setProtocols(response.data.protocols || []);
    } catch (error) {
      console.error("Error fetching marketplace:", error);
    } finally {
      setLoading(false);
    }
  };

  const fetchLeaderboard = async () => {
    try {
      const response = await api.get("/marketplace/leaderboard");
      setLeaderboard(response.data);
    } catch (error) {
      console.error("Error fetching leaderboard:", error);
    }
  };

  const fetchHeadlines = async () => {
    setLoadingHeadlines(true);
    try {
      const response = await api.get("/marketplace/headlines");
      setHeadlines(response.data.headlines || []);
    } catch (error) {
      console.error("Error fetching headlines:", error);
      // Set default headlines if API fails
      setHeadlines([
        { title: "New protocols added daily!", category: "Platform News" },
        { title: "Top seller of the week announced", category: "Community" },
        { title: "AI-powered search now available", category: "Features" }
      ]);
    } finally {
      setLoadingHeadlines(false);
    }
  };

  const fetchRecommendedProtocols = async () => {
    setLoadingRecommended(true);
    try {
      const response = await api.get("/marketplace/recommended");
      setRecommendedProtocols(response.data.protocols || []);
    } catch (error) {
      console.error("Error fetching recommended protocols:", error);
      // Use top protocols as fallback
      if (protocols.length > 0) {
        setRecommendedProtocols(protocols.slice(0, 3));
      }
    } finally {
      setLoadingRecommended(false);
    }
  };

  const handlePurchase = async (categoryId) => {
    try {
      await api.post("/marketplace/purchase", { category_id: categoryId });
      fetchMarketplace();
    } catch (error) {
      console.error("Purchase error:", error);
    }
  };

  const handleCopy = async (categoryId) => {
    try {
      await api.post("/marketplace/copy", { category_id: categoryId });
      alert("Protocol copied to your categories!");
    } catch (error) {
      console.error("Copy error:", error);
    }
  };

  return (
    <div className="p-6" data-testid="marketplace-page">
      <div className="max-w-7xl mx-auto">
        <h1 className="text-4xl font-bold font-['Outfit'] mb-2">Protocol Marketplace</h1>
        <p className="text-gray-600 mb-8">Discover and share powerful search protocols</p>

        {/* Headlines Section */}
        <Card className="glass-card mb-6">
          <CardHeader className="pb-3">
            <div className="flex items-center justify-between">
              <CardTitle className="flex items-center gap-2">
                <Zap className="w-5 h-5 text-[#FFD60A]" /> Headlines
              </CardTitle>
              <Button 
                variant="ghost" 
                size="sm" 
                onClick={fetchHeadlines}
                disabled={loadingHeadlines}
                data-testid="refresh-headlines-btn"
              >
                <RefreshCw className={`w-4 h-4 mr-2 ${loadingHeadlines ? 'animate-spin' : ''}`} /> Refresh Headlines
              </Button>
            </div>
          </CardHeader>
          <CardContent>
            <div className="flex flex-wrap gap-4">
              {headlines.map((headline, i) => (
                <div key={i} className="flex items-center gap-2 px-3 py-2 bg-gray-50 rounded-lg">
                  <Badge variant="outline" className="text-xs">{headline.category}</Badge>
                  <span className="text-sm">{headline.title}</span>
                </div>
              ))}
              {headlines.length === 0 && !loadingHeadlines && (
                <p className="text-sm text-gray-500">No headlines available</p>
              )}
            </div>
          </CardContent>
        </Card>

        {/* Recommended Protocols Section */}
        <Card className="glass-card mb-6">
          <CardHeader className="pb-3">
            <div className="flex items-center justify-between">
              <CardTitle className="flex items-center gap-2">
                <Star className="w-5 h-5 text-[#007AFF]" /> Recommended For You
              </CardTitle>
              <Button 
                variant="ghost" 
                size="sm" 
                onClick={fetchRecommendedProtocols}
                disabled={loadingRecommended}
                data-testid="refresh-recommended-btn"
              >
                <RefreshCw className={`w-4 h-4 mr-2 ${loadingRecommended ? 'animate-spin' : ''}`} /> Refresh
              </Button>
            </div>
          </CardHeader>
          <CardContent>
            {recommendedProtocols.length > 0 ? (
              <div className="grid grid-cols-1 md:grid-cols-3 gap-4">
                {recommendedProtocols.map((protocol, i) => (
                  <div key={protocol.category_id || i} className="p-4 bg-gray-50 rounded-lg">
                    <p className="font-medium">{protocol.name}</p>
                    <p className="text-sm text-gray-500 mt-1">{protocol.sales_count || 0} sales</p>
                    <Button size="sm" variant="outline" className="mt-3" onClick={() => handleCopy(protocol.category_id)}>
                      <Copy className="w-3 h-3 mr-1" /> Copy
                    </Button>
                  </div>
                ))}
              </div>
            ) : (
              <p className="text-sm text-gray-500">
                {loadingRecommended ? 'Loading recommendations...' : 'Keep searching to get personalized recommendations!'}
              </p>
            )}
          </CardContent>
        </Card>

        <div className="grid grid-cols-1 lg:grid-cols-3 gap-6">
          {/* Protocols Grid */}
          <div className="lg:col-span-2 space-y-4">
            {protocols.map((protocol) => (
              <Card key={protocol.category_id} className="glass-card hover-lift" data-testid={`protocol-${protocol.category_id}`}>
                <CardContent className="p-6">
                  <div className="flex items-start justify-between">
                    <div>
                      <h3 className="text-lg font-semibold">{protocol.name}</h3>
                      <p className="text-sm text-gray-500">by {protocol.creator?.name || "Anonymous"}</p>
                    </div>
                    <div className="text-right">
                      {protocol.price > 0 ? (
                        <p className="text-xl font-bold text-[#007AFF]">${protocol.price}</p>
                      ) : (
                        <Badge className="badge-secondary">FREE</Badge>
                      )}
                    </div>
                  </div>
                  <div className="mt-4 p-3 bg-gray-50 rounded-lg">
                    <code className="text-sm font-mono text-gray-600 truncate-2">
                      {protocol.protocol}
                    </code>
                  </div>
                  <div className="flex items-center justify-between mt-4">
                    <div className="flex items-center gap-4 text-sm text-gray-500">
                      <span><TrendingUp className="w-4 h-4 inline mr-1" />{protocol.sales_count} sales</span>
                    </div>
                    {protocol.price > 0 ? (
                      <Button onClick={() => handlePurchase(protocol.category_id)} data-testid={`buy-${protocol.category_id}`}>
                        Purchase
                      </Button>
                    ) : (
                      <Button variant="outline" onClick={() => handleCopy(protocol.category_id)} data-testid={`copy-${protocol.category_id}`}>
                        <Copy className="w-4 h-4 mr-2" /> Copy
                      </Button>
                    )}
                  </div>
                </CardContent>
              </Card>
            ))}

            {protocols.length === 0 && !loading && (
              <Card className="glass-card">
                <CardContent className="py-12 text-center">
                  <ShoppingBag className="w-12 h-12 text-gray-300 mx-auto mb-4" />
                  <p className="text-gray-500">No protocols available yet</p>
                </CardContent>
              </Card>
            )}
          </div>

          {/* Leaderboard */}
          <div className="space-y-6">
            <Card className="glass-card">
              <CardHeader>
                <CardTitle className="flex items-center gap-2">
                  <Award className="w-5 h-5 text-[#FFD60A]" /> Top Sellers
                </CardTitle>
              </CardHeader>
              <CardContent>
                <div className="space-y-3">
                  {(leaderboard?.top_sellers || []).map((seller, i) => (
                    <div key={i} className="flex items-center gap-3">
                      <span className="w-6 h-6 rounded-full bg-[#007AFF]/10 text-[#007AFF] text-sm font-bold flex items-center justify-center">
                        {i + 1}
                      </span>
                      <span className="flex-1">{seller.user?.name || "Anonymous"}</span>
                      <span className="text-sm font-medium">{seller.total_sales} sales</span>
                    </div>
                  ))}
                  {(!leaderboard?.top_sellers || leaderboard.top_sellers.length === 0) && (
                    <p className="text-sm text-gray-500 text-center py-4">No sales yet</p>
                  )}
                </div>
              </CardContent>
            </Card>

            <Card className="glass-card">
              <CardHeader>
                <CardTitle className="flex items-center gap-2">
                  <Copy className="w-5 h-5 text-[#34C759]" /> Most Copied
                </CardTitle>
              </CardHeader>
              <CardContent>
                <div className="space-y-3">
                  {(leaderboard?.most_copied || []).map((item, i) => (
                    <div key={i} className="flex items-center gap-3">
                      <span className="w-6 h-6 rounded-full bg-[#34C759]/10 text-[#34C759] text-sm font-bold flex items-center justify-center">
                        {i + 1}
                      </span>
                      <span className="flex-1 truncate">{item.protocol?.name || "Unknown"}</span>
                      <span className="text-sm font-medium">{item.copy_count}x</span>
                    </div>
                  ))}
                  {(!leaderboard?.most_copied || leaderboard.most_copied.length === 0) && (
                    <p className="text-sm text-gray-500 text-center py-4">No copies yet</p>
                  )}
                </div>
              </CardContent>
            </Card>
          </div>
        </div>
      </div>
    </div>
  );
};

// ============= FRIENDS PAGE =============
const FriendsPage = () => {
  const [friends, setFriends] = useState([]);
  const [searchQuery, setSearchQuery] = useState("");
  const [searchResults, setSearchResults] = useState([]);

  useEffect(() => {
    fetchFriends();
  }, []);

  const fetchFriends = async () => {
    try {
      const response = await api.get("/social/friends");
      setFriends(response.data.friends || []);
    } catch (error) {
      console.error("Error fetching friends:", error);
    }
  };

  const searchUsers = async () => {
    if (!searchQuery.trim()) return;
    try {
      const response = await api.get(`/users/search?q=${searchQuery}`);
      setSearchResults(response.data.users || []);
    } catch (error) {
      console.error("Search error:", error);
    }
  };

  const sendFriendRequest = async (userId) => {
    try {
      await api.post("/social/friends/request", { user_id: userId });
      alert("Friend request sent!");
    } catch (error) {
      console.error("Friend request error:", error);
    }
  };

  return (
    <div className="p-6" data-testid="friends-page">
      <div className="max-w-4xl mx-auto">
        <h1 className="text-4xl font-bold font-['Outfit'] mb-6">Friends</h1>

        {/* Search Users */}
        <Card className="glass-card mb-6">
          <CardContent className="p-6">
            <div className="flex gap-4">
              <Input
                placeholder="Search users by name, email, or username..."
                value={searchQuery}
                onChange={(e) => setSearchQuery(e.target.value)}
                onKeyDown={(e) => e.key === 'Enter' && searchUsers()}
                className="flex-1"
                data-testid="user-search-input"
              />
              <Button onClick={searchUsers} data-testid="search-users-btn">
                <Search className="w-4 h-4 mr-2" /> Search
              </Button>
            </div>

            {searchResults.length > 0 && (
              <div className="mt-4 space-y-2">
                {searchResults.map((user) => (
                  <div key={user.user_id} className="flex items-center justify-between p-3 bg-gray-50 rounded-lg">
                    <div className="flex items-center gap-3">
                      <img src={user.picture || "https://via.placeholder.com/40"} alt={user.name} className="w-10 h-10 rounded-full" />
                      <div>
                        <p className="font-medium">{user.name}</p>
                        <p className="text-sm text-gray-500">{user.callsign || user.user_id}</p>
                      </div>
                    </div>
                    <Button size="sm" onClick={() => sendFriendRequest(user.user_id)} data-testid={`add-friend-${user.user_id}`}>
                      <UserPlus className="w-4 h-4 mr-2" /> Add
                    </Button>
                  </div>
                ))}
              </div>
            )}
          </CardContent>
        </Card>

        {/* Friends List */}
        <Card className="glass-card">
          <CardHeader>
            <CardTitle>Your Friends ({friends.length})</CardTitle>
          </CardHeader>
          <CardContent>
            <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
              {friends.map((friend) => (
                <div key={friend.user_id} className="flex items-center gap-3 p-4 bg-gray-50 rounded-lg">
                  <img src={friend.picture || "https://via.placeholder.com/40"} alt={friend.name} className="w-12 h-12 rounded-full" />
                  <div className="flex-1">
                    <p className="font-medium">{friend.name}</p>
                    <p className="text-sm text-gray-500">{friend.callsign}</p>
                  </div>
                  <Button variant="outline" size="sm" data-testid={`message-${friend.user_id}`}>
                    <MessageCircle className="w-4 h-4" />
                  </Button>
                </div>
              ))}
              {friends.length === 0 && (
                <p className="text-gray-500 col-span-2 text-center py-8">No friends yet. Search for users to connect!</p>
              )}
            </div>
          </CardContent>
        </Card>
      </div>
    </div>
  );
};

// ============= GROUPS PAGE =============
const GroupsPage = () => {
  const [groups, setGroups] = useState([]);
  const [showCreateGroup, setShowCreateGroup] = useState(false);
  const [newGroupName, setNewGroupName] = useState("");
  const [newGroupDescription, setNewGroupDescription] = useState("");
  const [searchByName, setSearchByName] = useState("");
  const [searchByContent, setSearchByContent] = useState("");
  const [filteredGroups, setFilteredGroups] = useState([]);

  useEffect(() => {
    fetchGroups();
  }, []);

  useEffect(() => {
    filterGroups();
  }, [groups, searchByName, searchByContent]);

  const fetchGroups = async () => {
    try {
      const response = await api.get("/groups");
      setGroups(response.data.groups || []);
    } catch (error) {
      console.error("Error fetching groups:", error);
    }
  };

  const filterGroups = () => {
    let results = [...groups];
    
    if (searchByName.trim()) {
      results = results.filter(g => 
        g.name.toLowerCase().includes(searchByName.toLowerCase())
      );
    }
    
    if (searchByContent.trim()) {
      results = results.filter(g => 
        g.description?.toLowerCase().includes(searchByContent.toLowerCase()) ||
        g.posts?.some(p => p.content?.toLowerCase().includes(searchByContent.toLowerCase()))
      );
    }
    
    setFilteredGroups(results);
  };

  const searchGroupsAPI = async () => {
    try {
      const params = new URLSearchParams();
      if (searchByName) params.append("name", searchByName);
      if (searchByContent) params.append("content", searchByContent);
      
      const response = await api.get(`/groups/search?${params.toString()}`);
      setFilteredGroups(response.data.groups || []);
    } catch (error) {
      console.error("Error searching groups:", error);
      filterGroups(); // Fall back to local filtering
    }
  };

  const createGroup = async () => {
    if (!newGroupName.trim()) return;
    try {
      await api.post("/groups", {
        name: newGroupName,
        description: newGroupDescription
      });
      setNewGroupName("");
      setNewGroupDescription("");
      setShowCreateGroup(false);
      fetchGroups();
    } catch (error) {
      console.error("Error creating group:", error);
    }
  };

  const displayGroups = searchByName || searchByContent ? filteredGroups : groups;

  return (
    <div className="p-6" data-testid="groups-page">
      <div className="max-w-4xl mx-auto">
        <div className="flex items-center justify-between mb-6">
          <h1 className="text-4xl font-bold font-['Outfit']">Groups</h1>
          <Button onClick={() => setShowCreateGroup(true)} data-testid="create-group-btn">
            <Plus className="w-4 h-4 mr-2" /> Create Group
          </Button>
        </div>

        {/* Search by Name and Content */}
        <Card className="glass-card mb-6">
          <CardContent className="p-4">
            <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
              <div>
                <Label className="text-sm mb-2 block">Search by Group Name</Label>
                <div className="flex gap-2">
                  <Input
                    placeholder="Search groups by name..."
                    value={searchByName}
                    onChange={(e) => setSearchByName(e.target.value)}
                    data-testid="search-group-name"
                  />
                </div>
              </div>
              <div>
                <Label className="text-sm mb-2 block">Search by Content</Label>
                <div className="flex gap-2">
                  <Input
                    placeholder="Search within groups..."
                    value={searchByContent}
                    onChange={(e) => setSearchByContent(e.target.value)}
                    data-testid="search-group-content"
                  />
                </div>
              </div>
            </div>
            <Button className="mt-4" variant="outline" onClick={searchGroupsAPI} data-testid="search-groups-btn">
              <Search className="w-4 h-4 mr-2" /> Search Groups
            </Button>
          </CardContent>
        </Card>

        <p className="text-sm text-gray-500 mb-4">
          InfoPilot believes it does a better job than Facebook or LinkedIn for collaborative projects, 
          individual projects, certifications, advancement, and social interaction.
        </p>

        <div className="grid grid-cols-1 md:grid-cols-2 gap-6">
          {displayGroups.map((group) => (
            <Card key={group.group_id} className="glass-card hover-lift" data-testid={`group-${group.group_id}`}>
              <CardContent className="p-6">
                <h3 className="text-xl font-semibold mb-2">{group.name}</h3>
                <p className="text-gray-600 text-sm mb-4">{group.description || "No description"}</p>
                <div className="flex items-center justify-between">
                  <span className="text-sm text-gray-500">
                    <Users className="w-4 h-4 inline mr-1" />
                    {group.members?.length || 0} members
                  </span>
                  <Button variant="outline" size="sm">View Group</Button>
                </div>
              </CardContent>
            </Card>
          ))}
          {displayGroups.length === 0 && (
            <Card className="glass-card col-span-2">
              <CardContent className="py-12 text-center">
                <Users className="w-12 h-12 text-gray-300 mx-auto mb-4" />
                <p className="text-gray-500">
                  {searchByName || searchByContent 
                    ? "No groups found matching your search" 
                    : "No groups yet. Create one to start collaborating!"}
                </p>
              </CardContent>
            </Card>
          )}
        </div>

        {/* Create Group Dialog */}
        <Dialog open={showCreateGroup} onOpenChange={setShowCreateGroup}>
          <DialogContent>
            <DialogHeader>
              <DialogTitle>Create New Group</DialogTitle>
            </DialogHeader>
            <div className="space-y-4 mt-4">
              <div>
                <Label>Group Name</Label>
                <Input 
                  placeholder="e.g., Civil War Researchers" 
                  value={newGroupName}
                  onChange={(e) => setNewGroupName(e.target.value)}
                  data-testid="new-group-name"
                />
              </div>
              <div>
                <Label>Description</Label>
                <Textarea 
                  placeholder="What is this group about?"
                  value={newGroupDescription}
                  onChange={(e) => setNewGroupDescription(e.target.value)}
                  data-testid="new-group-description"
                />
              </div>
              <div className="flex justify-end gap-2">
                <Button variant="outline" onClick={() => setShowCreateGroup(false)}>Cancel</Button>
                <Button onClick={createGroup} data-testid="create-group-submit">Create Group</Button>
              </div>
            </div>
          </DialogContent>
        </Dialog>
      </div>
    </div>
  );
};

// ============= CHAT PAGE =============
const ChatPage = () => {
  const [conversations, setConversations] = useState([]);
  const [selectedConversation, setSelectedConversation] = useState(null);
  const [messages, setMessages] = useState([]);
  const [newMessage, setNewMessage] = useState("");
  const { user } = useAuth();

  useEffect(() => {
    fetchConversations();
  }, []);

  useEffect(() => {
    if (selectedConversation) {
      fetchMessages(selectedConversation.conversation_id);
    }
  }, [selectedConversation]);

  const fetchConversations = async () => {
    try {
      const response = await api.get("/chat/conversations");
      setConversations(response.data.conversations || []);
    } catch (error) {
      console.error("Error fetching conversations:", error);
    }
  };

  const fetchMessages = async (conversationId) => {
    try {
      const response = await api.get(`/chat/messages/${conversationId}`);
      setMessages(response.data.messages || []);
    } catch (error) {
      console.error("Error fetching messages:", error);
    }
  };

  const sendMessage = async () => {
    if (!newMessage.trim() || !selectedConversation) return;
    try {
      const otherUserId = selectedConversation.user_ids.find(id => id !== user.user_id);
      await api.post("/chat/messages", {
        recipient_id: otherUserId,
        content: newMessage
      });
      setNewMessage("");
      fetchMessages(selectedConversation.conversation_id);
    } catch (error) {
      console.error("Send message error:", error);
    }
  };

  return (
    <div className="p-6" data-testid="chat-page">
      <div className="max-w-6xl mx-auto">
        <h1 className="text-4xl font-bold font-['Outfit'] mb-6">Messages</h1>

        <div className="grid grid-cols-1 md:grid-cols-3 gap-6 h-[600px]">
          {/* Conversations List */}
          <Card className="glass-card">
            <CardHeader>
              <CardTitle>Conversations</CardTitle>
            </CardHeader>
            <CardContent>
              <ScrollArea className="h-[480px]">
                <div className="space-y-2">
                  {conversations.map((conv) => (
                    <div
                      key={conv.conversation_id}
                      onClick={() => setSelectedConversation(conv)}
                      className={`p-3 rounded-lg cursor-pointer transition-colors ${
                        selectedConversation?.conversation_id === conv.conversation_id 
                          ? 'bg-[#007AFF]/10' 
                          : 'hover:bg-gray-50'
                      }`}
                      data-testid={`conversation-${conv.conversation_id}`}
                    >
                      <div className="flex items-center gap-3">
                        <img 
                          src={conv.other_user?.picture || "https://via.placeholder.com/40"} 
                          alt={conv.other_user?.name}
                          className="w-10 h-10 rounded-full"
                        />
                        <div>
                          <p className="font-medium">{conv.other_user?.name || "Unknown"}</p>
                          <p className="text-xs text-gray-500">
                            {new Date(conv.last_message_at).toLocaleDateString()}
                          </p>
                        </div>
                      </div>
                    </div>
                  ))}
                  {conversations.length === 0 && (
                    <p className="text-sm text-gray-500 text-center py-8">No conversations yet</p>
                  )}
                </div>
              </ScrollArea>
            </CardContent>
          </Card>

          {/* Messages */}
          <Card className="glass-card md:col-span-2">
            <CardContent className="p-6 h-full flex flex-col">
              {selectedConversation ? (
                <>
                  <div className="border-b border-gray-100 pb-4 mb-4">
                    <div className="flex items-center gap-3">
                      <img 
                        src={selectedConversation.other_user?.picture || "https://via.placeholder.com/40"} 
                        alt={selectedConversation.other_user?.name}
                        className="w-10 h-10 rounded-full"
                      />
                      <span className="font-medium">{selectedConversation.other_user?.name}</span>
                    </div>
                  </div>
                  
                  <ScrollArea className="flex-1 mb-4">
                    <div className="space-y-4">
                      {messages.map((msg) => (
                        <div
                          key={msg.message_id}
                          className={`flex ${msg.sender_id === user.user_id ? 'justify-end' : 'justify-start'}`}
                        >
                          <div className={`max-w-[70%] p-3 rounded-2xl ${
                            msg.sender_id === user.user_id 
                              ? 'bg-[#007AFF] text-white' 
                              : 'bg-gray-100'
                          }`}>
                            <p>{msg.content}</p>
                            <p className={`text-xs mt-1 ${
                              msg.sender_id === user.user_id ? 'text-white/70' : 'text-gray-500'
                            }`}>
                              {new Date(msg.created_at).toLocaleTimeString()}
                            </p>
                          </div>
                        </div>
                      ))}
                    </div>
                  </ScrollArea>

                  <div className="flex gap-2">
                    <Input
                      placeholder="Type a message..."
                      value={newMessage}
                      onChange={(e) => setNewMessage(e.target.value)}
                      onKeyDown={(e) => e.key === 'Enter' && sendMessage()}
                      className="flex-1"
                      data-testid="message-input"
                    />
                    <Button onClick={sendMessage} data-testid="send-message-btn">
                      <Send className="w-4 h-4" />
                    </Button>
                  </div>
                </>
              ) : (
                <div className="flex-1 flex items-center justify-center">
                  <div className="text-center">
                    <MessageCircle className="w-12 h-12 text-gray-300 mx-auto mb-4" />
                    <p className="text-gray-500">Select a conversation to start messaging</p>
                  </div>
                </div>
              )}
            </CardContent>
          </Card>
        </div>
      </div>
    </div>
  );
};

// ============= SETTINGS PAGE =============
const SettingsPage = () => {
  const { user } = useAuth();
  const [settings, setSettings] = useState({
    usp_public: true,
    friends_visible: true,
    content_filter: "moderate",
    newsletter_subscribed: false
  });
  const [packages, setPackages] = useState([]);
  const [loadingPayment, setLoadingPayment] = useState(false);
  const [selectedPackage, setSelectedPackage] = useState('monthly');
  const [customAmount, setCustomAmount] = useState('0.99');

  useEffect(() => {
    fetchPackages();
  }, []);

  const fetchPackages = async () => {
    try {
      const response = await api.get("/payments/packages");
      setPackages(response.data.packages || []);
    } catch (error) {
      console.error("Error fetching packages:", error);
    }
  };

  const updateSetting = async (key, value) => {
    setSettings({ ...settings, [key]: value });
    // In a real app, you would save this to the backend
  };

  const handleStripePayment = async () => {
    setLoadingPayment(true);
    try {
      const response = await api.post("/payments/checkout/session", {
        origin_url: window.location.origin,
        package_type: selectedPackage,
        custom_amount: selectedPackage === 'pay_what_you_want' ? parseFloat(customAmount) : undefined
      });
      
      if (response.data.url) {
        window.location.href = response.data.url;
      }
    } catch (error) {
      console.error("Payment error:", error);
      alert("Failed to initiate payment. Please try again.");
    } finally {
      setLoadingPayment(false);
    }
  };

  return (
    <div className="p-6" data-testid="settings-page">
      <div className="max-w-3xl mx-auto">
        <h1 className="text-4xl font-bold font-['Outfit'] mb-6">Settings</h1>

        <div className="space-y-6">
          {/* Profile Settings */}
          <Card className="glass-card">
            <CardHeader>
              <CardTitle>Profile</CardTitle>
            </CardHeader>
            <CardContent className="space-y-4">
              <div className="flex items-center gap-4">
                <img 
                  src={user?.picture || "https://via.placeholder.com/80"} 
                  alt={user?.name}
                  className="w-20 h-20 rounded-full"
                />
                <div>
                  <p className="text-xl font-semibold">{user?.name}</p>
                  <p className="text-gray-500">{user?.email}</p>
                  <Badge className="mt-2">Level {user?.level || 1}</Badge>
                </div>
              </div>
            </CardContent>
          </Card>

          {/* Subscription & Payment */}
          <Card className="glass-card">
            <CardHeader>
              <CardTitle className="flex items-center gap-2">
                <CreditCard className="w-5 h-5 text-[#007AFF]" />
                Subscription
              </CardTitle>
              <CardDescription>First in Flight with Monetization of Searches</CardDescription>
            </CardHeader>
            <CardContent className="space-y-6">
              {user?.is_paid ? (
                <div className="p-4 bg-green-50 rounded-lg border border-green-200">
                  <div className="flex items-center gap-2 text-green-700 mb-2">
                    <CheckCircle className="w-5 h-5" />
                    <span className="font-medium">Premium Subscriber</span>
                  </div>
                  <p className="text-sm text-green-600">
                    {user?.subscription_until 
                      ? `Active until ${new Date(user.subscription_until).toLocaleDateString()}`
                      : 'Your subscription is active'
                    }
                  </p>
                </div>
              ) : (
                <>
                  <div className="grid grid-cols-2 gap-4">
                    {packages.map((pkg) => (
                      <div
                        key={pkg.id}
                        onClick={() => setSelectedPackage(pkg.id)}
                        className={`p-4 rounded-lg border-2 cursor-pointer transition-all ${
                          selectedPackage === pkg.id
                            ? 'border-[#007AFF] bg-[#007AFF]/5'
                            : 'border-gray-200 hover:border-gray-300'
                        }`}
                        data-testid={`package-${pkg.id}`}
                      >
                        <p className="font-semibold">{pkg.name}</p>
                        <p className="text-2xl font-bold text-[#007AFF]">${pkg.price}</p>
                        <p className="text-sm text-gray-500">/{pkg.period}</p>
                        <p className="text-xs text-gray-400 mt-2">{pkg.description}</p>
                      </div>
                    ))}
                  </div>

                  {selectedPackage === 'pay_what_you_want' && (
                    <div>
                      <Label>Your Amount (min $0.75)</Label>
                      <Input
                        type="number"
                        min="0.75"
                        step="0.01"
                        value={customAmount}
                        onChange={(e) => setCustomAmount(e.target.value)}
                        className="w-40"
                        data-testid="custom-amount"
                      />
                    </div>
                  )}

                  <div className="flex flex-col gap-3">
                    <Button 
                      className="btn-primary w-full"
                      onClick={handleStripePayment}
                      disabled={loadingPayment}
                      data-testid="pay-with-stripe"
                    >
                      {loadingPayment ? (
                        <RefreshCw className="w-4 h-4 mr-2 animate-spin" />
                      ) : (
                        <CreditCard className="w-4 h-4 mr-2" />
                      )}
                      Pay with Stripe
                    </Button>
                    <Button
                      variant="outline"
                      className="w-full"
                      onClick={() => window.open('https://www.paypal.com/ncp/payment/LGXMXSG3D2MXU', '_blank')}
                      data-testid="pay-with-paypal"
                    >
                      Pay with PayPal
                    </Button>
                  </div>
                </>
              )}
            </CardContent>
          </Card>

          {/* Privacy Settings */}
          <Card className="glass-card">
            <CardHeader>
              <CardTitle>Privacy</CardTitle>
            </CardHeader>
            <CardContent className="space-y-4">
              <div className="flex items-center justify-between">
                <div>
                  <p className="font-medium">Public Ultimate Search Page</p>
                  <p className="text-sm text-gray-500">Allow others to view your USP</p>
                </div>
                <Checkbox
                  checked={settings.usp_public}
                  onCheckedChange={(checked) => updateSetting('usp_public', checked)}
                  data-testid="setting-usp-public"
                />
              </div>
              <Separator />
              <div className="flex items-center justify-between">
                <div>
                  <p className="font-medium">Visible Friends List</p>
                  <p className="text-sm text-gray-500">Show your friends to other users</p>
                </div>
                <Checkbox
                  checked={settings.friends_visible}
                  onCheckedChange={(checked) => updateSetting('friends_visible', checked)}
                  data-testid="setting-friends-visible"
                />
              </div>
              <Separator />
              <div className="flex items-center justify-between">
                <div>
                  <p className="font-medium">Content Filter</p>
                  <p className="text-sm text-gray-500">Control search result filtering</p>
                </div>
                <Select value={settings.content_filter} onValueChange={(v) => updateSetting('content_filter', v)}>
                  <SelectTrigger className="w-32" data-testid="setting-content-filter">
                    <SelectValue />
                  </SelectTrigger>
                  <SelectContent>
                    <SelectItem value="strict">Strict</SelectItem>
                    <SelectItem value="moderate">Moderate</SelectItem>
                    <SelectItem value="off">Off</SelectItem>
                  </SelectContent>
                </Select>
              </div>
            </CardContent>
          </Card>

          {/* Notifications */}
          <Card className="glass-card">
            <CardHeader>
              <CardTitle>Notifications</CardTitle>
            </CardHeader>
            <CardContent className="space-y-4">
              <div className="flex items-center justify-between">
                <div>
                  <p className="font-medium">Newsletter Subscription</p>
                  <p className="text-sm text-gray-500">Receive our tri-weekly newsletter</p>
                </div>
                <Checkbox
                  checked={settings.newsletter_subscribed}
                  onCheckedChange={(checked) => updateSetting('newsletter_subscribed', checked)}
                  data-testid="setting-newsletter"
                />
              </div>
            </CardContent>
          </Card>

          {/* App Downloads */}
          <Card className="glass-card">
            <CardHeader>
              <CardTitle className="flex items-center gap-2">
                <Download className="w-5 h-5 text-[#007AFF]" />
                Download Apps
              </CardTitle>
            </CardHeader>
            <CardContent>
              <div className="grid grid-cols-2 gap-4">
                <a 
                  href="https://play.google.com/store/apps/details?id=com.infopilot.explorer"
                  target="_blank" 
                  rel="noopener noreferrer"
                  className="flex items-center gap-3 p-4 rounded-lg border border-gray-200 hover:border-[#007AFF] transition-colors"
                  data-testid="download-android-settings"
                >
                  <Smartphone className="w-8 h-8 text-[#34C759]" />
                  <div>
                    <p className="font-medium">Android</p>
                    <p className="text-xs text-gray-500">Google Play Store</p>
                  </div>
                </a>
                <a 
                  href="https://apps.apple.com/app/infojet"
                  target="_blank" 
                  rel="noopener noreferrer"
                  className="flex items-center gap-3 p-4 rounded-lg border border-gray-200 hover:border-[#007AFF] transition-colors"
                  data-testid="download-ios-settings"
                >
                  <Smartphone className="w-8 h-8 text-gray-700" />
                  <div>
                    <p className="font-medium">iOS</p>
                    <p className="text-xs text-gray-500">App Store</p>
                  </div>
                </a>
                <a 
                  href="https://www.infopilotexplorer.biz/download"
                  target="_blank" 
                  rel="noopener noreferrer"
                  className="flex items-center gap-3 p-4 rounded-lg border border-gray-200 hover:border-[#007AFF] transition-colors"
                  data-testid="download-desktop-settings"
                >
                  <Monitor className="w-8 h-8 text-[#007AFF]" />
                  <div>
                    <p className="font-medium">Desktop</p>
                    <p className="text-xs text-gray-500">Windows, macOS, Linux</p>
                  </div>
                </a>
                <a 
                  href="https://chrome.google.com/webstore/detail/infopilot"
                  target="_blank" 
                  rel="noopener noreferrer"
                  className="flex items-center gap-3 p-4 rounded-lg border border-gray-200 hover:border-[#007AFF] transition-colors"
                  data-testid="download-extension-settings"
                >
                  <Globe className="w-8 h-8 text-[#FFD60A]" />
                  <div>
                    <p className="font-medium">Browser Extension</p>
                    <p className="text-xs text-gray-500">Chrome, Firefox, Edge</p>
                  </div>
                </a>
              </div>
            </CardContent>
          </Card>

          {/* Legal Links */}
          <Card className="glass-card">
            <CardHeader>
              <CardTitle>Legal</CardTitle>
            </CardHeader>
            <CardContent>
              <div className="flex flex-wrap gap-4">
                <Link to="/privacy-policy" className="text-[#007AFF] hover:underline flex items-center gap-2">
                  <Shield className="w-4 h-4" /> Privacy Policy
                </Link>
                <Link to="/terms-of-service" className="text-[#007AFF] hover:underline flex items-center gap-2">
                  <Scale className="w-4 h-4" /> Terms of Service
                </Link>
              </div>
              <p className="text-xs text-gray-400 mt-4">
                InfoPilot Explorer - First in Flight with Monetization of Searches
                <br />
                © 2025-2026 Top Pilot Enterprises, Inc.
              </p>
            </CardContent>
          </Card>
        </div>
      </div>
    </div>
  );
};

// ============= GLOBAL RESEARCH PAGE =============
const GlobalResearchPage = () => {
  const [categories, setCategories] = useState([]);
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    fetchGlobalCategories();
  }, []);

  const fetchGlobalCategories = async () => {
    try {
      const response = await api.get("/categories?public_only=true");
      setCategories(response.data.categories || []);
    } catch (error) {
      console.error("Error fetching global categories:", error);
    } finally {
      setLoading(false);
    }
  };

  return (
    <div className="p-6" data-testid="global-research-page">
      <div className="max-w-7xl mx-auto">
        <h1 className="text-4xl font-bold font-['Outfit'] mb-2">Global Research Database</h1>
        <p className="text-gray-600 mb-8">Explore all public categories from the community</p>

        {loading ? (
          <div className="flex justify-center py-12">
            <div className="spinner"></div>
          </div>
        ) : (
          <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-6">
            {categories.map((cat) => (
              <Card key={cat.category_id} className="glass-card hover-lift" data-testid={`global-cat-${cat.category_id}`}>
                <CardContent className="p-6">
                  <h3 className="text-lg font-semibold mb-2">{cat.name}</h3>
                  <div className="p-3 bg-gray-50 rounded-lg mb-4">
                    <code className="text-xs font-mono text-gray-600 truncate-2">
                      {cat.protocol}
                    </code>
                  </div>
                  <Button variant="outline" className="w-full">
                    <Copy className="w-4 h-4 mr-2" /> Copy to My Categories
                  </Button>
                </CardContent>
              </Card>
            ))}
            {categories.length === 0 && (
              <Card className="glass-card col-span-full">
                <CardContent className="py-12 text-center">
                  <Globe className="w-12 h-12 text-gray-300 mx-auto mb-4" />
                  <p className="text-gray-500">No public categories yet</p>
                </CardContent>
              </Card>
            )}
          </div>
        )}
      </div>
    </div>
  );
};

// ============= ADMIN PANEL =============
const AdminPanel = () => {
  const [analytics, setAnalytics] = useState(null);
  const [users, setUsers] = useState([]);
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    fetchAnalytics();
    fetchUsers();
  }, []);

  const fetchAnalytics = async () => {
    try {
      const response = await api.get("/admin/analytics");
      setAnalytics(response.data);
    } catch (error) {
      console.error("Error fetching analytics:", error);
    } finally {
      setLoading(false);
    }
  };

  const fetchUsers = async () => {
    try {
      const response = await api.get("/admin/users");
      setUsers(response.data.users || []);
    } catch (error) {
      console.error("Error fetching users:", error);
    }
  };

  if (loading) {
    return (
      <div className="p-6 flex items-center justify-center min-h-screen">
        <div className="spinner"></div>
      </div>
    );
  }

  return (
    <div className="p-6" data-testid="admin-panel">
      <div className="max-w-7xl mx-auto">
        <h1 className="text-4xl font-bold font-['Outfit'] mb-6">Admin Panel</h1>

        <Tabs defaultValue="analytics">
          <TabsList>
            <TabsTrigger value="analytics">Analytics</TabsTrigger>
            <TabsTrigger value="users">Users</TabsTrigger>
            <TabsTrigger value="settings">Settings</TabsTrigger>
          </TabsList>

          <TabsContent value="analytics" className="mt-6">
            <div className="grid grid-cols-1 md:grid-cols-4 gap-6 mb-8">
              <Card className="stat-card">
                <CardContent className="pt-6">
                  <p className="text-3xl font-bold">{analytics?.total_users || 0}</p>
                  <p className="text-sm text-gray-500">Total Users</p>
                </CardContent>
              </Card>
              <Card className="stat-card">
                <CardContent className="pt-6">
                  <p className="text-3xl font-bold">{analytics?.paid_users || 0}</p>
                  <p className="text-sm text-gray-500">Paid Users</p>
                </CardContent>
              </Card>
              <Card className="stat-card">
                <CardContent className="pt-6">
                  <p className="text-3xl font-bold">{analytics?.total_categories || 0}</p>
                  <p className="text-sm text-gray-500">Categories</p>
                </CardContent>
              </Card>
              <Card className="stat-card">
                <CardContent className="pt-6">
                  <p className="text-3xl font-bold">{analytics?.total_results || 0}</p>
                  <p className="text-sm text-gray-500">Search Results</p>
                </CardContent>
              </Card>
            </div>
          </TabsContent>

          <TabsContent value="users" className="mt-6">
            <Card className="glass-card">
              <CardContent className="p-6">
                <div className="overflow-x-auto">
                  <table className="w-full">
                    <thead>
                      <tr className="border-b">
                        <th className="text-left py-3 px-4">User</th>
                        <th className="text-left py-3 px-4">Email</th>
                        <th className="text-left py-3 px-4">Status</th>
                        <th className="text-left py-3 px-4">Actions</th>
                      </tr>
                    </thead>
                    <tbody>
                      {users.map((u) => (
                        <tr key={u.user_id} className="border-b">
                          <td className="py-3 px-4">
                            <div className="flex items-center gap-3">
                              <img src={u.picture || "https://via.placeholder.com/32"} alt={u.name} className="w-8 h-8 rounded-full" />
                              <span>{u.name}</span>
                            </div>
                          </td>
                          <td className="py-3 px-4">{u.email}</td>
                          <td className="py-3 px-4">
                            {u.is_paid ? (
                              <Badge className="badge-secondary">Paid</Badge>
                            ) : (
                              <Badge variant="outline">Free</Badge>
                            )}
                          </td>
                          <td className="py-3 px-4">
                            <Button variant="ghost" size="sm">View</Button>
                          </td>
                        </tr>
                      ))}
                    </tbody>
                  </table>
                </div>
              </CardContent>
            </Card>
          </TabsContent>

          <TabsContent value="settings" className="mt-6">
            <Card className="glass-card">
              <CardContent className="p-6">
                <p className="text-gray-500">Admin settings coming soon...</p>
              </CardContent>
            </Card>
          </TabsContent>
        </Tabs>
      </div>
    </div>
  );
};

// ============= EASTER EGGS PAGE =============
const EasterEggsPage = () => {
  const [eggs, setEggs] = useState([]);
  const [leaderboard, setLeaderboard] = useState(null);

  useEffect(() => {
    fetchEasterEggs();
    fetchLeaderboard();
  }, []);

  const fetchEasterEggs = async () => {
    try {
      const response = await api.get("/easter-eggs");
      setEggs(response.data.easter_eggs || []);
    } catch (error) {
      console.error("Error fetching easter eggs:", error);
    }
  };

  const fetchLeaderboard = async () => {
    try {
      const response = await api.get("/easter-eggs/laugh-leaderboard");
      setLeaderboard(response.data);
    } catch (error) {
      console.error("Error fetching leaderboard:", error);
    }
  };

  const submitLaugh = async (eggId, laughType) => {
    try {
      const response = await api.post("/easter-eggs/laugh-submit", {
        egg_id: eggId,
        rating: laughType === 'rofl' ? 10 : laughType === 'laugh' ? 7 : 4,
        laugh_type: laughType
      });
      alert(`You earned ${response.data.xp_earned} XP! 😄`);
    } catch (error) {
      console.error("Error submitting laugh:", error);
    }
  };

  return (
    <div className="p-6" data-testid="easter-eggs-page">
      <div className="max-w-5xl mx-auto">
        <h1 className="text-4xl font-bold font-['Outfit'] mb-2">Easter Eggs 🥚</h1>
        <p className="text-gray-600 mb-8">Discover jokes, earn XP, and climb the Laugh-O-Meter!</p>

        <div className="grid grid-cols-1 md:grid-cols-2 gap-6">
          {/* Jokes */}
          <div className="space-y-4">
            <h2 className="text-xl font-semibold">Jokes</h2>
            {eggs.map((egg, i) => (
              <Card key={egg.egg_id || i} className="glass-card hover-lift easter-egg" data-testid={`easter-egg-${i}`}>
                <CardContent className="p-6">
                  <p className="text-lg mb-4">{egg.content}</p>
                  <div className="flex gap-2">
                    <Button size="sm" variant="outline" onClick={() => submitLaugh(egg.egg_id, 'chuckle')}>
                      😏 Chuckle (+1 XP)
                    </Button>
                    <Button size="sm" variant="outline" onClick={() => submitLaugh(egg.egg_id, 'laugh')}>
                      😂 Laugh (+3 XP)
                    </Button>
                    <Button size="sm" variant="outline" onClick={() => submitLaugh(egg.egg_id, 'rofl')}>
                      🤣 ROFL (+5 XP)
                    </Button>
                  </div>
                </CardContent>
              </Card>
            ))}
          </div>

          {/* Leaderboard */}
          <div className="space-y-4">
            <Card className="glass-card">
              <CardHeader>
                <CardTitle>🏆 Laugh-O-Meter Champions</CardTitle>
              </CardHeader>
              <CardContent>
                <div className="space-y-3">
                  {(leaderboard?.top_laughers || []).map((entry, i) => (
                    <div key={i} className="flex items-center gap-3">
                      <span className="w-8 h-8 rounded-full bg-yellow-100 text-yellow-800 font-bold flex items-center justify-center">
                        {i + 1}
                      </span>
                      <span className="flex-1">{entry.user?.name || "Anonymous"}</span>
                      <span className="text-sm">{entry.total_laughs} laughs</span>
                    </div>
                  ))}
                </div>
              </CardContent>
            </Card>

            <Card className="glass-card">
              <CardHeader>
                <CardTitle>😂 Funniest Jokes</CardTitle>
              </CardHeader>
              <CardContent>
                <div className="space-y-3">
                  {(leaderboard?.funniest_jokes || []).map((entry, i) => (
                    <div key={i} className="flex items-center gap-3">
                      <span className="w-8 h-8 rounded-full bg-green-100 text-green-800 font-bold flex items-center justify-center">
                        #{entry._id?.replace('egg_', '')}
                      </span>
                      <span className="text-sm">Rating: {entry.avg_rating?.toFixed(1)}/10</span>
                      <span className="text-sm text-gray-500">({entry.total_laughs} laughs)</span>
                    </div>
                  ))}
                </div>
              </CardContent>
            </Card>
          </div>
        </div>
      </div>
    </div>
  );
};

// ============= QUOTE GALLERY PAGE =============
const QuotesPage = () => {
  const [quotes, setQuotes] = useState([]);
  const [allQuotes, setAllQuotes] = useState([]);
  const [showAll, setShowAll] = useState(false);

  useEffect(() => {
    fetchQuotes();
  }, []);

  const fetchQuotes = async () => {
    try {
      const response = await api.get("/quotes?count=10");
      setQuotes(response.data.quotes || []);
      
      const allResponse = await api.get("/quotes/all");
      setAllQuotes(allResponse.data.quotes || []);
    } catch (error) {
      console.error("Error fetching quotes:", error);
    }
  };

  return (
    <div className="p-6" data-testid="quotes-page">
      <div className="max-w-4xl mx-auto">
        <h1 className="text-4xl font-bold font-['Outfit'] mb-2">Quote Gallery 📜</h1>
        <p className="text-gray-600 mb-8">Wisdom from the InfoPilot manuscript ({allQuotes.length} quotes)</p>

        <div className="flex gap-4 mb-6">
          <Button 
            variant={showAll ? "outline" : "default"} 
            onClick={() => setShowAll(false)}
          >
            Random 10
          </Button>
          <Button 
            variant={showAll ? "default" : "outline"} 
            onClick={() => setShowAll(true)}
          >
            Show All
          </Button>
          <Button variant="outline" onClick={fetchQuotes}>
            <RefreshCw className="w-4 h-4 mr-2" /> Refresh
          </Button>
        </div>

        <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
          {(showAll ? allQuotes : quotes).map((quote, i) => (
            <Card key={i} className="glass-card hover-lift" style={{ animationDelay: `${i * 0.1}s` }}>
              <CardContent className="p-6">
                <blockquote className="text-lg italic text-gray-700 border-l-4 border-[#007AFF] pl-4">
                  "{quote}"
                </blockquote>
              </CardContent>
            </Card>
          ))}
        </div>
      </div>
    </div>
  );
};

// ============= THEMES PAGE =============
const ThemesPage = () => {
  const [presets, setPresets] = useState({});
  const [currentTheme, setCurrentTheme] = useState('default');
  const [customColors, setCustomColors] = useState({
    background: '#FFFFF0',
    primary: '#007AFF',
    secondary: '#34C759',
    accent: '#FFD60A'
  });

  useEffect(() => {
    fetchThemes();
  }, []);

  const fetchThemes = async () => {
    try {
      const response = await api.get("/themes/presets");
      setPresets(response.data.presets || {});
    } catch (error) {
      console.error("Error fetching themes:", error);
    }
  };

  const applyTheme = (presetKey) => {
    setCurrentTheme(presetKey);
    const preset = presets[presetKey];
    if (preset) {
      document.documentElement.style.setProperty('--background', preset.background);
      document.documentElement.style.setProperty('--primary', preset.primary);
      document.documentElement.style.setProperty('--secondary', preset.secondary);
    }
  };

  const saveTheme = async () => {
    try {
      await api.post("/themes/save", {
        preset: currentTheme,
        custom: customColors,
        dark_mode: currentTheme === 'dark'
      });
      alert("Theme saved!");
    } catch (error) {
      console.error("Error saving theme:", error);
    }
  };

  return (
    <div className="p-6" data-testid="themes-page">
      <div className="max-w-4xl mx-auto">
        <h1 className="text-4xl font-bold font-['Outfit'] mb-2">Theme Gallery 🎨</h1>
        <p className="text-gray-600 mb-8">Customize your InfoPilot experience</p>

        <div className="grid grid-cols-2 md:grid-cols-4 gap-4 mb-8">
          {Object.entries(presets).map(([key, preset]) => (
            <Card 
              key={key} 
              className={`glass-card hover-lift cursor-pointer ${currentTheme === key ? 'ring-2 ring-[#007AFF]' : ''}`}
              onClick={() => applyTheme(key)}
              data-testid={`theme-${key}`}
            >
              <CardContent className="p-4">
                <div className="flex gap-1 mb-3">
                  <div className="w-8 h-8 rounded" style={{ backgroundColor: preset.background, border: '1px solid #ccc' }}></div>
                  <div className="w-8 h-8 rounded" style={{ backgroundColor: preset.primary }}></div>
                  <div className="w-8 h-8 rounded" style={{ backgroundColor: preset.secondary }}></div>
                </div>
                <p className="font-medium text-sm">{preset.name}</p>
              </CardContent>
            </Card>
          ))}
        </div>

        <Card className="glass-card">
          <CardHeader>
            <CardTitle>Current Theme: {presets[currentTheme]?.name || 'Default'}</CardTitle>
          </CardHeader>
          <CardContent>
            <Button onClick={saveTheme}>Save as My Theme</Button>
          </CardContent>
        </Card>
      </div>
    </div>
  );
};

// ============= COMMUNITY LEADERBOARD PAGE =============
const LeaderboardPage = () => {
  const [leaderboard, setLeaderboard] = useState(null);
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    fetchLeaderboard();
  }, []);

  const fetchLeaderboard = async () => {
    try {
      const response = await api.get("/social/leaderboard");
      setLeaderboard(response.data);
    } catch (error) {
      console.error("Error fetching leaderboard:", error);
    } finally {
      setLoading(false);
    }
  };

  if (loading) {
    return (
      <div className="p-6 flex items-center justify-center min-h-screen">
        <div className="spinner"></div>
      </div>
    );
  }

  return (
    <div className="p-6" data-testid="leaderboard-page">
      <div className="max-w-5xl mx-auto">
        <h1 className="text-4xl font-bold font-['Outfit'] mb-2">Community Leaderboard 🏆</h1>
        <p className="text-gray-600 mb-8">Top protocol creators and researchers</p>

        <div className="grid grid-cols-1 md:grid-cols-3 gap-6">
          {/* Top Sellers */}
          <Card className="glass-card">
            <CardHeader>
              <CardTitle className="flex items-center gap-2">
                <ShoppingBag className="w-5 h-5 text-[#007AFF]" /> Top Sellers
              </CardTitle>
            </CardHeader>
            <CardContent>
              <div className="space-y-3">
                {(leaderboard?.top_sellers || []).map((seller, i) => (
                  <div key={i} className="flex items-center gap-3">
                    <span className={`w-8 h-8 rounded-full flex items-center justify-center font-bold ${
                      i === 0 ? 'bg-yellow-100 text-yellow-800' :
                      i === 1 ? 'bg-gray-100 text-gray-800' :
                      i === 2 ? 'bg-orange-100 text-orange-800' :
                      'bg-gray-50 text-gray-600'
                    }`}>
                      {i + 1}
                    </span>
                    <img 
                      src={seller.user?.picture || "https://via.placeholder.com/32"} 
                      alt={seller.user?.name}
                      className="w-8 h-8 rounded-full"
                    />
                    <div className="flex-1">
                      <p className="font-medium text-sm">{seller.user?.name || "Anonymous"}</p>
                      <p className="text-xs text-gray-500">{seller.protocol_count} protocols</p>
                    </div>
                    <Badge>{seller.total_sales} sales</Badge>
                  </div>
                ))}
              </div>
            </CardContent>
          </Card>

          {/* Rising Stars */}
          <Card className="glass-card">
            <CardHeader>
              <CardTitle className="flex items-center gap-2">
                <Star className="w-5 h-5 text-[#FFD60A]" /> Rising Stars
              </CardTitle>
            </CardHeader>
            <CardContent>
              <div className="space-y-3">
                {(leaderboard?.rising_stars || []).map((star, i) => (
                  <div key={i} className="flex items-center gap-3">
                    <span className={`w-8 h-8 rounded-full flex items-center justify-center font-bold ${
                      i === 0 ? 'bg-purple-100 text-purple-800' :
                      'bg-gray-50 text-gray-600'
                    }`}>
                      {i + 1}
                    </span>
                    <span className="flex-1 text-sm">{star.user?.name || "Anonymous"}</span>
                    <Badge variant="outline">{star.total_copies}x copied</Badge>
                  </div>
                ))}
              </div>
            </CardContent>
          </Card>

          {/* Top XP */}
          <Card className="glass-card">
            <CardHeader>
              <CardTitle className="flex items-center gap-2">
                <Zap className="w-5 h-5 text-[#34C759]" /> Top XP Earners
              </CardTitle>
            </CardHeader>
            <CardContent>
              <div className="space-y-3">
                {(leaderboard?.top_xp || []).map((user, i) => (
                  <div key={i} className="flex items-center gap-3">
                    <span className={`w-8 h-8 rounded-full flex items-center justify-center font-bold ${
                      i === 0 ? 'bg-green-100 text-green-800' :
                      'bg-gray-50 text-gray-600'
                    }`}>
                      {i + 1}
                    </span>
                    <img 
                      src={user.picture || "https://via.placeholder.com/32"} 
                      alt={user.name}
                      className="w-8 h-8 rounded-full"
                    />
                    <div className="flex-1">
                      <p className="font-medium text-sm">{user.name}</p>
                      <p className="text-xs text-gray-500">Level {user.level || 1}</p>
                    </div>
                    <Badge className="badge-secondary">{user.xp} XP</Badge>
                  </div>
                ))}
              </div>
            </CardContent>
          </Card>
        </div>
      </div>
    </div>
  );
};

// ============= PERSONAL REPORTS PAGE =============
const PersonalReportsPage = () => {
  const [reports, setReports] = useState([]);
  const [showCreate, setShowCreate] = useState(false);
  const [newReport, setNewReport] = useState({ title: '', content: '', location: { city: '', state: '', country: 'USA' } });

  useEffect(() => {
    fetchReports();
  }, []);

  const fetchReports = async () => {
    try {
      const response = await api.get("/reports");
      setReports(response.data.reports || []);
    } catch (error) {
      console.error("Error fetching reports:", error);
    }
  };

  const createReport = async () => {
    if (!newReport.title.trim() || !newReport.content.trim()) return;
    try {
      await api.post("/reports", newReport);
      setNewReport({ title: '', content: '', location: { city: '', state: '', country: 'USA' } });
      setShowCreate(false);
      fetchReports();
    } catch (error) {
      console.error("Error creating report:", error);
    }
  };

  return (
    <div className="p-6" data-testid="reports-page">
      <div className="max-w-4xl mx-auto">
        <div className="flex items-center justify-between mb-6">
          <div>
            <h1 className="text-4xl font-bold font-['Outfit']">Personal Reports 📝</h1>
            <p className="text-gray-600">Share your research experiences and discoveries</p>
          </div>
          <Button onClick={() => setShowCreate(true)} data-testid="create-report-btn">
            <Plus className="w-4 h-4 mr-2" /> Create Report
          </Button>
        </div>

        <div className="space-y-4">
          {reports.map((report) => (
            <Card key={report.report_id} className="glass-card hover-lift" data-testid={`report-${report.report_id}`}>
              <CardContent className="p-6">
                <h3 className="text-xl font-semibold mb-2">{report.title}</h3>
                <p className="text-gray-600 mb-4">{report.content}</p>
                {report.location && (
                  <div className="flex items-center gap-2 text-sm text-gray-500">
                    <Map className="w-4 h-4" />
                    <span>{report.location.city}, {report.location.state}</span>
                  </div>
                )}
                {report.images && report.images.length > 0 && (
                  <div className="flex gap-2 mt-4">
                    {report.images.map((img, i) => (
                      <img key={i} src={img} alt={`Report ${i + 1}`} className="w-24 h-24 object-cover rounded-lg" />
                    ))}
                  </div>
                )}
              </CardContent>
            </Card>
          ))}
          {reports.length === 0 && (
            <Card className="glass-card">
              <CardContent className="py-12 text-center">
                <BookOpen className="w-12 h-12 text-gray-300 mx-auto mb-4" />
                <p className="text-gray-500">No reports yet. Create your first personal report!</p>
              </CardContent>
            </Card>
          )}
        </div>

        <Dialog open={showCreate} onOpenChange={setShowCreate}>
          <DialogContent>
            <DialogHeader>
              <DialogTitle>Create Personal Report</DialogTitle>
            </DialogHeader>
            <div className="space-y-4 mt-4">
              <div>
                <Label>Title</Label>
                <Input
                  placeholder="My Research Discovery"
                  value={newReport.title}
                  onChange={(e) => setNewReport({ ...newReport, title: e.target.value })}
                  data-testid="report-title"
                />
              </div>
              <div>
                <Label>Content</Label>
                <Textarea
                  placeholder="Share your research experience..."
                  value={newReport.content}
                  onChange={(e) => setNewReport({ ...newReport, content: e.target.value })}
                  rows={6}
                  data-testid="report-content"
                />
              </div>
              <div className="grid grid-cols-2 gap-4">
                <div>
                  <Label>City</Label>
                  <Input
                    placeholder="Gettysburg"
                    value={newReport.location.city}
                    onChange={(e) => setNewReport({ ...newReport, location: { ...newReport.location, city: e.target.value } })}
                  />
                </div>
                <div>
                  <Label>State</Label>
                  <Input
                    placeholder="Pennsylvania"
                    value={newReport.location.state}
                    onChange={(e) => setNewReport({ ...newReport, location: { ...newReport.location, state: e.target.value } })}
                  />
                </div>
              </div>
              <p className="text-xs text-gray-500">You can add up to 3 images (feature coming soon)</p>
              <div className="flex justify-end gap-2">
                <Button variant="outline" onClick={() => setShowCreate(false)}>Cancel</Button>
                <Button onClick={createReport} data-testid="submit-report">Create Report</Button>
              </div>
            </div>
          </DialogContent>
        </Dialog>
      </div>
    </div>
  );
};

// ============= LETTERS TO EVELYN BOOK PAGE =============
const BookPage = () => {
  const [bookInfo, setBookInfo] = useState(null);
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    fetchBookInfo();
  }, []);

  const fetchBookInfo = async () => {
    try {
      const response = await api.get("/promotions/book");
      setBookInfo(response.data);
    } catch (error) {
      console.error("Error fetching book info:", error);
    } finally {
      setLoading(false);
    }
  };

  if (loading) {
    return (
      <div className="p-6 flex items-center justify-center min-h-screen">
        <div className="spinner"></div>
      </div>
    );
  }

  return (
    <div className="p-6" data-testid="book-page">
      <div className="max-w-4xl mx-auto">
        <div className="glass-card p-8 mb-8">
          <div className="text-center mb-8">
            <Badge className="badge-primary mb-4">{bookInfo?.tagline}</Badge>
            <h1 className="text-5xl font-bold font-['Outfit'] mb-4">{bookInfo?.title}</h1>
            <p className="text-xl text-gray-600">by {bookInfo?.author}</p>
          </div>
          
          <p className="text-lg text-center text-gray-700 mb-8">{bookInfo?.description}</p>

          <div className="grid md:grid-cols-3 gap-4 mb-8">
            <Card className="text-center p-4">
              <p className="text-2xl font-bold text-[#007AFF]">${bookInfo?.prices?.ebook}</p>
              <p className="text-sm text-gray-500">eBook</p>
            </Card>
            <Card className="text-center p-4 ring-2 ring-[#007AFF]">
              <p className="text-2xl font-bold text-[#007AFF]">${bookInfo?.prices?.paperback}</p>
              <p className="text-sm text-gray-500">Paperback</p>
            </Card>
            <Card className="text-center p-4">
              <p className="text-2xl font-bold text-[#007AFF]">${bookInfo?.prices?.hardcover}</p>
              <p className="text-sm text-gray-500">Hardcover</p>
            </Card>
          </div>

          <div className="flex flex-wrap justify-center gap-4 mb-8">
            <Button 
              className="btn-primary px-8"
              onClick={() => window.open(bookInfo?.purchase_links?.amazon_paperback, '_blank')}
              data-testid="buy-amazon"
            >
              Buy on Amazon
            </Button>
            <Button 
              variant="outline"
              onClick={() => window.open(bookInfo?.purchase_links?.paypal, '_blank')}
              data-testid="buy-paypal"
            >
              Buy via PayPal
            </Button>
          </div>
        </div>

        <h2 className="text-2xl font-semibold mb-4">Features</h2>
        <ul className="space-y-2 mb-8">
          {(bookInfo?.features || []).map((feature, i) => (
            <li key={i} className="flex items-center gap-2">
              <Check className="w-5 h-5 text-[#34C759]" />
              <span>{feature}</span>
            </li>
          ))}
        </ul>

        <h2 className="text-2xl font-semibold mb-4">Reviews</h2>
        <div className="grid md:grid-cols-2 gap-4">
          {(bookInfo?.reviews || []).map((review, i) => (
            <Card key={i} className="glass-card">
              <CardContent className="p-4">
                <div className="flex items-center gap-1 mb-2">
                  {[...Array(review.rating)].map((_, j) => (
                    <Star key={j} className="w-4 h-4 fill-yellow-400 text-yellow-400" />
                  ))}
                </div>
                <p className="text-gray-700 italic mb-2">"{review.text}"</p>
                <p className="text-sm text-gray-500">- {review.reviewer}</p>
              </CardContent>
            </Card>
          ))}
        </div>
      </div>
    </div>
  );
};

// ============= LEGAL PAGE (Privacy Policy / Terms of Service) =============
const LegalPage = ({ docType }) => {
  const [document, setDocument] = useState(null);
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    fetchDocument();
  }, [docType]);

  const fetchDocument = async () => {
    try {
      // Use axios directly without auth for public legal pages
      const response = await axios.get(`${API}/legal/${docType}`);
      setDocument(response.data);
    } catch (error) {
      console.error("Error fetching legal document:", error);
    } finally {
      setLoading(false);
    }
  };

  if (loading) {
    return (
      <div className="p-6 flex items-center justify-center min-h-screen">
        <div className="spinner"></div>
      </div>
    );
  }

  return (
    <div className="min-h-screen bg-[#FFFFF0] py-12 px-6" data-testid={`legal-${docType}`}>
      <div className="max-w-3xl mx-auto">
        <Link to="/" className="flex items-center gap-2 text-[#007AFF] mb-8 hover:underline">
          <Globe className="w-5 h-5" />
          Back to InfoPilot Explorer
        </Link>
        
        <Card className="glass-card">
          <CardContent className="p-8">
            <div className="flex items-center gap-3 mb-6">
              {docType === 'privacy-policy' ? (
                <Shield className="w-8 h-8 text-[#007AFF]" />
              ) : (
                <Scale className="w-8 h-8 text-[#007AFF]" />
              )}
              <div>
                <h1 className="text-3xl font-bold font-['Outfit']">{document?.title}</h1>
                <p className="text-sm text-gray-500">Last Updated: {document?.last_updated}</p>
              </div>
            </div>
            
            <div className="prose prose-slate max-w-none">
              {/* Render markdown-like content */}
              {document?.content?.split('\n').map((line, i) => {
                if (line.startsWith('# ')) {
                  return <h1 key={i} className="text-2xl font-bold mt-8 mb-4">{line.substring(2)}</h1>;
                } else if (line.startsWith('## ')) {
                  return <h2 key={i} className="text-xl font-semibold mt-6 mb-3">{line.substring(3)}</h2>;
                } else if (line.startsWith('### ')) {
                  return <h3 key={i} className="text-lg font-medium mt-4 mb-2">{line.substring(4)}</h3>;
                } else if (line.startsWith('- ')) {
                  return <li key={i} className="ml-4">{line.substring(2)}</li>;
                } else if (line.startsWith('**') && line.endsWith('**')) {
                  return <p key={i} className="font-bold">{line.slice(2, -2)}</p>;
                } else if (line.startsWith('*') && line.endsWith('*')) {
                  return <p key={i} className="italic text-gray-600">{line.slice(1, -1)}</p>;
                } else if (line.startsWith('---')) {
                  return <hr key={i} className="my-6 border-gray-200" />;
                } else if (line.trim() === '') {
                  return <br key={i} />;
                } else {
                  return <p key={i} className="my-2">{line}</p>;
                }
              })}
            </div>
          </CardContent>
        </Card>
      </div>
    </div>
  );
};

// ============= PROTOCOL TEMPLATES PAGE =============
const ProtocolTemplatesPage = () => {
  const [templates, setTemplates] = useState([]);
  const [loading, setLoading] = useState(true);
  const [showCreate, setShowCreate] = useState(false);
  const [newTemplate, setNewTemplate] = useState({
    name: '',
    description: '',
    protocol_string: '',
    category: 'General',
    is_public: false
  });

  useEffect(() => {
    fetchTemplates();
  }, []);

  const fetchTemplates = async () => {
    try {
      const response = await api.get("/templates");
      setTemplates(response.data.templates || []);
    } catch (error) {
      console.error("Error fetching templates:", error);
    } finally {
      setLoading(false);
    }
  };

  const createTemplate = async () => {
    if (!newTemplate.name.trim() || !newTemplate.protocol_string.trim()) return;
    try {
      await api.post("/templates", newTemplate);
      setNewTemplate({ name: '', description: '', protocol_string: '', category: 'General', is_public: false });
      setShowCreate(false);
      fetchTemplates();
    } catch (error) {
      console.error("Error creating template:", error);
    }
  };

  const applyTemplate = async (templateId) => {
    try {
      await api.post(`/templates/${templateId}/use`);
      alert("Category created from template!");
    } catch (error) {
      console.error("Error using template:", error);
    }
  };

  const deleteTemplate = async (templateId) => {
    if (!window.confirm("Delete this template?")) return;
    try {
      await api.delete(`/templates/${templateId}`);
      fetchTemplates();
    } catch (error) {
      console.error("Error deleting template:", error);
    }
  };

  return (
    <div className="p-6" data-testid="templates-page">
      <div className="max-w-6xl mx-auto">
        <div className="flex items-center justify-between mb-8">
          <div>
            <h1 className="text-4xl font-bold font-['Outfit']">Protocol Templates</h1>
            <p className="text-gray-600">Create and use predefined protocol templates</p>
          </div>
          <Button onClick={() => setShowCreate(true)} data-testid="create-template-btn">
            <Plus className="w-4 h-4 mr-2" /> Create Template
          </Button>
        </div>

        {loading ? (
          <div className="text-center py-12">
            <div className="spinner mx-auto"></div>
          </div>
        ) : (
          <div className="grid md:grid-cols-2 lg:grid-cols-3 gap-6">
            {templates.map((template) => (
              <Card key={template.template_id} className="glass-card hover-lift" data-testid={`template-${template.template_id}`}>
                <CardContent className="p-6">
                  <div className="flex items-start justify-between mb-3">
                    <div>
                      <h3 className="text-lg font-semibold">{template.name}</h3>
                      <p className="text-sm text-gray-500">{template.creator?.name || 'You'}</p>
                    </div>
                    <Badge variant={template.is_public ? "default" : "secondary"}>
                      {template.is_public ? "Public" : "Private"}
                    </Badge>
                  </div>
                  
                  <p className="text-sm text-gray-600 mb-3">{template.description}</p>
                  
                  <div className="bg-gray-50 p-3 rounded-lg mb-4">
                    <code className="text-xs font-mono text-gray-700 break-all">
                      {template.protocol_string}
                    </code>
                  </div>
                  
                  <div className="flex items-center justify-between">
                    <Badge variant="outline">{template.category}</Badge>
                    <div className="flex gap-2">
                      <Button size="sm" onClick={() => applyTemplate(template.template_id)} data-testid={`use-template-${template.template_id}`}>
                        <Play className="w-4 h-4 mr-1" /> Use
                      </Button>
                      <Button size="sm" variant="ghost" onClick={() => deleteTemplate(template.template_id)}>
                        <Trash2 className="w-4 h-4" />
                      </Button>
                    </div>
                  </div>
                  
                  <p className="text-xs text-gray-400 mt-3">Used {template.usage_count || 0} times</p>
                </CardContent>
              </Card>
            ))}

            {templates.length === 0 && (
              <Card className="glass-card col-span-full">
                <CardContent className="py-12 text-center">
                  <Layout className="w-12 h-12 text-gray-300 mx-auto mb-4" />
                  <p className="text-gray-500">No templates yet. Create your first protocol template!</p>
                </CardContent>
              </Card>
            )}
          </div>
        )}

        {/* Create Template Dialog */}
        <Dialog open={showCreate} onOpenChange={setShowCreate}>
          <DialogContent>
            <DialogHeader>
              <DialogTitle>Create Protocol Template</DialogTitle>
            </DialogHeader>
            <div className="space-y-4 mt-4">
              <div>
                <Label>Template Name</Label>
                <Input
                  placeholder="e.g., Academic Research"
                  value={newTemplate.name}
                  onChange={(e) => setNewTemplate({ ...newTemplate, name: e.target.value })}
                  data-testid="template-name"
                />
              </div>
              <div>
                <Label>Description</Label>
                <Input
                  placeholder="What this template is for..."
                  value={newTemplate.description}
                  onChange={(e) => setNewTemplate({ ...newTemplate, description: e.target.value })}
                />
              </div>
              <div>
                <Label>Protocol String (InfoJet 2.0)</Label>
                <Textarea
                  placeholder="(term1 or term2) & (term3)+ & (exclude)^"
                  value={newTemplate.protocol_string}
                  onChange={(e) => setNewTemplate({ ...newTemplate, protocol_string: e.target.value })}
                  className="font-mono"
                  rows={4}
                  data-testid="template-protocol"
                />
              </div>
              <div className="grid grid-cols-2 gap-4">
                <div>
                  <Label>Category</Label>
                  <Select value={newTemplate.category} onValueChange={(v) => setNewTemplate({ ...newTemplate, category: v })}>
                    <SelectTrigger>
                      <SelectValue />
                    </SelectTrigger>
                    <SelectContent>
                      <SelectItem value="General">General</SelectItem>
                      <SelectItem value="Academic">Academic</SelectItem>
                      <SelectItem value="Business">Business</SelectItem>
                      <SelectItem value="Technology">Technology</SelectItem>
                      <SelectItem value="Science">Science</SelectItem>
                      <SelectItem value="History">History</SelectItem>
                    </SelectContent>
                  </Select>
                </div>
                <div className="flex items-center gap-2 mt-6">
                  <Checkbox
                    id="is-public"
                    checked={newTemplate.is_public}
                    onCheckedChange={(v) => setNewTemplate({ ...newTemplate, is_public: v })}
                  />
                  <Label htmlFor="is-public">Make Public</Label>
                </div>
              </div>
              <div className="flex justify-end gap-2">
                <Button variant="outline" onClick={() => setShowCreate(false)}>Cancel</Button>
                <Button onClick={createTemplate} data-testid="submit-template">Create Template</Button>
              </div>
            </div>
          </DialogContent>
        </Dialog>
      </div>
    </div>
  );
};

// ============= PAYMENT SUCCESS PAGE =============
const PaymentSuccessPage = () => {
  const [status, setStatus] = useState('checking');
  const [paymentInfo, setPaymentInfo] = useState(null);
  const navigate = useNavigate();
  const pollingRef = useRef(null);
  const attemptRef = useRef(0);

  useEffect(() => {
    const params = new URLSearchParams(window.location.search);
    const sessionId = params.get('session_id');
    
    if (sessionId) {
      pollPaymentStatus(sessionId);
    } else {
      setStatus('error');
    }

    return () => {
      if (pollingRef.current) {
        clearTimeout(pollingRef.current);
      }
    };
  }, []);

  const pollPaymentStatus = async (sessionId) => {
    const maxAttempts = 10;
    
    if (attemptRef.current >= maxAttempts) {
      setStatus('timeout');
      return;
    }

    try {
      const response = await api.get(`/payments/checkout/status/${sessionId}`);
      setPaymentInfo(response.data);

      if (response.data.payment_status === 'paid') {
        setStatus('success');
        return;
      } else if (response.data.status === 'expired') {
        setStatus('expired');
        return;
      }

      // Continue polling
      attemptRef.current += 1;
      pollingRef.current = setTimeout(() => pollPaymentStatus(sessionId), 2000);
      setStatus('processing');
    } catch (error) {
      console.error("Error checking payment status:", error);
      attemptRef.current += 1;
      pollingRef.current = setTimeout(() => pollPaymentStatus(sessionId), 2000);
    }
  };

  return (
    <div className="min-h-screen bg-[#FFFFF0] flex items-center justify-center p-6" data-testid="payment-success-page">
      <Card className="glass-card max-w-md w-full">
        <CardContent className="p-8 text-center">
          {status === 'checking' || status === 'processing' ? (
            <>
              <div className="spinner mx-auto mb-6"></div>
              <h1 className="text-2xl font-bold mb-2">Processing Payment</h1>
              <p className="text-gray-600">Please wait while we confirm your payment...</p>
            </>
          ) : status === 'success' ? (
            <>
              <CheckCircle className="w-16 h-16 text-[#34C759] mx-auto mb-6" />
              <h1 className="text-2xl font-bold mb-2">Payment Successful!</h1>
              <p className="text-gray-600 mb-4">Your subscription has been activated.</p>
              {paymentInfo && (
                <p className="text-sm text-gray-500 mb-6">
                  Amount: ${(paymentInfo.amount_total / 100).toFixed(2)} {paymentInfo.currency?.toUpperCase()}
                </p>
              )}
              <Button className="btn-primary w-full" onClick={() => navigate('/dashboard')} data-testid="go-to-dashboard">
                Go to Dashboard
              </Button>
            </>
          ) : status === 'expired' ? (
            <>
              <XCircle className="w-16 h-16 text-[#FF6B6B] mx-auto mb-6" />
              <h1 className="text-2xl font-bold mb-2">Session Expired</h1>
              <p className="text-gray-600 mb-6">Your payment session has expired. Please try again.</p>
              <Button className="btn-primary w-full" onClick={() => navigate('/settings')} data-testid="try-again">
                Try Again
              </Button>
            </>
          ) : status === 'timeout' ? (
            <>
              <AlertTriangle className="w-16 h-16 text-[#FFD60A] mx-auto mb-6" />
              <h1 className="text-2xl font-bold mb-2">Payment Status Unknown</h1>
              <p className="text-gray-600 mb-6">We couldn't confirm your payment. If you were charged, please contact support.</p>
              <Button className="btn-primary w-full" onClick={() => navigate('/dashboard')} data-testid="go-dashboard-anyway">
                Go to Dashboard
              </Button>
            </>
          ) : (
            <>
              <XCircle className="w-16 h-16 text-[#FF6B6B] mx-auto mb-6" />
              <h1 className="text-2xl font-bold mb-2">Something Went Wrong</h1>
              <p className="text-gray-600 mb-6">Please contact support if you need help.</p>
              <Button className="btn-primary w-full" onClick={() => navigate('/')} data-testid="go-home">
                Go Home
              </Button>
            </>
          )}
        </CardContent>
      </Card>
    </div>
  );
};

// ============= APP ROUTER =============
const AppRouter = () => {
  const location = useLocation();

  // Check URL fragment for session_id BEFORE any route renders
  if (location.hash?.includes('session_id=')) {
    return <AuthCallback />;
  }

  return (
    <Routes>
      <Route path="/" element={<LandingPage />} />
      <Route path="/dashboard" element={
        <ProtectedRoute>
          <DashboardLayout>
            <UltimateSearchPage />
          </DashboardLayout>
        </ProtectedRoute>
      } />
      <Route path="/map" element={
        <ProtectedRoute>
          <DashboardLayout>
            <MapViewPage />
          </DashboardLayout>
        </ProtectedRoute>
      } />
      <Route path="/stats" element={
        <ProtectedRoute>
          <DashboardLayout>
            <StatisticsPage />
          </DashboardLayout>
        </ProtectedRoute>
      } />
      <Route path="/global" element={
        <ProtectedRoute>
          <DashboardLayout>
            <GlobalResearchPage />
          </DashboardLayout>
        </ProtectedRoute>
      } />
      <Route path="/marketplace" element={
        <ProtectedRoute>
          <DashboardLayout>
            <MarketplacePage />
          </DashboardLayout>
        </ProtectedRoute>
      } />
      <Route path="/leaderboard" element={
        <ProtectedRoute>
          <DashboardLayout>
            <LeaderboardPage />
          </DashboardLayout>
        </ProtectedRoute>
      } />
      <Route path="/friends" element={
        <ProtectedRoute>
          <DashboardLayout>
            <FriendsPage />
          </DashboardLayout>
        </ProtectedRoute>
      } />
      <Route path="/groups" element={
        <ProtectedRoute>
          <DashboardLayout>
            <GroupsPage />
          </DashboardLayout>
        </ProtectedRoute>
      } />
      <Route path="/chat" element={
        <ProtectedRoute>
          <DashboardLayout>
            <ChatPage />
          </DashboardLayout>
        </ProtectedRoute>
      } />
      <Route path="/reports" element={
        <ProtectedRoute>
          <DashboardLayout>
            <PersonalReportsPage />
          </DashboardLayout>
        </ProtectedRoute>
      } />
      <Route path="/easter-eggs" element={
        <ProtectedRoute>
          <DashboardLayout>
            <EasterEggsPage />
          </DashboardLayout>
        </ProtectedRoute>
      } />
      <Route path="/quotes" element={
        <ProtectedRoute>
          <DashboardLayout>
            <QuotesPage />
          </DashboardLayout>
        </ProtectedRoute>
      } />
      <Route path="/themes" element={
        <ProtectedRoute>
          <DashboardLayout>
            <ThemesPage />
          </DashboardLayout>
        </ProtectedRoute>
      } />
      <Route path="/book" element={
        <ProtectedRoute>
          <DashboardLayout>
            <BookPage />
          </DashboardLayout>
        </ProtectedRoute>
      } />
      <Route path="/settings" element={
        <ProtectedRoute>
          <DashboardLayout>
            <SettingsPage />
          </DashboardLayout>
        </ProtectedRoute>
      } />
      <Route path="/admin" element={
        <ProtectedRoute>
          <DashboardLayout>
            <AdminPanel />
          </DashboardLayout>
        </ProtectedRoute>
      } />
      {/* New Routes for P0 Features */}
      <Route path="/templates" element={
        <ProtectedRoute>
          <DashboardLayout>
            <ProtocolTemplatesPage />
          </DashboardLayout>
        </ProtectedRoute>
      } />
      <Route path="/privacy-policy" element={<LegalPage docType="privacy-policy" />} />
      <Route path="/terms-of-service" element={<LegalPage docType="terms-of-service" />} />
      <Route path="/payment-success" element={
        <ProtectedRoute>
          <PaymentSuccessPage />
        </ProtectedRoute>
      } />
    </Routes>
  );
};

// ============= MAIN APP =============
function App() {
  return (
    <BrowserRouter>
      <AuthProvider>
        <AppRouter />
      </AuthProvider>
    </BrowserRouter>
  );
}

export default App;
