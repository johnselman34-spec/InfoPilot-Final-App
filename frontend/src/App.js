import React, { useState, useEffect, createContext, useContext, useCallback, useMemo } from "react";
import { BrowserRouter, Routes, Route, Navigate, useNavigate, useLocation, useParams } from "react-router-dom";
import axios from "axios";
import { Toaster, toast } from "sonner";
import { GoogleOAuthProvider, GoogleLogin } from "@react-oauth/google";
import { loadStripe } from "@stripe/stripe-js";
import { Elements, PaymentElement, useStripe, useElements } from "@stripe/react-stripe-js";
import { GoogleMap, useJsApiLoader, Marker, InfoWindow } from "@react-google-maps/api";
import {
  Search, Globe, FolderTree, BarChart3, Settings, LogOut, User, Plus, Trash2,
  Eye, EyeOff, ChevronDown, ChevronRight, Filter, Heart, ThumbsUp, Smile,
  Frown, AlertTriangle, Flag, Award, Home, Users, BookOpen, Menu, X, Loader2,
  ShoppingCart, CreditCard, Star, ExternalLink, Plane, Shield, Radar, Target,
  Crosshair, Navigation, Zap, Radio, Cpu, Book, Edit3, Copy, Check, Gift,
  Sparkles, Crown, Lock, Unlock, ArrowRight, DollarSign, Clock, Calendar, MapPin,
  FileText, UserPlus, MessageCircle, Send, Image, Lightbulb
} from "lucide-react";
import {
  PieChart, Pie, Cell, BarChart, Bar, XAxis, YAxis, CartesianGrid, Tooltip,
  Legend, ResponsiveContainer
} from "recharts";
import "@/App.css";

const BACKEND_URL = process.env.REACT_APP_BACKEND_URL;
const API = `${BACKEND_URL}/api`;
const GOOGLE_MAPS_API_KEY = process.env.REACT_APP_GOOGLE_MAPS_API_KEY;

// Google OAuth Client ID
const GOOGLE_CLIENT_ID = process.env.REACT_APP_GOOGLE_CLIENT_ID;

// Stripe Publishable Key - Only initialize if key exists (app is now FREE, Stripe optional)
const stripeKey = process.env.REACT_APP_STRIPE_PUBLISHABLE_KEY;
const stripePromise = stripeKey ? loadStripe(stripeKey) : null;

// All Images - Including new book images
const IMAGES = {
  globe: "https://customer-assets.emergentagent.com/job_0c3ceef4-3e2b-40c0-b767-31d91735cf23/artifacts/utj2uh0i_global-network-world-globe-focusing-usa-symbolizing-data-transfer-worldwide-concept-data-transfer-global-connectivity-information-exchange-world-globe-usa-symbolism_918839-41653.jpg",
  author: "https://customer-assets.emergentagent.com/job_0c3ceef4-3e2b-40c0-b767-31d91735cf23/artifacts/5150hnhi_FB_IMG_1767397923842.jpg",
  bookCoverMain: "https://customer-assets.emergentagent.com/job_5fdf2820-b9a7-4458-b1a2-1b10e8aac7a0/artifacts/sz2m7z1e_ebook-1.jpg",
  bookCover1: "https://customer-assets.emergentagent.com/job_f0e224b7-603f-43aa-9316-33b663f6e339/artifacts/kkmai0t8_Letters%20to%20Evelyn%20advertisement%201.jpg",
  bookCover2: "https://customer-assets.emergentagent.com/job_f0e224b7-603f-43aa-9316-33b663f6e339/artifacts/2p3c884v_Letters%20to%20Evelyn%20advertisement%202.jpg",
  bookCover3: "https://customer-assets.emergentagent.com/job_f0e224b7-603f-43aa-9316-33b663f6e339/artifacts/3qhi02pv_Letters%20to%20Evelyn%20advertisement%203.jpg",
  bookCover4: "https://customer-assets.emergentagent.com/job_f0e224b7-603f-43aa-9316-33b663f6e339/artifacts/qxfza2d2_Letters%20to%20Evelyn%20advertisement%204.jpg"
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

// Pricing Info
const SALE_PRICE = 0.75;
const REGULAR_PRICE = 4.62;

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

// Badge Notification Component - Shows when user earns new badges
const BadgeNotificationProvider = ({ children }) => {
  const { user, token } = useAuth();
  const [notification, setNotification] = useState(null);
  const [showNotification, setShowNotification] = useState(false);
  const navigate = useNavigate();

  useEffect(() => {
    if (user && token) {
      checkForNewBadges();
      // Check periodically
      const interval = setInterval(checkForNewBadges, 60000); // Every minute
      return () => clearInterval(interval);
    }
  }, [user, token]);

  const checkForNewBadges = async () => {
    try {
      const res = await axios.post(`${API}/badges/check-new`);
      if (res.data.has_new_badges && res.data.new_badges.length > 0) {
        setNotification(res.data);
        setShowNotification(true);
      }
    } catch (error) {
      // Silently fail - badge notifications are non-critical
    }
  };

  const dismissNotification = () => {
    setShowNotification(false);
    setTimeout(() => setNotification(null), 500);
  };

  return (
    <>
      {children}
      
      {/* Badge Notification Modal */}
      {showNotification && notification && (
        <div className="fixed inset-0 bg-black/80 flex items-center justify-center z-[100] p-4 animate-fadeIn">
          <div className="bg-gradient-to-br from-slate-900 via-purple-900/50 to-slate-900 border-2 border-yellow-500/50 rounded-2xl max-w-md w-full p-6 shadow-2xl shadow-yellow-500/20 animate-scaleIn">
            {/* Confetti effect */}
            <div className="absolute inset-0 overflow-hidden pointer-events-none rounded-2xl">
              {[...Array(20)].map((_, i) => (
                <div
                  key={i}
                  className="absolute w-2 h-2 rounded-full animate-confetti"
                  style={{
                    left: `${Math.random() * 100}%`,
                    backgroundColor: ['#ec4899', '#8b5cf6', '#eab308', '#22c55e', '#3b82f6'][i % 5],
                    animationDelay: `${Math.random() * 0.5}s`,
                    animationDuration: `${1 + Math.random()}s`
                  }}
                />
              ))}
            </div>
            
            {/* Header */}
            <div className="text-center mb-6 relative">
              <div className="text-6xl mb-4 animate-bounce">🎉</div>
              <h2 className="text-2xl font-bold text-transparent bg-clip-text bg-gradient-to-r from-yellow-400 to-orange-400 font-mono">
                BADGE UNLOCKED!
              </h2>
            </div>
            
            {/* Badges */}
            <div className="flex flex-wrap justify-center gap-4 mb-6">
              {notification.new_badges.map((badge) => (
                <div key={badge.id} className="text-center p-4 bg-slate-950 rounded-xl border border-yellow-500/30">
                  <span className="text-5xl block mb-2">{badge.icon}</span>
                  <p className="text-yellow-400 font-mono font-bold text-sm">{badge.name}</p>
                  <p className="text-purple-400/60 font-mono text-xs mt-1">{badge.description}</p>
                </div>
              ))}
            </div>
            
            {/* Promotional Message */}
            {notification.promotional_message && (
              <div className="bg-gradient-to-r from-pink-500/20 to-purple-500/20 p-4 rounded-lg border border-pink-500/30 mb-4">
                <p className="text-purple-300 font-mono text-sm text-center">
                  {notification.promotional_message}
                </p>
              </div>
            )}
            
            {/* Action Buttons */}
            <div className="flex flex-col gap-3">
              <div className="flex gap-3">
                <button
                  onClick={() => { dismissNotification(); navigate('/subscribe'); }}
                  className="flex-1 px-4 py-3 bg-gradient-to-r from-yellow-500 to-orange-500 text-black font-mono font-bold rounded-lg hover:scale-[1.02] transition-transform flex items-center justify-center gap-2"
                >
                  <Crown className="w-5 h-5" /> SUBSCRIBE
                </button>
                <a
                  href={notification.book_link}
                  target="_blank"
                  rel="noopener noreferrer"
                  onClick={dismissNotification}
                  className="flex-1 px-4 py-3 bg-gradient-to-r from-pink-600 to-purple-600 text-white font-mono font-bold rounded-lg hover:scale-[1.02] transition-transform flex items-center justify-center gap-2"
                >
                  <Book className="w-5 h-5" /> GET THE BOOK
                </a>
              </div>
              <button
                onClick={dismissNotification}
                className="w-full px-4 py-2 text-purple-400/60 hover:text-purple-300 font-mono text-sm"
              >
                Maybe Later
              </button>
            </div>
          </div>
        </div>
      )}
    </>
  );
};

// Protected Route
const ProtectedRoute = ({ children }) => {
  const { user, loading } = useAuth();
  if (loading) return <LoadingScreen />;
  if (!user) return <Navigate to="/login" />;
  return children;
};

// Loading Screen - Futuristic Theme
const LoadingScreen = () => (
  <div className="min-h-screen bg-gradient-to-br from-slate-950 via-purple-950 to-slate-950 flex items-center justify-center">
    <div className="text-center">
      <div className="relative w-24 h-24 mx-auto mb-6">
        <div className="absolute inset-0 border-4 border-pink-500/30 rounded-full animate-ping"></div>
        <div className="absolute inset-2 border-2 border-purple-400 rounded-full animate-spin"></div>
        <Radar className="absolute inset-0 m-auto w-12 h-12 text-pink-400 animate-pulse" />
      </div>
      <p className="text-purple-300 font-mono text-lg tracking-wider">INITIALIZING INFOPILOT EXPLORER...</p>
    </div>
  </div>
);

// Futuristic Frame Component
const FuturisticFrame = ({ children, title, className = "", color = "purple" }) => {
  const colors = {
    purple: { border: "border-purple-500/50", text: "text-purple-400", glow: "shadow-purple-500/20" },
    pink: { border: "border-pink-500/50", text: "text-pink-400", glow: "shadow-pink-500/20" },
    blue: { border: "border-blue-500/50", text: "text-blue-400", glow: "shadow-blue-500/20" },
    red: { border: "border-red-500/50", text: "text-red-400", glow: "shadow-red-500/20" }
  };
  const c = colors[color] || colors.purple;
  
  return (
    <div className={`relative ${className}`}>
      <div className={`absolute top-0 left-0 w-4 h-4 border-t-2 border-l-2 ${c.border} pointer-events-none`}></div>
      <div className={`absolute top-0 right-0 w-4 h-4 border-t-2 border-r-2 ${c.border} pointer-events-none`}></div>
      <div className={`absolute bottom-0 left-0 w-4 h-4 border-b-2 border-l-2 ${c.border} pointer-events-none`}></div>
      <div className={`absolute bottom-0 right-0 w-4 h-4 border-b-2 border-r-2 ${c.border} pointer-events-none`}></div>
      {title && (
        <div className="absolute -top-3 left-6 bg-slate-950 px-2 pointer-events-none">
          <span className={`${c.text} text-xs font-mono tracking-wider`}>{title}</span>
        </div>
      )}
      <div className="p-4 relative z-10">{children}</div>
    </div>
  );
};

// ============================================
// FACEBOOK-STYLE REACTIONS & COMMENTS
// ============================================

// Reaction Types Configuration
const REACTION_CONFIG = {
  like: { emoji: "👍", label: "Like", color: "text-blue-400" },
  love: { emoji: "❤️", label: "Love", color: "text-red-400" },
  haha: { emoji: "😂", label: "Haha", color: "text-yellow-400" },
  wow: { emoji: "😮", label: "Wow", color: "text-yellow-400" },
  sad: { emoji: "😢", label: "Sad", color: "text-yellow-400" },
  angry: { emoji: "😠", label: "Angry", color: "text-orange-400" }
};

// Reaction Button Component with Emoji Picker
const ReactionButton = ({ postType, postId, reactions = {}, reactionCounts = {}, userReaction, onUpdate }) => {
  const [showPicker, setShowPicker] = useState(false);
  const [loading, setLoading] = useState(false);
  const pickerRef = React.useRef(null);

  useEffect(() => {
    const handleClickOutside = (e) => {
      if (pickerRef.current && !pickerRef.current.contains(e.target)) {
        setShowPicker(false);
      }
    };
    document.addEventListener("mousedown", handleClickOutside);
    return () => document.removeEventListener("mousedown", handleClickOutside);
  }, []);

  const totalReactions = Object.values(reactionCounts || {}).reduce((a, b) => a + b, 0);
  
  const handleReaction = async (reactionType) => {
    setLoading(true);
    try {
      if (userReaction === reactionType) {
        await axios.delete(`${API}/posts/${postType}/${postId}/reactions`);
        onUpdate && onUpdate(null);
      } else {
        const res = await axios.post(`${API}/posts/${postType}/${postId}/reactions`, { reaction_type: reactionType });
        onUpdate && onUpdate(res.data.user_reaction, res.data.reactions, res.data.reaction_counts);
      }
    } catch (error) {
      toast.error("Failed to update reaction");
    } finally {
      setLoading(false);
      setShowPicker(false);
    }
  };

  const topReactions = Object.entries(reactionCounts || {})
    .filter(([_, count]) => count > 0)
    .sort((a, b) => b[1] - a[1])
    .slice(0, 3);

  return (
    <div className="relative" ref={pickerRef}>
      <button
        onClick={() => userReaction ? handleReaction(userReaction) : setShowPicker(!showPicker)}
        onMouseEnter={() => !loading && setShowPicker(true)}
        disabled={loading}
        className={`flex items-center gap-2 px-3 py-1.5 rounded-lg transition-all ${
          userReaction 
            ? `bg-${REACTION_CONFIG[userReaction]?.color.split('-')[1]}-500/20 ${REACTION_CONFIG[userReaction]?.color}` 
            : 'text-purple-400/60 hover:text-pink-400 hover:bg-pink-500/10'
        } font-mono text-sm`}
        data-testid={`reaction-btn-${postId}`}
      >
        {loading ? (
          <Loader2 className="w-4 h-4 animate-spin" />
        ) : (
          <>
            {userReaction ? (
              <span className="text-lg">{REACTION_CONFIG[userReaction]?.emoji}</span>
            ) : (
              <ThumbsUp className="w-4 h-4" />
            )}
            <span className="flex items-center gap-1">
              {topReactions.map(([type]) => (
                <span key={type} className="text-sm">{REACTION_CONFIG[type]?.emoji}</span>
              ))}
              {totalReactions > 0 && <span className="ml-1">{totalReactions}</span>}
            </span>
          </>
        )}
      </button>
      
      {/* Reaction Picker Popup */}
      {showPicker && (
        <div 
          className="absolute bottom-full left-0 mb-2 bg-slate-900 border border-purple-500/30 rounded-full px-2 py-1 flex gap-1 shadow-xl shadow-purple-500/20 z-50"
          onMouseLeave={() => setShowPicker(false)}
        >
          {Object.entries(REACTION_CONFIG).map(([type, config]) => (
            <button
              key={type}
              onClick={() => handleReaction(type)}
              className={`text-2xl hover:scale-125 transition-transform p-1 rounded-full ${userReaction === type ? 'bg-purple-500/30' : 'hover:bg-purple-500/20'}`}
              title={config.label}
              data-testid={`reaction-${type}-${postId}`}
            >
              {config.emoji}
            </button>
          ))}
        </div>
      )}
    </div>
  );
};

// Comment Input Component
const CommentInput = ({ postType, postId, parentId = null, onSubmit, placeholder = "Write a comment...", compact = false }) => {
  const [content, setContent] = useState("");
  const [submitting, setSubmitting] = useState(false);

  const handleSubmit = async (e) => {
    e.preventDefault();
    if (!content.trim()) return;
    setSubmitting(true);
    try {
      const res = await axios.post(`${API}/posts/${postType}/${postId}/comments`, {
        content: content.trim(),
        parent_id: parentId
      });
      setContent("");
      onSubmit && onSubmit(res.data.comment);
      toast.success(parentId ? "Reply added!" : "Comment added!");
    } catch (error) {
      toast.error("Failed to add comment");
    } finally {
      setSubmitting(false);
    }
  };

  return (
    <form onSubmit={handleSubmit} className={`flex gap-2 ${compact ? '' : 'mt-3'}`}>
      <input
        type="text"
        value={content}
        onChange={(e) => setContent(e.target.value)}
        placeholder={placeholder}
        className={`flex-1 ${compact ? 'px-3 py-1.5 text-sm' : 'px-4 py-2'} bg-slate-950 border border-purple-500/30 rounded-full text-purple-300 font-mono focus:border-pink-500 focus:outline-none`}
        data-testid={`comment-input-${postId}`}
      />
      <button
        type="submit"
        disabled={submitting || !content.trim()}
        className={`${compact ? 'px-3 py-1.5' : 'px-4 py-2'} bg-gradient-to-r from-pink-600 to-purple-600 text-white rounded-full hover:scale-105 transition-transform disabled:opacity-50 disabled:hover:scale-100`}
        data-testid={`comment-submit-${postId}`}
      >
        {submitting ? <Loader2 className="w-4 h-4 animate-spin" /> : <Send className="w-4 h-4" />}
      </button>
    </form>
  );
};

// Single Comment Component with Replies
const CommentItem = ({ comment, postType, postId, onDelete, onReplyAdded, depth = 0 }) => {
  const { user } = useAuth();
  const [showReplies, setShowReplies] = useState(depth < 2);
  const [showReplyInput, setShowReplyInput] = useState(false);
  const [localReaction, setLocalReaction] = useState(null);

  const handleReplyAdded = (newComment) => {
    setShowReplyInput(false);
    onReplyAdded && onReplyAdded(newComment);
  };

  return (
    <div className={`${depth > 0 ? 'ml-8 border-l-2 border-purple-500/20 pl-4' : ''}`}>
      <div className="bg-slate-900/50 rounded-lg p-3 mb-2">
        <div className="flex items-start gap-2">
          <div className="w-8 h-8 bg-gradient-to-br from-pink-500/20 to-purple-500/20 rounded-full flex items-center justify-center flex-shrink-0">
            <User className="w-4 h-4 text-pink-400" />
          </div>
          <div className="flex-1 min-w-0">
            <div className="flex items-center gap-2">
              <span className="text-purple-300 font-mono text-sm font-bold">{comment.username}</span>
              <span className="text-purple-400/40 font-mono text-xs">{new Date(comment.created_at).toLocaleString()}</span>
            </div>
            <p className="text-purple-300/90 font-mono text-sm mt-1 whitespace-pre-wrap break-words">{comment.content}</p>
            
            <div className="flex items-center gap-3 mt-2">
              <button
                onClick={() => setShowReplyInput(!showReplyInput)}
                className="text-purple-400/60 hover:text-pink-400 font-mono text-xs flex items-center gap-1"
              >
                <MessageCircle className="w-3 h-3" /> Reply
              </button>
              {user?.id === comment.user_id && (
                <button
                  onClick={() => onDelete && onDelete(comment.id)}
                  className="text-red-400/60 hover:text-red-400 font-mono text-xs flex items-center gap-1"
                >
                  <Trash2 className="w-3 h-3" /> Delete
                </button>
              )}
            </div>
          </div>
        </div>
        
        {showReplyInput && (
          <div className="mt-3 ml-10">
            <CommentInput
              postType={postType}
              postId={postId}
              parentId={comment.id}
              onSubmit={handleReplyAdded}
              placeholder={`Reply to ${comment.username}...`}
              compact
            />
          </div>
        )}
      </div>
      
      {/* Nested Replies */}
      {comment.replies && comment.replies.length > 0 && (
        <div>
          {!showReplies && (
            <button
              onClick={() => setShowReplies(true)}
              className="text-pink-400 font-mono text-xs mb-2 hover:underline"
            >
              Show {comment.replies.length} {comment.replies.length === 1 ? 'reply' : 'replies'}
            </button>
          )}
          {showReplies && comment.replies.map(reply => (
            <CommentItem
              key={reply.id}
              comment={reply}
              postType={postType}
              postId={postId}
              onDelete={onDelete}
              onReplyAdded={onReplyAdded}
              depth={depth + 1}
            />
          ))}
        </div>
      )}
    </div>
  );
};

// Comments Section Component
const CommentsSection = ({ postType, postId, initialCount = 0 }) => {
  const [comments, setComments] = useState([]);
  const [loading, setLoading] = useState(false);
  const [showComments, setShowComments] = useState(false);
  const [totalCount, setTotalCount] = useState(initialCount);

  const fetchComments = async () => {
    setLoading(true);
    try {
      const res = await axios.get(`${API}/posts/${postType}/${postId}/comments`);
      setComments(res.data.comments || []);
      setTotalCount(res.data.total_count || 0);
    } catch (error) {
      console.error("Failed to fetch comments");
    } finally {
      setLoading(false);
    }
  };

  const handleToggleComments = () => {
    if (!showComments && comments.length === 0) {
      fetchComments();
    }
    setShowComments(!showComments);
  };

  const handleCommentAdded = (newComment) => {
    fetchComments();
    setTotalCount(prev => prev + 1);
  };

  const handleDeleteComment = async (commentId) => {
    if (!window.confirm("Delete this comment?")) return;
    try {
      await axios.delete(`${API}/comments/${commentId}`);
      toast.success("Comment deleted");
      fetchComments();
      setTotalCount(prev => Math.max(0, prev - 1));
    } catch (error) {
      toast.error("Failed to delete comment");
    }
  };

  return (
    <div>
      <button
        onClick={handleToggleComments}
        className="flex items-center gap-2 text-purple-400/60 hover:text-blue-400 font-mono text-sm px-3 py-1.5 rounded-lg hover:bg-blue-500/10 transition-colors"
        data-testid={`comments-toggle-${postId}`}
      >
        <MessageCircle className="w-4 h-4" />
        {totalCount > 0 ? `${totalCount} Comment${totalCount !== 1 ? 's' : ''}` : 'Comment'}
      </button>
      
      {showComments && (
        <div className="mt-3 pt-3 border-t border-purple-500/20">
          <CommentInput
            postType={postType}
            postId={postId}
            onSubmit={handleCommentAdded}
          />
          
          {loading ? (
            <div className="flex justify-center py-4">
              <Loader2 className="w-6 h-6 text-pink-400 animate-spin" />
            </div>
          ) : comments.length > 0 ? (
            <div className="mt-4 space-y-2">
              {comments.map(comment => (
                <CommentItem
                  key={comment.id}
                  comment={comment}
                  postType={postType}
                  postId={postId}
                  onDelete={handleDeleteComment}
                  onReplyAdded={handleCommentAdded}
                />
              ))}
            </div>
          ) : (
            <p className="text-purple-400/40 font-mono text-sm text-center py-4">No comments yet. Be the first!</p>
          )}
        </div>
      )}
    </div>
  );
};

// Enhanced Post Card Component (for Groups, Pages, Updates)
const PostCard = ({ post, postType, onUpdate }) => {
  const { user } = useAuth();
  const [localReactions, setLocalReactions] = useState(post.reactions || {});
  const [localReactionCounts, setLocalReactionCounts] = useState(post.reaction_counts || {});
  
  // Calculate user's reaction without useEffect
  const userReaction = useMemo(() => {
    for (const [type, users] of Object.entries(localReactions)) {
      if (users && users.includes(user?.id)) {
        return type;
      }
    }
    return null;
  }, [localReactions, user?.id]);

  const handleReactionUpdate = (newReaction, newReactions, newCounts) => {
    if (newReactions) setLocalReactions(newReactions);
    if (newCounts) setLocalReactionCounts(newCounts);
    onUpdate && onUpdate();
  };

  return (
    <div className="p-4 bg-slate-900/80 rounded-lg border border-purple-500/20 hover:border-purple-500/40 transition-colors" data-testid={`post-card-${post.id}`}>
      {/* Post Header */}
      <div className="flex items-center gap-3 mb-3">
        <div className="w-10 h-10 bg-gradient-to-br from-pink-500/20 to-purple-500/20 rounded-full flex items-center justify-center">
          <User className="w-5 h-5 text-pink-400" />
        </div>
        <div className="flex-1">
          <p className="text-purple-300 font-mono font-bold">{post.username}</p>
          <p className="text-purple-400/40 font-mono text-xs">{new Date(post.created_at).toLocaleString()}</p>
        </div>
      </div>
      
      {/* Post Content */}
      <p className="text-purple-300/90 font-mono whitespace-pre-wrap mb-3">{post.content}</p>
      
      {/* Post Image */}
      {post.image_url && (
        <img src={post.image_url} alt="Post" className="w-full rounded-lg mb-3 max-h-96 object-cover" />
      )}
      
      {/* Reactions & Comments Bar */}
      <div className="flex items-center gap-4 pt-3 border-t border-purple-500/20">
        <ReactionButton
          postType={postType}
          postId={post.id}
          reactions={localReactions}
          reactionCounts={localReactionCounts}
          userReaction={userReaction}
          onUpdate={handleReactionUpdate}
        />
        <CommentsSection
          postType={postType}
          postId={post.id}
          initialCount={post.comment_count || 0}
        />
      </div>
    </div>
  );
};

// Updates Section Component (for Ultimate Search Page)
const UpdatesSection = () => {
  const { user } = useAuth();
  const [updates, setUpdates] = useState([]);
  const [loading, setLoading] = useState(true);
  const [newUpdate, setNewUpdate] = useState("");
  const [posting, setPosting] = useState(false);
  const [showUpdates, setShowUpdates] = useState(true);

  useEffect(() => {
    fetchUpdates();
  }, []);

  const fetchUpdates = async () => {
    try {
      const res = await axios.get(`${API}/updates`);
      setUpdates(res.data.updates || []);
    } catch (error) {
      console.error("Failed to fetch updates");
    } finally {
      setLoading(false);
    }
  };

  const handlePost = async (e) => {
    e.preventDefault();
    if (!newUpdate.trim()) return;
    setPosting(true);
    try {
      await axios.post(`${API}/updates`, { content: newUpdate.trim() });
      setNewUpdate("");
      fetchUpdates();
      toast.success("Update posted!");
    } catch (error) {
      toast.error("Failed to post update");
    } finally {
      setPosting(false);
    }
  };

  const handleDeleteUpdate = async (updateId) => {
    if (!window.confirm("Delete this update?")) return;
    try {
      await axios.delete(`${API}/updates/${updateId}`);
      toast.success("Update deleted");
      fetchUpdates();
    } catch (error) {
      toast.error("Failed to delete update");
    }
  };

  return (
    <FuturisticFrame title="📝 YOUR UPDATES" color="pink" className="bg-slate-900/80 border border-pink-500/30 rounded-lg">
      {/* Create Update Form */}
      <form onSubmit={handlePost} className="mb-4">
        <div className="flex gap-3">
          <div className="w-10 h-10 bg-gradient-to-br from-pink-500/20 to-purple-500/20 rounded-full flex items-center justify-center flex-shrink-0">
            <User className="w-5 h-5 text-pink-400" />
          </div>
          <div className="flex-1">
            <textarea
              value={newUpdate}
              onChange={(e) => setNewUpdate(e.target.value)}
              placeholder="What's on your mind? Share an update with your network..."
              className="w-full px-4 py-3 bg-slate-950 border border-purple-500/30 rounded-lg text-purple-300 font-mono h-20 focus:border-pink-500 resize-none"
              data-testid="update-input"
            />
            <div className="flex justify-end mt-2">
              <button
                type="submit"
                disabled={posting || !newUpdate.trim()}
                className="px-6 py-2 bg-gradient-to-r from-pink-600 to-purple-600 text-white font-mono rounded hover:scale-[1.02] disabled:opacity-50 flex items-center gap-2"
                data-testid="update-submit"
              >
                {posting ? <Loader2 className="w-4 h-4 animate-spin" /> : <Send className="w-4 h-4" />}
                POST UPDATE
              </button>
            </div>
          </div>
        </div>
      </form>

      {/* Updates List */}
      <div className="border-t border-purple-500/20 pt-4">
        <div className="flex items-center justify-between mb-3">
          <button
            onClick={() => setShowUpdates(!showUpdates)}
            className="text-purple-400 font-mono text-sm flex items-center gap-2 hover:text-pink-400"
          >
            {showUpdates ? <ChevronDown className="w-4 h-4" /> : <ChevronRight className="w-4 h-4" />}
            {updates.length} Update{updates.length !== 1 ? 's' : ''}
          </button>
        </div>

        {showUpdates && (
          loading ? (
            <div className="flex justify-center py-8">
              <Loader2 className="w-8 h-8 text-pink-400 animate-spin" />
            </div>
          ) : updates.length === 0 ? (
            <div className="text-center py-8">
              <MessageCircle className="w-12 h-12 text-purple-400/30 mx-auto mb-2" />
              <p className="text-purple-400/60 font-mono text-sm">No updates yet. Share your first update!</p>
            </div>
          ) : (
            <div className="space-y-4 max-h-96 overflow-y-auto">
              {updates.map((update) => (
                <div key={update.id} className="relative">
                  <PostCard post={update} postType="update" onUpdate={fetchUpdates} />
                  {update.user_id === user?.id && (
                    <button
                      onClick={() => handleDeleteUpdate(update.id)}
                      className="absolute top-4 right-4 p-2 text-red-400/60 hover:text-red-400 hover:bg-red-500/10 rounded"
                      title="Delete update"
                    >
                      <Trash2 className="w-4 h-4" />
                    </button>
                  )}
                </div>
              ))}
            </div>
          )
        )}
      </div>
    </FuturisticFrame>
  );
};

// ============================================
// PROTOCOL RECOMMENDATIONS COMPONENTS
// ============================================

// Suggest Change Modal - For recommending changes to public protocols
const SuggestChangeModal = ({ category, onClose, onSuccess }) => {
  const [originalProtocol] = useState(category.protocol_string || "");
  const [suggestedProtocol, setSuggestedProtocol] = useState(category.protocol_string || "");
  const [reason, setReason] = useState("");
  const [submitting, setSubmitting] = useState(false);

  const handleSubmit = async (e) => {
    e.preventDefault();
    if (!reason.trim()) {
      toast.error("Please provide a reason for your suggestion");
      return;
    }
    if (suggestedProtocol === originalProtocol) {
      toast.error("Please make changes to the protocol");
      return;
    }
    setSubmitting(true);
    try {
      await axios.post(`${API}/categories/${category.id}/recommendations`, {
        original_protocol: originalProtocol,
        suggested_protocol: suggestedProtocol,
        reason: reason.trim()
      });
      toast.success("Recommendation submitted successfully!");
      onSuccess && onSuccess();
      onClose();
    } catch (error) {
      toast.error(error.response?.data?.detail || "Failed to submit recommendation");
    } finally {
      setSubmitting(false);
    }
  };

  return (
    <div className="fixed inset-0 bg-black/80 backdrop-blur-sm flex items-center justify-center z-50 p-4">
      <div className="bg-slate-900 border border-purple-500/30 rounded-lg p-6 max-w-2xl w-full max-h-[90vh] overflow-y-auto">
        <div className="flex items-center justify-between mb-6">
          <h3 className="text-xl font-bold text-transparent bg-clip-text bg-gradient-to-r from-pink-400 to-purple-400 font-mono">
            SUGGEST PROTOCOL CHANGE
          </h3>
          <button onClick={onClose} className="text-purple-400 hover:text-pink-400">
            <X className="w-6 h-6" />
          </button>
        </div>

        <div className="mb-4 p-3 bg-purple-500/10 border border-purple-500/20 rounded">
          <p className="text-purple-400 font-mono text-sm">Category: <span className="text-pink-400">{category.name}</span></p>
        </div>

        <form onSubmit={handleSubmit} className="space-y-4">
          <div>
            <label className="block text-purple-400 font-mono text-sm mb-2">ORIGINAL PROTOCOL</label>
            <textarea
              value={originalProtocol}
              readOnly
              className="w-full px-4 py-3 bg-slate-950/50 border border-purple-500/20 rounded text-purple-300/60 font-mono h-24 resize-none cursor-not-allowed"
            />
          </div>

          <div>
            <label className="block text-purple-400 font-mono text-sm mb-2">YOUR SUGGESTED PROTOCOL</label>
            <textarea
              value={suggestedProtocol}
              onChange={(e) => setSuggestedProtocol(e.target.value)}
              placeholder="Modify the protocol above..."
              className="w-full px-4 py-3 bg-slate-950 border border-pink-500/30 rounded text-purple-300 font-mono h-24 resize-none focus:border-pink-500 focus:outline-none"
              required
              data-testid="suggest-protocol-input"
            />
          </div>

          <div>
            <label className="block text-purple-400 font-mono text-sm mb-2">REASON FOR CHANGE</label>
            <textarea
              value={reason}
              onChange={(e) => setReason(e.target.value)}
              placeholder="Explain why this change would improve the protocol..."
              className="w-full px-4 py-3 bg-slate-950 border border-purple-500/30 rounded text-purple-300 font-mono h-24 resize-none focus:border-pink-500 focus:outline-none"
              required
              maxLength={1000}
              data-testid="suggest-reason-input"
            />
            <p className="text-purple-400/40 font-mono text-xs mt-1">{reason.length}/1000 characters</p>
          </div>

          <div className="flex gap-3 pt-4">
            <button
              type="button"
              onClick={onClose}
              className="flex-1 px-4 py-3 border border-purple-500/30 text-purple-400 font-mono rounded hover:bg-purple-500/10"
            >
              CANCEL
            </button>
            <button
              type="submit"
              disabled={submitting}
              className="flex-1 px-4 py-3 bg-gradient-to-r from-pink-600 to-purple-600 text-white font-mono rounded hover:scale-[1.02] disabled:opacity-50 flex items-center justify-center gap-2"
              data-testid="submit-suggestion-btn"
            >
              {submitting ? <Loader2 className="w-5 h-5 animate-spin" /> : <Send className="w-5 h-5" />}
              SUBMIT RECOMMENDATION
            </button>
          </div>
        </form>
      </div>
    </div>
  );
};

// View Recommendations Modal - For owners to see recommendations
const ViewRecommendationsModal = ({ category, onClose, onUpdate }) => {
  const [recommendations, setRecommendations] = useState([]);
  const [loading, setLoading] = useState(true);
  const [updating, setUpdating] = useState(null);

  useEffect(() => {
    fetchRecommendations();
  }, [category.id]);

  const fetchRecommendations = async () => {
    try {
      const res = await axios.get(`${API}/categories/${category.id}/recommendations`);
      setRecommendations(res.data.recommendations || []);
    } catch (error) {
      toast.error("Failed to load recommendations");
    } finally {
      setLoading(false);
    }
  };

  const handleStatusUpdate = async (recId, status) => {
    setUpdating(recId);
    try {
      await axios.put(`${API}/recommendations/${recId}/status?status=${status}`);
      toast.success(`Recommendation ${status}`);
      fetchRecommendations();
      onUpdate && onUpdate();
    } catch (error) {
      toast.error("Failed to update status");
    } finally {
      setUpdating(null);
    }
  };

  const handleDelete = async (recId) => {
    if (!window.confirm("Delete this recommendation?")) return;
    try {
      await axios.delete(`${API}/recommendations/${recId}`);
      toast.success("Recommendation deleted");
      fetchRecommendations();
      onUpdate && onUpdate();
    } catch (error) {
      toast.error("Failed to delete");
    }
  };

  const handleApplyChange = async (rec) => {
    if (!window.confirm("Apply this protocol change? This will update your category's protocol.")) return;
    try {
      await axios.put(`${API}/categories/${category.id}`, {
        protocol_string: rec.suggested_protocol
      });
      await handleStatusUpdate(rec.id, "accepted");
      toast.success("Protocol updated with recommended change!");
    } catch (error) {
      toast.error("Failed to apply change");
    }
  };

  const statusColors = {
    pending: "bg-yellow-500/20 text-yellow-400 border-yellow-500/30",
    accepted: "bg-green-500/20 text-green-400 border-green-500/30",
    rejected: "bg-red-500/20 text-red-400 border-red-500/30"
  };

  return (
    <div className="fixed inset-0 bg-black/80 backdrop-blur-sm flex items-center justify-center z-50 p-4">
      <div className="bg-slate-900 border border-purple-500/30 rounded-lg p-6 max-w-3xl w-full max-h-[90vh] overflow-y-auto">
        <div className="flex items-center justify-between mb-6">
          <div>
            <h3 className="text-xl font-bold text-transparent bg-clip-text bg-gradient-to-r from-pink-400 to-purple-400 font-mono">
              PROTOCOL RECOMMENDATIONS
            </h3>
            <p className="text-purple-400/60 font-mono text-sm mt-1">For: {category.name}</p>
          </div>
          <button onClick={onClose} className="text-purple-400 hover:text-pink-400">
            <X className="w-6 h-6" />
          </button>
        </div>

        {loading ? (
          <div className="flex justify-center py-12">
            <Loader2 className="w-8 h-8 text-pink-400 animate-spin" />
          </div>
        ) : recommendations.length === 0 ? (
          <div className="text-center py-12">
            <MessageCircle className="w-16 h-16 text-purple-400/30 mx-auto mb-4" />
            <p className="text-purple-400/60 font-mono">No recommendations yet</p>
          </div>
        ) : (
          <div className="space-y-4">
            {recommendations.map((rec) => (
              <div key={rec.id} className="bg-slate-950 border border-purple-500/20 rounded-lg p-4">
                <div className="flex items-start justify-between mb-3">
                  <div className="flex items-center gap-2">
                    <User className="w-4 h-4 text-pink-400" />
                    <span className="text-purple-300 font-mono text-sm font-bold">{rec.username}</span>
                    <span className="text-purple-400/40 font-mono text-xs">{new Date(rec.created_at).toLocaleDateString()}</span>
                  </div>
                  <span className={`px-2 py-1 text-xs rounded font-mono border ${statusColors[rec.status]}`}>
                    {rec.status.toUpperCase()}
                  </span>
                </div>

                <div className="grid grid-cols-1 md:grid-cols-2 gap-4 mb-3">
                  <div>
                    <p className="text-purple-400/60 font-mono text-xs mb-1">ORIGINAL:</p>
                    <p className="text-purple-300/70 font-mono text-sm bg-slate-900 p-2 rounded break-all">{rec.original_protocol}</p>
                  </div>
                  <div>
                    <p className="text-pink-400/60 font-mono text-xs mb-1">SUGGESTED:</p>
                    <p className="text-pink-300 font-mono text-sm bg-pink-500/10 p-2 rounded break-all">{rec.suggested_protocol}</p>
                  </div>
                </div>

                <div className="mb-4">
                  <p className="text-purple-400/60 font-mono text-xs mb-1">REASON:</p>
                  <p className="text-purple-300/80 font-mono text-sm">{rec.reason}</p>
                </div>

                {rec.status === "pending" && (
                  <div className="flex gap-2 pt-3 border-t border-purple-500/20">
                    <button
                      onClick={() => handleApplyChange(rec)}
                      disabled={updating === rec.id}
                      className="px-4 py-2 bg-gradient-to-r from-green-600 to-emerald-600 text-white font-mono text-sm rounded hover:scale-[1.02] disabled:opacity-50 flex items-center gap-2"
                      data-testid={`apply-rec-${rec.id}`}
                    >
                      {updating === rec.id ? <Loader2 className="w-4 h-4 animate-spin" /> : <Check className="w-4 h-4" />}
                      APPLY CHANGE
                    </button>
                    <button
                      onClick={() => handleStatusUpdate(rec.id, "rejected")}
                      disabled={updating === rec.id}
                      className="px-4 py-2 border border-red-500/30 text-red-400 font-mono text-sm rounded hover:bg-red-500/10 flex items-center gap-2"
                    >
                      <X className="w-4 h-4" /> REJECT
                    </button>
                    <button
                      onClick={() => handleDelete(rec.id)}
                      className="px-4 py-2 text-purple-400/60 hover:text-red-400 font-mono text-sm rounded hover:bg-red-500/10 ml-auto"
                    >
                      <Trash2 className="w-4 h-4" />
                    </button>
                  </div>
                )}
              </div>
            ))}
          </div>
        )}
      </div>
    </div>
  );
};

// Recommendation Badge - Shows pending count on categories
const RecommendationBadge = ({ categoryId, isOwner, onClick }) => {
  const [count, setCount] = useState({ total: 0, pending: 0 });

  const fetchCount = useCallback(async () => {
    try {
      const res = await axios.get(`${API}/categories/${categoryId}/recommendations/count`);
      setCount({ total: res.data.count, pending: res.data.pending });
    } catch (error) {
      console.error("Failed to fetch recommendation count");
    }
  }, [categoryId]);

  useEffect(() => {
    if (isOwner) {
      fetchCount();
    }
  }, [isOwner, fetchCount]);

  if (!isOwner || count.total === 0) return null;

  return (
    <button
      onClick={onClick}
      className="relative p-1.5 text-yellow-400 hover:text-yellow-300 hover:bg-yellow-500/10 rounded transition-colors"
      title={`${count.pending} pending recommendation${count.pending !== 1 ? 's' : ''}`}
      data-testid={`rec-badge-${categoryId}`}
    >
      <Lightbulb className="w-4 h-4" />
      {count.pending > 0 && (
        <span className="absolute -top-1 -right-1 w-4 h-4 bg-yellow-500 text-black text-xs font-bold rounded-full flex items-center justify-center">
          {count.pending}
        </span>
      )}
    </button>
  );
};

// ============================================
// PRIVATE MESSAGING COMPONENTS
// ============================================

const MAX_IMAGE_SIZE_MB = 8;
const MAX_IMAGE_SIZE_BYTES = MAX_IMAGE_SIZE_MB * 1024 * 1024;

// Messages Page Component
const MessagesPage = () => {
  const { user, token } = useAuth();
  const [conversations, setConversations] = useState([]);
  const [selectedConversation, setSelectedConversation] = useState(null);
  const [messages, setMessages] = useState([]);
  const [newMessage, setNewMessage] = useState("");
  const [imagePreview, setImagePreview] = useState(null);
  const [imageData, setImageData] = useState(null);
  const [loading, setLoading] = useState(true);
  const [sending, setSending] = useState(false);
  const [searchQuery, setSearchQuery] = useState("");
  const [searchResults, setSearchResults] = useState([]);
  const [searching, setSearching] = useState(false);
  const [showNewConversation, setShowNewConversation] = useState(false);
  const [isTyping, setIsTyping] = useState(null);
  const [wsConnected, setWsConnected] = useState(false);
  const messagesEndRef = React.useRef(null);
  const fileInputRef = React.useRef(null);
  const wsRef = React.useRef(null);
  const typingTimeoutRef = React.useRef(null);

  // WebSocket connection
  useEffect(() => {
    if (!token) return;
    
    // Construct WebSocket URL from API URL
    // API is like https://infonavigator.preview.emergentagent.com/api
    // WebSocket should be wss://xxx.preview.emergentagent.com/ws/messages/{token}
    let wsUrl;
    try {
      const apiUrl = new URL(API);
      const wsProtocol = apiUrl.protocol === 'https:' ? 'wss:' : 'ws:';
      wsUrl = `${wsProtocol}//${apiUrl.host}/ws/messages/${token}`;
    } catch (e) {
      // Fallback for relative URLs
      const wsProtocol = window.location.protocol === 'https:' ? 'wss:' : 'ws:';
      wsUrl = `${wsProtocol}//${window.location.host}/ws/messages/${token}`;
    }
    
    console.log('WebSocket URL:', wsUrl);
    
    const connectWebSocket = () => {
      try {
        wsRef.current = new WebSocket(wsUrl);
        
        wsRef.current.onopen = () => {
          console.log('WebSocket connected');
          setWsConnected(true);
        };
        
        wsRef.current.onmessage = (event) => {
          const data = JSON.parse(event.data);
          
          if (data.type === 'new_message') {
            // Add new message if in current conversation
            if (selectedConversation && 
                (data.message.sender_id === selectedConversation.other_user?.id || 
                 data.message.recipient_id === selectedConversation.other_user?.id)) {
              setMessages(prev => [...prev, data.message]);
            }
            // Refresh conversations list
            fetchConversations();
            // Show notification toast for new messages
            if (data.message.sender_id !== user?.id) {
              toast.success(`💬 New message from ${data.sender_username}`);
            }
          }
          
          if (data.type === 'typing' && selectedConversation?.other_user?.id === data.sender_id) {
            setIsTyping(data.sender_username);
            // Clear typing after 3 seconds
            if (typingTimeoutRef.current) clearTimeout(typingTimeoutRef.current);
            typingTimeoutRef.current = setTimeout(() => setIsTyping(null), 3000);
          }
          
          if (data.type === 'read_receipt') {
            // Could update message read status here
          }
        };
        
        wsRef.current.onclose = () => {
          console.log('WebSocket disconnected');
          setWsConnected(false);
          // Reconnect after 5 seconds
          setTimeout(connectWebSocket, 5000);
        };
        
        wsRef.current.onerror = (error) => {
          console.error('WebSocket error:', error);
        };
      } catch (error) {
        console.error('WebSocket connection failed:', error);
      }
    };
    
    connectWebSocket();
    
    // Ping to keep connection alive
    const pingInterval = setInterval(() => {
      if (wsRef.current?.readyState === WebSocket.OPEN) {
        wsRef.current.send(JSON.stringify({ type: 'ping' }));
      }
    }, 30000);
    
    return () => {
      clearInterval(pingInterval);
      if (wsRef.current) {
        wsRef.current.close();
      }
    };
  }, [token, selectedConversation]);

  useEffect(() => {
    fetchConversations();
    // Fallback polling (less frequent when WS is connected)
    const interval = setInterval(fetchConversations, wsConnected ? 30000 : 10000);
    return () => clearInterval(interval);
  }, [wsConnected]);

  useEffect(() => {
    messagesEndRef.current?.scrollIntoView({ behavior: "smooth" });
  }, [messages]);

  // Send typing indicator
  const sendTypingIndicator = () => {
    if (wsRef.current?.readyState === WebSocket.OPEN && selectedConversation?.other_user?.id) {
      wsRef.current.send(JSON.stringify({
        type: 'typing',
        recipient_id: selectedConversation.other_user.id
      }));
    }
  };

  const fetchConversations = async () => {
    try {
      const res = await axios.get(`${API}/messages/conversations`);
      setConversations(res.data.conversations || []);
    } catch (error) {
      console.error("Failed to fetch conversations");
    } finally {
      setLoading(false);
    }
  };

  const fetchMessages = async (otherUserId) => {
    try {
      const res = await axios.get(`${API}/messages/conversation/${otherUserId}`);
      setMessages(res.data.messages || []);
      setSelectedConversation({
        id: res.data.conversation_id,
        other_user: res.data.other_user
      });
    } catch (error) {
      toast.error("Failed to load messages");
    }
  };

  const handleSendMessage = async (e) => {
    e.preventDefault();
    if (!newMessage.trim() && !imageData) return;
    if (!selectedConversation?.other_user?.id) return;

    setSending(true);
    try {
      const res = await axios.post(`${API}/messages/send`, {
        recipient_id: selectedConversation.other_user.id,
        content: newMessage.trim() || (imageData ? "📷 Image" : ""),
        image_url: imageData
      });
      setNewMessage("");
      setImagePreview(null);
      setImageData(null);
      // Message will be added via WebSocket, but add immediately for responsiveness
      if (res.data.data) {
        setMessages(prev => [...prev, res.data.data]);
      }
      fetchConversations();
    } catch (error) {
      toast.error(error.response?.data?.detail || "Failed to send message");
    } finally {
      setSending(false);
    }
  };

  const handleMessageInput = (e) => {
    setNewMessage(e.target.value);
    sendTypingIndicator();
  };

  const handleImageSelect = (e) => {
    const file = e.target.files?.[0];
    if (!file) return;

    if (file.size > MAX_IMAGE_SIZE_BYTES) {
      toast.error(`Image must be less than ${MAX_IMAGE_SIZE_MB}MB`);
      return;
    }

    if (!file.type.startsWith("image/")) {
      toast.error("Please select an image file");
      return;
    }

    const reader = new FileReader();
    reader.onload = (e) => {
      setImagePreview(e.target.result);
      setImageData(e.target.result);
    };
    reader.readAsDataURL(file);
  };

  const handleSearchUsers = async (query) => {
    setSearchQuery(query);
    if (query.length < 1) {
      setSearchResults([]);
      return;
    }
    setSearching(true);
    try {
      const res = await axios.get(`${API}/users/search?q=${encodeURIComponent(query)}`);
      setSearchResults(res.data.users || []);
    } catch (error) {
      console.error("Search failed");
    } finally {
      setSearching(false);
    }
  };

  const startConversation = (otherUser) => {
    setSelectedConversation({
      id: null,
      other_user: otherUser
    });
    setMessages([]);
    setShowNewConversation(false);
    setSearchQuery("");
    setSearchResults([]);
  };

  const getOtherParticipant = (conv) => {
    const otherId = conv.participants.find(p => p !== user?.id);
    return {
      id: otherId,
      username: conv.participant_usernames?.[otherId] || "Unknown"
    };
  };

  return (
    <Layout>
      <div className="max-w-6xl mx-auto">
        <div className="flex items-center justify-between mb-6">
          <div>
            <h1 className="text-3xl font-bold text-transparent bg-clip-text bg-gradient-to-r from-pink-400 to-purple-400 font-mono tracking-wider mb-2">MESSAGES</h1>
            <p className="text-purple-300/80 font-mono text-sm">Private conversations with other pilots</p>
          </div>
          <button
            onClick={() => setShowNewConversation(true)}
            className="px-4 py-2 bg-gradient-to-r from-pink-600 to-purple-600 text-white font-mono rounded hover:scale-[1.02] flex items-center gap-2"
            data-testid="new-message-btn"
          >
            <Plus className="w-5 h-5" /> NEW MESSAGE
          </button>
        </div>

        <div className="grid grid-cols-1 lg:grid-cols-3 gap-4 h-[calc(100vh-250px)] min-h-[500px]">
          {/* Conversations List */}
          <div className="bg-slate-900/80 border border-purple-500/30 rounded-lg overflow-hidden">
            <div className="p-3 border-b border-purple-500/20">
              <h3 className="text-purple-400 font-mono text-sm font-bold">CONVERSATIONS</h3>
            </div>
            <div className="overflow-y-auto h-full">
              {loading ? (
                <div className="flex justify-center py-8">
                  <Loader2 className="w-6 h-6 text-pink-400 animate-spin" />
                </div>
              ) : conversations.length === 0 ? (
                <div className="text-center py-8 px-4">
                  <MessageCircle className="w-12 h-12 text-purple-400/30 mx-auto mb-2" />
                  <p className="text-purple-400/60 font-mono text-sm">No conversations yet</p>
                  <p className="text-purple-400/40 font-mono text-xs mt-1">Start a new message!</p>
                </div>
              ) : (
                conversations.map((conv) => {
                  const other = getOtherParticipant(conv);
                  return (
                    <button
                      key={conv.id}
                      onClick={() => fetchMessages(other.id)}
                      className={`w-full p-3 text-left hover:bg-purple-500/10 border-b border-purple-500/10 transition-colors ${
                        selectedConversation?.other_user?.id === other.id ? 'bg-purple-500/20' : ''
                      }`}
                      data-testid={`conv-${conv.id}`}
                    >
                      <div className="flex items-center gap-3">
                        <div className="w-10 h-10 bg-gradient-to-br from-pink-500/20 to-purple-500/20 rounded-full flex items-center justify-center flex-shrink-0">
                          <User className="w-5 h-5 text-pink-400" />
                        </div>
                        <div className="flex-1 min-w-0">
                          <div className="flex items-center justify-between">
                            <span className="text-purple-300 font-mono font-bold text-sm truncate">{other.username}</span>
                            {conv.unread_count > 0 && (
                              <span className="w-5 h-5 bg-pink-500 text-white text-xs font-bold rounded-full flex items-center justify-center">
                                {conv.unread_count}
                              </span>
                            )}
                          </div>
                          <p className="text-purple-400/60 font-mono text-xs truncate">{conv.last_message}</p>
                        </div>
                      </div>
                    </button>
                  );
                })
              )}
            </div>
          </div>

          {/* Chat Area */}
          <div className="lg:col-span-2 bg-slate-900/80 border border-purple-500/30 rounded-lg flex flex-col overflow-hidden">
            {selectedConversation ? (
              <>
                {/* Chat Header */}
                <div className="p-4 border-b border-purple-500/20 flex items-center gap-3">
                  <div className="w-10 h-10 bg-gradient-to-br from-pink-500/20 to-purple-500/20 rounded-full flex items-center justify-center">
                    <User className="w-5 h-5 text-pink-400" />
                  </div>
                  <div>
                    <p className="text-purple-300 font-mono font-bold">{selectedConversation.other_user?.username}</p>
                    <p className="text-purple-400/40 font-mono text-xs">Private conversation</p>
                  </div>
                </div>

                {/* Messages */}
                <div className="flex-1 overflow-y-auto p-4 space-y-4">
                  {messages.length === 0 ? (
                    <div className="text-center py-8">
                      <MessageCircle className="w-12 h-12 text-purple-400/30 mx-auto mb-2" />
                      <p className="text-purple-400/60 font-mono text-sm">No messages yet. Say hello!</p>
                    </div>
                  ) : (
                    messages.map((msg) => (
                      <div
                        key={msg.id}
                        className={`flex ${msg.sender_id === user?.id ? 'justify-end' : 'justify-start'}`}
                      >
                        <div className={`max-w-[70%] ${msg.sender_id === user?.id ? 'bg-gradient-to-r from-pink-600 to-purple-600' : 'bg-slate-800'} rounded-lg p-3`}>
                          {msg.image_url && (
                            <img
                              src={msg.image_url}
                              alt="Attached"
                              className="max-w-full rounded mb-2 max-h-64 object-cover cursor-pointer"
                              onClick={() => window.open(msg.image_url, '_blank')}
                            />
                          )}
                          <p className="text-white font-mono text-sm whitespace-pre-wrap break-words">{msg.content}</p>
                          <p className={`text-xs mt-1 ${msg.sender_id === user?.id ? 'text-white/60' : 'text-purple-400/60'} font-mono`}>
                            {new Date(msg.created_at).toLocaleTimeString()}
                          </p>
                        </div>
                      </div>
                    ))
                  )}
                  <div ref={messagesEndRef} />
                </div>

                {/* Image Preview */}
                {imagePreview && (
                  <div className="px-4 py-2 border-t border-purple-500/20">
                    <div className="relative inline-block">
                      <img src={imagePreview} alt="Preview" className="max-h-32 rounded" />
                      <button
                        onClick={() => { setImagePreview(null); setImageData(null); }}
                        className="absolute -top-2 -right-2 w-6 h-6 bg-red-500 text-white rounded-full flex items-center justify-center hover:bg-red-600"
                      >
                        <X className="w-4 h-4" />
                      </button>
                    </div>
                  </div>
                )}

                {/* Message Input */}
                <form onSubmit={handleSendMessage} className="p-4 border-t border-purple-500/20 flex gap-2">
                  <input
                    type="file"
                    ref={fileInputRef}
                    onChange={handleImageSelect}
                    accept="image/*"
                    className="hidden"
                  />
                  <button
                    type="button"
                    onClick={() => fileInputRef.current?.click()}
                    className="p-3 text-purple-400 hover:text-pink-400 hover:bg-pink-500/10 rounded-lg transition-colors"
                    title="Attach image (max 8MB)"
                  >
                    <Image className="w-5 h-5" />
                  </button>
                  <input
                    type="text"
                    value={newMessage}
                    onChange={handleMessageInput}
                    placeholder="Type a message..."
                    className="flex-1 px-4 py-3 bg-slate-950 border border-purple-500/30 rounded-lg text-purple-300 font-mono focus:border-pink-500 focus:outline-none"
                    data-testid="message-input"
                  />
                  <button
                    type="submit"
                    disabled={sending || (!newMessage.trim() && !imageData)}
                    className="px-4 py-3 bg-gradient-to-r from-pink-600 to-purple-600 text-white rounded-lg hover:scale-[1.02] disabled:opacity-50 flex items-center gap-2"
                    data-testid="send-message-btn"
                  >
                    {sending ? <Loader2 className="w-5 h-5 animate-spin" /> : <Send className="w-5 h-5" />}
                  </button>
                </form>
                
                {/* Typing Indicator */}
                {isTyping && (
                  <div className="px-4 py-2 text-purple-400/60 font-mono text-sm animate-pulse">
                    {isTyping} is typing...
                  </div>
                )}
                
                {/* WebSocket Connection Status */}
                <div className={`px-4 py-1 text-xs font-mono flex items-center gap-2 ${wsConnected ? 'text-green-400/60' : 'text-yellow-400/60'}`}>
                  <span className={`w-2 h-2 rounded-full ${wsConnected ? 'bg-green-400' : 'bg-yellow-400 animate-pulse'}`}></span>
                  {wsConnected ? 'Real-time connected' : 'Connecting...'}
                </div>
              </>
            ) : (
              <div className="flex-1 flex items-center justify-center">
                <div className="text-center">
                  <MessageCircle className="w-16 h-16 text-purple-400/30 mx-auto mb-4" />
                  <p className="text-purple-400/60 font-mono">Select a conversation or start a new one</p>
                </div>
              </div>
            )}
          </div>
        </div>

        {/* New Conversation Modal */}
        {showNewConversation && (
          <div className="fixed inset-0 bg-black/80 backdrop-blur-sm flex items-center justify-center z-50 p-4">
            <div className="bg-slate-900 border border-purple-500/30 rounded-lg p-6 max-w-md w-full">
              <div className="flex items-center justify-between mb-4">
                <h3 className="text-xl font-bold text-transparent bg-clip-text bg-gradient-to-r from-pink-400 to-purple-400 font-mono">NEW MESSAGE</h3>
                <button onClick={() => setShowNewConversation(false)} className="text-purple-400 hover:text-pink-400">
                  <X className="w-6 h-6" />
                </button>
              </div>

              <div className="mb-4">
                <label className="block text-purple-400 font-mono text-sm mb-2">Search Users</label>
                <input
                  type="text"
                  value={searchQuery}
                  onChange={(e) => handleSearchUsers(e.target.value)}
                  placeholder="Type a username..."
                  className="w-full px-4 py-3 bg-slate-950 border border-purple-500/30 rounded-lg text-purple-300 font-mono focus:border-pink-500 focus:outline-none"
                  data-testid="user-search-input"
                />
              </div>

              {searching ? (
                <div className="flex justify-center py-4">
                  <Loader2 className="w-6 h-6 text-pink-400 animate-spin" />
                </div>
              ) : searchResults.length > 0 ? (
                <div className="space-y-2 max-h-60 overflow-y-auto">
                  {searchResults.map((u) => (
                    <button
                      key={u.id}
                      onClick={() => startConversation(u)}
                      className="w-full p-3 bg-slate-950 border border-purple-500/20 rounded-lg hover:border-pink-500/50 transition-colors flex items-center gap-3"
                      data-testid={`user-result-${u.id}`}
                    >
                      <div className="w-10 h-10 bg-gradient-to-br from-pink-500/20 to-purple-500/20 rounded-full flex items-center justify-center">
                        <User className="w-5 h-5 text-pink-400" />
                      </div>
                      <div className="text-left">
                        <p className="text-purple-300 font-mono font-bold">{u.username}</p>
                        <p className="text-purple-400/40 font-mono text-xs">{u.email}</p>
                      </div>
                    </button>
                  ))}
                </div>
              ) : searchQuery.length > 0 ? (
                <p className="text-purple-400/60 font-mono text-sm text-center py-4">No users found</p>
              ) : null}
            </div>
          </div>
        )}

        <BookSalesBanner variant="compact" />
      </div>
    </Layout>
  );
};

// Sale Countdown Timer
const SaleCountdown = ({ endDate }) => {
  const [timeLeft, setTimeLeft] = useState({ days: 0, hours: 0, minutes: 0, seconds: 0 });
  
  useEffect(() => {
    const calculateTimeLeft = () => {
      const end = new Date(endDate);
      const now = new Date();
      const diff = end - now;
      
      if (diff > 0) {
        setTimeLeft({
          days: Math.floor(diff / (1000 * 60 * 60 * 24)),
          hours: Math.floor((diff % (1000 * 60 * 60 * 24)) / (1000 * 60 * 60)),
          minutes: Math.floor((diff % (1000 * 60 * 60)) / (1000 * 60)),
          seconds: Math.floor((diff % (1000 * 60)) / 1000)
        });
      }
    };
    
    calculateTimeLeft();
    const timer = setInterval(calculateTimeLeft, 1000);
    return () => clearInterval(timer);
  }, [endDate]);
  
  return (
    <div className="flex items-center justify-center gap-2 text-sm font-mono">
      <Clock className="w-4 h-4 text-pink-400" />
      <span className="text-purple-300">Sale ends in:</span>
      <span className="text-pink-400 font-bold">{timeLeft.days}d {timeLeft.hours}h {timeLeft.minutes}m {timeLeft.seconds}s</span>
    </div>
  );
};

// Welcome Sale Banner - Now promotes the book instead
const WelcomeSaleBanner = ({ onUpgrade, compact }) => {
  const { user } = useAuth();
  const navigate = useNavigate();
  
  // App is now free - promote the book instead
  if (compact) {
    return (
      <div className="p-3 bg-gradient-to-r from-pink-900/30 to-purple-900/30 rounded-lg border border-pink-500/30 flex items-center justify-between">
        <div className="flex items-center gap-3">
          <img src={IMAGES.bookCoverMain} alt="Letters to Evelyn" className="w-12 h-16 object-cover rounded shadow-lg" />
          <div>
            <p className="text-pink-400 font-mono text-sm font-bold">📚 NEW BOOK!</p>
            <p className="text-purple-300 font-mono text-xs">Letters to Evelyn - $2.99</p>
          </div>
        </div>
        <button onClick={() => navigate("/book")} className="px-4 py-2 bg-gradient-to-r from-pink-600 to-purple-600 text-white font-mono text-sm rounded hover:scale-105 transition-transform">
          GET BOOK
        </button>
      </div>
    );
  }
  
  return (
    <div className="p-6 bg-gradient-to-r from-pink-900/40 via-purple-900/40 to-blue-900/40 rounded-xl border-2 border-pink-500/50">
      <div className="flex items-center justify-center gap-3 mb-4">
        <Book className="w-8 h-8 text-pink-400" />
        <Sparkles className="w-6 h-6 text-yellow-400 animate-pulse" />
      </div>
      <div className="text-center">
        <div className="bg-gradient-to-r from-pink-500 to-purple-500 text-white px-4 py-1 rounded-full text-sm font-bold inline-block mb-3">📖 FEATURED BOOK</div>
        <h3 className="text-2xl font-bold text-transparent bg-clip-text bg-gradient-to-r from-pink-400 to-purple-400 font-mono mb-2">LETTERS TO EVELYN</h3>
        <p className="text-purple-300/80 font-mono text-sm mb-1">A True Supernatural Thriller Comedy</p>
        <p className="text-pink-300 font-mono text-lg font-bold">Only $2.99</p>
        <p className="text-yellow-400 font-mono text-xs mb-4">⭐⭐⭐⭐⭐ 19 Five-Star Reviews</p>
        <button onClick={() => navigate("/book")} className="px-8 py-3 bg-gradient-to-r from-pink-600 via-purple-600 to-blue-600 text-white font-bold font-mono tracking-wider rounded-lg hover:scale-105 transition-transform flex items-center justify-center gap-2 mx-auto">
          <ShoppingCart className="w-5 h-5" /> VIEW BOOK
        </button>
      </div>
    </div>
  );
};

// MEGA Book Sales Banner - New Design
const BookSalesBanner = ({ variant = "full" }) => {
  const [currentImage, setCurrentImage] = useState(0);
  const bookImages = [IMAGES.bookCoverMain, IMAGES.bookCover1, IMAGES.bookCover2, IMAGES.bookCover3, IMAGES.bookCover4];
  
  useEffect(() => {
    const timer = setInterval(() => {
      setCurrentImage((prev) => (prev + 1) % bookImages.length);
    }, 4000);
    return () => clearInterval(timer);
  }, []);
  
  const openAmazon = () => window.open(BOOK_INFO.amazonUrl, '_blank');
  
  if (variant === "compact") {
    return (
      <div className="bg-gradient-to-r from-purple-900/40 to-blue-900/40 border border-purple-500/50 rounded-lg p-4 cursor-pointer hover:scale-[1.02] transition-transform" onClick={openAmazon}>
        <div className="flex items-center gap-4">
          <img src={IMAGES.bookCoverMain} alt="Letters to Evelyn" className="w-20 h-28 object-cover rounded-lg shadow-lg shadow-purple-500/30" />
          <div className="flex-1">
            <div className="flex items-center gap-2">
              <h3 className="text-pink-400 font-mono font-bold">LETTERS TO EVELYN</h3>
              <div className="flex">
                {[...Array(5)].map((_, i) => <Star key={i} className="w-3 h-3 fill-yellow-400 text-yellow-400" />)}
              </div>
            </div>
            <p className="text-purple-300 text-xs font-mono">19 Five-Star Reviews • Supernatural Thriller Comedy</p>
            <p className="text-blue-300/70 text-xs font-mono italic mt-1">"A profound and unforgettable literary piece"</p>
          </div>
          <button className="px-4 py-2 bg-gradient-to-r from-purple-600 to-pink-600 text-white font-mono text-sm rounded hover:scale-105 transition-transform flex items-center gap-1">
            <ShoppingCart className="w-4 h-4" />
            GET BOOK
          </button>
        </div>
      </div>
    );
  }
  
  return (
    <div className="bg-gradient-to-br from-purple-900/50 via-blue-900/40 to-pink-900/50 border-2 border-purple-500 rounded-xl overflow-hidden">
      <div className="p-6">
        <div className="flex flex-col lg:flex-row gap-6">
          {/* Book Images Gallery */}
          <div className="lg:w-1/3 flex flex-col items-center gap-4">
            <div className="relative group cursor-pointer" onClick={openAmazon}>
              <img 
                src={bookImages[currentImage]} 
                alt="Letters to Evelyn" 
                className="w-full max-w-xs rounded-lg shadow-2xl shadow-purple-500/40 group-hover:scale-105 transition-transform"
              />
              <div className="absolute top-2 right-2 bg-gradient-to-r from-yellow-500 to-orange-500 text-black px-2 py-1 rounded font-bold text-xs">
                ⭐ 19 FIVE-STAR REVIEWS
              </div>
            </div>
            {/* Thumbnail Gallery */}
            <div className="flex gap-2">
              {bookImages.map((img, idx) => (
                <button 
                  key={idx} 
                  onClick={() => setCurrentImage(idx)}
                  className={`w-12 h-16 rounded overflow-hidden border-2 transition-all ${currentImage === idx ? 'border-pink-500 scale-110' : 'border-purple-500/30 opacity-60 hover:opacity-100'}`}
                >
                  <img src={img} alt={`Book cover ${idx + 1}`} className="w-full h-full object-cover" />
                </button>
              ))}
            </div>
          </div>
          
          {/* Book Info */}
          <div className="lg:w-2/3">
            <div className="flex items-center gap-2 mb-2">
              <h2 className="text-3xl font-bold text-transparent bg-clip-text bg-gradient-to-r from-pink-400 via-purple-400 to-blue-400 font-mono">
                LETTERS TO EVELYN
              </h2>
            </div>
            
            <p className="text-purple-300 font-mono mb-2">By World Record Aviation Holder <span className="text-pink-400 font-bold">John Selman</span></p>
            
            <div className="flex items-center gap-4 mb-4">
              <div className="flex">
                {[...Array(5)].map((_, i) => <Star key={i} className="w-5 h-5 fill-yellow-400 text-yellow-400" />)}
              </div>
              <span className="text-yellow-400 font-mono font-bold">5.0 / 5.0</span>
              <span className="text-purple-300 font-mono text-sm">(19 Professional Reviews)</span>
            </div>
            
            <p className="text-xl text-pink-300 font-mono italic mb-4">
              "{BOOK_INFO.tagline}"
            </p>
            
            <p className="text-purple-300/80 font-mono text-sm mb-4">
              {BOOK_INFO.genre} • {BOOK_INFO.years}
            </p>
            
            {/* Review Quote */}
            <div className="bg-slate-900/50 rounded-lg p-4 mb-4 border-l-4 border-pink-500">
              <p className="text-purple-200/90 font-mono text-sm italic">
                "{BOOK_INFO.quotes[0].text}"
              </p>
              <p className="text-pink-400 font-mono text-xs mt-2">— {BOOK_INFO.quotes[0].author}</p>
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
                className="px-6 py-3 bg-gradient-to-r from-purple-600 to-pink-600 text-white font-mono rounded-lg hover:scale-105 transition-transform flex items-center gap-2"
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

// Sidebar Navigation - Futuristic Theme
const Sidebar = ({ isOpen, setIsOpen }) => {
  const { user, logout } = useAuth();
  const navigate = useNavigate();
  const location = useLocation();

  const menuItems = [
    { path: "/", icon: Home, label: "COMMAND CENTER" },
    { path: "/infopilot", icon: Radar, label: "INFOPILOT SEARCH" },
    { path: "/ultimate-search", icon: Target, label: "ULTIMATE SEARCH" },
    { path: "/categories", icon: FolderTree, label: "CATEGORIES" },
    { path: "/marketplace", icon: ShoppingCart, label: "MARKETPLACE", highlight: true },
    { path: "/messages", icon: MessageCircle, label: "MESSAGES" },
    { path: "/friends", icon: Users, label: "FRIENDS" },
    { path: "/groups", icon: Users, label: "GROUPS" },
    { path: "/pages", icon: FileText, label: "PAGES" },
    { path: "/statistics", icon: BarChart3, label: "INTEL STATS" },
    { path: "/global-database", icon: Globe, label: "GLOBAL DATABASE" },
    { path: "/book", icon: Book, label: "📚 GET THE BOOK", highlight: true },
  ];

  // Always add admin link for admin users - check both is_admin and role
  if (user?.is_admin || user?.role === 'admin') {
    menuItems.push({ path: "/admin", icon: Shield, label: "⚙️ ADMIN CONTROL", highlight: true });
  }

  // Debug logging
  console.log("Sidebar user:", user?.username, "is_admin:", user?.is_admin, "role:", user?.role);

  return (
    <>
      {isOpen && <div className="fixed inset-0 bg-black/70 z-40 lg:hidden" onClick={() => setIsOpen(false)} />}
      
      <aside className={`fixed top-0 left-0 h-full bg-gradient-to-b from-slate-950 via-purple-950/50 to-slate-950 border-r border-purple-500/30 z-50 transition-transform duration-300 w-72 flex flex-col ${isOpen ? "translate-x-0" : "-translate-x-full lg:translate-x-0"}`}>
        {/* Header - Fixed */}
        <div className="p-6 border-b border-purple-500/30 flex-shrink-0">
          <div className="flex items-center justify-between">
            <div className="flex items-center gap-3">
              <div className="w-12 h-12 bg-gradient-to-br from-pink-500/20 to-purple-500/20 border-2 border-pink-500 rounded-lg flex items-center justify-center relative">
                <Plane className="w-7 h-7 text-pink-400" />
                <div className="absolute -top-1 -right-1 w-3 h-3 bg-blue-400 rounded-full animate-pulse"></div>
              </div>
              <div>
                <h1 className="text-xl font-bold text-transparent bg-clip-text bg-gradient-to-r from-pink-400 to-purple-400 font-mono tracking-wider">INFOPILOT EXPLORER</h1>
                <p className="text-xs text-purple-400/60 font-mono">TACTICAL SEARCH v2.0</p>
              </div>
            </div>
            <button className="lg:hidden text-purple-400" onClick={() => setIsOpen(false)}>
              <X className="w-6 h-6" />
            </button>
          </div>
        </div>

        {/* Scrollable Navigation */}
        <nav className="flex-1 overflow-y-auto p-4 space-y-1 scrollbar-thin scrollbar-thumb-purple-500/30 scrollbar-track-transparent">
          {menuItems.map((item) => (
            <button
              key={item.path}
              onClick={() => { navigate(item.path); setIsOpen(false); }}
              className={`w-full flex items-center gap-3 px-4 py-3 rounded transition-all font-mono text-sm
                ${location.pathname === item.path
                  ? "bg-purple-500/20 text-pink-400 border border-pink-500/50"
                  : item.highlight
                    ? "text-pink-400 hover:bg-pink-500/10 border border-pink-500/30"
                    : "text-purple-300/70 hover:bg-purple-500/10 hover:text-purple-300 border border-transparent"
                }`}
              data-testid={`nav-${item.path.replace('/', '')}`}
            >
              <item.icon className="w-5 h-5" />
              <span className="tracking-wider">{item.label}</span>
            </button>
          ))}
          
          {/* Sidebar Book Promo - Inside scrollable area */}
          <div className="mt-4 p-3 bg-gradient-to-r from-pink-500/20 to-purple-500/20 rounded-lg border border-pink-500/50">
            <p className="text-pink-400 font-mono text-xs text-center">
              📚 NEW: <span className="font-bold">Letters to Evelyn</span>
            </p>
            <p className="text-purple-400/60 font-mono text-xs text-center mt-1">Only $2.99!</p>
          </div>
        </nav>

        {/* User Section - Fixed at bottom */}
        <div className="p-4 border-t border-purple-500/30 bg-slate-950/90 flex-shrink-0">
          <div className="flex items-center gap-3 mb-4">
            <div className="w-10 h-10 bg-gradient-to-br from-purple-500/20 to-pink-500/20 border border-purple-500 rounded-full flex items-center justify-center text-pink-400 font-bold font-mono">
              {user?.username?.[0]?.toUpperCase() || "P"}
            </div>
            <div className="flex-1 min-w-0">
              <p className="font-mono text-purple-300 text-sm truncate">{user?.username}</p>
              {/* Show admin badge if user is admin */}
              {user?.is_admin ? (
                <span className="px-2 py-0.5 rounded text-xs font-mono bg-pink-500/20 border border-pink-500/50 text-pink-400 flex items-center gap-1">
                  <Shield className="w-3 h-3" /> ADMIN
                </span>
              ) : (
                <span className="px-2 py-0.5 rounded text-xs font-mono bg-green-500/20 border border-green-500/50 text-green-400 flex items-center gap-1">
                  <Check className="w-3 h-3" /> FULL ACCESS
                </span>
              )}
            </div>
          </div>
          <button
            onClick={logout}
            className="w-full flex items-center justify-center gap-2 px-4 py-2 text-red-400 hover:bg-red-500/10 rounded transition-colors font-mono text-sm border border-red-500/30"
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
    <div className="min-h-screen bg-gradient-to-br from-slate-950 via-purple-950/30 to-slate-950">
      <Sidebar isOpen={sidebarOpen} setIsOpen={setSidebarOpen} />
      <header className="lg:hidden fixed top-0 left-0 right-0 h-16 bg-slate-950/90 border-b border-purple-500/30 z-30 flex items-center px-4 backdrop-blur">
        <button onClick={() => setSidebarOpen(true)} className="p-2 text-purple-400">
          <Menu className="w-6 h-6" />
        </button>
        <div className="flex items-center gap-2 ml-4">
          <Plane className="w-6 h-6 text-pink-400" />
          <span className="font-bold text-lg text-transparent bg-clip-text bg-gradient-to-r from-pink-400 to-purple-400 font-mono">INFOPILOT EXPLORER</span>
        </div>
      </header>
      <main className="lg:ml-72 pt-16 lg:pt-0 min-h-screen">
        <div className="p-4 lg:p-8">{children}</div>
      </main>
    </div>
  );
};

// Login Page - Futuristic Theme
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
    <div className="min-h-screen bg-gradient-to-br from-slate-950 via-purple-950 to-slate-950 flex items-center justify-center p-4 relative overflow-hidden">
      {/* Background effects */}
      <div className="absolute inset-0 opacity-20">
        <div className="absolute top-20 left-20 w-64 h-64 border border-pink-500/30 rounded-full animate-pulse"></div>
        <div className="absolute bottom-20 right-20 w-96 h-96 border border-purple-500/20 rounded-full animate-pulse"></div>
        <div className="absolute top-1/2 left-1/2 w-48 h-48 border border-blue-500/20 rounded-full animate-spin" style={{animationDuration: '20s'}}></div>
      </div>

      <div className="w-full max-w-md relative z-10">
        <div className="text-center mb-8">
          <div className="inline-flex items-center justify-center w-20 h-20 bg-gradient-to-br from-pink-500/20 to-purple-500/20 border-2 border-pink-500 rounded-xl mb-4 relative">
            <Plane className="w-12 h-12 text-pink-400" />
          </div>
          <h1 className="text-4xl font-bold text-transparent bg-clip-text bg-gradient-to-r from-pink-400 via-purple-400 to-blue-400 font-mono tracking-wider">INFOPILOT EXPLORER</h1>
          <p className="text-purple-400/80 mt-2 font-mono text-sm">TACTICAL INFORMATION EXCHANGE SYSTEM</p>
        </div>

        {/* Book Promotion Banner on Login Page */}
        <div className="mb-6 p-4 bg-gradient-to-r from-pink-500/20 via-purple-500/20 to-blue-500/20 rounded-lg border border-pink-500/50">
          <p className="text-center text-pink-300 font-mono font-bold">
            📚 NEW BOOK: "Letters to Evelyn" - A Supernatural Thriller Comedy
          </p>
          <p className="text-center text-purple-400/70 font-mono text-xs mt-1">⭐⭐⭐⭐⭐ 19 Five-Star Reviews • Only $2.99</p>
        </div>

        <FuturisticFrame title="AUTHENTICATION" color="pink" className="bg-slate-900/90 backdrop-blur border border-purple-500/30 rounded-lg">
          <div className="flex mb-6">
            <button onClick={() => setIsLogin(true)} className={`flex-1 py-3 text-center font-mono text-sm tracking-wider transition-colors rounded-l ${isLogin ? "bg-pink-500/20 text-pink-400 border border-pink-500" : "bg-slate-900 text-purple-400/50 border border-purple-500/20"}`}>LOGIN</button>
            <button onClick={() => setIsLogin(false)} className={`flex-1 py-3 text-center font-mono text-sm tracking-wider transition-colors rounded-r ${!isLogin ? "bg-pink-500/20 text-pink-400 border border-pink-500" : "bg-slate-900 text-purple-400/50 border border-purple-500/20"}`}>REGISTER</button>
          </div>

          <form onSubmit={handleSubmit} className="space-y-4">
            {!isLogin && (
              <div>
                <label className="block text-xs font-mono text-purple-400 mb-1 tracking-wider">CALLSIGN</label>
                <input type="text" value={username} onChange={(e) => setUsername(e.target.value)} className="w-full px-4 py-3 bg-slate-950 border border-purple-500/30 rounded text-purple-300 font-mono focus:border-pink-500 focus:outline-none" required={!isLogin} data-testid="username-input" />
              </div>
            )}
            <div>
              <label className="block text-xs font-mono text-purple-400 mb-1 tracking-wider">EMAIL</label>
              <input type="email" value={email} onChange={(e) => setEmail(e.target.value)} className="w-full px-4 py-3 bg-slate-950 border border-purple-500/30 rounded text-purple-300 font-mono focus:border-pink-500 focus:outline-none" required data-testid="email-input" />
            </div>
            <div>
              <label className="block text-xs font-mono text-purple-400 mb-1 tracking-wider">PASSWORD</label>
              <input type="password" value={password} onChange={(e) => setPassword(e.target.value)} className="w-full px-4 py-3 bg-slate-950 border border-purple-500/30 rounded text-purple-300 font-mono focus:border-pink-500 focus:outline-none" required data-testid="password-input" />
            </div>
            <button type="submit" disabled={loading} className="w-full py-3 bg-gradient-to-r from-pink-600 to-purple-600 text-white font-mono tracking-wider rounded hover:scale-[1.02] transition-all disabled:opacity-50" data-testid="submit-btn">
              {loading ? <Loader2 className="w-5 h-5 animate-spin mx-auto" /> : isLogin ? "AUTHENTICATE" : "CREATE ACCOUNT"}
            </button>
          </form>

          <div className="mt-6">
            <div className="relative"><div className="absolute inset-0 flex items-center"><div className="w-full border-t border-purple-500/20"></div></div><div className="relative flex justify-center text-xs"><span className="px-2 bg-slate-900 text-purple-400/60 font-mono">OR</span></div></div>
            <div className="mt-4 flex justify-center">
              <GoogleLogin onSuccess={handleGoogleLogin} onError={() => toast.error("Google Sign-In failed")} theme="filled_black" size="large" text="continue_with" shape="rectangular" />
            </div>
          </div>
        </FuturisticFrame>

        {/* Book Promo */}
        <div className="mt-6">
          <BookSalesBanner variant="compact" />
        </div>
      </div>
    </div>
  );
};

// Home Page - SALES FOCUSED with New Theme
const HomePage = () => {
  const { user } = useAuth();
  const navigate = useNavigate();

  return (
    <Layout>
      <div className="max-w-5xl mx-auto space-y-6">
        {/* Welcome Sale Promo - TOP PRIORITY */}
        <WelcomeSaleBanner onUpgrade={() => navigate("/subscribe")} />

        {/* Welcome */}
        <FuturisticFrame title="COMMAND CENTER" color="purple" className="bg-slate-900/80 border border-purple-500/30 rounded-lg">
          <div className="flex flex-col md:flex-row items-center gap-6">
            <img src={IMAGES.globe} alt="InfoPilot Explorer Global Network" className="w-32 h-32 rounded-lg border border-purple-500/50 object-cover shadow-lg shadow-purple-500/30" />
            <div className="flex-1">
              <h1 className="text-3xl font-bold text-transparent bg-clip-text bg-gradient-to-r from-pink-400 to-purple-400 font-mono tracking-wider mb-2">WELCOME, {user?.username?.toUpperCase()}</h1>
              <p className="text-purple-300/80 mb-4 font-mono text-sm">Your tactical gateway to the World Wide Web Information Exchange.</p>
              <div className="flex flex-wrap gap-3">
                <button onClick={() => navigate("/infopilot")} className="px-6 py-3 bg-purple-500/20 border border-purple-500 text-purple-300 font-mono tracking-wider rounded hover:bg-purple-500/30 transition-all flex items-center gap-2" data-testid="start-searching-btn">
                  <Radar className="w-5 h-5" /> BEGIN SEARCH
                </button>
                {!user?.is_paid && (
                  <button onClick={() => navigate("/subscribe")} className="px-6 py-3 bg-gradient-to-r from-pink-600 to-purple-600 text-white font-mono tracking-wider rounded hover:scale-105 transition-transform flex items-center gap-2 animate-pulse">
                    <Crown className="w-5 h-5" /> SALE: $0.75
                  </button>
                )}
              </div>
            </div>
          </div>
        </FuturisticFrame>

        {/* Book Promo - FULL */}
        <BookSalesBanner variant="full" />

        {/* Quick Actions */}
        <div className="grid md:grid-cols-3 gap-4">
          <QuickActionCard title="CREATE CATEGORIES" icon={FolderTree} onClick={() => navigate("/categories")} color="purple" />
          <QuickActionCard title="SEARCH & COLLATE" icon={Radar} onClick={() => navigate("/infopilot")} color="pink" />
          <QuickActionCard title="VIEW INTEL" icon={BarChart3} onClick={() => navigate("/statistics")} color="blue" />
        </div>

        {/* Book CTA - Replaced subscription CTA */}
        <div className="text-center p-6 bg-gradient-to-r from-pink-900/30 to-purple-900/30 rounded-lg border border-pink-500/30">
          <h3 className="text-2xl font-bold text-transparent bg-clip-text bg-gradient-to-r from-pink-400 to-purple-400 font-mono mb-2">📚 Support the Developer!</h3>
          <p className="text-purple-300 font-mono mb-4">Love InfoPilot Explorer? Check out my book "Letters to Evelyn" - A supernatural thriller comedy!</p>
          <button onClick={() => navigate("/book")} className="px-8 py-4 bg-gradient-to-r from-pink-600 via-purple-600 to-blue-600 text-white font-bold font-mono tracking-wider rounded-lg hover:scale-105 transition-transform flex items-center justify-center gap-2 mx-auto">
            <Book className="w-5 h-5" /> VIEW BOOK - $2.99
          </button>
        </div>
      </div>
    </Layout>
  );
};

const QuickActionCard = ({ title, icon: Icon, onClick, color = "purple" }) => {
  const colorClasses = { 
    purple: "border-purple-500/30 hover:border-purple-500 text-purple-400", 
    pink: "border-pink-500/30 hover:border-pink-500 text-pink-400", 
    blue: "border-blue-500/30 hover:border-blue-500 text-blue-400",
    red: "border-red-500/30 hover:border-red-500 text-red-400"
  };
  return (
    <button onClick={onClick} className={`bg-slate-900/80 p-6 rounded-lg border ${colorClasses[color]} transition-all hover:scale-[1.02] text-left group`}>
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
          <h1 className="text-3xl font-bold text-transparent bg-clip-text bg-gradient-to-r from-pink-400 to-purple-400 font-mono tracking-wider mb-2">INFOPILOT SEARCH</h1>
          <p className="text-purple-300/80 font-mono text-sm">Search the web and automatically categorize results.</p>
        </div>

        {/* Subscription Promo */}
        <WelcomeSaleBanner onUpgrade={() => navigate("/subscribe")} compact />

        {/* Search Box */}
        <FuturisticFrame title="SEARCH PARAMETERS" color="pink" className="bg-slate-900/80 border border-purple-500/30 rounded-lg">
          <div className="flex gap-4">
            <input type="text" value={searchQuery} onChange={(e) => setSearchQuery(e.target.value)} placeholder="Enter search query..." className="flex-1 px-4 py-3 bg-slate-950 border border-purple-500/30 rounded text-purple-300 font-mono focus:border-pink-500 focus:outline-none" onKeyPress={(e) => e.key === "Enter" && handleCollate()} data-testid="search-input" />
            <button onClick={handleCollate} disabled={loading} className="px-6 py-3 bg-gradient-to-r from-pink-600 to-purple-600 text-white font-mono tracking-wider rounded hover:scale-[1.02] transition-all disabled:opacity-50 flex items-center gap-2" data-testid="collate-btn">
              {loading ? <Loader2 className="w-5 h-5 animate-spin" /> : <Radar className="w-5 h-5" />} COLLATE
            </button>
          </div>
          {categories.length > 0 && (
            <div className="mt-4">
              <p className="text-xs text-purple-400/60 mb-2 font-mono">ACTIVE PROTOCOLS ({categories.length}):</p>
              <div className="flex flex-wrap gap-2">
                {categories.slice(0, 5).map((cat) => (<span key={cat.id} className="px-3 py-1 bg-purple-500/10 border border-purple-500/30 text-purple-300 rounded text-xs font-mono">{cat.name}</span>))}
              </div>
              <p className="text-xs text-green-400/60 mt-3 font-mono flex items-center gap-1">
                <Check className="w-3 h-3" /> All protocols are case insensitive
              </p>
            </div>
          )}
        </FuturisticFrame>

        {/* Book Promo */}
        <BookSalesBanner variant="compact" />

        {/* Results */}
        {results && (
          <FuturisticFrame title="COLLATED RESULTS" color="purple" className="bg-slate-900/80 border border-purple-500/30 rounded-lg">
            <p className="text-purple-300 font-mono text-sm mb-4">{results.categorized_count} of {results.total_searched} targets categorized</p>
            {results.results.length > 0 ? (
              <div className="space-y-4">{results.results.map((result) => (<SearchResultCard key={result.id} result={result} />))}</div>
            ) : (<p className="text-pink-400 text-center py-8 font-mono">NO MATCHES FOUND</p>)}
          </FuturisticFrame>
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
    <div className="bg-slate-950 p-4 rounded border border-purple-500/20 hover:border-pink-500/50 transition-colors">
      <a href={result.url} target="_blank" rel="noopener noreferrer" className="text-pink-400 hover:underline font-mono text-sm block truncate">{result.title}</a>
      <p className="text-purple-300/60 text-xs mt-1 line-clamp-2 font-mono">{result.snippet}</p>
      <div className="flex flex-wrap gap-2 mt-2">
        <span className="px-2 py-0.5 bg-pink-500/20 text-pink-400 text-xs rounded font-mono">{result.article_type}</span>
        <span className="px-2 py-0.5 bg-slate-900 text-purple-400/60 text-xs rounded font-mono">{result.domain}</span>
      </div>
      {showReactions && (
        <div className="flex gap-2 mt-3 pt-3 border-t border-purple-500/10">
          {[{ type: "like", icon: ThumbsUp }, { type: "love", icon: Heart }, { type: "best", icon: Award }].map(({ type, icon: Icon }) => (
            <button key={type} onClick={() => handleReaction(type)} disabled={reacting} className="flex items-center gap-1 px-2 py-1 text-xs text-purple-400/60 hover:text-pink-400 rounded transition-colors font-mono">
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
  const [newCategory, setNewCategory] = useState({ name: "", protocol: "", parentId: null, isPublic: true, forSale: false, price: 0.75 });
  const [creating, setCreating] = useState(false);
  const [updating, setUpdating] = useState(false);
  const [viewRecsCategory, setViewRecsCategory] = useState(null);
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
      await axios.post(`${API}/categories`, { 
        name: newCategory.name, 
        protocol: { protocol_string: newCategory.protocol }, 
        parent_id: newCategory.parentId || null, 
        is_public: newCategory.isPublic,
        for_sale: !newCategory.isPublic && newCategory.forSale,
        price: (!newCategory.isPublic && newCategory.forSale) ? newCategory.price : null
      });
      toast.success("CATEGORY CREATED");
      setShowCreate(false);
      setNewCategory({ name: "", protocol: "", parentId: null, isPublic: true, forSale: false, price: 0.75 });
      fetchCategories();
    } catch (error) { toast.error(error.response?.data?.detail || "CREATION FAILED"); }
    finally { setCreating(false); }
  };

  const handleEdit = (cat) => { 
    setEditingCategory({ 
      id: cat.id, 
      name: cat.name, 
      protocol_string: cat.protocol_string, 
      is_public: cat.is_public,
      for_sale: cat.for_sale || false,
      price: cat.price || 0.75
    }); 
    setShowEdit(true); 
  };

  const handleUpdate = async (e) => {
    e.preventDefault();
    if (!editingCategory) return;
    setUpdating(true);
    try {
      await axios.put(`${API}/categories/${editingCategory.id}`, { 
        name: editingCategory.name, 
        protocol_string: editingCategory.protocol_string, 
        is_public: editingCategory.is_public,
        for_sale: !editingCategory.is_public && editingCategory.for_sale,
        price: (!editingCategory.is_public && editingCategory.for_sale) ? editingCategory.price : null
      });
      toast.success("CATEGORY UPDATED");
      setShowEdit(false);
      setEditingCategory(null);
      fetchCategories();
    } catch (error) { toast.error(error.response?.data?.detail || "UPDATE FAILED"); }
    finally { setUpdating(false); }
  };

  const handleToggleSale = async (cat) => {
    try {
      const newForSale = !cat.for_sale;
      await axios.put(`${API}/categories/${cat.id}/sale-settings?for_sale=${newForSale}&price=${cat.price || 0.75}`);
      toast.success(newForSale ? "Protocol listed for sale!" : "Protocol removed from sale");
      fetchCategories();
    } catch (error) {
      toast.error(error.response?.data?.detail || "Failed to update sale settings");
    }
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
            <h1 className="text-3xl font-bold text-transparent bg-clip-text bg-gradient-to-r from-pink-400 to-purple-400 font-mono tracking-wider mb-2">CATEGORIES</h1>
            <p className="text-purple-300/80 font-mono text-sm">Manage your InfoPilot 2.0 protocols.</p>
          </div>
          <button onClick={() => setShowCreate(true)} className="px-4 py-2 bg-gradient-to-r from-pink-600 to-purple-600 text-white font-mono tracking-wider rounded hover:scale-[1.02] transition-colors flex items-center gap-2" data-testid="create-category-btn">
            <Plus className="w-5 h-5" /> NEW CATEGORY
          </button>
        </div>

        <WelcomeSaleBanner onUpgrade={() => navigate("/subscribe")} compact />

        {/* Create Modal */}
        {showCreate && (
          <div className="fixed inset-0 bg-black/80 flex items-center justify-center z-50 p-4">
            <FuturisticFrame title="CREATE CATEGORY" color="pink" className="bg-slate-900 border border-pink-500/30 rounded-lg max-w-lg w-full max-h-[90vh] overflow-y-auto">
              <form onSubmit={handleCreate} className="space-y-4">
                <div><label className="block text-xs font-mono text-purple-400 mb-1">CATEGORY NAME</label><input type="text" value={newCategory.name} onChange={(e) => setNewCategory({ ...newCategory, name: e.target.value })} className="w-full px-4 py-2 bg-slate-950 border border-purple-500/30 rounded text-purple-300 font-mono focus:border-pink-500" required /></div>
                <div>
                  <label className="block text-xs font-mono text-purple-400 mb-1">INFOPILOT 2.0 PROTOCOL</label>
                  <textarea value={newCategory.protocol} onChange={(e) => setNewCategory({ ...newCategory, protocol: e.target.value })} placeholder="(word1 or word2) & (word3)+ & (excluded)^" className="w-full px-4 py-2 bg-slate-950 border border-purple-500/30 rounded text-purple-300 font-mono h-24 focus:border-pink-500" required />
                  
                  {/* Case Insensitive Notice */}
                  <div className="mt-2 p-3 bg-green-500/10 border border-green-500/30 rounded-lg">
                    <p className="text-green-400 font-mono text-xs font-bold flex items-center gap-2">
                      <Check className="w-4 h-4" /> CASE INSENSITIVE
                    </p>
                    <p className="text-green-400/80 font-mono text-xs mt-1">
                      All protocols are case insensitive! "Science" = "science" = "SCIENCE"
                    </p>
                    <p className="text-purple-400/60 font-mono text-xs mt-1">
                      Syntax: (word1 or word2) & (required)+ & (excluded)^
                    </p>
                  </div>
                </div>
                <div className="flex items-center gap-2">
                  <input type="checkbox" id="isPublic" checked={newCategory.isPublic} onChange={(e) => setNewCategory({ ...newCategory, isPublic: e.target.checked, forSale: false })} className="rounded bg-slate-950 border-purple-500/30" />
                  <label htmlFor="isPublic" className="text-sm text-purple-300 font-mono">Make public (anyone can view)</label>
                </div>
                
                {/* Sell Options - Only for Private Protocols */}
                {!newCategory.isPublic && (
                  <div className="p-4 bg-yellow-500/10 border border-yellow-500/30 rounded-lg space-y-3">
                    <div className="flex items-center gap-2">
                      <DollarSign className="w-4 h-4 text-yellow-400" />
                      <span className="text-yellow-400 font-mono text-sm font-bold">MONETIZATION OPTIONS</span>
                    </div>
                    <div className="flex items-center gap-2">
                      <input type="checkbox" id="forSale" checked={newCategory.forSale} onChange={(e) => setNewCategory({ ...newCategory, forSale: e.target.checked })} className="rounded bg-slate-950 border-yellow-500/30" />
                      <label htmlFor="forSale" className="text-sm text-purple-300 font-mono">List for sale (users pay to view/copy)</label>
                    </div>
                    {newCategory.forSale && (
                      <div>
                        <label className="block text-xs font-mono text-yellow-400 mb-1">PRICE (USD)</label>
                        <div className="flex items-center gap-2">
                          <span className="text-yellow-400 font-mono">$</span>
                          <input 
                            type="number" 
                            value={newCategory.price} 
                            onChange={(e) => setNewCategory({ ...newCategory, price: Math.max(0.75, Math.min(2.99, parseFloat(e.target.value) || 0.75)) })}
                            min="0.75" 
                            max="2.99" 
                            step="0.01"
                            className="w-24 px-3 py-2 bg-slate-950 border border-yellow-500/30 rounded text-yellow-400 font-mono focus:border-yellow-500" 
                          />
                        </div>
                        <p className="text-xs text-purple-400/60 mt-1 font-mono">Price range: $0.75 - $2.99</p>
                      </div>
                    )}
                  </div>
                )}

                <div className="flex gap-4">
                  <button type="button" onClick={() => setShowCreate(false)} className="flex-1 px-4 py-2 border border-purple-500/30 text-purple-300 font-mono rounded hover:bg-purple-500/10">CANCEL</button>
                  <button type="submit" disabled={creating} className="flex-1 px-4 py-2 bg-gradient-to-r from-pink-600 to-purple-600 text-white font-mono rounded hover:scale-[1.02] disabled:opacity-50">{creating ? <Loader2 className="w-5 h-5 animate-spin mx-auto" /> : "CREATE"}</button>
                </div>
              </form>
            </FuturisticFrame>
          </div>
        )}

        {/* Edit Modal */}
        {showEdit && editingCategory && (
          <div className="fixed inset-0 bg-black/80 flex items-center justify-center z-50 p-4">
            <FuturisticFrame title="EDIT CATEGORY" color="blue" className="bg-slate-900 border border-blue-500/30 rounded-lg max-w-lg w-full max-h-[90vh] overflow-y-auto">
              <form onSubmit={handleUpdate} className="space-y-4">
                <div><label className="block text-xs font-mono text-blue-400 mb-1">CATEGORY NAME</label><input type="text" value={editingCategory.name} onChange={(e) => setEditingCategory({ ...editingCategory, name: e.target.value })} className="w-full px-4 py-2 bg-slate-950 border border-blue-500/30 rounded text-purple-300 font-mono focus:border-blue-500" required /></div>
                <div>
                  <label className="block text-xs font-mono text-blue-400 mb-1">INFOPILOT 2.0 PROTOCOL</label>
                  <textarea value={editingCategory.protocol_string} onChange={(e) => setEditingCategory({ ...editingCategory, protocol_string: e.target.value })} className="w-full px-4 py-2 bg-slate-950 border border-blue-500/30 rounded text-purple-300 font-mono h-32 focus:border-blue-500" required />
                  
                  {/* Case Insensitive Notice */}
                  <div className="mt-2 p-3 bg-green-500/10 border border-green-500/30 rounded-lg">
                    <p className="text-green-400 font-mono text-xs font-bold flex items-center gap-2">
                      <Check className="w-4 h-4" /> CASE INSENSITIVE
                    </p>
                    <p className="text-green-400/80 font-mono text-xs mt-1">
                      All protocols are case insensitive! "Science" = "science" = "SCIENCE"
                    </p>
                  </div>
                </div>
                <div className="flex items-center gap-2">
                  <input type="checkbox" id="editIsPublic" checked={editingCategory.is_public} onChange={(e) => setEditingCategory({ ...editingCategory, is_public: e.target.checked, for_sale: false })} className="rounded bg-slate-950 border-blue-500/30" />
                  <label htmlFor="editIsPublic" className="text-sm text-purple-300 font-mono">Make public</label>
                </div>
                
                {/* Sell Options - Only for Private Protocols */}
                {!editingCategory.is_public && (
                  <div className="p-4 bg-yellow-500/10 border border-yellow-500/30 rounded-lg space-y-3">
                    <div className="flex items-center gap-2">
                      <DollarSign className="w-4 h-4 text-yellow-400" />
                      <span className="text-yellow-400 font-mono text-sm font-bold">MONETIZATION OPTIONS</span>
                    </div>
                    <div className="flex items-center gap-2">
                      <input type="checkbox" id="editForSale" checked={editingCategory.for_sale} onChange={(e) => setEditingCategory({ ...editingCategory, for_sale: e.target.checked })} className="rounded bg-slate-950 border-yellow-500/30" />
                      <label htmlFor="editForSale" className="text-sm text-purple-300 font-mono">List for sale</label>
                    </div>
                    {editingCategory.for_sale && (
                      <div>
                        <label className="block text-xs font-mono text-yellow-400 mb-1">PRICE (USD)</label>
                        <div className="flex items-center gap-2">
                          <span className="text-yellow-400 font-mono">$</span>
                          <input 
                            type="number" 
                            value={editingCategory.price} 
                            onChange={(e) => setEditingCategory({ ...editingCategory, price: Math.max(0.75, Math.min(2.99, parseFloat(e.target.value) || 0.75)) })}
                            min="0.75" 
                            max="2.99" 
                            step="0.01"
                            className="w-24 px-3 py-2 bg-slate-950 border border-yellow-500/30 rounded text-yellow-400 font-mono focus:border-yellow-500" 
                          />
                        </div>
                        <p className="text-xs text-purple-400/60 mt-1 font-mono">Price range: $0.75 - $2.99</p>
                      </div>
                    )}
                  </div>
                )}

                <div className="flex gap-4">
                  <button type="button" onClick={() => { setShowEdit(false); setEditingCategory(null); }} className="flex-1 px-4 py-2 border border-purple-500/30 text-purple-300 font-mono rounded hover:bg-purple-500/10">CANCEL</button>
                  <button type="submit" disabled={updating} className="flex-1 px-4 py-2 bg-gradient-to-r from-blue-600 to-purple-600 text-white font-mono rounded hover:scale-[1.02] disabled:opacity-50">{updating ? <Loader2 className="w-5 h-5 animate-spin mx-auto" /> : "UPDATE"}</button>
                </div>
              </form>
            </FuturisticFrame>
          </div>
        )}

        {/* Categories List */}
        {loading ? (<div className="flex justify-center py-12"><Loader2 className="w-8 h-8 animate-spin text-pink-400" /></div>
        ) : categories.length === 0 ? (
          <FuturisticFrame title="NO CATEGORIES" color="purple" className="bg-slate-900/80 border border-purple-500/30 rounded-lg text-center py-12">
            <FolderTree className="w-16 h-16 text-purple-500/30 mx-auto mb-4" />
            <p className="text-purple-300 font-mono mb-4">CREATE YOUR FIRST CATEGORY TO BEGIN</p>
            <button onClick={() => setShowCreate(true)} className="px-6 py-3 bg-gradient-to-r from-pink-600 to-purple-600 text-white font-mono rounded hover:scale-[1.02]">CREATE CATEGORY</button>
          </FuturisticFrame>
        ) : (
          <div className="space-y-3">
            {categories.map((cat) => (
              <div key={cat.id} className="bg-slate-900/80 p-4 rounded border border-purple-500/20 hover:border-pink-500/50 transition-colors">
                <div className="flex items-start justify-between">
                  <div className="flex-1 min-w-0">
                    <button
                      onClick={() => navigate(`/ultimate-search?filter=${cat.id}&name=${encodeURIComponent(cat.name)}`)}
                      className="text-pink-400 font-mono font-bold hover:text-cyan-400 hover:underline transition-colors text-left"
                      title={`Click to view results in "${cat.name}"`}
                      data-testid={`category-link-${cat.id}`}
                    >
                      {cat.name}
                    </button>
                    <p className="text-purple-300/60 text-xs font-mono mt-1 break-all">{cat.protocol_string}</p>
                    <div className="flex items-center gap-2 mt-2">
                      <span className={`inline-block px-2 py-0.5 text-xs rounded font-mono ${cat.is_public ? "bg-purple-500/20 text-purple-400" : "bg-pink-500/20 text-pink-400"}`}>
                        {cat.is_public ? "PUBLIC" : "PRIVATE"}
                      </span>
                      {cat.for_sale && (
                        <span className="inline-flex items-center gap-1 px-2 py-0.5 text-xs rounded font-mono bg-yellow-500/20 text-yellow-400">
                          <DollarSign className="w-3 h-3" /> FOR SALE ${cat.price?.toFixed(2)}
                        </span>
                      )}
                      <span className="px-2 py-0.5 text-xs rounded font-mono bg-blue-500/20 text-blue-400">
                        {cat.result_count || 0} results
                      </span>
                    </div>
                  </div>
                  <div className="flex items-center gap-1 ml-2">
                    <RecommendationBadge 
                      categoryId={cat.id} 
                      isOwner={true} 
                      onClick={() => setViewRecsCategory(cat)} 
                    />
                    {/* Quick sell toggle for private protocols */}
                    {!cat.is_public && (
                      <button 
                        onClick={() => handleToggleSale(cat)} 
                        className={`p-2 rounded hover:bg-yellow-500/10 ${cat.for_sale ? 'text-yellow-400' : 'text-purple-400/60 hover:text-yellow-400'}`} 
                        title={cat.for_sale ? "Remove from sale" : "List for sale"}
                      >
                        <DollarSign className="w-4 h-4" />
                      </button>
                    )}
                    <button onClick={() => handleEdit(cat)} className="p-2 text-purple-400/60 hover:text-pink-400 rounded hover:bg-pink-500/10" title="Edit"><Edit3 className="w-4 h-4" /></button>
                    <button onClick={() => handleDelete(cat.id)} className="p-2 text-red-400/60 hover:text-red-400 rounded hover:bg-red-500/10" title="Delete"><Trash2 className="w-4 h-4" /></button>
                  </div>
                </div>
              </div>
            ))}
          </div>
        )}

        <BookSalesBanner variant="compact" />

        {/* View Recommendations Modal */}
        {viewRecsCategory && (
          <ViewRecommendationsModal 
            category={viewRecsCategory} 
            onClose={() => setViewRecsCategory(null)} 
            onUpdate={fetchCategories}
          />
        )}
      </div>
    </Layout>
  );
};

// ============================================
// PROTOCOL MARKETPLACE PAGE
// ============================================
const MarketplacePage = () => {
  const [activeTab, setActiveTab] = useState("browse");
  const [protocols, setProtocols] = useState([]);
  const [purchases, setPurchases] = useState([]);
  const [sales, setSales] = useState([]);
  const [loading, setLoading] = useState(true);
  const [purchasing, setPurchasing] = useState(null);
  const { user } = useAuth();
  const navigate = useNavigate();

  useEffect(() => {
    fetchData();
  }, [activeTab]);

  const fetchData = async () => {
    setLoading(true);
    try {
      if (activeTab === "browse") {
        const res = await axios.get(`${API}/marketplace/protocols`);
        setProtocols(res.data.protocols || []);
      } else if (activeTab === "purchases") {
        const res = await axios.get(`${API}/marketplace/my-purchases`);
        setPurchases(res.data.purchases || []);
      } else if (activeTab === "sales") {
        const res = await axios.get(`${API}/marketplace/my-sales`);
        setSales(res.data.sales || []);
      }
    } catch (error) {
      toast.error("Failed to load marketplace data");
    } finally {
      setLoading(false);
    }
  };

  const handlePurchase = async (protocolId) => {
    if (!window.confirm("Confirm purchase? You will be able to view and copy this protocol after payment.")) return;
    
    setPurchasing(protocolId);
    try {
      const res = await axios.post(`${API}/marketplace/protocols/${protocolId}/purchase`);
      toast.success(res.data.message);
      
      // Show the protocol
      alert(`Protocol purchased!\n\nProtocol: ${res.data.protocol_string}\n\nThis has been added to your purchases.`);
      
      fetchData();
    } catch (error) {
      toast.error(error.response?.data?.detail || "Purchase failed");
    } finally {
      setPurchasing(null);
    }
  };

  const copyProtocol = async (protocolString, categoryId = null) => {
    try {
      // Track the copy if we have a category ID
      if (categoryId) {
        await axios.post(`${API}/categories/${categoryId}/copy`);
      }
      navigator.clipboard.writeText(protocolString);
      toast.success("Protocol copied to clipboard!");
    } catch (error) {
      // Still copy even if tracking fails
      navigator.clipboard.writeText(protocolString);
      toast.success("Protocol copied!");
    }
  };

  return (
    <Layout>
      <div className="max-w-4xl mx-auto space-y-6">
        <div className="flex items-center justify-between mb-6">
          <div>
            <h1 className="text-3xl font-bold text-transparent bg-clip-text bg-gradient-to-r from-yellow-400 to-orange-400 font-mono tracking-wider mb-2">PROTOCOL MARKETPLACE</h1>
            <p className="text-purple-300/80 font-mono text-sm">Buy and sell private InfoPilot protocols</p>
          </div>
          <button onClick={() => navigate("/categories")} className="px-4 py-2 bg-gradient-to-r from-pink-600 to-purple-600 text-white font-mono tracking-wider rounded hover:scale-[1.02] flex items-center gap-2">
            <Plus className="w-5 h-5" /> SELL YOUR PROTOCOL
          </button>
        </div>

        {/* Tabs */}
        <div className="flex gap-2 border-b border-purple-500/30 pb-2">
          {[
            { id: "browse", label: "BROWSE", icon: ShoppingCart },
            { id: "purchases", label: "MY PURCHASES", icon: Gift },
            { id: "sales", label: "MY SALES", icon: DollarSign }
          ].map(tab => (
            <button
              key={tab.id}
              onClick={() => setActiveTab(tab.id)}
              className={`px-4 py-2 font-mono text-sm rounded-t flex items-center gap-2 transition-colors ${
                activeTab === tab.id 
                  ? "bg-yellow-500/20 text-yellow-400 border-b-2 border-yellow-400" 
                  : "text-purple-400/60 hover:text-purple-300"
              }`}
            >
              <tab.icon className="w-4 h-4" />
              {tab.label}
            </button>
          ))}
        </div>

        {/* Content */}
        {loading ? (
          <div className="flex justify-center py-12">
            <Loader2 className="w-8 h-8 animate-spin text-yellow-400" />
          </div>
        ) : (
          <>
            {/* Browse Tab */}
            {activeTab === "browse" && (
              <div className="space-y-4">
                {protocols.length === 0 ? (
                  <FuturisticFrame title="NO PROTOCOLS FOR SALE" color="yellow" className="bg-slate-900/80 border border-yellow-500/30 rounded-lg text-center py-12">
                    <ShoppingCart className="w-16 h-16 text-yellow-500/30 mx-auto mb-4" />
                    <p className="text-purple-300 font-mono mb-4">No protocols are currently listed for sale</p>
                    <p className="text-purple-400/60 font-mono text-sm">List your private protocols in Categories to start selling!</p>
                  </FuturisticFrame>
                ) : (
                  <div className="grid gap-4 md:grid-cols-2">
                    {protocols.map((protocol) => (
                      <div key={protocol.id} className="bg-slate-900/80 p-4 rounded-lg border border-yellow-500/20 hover:border-yellow-500/50 transition-colors">
                        <div className="flex items-start justify-between mb-3">
                          <div>
                            <h3 className="text-yellow-400 font-mono font-bold">{protocol.name}</h3>
                            <p className="text-purple-400/60 font-mono text-xs">by {protocol.owner_username}</p>
                          </div>
                          <span className="text-xl font-bold text-green-400 font-mono">${protocol.price?.toFixed(2)}</span>
                        </div>
                        
                        {protocol.is_purchased ? (
                          <div className="flex items-center gap-2">
                            <span className="flex-1 text-green-400 font-mono text-sm flex items-center gap-2">
                              <Check className="w-4 h-4" /> PURCHASED
                            </span>
                          </div>
                        ) : protocol.owner_id === user?.id ? (
                          <span className="text-purple-400/60 font-mono text-sm">YOUR PROTOCOL</span>
                        ) : (
                          <button
                            onClick={() => handlePurchase(protocol.id)}
                            disabled={purchasing === protocol.id}
                            className="w-full px-4 py-2 bg-gradient-to-r from-yellow-500 to-orange-500 text-black font-mono font-bold rounded hover:scale-[1.02] disabled:opacity-50 flex items-center justify-center gap-2"
                            data-testid={`buy-protocol-${protocol.id}`}
                          >
                            {purchasing === protocol.id ? (
                              <Loader2 className="w-4 h-4 animate-spin" />
                            ) : (
                              <>
                                <ShoppingCart className="w-4 h-4" /> BUY NOW
                              </>
                            )}
                          </button>
                        )}
                      </div>
                    ))}
                  </div>
                )}
              </div>
            )}

            {/* Purchases Tab */}
            {activeTab === "purchases" && (
              <div className="space-y-4">
                {purchases.length === 0 ? (
                  <FuturisticFrame title="NO PURCHASES" color="purple" className="bg-slate-900/80 border border-purple-500/30 rounded-lg text-center py-12">
                    <Gift className="w-16 h-16 text-purple-500/30 mx-auto mb-4" />
                    <p className="text-purple-300 font-mono mb-4">You haven't purchased any protocols yet</p>
                    <button onClick={() => setActiveTab("browse")} className="px-6 py-2 bg-gradient-to-r from-yellow-500 to-orange-500 text-black font-mono rounded hover:scale-[1.02]">
                      BROWSE MARKETPLACE
                    </button>
                  </FuturisticFrame>
                ) : (
                  <div className="space-y-3">
                    {purchases.map((purchase) => (
                      <div key={purchase.id} className="bg-slate-900/80 p-4 rounded-lg border border-green-500/20">
                        <div className="flex items-start justify-between mb-2">
                          <div>
                            <h3 className="text-green-400 font-mono font-bold">{purchase.category_name}</h3>
                            <p className="text-purple-400/60 font-mono text-xs">from {purchase.seller_username} • ${purchase.amount?.toFixed(2)}</p>
                          </div>
                          <button
                            onClick={() => copyProtocol(purchase.protocol_string, purchase.category_id)}
                            className="p-2 text-purple-400 hover:text-pink-400 rounded hover:bg-pink-500/10"
                            title="Copy Protocol"
                          >
                            <Copy className="w-4 h-4" />
                          </button>
                        </div>
                        <div className="bg-slate-950 p-3 rounded font-mono text-sm text-purple-300 break-all">
                          {purchase.protocol_string}
                        </div>
                        <p className="text-purple-400/40 font-mono text-xs mt-2">Purchased: {new Date(purchase.purchased_at).toLocaleDateString()}</p>
                      </div>
                    ))}
                  </div>
                )}
              </div>
            )}

            {/* Sales Tab */}
            {activeTab === "sales" && (
              <div className="space-y-4">
                {sales.length === 0 ? (
                  <FuturisticFrame title="NO SALES" color="blue" className="bg-slate-900/80 border border-blue-500/30 rounded-lg text-center py-12">
                    <DollarSign className="w-16 h-16 text-blue-500/30 mx-auto mb-4" />
                    <p className="text-purple-300 font-mono mb-4">You haven't made any sales yet</p>
                    <button onClick={() => navigate("/categories")} className="px-6 py-2 bg-gradient-to-r from-pink-600 to-purple-600 text-white font-mono rounded hover:scale-[1.02]">
                      LIST A PROTOCOL FOR SALE
                    </button>
                  </FuturisticFrame>
                ) : (
                  <>
                    <div className="bg-gradient-to-r from-green-500/20 to-emerald-500/20 p-4 rounded-lg border border-green-500/30">
                      <p className="text-green-400 font-mono text-sm">TOTAL REVENUE</p>
                      <p className="text-3xl font-bold text-green-400 font-mono">${sales.reduce((sum, s) => sum + (s.amount || 0), 0).toFixed(2)}</p>
                    </div>
                    <div className="space-y-3">
                      {sales.map((sale) => (
                        <div key={sale.id} className="bg-slate-900/80 p-4 rounded-lg border border-green-500/20 flex items-center justify-between">
                          <div>
                            <h3 className="text-purple-300 font-mono font-bold">{sale.category_name}</h3>
                            <p className="text-purple-400/60 font-mono text-xs">Buyer: {sale.buyer_username}</p>
                            <p className="text-purple-400/40 font-mono text-xs">{new Date(sale.sold_at).toLocaleDateString()}</p>
                          </div>
                          <span className="text-xl font-bold text-green-400 font-mono">+${sale.amount?.toFixed(2)}</span>
                        </div>
                      ))}
                    </div>
                  </>
                )}
              </div>
            )}
          </>
        )}

        <BookSalesBanner variant="compact" />
      </div>
    </Layout>
  );
};

// Google Maps Component with Category-Colored Markers
const CategoryMap = ({ selectedCategories }) => {
  const [mapData, setMapData] = useState({ markers: [], categories: {} });
  const [selectedMarker, setSelectedMarker] = useState(null);
  const [loading, setLoading] = useState(true);
  
  const { isLoaded, loadError } = useJsApiLoader({
    googleMapsApiKey: GOOGLE_MAPS_API_KEY || "",
    id: 'google-map-script'
  });
  
  const mapContainerStyle = {
    width: '100%',
    height: '400px',
    borderRadius: '8px'
  };
  
  const defaultCenter = useMemo(() => ({ lat: 39.8283, lng: -98.5795 }), []); // Center of USA
  
  const mapOptions = useMemo(() => ({
    styles: [
      { elementType: "geometry", stylers: [{ color: "#1a1a2e" }] },
      { elementType: "labels.text.stroke", stylers: [{ color: "#1a1a2e" }] },
      { elementType: "labels.text.fill", stylers: [{ color: "#8b5cf6" }] },
      { featureType: "water", elementType: "geometry", stylers: [{ color: "#0f0f1a" }] },
      { featureType: "road", elementType: "geometry", stylers: [{ color: "#2d2d44" }] },
      { featureType: "road", elementType: "geometry.stroke", stylers: [{ color: "#1a1a2e" }] },
      { featureType: "poi", elementType: "geometry", stylers: [{ color: "#1f1f35" }] },
    ],
    disableDefaultUI: false,
    zoomControl: true,
    mapTypeControl: false,
    streetViewControl: false,
    fullscreenControl: true
  }), []);
  
  useEffect(() => {
    fetchMapData();
  }, [selectedCategories]);
  
  const fetchMapData = async () => {
    setLoading(true);
    try {
      const res = await axios.get(`${API}/ultimate-search/map-data`);
      let markers = res.data.markers || [];
      
      // Filter by selected categories if any
      if (selectedCategories && selectedCategories.length > 0) {
        markers = markers.filter(m => selectedCategories.includes(m.category_id));
      }
      
      setMapData({
        markers,
        categories: res.data.categories || {}
      });
    } catch (error) {
      console.error("Failed to fetch map data");
    } finally {
      setLoading(false);
    }
  };
  
  if (loadError) {
    return (
      <div className="bg-slate-900/80 rounded-lg p-6 text-center">
        <MapPin className="w-12 h-12 text-red-400 mx-auto mb-2" />
        <p className="text-red-400 font-mono">Failed to load Google Maps</p>
      </div>
    );
  }
  
  if (!isLoaded || loading) {
    return (
      <div className="bg-slate-900/80 rounded-lg p-6 text-center h-[400px] flex items-center justify-center">
        <Loader2 className="w-8 h-8 animate-spin text-pink-400" />
      </div>
    );
  }
  
  return (
    <div className="space-y-4">
      <GoogleMap
        mapContainerStyle={mapContainerStyle}
        center={defaultCenter}
        zoom={4}
        options={mapOptions}
      >
        {mapData.markers.map((marker) => (
          <Marker
            key={marker.id}
            position={{ lat: marker.lat, lng: marker.lng }}
            onClick={() => setSelectedMarker(marker)}
            icon={{
              path: "M12 2C8.13 2 5 5.13 5 9c0 5.25 7 13 7 13s7-7.75 7-13c0-3.87-3.13-7-7-7zm0 9.5c-1.38 0-2.5-1.12-2.5-2.5s1.12-2.5 2.5-2.5 2.5 1.12 2.5 2.5-1.12 2.5-2.5 2.5z",
              fillColor: marker.color,
              fillOpacity: 1,
              strokeColor: "#ffffff",
              strokeWeight: 1,
              scale: 1.5,
              anchor: { x: 12, y: 24 }
            }}
          />
        ))}
        
        {selectedMarker && (
          <InfoWindow
            position={{ lat: selectedMarker.lat, lng: selectedMarker.lng }}
            onCloseClick={() => setSelectedMarker(null)}
          >
            <div className="bg-slate-900 p-3 max-w-xs">
              <h3 className="font-bold text-sm mb-1" style={{ color: selectedMarker.color }}>
                {selectedMarker.title}
              </h3>
              <p className="text-xs text-gray-600 mb-2">{selectedMarker.snippet?.substring(0, 100)}...</p>
              <div className="flex flex-wrap gap-1 mb-2">
                <span className="text-xs px-2 py-0.5 rounded" style={{ backgroundColor: selectedMarker.color + '30', color: selectedMarker.color }}>
                  {selectedMarker.category_name}
                </span>
                <span className="text-xs px-2 py-0.5 bg-gray-200 rounded text-gray-700">
                  📍 {selectedMarker.location_name}
                </span>
              </div>
              <a 
                href={selectedMarker.url} 
                target="_blank" 
                rel="noopener noreferrer"
                className="text-xs text-blue-500 hover:underline"
              >
                Open Article →
              </a>
            </div>
          </InfoWindow>
        )}
      </GoogleMap>
      
      {/* Color Key Legend */}
      <div className="bg-slate-900/50 rounded-lg p-4 border border-purple-500/20">
        <h4 className="text-purple-400 font-mono text-sm mb-3 flex items-center gap-2">
          <MapPin className="w-4 h-4" /> CATEGORY COLOR KEY
        </h4>
        <div className="flex flex-wrap gap-3">
          {Object.entries(mapData.categories).map(([catId, catInfo]) => (
            <div key={catId} className="flex items-center gap-2">
              <div 
                className="w-4 h-4 rounded-full border border-white/30"
                style={{ backgroundColor: catInfo.color }}
              />
              <span className="text-purple-300 font-mono text-xs">{catInfo.name}</span>
            </div>
          ))}
        </div>
        <p className="text-purple-400/60 font-mono text-xs mt-3">
          {mapData.markers.length} locations from {Object.keys(mapData.categories).length} categories
        </p>
      </div>
    </div>
  );
};

// Recursive Category Tree Component with +/- expansion and Suggest Change
const CategoryTreeItem = ({ category, selectedCategories, onToggle, level = 0, currentUserId, onSuggestChange, onCategoryClick, onClearCategory }) => {
  const [isExpanded, setIsExpanded] = useState(true);
  const hasChildren = category.children && category.children.length > 0;
  const isOwner = category.user_id === currentUserId;
  const canSuggest = category.is_public && !isOwner;
  
  return (
    <div className="select-none">
      <div 
        className={`flex items-center gap-2 p-2 hover:bg-purple-500/10 rounded cursor-pointer ${level > 0 ? 'ml-' + (level * 4) : ''}`}
        style={{ marginLeft: level * 16 }}
      >
        {hasChildren ? (
          <button
            onClick={(e) => { e.stopPropagation(); setIsExpanded(!isExpanded); }}
            className="w-5 h-5 flex items-center justify-center text-purple-400 hover:text-pink-400 transition-colors"
          >
            {isExpanded ? <ChevronDown className="w-4 h-4" /> : <ChevronRight className="w-4 h-4" />}
          </button>
        ) : (
          <span className="w-5 h-5" />
        )}
        <label className="flex items-center gap-2 flex-1 cursor-pointer">
          <input
            type="checkbox"
            checked={selectedCategories.includes(category.id)}
            onChange={() => onToggle(category.id)}
            className="w-4 h-4 rounded bg-slate-950 border-purple-500/30 text-pink-500 focus:ring-pink-500"
          />
          {/* Clickable category name */}
          <button
            onClick={(e) => { e.preventDefault(); e.stopPropagation(); onCategoryClick && onCategoryClick(category.id, category.name); }}
            className="text-purple-300 font-mono text-sm flex-1 text-left hover:text-cyan-400 hover:underline transition-colors"
            title={`Click to filter by "${category.name}"`}
            data-testid={`category-filter-${category.id}`}
          >
            {category.name}
          </button>
          <span className="text-pink-400 font-mono text-xs">({category.result_count || 0})</span>
        </label>
        {/* Clear category button for owners */}
        {isOwner && (category.result_count || 0) > 0 && (
          <button
            onClick={(e) => { e.stopPropagation(); onClearCategory && onClearCategory(category.id, category.name); }}
            className="p-1 text-red-400/40 hover:text-red-400 hover:bg-red-500/10 rounded transition-colors"
            title={`Clear all results from "${category.name}"`}
            data-testid={`clear-category-${category.id}`}
          >
            <Trash2 className="w-3.5 h-3.5" />
          </button>
        )}
        {/* Suggest Change button for non-owners viewing public protocols */}
        {canSuggest && (
          <button
            onClick={(e) => { e.stopPropagation(); onSuggestChange && onSuggestChange(category); }}
            className="p-1 text-yellow-400/60 hover:text-yellow-400 hover:bg-yellow-500/10 rounded transition-colors"
            title="Suggest protocol change"
            data-testid={`suggest-change-${category.id}`}
          >
            <Lightbulb className="w-3.5 h-3.5" />
          </button>
        )}
        {/* Recommendation badge for owners */}
        {isOwner && (
          <RecommendationBadge 
            categoryId={category.id} 
            isOwner={true} 
            onClick={() => onSuggestChange && onSuggestChange(category, true)} 
          />
        )}
      </div>
      {hasChildren && isExpanded && (
        <div className="border-l border-purple-500/20 ml-2">
          {category.children.map(child => (
            <CategoryTreeItem 
              key={child.id} 
              category={child} 
              selectedCategories={selectedCategories}
              onToggle={onToggle}
              level={level + 1}
              currentUserId={currentUserId}
              onSuggestChange={onSuggestChange}
              onCategoryClick={onCategoryClick}
              onClearCategory={onClearCategory}
            />
          ))}
        </div>
      )}
    </div>
  );
};

// Add Subcategory Modal
const AddSubcategoryModal = ({ parentCategory, onClose, onSuccess }) => {
  const [name, setName] = useState("");
  const [protocol, setProtocol] = useState("");
  const [isPublic, setIsPublic] = useState(true);
  const [creating, setCreating] = useState(false);
  
  const handleCreate = async (e) => {
    e.preventDefault();
    setCreating(true);
    try {
      await axios.post(`${API}/categories/${parentCategory.id}/subcategory`, {
        name,
        protocol: { protocol_string: protocol },
        is_public: isPublic
      });
      toast.success("Subcategory created!");
      onSuccess();
      onClose();
    } catch (error) {
      toast.error(error.response?.data?.detail || "Failed to create subcategory");
    } finally {
      setCreating(false);
    }
  };
  
  return (
    <div className="fixed inset-0 bg-black/80 flex items-center justify-center z-50 p-4">
      <FuturisticFrame title={`ADD SUBCATEGORY TO: ${parentCategory.name}`} color="pink" className="bg-slate-900 border border-pink-500/30 rounded-lg max-w-lg w-full">
        <form onSubmit={handleCreate} className="space-y-4">
          <div>
            <label className="block text-xs font-mono text-purple-400 mb-1">SUBCATEGORY NAME</label>
            <input type="text" value={name} onChange={(e) => setName(e.target.value)} className="w-full px-4 py-2 bg-slate-950 border border-purple-500/30 rounded text-purple-300 font-mono focus:border-pink-500" required />
          </div>
          <div>
            <label className="block text-xs font-mono text-purple-400 mb-1">INFOPILOT 2.0 PROTOCOL</label>
            <textarea value={protocol} onChange={(e) => setProtocol(e.target.value)} placeholder="(word1 or word2) & (word3)+ & (excluded)^" className="w-full px-4 py-2 bg-slate-950 border border-purple-500/30 rounded text-purple-300 font-mono h-24 focus:border-pink-500" required />
          </div>
          <div className="flex items-center gap-2">
            <input type="checkbox" id="subIsPublic" checked={isPublic} onChange={(e) => setIsPublic(e.target.checked)} className="rounded bg-slate-950 border-purple-500/30" />
            <label htmlFor="subIsPublic" className="text-sm text-purple-300 font-mono">Make public</label>
          </div>
          <div className="flex gap-4">
            <button type="button" onClick={onClose} className="flex-1 px-4 py-2 border border-purple-500/30 text-purple-300 font-mono rounded hover:bg-purple-500/10">CANCEL</button>
            <button type="submit" disabled={creating} className="flex-1 px-4 py-2 bg-gradient-to-r from-pink-600 to-purple-600 text-white font-mono rounded hover:scale-[1.02] disabled:opacity-50">
              {creating ? <Loader2 className="w-5 h-5 animate-spin mx-auto" /> : "CREATE"}
            </button>
          </div>
        </form>
      </FuturisticFrame>
    </div>
  );
};

// Page Name Editor Modal
const PageNameEditorModal = ({ currentName, suggestions, onSave, onClose }) => {
  const [name, setName] = useState(currentName);
  const [saving, setSaving] = useState(false);
  
  const handleSave = async () => {
    setSaving(true);
    try {
      await onSave(name);
      onClose();
    } finally {
      setSaving(false);
    }
  };
  
  return (
    <div className="fixed inset-0 bg-black/80 flex items-center justify-center z-50 p-4">
      <FuturisticFrame title="✨ CUSTOMIZE YOUR PAGE NAME" color="pink" className="bg-slate-900 border border-pink-500/30 rounded-lg max-w-lg w-full">
        <div className="space-y-4">
          <p className="text-purple-300/70 font-mono text-sm">Give your Ultimate Search page a unique, creative name!</p>
          <div>
            <label className="block text-xs font-mono text-purple-400 mb-1">PAGE NAME</label>
            <input 
              type="text" 
              value={name} 
              onChange={(e) => setName(e.target.value)} 
              maxLength={100}
              className="w-full px-4 py-3 bg-slate-950 border border-purple-500/30 rounded text-purple-300 font-mono focus:border-pink-500" 
            />
            <p className="text-purple-400/50 text-xs font-mono mt-1">{name.length}/100 characters</p>
          </div>
          
          {suggestions && suggestions.length > 0 && (
            <div>
              <label className="block text-xs font-mono text-purple-400 mb-2">💡 SUGGESTIONS (click to use)</label>
              <div className="space-y-2">
                {suggestions.map((suggestion, idx) => (
                  <button
                    key={idx}
                    onClick={() => setName(suggestion)}
                    className="w-full text-left px-3 py-2 bg-slate-950 border border-purple-500/20 rounded text-purple-300 font-mono text-sm hover:border-pink-500 hover:bg-pink-500/10 transition-colors"
                  >
                    {suggestion}
                  </button>
                ))}
              </div>
            </div>
          )}
          
          <div className="flex gap-4 pt-2">
            <button onClick={onClose} className="flex-1 px-4 py-2 border border-purple-500/30 text-purple-300 font-mono rounded hover:bg-purple-500/10">CANCEL</button>
            <button onClick={handleSave} disabled={saving || !name.trim()} className="flex-1 px-4 py-2 bg-gradient-to-r from-pink-600 to-purple-600 text-white font-mono rounded hover:scale-[1.02] disabled:opacity-50">
              {saving ? <Loader2 className="w-5 h-5 animate-spin mx-auto" /> : "SAVE"}
            </button>
          </div>
        </div>
      </FuturisticFrame>
    </div>
  );
};

// Photo Upload Component
const PhotoGallery = ({ photos, onUpload, onDelete, maxPhotos = 26 }) => {
  const [uploading, setUploading] = useState(false);
  const fileInputRef = React.useRef(null);
  
  const handleFileSelect = async (e) => {
    const file = e.target.files[0];
    if (!file) return;
    
    // Check file size (15MB max)
    if (file.size > 15 * 1024 * 1024) {
      toast.error("Photo must be less than 15MB");
      return;
    }
    
    // Check file type
    if (!file.type.startsWith('image/')) {
      toast.error("Please select an image file");
      return;
    }
    
    setUploading(true);
    try {
      // Convert to base64
      const reader = new FileReader();
      reader.onload = async () => {
        const base64 = reader.result.split(',')[1];
        await onUpload(base64, file.name);
      };
      reader.readAsDataURL(file);
    } catch (error) {
      toast.error("Failed to upload photo");
    } finally {
      setUploading(false);
      if (fileInputRef.current) fileInputRef.current.value = '';
    }
  };
  
  return (
    <div className="space-y-4">
      <div className="flex items-center justify-between">
        <p className="text-purple-400/70 font-mono text-sm">
          {photos.length}/{maxPhotos} photos uploaded
        </p>
        {photos.length < maxPhotos && (
          <button
            onClick={() => fileInputRef.current?.click()}
            disabled={uploading}
            className="px-4 py-2 bg-purple-500/20 border border-purple-500/30 text-purple-400 font-mono text-sm rounded hover:bg-purple-500/30 flex items-center gap-2 disabled:opacity-50"
          >
            {uploading ? <Loader2 className="w-4 h-4 animate-spin" /> : <Plus className="w-4 h-4" />}
            ADD PHOTO
          </button>
        )}
        <input
          ref={fileInputRef}
          type="file"
          accept="image/*"
          onChange={handleFileSelect}
          className="hidden"
        />
      </div>
      
      {photos.length > 0 ? (
        <div className="grid grid-cols-4 md:grid-cols-6 gap-2">
          {photos.map((photo) => (
            <div key={photo.id} className="relative group aspect-square">
              <div className="w-full h-full bg-slate-800 rounded border border-purple-500/20 flex items-center justify-center">
                <span className="text-purple-400/50 text-xs font-mono">{photo.name?.substring(0, 8)}...</span>
              </div>
              <button
                onClick={() => onDelete(photo.id)}
                className="absolute top-1 right-1 p-1 bg-red-500/80 text-white rounded opacity-0 group-hover:opacity-100 transition-opacity"
              >
                <Trash2 className="w-3 h-3" />
              </button>
            </div>
          ))}
        </div>
      ) : (
        <div className="text-center py-8 bg-slate-950 rounded border border-purple-500/20">
          <p className="text-purple-400/50 font-mono text-sm">No photos yet. Add up to 26 photos (max 15MB each)</p>
        </div>
      )}
    </div>
  );
};

// Ultimate Search Page - COMPREHENSIVE with AI Search, Document Types, AND/OR/AND Radio Buttons
const UltimateSearchPage = () => {
  const { user } = useAuth();
  const navigate = useNavigate();
  const location = useLocation();
  const [categories, setCategories] = useState([]);
  const [treeCategories, setTreeCategories] = useState([]);
  const [selectedCategories, setSelectedCategories] = useState([]);
  const [aggregationType, setAggregationType] = useState("and_or");
  const [documentTypes, setDocumentTypes] = useState([]);
  const [selectedDocTypes, setSelectedDocTypes] = useState([]);
  const [results, setResults] = useState([]);
  const [loading, setLoading] = useState(false);
  const [searchOnlyLoading, setSearchOnlyLoading] = useState(false);
  const [aiQuery, setAiQuery] = useState("");
  const [keyword, setKeyword] = useState("");
  const [filters, setFilters] = useState(null);
  const [sessions, setSessions] = useState([]);
  const [selectedSession, setSelectedSession] = useState(null);
  const [totalResults, setTotalResults] = useState(0);
  const [currentPage, setCurrentPage] = useState(1);
  const [totalPages, setTotalPages] = useState(1);
  const [showDeleteModal, setShowDeleteModal] = useState(false);
  const [resultsToDelete, setResultsToDelete] = useState([]);
  const [showAddSubcategory, setShowAddSubcategory] = useState(null);
  const [isPreviewResults, setIsPreviewResults] = useState(false);
  
  // Database stats state
  const [dbStats, setDbStats] = useState({ current_count: 0, max_allowed: 4000, remaining: 4000, percentage_used: 0 });
  
  // Category filter state (for clickable categories)
  const [filterByCategoryId, setFilterByCategoryId] = useState(null);
  const [filterByCategoryName, setFilterByCategoryName] = useState(null);
  
  // Page customization state
  const [pageSettings, setPageSettings] = useState({ page_name: "My Ultimate Search", photos: [], show_name_suggestion: true, name_suggestions: [] });
  const [showNameEditor, setShowNameEditor] = useState(false);
  const [photos, setPhotos] = useState([]);
  const [showPhotoUploader, setShowPhotoUploader] = useState(false);
  const [uploadingPhoto, setUploadingPhoto] = useState(false);
  const [showPhotoGallery, setShowPhotoGallery] = useState(false);
  
  // Protocol Recommendations state
  const [suggestChangeCategory, setSuggestChangeCategory] = useState(null);
  const [viewRecsCategory, setViewRecsCategory] = useState(null);
  
  // Determine if current user is the owner of their own Ultimate Search page
  const isOwner = true; // In this context, user always owns their own search page
  
  // Handle suggestion click (different behavior for owner vs non-owner)
  const handleSuggestChangeClick = (category, isViewRecs = false) => {
    if (isViewRecs) {
      setViewRecsCategory(category);
    } else {
      setSuggestChangeCategory(category);
    }
  };
  
  // Check for URL query params to auto-filter on load
  useEffect(() => {
    const params = new URLSearchParams(location.search);
    const filterId = params.get('filter');
    const filterName = params.get('name');
    if (filterId && filterName) {
      handleCategoryFilter(filterId, decodeURIComponent(filterName));
      // Clear the URL params after applying filter
      navigate('/ultimate-search', { replace: true });
    }
  }, [location.search]);
  
  useEffect(() => {
    fetchCategories();
    fetchTreeCategories();
    fetchFilters();
    fetchSessions();
    fetchPageSettings();
    fetchPhotos();
    fetchDbStats();
  }, []);
  
  const fetchDbStats = async () => {
    try {
      const res = await axios.get(`${API}/ultimate-search/user-stats`);
      setDbStats(res.data);
    } catch (error) {
      console.error("Failed to fetch db stats");
    }
  };
  
  const handleClearAllResults = async () => {
    if (!window.confirm(`Are you sure you want to clear ALL ${dbStats.current_count} results from your database? This cannot be undone.`)) return;
    try {
      const res = await axios.delete(`${API}/ultimate-search/clear-all`);
      toast.success(res.data.message);
      fetchDbStats();
      fetchSessions();
      fetchCategories();
      fetchTreeCategories();
      setResults([]);
      setTotalResults(0);
    } catch (error) {
      toast.error(error.response?.data?.detail || "Failed to clear results");
    }
  };
  
  const handleClearCategoryResults = async (categoryId, categoryName) => {
    if (!window.confirm(`Clear all results from "${categoryName}" and its subcategories?`)) return;
    try {
      const res = await axios.delete(`${API}/ultimate-search/category/${categoryId}/clear`);
      toast.success(res.data.message);
      fetchDbStats();
      fetchSessions();
      fetchCategories();
      fetchTreeCategories();
      handleViewResults();
    } catch (error) {
      toast.error(error.response?.data?.detail || "Failed to clear category results");
    }
  };
  
  // Handle hashtag click - triggers new search
  const handleHashtagSearch = (hashtag) => {
    const searchTerm = hashtag.replace('#', '');
    setKeyword(searchTerm);
    toast.info(`Searching for: ${searchTerm}`);
  };
  
  // Handle category click - filters results by category
  const handleCategoryFilter = async (categoryId, categoryName) => {
    setFilterByCategoryId(categoryId);
    setFilterByCategoryName(categoryName);
    setLoading(true);
    try {
      const res = await axios.get(`${API}/ultimate-search/category/${categoryId}/results?page=1`);
      setResults(res.data.results || []);
      setTotalResults(res.data.total || 0);
      setTotalPages(res.data.total_pages || 1);
      setCurrentPage(1);
      toast.success(`Showing ${res.data.total} results for "${categoryName}"`);
    } catch (error) {
      toast.error(error.response?.data?.detail || "Failed to filter by category");
    } finally {
      setLoading(false);
    }
  };
  
  // Clear category filter
  const clearCategoryFilter = () => {
    setFilterByCategoryId(null);
    setFilterByCategoryName(null);
  };
  
  const fetchPageSettings = async () => {
    try {
      const res = await axios.get(`${API}/ultimate-search/page-settings`);
      setPageSettings(res.data);
    } catch (error) {
      console.error("Failed to fetch page settings");
    }
  };
  
  const fetchPhotos = async () => {
    try {
      const res = await axios.get(`${API}/ultimate-search/photos`);
      setPhotos(res.data.photos || []);
    } catch (error) {
      console.error("Failed to fetch photos");
    }
  };
  
  const handleUpdatePageName = async (newName) => {
    try {
      await axios.put(`${API}/ultimate-search/page-settings`, { page_name: newName });
      setPageSettings(prev => ({ ...prev, page_name: newName, show_name_suggestion: false }));
      toast.success("Page name updated!");
      return true;
    } catch (error) {
      toast.error(error.response?.data?.detail || "Failed to update page name");
      return false;
    }
  };
  
  const handlePhotoUpload = async (file) => {
    if (!file) return;
    
    // Check file size (15MB limit)
    if (file.size > 15 * 1024 * 1024) {
      toast.error("Photo must be less than 15MB");
      return;
    }
    
    // Check file type
    if (!file.type.startsWith('image/')) {
      toast.error("Please select an image file");
      return;
    }
    
    setUploadingPhoto(true);
    try {
      // Convert to base64
      const reader = new FileReader();
      reader.onload = async (e) => {
        try {
          const base64Data = e.target.result.split(',')[1];
          const res = await axios.post(`${API}/ultimate-search/photos`, {
            photo_data: base64Data,
            photo_name: file.name
          });
          toast.success(res.data.message);
          fetchPhotos();
          setShowPhotoUploader(false);
        } catch (error) {
          toast.error(error.response?.data?.detail || "Failed to upload photo");
        } finally {
          setUploadingPhoto(false);
        }
      };
      reader.readAsDataURL(file);
    } catch (error) {
      toast.error("Failed to process photo");
      setUploadingPhoto(false);
    }
  };
  
  const handleDeletePhoto = async (photoId) => {
    if (!window.confirm("Delete this photo?")) return;
    try {
      await axios.delete(`${API}/ultimate-search/photos/${photoId}`);
      toast.success("Photo deleted");
      fetchPhotos();
    } catch (error) {
      toast.error("Failed to delete photo");
    }
  };
  
  const fetchCategories = async () => {
    try {
      const res = await axios.get(`${API}/categories/with-counts`);
      setCategories(res.data.categories || []);
    } catch (error) {
      console.error("Failed to fetch categories");
    }
  };
  
  const fetchTreeCategories = async () => {
    try {
      const res = await axios.get(`${API}/categories/tree`);
      setTreeCategories(res.data.categories || []);
    } catch (error) {
      console.error("Failed to fetch tree categories");
    }
  };
  
  const fetchFilters = async () => {
    try {
      const res = await axios.get(`${API}/ultimate-search/filters`);
      setFilters(res.data);
      setDocumentTypes(res.data.document_types || []);
    } catch (error) {
      console.error("Failed to fetch filters");
    }
  };
  
  const fetchSessions = async () => {
    try {
      const res = await axios.get(`${API}/ultimate-search/sessions`);
      setSessions(res.data.sessions || []);
    } catch (error) {
      console.error("Failed to fetch sessions");
    }
  };
  
  // Search & Collate - saves results to database
  const handleSearchAndCollate = async () => {
    setLoading(true);
    setIsPreviewResults(false);
    clearCategoryFilter();
    try {
      const res = await axios.post(`${API}/search/collate`, {
        search_query: keyword || aiQuery || "general search",
        max_results: 120  // 6 pages * 20 results
      });
      setResults(res.data.results || []);
      setTotalResults(res.data.categorized_count || 0);
      let msg = `Collated ${res.data.categorized_count} of ${res.data.total_searched} results`;
      if (res.data.limit_reached) {
        msg += ` (Database limit reached: ${res.data.current_count}/${res.data.max_allowed})`;
        toast.warning(msg);
      } else {
        toast.success(msg);
      }
      fetchSessions();
      fetchCategories();
      fetchTreeCategories();
      fetchDbStats();
    } catch (error) {
      toast.error(error.response?.data?.detail || "Search & Collate failed");
    } finally {
      setLoading(false);
    }
  };
  
  // Search Only - does NOT save to database (for visitors)
  const handleSearchOnly = async () => {
    setSearchOnlyLoading(true);
    setIsPreviewResults(true);
    try {
      const res = await axios.post(`${API}/search/search-only`, {
        search_query: keyword || aiQuery || "general search",
        max_results: 120
      });
      setResults(res.data.results || []);
      setTotalResults(res.data.categorized_count || 0);
      toast.success(`Found ${res.data.categorized_count} matching results (preview only)`);
    } catch (error) {
      toast.error(error.response?.data?.detail || "Search failed");
    } finally {
      setSearchOnlyLoading(false);
    }
  };
  
  // View saved results with filters
  const handleViewResults = async () => {
    setLoading(true);
    setIsPreviewResults(false);
    try {
      const res = await axios.post(`${API}/ultimate-search`, {
        category_ids: selectedCategories,
        aggregation_type: aggregationType,
        document_types: selectedDocTypes,
        keyword: keyword || null,
        ai_query: aiQuery || null,
        page: currentPage
      });
      setResults(res.data.results || []);
      setTotalResults(res.data.total || 0);
      setTotalPages(res.data.total_pages || 1);
      toast.success(`Found ${res.data.total} saved results`);
    } catch (error) {
      toast.error(error.response?.data?.detail || "Search failed");
    } finally {
      setLoading(false);
    }
  };
  
  const handleAISearch = async () => {
    if (!aiQuery.trim()) {
      toast.error("Enter an AI search query");
      return;
    }
    setLoading(true);
    try {
      const res = await axios.post(`${API}/ultimate-search/ai`, {
        query: aiQuery,
        category_ids: selectedCategories
      });
      setResults(res.data.results || []);
      setTotalResults(res.data.total || 0);
      toast.success(`AI found ${res.data.total} results`);
    } catch (error) {
      toast.error(error.response?.data?.detail || "AI search failed");
    } finally {
      setLoading(false);
    }
  };
  
  const toggleCategory = (catId) => {
    setSelectedCategories(prev => 
      prev.includes(catId) ? prev.filter(id => id !== catId) : [...prev, catId]
    );
  };
  
  const toggleDocType = (docType) => {
    setSelectedDocTypes(prev => 
      prev.includes(docType) ? prev.filter(dt => dt !== docType) : [...prev, docType]
    );
  };
  
  const handleDeleteResults = async () => {
    if (resultsToDelete.length === 0) return;
    try {
      await axios.delete(`${API}/ultimate-search/results`, { data: { result_ids: resultsToDelete } });
      toast.success(`Deleted ${resultsToDelete.length} results`);
      setResultsToDelete([]);
      setShowDeleteModal(false);
      handleViewResults(); // Refresh results
      fetchSessions();
      fetchCategories();
      fetchTreeCategories();
    } catch (error) {
      toast.error("Failed to delete results");
    }
  };
  
  const handleDeleteSession = async (timestamp) => {
    console.log("Delete session clicked for:", timestamp);
    if (!window.confirm(`Delete all results from session ${timestamp}?`)) {
      console.log("User cancelled deletion");
      return;
    }
    console.log("User confirmed, attempting delete...");
    try {
      const url = `${API}/ultimate-search/session/${encodeURIComponent(timestamp)}`;
      console.log("Calling DELETE:", url);
      const res = await axios.delete(url);
      console.log("Delete response:", res.data);
      toast.success(res.data.message || "Session deleted");
      fetchSessions();
      fetchCategories();
      fetchTreeCategories();
      fetchDbStats();
      handleViewResults();
    } catch (error) {
      console.error("Delete session error:", error);
      console.error("Error response:", error.response?.data);
      toast.error(error.response?.data?.detail || "Failed to delete session");
    }
  };
  
  const toggleResultForDelete = (resultId) => {
    setResultsToDelete(prev => 
      prev.includes(resultId) ? prev.filter(id => id !== resultId) : [...prev, resultId]
    );
  };
  
  return (
    <Layout>
      <div className="max-w-7xl mx-auto space-y-6">
        {/* Page Name Editor Modal */}
        {showNameEditor && (
          <PageNameEditorModal 
            currentName={pageSettings.page_name}
            suggestions={pageSettings.name_suggestions}
            onSave={handleUpdatePageName}
            onClose={() => setShowNameEditor(false)}
          />
        )}
        
        {/* Photo Gallery Modal */}
        {showPhotoGallery && (
          <div className="fixed inset-0 bg-black/80 flex items-center justify-center z-50 p-4">
            <FuturisticFrame title="📸 YOUR PHOTO GALLERY" color="purple" className="bg-slate-900 border border-purple-500/30 rounded-lg max-w-2xl w-full max-h-[80vh] overflow-y-auto">
              <PhotoGallery 
                photos={photos}
                onUpload={async (base64, fileName) => {
                  try {
                    const res = await axios.post(`${API}/ultimate-search/photos`, {
                      photo_data: base64,
                      photo_name: fileName
                    });
                    toast.success(res.data.message);
                    fetchPhotos();
                  } catch (error) {
                    toast.error(error.response?.data?.detail || "Failed to upload photo");
                  }
                }}
                onDelete={handleDeletePhoto}
              />
              <button 
                onClick={() => setShowPhotoGallery(false)}
                className="mt-4 w-full px-4 py-2 border border-purple-500/30 text-purple-300 font-mono rounded hover:bg-purple-500/10"
              >
                CLOSE
              </button>
            </FuturisticFrame>
          </div>
        )}
        
        {/* Page Header with Custom Name */}
        <div className="flex items-center justify-between flex-wrap gap-4">
          <div className="flex items-center gap-3">
            <div>
              <h1 
                className="text-3xl font-bold text-transparent bg-clip-text bg-gradient-to-r from-pink-400 to-purple-400 font-mono tracking-wider cursor-pointer hover:opacity-80 flex items-center gap-2"
                onClick={() => setShowNameEditor(true)}
                data-testid="page-name-heading"
              >
                {pageSettings.page_name}
                <Edit3 className="w-5 h-5 text-pink-400/60" />
              </h1>
              <p className="text-purple-300/80 font-mono text-sm">Advanced filtering with AI-powered intelligent search</p>
            </div>
          </div>
          <div className="flex items-center gap-3">
            {/* Show suggestion if using default name */}
            {pageSettings.show_name_suggestion && (
              <button
                onClick={() => setShowNameEditor(true)}
                className="px-3 py-1 bg-yellow-500/20 text-yellow-400 font-mono text-xs rounded border border-yellow-500/50 animate-pulse"
                data-testid="customize-name-suggestion"
              >
                ✨ Customize your page name!
              </button>
            )}
            {isOwner && (
              <span className="px-3 py-1 bg-pink-500/20 text-pink-400 font-mono text-sm rounded border border-pink-500/50">
                OWNER MODE: Search & Collate
              </span>
            )}
          </div>
        </div>
        
        <WelcomeSaleBanner onUpgrade={() => navigate("/subscribe")} compact />
        
        {/* Page Customization Section */}
        <FuturisticFrame title="⚙️ CUSTOMIZE YOUR PAGE" color="purple" className="bg-slate-900/80 border border-purple-500/30 rounded-lg">
          <div className="flex flex-wrap items-center justify-between gap-4">
            <div className="flex items-center gap-4">
              <button
                onClick={() => setShowNameEditor(true)}
                className="px-4 py-2 bg-purple-500/20 border border-purple-500/30 text-purple-400 font-mono text-sm rounded hover:bg-purple-500/30 flex items-center gap-2"
                data-testid="edit-page-name-btn"
              >
                <Edit3 className="w-4 h-4" /> RENAME PAGE
              </button>
              <button
                onClick={() => setShowPhotoGallery(true)}
                className="px-4 py-2 bg-pink-500/20 border border-pink-500/30 text-pink-400 font-mono text-sm rounded hover:bg-pink-500/30 flex items-center gap-2"
                data-testid="photo-gallery-btn"
              >
                <Plus className="w-4 h-4" /> PHOTOS ({photos.length}/26)
              </button>
            </div>
            <p className="text-purple-400/60 font-mono text-xs">
              Make your Ultimate Search page unique! Change the name and add up to 26 photos.
            </p>
          </div>
          
          {/* Photo Preview Strip */}
          {photos.length > 0 && (
            <div className="mt-4 pt-4 border-t border-purple-500/20">
              <p className="text-purple-400/60 font-mono text-xs mb-2">YOUR PHOTOS:</p>
              <div className="flex gap-2 overflow-x-auto pb-2">
                {photos.slice(0, 10).map((photo) => (
                  <div key={photo.id} className="flex-shrink-0 w-12 h-12 bg-slate-800 rounded border border-purple-500/30 flex items-center justify-center">
                    <span className="text-purple-400/40 text-xs">{photo.name?.substring(0, 3)}</span>
                  </div>
                ))}
                {photos.length > 10 && (
                  <button 
                    onClick={() => setShowPhotoGallery(true)}
                    className="flex-shrink-0 w-12 h-12 bg-purple-500/20 rounded border border-purple-500/30 flex items-center justify-center text-purple-400 font-mono text-xs hover:bg-purple-500/30"
                  >
                    +{photos.length - 10}
                  </button>
                )}
              </div>
            </div>
          )}
        </FuturisticFrame>
        
        {/* Database Stats & Data Management Section */}
        <FuturisticFrame title="📊 DATABASE STATS & MANAGEMENT" color="blue" className="bg-slate-900/80 border border-blue-500/30 rounded-lg">
          <div className="space-y-4">
            {/* Stats Display */}
            <div className="grid grid-cols-1 md:grid-cols-4 gap-4">
              <div className="bg-slate-950 p-4 rounded border border-purple-500/30">
                <p className="text-purple-400/60 font-mono text-xs">STORED RESULTS</p>
                <p className="text-2xl font-mono text-purple-300">{dbStats.current_count.toLocaleString()}</p>
              </div>
              <div className="bg-slate-950 p-4 rounded border border-pink-500/30">
                <p className="text-pink-400/60 font-mono text-xs">LIMIT</p>
                <p className="text-2xl font-mono text-pink-300">{dbStats.max_allowed.toLocaleString()}</p>
              </div>
              <div className="bg-slate-950 p-4 rounded border border-green-500/30">
                <p className="text-green-400/60 font-mono text-xs">REMAINING</p>
                <p className="text-2xl font-mono text-green-300">{dbStats.remaining.toLocaleString()}</p>
              </div>
              <div className="bg-slate-950 p-4 rounded border border-yellow-500/30">
                <p className="text-yellow-400/60 font-mono text-xs">USAGE</p>
                <p className="text-2xl font-mono text-yellow-300">{dbStats.percentage_used}%</p>
              </div>
            </div>
            
            {/* Progress Bar */}
            <div className="relative h-4 bg-slate-800 rounded-full overflow-hidden">
              <div 
                className={`absolute left-0 top-0 h-full rounded-full transition-all ${
                  dbStats.percentage_used > 90 ? 'bg-red-500' : 
                  dbStats.percentage_used > 70 ? 'bg-yellow-500' : 'bg-green-500'
                }`}
                style={{ width: `${Math.min(dbStats.percentage_used, 100)}%` }}
              />
            </div>
            
            {/* Warning if near limit */}
            {dbStats.percentage_used > 80 && (
              <div className="flex items-center gap-2 p-3 bg-yellow-500/10 border border-yellow-500/30 rounded">
                <AlertTriangle className="w-5 h-5 text-yellow-400" />
                <p className="text-yellow-400 font-mono text-sm">
                  {dbStats.percentage_used > 95 
                    ? "Database almost full! Clear some results to continue collating."
                    : "Database filling up. Consider clearing old results."
                  }
                </p>
              </div>
            )}
            
            {/* Clear All Button */}
            <div className="flex flex-wrap gap-3">
              <button
                onClick={handleClearAllResults}
                disabled={dbStats.current_count === 0}
                className="px-4 py-2 bg-red-500/20 border border-red-500/30 text-red-400 font-mono text-sm rounded hover:bg-red-500/30 disabled:opacity-50 flex items-center gap-2"
                data-testid="clear-all-results-btn"
              >
                <Trash2 className="w-4 h-4" /> CLEAR ALL RESULTS ({dbStats.current_count})
              </button>
              <button
                onClick={fetchDbStats}
                className="px-4 py-2 bg-blue-500/20 border border-blue-500/30 text-blue-400 font-mono text-sm rounded hover:bg-blue-500/30 flex items-center gap-2"
              >
                <BarChart3 className="w-4 h-4" /> REFRESH STATS
              </button>
            </div>
          </div>
        </FuturisticFrame>
        
        {/* Category Filter Active Banner */}
        {filterByCategoryId && (
          <div className="flex items-center justify-between p-4 bg-cyan-500/10 border border-cyan-500/30 rounded-lg">
            <div className="flex items-center gap-2">
              <Filter className="w-5 h-5 text-cyan-400" />
              <span className="text-cyan-300 font-mono">Filtering by category: <strong>{filterByCategoryName}</strong></span>
            </div>
            <button
              onClick={clearCategoryFilter}
              className="px-3 py-1 bg-cyan-500/20 text-cyan-400 font-mono text-sm rounded hover:bg-cyan-500/30 flex items-center gap-2"
            >
              <X className="w-4 h-4" /> Clear Filter
            </button>
          </div>
        )}
        
        {/* Updates Section - Facebook-like Posts */}
        <UpdatesSection />
        
        {/* Interactive Map with Category-Colored Dots */}
        <FuturisticFrame title="🗺️ LOCATION MAP - Click dots to view articles" color="blue" className="bg-slate-900/80 border border-blue-500/30 rounded-lg">
          <CategoryMap selectedCategories={selectedCategories} />
        </FuturisticFrame>
        
        {/* AI Search Section */}
        <FuturisticFrame title="🤖 AI-POWERED INTELLIGENT SEARCH" color="pink" className="bg-slate-900/80 border border-pink-500/30 rounded-lg">
          <div className="space-y-4">
            <p className="text-purple-300/70 font-mono text-sm">Use natural language to find results intelligently</p>
            <div className="flex gap-4">
              <input 
                type="text"
                value={aiQuery}
                onChange={(e) => setAiQuery(e.target.value)}
                placeholder="Ask AI: 'Find research papers about climate change' or 'Show me educational content about history'..."
                className="flex-1 px-4 py-3 bg-slate-950 border border-pink-500/30 rounded text-purple-300 font-mono focus:border-pink-500 focus:outline-none"
                onKeyPress={(e) => e.key === "Enter" && handleAISearch()}
              />
              <button 
                onClick={handleAISearch}
                disabled={loading}
                className="px-6 py-3 bg-gradient-to-r from-pink-600 to-purple-600 text-white font-mono tracking-wider rounded hover:scale-[1.02] transition-all disabled:opacity-50 flex items-center gap-2"
              >
                {loading ? <Loader2 className="w-5 h-5 animate-spin" /> : <Zap className="w-5 h-5" />}
                AI SEARCH
              </button>
            </div>
          </div>
        </FuturisticFrame>
        
        {/* Add Subcategory Modal */}
        {showAddSubcategory && (
          <AddSubcategoryModal 
            parentCategory={showAddSubcategory}
            onClose={() => setShowAddSubcategory(null)}
            onSuccess={() => { fetchCategories(); fetchTreeCategories(); }}
          />
        )}
        
        <div className="grid lg:grid-cols-3 gap-6">
          {/* Left Column - Hierarchical Categories with +/- expansion */}
          <div className="lg:col-span-1 space-y-4">
            <FuturisticFrame title="📂 CATEGORIES (Click + to expand)" color="purple" className="bg-slate-900/80 border border-purple-500/30 rounded-lg">
              <div className="space-y-1 max-h-80 overflow-y-auto">
                {treeCategories.length === 0 ? (
                  <p className="text-purple-400/60 font-mono text-sm text-center py-4">No categories yet. Create one to start!</p>
                ) : (
                  treeCategories.map(cat => (
                    <div key={cat.id}>
                      <CategoryTreeItem 
                        category={cat} 
                        selectedCategories={selectedCategories}
                        onToggle={toggleCategory}
                        currentUserId={user?.id}
                        onSuggestChange={handleSuggestChangeClick}
                        onCategoryClick={handleCategoryFilter}
                        onClearCategory={handleClearCategoryResults}
                      />
                      {/* Add subcategory button for root categories */}
                      <button
                        onClick={() => setShowAddSubcategory(cat)}
                        className="ml-7 text-xs text-pink-400/60 hover:text-pink-400 font-mono flex items-center gap-1 mb-2"
                      >
                        <Plus className="w-3 h-3" /> Add subcategory
                      </button>
                    </div>
                  ))
                )}
              </div>
              <button
                onClick={() => navigate('/categories')}
                className="mt-3 w-full px-3 py-2 bg-purple-500/20 border border-purple-500/30 text-purple-400 font-mono text-xs rounded hover:bg-purple-500/30 flex items-center justify-center gap-2"
              >
                <Plus className="w-4 h-4" /> MANAGE CATEGORIES
              </button>
            </FuturisticFrame>
            
            {/* Aggregation Type Radio Buttons */}
            <FuturisticFrame title="🔗 SEARCH LOGIC" color="blue" className="bg-slate-900/80 border border-blue-500/30 rounded-lg">
              <div className="space-y-3">
                <label className="flex items-start gap-3 p-2 hover:bg-blue-500/10 rounded cursor-pointer">
                  <input
                    type="radio"
                    name="aggregation"
                    value="and_or"
                    checked={aggregationType === "and_or"}
                    onChange={(e) => setAggregationType(e.target.value)}
                    className="mt-1 w-4 h-4 text-pink-500 bg-slate-950 border-blue-500/30 focus:ring-pink-500"
                  />
                  <div>
                    <span className="text-blue-400 font-mono text-sm font-bold">AND/OR</span>
                    <p className="text-purple-400/60 font-mono text-xs">Results matching ALL or ANY categories</p>
                  </div>
                </label>
                <label className="flex items-start gap-3 p-2 hover:bg-blue-500/10 rounded cursor-pointer">
                  <input
                    type="radio"
                    name="aggregation"
                    value="or"
                    checked={aggregationType === "or"}
                    onChange={(e) => setAggregationType(e.target.value)}
                    className="mt-1 w-4 h-4 text-pink-500 bg-slate-950 border-blue-500/30 focus:ring-pink-500"
                  />
                  <div>
                    <span className="text-blue-400 font-mono text-sm font-bold">OR</span>
                    <p className="text-purple-400/60 font-mono text-xs">Results matching ANY selected category</p>
                  </div>
                </label>
                <label className="flex items-start gap-3 p-2 hover:bg-blue-500/10 rounded cursor-pointer">
                  <input
                    type="radio"
                    name="aggregation"
                    value="and"
                    checked={aggregationType === "and"}
                    onChange={(e) => setAggregationType(e.target.value)}
                    className="mt-1 w-4 h-4 text-pink-500 bg-slate-950 border-blue-500/30 focus:ring-pink-500"
                  />
                  <div>
                    <span className="text-blue-400 font-mono text-sm font-bold">AND</span>
                    <p className="text-purple-400/60 font-mono text-xs">Results matching ALL selected categories</p>
                  </div>
                </label>
              </div>
            </FuturisticFrame>
            
            {/* Document Type Checkboxes */}
            <FuturisticFrame title="📄 DOCUMENT TYPES" color="purple" className="bg-slate-900/80 border border-purple-500/30 rounded-lg">
              <div className="flex gap-2 mb-3">
                <button
                  type="button"
                  onClick={() => setSelectedDocTypes([...documentTypes])}
                  className="px-3 py-1 bg-purple-500/20 text-purple-400 font-mono text-xs rounded hover:bg-purple-500/30 transition-colors"
                  data-testid="select-all-doc-types"
                >
                  Select All
                </button>
                <button
                  type="button"
                  onClick={() => setSelectedDocTypes([])}
                  className="px-3 py-1 bg-pink-500/20 text-pink-400 font-mono text-xs rounded hover:bg-pink-500/30 transition-colors"
                  data-testid="deselect-all-doc-types"
                >
                  Deselect All
                </button>
              </div>
              <div className="space-y-2 max-h-48 overflow-y-auto">
                {documentTypes.map(docType => (
                  <label key={docType} className="flex items-center gap-3 p-2 hover:bg-purple-500/10 rounded cursor-pointer">
                    <input
                      type="checkbox"
                      checked={selectedDocTypes.includes(docType)}
                      onChange={() => toggleDocType(docType)}
                      className="w-4 h-4 rounded bg-slate-950 border-purple-500/30 text-pink-500 focus:ring-pink-500"
                    />
                    <span className="text-purple-300 font-mono text-xs">{docType}</span>
                  </label>
                ))}
              </div>
              <p className="text-purple-400/50 font-mono text-xs mt-2">
                {selectedDocTypes.length === 0 ? "All types selected (no filter)" : `${selectedDocTypes.length} type(s) selected`}
              </p>
            </FuturisticFrame>
          </div>
          
          {/* Right Column - Search & Results */}
          <div className="lg:col-span-2 space-y-4">
            {/* Traditional Keyword Search */}
            <FuturisticFrame title="🔍 WEB SEARCH" color="purple" className="bg-slate-900/80 border border-purple-500/30 rounded-lg">
              <div className="flex gap-4 flex-wrap">
                <input 
                  type="text"
                  value={keyword}
                  onChange={(e) => setKeyword(e.target.value)}
                  placeholder="Enter search query..."
                  className="flex-1 min-w-[200px] px-4 py-3 bg-slate-950 border border-purple-500/30 rounded text-purple-300 font-mono focus:border-pink-500 focus:outline-none"
                  onKeyPress={(e) => e.key === "Enter" && handleSearchOnly()}
                />
                {/* Search Only Button - for preview without saving */}
                <button 
                  onClick={handleSearchOnly}
                  disabled={searchOnlyLoading || loading}
                  className="px-5 py-3 bg-slate-700 border border-purple-500 text-purple-300 font-mono tracking-wider rounded hover:bg-slate-600 transition-all disabled:opacity-50 flex items-center gap-2"
                  title="Preview results without saving"
                >
                  {searchOnlyLoading ? <Loader2 className="w-5 h-5 animate-spin" /> : <Eye className="w-5 h-5" />}
                  SEARCH
                </button>
                {/* Search & Collate Button - saves to database (owner only) */}
                {isOwner && (
                  <button 
                    onClick={handleSearchAndCollate}
                    disabled={loading || searchOnlyLoading}
                    className="px-5 py-3 bg-gradient-to-r from-pink-600 to-purple-600 text-white font-mono tracking-wider rounded hover:scale-[1.02] transition-all disabled:opacity-50 flex items-center gap-2"
                    title="Search and save results to categories"
                  >
                    {loading ? <Loader2 className="w-5 h-5 animate-spin" /> : <><Search className="w-5 h-5" /><Plus className="w-4 h-4" /></>}
                    SEARCH & COLLATE
                  </button>
                )}
              </div>
              <div className="flex items-center gap-4 mt-4 text-xs font-mono text-purple-400/60 flex-wrap">
                <span>Selected: {selectedCategories.length} categories</span>
                <span>•</span>
                <span>Logic: {aggregationType.toUpperCase()}</span>
                <span>•</span>
                <span>Doc Types: {selectedDocTypes.length || "All"}</span>
                <span>•</span>
                <span>Max: 6 pages (120 results)</span>
              </div>
            </FuturisticFrame>
            
            {/* View Saved Results Button */}
            <FuturisticFrame title="📁 VIEW SAVED RESULTS" color="blue" className="bg-slate-900/80 border border-blue-500/30 rounded-lg">
              <div className="flex gap-4 items-center flex-wrap">
                <p className="text-purple-300/70 font-mono text-sm flex-1">Filter through your previously collated results:</p>
                <button 
                  onClick={handleViewResults}
                  disabled={loading}
                  className="px-6 py-2 bg-blue-600/80 text-white font-mono tracking-wider rounded hover:bg-blue-600 transition-all disabled:opacity-50 flex items-center gap-2"
                >
                  {loading ? <Loader2 className="w-4 h-4 animate-spin" /> : <Filter className="w-4 h-4" />}
                  FILTER RESULTS
                </button>
              </div>
              {totalPages > 1 && (
                <div className="flex items-center justify-center gap-2 mt-4">
                  <button 
                    onClick={() => { setCurrentPage(p => Math.max(1, p - 1)); handleViewResults(); }}
                    disabled={currentPage <= 1}
                    className="px-3 py-1 bg-slate-800 text-purple-400 rounded disabled:opacity-30"
                  >
                    ←
                  </button>
                  <span className="text-purple-400 font-mono text-sm">Page {currentPage} of {totalPages}</span>
                  <button 
                    onClick={() => { setCurrentPage(p => Math.min(totalPages, p + 1)); handleViewResults(); }}
                    disabled={currentPage >= totalPages}
                    className="px-3 py-1 bg-slate-800 text-purple-400 rounded disabled:opacity-30"
                  >
                    →
                  </button>
                </div>
              )}
            </FuturisticFrame>
            
            {/* Results Section */}
            <FuturisticFrame title={`📊 RESULTS (${totalResults})${isPreviewResults ? ' - PREVIEW' : ''}`} color="pink" className="bg-slate-900/80 border border-pink-500/30 rounded-lg">
              {isPreviewResults && results.length > 0 && (
                <div className="mb-4 p-3 bg-yellow-500/10 border border-yellow-500/30 rounded">
                  <p className="text-yellow-400 font-mono text-sm flex items-center gap-2">
                    <Eye className="w-4 h-4" /> Preview mode - results not saved. Use "Search & Collate" to save.
                  </p>
                </div>
              )}
              {results.length === 0 ? (
                <div className="text-center py-12">
                  <Search className="w-16 h-16 text-purple-500/30 mx-auto mb-4" />
                  <p className="text-purple-300 font-mono">No results yet. Use the search above!</p>
                </div>
              ) : (
                <div className="space-y-3">
                  {isOwner && !isPreviewResults && resultsToDelete.length > 0 && (
                    <div className="flex items-center justify-between p-3 bg-red-500/10 border border-red-500/30 rounded">
                      <span className="text-red-400 font-mono text-sm">{resultsToDelete.length} selected for deletion</span>
                      <button 
                        onClick={handleDeleteResults}
                        className="px-4 py-2 bg-red-600 text-white font-mono text-sm rounded hover:bg-red-700 flex items-center gap-2"
                      >
                        <Trash2 className="w-4 h-4" /> DELETE SELECTED
                      </button>
                    </div>
                  )}
                  {results.map(result => (
                    <div key={result.id} className={`bg-slate-950 p-4 rounded border ${isPreviewResults ? 'border-yellow-500/30' : 'border-purple-500/20'} hover:border-pink-500/50 transition-colors`}>
                      <div className="flex items-start gap-3">
                        {isOwner && !isPreviewResults && (
                          <input
                            type="checkbox"
                            checked={resultsToDelete.includes(result.id)}
                            onChange={() => toggleResultForDelete(result.id)}
                            className="mt-1 w-4 h-4 rounded bg-slate-950 border-red-500/30 text-red-500 focus:ring-red-500"
                          />
                        )}
                        <div className="flex-1 min-w-0">
                          <a href={result.url} target="_blank" rel="noopener noreferrer" className="text-pink-400 hover:underline font-mono text-sm block truncate">
                            {result.title}
                          </a>
                          <p className="text-purple-300/60 text-xs mt-1 line-clamp-2 font-mono">{result.snippet}</p>
                          <div className="flex flex-wrap gap-2 mt-2">
                            <span className="px-2 py-0.5 bg-pink-500/20 text-pink-400 text-xs rounded font-mono">{result.article_type}</span>
                            {result.document_type && (
                              <span className="px-2 py-0.5 bg-blue-500/20 text-blue-400 text-xs rounded font-mono">{result.document_type}</span>
                            )}
                            <span className="px-2 py-0.5 bg-slate-800 text-purple-400/60 text-xs rounded font-mono">{result.domain}</span>
                            {/* Clickable Category Names */}
                            {result.categories?.map((catId, idx) => (
                              <button
                                key={catId}
                                onClick={() => handleCategoryFilter(catId, result.category_names?.[idx] || 'Category')}
                                className="px-2 py-0.5 bg-purple-500/20 text-purple-400 text-xs rounded font-mono hover:bg-purple-500/30 hover:text-pink-400 cursor-pointer transition-colors"
                                title={`Click to filter by "${result.category_names?.[idx] || 'Category'}"`}
                                data-testid={`result-category-${catId}`}
                              >
                                {result.category_names?.[idx] || 'Category'}
                              </button>
                            ))}
                          </div>
                          {/* Hashtags Section - Clickable for search */}
                          {result.hashtags && result.hashtags.length > 0 && (
                            <div className="flex flex-wrap gap-1.5 mt-2 pt-2 border-t border-purple-500/10">
                              {result.hashtags.map((hashtag, idx) => (
                                <button
                                  key={idx}
                                  onClick={() => handleHashtagSearch(hashtag)}
                                  className="px-2 py-0.5 bg-cyan-500/10 text-cyan-400 text-xs rounded font-mono hover:bg-cyan-500/20 hover:text-cyan-300 transition-colors"
                                  title={`Search for ${hashtag}`}
                                  data-testid={`hashtag-${hashtag.replace('#', '')}`}
                                >
                                  {hashtag}
                                </button>
                              ))}
                            </div>
                          )}
                          {/* Reactions & Comments for Search Results */}
                          <div className="flex items-center gap-4 mt-3 pt-3 border-t border-purple-500/20">
                            <ReactionButton
                              postType="search_result"
                              postId={result.id}
                              reactions={result.reactions || {}}
                              reactionCounts={result.reaction_counts || {}}
                              userReaction={null}
                              onUpdate={() => {}}
                            />
                            <CommentsSection
                              postType="search_result"
                              postId={result.id}
                              initialCount={result.comment_count || 0}
                            />
                          </div>
                        </div>
                      </div>
                    </div>
                  ))}
                </div>
              )}
            </FuturisticFrame>
            
            {/* Collate Sessions - Owner Only */}
            {isOwner && sessions.length > 0 && (
              <FuturisticFrame title="📅 COLLATE SESSIONS" color="blue" className="bg-slate-900/80 border border-blue-500/30 rounded-lg">
                <div className="space-y-2 max-h-40 overflow-y-auto">
                  {sessions.map((session, idx) => (
                    <div key={idx} className="flex items-center justify-between p-2 hover:bg-blue-500/10 rounded">
                      <div className="flex items-center gap-3">
                        <Calendar className="w-4 h-4 text-blue-400" />
                        <span className="text-purple-300 font-mono text-sm">{session.timestamp}</span>
                        <span className="text-pink-400 font-mono text-xs">({session.result_count} results)</span>
                      </div>
                      <button
                        type="button"
                        onClick={(e) => {
                          e.preventDefault();
                          e.stopPropagation();
                          handleDeleteSession(session.timestamp);
                        }}
                        className="p-1 text-red-400/60 hover:text-red-400 rounded hover:bg-red-500/10 cursor-pointer z-10"
                        title={`Delete session ${session.timestamp}`}
                        data-testid={`delete-session-${idx}`}
                      >
                        <Trash2 className="w-4 h-4" />
                      </button>
                    </div>
                  ))}
                </div>
              </FuturisticFrame>
            )}
          </div>
        </div>
        
        <BookSalesBanner variant="compact" />
        
        {/* Protocol Recommendation Modals */}
        {suggestChangeCategory && (
          <SuggestChangeModal 
            category={suggestChangeCategory} 
            onClose={() => setSuggestChangeCategory(null)} 
            onSuccess={() => {
              setSuggestChangeCategory(null);
              toast.success("Your recommendation has been submitted to the protocol owner!");
            }}
          />
        )}
        
        {viewRecsCategory && (
          <ViewRecommendationsModal 
            category={viewRecsCategory} 
            onClose={() => setViewRecsCategory(null)} 
            onUpdate={fetchTreeCategories}
          />
        )}
      </div>
    </Layout>
  );
};

const StatisticsPage = () => {
  const navigate = useNavigate();
  const [stats, setStats] = useState(null);
  const [globalStats, setGlobalStats] = useState(null);
  const [popularProtocols, setPopularProtocols] = useState([]);
  const [badges, setBadges] = useState(null);
  const [badgeLeaderboard, setBadgeLeaderboard] = useState([]);
  const [loading, setLoading] = useState(true);
  const [activeTab, setActiveTab] = useState("overview");
  const { user } = useAuth();

  useEffect(() => {
    fetchAllStats();
  }, []);

  const fetchAllStats = async () => {
    setLoading(true);
    try {
      const [userStats, global, popular, myBadges, leaderboard] = await Promise.all([
        axios.get(`${API}/statistics`),
        axios.get(`${API}/statistics/global`),
        axios.get(`${API}/statistics/popular-protocols?limit=10`),
        axios.get(`${API}/badges/my-badges`),
        axios.get(`${API}/badges/leaderboard`)
      ]);
      setStats(userStats.data);
      setGlobalStats(global.data);
      setPopularProtocols(popular.data.popular_protocols || []);
      setBadges(myBadges.data);
      setBadgeLeaderboard(leaderboard.data.leaderboard || []);
    } catch (error) {
      console.error("Failed to load statistics");
    } finally {
      setLoading(false);
    }
  };

  const handleCopyProtocol = async (protocol) => {
    try {
      await axios.post(`${API}/categories/${protocol.id}/copy`);
      navigator.clipboard.writeText(protocol.protocol_string);
      toast.success("Protocol copied to clipboard!");
      // Refresh stats to update counts and badges
      fetchAllStats();
    } catch (error) {
      // Still copy even if tracking fails
      navigator.clipboard.writeText(protocol.protocol_string);
      toast.success("Protocol copied!");
    }
  };

  // Chart colors
  const COLORS = ['#ec4899', '#8b5cf6', '#3b82f6', '#10b981', '#f59e0b', '#ef4444', '#06b6d4', '#84cc16'];

  if (loading) {
    return (
      <Layout>
        <div className="flex justify-center py-12">
          <Loader2 className="w-12 h-12 text-pink-400 animate-spin" />
        </div>
      </Layout>
    );
  }

  return (
    <Layout>
      <div className="max-w-6xl mx-auto space-y-6">
        <div className="flex items-center justify-between">
          <h1 className="text-3xl font-bold text-transparent bg-clip-text bg-gradient-to-r from-pink-400 to-purple-400 font-mono tracking-wider">INTEL STATISTICS</h1>
          <button onClick={fetchAllStats} className="px-4 py-2 bg-slate-900 border border-purple-500/30 text-purple-400 font-mono rounded hover:border-pink-500 flex items-center gap-2">
            <Loader2 className="w-4 h-4" /> REFRESH
          </button>
        </div>

        <WelcomeSaleBanner onUpgrade={() => navigate("/subscribe")} compact />

        {/* Global Platform Stats */}
        <FuturisticFrame title="PLATFORM OVERVIEW" color="blue" className="bg-slate-900/80 border border-blue-500/30 rounded-lg">
          <div className="grid grid-cols-2 md:grid-cols-4 gap-4">
            <div className="bg-slate-950 p-4 rounded-lg text-center">
              <Users className="w-8 h-8 text-blue-400 mx-auto mb-2" />
              <p className="text-2xl font-bold text-blue-400 font-mono">{globalStats?.total_users || 0}</p>
              <p className="text-purple-400/60 font-mono text-xs">TOTAL PILOTS</p>
            </div>
            <div className="bg-slate-950 p-4 rounded-lg text-center">
              <Globe className="w-8 h-8 text-purple-400 mx-auto mb-2" />
              <p className="text-2xl font-bold text-purple-400 font-mono">{globalStats?.total_public_categories || 0}</p>
              <p className="text-purple-400/60 font-mono text-xs">PUBLIC PROTOCOLS</p>
            </div>
            <div className="bg-slate-950 p-4 rounded-lg text-center">
              <Copy className="w-8 h-8 text-pink-400 mx-auto mb-2" />
              <p className="text-2xl font-bold text-pink-400 font-mono">{globalStats?.total_clipboard_copies || 0}</p>
              <p className="text-purple-400/60 font-mono text-xs">TOTAL COPIES</p>
            </div>
            <div className="bg-slate-950 p-4 rounded-lg text-center">
              <ShoppingCart className="w-8 h-8 text-yellow-400 mx-auto mb-2" />
              <p className="text-2xl font-bold text-yellow-400 font-mono">{globalStats?.total_protocol_purchases || 0}</p>
              <p className="text-purple-400/60 font-mono text-xs">MARKETPLACE SALES</p>
            </div>
          </div>
        </FuturisticFrame>

        {/* Popular Protocols by Copies */}
        <FuturisticFrame title="🏆 MOST POPULAR PROTOCOLS (BY COPIES)" color="yellow" className="bg-slate-900/80 border border-yellow-500/30 rounded-lg">
          {popularProtocols.length === 0 ? (
            <div className="text-center py-8">
              <Copy className="w-16 h-16 text-yellow-500/30 mx-auto mb-4" />
              <p className="text-purple-300 font-mono">No protocols have been copied yet</p>
              <p className="text-purple-400/60 font-mono text-sm mt-2">Start copying protocols to see them ranked here!</p>
            </div>
          ) : (
            <div className="space-y-3">
              {popularProtocols.map((protocol, index) => (
                <div key={protocol.id} className="flex items-center gap-4 p-3 bg-slate-950 rounded-lg hover:bg-slate-950/80 transition-colors">
                  <div className={`w-10 h-10 rounded-full flex items-center justify-center font-mono font-bold text-lg ${
                    index === 0 ? 'bg-yellow-500 text-black' :
                    index === 1 ? 'bg-gray-300 text-black' :
                    index === 2 ? 'bg-orange-600 text-white' :
                    'bg-purple-500/20 text-purple-400'
                  }`}>
                    {index + 1}
                  </div>
                  <div className="flex-1 min-w-0">
                    <div className="flex items-center gap-2">
                      <h4 className="text-pink-400 font-mono font-bold truncate">{protocol.name}</h4>
                      {protocol.for_sale && (
                        <span className="px-2 py-0.5 bg-yellow-500/20 text-yellow-400 text-xs rounded font-mono">
                          ${protocol.price?.toFixed(2)}
                        </span>
                      )}
                    </div>
                    <p className="text-purple-400/60 font-mono text-xs truncate">{protocol.protocol_string}</p>
                    <p className="text-purple-400/40 font-mono text-xs">by {protocol.owner_username}</p>
                  </div>
                  <div className="text-right">
                    <p className="text-lg font-bold text-yellow-400 font-mono">{protocol.copy_count}</p>
                    <p className="text-purple-400/40 font-mono text-xs">copies</p>
                  </div>
                  <button
                    onClick={() => handleCopyProtocol(protocol)}
                    className="p-2 text-purple-400 hover:text-pink-400 hover:bg-pink-500/10 rounded"
                    title="Copy Protocol"
                  >
                    <Copy className="w-5 h-5" />
                  </button>
                </div>
              ))}
            </div>
          )}
        </FuturisticFrame>

        {/* Top Contributors */}
        {globalStats?.top_contributors?.length > 0 && (
          <FuturisticFrame title="TOP CONTRIBUTORS" color="green" className="bg-slate-900/80 border border-green-500/30 rounded-lg">
            <div className="grid grid-cols-2 md:grid-cols-5 gap-4">
              {globalStats.top_contributors.map((contrib, index) => (
                <div key={contrib._id} className="bg-slate-950 p-4 rounded-lg text-center">
                  <div className={`w-12 h-12 rounded-full mx-auto mb-2 flex items-center justify-center ${
                    index === 0 ? 'bg-yellow-500/20 text-yellow-400' :
                    index === 1 ? 'bg-gray-300/20 text-gray-300' :
                    'bg-purple-500/20 text-purple-400'
                  }`}>
                    <Award className="w-6 h-6" />
                  </div>
                  <p className="text-purple-300 font-mono font-bold truncate">{contrib.username}</p>
                  <p className="text-purple-400/60 font-mono text-xs">{contrib.count} protocols</p>
                </div>
              ))}
            </div>
          </FuturisticFrame>
        )}

        {/* Your Statistics */}
        <FuturisticFrame title="YOUR DATA" color="purple" className="bg-slate-900/80 border border-purple-500/30 rounded-lg">
          <div className="grid grid-cols-2 md:grid-cols-4 gap-4 mb-6">
            <div className="bg-slate-950 p-4 rounded-lg text-center">
              <FileText className="w-8 h-8 text-pink-400 mx-auto mb-2" />
              <p className="text-2xl font-bold text-pink-400 font-mono">{stats?.total_results || 0}</p>
              <p className="text-purple-400/60 font-mono text-xs">COLLATED RESULTS</p>
            </div>
            <div className="bg-slate-950 p-4 rounded-lg text-center">
              <FolderTree className="w-8 h-8 text-purple-400 mx-auto mb-2" />
              <p className="text-2xl font-bold text-purple-400 font-mono">{stats?.total_categories || 0}</p>
              <p className="text-purple-400/60 font-mono text-xs">YOUR CATEGORIES</p>
            </div>
            <div className="bg-slate-950 p-4 rounded-lg text-center">
              <Globe className="w-8 h-8 text-blue-400 mx-auto mb-2" />
              <p className="text-2xl font-bold text-blue-400 font-mono">{stats?.top_domains?.length || 0}</p>
              <p className="text-purple-400/60 font-mono text-xs">DOMAINS TRACKED</p>
            </div>
            <div className="bg-slate-950 p-4 rounded-lg text-center">
              <BarChart3 className="w-8 h-8 text-green-400 mx-auto mb-2" />
              <p className="text-2xl font-bold text-green-400 font-mono">{stats?.by_category?.length || 0}</p>
              <p className="text-purple-400/60 font-mono text-xs">ACTIVE CATEGORIES</p>
            </div>
          </div>

          {/* Charts */}
          {stats?.article_types?.length > 0 && (
            <div className="grid md:grid-cols-2 gap-6">
              {/* Article Types Pie Chart */}
              <div className="bg-slate-950 p-4 rounded-lg">
                <h4 className="text-purple-400 font-mono text-sm mb-4 text-center">RESULTS BY TYPE</h4>
                <ResponsiveContainer width="100%" height={200}>
                  <PieChart>
                    <Pie
                      data={stats.article_types}
                      dataKey="count"
                      nameKey="_id"
                      cx="50%"
                      cy="50%"
                      outerRadius={80}
                      label={({ name, percent }) => `${name} ${(percent * 100).toFixed(0)}%`}
                    >
                      {stats.article_types.map((_, index) => (
                        <Cell key={index} fill={COLORS[index % COLORS.length]} />
                      ))}
                    </Pie>
                    <Tooltip />
                  </PieChart>
                </ResponsiveContainer>
              </div>

              {/* Top Domains Bar Chart */}
              {stats?.top_domains?.length > 0 && (
                <div className="bg-slate-950 p-4 rounded-lg">
                  <h4 className="text-purple-400 font-mono text-sm mb-4 text-center">TOP DOMAINS</h4>
                  <ResponsiveContainer width="100%" height={200}>
                    <BarChart data={stats.top_domains.slice(0, 5)} layout="vertical">
                      <CartesianGrid strokeDasharray="3 3" stroke="#4c1d95" />
                      <XAxis type="number" stroke="#a78bfa" />
                      <YAxis dataKey="_id" type="category" width={100} stroke="#a78bfa" tick={{ fontSize: 10 }} />
                      <Tooltip />
                      <Bar dataKey="count" fill="#ec4899" />
                    </BarChart>
                  </ResponsiveContainer>
                </div>
              )}
            </div>
          )}

          {/* Results by Year */}
          {stats?.by_year?.length > 0 && (
            <div className="bg-slate-950 p-4 rounded-lg mt-6">
              <h4 className="text-purple-400 font-mono text-sm mb-4 text-center">RESULTS BY YEAR</h4>
              <ResponsiveContainer width="100%" height={200}>
                <BarChart data={stats.by_year}>
                  <CartesianGrid strokeDasharray="3 3" stroke="#4c1d95" />
                  <XAxis dataKey="_id" stroke="#a78bfa" />
                  <YAxis stroke="#a78bfa" />
                  <Tooltip />
                  <Bar dataKey="count" fill="#8b5cf6" />
                </BarChart>
              </ResponsiveContainer>
            </div>
          )}
        </FuturisticFrame>

        {/* Badges & Achievements Section */}
        <FuturisticFrame title="🏅 YOUR BADGES & ACHIEVEMENTS" color="yellow" className="bg-slate-900/80 border border-yellow-500/30 rounded-lg">
          {badges && (
            <div className="space-y-6">
              {/* Badge Stats Summary */}
              <div className="grid grid-cols-2 md:grid-cols-4 gap-4">
                <div className="bg-slate-950 p-4 rounded-lg text-center">
                  <Award className="w-8 h-8 text-yellow-400 mx-auto mb-2" />
                  <p className="text-2xl font-bold text-yellow-400 font-mono">{badges.total_earned}</p>
                  <p className="text-purple-400/60 font-mono text-xs">BADGES EARNED</p>
                </div>
                <div className="bg-slate-950 p-4 rounded-lg text-center">
                  <Copy className="w-8 h-8 text-pink-400 mx-auto mb-2" />
                  <p className="text-2xl font-bold text-pink-400 font-mono">{badges.stats?.total_copies_received || 0}</p>
                  <p className="text-purple-400/60 font-mono text-xs">COPIES RECEIVED</p>
                </div>
                <div className="bg-slate-950 p-4 rounded-lg text-center">
                  <FolderTree className="w-8 h-8 text-blue-400 mx-auto mb-2" />
                  <p className="text-2xl font-bold text-blue-400 font-mono">{badges.stats?.protocols_created || 0}</p>
                  <p className="text-purple-400/60 font-mono text-xs">PROTOCOLS CREATED</p>
                </div>
                <div className="bg-slate-950 p-4 rounded-lg text-center">
                  <DollarSign className="w-8 h-8 text-green-400 mx-auto mb-2" />
                  <p className="text-2xl font-bold text-green-400 font-mono">{badges.stats?.sales_count || 0}</p>
                  <p className="text-purple-400/60 font-mono text-xs">SALES MADE</p>
                </div>
              </div>

              {/* Top Protocol */}
              {badges.top_protocol && (
                <div className="bg-gradient-to-r from-yellow-500/10 to-orange-500/10 p-4 rounded-lg border border-yellow-500/30">
                  <p className="text-yellow-400 font-mono text-sm mb-1">🌟 YOUR TOP PROTOCOL</p>
                  <p className="text-white font-mono font-bold">{badges.top_protocol.name}</p>
                  <p className="text-purple-400/60 font-mono text-xs">{badges.top_protocol.copy_count} copies</p>
                </div>
              )}

              {/* Earned Badges */}
              {badges.earned_badges?.length > 0 && (
                <div>
                  <h4 className="text-green-400 font-mono text-sm mb-3 flex items-center gap-2">
                    <Check className="w-4 h-4" /> EARNED BADGES ({badges.earned_badges.length})
                  </h4>
                  <div className="grid grid-cols-2 md:grid-cols-4 lg:grid-cols-6 gap-3">
                    {badges.earned_badges.map((badge) => (
                      <div key={badge.id} className="bg-slate-950 p-3 rounded-lg text-center border border-green-500/30 hover:border-green-500 transition-colors">
                        <span className="text-3xl">{badge.icon}</span>
                        <p className="text-green-400 font-mono text-xs font-bold mt-2">{badge.name}</p>
                        <p className="text-purple-400/40 font-mono text-xs mt-1">{badge.description}</p>
                      </div>
                    ))}
                  </div>
                </div>
              )}

              {/* Locked Badges (Next to Earn) */}
              {badges.locked_badges?.length > 0 && (
                <div>
                  <h4 className="text-purple-400 font-mono text-sm mb-3 flex items-center gap-2">
                    <Lock className="w-4 h-4" /> BADGES TO UNLOCK ({badges.locked_badges.length})
                  </h4>
                  <div className="grid grid-cols-2 md:grid-cols-4 lg:grid-cols-6 gap-3">
                    {badges.locked_badges.slice(0, 6).map((badge) => (
                      <div key={badge.id} className="bg-slate-950/50 p-3 rounded-lg text-center border border-purple-500/20 opacity-60">
                        <span className="text-3xl grayscale">{badge.icon}</span>
                        <p className="text-purple-400/60 font-mono text-xs font-bold mt-2">{badge.name}</p>
                        <div className="mt-2 h-1 bg-slate-800 rounded-full overflow-hidden">
                          <div 
                            className="h-full bg-gradient-to-r from-pink-500 to-purple-500 transition-all" 
                            style={{ width: `${Math.min(100, badge.progress || 0)}%` }}
                          />
                        </div>
                        <p className="text-purple-400/40 font-mono text-xs mt-1">{Math.round(badge.progress || 0)}%</p>
                      </div>
                    ))}
                  </div>
                </div>
              )}
            </div>
          )}
        </FuturisticFrame>

        {/* Badge Leaderboard */}
        {badgeLeaderboard.length > 0 && (
          <FuturisticFrame title="🏆 BADGE LEADERBOARD" color="green" className="bg-slate-900/80 border border-green-500/30 rounded-lg">
            <div className="space-y-3">
              {badgeLeaderboard.slice(0, 10).map((entry, index) => (
                <div key={entry.user_id} className="flex items-center gap-4 p-3 bg-slate-950 rounded-lg">
                  <div className={`w-10 h-10 rounded-full flex items-center justify-center font-mono font-bold text-lg ${
                    index === 0 ? 'bg-yellow-500 text-black' :
                    index === 1 ? 'bg-gray-300 text-black' :
                    index === 2 ? 'bg-orange-600 text-white' :
                    'bg-purple-500/20 text-purple-400'
                  }`}>
                    {index + 1}
                  </div>
                  <div className="flex-1">
                    <p className="text-purple-300 font-mono font-bold">{entry.username}</p>
                    <p className="text-purple-400/60 font-mono text-xs">{entry.total_copies} total copies</p>
                  </div>
                  <div className="flex items-center gap-1">
                    {entry.top_badges?.slice(0, 3).map((badge, i) => (
                      <span key={i} className="text-xl" title={badge.name}>{badge.icon}</span>
                    ))}
                  </div>
                  <div className="text-right">
                    <p className="text-lg font-bold text-green-400 font-mono">{entry.badges_earned}</p>
                    <p className="text-purple-400/40 font-mono text-xs">badges</p>
                  </div>
                </div>
              ))}
            </div>
          </FuturisticFrame>
        )}

        {/* Empty State */}
        {(!stats?.total_results || stats.total_results === 0) && (
          <FuturisticFrame title="GET STARTED" color="pink" className="bg-slate-900/80 border border-pink-500/30 rounded-lg text-center py-8">
            <Search className="w-16 h-16 text-pink-500/30 mx-auto mb-4" />
            <p className="text-purple-300 font-mono mb-4">Start collating data to see your personalized statistics</p>
            <button onClick={() => navigate("/infopilot")} className="px-6 py-3 bg-gradient-to-r from-pink-600 to-purple-600 text-white font-mono rounded hover:scale-[1.02]">
              START SEARCHING
            </button>
          </FuturisticFrame>
        )}

        <BookSalesBanner variant="compact" />
      </div>
    </Layout>
  );
};

const GlobalDatabasePage = () => {
  const navigate = useNavigate();
  return (
    <Layout>
      <div className="max-w-6xl mx-auto space-y-6">
        <h1 className="text-3xl font-bold text-transparent bg-clip-text bg-gradient-to-r from-pink-400 to-purple-400 font-mono tracking-wider">GLOBAL DATABASE</h1>
        <WelcomeSaleBanner onUpgrade={() => navigate("/subscribe")} />
        <FuturisticFrame title="PUBLIC CATEGORIES" color="purple" className="bg-slate-900/80 border border-purple-500/30 rounded-lg text-center py-12">
          <Globe className="w-16 h-16 text-purple-500/30 mx-auto mb-4" />
          <p className="text-purple-300 font-mono">Access public categories from pilots worldwide.</p>
        </FuturisticFrame>
        <BookSalesBanner variant="compact" />
      </div>
    </Layout>
  );
};

// Book Page - FULL SALES PAGE with new images
const BookPage = () => {
  const [currentImage, setCurrentImage] = useState(0);
  const bookImages = [IMAGES.bookCoverMain, IMAGES.bookCover1, IMAGES.bookCover2, IMAGES.bookCover3, IMAGES.bookCover4];
  
  return (
    <Layout>
      <div className="max-w-4xl mx-auto space-y-8">
        {/* Hero Section */}
        <div className="relative rounded-xl overflow-hidden">
          <img src={bookImages[currentImage]} alt="Letters to Evelyn" className="w-full h-64 md:h-96 object-cover" />
          <div className="absolute inset-0 bg-gradient-to-t from-slate-950 via-slate-950/50 to-transparent"></div>
          <div className="absolute bottom-0 left-0 right-0 p-6">
            <h1 className="text-4xl md:text-5xl font-bold text-transparent bg-clip-text bg-gradient-to-r from-pink-400 via-purple-400 to-blue-400 font-mono mb-2">LETTERS TO EVELYN</h1>
            <p className="text-xl text-purple-300 font-mono">{BOOK_INFO.genre}</p>
          </div>
        </div>
        
        {/* Image Gallery */}
        <div className="flex justify-center gap-4">
          {bookImages.map((img, idx) => (
            <button 
              key={idx} 
              onClick={() => setCurrentImage(idx)}
              className={`w-16 h-20 rounded overflow-hidden border-2 transition-all ${currentImage === idx ? 'border-pink-500 scale-110' : 'border-purple-500/30 opacity-60 hover:opacity-100'}`}
            >
              <img src={img} alt={`Book cover ${idx + 1}`} className="w-full h-full object-cover" />
            </button>
          ))}
        </div>

        {/* Rating Banner */}
        <div className="flex items-center justify-center gap-4 p-4 bg-gradient-to-r from-yellow-500/20 to-orange-500/20 rounded-lg border border-yellow-500">
          <div className="flex">{[...Array(5)].map((_, i) => <Star key={i} className="w-8 h-8 fill-yellow-400 text-yellow-400" />)}</div>
          <span className="text-2xl font-bold text-yellow-400 font-mono">19 FIVE-STAR REVIEWS</span>
        </div>

        {/* Author Section */}
        <FuturisticFrame title="ABOUT THE AUTHOR" color="pink" className="bg-slate-900/80 border border-pink-500/30 rounded-lg">
          <div className="flex flex-col md:flex-row gap-6 items-center">
            <img src={IMAGES.author} alt="John Selman" className="w-32 h-32 rounded-full border-4 border-pink-500 object-cover shadow-lg shadow-pink-500/30" />
            <div>
              <h2 className="text-2xl font-bold text-pink-400 font-mono">John Selman</h2>
              <p className="text-purple-300 font-mono mb-2">World Record Aviation Holder • U.S. Navy Pilot • Author</p>
              <p className="text-purple-400/80 font-mono text-sm italic">"{BOOK_INFO.tagline}"</p>
            </div>
          </div>
        </FuturisticFrame>

        {/* Reviews */}
        <FuturisticFrame title="CRITICAL ACCLAIM" color="purple" className="bg-slate-900/80 border border-purple-500/30 rounded-lg">
          <div className="space-y-4">
            {BOOK_INFO.quotes.map((quote, idx) => (
              <div key={idx} className="bg-slate-950 p-4 rounded border-l-4 border-pink-500">
                <p className="text-purple-300/90 font-mono text-sm italic">"{quote.text}"</p>
                <p className="text-pink-400 font-mono text-xs mt-2">— {quote.author}</p>
              </div>
            ))}
          </div>
        </FuturisticFrame>

        {/* Purchase Links */}
        <FuturisticFrame title="GET YOUR COPY" color="blue" className="bg-slate-900/80 border border-blue-500/30 rounded-lg">
          <div className="grid md:grid-cols-2 gap-4">
            <a href={BOOK_INFO.amazonUrl} target="_blank" rel="noopener noreferrer" className="flex items-center gap-3 px-6 py-4 bg-gradient-to-r from-yellow-500 to-orange-500 text-black font-bold font-mono rounded-lg hover:scale-105 transition-transform">
              <ShoppingCart className="w-6 h-6" /> BUY ON AMAZON
            </a>
            <a href={BOOK_INFO.officialUrl} target="_blank" rel="noopener noreferrer" className="flex items-center gap-3 px-6 py-4 bg-gradient-to-r from-purple-600 to-pink-600 text-white font-mono rounded-lg hover:scale-105 transition-transform">
              <ExternalLink className="w-6 h-6" /> OFFICIAL WEBSITE
            </a>
            <a href={BOOK_INFO.sintraUrl} target="_blank" rel="noopener noreferrer" className="flex items-center gap-3 px-6 py-4 border border-purple-500 text-purple-400 font-mono rounded-lg hover:bg-purple-500/20 transition-colors">
              <Globe className="w-6 h-6" /> SINTRA SITE
            </a>
            <a href={BOOK_INFO.readersFavoriteUrl} target="_blank" rel="noopener noreferrer" className="flex items-center gap-3 px-6 py-4 border border-yellow-500 text-yellow-400 font-mono rounded-lg hover:bg-yellow-500/20 transition-colors">
              <Star className="w-6 h-6" /> READ ALL REVIEWS
            </a>
            <a href={BOOK_INFO.googleDriveUrl} target="_blank" rel="noopener noreferrer" className="flex items-center gap-3 px-6 py-4 border border-blue-500 text-blue-400 font-mono rounded-lg hover:bg-blue-500/20 transition-colors md:col-span-2">
              <BookOpen className="w-6 h-6" /> PREVIEW ON GOOGLE DRIVE
            </a>
          </div>
        </FuturisticFrame>
      </div>
    </Layout>
  );
};

// Stripe Checkout Form Component
const StripeCheckoutForm = ({ onSuccess }) => {
  const stripe = useStripe();
  const elements = useElements();
  const [processing, setProcessing] = useState(false);
  const [error, setError] = useState(null);
  
  const handleSubmit = async (e) => {
    e.preventDefault();
    if (!stripe || !elements) return;
    
    setProcessing(true);
    setError(null);
    
    try {
      const { error: submitError, paymentIntent } = await stripe.confirmPayment({
        elements,
        confirmParams: {
          return_url: window.location.origin + "/subscribe?success=true",
        },
        redirect: "if_required"
      });
      
      if (submitError) {
        setError(submitError.message);
      } else if (paymentIntent && paymentIntent.status === "succeeded") {
        // Confirm with backend
        await axios.post(`${API}/payments/confirm?payment_intent_id=${paymentIntent.id}`);
        toast.success("🎉 PAYMENT SUCCESSFUL!");
        onSuccess();
      }
    } catch (err) {
      setError(err.response?.data?.detail || "Payment failed");
    } finally {
      setProcessing(false);
    }
  };
  
  return (
    <form onSubmit={handleSubmit} className="space-y-4">
      <PaymentElement />
      {error && (
        <div className="p-3 bg-red-500/20 border border-red-500 rounded text-red-400 text-sm font-mono">
          {error}
        </div>
      )}
      <button
        type="submit"
        disabled={!stripe || processing}
        className="w-full py-4 bg-gradient-to-r from-pink-600 via-purple-600 to-blue-600 text-white font-bold font-mono tracking-wider rounded-lg hover:scale-[1.02] transition-transform disabled:opacity-50 flex items-center justify-center gap-2 text-lg"
      >
        {processing ? <Loader2 className="w-6 h-6 animate-spin" /> : <><CreditCard className="w-6 h-6" /> PAY $0.75 - GET LIFETIME ACCESS</>}
      </button>
    </form>
  );
};

// Subscribe Page - STRIPE INTEGRATION
// Subscribe Page - Now redirects to book page since app is free
const SubscribePage = () => {
  const { user } = useAuth();
  const navigate = useNavigate();
  const [config, setConfig] = useState(null);
  const [subscriptionStatus, setSubscriptionStatus] = useState(null);
  const [customAmount, setCustomAmount] = useState("1.00");
  const [loading, setLoading] = useState(true);
  const [recording, setRecording] = useState(false);
  const [transactionId, setTransactionId] = useState("");
  const [showRecordPayment, setShowRecordPayment] = useState(false);
  const [paymentPending, setPaymentPending] = useState(false);

  useEffect(() => {
    fetchConfig();
    fetchSubscriptionStatus();
    
    // Check if user is returning from PayPal payment
    const pendingPayment = localStorage.getItem('paypal_payment_pending');
    if (pendingPayment) {
      const { amount, timestamp } = JSON.parse(pendingPayment);
      // Only show if payment was initiated within last 30 minutes
      if (Date.now() - timestamp < 30 * 60 * 1000) {
        setCustomAmount(amount);
        setShowRecordPayment(true);
        setPaymentPending(true);
      } else {
        localStorage.removeItem('paypal_payment_pending');
      }
    }
  }, []);

  // Poll for subscription status when payment is pending
  useEffect(() => {
    if (paymentPending) {
      const interval = setInterval(() => {
        fetchSubscriptionStatus();
      }, 5000); // Check every 5 seconds
      return () => clearInterval(interval);
    }
  }, [paymentPending]);

  // Initialize PayPal Hosted Button
  useEffect(() => {
    if (!showRecordPayment && window.paypal) {
      const container = document.getElementById('paypal-container-765S46VPPEP5C');
      if (container && container.children.length === 0) {
        try {
          window.paypal.HostedButtons({
            hostedButtonId: "765S46VPPEP5C",
          }).render("#paypal-container-765S46VPPEP5C").catch(err => {
            console.log("PayPal button render info:", err);
          });
        } catch (e) {
          console.log("PayPal SDK not fully loaded yet");
        }
      }
    }
  }, [showRecordPayment, loading]);

  const fetchConfig = async () => {
    try {
      const res = await axios.get(`${API}/subscription/config`);
      setConfig(res.data);
    } catch (error) {
      console.error("Failed to fetch subscription config");
    } finally {
      setLoading(false);
    }
  };

  const fetchSubscriptionStatus = async () => {
    try {
      const res = await axios.get(`${API}/subscription/status`);
      setSubscriptionStatus(res.data);
      
      // If subscription is now active and we were waiting, redirect to home
      if (res.data.is_subscribed && paymentPending) {
        localStorage.removeItem('paypal_payment_pending');
        toast.success("🎉 Subscription activated! Welcome to InfoPilot Explorer!");
        setTimeout(() => navigate("/"), 1500);
      }
    } catch (error) {
      console.error("Failed to fetch subscription status");
    }
  };

  const handlePayPalClick = (link) => {
    // Store payment intent in localStorage before opening PayPal
    localStorage.setItem('paypal_payment_pending', JSON.stringify({
      amount: customAmount,
      timestamp: Date.now()
    }));
    
    // Open PayPal in same window for better UX
    window.location.href = link;
  };

  const handleRecordPayment = async () => {
    const amount = parseFloat(customAmount);
    if (isNaN(amount) || amount < 0.01) {
      toast.error("Please enter a valid amount");
      return;
    }
    
    setRecording(true);
    try {
      const res = await axios.post(`${API}/subscription/record-payment?amount=${amount}&paypal_transaction_id=${encodeURIComponent(transactionId || '')}`);
      
      // Clear pending payment from localStorage
      localStorage.removeItem('paypal_payment_pending');
      
      toast.success("🎉 " + res.data.message);
      
      // Redirect to home page after successful activation
      setTimeout(() => {
        navigate("/");
      }, 1500);
      
    } catch (error) {
      toast.error(error.response?.data?.detail || "Failed to record payment");
    } finally {
      setRecording(false);
    }
  };

  // Calculate time remaining until promo ends
  const getTimeRemaining = () => {
    if (!config?.promo_end_date) return null;
    const end = new Date(config.promo_end_date);
    const now = new Date();
    const diff = end - now;
    if (diff <= 0) return null;
    
    const days = Math.floor(diff / (1000 * 60 * 60 * 24));
    const hours = Math.floor((diff % (1000 * 60 * 60 * 24)) / (1000 * 60 * 60));
    return { days, hours };
  };

  const timeRemaining = getTimeRemaining();

  if (loading) {
    return (
      <Layout>
        <div className="flex justify-center py-12">
          <Loader2 className="w-12 h-12 text-pink-400 animate-spin" />
        </div>
      </Layout>
    );
  }

  // If already subscribed, show status
  if (subscriptionStatus?.is_subscribed) {
    return (
      <Layout>
        <div className="max-w-lg mx-auto space-y-6">
          <FuturisticFrame title="✅ SUBSCRIPTION ACTIVE" color="green" className="bg-slate-900/80 border border-green-500/30 rounded-lg text-center py-8">
            <Crown className="w-16 h-16 text-yellow-400 mx-auto mb-4" />
            <h2 className="text-2xl font-bold text-transparent bg-clip-text bg-gradient-to-r from-green-400 to-emerald-400 font-mono mb-2">YOU'RE SUBSCRIBED!</h2>
            <p className="text-purple-300/80 font-mono text-sm mb-2">Thank you for supporting InfoPilot Explorer!</p>
            <div className="bg-slate-950 p-4 rounded-lg mt-4 max-w-xs mx-auto">
              <p className="text-purple-400/60 font-mono text-xs">Amount Paid</p>
              <p className="text-green-400 font-mono text-xl font-bold">${subscriptionStatus.subscription?.amount_paid?.toFixed(2)}</p>
              <p className="text-purple-400/60 font-mono text-xs mt-2">Expires</p>
              <p className="text-purple-300 font-mono text-sm">{new Date(subscriptionStatus.subscription?.expires_at).toLocaleDateString()}</p>
            </div>
            <button onClick={() => navigate("/")} className="mt-6 px-6 py-3 bg-gradient-to-r from-green-600 to-emerald-600 text-white font-mono rounded hover:scale-[1.02]">
              GO TO COMMAND CENTER
            </button>
          </FuturisticFrame>
          
          <BookSalesBanner variant="compact" />
        </div>
      </Layout>
    );
  }

  return (
    <Layout>
      <div className="max-w-2xl mx-auto space-y-6">
        {/* Pay What You Want Header */}
        <div className="text-center mb-8">
          <h1 className="text-4xl font-bold text-transparent bg-clip-text bg-gradient-to-r from-pink-400 via-purple-400 to-blue-400 font-mono tracking-wider mb-2">
            {config?.is_promo_active ? "PAY WHAT YOU WANT!" : "SUBSCRIBE NOW"}
          </h1>
          <p className="text-purple-300/80 font-mono">Support InfoPilot Explorer's development</p>
        </div>

        {/* Promo Timer */}
        {config?.is_promo_active && timeRemaining && (
          <FuturisticFrame title="⏰ LIMITED TIME OFFER" color="yellow" className="bg-slate-900/80 border border-yellow-500/30 rounded-lg">
            <div className="text-center">
              <p className="text-yellow-400 font-mono text-lg mb-2">Pay What You Want ends in:</p>
              <div className="flex justify-center gap-4">
                <div className="bg-slate-950 px-4 py-2 rounded">
                  <p className="text-3xl font-bold text-yellow-400 font-mono">{timeRemaining.days}</p>
                  <p className="text-purple-400/60 font-mono text-xs">DAYS</p>
                </div>
                <div className="bg-slate-950 px-4 py-2 rounded">
                  <p className="text-3xl font-bold text-yellow-400 font-mono">{timeRemaining.hours}</p>
                  <p className="text-purple-400/60 font-mono text-xs">HOURS</p>
                </div>
              </div>
              <p className="text-purple-300/60 font-mono text-sm mt-3">After March 2nd, 2026: ${config?.regular_price}/year</p>
            </div>
          </FuturisticFrame>
        )}

        {/* Subscription Options */}
        <FuturisticFrame title="💳 CHOOSE YOUR SUPPORT LEVEL" color="pink" className="bg-slate-900/80 border border-pink-500/30 rounded-lg">
          <div className="space-y-6">
            {/* Custom Amount Input (Promo only) */}
            {config?.is_promo_active && (
              <div className="text-center">
                <label className="block text-purple-400 font-mono text-sm mb-2">YOUR CHOSEN AMOUNT (per year)</label>
                <div className="flex items-center justify-center gap-2 mb-4">
                  <span className="text-3xl font-bold text-pink-400 font-mono">$</span>
                  <input
                    type="number"
                    value={customAmount}
                    onChange={(e) => setCustomAmount(e.target.value)}
                    min="0.01"
                    step="0.01"
                    className="w-32 px-4 py-3 bg-slate-950 border border-pink-500/30 rounded-lg text-pink-400 font-mono text-2xl font-bold text-center focus:border-pink-500 focus:outline-none"
                    placeholder="1.00"
                    data-testid="custom-amount-input"
                  />
                  <span className="text-purple-400/60 font-mono">/year</span>
                </div>
                <p className="text-purple-400/40 font-mono text-xs">Minimum: $0.01 • Suggested: $0.75 - $4.62</p>
              </div>
            )}

            {/* Fixed Price (After promo) */}
            {!config?.is_promo_active && (
              <div className="text-center">
                <p className="text-purple-400 font-mono text-sm mb-2">ANNUAL SUBSCRIPTION</p>
                <p className="text-4xl font-bold text-pink-400 font-mono">${config?.regular_price}</p>
                <p className="text-purple-400/60 font-mono text-sm">/year</p>
              </div>
            )}

            {/* Quick Amount Buttons - Uses admin-configured preset amounts */}
            {config?.is_promo_active && (
              <div className="flex flex-wrap justify-center gap-2">
                {(config?.preset_amounts || "1.00, 2.00, 4.62, 10.00").split(",").map(amt => {
                  const amount = parseFloat(amt.trim());
                  return (
                    <button
                      key={amount}
                      onClick={() => setCustomAmount(amount.toFixed(2))}
                      className={`px-4 py-2 rounded font-mono text-sm transition-colors ${
                        parseFloat(customAmount) === amount
                          ? 'bg-pink-600 text-white'
                          : 'bg-slate-950 text-purple-400 border border-purple-500/30 hover:border-pink-500'
                      }`}
                    >
                      ${amount.toFixed(2)}
                    </button>
                  );
                })}
              </div>
            )}

            {/* PayPal Buttons - Hide if already recording */}
            {!showRecordPayment && (
              <div className="space-y-4 pt-4">
                <p className="text-center text-purple-400 font-mono text-sm mb-2">Pay securely with PayPal:</p>
                
                {/* PayPal Hosted Button Container */}
                <div className="bg-white/5 rounded-lg p-4 border border-purple-500/20">
                  <div id="paypal-container-765S46VPPEP5C" className="min-h-[45px]"></div>
                </div>
                
                {/* Note about PayPal button */}
                <p className="text-center text-purple-400/40 font-mono text-xs">
                  If the PayPal button doesn't load, use the link below:
                </p>

                <button
                  onClick={() => handlePayPalClick(config?.paypal_link_1 || "https://www.paypal.com/ncp/payment/765S46VPPEP5C")}
                  className="w-full px-6 py-4 bg-[#0070ba] hover:bg-[#003087] text-white font-mono rounded-lg transition-colors flex items-center justify-center gap-3"
                  data-testid="paypal-btn-1"
                >
                  <svg className="w-6 h-6" viewBox="0 0 24 24" fill="currentColor">
                    <path d="M7.076 21.337H2.47a.641.641 0 0 1-.633-.74L4.944.901C5.026.382 5.474 0 5.998 0h7.46c2.57 0 4.578.543 5.69 1.81 1.01 1.15 1.304 2.42 1.012 4.287-.023.143-.047.288-.077.437-.983 5.05-4.349 6.797-8.647 6.797h-2.19c-.524 0-.968.382-1.05.9l-1.12 7.106zm14.146-14.42a3.35 3.35 0 0 0-.607-.541c-.013.076-.026.175-.041.254-.59 3.025-2.566 6.082-8.558 6.082H9.838l-1.363 8.642h2.464c.456 0 .843-.32.915-.77l.038-.19.735-4.66.047-.256c.072-.45.46-.77.915-.77h.576c3.727 0 6.645-1.514 7.499-5.893.32-1.634.193-3.002-.442-3.898z"/>
                  </svg>
                  PAY ${customAmount} WITH PAYPAL
                </button>
                
                {/* Already paid button */}
                <button
                  onClick={() => setShowRecordPayment(true)}
                  className="w-full px-4 py-2 text-purple-400/60 hover:text-purple-400 font-mono text-sm underline"
                >
                  I've already completed my PayPal payment →
                </button>
              </div>
            )}

            {/* Record Payment Section */}
            {showRecordPayment && (
              <div className="mt-2 p-6 bg-gradient-to-br from-green-500/10 to-emerald-500/10 border-2 border-green-500/50 rounded-lg">
                <div className="flex items-center gap-3 mb-4">
                  <div className="w-10 h-10 bg-green-500/20 rounded-full flex items-center justify-center">
                    <Check className="w-6 h-6 text-green-400" />
                  </div>
                  <div>
                    <h4 className="text-green-400 font-mono font-bold">PAYMENT COMPLETE?</h4>
                    <p className="text-purple-400/60 font-mono text-xs">Click below to activate your subscription</p>
                  </div>
                </div>
                <div className="space-y-3">
                  <div>
                    <label className="block text-purple-400/60 font-mono text-xs mb-1">PayPal Transaction ID (optional - from receipt)</label>
                    <input
                      type="text"
                      value={transactionId}
                      onChange={(e) => setTransactionId(e.target.value)}
                      placeholder="e.g., 1AB23456CD789012E"
                      className="w-full px-3 py-2 bg-slate-900 border border-purple-500/30 rounded text-purple-300 font-mono text-sm focus:border-green-500 focus:outline-none"
                    />
                  </div>
                  <button
                    onClick={handleRecordPayment}
                    disabled={recording}
                    className="w-full px-6 py-4 bg-gradient-to-r from-green-600 to-emerald-600 text-white font-mono text-lg rounded-lg hover:scale-[1.02] disabled:opacity-50 flex items-center justify-center gap-3 shadow-lg shadow-green-500/30"
                    data-testid="record-payment-btn"
                  >
                    {recording ? (
                      <><Loader2 className="w-6 h-6 animate-spin" /> ACTIVATING...</>
                    ) : (
                      <><Crown className="w-6 h-6" /> ACTIVATE MY ${customAmount} SUBSCRIPTION</>
                    )}
                  </button>
                  <button
                    onClick={() => setShowRecordPayment(false)}
                    className="w-full px-4 py-2 text-purple-400/40 hover:text-purple-400 font-mono text-sm"
                  >
                    ← Back to payment options
                  </button>
                </div>
              </div>
            )}
          </div>
        </FuturisticFrame>

        {/* What You Get */}
        <FuturisticFrame title="✨ WHAT YOU GET" color="purple" className="bg-slate-900/80 border border-purple-500/30 rounded-lg">
          <ul className="space-y-3">
            {[
              "Unlimited AI-powered searches",
              "Create unlimited categories & protocols",
              "Access to all social features (Groups, Pages, Messaging)",
              "Protocol recommendations & collaboration",
              "Priority support from the developer",
              "Help sustain and improve InfoPilot Explorer"
            ].map((item, idx) => (
              <li key={idx} className="flex items-center gap-3 text-purple-300 font-mono text-sm">
                <Check className="w-5 h-5 text-green-400 flex-shrink-0" />
                {item}
              </li>
            ))}
          </ul>
        </FuturisticFrame>

        {/* Book Promotion */}
        <BookSalesBanner variant="compact" />
      </div>
    </Layout>
  );
};

// ============================================
// SOCIAL FEATURES - FRIENDS PAGE
// ============================================
const FriendsPage = () => {
  const { user } = useAuth();
  const [friends, setFriends] = useState([]);
  const [requests, setRequests] = useState({ incoming: [], outgoing: [] });
  const [loading, setLoading] = useState(true);
  const [searchEmail, setSearchEmail] = useState('');
  const navigate = useNavigate();

  useEffect(() => {
    fetchFriends();
    fetchRequests();
  }, []);

  const fetchFriends = async () => {
    try {
      const res = await axios.get(`${API}/friends`);
      setFriends(res.data.friends || []);
    } catch (error) {
      console.error("Failed to fetch friends");
    } finally {
      setLoading(false);
    }
  };

  const fetchRequests = async () => {
    try {
      const res = await axios.get(`${API}/friends/requests`);
      setRequests(res.data);
    } catch (error) {
      console.error("Failed to fetch requests");
    }
  };

  const handleAccept = async (requestId) => {
    try {
      await axios.post(`${API}/friends/accept/${requestId}`);
      toast.success("Friend request accepted!");
      fetchFriends();
      fetchRequests();
    } catch (error) {
      toast.error("Failed to accept request");
    }
  };

  const handleReject = async (requestId) => {
    try {
      await axios.post(`${API}/friends/reject/${requestId}`);
      toast.success("Friend request rejected");
      fetchRequests();
    } catch (error) {
      toast.error("Failed to reject request");
    }
  };

  const handleRemove = async (friendId) => {
    if (!window.confirm("Remove this friend?")) return;
    try {
      await axios.delete(`${API}/friends/${friendId}`);
      toast.success("Friend removed");
      fetchFriends();
    } catch (error) {
      toast.error("Failed to remove friend");
    }
  };

  return (
    <Layout>
      <div className="max-w-4xl mx-auto space-y-6">
        <div className="flex items-center justify-between">
          <h1 className="text-3xl font-bold text-transparent bg-clip-text bg-gradient-to-r from-pink-400 to-purple-400 font-mono tracking-wider">FRIENDS</h1>
          <span className="px-3 py-1 bg-purple-500/20 border border-purple-500/50 text-purple-300 font-mono rounded">{friends.length} Friends</span>
        </div>

        {/* Friend Requests */}
        {requests.incoming.length > 0 && (
          <FuturisticFrame title="FRIEND REQUESTS" color="pink" className="bg-slate-900/80 border border-pink-500/30 rounded-lg">
            <div className="space-y-3">
              {requests.incoming.map((req) => (
                <div key={req.id} className="flex items-center justify-between p-3 bg-purple-500/10 rounded-lg">
                  <div className="flex items-center gap-3">
                    <div className="w-10 h-10 bg-gradient-to-br from-pink-500/20 to-purple-500/20 rounded-full flex items-center justify-center">
                      <User className="w-5 h-5 text-pink-400" />
                    </div>
                    <span className="text-purple-300 font-mono">{req.from_username}</span>
                  </div>
                  <div className="flex gap-2">
                    <button onClick={() => handleAccept(req.id)} className="px-3 py-1 bg-green-600 text-white font-mono text-sm rounded hover:bg-green-700">
                      <Check className="w-4 h-4" />
                    </button>
                    <button onClick={() => handleReject(req.id)} className="px-3 py-1 bg-red-600 text-white font-mono text-sm rounded hover:bg-red-700">
                      <X className="w-4 h-4" />
                    </button>
                  </div>
                </div>
              ))}
            </div>
          </FuturisticFrame>
        )}

        {/* Friends List */}
        <FuturisticFrame title="YOUR FRIENDS" color="purple" className="bg-slate-900/80 border border-purple-500/30 rounded-lg">
          {loading ? (
            <div className="flex justify-center py-8"><Loader2 className="w-8 h-8 text-pink-400 animate-spin" /></div>
          ) : friends.length === 0 ? (
            <div className="text-center py-8">
              <Users className="w-16 h-16 text-purple-400/30 mx-auto mb-4" />
              <p className="text-purple-400/60 font-mono">No friends yet</p>
              <p className="text-purple-400/40 font-mono text-sm mt-2">The admin has been added as your first friend!</p>
            </div>
          ) : (
            <div className="grid gap-3">
              {friends.map((friend) => (
                <div key={friend.id} className="flex items-center justify-between p-4 bg-purple-500/10 rounded-lg hover:bg-purple-500/20 transition-colors">
                  <div className="flex items-center gap-4">
                    <div className="w-12 h-12 bg-gradient-to-br from-pink-500/20 to-purple-500/20 rounded-full flex items-center justify-center border border-purple-500/30">
                      {friend.profile_photo ? (
                        <img src={friend.profile_photo} alt={friend.username} className="w-12 h-12 rounded-full object-cover" />
                      ) : (
                        <User className="w-6 h-6 text-pink-400" />
                      )}
                    </div>
                    <div>
                      <p className="text-purple-300 font-mono font-bold">{friend.username}</p>
                      {friend.is_admin && <span className="text-xs text-pink-400 font-mono">ADMIN</span>}
                    </div>
                  </div>
                  <button onClick={() => handleRemove(friend.id)} className="p-2 text-red-400/60 hover:text-red-400 hover:bg-red-500/10 rounded">
                    <Trash2 className="w-5 h-5" />
                  </button>
                </div>
              ))}
            </div>
          )}
        </FuturisticFrame>
      </div>
    </Layout>
  );
};

// ============================================
// SOCIAL FEATURES - GROUPS PAGE
// ============================================
const GroupsPage = () => {
  const [myGroups, setMyGroups] = useState([]);
  const [publicGroups, setPublicGroups] = useState([]);
  const [loading, setLoading] = useState(true);
  const [showCreate, setShowCreate] = useState(false);
  const [newGroup, setNewGroup] = useState({ name: '', description: '', privacy: 'public' });
  const [creating, setCreating] = useState(false);
  const navigate = useNavigate();

  useEffect(() => { fetchGroups(); }, []);

  const fetchGroups = async () => {
    try {
      const res = await axios.get(`${API}/groups`);
      setMyGroups(res.data.my_groups || []);
      setPublicGroups(res.data.public_groups || []);
    } catch (error) {
      console.error("Failed to fetch groups");
    } finally {
      setLoading(false);
    }
  };

  const handleCreate = async (e) => {
    e.preventDefault();
    setCreating(true);
    try {
      await axios.post(`${API}/groups`, newGroup);
      toast.success("Group created!");
      setShowCreate(false);
      setNewGroup({ name: '', description: '', privacy: 'public' });
      fetchGroups();
    } catch (error) {
      toast.error(error.response?.data?.detail || "Failed to create group");
    } finally {
      setCreating(false);
    }
  };

  const handleJoin = async (groupId) => {
    try {
      await axios.post(`${API}/groups/${groupId}/join`);
      toast.success("Joined group!");
      fetchGroups();
    } catch (error) {
      toast.error(error.response?.data?.detail || "Failed to join group");
    }
  };

  return (
    <Layout>
      <div className="max-w-4xl mx-auto space-y-6">
        <div className="flex items-center justify-between">
          <h1 className="text-3xl font-bold text-transparent bg-clip-text bg-gradient-to-r from-pink-400 to-purple-400 font-mono tracking-wider">GROUPS</h1>
          <button onClick={() => setShowCreate(true)} className="px-4 py-2 bg-gradient-to-r from-pink-600 to-purple-600 text-white font-mono rounded hover:scale-[1.02] flex items-center gap-2">
            <Plus className="w-5 h-5" /> CREATE GROUP
          </button>
        </div>

        {/* Create Modal */}
        {showCreate && (
          <div className="fixed inset-0 bg-black/80 flex items-center justify-center z-50 p-4">
            <FuturisticFrame title="CREATE GROUP" color="pink" className="bg-slate-900 border border-pink-500/30 rounded-lg max-w-lg w-full">
              <form onSubmit={handleCreate} className="space-y-4">
                <div>
                  <label className="block text-xs font-mono text-purple-400 mb-1">GROUP NAME</label>
                  <input type="text" value={newGroup.name} onChange={(e) => setNewGroup({ ...newGroup, name: e.target.value })} className="w-full px-4 py-2 bg-slate-950 border border-purple-500/30 rounded text-purple-300 font-mono focus:border-pink-500" required />
                </div>
                <div>
                  <label className="block text-xs font-mono text-purple-400 mb-1">DESCRIPTION</label>
                  <textarea value={newGroup.description} onChange={(e) => setNewGroup({ ...newGroup, description: e.target.value })} className="w-full px-4 py-2 bg-slate-950 border border-purple-500/30 rounded text-purple-300 font-mono h-24 focus:border-pink-500" placeholder="What's your group about?" />
                </div>
                <div>
                  <label className="block text-xs font-mono text-purple-400 mb-1">PRIVACY</label>
                  <select value={newGroup.privacy} onChange={(e) => setNewGroup({ ...newGroup, privacy: e.target.value })} className="w-full px-4 py-2 bg-slate-950 border border-purple-500/30 rounded text-purple-300 font-mono focus:border-pink-500">
                    <option value="public">Public - Anyone can see and join</option>
                    <option value="private">Private - Anyone can see, but must request to join</option>
                    <option value="secret">Secret - Only members can see</option>
                  </select>
                </div>
                <div className="flex gap-4">
                  <button type="button" onClick={() => setShowCreate(false)} className="flex-1 px-4 py-2 border border-purple-500/30 text-purple-300 font-mono rounded hover:bg-purple-500/10">CANCEL</button>
                  <button type="submit" disabled={creating} className="flex-1 px-4 py-2 bg-gradient-to-r from-pink-600 to-purple-600 text-white font-mono rounded hover:scale-[1.02] disabled:opacity-50">
                    {creating ? <Loader2 className="w-5 h-5 animate-spin mx-auto" /> : "CREATE"}
                  </button>
                </div>
              </form>
            </FuturisticFrame>
          </div>
        )}

        {/* My Groups */}
        <FuturisticFrame title="MY GROUPS" color="purple" className="bg-slate-900/80 border border-purple-500/30 rounded-lg">
          {loading ? (
            <div className="flex justify-center py-8"><Loader2 className="w-8 h-8 text-pink-400 animate-spin" /></div>
          ) : myGroups.length === 0 ? (
            <div className="text-center py-8">
              <Users className="w-16 h-16 text-purple-400/30 mx-auto mb-4" />
              <p className="text-purple-400/60 font-mono">You haven't joined any groups yet</p>
              <button onClick={() => setShowCreate(true)} className="mt-4 px-4 py-2 bg-pink-600 text-white font-mono rounded hover:bg-pink-700">Create Your First Group</button>
            </div>
          ) : (
            <div className="grid md:grid-cols-2 gap-4">
              {myGroups.map((group) => (
                <div key={group.id} onClick={() => navigate(`/groups/${group.id}`)} className="p-4 bg-purple-500/10 rounded-lg hover:bg-purple-500/20 cursor-pointer transition-colors">
                  <div className="flex items-start gap-3">
                    <div className="w-14 h-14 bg-gradient-to-br from-pink-500/30 to-purple-500/30 rounded-lg flex items-center justify-center">
                      <Users className="w-7 h-7 text-pink-400" />
                    </div>
                    <div className="flex-1">
                      <h3 className="text-purple-300 font-mono font-bold">{group.name}</h3>
                      <p className="text-purple-400/60 font-mono text-xs mt-1">{group.member_count} members • {group.privacy}</p>
                      <p className="text-purple-400/40 font-mono text-xs mt-1 line-clamp-2">{group.description || "No description"}</p>
                    </div>
                  </div>
                </div>
              ))}
            </div>
          )}
        </FuturisticFrame>

        {/* Discover Groups */}
        {publicGroups.length > 0 && (
          <FuturisticFrame title="DISCOVER GROUPS" color="blue" className="bg-slate-900/80 border border-blue-500/30 rounded-lg">
            <div className="grid md:grid-cols-2 gap-4">
              {publicGroups.filter(g => !myGroups.find(m => m.id === g.id)).slice(0, 6).map((group) => (
                <div key={group.id} className="p-4 bg-blue-500/10 rounded-lg">
                  <div className="flex items-start justify-between">
                    <div className="flex items-start gap-3">
                      <div className="w-12 h-12 bg-gradient-to-br from-blue-500/30 to-purple-500/30 rounded-lg flex items-center justify-center">
                        <Users className="w-6 h-6 text-blue-400" />
                      </div>
                      <div>
                        <h3 className="text-purple-300 font-mono font-bold">{group.name}</h3>
                        <p className="text-purple-400/60 font-mono text-xs">{group.member_count} members</p>
                      </div>
                    </div>
                    <button onClick={() => handleJoin(group.id)} className="px-3 py-1 bg-blue-600 text-white font-mono text-sm rounded hover:bg-blue-700">
                      JOIN
                    </button>
                  </div>
                </div>
              ))}
            </div>
          </FuturisticFrame>
        )}
      </div>
    </Layout>
  );
};

// Group Detail Page
const GroupDetailPage = () => {
  const { groupId } = useParams();
  const { user } = useAuth();
  const [group, setGroup] = useState(null);
  const [posts, setPosts] = useState([]);
  const [loading, setLoading] = useState(true);
  const [newPost, setNewPost] = useState('');
  const [posting, setPosting] = useState(false);
  const navigate = useNavigate();

  useEffect(() => { if (groupId) fetchGroup(); }, [groupId]);

  const fetchGroup = async () => {
    try {
      const res = await axios.get(`${API}/groups/${groupId}`);
      setGroup(res.data.group);
      setPosts(res.data.posts || []);
    } catch (error) {
      toast.error("Failed to load group");
      navigate("/groups");
    } finally {
      setLoading(false);
    }
  };

  const handlePost = async (e) => {
    e.preventDefault();
    if (!newPost.trim()) return;
    setPosting(true);
    try {
      await axios.post(`${API}/groups/${groupId}/posts`, { content: newPost });
      setNewPost('');
      fetchGroup();
      toast.success("Post created!");
    } catch (error) {
      toast.error(error.response?.data?.detail || "Failed to post");
    } finally {
      setPosting(false);
    }
  };

  const handleLeave = async () => {
    if (!window.confirm("Leave this group?")) return;
    try {
      await axios.post(`${API}/groups/${groupId}/leave`);
      toast.success("Left group");
      navigate("/groups");
    } catch (error) {
      toast.error(error.response?.data?.detail || "Failed to leave group");
    }
  };

  if (loading) return <Layout><div className="flex justify-center py-20"><Loader2 className="w-12 h-12 text-pink-400 animate-spin" /></div></Layout>;
  if (!group) return <Layout><div className="text-center py-20 text-purple-400 font-mono">Group not found</div></Layout>;

  const isMember = group.members?.includes(user?.id);

  return (
    <Layout>
      <div className="max-w-4xl mx-auto space-y-6">
        {/* Group Header */}
        <div className="bg-gradient-to-r from-pink-900/40 to-purple-900/40 rounded-xl p-6 border border-pink-500/30">
          <div className="flex items-start justify-between">
            <div className="flex items-center gap-4">
              <div className="w-20 h-20 bg-gradient-to-br from-pink-500/30 to-purple-500/30 rounded-xl flex items-center justify-center">
                <Users className="w-10 h-10 text-pink-400" />
              </div>
              <div>
                <h1 className="text-2xl font-bold text-transparent bg-clip-text bg-gradient-to-r from-pink-400 to-purple-400 font-mono">{group.name}</h1>
                <p className="text-purple-400/60 font-mono text-sm">{group.member_count} members • {group.privacy}</p>
                <p className="text-purple-300/80 font-mono text-sm mt-2">{group.description || "No description"}</p>
              </div>
            </div>
            {isMember && group.owner_id !== user?.id && (
              <button onClick={handleLeave} className="px-4 py-2 border border-red-500/50 text-red-400 font-mono rounded hover:bg-red-500/10">
                LEAVE
              </button>
            )}
          </div>
        </div>

        {/* Create Post */}
        {isMember && (
          <FuturisticFrame title="CREATE POST" color="purple" className="bg-slate-900/80 border border-purple-500/30 rounded-lg">
            <form onSubmit={handlePost} className="space-y-4">
              <textarea value={newPost} onChange={(e) => setNewPost(e.target.value)} placeholder="What's on your mind?" className="w-full px-4 py-3 bg-slate-950 border border-purple-500/30 rounded-lg text-purple-300 font-mono h-24 focus:border-pink-500 resize-none" data-testid="group-post-input" />
              <button type="submit" disabled={posting || !newPost.trim()} className="px-6 py-2 bg-gradient-to-r from-pink-600 to-purple-600 text-white font-mono rounded hover:scale-[1.02] disabled:opacity-50 flex items-center gap-2" data-testid="group-post-submit">
                {posting ? <Loader2 className="w-5 h-5 animate-spin" /> : <><Send className="w-5 h-5" /> POST</>}
              </button>
            </form>
          </FuturisticFrame>
        )}

        {/* Posts */}
        <div className="space-y-4">
          {posts.length === 0 ? (
            <div className="text-center py-12 bg-slate-900/50 rounded-lg border border-purple-500/20">
              <MessageCircle className="w-16 h-16 text-purple-400/30 mx-auto mb-4" />
              <p className="text-purple-400/60 font-mono">No posts yet. Be the first to post!</p>
            </div>
          ) : (
            posts.map((post) => (
              <PostCard key={post.id} post={post} postType="group" onUpdate={fetchGroup} />
            ))
          )}
        </div>
      </div>
    </Layout>
  );
};

// ============================================
// SOCIAL FEATURES - PAGES
// ============================================
const PagesPage = () => {
  const [myPages, setMyPages] = useState([]);
  const [following, setFollowing] = useState([]);
  const [popular, setPopular] = useState([]);
  const [loading, setLoading] = useState(true);
  const [showCreate, setShowCreate] = useState(false);
  const [newPage, setNewPage] = useState({ name: '', description: '', category: 'General' });
  const [creating, setCreating] = useState(false);
  const navigate = useNavigate();

  useEffect(() => { fetchPages(); }, []);

  const fetchPages = async () => {
    try {
      const res = await axios.get(`${API}/pages`);
      setMyPages(res.data.my_pages || []);
      setFollowing(res.data.following || []);
      setPopular(res.data.popular || []);
    } catch (error) {
      console.error("Failed to fetch pages");
    } finally {
      setLoading(false);
    }
  };

  const handleCreate = async (e) => {
    e.preventDefault();
    setCreating(true);
    try {
      await axios.post(`${API}/pages`, newPage);
      toast.success("Page created!");
      setShowCreate(false);
      setNewPage({ name: '', description: '', category: 'General' });
      fetchPages();
    } catch (error) {
      toast.error(error.response?.data?.detail || "Failed to create page");
    } finally {
      setCreating(false);
    }
  };

  const handleFollow = async (pageId) => {
    try {
      await axios.post(`${API}/pages/${pageId}/follow`);
      toast.success("Now following!");
      fetchPages();
    } catch (error) {
      toast.error(error.response?.data?.detail || "Failed to follow");
    }
  };

  const categories = ['General', 'Business', 'Community', 'Entertainment', 'Education', 'Technology', 'News', 'Sports'];

  return (
    <Layout>
      <div className="max-w-4xl mx-auto space-y-6">
        <div className="flex items-center justify-between">
          <h1 className="text-3xl font-bold text-transparent bg-clip-text bg-gradient-to-r from-pink-400 to-purple-400 font-mono tracking-wider">PAGES</h1>
          <button onClick={() => setShowCreate(true)} className="px-4 py-2 bg-gradient-to-r from-pink-600 to-purple-600 text-white font-mono rounded hover:scale-[1.02] flex items-center gap-2">
            <Plus className="w-5 h-5" /> CREATE PAGE
          </button>
        </div>

        {/* Create Modal */}
        {showCreate && (
          <div className="fixed inset-0 bg-black/80 flex items-center justify-center z-50 p-4">
            <FuturisticFrame title="CREATE PAGE" color="pink" className="bg-slate-900 border border-pink-500/30 rounded-lg max-w-lg w-full">
              <form onSubmit={handleCreate} className="space-y-4">
                <div>
                  <label className="block text-xs font-mono text-purple-400 mb-1">PAGE NAME</label>
                  <input type="text" value={newPage.name} onChange={(e) => setNewPage({ ...newPage, name: e.target.value })} className="w-full px-4 py-2 bg-slate-950 border border-purple-500/30 rounded text-purple-300 font-mono focus:border-pink-500" required />
                </div>
                <div>
                  <label className="block text-xs font-mono text-purple-400 mb-1">DESCRIPTION</label>
                  <textarea value={newPage.description} onChange={(e) => setNewPage({ ...newPage, description: e.target.value })} className="w-full px-4 py-2 bg-slate-950 border border-purple-500/30 rounded text-purple-300 font-mono h-24 focus:border-pink-500" placeholder="What's your page about?" />
                </div>
                <div>
                  <label className="block text-xs font-mono text-purple-400 mb-1">CATEGORY</label>
                  <select value={newPage.category} onChange={(e) => setNewPage({ ...newPage, category: e.target.value })} className="w-full px-4 py-2 bg-slate-950 border border-purple-500/30 rounded text-purple-300 font-mono focus:border-pink-500">
                    {categories.map(cat => <option key={cat} value={cat}>{cat}</option>)}
                  </select>
                </div>
                <div className="flex gap-4">
                  <button type="button" onClick={() => setShowCreate(false)} className="flex-1 px-4 py-2 border border-purple-500/30 text-purple-300 font-mono rounded hover:bg-purple-500/10">CANCEL</button>
                  <button type="submit" disabled={creating} className="flex-1 px-4 py-2 bg-gradient-to-r from-pink-600 to-purple-600 text-white font-mono rounded hover:scale-[1.02] disabled:opacity-50">
                    {creating ? <Loader2 className="w-5 h-5 animate-spin mx-auto" /> : "CREATE"}
                  </button>
                </div>
              </form>
            </FuturisticFrame>
          </div>
        )}

        {/* My Pages */}
        <FuturisticFrame title="MY PAGES" color="purple" className="bg-slate-900/80 border border-purple-500/30 rounded-lg">
          {loading ? (
            <div className="flex justify-center py-8"><Loader2 className="w-8 h-8 text-pink-400 animate-spin" /></div>
          ) : myPages.length === 0 ? (
            <div className="text-center py-8">
              <FileText className="w-16 h-16 text-purple-400/30 mx-auto mb-4" />
              <p className="text-purple-400/60 font-mono">You haven't created any pages yet</p>
              <button onClick={() => setShowCreate(true)} className="mt-4 px-4 py-2 bg-pink-600 text-white font-mono rounded hover:bg-pink-700">Create Your First Page</button>
            </div>
          ) : (
            <div className="grid md:grid-cols-2 gap-4">
              {myPages.map((page) => (
                <div key={page.id} onClick={() => navigate(`/pages/${page.id}`)} className="p-4 bg-purple-500/10 rounded-lg hover:bg-purple-500/20 cursor-pointer transition-colors">
                  <div className="flex items-start gap-3">
                    <div className="w-14 h-14 bg-gradient-to-br from-pink-500/30 to-purple-500/30 rounded-lg flex items-center justify-center">
                      <FileText className="w-7 h-7 text-pink-400" />
                    </div>
                    <div className="flex-1">
                      <h3 className="text-purple-300 font-mono font-bold">{page.name}</h3>
                      <p className="text-purple-400/60 font-mono text-xs mt-1">{page.follower_count} followers • {page.category}</p>
                      <p className="text-purple-400/40 font-mono text-xs mt-1 line-clamp-2">{page.description || "No description"}</p>
                    </div>
                  </div>
                </div>
              ))}
            </div>
          )}
        </FuturisticFrame>

        {/* Popular Pages */}
        {popular.length > 0 && (
          <FuturisticFrame title="POPULAR PAGES" color="blue" className="bg-slate-900/80 border border-blue-500/30 rounded-lg">
            <div className="grid md:grid-cols-2 gap-4">
              {popular.filter(p => !myPages.find(m => m.id === p.id)).slice(0, 6).map((page) => (
                <div key={page.id} className="p-4 bg-blue-500/10 rounded-lg">
                  <div className="flex items-start justify-between">
                    <div className="flex items-start gap-3 cursor-pointer" onClick={() => navigate(`/pages/${page.id}`)}>
                      <div className="w-12 h-12 bg-gradient-to-br from-blue-500/30 to-purple-500/30 rounded-lg flex items-center justify-center">
                        <FileText className="w-6 h-6 text-blue-400" />
                      </div>
                      <div>
                        <h3 className="text-purple-300 font-mono font-bold">{page.name}</h3>
                        <p className="text-purple-400/60 font-mono text-xs">{page.follower_count} followers</p>
                      </div>
                    </div>
                    <button onClick={() => handleFollow(page.id)} className="px-3 py-1 bg-blue-600 text-white font-mono text-sm rounded hover:bg-blue-700">
                      FOLLOW
                    </button>
                  </div>
                </div>
              ))}
            </div>
          </FuturisticFrame>
        )}
      </div>
    </Layout>
  );
};

// Page Detail Page
const PageDetailPage = () => {
  const { pageId } = useParams();
  const { user } = useAuth();
  const [page, setPage] = useState(null);
  const [posts, setPosts] = useState([]);
  const [isFollowing, setIsFollowing] = useState(false);
  const [loading, setLoading] = useState(true);
  const [newPost, setNewPost] = useState('');
  const [posting, setPosting] = useState(false);
  const navigate = useNavigate();

  useEffect(() => { if (pageId) fetchPage(); }, [pageId]);

  const fetchPage = async () => {
    try {
      const res = await axios.get(`${API}/pages/${pageId}`);
      setPage(res.data.page);
      setPosts(res.data.posts || []);
      setIsFollowing(res.data.is_following);
    } catch (error) {
      toast.error("Failed to load page");
      navigate("/pages");
    } finally {
      setLoading(false);
    }
  };

  const handlePost = async (e) => {
    e.preventDefault();
    if (!newPost.trim()) return;
    setPosting(true);
    try {
      await axios.post(`${API}/pages/${pageId}/posts`, { content: newPost });
      setNewPost('');
      fetchPage();
      toast.success("Post created!");
    } catch (error) {
      toast.error(error.response?.data?.detail || "Failed to post");
    } finally {
      setPosting(false);
    }
  };

  const handleFollow = async () => {
    try {
      if (isFollowing) {
        await axios.post(`${API}/pages/${pageId}/unfollow`);
        toast.success("Unfollowed");
      } else {
        await axios.post(`${API}/pages/${pageId}/follow`);
        toast.success("Now following!");
      }
      fetchPage();
    } catch (error) {
      toast.error("Failed to update follow status");
    }
  };

  if (loading) return <Layout><div className="flex justify-center py-20"><Loader2 className="w-12 h-12 text-pink-400 animate-spin" /></div></Layout>;
  if (!page) return <Layout><div className="text-center py-20 text-purple-400 font-mono">Page not found</div></Layout>;

  const isAdmin = page.admins?.includes(user?.id);

  return (
    <Layout>
      <div className="max-w-4xl mx-auto space-y-6">
        {/* Page Header */}
        <div className="bg-gradient-to-r from-pink-900/40 to-purple-900/40 rounded-xl p-6 border border-pink-500/30">
          <div className="flex items-start justify-between">
            <div className="flex items-center gap-4">
              <div className="w-20 h-20 bg-gradient-to-br from-pink-500/30 to-purple-500/30 rounded-xl flex items-center justify-center">
                <FileText className="w-10 h-10 text-pink-400" />
              </div>
              <div>
                <h1 className="text-2xl font-bold text-transparent bg-clip-text bg-gradient-to-r from-pink-400 to-purple-400 font-mono">{page.name}</h1>
                <p className="text-purple-400/60 font-mono text-sm">{page.follower_count} followers • {page.category}</p>
                <p className="text-purple-300/80 font-mono text-sm mt-2">{page.description || "No description"}</p>
              </div>
            </div>
            <button onClick={handleFollow} className={`px-4 py-2 font-mono rounded ${isFollowing ? 'border border-purple-500/50 text-purple-400 hover:bg-purple-500/10' : 'bg-pink-600 text-white hover:bg-pink-700'}`}>
              {isFollowing ? 'FOLLOWING' : 'FOLLOW'}
            </button>
          </div>
        </div>

        {/* Create Post (Admin only) */}
        {isAdmin && (
          <FuturisticFrame title="CREATE POST" color="purple" className="bg-slate-900/80 border border-purple-500/30 rounded-lg">
            <form onSubmit={handlePost} className="space-y-4">
              <textarea value={newPost} onChange={(e) => setNewPost(e.target.value)} placeholder="Share an update with your followers..." className="w-full px-4 py-3 bg-slate-950 border border-purple-500/30 rounded-lg text-purple-300 font-mono h-24 focus:border-pink-500 resize-none" data-testid="page-post-input" />
              <button type="submit" disabled={posting || !newPost.trim()} className="px-6 py-2 bg-gradient-to-r from-pink-600 to-purple-600 text-white font-mono rounded hover:scale-[1.02] disabled:opacity-50 flex items-center gap-2" data-testid="page-post-submit">
                {posting ? <Loader2 className="w-5 h-5 animate-spin" /> : <><Send className="w-5 h-5" /> POST</>}
              </button>
            </form>
          </FuturisticFrame>
        )}

        {/* Posts */}
        <div className="space-y-4">
          {posts.length === 0 ? (
            <div className="text-center py-12 bg-slate-900/50 rounded-lg border border-purple-500/20">
              <MessageCircle className="w-16 h-16 text-purple-400/30 mx-auto mb-4" />
              <p className="text-purple-400/60 font-mono">No posts yet.</p>
            </div>
          ) : (
            posts.map((post) => (
              <PostCard key={post.id} post={{...post, username: page.name}} postType="page" onUpdate={fetchPage} />
            ))
          )}
        </div>
      </div>
    </Layout>
  );
};

// Admin Page
const AdminPage = () => {
  const { user } = useAuth();
  const [activeTab, setActiveTab] = useState("dashboard");
  const [privacyPolicy, setPrivacyPolicy] = useState("");
  const [termsOfService, setTermsOfService] = useState("");
  const [loading, setLoading] = useState(true);
  const [saving, setSaving] = useState(false);
  
  // Subscription management state
  const [subscriptionConfig, setSubscriptionConfig] = useState({
    regular_price: 4.62,
    min_price: 0.01,
    promo_end_date: "2026-03-02",
    paypal_link_1: "",
    paypal_link_2: ""
  });
  const [subscriptions, setSubscriptions] = useState({ subscriptions: [], total_count: 0, active_count: 0, total_revenue: 0 });
  
  // Database limits state
  const [dbLimits, setDbLimits] = useState({ user_max_results_limit: 4000, top_users_by_results: [] });
  const [newDbLimit, setNewDbLimit] = useState(4000);
  
  // Search pages config state
  const [searchPagesConfig, setSearchPagesConfig] = useState({
    unpaid_user_search_pages: 50,
    paid_user_search_pages: 99,
    results_per_page: 20,
    is_app_free: true
  });
  const [newUnpaidPages, setNewUnpaidPages] = useState(50);
  const [newPaidPages, setNewPaidPages] = useState(99);

  useEffect(() => {
    if (user?.is_admin) {
      fetchLegalPages();
      fetchSubscriptionConfig();
      fetchSubscriptions();
      fetchDbLimits();
      fetchSearchPagesConfig();
    }
  }, [user]);
  
  const fetchSearchPagesConfig = async () => {
    try {
      const res = await axios.get(`${API}/admin/search-pages-config`);
      setSearchPagesConfig(res.data);
      setNewUnpaidPages(res.data.unpaid_user_search_pages);
      setNewPaidPages(res.data.paid_user_search_pages);
    } catch (error) {
      console.error("Failed to fetch search pages config");
    }
  };
  
  const saveSearchPagesConfig = async () => {
    setSaving(true);
    try {
      const params = new URLSearchParams();
      params.append('unpaid_user_search_pages', newUnpaidPages);
      params.append('paid_user_search_pages', newPaidPages);
      const res = await axios.put(`${API}/admin/search-pages-config?${params.toString()}`);
      toast.success(res.data.message);
      setSearchPagesConfig(res.data);
    } catch (error) {
      toast.error(error.response?.data?.detail || "Failed to save search pages config");
    } finally {
      setSaving(false);
    }
  };
  
  const fetchDbLimits = async () => {
    try {
      const res = await axios.get(`${API}/admin/database-limits`);
      setDbLimits(res.data);
      setNewDbLimit(res.data.user_max_results_limit);
    } catch (error) {
      console.error("Failed to fetch database limits");
    }
  };
  
  const saveDbLimit = async () => {
    setSaving(true);
    try {
      await axios.put(`${API}/admin/database-limits?user_max_results_limit=${newDbLimit}`);
      toast.success(`Database limit updated to ${newDbLimit} results per user`);
      fetchDbLimits();
    } catch (error) {
      toast.error(error.response?.data?.detail || "Failed to save database limit");
    } finally {
      setSaving(false);
    }
  };

  const fetchLegalPages = async () => {
    try {
      const [privacyRes, termsRes] = await Promise.all([
        axios.get(`${API}/legal/privacy-policy`),
        axios.get(`${API}/legal/terms-of-service`)
      ]);
      setPrivacyPolicy(privacyRes.data.content);
      setTermsOfService(termsRes.data.content);
    } catch (error) {
      console.error("Failed to fetch legal pages");
    } finally {
      setLoading(false);
    }
  };

  const fetchSubscriptionConfig = async () => {
    try {
      const res = await axios.get(`${API}/subscription/config`);
      setSubscriptionConfig(prev => ({
        ...prev,
        regular_price: res.data.regular_price || 4.62,
        min_price: res.data.min_price || 0.01,
        max_price: res.data.max_price || 100,
        preset_amounts: res.data.preset_amounts || "1.00, 2.00, 4.62, 10.00",
        promo_end_date: res.data.promo_end_date?.split("T")[0] || "2026-03-02",
        promo_message: res.data.promo_message || "Pay What You Want - Limited Time!",
        paypal_link_1: res.data.paypal_link_1 || "",
        paypal_link_2: res.data.paypal_link_2 || ""
      }));
    } catch (error) {
      console.error("Failed to fetch subscription config");
    }
  };

  const fetchSubscriptions = async () => {
    try {
      const res = await axios.get(`${API}/admin/subscriptions`);
      setSubscriptions(res.data);
    } catch (error) {
      console.error("Failed to fetch subscriptions");
    }
  };

  const saveSubscriptionConfig = async () => {
    setSaving(true);
    try {
      const params = new URLSearchParams();
      params.append("regular_price", subscriptionConfig.regular_price);
      params.append("min_price", subscriptionConfig.min_price);
      params.append("max_price", subscriptionConfig.max_price || 100);
      params.append("preset_amounts", subscriptionConfig.preset_amounts || "1.00, 2.00, 4.62, 10.00");
      params.append("promo_end_date", subscriptionConfig.promo_end_date);
      params.append("promo_message", subscriptionConfig.promo_message || "Pay What You Want - Limited Time!");
      if (subscriptionConfig.paypal_link_1) params.append("paypal_link_1", subscriptionConfig.paypal_link_1);
      if (subscriptionConfig.paypal_link_2) params.append("paypal_link_2", subscriptionConfig.paypal_link_2);
      
      await axios.put(`${API}/admin/subscription/config?${params.toString()}`);
      toast.success("Subscription pricing settings saved!");
    } catch (error) {
      toast.error("Failed to save subscription settings");
    } finally {
      setSaving(false);
    }
  };

  const savePrivacyPolicy = async () => {
    setSaving(true);
    try {
      await axios.put(`${API}/admin/legal/privacy-policy?content=${encodeURIComponent(privacyPolicy)}`);
      toast.success("Privacy Policy updated!");
    } catch (error) {
      toast.error("Failed to save Privacy Policy");
    } finally {
      setSaving(false);
    }
  };

  const saveTermsOfService = async () => {
    setSaving(true);
    try {
      await axios.put(`${API}/admin/legal/terms-of-service?content=${encodeURIComponent(termsOfService)}`);
      toast.success("Terms of Service updated!");
    } catch (error) {
      toast.error("Failed to save Terms of Service");
    } finally {
      setSaving(false);
    }
  };

  if (!user?.is_admin) {
    return (<Layout><div className="text-center py-12"><Shield className="w-16 h-16 text-red-400/50 mx-auto mb-4" /><h1 className="text-2xl font-bold text-red-400 font-mono">ACCESS DENIED</h1></div></Layout>);
  }

  return (
    <Layout>
      <div className="max-w-6xl mx-auto">
        <h1 className="text-3xl font-bold text-transparent bg-clip-text bg-gradient-to-r from-pink-400 to-purple-400 font-mono tracking-wider mb-6">ADMIN CONTROL</h1>
        
        {/* Admin Tabs */}
        <div className="flex gap-2 mb-6 overflow-x-auto">
          {[
            { id: "dashboard", label: "Dashboard", icon: Shield },
            { id: "search-pages", label: "Search Pages", icon: Search },
            { id: "database", label: "Database Limits", icon: BarChart3 },
            { id: "subscriptions", label: "Subscriptions", icon: CreditCard },
            { id: "privacy", label: "Privacy Policy", icon: Lock },
            { id: "terms", label: "Terms of Service", icon: FileText }
          ].map(tab => (
            <button
              key={tab.id}
              onClick={() => setActiveTab(tab.id)}
              className={`flex items-center gap-2 px-4 py-2 rounded font-mono text-sm whitespace-nowrap ${
                activeTab === tab.id 
                  ? 'bg-gradient-to-r from-pink-600 to-purple-600 text-white' 
                  : 'bg-slate-900 text-purple-400 border border-purple-500/30 hover:border-pink-500/50'
              }`}
              data-testid={`admin-tab-${tab.id}`}
            >
              <tab.icon className="w-4 h-4" /> {tab.label}
            </button>
          ))}
        </div>

        {/* Dashboard Tab */}
        {activeTab === "dashboard" && (
          <FuturisticFrame title="SYSTEM STATUS" color="purple" className="bg-slate-900/80 border border-purple-500/30 rounded-lg">
            <div className="space-y-4">
              <p className="text-purple-300 font-mono">Admin dashboard for InfoPilot Explorer system management.</p>
              <div className="grid grid-cols-1 md:grid-cols-4 gap-4 mt-4">
                <div className="bg-slate-950 p-4 rounded border border-green-500/30">
                  <p className="text-green-400 font-mono text-sm">SYSTEM STATUS</p>
                  <p className="text-green-300 font-mono text-2xl mt-2">OPERATIONAL</p>
                </div>
                <div className="bg-slate-950 p-4 rounded border border-purple-500/30">
                  <p className="text-purple-400 font-mono text-sm">APP VERSION</p>
                  <p className="text-purple-300 font-mono text-2xl mt-2">2.0.0</p>
                </div>
                <div className="bg-slate-950 p-4 rounded border border-pink-500/30">
                  <p className="text-pink-400 font-mono text-sm">TOTAL SUBSCRIBERS</p>
                  <p className="text-pink-300 font-mono text-2xl mt-2">{subscriptions.active_count}</p>
                </div>
                <div className="bg-slate-950 p-4 rounded border border-yellow-500/30">
                  <p className="text-yellow-400 font-mono text-sm">TOTAL REVENUE</p>
                  <p className="text-yellow-300 font-mono text-2xl mt-2">${subscriptions.total_revenue}</p>
                </div>
              </div>
              <div className="mt-4 p-4 bg-slate-950 rounded border border-pink-500/20">
                <p className="text-pink-400 font-mono text-sm mb-2">QUICK LINKS</p>
                <div className="flex flex-wrap gap-2">
                  <a href="/privacy-policy" target="_blank" className="text-purple-400 hover:text-pink-400 font-mono text-sm underline">Privacy Policy</a>
                  <span className="text-purple-400/40">|</span>
                  <a href="/terms-of-service" target="_blank" className="text-purple-400 hover:text-pink-400 font-mono text-sm underline">Terms of Service</a>
                  <span className="text-purple-400/40">|</span>
                  <a href="/subscribe" target="_blank" className="text-purple-400 hover:text-pink-400 font-mono text-sm underline">Subscribe Page</a>
                </div>
              </div>
            </div>
          </FuturisticFrame>
        )}

        {/* Search Pages Config Tab */}
        {activeTab === "search-pages" && (
          <div className="space-y-6">
            <FuturisticFrame title="🔍 SEARCH PAGES CONFIGURATION" color="purple" className="bg-slate-900/80 border border-purple-500/30 rounded-lg">
              <div className="space-y-6">
                <p className="text-purple-300/70 font-mono text-sm">
                  Control how many pages of search results users can collate per search. Each page contains {searchPagesConfig.results_per_page} results.
                </p>
                
                {/* App Status Banner */}
                <div className={`p-4 rounded border ${searchPagesConfig.is_app_free ? 'bg-green-500/10 border-green-500/30' : 'bg-yellow-500/10 border-yellow-500/30'}`}>
                  <div className="flex items-center gap-3">
                    {searchPagesConfig.is_app_free ? (
                      <>
                        <div className="w-3 h-3 bg-green-500 rounded-full animate-pulse" />
                        <span className="text-green-400 font-mono font-bold">APP IS FREE</span>
                        <span className="text-green-300/70 font-mono text-sm">- Unpaid users get {searchPagesConfig.unpaid_user_search_pages} pages (more than 40)</span>
                      </>
                    ) : (
                      <>
                        <div className="w-3 h-3 bg-yellow-500 rounded-full" />
                        <span className="text-yellow-400 font-mono font-bold">SUBSCRIPTION REQUIRED</span>
                        <span className="text-yellow-300/70 font-mono text-sm">- Unpaid users limited to {searchPagesConfig.unpaid_user_search_pages} pages</span>
                      </>
                    )}
                  </div>
                </div>
                
                {/* Current Settings Display */}
                <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
                  <div className="bg-slate-950 p-4 rounded border border-purple-500/30">
                    <p className="text-purple-400/60 font-mono text-xs">UNPAID USERS</p>
                    <p className="text-3xl font-mono text-purple-300">{searchPagesConfig.unpaid_user_search_pages} pages</p>
                    <p className="text-purple-400/50 font-mono text-xs mt-1">= {searchPagesConfig.unpaid_max_results} max results</p>
                  </div>
                  <div className="bg-slate-950 p-4 rounded border border-pink-500/30">
                    <p className="text-pink-400/60 font-mono text-xs">PAID USERS</p>
                    <p className="text-3xl font-mono text-pink-300">{searchPagesConfig.paid_user_search_pages} pages</p>
                    <p className="text-pink-400/50 font-mono text-xs mt-1">= {searchPagesConfig.paid_max_results} max results</p>
                  </div>
                </div>
                
                {/* Update Settings Form */}
                <div className="space-y-4 pt-4 border-t border-purple-500/20">
                  <h3 className="text-lg font-mono text-purple-400">Update Settings</h3>
                  
                  <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
                    <div>
                      <label className="block text-xs font-mono text-purple-400 mb-2">
                        UNPAID USER PAGES (1-99)
                        <span className="text-green-400 ml-2">{newUnpaidPages > 40 ? '= FREE APP' : ''}</span>
                      </label>
                      <input
                        type="number"
                        min="1"
                        max="99"
                        value={newUnpaidPages}
                        onChange={(e) => setNewUnpaidPages(parseInt(e.target.value) || 1)}
                        className="w-full px-4 py-2 bg-slate-950 border border-purple-500/30 rounded text-purple-300 font-mono focus:border-pink-500"
                        data-testid="unpaid-pages-input"
                      />
                      <p className="text-purple-400/50 font-mono text-xs mt-1">
                        &gt;40 pages = App is advertised as FREE
                      </p>
                    </div>
                    <div>
                      <label className="block text-xs font-mono text-pink-400 mb-2">PAID USER PAGES (1-99)</label>
                      <input
                        type="number"
                        min="1"
                        max="99"
                        value={newPaidPages}
                        onChange={(e) => setNewPaidPages(parseInt(e.target.value) || 1)}
                        className="w-full px-4 py-2 bg-slate-950 border border-pink-500/30 rounded text-pink-300 font-mono focus:border-pink-500"
                        data-testid="paid-pages-input"
                      />
                    </div>
                  </div>
                  
                  {/* Quick Preset Buttons */}
                  <div className="flex flex-wrap gap-2">
                    <span className="text-purple-400/60 font-mono text-xs">Unpaid presets:</span>
                    {[6, 20, 40, 50, 75, 99].map(preset => (
                      <button
                        key={preset}
                        type="button"
                        onClick={() => setNewUnpaidPages(preset)}
                        className={`px-3 py-1 font-mono text-xs rounded ${
                          newUnpaidPages === preset 
                            ? 'bg-purple-500/30 text-purple-300 border border-purple-500/50'
                            : 'bg-slate-800 text-purple-400 hover:bg-slate-700'
                        } ${preset > 40 ? 'ring-1 ring-green-500/30' : ''}`}
                      >
                        {preset} {preset > 40 ? '(FREE)' : ''}
                      </button>
                    ))}
                  </div>
                  
                  <button
                    type="button"
                    onClick={saveSearchPagesConfig}
                    disabled={saving}
                    className="px-6 py-2 bg-gradient-to-r from-purple-600 to-pink-600 text-white font-mono rounded hover:scale-[1.02] disabled:opacity-50 flex items-center gap-2"
                    data-testid="save-search-pages-btn"
                  >
                    {saving ? <Loader2 className="w-4 h-4 animate-spin" /> : "SAVE CONFIGURATION"}
                  </button>
                </div>
              </div>
            </FuturisticFrame>
          </div>
        )}

        {/* Database Limits Tab */}
        {activeTab === "database" && (
          <div className="space-y-6">
            <FuturisticFrame title="📊 USER DATABASE LIMITS" color="blue" className="bg-slate-900/80 border border-blue-500/30 rounded-lg">
              <div className="space-y-6">
                <p className="text-purple-300/70 font-mono text-sm">
                  Control the maximum number of search results each user can store in their database.
                </p>
                
                {/* Current Limit Display */}
                <div className="flex items-center gap-4 p-4 bg-slate-950 rounded border border-blue-500/30">
                  <div className="flex-1">
                    <p className="text-blue-400/60 font-mono text-xs">CURRENT LIMIT PER USER</p>
                    <p className="text-3xl font-mono text-blue-300">{dbLimits.user_max_results_limit.toLocaleString()} results</p>
                  </div>
                </div>
                
                {/* Update Limit Form */}
                <div className="space-y-4">
                  <div>
                    <label className="block text-xs font-mono text-purple-400 mb-2">SET NEW LIMIT (100 - 10,000)</label>
                    <div className="flex gap-4">
                      <input
                        type="number"
                        min="100"
                        max="10000"
                        value={newDbLimit}
                        onChange={(e) => setNewDbLimit(parseInt(e.target.value) || 4000)}
                        className="flex-1 px-4 py-2 bg-slate-950 border border-purple-500/30 rounded text-purple-300 font-mono focus:border-pink-500"
                        data-testid="db-limit-input"
                      />
                      <button
                        onClick={saveDbLimit}
                        disabled={saving || newDbLimit < 100 || newDbLimit > 10000}
                        className="px-6 py-2 bg-gradient-to-r from-blue-600 to-purple-600 text-white font-mono rounded hover:scale-[1.02] disabled:opacity-50 flex items-center gap-2"
                        data-testid="save-db-limit-btn"
                      >
                        {saving ? <Loader2 className="w-4 h-4 animate-spin" /> : "SAVE LIMIT"}
                      </button>
                    </div>
                  </div>
                  
                  {/* Quick Preset Buttons */}
                  <div className="flex flex-wrap gap-2">
                    <span className="text-purple-400/60 font-mono text-xs">Quick presets:</span>
                    {[1000, 2000, 4000, 5000, 10000].map(preset => (
                      <button
                        key={preset}
                        onClick={() => setNewDbLimit(preset)}
                        className={`px-3 py-1 font-mono text-xs rounded ${
                          newDbLimit === preset 
                            ? 'bg-blue-500/30 text-blue-300 border border-blue-500/50'
                            : 'bg-slate-800 text-purple-400 hover:bg-slate-700'
                        }`}
                      >
                        {preset.toLocaleString()}
                      </button>
                    ))}
                  </div>
                </div>
                
                {/* Top Users by Results */}
                {dbLimits.top_users_by_results && dbLimits.top_users_by_results.length > 0 && (
                  <div className="mt-6 pt-6 border-t border-purple-500/20">
                    <h3 className="text-lg font-mono text-purple-400 mb-4">TOP USERS BY STORED RESULTS</h3>
                    <div className="space-y-2 max-h-64 overflow-y-auto">
                      {dbLimits.top_users_by_results.map((userStat, idx) => (
                        <div key={userStat.user_id} className="flex items-center justify-between p-3 bg-slate-950 rounded border border-purple-500/20">
                          <div className="flex items-center gap-3">
                            <span className="text-pink-400 font-mono text-sm">#{idx + 1}</span>
                            <span className="text-purple-300 font-mono">{userStat.username || 'Unknown User'}</span>
                          </div>
                          <div className="flex items-center gap-2">
                            <span className="text-purple-400 font-mono text-sm">{userStat.result_count.toLocaleString()} results</span>
                            <div className="w-24 h-2 bg-slate-800 rounded-full overflow-hidden">
                              <div 
                                className={`h-full rounded-full ${
                                  (userStat.result_count / dbLimits.user_max_results_limit) > 0.9 ? 'bg-red-500' :
                                  (userStat.result_count / dbLimits.user_max_results_limit) > 0.7 ? 'bg-yellow-500' : 'bg-green-500'
                                }`}
                                style={{ width: `${Math.min((userStat.result_count / dbLimits.user_max_results_limit) * 100, 100)}%` }}
                              />
                            </div>
                          </div>
                        </div>
                      ))}
                    </div>
                  </div>
                )}
              </div>
            </FuturisticFrame>
          </div>
        )}

        {/* Subscriptions Tab */}
        {activeTab === "subscriptions" && (
          <div className="space-y-6">
            {/* Subscription Config */}
            <FuturisticFrame title="💳 SUBSCRIPTION PRICING" color="pink" className="bg-slate-900/80 border border-pink-500/30 rounded-lg">
              <div className="space-y-6">
                {/* Pricing Section */}
                <div className="p-4 bg-yellow-500/10 border border-yellow-500/30 rounded-lg">
                  <h4 className="text-yellow-400 font-mono font-bold mb-4 flex items-center gap-2">
                    <DollarSign className="w-5 h-5" /> 1-YEAR SUBSCRIPTION PRICING
                  </h4>
                  <div className="grid grid-cols-1 md:grid-cols-3 gap-4">
                    <div>
                      <label className="block text-purple-400 font-mono text-sm mb-2">Minimum Price ($)</label>
                      <input
                        type="number"
                        value={subscriptionConfig.min_price}
                        onChange={(e) => setSubscriptionConfig(prev => ({ ...prev, min_price: parseFloat(e.target.value) || 0.01 }))}
                        step="0.01"
                        min="0.01"
                        className="w-full px-4 py-2 bg-slate-950 border border-purple-500/30 rounded text-purple-300 font-mono focus:border-pink-500"
                      />
                      <p className="text-purple-400/40 font-mono text-xs mt-1">Lowest amount users can pay</p>
                    </div>
                    <div>
                      <label className="block text-purple-400 font-mono text-sm mb-2">Regular Price ($/year)</label>
                      <input
                        type="number"
                        value={subscriptionConfig.regular_price}
                        onChange={(e) => setSubscriptionConfig(prev => ({ ...prev, regular_price: parseFloat(e.target.value) || 4.62 }))}
                        step="0.01"
                        min="0.01"
                        className="w-full px-4 py-2 bg-slate-950 border border-purple-500/30 rounded text-purple-300 font-mono focus:border-pink-500"
                      />
                      <p className="text-purple-400/40 font-mono text-xs mt-1">Price after promo ends</p>
                    </div>
                    <div>
                      <label className="block text-purple-400 font-mono text-sm mb-2">Max Custom Price ($)</label>
                      <input
                        type="number"
                        value={subscriptionConfig.max_price || 100}
                        onChange={(e) => setSubscriptionConfig(prev => ({ ...prev, max_price: parseFloat(e.target.value) || 100 }))}
                        step="1"
                        min="1"
                        className="w-full px-4 py-2 bg-slate-950 border border-purple-500/30 rounded text-purple-300 font-mono focus:border-pink-500"
                      />
                      <p className="text-purple-400/40 font-mono text-xs mt-1">Maximum for custom amount</p>
                    </div>
                  </div>
                </div>

                {/* Preset Amounts Section */}
                <div className="p-4 bg-blue-500/10 border border-blue-500/30 rounded-lg">
                  <h4 className="text-blue-400 font-mono font-bold mb-4 flex items-center gap-2">
                    <Settings className="w-5 h-5" /> PRESET AMOUNT BUTTONS
                  </h4>
                  <p className="text-purple-400/60 font-mono text-xs mb-4">
                    Comma-separated list of preset amounts shown to users (e.g., "1.00, 2.00, 4.62, 10.00")
                  </p>
                  <input
                    type="text"
                    value={subscriptionConfig.preset_amounts || "1.00, 2.00, 4.62, 10.00"}
                    onChange={(e) => setSubscriptionConfig(prev => ({ ...prev, preset_amounts: e.target.value }))}
                    placeholder="1.00, 2.00, 4.62, 10.00"
                    className="w-full px-4 py-2 bg-slate-950 border border-purple-500/30 rounded text-purple-300 font-mono focus:border-pink-500"
                  />
                  <div className="mt-3 flex flex-wrap gap-2">
                    <span className="text-purple-400/60 font-mono text-xs">Preview:</span>
                    {(subscriptionConfig.preset_amounts || "1.00, 2.00, 4.62, 10.00").split(",").map((amt, i) => (
                      <span key={i} className="px-3 py-1 bg-purple-500/20 text-purple-300 rounded font-mono text-sm">
                        ${amt.trim()}
                      </span>
                    ))}
                  </div>
                </div>

                {/* Promo Period Section */}
                <div className="p-4 bg-green-500/10 border border-green-500/30 rounded-lg">
                  <h4 className="text-green-400 font-mono font-bold mb-4 flex items-center gap-2">
                    <Calendar className="w-5 h-5" /> PROMOTIONAL PERIOD
                  </h4>
                  <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
                    <div>
                      <label className="block text-purple-400 font-mono text-sm mb-2">Promo End Date</label>
                      <input
                        type="date"
                        value={subscriptionConfig.promo_end_date}
                        onChange={(e) => setSubscriptionConfig(prev => ({ ...prev, promo_end_date: e.target.value }))}
                        className="w-full px-4 py-2 bg-slate-950 border border-purple-500/30 rounded text-purple-300 font-mono focus:border-pink-500"
                      />
                      <p className="text-purple-400/40 font-mono text-xs mt-1">"Pay What You Want" ends on this date</p>
                    </div>
                    <div>
                      <label className="block text-purple-400 font-mono text-sm mb-2">Promo Message</label>
                      <input
                        type="text"
                        value={subscriptionConfig.promo_message || "Pay What You Want - Limited Time!"}
                        onChange={(e) => setSubscriptionConfig(prev => ({ ...prev, promo_message: e.target.value }))}
                        className="w-full px-4 py-2 bg-slate-950 border border-purple-500/30 rounded text-purple-300 font-mono focus:border-pink-500"
                      />
                    </div>
                  </div>
                </div>

                {/* PayPal Links Section */}
                <div className="p-4 bg-purple-500/10 border border-purple-500/30 rounded-lg">
                  <h4 className="text-purple-400 font-mono font-bold mb-4 flex items-center gap-2">
                    <CreditCard className="w-5 h-5" /> PAYPAL INTEGRATION
                  </h4>
                  <div className="grid grid-cols-1 gap-4">
                    <div>
                      <label className="block text-purple-400 font-mono text-sm mb-2">PayPal Payment Link</label>
                      <input
                        type="url"
                        value={subscriptionConfig.paypal_link_1}
                        onChange={(e) => setSubscriptionConfig(prev => ({ ...prev, paypal_link_1: e.target.value }))}
                        placeholder="https://www.paypal.com/ncp/payment/..."
                        className="w-full px-4 py-2 bg-slate-950 border border-purple-500/30 rounded text-purple-300 font-mono focus:border-pink-500"
                      />
                    </div>
                    <div>
                      <label className="block text-purple-400 font-mono text-sm mb-2">Alternative PayPal Link</label>
                      <input
                        type="url"
                        value={subscriptionConfig.paypal_link_2}
                        onChange={(e) => setSubscriptionConfig(prev => ({ ...prev, paypal_link_2: e.target.value }))}
                        placeholder="https://www.paypal.com/ncp/payment/..."
                        className="w-full px-4 py-2 bg-slate-950 border border-purple-500/30 rounded text-purple-300 font-mono focus:border-pink-500"
                      />
                    </div>
                    <div className="p-3 bg-slate-950 rounded border border-yellow-500/20">
                      <p className="text-yellow-400 font-mono text-xs">
                        💡 TIP: PayPal IPN (Instant Payment Notification) is enabled. Payments are automatically recorded when completed.
                      </p>
                    </div>
                  </div>
                </div>
              </div>
              
              <div className="mt-6 flex justify-end">
                <button
                  onClick={saveSubscriptionConfig}
                  disabled={saving}
                  className="px-6 py-3 bg-gradient-to-r from-pink-600 to-purple-600 text-white font-mono rounded hover:scale-[1.02] disabled:opacity-50 flex items-center gap-2"
                >
                  {saving ? <Loader2 className="w-5 h-5 animate-spin" /> : <Check className="w-5 h-5" />}
                  SAVE ALL PRICING SETTINGS
                </button>
              </div>
            </FuturisticFrame>

            {/* Subscription Stats */}
            <FuturisticFrame title="📊 SUBSCRIPTION STATS" color="green" className="bg-slate-900/80 border border-green-500/30 rounded-lg">
              <div className="grid grid-cols-1 md:grid-cols-3 gap-4 mb-4">
                <div className="bg-slate-950 p-4 rounded border border-green-500/20 text-center">
                  <p className="text-green-400 font-mono text-sm">ACTIVE SUBSCRIBERS</p>
                  <p className="text-green-300 font-mono text-3xl font-bold mt-2">{subscriptions.active_count}</p>
                </div>
                <div className="bg-slate-950 p-4 rounded border border-purple-500/20 text-center">
                  <p className="text-purple-400 font-mono text-sm">TOTAL SUBSCRIPTIONS</p>
                  <p className="text-purple-300 font-mono text-3xl font-bold mt-2">{subscriptions.total_count}</p>
                </div>
                <div className="bg-slate-950 p-4 rounded border border-yellow-500/20 text-center">
                  <p className="text-yellow-400 font-mono text-sm">TOTAL REVENUE</p>
                  <p className="text-yellow-300 font-mono text-3xl font-bold mt-2">${subscriptions.total_revenue}</p>
                </div>
              </div>

              {/* Recent Subscriptions */}
              {subscriptions.subscriptions?.length > 0 && (
                <div className="mt-4">
                  <p className="text-purple-400 font-mono text-sm mb-2">RECENT SUBSCRIPTIONS</p>
                  <div className="overflow-x-auto">
                    <table className="w-full text-sm font-mono">
                      <thead>
                        <tr className="text-purple-400/60 border-b border-purple-500/20">
                          <th className="text-left py-2 px-2">User</th>
                          <th className="text-left py-2 px-2">Amount</th>
                          <th className="text-left py-2 px-2">Date</th>
                          <th className="text-left py-2 px-2">Status</th>
                        </tr>
                      </thead>
                      <tbody>
                        {subscriptions.subscriptions.slice(0, 10).map(sub => (
                          <tr key={sub.id} className="border-b border-purple-500/10 text-purple-300">
                            <td className="py-2 px-2">{sub.username}</td>
                            <td className="py-2 px-2 text-green-400">${sub.amount_paid?.toFixed(2)}</td>
                            <td className="py-2 px-2 text-purple-400/60">{new Date(sub.started_at).toLocaleDateString()}</td>
                            <td className="py-2 px-2">
                              <span className={`px-2 py-0.5 rounded text-xs ${sub.status === 'active' ? 'bg-green-500/20 text-green-400' : 'bg-red-500/20 text-red-400'}`}>
                                {sub.status}
                              </span>
                            </td>
                          </tr>
                        ))}
                      </tbody>
                    </table>
                  </div>
                </div>
              )}
            </FuturisticFrame>
          </div>
        )}

        {/* Privacy Policy Tab */}
        {activeTab === "privacy" && (
          <FuturisticFrame title="EDIT PRIVACY POLICY" color="pink" className="bg-slate-900/80 border border-pink-500/30 rounded-lg">
            {loading ? (
              <div className="flex justify-center py-8"><Loader2 className="w-8 h-8 text-pink-400 animate-spin" /></div>
            ) : (
              <div className="space-y-4">
                <p className="text-purple-400/60 font-mono text-sm">Edit the Privacy Policy below. Supports Markdown formatting.</p>
                <textarea
                  value={privacyPolicy}
                  onChange={(e) => setPrivacyPolicy(e.target.value)}
                  className="w-full h-96 px-4 py-3 bg-slate-950 border border-purple-500/30 rounded-lg text-purple-300 font-mono text-sm focus:border-pink-500 focus:outline-none resize-y"
                  placeholder="Enter Privacy Policy content..."
                  data-testid="privacy-policy-editor"
                />
                <div className="flex justify-between items-center">
                  <a href="/privacy-policy" target="_blank" className="text-purple-400 hover:text-pink-400 font-mono text-sm flex items-center gap-1">
                    <ExternalLink className="w-4 h-4" /> Preview
                  </a>
                  <button
                    onClick={savePrivacyPolicy}
                    disabled={saving}
                    className="px-6 py-2 bg-gradient-to-r from-pink-600 to-purple-600 text-white font-mono rounded hover:scale-[1.02] disabled:opacity-50 flex items-center gap-2"
                    data-testid="save-privacy-policy"
                  >
                    {saving ? <Loader2 className="w-4 h-4 animate-spin" /> : <Check className="w-4 h-4" />}
                    SAVE CHANGES
                  </button>
                </div>
              </div>
            )}
          </FuturisticFrame>
        )}

        {/* Terms of Service Tab */}
        {activeTab === "terms" && (
          <FuturisticFrame title="EDIT TERMS OF SERVICE" color="blue" className="bg-slate-900/80 border border-blue-500/30 rounded-lg">
            {loading ? (
              <div className="flex justify-center py-8"><Loader2 className="w-8 h-8 text-blue-400 animate-spin" /></div>
            ) : (
              <div className="space-y-4">
                <p className="text-purple-400/60 font-mono text-sm">Edit the Terms of Service below. Supports Markdown formatting.</p>
                <textarea
                  value={termsOfService}
                  onChange={(e) => setTermsOfService(e.target.value)}
                  className="w-full h-96 px-4 py-3 bg-slate-950 border border-purple-500/30 rounded-lg text-purple-300 font-mono text-sm focus:border-blue-500 focus:outline-none resize-y"
                  placeholder="Enter Terms of Service content..."
                  data-testid="terms-of-service-editor"
                />
                <div className="flex justify-between items-center">
                  <a href="/terms-of-service" target="_blank" className="text-purple-400 hover:text-blue-400 font-mono text-sm flex items-center gap-1">
                    <ExternalLink className="w-4 h-4" /> Preview
                  </a>
                  <button
                    onClick={saveTermsOfService}
                    disabled={saving}
                    className="px-6 py-2 bg-gradient-to-r from-blue-600 to-purple-600 text-white font-mono rounded hover:scale-[1.02] disabled:opacity-50 flex items-center gap-2"
                    data-testid="save-terms-of-service"
                  >
                    {saving ? <Loader2 className="w-4 h-4 animate-spin" /> : <Check className="w-4 h-4" />}
                    SAVE CHANGES
                  </button>
                </div>
              </div>
            )}
          </FuturisticFrame>
        )}
      </div>
    </Layout>
  );
};

// Privacy Policy Page (Public)
const PrivacyPolicyPage = () => {
  const [content, setContent] = useState("");
  const [lastUpdated, setLastUpdated] = useState("");
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    fetchPolicy();
  }, []);

  const fetchPolicy = async () => {
    try {
      const res = await axios.get(`${API}/legal/privacy-policy`);
      setContent(res.data.content);
      setLastUpdated(res.data.last_updated);
    } catch (error) {
      setContent("Failed to load Privacy Policy. Please try again later.");
    } finally {
      setLoading(false);
    }
  };

  return (
    <div className="min-h-screen bg-gradient-to-br from-slate-950 via-purple-950/30 to-slate-950">
      <div className="max-w-4xl mx-auto px-4 py-12">
        <div className="mb-8">
          <a href="/" className="text-pink-400 hover:text-pink-300 font-mono text-sm flex items-center gap-2 mb-4">
            <Home className="w-4 h-4" /> Back to Home
          </a>
          <h1 className="text-4xl font-bold text-transparent bg-clip-text bg-gradient-to-r from-pink-400 to-purple-400 font-mono tracking-wider">PRIVACY POLICY</h1>
          <p className="text-purple-400/60 font-mono text-sm mt-2">Last Updated: {lastUpdated}</p>
        </div>
        
        {loading ? (
          <div className="flex justify-center py-12">
            <Loader2 className="w-8 h-8 text-pink-400 animate-spin" />
          </div>
        ) : (
          <div className="bg-slate-900/80 border border-purple-500/30 rounded-lg p-6 md:p-8">
            <div className="prose prose-invert prose-pink max-w-none font-mono text-purple-300/90 whitespace-pre-wrap">
              {content}
            </div>
          </div>
        )}
        
        <div className="mt-8 text-center">
          <p className="text-purple-400/40 font-mono text-xs">InfoPilot Explorer © 2026</p>
        </div>
      </div>
    </div>
  );
};

// Terms of Service Page (Public)
const TermsOfServicePage = () => {
  const [content, setContent] = useState("");
  const [lastUpdated, setLastUpdated] = useState("");
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    fetchTerms();
  }, []);

  const fetchTerms = async () => {
    try {
      const res = await axios.get(`${API}/legal/terms-of-service`);
      setContent(res.data.content);
      setLastUpdated(res.data.last_updated);
    } catch (error) {
      setContent("Failed to load Terms of Service. Please try again later.");
    } finally {
      setLoading(false);
    }
  };

  return (
    <div className="min-h-screen bg-gradient-to-br from-slate-950 via-purple-950/30 to-slate-950">
      <div className="max-w-4xl mx-auto px-4 py-12">
        <div className="mb-8">
          <a href="/" className="text-pink-400 hover:text-pink-300 font-mono text-sm flex items-center gap-2 mb-4">
            <Home className="w-4 h-4" /> Back to Home
          </a>
          <h1 className="text-4xl font-bold text-transparent bg-clip-text bg-gradient-to-r from-blue-400 to-purple-400 font-mono tracking-wider">TERMS OF SERVICE</h1>
          <p className="text-purple-400/60 font-mono text-sm mt-2">Last Updated: {lastUpdated}</p>
        </div>
        
        {loading ? (
          <div className="flex justify-center py-12">
            <Loader2 className="w-8 h-8 text-blue-400 animate-spin" />
          </div>
        ) : (
          <div className="bg-slate-900/80 border border-purple-500/30 rounded-lg p-6 md:p-8">
            <div className="prose prose-invert prose-blue max-w-none font-mono text-purple-300/90 whitespace-pre-wrap">
              {content}
            </div>
          </div>
        )}
        
        <div className="mt-8 text-center">
          <p className="text-purple-400/40 font-mono text-xs">InfoPilot Explorer © 2026</p>
        </div>
      </div>
    </div>
  );
};

// Main App
function App() {
  const appContent = (
    <AuthProvider>
      <Toaster position="top-right" toastOptions={{ style: { background: '#0f172a', border: '1px solid #ec4899', color: '#c084fc', fontFamily: 'monospace' } }} />
      <BrowserRouter>
        <BadgeNotificationProvider>
          <Routes>
            <Route path="/login" element={<LoginPage />} />
            <Route path="/privacy-policy" element={<PrivacyPolicyPage />} />
            <Route path="/terms-of-service" element={<TermsOfServicePage />} />
            <Route path="/" element={<ProtectedRoute><HomePage /></ProtectedRoute>} />
            <Route path="/infopilot" element={<ProtectedRoute><InfoPilotPage /></ProtectedRoute>} />
            <Route path="/ultimate-search" element={<ProtectedRoute><UltimateSearchPage /></ProtectedRoute>} />
            <Route path="/categories" element={<ProtectedRoute><CategoriesPage /></ProtectedRoute>} />
            <Route path="/marketplace" element={<ProtectedRoute><MarketplacePage /></ProtectedRoute>} />
            <Route path="/messages" element={<ProtectedRoute><MessagesPage /></ProtectedRoute>} />
            <Route path="/friends" element={<ProtectedRoute><FriendsPage /></ProtectedRoute>} />
            <Route path="/groups" element={<ProtectedRoute><GroupsPage /></ProtectedRoute>} />
            <Route path="/groups/:groupId" element={<ProtectedRoute><GroupDetailPage /></ProtectedRoute>} />
            <Route path="/pages" element={<ProtectedRoute><PagesPage /></ProtectedRoute>} />
            <Route path="/pages/:pageId" element={<ProtectedRoute><PageDetailPage /></ProtectedRoute>} />
            <Route path="/statistics" element={<ProtectedRoute><StatisticsPage /></ProtectedRoute>} />
            <Route path="/global-database" element={<ProtectedRoute><GlobalDatabasePage /></ProtectedRoute>} />
            <Route path="/book" element={<ProtectedRoute><BookPage /></ProtectedRoute>} />
            <Route path="/subscribe" element={<ProtectedRoute><SubscribePage /></ProtectedRoute>} />
            <Route path="/admin" element={<ProtectedRoute><AdminPage /></ProtectedRoute>} />
            <Route path="*" element={<Navigate to="/" />} />
          </Routes>
        </BadgeNotificationProvider>
      </BrowserRouter>
    </AuthProvider>
  );

  // Wrap with GoogleOAuthProvider only if client ID is available
  if (GOOGLE_CLIENT_ID) {
    return <GoogleOAuthProvider clientId={GOOGLE_CLIENT_ID}>{appContent}</GoogleOAuthProvider>;
  }
  
  return appContent;
}

export default App;
