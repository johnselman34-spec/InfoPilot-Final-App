import React, { useState, useEffect, createContext, useContext, useCallback } from "react";
import { BrowserRouter, Routes, Route, Navigate, useNavigate, useLocation } from "react-router-dom";
import axios from "axios";
import { Toaster, toast } from "sonner";
import {
  Search, Globe, FolderTree, BarChart3, Settings, LogOut, User, Plus, Trash2,
  Eye, EyeOff, ChevronDown, ChevronRight, Filter, Heart, ThumbsUp, Smile,
  Frown, AlertTriangle, Flag, Award, Home, Users, BookOpen, Menu, X, Loader2
} from "lucide-react";
import {
  PieChart, Pie, Cell, BarChart, Bar, XAxis, YAxis, CartesianGrid, Tooltip,
  Legend, ResponsiveContainer
} from "recharts";
import "@/App.css";

const BACKEND_URL = process.env.REACT_APP_BACKEND_URL;
const API = `${BACKEND_URL}/api`;

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

  const logout = () => {
    localStorage.removeItem("token");
    setToken(null);
    setUser(null);
    delete axios.defaults.headers.common["Authorization"];
  };

  return (
    <AuthContext.Provider value={{ user, token, login, register, logout, loading }}>
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
  <div className="min-h-screen bg-cream flex items-center justify-center">
    <div className="text-center">
      <Loader2 className="w-12 h-12 animate-spin text-infojet-blue mx-auto" />
      <p className="mt-4 text-gray-600">Loading InfoJet...</p>
    </div>
  </div>
);

// Sidebar Navigation
const Sidebar = ({ isOpen, setIsOpen }) => {
  const { user, logout } = useAuth();
  const navigate = useNavigate();
  const location = useLocation();

  const menuItems = [
    { path: "/", icon: Home, label: "Home" },
    { path: "/infojet", icon: Search, label: "InfoJet Search" },
    { path: "/ultimate-search", icon: Globe, label: "Ultimate Search" },
    { path: "/categories", icon: FolderTree, label: "My Categories" },
    { path: "/statistics", icon: BarChart3, label: "Statistics" },
    { path: "/global-database", icon: Users, label: "Global Database" },
  ];

  if (user?.is_admin) {
    menuItems.push({ path: "/admin", icon: Settings, label: "Admin Panel" });
  }

  return (
    <>
      {/* Mobile overlay */}
      {isOpen && (
        <div
          className="fixed inset-0 bg-black/50 z-40 lg:hidden"
          onClick={() => setIsOpen(false)}
        />
      )}

      {/* Sidebar */}
      <aside
        className={`fixed top-0 left-0 h-full bg-white shadow-xl z-50 transition-transform duration-300 w-64
          ${isOpen ? "translate-x-0" : "-translate-x-full lg:translate-x-0"}`}
      >
        <div className="p-6 border-b border-gray-200">
          <div className="flex items-center justify-between">
            <div className="flex items-center gap-3">
              <div className="w-10 h-10 bg-gradient-to-br from-infojet-blue to-infojet-green rounded-lg flex items-center justify-center">
                <Globe className="w-6 h-6 text-white" />
              </div>
              <div>
                <h1 className="text-xl font-bold text-gray-800">InfoJet</h1>
                <p className="text-xs text-gray-500">Information Exchange</p>
              </div>
            </div>
            <button className="lg:hidden" onClick={() => setIsOpen(false)}>
              <X className="w-6 h-6" />
            </button>
          </div>
        </div>

        <nav className="p-4 space-y-2">
          {menuItems.map((item) => (
            <button
              key={item.path}
              onClick={() => {
                navigate(item.path);
                setIsOpen(false);
              }}
              className={`w-full flex items-center gap-3 px-4 py-3 rounded-lg transition-all
                ${location.pathname === item.path
                  ? "bg-infojet-blue text-white shadow-md"
                  : "text-gray-600 hover:bg-gray-100"
                }`}
            >
              <item.icon className="w-5 h-5" />
              <span className="font-medium">{item.label}</span>
            </button>
          ))}
        </nav>

        <div className="absolute bottom-0 left-0 right-0 p-4 border-t border-gray-200 bg-white">
          <div className="flex items-center gap-3 mb-4">
            <div className="w-10 h-10 bg-infojet-green rounded-full flex items-center justify-center text-white font-bold">
              {user?.username?.[0]?.toUpperCase() || "U"}
            </div>
            <div className="flex-1 min-w-0">
              <p className="font-medium text-gray-800 truncate">{user?.username}</p>
              <p className="text-xs text-gray-500 truncate">{user?.email}</p>
              {user?.is_paid && (
                <span className="inline-block px-2 py-0.5 bg-infojet-green/10 text-infojet-green text-xs rounded-full">
                  Premium
                </span>
              )}
            </div>
          </div>
          <button
            onClick={logout}
            className="w-full flex items-center justify-center gap-2 px-4 py-2 text-red-600 hover:bg-red-50 rounded-lg transition-colors"
          >
            <LogOut className="w-4 h-4" />
            <span>Logout</span>
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
    <div className="min-h-screen bg-cream">
      <Sidebar isOpen={sidebarOpen} setIsOpen={setSidebarOpen} />

      {/* Mobile header */}
      <header className="lg:hidden fixed top-0 left-0 right-0 h-16 bg-white shadow-sm z-30 flex items-center px-4">
        <button onClick={() => setSidebarOpen(true)} className="p-2">
          <Menu className="w-6 h-6" />
        </button>
        <div className="flex items-center gap-2 ml-4">
          <Globe className="w-6 h-6 text-infojet-blue" />
          <span className="font-bold text-lg">InfoJet</span>
        </div>
      </header>

      {/* Main content */}
      <main className="lg:ml-64 pt-16 lg:pt-0 min-h-screen">
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
  const { login, register, user } = useAuth();
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
      toast.success(isLogin ? "Welcome back!" : "Account created successfully!");
      navigate("/");
    } catch (error) {
      toast.error(error.response?.data?.detail || "An error occurred");
    } finally {
      setLoading(false);
    }
  };

  return (
    <div className="min-h-screen bg-gradient-to-br from-cream via-white to-infojet-blue/10 flex items-center justify-center p-4">
      <div className="w-full max-w-md">
        <div className="text-center mb-8">
          <div className="inline-flex items-center justify-center w-16 h-16 bg-gradient-to-br from-infojet-blue to-infojet-green rounded-2xl shadow-lg mb-4">
            <Globe className="w-10 h-10 text-white" />
          </div>
          <h1 className="text-3xl font-bold text-gray-800">InfoJet</h1>
          <p className="text-gray-600 mt-2">World Wide Web Information Exchange</p>
        </div>

        <div className="bg-white rounded-2xl shadow-xl p-8">
          <div className="flex mb-6">
            <button
              onClick={() => setIsLogin(true)}
              className={`flex-1 py-3 text-center font-medium rounded-l-lg transition-colors
                ${isLogin ? "bg-infojet-blue text-white" : "bg-gray-100 text-gray-600"}`}
            >
              Login
            </button>
            <button
              onClick={() => setIsLogin(false)}
              className={`flex-1 py-3 text-center font-medium rounded-r-lg transition-colors
                ${!isLogin ? "bg-infojet-blue text-white" : "bg-gray-100 text-gray-600"}`}
            >
              Register
            </button>
          </div>

          <form onSubmit={handleSubmit} className="space-y-4">
            {!isLogin && (
              <div>
                <label className="block text-sm font-medium text-gray-700 mb-1">Username</label>
                <input
                  type="text"
                  value={username}
                  onChange={(e) => setUsername(e.target.value)}
                  className="w-full px-4 py-3 border border-gray-300 rounded-lg focus:ring-2 focus:ring-infojet-blue focus:border-transparent"
                  required={!isLogin}
                  data-testid="username-input"
                />
              </div>
            )}
            <div>
              <label className="block text-sm font-medium text-gray-700 mb-1">Email</label>
              <input
                type="email"
                value={email}
                onChange={(e) => setEmail(e.target.value)}
                className="w-full px-4 py-3 border border-gray-300 rounded-lg focus:ring-2 focus:ring-infojet-blue focus:border-transparent"
                required
                data-testid="email-input"
              />
            </div>
            <div>
              <label className="block text-sm font-medium text-gray-700 mb-1">Password</label>
              <input
                type="password"
                value={password}
                onChange={(e) => setPassword(e.target.value)}
                className="w-full px-4 py-3 border border-gray-300 rounded-lg focus:ring-2 focus:ring-infojet-blue focus:border-transparent"
                required
                data-testid="password-input"
              />
            </div>
            <button
              type="submit"
              disabled={loading}
              className="w-full py-3 bg-gradient-to-r from-infojet-blue to-infojet-green text-white font-medium rounded-lg hover:shadow-lg transition-all disabled:opacity-50"
              data-testid="submit-btn"
            >
              {loading ? <Loader2 className="w-5 h-5 animate-spin mx-auto" /> : isLogin ? "Login" : "Create Account"}
            </button>
          </form>

          <div className="mt-6 text-center text-sm text-gray-600">
            <p>Subscribe for just <span className="font-bold text-infojet-green">$0.99</span> to unlock all features!</p>
          </div>
        </div>
      </div>
    </div>
  );
};

// Home Page
const HomePage = () => {
  const { user } = useAuth();
  const navigate = useNavigate();

  return (
    <Layout>
      <div className="max-w-4xl mx-auto">
        {/* Welcome Banner */}
        <div className="bg-gradient-to-r from-infojet-blue to-infojet-green rounded-2xl p-8 text-white mb-8">
          <h1 className="text-3xl font-bold mb-2">Welcome to InfoJet, {user?.username}!</h1>
          <p className="text-white/80 mb-6">
            Your personal gateway to the World Wide Web Information Exchange. 
            Create categories, write protocols, and collate information from across the internet.
          </p>
          <button
            onClick={() => navigate("/infojet")}
            className="px-6 py-3 bg-white text-infojet-blue font-medium rounded-lg hover:shadow-lg transition-all"
            data-testid="start-searching-btn"
          >
            Start Searching
          </button>
        </div>

        {/* Quick Stats */}
        <div className="grid md:grid-cols-3 gap-4 mb-8">
          <QuickStatCard title="Create Categories" icon={FolderTree} onClick={() => navigate("/categories")} />
          <QuickStatCard title="Search & Collate" icon={Search} onClick={() => navigate("/infojet")} />
          <QuickStatCard title="View Statistics" icon={BarChart3} onClick={() => navigate("/statistics")} />
        </div>

        {/* InfoJet 2.0 Guide */}
        <div className="bg-white rounded-2xl shadow-lg p-8">
          <h2 className="text-2xl font-bold text-gray-800 mb-4 flex items-center gap-2">
            <BookOpen className="w-6 h-6 text-infojet-blue" />
            InfoJet 2.0 Protocol Guide
          </h2>
          <div className="prose max-w-none">
            <p className="text-gray-600 mb-4">
              InfoJet 2.0 is a powerful Boolean search language that lets you precisely define what information you're looking for.
            </p>

            <h3 className="text-lg font-semibold text-gray-800 mt-6 mb-3">Syntax Rules:</h3>
            <ul className="space-y-2 text-gray-600">
              <li><code className="bg-gray-100 px-2 py-1 rounded">(word1 or word2)</code> - Match ANY word in the group</li>
              <li><code className="bg-gray-100 px-2 py-1 rounded">&</code> - AND operator between groups</li>
              <li><code className="bg-gray-100 px-2 py-1 rounded">+</code> - INCLUDE ALL words (all must be present)</li>
              <li><code className="bg-gray-100 px-2 py-1 rounded">^</code> - EXCLUDE ALL words (none should be present)</li>
            </ul>

            <h3 className="text-lg font-semibold text-gray-800 mt-6 mb-3">Examples:</h3>
            <div className="space-y-4">
              <div className="bg-cream rounded-lg p-4">
                <p className="font-medium text-gray-800">American Civil War Category:</p>
                <code className="text-sm text-infojet-blue block mt-2">
                  (American civil war or civil war) & (1860 or 1861 or 1862 or 1863 or 1864 or 1865)+
                </code>
              </div>
              <div className="bg-cream rounded-lg p-4">
                <p className="font-medium text-gray-800">Heroes Subcategory:</p>
                <code className="text-sm text-infojet-blue block mt-2">
                  (hero or heroes or heroic) & (civil war) & (villain or enemy)^
                </code>
              </div>
            </div>
          </div>
        </div>
      </div>
    </Layout>
  );
};

const QuickStatCard = ({ title, icon: Icon, onClick }) => (
  <button
    onClick={onClick}
    className="bg-white rounded-xl p-6 shadow-lg hover:shadow-xl transition-all text-left group"
    data-testid={`quick-stat-${title.toLowerCase().replace(/\s/g, '-')}`}
  >
    <div className="w-12 h-12 bg-infojet-blue/10 rounded-lg flex items-center justify-center mb-4 group-hover:bg-infojet-blue group-hover:text-white transition-colors">
      <Icon className="w-6 h-6 text-infojet-blue group-hover:text-white" />
    </div>
    <h3 className="font-semibold text-gray-800">{title}</h3>
  </button>
);

// InfoJet Search Page
const InfoJetPage = () => {
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
      toast.error("Please enter a search query");
      return;
    }

    if (categories.length === 0) {
      toast.error("Please create at least one category with a protocol first");
      return;
    }

    setLoading(true);
    try {
      const res = await axios.post(`${API}/search/collate`, {
        search_query: searchQuery,
        max_results: 20
      });
      setResults(res.data);
      toast.success(`Collated ${res.data.categorized_count} results!`);
    } catch (error) {
      toast.error(error.response?.data?.detail || "Search failed");
    } finally {
      setLoading(false);
    }
  };

  return (
    <Layout>
      <div className="max-w-4xl mx-auto">
        <div className="mb-8">
          <h1 className="text-3xl font-bold text-gray-800 mb-2">InfoJet Search</h1>
          <p className="text-gray-600">Search the web and automatically categorize results using your protocols.</p>
        </div>

        {/* Search Modifiers Reference */}
        <div className="bg-white rounded-xl shadow-lg p-6 mb-6">
          <h3 className="font-semibold text-gray-800 mb-3 flex items-center gap-2">
            <BookOpen className="w-5 h-5 text-infojet-blue" />
            Google Search Modifiers
          </h3>
          <div className="grid md:grid-cols-2 gap-2 text-sm text-gray-600">
            <div><code className="bg-gray-100 px-2 py-0.5 rounded">site:example.com</code> - Search within a site</div>
            <div><code className="bg-gray-100 px-2 py-0.5 rounded">"exact phrase"</code> - Exact match</div>
            <div><code className="bg-gray-100 px-2 py-0.5 rounded">-word</code> - Exclude word</div>
            <div><code className="bg-gray-100 px-2 py-0.5 rounded">filetype:pdf</code> - Specific file type</div>
            <div><code className="bg-gray-100 px-2 py-0.5 rounded">intitle:word</code> - Word in title</div>
            <div><code className="bg-gray-100 px-2 py-0.5 rounded">inurl:word</code> - Word in URL</div>
          </div>
        </div>

        {/* Search Box */}
        <div className="bg-white rounded-2xl shadow-lg p-6 mb-6">
          <div className="flex gap-4">
            <div className="flex-1">
              <input
                type="text"
                value={searchQuery}
                onChange={(e) => setSearchQuery(e.target.value)}
                placeholder="Enter your search query..."
                className="w-full px-4 py-3 border border-gray-300 rounded-lg focus:ring-2 focus:ring-infojet-blue focus:border-transparent"
                onKeyPress={(e) => e.key === "Enter" && handleCollate()}
                data-testid="search-input"
              />
            </div>
            <button
              onClick={handleCollate}
              disabled={loading}
              className="px-6 py-3 bg-gradient-to-r from-infojet-blue to-infojet-green text-white font-medium rounded-lg hover:shadow-lg transition-all disabled:opacity-50 flex items-center gap-2"
              data-testid="collate-btn"
            >
              {loading ? <Loader2 className="w-5 h-5 animate-spin" /> : <Search className="w-5 h-5" />}
              Collate
            </button>
          </div>

          {categories.length === 0 && (
            <div className="mt-4 p-4 bg-yellow-50 border border-yellow-200 rounded-lg text-yellow-800">
              <p>You need to create at least one category with a protocol before searching.</p>
              <a href="/categories" className="text-infojet-blue underline">Create a category →</a>
            </div>
          )}

          {categories.length > 0 && (
            <div className="mt-4">
              <p className="text-sm text-gray-500 mb-2">Your active categories ({categories.length}):</p>
              <div className="flex flex-wrap gap-2">
                {categories.slice(0, 5).map((cat) => (
                  <span key={cat.id} className="px-3 py-1 bg-infojet-blue/10 text-infojet-blue rounded-full text-sm">
                    {cat.name}
                  </span>
                ))}
                {categories.length > 5 && (
                  <span className="px-3 py-1 bg-gray-100 text-gray-600 rounded-full text-sm">
                    +{categories.length - 5} more
                  </span>
                )}
              </div>
            </div>
          )}
        </div>

        {/* Results */}
        {results && (
          <div className="bg-white rounded-2xl shadow-lg p-6">
            <h3 className="font-semibold text-gray-800 mb-4">
              Collated Results ({results.categorized_count} of {results.total_searched} categorized)
            </h3>
            {results.results.length > 0 ? (
              <div className="space-y-4">
                {results.results.map((result) => (
                  <SearchResultCard key={result.id} result={result} />
                ))}
              </div>
            ) : (
              <p className="text-gray-500 text-center py-8">No results matched your protocols.</p>
            )}
          </div>
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
    try {
      await axios.post(`${API}/results/${result.id}/react`, { reaction_type: type });
      toast.success("Reaction added!");
    } catch (error) {
      toast.error("Failed to add reaction");
    } finally {
      setReacting(false);
    }
  };

  const reactions = [
    { type: "like", icon: ThumbsUp, label: "Like" },
    { type: "love", icon: Heart, label: "Love" },
    { type: "funny", icon: Smile, label: "Funny" },
    { type: "sad", icon: Frown, label: "Sad" },
    { type: "caution", icon: AlertTriangle, label: "Caution" },
    { type: "spam", icon: Flag, label: "Spam" },
    { type: "best", icon: Award, label: "Best" },
  ];

  return (
    <div className="border border-gray-200 rounded-lg p-4 hover:shadow-md transition-shadow" data-testid={`result-${result.id}`}>
      <div className="flex items-start justify-between gap-4">
        <div className="flex-1 min-w-0">
          <a
            href={result.url}
            target="_blank"
            rel="noopener noreferrer"
            className="text-infojet-blue hover:underline font-medium block truncate"
          >
            {result.title}
          </a>
          <p className="text-sm text-gray-600 mt-1 line-clamp-2">{result.snippet}</p>
          <div className="flex flex-wrap gap-2 mt-2">
            <span className="px-2 py-0.5 bg-infojet-green/10 text-infojet-green text-xs rounded-full">
              {result.article_type}
            </span>
            <span className="px-2 py-0.5 bg-gray-100 text-gray-600 text-xs rounded-full">
              {result.domain}
            </span>
            {result.detected_year && (
              <span className="px-2 py-0.5 bg-gray-100 text-gray-600 text-xs rounded-full">
                {result.detected_year}
              </span>
            )}
          </div>
          {result.category_names && (
            <div className="flex flex-wrap gap-1 mt-2">
              {result.category_names.map((name, idx) => (
                <span key={idx} className="px-2 py-0.5 bg-infojet-blue/10 text-infojet-blue text-xs rounded-full">
                  {name}
                </span>
              ))}
            </div>
          )}
        </div>
      </div>

      {showReactions && (
        <div className="flex flex-wrap gap-2 mt-4 pt-4 border-t border-gray-100">
          {reactions.map(({ type, icon: Icon, label }) => (
            <button
              key={type}
              onClick={() => handleReaction(type)}
              disabled={reacting}
              className="flex items-center gap-1 px-3 py-1 text-sm text-gray-600 hover:bg-gray-100 rounded-full transition-colors"
              title={label}
            >
              <Icon className="w-4 h-4" />
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
      toast.error("Failed to fetch categories");
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
      toast.success("Category created!");
      setShowCreate(false);
      setNewCategory({ name: "", protocol: "", parentId: null, isPublic: true });
      fetchCategories();
    } catch (error) {
      toast.error(error.response?.data?.detail || "Failed to create category");
    } finally {
      setCreating(false);
    }
  };

  const handleDelete = async (id) => {
    if (!window.confirm("Delete this category?")) return;
    try {
      await axios.delete(`${API}/categories/${id}`);
      toast.success("Category deleted");
      fetchCategories();
    } catch (error) {
      toast.error("Failed to delete category");
    }
  };

  const toggleVisibility = async (id, currentVisibility) => {
    try {
      await axios.put(`${API}/categories/${id}/visibility?is_public=${!currentVisibility}`);
      toast.success("Visibility updated");
      fetchCategories();
    } catch (error) {
      toast.error("Failed to update visibility");
    }
  };

  const buildTree = (cats, parentId = null, level = 0) => {
    return cats
      .filter(c => c.parent_id === parentId)
      .map(cat => ({
        ...cat,
        level,
        children: buildTree(cats, cat.id, level + 1)
      }));
  };

  const categoryTree = buildTree(categories);

  return (
    <Layout>
      <div className="max-w-4xl mx-auto">
        <div className="flex items-center justify-between mb-8">
          <div>
            <h1 className="text-3xl font-bold text-gray-800 mb-2">My Categories</h1>
            <p className="text-gray-600">Create and manage your InfoJet 2.0 categories and protocols.</p>
          </div>
          <button
            onClick={() => setShowCreate(true)}
            className="px-4 py-2 bg-infojet-blue text-white rounded-lg hover:bg-infojet-blue/90 transition-colors flex items-center gap-2"
            data-testid="create-category-btn"
          >
            <Plus className="w-5 h-5" />
            New Category
          </button>
        </div>

        {/* Create Category Modal */}
        {showCreate && (
          <div className="fixed inset-0 bg-black/50 flex items-center justify-center z-50 p-4">
            <div className="bg-white rounded-2xl shadow-xl max-w-lg w-full p-6">
              <h2 className="text-xl font-bold text-gray-800 mb-4">Create Category</h2>
              <form onSubmit={handleCreate} className="space-y-4">
                <div>
                  <label className="block text-sm font-medium text-gray-700 mb-1">Category Name</label>
                  <input
                    type="text"
                    value={newCategory.name}
                    onChange={(e) => setNewCategory({ ...newCategory, name: e.target.value })}
                    placeholder="e.g., American Civil War"
                    className="w-full px-4 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-infojet-blue"
                    required
                    data-testid="category-name-input"
                  />
                </div>
                <div>
                  <label className="block text-sm font-medium text-gray-700 mb-1">InfoJet 2.0 Protocol</label>
                  <textarea
                    value={newCategory.protocol}
                    onChange={(e) => setNewCategory({ ...newCategory, protocol: e.target.value })}
                    placeholder="(word1 or word2) & (word3)+ & (excluded)^"
                    className="w-full px-4 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-infojet-blue h-24"
                    required
                    data-testid="protocol-input"
                  />
                  <p className="text-xs text-gray-500 mt-1">
                    Use & for AND, "or" for OR, + for include all, ^ for exclude all
                  </p>
                </div>
                <div>
                  <label className="block text-sm font-medium text-gray-700 mb-1">Parent Category (optional)</label>
                  <select
                    value={newCategory.parentId || ""}
                    onChange={(e) => setNewCategory({ ...newCategory, parentId: e.target.value || null })}
                    className="w-full px-4 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-infojet-blue"
                    data-testid="parent-select"
                  >
                    <option value="">None (Main Category)</option>
                    {categories.map((cat) => (
                      <option key={cat.id} value={cat.id}>
                        {"—".repeat(cat.level)} {cat.name}
                      </option>
                    ))}
                  </select>
                </div>
                <div className="flex items-center gap-2">
                  <input
                    type="checkbox"
                    id="isPublic"
                    checked={newCategory.isPublic}
                    onChange={(e) => setNewCategory({ ...newCategory, isPublic: e.target.checked })}
                    className="rounded"
                    data-testid="public-checkbox"
                  />
                  <label htmlFor="isPublic" className="text-sm text-gray-700">Make this category public</label>
                </div>
                <div className="flex gap-4 pt-4">
                  <button
                    type="button"
                    onClick={() => setShowCreate(false)}
                    className="flex-1 px-4 py-2 border border-gray-300 text-gray-700 rounded-lg hover:bg-gray-50"
                  >
                    Cancel
                  </button>
                  <button
                    type="submit"
                    disabled={creating}
                    className="flex-1 px-4 py-2 bg-infojet-blue text-white rounded-lg hover:bg-infojet-blue/90 disabled:opacity-50"
                    data-testid="save-category-btn"
                  >
                    {creating ? <Loader2 className="w-5 h-5 animate-spin mx-auto" /> : "Create"}
                  </button>
                </div>
              </form>
            </div>
          </div>
        )}

        {/* Categories List */}
        {loading ? (
          <div className="flex justify-center py-12">
            <Loader2 className="w-8 h-8 animate-spin text-infojet-blue" />
          </div>
        ) : categories.length === 0 ? (
          <div className="bg-white rounded-2xl shadow-lg p-12 text-center">
            <FolderTree className="w-16 h-16 text-gray-300 mx-auto mb-4" />
            <h3 className="text-xl font-semibold text-gray-800 mb-2">No categories yet</h3>
            <p className="text-gray-600 mb-6">Create your first category to start organizing information.</p>
            <button
              onClick={() => setShowCreate(true)}
              className="px-6 py-3 bg-infojet-blue text-white rounded-lg hover:bg-infojet-blue/90"
            >
              Create First Category
            </button>
          </div>
        ) : (
          <div className="bg-white rounded-2xl shadow-lg p-6">
            <CategoryTree
              categories={categoryTree}
              onDelete={handleDelete}
              onToggleVisibility={toggleVisibility}
            />
          </div>
        )}
      </div>
    </Layout>
  );
};

const CategoryTree = ({ categories, onDelete, onToggleVisibility, level = 0 }) => {
  const [expanded, setExpanded] = useState({});

  const toggleExpand = (id) => {
    setExpanded((prev) => ({ ...prev, [id]: !prev[id] }));
  };

  return (
    <div className="space-y-2">
      {categories.map((cat) => (
        <div key={cat.id} style={{ marginLeft: level * 20 }}>
          <div className="flex items-center gap-2 p-3 bg-gray-50 rounded-lg hover:bg-gray-100 transition-colors">
            {cat.children?.length > 0 && (
              <button onClick={() => toggleExpand(cat.id)} className="p-1">
                {expanded[cat.id] ? (
                  <ChevronDown className="w-4 h-4 text-gray-500" />
                ) : (
                  <ChevronRight className="w-4 h-4 text-gray-500" />
                )}
              </button>
            )}
            {!cat.children?.length && <div className="w-6" />}

            <div className="flex-1">
              <div className="flex items-center gap-2">
                <span className="font-medium text-gray-800">{cat.name}</span>
                <span className={`px-2 py-0.5 text-xs rounded-full ${cat.is_public ? "bg-green-100 text-green-700" : "bg-gray-200 text-gray-600"}`}>
                  {cat.is_public ? "Public" : "Private"}
                </span>
              </div>
              <p className="text-xs text-gray-500 mt-1 font-mono truncate">{cat.protocol_string}</p>
            </div>

            <div className="flex items-center gap-2">
              <button
                onClick={() => onToggleVisibility(cat.id, cat.is_public)}
                className="p-2 text-gray-500 hover:text-infojet-blue rounded-lg hover:bg-white"
                title={cat.is_public ? "Make private" : "Make public"}
              >
                {cat.is_public ? <Eye className="w-4 h-4" /> : <EyeOff className="w-4 h-4" />}
              </button>
              <button
                onClick={() => onDelete(cat.id)}
                className="p-2 text-gray-500 hover:text-red-500 rounded-lg hover:bg-white"
                title="Delete"
              >
                <Trash2 className="w-4 h-4" />
              </button>
            </div>
          </div>

          {expanded[cat.id] && cat.children?.length > 0 && (
            <div className="mt-2">
              <CategoryTree
                categories={cat.children}
                onDelete={onDelete}
                onToggleVisibility={onToggleVisibility}
                level={level + 1}
              />
            </div>
          )}
        </div>
      ))}
    </div>
  );
};

// Ultimate Search Page
const UltimateSearchPage = () => {
  const [categories, setCategories] = useState([]);
  const [selectedCategories, setSelectedCategories] = useState([]);
  const [aggregationType, setAggregationType] = useState("and_or");
  const [articleTypes, setArticleTypes] = useState([]);
  const [selectedArticleTypes, setSelectedArticleTypes] = useState([]);
  const [domains, setDomains] = useState([]);
  const [selectedDomains, setSelectedDomains] = useState([]);
  const [keyword, setKeyword] = useState("");
  const [results, setResults] = useState(null);
  const [loading, setLoading] = useState(false);
  const [page, setPage] = useState(1);
  const { user } = useAuth();

  useEffect(() => {
    fetchCategories();
    fetchFilters();
  }, []);

  const fetchCategories = async () => {
    try {
      const res = await axios.get(`${API}/categories`);
      setCategories(res.data.filter(c => c.user_id === user?.id));
    } catch (error) {
      console.error("Failed to fetch categories");
    }
  };

  const fetchFilters = async () => {
    try {
      const res = await axios.get(`${API}/ultimate-search/filters`);
      setArticleTypes(res.data.article_types);
      setDomains(res.data.domains);
    } catch (error) {
      console.error("Failed to fetch filters");
    }
  };

  const handleSearch = async (newPage = 1) => {
    setLoading(true);
    try {
      const res = await axios.post(`${API}/ultimate-search`, {
        category_ids: selectedCategories,
        aggregation_type: aggregationType,
        article_types: selectedArticleTypes,
        domains: selectedDomains,
        keyword: keyword || null,
        page: newPage
      });
      setResults(res.data);
      setPage(newPage);
    } catch (error) {
      toast.error(error.response?.data?.detail || "Search failed");
    } finally {
      setLoading(false);
    }
  };

  const toggleCategory = (id) => {
    setSelectedCategories((prev) =>
      prev.includes(id) ? prev.filter((c) => c !== id) : [...prev, id]
    );
  };

  return (
    <Layout>
      <div className="max-w-6xl mx-auto">
        <div className="mb-8">
          <h1 className="text-3xl font-bold text-gray-800 mb-2">Ultimate Search</h1>
          <p className="text-gray-600">Search through your collated results with advanced filters.</p>
        </div>

        <div className="grid lg:grid-cols-4 gap-6">
          {/* Filters Sidebar */}
          <div className="lg:col-span-1 space-y-6">
            {/* Categories */}
            <div className="bg-white rounded-xl shadow-lg p-4">
              <h3 className="font-semibold text-gray-800 mb-3 flex items-center gap-2">
                <FolderTree className="w-5 h-5 text-infojet-blue" />
                Categories
              </h3>
              <div className="space-y-2 max-h-60 overflow-y-auto">
                {categories.map((cat) => (
                  <label key={cat.id} className="flex items-center gap-2 cursor-pointer">
                    <input
                      type="checkbox"
                      checked={selectedCategories.includes(cat.id)}
                      onChange={() => toggleCategory(cat.id)}
                      className="rounded text-infojet-blue"
                    />
                    <span className="text-sm text-gray-700">{cat.name}</span>
                  </label>
                ))}
              </div>
            </div>

            {/* Search Aggregation */}
            <div className="bg-white rounded-xl shadow-lg p-4">
              <h3 className="font-semibold text-gray-800 mb-3">Search Aggregation</h3>
              <div className="space-y-2">
                {[
                  { value: "and_or", label: "And/Or", desc: "All selected + possibly others" },
                  { value: "and", label: "And", desc: "Exactly selected categories only" },
                  { value: "or", label: "Or", desc: "Any of selected categories" },
                ].map((opt) => (
                  <label key={opt.value} className="flex items-start gap-2 cursor-pointer">
                    <input
                      type="radio"
                      name="aggregation"
                      value={opt.value}
                      checked={aggregationType === opt.value}
                      onChange={(e) => setAggregationType(e.target.value)}
                      className="mt-1 text-infojet-blue"
                    />
                    <div>
                      <span className="text-sm font-medium text-gray-700">{opt.label}</span>
                      <p className="text-xs text-gray-500">{opt.desc}</p>
                    </div>
                  </label>
                ))}
              </div>
            </div>

            {/* Article Types */}
            <div className="bg-white rounded-xl shadow-lg p-4">
              <h3 className="font-semibold text-gray-800 mb-3">Article Types</h3>
              <div className="space-y-2 max-h-40 overflow-y-auto">
                {articleTypes.map((type) => (
                  <label key={type} className="flex items-center gap-2 cursor-pointer">
                    <input
                      type="checkbox"
                      checked={selectedArticleTypes.includes(type)}
                      onChange={(e) => {
                        if (e.target.checked) {
                          setSelectedArticleTypes([...selectedArticleTypes, type]);
                        } else {
                          setSelectedArticleTypes(selectedArticleTypes.filter((t) => t !== type));
                        }
                      }}
                      className="rounded text-infojet-blue"
                    />
                    <span className="text-sm text-gray-700">{type}</span>
                  </label>
                ))}
              </div>
            </div>

            {/* Domains */}
            {domains.length > 0 && (
              <div className="bg-white rounded-xl shadow-lg p-4">
                <h3 className="font-semibold text-gray-800 mb-3">Top Domains</h3>
                <div className="space-y-2 max-h-40 overflow-y-auto">
                  {domains.slice(0, 10).map((domain) => (
                    <label key={domain} className="flex items-center gap-2 cursor-pointer">
                      <input
                        type="checkbox"
                        checked={selectedDomains.includes(domain)}
                        onChange={(e) => {
                          if (e.target.checked) {
                            setSelectedDomains([...selectedDomains, domain]);
                          } else {
                            setSelectedDomains(selectedDomains.filter((d) => d !== domain));
                          }
                        }}
                        className="rounded text-infojet-blue"
                      />
                      <span className="text-sm text-gray-700 truncate">{domain}</span>
                    </label>
                  ))}
                </div>
              </div>
            )}
          </div>

          {/* Results Area */}
          <div className="lg:col-span-3">
            {/* Search Bar */}
            <div className="bg-white rounded-xl shadow-lg p-4 mb-6">
              <div className="flex gap-4">
                <input
                  type="text"
                  value={keyword}
                  onChange={(e) => setKeyword(e.target.value)}
                  placeholder="Search keywords in titles and snippets..."
                  className="flex-1 px-4 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-infojet-blue"
                  data-testid="ultimate-search-input"
                />
                <button
                  onClick={() => handleSearch(1)}
                  disabled={loading}
                  className="px-6 py-2 bg-infojet-blue text-white rounded-lg hover:bg-infojet-blue/90 disabled:opacity-50 flex items-center gap-2"
                  data-testid="ultimate-search-btn"
                >
                  {loading ? <Loader2 className="w-5 h-5 animate-spin" /> : <Search className="w-5 h-5" />}
                  Search
                </button>
              </div>
            </div>

            {/* Results */}
            {results && (
              <>
                <div className="mb-4 text-sm text-gray-600">
                  Found {results.total} results (Page {results.page} of {results.total_pages})
                </div>
                <div className="space-y-4">
                  {results.results.map((result) => (
                    <SearchResultCard key={result.id} result={result} />
                  ))}
                </div>

                {/* Pagination */}
                {results.total_pages > 1 && (
                  <div className="flex justify-center gap-2 mt-6">
                    <button
                      onClick={() => handleSearch(page - 1)}
                      disabled={page === 1 || loading}
                      className="px-4 py-2 border border-gray-300 rounded-lg disabled:opacity-50"
                    >
                      Previous
                    </button>
                    <span className="px-4 py-2 text-gray-600">
                      Page {page} of {results.total_pages}
                    </span>
                    <button
                      onClick={() => handleSearch(page + 1)}
                      disabled={page === results.total_pages || loading}
                      className="px-4 py-2 border border-gray-300 rounded-lg disabled:opacity-50"
                    >
                      Next
                    </button>
                  </div>
                )}
              </>
            )}

            {!results && (
              <div className="bg-white rounded-2xl shadow-lg p-12 text-center">
                <Search className="w-16 h-16 text-gray-300 mx-auto mb-4" />
                <h3 className="text-xl font-semibold text-gray-800 mb-2">Start Searching</h3>
                <p className="text-gray-600">Select categories and filters, then click Search to view your collated results.</p>
              </div>
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
      toast.error("Failed to load statistics");
    } finally {
      setLoading(false);
    }
  };

  const COLORS = ["#0088FE", "#00C49F", "#FFBB28", "#FF8042", "#8884D8", "#82ca9d"];

  return (
    <Layout>
      <div className="max-w-6xl mx-auto">
        <div className="mb-8">
          <h1 className="text-3xl font-bold text-gray-800 mb-2">Statistics</h1>
          <p className="text-gray-600">View insights about your collated data.</p>
        </div>

        {loading ? (
          <div className="flex justify-center py-12">
            <Loader2 className="w-8 h-8 animate-spin text-infojet-blue" />
          </div>
        ) : stats ? (
          <div className="grid md:grid-cols-2 gap-6">
            {/* Summary Cards */}
            <div className="md:col-span-2 grid grid-cols-2 md:grid-cols-4 gap-4">
              <StatCard label="Total Results" value={stats.total_results} />
              <StatCard label="Categories" value={stats.total_categories} />
              <StatCard label="Domains" value={stats.top_domains?.length || 0} />
              <StatCard label="Article Types" value={stats.article_types?.length || 0} />
            </div>

            {/* Article Types Pie Chart */}
            {stats.article_types?.length > 0 && (
              <div className="bg-white rounded-2xl shadow-lg p-6">
                <h3 className="font-semibold text-gray-800 mb-4">Article Types Distribution</h3>
                <ResponsiveContainer width="100%" height={300}>
                  <PieChart>
                    <Pie
                      data={stats.article_types.map((t) => ({ name: t._id, value: t.count }))}
                      dataKey="value"
                      nameKey="name"
                      cx="50%"
                      cy="50%"
                      outerRadius={100}
                      label
                    >
                      {stats.article_types.map((_, index) => (
                        <Cell key={`cell-${index}`} fill={COLORS[index % COLORS.length]} />
                      ))}
                    </Pie>
                    <Tooltip />
                    <Legend />
                  </PieChart>
                </ResponsiveContainer>
              </div>
            )}

            {/* Top Domains Bar Chart */}
            {stats.top_domains?.length > 0 && (
              <div className="bg-white rounded-2xl shadow-lg p-6">
                <h3 className="font-semibold text-gray-800 mb-4">Top Domains</h3>
                <ResponsiveContainer width="100%" height={300}>
                  <BarChart data={stats.top_domains.map((d) => ({ name: d._id?.substring(0, 20) || "Unknown", count: d.count }))}>
                    <CartesianGrid strokeDasharray="3 3" />
                    <XAxis dataKey="name" tick={{ fontSize: 10 }} angle={-45} textAnchor="end" height={80} />
                    <YAxis />
                    <Tooltip />
                    <Bar dataKey="count" fill="#0088FE" />
                  </BarChart>
                </ResponsiveContainer>
              </div>
            )}

            {/* By Category */}
            {stats.by_category?.length > 0 && (
              <div className="bg-white rounded-2xl shadow-lg p-6 md:col-span-2">
                <h3 className="font-semibold text-gray-800 mb-4">Results by Category</h3>
                <ResponsiveContainer width="100%" height={300}>
                  <BarChart data={stats.by_category.map((c) => ({ name: c.name?.substring(0, 15) || "Unknown", count: c.count }))}>
                    <CartesianGrid strokeDasharray="3 3" />
                    <XAxis dataKey="name" tick={{ fontSize: 10 }} angle={-45} textAnchor="end" height={80} />
                    <YAxis />
                    <Tooltip />
                    <Bar dataKey="count" fill="#00C49F" />
                  </BarChart>
                </ResponsiveContainer>
              </div>
            )}
          </div>
        ) : (
          <div className="bg-white rounded-2xl shadow-lg p-12 text-center">
            <BarChart3 className="w-16 h-16 text-gray-300 mx-auto mb-4" />
            <h3 className="text-xl font-semibold text-gray-800 mb-2">No Data Yet</h3>
            <p className="text-gray-600">Start collating search results to see statistics.</p>
          </div>
        )}
      </div>
    </Layout>
  );
};

const StatCard = ({ label, value }) => (
  <div className="bg-white rounded-xl shadow-lg p-6 text-center">
    <p className="text-3xl font-bold text-infojet-blue">{value}</p>
    <p className="text-sm text-gray-600 mt-1">{label}</p>
  </div>
);

// Global Database Page
const GlobalDatabasePage = () => {
  const [data, setData] = useState(null);
  const [loading, setLoading] = useState(true);
  const [page, setPage] = useState(1);
  const [selectedCategory, setSelectedCategory] = useState(null);

  useEffect(() => {
    fetchData();
  }, [page, selectedCategory]);

  const fetchData = async () => {
    setLoading(true);
    try {
      const params = new URLSearchParams({ page: page.toString() });
      if (selectedCategory) params.append("category_id", selectedCategory);
      const res = await axios.get(`${API}/global-database?${params}`);
      setData(res.data);
    } catch (error) {
      toast.error(error.response?.data?.detail || "Failed to load global database");
    } finally {
      setLoading(false);
    }
  };

  return (
    <Layout>
      <div className="max-w-6xl mx-auto">
        <div className="mb-8">
          <h1 className="text-3xl font-bold text-gray-800 mb-2">Global Research Database</h1>
          <p className="text-gray-600">Explore public categories and results from all users.</p>
        </div>

        <div className="grid lg:grid-cols-4 gap-6">
          {/* Categories Sidebar */}
          <div className="lg:col-span-1">
            <div className="bg-white rounded-xl shadow-lg p-4">
              <h3 className="font-semibold text-gray-800 mb-3">Public Categories</h3>
              <div className="space-y-2 max-h-96 overflow-y-auto">
                <button
                  onClick={() => {
                    setSelectedCategory(null);
                    setPage(1);
                  }}
                  className={`w-full text-left px-3 py-2 rounded-lg text-sm ${!selectedCategory ? "bg-infojet-blue text-white" : "hover:bg-gray-100"}`}
                >
                  All Categories
                </button>
                {data?.public_categories?.map((cat) => (
                  <button
                    key={cat.id}
                    onClick={() => {
                      setSelectedCategory(cat.id);
                      setPage(1);
                    }}
                    className={`w-full text-left px-3 py-2 rounded-lg text-sm ${selectedCategory === cat.id ? "bg-infojet-blue text-white" : "hover:bg-gray-100"}`}
                  >
                    {cat.name}
                  </button>
                ))}
              </div>
            </div>
          </div>

          {/* Results */}
          <div className="lg:col-span-3">
            {loading ? (
              <div className="flex justify-center py-12">
                <Loader2 className="w-8 h-8 animate-spin text-infojet-blue" />
              </div>
            ) : data?.results?.length > 0 ? (
              <>
                <div className="mb-4 text-sm text-gray-600">
                  Found {data.total} results (Page {data.page} of {data.total_pages})
                </div>
                <div className="space-y-4">
                  {data.results.map((result) => (
                    <SearchResultCard key={result.id} result={result} />
                  ))}
                </div>

                {data.total_pages > 1 && (
                  <div className="flex justify-center gap-2 mt-6">
                    <button
                      onClick={() => setPage(page - 1)}
                      disabled={page === 1}
                      className="px-4 py-2 border border-gray-300 rounded-lg disabled:opacity-50"
                    >
                      Previous
                    </button>
                    <span className="px-4 py-2 text-gray-600">
                      Page {page} of {data.total_pages}
                    </span>
                    <button
                      onClick={() => setPage(page + 1)}
                      disabled={page === data.total_pages}
                      className="px-4 py-2 border border-gray-300 rounded-lg disabled:opacity-50"
                    >
                      Next
                    </button>
                  </div>
                )}
              </>
            ) : (
              <div className="bg-white rounded-2xl shadow-lg p-12 text-center">
                <Users className="w-16 h-16 text-gray-300 mx-auto mb-4" />
                <h3 className="text-xl font-semibold text-gray-800 mb-2">No Public Results</h3>
                <p className="text-gray-600">There are no public results available yet.</p>
              </div>
            )}
          </div>
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
  const [saving, setSaving] = useState(false);
  const [newBlockedWord, setNewBlockedWord] = useState("");
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
      toast.error("Failed to load admin data");
    } finally {
      setLoading(false);
    }
  };

  const handleSaveSettings = async () => {
    setSaving(true);
    try {
      await axios.put(`${API}/admin/settings`, {
        results_per_page: settings.results_per_page,
        free_user_pages: settings.free_user_pages,
        max_category_levels: settings.max_category_levels,
        subscription_price: settings.subscription_price,
        informative_min_words: settings.informative_min_words,
        phd_keyword_count: settings.phd_keyword_count,
        blog_keyword_count: settings.blog_keyword_count
      });
      toast.success("Settings saved!");
    } catch (error) {
      toast.error("Failed to save settings");
    } finally {
      setSaving(false);
    }
  };

  const handleAddBlockedWord = async () => {
    if (!newBlockedWord.trim()) return;
    try {
      await axios.post(`${API}/admin/ban-word?word=${encodeURIComponent(newBlockedWord)}`);
      setSettings({
        ...settings,
        blocked_words: [...settings.blocked_words, newBlockedWord.toLowerCase()]
      });
      setNewBlockedWord("");
      toast.success("Word blocked!");
    } catch (error) {
      toast.error("Failed to block word");
    }
  };

  const handleRemoveBlockedWord = async (word) => {
    try {
      await axios.delete(`${API}/admin/ban-word/${encodeURIComponent(word)}`);
      setSettings({
        ...settings,
        blocked_words: settings.blocked_words.filter((w) => w !== word)
      });
      toast.success("Word unblocked!");
    } catch (error) {
      toast.error("Failed to unblock word");
    }
  };

  const handleTogglePaid = async (userId, currentStatus) => {
    try {
      await axios.post(`${API}/admin/set-paid/${userId}?is_paid=${!currentStatus}`);
      setUsers(users.map((u) => (u.id === userId ? { ...u, is_paid: !currentStatus } : u)));
      toast.success("User status updated!");
    } catch (error) {
      toast.error("Failed to update user status");
    }
  };

  const handleBanUser = async (userId) => {
    if (!window.confirm("Ban this user?")) return;
    try {
      await axios.post(`${API}/admin/ban-user/${userId}`);
      setUsers(users.map((u) => (u.id === userId ? { ...u, is_banned: true } : u)));
      toast.success("User banned!");
    } catch (error) {
      toast.error("Failed to ban user");
    }
  };

  if (!user?.is_admin) {
    return (
      <Layout>
        <div className="text-center py-12">
          <h1 className="text-2xl font-bold text-gray-800">Access Denied</h1>
          <p className="text-gray-600 mt-2">You need admin privileges to access this page.</p>
        </div>
      </Layout>
    );
  }

  return (
    <Layout>
      <div className="max-w-4xl mx-auto">
        <div className="mb-8">
          <h1 className="text-3xl font-bold text-gray-800 mb-2">Admin Panel</h1>
          <p className="text-gray-600">Manage settings, users, and content moderation.</p>
        </div>

        {loading ? (
          <div className="flex justify-center py-12">
            <Loader2 className="w-8 h-8 animate-spin text-infojet-blue" />
          </div>
        ) : (
          <div className="space-y-6">
            {/* General Settings */}
            <div className="bg-white rounded-2xl shadow-lg p-6">
              <h2 className="text-xl font-semibold text-gray-800 mb-4">General Settings</h2>
              <div className="grid md:grid-cols-2 gap-4">
                <div>
                  <label className="block text-sm font-medium text-gray-700 mb-1">Results Per Page</label>
                  <input
                    type="number"
                    value={settings?.results_per_page || 20}
                    onChange={(e) => setSettings({ ...settings, results_per_page: parseInt(e.target.value) })}
                    className="w-full px-4 py-2 border border-gray-300 rounded-lg"
                    data-testid="results-per-page-input"
                  />
                </div>
                <div>
                  <label className="block text-sm font-medium text-gray-700 mb-1">Free User Pages Limit</label>
                  <input
                    type="number"
                    value={settings?.free_user_pages || 1}
                    onChange={(e) => setSettings({ ...settings, free_user_pages: parseInt(e.target.value) })}
                    className="w-full px-4 py-2 border border-gray-300 rounded-lg"
                    data-testid="free-pages-input"
                  />
                </div>
                <div>
                  <label className="block text-sm font-medium text-gray-700 mb-1">Max Category Levels</label>
                  <input
                    type="number"
                    value={settings?.max_category_levels || 100}
                    onChange={(e) => setSettings({ ...settings, max_category_levels: parseInt(e.target.value) })}
                    className="w-full px-4 py-2 border border-gray-300 rounded-lg"
                  />
                </div>
                <div>
                  <label className="block text-sm font-medium text-gray-700 mb-1">Subscription Price ($)</label>
                  <input
                    type="number"
                    step="0.01"
                    value={settings?.subscription_price || 0.99}
                    onChange={(e) => setSettings({ ...settings, subscription_price: parseFloat(e.target.value) })}
                    className="w-full px-4 py-2 border border-gray-300 rounded-lg"
                  />
                </div>
              </div>

              <h3 className="font-medium text-gray-800 mt-6 mb-3">Article Classification Settings</h3>
              <div className="grid md:grid-cols-3 gap-4">
                <div>
                  <label className="block text-sm font-medium text-gray-700 mb-1">Informative Min Words</label>
                  <input
                    type="number"
                    value={settings?.informative_min_words || 1500}
                    onChange={(e) => setSettings({ ...settings, informative_min_words: parseInt(e.target.value) })}
                    className="w-full px-4 py-2 border border-gray-300 rounded-lg"
                  />
                </div>
                <div>
                  <label className="block text-sm font-medium text-gray-700 mb-1">Ph.D Keyword Count</label>
                  <input
                    type="number"
                    value={settings?.phd_keyword_count || 3}
                    onChange={(e) => setSettings({ ...settings, phd_keyword_count: parseInt(e.target.value) })}
                    className="w-full px-4 py-2 border border-gray-300 rounded-lg"
                  />
                </div>
                <div>
                  <label className="block text-sm font-medium text-gray-700 mb-1">Blog Keyword Count</label>
                  <input
                    type="number"
                    value={settings?.blog_keyword_count || 3}
                    onChange={(e) => setSettings({ ...settings, blog_keyword_count: parseInt(e.target.value) })}
                    className="w-full px-4 py-2 border border-gray-300 rounded-lg"
                  />
                </div>
              </div>

              <button
                onClick={handleSaveSettings}
                disabled={saving}
                className="mt-6 px-6 py-2 bg-infojet-blue text-white rounded-lg hover:bg-infojet-blue/90 disabled:opacity-50"
                data-testid="save-settings-btn"
              >
                {saving ? <Loader2 className="w-5 h-5 animate-spin" /> : "Save Settings"}
              </button>
            </div>

            {/* Blocked Words */}
            <div className="bg-white rounded-2xl shadow-lg p-6">
              <h2 className="text-xl font-semibold text-gray-800 mb-4">Blocked Words</h2>
              <div className="flex gap-2 mb-4">
                <input
                  type="text"
                  value={newBlockedWord}
                  onChange={(e) => setNewBlockedWord(e.target.value)}
                  placeholder="Add word to block..."
                  className="flex-1 px-4 py-2 border border-gray-300 rounded-lg"
                  data-testid="blocked-word-input"
                />
                <button
                  onClick={handleAddBlockedWord}
                  className="px-4 py-2 bg-red-500 text-white rounded-lg hover:bg-red-600"
                  data-testid="add-blocked-word-btn"
                >
                  Block
                </button>
              </div>
              <div className="flex flex-wrap gap-2">
                {settings?.blocked_words?.map((word) => (
                  <span key={word} className="inline-flex items-center gap-1 px-3 py-1 bg-red-100 text-red-700 rounded-full text-sm">
                    {word}
                    <button onClick={() => handleRemoveBlockedWord(word)} className="hover:text-red-900">
                      <X className="w-4 h-4" />
                    </button>
                  </span>
                ))}
              </div>
            </div>

            {/* User Management */}
            <div className="bg-white rounded-2xl shadow-lg p-6">
              <h2 className="text-xl font-semibold text-gray-800 mb-4">User Management</h2>
              <div className="overflow-x-auto">
                <table className="w-full">
                  <thead>
                    <tr className="border-b">
                      <th className="text-left py-3 px-4 text-sm font-medium text-gray-600">Username</th>
                      <th className="text-left py-3 px-4 text-sm font-medium text-gray-600">Email</th>
                      <th className="text-left py-3 px-4 text-sm font-medium text-gray-600">Status</th>
                      <th className="text-left py-3 px-4 text-sm font-medium text-gray-600">Actions</th>
                    </tr>
                  </thead>
                  <tbody>
                    {users.map((u) => (
                      <tr key={u.id} className="border-b hover:bg-gray-50">
                        <td className="py-3 px-4">
                          <span className="font-medium">{u.username}</span>
                          {u.is_admin && (
                            <span className="ml-2 px-2 py-0.5 bg-purple-100 text-purple-700 text-xs rounded-full">Admin</span>
                          )}
                        </td>
                        <td className="py-3 px-4 text-sm text-gray-600">{u.email}</td>
                        <td className="py-3 px-4">
                          <span className={`px-2 py-0.5 text-xs rounded-full ${u.is_paid ? "bg-green-100 text-green-700" : "bg-gray-100 text-gray-600"}`}>
                            {u.is_paid ? "Premium" : "Free"}
                          </span>
                          {u.is_banned && (
                            <span className="ml-1 px-2 py-0.5 bg-red-100 text-red-700 text-xs rounded-full">Banned</span>
                          )}
                        </td>
                        <td className="py-3 px-4">
                          <div className="flex gap-2">
                            <button
                              onClick={() => handleTogglePaid(u.id, u.is_paid)}
                              className="text-sm text-infojet-blue hover:underline"
                            >
                              {u.is_paid ? "Remove Premium" : "Make Premium"}
                            </button>
                            {!u.is_banned && !u.is_admin && (
                              <button
                                onClick={() => handleBanUser(u.id)}
                                className="text-sm text-red-500 hover:underline"
                              >
                                Ban
                              </button>
                            )}
                          </div>
                        </td>
                      </tr>
                    ))}
                  </tbody>
                </table>
              </div>
            </div>
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
      <Toaster position="top-right" richColors />
      <BrowserRouter>
        <Routes>
          <Route path="/login" element={<LoginPage />} />
          <Route
            path="/"
            element={
              <ProtectedRoute>
                <HomePage />
              </ProtectedRoute>
            }
          />
          <Route
            path="/infojet"
            element={
              <ProtectedRoute>
                <InfoJetPage />
              </ProtectedRoute>
            }
          />
          <Route
            path="/ultimate-search"
            element={
              <ProtectedRoute>
                <UltimateSearchPage />
              </ProtectedRoute>
            }
          />
          <Route
            path="/categories"
            element={
              <ProtectedRoute>
                <CategoriesPage />
              </ProtectedRoute>
            }
          />
          <Route
            path="/statistics"
            element={
              <ProtectedRoute>
                <StatisticsPage />
              </ProtectedRoute>
            }
          />
          <Route
            path="/global-database"
            element={
              <ProtectedRoute>
                <GlobalDatabasePage />
              </ProtectedRoute>
            }
          />
          <Route
            path="/admin"
            element={
              <ProtectedRoute>
                <AdminPage />
              </ProtectedRoute>
            }
          />
          <Route path="*" element={<Navigate to="/" />} />
        </Routes>
      </BrowserRouter>
    </AuthProvider>
  );
}

export default App;
