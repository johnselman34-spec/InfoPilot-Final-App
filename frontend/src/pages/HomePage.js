/**
 * InfoPilot Explorer - Home Page
 */
import React from 'react';
import { Link } from 'react-router-dom';
import { useQuery } from '@tanstack/react-query';
import axios from 'axios';
import { 
  Sparkles, Search, Map, Store, MessageCircle, FileText, Trophy, Star,
  Book, Utensils, ChevronRight, Users, BarChart3, Newspaper
} from 'lucide-react';
import { useAuth } from '../context/AuthContext';
import { API, PAYPAL_INFOPILOT_LINK, AMAZON_BOOK_LINK } from '../utils/api';
import StarsBackground from '../components/StarsBackground';
import { Card, CardHeader, CardTitle, CardDescription, CardContent } from '../components/ui/card';
import { Button } from '../components/ui/button';
import { Badge } from '../components/ui/badge';

const HomePage = () => {
  const { user } = useAuth();

  const { data: statsData } = useQuery({
    queryKey: ["stats"],
    queryFn: () => axios.get(`${API}/stats`).then(r => r.data)
  });

  const { data: leaderboardData } = useQuery({
    queryKey: ["leaderboard"],
    queryFn: () => axios.get(`${API}/users/leaderboard`).then(r => r.data)
  });

  const features = [
    { icon: <Search size={32} />, title: "Ultimate Search", desc: "Create custom search protocols", link: "/search", color: "text-yellow-400" },
    { icon: <Map size={32} />, title: "Interactive Map", desc: "Visualize results geographically", link: "/map", color: "text-blue-400" },
    { icon: <Store size={32} />, title: "Marketplace", desc: "Buy & sell search protocols", link: "/marketplace", color: "text-green-400" },
    { icon: <MessageCircle size={32} />, title: "Chat & Groups", desc: "Connect with other pilots", link: "/chat", color: "text-purple-400" },
    { icon: <FileText size={32} />, title: "Personal Reports", desc: "Create organic content", link: "/reports", color: "text-pink-400" },
    { icon: <BarChart3 size={32} />, title: "Statistics", desc: "Track your progress", link: "/stats", color: "text-cyan-400" }
  ];

  return (
    <div className="min-h-screen pt-20 px-4">
      <StarsBackground />
      
      {/* Hero Section */}
      <div className="max-w-6xl mx-auto text-center py-12">
        <Badge className="mb-2 bg-blue-600/30 text-blue-300 border-blue-500/30 px-4 py-1">
          Worldwide Information Exchange Database
        </Badge>
        <Badge className="mb-4 bg-yellow-400/20 text-yellow-400 border-yellow-400/30 text-sm px-4 py-1 ml-2">
          🎉 First in Flight with Monetization of Searches! It&apos;s a Bear! 🐻
        </Badge>
        
        <h1 className="text-5xl md:text-6xl font-bold text-gradient-gold text-shadow-glow mb-4">
          InfoPilot Explorer
        </h1>
        <p className="text-white/60 text-lg max-w-2xl mx-auto mb-8">
          Create powerful Boolean search protocols, categorize web content, and monetize your expertise in the world&apos;s first search protocol marketplace.
        </p>
        
        {!user ? (
          <div className="flex gap-4 justify-center">
            <Link to="/login">
              <Button className="btn-gold text-lg px-8 py-6" data-testid="get-started-btn">
                <Sparkles className="mr-2" /> Get Started Free
              </Button>
            </Link>
            <a href={PAYPAL_INFOPILOT_LINK} target="_blank" rel="noopener noreferrer">
              <Button className="bg-green-600 hover:bg-green-500 text-lg px-8 py-6">
                <Star className="mr-2" /> Subscribe $1/mo
              </Button>
            </a>
          </div>
        ) : (
          <Link to="/search">
            <Button className="btn-gold text-lg px-8 py-6" data-testid="go-to-search-btn">
              <Search className="mr-2" /> Go to Ultimate Search
            </Button>
          </Link>
        )}

        <p className="text-white/60 text-sm mt-4">
          Top Pilot Enterprises, Inc. - It&apos;s a Bear! 🐻
        </p>
      </div>

      {/* Features Grid */}
      <div className="max-w-6xl mx-auto mb-16">
        <h2 className="text-2xl font-bold text-white text-center mb-8">Explore Features</h2>
        <div className="grid md:grid-cols-2 lg:grid-cols-3 gap-6">
          {features.map((f, i) => (
            <Link key={i} to={user ? f.link : "/login"}>
              <Card className="card-glass p-6 hover:border-yellow-400/50 hover:scale-105 transition-all cursor-pointer h-full">
                <div className={`${f.color} mb-4`}>{f.icon}</div>
                <h3 className="text-xl font-bold text-white mb-2">{f.title}</h3>
                <p className="text-white/60">{f.desc}</p>
              </Card>
            </Link>
          ))}
        </div>
      </div>

      {/* Stats & Leaderboard */}
      <div className="max-w-6xl mx-auto grid md:grid-cols-2 gap-8 mb-16">
        {/* Platform Stats */}
        <Card className="card-glass p-6">
          <h3 className="text-xl font-bold text-yellow-400 mb-4 flex items-center gap-2">
            <BarChart3 /> Platform Stats
          </h3>
          <div className="grid grid-cols-2 gap-4">
            <div className="text-center p-4 bg-white/5 rounded-lg">
              <p className="text-3xl font-bold text-white">{statsData?.global?.total_users || 0}</p>
              <p className="text-white/60 text-sm">Pilots</p>
            </div>
            <div className="text-center p-4 bg-white/5 rounded-lg">
              <p className="text-3xl font-bold text-white">{statsData?.global?.total_categories || 0}</p>
              <p className="text-white/60 text-sm">Protocols</p>
            </div>
            <div className="text-center p-4 bg-white/5 rounded-lg">
              <p className="text-3xl font-bold text-white">{statsData?.global?.total_results || 0}</p>
              <p className="text-white/60 text-sm">Results</p>
            </div>
            <div className="text-center p-4 bg-white/5 rounded-lg">
              <p className="text-3xl font-bold text-white">{statsData?.global?.total_reports || 0}</p>
              <p className="text-white/60 text-sm">Reports</p>
            </div>
          </div>
        </Card>

        {/* Leaderboard */}
        <Card className="card-glass p-6">
          <h3 className="text-xl font-bold text-yellow-400 mb-4 flex items-center gap-2">
            <Trophy /> Laughter Leaderboard
          </h3>
          <div className="space-y-2">
            {leaderboardData?.leaderboard?.slice(0, 5).map((u, i) => (
              <div key={i} className="flex items-center justify-between p-3 bg-white/5 rounded-lg">
                <div className="flex items-center gap-3">
                  <span className="text-xl">{i === 0 ? '🥇' : i === 1 ? '🥈' : i === 2 ? '🥉' : `${i + 1}.`}</span>
                  <span className="text-white">{u.username}</span>
                </div>
                <Badge className="bg-yellow-400/20 text-yellow-400">😂 {u.laughter_points}</Badge>
              </div>
            ))}
            {!leaderboardData?.leaderboard?.length && (
              <p className="text-white/60 text-center py-4">No pilots yet! Be the first!</p>
            )}
          </div>
        </Card>
      </div>

      {/* Book & Food Promo */}
      <div className="max-w-6xl mx-auto grid md:grid-cols-2 gap-8 mb-16">
        <Card className="card-glass p-6 border-purple-400/30">
          <div className="flex items-start gap-4">
            <Book className="text-purple-400 flex-shrink-0" size={40} />
            <div>
              <h3 className="text-xl font-bold text-white mb-2">Letters to Evelyn</h3>
              <p className="text-white/60 text-sm mb-3">A True Supernatural Thriller Comedy by John Selman</p>
              <div className="flex gap-2">
                <a href={AMAZON_BOOK_LINK} target="_blank" rel="noopener noreferrer">
                  <Button size="sm" className="bg-orange-500 hover:bg-orange-400">Amazon</Button>
                </a>
                <Link to="/book">
                  <Button size="sm" variant="outline" className="text-purple-400 border-purple-400/30">
                    Learn More <ChevronRight size={16} />
                  </Button>
                </Link>
              </div>
            </div>
          </div>
        </Card>

        <Card className="card-glass p-6 border-green-400/30">
          <div className="flex items-start gap-4">
            <Utensils className="text-green-400 flex-shrink-0" size={40} />
            <div>
              <h3 className="text-xl font-bold text-white mb-2">Maestro Bistro</h3>
              <p className="text-white/60 text-sm mb-3">German Food Truck in Brunswick, Maine</p>
              <Link to="/food">
                <Button size="sm" className="bg-green-600 hover:bg-green-500">
                  View Menu <ChevronRight size={16} />
                </Button>
              </Link>
            </div>
          </div>
        </Card>
      </div>
    </div>
  );
};

export default HomePage;
