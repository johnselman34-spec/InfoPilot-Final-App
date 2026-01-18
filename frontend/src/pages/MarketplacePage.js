import React, { useState } from 'react';
import { Navigate, Link } from 'react-router-dom';
import { useQuery, useMutation } from '@tanstack/react-query';
import axios from 'axios';
import { useAuth } from '../context/AuthContext';
import { useToast } from '../context/ToastContext';
import StarsBackground from '../components/StarsBackground';
import { Card, CardContent, CardFooter, CardHeader, CardTitle } from '../components/ui/card';
import { Button } from '../components/ui/button';
import { Badge } from '../components/ui/badge';
import { Dialog, DialogContent, DialogDescription, DialogFooter, DialogHeader, DialogTitle } from '../components/ui/dialog';
import { Store, CreditCard, Copy, CheckCircle } from 'lucide-react';
import { API } from '../utils/api';

const MarketplacePage = () => {
  const { user } = useAuth();
  const showToast = useToast();
  const [selectedCategory, setSelectedCategory] = useState("all");
  const [showSellerInfo, setShowSellerInfo] = useState(false);
  
  const { data: protocols, isLoading } = useQuery({
    queryKey: ["marketplace", selectedCategory],
    queryFn: () => axios.get(`${API}/marketplace/protocols`, { params: selectedCategory !== "all" ? { category: selectedCategory } : {} }).then(r => r.data)
  });

  // Use Stripe for payments
  const buyMutation = useMutation({
    mutationFn: async (protocol) => {
      const response = await axios.post(`${API}/stripe/create-checkout`, {
        protocol_id: protocol.id,
        package_type: "protocol_purchase",
        origin_url: window.location.origin
      });
      return response.data;
    },
    onSuccess: (data) => {
      showToast("Redirecting to secure checkout...", "success");
      if (data.checkout_url) {
        window.location.href = data.checkout_url;
      }
    },
    onError: (err) => showToast(err.response?.data?.detail || "Purchase failed", "error")
  });

  if (!user) return <Navigate to="/login" />;

  // Extract unique category keywords for filtering
  const categoryKeywords = ["History", "Technology", "Science", "Business", "Health", "Sports", "Education", "Entertainment"];
  const protocolList = protocols?.protocols || [];

  return (
    <div className="min-h-screen pt-20 px-4">
      <StarsBackground />
      <div className="max-w-6xl mx-auto">
        <div className="text-center mb-8">
          <Badge className="mb-4 bg-red-500/20 text-red-300">🐻 As Dangerous as a Kodiak Bear!</Badge>
          <h1 className="text-3xl font-bold text-gradient-gold mb-2">Protocol Marketplace</h1>
          <p className="text-white/60">First in Flight with Monetization of Searches!</p>
        </div>

        {/* Category Filter */}
        <Card className="card-glass p-4 mb-6" data-testid="marketplace-categories">
          <div className="flex flex-wrap items-center gap-2">
            <span className="text-white/70 text-sm mr-2">Filter by Category:</span>
            <Badge 
              className={`cursor-pointer transition ${selectedCategory === "all" ? "bg-yellow-400/30 text-yellow-300" : "bg-white/10 text-white/60 hover:bg-white/20"}`}
              onClick={() => setSelectedCategory("all")}
            >
              All ({protocols?.total || 0})
            </Badge>
            {categoryKeywords.map(cat => (
              <Badge 
                key={cat}
                className={`cursor-pointer transition ${selectedCategory === cat ? "bg-yellow-400/30 text-yellow-300" : "bg-white/10 text-white/60 hover:bg-white/20"}`}
                onClick={() => setSelectedCategory(cat)}
              >
                {cat}
              </Badge>
            ))}
          </div>
        </Card>

        {/* Seller Dashboard Card */}
        <Card className="card-glass p-4 mb-6 border border-green-400/30" data-testid="seller-dashboard">
          <div className="flex items-center justify-between">
            <div>
              <h3 className="text-lg font-bold text-green-400">💰 Become a Seller</h3>
              <p className="text-white/60 text-sm">List your protocols for sale and earn 85% commission on every purchase!</p>
            </div>
            <Button onClick={() => setShowSellerInfo(true)} className="bg-gradient-to-r from-green-500 to-emerald-600 hover:from-green-600 hover:to-emerald-700 text-white" data-testid="seller-info-btn">
              <CreditCard className="mr-2" /> Learn More
            </Button>
          </div>
        </Card>

        {isLoading ? <p className="text-center text-white/60">Loading...</p> : protocolList.length === 0 ? (
          <Card className="card-glass p-8 text-center" data-testid="marketplace-empty">
            <Store className="mx-auto text-yellow-400 mb-4" size={48} />
            <h3 className="text-xl text-white mb-2">No protocols for sale{selectedCategory !== "all" ? ` in ${selectedCategory}` : ""} yet!</h3>
            <p className="text-white/60 mb-4">Be the first to list your protocols in Ultimate Search.</p>
            <Link to="/search"><Button className="btn-gold">Go to Ultimate Search</Button></Link>
          </Card>
        ) : (
          <div className="grid md:grid-cols-2 lg:grid-cols-3 gap-6">
            {protocolList.map(p => (
              <Card key={p.id} className="card-glass p-4 hover:border-yellow-400/50 transition" data-testid={`protocol-${p.id}`}>
                <CardHeader className="pb-2">
                  <div className="flex items-start justify-between">
                    <CardTitle className="text-white text-lg">{p.name}</CardTitle>
                    <Badge className="bg-green-500/20 text-green-300 font-bold">${p.price?.toFixed(2)}</Badge>
                  </div>
                </CardHeader>
                <CardContent className="py-2">
                  <div className="bg-slate-800/50 p-2 rounded font-mono text-xs text-green-400 mb-3 max-h-16 overflow-y-auto">{p.protocol}</div>
                  <div className="flex items-center justify-between text-white/50 text-xs">
                    <span>By: {p.owner?.username || "Anonymous"}</span>
                    <span>{p.search_result_count || 0} results</span>
                  </div>
                </CardContent>
                <CardFooter className="pt-2 flex gap-2">
                  <Button onClick={() => buyMutation.mutate(p)} className="btn-gold flex-1" disabled={buyMutation.isPending || p.user_id === user.id} data-testid={`buy-protocol-${p.id}`}>
                    <CreditCard className="mr-2" size={16} /> {p.user_id === user.id ? "Your Protocol" : "Buy Protocol"}
                  </Button>
                  <Button variant="outline" onClick={() => { navigator.clipboard.writeText(p.protocol); showToast("Protocol copied!", "success"); }} title="Copy Protocol">
                    <Copy size={16} />
                  </Button>
                </CardFooter>
              </Card>
            ))}
          </div>
        )}

        {/* Seller Info Modal */}
        <Dialog open={showSellerInfo} onOpenChange={setShowSellerInfo}>
          <DialogContent className="bg-slate-900 border-yellow-400/30">
            <DialogHeader>
              <DialogTitle className="text-yellow-400">Sell Your Protocols 💰</DialogTitle>
              <DialogDescription className="text-white/70">Monetize your search expertise and earn passive income!</DialogDescription>
            </DialogHeader>
            <div className="py-4 space-y-4">
              <Card className="bg-green-900/20 border-green-400/30 p-4">
                <h4 className="text-green-400 font-semibold mb-2">How It Works</h4>
                <ul className="text-white/70 text-sm space-y-2">
                  <li className="flex items-start gap-2"><CheckCircle className="text-green-400 mt-0.5" size={16} /> Create a protocol in Ultimate Search</li>
                  <li className="flex items-start gap-2"><CheckCircle className="text-green-400 mt-0.5" size={16} /> Set a price and mark it "For Sale"</li>
                  <li className="flex items-start gap-2"><CheckCircle className="text-green-400 mt-0.5" size={16} /> Buyers pay via Stripe (secure checkout)</li>
                  <li className="flex items-start gap-2"><CheckCircle className="text-green-400 mt-0.5" size={16} /> You receive 85% of each sale</li>
                </ul>
              </Card>
              <Card className="bg-blue-900/20 border-blue-400/30 p-4">
                <h4 className="text-blue-400 font-semibold mb-2">Commission Structure</h4>
                <div className="flex justify-between text-white/70 text-sm">
                  <span>Your Earnings:</span>
                  <span className="text-green-400 font-bold">85%</span>
                </div>
                <div className="flex justify-between text-white/70 text-sm">
                  <span>Platform Fee:</span>
                  <span className="text-white/50">15%</span>
                </div>
              </Card>
              <div className="text-center">
                <Link to="/search">
                  <Button className="btn-gold">
                    <Store className="mr-2" size={16} /> Go to Ultimate Search
                  </Button>
                </Link>
                <p className="text-white/50 text-xs mt-2">Create and list your first protocol today!</p>
              </div>
            </div>
            <DialogFooter>
              <Button variant="outline" onClick={() => setShowSellerInfo(false)}>Close</Button>
            </DialogFooter>
          </DialogContent>
        </Dialog>
      </div>
    </div>
  );
};

export default MarketplacePage;
