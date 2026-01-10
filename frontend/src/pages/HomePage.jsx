/**
 * Home/Dashboard Page Component
 */
import React, { useState, useEffect } from 'react';
import { useNavigate } from 'react-router-dom';
import axios from 'axios';
import { 
  Radar, Target, FolderTree, ShoppingCart, MessageCircle, 
  Users, Globe, Book, Shield, Loader2, Star, ExternalLink,
  TrendingUp, Award, Activity
} from 'lucide-react';
import { useAuth } from '../contexts/AuthContext';
import { Layout } from '../components/layout';
import { API, BOOK_INFO, IMAGES } from '../utils/constants';

const HomePage = () => {
  const navigate = useNavigate();
  const { user } = useAuth();
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
      console.error("Error fetching stats:", error);
    } finally {
      setLoading(false);
    }
  };

  const quickActions = [
    { path: "/infopilot", icon: Radar, label: "INFOPILOT SEARCH", color: "from-pink-600 to-purple-600", desc: "AI-powered research" },
    { path: "/ultimate-search", icon: Target, label: "ULTIMATE SEARCH", color: "from-purple-600 to-blue-600", desc: "Advanced filtering" },
    { path: "/categories", icon: FolderTree, label: "MY PROTOCOLS", color: "from-blue-600 to-cyan-600", desc: "Manage categories" },
    { path: "/marketplace", icon: ShoppingCart, label: "MARKETPLACE", color: "from-cyan-600 to-teal-600", desc: "Buy & sell protocols" },
    { path: "/messages", icon: MessageCircle, label: "MESSAGES", color: "from-teal-600 to-green-600", desc: "Private messaging" },
    { path: "/global-database", icon: Globe, label: "GLOBAL DATABASE", color: "from-green-600 to-emerald-600", desc: "Worldwide research" },
  ];

  return (
    <Layout>
      <div className="max-w-7xl mx-auto space-y-8">
        {/* Welcome Banner */}
        <div className="bg-gradient-to-r from-pink-600/20 via-purple-600/20 to-blue-600/20 border border-purple-500/30 rounded-xl p-8">
          <div className="flex flex-col md:flex-row items-center justify-between gap-6">
            <div>
              <h1 className="text-3xl md:text-4xl font-bold text-transparent bg-clip-text bg-gradient-to-r from-pink-400 via-purple-400 to-blue-400 font-mono tracking-wider">
                WELCOME, {user?.username?.toUpperCase()}
              </h1>
              <p className="text-purple-300/80 font-mono mt-2">
                Your tactical research command center is ready.
              </p>
              {user?.is_admin && (
                <span className="inline-flex items-center gap-2 mt-3 px-3 py-1 bg-pink-500/20 border border-pink-500/50 rounded text-pink-400 font-mono text-sm">
                  <Shield className="w-4 h-4" /> ADMIN ACCESS
                </span>
              )}
            </div>
            <div className="text-center">
              <div className="text-4xl font-black text-pink-400 font-mono">
                {stats?.my_protocols || 0}
              </div>
              <div className="text-sm text-purple-400/70 font-mono">YOUR PROTOCOLS</div>
            </div>
          </div>
        </div>

        {/* Quick Actions Grid */}
        <div className="grid md:grid-cols-2 lg:grid-cols-3 gap-4">
          {quickActions.map((action) => (
            <button
              key={action.path}
              onClick={() => navigate(action.path)}
              className={`group relative bg-gradient-to-br ${action.color} p-1 rounded-xl hover:scale-[1.02] transition-all`}
            >
              <div className="bg-slate-900/90 rounded-lg p-6 h-full">
                <action.icon className="w-10 h-10 text-white mb-3" />
                <h3 className="text-lg font-bold text-white font-mono">{action.label}</h3>
                <p className="text-purple-300/70 text-sm font-mono">{action.desc}</p>
              </div>
            </button>
          ))}
        </div>

        {/* Book Promotion */}
        <div className="bg-gradient-to-r from-purple-900/40 via-pink-900/40 to-blue-900/40 border border-purple-500/50 rounded-xl p-6">
          <div className="flex flex-col md:flex-row items-center gap-6">
            <img 
              src={IMAGES.bookCoverMain} 
              alt="Letters to Evelyn" 
              className="w-32 h-44 object-cover rounded-lg shadow-xl shadow-purple-500/30"
            />
            <div className="flex-1 text-center md:text-left">
              <h3 className="text-2xl font-bold text-transparent bg-clip-text bg-gradient-to-r from-pink-400 to-purple-400 font-mono">
                LETTERS TO EVELYN
              </h3>
              <p className="text-purple-300 font-mono text-sm">By John Selman • Supernatural Thriller Comedy</p>
              <div className="flex items-center justify-center md:justify-start gap-1 mt-2">
                {[...Array(5)].map((_, i) => (
                  <Star key={i} className="w-4 h-4 fill-yellow-400 text-yellow-400" />
                ))}
                <span className="text-yellow-400 font-mono text-sm ml-2">19 Five-Star Reviews</span>
              </div>
              <p className="text-purple-400/70 font-mono text-sm italic mt-2">
                "{BOOK_INFO.tagline}"
              </p>
            </div>
            <a
              href={BOOK_INFO.amazonUrl}
              target="_blank"
              rel="noopener noreferrer"
              className="px-6 py-3 bg-gradient-to-r from-yellow-500 to-orange-500 text-black font-bold font-mono rounded-lg hover:scale-105 transition-transform flex items-center gap-2"
            >
              <ExternalLink className="w-5 h-5" />
              GET ON AMAZON
            </a>
          </div>
        </div>

        {/* Stats Overview */}
        {loading ? (
          <div className="text-center py-8">
            <Loader2 className="w-8 h-8 text-pink-400 animate-spin mx-auto" />
          </div>
        ) : stats && (
          <div className="grid md:grid-cols-4 gap-4">
            {[
              { label: "Total Results", value: stats.total_results || 0, icon: Activity },
              { label: "Public Protocols", value: stats.public_protocols || 0, icon: FolderTree },
              { label: "Total Users", value: stats.total_users || 0, icon: Users },
              { label: "Trending Now", value: stats.trending_count || 0, icon: TrendingUp }
            ].map((stat, i) => (
              <div key={i} className="bg-slate-900/50 border border-purple-500/30 rounded-lg p-4 text-center">
                <stat.icon className="w-8 h-8 text-pink-400 mx-auto mb-2" />
                <div className="text-2xl font-bold text-purple-200 font-mono">{stat.value.toLocaleString()}</div>
                <div className="text-xs text-purple-400/70 font-mono">{stat.label}</div>
              </div>
            ))}
          </div>
        )}
      </div>
    </Layout>
  );
};

export default HomePage;
