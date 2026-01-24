import React, { useEffect } from "react";
import { useNavigate, Link } from "react-router-dom";
import { 
  Search, Map, BarChart3, Users, Globe, Folder,
  ShoppingBag, Check, Play, Zap, Smartphone, Monitor
} from "lucide-react";
import { Button } from "@/components/ui/button";
import { Card } from "@/components/ui/card";
import { Badge } from "@/components/ui/badge";
import { useAuth } from "../contexts/AuthContext";

const LandingPage = () => {
  const { user, login } = useAuth();
  const navigate = useNavigate();

  useEffect(() => {
    if (user) {
      navigate("/dashboard");
    }
  }, [user, navigate]);

  return (
    <div className="min-h-screen bg-[#FFFFF0]">
      {/* Navigation */}
      <nav className="fixed top-0 left-0 right-0 z-50 bg-white/80 backdrop-blur-md border-b border-gray-100/50">
        <div className="max-w-7xl mx-auto px-6 py-4 flex items-center justify-between">
          <div className="flex items-center gap-2">
            <Globe className="w-8 h-8 text-[#007AFF]" />
            <span className="text-xl font-bold font-['Outfit']">InfoPilot Explorer</span>
          </div>
          <div className="flex items-center gap-4">
            <Button variant="ghost" onClick={login} data-testid="login-btn">
              Sign In
            </Button>
            <Button className="btn-primary px-6" onClick={login} data-testid="get-started-btn">
              Get Started
            </Button>
          </div>
        </div>
      </nav>

      {/* Hero Section */}
      <section className="pt-32 pb-20 px-6">
        <div className="max-w-7xl mx-auto">
          <div className="grid md:grid-cols-2 gap-12 items-center">
            <div className="slide-up">
              <Badge className="mb-4 badge-primary">World Wide Web Information Exchange</Badge>
              <h1 className="text-6xl md:text-7xl font-bold tracking-tight mb-6 font-['Outfit']">
                Your <span className="text-[#007AFF]">3D View</span> of the Internet
              </h1>
              <p className="text-xl text-gray-600 mb-8 leading-relaxed">
                The #1 resource for finding information valuable to YOU. Create custom search protocols, 
                collate results into categories, and explore the web like never before.
              </p>
              <div className="flex flex-wrap gap-4">
                <Button className="btn-primary h-14 px-8 text-lg" onClick={login} data-testid="hero-get-started">
                  <Zap className="w-5 h-5 mr-2" /> Start Exploring
                </Button>
                <Button variant="outline" className="h-14 px-8 text-lg rounded-full" data-testid="learn-more-btn">
                  <Play className="w-5 h-5 mr-2" /> Watch Demo
                </Button>
              </div>
            </div>
            <div className="relative slide-up stagger-2">
              <div className="glass-card p-8 hover-lift">
                <img 
                  src="https://images.unsplash.com/photo-1765527977786-93d61f48a963?w=800"
                  alt="3D Digital Globe Network"
                  className="rounded-xl w-full"
                />
              </div>
            </div>
          </div>
        </div>
      </section>

      {/* Features Section */}
      <section className="py-20 px-6 bg-white/50">
        <div className="max-w-7xl mx-auto">
          <div className="text-center mb-16">
            <h2 className="text-4xl md:text-5xl font-semibold mb-4 font-['Outfit']">
              Powerful Features
            </h2>
            <p className="text-xl text-gray-600">Search the web on your terms using InfoJet 2.0</p>
          </div>
          
          <div className="grid md:grid-cols-3 gap-8">
            {[
              { icon: Search, title: "Smart Protocols", desc: "Create custom Boolean search protocols for any topic imaginable" },
              { icon: Folder, title: "Auto-Categorization", desc: "Our Internet Robot automatically collates results into your categories" },
              { icon: Map, title: "Visual Mapping", desc: "See your research on an interactive world map with location data" },
              { icon: BarChart3, title: "Deep Analytics", desc: "Charts and statistics to understand your information landscape" },
              { icon: Users, title: "Social Network", desc: "Connect with researchers, share protocols, and collaborate" },
              { icon: ShoppingBag, title: "Protocol Marketplace", desc: "Buy and sell proven search protocols with the community" }
            ].map((feature, i) => (
              <Card key={i} className="glass-card hover-lift p-6 slide-up" style={{ animationDelay: `${i * 0.1}s` }}>
                <feature.icon className="w-12 h-12 text-[#007AFF] mb-4" />
                <h3 className="text-xl font-semibold mb-2 font-['Outfit']">{feature.title}</h3>
                <p className="text-gray-600">{feature.desc}</p>
              </Card>
            ))}
          </div>
        </div>
      </section>

      {/* Protocol Example Section */}
      <section className="py-20 px-6">
        <div className="max-w-7xl mx-auto">
          <div className="grid md:grid-cols-2 gap-12 items-center">
            <div>
              <Badge className="mb-4 badge-secondary">InfoJet 2.0</Badge>
              <h2 className="text-4xl font-semibold mb-6 font-['Outfit']">
                Protocol Examples
              </h2>
              <div className="space-y-4">
                <div className="glass-card p-4">
                  <p className="text-sm font-medium text-gray-500 mb-2">American Civil War Research</p>
                  <code className="protocol-editor block text-sm">
                    (American civil war) & (battle or battles) & (1860 to 1865)+
                  </code>
                </div>
                <div className="glass-card p-4">
                  <p className="text-sm font-medium text-gray-500 mb-2">Civil War Heroes</p>
                  <code className="protocol-editor block text-sm">
                    (heroically or hero) & (Gettysburg or Princeton) & (isn't or wasn't)^
                  </code>
                </div>
                <div className="glass-card p-4">
                  <p className="text-sm font-medium text-gray-500 mb-2">William C. Gamble</p>
                  <code className="protocol-editor block text-sm">
                    (William Gamble or General Gamble) & (Civil War) & (U.S. Army)+
                  </code>
                </div>
              </div>
            </div>
            <div className="glass-card p-8">
              <h3 className="text-xl font-semibold mb-4 font-['Outfit']">Protocol Syntax</h3>
              <ul className="space-y-3">
                <li className="flex items-start gap-3">
                  <Check className="w-5 h-5 text-[#34C759] mt-0.5" />
                  <span><code className="bg-gray-100 px-2 py-1 rounded">or</code> - Alternative terms within a group</span>
                </li>
                <li className="flex items-start gap-3">
                  <Check className="w-5 h-5 text-[#34C759] mt-0.5" />
                  <span><code className="bg-gray-100 px-2 py-1 rounded">&</code> - AND between groups</span>
                </li>
                <li className="flex items-start gap-3">
                  <Check className="w-5 h-5 text-[#34C759] mt-0.5" />
                  <span><code className="bg-gray-100 px-2 py-1 rounded">+</code> - Include these terms</span>
                </li>
                <li className="flex items-start gap-3">
                  <Check className="w-5 h-5 text-[#34C759] mt-0.5" />
                  <span><code className="bg-gray-100 px-2 py-1 rounded">^</code> - Exclude these terms</span>
                </li>
                <li className="flex items-start gap-3">
                  <Check className="w-5 h-5 text-[#34C759] mt-0.5" />
                  <span>Case insensitive matching</span>
                </li>
                <li className="flex items-start gap-3">
                  <Check className="w-5 h-5 text-[#34C759] mt-0.5" />
                  <span>Works with any language in the world</span>
                </li>
              </ul>
            </div>
          </div>
        </div>
      </section>

      {/* CTA Section */}
      <section className="py-20 px-6 bg-gradient-to-br from-[#007AFF]/5 to-[#34C759]/5">
        <div className="max-w-3xl mx-auto text-center">
          <h2 className="text-4xl font-semibold mb-6 font-['Outfit']">
            Ready to Transform Your Research?
          </h2>
          <p className="text-xl text-gray-600 mb-8">
            Join thousands of researchers, professionals, and curious minds exploring the web smarter.
          </p>
          <Button className="btn-primary h-14 px-12 text-lg" onClick={login} data-testid="cta-get-started">
            Start Free - $0.99/month
          </Button>
          <p className="text-sm text-gray-500 mt-4">No credit card required for trial</p>
        </div>
      </section>

      {/* Footer */}
      <footer className="py-12 px-6 border-t border-gray-200">
        <div className="max-w-7xl mx-auto">
          <div className="grid md:grid-cols-4 gap-8 mb-8">
            {/* Brand */}
            <div>
              <div className="flex items-center gap-2 mb-4">
                <Globe className="w-6 h-6 text-[#007AFF]" />
                <span className="font-bold font-['Outfit']">InfoPilot Explorer</span>
              </div>
              <p className="text-sm text-gray-500">First in Flight with Monetization of Searches</p>
              <p className="text-xs text-gray-400 mt-2">Top Pilot Enterprises Inc.</p>
            </div>
            
            {/* Legal */}
            <div>
              <h4 className="font-semibold mb-4">Legal</h4>
              <div className="space-y-2 text-sm text-gray-600">
                <Link to="/privacy-policy" className="block hover:text-[#007AFF]" data-testid="footer-privacy">Privacy Policy</Link>
                <Link to="/terms-of-service" className="block hover:text-[#007AFF]" data-testid="footer-terms">Terms of Service</Link>
              </div>
            </div>
            
            {/* Download Apps */}
            <div>
              <h4 className="font-semibold mb-4">Download</h4>
              <div className="space-y-2 text-sm text-gray-600">
                <a href="https://play.google.com/store/apps/details?id=com.infopilot.explorer" target="_blank" rel="noopener noreferrer" className="flex items-center gap-2 hover:text-[#007AFF]" data-testid="download-android">
                  <Smartphone className="w-4 h-4" /> Android App
                </a>
                <a href="https://apps.apple.com/app/infojet" target="_blank" rel="noopener noreferrer" className="flex items-center gap-2 hover:text-[#007AFF]" data-testid="download-ios">
                  <Smartphone className="w-4 h-4" /> iOS App
                </a>
                <a href="https://www.infopilotexplorer.biz/download" target="_blank" rel="noopener noreferrer" className="flex items-center gap-2 hover:text-[#007AFF]" data-testid="download-desktop">
                  <Monitor className="w-4 h-4" /> Desktop App
                </a>
              </div>
            </div>
            
            {/* Contact */}
            <div>
              <h4 className="font-semibold mb-4">Contact</h4>
              <div className="space-y-2 text-sm text-gray-600">
                <p>Brunswick, Maine</p>
                <p>JJSpilot24@gmail.com</p>
                <p>(207) 522-0894</p>
              </div>
            </div>
          </div>
          
          <div className="pt-8 border-t border-gray-200 flex flex-col md:flex-row justify-between items-center gap-4">
            <p className="text-sm text-gray-500">© 2025-2026 Top Pilot Enterprises, Inc. All rights reserved.</p>
            <p className="text-xs text-gray-400">InfoPilot Explorer - First in Flight with Monetization of Searches</p>
          </div>
        </div>
      </footer>
    </div>
  );
};

export default LandingPage;
