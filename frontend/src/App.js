import React, { useState, useEffect, createContext, useContext, useCallback } from "react";
import { BrowserRouter, Routes, Route, Navigate, useNavigate, useLocation } from "react-router-dom";
import axios from "axios";
import { Toaster, toast } from "sonner";
import { GoogleOAuthProvider, GoogleLogin } from "@react-oauth/google";
import {
  Search, Globe, FolderTree, BarChart3, Settings, LogOut, User, Plus, Trash2,
  Eye, EyeOff, ChevronDown, ChevronRight, Filter, Heart, ThumbsUp, Smile,
  Frown, AlertTriangle, Flag, Award, Home, Users, BookOpen, Menu, X, Loader2,
  ShoppingCart, CreditCard, Star, ExternalLink, Plane, Shield, Radar, Target,
  Crosshair, Navigation, Zap, Radio, Cpu, Book
} from "lucide-react";
import {
  PieChart, Pie, Cell, BarChart, Bar, XAxis, YAxis, CartesianGrid, Tooltip,
  Legend, ResponsiveContainer
} from "recharts";
import "@/App.css";

const BACKEND_URL = process.env.REACT_APP_BACKEND_URL;
const API = `${BACKEND_URL}/api`;

// Google OAuth Client ID
const GOOGLE_CLIENT_ID = "553762726406-a6it1kotb3tbb8o9j9ijad82r965o9va.apps.googleusercontent.com";

// Book Images
const BOOK_IMAGES = {
  globe: "https://customer-assets.emergentagent.com/job_0c3ceef4-3e2b-40c0-b767-31d91735cf23/artifacts/xxl3i9cv_global-network-world-globe-focusing-usa-symbolizing-data-transfer-worldwide-concept-data-transfer-global-connectivity-information-exchange-world-globe-usa-symbolism_918839-41653.jpg",
  author: "https://customer-assets.emergentagent.com/job_0c3ceef4-3e2b-40c0-b767-31d91735cf23/artifacts/rubak3hv_FB_IMG_1767397923842.jpg",
  infopilot: "https://customer-assets.emergentagent.com/job_0c3ceef4-3e2b-40c0-b767-31d91735cf23/artifacts/zxojhw91_image_1767356779418.png"
};

// Book Info
const BOOK_INFO = {
  title: "Letters to Evelyn",
  author: "John Selman",
  tagline: "A Prolific Odyssey of Love and Redemption",
  rating: 5.0,
  reviewsCount: 15,
  price: "$2.99",
  amazonUrl: "https://a.co/d/atfpIds",
  sintraUrl: "https://www.Letters-to-Evelyn.sintra.site",
  officialUrl: "https://letterstoevelynbyjohnselmanii.com",
  readersFavoriteUrl: "https://readersfavorite.com/book-review/letters-to-evelyn",
  googleDriveUrl: "https://drive.google.com/file/d/1YFhr75fWLzF2nu6nYDgVKB0fjEzZ36Pt/view?usp=drivesdk",
  quotes: [
    { text: "A profound and unforgettable literary piece... poetic prose and introspective storytelling create an immersive reading experience.", author: "Divine Zape, Readers' Favorite" },
    { text: "The author's imagination is off the charts. I did not think a novel combining science fiction, romance, and biblical characters could be achieved.", author: "Lesley Jones, Readers' Favorite" },
    { text: "Such a unique and wonderfully woven story that had me riveted from the moment I started reading it.", author: "Rabia Tanveer, Readers' Favorite" }
  ]
};

// Auth Context
const AuthContext = createContext(null);

const useAuth = () => useContext(AuthContext);

const AuthProvider = ({ children }) => {
  const [user, setUser] = useState(null);
  const [token, setToken] = useState(localStorage.getItem("token"));
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    if (token) {
      axios.defaults.headers.common["Authorization"] = `Bearer ${token}`;
      fetchUser();
    } else {
      setLoading(false);
    }
  }, [token]);

  const fetchUser = async () => {
    try {
      const res = await axios.get(`${API}/auth/me`);
      setUser(res.data);
    } catch (e) {
      localStorage.removeItem("token");
      setToken(null);
    } finally {
      setLoading(false);
    }
  };

  const login = async (email, password) => {
    const res = await axios.post(`${API}/auth/login`, { email, password });
    localStorage.setItem("token", res.data.access_token);
    setToken(res.data.access_token);
    setUser(res.data.user);
    axios.defaults.headers.common["Authorization"] = `Bearer ${res.data.access_token}`;
    return res.data;
  };

  const register = async (username, email, password) => {
    const res = await axios.post(`${API}/auth/register`, { username, email, password });
    localStorage.setItem("token", res.data.access_token);
    setToken(res.data.access_token);
    setUser(res.data.user);
    axios.defaults.headers.common["Authorization"] = `Bearer ${res.data.access_token}`;
    return res.data;
  };

  const googleLogin = async (credential) => {
    const res = await axios.post(`${API}/auth/google`, { credential });
    localStorage.setItem("token", res.data.access_token);
    setToken(res.data.access_token);
    setUser(res.data.user);
    axios.defaults.headers.common["Authorization"] = `Bearer ${res.data.access_token}`;
    return res.data;
  };

  const logout = () => {
    localStorage.removeItem("token");
    setToken(null);
    setUser(null);
    delete axios.defaults.headers.common["Authorization"];
  };

  const refreshUser = async () => {
    await fetchUser();
  };

  return (
    <AuthContext.Provider value={{ user, token, login, register, googleLogin, logout, loading, refreshUser }}>
      {children}
    </AuthContext.Provider>
  );
};

// Protected Route
const ProtectedRoute = ({ children }) => {
  const { user, loading } = useAuth();
  if (loading) return <LoadingScreen />;
  if (!user) return <Navigate to="/login" />;
  return children;
};

// Loading Screen - F-35B Style
const LoadingScreen = () => (
  <div className="min-h-screen bg-cockpit flex items-center justify-center">
    <div className="text-center">
      <div className="relative w-24 h-24 mx-auto mb-6">
        <div className="absolute inset-0 border-4 border-hud-cyan/30 rounded-full animate-ping"></div>
        <div className="absolute inset-2 border-2 border-hud-green rounded-full animate-spin"></div>
        <Radar className="absolute inset-0 m-auto w-12 h-12 text-hud-cyan animate-pulse" />
      </div>
      <p className="text-hud-green font-mono text-lg tracking-wider">INITIALIZING SYSTEMS...</p>
      <p className="text-hud-cyan/60 font-mono text-sm mt-2">InfoPilot v2.0 Tactical Interface</p>
    </div>
  </div>
);

// HUD Frame Component
const HUDFrame = ({ children, title, className = "" }) => (
  <div className={`relative ${className}`}>
    <div className="absolute top-0 left-0 w-4 h-4 border-t-2 border-l-2 border-hud-cyan"></div>
    <div className="absolute top-0 right-0 w-4 h-4 border-t-2 border-r-2 border-hud-cyan"></div>
    <div className="absolute bottom-0 left-0 w-4 h-4 border-b-2 border-l-2 border-hud-cyan"></div>
    <div className="absolute bottom-0 right-0 w-4 h-4 border-b-2 border-r-2 border-hud-cyan"></div>
    {title && (
      <div className="absolute -top-3 left-6 bg-cockpit px-2">
        <span className="text-hud-cyan text-xs font-mono tracking-wider">{title}</span>
      </div>
    )}
    <div className="p-4">{children}</div>
  </div>
);

// Sidebar Navigation - F-35B Cockpit Style
const Sidebar = ({ isOpen, setIsOpen }) => {
  const { user, logout } = useAuth();
  const navigate = useNavigate();
  const location = useLocation();

  const menuItems = [
    { path: "/", icon: Home, label: "COMMAND CENTER" },
    { path: "/infopilot", icon: Radar, label: "INFOPILOT SEARCH" },
    { path: "/ultimate-search", icon: Target, label: "ULTIMATE SEARCH" },
    { path: "/categories", icon: FolderTree, label: "CATEGORIES" },
    { path: "/statistics", icon: BarChart3, label: "INTEL STATS" },
    { path: "/global-database", icon: Globe, label: "GLOBAL DATABASE" },
    { path: "/book", icon: Book, label: "LETTERS TO EVELYN" },
    { path: "/subscribe", icon: ShoppingCart, label: "UPGRADE" },
  ];

  if (user?.is_admin) {
    menuItems.push({ path: "/admin", icon: Shield, label: "ADMIN CONTROL" });
  }

  return (
    <>
      {isOpen && (
        <div
          className="fixed inset-0 bg-black/70 z-40 lg:hidden"
          onClick={() => setIsOpen(false)}
        />
      )}

      <aside
        className={`fixed top-0 left-0 h-full bg-cockpit-dark border-r border-hud-cyan/30 z-50 transition-transform duration-300 w-72
          ${isOpen ? "translate-x-0" : "-translate-x-full lg:translate-x-0"}`}
      >
        <div className="p-6 border-b border-hud-cyan/30">
          <div className="flex items-center justify-between">
            <div className="flex items-center gap-3">
              <div className="w-12 h-12 bg-cockpit border-2 border-hud-cyan rounded-lg flex items-center justify-center relative">
                <Plane className="w-7 h-7 text-hud-cyan" />
                <div className="absolute -top-1 -right-1 w-3 h-3 bg-hud-green rounded-full animate-pulse"></div>
              </div>
              <div>
                <h1 className="text-xl font-bold text-hud-green font-mono tracking-wider">INFOPILOT</h1>
                <p className="text-xs text-hud-cyan/60 font-mono">TACTICAL SEARCH v2.0</p>
              </div>
            </div>
            <button className="lg:hidden text-hud-cyan" onClick={() => setIsOpen(false)}>
              <X className="w-6 h-6" />
            </button>
          </div>
        </div>

        <nav className="p-4 space-y-1">
          {menuItems.map((item) => (
            <button
              key={item.path}
              onClick={() => {
                navigate(item.path);
                setIsOpen(false);
              }}
              className={`w-full flex items-center gap-3 px-4 py-3 rounded transition-all font-mono text-sm
                ${location.pathname === item.path
                  ? "bg-hud-cyan/20 text-hud-cyan border border-hud-cyan/50"
                  : "text-hud-green/70 hover:bg-hud-green/10 hover:text-hud-green border border-transparent"
                }`}
            >
              <item.icon className="w-5 h-5" />
              <span className="tracking-wider">{item.label}</span>
            </button>
          ))}
        </nav>

        <div className="absolute bottom-0 left-0 right-0 p-4 border-t border-hud-cyan/30 bg-cockpit-dark">
          <div className="flex items-center gap-3 mb-4">
            <div className="w-10 h-10 bg-cockpit border border-hud-green rounded-full flex items-center justify-center text-hud-green font-bold font-mono">
              {user?.username?.[0]?.toUpperCase() || "P"}
            </div>
            <div className="flex-1 min-w-0">
              <p className="font-mono text-hud-green text-sm truncate">{user?.username}</p>
              <p className="text-xs text-hud-cyan/60 truncate font-mono">{user?.email}</p>
              {user?.is_paid ? (
                <span className="inline-block px-2 py-0.5 bg-hud-green/20 text-hud-green text-xs rounded font-mono mt-1">
                  LIFETIME ACCESS
                </span>
              ) : (
                <span className="inline-block px-2 py-0.5 bg-hud-orange/20 text-hud-orange text-xs rounded font-mono mt-1">
                  FREE TIER
                </span>
              )}
            </div>
          </div>
          <button
            onClick={logout}
            className="w-full flex items-center justify-center gap-2 px-4 py-2 text-hud-red hover:bg-hud-red/10 rounded transition-colors font-mono text-sm border border-hud-red/30"
          >
            <LogOut className="w-4 h-4" />
            <span>DISCONNECT</span>
          </button>
        </div>
      </aside>
    </>
  );
};

// Layout Component
const Layout = ({ children }) => {
  const [sidebarOpen, setSidebarOpen] = useState(false);

  return (
    <div className="min-h-screen bg-cockpit">
      <Sidebar isOpen={sidebarOpen} setIsOpen={setSidebarOpen} />

      <header className="lg:hidden fixed top-0 left-0 right-0 h-16 bg-cockpit-dark border-b border-hud-cyan/30 z-30 flex items-center px-4">
        <button onClick={() => setSidebarOpen(true)} className="p-2 text-hud-cyan">
          <Menu className="w-6 h-6" />
        </button>
        <div className="flex items-center gap-2 ml-4">
          <Plane className="w-6 h-6 text-hud-cyan" />
          <span className="font-bold text-lg text-hud-green font-mono">INFOPILOT</span>
        </div>
      </header>

      <main className="lg:ml-72 pt-16 lg:pt-0 min-h-screen">
        <div className="p-4 lg:p-8">{children}</div>
      </main>
    </div>
  );
};

// Login Page - F-35B Style
const LoginPage = () => {
  const [isLogin, setIsLogin] = useState(true);
  const [email, setEmail] = useState("");
  const [password, setPassword] = useState("");
  const [username, setUsername] = useState("");
  const [loading, setLoading] = useState(false);
  const { login, register, googleLogin, user } = useAuth();
  const navigate = useNavigate();

  useEffect(() => {
    if (user) navigate("/");
  }, [user, navigate]);

  const handleSubmit = async (e) => {
    e.preventDefault();
    setLoading(true);
    try {
      if (isLogin) {
        await login(email, password);
      } else {
        await register(username, email, password);
      }
      toast.success(isLogin ? "PILOT AUTHENTICATED" : "PILOT REGISTERED");
      navigate("/");
    } catch (error) {
      toast.error(error.response?.data?.detail || "AUTHENTICATION FAILED");
    } finally {
      setLoading(false);
    }
  };

  const handleGoogleLogin = async (credentialResponse) => {
    setLoading(true);
    try {
      const response = await googleLogin(credentialResponse.credential);
      toast.success("GOOGLE AUTH SUCCESSFUL");
      navigate("/");
    } catch (error) {
      toast.error(error.response?.data?.detail || "Google authentication failed");
    } finally {
      setLoading(false);
    }
  };

  const handleGoogleError = () => {
    toast.error("Google Sign-In failed. Please try again.");
  };

  return (
    <div className="min-h-screen bg-cockpit flex items-center justify-center p-4 relative overflow-hidden">
      {/* HUD Background Elements */}
      <div className="absolute inset-0 opacity-20">
        <div className="absolute top-20 left-20 w-64 h-64 border border-hud-cyan/30 rounded-full"></div>
        <div className="absolute bottom-20 right-20 w-96 h-96 border border-hud-green/20 rounded-full"></div>
        <div className="absolute top-1/2 left-1/4 w-32 h-32 border border-hud-cyan/20 rotate-45"></div>
      </div>

      <div className="w-full max-w-md relative z-10">
        <div className="text-center mb-8">
          <div className="inline-flex items-center justify-center w-20 h-20 bg-cockpit-dark border-2 border-hud-cyan rounded-xl mb-4 relative">
            <Plane className="w-12 h-12 text-hud-cyan" />
            <div className="absolute -top-2 -right-2 w-4 h-4 bg-hud-green rounded-full animate-pulse"></div>
          </div>
          <h1 className="text-4xl font-bold text-hud-green font-mono tracking-wider">INFOPILOT</h1>
          <p className="text-hud-cyan/80 mt-2 font-mono text-sm">TACTICAL INFORMATION EXCHANGE SYSTEM</p>
        </div>

        <HUDFrame title="AUTHENTICATION" className="bg-cockpit-dark/90 backdrop-blur border border-hud-cyan/30 rounded-lg">
          <div className="flex mb-6">
            <button
              onClick={() => setIsLogin(true)}
              className={`flex-1 py-3 text-center font-mono text-sm tracking-wider transition-colors rounded-l
                ${isLogin ? "bg-hud-cyan/20 text-hud-cyan border border-hud-cyan" : "bg-cockpit text-hud-green/50 border border-hud-green/20"}`}
            >
              LOGIN
            </button>
            <button
              onClick={() => setIsLogin(false)}
              className={`flex-1 py-3 text-center font-mono text-sm tracking-wider transition-colors rounded-r
                ${!isLogin ? "bg-hud-cyan/20 text-hud-cyan border border-hud-cyan" : "bg-cockpit text-hud-green/50 border border-hud-green/20"}`}
            >
              REGISTER
            </button>
          </div>

          <form onSubmit={handleSubmit} className="space-y-4">
            {!isLogin && (
              <div>
                <label className="block text-xs font-mono text-hud-cyan mb-1 tracking-wider">CALLSIGN</label>
                <input
                  type="text"
                  value={username}
                  onChange={(e) => setUsername(e.target.value)}
                  className="w-full px-4 py-3 bg-cockpit border border-hud-green/30 rounded text-hud-green font-mono focus:border-hud-cyan focus:outline-none"
                  required={!isLogin}
                  data-testid="username-input"
                />
              </div>
            )}
            <div>
              <label className="block text-xs font-mono text-hud-cyan mb-1 tracking-wider">EMAIL IDENTIFIER</label>
              <input
                type="email"
                value={email}
                onChange={(e) => setEmail(e.target.value)}
                className="w-full px-4 py-3 bg-cockpit border border-hud-green/30 rounded text-hud-green font-mono focus:border-hud-cyan focus:outline-none"
                required
                data-testid="email-input"
              />
            </div>
            <div>
              <label className="block text-xs font-mono text-hud-cyan mb-1 tracking-wider">ACCESS CODE</label>
              <input
                type="password"
                value={password}
                onChange={(e) => setPassword(e.target.value)}
                className="w-full px-4 py-3 bg-cockpit border border-hud-green/30 rounded text-hud-green font-mono focus:border-hud-cyan focus:outline-none"
                required
                data-testid="password-input"
              />
            </div>
            <button
              type="submit"
              disabled={loading}
              className="w-full py-3 bg-hud-cyan/20 border border-hud-cyan text-hud-cyan font-mono tracking-wider rounded hover:bg-hud-cyan/30 transition-all disabled:opacity-50"
              data-testid="submit-btn"
            >
              {loading ? <Loader2 className="w-5 h-5 animate-spin mx-auto" /> : isLogin ? "AUTHENTICATE" : "INITIATE REGISTRATION"}
            </button>
          </form>

          <div className="mt-6">
            <div className="relative">
              <div className="absolute inset-0 flex items-center">
                <div className="w-full border-t border-hud-cyan/20"></div>
              </div>
              <div className="relative flex justify-center text-xs">
                <span className="px-2 bg-cockpit-dark text-hud-cyan/60 font-mono">OR</span>
              </div>
            </div>
            <button
              onClick={handleGoogleLogin}
              disabled={loading}
              className="w-full mt-4 py-3 bg-cockpit border border-hud-green/30 text-hud-green font-mono tracking-wider rounded hover:bg-hud-green/10 transition-all flex items-center justify-center gap-2"
            >
              <svg className="w-5 h-5" viewBox="0 0 24 24">
                <path fill="currentColor" d="M22.56 12.25c0-.78-.07-1.53-.2-2.25H12v4.26h5.92c-.26 1.37-1.04 2.53-2.21 3.31v2.77h3.57c2.08-1.92 3.28-4.74 3.28-8.09z"/>
                <path fill="currentColor" d="M12 23c2.97 0 5.46-.98 7.28-2.66l-3.57-2.77c-.98.66-2.23 1.06-3.71 1.06-2.86 0-5.29-1.93-6.16-4.53H2.18v2.84C3.99 20.53 7.7 23 12 23z"/>
                <path fill="currentColor" d="M5.84 14.09c-.22-.66-.35-1.36-.35-2.09s.13-1.43.35-2.09V7.07H2.18C1.43 8.55 1 10.22 1 12s.43 3.45 1.18 4.93l2.85-2.22.81-.62z"/>
                <path fill="currentColor" d="M12 5.38c1.62 0 3.06.56 4.21 1.64l3.15-3.15C17.45 2.09 14.97 1 12 1 7.7 1 3.99 3.47 2.18 7.07l3.66 2.84c.87-2.6 3.3-4.53 6.16-4.53z"/>
              </svg>
              GOOGLE AUTH (DEMO)
            </button>
          </div>

          <div className="mt-6 text-center">
            <p className="text-hud-green text-sm font-mono">
              LIFETIME ACCESS: <span className="text-hud-cyan font-bold">$0.95</span>
            </p>
          </div>
        </HUDFrame>
      </div>
    </div>
  );
};

// Book Promo Banner
const BookPromoBanner = ({ compact = false }) => (
  <div className={`bg-cockpit-dark border border-hud-orange/30 rounded-lg overflow-hidden ${compact ? 'p-4' : 'p-6'}`}>
    <div className="flex flex-col md:flex-row gap-4 items-center">
      <img 
        src={BOOK_IMAGES.author} 
        alt="John Selman - Author"
        className={`${compact ? 'w-16 h-16' : 'w-24 h-24'} rounded-lg border-2 border-hud-orange object-cover`}
      />
      <div className="flex-1 text-center md:text-left">
        <h3 className="text-hud-orange font-mono text-lg font-bold tracking-wider">
          LETTERS TO EVELYN
        </h3>
        <p className="text-hud-cyan/80 text-sm font-mono mt-1">
          By World Record Aviation Holder John Selman
        </p>
        <div className="flex items-center justify-center md:justify-start gap-1 mt-2">
          {[...Array(5)].map((_, i) => (
            <Star key={i} className="w-4 h-4 fill-hud-orange text-hud-orange" />
          ))}
          <span className="text-hud-green text-xs ml-2 font-mono">15 Five-Star Reviews</span>
        </div>
        {!compact && (
          <p className="text-hud-green/70 text-xs mt-2 font-mono italic">
            "A profound and unforgettable literary piece... poetic prose and introspective storytelling"
          </p>
        )}
      </div>
      <a
        href={BOOK_INFO.amazonUrl}
        target="_blank"
        rel="noopener noreferrer"
        className="px-6 py-3 bg-hud-orange/20 border border-hud-orange text-hud-orange font-mono text-sm tracking-wider rounded hover:bg-hud-orange/30 transition-all flex items-center gap-2"
      >
        <ShoppingCart className="w-4 h-4" />
        GET NOW
      </a>
    </div>
  </div>
);

// Home Page - Command Center
const HomePage = () => {
  const { user } = useAuth();
  const navigate = useNavigate();

  return (
    <Layout>
      <div className="max-w-5xl mx-auto">
        {/* Welcome Banner */}
        <HUDFrame title="COMMAND CENTER" className="bg-cockpit-dark/80 border border-hud-cyan/30 rounded-lg mb-8">
          <div className="flex flex-col md:flex-row items-center gap-6">
            <img 
              src={BOOK_IMAGES.globe}
              alt="InfoPilot Global Network"
              className="w-32 h-32 rounded-lg border border-hud-cyan/50 object-cover"
            />
            <div className="flex-1">
              <h1 className="text-3xl font-bold text-hud-green font-mono tracking-wider mb-2">
                WELCOME, {user?.username?.toUpperCase()}
              </h1>
              <p className="text-hud-cyan/80 mb-4 font-mono text-sm">
                Your tactical gateway to the World Wide Web Information Exchange.
                Create categories, write protocols, and collate intelligence from across the internet.
              </p>
              <div className="flex flex-wrap gap-3">
                <button
                  onClick={() => navigate("/infopilot")}
                  className="px-6 py-3 bg-hud-cyan/20 border border-hud-cyan text-hud-cyan font-mono tracking-wider rounded hover:bg-hud-cyan/30 transition-all flex items-center gap-2"
                  data-testid="start-searching-btn"
                >
                  <Radar className="w-5 h-5" />
                  BEGIN SEARCH
                </button>
                <button
                  onClick={() => navigate("/subscribe")}
                  className="px-6 py-3 bg-hud-green/20 border border-hud-green text-hud-green font-mono tracking-wider rounded hover:bg-hud-green/30 transition-all flex items-center gap-2"
                >
                  <Zap className="w-5 h-5" />
                  UPGRADE $0.95
                </button>
              </div>
            </div>
          </div>
        </HUDFrame>

        {/* Book Promo */}
        <div className="mb-8">
          <BookPromoBanner />
        </div>

        {/* Quick Actions */}
        <div className="grid md:grid-cols-3 gap-4 mb-8">
          <QuickActionCard 
            title="CREATE CATEGORIES" 
            icon={FolderTree} 
            onClick={() => navigate("/categories")}
            color="cyan"
          />
          <QuickActionCard 
            title="SEARCH & COLLATE" 
            icon={Radar} 
            onClick={() => navigate("/infopilot")}
            color="green"
          />
          <QuickActionCard 
            title="VIEW INTEL" 
            icon={BarChart3} 
            onClick={() => navigate("/statistics")}
            color="orange"
          />
        </div>

        {/* InfoPilot 2.0 Guide */}
        <HUDFrame title="INFOPILOT 2.0 PROTOCOL MANUAL" className="bg-cockpit-dark/80 border border-hud-cyan/30 rounded-lg">
          <div className="space-y-6">
            <p className="text-hud-green/80 font-mono text-sm">
              InfoPilot 2.0 is a powerful Boolean search protocol that lets you precisely define what intelligence you're seeking.
            </p>

            <div>
              <h3 className="text-hud-cyan font-mono text-sm tracking-wider mb-3">SYNTAX COMMANDS:</h3>
              <div className="grid md:grid-cols-2 gap-3">
                <div className="bg-cockpit p-3 rounded border border-hud-green/20">
                  <code className="text-hud-green text-sm">(word1 or word2)</code>
                  <p className="text-hud-cyan/60 text-xs mt-1">Match ANY word in group</p>
                </div>
                <div className="bg-cockpit p-3 rounded border border-hud-green/20">
                  <code className="text-hud-green text-sm">&</code>
                  <p className="text-hud-cyan/60 text-xs mt-1">AND operator between groups</p>
                </div>
                <div className="bg-cockpit p-3 rounded border border-hud-green/20">
                  <code className="text-hud-green text-sm">+</code>
                  <p className="text-hud-cyan/60 text-xs mt-1">INCLUDE ALL (must be present)</p>
                </div>
                <div className="bg-cockpit p-3 rounded border border-hud-green/20">
                  <code className="text-hud-red text-sm">^</code>
                  <p className="text-hud-cyan/60 text-xs mt-1">EXCLUDE ALL (none should be present)</p>
                </div>
              </div>
            </div>

            <div>
              <h3 className="text-hud-cyan font-mono text-sm tracking-wider mb-3">EXAMPLE PROTOCOLS:</h3>
              <div className="bg-cockpit p-4 rounded border border-hud-cyan/20 font-mono text-sm">
                <p className="text-hud-orange mb-2">// American Civil War Category</p>
                <p className="text-hud-green">(American civil war or civil war) & (1860 or 1861 or 1862 or 1863)+</p>
                <p className="text-hud-orange mt-4 mb-2">// Heroes Subcategory</p>
                <p className="text-hud-green">(hero or heroes or heroic) & (civil war)+ & (villain)^</p>
              </div>
            </div>
          </div>
        </HUDFrame>
      </div>
    </Layout>
  );
};

const QuickActionCard = ({ title, icon: Icon, onClick, color = "cyan" }) => {
  const colorClasses = {
    cyan: "border-hud-cyan/30 hover:border-hud-cyan text-hud-cyan",
    green: "border-hud-green/30 hover:border-hud-green text-hud-green",
    orange: "border-hud-orange/30 hover:border-hud-orange text-hud-orange"
  };

  return (
    <button
      onClick={onClick}
      className={`bg-cockpit-dark p-6 rounded-lg border ${colorClasses[color]} transition-all hover:bg-opacity-80 text-left group`}
    >
      <div className={`w-12 h-12 rounded-lg border ${colorClasses[color]} flex items-center justify-center mb-4 group-hover:scale-110 transition-transform`}>
        <Icon className="w-6 h-6" />
      </div>
      <h3 className="font-mono text-sm tracking-wider">{title}</h3>
    </button>
  );
};

// InfoPilot Search Page
const InfoPilotPage = () => {
  const [searchQuery, setSearchQuery] = useState("");
  const [loading, setLoading] = useState(false);
  const [results, setResults] = useState(null);
  const [categories, setCategories] = useState([]);

  useEffect(() => {
    fetchCategories();
  }, []);

  const fetchCategories = async () => {
    try {
      const res = await axios.get(`${API}/categories`);
      setCategories(res.data);
    } catch (error) {
      console.error("Failed to fetch categories");
    }
  };

  const handleCollate = async () => {
    if (!searchQuery.trim()) {
      toast.error("ENTER SEARCH PARAMETERS");
      return;
    }

    if (categories.length === 0) {
      toast.error("CREATE CATEGORY PROTOCOLS FIRST");
      return;
    }

    setLoading(true);
    try {
      const res = await axios.post(`${API}/search/collate`, {
        search_query: searchQuery,
        max_results: 20
      });
      setResults(res.data);
      toast.success(`COLLATED ${res.data.categorized_count} TARGETS`);
    } catch (error) {
      toast.error(error.response?.data?.detail || "SEARCH FAILED");
    } finally {
      setLoading(false);
    }
  };

  return (
    <Layout>
      <div className="max-w-4xl mx-auto">
        <div className="mb-8">
          <h1 className="text-3xl font-bold text-hud-green font-mono tracking-wider mb-2">INFOPILOT SEARCH</h1>
          <p className="text-hud-cyan/80 font-mono text-sm">Search the web and automatically categorize results using your protocols.</p>
        </div>

        {/* Search Modifiers Reference */}
        <HUDFrame title="SEARCH MODIFIERS" className="bg-cockpit-dark/80 border border-hud-green/30 rounded-lg mb-6">
          <div className="grid md:grid-cols-2 gap-2 text-sm font-mono">
            <div><code className="text-hud-cyan">site:example.com</code> <span className="text-hud-green/60">- Search within a site</span></div>
            <div><code className="text-hud-cyan">"exact phrase"</code> <span className="text-hud-green/60">- Exact match</span></div>
            <div><code className="text-hud-cyan">-word</code> <span className="text-hud-green/60">- Exclude word</span></div>
            <div><code className="text-hud-cyan">filetype:pdf</code> <span className="text-hud-green/60">- Specific file type</span></div>
          </div>
        </HUDFrame>

        {/* Search Box */}
        <HUDFrame title="SEARCH PARAMETERS" className="bg-cockpit-dark/80 border border-hud-cyan/30 rounded-lg mb-6">
          <div className="flex gap-4">
            <input
              type="text"
              value={searchQuery}
              onChange={(e) => setSearchQuery(e.target.value)}
              placeholder="Enter search query..."
              className="flex-1 px-4 py-3 bg-cockpit border border-hud-green/30 rounded text-hud-green font-mono focus:border-hud-cyan focus:outline-none"
              onKeyPress={(e) => e.key === "Enter" && handleCollate()}
              data-testid="search-input"
            />
            <button
              onClick={handleCollate}
              disabled={loading}
              className="px-6 py-3 bg-hud-cyan/20 border border-hud-cyan text-hud-cyan font-mono tracking-wider rounded hover:bg-hud-cyan/30 transition-all disabled:opacity-50 flex items-center gap-2"
              data-testid="collate-btn"
            >
              {loading ? <Loader2 className="w-5 h-5 animate-spin" /> : <Radar className="w-5 h-5" />}
              COLLATE
            </button>
          </div>

          {categories.length > 0 && (
            <div className="mt-4">
              <p className="text-xs text-hud-cyan/60 mb-2 font-mono">ACTIVE PROTOCOLS ({categories.length}):</p>
              <div className="flex flex-wrap gap-2">
                {categories.slice(0, 5).map((cat) => (
                  <span key={cat.id} className="px-3 py-1 bg-hud-green/10 border border-hud-green/30 text-hud-green rounded text-xs font-mono">
                    {cat.name}
                  </span>
                ))}
                {categories.length > 5 && (
                  <span className="px-3 py-1 bg-cockpit text-hud-cyan/60 rounded text-xs font-mono">
                    +{categories.length - 5} more
                  </span>
                )}
              </div>
            </div>
          )}
        </HUDFrame>

        {/* Book Promo */}
        <div className="mb-6">
          <BookPromoBanner compact />
        </div>

        {/* Results */}
        {results && (
          <HUDFrame title="COLLATED RESULTS" className="bg-cockpit-dark/80 border border-hud-cyan/30 rounded-lg">
            <p className="text-hud-cyan font-mono text-sm mb-4">
              {results.categorized_count} of {results.total_searched} targets categorized
            </p>
            {results.results.length > 0 ? (
              <div className="space-y-4">
                {results.results.map((result) => (
                  <SearchResultCard key={result.id} result={result} />
                ))}
              </div>
            ) : (
              <p className="text-hud-orange text-center py-8 font-mono">NO MATCHES FOUND</p>
            )}
          </HUDFrame>
        )}
      </div>
    </Layout>
  );
};

// Search Result Card - Tactical Style
const SearchResultCard = ({ result, showReactions = true }) => {
  const [reacting, setReacting] = useState(false);

  const handleReaction = async (type) => {
    setReacting(true);
    try {
      await axios.post(`${API}/results/${result.id}/react`, { reaction_type: type });
      toast.success("REACTION LOGGED");
    } catch (error) {
      toast.error("REACTION FAILED");
    } finally {
      setReacting(false);
    }
  };

  const reactions = [
    { type: "like", icon: ThumbsUp },
    { type: "love", icon: Heart },
    { type: "best", icon: Award },
    { type: "caution", icon: AlertTriangle },
  ];

  return (
    <div className="bg-cockpit p-4 rounded border border-hud-green/20 hover:border-hud-cyan/50 transition-colors">
      <a
        href={result.url}
        target="_blank"
        rel="noopener noreferrer"
        className="text-hud-cyan hover:underline font-mono text-sm block truncate"
      >
        {result.title}
      </a>
      <p className="text-hud-green/60 text-xs mt-1 line-clamp-2 font-mono">{result.snippet}</p>
      <div className="flex flex-wrap gap-2 mt-2">
        <span className="px-2 py-0.5 bg-hud-orange/20 text-hud-orange text-xs rounded font-mono">
          {result.article_type}
        </span>
        <span className="px-2 py-0.5 bg-cockpit-dark text-hud-cyan/60 text-xs rounded font-mono">
          {result.domain}
        </span>
      </div>

      {showReactions && (
        <div className="flex gap-2 mt-3 pt-3 border-t border-hud-green/10">
          {reactions.map(({ type, icon: Icon }) => (
            <button
              key={type}
              onClick={() => handleReaction(type)}
              disabled={reacting}
              className="flex items-center gap-1 px-2 py-1 text-xs text-hud-green/60 hover:text-hud-cyan rounded transition-colors font-mono"
            >
              <Icon className="w-3 h-3" />
              {result.reactions?.[type] > 0 && <span>{result.reactions[type]}</span>}
            </button>
          ))}
        </div>
      )}
    </div>
  );
};

// Categories Page
const CategoriesPage = () => {
  const [categories, setCategories] = useState([]);
  const [loading, setLoading] = useState(true);
  const [showCreate, setShowCreate] = useState(false);
  const [newCategory, setNewCategory] = useState({ name: "", protocol: "", parentId: null, isPublic: true });
  const [creating, setCreating] = useState(false);
  const { user } = useAuth();

  useEffect(() => {
    fetchCategories();
  }, []);

  const fetchCategories = async () => {
    try {
      const res = await axios.get(`${API}/categories`);
      setCategories(res.data.filter(c => c.user_id === user?.id));
    } catch (error) {
      toast.error("FAILED TO LOAD CATEGORIES");
    } finally {
      setLoading(false);
    }
  };

  const handleCreate = async (e) => {
    e.preventDefault();
    setCreating(true);
    try {
      await axios.post(`${API}/categories`, {
        name: newCategory.name,
        protocol: { protocol_string: newCategory.protocol },
        parent_id: newCategory.parentId || null,
        is_public: newCategory.isPublic
      });
      toast.success("CATEGORY CREATED");
      setShowCreate(false);
      setNewCategory({ name: "", protocol: "", parentId: null, isPublic: true });
      fetchCategories();
    } catch (error) {
      toast.error(error.response?.data?.detail || "CREATION FAILED");
    } finally {
      setCreating(false);
    }
  };

  const handleDelete = async (id) => {
    if (!window.confirm("DELETE THIS CATEGORY?")) return;
    try {
      await axios.delete(`${API}/categories/${id}`);
      toast.success("CATEGORY DELETED");
      fetchCategories();
    } catch (error) {
      toast.error("DELETE FAILED");
    }
  };

  return (
    <Layout>
      <div className="max-w-4xl mx-auto">
        <div className="flex items-center justify-between mb-8">
          <div>
            <h1 className="text-3xl font-bold text-hud-green font-mono tracking-wider mb-2">CATEGORIES</h1>
            <p className="text-hud-cyan/80 font-mono text-sm">Manage your InfoPilot 2.0 protocols.</p>
          </div>
          <button
            onClick={() => setShowCreate(true)}
            className="px-4 py-2 bg-hud-cyan/20 border border-hud-cyan text-hud-cyan font-mono tracking-wider rounded hover:bg-hud-cyan/30 transition-colors flex items-center gap-2"
            data-testid="create-category-btn"
          >
            <Plus className="w-5 h-5" />
            NEW CATEGORY
          </button>
        </div>

        {/* Create Modal */}
        {showCreate && (
          <div className="fixed inset-0 bg-black/80 flex items-center justify-center z-50 p-4">
            <HUDFrame title="CREATE CATEGORY" className="bg-cockpit-dark border border-hud-cyan/30 rounded-lg max-w-lg w-full">
              <form onSubmit={handleCreate} className="space-y-4">
                <div>
                  <label className="block text-xs font-mono text-hud-cyan mb-1">CATEGORY NAME</label>
                  <input
                    type="text"
                    value={newCategory.name}
                    onChange={(e) => setNewCategory({ ...newCategory, name: e.target.value })}
                    className="w-full px-4 py-2 bg-cockpit border border-hud-green/30 rounded text-hud-green font-mono focus:border-hud-cyan"
                    required
                    data-testid="category-name-input"
                  />
                </div>
                <div>
                  <label className="block text-xs font-mono text-hud-cyan mb-1">INFOPILOT 2.0 PROTOCOL</label>
                  <textarea
                    value={newCategory.protocol}
                    onChange={(e) => setNewCategory({ ...newCategory, protocol: e.target.value })}
                    placeholder="(word1 or word2) & (word3)+ & (excluded)^"
                    className="w-full px-4 py-2 bg-cockpit border border-hud-green/30 rounded text-hud-green font-mono h-24 focus:border-hud-cyan"
                    required
                    data-testid="protocol-input"
                  />
                </div>
                <div className="flex gap-4">
                  <button
                    type="button"
                    onClick={() => setShowCreate(false)}
                    className="flex-1 px-4 py-2 border border-hud-green/30 text-hud-green font-mono rounded hover:bg-hud-green/10"
                  >
                    CANCEL
                  </button>
                  <button
                    type="submit"
                    disabled={creating}
                    className="flex-1 px-4 py-2 bg-hud-cyan/20 border border-hud-cyan text-hud-cyan font-mono rounded hover:bg-hud-cyan/30 disabled:opacity-50"
                    data-testid="save-category-btn"
                  >
                    {creating ? <Loader2 className="w-5 h-5 animate-spin mx-auto" /> : "CREATE"}
                  </button>
                </div>
              </form>
            </HUDFrame>
          </div>
        )}

        {/* Categories List */}
        {loading ? (
          <div className="flex justify-center py-12">
            <Loader2 className="w-8 h-8 animate-spin text-hud-cyan" />
          </div>
        ) : categories.length === 0 ? (
          <HUDFrame title="NO CATEGORIES" className="bg-cockpit-dark/80 border border-hud-cyan/30 rounded-lg text-center py-12">
            <FolderTree className="w-16 h-16 text-hud-cyan/30 mx-auto mb-4" />
            <p className="text-hud-green font-mono mb-4">CREATE YOUR FIRST CATEGORY TO BEGIN</p>
            <button
              onClick={() => setShowCreate(true)}
              className="px-6 py-3 bg-hud-cyan/20 border border-hud-cyan text-hud-cyan font-mono rounded hover:bg-hud-cyan/30"
            >
              CREATE CATEGORY
            </button>
          </HUDFrame>
        ) : (
          <div className="space-y-3">
            {categories.map((cat) => (
              <div key={cat.id} className="bg-cockpit-dark p-4 rounded border border-hud-green/20 hover:border-hud-cyan/50 transition-colors">
                <div className="flex items-start justify-between">
                  <div className="flex-1">
                    <h3 className="text-hud-cyan font-mono font-bold">{cat.name}</h3>
                    <p className="text-hud-green/60 text-xs font-mono mt-1 truncate">{cat.protocol_string}</p>
                    <span className={`inline-block mt-2 px-2 py-0.5 text-xs rounded font-mono ${cat.is_public ? "bg-hud-green/20 text-hud-green" : "bg-hud-orange/20 text-hud-orange"}`}>
                      {cat.is_public ? "PUBLIC" : "PRIVATE"}
                    </span>
                  </div>
                  <button
                    onClick={() => handleDelete(cat.id)}
                    className="p-2 text-hud-red/60 hover:text-hud-red rounded"
                  >
                    <Trash2 className="w-4 h-4" />
                  </button>
                </div>
              </div>
            ))}
          </div>
        )}
      </div>
    </Layout>
  );
};

// Ultimate Search Page
const UltimateSearchPage = () => {
  const [categories, setCategories] = useState([]);
  const [selectedCategories, setSelectedCategories] = useState([]);
  const [aggregationType, setAggregationType] = useState("and_or");
  const [keyword, setKeyword] = useState("");
  const [results, setResults] = useState(null);
  const [loading, setLoading] = useState(false);
  const [page, setPage] = useState(1);
  const { user } = useAuth();

  useEffect(() => {
    fetchCategories();
  }, []);

  const fetchCategories = async () => {
    try {
      const res = await axios.get(`${API}/categories`);
      setCategories(res.data.filter(c => c.user_id === user?.id));
    } catch (error) {
      console.error("Failed to fetch categories");
    }
  };

  const handleSearch = async (newPage = 1) => {
    setLoading(true);
    try {
      const res = await axios.post(`${API}/ultimate-search`, {
        category_ids: selectedCategories,
        aggregation_type: aggregationType,
        keyword: keyword || null,
        page: newPage
      });
      setResults(res.data);
      setPage(newPage);
    } catch (error) {
      toast.error(error.response?.data?.detail || "SEARCH FAILED");
    } finally {
      setLoading(false);
    }
  };

  return (
    <Layout>
      <div className="max-w-6xl mx-auto">
        <div className="mb-8">
          <h1 className="text-3xl font-bold text-hud-green font-mono tracking-wider mb-2">ULTIMATE SEARCH</h1>
          <p className="text-hud-cyan/80 font-mono text-sm">Advanced filtering of collated intelligence.</p>
        </div>

        <div className="grid lg:grid-cols-4 gap-6">
          {/* Filters */}
          <div className="lg:col-span-1 space-y-4">
            <HUDFrame title="CATEGORIES" className="bg-cockpit-dark/80 border border-hud-cyan/30 rounded-lg">
              <div className="space-y-2 max-h-60 overflow-y-auto">
                {categories.map((cat) => (
                  <label key={cat.id} className="flex items-center gap-2 cursor-pointer">
                    <input
                      type="checkbox"
                      checked={selectedCategories.includes(cat.id)}
                      onChange={() => {
                        setSelectedCategories(prev =>
                          prev.includes(cat.id) ? prev.filter(c => c !== cat.id) : [...prev, cat.id]
                        );
                      }}
                      className="rounded bg-cockpit border-hud-green/30 text-hud-cyan"
                    />
                    <span className="text-sm text-hud-green font-mono">{cat.name}</span>
                  </label>
                ))}
              </div>
            </HUDFrame>

            <HUDFrame title="AGGREGATION" className="bg-cockpit-dark/80 border border-hud-green/30 rounded-lg">
              <div className="space-y-2">
                {[
                  { value: "and_or", label: "AND/OR" },
                  { value: "and", label: "AND" },
                  { value: "or", label: "OR" },
                ].map((opt) => (
                  <label key={opt.value} className="flex items-center gap-2 cursor-pointer">
                    <input
                      type="radio"
                      name="aggregation"
                      value={opt.value}
                      checked={aggregationType === opt.value}
                      onChange={(e) => setAggregationType(e.target.value)}
                      className="text-hud-cyan"
                    />
                    <span className="text-sm text-hud-green font-mono">{opt.label}</span>
                  </label>
                ))}
              </div>
            </HUDFrame>
          </div>

          {/* Results */}
          <div className="lg:col-span-3">
            <div className="flex gap-4 mb-6">
              <input
                type="text"
                value={keyword}
                onChange={(e) => setKeyword(e.target.value)}
                placeholder="Keyword filter..."
                className="flex-1 px-4 py-2 bg-cockpit border border-hud-green/30 rounded text-hud-green font-mono focus:border-hud-cyan"
                data-testid="ultimate-search-input"
              />
              <button
                onClick={() => handleSearch(1)}
                disabled={loading}
                className="px-6 py-2 bg-hud-cyan/20 border border-hud-cyan text-hud-cyan font-mono rounded hover:bg-hud-cyan/30 disabled:opacity-50 flex items-center gap-2"
                data-testid="ultimate-search-btn"
              >
                {loading ? <Loader2 className="w-5 h-5 animate-spin" /> : <Target className="w-5 h-5" />}
                SEARCH
              </button>
            </div>

            {results ? (
              <>
                <p className="text-hud-cyan font-mono text-sm mb-4">
                  {results.total} RESULTS | PAGE {results.page} OF {results.total_pages}
                </p>
                <div className="space-y-3">
                  {results.results.map((result) => (
                    <SearchResultCard key={result.id} result={result} />
                  ))}
                </div>
                {results.total_pages > 1 && (
                  <div className="flex justify-center gap-2 mt-6">
                    <button
                      onClick={() => handleSearch(page - 1)}
                      disabled={page === 1}
                      className="px-4 py-2 border border-hud-green/30 text-hud-green font-mono rounded disabled:opacity-50"
                    >
                      PREV
                    </button>
                    <button
                      onClick={() => handleSearch(page + 1)}
                      disabled={page === results.total_pages}
                      className="px-4 py-2 border border-hud-green/30 text-hud-green font-mono rounded disabled:opacity-50"
                    >
                      NEXT
                    </button>
                  </div>
                )}
              </>
            ) : (
              <HUDFrame title="AWAITING PARAMETERS" className="bg-cockpit-dark/80 border border-hud-cyan/30 rounded-lg text-center py-12">
                <Target className="w-16 h-16 text-hud-cyan/30 mx-auto mb-4" />
                <p className="text-hud-green font-mono">SELECT CATEGORIES AND EXECUTE SEARCH</p>
              </HUDFrame>
            )}
          </div>
        </div>
      </div>
    </Layout>
  );
};

// Statistics Page
const StatisticsPage = () => {
  const [stats, setStats] = useState(null);
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    fetchStats();
  }, []);

  const fetchStats = async () => {
    try {
      const res = await axios.get(`${API}/statistics`);
      setStats(res.data);
    } catch (error) {
      toast.error("FAILED TO LOAD INTEL");
    } finally {
      setLoading(false);
    }
  };

  const COLORS = ["#00ffff", "#00ff88", "#ff8800", "#ff0066", "#8844ff"];

  return (
    <Layout>
      <div className="max-w-6xl mx-auto">
        <div className="mb-8">
          <h1 className="text-3xl font-bold text-hud-green font-mono tracking-wider mb-2">INTEL STATISTICS</h1>
          <p className="text-hud-cyan/80 font-mono text-sm">Analysis of collated data.</p>
        </div>

        {loading ? (
          <div className="flex justify-center py-12">
            <Loader2 className="w-8 h-8 animate-spin text-hud-cyan" />
          </div>
        ) : stats ? (
          <div className="grid md:grid-cols-2 gap-6">
            <div className="md:col-span-2 grid grid-cols-2 md:grid-cols-4 gap-4">
              <StatCard label="TOTAL RESULTS" value={stats.total_results} />
              <StatCard label="CATEGORIES" value={stats.total_categories} />
              <StatCard label="DOMAINS" value={stats.top_domains?.length || 0} />
              <StatCard label="ARTICLE TYPES" value={stats.article_types?.length || 0} />
            </div>

            {stats.article_types?.length > 0 && (
              <HUDFrame title="ARTICLE TYPES" className="bg-cockpit-dark/80 border border-hud-cyan/30 rounded-lg">
                <ResponsiveContainer width="100%" height={300}>
                  <PieChart>
                    <Pie
                      data={stats.article_types.map((t) => ({ name: t._id, value: t.count }))}
                      dataKey="value"
                      nameKey="name"
                      cx="50%"
                      cy="50%"
                      outerRadius={80}
                      label
                    >
                      {stats.article_types.map((_, index) => (
                        <Cell key={`cell-${index}`} fill={COLORS[index % COLORS.length]} />
                      ))}
                    </Pie>
                    <Tooltip contentStyle={{ backgroundColor: '#0a0a0a', border: '1px solid #00ffff' }} />
                    <Legend />
                  </PieChart>
                </ResponsiveContainer>
              </HUDFrame>
            )}

            {stats.top_domains?.length > 0 && (
              <HUDFrame title="TOP DOMAINS" className="bg-cockpit-dark/80 border border-hud-cyan/30 rounded-lg">
                <ResponsiveContainer width="100%" height={300}>
                  <BarChart data={stats.top_domains.map((d) => ({ name: d._id?.substring(0, 15) || "Unknown", count: d.count }))}>
                    <CartesianGrid strokeDasharray="3 3" stroke="#333" />
                    <XAxis dataKey="name" tick={{ fill: '#00ff88', fontSize: 10 }} angle={-45} textAnchor="end" height={80} />
                    <YAxis tick={{ fill: '#00ffff' }} />
                    <Tooltip contentStyle={{ backgroundColor: '#0a0a0a', border: '1px solid #00ffff' }} />
                    <Bar dataKey="count" fill="#00ffff" />
                  </BarChart>
                </ResponsiveContainer>
              </HUDFrame>
            )}
          </div>
        ) : (
          <HUDFrame title="NO DATA" className="bg-cockpit-dark/80 border border-hud-cyan/30 rounded-lg text-center py-12">
            <BarChart3 className="w-16 h-16 text-hud-cyan/30 mx-auto mb-4" />
            <p className="text-hud-green font-mono">COLLATE DATA TO VIEW STATISTICS</p>
          </HUDFrame>
        )}
      </div>
    </Layout>
  );
};

const StatCard = ({ label, value }) => (
  <div className="bg-cockpit-dark p-6 rounded-lg border border-hud-cyan/30 text-center">
    <p className="text-3xl font-bold text-hud-cyan font-mono">{value}</p>
    <p className="text-sm text-hud-green/60 mt-1 font-mono">{label}</p>
  </div>
);

// Global Database Page
const GlobalDatabasePage = () => {
  const [data, setData] = useState(null);
  const [loading, setLoading] = useState(true);
  const [page, setPage] = useState(1);

  useEffect(() => {
    fetchData();
  }, [page]);

  const fetchData = async () => {
    setLoading(true);
    try {
      const res = await axios.get(`${API}/global-database?page=${page}`);
      setData(res.data);
    } catch (error) {
      toast.error(error.response?.data?.detail || "FAILED TO LOAD DATABASE");
    } finally {
      setLoading(false);
    }
  };

  return (
    <Layout>
      <div className="max-w-6xl mx-auto">
        <div className="mb-8">
          <h1 className="text-3xl font-bold text-hud-green font-mono tracking-wider mb-2">GLOBAL DATABASE</h1>
          <p className="text-hud-cyan/80 font-mono text-sm">Access public categories from all pilots.</p>
        </div>

        {loading ? (
          <div className="flex justify-center py-12">
            <Loader2 className="w-8 h-8 animate-spin text-hud-cyan" />
          </div>
        ) : data?.results?.length > 0 ? (
          <>
            <p className="text-hud-cyan font-mono text-sm mb-4">
              {data.total} RECORDS | PAGE {data.page} OF {data.total_pages}
            </p>
            <div className="space-y-3">
              {data.results.map((result) => (
                <SearchResultCard key={result.id} result={result} />
              ))}
            </div>
          </>
        ) : (
          <HUDFrame title="NO PUBLIC DATA" className="bg-cockpit-dark/80 border border-hud-cyan/30 rounded-lg text-center py-12">
            <Globe className="w-16 h-16 text-hud-cyan/30 mx-auto mb-4" />
            <p className="text-hud-green font-mono">NO PUBLIC RESULTS AVAILABLE</p>
          </HUDFrame>
        )}
      </div>
    </Layout>
  );
};

// Book Page
const BookPage = () => {
  return (
    <Layout>
      <div className="max-w-4xl mx-auto">
        <HUDFrame title="LETTERS TO EVELYN" className="bg-cockpit-dark/80 border border-hud-orange/30 rounded-lg mb-8">
          <div className="flex flex-col md:flex-row gap-8">
            <div className="flex-shrink-0">
              <img 
                src={BOOK_IMAGES.author}
                alt="John Selman"
                className="w-48 h-48 rounded-lg border-2 border-hud-orange object-cover"
              />
              <div className="flex justify-center mt-4">
                {[...Array(5)].map((_, i) => (
                  <Star key={i} className="w-6 h-6 fill-hud-orange text-hud-orange" />
                ))}
              </div>
              <p className="text-center text-hud-green text-sm font-mono mt-2">15 Five-Star Reviews</p>
            </div>
            <div className="flex-1">
              <h1 className="text-3xl font-bold text-hud-orange font-mono tracking-wider mb-2">
                LETTERS TO EVELYN
              </h1>
              <p className="text-hud-cyan text-lg font-mono mb-4">By John Selman</p>
              <p className="text-hud-green/80 font-mono text-sm mb-4">
                A prolific odyssey of love and redemption - from the author who holds a World Record in Aviation.
              </p>
              <p className="text-hud-green/60 font-mono text-sm mb-6 italic">
                "A profound and unforgettable literary piece... poetic prose and introspective storytelling create an immersive reading experience that is as enlightening as it is emotionally resonant."
                <br />— Divine Zape, Readers' Favorite
              </p>

              <div className="flex flex-wrap gap-3">
                <a
                  href={BOOK_INFO.amazonUrl}
                  target="_blank"
                  rel="noopener noreferrer"
                  className="px-6 py-3 bg-hud-orange/20 border border-hud-orange text-hud-orange font-mono tracking-wider rounded hover:bg-hud-orange/30 transition-all flex items-center gap-2"
                >
                  <ShoppingCart className="w-5 h-5" />
                  BUY ON AMAZON
                </a>
                <a
                  href={BOOK_INFO.officialUrl}
                  target="_blank"
                  rel="noopener noreferrer"
                  className="px-6 py-3 bg-hud-cyan/20 border border-hud-cyan text-hud-cyan font-mono tracking-wider rounded hover:bg-hud-cyan/30 transition-all flex items-center gap-2"
                >
                  <ExternalLink className="w-5 h-5" />
                  OFFICIAL SITE
                </a>
              </div>
            </div>
          </div>
        </HUDFrame>

        {/* Reviews */}
        <HUDFrame title="CRITICAL ACCLAIM" className="bg-cockpit-dark/80 border border-hud-cyan/30 rounded-lg mb-8">
          <div className="space-y-4">
            {BOOK_INFO.quotes.map((quote, idx) => (
              <div key={idx} className="bg-cockpit p-4 rounded border border-hud-green/20">
                <p className="text-hud-green/80 font-mono text-sm italic">"{quote.text}"</p>
                <p className="text-hud-cyan text-xs font-mono mt-2">— {quote.author}</p>
              </div>
            ))}
          </div>
        </HUDFrame>

        {/* Links */}
        <HUDFrame title="PURCHASE LINKS" className="bg-cockpit-dark/80 border border-hud-green/30 rounded-lg">
          <div className="grid md:grid-cols-2 gap-4">
            {[
              { label: "Amazon", url: BOOK_INFO.amazonUrl },
              { label: "Official Website", url: BOOK_INFO.officialUrl },
              { label: "Sintra Site", url: BOOK_INFO.sintraUrl },
              { label: "Readers' Favorite", url: BOOK_INFO.readersFavoriteUrl },
              { label: "Google Drive Preview", url: BOOK_INFO.googleDriveUrl },
            ].map((link, idx) => (
              <a
                key={idx}
                href={link.url}
                target="_blank"
                rel="noopener noreferrer"
                className="flex items-center gap-2 px-4 py-3 bg-cockpit border border-hud-cyan/30 rounded hover:border-hud-cyan transition-colors text-hud-green font-mono text-sm"
              >
                <ExternalLink className="w-4 h-4 text-hud-cyan" />
                {link.label}
              </a>
            ))}
          </div>
        </HUDFrame>
      </div>
    </Layout>
  );
};

// Subscribe Page
const SubscribePage = () => {
  const { user, refreshUser } = useAuth();
  const [processing, setProcessing] = useState(false);
  const [selectedMethod, setSelectedMethod] = useState("paypal");

  const handlePayment = async () => {
    setProcessing(true);
    try {
      await axios.post(`${API}/payments/process`, {
        payment_method: selectedMethod,
        item_type: "subscription",
        amount: 0.95
      });
      toast.success("PAYMENT SUCCESSFUL (SANDBOX)");
      await refreshUser();
    } catch (error) {
      toast.error("PAYMENT FAILED");
    } finally {
      setProcessing(false);
    }
  };

  if (user?.is_paid) {
    return (
      <Layout>
        <div className="max-w-lg mx-auto">
          <HUDFrame title="LIFETIME ACCESS ACTIVE" className="bg-cockpit-dark/80 border border-hud-green/30 rounded-lg text-center py-12">
            <Shield className="w-20 h-20 text-hud-green mx-auto mb-4" />
            <h2 className="text-2xl font-bold text-hud-green font-mono mb-2">PREMIUM STATUS ACTIVE</h2>
            <p className="text-hud-cyan/80 font-mono text-sm">You have unlimited access to all features.</p>
          </HUDFrame>
        </div>
      </Layout>
    );
  }

  return (
    <Layout>
      <div className="max-w-lg mx-auto">
        <HUDFrame title="UPGRADE TO PREMIUM" className="bg-cockpit-dark/80 border border-hud-cyan/30 rounded-lg">
          <div className="text-center mb-6">
            <div className="text-5xl font-bold text-hud-cyan font-mono mb-2">$0.95</div>
            <p className="text-hud-green font-mono">LIFETIME ACCESS</p>
          </div>

          <div className="space-y-3 mb-6">
            {[
              "Unlimited search results pages",
              "Unlimited categories",
              "Advanced statistics",
              "Global Research Database",
              "Priority support"
            ].map((feature, idx) => (
              <div key={idx} className="flex items-center gap-2 text-hud-green font-mono text-sm">
                <Zap className="w-4 h-4 text-hud-cyan" />
                {feature}
              </div>
            ))}
          </div>

          <div className="space-y-3 mb-6">
            <p className="text-xs text-hud-cyan font-mono mb-2">SELECT PAYMENT METHOD:</p>
            {[
              { id: "paypal", label: "PayPal (Sandbox)" },
              { id: "google_pay", label: "Google Pay (Sandbox)" },
              { id: "shopify", label: "Shopify (Sandbox)" }
            ].map((method) => (
              <label key={method.id} className="flex items-center gap-3 p-3 bg-cockpit border border-hud-green/20 rounded cursor-pointer hover:border-hud-cyan/50">
                <input
                  type="radio"
                  name="payment"
                  value={method.id}
                  checked={selectedMethod === method.id}
                  onChange={(e) => setSelectedMethod(e.target.value)}
                  className="text-hud-cyan"
                />
                <span className="text-hud-green font-mono text-sm">{method.label}</span>
              </label>
            ))}
          </div>

          <button
            onClick={handlePayment}
            disabled={processing}
            className="w-full py-4 bg-hud-cyan/20 border border-hud-cyan text-hud-cyan font-mono tracking-wider rounded hover:bg-hud-cyan/30 disabled:opacity-50 flex items-center justify-center gap-2"
          >
            {processing ? <Loader2 className="w-5 h-5 animate-spin" /> : <CreditCard className="w-5 h-5" />}
            PROCESS PAYMENT
          </button>

          <p className="text-center text-hud-orange text-xs font-mono mt-4">
            * SANDBOX MODE - No real charges
          </p>
        </HUDFrame>

        {/* Book Promo */}
        <div className="mt-8">
          <BookPromoBanner />
        </div>
      </div>
    </Layout>
  );
};

// Admin Page
const AdminPage = () => {
  const [settings, setSettings] = useState(null);
  const [users, setUsers] = useState([]);
  const [loading, setLoading] = useState(true);
  const { user } = useAuth();

  useEffect(() => {
    fetchData();
  }, []);

  const fetchData = async () => {
    try {
      const [settingsRes, usersRes] = await Promise.all([
        axios.get(`${API}/admin/settings`),
        axios.get(`${API}/admin/users`)
      ]);
      setSettings(settingsRes.data);
      setUsers(usersRes.data);
    } catch (error) {
      toast.error("FAILED TO LOAD ADMIN DATA");
    } finally {
      setLoading(false);
    }
  };

  if (!user?.is_admin) {
    return (
      <Layout>
        <div className="text-center py-12">
          <Shield className="w-16 h-16 text-hud-red/50 mx-auto mb-4" />
          <h1 className="text-2xl font-bold text-hud-red font-mono">ACCESS DENIED</h1>
          <p className="text-hud-cyan/60 mt-2 font-mono">Admin clearance required</p>
        </div>
      </Layout>
    );
  }

  return (
    <Layout>
      <div className="max-w-4xl mx-auto">
        <div className="mb-8">
          <h1 className="text-3xl font-bold text-hud-green font-mono tracking-wider mb-2">ADMIN CONTROL</h1>
          <p className="text-hud-cyan/80 font-mono text-sm">System configuration and user management.</p>
        </div>

        {loading ? (
          <div className="flex justify-center py-12">
            <Loader2 className="w-8 h-8 animate-spin text-hud-cyan" />
          </div>
        ) : (
          <div className="space-y-6">
            <HUDFrame title="SYSTEM SETTINGS" className="bg-cockpit-dark/80 border border-hud-cyan/30 rounded-lg">
              <div className="grid md:grid-cols-2 gap-4">
                <div>
                  <label className="block text-xs font-mono text-hud-cyan mb-1">RESULTS PER PAGE</label>
                  <input
                    type="number"
                    value={settings?.results_per_page || 20}
                    readOnly
                    className="w-full px-4 py-2 bg-cockpit border border-hud-green/30 rounded text-hud-green font-mono"
                  />
                </div>
                <div>
                  <label className="block text-xs font-mono text-hud-cyan mb-1">FREE USER PAGES</label>
                  <input
                    type="number"
                    value={settings?.free_user_pages || 1}
                    readOnly
                    className="w-full px-4 py-2 bg-cockpit border border-hud-green/30 rounded text-hud-green font-mono"
                  />
                </div>
                <div>
                  <label className="block text-xs font-mono text-hud-cyan mb-1">SUBSCRIPTION PRICE</label>
                  <input
                    type="text"
                    value={`$${settings?.subscription_price || 0.95}`}
                    readOnly
                    className="w-full px-4 py-2 bg-cockpit border border-hud-green/30 rounded text-hud-green font-mono"
                  />
                </div>
                <div>
                  <label className="block text-xs font-mono text-hud-cyan mb-1">MAX CATEGORY LEVELS</label>
                  <input
                    type="number"
                    value={settings?.max_category_levels || 100}
                    readOnly
                    className="w-full px-4 py-2 bg-cockpit border border-hud-green/30 rounded text-hud-green font-mono"
                  />
                </div>
              </div>
            </HUDFrame>

            <HUDFrame title="USER ROSTER" className="bg-cockpit-dark/80 border border-hud-green/30 rounded-lg">
              <div className="overflow-x-auto">
                <table className="w-full">
                  <thead>
                    <tr className="border-b border-hud-cyan/30">
                      <th className="text-left py-3 px-4 text-xs font-mono text-hud-cyan">CALLSIGN</th>
                      <th className="text-left py-3 px-4 text-xs font-mono text-hud-cyan">EMAIL</th>
                      <th className="text-left py-3 px-4 text-xs font-mono text-hud-cyan">STATUS</th>
                    </tr>
                  </thead>
                  <tbody>
                    {users.map((u) => (
                      <tr key={u.id} className="border-b border-hud-green/10">
                        <td className="py-3 px-4">
                          <span className="text-hud-green font-mono text-sm">{u.username}</span>
                          {u.is_admin && (
                            <span className="ml-2 px-2 py-0.5 bg-hud-orange/20 text-hud-orange text-xs rounded font-mono">ADMIN</span>
                          )}
                        </td>
                        <td className="py-3 px-4 text-sm text-hud-cyan/60 font-mono">{u.email}</td>
                        <td className="py-3 px-4">
                          <span className={`px-2 py-0.5 text-xs rounded font-mono ${u.is_paid ? "bg-hud-green/20 text-hud-green" : "bg-hud-orange/20 text-hud-orange"}`}>
                            {u.is_paid ? "PREMIUM" : "FREE"}
                          </span>
                        </td>
                      </tr>
                    ))}
                  </tbody>
                </table>
              </div>
            </HUDFrame>
          </div>
        )}
      </div>
    </Layout>
  );
};

// Main App
function App() {
  return (
    <AuthProvider>
      <Toaster 
        position="top-right" 
        toastOptions={{
          style: {
            background: '#0a0a0a',
            border: '1px solid #00ffff',
            color: '#00ff88',
            fontFamily: 'monospace'
          }
        }}
      />
      <BrowserRouter>
        <Routes>
          <Route path="/login" element={<LoginPage />} />
          <Route path="/" element={<ProtectedRoute><HomePage /></ProtectedRoute>} />
          <Route path="/infopilot" element={<ProtectedRoute><InfoPilotPage /></ProtectedRoute>} />
          <Route path="/ultimate-search" element={<ProtectedRoute><UltimateSearchPage /></ProtectedRoute>} />
          <Route path="/categories" element={<ProtectedRoute><CategoriesPage /></ProtectedRoute>} />
          <Route path="/statistics" element={<ProtectedRoute><StatisticsPage /></ProtectedRoute>} />
          <Route path="/global-database" element={<ProtectedRoute><GlobalDatabasePage /></ProtectedRoute>} />
          <Route path="/book" element={<ProtectedRoute><BookPage /></ProtectedRoute>} />
          <Route path="/subscribe" element={<ProtectedRoute><SubscribePage /></ProtectedRoute>} />
          <Route path="/admin" element={<ProtectedRoute><AdminPage /></ProtectedRoute>} />
          <Route path="*" element={<Navigate to="/" />} />
        </Routes>
      </BrowserRouter>
    </AuthProvider>
  );
}

export default App;
