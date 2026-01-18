import React, { useState } from 'react';
import { Navigate, Link } from 'react-router-dom';
import { useQuery, useMutation, useQueryClient } from '@tanstack/react-query';
import axios from 'axios';
import { useAuth } from '../context/AuthContext';
import { useToast } from '../context/ToastContext';
import StarsBackground from '../components/StarsBackground';
import { Card, CardContent, CardFooter, CardHeader, CardTitle, CardDescription } from '../components/ui/card';
import { Button } from '../components/ui/button';
import { Badge } from '../components/ui/badge';
import { Dialog, DialogContent, DialogDescription, DialogFooter, DialogHeader, DialogTitle } from '../components/ui/dialog';
import { 
  CreditCard, 
  Calendar, 
  CheckCircle, 
  XCircle, 
  AlertTriangle,
  Clock,
  DollarSign,
  ArrowUpCircle,
  RefreshCw,
  History,
  Wallet,
  Crown
} from 'lucide-react';
import { API } from '../utils/api';

const SubscriptionDashboard = () => {
  const { user } = useAuth();
  const showToast = useToast();
  const queryClient = useQueryClient();
  const [showCancelDialog, setShowCancelDialog] = useState(false);
  const [showUpgradeDialog, setShowUpgradeDialog] = useState(false);

  // Fetch subscription details
  const { data: subscription, isLoading: subLoading, error: subError } = useQuery({
    queryKey: ['subscription'],
    queryFn: () => axios.get(`${API}/stripe/subscription`).then(r => r.data),
    retry: 1
  });

  // Fetch billing history
  const { data: billing, isLoading: billLoading } = useQuery({
    queryKey: ['billing-history'],
    queryFn: () => axios.get(`${API}/stripe/billing-history`).then(r => r.data)
  });

  // Cancel subscription mutation
  const cancelMutation = useMutation({
    mutationFn: () => axios.post(`${API}/stripe/cancel-subscription`),
    onSuccess: (res) => {
      showToast(res.data.message, 'success');
      queryClient.invalidateQueries(['subscription']);
      setShowCancelDialog(false);
    },
    onError: (err) => showToast(err.response?.data?.detail || 'Failed to cancel', 'error')
  });

  // Reactivate subscription mutation
  const reactivateMutation = useMutation({
    mutationFn: () => axios.post(`${API}/stripe/reactivate-subscription`),
    onSuccess: (res) => {
      showToast(res.data.message, 'success');
      queryClient.invalidateQueries(['subscription']);
    },
    onError: (err) => showToast(err.response?.data?.detail || 'Failed to reactivate', 'error')
  });

  // Handle upgrade/downgrade
  const handleUpgrade = async (packageType) => {
    try {
      const response = await axios.post(`${API}/stripe/create-checkout`, {
        package_type: packageType,
        origin_url: window.location.origin
      });
      if (response.data.checkout_url) {
        window.location.href = response.data.checkout_url;
      }
    } catch (err) {
      showToast(err.response?.data?.detail || 'Failed to start checkout', 'error');
    }
    setShowUpgradeDialog(false);
  };

  if (!user) return <Navigate to="/login" />;

  const formatDate = (dateStr) => {
    if (!dateStr) return 'N/A';
    return new Date(dateStr).toLocaleDateString('en-US', {
      year: 'numeric',
      month: 'long',
      day: 'numeric'
    });
  };

  const formatCurrency = (amount) => {
    return new Intl.NumberFormat('en-US', {
      style: 'currency',
      currency: 'USD'
    }).format(amount || 0);
  };

  return (
    <div className="min-h-screen pt-20 px-4 pb-12">
      <StarsBackground />
      <div className="max-w-5xl mx-auto">
        {/* Header */}
        <div className="text-center mb-8">
          <Badge className="mb-4 bg-purple-500/20 text-purple-300">
            <Crown className="w-4 h-4 mr-1" /> Premium
          </Badge>
          <h1 className="text-3xl font-bold text-gradient-gold mb-2" data-testid="subscription-dashboard-title">
            Subscription Dashboard
          </h1>
          <p className="text-white/60">Manage your InfoPilot subscription and billing</p>
        </div>

        {subLoading ? (
          <div className="text-center py-12">
            <RefreshCw className="w-12 h-12 text-yellow-400 animate-spin mx-auto mb-4" />
            <p className="text-white/60">Loading subscription details...</p>
          </div>
        ) : subError ? (
          <Card className="card-glass p-8 text-center">
            <AlertTriangle className="w-16 h-16 text-red-400 mx-auto mb-4" />
            <h3 className="text-xl text-white mb-2">Error Loading Subscription</h3>
            <p className="text-white/60 mb-4">Please try again or contact support.</p>
            <Button onClick={() => window.location.reload()} className="btn-gold">
              <RefreshCw className="mr-2" size={16} /> Retry
            </Button>
          </Card>
        ) : (
          <div className="grid md:grid-cols-3 gap-6">
            {/* Current Plan Card */}
            <Card className="card-glass md:col-span-2 border-yellow-400/30" data-testid="current-plan-card">
              <CardHeader className="pb-2">
                <div className="flex items-center justify-between">
                  <CardTitle className="text-white flex items-center gap-2">
                    <CreditCard className="text-yellow-400" size={24} />
                    Current Plan
                  </CardTitle>
                  {subscription?.subscription_active && (
                    <Badge className={subscription?.subscription_cancelled ? "bg-orange-500/20 text-orange-300" : "bg-green-500/20 text-green-300"}>
                      {subscription?.subscription_cancelled ? 'Cancelling' : 'Active'}
                    </Badge>
                  )}
                </div>
              </CardHeader>
              <CardContent className="py-4">
                {subscription?.subscription_active ? (
                  <div className="space-y-4">
                    <div className="flex items-center justify-between p-4 bg-gradient-to-r from-yellow-500/10 to-orange-500/10 rounded-lg border border-yellow-400/20">
                      <div>
                        <h3 className="text-2xl font-bold text-gradient-gold" data-testid="plan-name">
                          {subscription?.package_name || 'Premium Plan'}
                        </h3>
                        <p className="text-white/60 text-sm">
                          {subscription?.subscription_type === 'yearly' ? 'Billed annually' : 'Billed monthly'}
                        </p>
                      </div>
                      <div className="text-right">
                        <p className="text-3xl font-bold text-white" data-testid="plan-price">
                          {formatCurrency(subscription?.package_amount)}
                        </p>
                        <p className="text-white/50 text-sm">
                          /{subscription?.subscription_type === 'yearly' ? 'year' : 'month'}
                        </p>
                      </div>
                    </div>

                    <div className="grid sm:grid-cols-2 gap-4">
                      <div className="flex items-center gap-3 p-3 bg-white/5 rounded-lg">
                        <Calendar className="text-blue-400" size={20} />
                        <div>
                          <p className="text-white/50 text-xs">Started</p>
                          <p className="text-white text-sm" data-testid="start-date">
                            {formatDate(subscription?.subscription_started_at)}
                          </p>
                        </div>
                      </div>
                      <div className="flex items-center gap-3 p-3 bg-white/5 rounded-lg">
                        <Clock className="text-purple-400" size={20} />
                        <div>
                          <p className="text-white/50 text-xs">
                            {subscription?.subscription_cancelled ? 'Access Until' : 'Renews'}
                          </p>
                          <p className="text-white text-sm" data-testid="end-date">
                            {formatDate(subscription?.subscription_end_date)}
                          </p>
                        </div>
                      </div>
                    </div>

                    {subscription?.subscription_cancelled && (
                      <div className="p-4 bg-orange-500/10 border border-orange-400/30 rounded-lg">
                        <div className="flex items-center gap-2 text-orange-300 mb-2">
                          <AlertTriangle size={18} />
                          <span className="font-semibold">Subscription Cancelled</span>
                        </div>
                        <p className="text-white/70 text-sm mb-3">
                          Your subscription was cancelled on {formatDate(subscription?.subscription_cancelled_at)}. 
                          You&apos;ll continue to have access until your billing period ends.
                        </p>
                        <Button 
                          onClick={() => reactivateMutation.mutate()}
                          className="bg-orange-500 hover:bg-orange-600 text-white"
                          disabled={reactivateMutation.isPending}
                          data-testid="reactivate-btn"
                        >
                          <RefreshCw className={`mr-2 ${reactivateMutation.isPending ? 'animate-spin' : ''}`} size={16} />
                          {reactivateMutation.isPending ? 'Reactivating...' : 'Reactivate Subscription'}
                        </Button>
                      </div>
                    )}
                  </div>
                ) : (
                  <div className="text-center py-8">
                    <XCircle className="w-16 h-16 text-white/30 mx-auto mb-4" />
                    <h3 className="text-xl text-white mb-2">No Active Subscription</h3>
                    <p className="text-white/60 mb-6">
                      Subscribe to unlock premium features and support InfoPilot!
                    </p>
                    <Link to="/subscribe">
                      <Button className="btn-gold" data-testid="subscribe-now-btn">
                        <Crown className="mr-2" size={16} /> Subscribe Now
                      </Button>
                    </Link>
                  </div>
                )}
              </CardContent>
              {subscription?.subscription_active && !subscription?.subscription_cancelled && (
                <CardFooter className="pt-0 flex flex-wrap gap-3">
                  <Button 
                    onClick={() => setShowUpgradeDialog(true)}
                    className="bg-gradient-to-r from-purple-500 to-pink-500 hover:from-purple-600 hover:to-pink-600 text-white"
                    data-testid="change-plan-btn"
                  >
                    <ArrowUpCircle className="mr-2" size={16} /> Change Plan
                  </Button>
                  <Button 
                    variant="outline" 
                    onClick={() => setShowCancelDialog(true)}
                    className="text-red-400 border-red-400/30 hover:bg-red-500/10"
                    data-testid="cancel-subscription-btn"
                  >
                    Cancel Subscription
                  </Button>
                </CardFooter>
              )}
            </Card>

            {/* Wallet/Stats Card */}
            <Card className="card-glass" data-testid="wallet-card">
              <CardHeader className="pb-2">
                <CardTitle className="text-white flex items-center gap-2">
                  <Wallet className="text-green-400" size={20} />
                  Wallet
                </CardTitle>
              </CardHeader>
              <CardContent className="py-4">
                <div className="text-center p-4 bg-green-500/10 rounded-lg border border-green-400/20 mb-4">
                  <p className="text-white/50 text-sm mb-1">Balance</p>
                  <p className="text-3xl font-bold text-green-400" data-testid="wallet-balance">
                    {formatCurrency(subscription?.wallet_balance)}
                  </p>
                </div>
                <p className="text-white/50 text-xs text-center">
                  Earnings from marketplace sales
                </p>
              </CardContent>
              <CardFooter>
                <Link to="/revenue" className="w-full">
                  <Button variant="outline" className="w-full">
                    <DollarSign className="mr-2" size={16} /> View Revenue
                  </Button>
                </Link>
              </CardFooter>
            </Card>

            {/* Billing History Card */}
            <Card className="card-glass md:col-span-3" data-testid="billing-history-card">
              <CardHeader className="pb-2">
                <div className="flex items-center justify-between">
                  <CardTitle className="text-white flex items-center gap-2">
                    <History className="text-blue-400" size={20} />
                    Billing History
                  </CardTitle>
                  {billing?.total_spent > 0 && (
                    <Badge className="bg-blue-500/20 text-blue-300">
                      Total: {formatCurrency(billing?.total_spent)}
                    </Badge>
                  )}
                </div>
                <CardDescription className="text-white/50">
                  Your payment and subscription history
                </CardDescription>
              </CardHeader>
              <CardContent>
                {billLoading ? (
                  <div className="text-center py-8">
                    <RefreshCw className="w-8 h-8 text-white/30 animate-spin mx-auto" />
                  </div>
                ) : billing?.billing_history?.length > 0 ? (
                  <div className="overflow-x-auto">
                    <table className="w-full">
                      <thead>
                        <tr className="border-b border-white/10">
                          <th className="text-left py-3 px-2 text-white/50 text-sm font-medium">Date</th>
                          <th className="text-left py-3 px-2 text-white/50 text-sm font-medium">Description</th>
                          <th className="text-left py-3 px-2 text-white/50 text-sm font-medium">Amount</th>
                          <th className="text-left py-3 px-2 text-white/50 text-sm font-medium">Status</th>
                        </tr>
                      </thead>
                      <tbody>
                        {billing.billing_history.map((item, idx) => (
                          <tr key={item.id || idx} className="border-b border-white/5 hover:bg-white/5" data-testid={`billing-row-${idx}`}>
                            <td className="py-3 px-2 text-white/70 text-sm">
                              {formatDate(item.date)}
                            </td>
                            <td className="py-3 px-2 text-white text-sm">
                              {item.description}
                              <span className="ml-2 text-white/40 text-xs">
                                ({item.type})
                              </span>
                            </td>
                            <td className="py-3 px-2 text-white font-medium text-sm">
                              {formatCurrency(item.amount)}
                            </td>
                            <td className="py-3 px-2">
                              <Badge className={
                                item.status === 'paid' 
                                  ? 'bg-green-500/20 text-green-300' 
                                  : item.status === 'pending'
                                  ? 'bg-yellow-500/20 text-yellow-300'
                                  : 'bg-red-500/20 text-red-300'
                              }>
                                {item.status === 'paid' && <CheckCircle className="w-3 h-3 mr-1" />}
                                {item.status}
                              </Badge>
                            </td>
                          </tr>
                        ))}
                      </tbody>
                    </table>
                  </div>
                ) : (
                  <div className="text-center py-8">
                    <History className="w-12 h-12 text-white/20 mx-auto mb-3" />
                    <p className="text-white/50">No billing history yet</p>
                  </div>
                )}
              </CardContent>
            </Card>
          </div>
        )}

        {/* Cancel Confirmation Dialog */}
        <Dialog open={showCancelDialog} onOpenChange={setShowCancelDialog}>
          <DialogContent className="bg-slate-900 border-red-400/30">
            <DialogHeader>
              <DialogTitle className="text-red-400 flex items-center gap-2">
                <AlertTriangle size={20} /> Cancel Subscription?
              </DialogTitle>
              <DialogDescription className="text-white/70">
                Are you sure you want to cancel your subscription?
              </DialogDescription>
            </DialogHeader>
            <div className="py-4">
              <ul className="space-y-2 text-white/70 text-sm">
                <li className="flex items-center gap-2">
                  <CheckCircle className="text-green-400" size={16} />
                  You&apos;ll keep access until {formatDate(subscription?.subscription_end_date)}
                </li>
                <li className="flex items-center gap-2">
                  <CheckCircle className="text-green-400" size={16} />
                  You can reactivate anytime before that date
                </li>
                <li className="flex items-center gap-2">
                  <XCircle className="text-red-400" size={16} />
                  After cancellation, premium features will be disabled
                </li>
              </ul>
            </div>
            <DialogFooter className="gap-2">
              <Button variant="outline" onClick={() => setShowCancelDialog(false)}>
                Keep Subscription
              </Button>
              <Button 
                onClick={() => cancelMutation.mutate()}
                className="bg-red-500 hover:bg-red-600 text-white"
                disabled={cancelMutation.isPending}
                data-testid="confirm-cancel-btn"
              >
                {cancelMutation.isPending ? 'Cancelling...' : 'Yes, Cancel'}
              </Button>
            </DialogFooter>
          </DialogContent>
        </Dialog>

        {/* Upgrade/Change Plan Dialog */}
        <Dialog open={showUpgradeDialog} onOpenChange={setShowUpgradeDialog}>
          <DialogContent className="bg-slate-900 border-purple-400/30">
            <DialogHeader>
              <DialogTitle className="text-gradient-gold flex items-center gap-2">
                <ArrowUpCircle size={20} /> Change Your Plan
              </DialogTitle>
              <DialogDescription className="text-white/70">
                Switch between monthly and yearly billing
              </DialogDescription>
            </DialogHeader>
            <div className="py-4 grid gap-4">
              <Card 
                className={`p-4 cursor-pointer transition hover:border-yellow-400/50 ${
                  subscription?.subscription_type === 'monthly' 
                    ? 'border-yellow-400/50 bg-yellow-400/5' 
                    : 'card-glass'
                }`}
                onClick={() => subscription?.subscription_type !== 'monthly' && handleUpgrade('monthly')}
                data-testid="select-monthly-plan"
              >
                <div className="flex items-center justify-between">
                  <div>
                    <h4 className="text-white font-semibold">Monthly</h4>
                    <p className="text-white/50 text-sm">Flexible, cancel anytime</p>
                  </div>
                  <div className="text-right">
                    <p className="text-xl font-bold text-white">$1.00<span className="text-sm text-white/50">/mo</span></p>
                    {subscription?.subscription_type === 'monthly' && (
                      <Badge className="bg-yellow-400/20 text-yellow-300">Current</Badge>
                    )}
                  </div>
                </div>
              </Card>
              
              <Card 
                className={`p-4 cursor-pointer transition hover:border-green-400/50 ${
                  subscription?.subscription_type === 'yearly' 
                    ? 'border-green-400/50 bg-green-400/5' 
                    : 'card-glass'
                }`}
                onClick={() => subscription?.subscription_type !== 'yearly' && handleUpgrade('yearly')}
                data-testid="select-yearly-plan"
              >
                <div className="flex items-center justify-between">
                  <div>
                    <h4 className="text-white font-semibold">Yearly</h4>
                    <p className="text-white/50 text-sm">Save 17% - Best value!</p>
                  </div>
                  <div className="text-right">
                    <p className="text-xl font-bold text-white">$9.98<span className="text-sm text-white/50">/yr</span></p>
                    {subscription?.subscription_type === 'yearly' && (
                      <Badge className="bg-green-400/20 text-green-300">Current</Badge>
                    )}
                  </div>
                </div>
              </Card>
            </div>
            <DialogFooter>
              <Button variant="outline" onClick={() => setShowUpgradeDialog(false)}>
                Close
              </Button>
            </DialogFooter>
          </DialogContent>
        </Dialog>
      </div>
    </div>
  );
};

export default SubscriptionDashboard;
