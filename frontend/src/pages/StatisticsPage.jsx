/**
 * Statistics Page Component
 * Shows platform stats, popular protocols, badges, and leaderboards
 */
import React, { useState, useEffect } from 'react';
import { useNavigate } from 'react-router-dom';
import axios from 'axios';
import { toast } from 'sonner';
import {
  Loader2, Users, Globe, Copy, ShoppingCart, FileText, FolderTree,
  BarChart3, Award, DollarSign, Lock, Check, Search
} from 'lucide-react';
import {
  PieChart, Pie, Cell, BarChart, Bar, XAxis, YAxis, CartesianGrid, Tooltip,
  ResponsiveContainer
} from 'recharts';
import { useAuth } from '../contexts/AuthContext';
import { Layout } from '../components/layout/Layout';
import { FuturisticFrame } from '../components/common/FuturisticFrame';
import { WelcomeSaleBanner, BookSalesBanner } from '../components/common';
import { API } from '../utils/constants';

const StatisticsPage = () => {
  const navigate = useNavigate();
  const [stats, setStats] = useState(null);
  const [globalStats, setGlobalStats] = useState(null);
  const [popularProtocols, setPopularProtocols] = useState([]);
  const [badges, setBadges] = useState(null);
  const [badgeLeaderboard, setBadgeLeaderboard] = useState([]);
  const [loading, setLoading] = useState(true);
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
      fetchAllStats();
    } catch (error) {
      navigator.clipboard.writeText(protocol.protocol_string);
      toast.success("Protocol copied!");
    }
  };

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

              {badges.top_protocol && (
                <div className="bg-gradient-to-r from-yellow-500/10 to-orange-500/10 p-4 rounded-lg border border-yellow-500/30">
                  <p className="text-yellow-400 font-mono text-sm mb-1">🌟 YOUR TOP PROTOCOL</p>
                  <p className="text-white font-mono font-bold">{badges.top_protocol.name}</p>
                  <p className="text-purple-400/60 font-mono text-xs">{badges.top_protocol.copy_count} copies</p>
                </div>
              )}

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

export default StatisticsPage;
