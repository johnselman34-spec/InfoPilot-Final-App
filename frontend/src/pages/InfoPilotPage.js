import React from 'react';
import { Link } from 'react-router-dom';
import StarsBackground from '../components/StarsBackground';
import { Card } from '../components/ui/card';
import { Button } from '../components/ui/button';
import { Badge } from '../components/ui/badge';
import { Sparkles, Star, Search, Map, Store, MessageCircle } from 'lucide-react';
import { PAYPAL_INFOPILOT_LINK } from '../utils/api';

const InfoPilotPage = () => {
  return (
    <div className="min-h-screen pt-20 px-4">
      <StarsBackground />
      <div className="max-w-4xl mx-auto">
        <div className="text-center mb-12">
          <div className="w-24 h-24 rounded-full bg-gradient-to-br from-yellow-400 to-orange-500 flex items-center justify-center mx-auto mb-6">
            <Sparkles className="text-slate-900" size={48} />
          </div>
          <Badge className="mb-4 bg-yellow-400/20 text-yellow-400">First in Flight!</Badge>
          <h1 className="text-5xl font-bold text-gradient-gold mb-4">InfoPilot Explorer</h1>
          <p className="text-white/60 text-lg max-w-2xl mx-auto">The worlds first search protocol marketplace. Create, categorize, and monetize your search expertise.</p>
        </div>
        
        <div className="grid md:grid-cols-2 gap-6 mb-12">
          {[
            { icon: <Search />, title: "InfoJet 2.0 Protocols", desc: "Create powerful Boolean search queries" },
            { icon: <Map />, title: "Interactive Maps", desc: "Visualize results geographically" },
            { icon: <Store />, title: "Protocol Marketplace", desc: "Buy and sell search protocols" },
            { icon: <MessageCircle />, title: "Community", desc: "Chat rooms and groups" }
          ].map((f, i) => (
            <Card key={i} className="card-glass p-6">
              <div className="text-yellow-400 mb-3">{f.icon}</div>
              <h3 className="text-xl font-bold text-white mb-2">{f.title}</h3>
              <p className="text-white/60">{f.desc}</p>
            </Card>
          ))}
        </div>
        
        <Card className="card-glass p-8 text-center border-yellow-400/30">
          <Star className="mx-auto text-yellow-400 mb-4" size={48} />
          <h2 className="text-2xl font-bold text-white mb-4">Subscribe Now</h2>
          <p className="text-white/60 mb-6">Get full access to all features for just $1/month or $9.98/year</p>
          <div className="flex gap-4 justify-center">
            <a href={PAYPAL_INFOPILOT_LINK} target="_blank" rel="noopener noreferrer">
              <Button className="btn-gold text-lg px-8 py-6">Subscribe $1/mo</Button>
            </a>
            <Link to="/login">
              <Button variant="outline" className="text-lg px-8 py-6 text-yellow-400 border-yellow-400/30">Try Free</Button>
            </Link>
          </div>
        </Card>
      </div>
    </div>
  );
};
export default InfoPilotPage;
