import React from 'react';
import { Navigate, Link } from 'react-router-dom';
import { useQuery } from '@tanstack/react-query';
import axios from 'axios';
import { useAuth } from '../context/AuthContext';
import StarsBackground from '../components/StarsBackground';
import { Card, CardContent, CardHeader, CardTitle, CardDescription } from '../components/ui/card';
import { Button } from '../components/ui/button';
import { Badge } from '../components/ui/badge';
import { 
  Shield,
  Server,
  Database,
  Search,
  Mail,
  CreditCard,
  Zap,
  Users,
  ShoppingBag,
  FileText,
  MessageSquare,
  RefreshCw,
  CheckCircle,
  XCircle,
  AlertTriangle,
  Activity,
  Globe,
  Filter,
  HardDrive
} from 'lucide-react';
import { API } from '../utils/api';

const AdminDashboard = () => {
  const { user } = useAuth();

  // Fetch system status
  const { data: systemStatus, isLoading, error, refetch } = useQuery({
    queryKey: ['admin-system-status'],
    queryFn: () => axios.get(`${API}/admin/system-status`).then(r => r.data),
    refetchInterval: 60000, // Refresh every minute
    retry: 1
  });

  // Fetch recent activity
  const { data: activity } = useQuery({
    queryKey: ['admin-recent-activity'],
    queryFn: () => axios.get(`${API}/admin/recent-activity`).then(r => r.data),
    refetchInterval: 30000
  });

  // Redirect if not admin
  if (!user) return <Navigate to="/login" />;
  if (!user.is_admin) return <Navigate to="/" />;

  const StatusBadge = ({ status, text }) => {
    const variants = {
      operational: { bg: 'bg-green-500/20', text: 'text-green-300', icon: CheckCircle },
      healthy: { bg: 'bg-green-500/20', text: 'text-green-300', icon: CheckCircle },
      connected: { bg: 'bg-green-500/20', text: 'text-green-300', icon: CheckCircle },
      configured: { bg: 'bg-green-500/20', text: 'text-green-300', icon: CheckCircle },
      not_configured: { bg: 'bg-yellow-500/20', text: 'text-yellow-300', icon: AlertTriangle },
      blocked: { bg: 'bg-red-500/20', text: 'text-red-300', icon: XCircle },
      error: { bg: 'bg-red-500/20', text: 'text-red-300', icon: XCircle },
      test: { bg: 'bg-blue-500/20', text: 'text-blue-300', icon: Activity },
      live: { bg: 'bg-green-500/20', text: 'text-green-300', icon: Zap }
    };
    
    const variant = variants[status] || variants.error;
    const Icon = variant.icon;
    
    return (
      <Badge className={`${variant.bg} ${variant.text} flex items-center gap-1`}>
        <Icon size={12} />
        {text || status}
      </Badge>
    );
  };

  return (
    <div className="min-h-screen pt-20 px-4 pb-12">
      <StarsBackground />
      <div className="max-w-7xl mx-auto">
        {/* Header */}
        <div className="flex items-center justify-between mb-8">
          <div>
            <div className="flex items-center gap-3 mb-2">
              <Shield className="text-yellow-400" size={32} />
              <h1 className="text-3xl font-bold text-gradient-gold" data-testid="admin-dashboard-title">
                Admin Dashboard
              </h1>
            </div>
            <p className="text-white/60">System status and platform management</p>
          </div>
          <Button onClick={() => refetch()} variant="outline" className="flex items-center gap-2">
            <RefreshCw size={16} className={isLoading ? 'animate-spin' : ''} />
            Refresh
          </Button>
        </div>

        {isLoading ? (
          <div className="text-center py-12">
            <RefreshCw className="w-12 h-12 text-yellow-400 animate-spin mx-auto mb-4" />
            <p className="text-white/60">Loading system status...</p>
          </div>
        ) : error ? (
          <Card className="card-glass p-8 text-center">
            <XCircle className="w-16 h-16 text-red-400 mx-auto mb-4" />
            <h3 className="text-xl text-white mb-2">Error Loading Status</h3>
            <p className="text-white/60 mb-4">{error.response?.data?.detail || 'Failed to fetch system status'}</p>
            <Button onClick={() => refetch()} className="btn-gold">
              <RefreshCw className="mr-2" size={16} /> Retry
            </Button>
          </Card>
        ) : (
          <div className="space-y-6">
            {/* Overall Status Banner */}
            <Card className="card-glass border-green-400/30 p-4" data-testid="overall-status">
              <div className="flex items-center justify-between">
                <div className="flex items-center gap-4">
                  <div className="w-12 h-12 rounded-full bg-green-500/20 flex items-center justify-center">
                    <Activity className="text-green-400" size={24} />
                  </div>
                  <div>
                    <h2 className="text-xl font-bold text-white">System Status</h2>
                    <p className="text-white/50 text-sm">
                      Last updated: {new Date(systemStatus?.timestamp).toLocaleString()}
                    </p>
                  </div>
                </div>
                <StatusBadge status={systemStatus?.overall_status} text="All Systems Operational" />
              </div>
            </Card>

            {/* Services Grid */}
            <div className="grid md:grid-cols-2 lg:grid-cols-3 gap-4">
              {/* Database Status */}
              <Card className="card-glass" data-testid="database-status">
                <CardHeader className="pb-2">
                  <CardTitle className="text-white flex items-center gap-2 text-lg">
                    <Database className="text-blue-400" size={20} />
                    Database
                  </CardTitle>
                </CardHeader>
                <CardContent>
                  <div className="flex items-center justify-between mb-2">
                    <span className="text-white/70">MongoDB</span>
                    <StatusBadge 
                      status={systemStatus?.services?.database?.connected ? 'connected' : 'error'} 
                      text={systemStatus?.services?.database?.connected ? 'Connected' : 'Error'}
                    />
                  </div>
                  <p className="text-white/50 text-sm">
                    DB: {systemStatus?.services?.database?.name}
                  </p>
                </CardContent>
              </Card>

              {/* Search Engines Status */}
              <Card className="card-glass" data-testid="search-engines-status">
                <CardHeader className="pb-2">
                  <CardTitle className="text-white flex items-center gap-2 text-lg">
                    <Search className="text-purple-400" size={20} />
                    Search Engines
                  </CardTitle>
                </CardHeader>
                <CardContent className="space-y-2">
                  {systemStatus?.services?.search_engines?.map(engine => (
                    <div key={engine.id} className="flex items-center justify-between">
                      <span className="text-white/70 flex items-center gap-2">
                        {engine.id === 'duckduckgo' ? '🦆' : '🦁'} {engine.name}
                      </span>
                      <StatusBadge status={engine.status} />
                    </div>
                  ))}
                </CardContent>
              </Card>

              {/* Elasticsearch Status */}
              <Card className="card-glass" data-testid="elasticsearch-status">
                <CardHeader className="pb-2">
                  <CardTitle className="text-white flex items-center gap-2 text-lg">
                    <Globe className="text-cyan-400" size={20} />
                    Elasticsearch
                  </CardTitle>
                </CardHeader>
                <CardContent>
                  <div className="flex items-center justify-between mb-2">
                    <span className="text-white/70">Semantic Search</span>
                    <StatusBadge 
                      status={systemStatus?.services?.elasticsearch?.connected ? 'connected' : 'not_configured'} 
                      text={systemStatus?.services?.elasticsearch?.connected ? 'Connected' : 'Not Connected'}
                    />
                  </div>
                  {systemStatus?.services?.elasticsearch?.connected && (
                    <p className="text-white/50 text-sm">
                      v{systemStatus?.services?.elasticsearch?.version} • {systemStatus?.services?.elasticsearch?.cluster_name?.slice(0, 8)}...
                    </p>
                  )}
                </CardContent>
              </Card>

              {/* Email Status */}
              <Card className="card-glass" data-testid="email-status">
                <CardHeader className="pb-2">
                  <CardTitle className="text-white flex items-center gap-2 text-lg">
                    <Mail className="text-pink-400" size={20} />
                    Email Service
                  </CardTitle>
                </CardHeader>
                <CardContent>
                  <div className="flex items-center justify-between mb-2">
                    <span className="text-white/70">{systemStatus?.services?.email?.provider}</span>
                    <StatusBadge 
                      status={systemStatus?.services?.email?.configured ? 'configured' : 'not_configured'} 
                    />
                  </div>
                  <p className="text-white/50 text-sm truncate">
                    From: {systemStatus?.services?.email?.sender_email}
                  </p>
                </CardContent>
              </Card>

              {/* Payment Status */}
              <Card className="card-glass" data-testid="payment-status">
                <CardHeader className="pb-2">
                  <CardTitle className="text-white flex items-center gap-2 text-lg">
                    <CreditCard className="text-green-400" size={20} />
                    Payments
                  </CardTitle>
                </CardHeader>
                <CardContent className="space-y-2">
                  <div className="flex items-center justify-between">
                    <span className="text-white/70">Stripe (Primary)</span>
                    <StatusBadge 
                      status={systemStatus?.services?.payments?.primary?.mode} 
                      text={systemStatus?.services?.payments?.primary?.mode === 'test' ? 'Test Mode' : 
                            systemStatus?.services?.payments?.primary?.mode === 'live' ? 'Live' : 'Not Set'}
                    />
                  </div>
                  <div className="flex items-center justify-between">
                    <span className="text-white/50 text-sm">PayPal (Backup)</span>
                    <StatusBadge status={systemStatus?.services?.payments?.secondary?.status} />
                  </div>
                </CardContent>
              </Card>

              {/* Paywall Filter */}
              <Card className="card-glass" data-testid="paywall-status">
                <CardHeader className="pb-2">
                  <CardTitle className="text-white flex items-center gap-2 text-lg">
                    <Filter className="text-orange-400" size={20} />
                    Paywall Filter
                  </CardTitle>
                </CardHeader>
                <CardContent>
                  <div className="flex items-center justify-between mb-2">
                    <span className="text-white/70">Content Filter</span>
                    <StatusBadge 
                      status={systemStatus?.services?.paywall_filter?.enabled ? 'operational' : 'not_configured'} 
                      text={systemStatus?.services?.paywall_filter?.enabled ? 'Active' : 'Disabled'}
                    />
                  </div>
                  <p className="text-white/50 text-sm">
                    {systemStatus?.services?.paywall_filter?.blocked_domains || 0} domains blocked
                  </p>
                </CardContent>
              </Card>

              {/* Cache Status */}
              <Card className="card-glass" data-testid="cache-status">
                <CardHeader className="pb-2">
                  <CardTitle className="text-white flex items-center gap-2 text-lg">
                    <HardDrive className="text-indigo-400" size={20} />
                    Cache
                  </CardTitle>
                </CardHeader>
                <CardContent>
                  <div className="flex items-center justify-between mb-2">
                    <span className="text-white/70">In-Memory Cache</span>
                    <StatusBadge 
                      status={systemStatus?.services?.cache?.enabled ? 'operational' : 'not_configured'} 
                      text={systemStatus?.services?.cache?.enabled ? 'Active' : 'Disabled'}
                    />
                  </div>
                  <p className="text-white/50 text-sm">
                    {systemStatus?.services?.cache?.entries || 0} cached entries
                  </p>
                </CardContent>
              </Card>
            </div>

            {/* Platform Statistics */}
            <Card className="card-glass" data-testid="platform-stats">
              <CardHeader>
                <CardTitle className="text-white flex items-center gap-2">
                  <Server className="text-yellow-400" size={20} />
                  Platform Statistics
                </CardTitle>
                <CardDescription className="text-white/50">
                  Overall platform usage metrics
                </CardDescription>
              </CardHeader>
              <CardContent>
                <div className="grid grid-cols-2 md:grid-cols-5 gap-4">
                  <div className="text-center p-4 bg-white/5 rounded-lg">
                    <Users className="mx-auto text-blue-400 mb-2" size={24} />
                    <p className="text-2xl font-bold text-white">{systemStatus?.statistics?.total_users || 0}</p>
                    <p className="text-white/50 text-sm">Users</p>
                  </div>
                  <div className="text-center p-4 bg-white/5 rounded-lg">
                    <FileText className="mx-auto text-purple-400 mb-2" size={24} />
                    <p className="text-2xl font-bold text-white">{systemStatus?.statistics?.total_categories || 0}</p>
                    <p className="text-white/50 text-sm">Categories</p>
                  </div>
                  <div className="text-center p-4 bg-white/5 rounded-lg">
                    <ShoppingBag className="mx-auto text-green-400 mb-2" size={24} />
                    <p className="text-2xl font-bold text-white">{systemStatus?.statistics?.public_protocols || 0}</p>
                    <p className="text-white/50 text-sm">Protocols for Sale</p>
                  </div>
                  <div className="text-center p-4 bg-white/5 rounded-lg">
                    <Search className="mx-auto text-orange-400 mb-2" size={24} />
                    <p className="text-2xl font-bold text-white">{systemStatus?.statistics?.total_search_results || 0}</p>
                    <p className="text-white/50 text-sm">Search Results</p>
                  </div>
                  <div className="text-center p-4 bg-white/5 rounded-lg">
                    <CreditCard className="mx-auto text-pink-400 mb-2" size={24} />
                    <p className="text-2xl font-bold text-white">{systemStatus?.statistics?.total_purchases || 0}</p>
                    <p className="text-white/50 text-sm">Purchases</p>
                  </div>
                </div>
              </CardContent>
            </Card>

            {/* Recent Activity */}
            {activity && (
              <div className="grid md:grid-cols-2 gap-6">
                {/* Recent Users */}
                <Card className="card-glass" data-testid="recent-users">
                  <CardHeader>
                    <CardTitle className="text-white flex items-center gap-2">
                      <Users className="text-blue-400" size={20} />
                      Recent Users
                    </CardTitle>
                  </CardHeader>
                  <CardContent>
                    {activity.recent_users?.length > 0 ? (
                      <div className="space-y-2">
                        {activity.recent_users.map((u, idx) => (
                          <div key={u.id || idx} className="flex items-center justify-between p-2 bg-white/5 rounded">
                            <div>
                              <p className="text-white text-sm">{u.username}</p>
                              <p className="text-white/50 text-xs">{u.email}</p>
                            </div>
                            {u.is_paid && <Badge className="bg-green-500/20 text-green-300">Paid</Badge>}
                          </div>
                        ))}
                      </div>
                    ) : (
                      <p className="text-white/50 text-center py-4">No recent users</p>
                    )}
                  </CardContent>
                </Card>

                {/* Recent Purchases */}
                <Card className="card-glass" data-testid="recent-purchases">
                  <CardHeader>
                    <CardTitle className="text-white flex items-center gap-2">
                      <ShoppingBag className="text-green-400" size={20} />
                      Recent Purchases
                    </CardTitle>
                  </CardHeader>
                  <CardContent>
                    {activity.recent_purchases?.length > 0 ? (
                      <div className="space-y-2">
                        {activity.recent_purchases.map((p, idx) => (
                          <div key={p.id || idx} className="flex items-center justify-between p-2 bg-white/5 rounded">
                            <div>
                              <p className="text-white text-sm">{p.protocol_name || 'Protocol'}</p>
                              <p className="text-white/50 text-xs">
                                {p.created_at ? new Date(p.created_at).toLocaleDateString() : 'Recent'}
                              </p>
                            </div>
                            <Badge className="bg-green-500/20 text-green-300">
                              ${p.amount?.toFixed(2)}
                            </Badge>
                          </div>
                        ))}
                      </div>
                    ) : (
                      <p className="text-white/50 text-center py-4">No recent purchases</p>
                    )}
                    <div className="mt-4 p-3 bg-blue-500/10 rounded-lg border border-blue-400/20">
                      <div className="flex items-center justify-between">
                        <div className="flex items-center gap-2">
                          <MessageSquare className="text-blue-400" size={16} />
                          <span className="text-white/70 text-sm">Chat Messages (24h)</span>
                        </div>
                        <span className="text-blue-300 font-bold">{activity.chat_messages_24h || 0}</span>
                      </div>
                    </div>
                  </CardContent>
                </Card>
              </div>
            )}

            {/* Quick Links */}
            <Card className="card-glass p-4">
              <div className="flex flex-wrap gap-3">
                <Link to="/marketplace">
                  <Button variant="outline" className="flex items-center gap-2">
                    <ShoppingBag size={16} /> Marketplace
                  </Button>
                </Link>
                <Link to="/stats">
                  <Button variant="outline" className="flex items-center gap-2">
                    <Activity size={16} /> Stats
                  </Button>
                </Link>
                <Link to="/revenue">
                  <Button variant="outline" className="flex items-center gap-2">
                    <CreditCard size={16} /> Revenue
                  </Button>
                </Link>
                <Link to="/chat">
                  <Button variant="outline" className="flex items-center gap-2">
                    <MessageSquare size={16} /> Chat
                  </Button>
                </Link>
              </div>
            </Card>
          </div>
        )}
      </div>
    </div>
  );
};

export default AdminDashboard;
