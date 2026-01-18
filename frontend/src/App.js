import { useState, useEffect, createContext, useContext, useCallback, useMemo } from "react";
import { BrowserRouter, Routes, Route, Navigate, useNavigate, Link } from "react-router-dom";
import { QueryClient, QueryClientProvider, useQuery, useMutation, useQueryClient } from "@tanstack/react-query";
import axios from "axios";
import { MapContainer, TileLayer, CircleMarker, Popup } from "react-leaflet";
import "leaflet/dist/leaflet.css";
import "@/App.css";
import { Button } from "@/components/ui/button";
import { Card, CardContent, CardDescription, CardFooter, CardHeader, CardTitle } from "@/components/ui/card";
import { Input } from "@/components/ui/input";
import { Label } from "@/components/ui/label";
import { Textarea } from "@/components/ui/textarea";
import { Badge } from "@/components/ui/badge";
import { Tabs, TabsContent, TabsList, TabsTrigger } from "@/components/ui/tabs";
import { Dialog, DialogContent, DialogDescription, DialogFooter, DialogHeader, DialogTitle } from "@/components/ui/dialog";
import { Select, SelectContent, SelectItem, SelectTrigger, SelectValue } from "@/components/ui/select";
import { Separator } from "@/components/ui/separator";
import { Checkbox } from "@/components/ui/checkbox";
import { 
  Book, ShoppingCart, Utensils, Star, Mail, MapPin, Phone, Clock, Rocket, Sparkles, Heart, 
  ChevronDown, ChevronRight, Menu, X, Send, Plus, Minus, AlertTriangle, CheckCircle, Ship, 
  Globe, CreditCard, Search, User, LogOut, Settings, Home, BarChart3, Map, Store, Egg,
  Trophy, FileText, Users, Shield, Trash2, Edit, Copy, RefreshCw, Newspaper, Quote, Gift,
  MessageCircle, UserPlus, Download, Palette, Sun, Moon, Layers, DollarSign, TrendingUp
} from "lucide-react";

const BACKEND_URL = process.env.REACT_APP_BACKEND_URL;
const API = `${BACKEND_URL}/api`;

const queryClient = new QueryClient({
  defaultOptions: { queries: { staleTime: 30000, retry: 1 } }
});

// PayPal Configuration
const PAYPAL_INFOPILOT_LINK = "https://www.paypal.com/ncp/payment/LZDBN3SQU4NWQ";
const PAYPAL_BOOK_LINK = "https://www.paypal.com/ncp/payment/LGXMXSG3D2MXU";
const AMAZON_BOOK_LINK = "https://www.amazon.com/Letters-Evelyn-John-Selman/dp/B0F3XFG14J";

// Theme Context
const ThemeContext = createContext(null);
export const useTheme = () => useContext(ThemeContext);

const ThemeProvider = ({ children }) => {
  const [theme, setTheme] = useState(() => {
    const saved = localStorage.getItem("theme");
    return saved ? JSON.parse(saved) : { mode: "dark", preset: "cosmic" };
  });

  const themes = {
    cosmic: { primary: "#fbbf24", secondary: "#8b5cf6", background: "#0f172a" },
    royal: { primary: "#3b82f6", secondary: "#6366f1", background: "#1e1b4b" },
    hot: { primary: "#ef4444", secondary: "#f97316", background: "#1c1917" },
    ocean: { primary: "#06b6d4", secondary: "#0ea5e9", background: "#0c4a6e" },
    forest: { primary: "#22c55e", secondary: "#10b981", background: "#14532d" },
    sunset: { primary: "#f59e0b", secondary: "#ec4899", background: "#431407" },
    ruby: { primary: "#dc2626", secondary: "#be123c", background: "#450a0a" },
    light: { primary: "#3b82f6", secondary: "#8b5cf6", background: "#f8fafc" }
  };

  useEffect(() => {
    localStorage.setItem("theme", JSON.stringify(theme));
    const colors = themes[theme.preset] || themes.cosmic;
    document.documentElement.style.setProperty("--color-primary", colors.primary);
    document.documentElement.style.setProperty("--color-secondary", colors.secondary);
    document.documentElement.style.setProperty("--color-background", colors.background);
    document.body.className = theme.mode === "light" ? "light-mode" : "";
  }, [theme]);

  return (
    <ThemeContext.Provider value={{ theme, setTheme, themes }}>
      {children}
    </ThemeContext.Provider>
  );
};

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
            <button onClick={() => setToasts(prev => prev.filter(t => t.id !== toast.id))} className="ml-2"><X size={16} /></button>
          </div>
        ))}
      </div>
    </ToastContext.Provider>
  );
};

// ============ FLOATING EASTER EGG ============
const FloatingEasterEgg = () => {
  const [visible, setVisible] = useState(false);
  const [egg, setEgg] = useState(null);
  const [position, setPosition] = useState({ x: 0, y: 0 });
  const [showContent, setShowContent] = useState(false);
  const { user, setUser } = useAuth();
  const showToast = useToast();

  useEffect(() => {
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
    if (!user) { setShowContent(true); return; }
    try {
      const res = await axios.post(`${API}/easter-eggs/catch`, { egg_index: 0 });
      showToast(res.data.message, "success");
      setUser(prev => ({ ...prev, laughter_points: res.data.total_points }));
      setShowContent(true);
    } catch (e) { setShowContent(true); }
  };

  if (!visible || !egg) return null;

  return (
    <div className="fixed z-40 cursor-pointer animate-bounce-slow" style={{ left: position.x, top: position.y }} data-testid="floating-easter-egg">
      {!showContent ? (
        <div onClick={catchEgg} className="text-6xl hover:scale-125 transition-transform">🥚</div>
      ) : (
        <Card className="card-glass w-80 p-4 animate-slide-in" data-testid="easter-egg-content">
          <button onClick={() => { setVisible(false); setShowContent(false); }} className="absolute top-2 right-2 text-white/60 hover:text-white"><X size={20} /></button>
          <div className="text-center mb-3">
            <span className="text-4xl">🥚</span>
            <Badge className="ml-2 bg-yellow-400/20 text-yellow-300">+{user ? '10' : '0'} Laughter Points!</Badge>
          </div>
          <div className="space-y-3 text-sm">
            <div className="bg-purple-500/20 p-3 rounded-lg"><p className="text-white/90 italic">{egg.joke}</p></div>
            {egg.protocol_idea && (
              <div className="bg-blue-500/20 p-3 rounded-lg">
                <p className="text-blue-300 font-semibold text-xs mb-1">💡 Protocol Idea:</p>
                <p className="text-white/80 text-xs font-mono">{egg.protocol_idea}</p>
                <Button size="sm" variant="outline" className="mt-2 text-xs" onClick={() => { navigator.clipboard.writeText(egg.protocol_idea); showToast("Protocol copied!"); }}>
                  <Copy size={12} className="mr-1" /> Copy Protocol
                </Button>
              </div>
            )}
            {egg.pricing_suggestion && <div className="bg-green-500/20 p-3 rounded-lg"><p className="text-green-300 font-semibold text-xs">💰 {egg.pricing_suggestion}</p></div>}
            {egg.map_instruction && <div className="bg-orange-500/20 p-3 rounded-lg"><p className="text-orange-300 text-xs">{egg.map_instruction}</p></div>}
          </div>
        </Card>
      )}
    </div>
  );
};

// ============ NEWS HEADLINES ============
const NewsHeadlines = () => {
  const [expanded, setExpanded] = useState(false);
  const { data, refetch, isLoading } = useQuery({
    queryKey: ["headlines"],
    queryFn: () => axios.get(`${API}/news/headlines`).then(r => r.data)
  });

  return (
    <div className="fixed top-16 right-4 z-30" data-testid="news-headlines">
      <button onClick={() => setExpanded(!expanded)} className="bg-gradient-to-r from-red-500 to-orange-500 text-white px-3 py-2 rounded-lg flex items-center gap-2 text-sm font-semibold shadow-lg">
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
  const { theme, setTheme } = useTheme();
  const navigate = useNavigate();
  const [mobileOpen, setMobileOpen] = useState(false);

  const navItems = user ? [
    { path: "/", label: "Home", icon: <Home size={18} /> },
    { path: "/search", label: "Search", icon: <Search size={18} /> },
    { path: "/map", label: "Map", icon: <Map size={18} /> },
    { path: "/stats", label: "Stats", icon: <BarChart3 size={18} /> },
    { path: "/marketplace", label: "Market", icon: <Store size={18} /> },
    { path: "/chat", label: "Chat", icon: <MessageCircle size={18} /> },
    { path: "/templates", label: "Templates", icon: <Layers size={18} /> },
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

        <div className="hidden lg:flex items-center gap-2">
          {navItems.map(item => (
            <Link key={item.path} to={item.path} className="flex items-center gap-1 px-3 py-2 rounded-lg text-white/80 hover:text-yellow-400 hover:bg-yellow-400/10 transition text-sm">
              {item.icon} <span>{item.label}</span>
            </Link>
          ))}
        </div>

        <div className="flex items-center gap-2">
          <Button variant="ghost" size="sm" onClick={() => setTheme(prev => ({ ...prev, mode: prev.mode === "dark" ? "light" : "dark" }))}>
            {theme.mode === "dark" ? <Sun size={18} /> : <Moon size={18} />}
          </Button>
          
          {user ? (
            <>
              <Badge className="bg-yellow-400/20 text-yellow-300 hidden sm:flex items-center gap-1">
                <Egg size={14} /> {user.laughter_points || 0}
              </Badge>
              <div className="relative group">
                <Button variant="ghost" className="flex items-center gap-2 text-white">
                  <User size={18} /> <span className="hidden sm:inline">{user.username}</span>
                </Button>
                <div className="absolute right-0 mt-2 w-48 bg-slate-800 rounded-lg shadow-xl opacity-0 invisible group-hover:opacity-100 group-hover:visible transition-all">
                  <Link to="/settings" className="flex items-center gap-2 px-4 py-2 text-white/80 hover:bg-white/10"><Settings size={16} /> Settings</Link>
                  <Link to="/reports" className="flex items-center gap-2 px-4 py-2 text-white/80 hover:bg-white/10"><FileText size={16} /> My Reports</Link>
                  <Link to="/revenue" className="flex items-center gap-2 px-4 py-2 text-white/80 hover:bg-white/10"><DollarSign size={16} /> Revenue</Link>
                  <Link to="/themes" className="flex items-center gap-2 px-4 py-2 text-white/80 hover:bg-white/10"><Palette size={16} /> Themes</Link>
                  {user.is_admin && <Link to="/admin" className="flex items-center gap-2 px-4 py-2 text-white/80 hover:bg-white/10"><Shield size={16} /> Admin</Link>}
                  <button onClick={logout} className="flex items-center gap-2 px-4 py-2 text-red-400 hover:bg-white/10 w-full"><LogOut size={16} /> Logout</button>
                </div>
              </div>
            </>
          ) : (
            <Link to="/login"><Button className="btn-gold">Login</Button></Link>
          )}
          <button className="lg:hidden text-white" onClick={() => setMobileOpen(!mobileOpen)}>
            {mobileOpen ? <X size={28} /> : <Menu size={28} />}
          </button>
        </div>
      </div>

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
      <section className="min-h-[80vh] flex flex-col items-center justify-center relative overflow-hidden" data-testid="hero-section">
        <div className="absolute inset-0 opacity-20">
          <div className="absolute top-20 left-10 text-8xl animate-float">🚀</div>
          <div className="absolute top-40 right-20 text-7xl animate-float" style={{ animationDelay: '0.5s' }}>📚</div>
          <div className="absolute bottom-40 left-20 text-7xl animate-float" style={{ animationDelay: '1s' }}>🚢</div>
          <div className="absolute bottom-20 right-10 text-8xl animate-float" style={{ animationDelay: '1.5s' }}>🥩</div>
        </div>

        <div className="text-center z-10 max-w-4xl mx-auto animate-slide-in">
          <Badge className="mb-2 bg-blue-600/30 text-blue-300 border-blue-500/30 text-xs px-3 py-1">✈️ A Top Pilot Enterprises, Inc. Company</Badge>
          <Badge className="mb-4 bg-yellow-400/20 text-yellow-400 border-yellow-400/30 text-sm px-4 py-1 ml-2">🎉 First in Flight with Monetization of Searches! It's a Bear! 🐻</Badge>
          
          <h1 className="hero-title text-5xl md:text-7xl font-bold mb-6 text-gradient-gold text-shadow-glow">InfoPilot Explorer</h1>
          <p className="hero-subtitle text-xl md:text-2xl text-white/90 mb-4">Your #1 Resource for Finding Information Valuable to You!</p>
          <p className="text-lg text-white/70 mb-4 max-w-2xl mx-auto">A Worldwide Information Exchange Database with Boolean Search & Categorization. Plus: Letters to Evelyn & Maestro Bistro! 🌌</p>

          <div className="flex flex-wrap justify-center gap-2 mb-8">
            <Badge className="bg-green-500/20 text-green-300">⭐ 19 Five-Star Reviews</Badge>
            <Badge className="bg-purple-500/20 text-purple-300">🎬 Film by Voyage Media!</Badge>
            <Badge className="bg-red-500/20 text-red-300">🐻 Dangerous to the App Market!</Badge>
          </div>

          <div className="flex flex-col sm:flex-row gap-4 justify-center">
            {user ? (
              <>
                <Button onClick={() => navigate('/search')} className="btn-gold text-lg px-8 py-6" data-testid="cta-search"><Search className="mr-2" /> Ultimate Search</Button>
                <Button onClick={() => navigate('/map')} className="btn-navy text-lg px-8 py-6"><Map className="mr-2" /> Map View</Button>
              </>
            ) : (
              <>
                <Button onClick={() => navigate('/login')} className="btn-gold text-lg px-8 py-6" data-testid="cta-login"><Rocket className="mr-2" /> Get Started - $1/mo</Button>
                <Button onClick={() => navigate('/book')} className="btn-navy text-lg px-8 py-6"><Book className="mr-2" /> Letters to Evelyn</Button>
              </>
            )}
            <Button onClick={() => navigate('/food')} className="bg-gradient-to-r from-orange-600 to-red-600 text-white font-bold px-8 py-6 rounded-full hover:scale-105 transition-all">
              <Utensils className="mr-2" /> Maestro Bistro
            </Button>
          </div>
        </div>
        <div className="absolute bottom-10 animate-bounce"><ChevronDown size={32} className="text-yellow-400" /></div>
      </section>

      <section className="py-16 max-w-6xl mx-auto">
        <h2 className="text-3xl font-bold text-center text-gradient-gold mb-12">What Makes InfoPilot Powerful?</h2>
        <div className="grid md:grid-cols-3 gap-6">
          {[
            { icon: <Search size={32} />, title: "InfoJet 2.0 Protocols", desc: "Create custom Boolean search protocols to categorize ANY information!" },
            { icon: <Map size={32} />, title: "Interactive Maps", desc: "See results plotted on a global map with color-coded categories!" },
            { icon: <Store size={32} />, title: "Protocol Marketplace", desc: "Sell your protocols! First in Flight with Monetization of Searches!" },
            { icon: <Egg size={32} />, title: "Easter Eggs", desc: "Catch floating eggs for jokes, protocol ideas, and earn points! 🥚" },
            { icon: <MessageCircle size={32} />, title: "Chat & Groups", desc: "Connect with other researchers in chat rooms and groups!" },
            { icon: <Layers size={32} />, title: "Protocol Templates", desc: "Browse and copy proven protocol templates to get started!" },
          ].map((f, i) => (
            <Card key={i} className="card-glass p-6 card-hover">
              <div className="text-yellow-400 mb-4">{f.icon}</div>
              <h3 className="text-xl font-bold text-white mb-2">{f.title}</h3>
              <p className="text-white/70">{f.desc}</p>
            </Card>
          ))}
        </div>
      </section>

      <footer className="footer py-12 px-4 mt-16">
        <div className="max-w-6xl mx-auto text-center">
          <div className="flex items-center justify-center gap-2 mb-4">
            <Sparkles className="text-yellow-400" size={24} />
            <span className="text-xl font-bold text-gradient-gold">InfoPilot Explorer</span>
          </div>
          <p className="text-white/60 text-sm">Top Pilot Enterprises, Inc. - "It's a Bear!" 🐻</p>
          <div className="flex justify-center gap-4 mt-4 text-white/40 text-sm">
            <Link to="/book" className="hover:text-yellow-400">📚 Book</Link>
            <Link to="/food" className="hover:text-yellow-400">🚚 Food</Link>
            <Link to="/legal/user-agreement" className="hover:text-yellow-400">📜 Terms</Link>
            <Link to="/legal/privacy" className="hover:text-yellow-400">🔒 Privacy</Link>
          </div>
          <p className="text-white/30 text-xs mt-4">© 2014-2025 John Selman - Letters to Evelyn | © 2025 Top Pilot Enterprises, Inc.</p>
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
          <CardTitle className="text-2xl text-gradient-gold text-center">{mode === "login" ? "Welcome Back!" : "Join InfoPilot"}</CardTitle>
        </CardHeader>
        <CardContent>
          <form onSubmit={handleSubmit} className="space-y-4">
            {mode === "register" && (
              <div>
                <Label className="text-white">Username *</Label>
                <Input className="form-input mt-1" placeholder="Username" value={form.username} onChange={e => setForm({...form, username: e.target.value})} required data-testid="register-username" />
              </div>
            )}
            <div>
              <Label className="text-white">Email *</Label>
              <Input className="form-input mt-1" type="email" placeholder="you@example.com" value={form.email} onChange={e => setForm({...form, email: e.target.value})} required data-testid="login-email" />
            </div>
            <div>
              <Label className="text-white">Password *</Label>
              <Input className="form-input mt-1" type="password" placeholder="••••••••" value={form.password} onChange={e => setForm({...form, password: e.target.value})} required data-testid="login-password" />
            </div>
            <Button type="submit" className="btn-gold w-full" disabled={loading} data-testid="login-submit">
              {loading ? "Loading..." : (mode === "login" ? "Login" : "Create Account")}
            </Button>
          </form>
        </CardContent>
        <CardFooter className="flex flex-col gap-4">
          <button onClick={() => setMode(mode === "login" ? "register" : "login")} className="text-yellow-400 text-sm hover:underline">
            {mode === "login" ? "Don't have an account? Register" : "Already have an account? Login"}
          </button>
          <a href={PAYPAL_INFOPILOT_LINK} target="_blank" rel="noopener noreferrer" className="text-blue-400 text-xs hover:underline">Subscribe via PayPal - $1/mo →</a>
        </CardFooter>
      </Card>
    </div>
  );
};

// ============ INTERACTIVE MAP PAGE ============
const MapPage = () => {
  const { user } = useAuth();
  const [scope, setScope] = useState("personal");
  const { data: mapData, isLoading } = useQuery({
    queryKey: ["map-data", scope],
    queryFn: () => axios.get(`${API}/map/data`, { params: { scope } }).then(r => r.data),
    enabled: !!user
  });
  const { data: categoriesData } = useQuery({
    queryKey: ["categories"],
    queryFn: () => axios.get(`${API}/categories`).then(r => r.data),
    enabled: !!user
  });

  if (!user) return <Navigate to="/login" />;

  const categories = categoriesData?.categories || [];
  const points = mapData?.points || [];

  return (
    <div className="min-h-screen pt-20 px-4">
      <StarsBackground />
      <div className="max-w-7xl mx-auto">
        <div className="flex items-center justify-between mb-6">
          <div>
            <h1 className="text-3xl font-bold text-gradient-gold">Interactive Map View</h1>
            <p className="text-white/60">Explore search results plotted on a global map</p>
          </div>
          <div className="flex items-center gap-4">
            <Select value={scope} onValueChange={setScope}>
              <SelectTrigger className="form-input w-40">
                <SelectValue />
              </SelectTrigger>
              <SelectContent className="bg-slate-800">
                <SelectItem value="personal">My Results</SelectItem>
                <SelectItem value="worldwide">Worldwide</SelectItem>
              </SelectContent>
            </Select>
          </div>
        </div>

        <Card className="card-glass overflow-hidden" data-testid="map-container">
          {isLoading ? (
            <div className="h-[600px] flex items-center justify-center"><RefreshCw className="animate-spin text-yellow-400" size={48} /></div>
          ) : (
            <MapContainer center={[40, -40]} zoom={2} style={{ height: "600px", width: "100%" }} className="rounded-lg">
              <TileLayer
                url="https://{s}.basemaps.cartocdn.com/dark_all/{z}/{x}/{y}{r}.png"
                attribution='&copy; <a href="https://www.openstreetmap.org/copyright">OpenStreetMap</a>'
              />
              {points.map((point, idx) => (
                <CircleMarker
                  key={idx}
                  center={[point.lat, point.lng]}
                  radius={Math.min(8 + point.result_count * 2, 20)}
                  fillColor={point.color}
                  color={point.color}
                  weight={2}
                  opacity={0.8}
                  fillOpacity={0.6}
                >
                  <Popup className="custom-popup">
                    <div className="bg-slate-900 p-3 rounded-lg min-w-[250px]">
                      <div className="flex items-center justify-between mb-2">
                        <Badge className="bg-blue-500/20 text-blue-300">{point.result_count} results</Badge>
                        <span className="text-xs text-white/60">{point.category_count} categories</span>
                      </div>
                      <div className="space-y-2 max-h-48 overflow-y-auto">
                        {point.results?.map((r, i) => (
                          <div key={i} className="p-2 bg-white/5 rounded">
                            <a href={r.url} target="_blank" rel="noopener noreferrer" className="text-yellow-400 text-sm hover:underline font-semibold block truncate">{r.title}</a>
                            <p className="text-white/60 text-xs mt-1 line-clamp-2">{r.snippet}</p>
                            <Badge className="text-xs mt-1">{r.document_type}</Badge>
                          </div>
                        ))}
                      </div>
                    </div>
                  </Popup>
                </CircleMarker>
              ))}
            </MapContainer>
          )}
        </Card>

        <div className="mt-6 grid md:grid-cols-4 gap-4">
          <Card className="card-glass p-4 text-center">
            <MapPin className="mx-auto text-yellow-400 mb-2" size={24} />
            <p className="text-2xl font-bold text-white">{points.length}</p>
            <p className="text-white/60 text-sm">Locations</p>
          </Card>
          <Card className="card-glass p-4 text-center">
            <FileText className="mx-auto text-blue-400 mb-2" size={24} />
            <p className="text-2xl font-bold text-white">{points.reduce((a, p) => a + p.result_count, 0)}</p>
            <p className="text-white/60 text-sm">Total Results</p>
          </Card>
          <Card className="card-glass p-4 text-center">
            <Layers className="mx-auto text-green-400 mb-2" size={24} />
            <p className="text-2xl font-bold text-white">{categories.length}</p>
            <p className="text-white/60 text-sm">Categories</p>
          </Card>
          <Card className="card-glass p-4 text-center">
            <Globe className="mx-auto text-purple-400 mb-2" size={24} />
            <p className="text-2xl font-bold text-white">{scope === "personal" ? "Personal" : "Worldwide"}</p>
            <p className="text-white/60 text-sm">View Scope</p>
          </Card>
        </div>
      </div>
    </div>
  );
};

// ============ PROTOCOL TEMPLATES PAGE ============
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
            <Button onClick={() => setShowCreate(true)} className="btn-gold">
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
                <Input className="form-input mt-1" placeholder="e.g., Tech Innovation Finder" value={newTemplate.name} onChange={e => setNewTemplate({...newTemplate, name: e.target.value})} />
              </div>
              <div>
                <Label className="text-white">Description *</Label>
                <Textarea className="form-input mt-1" placeholder="What does this protocol find?" value={newTemplate.description} onChange={e => setNewTemplate({...newTemplate, description: e.target.value})} />
              </div>
              <div>
                <Label className="text-white">Protocol (InfoJet 2.0) *</Label>
                <Textarea className="form-input mt-1 font-mono text-sm" rows={3} placeholder="(word1 or word2) & (word3)+" value={newTemplate.protocol} onChange={e => setNewTemplate({...newTemplate, protocol: e.target.value})} />
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
              <Button className="btn-gold" onClick={() => createMutation.mutate(newTemplate)} disabled={!newTemplate.name || !newTemplate.protocol || createMutation.isPending}>
                {createMutation.isPending ? "Creating..." : "Create Template"}
              </Button>
            </DialogFooter>
          </DialogContent>
        </Dialog>
      </div>
    </div>
  );
};

// ============ CHAT PAGE ============
const ChatPage = () => {
  const { user } = useAuth();
  const showToast = useToast();
  const queryClient = useQueryClient();
  const [selectedRoom, setSelectedRoom] = useState(null);
  const [message, setMessage] = useState("");
  const [showCreate, setShowCreate] = useState(false);
  const [newRoom, setNewRoom] = useState({ name: "", description: "", is_public: true });

  const { data: roomsData, isLoading: loadingRooms } = useQuery({
    queryKey: ["chat-rooms"],
    queryFn: () => axios.get(`${API}/chat/rooms`).then(r => r.data),
    enabled: !!user
  });

  const { data: messagesData, refetch: refetchMessages } = useQuery({
    queryKey: ["chat-messages", selectedRoom],
    queryFn: () => axios.get(`${API}/chat/rooms/${selectedRoom}/messages`).then(r => r.data),
    enabled: !!selectedRoom,
    refetchInterval: 3000
  });

  const createRoomMutation = useMutation({
    mutationFn: (room) => axios.post(`${API}/chat/rooms`, room),
    onSuccess: () => {
      showToast("Room created! 🎉", "success");
      queryClient.invalidateQueries(["chat-rooms"]);
      setShowCreate(false);
      setNewRoom({ name: "", description: "", is_public: true });
    },
    onError: () => showToast("Failed to create room", "error")
  });

  const sendMessageMutation = useMutation({
    mutationFn: (content) => axios.post(`${API}/chat/rooms/${selectedRoom}/messages`, { content }),
    onSuccess: () => {
      setMessage("");
      refetchMessages();
    }
  });

  const joinRoomMutation = useMutation({
    mutationFn: (roomId) => axios.post(`${API}/chat/rooms/${roomId}/join`),
    onSuccess: () => {
      showToast("Joined room!", "success");
      queryClient.invalidateQueries(["chat-rooms"]);
    }
  });

  if (!user) return <Navigate to="/login" />;

  const rooms = roomsData?.rooms || [];
  const messages = messagesData?.messages || [];

  return (
    <div className="min-h-screen pt-20 px-4">
      <StarsBackground />
      <div className="max-w-6xl mx-auto">
        <div className="flex items-center justify-between mb-6">
          <h1 className="text-3xl font-bold text-gradient-gold">Chat Rooms</h1>
          <Button onClick={() => setShowCreate(true)} className="btn-gold"><Plus className="mr-2" /> Create Room</Button>
        </div>

        <div className="grid md:grid-cols-3 gap-6">
          <Card className="card-glass p-4 md:col-span-1 max-h-[600px] overflow-y-auto">
            <h3 className="text-lg font-bold text-yellow-400 mb-4">Rooms</h3>
            {loadingRooms ? (
              <p className="text-white/60">Loading...</p>
            ) : rooms.length === 0 ? (
              <p className="text-white/60 text-sm">No rooms yet. Create one!</p>
            ) : (
              <div className="space-y-2">
                {rooms.map(room => (
                  <div
                    key={room.id}
                    onClick={() => setSelectedRoom(room.id)}
                    className={`p-3 rounded-lg cursor-pointer transition ${selectedRoom === room.id ? 'bg-yellow-400/20 border border-yellow-400/50' : 'bg-white/5 hover:bg-white/10'}`}
                  >
                    <div className="flex items-center justify-between">
                      <span className="text-white font-semibold">{room.name}</span>
                      <Badge className="text-xs">{room.members?.length || 0} members</Badge>
                    </div>
                    {room.description && <p className="text-white/50 text-xs mt-1">{room.description}</p>}
                  </div>
                ))}
              </div>
            )}
          </Card>

          <Card className="card-glass p-4 md:col-span-2 flex flex-col h-[600px]">
            {selectedRoom ? (
              <>
                <div className="flex-1 overflow-y-auto mb-4 space-y-3">
                  {messages.map(msg => (
                    <div key={msg.id} className={`p-3 rounded-lg ${msg.user_id === user.id ? 'bg-yellow-400/10 ml-8' : 'bg-white/5 mr-8'}`}>
                      <div className="flex items-center gap-2 mb-1">
                        <span className="text-yellow-400 text-sm font-semibold">{msg.username}</span>
                        <span className="text-white/40 text-xs">{new Date(msg.created_at).toLocaleTimeString()}</span>
                      </div>
                      <p className="text-white/90">{msg.content}</p>
                    </div>
                  ))}
                </div>
                <div className="flex gap-2">
                  <Input className="form-input flex-1" placeholder="Type a message..." value={message} onChange={e => setMessage(e.target.value)} onKeyPress={e => e.key === 'Enter' && sendMessageMutation.mutate(message)} />
                  <Button onClick={() => sendMessageMutation.mutate(message)} className="btn-gold" disabled={!message || sendMessageMutation.isPending}>
                    <Send size={18} />
                  </Button>
                </div>
              </>
            ) : (
              <div className="flex-1 flex items-center justify-center">
                <div className="text-center">
                  <MessageCircle className="mx-auto text-yellow-400/50 mb-4" size={48} />
                  <p className="text-white/60">Select a room to start chatting</p>
                </div>
              </div>
            )}
          </Card>
        </div>

        <Dialog open={showCreate} onOpenChange={setShowCreate}>
          <DialogContent className="bg-slate-900 border-yellow-400/30">
            <DialogHeader>
              <DialogTitle className="text-yellow-400">Create Chat Room</DialogTitle>
            </DialogHeader>
            <div className="space-y-4 py-4">
              <div>
                <Label className="text-white">Room Name *</Label>
                <Input className="form-input mt-1" placeholder="My Chat Room" value={newRoom.name} onChange={e => setNewRoom({...newRoom, name: e.target.value})} />
              </div>
              <div>
                <Label className="text-white">Description</Label>
                <Textarea className="form-input mt-1" placeholder="What's this room about?" value={newRoom.description} onChange={e => setNewRoom({...newRoom, description: e.target.value})} />
              </div>
              <div className="flex items-center gap-2">
                <Checkbox checked={newRoom.is_public} onCheckedChange={checked => setNewRoom({...newRoom, is_public: checked})} />
                <Label className="text-white">Public Room</Label>
              </div>
            </div>
            <DialogFooter>
              <Button variant="outline" onClick={() => setShowCreate(false)}>Cancel</Button>
              <Button className="btn-gold" onClick={() => createRoomMutation.mutate(newRoom)} disabled={!newRoom.name || createRoomMutation.isPending}>
                Create Room
              </Button>
            </DialogFooter>
          </DialogContent>
        </Dialog>
      </div>
    </div>
  );
};

// ============ REVENUE DASHBOARD ============
const RevenuePage = () => {
  const { user } = useAuth();
  const { data, isLoading } = useQuery({
    queryKey: ["revenue"],
    queryFn: () => axios.get(`${API}/revenue/dashboard`).then(r => r.data),
    enabled: !!user
  });

  if (!user) return <Navigate to="/login" />;

  const exportCSV = async () => {
    window.open(`${API}/revenue/export`, '_blank');
  };

  return (
    <div className="min-h-screen pt-20 px-4">
      <StarsBackground />
      <div className="max-w-6xl mx-auto">
        <div className="flex items-center justify-between mb-8">
          <div>
            <h1 className="text-3xl font-bold text-gradient-gold">Revenue Dashboard</h1>
            <p className="text-white/60">Track your protocol sales and earnings</p>
          </div>
          <Button onClick={exportCSV} className="btn-gold"><Download className="mr-2" /> Export CSV</Button>
        </div>

        {isLoading ? (
          <div className="text-center py-12"><RefreshCw className="animate-spin mx-auto text-yellow-400" size={48} /></div>
        ) : (
          <>
            <div className="grid md:grid-cols-4 gap-6 mb-8">
              <Card className="card-glass p-6 text-center">
                <DollarSign className="mx-auto text-green-400 mb-2" size={32} />
                <p className="text-3xl font-bold text-white">${data?.total_revenue?.toFixed(2) || '0.00'}</p>
                <p className="text-white/60 text-sm">Total Revenue</p>
              </Card>
              <Card className="card-glass p-6 text-center">
                <TrendingUp className="mx-auto text-blue-400 mb-2" size={32} />
                <p className="text-3xl font-bold text-white">{data?.total_sales || 0}</p>
                <p className="text-white/60 text-sm">Total Sales</p>
              </Card>
              <Card className="card-glass p-6 text-center">
                <Store className="mx-auto text-purple-400 mb-2" size={32} />
                <p className="text-3xl font-bold text-white">{data?.top_protocols?.length || 0}</p>
                <p className="text-white/60 text-sm">Products Sold</p>
              </Card>
              <Card className="card-glass p-6 text-center">
                <CreditCard className="mx-auto text-yellow-400 mb-2" size={32} />
                <p className="text-3xl font-bold text-white">${data?.wallet_balance?.toFixed(2) || '0.00'}</p>
                <p className="text-white/60 text-sm">Wallet Balance</p>
              </Card>
            </div>

            <Card className="card-glass p-6">
              <h3 className="text-xl font-bold text-yellow-400 mb-4">Top Selling Protocols</h3>
              {data?.top_protocols?.length === 0 ? (
                <p className="text-white/60 text-center py-8">No sales yet. List your protocols in the marketplace!</p>
              ) : (
                <div className="space-y-3">
                  {data?.top_protocols?.map((p, i) => (
                    <div key={i} className="flex items-center justify-between p-4 bg-white/5 rounded-lg">
                      <div className="flex items-center gap-4">
                        <span className="text-2xl">{i === 0 ? '🥇' : i === 1 ? '🥈' : i === 2 ? '🥉' : `${i + 1}.`}</span>
                        <div>
                          <p className="text-white font-semibold">{p.name}</p>
                          <p className="text-white/50 text-sm">{p.count} sales</p>
                        </div>
                      </div>
                      <Badge className="bg-green-500/20 text-green-300 text-lg">${p.revenue?.toFixed(2)}</Badge>
                    </div>
                  ))}
                </div>
              )}
            </Card>
          </>
        )}
      </div>
    </div>
  );
};

// ============ THEME GALLERY PAGE ============
const ThemesPage = () => {
  const { user } = useAuth();
  const { theme, setTheme, themes } = useTheme();
  const showToast = useToast();

  if (!user) return <Navigate to="/login" />;

  const presetList = [
    { id: "cosmic", name: "Cosmic", emoji: "🌌" },
    { id: "royal", name: "Royal", emoji: "👑" },
    { id: "hot", name: "Hot", emoji: "🔥" },
    { id: "ocean", name: "Ocean", emoji: "🌊" },
    { id: "forest", name: "Forest", emoji: "🌲" },
    { id: "sunset", name: "Sunset", emoji: "🌅" },
    { id: "ruby", name: "Ruby", emoji: "💎" },
    { id: "light", name: "Light Mode", emoji: "☀️" }
  ];

  const applyTheme = (preset) => {
    setTheme({ mode: preset === "light" ? "light" : "dark", preset });
    showToast(`Theme changed to ${preset}! ✨`, "success");
    axios.put(`${API}/users/theme`, { mode: preset === "light" ? "light" : "dark", preset }).catch(() => {});
  };

  return (
    <div className="min-h-screen pt-20 px-4">
      <StarsBackground />
      <div className="max-w-4xl mx-auto">
        <div className="text-center mb-8">
          <h1 className="text-3xl font-bold text-gradient-gold mb-2">Theme Gallery</h1>
          <p className="text-white/60">Customize your InfoPilot experience</p>
        </div>

        <div className="flex justify-center gap-4 mb-8">
          <Button onClick={() => setTheme(prev => ({ ...prev, mode: "dark" }))} className={`${theme.mode === "dark" ? "btn-gold" : "btn-navy"}`}>
            <Moon className="mr-2" size={18} /> Dark Mode
          </Button>
          <Button onClick={() => setTheme(prev => ({ ...prev, mode: "light" }))} className={`${theme.mode === "light" ? "btn-gold" : "btn-navy"}`}>
            <Sun className="mr-2" size={18} /> Light Mode
          </Button>
        </div>

        <div className="grid grid-cols-2 md:grid-cols-4 gap-4">
          {presetList.map(p => (
            <Card
              key={p.id}
              onClick={() => applyTheme(p.id)}
              className={`card-glass p-4 cursor-pointer transition hover:scale-105 ${theme.preset === p.id ? 'ring-2 ring-yellow-400' : ''}`}
              style={{ borderColor: themes[p.id]?.primary }}
            >
              <div className="text-center">
                <span className="text-4xl mb-2 block">{p.emoji}</span>
                <p className="text-white font-semibold">{p.name}</p>
                <div className="flex justify-center gap-1 mt-2">
                  <div className="w-4 h-4 rounded-full" style={{ backgroundColor: themes[p.id]?.primary }} />
                  <div className="w-4 h-4 rounded-full" style={{ backgroundColor: themes[p.id]?.secondary }} />
                  <div className="w-4 h-4 rounded-full" style={{ backgroundColor: themes[p.id]?.background }} />
                </div>
              </div>
            </Card>
          ))}
        </div>

        <Card className="card-glass p-6 mt-8">
          <h3 className="text-xl font-bold text-yellow-400 mb-4">Current Theme Preview</h3>
          <div className="grid grid-cols-3 gap-4">
            <div className="p-4 rounded-lg text-center" style={{ backgroundColor: themes[theme.preset]?.background }}>
              <p className="text-white/60 text-xs">Background</p>
              <p className="text-white font-mono text-sm">{themes[theme.preset]?.background}</p>
            </div>
            <div className="p-4 rounded-lg text-center" style={{ backgroundColor: themes[theme.preset]?.primary }}>
              <p className="text-black/60 text-xs">Primary</p>
              <p className="text-black font-mono text-sm">{themes[theme.preset]?.primary}</p>
            </div>
            <div className="p-4 rounded-lg text-center" style={{ backgroundColor: themes[theme.preset]?.secondary }}>
              <p className="text-white/60 text-xs">Secondary</p>
              <p className="text-white font-mono text-sm">{themes[theme.preset]?.secondary}</p>
            </div>
          </div>
        </Card>
      </div>
    </div>
  );
};

// ============ PERSONAL REPORTS PAGE ============
const ReportsPage = () => {
  const { user } = useAuth();
  const showToast = useToast();
  const queryClient = useQueryClient();
  const [showCreate, setShowCreate] = useState(false);
  const [newReport, setNewReport] = useState({ title: "", content: "", location: null });

  const { data, isLoading } = useQuery({
    queryKey: ["reports"],
    queryFn: () => axios.get(`${API}/reports`).then(r => r.data),
    enabled: !!user
  });

  const createMutation = useMutation({
    mutationFn: (report) => axios.post(`${API}/reports`, report),
    onSuccess: () => {
      showToast("Report created! 🎉", "success");
      queryClient.invalidateQueries(["reports"]);
      setShowCreate(false);
      setNewReport({ title: "", content: "", location: null });
    },
    onError: () => showToast("Failed to create report", "error")
  });

  const deleteMutation = useMutation({
    mutationFn: (id) => axios.delete(`${API}/reports/${id}`),
    onSuccess: () => {
      showToast("Report deleted", "success");
      queryClient.invalidateQueries(["reports"]);
    }
  });

  if (!user) return <Navigate to="/login" />;

  return (
    <div className="min-h-screen pt-20 px-4">
      <StarsBackground />
      <div className="max-w-4xl mx-auto">
        <div className="flex items-center justify-between mb-8">
          <div>
            <h1 className="text-3xl font-bold text-gradient-gold">My Personal Reports</h1>
            <p className="text-white/60">Create organic reports about any topic</p>
          </div>
          <Button onClick={() => setShowCreate(true)} className="btn-gold"><Plus className="mr-2" /> Create Report</Button>
        </div>

        {isLoading ? (
          <div className="text-center py-12"><RefreshCw className="animate-spin mx-auto text-yellow-400" size={48} /></div>
        ) : data?.reports?.length === 0 ? (
          <Card className="card-glass p-8 text-center">
            <FileText className="mx-auto text-yellow-400 mb-4" size={48} />
            <h3 className="text-xl text-white mb-2">No reports yet!</h3>
            <p className="text-white/60">Create your first personal report to share your knowledge.</p>
          </Card>
        ) : (
          <div className="space-y-4">
            {data?.reports?.map(report => (
              <Card key={report.id} className="card-glass p-4">
                <div className="flex items-start justify-between">
                  <div className="flex-1">
                    <h3 className="text-lg font-bold text-white">{report.title}</h3>
                    <p className="text-white/70 mt-2">{report.content}</p>
                    <div className="flex items-center gap-4 mt-3 text-white/50 text-sm">
                      <Badge>{report.document_type}</Badge>
                      <span>{new Date(report.created_at).toLocaleDateString()}</span>
                      {report.location && <span className="flex items-center gap-1"><MapPin size={14} /> Location attached</span>}
                    </div>
                  </div>
                  <Button variant="ghost" size="sm" onClick={() => deleteMutation.mutate(report.id)} className="text-red-400 hover:text-red-300">
                    <Trash2 size={18} />
                  </Button>
                </div>
              </Card>
            ))}
          </div>
        )}

        <Dialog open={showCreate} onOpenChange={setShowCreate}>
          <DialogContent className="bg-slate-900 border-yellow-400/30">
            <DialogHeader>
              <DialogTitle className="text-yellow-400">Create Personal Report</DialogTitle>
              <DialogDescription className="text-white/70">Share your knowledge on any topic (max 3 images)</DialogDescription>
            </DialogHeader>
            <div className="space-y-4 py-4">
              <div>
                <Label className="text-white">Title *</Label>
                <Input className="form-input mt-1" placeholder="Report title" value={newReport.title} onChange={e => setNewReport({...newReport, title: e.target.value})} />
              </div>
              <div>
                <Label className="text-white">Content *</Label>
                <Textarea className="form-input mt-1" rows={6} placeholder="Your report content..." value={newReport.content} onChange={e => setNewReport({...newReport, content: e.target.value})} />
              </div>
            </div>
            <DialogFooter>
              <Button variant="outline" onClick={() => setShowCreate(false)}>Cancel</Button>
              <Button className="btn-gold" onClick={() => createMutation.mutate(newReport)} disabled={!newReport.title || !newReport.content || createMutation.isPending}>
                Create Report
              </Button>
            </DialogFooter>
          </DialogContent>
        </Dialog>
      </div>
    </div>
  );
};

// ============ BOOK PAGE ============
const BookPage = () => {
  const { data: book } = useQuery({ queryKey: ["book"], queryFn: () => axios.get(`${API}/book`).then(r => r.data) });
  const { data: prices } = useQuery({ queryKey: ["book-prices"], queryFn: () => axios.get(`${API}/book/prices`).then(r => r.data) });

  if (!book) return <div className="min-h-screen pt-24 flex items-center justify-center text-white">Loading...</div>;

  return (
    <div className="min-h-screen pt-24 px-4">
      <StarsBackground />
      <div className="max-w-6xl mx-auto">
        <div className="text-center mb-12 animate-slide-in">
          <Badge className="mb-4 bg-purple-500/20 text-purple-300">📖 True Supernatural Thriller Comedy</Badge>
          <h1 className="text-4xl md:text-5xl font-bold text-gradient-gold mb-4">{book.title}</h1>
          <p className="text-xl text-white/80">by {book.author}</p>
          <Badge className="mt-4 bg-green-500/20 text-green-300">⭐ {book.review_count} Five-Star Reviews</Badge>
        </div>

        <div className="grid md:grid-cols-2 gap-8">
          <Card className="card-glass p-6" data-testid="book-info">
            <div className="h-48 bg-gradient-to-br from-purple-900 to-indigo-900 rounded-lg flex items-center justify-center mb-6">
              <span className="text-8xl">📚</span>
            </div>
            <p className="text-white/80 mb-4">{book.long_description}</p>
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
          </div>
        </div>
      </div>
    </div>
  );
};

// ============ FOOD PAGE ============
const FoodPage = () => {
  const showToast = useToast();
  const { data: menu } = useQuery({ queryKey: ["food-menu"], queryFn: () => axios.get(`${API}/food/menu`).then(r => r.data) });
  const [cart, setCart] = useState([]);

  const addToCart = (item) => {
    const existing = cart.find(c => c.id === item.id);
    if (existing) setCart(cart.map(c => c.id === item.id ? {...c, quantity: c.quantity + 1} : c));
    else setCart([...cart, { ...item, quantity: 1 }]);
    showToast(`Added ${item.name} to cart! 🛒`, "success");
  };

  if (!menu) return <div className="min-h-screen pt-24 flex items-center justify-center text-white">Loading...</div>;

  return (
    <div className="min-h-screen pt-24 px-4">
      <StarsBackground />
      <div className="max-w-6xl mx-auto">
        <div className="text-center mb-12 animate-slide-in">
          <Badge className="mb-4 bg-orange-500/20 text-orange-300">🚚 Now Serving in Brunswick, Maine!</Badge>
          <h1 className="text-4xl md:text-5xl font-bold text-gradient-gold mb-4">{menu.restaurant_name}</h1>
          <p className="text-xl text-white/80">{menu.tagline}</p>
        </div>

        <div className="grid md:grid-cols-2 lg:grid-cols-3 gap-6 mb-12">
          {menu.menu?.map(item => (
            <Card key={item.id} className="card-glass overflow-hidden card-hover">
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
              <CardContent><p className="text-white/70 text-sm">{item.description}</p></CardContent>
              <CardFooter>
                <Button onClick={() => addToCart(item)} className="btn-gold w-full"><Plus className="mr-2" /> Add to Cart</Button>
              </CardFooter>
            </Card>
          ))}
        </div>

        {cart.length > 0 && (
          <Card className="card-glass p-6 sticky bottom-4">
            <div className="flex items-center justify-between mb-4">
              <h3 className="text-xl font-bold text-yellow-400 flex items-center gap-2"><ShoppingCart /> Cart ({cart.length})</h3>
              <span className="text-2xl font-bold text-white">${cart.reduce((s, i) => s + i.price * i.quantity, 0).toFixed(2)}</span>
            </div>
            <p className="text-center text-white/60 text-sm">Visit us at {menu.location} to place your order!</p>
          </Card>
        )}
      </div>
    </div>
  );
};

// ============ INFOPILOT PAGE ============
const InfoPilotPage = () => {
  const { data: plans } = useQuery({ queryKey: ["infopilot-plans"], queryFn: () => axios.get(`${API}/infopilot/plans`).then(r => r.data) });

  if (!plans) return <div className="min-h-screen pt-24 flex items-center justify-center text-white">Loading...</div>;

  return (
    <div className="min-h-screen pt-24 px-4">
      <StarsBackground />
      <div className="max-w-4xl mx-auto">
        <div className="text-center mb-12">
          <h1 className="text-4xl md:text-5xl font-bold text-gradient-gold mb-4">InfoPilot Explorer</h1>
          <p className="text-xl text-white/80">Boolean Search & Categorization Platform - Only $1/month!</p>
        </div>

        <div className="grid md:grid-cols-2 gap-6 mb-8">
          <Card className="card-glass p-6 border-2 border-blue-500/30">
            <Badge className="bg-blue-500/20 text-blue-300 mb-4">Most Popular</Badge>
            <h3 className="text-2xl font-bold text-white mb-2">Monthly</h3>
            <div className="text-4xl font-bold text-yellow-400 mb-4">${plans.monthly?.price}<span className="text-lg text-white/60">/mo</span></div>
            <ul className="space-y-2 mb-6">
              {plans.monthly?.features?.map((f, i) => (
                <li key={i} className="flex items-center gap-2 text-white/80"><CheckCircle className="text-green-400" size={16} /> {f}</li>
              ))}
            </ul>
            <a href={PAYPAL_INFOPILOT_LINK} target="_blank" rel="noopener noreferrer"><Button className="btn-gold w-full">Subscribe Now</Button></a>
          </Card>

          <Card className="card-glass p-6 border-2 border-yellow-500/30">
            <Badge className="bg-yellow-500/20 text-yellow-300 mb-4">Save 17%!</Badge>
            <h3 className="text-2xl font-bold text-white mb-2">Yearly</h3>
            <div className="text-4xl font-bold text-yellow-400 mb-4">${plans.yearly?.price}<span className="text-lg text-white/60">/yr</span></div>
            <ul className="space-y-2 mb-6">
              {plans.yearly?.features?.map((f, i) => (
                <li key={i} className="flex items-center gap-2 text-white/80"><CheckCircle className="text-green-400" size={16} /> {f}</li>
              ))}
            </ul>
            <a href={PAYPAL_INFOPILOT_LINK} target="_blank" rel="noopener noreferrer"><Button className="btn-gold w-full">Subscribe Now</Button></a>
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
  const [quickSearchQuery, setQuickSearchQuery] = useState("");
  const [selectedCategories, setSelectedCategories] = useState([]);
  const [aggregation, setAggregation] = useState("and_or");
  const [showCreateCategory, setShowCreateCategory] = useState(false);
  const [showEditCategory, setShowEditCategory] = useState(false);
  const [editingCategory, setEditingCategory] = useState(null);
  const [newCategory, setNewCategory] = useState({ name: "", protocol: "", parent_id: null, is_public: true, price: null });
  const [expandedCategories, setExpandedCategories] = useState({});

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

  const updateCategoryMutation = useMutation({
    mutationFn: ({ id, updates }) => axios.put(`${API}/categories/${id}`, updates),
    onSuccess: () => {
      showToast("Protocol saved! 🎉", "success");
      queryClient.invalidateQueries(["categories"]);
      setShowEditCategory(false);
      setEditingCategory(null);
    },
    onError: (err) => showToast(err.response?.data?.detail || "Failed to update category", "error")
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
              <span className="text-white/90 text-sm flex-1">{cat.name}</span>
              <Badge className="text-xs bg-white/10">({cat.search_result_count || 0})</Badge>
              <div className="opacity-0 group-hover:opacity-100 flex gap-1">
                <button onClick={() => openEditCategory(cat)} className="text-blue-400" title="Edit Protocol" data-testid={`edit-category-${cat.id}`}><Edit size={14} /></button>
                <button onClick={() => { setNewCategory({...newCategory, parent_id: cat.id}); setShowCreateCategory(true); }} className="text-green-400" title="Add subcategory"><Plus size={14} /></button>
                <button onClick={() => deleteCategoryMutation.mutate(cat.id)} className="text-red-400" title="Delete"><Trash2 size={14} /></button>
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
                    <Button size="sm" variant="outline" onClick={() => setSelectedCategories([])} className="text-xs" data-testid="deselect-all-btn">Deselect All</Button>
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
                    <SelectItem value="and">And (Exact Match)</SelectItem>
                    <SelectItem value="or">Or (Any Match)</SelectItem>
                  </SelectContent>
                </Select>
              </div>
            </Card>

            {/* Recommended Protocols Section */}
            <Card className="card-glass p-4" data-testid="recommended-protocols">
              <h3 className="text-lg font-bold text-yellow-400 mb-3 flex items-center gap-2"><Star size={16} /> Recommended</h3>
              <div className="space-y-2">
                {recommendedProtocols.map(t => (
                  <div key={t.id} className="p-2 bg-white/5 rounded-lg hover:bg-white/10 cursor-pointer transition" onClick={() => { setNewCategory({...newCategory, protocol: t.protocol, name: t.name}); setShowCreateCategory(true); }}>
                    <p className="text-white/90 text-sm font-semibold">{t.name}</p>
                    <p className="text-white/50 text-xs truncate">{t.protocol}</p>
                  </div>
                ))}
                {recommendedProtocols.length === 0 && <p className="text-white/50 text-xs">No recommendations available</p>}
              </div>
            </Card>
          </div>

          <div className="lg:col-span-3">
            <Card className="card-glass p-4 mb-6">
              <div className="flex gap-4 mb-4">
                <Input className="form-input flex-1" placeholder="Enter search query..." value={searchQuery} onChange={e => setSearchQuery(e.target.value)} data-testid="search-query-input" />
                <Button onClick={() => collateMutation.mutate(searchQuery)} disabled={!searchQuery || collateMutation.isPending} className="btn-gold" data-testid="collate-btn">
                  {collateMutation.isPending ? <RefreshCw className="animate-spin" /> : <Search className="mr-2" />} Search & Collate
                </Button>
              </div>
              {/* Quick Search within Results */}
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
                {quickSearchQuery && <Badge className="bg-blue-500/20 text-blue-300">Filtered: "{quickSearchQuery}"</Badge>}
              </div>
              {loadingResults ? <p className="text-white/60">Loading...</p> : filteredResults.length === 0 ? (
                <p className="text-white/60">{results.length > 0 ? "No results match your quick search." : "No results yet. Use Search & Collate!"}</p>
              ) : (
                <div className="space-y-4 max-h-[600px] overflow-y-auto">
                  {filteredResults.map(result => (
                    <div key={result.id} className="p-4 bg-white/5 rounded-lg hover:bg-white/10 transition" data-testid={`search-result-${result.id}`}>
                      <div className="flex items-start justify-between mb-2">
                        <a href={result.url} target="_blank" rel="noopener noreferrer" className="text-yellow-400 hover:underline font-semibold">{result.title}</a>
                        <Badge className="text-xs">{result.document_type}</Badge>
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
              <DialogDescription className="text-white/70">Write an InfoJet 2.0 protocol. Use "and" or "&amp;", "or" within groups, + for include all, ^ for exclude.</DialogDescription>
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
                  <Label className="text-white/80">Public (visible in Marketplace)</Label>
                </div>
                <div className="flex-1">
                  <Label className="text-white/80 text-xs">Sell Price ($)</Label>
                  <Input className="form-input mt-1" type="number" step="0.01" min="1" placeholder="Free (or $1+)" value={newCategory.price || ""} onChange={e => setNewCategory({...newCategory, price: e.target.value ? parseFloat(e.target.value) : null})} />
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

        {/* Edit Category / Save Protocol Modal */}
        <Dialog open={showEditCategory} onOpenChange={setShowEditCategory}>
          <DialogContent className="bg-slate-900 border-yellow-400/30">
            <DialogHeader>
              <DialogTitle className="text-yellow-400">Edit Category - Save Protocol</DialogTitle>
              <DialogDescription className="text-white/70">Modify your InfoJet 2.0 protocol. Changes will apply to future searches.</DialogDescription>
            </DialogHeader>
            {editingCategory && (
              <div className="space-y-4 py-4">
                <div>
                  <Label className="text-white">Category Name *</Label>
                  <Input className="form-input mt-1" value={editingCategory.name} onChange={e => setEditingCategory({...editingCategory, name: e.target.value})} data-testid="edit-category-name" />
                </div>
                <div>
                  <Label className="text-white">Protocol (InfoJet 2.0) *</Label>
                  <Textarea className="form-input mt-1 font-mono text-sm" rows={4} value={editingCategory.protocol} onChange={e => setEditingCategory({...editingCategory, protocol: e.target.value})} data-testid="edit-category-protocol" />
                </div>
                <div className="flex items-center gap-4">
                  <div className="flex items-center gap-2">
                    <Checkbox checked={editingCategory.is_public} onCheckedChange={checked => setEditingCategory({...editingCategory, is_public: checked})} />
                    <Label className="text-white/80">Public</Label>
                  </div>
                  <div className="flex items-center gap-2">
                    <Checkbox checked={editingCategory.price > 0} onCheckedChange={checked => setEditingCategory({...editingCategory, price: checked ? 1.00 : null})} />
                    <Label className="text-white/80">List on Marketplace</Label>
                  </div>
                  {editingCategory.price > 0 && (
                    <div className="flex-1">
                      <Label className="text-white/80 text-xs">Price ($)</Label>
                      <Input className="form-input mt-1" type="number" step="0.01" min="1" value={editingCategory.price || ""} onChange={e => setEditingCategory({...editingCategory, price: e.target.value ? parseFloat(e.target.value) : null})} />
                    </div>
                  )}
                </div>
              </div>
            )}
            <DialogFooter>
              <Button variant="outline" onClick={() => { setShowEditCategory(false); setEditingCategory(null); }}>Cancel</Button>
              <Button className="btn-gold" onClick={() => updateCategoryMutation.mutate({ id: editingCategory.id, updates: { name: editingCategory.name, protocol: editingCategory.protocol, is_public: editingCategory.is_public, price: editingCategory.price } })} disabled={!editingCategory?.name || !editingCategory?.protocol || updateCategoryMutation.isPending} data-testid="save-protocol-btn">
                {updateCategoryMutation.isPending ? "Saving..." : "Save Protocol"}
              </Button>
            </DialogFooter>
          </DialogContent>
        </Dialog>
      </div>
    </div>
  );
};

// ============ STATS PAGE ============
const StatsPage = () => {
  const { user } = useAuth();
  const { data: stats } = useQuery({ queryKey: ["stats"], queryFn: () => axios.get(`${API}/stats`).then(r => r.data) });
  const { data: leaderboard } = useQuery({ queryKey: ["leaderboard"], queryFn: () => axios.get(`${API}/leaderboard`).then(r => r.data) });

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
            <p className="text-white/60 text-sm">Your Points</p>
          </Card>
        </div>

        <div className="grid md:grid-cols-2 gap-6">
          <Card className="card-glass p-6">
            <h3 className="text-xl font-bold text-yellow-400 mb-4 flex items-center gap-2"><Trophy /> Top Laughter Points</h3>
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
            <h3 className="text-xl font-bold text-yellow-400 mb-4 flex items-center gap-2"><Star /> Top Protocol Creators</h3>
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
  const [selectedCategory, setSelectedCategory] = useState("all");
  const [showPayPalConnect, setShowPayPalConnect] = useState(false);
  
  const { data: protocols, isLoading } = useQuery({
    queryKey: ["marketplace", selectedCategory],
    queryFn: () => axios.get(`${API}/marketplace/protocols`, { params: selectedCategory !== "all" ? { category: selectedCategory } : {} }).then(r => r.data)
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

  // Extract unique category keywords for filtering
  const categoryKeywords = ["History", "Technology", "Science", "Business", "Health", "Sports", "Education", "Entertainment"];
  const protocolList = protocols?.protocols || [];

  return (
    <div className="min-h-screen pt-20 px-4">
      <StarsBackground />
      <div className="max-w-6xl mx-auto">
        <div className="text-center mb-8">
          <Badge className="mb-4 bg-red-500/20 text-red-300">🐻 As Dangerous as a Kodiak Bear!</Badge>
          <h1 className="text-3xl font-bold text-gradient-gold mb-2">Protocol Marketplace</h1>
          <p className="text-white/60">First in Flight with Monetization of Searches!</p>
        </div>

        {/* Category Filter */}
        <Card className="card-glass p-4 mb-6" data-testid="marketplace-categories">
          <div className="flex flex-wrap items-center gap-2">
            <span className="text-white/70 text-sm mr-2">Filter by Category:</span>
            <Badge 
              className={`cursor-pointer transition ${selectedCategory === "all" ? "bg-yellow-400/30 text-yellow-300" : "bg-white/10 text-white/60 hover:bg-white/20"}`}
              onClick={() => setSelectedCategory("all")}
            >
              All ({protocols?.total || 0})
            </Badge>
            {categoryKeywords.map(cat => (
              <Badge 
                key={cat}
                className={`cursor-pointer transition ${selectedCategory === cat ? "bg-yellow-400/30 text-yellow-300" : "bg-white/10 text-white/60 hover:bg-white/20"}`}
                onClick={() => setSelectedCategory(cat)}
              >
                {cat}
              </Badge>
            ))}
          </div>
        </Card>

        {/* Seller Dashboard Card */}
        <Card className="card-glass p-4 mb-6 border border-green-400/30" data-testid="seller-dashboard">
          <div className="flex items-center justify-between">
            <div>
              <h3 className="text-lg font-bold text-green-400">Become a Seller</h3>
              <p className="text-white/60 text-sm">Connect PayPal to receive payments for your protocols (85% commission)</p>
            </div>
            <Button onClick={() => setShowPayPalConnect(true)} className="bg-[#0070ba] hover:bg-[#003087] text-white" data-testid="connect-paypal-btn">
              <CreditCard className="mr-2" /> Connect PayPal
            </Button>
          </div>
        </Card>

        {isLoading ? <p className="text-center text-white/60">Loading...</p> : protocolList.length === 0 ? (
          <Card className="card-glass p-8 text-center" data-testid="marketplace-empty">
            <Store className="mx-auto text-yellow-400 mb-4" size={48} />
            <h3 className="text-xl text-white mb-2">No protocols for sale{selectedCategory !== "all" ? ` in ${selectedCategory}` : ""} yet!</h3>
            <p className="text-white/60 mb-4">Be the first to list your protocols in Ultimate Search.</p>
            <Link to="/search"><Button className="btn-gold">Go to Ultimate Search</Button></Link>
          </Card>
        ) : (
          <div className="grid md:grid-cols-2 lg:grid-cols-3 gap-6">
            {protocolList.map(p => (
              <Card key={p.id} className="card-glass p-4 hover:border-yellow-400/50 transition" data-testid={`protocol-${p.id}`}>
                <CardHeader className="pb-2">
                  <div className="flex items-start justify-between">
                    <CardTitle className="text-white text-lg">{p.name}</CardTitle>
                    <Badge className="bg-green-500/20 text-green-300 font-bold">${p.price?.toFixed(2)}</Badge>
                  </div>
                </CardHeader>
                <CardContent className="py-2">
                  <div className="bg-slate-800/50 p-2 rounded font-mono text-xs text-green-400 mb-3 max-h-16 overflow-y-auto">{p.protocol}</div>
                  <div className="flex items-center justify-between text-white/50 text-xs">
                    <span>By: {p.owner?.username || "Anonymous"}</span>
                    <span>{p.search_result_count || 0} results</span>
                  </div>
                </CardContent>
                <CardFooter className="pt-2 flex gap-2">
                  <Button onClick={() => buyMutation.mutate(p.id)} className="btn-gold flex-1" disabled={buyMutation.isPending || p.user_id === user.id} data-testid={`buy-protocol-${p.id}`}>
                    <CreditCard className="mr-2" size={16} /> {p.user_id === user.id ? "Your Protocol" : "Buy Protocol"}
                  </Button>
                  <Button variant="outline" onClick={() => { navigator.clipboard.writeText(p.protocol); showToast("Protocol copied!", "success"); }} title="Copy Protocol">
                    <Copy size={16} />
                  </Button>
                </CardFooter>
              </Card>
            ))}
          </div>
        )}

        {/* PayPal Connect Modal */}
        <Dialog open={showPayPalConnect} onOpenChange={setShowPayPalConnect}>
          <DialogContent className="bg-slate-900 border-yellow-400/30">
            <DialogHeader>
              <DialogTitle className="text-yellow-400">Connect PayPal Account</DialogTitle>
              <DialogDescription className="text-white/70">Link your PayPal Business account to receive payments</DialogDescription>
            </DialogHeader>
            <div className="py-4 space-y-4">
              <Card className="bg-blue-900/20 border-blue-400/30 p-4">
                <h4 className="text-blue-400 font-semibold mb-2">How It Works</h4>
                <ul className="text-white/70 text-sm space-y-1">
                  <li>• You receive 85% of each protocol sale</li>
                  <li>• InfoPilot keeps 15% platform fee</li>
                  <li>• Minimum PayPal payment: $1.00</li>
                  <li>• Payouts processed automatically</li>
                </ul>
              </Card>
              <div className="text-center">
                <a href="https://www.paypal.com/business" target="_blank" rel="noopener noreferrer" className="inline-flex items-center gap-2 bg-[#0070ba] hover:bg-[#003087] text-white font-bold py-3 px-6 rounded-lg transition">
                  <CreditCard size={20} /> Open PayPal Business
                </a>
                <p className="text-white/50 text-xs mt-2">PayPal integration coming soon! Your email will be linked automatically.</p>
              </div>
            </div>
            <DialogFooter>
              <Button variant="outline" onClick={() => setShowPayPalConnect(false)}>Close</Button>
            </DialogFooter>
          </DialogContent>
        </Dialog>
      </div>
    </div>
  );
};

// ============ LEGAL PAGES ============
const UserAgreementPage = () => {
  const { data } = useQuery({ queryKey: ["user-agreement"], queryFn: () => axios.get(`${API}/legal/user-agreement`).then(r => r.data) });

  return (
    <div className="min-h-screen pt-20 px-4">
      <StarsBackground />
      <div className="max-w-4xl mx-auto">
        <Card className="card-glass p-8">
          <h1 className="text-3xl font-bold text-gradient-gold mb-6">{data?.title || "User Agreement"}</h1>
          <div className="prose prose-invert max-w-none text-white/80 whitespace-pre-wrap">{data?.content || "Loading..."}</div>
        </Card>
      </div>
    </div>
  );
};

const PrivacyPage = () => {
  const { data } = useQuery({ queryKey: ["privacy"], queryFn: () => axios.get(`${API}/legal/privacy-policy`).then(r => r.data) });

  return (
    <div className="min-h-screen pt-20 px-4">
      <StarsBackground />
      <div className="max-w-4xl mx-auto">
        <Card className="card-glass p-8">
          <h1 className="text-3xl font-bold text-gradient-gold mb-6">{data?.title || "Privacy Policy"}</h1>
          <div className="prose prose-invert max-w-none text-white/80 whitespace-pre-wrap">{data?.content || "Loading..."}</div>
        </Card>
      </div>
    </div>
  );
};

// ============ MAIN APP ============
function App() {
  return (
    <QueryClientProvider client={queryClient}>
      <ThemeProvider>
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
                  <Route path="/chat" element={<ChatPage />} />
                  <Route path="/templates" element={<TemplatesPage />} />
                  <Route path="/reports" element={<ReportsPage />} />
                  <Route path="/revenue" element={<RevenuePage />} />
                  <Route path="/themes" element={<ThemesPage />} />
                  <Route path="/legal/user-agreement" element={<UserAgreementPage />} />
                  <Route path="/legal/privacy" element={<PrivacyPage />} />
                  <Route path="*" element={<Navigate to="/" />} />
                </Routes>
              </div>
            </BrowserRouter>
          </ToastProvider>
        </AuthProvider>
      </ThemeProvider>
    </QueryClientProvider>
  );
}

export default App;
