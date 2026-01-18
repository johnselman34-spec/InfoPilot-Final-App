import React from 'react';
import { Navigate } from 'react-router-dom';
import { useQuery } from '@tanstack/react-query';
import axios from 'axios';
import { useAuth } from '../context/AuthContext';
import StarsBackground from '../components/StarsBackground';
import { Card } from '../components/ui/card';
import { Badge } from '../components/ui/badge';
import { Users, FileText, Search, Egg, Trophy, Star } from 'lucide-react';

const API = process.env.REACT_APP_BACKEND_URL + '/api';

const StatsPage = () => {
  const { user } = useAuth();
  const { data: stats } = useQuery({ queryKey: ["stats"], queryFn: () => axios.get(`${API}/stats`).then(r => r.data) });
  const { data: leaderboard } = useQuery({ queryKey: ["leaderboard"], queryFn: () => axios.get(`${API}/users/leaderboard`).then(r => r.data) });

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
            <h3 className="text-xl font-bold text-yellow-400 mb-4 flex items-center gap-2"><Trophy size={24} /> Top Laughter Points</h3>
            <div className="space-y-3">
              {leaderboard?.top_laughter_points?.map((u, i) => (
                <div key={u.id} className="flex items-center gap-3 p-2 bg-white/5 rounded">
                  <span className="text-2xl">{i === 0 ? '🥇' : i === 1 ? '🥈' : i === 2 ? '🥉' : `${i + 1}.`}</span>
                  <span className="flex-1 text-white">{u.username}</span>
                  <Badge className="bg-yellow-400/20 text-yellow-300">{u.laughter_points || 0} pts</Badge>
                </div>
              )) || (
                <p className="text-white/60 text-center py-4">No leaderboard data yet</p>
              )}
            </div>
          </Card>

          <Card className="card-glass p-6">
            <h3 className="text-xl font-bold text-yellow-400 mb-4 flex items-center gap-2"><Star size={24} /> Top Protocol Creators</h3>
            <div className="space-y-3">
              {leaderboard?.top_protocol_creators?.map((tc, i) => (
                <div key={tc.user?.id} className="flex items-center gap-3 p-2 bg-white/5 rounded">
                  <span className="text-2xl">{i === 0 ? '🥇' : i === 1 ? '🥈' : i === 2 ? '🥉' : `${i + 1}.`}</span>
                  <span className="flex-1 text-white">{tc.user?.username}</span>
                  <Badge className="bg-blue-400/20 text-blue-300">{tc.protocol_count} protocols</Badge>
                </div>
              )) || (
                <p className="text-white/60 text-center py-4">No protocol creators yet</p>
              )}
            </div>
          </Card>
        </div>
      </div>
    </div>
  );
};

export default StatsPage;
