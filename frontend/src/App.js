import { useState, useEffect, createContext, useContext, useCallback } from "react";
import { BrowserRouter, Routes, Route, Navigate, useNavigate, Link } from "react-router-dom";
import { QueryClient, QueryClientProvider, useQuery, useMutation, useQueryClient } from "@tanstack/react-query";
import axios from "axios";
import "@/App.css";
import { Button } from "@/components/ui/button";
import { Card, CardContent, CardDescription, CardFooter, CardHeader, CardTitle } from "@/components/ui/card";
import { Input } from "@/components/ui/input";
import { Label } from "@/components/ui/label";
import { Textarea } from "@/components/ui/textarea";
import { Badge } from "@/components/ui/badge";
import { Tabs, TabsContent, TabsList, TabsTrigger } from "@/components/ui/tabs";
import { Dialog, DialogContent, DialogDescription, DialogFooter, DialogHeader, DialogTitle, DialogTrigger } from "@/components/ui/dialog";
import { Select, SelectContent, SelectItem, SelectTrigger, SelectValue } from "@/components/ui/select";
import { Separator } from "@/components/ui/separator";
import { Checkbox } from "@/components/ui/checkbox";
import { 
  Book, ShoppingCart, Utensils, Star, Mail, MapPin, Phone, Clock, Rocket, Sparkles, Heart, 
  ChevronDown, ChevronRight, Menu, X, Send, Plus, Minus, AlertTriangle, CheckCircle, Ship, 
  Globe, CreditCard, Search, User, LogOut, Settings, Home, BarChart3, Map, Store, Egg,
  Trophy, FileText, Users, Shield, Trash2, Edit, Copy, RefreshCw, Newspaper, Quote, Gift
} from "lucide-react";

const BACKEND_URL = process.env.REACT_APP_BACKEND_URL;
const API = `${BACKEND_URL}/api`;

// Query client for React Query
const queryClient = new QueryClient({
  defaultOptions: {
    queries: { staleTime: 30000, retry: 1 }
  }
});

// PayPal Configuration
const PAYPAL_INFOPILOT_LINK = "https://www.paypal.com/ncp/payment/LZDBN3SQU4NWQ";
const PAYPAL_BOOK_LINK = "https://www.paypal.com/ncp/payment/LGXMXSG3D2MXU";
const AMAZON_BOOK_LINK = "https://www.amazon.com/Letters-Evelyn-John-Selman/dp/B0F3XFG14J";

// Auth Context
const AuthContext = createContext(null);

export const useAuth = () => useContext(AuthContext);

const AuthProvider = ({ children }) => {
  const [user, setUser] = useState(null);
  const [token, setToken] = useState(localStorage.getItem("token"));
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    if (token) {
      axios.defaults.headers.common["Authorization"] = `Bearer ${token}`;
      axios.get(`${API}/auth/me`)
        .then(res => setUser(res.data))
        .catch(() => { localStorage.removeItem("token"); setToken(null); })
        .finally(() => setLoading(false));
    } else {
      setLoading(false);
    }
  }, [token]);

  const login = async (email, password) => {
    const res = await axios.post(`${API}/auth/login`, { email, password });
    localStorage.setItem("token", res.data.token);
    axios.defaults.headers.common["Authorization"] = `Bearer ${res.data.token}`;
    setToken(res.data.token);
    setUser(res.data.user);
    return res.data;
  };

  const register = async (data) => {
    const res = await axios.post(`${API}/auth/register`, data);
    localStorage.setItem("token", res.data.token);
    axios.defaults.headers.common["Authorization"] = `Bearer ${res.data.token}`;
    setToken(res.data.token);
    setUser(res.data.user);
    return res.data;
  };

  const logout = () => {
    localStorage.removeItem("token");
    delete axios.defaults.headers.common["Authorization"];
    setToken(null);
    setUser(null);
  };

  return (
    <AuthContext.Provider value={{ user, token, login, register, logout, loading, setUser }}>
      {children}
    </AuthContext.Provider>
  );
};

// Toast Context
const ToastContext = createContext(null);
export const useToast = () => useContext(ToastContext);

const ToastProvider = ({ children }) => {
  const [toasts, setToasts] = useState([]);
  
  const showToast = useCallback((message, type = "success") => {
    const id = Date.now();
    setToasts(prev => [...prev, { id, message, type }]);
    setTimeout(() => setToasts(prev => prev.filter(t => t.id !== id)), 5000);
  }, []);

  return (
    <ToastContext.Provider value={showToast}>
      {children}
      <div className="fixed top-20 right-4 z-50 space-y-2">
        {toasts.map(toast => (
          <div key={toast.id} className={`toast ${toast.type === 'success' ? 'toast-success' : 'toast-error'} flex items-center gap-2`}>
            {toast.type === 'success' ? <CheckCircle size={20} /> : <AlertTriangle size={20} />}
            <span>{toast.message}</span>
            <button onClick={() => setToasts(prev => prev.filter(t => t.id !== toast.id))} className="ml-2">
              <X size={16} />
            </button>
          </div>
        ))}
      </div>
    </ToastContext.Provider>
  );
};

// ============ FLOATING EASTER EGG COMPONENT ============
const FloatingEasterEgg = () => {
  const [visible, setVisible] = useState(false);
  const [egg, setEgg] = useState(null);
  const [position, setPosition] = useState({ x: 0, y: 0 });
  const [showContent, setShowContent] = useState(false);
  const { user, setUser } = useAuth();
  const showToast = useToast();

  useEffect(() => {
    // Show egg randomly every 30-60 seconds
    const interval = setInterval(() => {
      if (Math.random() > 0.7) {
        setPosition({ 
          x: Math.random() * (window.innerWidth - 100),
          y: Math.random() * (window.innerHeight - 100)
        });
        axios.get(`${API}/easter-eggs/random`).then(res => {
          setEgg(res.data.egg);
          setVisible(true);
        });
      }
    }, 30000);

    // Initial egg after 5 seconds
    setTimeout(() => {
      setPosition({ x: window.innerWidth - 150, y: 100 });
      axios.get(`${API}/easter-eggs/random`).then(res => {
        setEgg(res.data.egg);
        setVisible(true);
      });
    }, 5000);

    return () => clearInterval(interval);
  }, []);

  const catchEgg = async () => {
    if (!user) {
      setShowContent(true);
      return;
    }
    try {
      const res = await axios.post(`${API}/easter-eggs/catch`, { egg_index: 0 });
      showToast(res.data.message, "success");
      setUser(prev => ({ ...prev, laughter_points: res.data.total_points }));
      setShowContent(true);
    } catch (e) {
      setShowContent(true);
    }
  };

  if (!visible || !egg) return null;

  return (
    <div 
      className="fixed z-40 cursor-pointer animate-bounce-slow"
      style={{ left: position.x, top: position.y }}
    >
      {!showContent ? (
        <div onClick={catchEgg} className="text-6xl hover:scale-125 transition-transform" data-testid="floating-easter-egg">
          🥚
        </div>
      ) : (
        <Card className="card-glass w-80 p-4 animate-slide-in" data-testid="easter-egg-content">
          <button onClick={() => { setVisible(false); setShowContent(false); }} className="absolute top-2 right-2 text-white/60 hover:text-white">
            <X size={20} />
          </button>
          <div className="text-center mb-3">
            <span className="text-4xl">🥚</span>
            <Badge className="ml-2 bg-yellow-400/20 text-yellow-300">+{user ? '10' : '0'} Laughter Points!</Badge>
          </div>
          <div className="space-y-3 text-sm">
            <div className="bg-purple-500/20 p-3 rounded-lg">
              <p className="text-white/90 italic">{egg.joke}</p>
            </div>
            {egg.protocol_idea && (
              <div className="bg-blue-500/20 p-3 rounded-lg">
                <p className="text-blue-300 font-semibold text-xs mb-1">💡 Protocol Idea:</p>
                <p className="text-white/80 text-xs font-mono">{egg.protocol_idea}</p>
                <Button size="sm" variant="outline" className="mt-2 text-xs" onClick={() => { navigator.clipboard.writeText(egg.protocol_idea); showToast("Protocol copied!"); }}>
                  <Copy size={12} className="mr-1" /> Copy Protocol
                </Button>
              </div>
            )}
            {egg.pricing_suggestion && (
              <div className="bg-green-500/20 p-3 rounded-lg">
                <p className="text-green-300 font-semibold text-xs">💰 Pricing: {egg.pricing_suggestion}</p>
              </div>
            )}
            {egg.map_instruction && (
              <div className="bg-orange-500/20 p-3 rounded-lg">
                <p className="text-orange-300 text-xs">{egg.map_instruction}</p>
              </div>
            )}
          </div>
        </Card>
      )}
    </div>
  );
};

// ============ NEWS HEADLINES COMPONENT ============
const NewsHeadlines = () => {
  const [expanded, setExpanded] = useState(false);
  const { data, refetch, isLoading } = useQuery({
    queryKey: ["headlines"],
    queryFn: () => axios.get(`${API}/news/headlines`).then(r => r.data)
  });

  return (
    <div className="fixed top-16 right-4 z-30" data-testid="news-headlines">
      <button 
        onClick={() => setExpanded(!expanded)}
        className="bg-gradient-to-r from-red-500 to-orange-500 text-white px-3 py-2 rounded-lg flex items-center gap-2 text-sm font-semibold shadow-lg"
      >
        <Newspaper size={16} /> Headlines {expanded ? <ChevronDown size={14} /> : <ChevronRight size={14} />}
      </button>
      {expanded && (
        <Card className="card-glass mt-2 w-72 max-h-96 overflow-y-auto animate-slide-in">
          <CardHeader className="py-2 px-3">
            <div className="flex items-center justify-between">
              <CardTitle className="text-sm text-yellow-400">🌍 World News</CardTitle>
              <Button size="sm" variant="ghost" onClick={() => refetch()} disabled={isLoading} data-testid="refresh-headlines">
                <RefreshCw size={14} className={isLoading ? "animate-spin" : ""} />
              </Button>
            </div>
          </CardHeader>
          <CardContent className="p-2 space-y-2">
            {data?.headlines?.map((h, i) => (
              <a key={i} href={h.url} target="_blank" rel="noopener noreferrer" className="block p-2 bg-white/5 rounded hover:bg-white/10 transition">
                <Badge className="text-xs mb-1" style={{ backgroundColor: `hsl(${i * 36}, 70%, 30%)` }}>{h.category}</Badge>
                <p className="text-white/90 text-xs">{h.title}</p>
              </a>
            ))}
          </CardContent>
        </Card>
      )}
    </div>
  );
};

// ============ NAVBAR ============
const Navbar = () => {
  const { user, logout } = useAuth();
  const navigate = useNavigate();
  const [mobileOpen, setMobileOpen] = useState(false);

  const navItems = user ? [
    { path: "/", label: "Home", icon: <Home size={18} /> },
    { path: "/search", label: "Ultimate Search", icon: <Search size={18} /> },
    { path: "/map", label: "Map View", icon: <Map size={18} /> },
    { path: "/stats", label: "Statistics", icon: <BarChart3 size={18} /> },
    { path: "/marketplace", label: "Marketplace", icon: <Store size={18} /> },
    { path: "/book", label: "Book", icon: <Book size={18} /> },
    { path: "/food", label: "Food", icon: <Utensils size={18} /> },
  ] : [
    { path: "/", label: "Home", icon: <Home size={18} /> },
    { path: "/book", label: "Book", icon: <Book size={18} /> },
    { path: "/food", label: "Food", icon: <Utensils size={18} /> },
    { path: "/infopilot", label: "InfoPilot", icon: <Globe size={18} /> },
  ];

  return (
    <nav className="navbar fixed top-0 left-0 right-0 z-50 px-4 py-3" data-testid="navbar">
      <div className="max-w-7xl mx-auto flex items-center justify-between">
        <Link to="/" className="flex items-center gap-2" data-testid="logo">
          <Sparkles className="text-yellow-400 animate-sparkle" size={28} />
          <div className="flex flex-col">
            <span className="text-xl font-bold text-gradient-gold">InfoPilot Explorer</span>
            <span className="text-xs text-white/50">Top Pilot Enterprises, Inc.</span>
          </div>
        </Link>

        {/* Desktop Nav */}
        <div className="hidden lg:flex items-center gap-4">
          {navItems.map(item => (
            <Link key={item.path} to={item.path} className="flex items-center gap-2 px-3 py-2 rounded-lg text-white/80 hover:text-yellow-400 hover:bg-yellow-400/10 transition">
              {item.icon} <span className="text-sm">{item.label}</span>
            </Link>
          ))}
        </div>

        {/* User Menu */}
        <div className="flex items-center gap-4">
          {user ? (
            <>
              <Badge className="bg-yellow-400/20 text-yellow-300 hidden sm:flex items-center gap-1">
                <Egg size={14} /> {user.laughter_points || 0} pts
              </Badge>
              <div className="relative group">
                <Button variant="ghost" className="flex items-center gap-2 text-white">
                  <User size={18} /> <span className="hidden sm:inline">{user.username}</span>
                </Button>
                <div className="absolute right-0 mt-2 w-48 bg-slate-800 rounded-lg shadow-xl opacity-0 invisible group-hover:opacity-100 group-hover:visible transition-all">
                  <Link to="/settings" className="flex items-center gap-2 px-4 py-2 text-white/80 hover:bg-white/10">
                    <Settings size={16} /> Settings
                  </Link>
                  {user.is_admin && (
                    <Link to="/admin" className="flex items-center gap-2 px-4 py-2 text-white/80 hover:bg-white/10">
                      <Shield size={16} /> Admin Panel
                    </Link>
                  )}
                  <button onClick={logout} className="flex items-center gap-2 px-4 py-2 text-red-400 hover:bg-white/10 w-full">
                    <LogOut size={16} /> Logout
                  </button>
                </div>
              </div>
            </>
          ) : (
            <Link to="/login">
              <Button className="btn-gold">Login / Register</Button>
            </Link>
          )}

          {/* Mobile Menu */}
          <button className="lg:hidden text-white" onClick={() => setMobileOpen(!mobileOpen)}>
            {mobileOpen ? <X size={28} /> : <Menu size={28} />}
          </button>
        </div>
      </div>

      {/* Mobile Nav */}
      {mobileOpen && (
        <div className="lg:hidden mt-4 pb-4 animate-slide-in">
          {navItems.map(item => (
            <Link key={item.path} to={item.path} onClick={() => setMobileOpen(false)} className="flex items-center gap-2 w-full px-4 py-3 text-white/80">
              {item.icon} <span>{item.label}</span>
            </Link>
          ))}
        </div>
      )}
    </nav>
  );
};

// ============ STARS BACKGROUND ============
const STAR_POSITIONS = Array.from({ length: 50 }, (_, i) => ({
  id: i, left: `${(i * 17 + 3) % 100}%`, top: `${(i * 23 + 7) % 100}%`, delay: `${(i * 0.06) % 3}s`, size: `${1 + (i % 3)}px`
}));

const StarsBackground = () => (
  <div className="stars-bg">
    {STAR_POSITIONS.map(star => (
      <div key={star.id} className="star" style={{ left: star.left, top: star.top, animationDelay: star.delay, width: star.size, height: star.size }} />
    ))}
  </div>
);

// ============ HOME PAGE ============
const HomePage = () => {
  const { user } = useAuth();
  const navigate = useNavigate();

  return (
    <div className="min-h-screen pt-20 px-4">
      <StarsBackground />
      
      {/* Hero */}
      <section className="min-h-[80vh] flex flex-col items-center justify-center relative overflow-hidden" data-testid="hero-section">
        <div className="absolute inset-0 opacity-20">
          <div className="absolute top-20 left-10 text-8xl animate-float">🚀</div>
          <div className="absolute top-40 right-20 text-7xl animate-float" style={{ animationDelay: '0.5s' }}>📚</div>
          <div className="absolute bottom-40 left-20 text-7xl animate-float" style={{ animationDelay: '1s' }}>🚢</div>
          <div className="absolute bottom-20 right-10 text-8xl animate-float" style={{ animationDelay: '1.5s' }}>🥩</div>
          <div className="absolute top-1/3 left-1/4 text-6xl animate-bounce-slow">👽</div>
          <div className="absolute top-1/2 right-1/4 text-6xl animate-bounce-slow" style={{ animationDelay: '0.5s' }}>⭐</div>
        </div>

        <div className="text-center z-10 max-w-4xl mx-auto animate-slide-in">
          <Badge className="mb-2 bg-blue-600/30 text-blue-300 border-blue-500/30 text-xs px-3 py-1">
            ✈️ A Top Pilot Enterprises, Inc. Company
          </Badge>
          <Badge className="mb-4 bg-yellow-400/20 text-yellow-400 border-yellow-400/30 text-sm px-4 py-1 ml-2">
            🎉 First in Flight with Monetization of Searches! It's a Bear! 🐻
          </Badge>
          
          <h1 className="hero-title text-5xl md:text-7xl font-bold mb-6 text-gradient-gold text-shadow-glow">
            InfoPilot Explorer
          </h1>
          
          <p className="hero-subtitle text-xl md:text-2xl text-white/90 mb-4">
            Your #1 Resource for Finding Information Valuable to You!
          </p>
          
          <p className="text-lg text-white/70 mb-4 max-w-2xl mx-auto">
            A Worldwide Information Exchange Database with Boolean Search & Categorization for Scholars and Tradesmen. 
            Plus: Letters to Evelyn & Maestro Bistro! 🌌
          </p>

          <div className="flex flex-wrap justify-center gap-2 mb-8">
            <Badge className="bg-green-500/20 text-green-300 border-green-500/30">⭐ 19 Five-Star Reviews</Badge>
            <Badge className="bg-purple-500/20 text-purple-300 border-purple-500/30">🎬 Film Production by Voyage Media!</Badge>
            <Badge className="bg-red-500/20 text-red-300 border-red-500/30">🐻 Dangerous to the App Market!</Badge>
          </div>

          <div className="flex flex-col sm:flex-row gap-4 justify-center">
            {user ? (
              <>
                <Button onClick={() => navigate('/search')} className="btn-gold text-lg px-8 py-6" data-testid="cta-search">
                  <Search className="mr-2" /> Ultimate Search
                </Button>
                <Button onClick={() => navigate('/marketplace')} className="btn-navy text-lg px-8 py-6" data-testid="cta-marketplace">
                  <Store className="mr-2" /> Marketplace
                </Button>
              </>
            ) : (
              <>
                <Button onClick={() => navigate('/login')} className="btn-gold text-lg px-8 py-6" data-testid="cta-login">
                  <Rocket className="mr-2" /> Get Started - $1/mo
                </Button>
                <Button onClick={() => navigate('/book')} className="btn-navy text-lg px-8 py-6" data-testid="cta-book">
                  <Book className="mr-2" /> Letters to Evelyn
                </Button>
              </>
            )}
            <Button onClick={() => navigate('/food')} className="bg-gradient-to-r from-orange-600 to-red-600 text-white font-bold px-8 py-6 rounded-full hover:scale-105 transition-all" data-testid="cta-food">
              <Utensils className="mr-2" /> Maestro Bistro
            </Button>
          </div>

          <div className="mt-12 flex flex-wrap justify-center gap-8 text-white/60">
            <div className="flex items-center gap-2"><Ship className="text-yellow-400" /><span>Navy Aviation</span></div>
            <div className="flex items-center gap-2"><Globe className="text-purple-400" /><span>InfoJet 2.0 Protocols</span></div>
            <div className="flex items-center gap-2"><Heart className="text-red-400" /><span>True Love Story</span></div>
            <div className="flex items-center gap-2"><MapPin className="text-orange-400" /><span>Brunswick, Maine</span></div>
          </div>
        </div>

        <div className="absolute bottom-10 animate-bounce">
          <ChevronDown size={32} className="text-yellow-400" />
        </div>
      </section>

      {/* Features Grid */}
      <section className="py-16 max-w-6xl mx-auto">
        <h2 className="text-3xl font-bold text-center text-gradient-gold mb-12">What Makes InfoPilot Powerful?</h2>
        <div className="grid md:grid-cols-3 gap-6">
          {[
            { icon: <Search size={32} />, title: "InfoJet 2.0 Protocols", desc: "Create custom Boolean search protocols to categorize ANY information from the web!" },
            { icon: <Map size={32} />, title: "Interactive Maps", desc: "See your search results plotted on a global map with color-coded categories!" },
            { icon: <Store size={32} />, title: "Protocol Marketplace", desc: "Sell your protocols to other users! First in Flight with Monetization of Searches!" },
            { icon: <Egg size={32} />, title: "Easter Eggs & Laughter Points", desc: "Catch floating eggs for jokes, protocol ideas, and earn points! 🥚" },
            { icon: <Trophy size={32} />, title: "Community Leaderboard", desc: "Compete for top protocol creator and highest laughter points!" },
            { icon: <BarChart3 size={32} />, title: "Advanced Statistics", desc: "Analyze your data with pie charts, bar graphs, and worldwide insights!" },
          ].map((f, i) => (
            <Card key={i} className="card-glass p-6 card-hover">
              <div className="text-yellow-400 mb-4">{f.icon}</div>
              <h3 className="text-xl font-bold text-white mb-2">{f.title}</h3>
              <p className="text-white/70">{f.desc}</p>
            </Card>
          ))}
        </div>
      </section>

      {/* Testimonials Preview */}
      <section className="py-16 max-w-4xl mx-auto">
        <h2 className="text-3xl font-bold text-center text-gradient-gold mb-8">What People Are Saying</h2>
        <div className="grid md:grid-cols-2 gap-6">
          <Card className="card-glass p-6">
            <div className="flex gap-1 mb-2">{[...Array(5)].map((_, i) => <Star key={i} size={16} className="text-yellow-400 fill-yellow-400" />)}</div>
            <p className="text-white/90 italic mb-4">"Letters to Evelyn is an extraordinary book with a unique plot that captivated me from the first chapter!"</p>
            <p className="text-yellow-400 font-semibold">- L. Jones, Readers' Favorite</p>
          </Card>
          <Card className="card-glass p-6">
            <div className="flex gap-1 mb-2">{[...Array(5)].map((_, i) => <Star key={i} size={16} className="text-yellow-400 fill-yellow-400" />)}</div>
            <p className="text-white/90 italic mb-4">"The beef rouladen at Maestro Bistro made me call my grandmother in Germany to apologize. It's THAT good!"</p>
            <p className="text-orange-400 font-semibold">- Hans the Hungry, Brunswick</p>
          </Card>
        </div>
      </section>

      {/* Footer */}
      <footer className="footer py-12 px-4 mt-16">
        <div className="max-w-6xl mx-auto">
          <div className="grid md:grid-cols-3 gap-8 mb-8">
            <div>
              <div className="flex items-center gap-2 mb-4">
                <Sparkles className="text-yellow-400" size={24} />
                <span className="text-xl font-bold text-gradient-gold">InfoPilot Explorer</span>
              </div>
              <p className="text-white/60 text-sm">Top Pilot Enterprises, Inc. - "It's a Bear!" 🐻</p>
              <p className="text-white/40 text-xs mt-2">First in Flight with Monetization of Searches!</p>
            </div>
            <div>
              <h4 className="text-lg font-bold text-yellow-400 mb-4">Quick Links</h4>
              <ul className="space-y-2 text-white/60">
                <li><Link to="/book" className="hover:text-yellow-400">📚 Letters to Evelyn</Link></li>
                <li><Link to="/food" className="hover:text-yellow-400">🚚 Maestro Bistro</Link></li>
                <li><Link to="/infopilot" className="hover:text-yellow-400">🌐 InfoPilot - $1/mo</Link></li>
                <li><Link to="/legal/user-agreement" className="hover:text-yellow-400">📜 User Agreement</Link></li>
                <li><Link to="/legal/privacy" className="hover:text-yellow-400">🔒 Privacy Policy</Link></li>
              </ul>
            </div>
            <div>
              <h4 className="text-lg font-bold text-yellow-400 mb-4">Contact</h4>
              <p className="text-white/60 text-sm">john.1976.selman@gmail.com</p>
              <p className="text-white/60 text-sm">207-522-0894</p>
              <p className="text-white/60 text-sm mt-2">Brunswick, Maine</p>
            </div>
          </div>
          <Separator className="bg-yellow-400/20 mb-8" />
          <div className="text-center text-white/40 text-sm">
            <p>© 2014-2025 John Selman - Letters to Evelyn | © 2025 Top Pilot Enterprises, Inc.</p>
            <p className="mt-2">🛸 No aliens were harmed in the making of this app 🛸</p>
          </div>
        </div>
      </footer>
    </div>
  );
};

// ============ LOGIN PAGE ============
const LoginPage = () => {
  const { login, register } = useAuth();
  const navigate = useNavigate();
  const showToast = useToast();
  const [mode, setMode] = useState("login");
  const [form, setForm] = useState({ email: "", password: "", username: "", first_name: "", last_name: "" });
  const [loading, setLoading] = useState(false);
  const [showAgreement, setShowAgreement] = useState(false);

  const handleSubmit = async (e) => {
    e.preventDefault();
    setLoading(true);
    try {
      if (mode === "login") {
        await login(form.email, form.password);
        showToast("Welcome back! 🚀", "success");
      } else {
        await register(form);
        showToast("Account created! Welcome to InfoPilot! 🎉", "success");
      }
      navigate("/search");
    } catch (err) {
      showToast(err.response?.data?.detail || "Error occurred", "error");
    }
    setLoading(false);
  };

  return (
    <div className="min-h-screen pt-24 px-4 flex items-center justify-center">
      <StarsBackground />
      <Card className="card-glass w-full max-w-md p-6" data-testid="login-card">
        <CardHeader>
          <CardTitle className="text-2xl text-gradient-gold text-center">
            {mode === "login" ? "Welcome Back!" : "Join InfoPilot Explorer"}
          </CardTitle>
          <CardDescription className="text-center text-white/70">
            {mode === "login" ? "Login to access your Ultimate Search Page" : "Create an account to start categorizing the world!"}
          </CardDescription>
        </CardHeader>
        <CardContent>
          <form onSubmit={handleSubmit} className="space-y-4">
            {mode === "register" && (
              <>
                <div>
                  <Label className="text-white">Username *</Label>
                  <Input className="form-input mt-1" placeholder="Your unique username" value={form.username} onChange={e => setForm({...form, username: e.target.value})} required data-testid="register-username" />
                </div>
                <div className="grid grid-cols-2 gap-4">
                  <div>
                    <Label className="text-white">First Name</Label>
                    <Input className="form-input mt-1" placeholder="First name" value={form.first_name} onChange={e => setForm({...form, first_name: e.target.value})} />
                  </div>
                  <div>
                    <Label className="text-white">Last Name</Label>
                    <Input className="form-input mt-1" placeholder="Last name" value={form.last_name} onChange={e => setForm({...form, last_name: e.target.value})} />
                  </div>
                </div>
              </>
            )}
            <div>
              <Label className="text-white">Email *</Label>
              <Input className="form-input mt-1" type="email" placeholder="you@example.com" value={form.email} onChange={e => setForm({...form, email: e.target.value})} required data-testid="login-email" />
            </div>
            <div>
              <Label className="text-white">Password *</Label>
              <Input className="form-input mt-1" type="password" placeholder="••••••••" value={form.password} onChange={e => setForm({...form, password: e.target.value})} required data-testid="login-password" />
            </div>
            {mode === "register" && (
              <div className="flex items-center gap-2">
                <Checkbox id="agree" required />
                <Label htmlFor="agree" className="text-white/70 text-sm">
                  I agree to the <button type="button" onClick={() => setShowAgreement(true)} className="text-yellow-400 underline">User Agreement</button>
                </Label>
              </div>
            )}
            <Button type="submit" className="btn-gold w-full" disabled={loading} data-testid="login-submit">
              {loading ? "Loading..." : (mode === "login" ? "Login" : "Create Account")}
            </Button>
          </form>
        </CardContent>
        <CardFooter className="flex flex-col gap-4">
          <button onClick={() => setMode(mode === "login" ? "register" : "login")} className="text-yellow-400 text-sm hover:underline">
            {mode === "login" ? "Don't have an account? Register" : "Already have an account? Login"}
          </button>
          <div className="text-center">
            <p className="text-white/50 text-xs">Subscribe for just $1/month!</p>
            <a href={PAYPAL_INFOPILOT_LINK} target="_blank" rel="noopener noreferrer" className="text-blue-400 text-xs hover:underline">
              Subscribe via PayPal →
            </a>
          </div>
        </CardFooter>
      </Card>

      <Dialog open={showAgreement} onOpenChange={setShowAgreement}>
        <DialogContent className="bg-slate-900 border-yellow-400/30 max-h-[80vh] overflow-y-auto">
          <DialogHeader>
            <DialogTitle className="text-yellow-400">User Agreement</DialogTitle>
          </DialogHeader>
          <div className="text-white/80 text-sm space-y-4">
            <p><strong>InfoPilot Explorer is FIRST IN FLIGHT with Monetization of Searches!</strong></p>
            <p>So much time is spent searching for valuable information. Why can't it be worth anything? If it's valuable to businesses, then it should be valuable to YOU!</p>
            <p>The code and design of InfoPilot Explorer are copyrighted and MAY NOT be emulated by any other person.</p>
            <p>By using this service, you agree to:</p>
            <ul className="list-disc pl-4 space-y-1">
              <li>Use the platform for lawful purposes only</li>
              <li>Not upload prohibited content</li>
              <li>Respect other users and their content</li>
            </ul>
          </div>
          <DialogFooter>
            <Button onClick={() => setShowAgreement(false)} className="btn-gold">I Understand</Button>
          </DialogFooter>
        </DialogContent>
      </Dialog>
    </div>
  );
};

// ============ BOOK PAGE ============
const BookPage = () => {
  const { data: book } = useQuery({
    queryKey: ["book"],
    queryFn: () => axios.get(`${API}/book`).then(r => r.data)
  });
  const { data: prices } = useQuery({
    queryKey: ["book-prices"],
    queryFn: () => axios.get(`${API}/book/prices`).then(r => r.data)
  });

  if (!book) return <div className="min-h-screen pt-24 flex items-center justify-center text-white">Loading...</div>;

  return (
    <div className="min-h-screen pt-24 px-4">
      <StarsBackground />
      <div className="max-w-6xl mx-auto">
        <div className="text-center mb-12 animate-slide-in">
          <Badge className="mb-2 bg-blue-600/30 text-blue-300">✈️ John Selman Publications</Badge>
          <Badge className="mb-4 bg-purple-500/20 text-purple-300 ml-2">📖 True Supernatural Thriller Comedy</Badge>
          <h1 className="text-4xl md:text-5xl font-bold text-gradient-gold mb-4">{book.title}</h1>
          <p className="text-xl text-white/80">by {book.author}</p>
          <div className="flex flex-wrap justify-center gap-2 mt-4">
            <Badge className="bg-green-500/20 text-green-300">⭐ {book.review_count} Five-Star Reviews</Badge>
            <Badge className="bg-red-500/20 text-red-300">🎬 {book.film_news}</Badge>
          </div>
        </div>

        <div className="grid md:grid-cols-2 gap-8">
          <Card className="card-glass p-6" data-testid="book-info">
            <div className="h-48 bg-gradient-to-br from-purple-900 to-indigo-900 rounded-lg flex items-center justify-center mb-6">
              <span className="text-8xl">📚</span>
            </div>
            <div className="flex flex-wrap gap-2 mb-4">
              <Badge className="bg-yellow-400/20 text-yellow-300">Supernatural</Badge>
              <Badge className="bg-blue-400/20 text-blue-300">Thriller</Badge>
              <Badge className="bg-pink-400/20 text-pink-300">Comedy</Badge>
              <Badge className="bg-green-400/20 text-green-300">Navy Memoir</Badge>
            </div>
            <p className="text-white/80 mb-4">{book.long_description}</p>
            <p className="text-white/60 text-sm">{book.copyright}</p>
          </Card>

          <div className="space-y-6">
            <Card className="card-glass p-6 border-2 border-yellow-400/50" data-testid="buy-options">
              <h3 className="text-2xl font-bold text-yellow-400 mb-4">🔥 Buy Now!</h3>
              <div className="grid grid-cols-2 gap-4">
                <a href={PAYPAL_BOOK_LINK} target="_blank" rel="noopener noreferrer" className="flex items-center justify-center gap-2 bg-[#0070ba] hover:bg-[#003087] text-white font-bold py-4 px-4 rounded-lg transition" data-testid="buy-paypal">
                  <CreditCard size={20} /> PayPal
                </a>
                <a href={AMAZON_BOOK_LINK} target="_blank" rel="noopener noreferrer" className="flex items-center justify-center gap-2 bg-[#FF9900] hover:bg-[#e88b00] text-black font-bold py-4 px-4 rounded-lg transition" data-testid="buy-amazon">
                  <ShoppingCart size={20} /> Amazon
                </a>
              </div>
              <p className="text-center text-white/50 text-sm mt-3">⭐ 19 Five-Star Reviews from Readers Favorite!</p>
            </Card>

            {prices && (
              <Card className="card-glass p-6">
                <h3 className="text-xl font-bold text-white mb-4">Format Options</h3>
                {Object.entries(prices).map(([format, price]) => (
                  <div key={format} className="flex justify-between items-center p-3 bg-white/5 rounded-lg mb-2">
                    <span className="text-white capitalize">{format}</span>
                    <span className="text-yellow-400 font-bold">${price.toFixed(2)}</span>
                  </div>
                ))}
              </Card>
            )}

            <Card className="card-glass p-6" data-testid="warnings">
              <h3 className="text-xl font-bold text-red-400 mb-4 flex items-center gap-2">
                <AlertTriangle /> Important Warnings!
              </h3>
              <ul className="space-y-2">
                {book.warnings?.map((w, i) => (
                  <li key={i} className="flex items-start gap-2 text-white/70 text-sm">
                    <span className="text-yellow-400">⚠️</span> {w}
                  </li>
                ))}
              </ul>
            </Card>
          </div>
        </div>

        {/* Reviews */}
        <Card className="card-glass p-6 mt-8">
          <h3 className="text-2xl font-bold text-yellow-400 mb-6">⭐ Professional Reviews</h3>
          <div className="grid md:grid-cols-2 gap-6">
            {book.professional_reviews?.map((r, i) => (
              <div key={i} className="bg-white/5 p-4 rounded-lg">
                <div className="flex gap-1 mb-2">{[...Array(5)].map((_, j) => <Star key={j} size={14} className="text-yellow-400 fill-yellow-400" />)}</div>
                <p className="text-white/90 italic mb-2">"{r.quote}"</p>
                <p className="text-yellow-400 text-sm font-semibold">- {r.author}, {r.source}</p>
              </div>
            ))}
          </div>
        </Card>
      </div>
    </div>
  );
};

// ============ FOOD PAGE ============
const FoodPage = () => {
  const showToast = useToast();
  const { data: menu } = useQuery({
    queryKey: ["food-menu"],
    queryFn: () => axios.get(`${API}/food/menu`).then(r => r.data)
  });
  const [cart, setCart] = useState([]);

  const addToCart = (item) => {
    const existing = cart.find(c => c.id === item.id);
    if (existing) {
      setCart(cart.map(c => c.id === item.id ? {...c, quantity: c.quantity + 1} : c));
    } else {
      setCart([...cart, { ...item, quantity: 1 }]);
    }
    showToast(`Added ${item.name} to cart! 🛒`, "success");
  };

  const getTotal = () => cart.reduce((sum, item) => sum + (item.price * item.quantity), 0);

  if (!menu) return <div className="min-h-screen pt-24 flex items-center justify-center text-white">Loading...</div>;

  return (
    <div className="min-h-screen pt-24 px-4">
      <StarsBackground />
      <div className="max-w-6xl mx-auto">
        <div className="text-center mb-12 animate-slide-in">
          <Badge className="mb-4 bg-orange-500/20 text-orange-300">🚚 Now Serving in Brunswick, Maine!</Badge>
          <h1 className="text-4xl md:text-5xl font-bold text-gradient-gold mb-4">{menu.restaurant_name}</h1>
          <p className="text-xl text-white/80">{menu.tagline}</p>
          <div className="flex items-center justify-center gap-2 mt-4 text-white/60">
            <MapPin className="text-yellow-400" /> <span>{menu.location}</span>
          </div>
        </div>

        <div className="grid md:grid-cols-2 lg:grid-cols-3 gap-6 mb-12">
          {menu.menu?.map(item => (
            <Card key={item.id} className="card-glass overflow-hidden card-hover" data-testid={`menu-item-${item.id}`}>
              <CardHeader>
                <div className="flex justify-between">
                  <div className="text-5xl mb-2">
                    {item.id === 'beef-rouladen' && '🥩'}
                    {item.id === 'veggie-rouladen' && '🥬'}
                    {item.id === 'fish-chowder' && '🐟'}
                    {item.id === 'pretzel' && '🥨'}
                    {item.id === 'apple-strudel' && '🥧'}
                  </div>
                  <Badge className="bg-yellow-400/20 text-yellow-300 text-lg h-fit">${item.price}</Badge>
                </div>
                <CardTitle className="text-white">{item.name}</CardTitle>
                <CardDescription className="text-yellow-300/80 italic">"{item.funny_tagline}"</CardDescription>
              </CardHeader>
              <CardContent>
                <p className="text-white/70 text-sm">{item.description}</p>
              </CardContent>
              <CardFooter>
                <Button onClick={() => addToCart(item)} className="btn-gold w-full" data-testid={`add-${item.id}`}>
                  <Plus className="mr-2" /> Add to Cart
                </Button>
              </CardFooter>
            </Card>
          ))}
        </div>

        {cart.length > 0 && (
          <Card className="card-glass p-6 sticky bottom-4" data-testid="cart">
            <div className="flex items-center justify-between mb-4">
              <h3 className="text-xl font-bold text-yellow-400 flex items-center gap-2">
                <ShoppingCart /> Cart ({cart.length} items)
              </h3>
              <span className="text-2xl font-bold text-white">${getTotal().toFixed(2)}</span>
            </div>
            <div className="space-y-2 mb-4">
              {cart.map(item => (
                <div key={item.id} className="flex items-center justify-between bg-white/5 p-3 rounded-lg">
                  <span className="text-white">{item.name} x{item.quantity}</span>
                  <span className="text-yellow-400">${(item.price * item.quantity).toFixed(2)}</span>
                </div>
              ))}
            </div>
            <p className="text-center text-white/60 text-sm">Visit us at {menu.location} to place your order!</p>
          </Card>
        )}
      </div>
    </div>
  );
};

// ============ INFOPILOT SUBSCRIPTION PAGE ============
const InfoPilotPage = () => {
  const { data: plans } = useQuery({
    queryKey: ["infopilot-plans"],
    queryFn: () => axios.get(`${API}/infopilot/plans`).then(r => r.data)
  });

  if (!plans) return <div className="min-h-screen pt-24 flex items-center justify-center text-white">Loading...</div>;

  return (
    <div className="min-h-screen pt-24 px-4">
      <StarsBackground />
      <div className="max-w-4xl mx-auto">
        <div className="text-center mb-12">
          <Badge className="mb-2 bg-blue-600/30 text-blue-300">✈️ Top Pilot Enterprises, Inc.</Badge>
          <Badge className="mb-4 bg-green-500/20 text-green-300 ml-2">🔍 Boolean Search & Categorization Platform</Badge>
          <h1 className="text-4xl md:text-5xl font-bold text-gradient-gold mb-4">InfoPilot Explorer</h1>
          <p className="text-xl text-white/80">Mobile & Desktop Application for Information Exchange</p>
          <p className="text-white/60 mt-2">Built for Scholars and Tradesmen - Only $1/month!</p>
        </div>

        <div className="grid md:grid-cols-2 gap-6 mb-8">
          <Card className="card-glass p-6 border-2 border-blue-500/30" data-testid="monthly-plan">
            <Badge className="bg-blue-500/20 text-blue-300 mb-4">Most Popular</Badge>
            <h3 className="text-2xl font-bold text-white mb-2">Monthly Plan</h3>
            <div className="text-4xl font-bold text-yellow-400 mb-4">${plans.monthly?.price}<span className="text-lg text-white/60">/mo</span></div>
            <ul className="space-y-2 mb-6">
              {plans.monthly?.features?.map((f, i) => (
                <li key={i} className="flex items-center gap-2 text-white/80"><CheckCircle className="text-green-400" size={16} /> {f}</li>
              ))}
            </ul>
            <a href={PAYPAL_INFOPILOT_LINK} target="_blank" rel="noopener noreferrer" className="block">
              <Button className="btn-gold w-full">Subscribe Now</Button>
            </a>
          </Card>

          <Card className="card-glass p-6 border-2 border-yellow-500/30" data-testid="yearly-plan">
            <Badge className="bg-yellow-500/20 text-yellow-300 mb-4">Save 17%!</Badge>
            <h3 className="text-2xl font-bold text-white mb-2">Yearly Plan</h3>
            <div className="text-4xl font-bold text-yellow-400 mb-4">${plans.yearly?.price}<span className="text-lg text-white/60">/yr</span></div>
            <ul className="space-y-2 mb-6">
              {plans.yearly?.features?.map((f, i) => (
                <li key={i} className="flex items-center gap-2 text-white/80"><CheckCircle className="text-green-400" size={16} /> {f}</li>
              ))}
            </ul>
            <a href={PAYPAL_INFOPILOT_LINK} target="_blank" rel="noopener noreferrer" className="block">
              <Button className="btn-gold w-full">Subscribe Now</Button>
            </a>
          </Card>
        </div>

        {plans.upgrade_message && (
          <Card className="card-glass p-4 bg-red-500/10 border border-red-500/30">
            <p className="text-white/80 text-sm text-center">{plans.upgrade_message}</p>
          </Card>
        )}
      </div>
    </div>
  );
};

// ============ ULTIMATE SEARCH PAGE ============
const UltimateSearchPage = () => {
  const { user } = useAuth();
  const showToast = useToast();
  const queryClient = useQueryClient();
  const [searchQuery, setSearchQuery] = useState("");
  const [selectedCategories, setSelectedCategories] = useState([]);
  const [aggregation, setAggregation] = useState("and_or");
  const [showCreateCategory, setShowCreateCategory] = useState(false);
  const [newCategory, setNewCategory] = useState({ name: "", protocol: "", parent_id: null, is_public: true, price: null });
  const [expandedCategories, setExpandedCategories] = useState({});

  const { data: categoriesData, isLoading: loadingCategories } = useQuery({
    queryKey: ["categories"],
    queryFn: () => axios.get(`${API}/categories`).then(r => r.data),
    enabled: !!user
  });

  const { data: resultsData, isLoading: loadingResults, refetch: refetchResults } = useQuery({
    queryKey: ["search-results", selectedCategories, aggregation],
    queryFn: () => axios.get(`${API}/search/results`, {
      params: { category_ids: selectedCategories.join(","), aggregation }
    }).then(r => r.data),
    enabled: !!user && selectedCategories.length > 0
  });

  const collateMutation = useMutation({
    mutationFn: (query) => axios.post(`${API}/search/collate`, { query }),
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

  const deleteCategoryMutation = useMutation({
    mutationFn: (id) => axios.delete(`${API}/categories/${id}`),
    onSuccess: () => {
      showToast("Category deleted", "success");
      queryClient.invalidateQueries(["categories"]);
    }
  });

  const cleanCategoryMutation = useMutation({
    mutationFn: (id) => axios.post(`${API}/categories/${id}/clean`),
    onSuccess: () => {
      showToast("Category cleaned! All results removed.", "success");
      queryClient.invalidateQueries(["categories"]);
      refetchResults();
    }
  });

  if (!user) return <Navigate to="/login" />;

  const categories = categoriesData?.categories || [];
  const results = resultsData?.results || [];

  // Build category tree
  const categoryTree = categories.filter(c => !c.parent_id);
  const getChildren = (parentId) => categories.filter(c => c.parent_id === parentId);

  const toggleCategory = (id) => {
    setSelectedCategories(prev => 
      prev.includes(id) ? prev.filter(c => c !== id) : [...prev, id]
    );
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
              <Checkbox 
                checked={selectedCategories.includes(cat.id)}
                onCheckedChange={() => toggleCategory(cat.id)}
                data-testid={`cat-checkbox-${cat.id}`}
              />
              <span className="text-white/90 text-sm flex-1">{cat.name}</span>
              <Badge className="text-xs bg-white/10">({cat.search_result_count || 0})</Badge>
              <div className="opacity-0 group-hover:opacity-100 flex gap-1">
                <button onClick={() => { setNewCategory({...newCategory, parent_id: cat.id}); setShowCreateCategory(true); }} className="text-green-400" title="Add subcategory">
                  <Plus size={14} />
                </button>
                <button onClick={() => cleanCategoryMutation.mutate(cat.id)} className="text-yellow-400" title="Clean category">
                  <RefreshCw size={14} />
                </button>
                <button onClick={() => deleteCategoryMutation.mutate(cat.id)} className="text-red-400" title="Delete">
                  <Trash2 size={14} />
                </button>
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
          <h1 className="text-3xl font-bold text-gradient-gold mb-2">{user.ultimate_search_name || user.username}'s Ultimate Search</h1>
          <p className="text-white/60">Your personal InfoJet 2.0 categorization dashboard</p>
        </div>

        <div className="grid lg:grid-cols-4 gap-6">
          {/* Left Sidebar - Categories */}
          <div className="lg:col-span-1">
            <Card className="card-glass p-4" data-testid="categories-panel">
              <div className="flex items-center justify-between mb-4">
                <h3 className="text-lg font-bold text-yellow-400">Categories</h3>
                <Button size="sm" onClick={() => setShowCreateCategory(true)} data-testid="create-category-btn">
                  <Plus size={14} />
                </Button>
              </div>
              
              {loadingCategories ? (
                <p className="text-white/60 text-sm">Loading...</p>
              ) : categories.length === 0 ? (
                <p className="text-white/60 text-sm">No categories yet. Create one to start!</p>
              ) : (
                <>
                  <div className="flex gap-2 mb-3">
                    <Button size="sm" variant="outline" onClick={() => setSelectedCategories(categories.map(c => c.id))} className="text-xs">Select All</Button>
                    <Button size="sm" variant="outline" onClick={() => setSelectedCategories([])} className="text-xs">Deselect All</Button>
                  </div>
                  <div className="max-h-[400px] overflow-y-auto">
                    {renderCategoryTree(categoryTree)}
                  </div>
                </>
              )}

              {/* Aggregation Options */}
              <div className="mt-4 pt-4 border-t border-white/10">
                <Label className="text-white/70 text-xs">Search Aggregation:</Label>
                <Select value={aggregation} onValueChange={setAggregation}>
                  <SelectTrigger className="form-input mt-1 text-xs">
                    <SelectValue />
                  </SelectTrigger>
                  <SelectContent className="bg-slate-800">
                    <SelectItem value="and_or">And/Or (All selected + more)</SelectItem>
                    <SelectItem value="and">And (Exactly selected)</SelectItem>
                    <SelectItem value="or">Or (Any of selected)</SelectItem>
                  </SelectContent>
                </Select>
              </div>
            </Card>
          </div>

          {/* Main Content */}
          <div className="lg:col-span-3">
            {/* Search Bar */}
            <Card className="card-glass p-4 mb-6" data-testid="search-bar">
              <div className="flex gap-4">
                <Input 
                  className="form-input flex-1"
                  placeholder="Enter search query to collate..."
                  value={searchQuery}
                  onChange={e => setSearchQuery(e.target.value)}
                  data-testid="search-input"
                />
                <Button 
                  onClick={() => collateMutation.mutate(searchQuery)}
                  disabled={!searchQuery || collateMutation.isPending}
                  className="btn-gold"
                  data-testid="collate-btn"
                >
                  {collateMutation.isPending ? <RefreshCw className="animate-spin" /> : <Search className="mr-2" />}
                  Search & Collate
                </Button>
                <Button 
                  onClick={() => refetchResults()}
                  variant="outline"
                  data-testid="quick-search-btn"
                >
                  Quick Search
                </Button>
              </div>
            </Card>

            {/* Results */}
            <Card className="card-glass p-4" data-testid="results-panel">
              <div className="flex items-center justify-between mb-4">
                <h3 className="text-lg font-bold text-white">Search Results ({results.length})</h3>
              </div>
              
              {loadingResults ? (
                <p className="text-white/60">Loading results...</p>
              ) : results.length === 0 ? (
                <p className="text-white/60">No results yet. Use Search & Collate to populate!</p>
              ) : (
                <div className="space-y-4 max-h-[600px] overflow-y-auto">
                  {results.map(result => (
                    <div key={result.id} className="p-4 bg-white/5 rounded-lg hover:bg-white/10 transition" data-testid={`result-${result.id}`}>
                      <div className="flex items-start justify-between mb-2">
                        <a href={result.url} target="_blank" rel="noopener noreferrer" className="text-yellow-400 hover:underline font-semibold">
                          {result.title}
                        </a>
                        <Badge className="text-xs">{result.document_type}</Badge>
                      </div>
                      <p className="text-white/70 text-sm mb-2">{result.snippet}</p>
                      <div className="flex flex-wrap gap-1">
                        {result.category_ids?.map(catId => {
                          const cat = categories.find(c => c.id === catId);
                          return cat ? <Badge key={catId} className="text-xs bg-blue-500/20">{cat.name}</Badge> : null;
                        })}
                      </div>
                      {result.location && (
                        <p className="text-white/50 text-xs mt-2">📍 {result.location.lat.toFixed(2)}, {result.location.lng.toFixed(2)}</p>
                      )}
                    </div>
                  ))}
                </div>
              )}
            </Card>
          </div>
        </div>

        {/* Create Category Dialog */}
        <Dialog open={showCreateCategory} onOpenChange={setShowCreateCategory}>
          <DialogContent className="bg-slate-900 border-yellow-400/30">
            <DialogHeader>
              <DialogTitle className="text-yellow-400">Create Category</DialogTitle>
              <DialogDescription className="text-white/70">
                Write an InfoJet 2.0 protocol to categorize web content. Use "and" or "&" between groups, "or" within groups. Use + for include all, ^ for exclude all.
              </DialogDescription>
            </DialogHeader>
            <div className="space-y-4 py-4">
              <div>
                <Label className="text-white">Category Name *</Label>
                <Input 
                  className="form-input mt-1"
                  placeholder="e.g., American Civil War Heroes"
                  value={newCategory.name}
                  onChange={e => setNewCategory({...newCategory, name: e.target.value})}
                  data-testid="category-name-input"
                />
              </div>
              <div>
                <Label className="text-white">Protocol (InfoJet 2.0) *</Label>
                <Textarea 
                  className="form-input mt-1 font-mono text-sm"
                  rows={4}
                  placeholder="(word1 or word2) & (word3 or word4)+"
                  value={newCategory.protocol}
                  onChange={e => setNewCategory({...newCategory, protocol: e.target.value})}
                  data-testid="category-protocol-input"
                />
                <p className="text-white/50 text-xs mt-1">
                  Tip: "and" works as "&". Use + to include all words, ^ to exclude all words in a group.
                </p>
              </div>
              <div className="flex items-center gap-4">
                <div className="flex items-center gap-2">
                  <Checkbox 
                    checked={newCategory.is_public}
                    onCheckedChange={checked => setNewCategory({...newCategory, is_public: checked})}
                  />
                  <Label className="text-white/80">Public</Label>
                </div>
                <div className="flex-1">
                  <Label className="text-white/80 text-xs">Price (for Marketplace)</Label>
                  <Input 
                    className="form-input mt-1"
                    type="number"
                    step="0.01"
                    placeholder="Leave empty if free"
                    value={newCategory.price || ""}
                    onChange={e => setNewCategory({...newCategory, price: e.target.value ? parseFloat(e.target.value) : null})}
                  />
                </div>
              </div>
            </div>
            <DialogFooter>
              <Button variant="outline" onClick={() => setShowCreateCategory(false)}>Cancel</Button>
              <Button 
                className="btn-gold"
                onClick={() => createCategoryMutation.mutate(newCategory)}
                disabled={!newCategory.name || !newCategory.protocol || createCategoryMutation.isPending}
                data-testid="save-category-btn"
              >
                {createCategoryMutation.isPending ? "Saving..." : "Create Category"}
              </Button>
            </DialogFooter>
          </DialogContent>
        </Dialog>
      </div>
    </div>
  );
};

// ============ STATISTICS PAGE ============
const StatsPage = () => {
  const { user } = useAuth();
  const { data: stats } = useQuery({
    queryKey: ["stats"],
    queryFn: () => axios.get(`${API}/stats`).then(r => r.data)
  });
  const { data: leaderboard } = useQuery({
    queryKey: ["leaderboard"],
    queryFn: () => axios.get(`${API}/leaderboard`).then(r => r.data)
  });

  if (!user) return <Navigate to="/login" />;

  return (
    <div className="min-h-screen pt-20 px-4">
      <StarsBackground />
      <div className="max-w-6xl mx-auto">
        <h1 className="text-3xl font-bold text-gradient-gold mb-8 text-center">Statistics & Leaderboard</h1>

        <div className="grid md:grid-cols-2 lg:grid-cols-4 gap-6 mb-8">
          <Card className="card-glass p-6 text-center">
            <Users className="mx-auto text-blue-400 mb-2" size={32} />
            <p className="text-3xl font-bold text-white">{stats?.global?.total_users || 0}</p>
            <p className="text-white/60 text-sm">Total Users</p>
          </Card>
          <Card className="card-glass p-6 text-center">
            <FileText className="mx-auto text-green-400 mb-2" size={32} />
            <p className="text-3xl font-bold text-white">{stats?.global?.public_categories || 0}</p>
            <p className="text-white/60 text-sm">Public Categories</p>
          </Card>
          <Card className="card-glass p-6 text-center">
            <Search className="mx-auto text-purple-400 mb-2" size={32} />
            <p className="text-3xl font-bold text-white">{stats?.global?.total_search_results || 0}</p>
            <p className="text-white/60 text-sm">Search Results</p>
          </Card>
          <Card className="card-glass p-6 text-center">
            <Egg className="mx-auto text-yellow-400 mb-2" size={32} />
            <p className="text-3xl font-bold text-white">{user.laughter_points || 0}</p>
            <p className="text-white/60 text-sm">Your Laughter Points</p>
          </Card>
        </div>

        <div className="grid md:grid-cols-2 gap-6">
          <Card className="card-glass p-6">
            <h3 className="text-xl font-bold text-yellow-400 mb-4 flex items-center gap-2">
              <Trophy /> Top Laughter Points
            </h3>
            <div className="space-y-3">
              {leaderboard?.top_laughter_points?.map((u, i) => (
                <div key={u.id} className="flex items-center gap-3 p-2 bg-white/5 rounded">
                  <span className="text-2xl">{i === 0 ? '🥇' : i === 1 ? '🥈' : i === 2 ? '🥉' : `${i + 1}.`}</span>
                  <span className="flex-1 text-white">{u.username}</span>
                  <Badge className="bg-yellow-400/20 text-yellow-300">{u.laughter_points || 0} pts</Badge>
                </div>
              ))}
            </div>
          </Card>

          <Card className="card-glass p-6">
            <h3 className="text-xl font-bold text-yellow-400 mb-4 flex items-center gap-2">
              <Star /> Top Protocol Creators
            </h3>
            <div className="space-y-3">
              {leaderboard?.top_protocol_creators?.map((tc, i) => (
                <div key={tc.user?.id} className="flex items-center gap-3 p-2 bg-white/5 rounded">
                  <span className="text-2xl">{i === 0 ? '🥇' : i === 1 ? '🥈' : i === 2 ? '🥉' : `${i + 1}.`}</span>
                  <span className="flex-1 text-white">{tc.user?.username}</span>
                  <Badge className="bg-blue-400/20 text-blue-300">{tc.protocol_count} protocols</Badge>
                </div>
              ))}
            </div>
          </Card>
        </div>
      </div>
    </div>
  );
};

// ============ MARKETPLACE PAGE ============
const MarketplacePage = () => {
  const { user } = useAuth();
  const showToast = useToast();
  const { data: protocols, isLoading } = useQuery({
    queryKey: ["marketplace"],
    queryFn: () => axios.get(`${API}/marketplace/protocols`).then(r => r.data)
  });

  const buyMutation = useMutation({
    mutationFn: (id) => axios.post(`${API}/marketplace/buy/${id}`),
    onSuccess: (data) => {
      showToast("Redirecting to PayPal...", "success");
      window.open(data.data.paypal_url, '_blank');
    },
    onError: (err) => showToast(err.response?.data?.detail || "Purchase failed", "error")
  });

  if (!user) return <Navigate to="/login" />;

  return (
    <div className="min-h-screen pt-20 px-4">
      <StarsBackground />
      <div className="max-w-6xl mx-auto">
        <div className="text-center mb-8">
          <Badge className="mb-4 bg-red-500/20 text-red-300">🐻 As Dangerous to the App Market as a Kodiak Bear!</Badge>
          <h1 className="text-3xl font-bold text-gradient-gold mb-2">Protocol Marketplace</h1>
          <p className="text-white/60">Buy and sell InfoJet 2.0 protocols - First in Flight with Monetization of Searches!</p>
        </div>

        {isLoading ? (
          <p className="text-center text-white/60">Loading marketplace...</p>
        ) : protocols?.protocols?.length === 0 ? (
          <Card className="card-glass p-8 text-center">
            <Store className="mx-auto text-yellow-400 mb-4" size={48} />
            <h3 className="text-xl text-white mb-2">No protocols for sale yet!</h3>
            <p className="text-white/60">Be the first to list your protocols in the marketplace.</p>
          </Card>
        ) : (
          <div className="grid md:grid-cols-2 lg:grid-cols-3 gap-6">
            {protocols?.protocols?.map(p => (
              <Card key={p.id} className="card-glass p-4" data-testid={`protocol-${p.id}`}>
                <CardHeader>
                  <CardTitle className="text-white">{p.name}</CardTitle>
                  <CardDescription className="text-white/60 font-mono text-xs">{p.protocol}</CardDescription>
                </CardHeader>
                <CardContent>
                  <div className="flex items-center justify-between mb-4">
                    <Badge className="bg-green-500/20 text-green-300 text-lg">${p.price?.toFixed(2)}</Badge>
                    <span className="text-white/50 text-sm">{p.search_result_count || 0} results</span>
                  </div>
                  <p className="text-white/60 text-sm">By: {p.owner?.username}</p>
                </CardContent>
                <CardFooter>
                  <Button 
                    onClick={() => buyMutation.mutate(p.id)}
                    className="btn-gold w-full"
                    disabled={buyMutation.isPending}
                  >
                    <CreditCard className="mr-2" /> Buy Protocol
                  </Button>
                </CardFooter>
              </Card>
            ))}
          </div>
        )}
      </div>
    </div>
  );
};

// ============ MAP PAGE (Placeholder) ============
const MapPage = () => {
  const { user } = useAuth();

  if (!user) return <Navigate to="/login" />;

  return (
    <div className="min-h-screen pt-20 px-4">
      <StarsBackground />
      <div className="max-w-6xl mx-auto">
        <h1 className="text-3xl font-bold text-gradient-gold mb-8 text-center">Map View</h1>
        <Card className="card-glass p-8 text-center">
          <Map className="mx-auto text-yellow-400 mb-4" size={64} />
          <h3 className="text-xl text-white mb-2">Interactive Map Coming Soon!</h3>
          <p className="text-white/60">View your search results plotted on a global map with color-coded categories.</p>
          <p className="text-white/50 text-sm mt-4">Each dot will have a clickable popup with article details!</p>
        </Card>
      </div>
    </div>
  );
};

// ============ LEGAL PAGES ============
const UserAgreementPage = () => {
  const { data } = useQuery({
    queryKey: ["user-agreement"],
    queryFn: () => axios.get(`${API}/legal/user-agreement`).then(r => r.data)
  });

  return (
    <div className="min-h-screen pt-20 px-4">
      <StarsBackground />
      <div className="max-w-4xl mx-auto">
        <Card className="card-glass p-8">
          <h1 className="text-3xl font-bold text-gradient-gold mb-6">{data?.title || "User Agreement"}</h1>
          <div className="prose prose-invert max-w-none text-white/80 whitespace-pre-wrap">
            {data?.content || "Loading..."}
          </div>
        </Card>
      </div>
    </div>
  );
};

const PrivacyPage = () => {
  const { data } = useQuery({
    queryKey: ["privacy"],
    queryFn: () => axios.get(`${API}/legal/privacy-policy`).then(r => r.data)
  });

  return (
    <div className="min-h-screen pt-20 px-4">
      <StarsBackground />
      <div className="max-w-4xl mx-auto">
        <Card className="card-glass p-8">
          <h1 className="text-3xl font-bold text-gradient-gold mb-6">{data?.title || "Privacy Policy"}</h1>
          <div className="prose prose-invert max-w-none text-white/80 whitespace-pre-wrap">
            {data?.content || "Loading..."}
          </div>
        </Card>
      </div>
    </div>
  );
};

// ============ MAIN APP ============
function App() {
  return (
    <QueryClientProvider client={queryClient}>
      <AuthProvider>
        <ToastProvider>
          <BrowserRouter>
            <div className="app-container">
              <Navbar />
              <NewsHeadlines />
              <FloatingEasterEgg />
              <Routes>
                <Route path="/" element={<HomePage />} />
                <Route path="/login" element={<LoginPage />} />
                <Route path="/book" element={<BookPage />} />
                <Route path="/food" element={<FoodPage />} />
                <Route path="/infopilot" element={<InfoPilotPage />} />
                <Route path="/search" element={<UltimateSearchPage />} />
                <Route path="/stats" element={<StatsPage />} />
                <Route path="/marketplace" element={<MarketplacePage />} />
                <Route path="/map" element={<MapPage />} />
                <Route path="/legal/user-agreement" element={<UserAgreementPage />} />
                <Route path="/legal/privacy" element={<PrivacyPage />} />
                <Route path="*" element={<Navigate to="/" />} />
              </Routes>
            </div>
          </BrowserRouter>
        </ToastProvider>
      </AuthProvider>
    </QueryClientProvider>
  );
}

export default App;
