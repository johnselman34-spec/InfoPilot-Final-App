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
  Crosshair, Navigation, Zap, Radio, Cpu, Book, Edit3, Copy, Check, Gift,
  Sparkles, Crown, Lock, Unlock, ArrowRight, DollarSign
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

// All Images
const IMAGES = {
  globe: "https://customer-assets.emergentagent.com/job_0c3ceef4-3e2b-40c0-b767-31d91735cf23/artifacts/utj2uh0i_global-network-world-globe-focusing-usa-symbolizing-data-transfer-worldwide-concept-data-transfer-global-connectivity-information-exchange-world-globe-usa-symbolism_918839-41653.jpg",
  author: "https://customer-assets.emergentagent.com/job_0c3ceef4-3e2b-40c0-b767-31d91735cf23/artifacts/5150hnhi_FB_IMG_1767397923842.jpg",
  bookCover1: "https://customer-assets.emergentagent.com/job_0c3ceef4-3e2b-40c0-b767-31d91735cf23/artifacts/ls79opar_IMG_20251230_025749_432.jpg",
  bookCover2: "https://customer-assets.emergentagent.com/job_0c3ceef4-3e2b-40c0-b767-31d91735cf23/artifacts/yrjcamzy_IMG_20251230_025749_282.jpg"
};

// Book Info with 19 Five-Star Reviews
const BOOK_INFO = {
  title: "Letters to Evelyn",
  author: "John Selman",
  tagline: "The Navy Taught Me to Fly Jets. The Universe Taught Me Everything Else.",
  genre: "A True Supernatural Thriller Comedy",
  years: "13 Years of Cosmic Chaos",
  rating: 5.0,
  reviewsCount: 19,
  price: "$2.99",
  amazonUrl: "https://a.co/d/atfpIds",
  sintraUrl: "https://www.Letters-to-Evelyn.sintra.site",
  officialUrl: "https://letterstoevelynbyjohnselmanii.com",
  readersFavoriteUrl: "https://readersfavorite.com/book-review/letters-to-evelyn",
  googleDriveUrl: "https://drive.google.com/file/d/1YFhr75fWLzF2nu6nYDgVKB0fjEzZ36Pt/view?usp=drivesdk",
  quotes: [
    { text: "A profound and unforgettable literary piece... poetic prose and introspective storytelling create an immersive reading experience that is as enlightening as it is emotionally resonant.", author: "Divine Zape, Readers' Favorite ⭐⭐⭐⭐⭐" },
    { text: "The author's imagination is off the charts. I did not think a novel combining science fiction, romance, and biblical characters could be achieved.", author: "Lesley Jones, Readers' Favorite ⭐⭐⭐⭐⭐" },
    { text: "Such a unique and wonderfully woven story that had me riveted from the moment I started reading it.", author: "Rabia Tanveer, Readers' Favorite ⭐⭐⭐⭐⭐" },
    { text: "A mesmerizing exploration of the human condition and the quest for meaning in a chaotic world.", author: "Readers' Favorite Review ⭐⭐⭐⭐⭐" },
    { text: "Selman's unwavering devotion to Evelyn is heartbreaking and inspiring, a light amidst the darkness.", author: "Professional Review ⭐⭐⭐⭐⭐" }
  ]
};

// Subscription Price - NOW 90 CENTS!
const SUBSCRIPTION_PRICE = 0.90;

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

// Loading Screen
const LoadingScreen = () => (
  <div className="min-h-screen bg-cockpit flex items-center justify-center">
    <div className="text-center">
      <div className="relative w-24 h-24 mx-auto mb-6">
        <div className="absolute inset-0 border-4 border-hud-cyan/30 rounded-full animate-ping"></div>
        <div className="absolute inset-2 border-2 border-hud-green rounded-full animate-spin"></div>
        <Radar className="absolute inset-0 m-auto w-12 h-12 text-hud-cyan animate-pulse" />
      </div>
      <p className="text-hud-green font-mono text-lg tracking-wider">INITIALIZING INFOPILOT...</p>
    </div>
  </div>
);

// HUD Frame Component
const HUDFrame = ({ children, title, className = "", color = "cyan" }) => {
  const borderColor = color === "orange" ? "border-hud-orange" : color === "green" ? "border-hud-green" : "border-hud-cyan";
  const textColor = color === "orange" ? "text-hud-orange" : color === "green" ? "text-hud-green" : "text-hud-cyan";
  
  return (
    <div className={`relative ${className}`}>
      <div className={`absolute top-0 left-0 w-4 h-4 border-t-2 border-l-2 ${borderColor}`}></div>
      <div className={`absolute top-0 right-0 w-4 h-4 border-t-2 border-r-2 ${borderColor}`}></div>
      <div className={`absolute bottom-0 left-0 w-4 h-4 border-b-2 border-l-2 ${borderColor}`}></div>
      <div className={`absolute bottom-0 right-0 w-4 h-4 border-b-2 border-r-2 ${borderColor}`}></div>
      {title && (
        <div className="absolute -top-3 left-6 bg-cockpit px-2">
          <span className={`${textColor} text-xs font-mono tracking-wider`}>{title}</span>
        </div>
      )}
      <div className="p-4">{children}</div>
    </div>
  );
};

// MEGA Sales Banner - Subscription
const SubscriptionSalesBanner = ({ onUpgrade, compact = false }) => {
  const { user } = useAuth();
  
  if (user?.is_paid) return null;
  
  return (
    <div className={`bg-gradient-to-r from-hud-orange/20 via-hud-cyan/20 to-hud-green/20 border-2 border-hud-orange rounded-xl overflow-hidden ${compact ? 'p-4' : 'p-6'} animate-pulse-slow`}>
      <div className="flex flex-col md:flex-row items-center justify-between gap-4">
        <div className="flex items-center gap-4">
          <div className="relative">
            <Crown className="w-12 h-12 text-hud-orange animate-bounce" />
            <Sparkles className="w-6 h-6 text-hud-cyan absolute -top-1 -right-1" />
          </div>
          <div>
            <div className="flex items-center gap-2">
              <span className="text-4xl font-bold text-hud-orange font-mono">$0.90</span>
              <span className="text-hud-green font-mono text-sm line-through opacity-50">$9.99</span>
              <span className="bg-hud-red text-white px-2 py-1 rounded text-xs font-bold animate-pulse">91% OFF!</span>
            </div>
            <p className="text-hud-cyan font-mono text-sm">LIFETIME PREMIUM ACCESS - ONE TIME PAYMENT!</p>
            {!compact && (
              <p className="text-hud-green/70 text-xs font-mono mt-1">Unlimited searches • Unlimited categories • Full access forever</p>
            )}
          </div>
        </div>
        <button
          onClick={onUpgrade}
          className="px-8 py-4 bg-gradient-to-r from-hud-orange to-hud-red text-white font-bold font-mono tracking-wider rounded-lg hover:scale-105 transition-transform shadow-lg shadow-hud-orange/30 flex items-center gap-2"
        >
          <Zap className="w-5 h-5" />
          UPGRADE NOW
          <ArrowRight className="w-5 h-5" />
        </button>
      </div>
    </div>
  );
};

// MEGA Book Sales Banner
const BookSalesBanner = ({ variant = "full" }) => {
  const openAmazon = () => window.open(BOOK_INFO.amazonUrl, '_blank');
  
  if (variant === "compact") {
    return (
      <div className="bg-gradient-to-r from-purple-900/30 to-blue-900/30 border border-purple-500/50 rounded-lg p-4 cursor-pointer hover:scale-[1.02] transition-transform" onClick={openAmazon}>
        <div className="flex items-center gap-4">
          <img src={IMAGES.bookCover1} alt="Letters to Evelyn" className="w-20 h-20 object-cover rounded-lg shadow-lg" />
          <div className="flex-1">
            <div className="flex items-center gap-2">
              <h3 className="text-hud-orange font-mono font-bold">LETTERS TO EVELYN</h3>
              <div className="flex">
                {[...Array(5)].map((_, i) => <Star key={i} className="w-3 h-3 fill-yellow-400 text-yellow-400" />)}
              </div>
            </div>
            <p className="text-hud-cyan text-xs font-mono">19 Five-Star Reviews • Supernatural Thriller Comedy</p>
            <p className="text-hud-green/70 text-xs font-mono italic mt-1">"A profound and unforgettable literary piece"</p>
          </div>
          <button className="px-4 py-2 bg-purple-600 text-white font-mono text-sm rounded hover:bg-purple-500 flex items-center gap-1">
            <ShoppingCart className="w-4 h-4" />
            GET BOOK
          </button>
        </div>
      </div>
    );
  }
  
  return (
    <div className="bg-gradient-to-br from-purple-900/40 via-blue-900/30 to-pink-900/40 border-2 border-purple-500 rounded-xl overflow-hidden">
      <div className="p-6">
        <div className="flex flex-col lg:flex-row gap-6">
          {/* Book Image */}
          <div className="lg:w-1/3 flex justify-center">
            <div className="relative group cursor-pointer" onClick={openAmazon}>
              <img 
                src={IMAGES.bookCover2} 
                alt="Letters to Evelyn - 13 Years of Cosmic Chaos" 
                className="w-full max-w-xs rounded-lg shadow-2xl shadow-purple-500/30 group-hover:scale-105 transition-transform"
              />
              <div className="absolute top-2 right-2 bg-yellow-500 text-black px-2 py-1 rounded font-bold text-xs">
                ⭐ 19 FIVE-STAR REVIEWS
              </div>
            </div>
          </div>
          
          {/* Book Info */}
          <div className="lg:w-2/3">
            <div className="flex items-center gap-2 mb-2">
              <h2 className="text-3xl font-bold text-transparent bg-clip-text bg-gradient-to-r from-purple-400 to-pink-400 font-mono">
                LETTERS TO EVELYN
              </h2>
            </div>
            
            <p className="text-hud-cyan font-mono mb-2">By World Record Aviation Holder <span className="text-hud-orange font-bold">John Selman</span></p>
            
            <div className="flex items-center gap-4 mb-4">
              <div className="flex">
                {[...Array(5)].map((_, i) => <Star key={i} className="w-5 h-5 fill-yellow-400 text-yellow-400" />)}
              </div>
              <span className="text-yellow-400 font-mono font-bold">5.0 / 5.0</span>
              <span className="text-hud-green font-mono text-sm">(19 Professional Reviews)</span>
            </div>
            
            <p className="text-xl text-hud-orange font-mono italic mb-4">
              "{BOOK_INFO.tagline}"
            </p>
            
            <p className="text-hud-green/80 font-mono text-sm mb-4">
              {BOOK_INFO.genre} • {BOOK_INFO.years}
            </p>
            
            {/* Review Quote */}
            <div className="bg-cockpit/50 rounded-lg p-4 mb-4 border-l-4 border-purple-500">
              <p className="text-hud-green/90 font-mono text-sm italic">
                "{BOOK_INFO.quotes[0].text}"
              </p>
              <p className="text-purple-400 font-mono text-xs mt-2">— {BOOK_INFO.quotes[0].author}</p>
            </div>
            
            {/* CTA Buttons */}
            <div className="flex flex-wrap gap-3">
              <a
                href={BOOK_INFO.amazonUrl}
                target="_blank"
                rel="noopener noreferrer"
                className="px-6 py-3 bg-gradient-to-r from-yellow-500 to-orange-500 text-black font-bold font-mono rounded-lg hover:scale-105 transition-transform shadow-lg flex items-center gap-2"
              >
                <ShoppingCart className="w-5 h-5" />
                BUY ON AMAZON
              </a>
              <a
                href={BOOK_INFO.officialUrl}
                target="_blank"
                rel="noopener noreferrer"
                className="px-6 py-3 bg-purple-600 text-white font-mono rounded-lg hover:bg-purple-500 transition-colors flex items-center gap-2"
              >
                <ExternalLink className="w-5 h-5" />
                OFFICIAL SITE
              </a>
              <a
                href={BOOK_INFO.readersFavoriteUrl}
                target="_blank"
                rel="noopener noreferrer"
                className="px-6 py-3 border border-purple-500 text-purple-400 font-mono rounded-lg hover:bg-purple-500/20 transition-colors flex items-center gap-2"
              >
                <Star className="w-5 h-5" />
                READ REVIEWS
              </a>
            </div>
          </div>
        </div>
      </div>
    </div>
  );
};

// Sidebar Navigation
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
    { path: "/book", icon: Book, label: "📚 LETTERS TO EVELYN", highlight: true },
    { path: "/subscribe", icon: Crown, label: user?.is_paid ? "✅ PREMIUM" : "⚡ UPGRADE $0.90", highlight: !user?.is_paid },
  ];

  if (user?.is_admin) {
    menuItems.push({ path: "/admin", icon: Shield, label: "ADMIN CONTROL" });
  }

  return (
    <>
      {isOpen && <div className="fixed inset-0 bg-black/70 z-40 lg:hidden" onClick={() => setIsOpen(false)} />}
      
      <aside className={`fixed top-0 left-0 h-full bg-cockpit-dark border-r border-hud-cyan/30 z-50 transition-transform duration-300 w-72 ${isOpen ? "translate-x-0" : "-translate-x-full lg:translate-x-0"}`}>
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
              onClick={() => { navigate(item.path); setIsOpen(false); }}
              className={`w-full flex items-center gap-3 px-4 py-3 rounded transition-all font-mono text-sm
                ${location.pathname === item.path
                  ? "bg-hud-cyan/20 text-hud-cyan border border-hud-cyan/50"
                  : item.highlight
                    ? "text-hud-orange hover:bg-hud-orange/10 border border-hud-orange/30 animate-pulse"
                    : "text-hud-green/70 hover:bg-hud-green/10 hover:text-hud-green border border-transparent"
                }`}
            >
              <item.icon className="w-5 h-5" />
              <span className="tracking-wider">{item.label}</span>
            </button>
          ))}
        </nav>

        {/* Sidebar Promo */}
        {!user?.is_paid && (
          <div className="mx-4 p-3 bg-gradient-to-r from-hud-orange/20 to-hud-red/20 rounded-lg border border-hud-orange/50">
            <p className="text-hud-orange font-mono text-xs text-center">
              🔥 LIMITED TIME: <span className="font-bold">$0.90</span> LIFETIME ACCESS!
            </p>
          </div>
        )}

        <div className="absolute bottom-0 left-0 right-0 p-4 border-t border-hud-cyan/30 bg-cockpit-dark">
          <div className="flex items-center gap-3 mb-4">
            <div className="w-10 h-10 bg-cockpit border border-hud-green rounded-full flex items-center justify-center text-hud-green font-bold font-mono">
              {user?.username?.[0]?.toUpperCase() || "P"}
            </div>
            <div className="flex-1 min-w-0">
              <p className="font-mono text-hud-green text-sm truncate">{user?.username}</p>
              {user?.is_paid ? (
                <span className="inline-flex items-center gap-1 px-2 py-0.5 bg-hud-green/20 text-hud-green text-xs rounded font-mono">
                  <Crown className="w-3 h-3" /> PREMIUM
                </span>
              ) : (
                <span className="inline-block px-2 py-0.5 bg-hud-orange/20 text-hud-orange text-xs rounded font-mono">
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

// Login Page
const LoginPage = () => {
  const [isLogin, setIsLogin] = useState(true);
  const [email, setEmail] = useState("");
  const [password, setPassword] = useState("");
  const [username, setUsername] = useState("");
  const [loading, setLoading] = useState(false);
  const { login, register, googleLogin, user } = useAuth();
  const navigate = useNavigate();

  useEffect(() => { if (user) navigate("/"); }, [user, navigate]);

  const handleSubmit = async (e) => {
    e.preventDefault();
    setLoading(true);
    try {
      if (isLogin) { await login(email, password); }
      else { await register(username, email, password); }
      toast.success(isLogin ? "PILOT AUTHENTICATED" : "PILOT REGISTERED");
      navigate("/");
    } catch (error) {
      toast.error(error.response?.data?.detail || "AUTHENTICATION FAILED");
    } finally { setLoading(false); }
  };

  const handleGoogleLogin = async (credentialResponse) => {
    setLoading(true);
    try {
      await googleLogin(credentialResponse.credential);
      toast.success("GOOGLE AUTH SUCCESSFUL");
      navigate("/");
    } catch (error) {
      toast.error(error.response?.data?.detail || "Google authentication failed");
    } finally { setLoading(false); }
  };

  return (
    <div className="min-h-screen bg-cockpit flex items-center justify-center p-4 relative overflow-hidden">
      <div className="absolute inset-0 opacity-20">
        <div className="absolute top-20 left-20 w-64 h-64 border border-hud-cyan/30 rounded-full"></div>
        <div className="absolute bottom-20 right-20 w-96 h-96 border border-hud-green/20 rounded-full"></div>
      </div>

      <div className="w-full max-w-md relative z-10">
        <div className="text-center mb-8">
          <div className="inline-flex items-center justify-center w-20 h-20 bg-cockpit-dark border-2 border-hud-cyan rounded-xl mb-4 relative">
            <Plane className="w-12 h-12 text-hud-cyan" />
          </div>
          <h1 className="text-4xl font-bold text-hud-green font-mono tracking-wider">INFOPILOT</h1>
          <p className="text-hud-cyan/80 mt-2 font-mono text-sm">TACTICAL INFORMATION EXCHANGE SYSTEM</p>
        </div>

        {/* Special Offer Banner */}
        <div className="mb-6 p-4 bg-gradient-to-r from-hud-orange/30 to-hud-red/30 rounded-lg border border-hud-orange animate-pulse">
          <p className="text-center text-hud-orange font-mono font-bold">
            🎉 NEW USERS: Get LIFETIME ACCESS for just $0.90!
          </p>
        </div>

        <HUDFrame title="AUTHENTICATION" className="bg-cockpit-dark/90 backdrop-blur border border-hud-cyan/30 rounded-lg">
          <div className="flex mb-6">
            <button onClick={() => setIsLogin(true)} className={`flex-1 py-3 text-center font-mono text-sm tracking-wider transition-colors rounded-l ${isLogin ? "bg-hud-cyan/20 text-hud-cyan border border-hud-cyan" : "bg-cockpit text-hud-green/50 border border-hud-green/20"}`}>LOGIN</button>
            <button onClick={() => setIsLogin(false)} className={`flex-1 py-3 text-center font-mono text-sm tracking-wider transition-colors rounded-r ${!isLogin ? "bg-hud-cyan/20 text-hud-cyan border border-hud-cyan" : "bg-cockpit text-hud-green/50 border border-hud-green/20"}`}>REGISTER</button>
          </div>

          <form onSubmit={handleSubmit} className="space-y-4">
            {!isLogin && (
              <div>
                <label className="block text-xs font-mono text-hud-cyan mb-1 tracking-wider">CALLSIGN</label>
                <input type="text" value={username} onChange={(e) => setUsername(e.target.value)} className="w-full px-4 py-3 bg-cockpit border border-hud-green/30 rounded text-hud-green font-mono focus:border-hud-cyan focus:outline-none" required={!isLogin} data-testid="username-input" />
              </div>
            )}
            <div>
              <label className="block text-xs font-mono text-hud-cyan mb-1 tracking-wider">EMAIL</label>
              <input type="email" value={email} onChange={(e) => setEmail(e.target.value)} className="w-full px-4 py-3 bg-cockpit border border-hud-green/30 rounded text-hud-green font-mono focus:border-hud-cyan focus:outline-none" required data-testid="email-input" />
            </div>
            <div>
              <label className="block text-xs font-mono text-hud-cyan mb-1 tracking-wider">PASSWORD</label>
              <input type="password" value={password} onChange={(e) => setPassword(e.target.value)} className="w-full px-4 py-3 bg-cockpit border border-hud-green/30 rounded text-hud-green font-mono focus:border-hud-cyan focus:outline-none" required data-testid="password-input" />
            </div>
            <button type="submit" disabled={loading} className="w-full py-3 bg-hud-cyan/20 border border-hud-cyan text-hud-cyan font-mono tracking-wider rounded hover:bg-hud-cyan/30 transition-all disabled:opacity-50" data-testid="submit-btn">
              {loading ? <Loader2 className="w-5 h-5 animate-spin mx-auto" /> : isLogin ? "AUTHENTICATE" : "CREATE ACCOUNT"}
            </button>
          </form>

          <div className="mt-6">
            <div className="relative"><div className="absolute inset-0 flex items-center"><div className="w-full border-t border-hud-cyan/20"></div></div><div className="relative flex justify-center text-xs"><span className="px-2 bg-cockpit-dark text-hud-cyan/60 font-mono">OR</span></div></div>
            <div className="mt-4 flex justify-center">
              <GoogleLogin onSuccess={handleGoogleLogin} onError={() => toast.error("Google Sign-In failed")} theme="filled_black" size="large" text="continue_with" shape="rectangular" />
            </div>
          </div>
        </HUDFrame>

        {/* Book Promo */}
        <div className="mt-6">
          <BookSalesBanner variant="compact" />
        </div>
      </div>
    </div>
  );
};

// Home Page - SALES FOCUSED
const HomePage = () => {
  const { user } = useAuth();
  const navigate = useNavigate();

  return (
    <Layout>
      <div className="max-w-5xl mx-auto space-y-6">
        {/* Subscription Promo - TOP PRIORITY */}
        <SubscriptionSalesBanner onUpgrade={() => navigate("/subscribe")} />

        {/* Welcome */}
        <HUDFrame title="COMMAND CENTER" className="bg-cockpit-dark/80 border border-hud-cyan/30 rounded-lg">
          <div className="flex flex-col md:flex-row items-center gap-6">
            <img src={IMAGES.globe} alt="InfoPilot Global Network" className="w-32 h-32 rounded-lg border border-hud-cyan/50 object-cover" />
            <div className="flex-1">
              <h1 className="text-3xl font-bold text-hud-green font-mono tracking-wider mb-2">WELCOME, {user?.username?.toUpperCase()}</h1>
              <p className="text-hud-cyan/80 mb-4 font-mono text-sm">Your tactical gateway to the World Wide Web Information Exchange.</p>
              <div className="flex flex-wrap gap-3">
                <button onClick={() => navigate("/infopilot")} className="px-6 py-3 bg-hud-cyan/20 border border-hud-cyan text-hud-cyan font-mono tracking-wider rounded hover:bg-hud-cyan/30 transition-all flex items-center gap-2" data-testid="start-searching-btn">
                  <Radar className="w-5 h-5" /> BEGIN SEARCH
                </button>
                {!user?.is_paid && (
                  <button onClick={() => navigate("/subscribe")} className="px-6 py-3 bg-gradient-to-r from-hud-orange to-hud-red text-white font-mono tracking-wider rounded hover:scale-105 transition-transform flex items-center gap-2 animate-pulse">
                    <Crown className="w-5 h-5" /> UPGRADE $0.90
                  </button>
                )}
              </div>
            </div>
          </div>
        </HUDFrame>

        {/* Book Promo - FULL */}
        <BookSalesBanner variant="full" />

        {/* Quick Actions */}
        <div className="grid md:grid-cols-3 gap-4">
          <QuickActionCard title="CREATE CATEGORIES" icon={FolderTree} onClick={() => navigate("/categories")} color="cyan" />
          <QuickActionCard title="SEARCH & COLLATE" icon={Radar} onClick={() => navigate("/infopilot")} color="green" />
          <QuickActionCard title="VIEW INTEL" icon={BarChart3} onClick={() => navigate("/statistics")} color="orange" />
        </div>

        {/* Another Subscription CTA */}
        {!user?.is_paid && (
          <div className="text-center p-6 bg-cockpit-dark rounded-lg border border-hud-orange/30">
            <h3 className="text-2xl font-bold text-hud-orange font-mono mb-2">Don't Miss Out!</h3>
            <p className="text-hud-cyan font-mono mb-4">Unlock unlimited searches, categories, and premium features for life.</p>
            <button onClick={() => navigate("/subscribe")} className="px-8 py-4 bg-gradient-to-r from-hud-orange to-hud-red text-white font-bold font-mono tracking-wider rounded-lg hover:scale-105 transition-transform">
              GET LIFETIME ACCESS - ONLY $0.90
            </button>
          </div>
        )}
      </div>
    </Layout>
  );
};

const QuickActionCard = ({ title, icon: Icon, onClick, color = "cyan" }) => {
  const colorClasses = { cyan: "border-hud-cyan/30 hover:border-hud-cyan text-hud-cyan", green: "border-hud-green/30 hover:border-hud-green text-hud-green", orange: "border-hud-orange/30 hover:border-hud-orange text-hud-orange" };
  return (
    <button onClick={onClick} className={`bg-cockpit-dark p-6 rounded-lg border ${colorClasses[color]} transition-all hover:bg-opacity-80 text-left group`}>
      <div className={`w-12 h-12 rounded-lg border ${colorClasses[color]} flex items-center justify-center mb-4 group-hover:scale-110 transition-transform`}><Icon className="w-6 h-6" /></div>
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
  const { user } = useAuth();
  const navigate = useNavigate();

  useEffect(() => { fetchCategories(); }, []);

  const fetchCategories = async () => {
    try {
      const res = await axios.get(`${API}/categories`);
      setCategories(res.data.filter(c => c.user_id === user?.id));
    } catch (error) { console.error("Failed to fetch categories"); }
  };

  const handleCollate = async () => {
    if (!searchQuery.trim()) { toast.error("ENTER SEARCH PARAMETERS"); return; }
    if (categories.length === 0) { toast.error("CREATE CATEGORY PROTOCOLS FIRST"); return; }
    setLoading(true);
    try {
      const res = await axios.post(`${API}/search/collate`, { search_query: searchQuery, max_results: 20 });
      setResults(res.data);
      toast.success(`COLLATED ${res.data.categorized_count} TARGETS`);
    } catch (error) { toast.error(error.response?.data?.detail || "SEARCH FAILED"); }
    finally { setLoading(false); }
  };

  return (
    <Layout>
      <div className="max-w-4xl mx-auto space-y-6">
        <div className="mb-6">
          <h1 className="text-3xl font-bold text-hud-green font-mono tracking-wider mb-2">INFOPILOT SEARCH</h1>
          <p className="text-hud-cyan/80 font-mono text-sm">Search the web and automatically categorize results.</p>
        </div>

        {/* Subscription Promo */}
        <SubscriptionSalesBanner onUpgrade={() => navigate("/subscribe")} compact />

        {/* Search Box */}
        <HUDFrame title="SEARCH PARAMETERS" className="bg-cockpit-dark/80 border border-hud-cyan/30 rounded-lg">
          <div className="flex gap-4">
            <input type="text" value={searchQuery} onChange={(e) => setSearchQuery(e.target.value)} placeholder="Enter search query..." className="flex-1 px-4 py-3 bg-cockpit border border-hud-green/30 rounded text-hud-green font-mono focus:border-hud-cyan focus:outline-none" onKeyPress={(e) => e.key === "Enter" && handleCollate()} data-testid="search-input" />
            <button onClick={handleCollate} disabled={loading} className="px-6 py-3 bg-hud-cyan/20 border border-hud-cyan text-hud-cyan font-mono tracking-wider rounded hover:bg-hud-cyan/30 transition-all disabled:opacity-50 flex items-center gap-2" data-testid="collate-btn">
              {loading ? <Loader2 className="w-5 h-5 animate-spin" /> : <Radar className="w-5 h-5" />} COLLATE
            </button>
          </div>
          {categories.length > 0 && (
            <div className="mt-4">
              <p className="text-xs text-hud-cyan/60 mb-2 font-mono">ACTIVE PROTOCOLS ({categories.length}):</p>
              <div className="flex flex-wrap gap-2">
                {categories.slice(0, 5).map((cat) => (<span key={cat.id} className="px-3 py-1 bg-hud-green/10 border border-hud-green/30 text-hud-green rounded text-xs font-mono">{cat.name}</span>))}
              </div>
            </div>
          )}
        </HUDFrame>

        {/* Book Promo */}
        <BookSalesBanner variant="compact" />

        {/* Results */}
        {results && (
          <HUDFrame title="COLLATED RESULTS" className="bg-cockpit-dark/80 border border-hud-cyan/30 rounded-lg">
            <p className="text-hud-cyan font-mono text-sm mb-4">{results.categorized_count} of {results.total_searched} targets categorized</p>
            {results.results.length > 0 ? (
              <div className="space-y-4">{results.results.map((result) => (<SearchResultCard key={result.id} result={result} />))}</div>
            ) : (<p className="text-hud-orange text-center py-8 font-mono">NO MATCHES FOUND</p>)}
          </HUDFrame>
        )}
      </div>
    </Layout>
  );
};

// Search Result Card
const SearchResultCard = ({ result, showReactions = true }) => {
  const [reacting, setReacting] = useState(false);
  const handleReaction = async (type) => {
    setReacting(true);
    try { await axios.post(`${API}/results/${result.id}/react`, { reaction_type: type }); toast.success("REACTION LOGGED"); }
    catch (error) { toast.error("REACTION FAILED"); }
    finally { setReacting(false); }
  };

  return (
    <div className="bg-cockpit p-4 rounded border border-hud-green/20 hover:border-hud-cyan/50 transition-colors">
      <a href={result.url} target="_blank" rel="noopener noreferrer" className="text-hud-cyan hover:underline font-mono text-sm block truncate">{result.title}</a>
      <p className="text-hud-green/60 text-xs mt-1 line-clamp-2 font-mono">{result.snippet}</p>
      <div className="flex flex-wrap gap-2 mt-2">
        <span className="px-2 py-0.5 bg-hud-orange/20 text-hud-orange text-xs rounded font-mono">{result.article_type}</span>
        <span className="px-2 py-0.5 bg-cockpit-dark text-hud-cyan/60 text-xs rounded font-mono">{result.domain}</span>
      </div>
      {showReactions && (
        <div className="flex gap-2 mt-3 pt-3 border-t border-hud-green/10">
          {[{ type: "like", icon: ThumbsUp }, { type: "love", icon: Heart }, { type: "best", icon: Award }].map(({ type, icon: Icon }) => (
            <button key={type} onClick={() => handleReaction(type)} disabled={reacting} className="flex items-center gap-1 px-2 py-1 text-xs text-hud-green/60 hover:text-hud-cyan rounded transition-colors font-mono">
              <Icon className="w-3 h-3" />{result.reactions?.[type] > 0 && <span>{result.reactions[type]}</span>}
            </button>
          ))}
        </div>
      )}
    </div>
  );
};

// Categories Page with Edit
const CategoriesPage = () => {
  const [categories, setCategories] = useState([]);
  const [loading, setLoading] = useState(true);
  const [showCreate, setShowCreate] = useState(false);
  const [showEdit, setShowEdit] = useState(false);
  const [editingCategory, setEditingCategory] = useState(null);
  const [newCategory, setNewCategory] = useState({ name: "", protocol: "", parentId: null, isPublic: true });
  const [creating, setCreating] = useState(false);
  const [updating, setUpdating] = useState(false);
  const { user } = useAuth();
  const navigate = useNavigate();

  useEffect(() => { fetchCategories(); }, []);

  const fetchCategories = async () => {
    try {
      const res = await axios.get(`${API}/categories`);
      setCategories(res.data.filter(c => c.user_id === user?.id));
    } catch (error) { toast.error("FAILED TO LOAD CATEGORIES"); }
    finally { setLoading(false); }
  };

  const handleCreate = async (e) => {
    e.preventDefault();
    setCreating(true);
    try {
      await axios.post(`${API}/categories`, { name: newCategory.name, protocol: { protocol_string: newCategory.protocol }, parent_id: newCategory.parentId || null, is_public: newCategory.isPublic });
      toast.success("CATEGORY CREATED");
      setShowCreate(false);
      setNewCategory({ name: "", protocol: "", parentId: null, isPublic: true });
      fetchCategories();
    } catch (error) { toast.error(error.response?.data?.detail || "CREATION FAILED"); }
    finally { setCreating(false); }
  };

  const handleEdit = (cat) => { setEditingCategory({ id: cat.id, name: cat.name, protocol_string: cat.protocol_string, is_public: cat.is_public }); setShowEdit(true); };

  const handleUpdate = async (e) => {
    e.preventDefault();
    if (!editingCategory) return;
    setUpdating(true);
    try {
      await axios.put(`${API}/categories/${editingCategory.id}`, { name: editingCategory.name, protocol_string: editingCategory.protocol_string, is_public: editingCategory.is_public });
      toast.success("CATEGORY UPDATED");
      setShowEdit(false);
      setEditingCategory(null);
      fetchCategories();
    } catch (error) { toast.error(error.response?.data?.detail || "UPDATE FAILED"); }
    finally { setUpdating(false); }
  };

  const handleDelete = async (id) => {
    if (!window.confirm("DELETE THIS CATEGORY?")) return;
    try { await axios.delete(`${API}/categories/${id}`); toast.success("CATEGORY DELETED"); fetchCategories(); }
    catch (error) { toast.error("DELETE FAILED"); }
  };

  return (
    <Layout>
      <div className="max-w-4xl mx-auto space-y-6">
        <div className="flex items-center justify-between mb-6">
          <div>
            <h1 className="text-3xl font-bold text-hud-green font-mono tracking-wider mb-2">CATEGORIES</h1>
            <p className="text-hud-cyan/80 font-mono text-sm">Manage your InfoPilot 2.0 protocols.</p>
          </div>
          <button onClick={() => setShowCreate(true)} className="px-4 py-2 bg-hud-cyan/20 border border-hud-cyan text-hud-cyan font-mono tracking-wider rounded hover:bg-hud-cyan/30 transition-colors flex items-center gap-2" data-testid="create-category-btn">
            <Plus className="w-5 h-5" /> NEW CATEGORY
          </button>
        </div>

        <SubscriptionSalesBanner onUpgrade={() => navigate("/subscribe")} compact />

        {/* Create Modal */}
        {showCreate && (
          <div className="fixed inset-0 bg-black/80 flex items-center justify-center z-50 p-4">
            <HUDFrame title="CREATE CATEGORY" className="bg-cockpit-dark border border-hud-cyan/30 rounded-lg max-w-lg w-full">
              <form onSubmit={handleCreate} className="space-y-4">
                <div><label className="block text-xs font-mono text-hud-cyan mb-1">CATEGORY NAME</label><input type="text" value={newCategory.name} onChange={(e) => setNewCategory({ ...newCategory, name: e.target.value })} className="w-full px-4 py-2 bg-cockpit border border-hud-green/30 rounded text-hud-green font-mono focus:border-hud-cyan" required /></div>
                <div><label className="block text-xs font-mono text-hud-cyan mb-1">INFOPILOT 2.0 PROTOCOL</label><textarea value={newCategory.protocol} onChange={(e) => setNewCategory({ ...newCategory, protocol: e.target.value })} placeholder="(word1 or word2) & (word3)+ & (excluded)^" className="w-full px-4 py-2 bg-cockpit border border-hud-green/30 rounded text-hud-green font-mono h-24 focus:border-hud-cyan" required /></div>
                <div className="flex items-center gap-2"><input type="checkbox" id="isPublic" checked={newCategory.isPublic} onChange={(e) => setNewCategory({ ...newCategory, isPublic: e.target.checked })} className="rounded bg-cockpit border-hud-green/30" /><label htmlFor="isPublic" className="text-sm text-hud-green font-mono">Make public</label></div>
                <div className="flex gap-4">
                  <button type="button" onClick={() => setShowCreate(false)} className="flex-1 px-4 py-2 border border-hud-green/30 text-hud-green font-mono rounded hover:bg-hud-green/10">CANCEL</button>
                  <button type="submit" disabled={creating} className="flex-1 px-4 py-2 bg-hud-cyan/20 border border-hud-cyan text-hud-cyan font-mono rounded hover:bg-hud-cyan/30 disabled:opacity-50">{creating ? <Loader2 className="w-5 h-5 animate-spin mx-auto" /> : "CREATE"}</button>
                </div>
              </form>
            </HUDFrame>
          </div>
        )}

        {/* Edit Modal */}
        {showEdit && editingCategory && (
          <div className="fixed inset-0 bg-black/80 flex items-center justify-center z-50 p-4">
            <HUDFrame title="EDIT CATEGORY" color="orange" className="bg-cockpit-dark border border-hud-orange/30 rounded-lg max-w-lg w-full">
              <form onSubmit={handleUpdate} className="space-y-4">
                <div><label className="block text-xs font-mono text-hud-orange mb-1">CATEGORY NAME</label><input type="text" value={editingCategory.name} onChange={(e) => setEditingCategory({ ...editingCategory, name: e.target.value })} className="w-full px-4 py-2 bg-cockpit border border-hud-orange/30 rounded text-hud-green font-mono focus:border-hud-orange" required /></div>
                <div><label className="block text-xs font-mono text-hud-orange mb-1">INFOPILOT 2.0 PROTOCOL</label><textarea value={editingCategory.protocol_string} onChange={(e) => setEditingCategory({ ...editingCategory, protocol_string: e.target.value })} className="w-full px-4 py-2 bg-cockpit border border-hud-orange/30 rounded text-hud-green font-mono h-32 focus:border-hud-orange" required /><p className="text-xs text-hud-cyan/60 mt-1 font-mono">Syntax: (word1 or word2) & (required)+ & (excluded)^</p></div>
                <div className="flex items-center gap-2"><input type="checkbox" id="editIsPublic" checked={editingCategory.is_public} onChange={(e) => setEditingCategory({ ...editingCategory, is_public: e.target.checked })} className="rounded bg-cockpit border-hud-orange/30" /><label htmlFor="editIsPublic" className="text-sm text-hud-green font-mono">Make public</label></div>
                <div className="flex gap-4">
                  <button type="button" onClick={() => { setShowEdit(false); setEditingCategory(null); }} className="flex-1 px-4 py-2 border border-hud-green/30 text-hud-green font-mono rounded hover:bg-hud-green/10">CANCEL</button>
                  <button type="submit" disabled={updating} className="flex-1 px-4 py-2 bg-hud-orange/20 border border-hud-orange text-hud-orange font-mono rounded hover:bg-hud-orange/30 disabled:opacity-50">{updating ? <Loader2 className="w-5 h-5 animate-spin mx-auto" /> : "UPDATE"}</button>
                </div>
              </form>
            </HUDFrame>
          </div>
        )}

        {/* Categories List */}
        {loading ? (<div className="flex justify-center py-12"><Loader2 className="w-8 h-8 animate-spin text-hud-cyan" /></div>
        ) : categories.length === 0 ? (
          <HUDFrame title="NO CATEGORIES" className="bg-cockpit-dark/80 border border-hud-cyan/30 rounded-lg text-center py-12">
            <FolderTree className="w-16 h-16 text-hud-cyan/30 mx-auto mb-4" />
            <p className="text-hud-green font-mono mb-4">CREATE YOUR FIRST CATEGORY TO BEGIN</p>
            <button onClick={() => setShowCreate(true)} className="px-6 py-3 bg-hud-cyan/20 border border-hud-cyan text-hud-cyan font-mono rounded hover:bg-hud-cyan/30">CREATE CATEGORY</button>
          </HUDFrame>
        ) : (
          <div className="space-y-3">
            {categories.map((cat) => (
              <div key={cat.id} className="bg-cockpit-dark p-4 rounded border border-hud-green/20 hover:border-hud-cyan/50 transition-colors">
                <div className="flex items-start justify-between">
                  <div className="flex-1 min-w-0">
                    <h3 className="text-hud-cyan font-mono font-bold">{cat.name}</h3>
                    <p className="text-hud-green/60 text-xs font-mono mt-1 break-all">{cat.protocol_string}</p>
                    <span className={`inline-block mt-2 px-2 py-0.5 text-xs rounded font-mono ${cat.is_public ? "bg-hud-green/20 text-hud-green" : "bg-hud-orange/20 text-hud-orange"}`}>{cat.is_public ? "PUBLIC" : "PRIVATE"}</span>
                  </div>
                  <div className="flex items-center gap-1 ml-2">
                    <button onClick={() => handleEdit(cat)} className="p-2 text-hud-cyan/60 hover:text-hud-cyan rounded hover:bg-hud-cyan/10" title="Edit"><Edit3 className="w-4 h-4" /></button>
                    <button onClick={() => handleDelete(cat.id)} className="p-2 text-hud-red/60 hover:text-hud-red rounded hover:bg-hud-red/10" title="Delete"><Trash2 className="w-4 h-4" /></button>
                  </div>
                </div>
              </div>
            ))}
          </div>
        )}

        <BookSalesBanner variant="compact" />
      </div>
    </Layout>
  );
};

// Ultimate Search, Statistics, Global Database - Simplified versions with promos
const UltimateSearchPage = () => {
  const navigate = useNavigate();
  return (
    <Layout>
      <div className="max-w-6xl mx-auto space-y-6">
        <h1 className="text-3xl font-bold text-hud-green font-mono tracking-wider">ULTIMATE SEARCH</h1>
        <SubscriptionSalesBanner onUpgrade={() => navigate("/subscribe")} />
        <HUDFrame title="ADVANCED FILTERS" className="bg-cockpit-dark/80 border border-hud-cyan/30 rounded-lg">
          <p className="text-hud-cyan font-mono">Search through your collated results with advanced filtering options.</p>
          <button onClick={() => navigate("/infopilot")} className="mt-4 px-6 py-2 bg-hud-cyan/20 border border-hud-cyan text-hud-cyan font-mono rounded">START SEARCHING</button>
        </HUDFrame>
        <BookSalesBanner variant="compact" />
      </div>
    </Layout>
  );
};

const StatisticsPage = () => {
  const navigate = useNavigate();
  return (
    <Layout>
      <div className="max-w-6xl mx-auto space-y-6">
        <h1 className="text-3xl font-bold text-hud-green font-mono tracking-wider">INTEL STATISTICS</h1>
        <SubscriptionSalesBanner onUpgrade={() => navigate("/subscribe")} />
        <HUDFrame title="ANALYTICS" className="bg-cockpit-dark/80 border border-hud-cyan/30 rounded-lg text-center py-12">
          <BarChart3 className="w-16 h-16 text-hud-cyan/30 mx-auto mb-4" />
          <p className="text-hud-green font-mono">Collate data to view detailed statistics and insights.</p>
        </HUDFrame>
        <BookSalesBanner variant="full" />
      </div>
    </Layout>
  );
};

const GlobalDatabasePage = () => {
  const navigate = useNavigate();
  return (
    <Layout>
      <div className="max-w-6xl mx-auto space-y-6">
        <h1 className="text-3xl font-bold text-hud-green font-mono tracking-wider">GLOBAL DATABASE</h1>
        <SubscriptionSalesBanner onUpgrade={() => navigate("/subscribe")} />
        <HUDFrame title="PUBLIC CATEGORIES" className="bg-cockpit-dark/80 border border-hud-cyan/30 rounded-lg text-center py-12">
          <Globe className="w-16 h-16 text-hud-cyan/30 mx-auto mb-4" />
          <p className="text-hud-green font-mono">Access public categories from pilots worldwide.</p>
        </HUDFrame>
        <BookSalesBanner variant="compact" />
      </div>
    </Layout>
  );
};

// Book Page - FULL SALES PAGE
const BookPage = () => {
  return (
    <Layout>
      <div className="max-w-4xl mx-auto space-y-8">
        {/* Hero Section */}
        <div className="relative rounded-xl overflow-hidden">
          <img src={IMAGES.bookCover1} alt="Letters to Evelyn" className="w-full h-64 md:h-96 object-cover" />
          <div className="absolute inset-0 bg-gradient-to-t from-cockpit via-cockpit/50 to-transparent"></div>
          <div className="absolute bottom-0 left-0 right-0 p-6">
            <h1 className="text-4xl md:text-5xl font-bold text-transparent bg-clip-text bg-gradient-to-r from-purple-400 to-pink-400 font-mono mb-2">LETTERS TO EVELYN</h1>
            <p className="text-xl text-hud-cyan font-mono">{BOOK_INFO.genre}</p>
          </div>
        </div>

        {/* Rating Banner */}
        <div className="flex items-center justify-center gap-4 p-4 bg-yellow-500/20 rounded-lg border border-yellow-500">
          <div className="flex">{[...Array(5)].map((_, i) => <Star key={i} className="w-8 h-8 fill-yellow-400 text-yellow-400" />)}</div>
          <span className="text-2xl font-bold text-yellow-400 font-mono">19 FIVE-STAR REVIEWS</span>
        </div>

        {/* Author Section */}
        <HUDFrame title="ABOUT THE AUTHOR" className="bg-cockpit-dark/80 border border-purple-500/30 rounded-lg">
          <div className="flex flex-col md:flex-row gap-6 items-center">
            <img src={IMAGES.author} alt="John Selman" className="w-32 h-32 rounded-full border-4 border-purple-500 object-cover" />
            <div>
              <h2 className="text-2xl font-bold text-hud-orange font-mono">John Selman</h2>
              <p className="text-hud-cyan font-mono mb-2">World Record Aviation Holder • U.S. Navy Pilot • Author</p>
              <p className="text-hud-green/80 font-mono text-sm italic">"{BOOK_INFO.tagline}"</p>
            </div>
          </div>
        </HUDFrame>

        {/* Reviews */}
        <HUDFrame title="CRITICAL ACCLAIM" color="orange" className="bg-cockpit-dark/80 border border-hud-orange/30 rounded-lg">
          <div className="space-y-4">
            {BOOK_INFO.quotes.map((quote, idx) => (
              <div key={idx} className="bg-cockpit p-4 rounded border-l-4 border-purple-500">
                <p className="text-hud-green/90 font-mono text-sm italic">"{quote.text}"</p>
                <p className="text-purple-400 font-mono text-xs mt-2">— {quote.author}</p>
              </div>
            ))}
          </div>
        </HUDFrame>

        {/* Purchase Links */}
        <HUDFrame title="GET YOUR COPY" color="green" className="bg-cockpit-dark/80 border border-hud-green/30 rounded-lg">
          <div className="grid md:grid-cols-2 gap-4">
            <a href={BOOK_INFO.amazonUrl} target="_blank" rel="noopener noreferrer" className="flex items-center gap-3 px-6 py-4 bg-gradient-to-r from-yellow-500 to-orange-500 text-black font-bold font-mono rounded-lg hover:scale-105 transition-transform">
              <ShoppingCart className="w-6 h-6" /> BUY ON AMAZON
            </a>
            <a href={BOOK_INFO.officialUrl} target="_blank" rel="noopener noreferrer" className="flex items-center gap-3 px-6 py-4 bg-purple-600 text-white font-mono rounded-lg hover:bg-purple-500 transition-colors">
              <ExternalLink className="w-6 h-6" /> OFFICIAL WEBSITE
            </a>
            <a href={BOOK_INFO.sintraUrl} target="_blank" rel="noopener noreferrer" className="flex items-center gap-3 px-6 py-4 border border-purple-500 text-purple-400 font-mono rounded-lg hover:bg-purple-500/20 transition-colors">
              <Globe className="w-6 h-6" /> SINTRA SITE
            </a>
            <a href={BOOK_INFO.readersFavoriteUrl} target="_blank" rel="noopener noreferrer" className="flex items-center gap-3 px-6 py-4 border border-yellow-500 text-yellow-400 font-mono rounded-lg hover:bg-yellow-500/20 transition-colors">
              <Star className="w-6 h-6" /> READ ALL REVIEWS
            </a>
            <a href={BOOK_INFO.googleDriveUrl} target="_blank" rel="noopener noreferrer" className="flex items-center gap-3 px-6 py-4 border border-hud-cyan text-hud-cyan font-mono rounded-lg hover:bg-hud-cyan/20 transition-colors md:col-span-2">
              <BookOpen className="w-6 h-6" /> PREVIEW ON GOOGLE DRIVE
            </a>
          </div>
        </HUDFrame>
      </div>
    </Layout>
  );
};

// Subscribe Page - FIXED & SALES FOCUSED
const SubscribePage = () => {
  const { user, refreshUser } = useAuth();
  const [processing, setProcessing] = useState(false);
  const [selectedMethod, setSelectedMethod] = useState("paypal");
  const navigate = useNavigate();

  const handlePayment = async () => {
    setProcessing(true);
    try {
      const response = await axios.post(`${API}/payments/process`, {
        payment_method: selectedMethod,
        item_type: "subscription",
        amount: SUBSCRIPTION_PRICE
      });
      
      if (response.data.success) {
        toast.success("🎉 PAYMENT SUCCESSFUL! Welcome to Premium!");
        await refreshUser();
        setTimeout(() => navigate("/"), 2000);
      } else {
        toast.error("Payment failed. Please try again.");
      }
    } catch (error) {
      toast.error(error.response?.data?.detail || "PAYMENT FAILED");
    } finally {
      setProcessing(false);
    }
  };

  if (user?.is_paid) {
    return (
      <Layout>
        <div className="max-w-lg mx-auto space-y-6">
          <HUDFrame title="LIFETIME ACCESS ACTIVE" color="green" className="bg-cockpit-dark/80 border border-hud-green/30 rounded-lg text-center py-12">
            <Crown className="w-20 h-20 text-hud-green mx-auto mb-4" />
            <h2 className="text-2xl font-bold text-hud-green font-mono mb-2">🎉 YOU'RE A PREMIUM MEMBER!</h2>
            <p className="text-hud-cyan/80 font-mono text-sm">Enjoy unlimited access to all InfoPilot features forever.</p>
            <button onClick={() => navigate("/")} className="mt-6 px-6 py-3 bg-hud-cyan/20 border border-hud-cyan text-hud-cyan font-mono rounded">GO TO COMMAND CENTER</button>
          </HUDFrame>
          <BookSalesBanner variant="full" />
        </div>
      </Layout>
    );
  }

  return (
    <Layout>
      <div className="max-w-lg mx-auto space-y-6">
        {/* MEGA Price Banner */}
        <div className="text-center p-8 bg-gradient-to-r from-hud-orange/30 via-hud-red/30 to-hud-orange/30 rounded-xl border-2 border-hud-orange animate-pulse">
          <div className="flex items-center justify-center gap-2 mb-4">
            <Crown className="w-10 h-10 text-hud-orange" />
            <Sparkles className="w-6 h-6 text-yellow-400 animate-bounce" />
          </div>
          <div className="text-6xl font-bold text-hud-orange font-mono mb-2">$0.90</div>
          <div className="flex items-center justify-center gap-2 mb-2">
            <span className="text-hud-green/50 font-mono line-through">$9.99</span>
            <span className="bg-hud-red text-white px-3 py-1 rounded-full text-sm font-bold animate-pulse">SAVE 91%!</span>
          </div>
          <p className="text-hud-cyan font-mono text-lg">LIFETIME PREMIUM ACCESS</p>
          <p className="text-hud-green/60 font-mono text-sm">One payment. Forever access. No subscriptions.</p>
        </div>

        {/* Features */}
        <HUDFrame title="PREMIUM FEATURES" className="bg-cockpit-dark/80 border border-hud-cyan/30 rounded-lg">
          <div className="space-y-3">
            {[
              { icon: Unlock, text: "Unlimited search results pages" },
              { icon: FolderTree, text: "Unlimited categories & protocols" },
              { icon: BarChart3, text: "Advanced statistics & analytics" },
              { icon: Globe, text: "Full Global Research Database access" },
              { icon: Zap, text: "Priority search performance" },
              { icon: Crown, text: "Lifetime access - no recurring fees" }
            ].map((feature, idx) => (
              <div key={idx} className="flex items-center gap-3 text-hud-green font-mono text-sm">
                <feature.icon className="w-5 h-5 text-hud-cyan" />
                <span>{feature.text}</span>
                <Check className="w-4 h-4 text-hud-green ml-auto" />
              </div>
            ))}
          </div>
        </HUDFrame>

        {/* Payment Methods */}
        <HUDFrame title="SELECT PAYMENT METHOD" color="orange" className="bg-cockpit-dark/80 border border-hud-orange/30 rounded-lg">
          <div className="space-y-3 mb-6">
            {[
              { id: "paypal", label: "PayPal", icon: "💳" },
              { id: "google_pay", label: "Google Pay", icon: "🔵" },
              { id: "shopify", label: "Credit Card (Shopify)", icon: "💳" }
            ].map((method) => (
              <label key={method.id} className={`flex items-center gap-3 p-4 rounded-lg cursor-pointer transition-colors ${selectedMethod === method.id ? "bg-hud-orange/20 border-2 border-hud-orange" : "bg-cockpit border border-hud-green/20 hover:border-hud-cyan/50"}`}>
                <input type="radio" name="payment" value={method.id} checked={selectedMethod === method.id} onChange={(e) => setSelectedMethod(e.target.value)} className="hidden" />
                <span className="text-2xl">{method.icon}</span>
                <span className="text-hud-green font-mono">{method.label}</span>
                {selectedMethod === method.id && <Check className="w-5 h-5 text-hud-orange ml-auto" />}
              </label>
            ))}
          </div>

          <button
            onClick={handlePayment}
            disabled={processing}
            className="w-full py-4 bg-gradient-to-r from-hud-orange to-hud-red text-white font-bold font-mono tracking-wider rounded-lg hover:scale-[1.02] transition-transform disabled:opacity-50 flex items-center justify-center gap-2 text-lg"
            data-testid="process-payment-btn"
          >
            {processing ? <Loader2 className="w-6 h-6 animate-spin" /> : <><CreditCard className="w-6 h-6" /> PAY $0.90 - GET LIFETIME ACCESS</>}
          </button>

          <p className="text-center text-hud-cyan/60 text-xs font-mono mt-4">🔒 Secure payment • Sandbox mode for testing</p>
        </HUDFrame>

        {/* Book Promo */}
        <BookSalesBanner variant="full" />
      </div>
    </Layout>
  );
};

// Admin Page
const AdminPage = () => {
  const { user } = useAuth();
  if (!user?.is_admin) {
    return (<Layout><div className="text-center py-12"><Shield className="w-16 h-16 text-hud-red/50 mx-auto mb-4" /><h1 className="text-2xl font-bold text-hud-red font-mono">ACCESS DENIED</h1></div></Layout>);
  }
  return (
    <Layout>
      <div className="max-w-4xl mx-auto">
        <h1 className="text-3xl font-bold text-hud-green font-mono tracking-wider mb-6">ADMIN CONTROL</h1>
        <HUDFrame title="SYSTEM STATUS" className="bg-cockpit-dark/80 border border-hud-cyan/30 rounded-lg">
          <p className="text-hud-green font-mono">Admin dashboard for system management.</p>
        </HUDFrame>
      </div>
    </Layout>
  );
};

// Main App
function App() {
  return (
    <GoogleOAuthProvider clientId={GOOGLE_CLIENT_ID}>
      <AuthProvider>
        <Toaster position="top-right" toastOptions={{ style: { background: '#0a0a0a', border: '1px solid #00ffff', color: '#00ff88', fontFamily: 'monospace' } }} />
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
    </GoogleOAuthProvider>
  );
}

export default App;
