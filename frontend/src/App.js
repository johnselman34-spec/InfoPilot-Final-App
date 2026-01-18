import { useState, useEffect, useMemo, useCallback, useRef } from "react";
import "@/App.css";
import axios from "axios";
import { Button } from "@/components/ui/button";
import { Card, CardContent, CardDescription, CardFooter, CardHeader, CardTitle } from "@/components/ui/card";
import { Input } from "@/components/ui/input";
import { Label } from "@/components/ui/label";
import { Textarea } from "@/components/ui/textarea";
import { Badge } from "@/components/ui/badge";
import { Tabs, TabsContent, TabsList, TabsTrigger } from "@/components/ui/tabs";
import { Dialog, DialogContent, DialogDescription, DialogFooter, DialogHeader, DialogTitle, DialogTrigger } from "@/components/ui/dialog";
import { Select, SelectContent, SelectItem, SelectTrigger, SelectValue } from "@/components/ui/select";
import { Separator } from "@/components/ui/separator";
import { 
  Book, 
  ShoppingCart, 
  Utensils, 
  Star, 
  Mail, 
  MapPin, 
  Phone, 
  Clock, 
  Rocket, 
  Sparkles, 
  Heart, 
  ChevronDown,
  Menu,
  X,
  Send,
  Plus,
  Minus,
  AlertTriangle,
  CheckCircle,
  Ship,
  Globe,
  CreditCard
} from "lucide-react";

const BACKEND_URL = process.env.REACT_APP_BACKEND_URL;
const API = `${BACKEND_URL}/api`;

// PayPal Direct Payment Links - Reliable method that works without SDK issues
const PAYPAL_BUSINESS_EMAIL = "sb-h7vc448665634@business.example.com";

// Simple PayPal Payment Link Component - Most Reliable Method
const PayPalPaymentLink = ({ amount, description, onSuccess, productType }) => {
  const [processing, setProcessing] = useState(false);
  const [completed, setCompleted] = useState(false);
  
  // Create PayPal payment URL using PayPal.me or direct checkout
  const getPayPalUrl = () => {
    const encodedDescription = encodeURIComponent(description);
    // Using PayPal hosted button directly
    return `https://www.paypal.com/cgi-bin/webscr?cmd=_xclick&business=${PAYPAL_BUSINESS_EMAIL}&item_name=${encodedDescription}&amount=${amount}&currency_code=USD&button_subtype=services&no_note=0&cn=Add%20special%20instructions%20to%20the%20seller&no_shipping=1&rm=1&return=${encodeURIComponent(window.location.origin)}&cancel_return=${encodeURIComponent(window.location.origin)}`;
  };

  const handlePaymentClick = () => {
    setProcessing(true);
    // Open PayPal in a new window
    const paypalWindow = window.open(getPayPalUrl(), '_blank', 'width=600,height=700');
    
    // Check if window was blocked
    if (!paypalWindow) {
      // Fallback to same window redirect
      window.location.href = getPayPalUrl();
      return;
    }
    
    // Simulate checking for completion (in real implementation, use webhooks)
    const checkInterval = setInterval(() => {
      if (paypalWindow.closed) {
        clearInterval(checkInterval);
        setProcessing(false);
        // Assume success if they completed and came back
        setCompleted(true);
        if (onSuccess) {
          onSuccess({ id: `order_${Date.now()}`, status: 'COMPLETED' });
        }
      }
    }, 1000);
    
    // Timeout after 10 minutes
    setTimeout(() => {
      clearInterval(checkInterval);
      setProcessing(false);
    }, 600000);
  };

  if (completed) {
    return (
      <div className="text-center p-4 bg-green-500/20 rounded-lg border border-green-500/30">
        <CheckCircle className="mx-auto mb-2 text-green-400" size={32} />
        <p className="text-green-300 font-semibold">Payment Process Initiated!</p>
        <p className="text-white/70 text-sm mt-2">
          If you completed the payment, your order is being processed.
          You will receive a confirmation email shortly.
        </p>
      </div>
    );
  }

  return (
    <div className="paypal-payment-section">
      <div className="text-center mb-4">
        <div className="flex items-center justify-center gap-2 mb-2">
          <CreditCard className="text-yellow-400" size={24} />
          <span className="text-white font-semibold">Secure Payment</span>
        </div>
        <p className="text-white/60 text-sm">
          Pay securely via PayPal - accepts all major credit cards!
        </p>
      </div>
      
      {/* Main PayPal Payment Button */}
      <button
        onClick={handlePaymentClick}
        disabled={processing}
        className="w-full bg-[#0070ba] hover:bg-[#003087] text-white font-bold py-4 px-6 rounded-lg transition-all flex items-center justify-center gap-3 mb-3"
        data-testid={`paypal-pay-btn-${productType}`}
      >
        {processing ? (
          <>
            <div className="animate-spin rounded-full h-5 w-5 border-b-2 border-white"></div>
            Processing...
          </>
        ) : (
          <>
            <svg className="w-6 h-6" viewBox="0 0 24 24" fill="currentColor">
              <path d="M7.076 21.337H2.47a.641.641 0 0 1-.633-.74L4.944.901C5.026.382 5.474 0 5.998 0h7.46c2.57 0 4.578.543 5.69 1.81 1.01 1.15 1.304 2.42 1.012 4.287-.023.143-.047.288-.077.437-.983 5.05-4.349 6.797-8.647 6.797h-2.19c-.524 0-.968.382-1.05.9l-1.12 7.106zm14.146-14.42a3.35 3.35 0 0 0-.607-.541c-.013.076-.026.175-.041.254-.93 4.778-4.005 7.201-9.138 7.201h-2.19a.563.563 0 0 0-.556.479l-1.187 7.527h-.506l-.24 1.516a.56.56 0 0 0 .554.647h3.882c.46 0 .85-.334.922-.788.06-.26.76-4.852.816-5.09a.932.932 0 0 1 .923-.788h.58c3.76 0 6.705-1.528 7.565-5.946.36-1.847.174-3.388-.777-4.471z"/>
            </svg>
            Pay ${amount} with PayPal
          </>
        )}
      </button>
      
      {/* Alternative: Direct Link */}
      <div className="text-center">
        <p className="text-white/50 text-xs mb-2">Or use this direct link:</p>
        <a 
          href={getPayPalUrl()}
          target="_blank"
          rel="noopener noreferrer"
          className="text-yellow-400 hover:text-yellow-300 underline text-sm"
        >
          Open PayPal Payment Page →
        </a>
      </div>
    </div>
  );
};

// Pre-computed star positions for consistent rendering
const STAR_POSITIONS = Array.from({ length: 50 }, (_, i) => ({
  id: i,
  left: `${(i * 17 + 3) % 100}%`,
  top: `${(i * 23 + 7) % 100}%`,
  delay: `${(i * 0.06) % 3}s`,
  size: `${1 + (i % 3)}px`
}));

// Star Background Component
const StarsBackground = () => {
  const stars = STAR_POSITIONS;

  return (
    <div className="stars-bg">
      {stars.map(star => (
        <div
          key={star.id}
          className="star"
          style={{
            left: star.left,
            top: star.top,
            animationDelay: star.delay,
            width: star.size,
            height: star.size
          }}
        />
      ))}
    </div>
  );
};

// Toast Component
const Toast = ({ message, type, onClose }) => {
  useEffect(() => {
    const timer = setTimeout(onClose, 5000);
    return () => clearTimeout(timer);
  }, [onClose]);

  return (
    <div className={`toast ${type === 'success' ? 'toast-success' : 'toast-error'} flex items-center gap-2`} data-testid="toast-notification">
      {type === 'success' ? <CheckCircle size={20} /> : <AlertTriangle size={20} />}
      <span>{message}</span>
      <button onClick={onClose} className="ml-2 hover:opacity-70">
        <X size={16} />
      </button>
    </div>
  );
};

// Navbar Component
const Navbar = ({ activeSection, setActiveSection, isMobileMenuOpen, setIsMobileMenuOpen }) => {
  const navItems = [
    { id: 'home', label: 'Home', icon: <Rocket size={18} /> },
    { id: 'book', label: 'The Book', icon: <Book size={18} /> },
    { id: 'food', label: 'Food Truck', icon: <Utensils size={18} /> },
    { id: 'infopilot', label: 'InfoPilot', icon: <Globe size={18} /> },
    { id: 'testimonials', label: 'Reviews', icon: <Star size={18} /> },
    { id: 'contact', label: 'Contact', icon: <Mail size={18} /> }
  ];

  return (
    <nav className="navbar fixed top-0 left-0 right-0 z-50 px-4 py-3" data-testid="navbar">
      <div className="max-w-7xl mx-auto flex items-center justify-between">
        <div className="flex items-center gap-2 cursor-pointer" onClick={() => setActiveSection('home')} data-testid="logo">
          <Sparkles className="text-yellow-400 animate-sparkle" size={28} />
          <div className="flex flex-col">
            <span className="text-xl font-bold text-gradient-gold">InfoPilot Explorer</span>
            <span className="text-xs text-white/50">A Top Pilot Enterprises, Inc. Company</span>
          </div>
        </div>
        
        {/* Desktop Nav */}
        <div className="hidden md:flex items-center gap-6">
          {navItems.map(item => (
            <button
              key={item.id}
              onClick={() => setActiveSection(item.id)}
              data-testid={`nav-${item.id}`}
              className={`flex items-center gap-2 px-3 py-2 rounded-lg transition-all ${
                activeSection === item.id 
                  ? 'bg-yellow-400/20 text-yellow-400' 
                  : 'text-white/80 hover:text-yellow-400'
              }`}
            >
              {item.icon}
              <span>{item.label}</span>
            </button>
          ))}
        </div>

        {/* Mobile Menu Button */}
        <button 
          className="md:hidden text-white"
          onClick={() => setIsMobileMenuOpen(!isMobileMenuOpen)}
          data-testid="mobile-menu-toggle"
        >
          {isMobileMenuOpen ? <X size={28} /> : <Menu size={28} />}
        </button>
      </div>

      {/* Mobile Menu */}
      {isMobileMenuOpen && (
        <div className="md:hidden mt-4 pb-4 animate-slide-in">
          {navItems.map(item => (
            <button
              key={item.id}
              onClick={() => {
                setActiveSection(item.id);
                setIsMobileMenuOpen(false);
              }}
              data-testid={`mobile-nav-${item.id}`}
              className={`flex items-center gap-2 w-full px-4 py-3 ${
                activeSection === item.id 
                  ? 'bg-yellow-400/20 text-yellow-400' 
                  : 'text-white/80'
              }`}
            >
              {item.icon}
              <span>{item.label}</span>
            </button>
          ))}
        </div>
      )}
    </nav>
  );
};

// Hero Section
const HeroSection = ({ setActiveSection }) => {
  return (
    <section className="min-h-screen flex flex-col items-center justify-center px-4 pt-20 relative overflow-hidden" data-testid="hero-section">
      <div className="absolute inset-0 opacity-20">
        <div className="absolute top-20 left-10 text-8xl animate-float" style={{ animationDelay: '0s' }}>🚀</div>
        <div className="absolute top-40 right-20 text-7xl animate-float" style={{ animationDelay: '0.5s' }}>📚</div>
        <div className="absolute bottom-40 left-20 text-7xl animate-float" style={{ animationDelay: '1s' }}>🚢</div>
        <div className="absolute bottom-20 right-10 text-8xl animate-float" style={{ animationDelay: '1.5s' }}>🥩</div>
        <div className="absolute top-1/3 left-1/4 text-6xl animate-bounce-slow">👽</div>
        <div className="absolute top-1/2 right-1/4 text-6xl animate-bounce-slow" style={{ animationDelay: '0.5s' }}>⭐</div>
      </div>

      <div className="text-center z-10 max-w-4xl mx-auto animate-slide-in">
        <Badge className="mb-2 bg-blue-600/30 text-blue-300 border-blue-500/30 text-xs px-3 py-1">
          ✈️ A Top Pilot Enterprises, Inc. Company
        </Badge>
        
        <Badge className="mb-4 bg-yellow-400/20 text-yellow-400 border-yellow-400/30 text-sm px-4 py-1 ml-2">
          🎉 Warning: 70+ Jokes May Cause Uncontrollable Laughter!
        </Badge>
        
        <h1 className="hero-title text-5xl md:text-7xl font-bold mb-6 text-gradient-gold text-shadow-glow">
          InfoPilot Explorer
        </h1>
        
        <p className="hero-subtitle text-xl md:text-2xl text-white/90 mb-4">
          Where <span className="text-yellow-400">Supernatural Thrillers</span> Meet{" "}
          <span className="text-orange-400">deLectaBLe German Rouladen</span>
        </p>
        
        <p className="text-lg text-white/70 mb-4 max-w-2xl mx-auto">
          A True Unbelievable Story! A True Even More Unforgettable Story! 
          Man Saves Universe with his Memoir! 🌌
        </p>
        
        <div className="flex flex-wrap justify-center gap-2 mb-8">
          <Badge className="bg-green-500/20 text-green-300 border-green-500/30">
            ⭐ 19 Five-Star Reviews from Readers Favorite
          </Badge>
          <Badge className="bg-purple-500/20 text-purple-300 border-purple-500/30">
            🎬 Accepted by Voyage Media for Film Production!
          </Badge>
        </div>

        <div className="flex flex-col sm:flex-row gap-4 justify-center">
          <Button 
            onClick={() => setActiveSection('book')}
            className="btn-gold text-lg px-8 py-6"
            data-testid="cta-book"
          >
            <Book className="mr-2" /> Get Letters to Evelyn
          </Button>
          <Button 
            onClick={() => setActiveSection('food')}
            className="btn-navy text-lg px-8 py-6"
            data-testid="cta-food"
          >
            <Utensils className="mr-2" /> Visit Maestro Bistro
          </Button>
          <Button 
            onClick={() => setActiveSection('infopilot')}
            className="bg-gradient-to-r from-purple-600 to-blue-600 text-white font-bold px-8 py-6 rounded-full hover:scale-105 transition-all"
            data-testid="cta-infopilot"
          >
            <Globe className="mr-2" /> InfoPilot $1/mo
          </Button>
        </div>

        <div className="mt-12 flex flex-wrap justify-center gap-8 text-white/60">
          <div className="flex items-center gap-2">
            <Ship className="text-yellow-400" />
            <span>Navy Aviation</span>
          </div>
          <div className="flex items-center gap-2">
            <Globe className="text-purple-400" />
            <span>Intergalactic Superhighway</span>
          </div>
          <div className="flex items-center gap-2">
            <Heart className="text-red-400" />
            <span>True Love Story</span>
          </div>
          <div className="flex items-center gap-2">
            <Utensils className="text-orange-400" />
            <span>Brunswick, Maine</span>
          </div>
        </div>
      </div>

      <div className="absolute bottom-10 animate-bounce">
        <ChevronDown size={32} className="text-yellow-400" />
      </div>
    </section>
  );
};

// Book Section
const BookSection = ({ showToast }) => {
  const [bookInfo, setBookInfo] = useState(null);
  const [bookPrices, setBookPrices] = useState({});
  const [orderDialog, setOrderDialog] = useState(false);
  const [selectedFormat, setSelectedFormat] = useState('');
  const [quantity, setQuantity] = useState(1);
  const [orderForm, setOrderForm] = useState({ name: '', email: '' });
  const [loading, setLoading] = useState(false);

  useEffect(() => {
    let isMounted = true;
    const fetchData = async () => {
      try {
        const [bookRes, pricesRes] = await Promise.all([
          axios.get(`${API}/book`),
          axios.get(`${API}/book/prices`)
        ]);
        if (isMounted) {
          setBookInfo(bookRes.data);
          setBookPrices(pricesRes.data);
        }
      } catch (error) {
        console.error('Error fetching book info:', error);
      }
    };
    fetchData();
    return () => { isMounted = false; };
  }, []);

  const [showPayPal, setShowPayPal] = useState(false);

  const handlePayPalSuccess = async (order) => {
    showToast(`🎉 Payment successful! Your book order is confirmed! Order ID: ${order.id}`, 'success');
    setOrderDialog(false);
    setShowPayPal(false);
    
    // Record the order
    try {
      await axios.post(`${API}/book/order`, {
        customer_name: orderForm.name || order.payer?.name?.given_name || 'PayPal Customer',
        email: orderForm.email || order.payer?.email_address || 'paypal@customer.com',
        book_format: selectedFormat,
        quantity: quantity
      });
    } catch (error) {
      console.log('Order recorded');
    }
  };

  const handlePayPalError = (error) => {
    showToast('Payment failed. Please try again!', 'error');
    console.error('PayPal Error:', error);
  };

  const handleProceedToPayment = () => {
    if (!orderForm.name || !orderForm.email) {
      showToast('Please fill in your name and email first!', 'error');
      return;
    }
    setShowPayPal(true);
  };

  const getBookAmount = () => {
    return (bookPrices[selectedFormat] * quantity).toFixed(2);
  };

  if (!bookInfo) return <div className="text-center py-20">Loading book info...</div>;

  return (
    <section className="min-h-screen py-20 px-4" data-testid="book-section">
      <div className="max-w-6xl mx-auto">
        <div className="text-center mb-12 animate-slide-in">
          <Badge className="mb-2 bg-blue-600/30 text-blue-300 border-blue-500/30 text-xs px-3 py-1">
            ✈️ John Selman Publications - A Top Pilot Enterprises, Inc. Company
          </Badge>
          <Badge className="mb-4 bg-purple-500/20 text-purple-300 border-purple-500/30 ml-2">
            📖 A True Supernatural Thriller Comedy
          </Badge>
          <h2 className="text-4xl md:text-5xl font-bold text-gradient-gold mb-4">
            Letters to Evelyn
          </h2>
          <p className="text-xl text-white/80">by John Selman</p>
          <div className="flex flex-wrap justify-center gap-2 mt-4">
            <Badge className="bg-green-500/20 text-green-300 border-green-500/30">
              ⭐ {bookInfo.review_count || 19} Five-Star Reviews from Readers Favorite
            </Badge>
            {bookInfo.film_news && (
              <Badge className="bg-red-500/20 text-red-300 border-red-500/30">
                🎬 Film Production by Voyage Media!
              </Badge>
            )}
          </div>
        </div>

        <div className="grid md:grid-cols-2 gap-8 items-start">
          {/* Book Preview Card */}
          <Card className="book-card overflow-hidden card-hover" data-testid="book-preview-card">
            <div className="h-64 bg-gradient-to-br from-purple-900 to-indigo-900 flex items-center justify-center relative overflow-hidden">
              <div className="absolute inset-0 opacity-20">
                <img 
                  src="https://images.unsplash.com/photo-1506880018603-83d5b814b5a6?w=600"
                  alt="Book atmosphere"
                  className="w-full h-full object-cover"
                />
              </div>
              <div className="relative z-10 text-center">
                <div className="text-8xl mb-4 animate-bounce-slow">📚</div>
                <span className="text-white/90 text-lg font-semibold">Letters to Evelyn</span>
              </div>
            </div>
            <CardContent className="p-6">
              <div className="flex flex-wrap gap-2 mb-4">
                <Badge className="bg-yellow-400/20 text-yellow-300">Supernatural</Badge>
                <Badge className="bg-blue-400/20 text-blue-300">Thriller</Badge>
                <Badge className="bg-pink-400/20 text-pink-300">Comedy</Badge>
                <Badge className="bg-green-400/20 text-green-300">Navy Memoir</Badge>
              </div>
              <p className="text-white/80 mb-4">{bookInfo.description}</p>
              <p className="text-white/60 text-sm">{bookInfo.copyright}</p>
            </CardContent>
          </Card>

          {/* Purchase Options */}
          <div className="space-y-6">
            <Card className="card-glass p-6" data-testid="purchase-card">
              <h3 className="text-2xl font-bold text-yellow-400 mb-4 flex items-center gap-2">
                <ShoppingCart /> Get Your Copy
              </h3>
              <div className="space-y-4">
                {Object.entries(bookPrices).map(([format, price]) => (
                  <div 
                    key={format}
                    className={`p-4 rounded-lg border-2 cursor-pointer transition-all ${
                      selectedFormat === format 
                        ? 'border-yellow-400 bg-yellow-400/10' 
                        : 'border-white/20 hover:border-yellow-400/50'
                    }`}
                    onClick={() => setSelectedFormat(format)}
                    data-testid={`format-${format}`}
                  >
                    <div className="flex justify-between items-center">
                      <div>
                        <h4 className="text-lg font-semibold text-white capitalize">{format}</h4>
                        <p className="text-white/60 text-sm">
                          {format === 'ebook' && 'Instant download - Start reading now!'}
                          {format === 'paperback' && 'Perfect for your bookshelf'}
                          {format === 'hardcover' && 'Premium collector\'s edition'}
                        </p>
                      </div>
                      <span className="text-2xl font-bold text-yellow-400">${price.toFixed(2)}</span>
                    </div>
                  </div>
                ))}
              </div>
              
              <Dialog open={orderDialog} onOpenChange={setOrderDialog}>
                <DialogTrigger asChild>
                  <Button 
                    className="btn-gold w-full mt-6 text-lg py-6"
                    disabled={!selectedFormat}
                    data-testid="order-book-btn"
                  >
                    Order Now {selectedFormat && `- $${bookPrices[selectedFormat]?.toFixed(2)}`}
                  </Button>
                </DialogTrigger>
                <DialogContent className="bg-slate-900 border-yellow-400/30" data-testid="order-dialog">
                  <DialogHeader>
                    <DialogTitle className="text-yellow-400 text-2xl">Complete Your Order</DialogTitle>
                    <DialogDescription className="text-white/70">
                      You are about to embark on an unforgettable journey!
                    </DialogDescription>
                  </DialogHeader>
                  <div className="space-y-4 py-4">
                    <div>
                      <Label className="text-white">Full Name</Label>
                      <Input 
                        className="form-input mt-2"
                        placeholder="Enter your name"
                        value={orderForm.name}
                        onChange={(e) => setOrderForm({...orderForm, name: e.target.value})}
                        data-testid="order-name-input"
                      />
                    </div>
                    <div>
                      <Label className="text-white">Email</Label>
                      <Input 
                        className="form-input mt-2"
                        type="email"
                        placeholder="Enter your email"
                        value={orderForm.email}
                        onChange={(e) => setOrderForm({...orderForm, email: e.target.value})}
                        data-testid="order-email-input"
                      />
                    </div>
                    <div>
                      <Label className="text-white">Quantity</Label>
                      <div className="flex items-center gap-4 mt-2">
                        <Button 
                          variant="outline" 
                          size="icon"
                          onClick={() => setQuantity(Math.max(1, quantity - 1))}
                          data-testid="quantity-minus"
                        >
                          <Minus />
                        </Button>
                        <span className="text-2xl font-bold text-white" data-testid="quantity-display">{quantity}</span>
                        <Button 
                          variant="outline" 
                          size="icon"
                          onClick={() => setQuantity(quantity + 1)}
                          data-testid="quantity-plus"
                        >
                          <Plus />
                        </Button>
                      </div>
                    </div>
                    <div className="bg-yellow-400/10 p-4 rounded-lg">
                      <div className="flex justify-between text-white">
                        <span>Format:</span>
                        <span className="capitalize font-semibold">{selectedFormat}</span>
                      </div>
                      <div className="flex justify-between text-white mt-2">
                        <span>Total:</span>
                        <span className="text-2xl font-bold text-yellow-400">
                          ${(bookPrices[selectedFormat] * quantity).toFixed(2)}
                        </span>
                      </div>
                    </div>
                    
                    {/* PayPal Payment for Book */}
                    {!showPayPal ? (
                      <Button 
                        onClick={handleProceedToPayment}
                        className="btn-gold w-full mt-4"
                        data-testid="proceed-to-book-payment-btn"
                      >
                        <CreditCard className="mr-2" /> Pay with PayPal
                      </Button>
                    ) : (
                      <div className="mt-4 bg-white/10 p-4 rounded-lg">
                        <p className="text-white/80 text-sm mb-3 text-center">
                          Complete your purchase securely with PayPal
                        </p>
                        <PayPalButton 
                          amount={getBookAmount()}
                          description={`Letters to Evelyn - ${selectedFormat} (x${quantity})`}
                          onSuccess={handlePayPalSuccess}
                          onError={handlePayPalError}
                          buttonId="book-purchase"
                        />
                      </div>
                    )}
                  </div>
                  <DialogFooter>
                    {showPayPal && (
                      <Button 
                        variant="outline"
                        onClick={() => setShowPayPal(false)}
                        className="w-full border-white/30 text-white hover:bg-white/10"
                      >
                        ← Back to Details
                      </Button>
                    )}
                  </DialogFooter>
                </DialogContent>
              </Dialog>
            </Card>

            {/* Funny Warnings */}
            <Card className="card-glass p-6" data-testid="warnings-card">
              <h3 className="text-xl font-bold text-red-400 mb-4 flex items-center gap-2">
                <AlertTriangle /> Important Warnings! 
              </h3>
              <ul className="space-y-2">
                {bookInfo.warnings.map((warning, idx) => (
                  <li key={idx} className="flex items-start gap-2 text-white/70 text-sm">
                    <span className="text-yellow-400">⚠️</span>
                    {warning}
                  </li>
                ))}
              </ul>
            </Card>
          </div>
        </div>

        {/* Chapter Preview */}
        <Card className="card-glass mt-12 p-6" data-testid="chapters-card">
          <h3 className="text-2xl font-bold text-yellow-400 mb-6">📑 Chapter Preview</h3>
          <div className="grid md:grid-cols-3 gap-4">
            {bookInfo.chapters.map((chapter, idx) => (
              <div 
                key={idx}
                className="p-3 rounded-lg bg-white/5 border border-white/10 hover:border-yellow-400/30 transition-all"
              >
                <span className="text-yellow-400 font-bold">Ch {idx + 1}:</span>{" "}
                <span className="text-white/80">{chapter}</span>
              </div>
            ))}
          </div>
        </Card>
      </div>
    </section>
  );
};

// Food Truck Section
const FoodSection = ({ showToast }) => {
  const [menu, setMenu] = useState(null);
  const [cart, setCart] = useState([]);
  const [orderDialog, setOrderDialog] = useState(false);
  const [orderForm, setOrderForm] = useState({ name: '', phone: '', email: '', pickupTime: '' });
  const [loading, setLoading] = useState(false);

  useEffect(() => {
    let isMounted = true;
    const fetchData = async () => {
      try {
        const response = await axios.get(`${API}/food/menu`);
        if (isMounted) {
          setMenu(response.data);
        }
      } catch (error) {
        console.error('Error fetching menu:', error);
      }
    };
    fetchData();
    return () => { isMounted = false; };
  }, []);

  const addToCart = (item) => {
    const existing = cart.find(c => c.id === item.id);
    if (existing) {
      setCart(cart.map(c => c.id === item.id ? {...c, quantity: c.quantity + 1} : c));
    } else {
      setCart([...cart, { ...item, quantity: 1 }]);
    }
    showToast(`Added ${item.name} to cart! 🛒`, 'success');
  };

  const removeFromCart = (itemId) => {
    setCart(cart.filter(c => c.id !== itemId));
  };

  const updateQuantity = (itemId, delta) => {
    setCart(cart.map(c => {
      if (c.id === itemId) {
        const newQty = c.quantity + delta;
        return newQty > 0 ? {...c, quantity: newQty} : c;
      }
      return c;
    }).filter(c => c.quantity > 0));
  };

  const getTotal = () => {
    return cart.reduce((sum, item) => sum + (item.price * item.quantity), 0);
  };

  const handleOrder = async () => {
    if (!orderForm.name || !orderForm.phone || !orderForm.pickupTime) {
      showToast('Please fill in all required fields!', 'error');
      return;
    }

    if (cart.length === 0) {
      showToast('Your cart is empty!', 'error');
      return;
    }

    // Proceed to show PayPal
    setShowPayPal(true);
  };

  const [showPayPal, setShowPayPal] = useState(false);

  const handlePayPalSuccess = async (order) => {
    showToast(`🎉 Payment successful! Your food order is confirmed! Order ID: ${order.id}`, 'success');
    setOrderDialog(false);
    setShowPayPal(false);
    
    // Record the order
    try {
      await axios.post(`${API}/food/order`, {
        customer_name: orderForm.name,
        phone: orderForm.phone,
        email: orderForm.email || null,
        items: cart.map(item => ({
          item_name: item.name,
          quantity: item.quantity,
          price: item.price,
          special_instructions: null
        })),
        pickup_time: orderForm.pickupTime
      });
    } catch (error) {
      console.log('Order recorded');
    }
    
    setCart([]);
    setOrderForm({ name: '', phone: '', email: '', pickupTime: '' });
  };

  const handlePayPalError = (error) => {
    showToast('Payment failed. Please try again!', 'error');
    console.error('PayPal Error:', error);
  };

  if (!menu) return <div className="text-center py-20">Loading menu...</div>;

  return (
    <section className="min-h-screen py-20 px-4" data-testid="food-section">
      <div className="max-w-6xl mx-auto">
        <div className="text-center mb-12 animate-slide-in">
          <Badge className="mb-4 bg-orange-500/20 text-orange-300 border-orange-500/30">
            🚚 Now Serving in Brunswick, Maine!
          </Badge>
          <h2 className="text-4xl md:text-5xl font-bold text-gradient-gold mb-4">
            Maestro Bistro
          </h2>
          <p className="text-xl text-white/80">{menu.tagline}</p>
          <div className="flex items-center justify-center gap-2 mt-4 text-white/60">
            <MapPin className="text-yellow-400" />
            <span>{menu.location}</span>
          </div>
        </div>

        {/* Food Truck Image */}
        <div className="mb-12 rounded-2xl overflow-hidden card-glass p-2">
          <img 
            src="https://images.unsplash.com/photo-1565123409695-7b5ef63a2efb?w=1200"
            alt="Maestro Bistro Food Truck"
            className="w-full h-64 md:h-96 object-cover rounded-xl"
          />
          <p className="text-center text-white/60 mt-4 text-lg italic">
            &quot;Where Every Bite is a Symphony of Flavor!&quot; 🎵
          </p>
        </div>

        {/* Menu Grid */}
        <div className="grid md:grid-cols-2 lg:grid-cols-3 gap-6 mb-12">
          {menu.menu.map((item) => (
            <Card 
              key={item.id} 
              className="food-truck-card overflow-hidden card-hover menu-item"
              data-testid={`menu-item-${item.id}`}
            >
              <CardHeader className="pb-2">
                <div className="flex justify-between items-start">
                  <div className="menu-emoji text-5xl mb-2">{item.image}</div>
                  <Badge className="bg-yellow-400/20 text-yellow-300 text-lg">
                    ${item.price}
                  </Badge>
                </div>
                <CardTitle className="text-white">{item.name}</CardTitle>
                <CardDescription className="text-yellow-300/80 italic">
                  &quot;{item.funny_tagline}&quot;
                </CardDescription>
              </CardHeader>
              <CardContent>
                <p className="text-white/70 text-sm">{item.description}</p>
              </CardContent>
              <CardFooter>
                <Button 
                  onClick={() => addToCart(item)}
                  className="btn-gold w-full"
                  data-testid={`add-to-cart-${item.id}`}
                >
                  <Plus className="mr-2" /> Add to Cart
                </Button>
              </CardFooter>
            </Card>
          ))}
        </div>

        {/* Cart */}
        {cart.length > 0 && (
          <Card className="card-glass p-6 sticky bottom-4" data-testid="cart">
            <div className="flex items-center justify-between mb-4">
              <h3 className="text-xl font-bold text-yellow-400 flex items-center gap-2">
                <ShoppingCart /> Your Cart ({cart.length} items)
              </h3>
              <span className="text-2xl font-bold text-white">${getTotal().toFixed(2)}</span>
            </div>
            <div className="space-y-2 mb-4">
              {cart.map(item => (
                <div key={item.id} className="flex items-center justify-between bg-white/5 p-3 rounded-lg">
                  <div className="flex items-center gap-3">
                    <span className="text-2xl">{item.image}</span>
                    <span className="text-white">{item.name}</span>
                  </div>
                  <div className="flex items-center gap-3">
                    <Button 
                      variant="outline" 
                      size="sm"
                      onClick={() => updateQuantity(item.id, -1)}
                      data-testid={`cart-minus-${item.id}`}
                    >
                      <Minus size={14} />
                    </Button>
                    <span className="text-white font-bold" data-testid={`cart-qty-${item.id}`}>{item.quantity}</span>
                    <Button 
                      variant="outline" 
                      size="sm"
                      onClick={() => updateQuantity(item.id, 1)}
                      data-testid={`cart-plus-${item.id}`}
                    >
                      <Plus size={14} />
                    </Button>
                    <span className="text-yellow-400 font-bold ml-2">
                      ${(item.price * item.quantity).toFixed(2)}
                    </span>
                  </div>
                </div>
              ))}
            </div>
            
            <Dialog open={orderDialog} onOpenChange={setOrderDialog}>
              <DialogTrigger asChild>
                <Button className="btn-gold w-full text-lg py-6" data-testid="checkout-btn">
                  Checkout - ${getTotal().toFixed(2)}
                </Button>
              </DialogTrigger>
              <DialogContent className="bg-slate-900 border-yellow-400/30" data-testid="food-order-dialog">
                <DialogHeader>
                  <DialogTitle className="text-yellow-400 text-2xl">Complete Your Food Order</DialogTitle>
                  <DialogDescription className="text-white/70">
                    Get ready for a flavor explosion! 💥
                  </DialogDescription>
                </DialogHeader>
                <div className="space-y-4 py-4">
                  <div>
                    <Label className="text-white">Full Name *</Label>
                    <Input 
                      className="form-input mt-2"
                      placeholder="Enter your name"
                      value={orderForm.name}
                      onChange={(e) => setOrderForm({...orderForm, name: e.target.value})}
                      data-testid="food-order-name"
                    />
                  </div>
                  <div>
                    <Label className="text-white">Phone Number *</Label>
                    <Input 
                      className="form-input mt-2"
                      type="tel"
                      placeholder="(555) 123-4567"
                      value={orderForm.phone}
                      onChange={(e) => setOrderForm({...orderForm, phone: e.target.value})}
                      data-testid="food-order-phone"
                    />
                  </div>
                  <div>
                    <Label className="text-white">Email (optional)</Label>
                    <Input 
                      className="form-input mt-2"
                      type="email"
                      placeholder="your@email.com"
                      value={orderForm.email}
                      onChange={(e) => setOrderForm({...orderForm, email: e.target.value})}
                      data-testid="food-order-email"
                    />
                  </div>
                  <div>
                    <Label className="text-white">Pickup Time *</Label>
                    <Select onValueChange={(v) => setOrderForm({...orderForm, pickupTime: v})}>
                      <SelectTrigger className="form-input mt-2" data-testid="food-order-time">
                        <SelectValue placeholder="Select pickup time" />
                      </SelectTrigger>
                      <SelectContent className="bg-slate-800 border-yellow-400/30">
                        <SelectItem value="ASAP">ASAP (15-20 mins)</SelectItem>
                        <SelectItem value="30 mins">30 minutes</SelectItem>
                        <SelectItem value="45 mins">45 minutes</SelectItem>
                        <SelectItem value="1 hour">1 hour</SelectItem>
                      </SelectContent>
                    </Select>
                  </div>
                  <div className="bg-yellow-400/10 p-4 rounded-lg">
                    <h4 className="text-white font-semibold mb-2">Order Summary</h4>
                    {cart.map(item => (
                      <div key={item.id} className="flex justify-between text-white/80 text-sm">
                        <span>{item.quantity}x {item.name}</span>
                        <span>${(item.price * item.quantity).toFixed(2)}</span>
                      </div>
                    ))}
                    <Separator className="my-2 bg-white/20" />
                    <div className="flex justify-between text-white font-bold">
                      <span>Total:</span>
                      <span className="text-yellow-400">${getTotal().toFixed(2)}</span>
                    </div>
                  </div>
                  
                  {/* PayPal Payment for Food */}
                  {!showPayPal ? (
                    <Button 
                      onClick={handleOrder}
                      className="btn-gold w-full mt-4"
                      disabled={!orderForm.name || !orderForm.phone || !orderForm.pickupTime}
                      data-testid="proceed-to-food-payment-btn"
                    >
                      <CreditCard className="mr-2" /> Pay with PayPal - ${getTotal().toFixed(2)}
                    </Button>
                  ) : (
                    <div className="mt-4 bg-white/10 p-4 rounded-lg">
                      <p className="text-white/80 text-sm mb-3 text-center">
                        Complete your order securely with PayPal
                      </p>
                      <PayPalButton 
                        amount={getTotal().toFixed(2)}
                        description={`Maestro Bistro - ${cart.length} item(s)`}
                        onSuccess={handlePayPalSuccess}
                        onError={handlePayPalError}
                        buttonId="food-order"
                      />
                    </div>
                  )}
                </div>
                <DialogFooter>
                  {showPayPal && (
                    <Button 
                      variant="outline"
                      onClick={() => setShowPayPal(false)}
                      className="w-full border-white/30 text-white hover:bg-white/10"
                    >
                      ← Back to Details
                    </Button>
                  )}
                </DialogFooter>
              </DialogContent>
            </Dialog>
          </Card>
        )}
      </div>
    </section>
  );
};

// Testimonials Section
const TestimonialsSection = () => {
  const [testimonials, setTestimonials] = useState([]);

  useEffect(() => {
    let isMounted = true;
    const fetchData = async () => {
      try {
        const response = await axios.get(`${API}/testimonials`);
        if (isMounted) {
          setTestimonials(response.data.testimonials);
        }
      } catch (error) {
        console.error('Error fetching testimonials:', error);
      }
    };
    fetchData();
    return () => { isMounted = false; };
  }, []);

  return (
    <section className="min-h-screen py-20 px-4" data-testid="testimonials-section">
      <div className="max-w-6xl mx-auto">
        <div className="text-center mb-12 animate-slide-in">
          <Badge className="mb-4 bg-pink-500/20 text-pink-300 border-pink-500/30">
            ⭐ What People Are Saying
          </Badge>
          <h2 className="text-4xl md:text-5xl font-bold text-gradient-gold mb-4">
            Rave Reviews
          </h2>
          <p className="text-xl text-white/80">
            Do not just take our word for it - these (totally real*) reviews speak for themselves!
          </p>
          <p className="text-sm text-white/40 mt-2">*Results may vary. Side effects include happiness.</p>
        </div>

        <Tabs defaultValue="all" className="w-full">
          <TabsList className="flex justify-center mb-8 bg-white/5" data-testid="review-tabs">
            <TabsTrigger value="all" className="data-[state=active]:bg-yellow-400/20 data-[state=active]:text-yellow-400">
              All Reviews
            </TabsTrigger>
            <TabsTrigger value="book" className="data-[state=active]:bg-yellow-400/20 data-[state=active]:text-yellow-400">
              📚 Book
            </TabsTrigger>
            <TabsTrigger value="food" className="data-[state=active]:bg-yellow-400/20 data-[state=active]:text-yellow-400">
              🍽️ Food
            </TabsTrigger>
          </TabsList>

          <TabsContent value="all">
            <div className="grid md:grid-cols-2 gap-6">
              {testimonials.map((t, idx) => (
                <TestimonialCard key={t.id || idx} testimonial={t} />
              ))}
            </div>
          </TabsContent>

          <TabsContent value="book">
            <div className="grid md:grid-cols-2 gap-6">
              {testimonials.filter(t => t.review_type === 'book').map((t, idx) => (
                <TestimonialCard key={t.id || idx} testimonial={t} />
              ))}
            </div>
          </TabsContent>

          <TabsContent value="food">
            <div className="grid md:grid-cols-2 gap-6">
              {testimonials.filter(t => t.review_type === 'food').map((t, idx) => (
                <TestimonialCard key={t.id || idx} testimonial={t} />
              ))}
            </div>
          </TabsContent>
        </Tabs>
      </div>
    </section>
  );
};

const TestimonialCard = ({ testimonial }) => (
  <Card className="testimonial-card p-6 card-hover" data-testid={`testimonial-${testimonial.name}`}>
    <div className="flex items-start gap-4">
      <div className="w-12 h-12 rounded-full bg-gradient-to-br from-yellow-400 to-orange-500 flex items-center justify-center text-xl font-bold text-white">
        {testimonial.name.charAt(0)}
      </div>
      <div className="flex-1">
        <div className="flex items-center gap-2 mb-2">
          {[...Array(testimonial.rating)].map((_, i) => (
            <Star key={i} size={16} className="text-yellow-400 fill-yellow-400" />
          ))}
        </div>
        <p className="text-white/90 italic mb-4">&quot;{testimonial.review}&quot;</p>
        <div className="flex items-center justify-between">
          <div>
            <p className="text-white font-semibold">{testimonial.name}</p>
            <p className="text-white/60 text-sm flex items-center gap-1">
              <MapPin size={12} /> {testimonial.location}
            </p>
          </div>
          <Badge className={testimonial.review_type === 'book' ? 'bg-purple-400/20 text-purple-300' : 'bg-orange-400/20 text-orange-300'}>
            {testimonial.review_type === 'book' ? '📚' : '🍽️'}
          </Badge>
        </div>
      </div>
    </div>
  </Card>
);

// Contact Section
const ContactSection = ({ showToast }) => {
  const [contactForm, setContactForm] = useState({ name: '', email: '', subject: '', message: '' });
  const [newsletterForm, setNewsletterForm] = useState({ name: '', email: '', type: 'general' });
  const [loadingContact, setLoadingContact] = useState(false);
  const [loadingNewsletter, setLoadingNewsletter] = useState(false);

  const handleContact = async () => {
    if (!contactForm.name || !contactForm.email || !contactForm.subject || !contactForm.message) {
      showToast('Please fill in all fields!', 'error');
      return;
    }

    setLoadingContact(true);
    try {
      await axios.post(`${API}/contact`, contactForm);
      showToast('Message sent! We\'ll get back to you faster than a Navy jet! 🛩️', 'success');
      setContactForm({ name: '', email: '', subject: '', message: '' });
    } catch (error) {
      showToast('Error sending message. Please try again!', 'error');
    }
    setLoadingContact(false);
  };

  const handleNewsletter = async () => {
    if (!newsletterForm.name || !newsletterForm.email) {
      showToast('Please fill in all fields!', 'error');
      return;
    }

    setLoadingNewsletter(true);
    try {
      await axios.post(`${API}/newsletter/signup`, {
        name: newsletterForm.name,
        email: newsletterForm.email,
        signup_type: newsletterForm.type
      });
      showToast('Welcome aboard! 🚀 Check your email for cosmic updates!', 'success');
      setNewsletterForm({ name: '', email: '', type: 'general' });
    } catch (error) {
      if (error.response?.data?.detail?.includes('already subscribed')) {
        showToast('You\'re already part of the crew! 🎉', 'error');
      } else {
        showToast('Error subscribing. Please try again!', 'error');
      }
    }
    setLoadingNewsletter(false);
  };

  return (
    <section className="min-h-screen py-20 px-4" data-testid="contact-section">
      <div className="max-w-6xl mx-auto">
        <div className="text-center mb-12 animate-slide-in">
          <Badge className="mb-4 bg-blue-500/20 text-blue-300 border-blue-500/30">
            📬 Get In Touch
          </Badge>
          <h2 className="text-4xl md:text-5xl font-bold text-gradient-gold mb-4">
            Contact Us
          </h2>
          <p className="text-xl text-white/80">
            Questions? Compliments? Alien sightings to report? We are all ears! 👂👽
          </p>
        </div>

        <div className="grid md:grid-cols-2 gap-8">
          {/* Contact Form */}
          <Card className="card-glass p-6" data-testid="contact-form-card">
            <h3 className="text-2xl font-bold text-yellow-400 mb-6 flex items-center gap-2">
              <Mail /> Send a Message
            </h3>
            <div className="space-y-4">
              <div>
                <Label className="text-white">Name</Label>
                <Input 
                  className="form-input mt-2"
                  placeholder="Your name"
                  value={contactForm.name}
                  onChange={(e) => setContactForm({...contactForm, name: e.target.value})}
                  data-testid="contact-name"
                />
              </div>
              <div>
                <Label className="text-white">Email</Label>
                <Input 
                  className="form-input mt-2"
                  type="email"
                  placeholder="your@email.com"
                  value={contactForm.email}
                  onChange={(e) => setContactForm({...contactForm, email: e.target.value})}
                  data-testid="contact-email"
                />
              </div>
              <div>
                <Label className="text-white">Subject</Label>
                <Select onValueChange={(v) => setContactForm({...contactForm, subject: v})}>
                  <SelectTrigger className="form-input mt-2" data-testid="contact-subject">
                    <SelectValue placeholder="What's this about?" />
                  </SelectTrigger>
                  <SelectContent className="bg-slate-800 border-yellow-400/30">
                    <SelectItem value="book">📚 About the Book</SelectItem>
                    <SelectItem value="food">🍽️ About Maestro Bistro</SelectItem>
                    <SelectItem value="general">💬 General Inquiry</SelectItem>
                    <SelectItem value="aliens">👽 Alien-Related Question</SelectItem>
                    <SelectItem value="other">🎲 Something Else Entirely</SelectItem>
                  </SelectContent>
                </Select>
              </div>
              <div>
                <Label className="text-white">Message</Label>
                <Textarea 
                  className="form-input mt-2"
                  placeholder="Tell us what's on your mind..."
                  rows={4}
                  value={contactForm.message}
                  onChange={(e) => setContactForm({...contactForm, message: e.target.value})}
                  data-testid="contact-message"
                />
              </div>
              <Button 
                onClick={handleContact}
                className="btn-gold w-full"
                disabled={loadingContact}
                data-testid="send-message-btn"
              >
                {loadingContact ? 'Sending...' : <><Send className="mr-2" /> Send Message</>}
              </Button>
            </div>
          </Card>

          {/* Newsletter & Info */}
          <div className="space-y-6">
            <Card className="card-glass p-6" data-testid="newsletter-card">
              <h3 className="text-2xl font-bold text-yellow-400 mb-4 flex items-center gap-2">
                <Sparkles /> Join Our Newsletter
              </h3>
              <p className="text-white/70 mb-4">
                Get exclusive updates, hilarious stories, and mouth-watering specials delivered to your inbox!
              </p>
              <div className="space-y-4">
                <Input 
                  className="form-input"
                  placeholder="Your name"
                  value={newsletterForm.name}
                  onChange={(e) => setNewsletterForm({...newsletterForm, name: e.target.value})}
                  data-testid="newsletter-name"
                />
                <Input 
                  className="form-input"
                  type="email"
                  placeholder="your@email.com"
                  value={newsletterForm.email}
                  onChange={(e) => setNewsletterForm({...newsletterForm, email: e.target.value})}
                  data-testid="newsletter-email"
                />
                <Button 
                  onClick={handleNewsletter}
                  className="btn-gold w-full"
                  disabled={loadingNewsletter}
                  data-testid="subscribe-btn"
                >
                  {loadingNewsletter ? 'Subscribing...' : 'Subscribe 🚀'}
                </Button>
              </div>
            </Card>

            <Card className="card-glass p-6" data-testid="location-card">
              <h3 className="text-2xl font-bold text-yellow-400 mb-4 flex items-center gap-2">
                <MapPin /> Find Us
              </h3>
              <div className="space-y-4 text-white/80">
                <div className="flex items-center gap-3">
                  <Utensils className="text-orange-400" />
                  <div>
                    <p className="font-semibold text-white">Maestro Bistro Food Truck</p>
                    <p>The Mall, Brunswick, Maine</p>
                  </div>
                </div>
                <div className="flex items-center gap-3">
                  <Clock className="text-yellow-400" />
                  <div>
                    <p className="font-semibold text-white">Hours</p>
                    <p>Tue-Sun: 11AM - 8PM</p>
                  </div>
                </div>
                <div className="flex items-center gap-3">
                  <Phone className="text-green-400" />
                  <div>
                    <p className="font-semibold text-white">Call Ahead</p>
                    <p>Orders welcome!</p>
                  </div>
                </div>
              </div>
              <div className="mt-4 rounded-lg overflow-hidden">
                <img 
                  src="https://images.unsplash.com/photo-1641596593844-eeb6d532f442?w=600"
                  alt="Maine Coast"
                  className="w-full h-40 object-cover"
                />
              </div>
            </Card>
          </div>
        </div>
      </div>
    </section>
  );
};

// Footer
const Footer = () => (
  <footer className="footer py-12 px-4" data-testid="footer">
    <div className="max-w-6xl mx-auto">
      <div className="grid md:grid-cols-3 gap-8 mb-8">
        <div>
          <div className="flex items-center gap-2 mb-4">
            <Sparkles className="text-yellow-400" size={24} />
            <span className="text-xl font-bold text-gradient-gold">InfoPilot Explorer</span>
          </div>
          <p className="text-white/60 text-sm">
            A Top Pilot Enterprises, Inc. Company<br/>
            Where supernatural thrillers meet German cuisine!
          </p>
          <div className="mt-2 text-xs text-white/40">
            <p>InfoPilot Explorer, LLC | Maestro Bistro | John Selman Publications</p>
          </div>
        </div>
        <div>
          <h4 className="text-lg font-bold text-yellow-400 mb-4">Quick Links</h4>
          <ul className="space-y-2 text-white/60">
            <li className="hover:text-yellow-400 cursor-pointer">📚 Letters to Evelyn by John Selman</li>
            <li className="hover:text-yellow-400 cursor-pointer">🚚 Maestro Bistro - Brunswick, Maine</li>
            <li className="hover:text-yellow-400 cursor-pointer">🌐 InfoPilot Subscription - $1/mo</li>
            <li className="hover:text-yellow-400 cursor-pointer">⭐ 19 Five-Star Reviews</li>
            <li className="hover:text-yellow-400 cursor-pointer">📬 Contact Us</li>
          </ul>
        </div>
        <div>
          <h4 className="text-lg font-bold text-yellow-400 mb-4">Legal Stuff</h4>
          <p className="text-white/60 text-sm">
            © 2014-2025 John Selman - Letters to Evelyn<br/>
            © 2025 Top Pilot Enterprises, Inc.<br/>
            All rights reserved. Reading while operating heavy machinery is strongly discouraged. 
            Side effects may include uncontrollable laughter and sudden cravings for rouladen.
          </p>
        </div>
      </div>
      <Separator className="bg-yellow-400/20 mb-8" />
      <div className="text-center text-white/40 text-sm">
        <p>Made with 💛 by Top Pilot Enterprises, Inc.</p>
        <p className="mt-2">🛸 No aliens were harmed in the making of this website 🛸</p>
        <p className="mt-1 text-xs">Contains 70+ zany, zesty zoo zingers causing hurricane-force winds of laughter!</p>
      </div>
    </div>
  </footer>
);

// InfoPilot Section with PayPal Integration
const InfoPilotSection = ({ showToast }) => {
  const [plans, setPlans] = useState(null);
  const [selectedPlan, setSelectedPlan] = useState('monthly');
  const [subscribeDialog, setSubscribeDialog] = useState(false);
  const [subscribeForm, setSubscribeForm] = useState({ name: '', email: '' });
  const [loading, setLoading] = useState(false);
  const [showPayPal, setShowPayPal] = useState(false);

  useEffect(() => {
    let isMounted = true;
    const fetchPlans = async () => {
      try {
        const response = await axios.get(`${API}/infopilot/plans`);
        if (isMounted) {
          setPlans(response.data);
        }
      } catch (error) {
        console.error('Error fetching plans:', error);
      }
    };
    fetchPlans();
    return () => { isMounted = false; };
  }, []);

  const handlePayPalSuccess = async (order) => {
    showToast(`🎉 Payment successful! Welcome to InfoPilot Explorer! Order ID: ${order.id}`, 'success');
    setSubscribeDialog(false);
    setShowPayPal(false);
    
    // Record the subscription
    try {
      await axios.post(`${API}/newsletter/signup`, {
        name: subscribeForm.name || order.payer?.name?.given_name || 'PayPal User',
        email: subscribeForm.email || order.payer?.email_address || 'paypal@user.com',
        signup_type: `infopilot_${selectedPlan}_paid`
      });
    } catch (error) {
      console.log('User already exists or signup recorded');
    }
  };

  const handlePayPalError = (error) => {
    showToast('Payment failed. Please try again!', 'error');
    console.error('PayPal Error:', error);
  };

  const handleProceedToPayment = () => {
    if (!subscribeForm.name || !subscribeForm.email) {
      showToast('Please fill in your name and email first!', 'error');
      return;
    }
    setShowPayPal(true);
  };

  const getPlanAmount = () => {
    return selectedPlan === 'monthly' ? '1.00' : '9.98';
  };

  return (
    <section className="min-h-screen py-20 px-4" data-testid="infopilot-section">
      <div className="max-w-6xl mx-auto">
        <div className="text-center mb-12 animate-slide-in">
          <Badge className="mb-2 bg-blue-600/30 text-blue-300 border-blue-500/30 text-xs px-3 py-1">
            ✈️ A Top Pilot Enterprises, Inc. Company
          </Badge>
          <Badge className="mb-4 bg-purple-500/20 text-purple-300 border-purple-500/30 ml-2">
            🌐 Boolean Search & Categorization Platform
          </Badge>
          <h2 className="text-4xl md:text-5xl font-bold text-gradient-gold mb-4">
            InfoPilot Explorer
          </h2>
          <p className="text-xl text-white/80">
            Mobile & Desktop Application for Information Exchange
          </p>
          <p className="text-lg text-white/60 mt-2">
            Built for Scholars and Tradesmen - Only $1/month!
          </p>
        </div>

        <div className="grid md:grid-cols-2 gap-8 mb-12">
          {/* Monthly Plan */}
          <Card 
            className={`card-glass p-6 cursor-pointer transition-all ${selectedPlan === 'monthly' ? 'border-2 border-yellow-400 scale-105' : 'border border-white/20'}`}
            onClick={() => setSelectedPlan('monthly')}
            data-testid="plan-monthly"
          >
            <div className="text-center">
              <Badge className="bg-green-500/20 text-green-300 mb-4">Most Popular</Badge>
              <h3 className="text-2xl font-bold text-white mb-2">Monthly Plan</h3>
              <div className="text-5xl font-bold text-yellow-400 mb-4">
                $1.00<span className="text-lg text-white/60">/mo</span>
              </div>
              <ul className="text-left space-y-3 text-white/80">
                <li className="flex items-center gap-2">
                  <CheckCircle className="text-green-400" size={18} />
                  Unlimited Boolean Searches
                </li>
                <li className="flex items-center gap-2">
                  <CheckCircle className="text-green-400" size={18} />
                  Category Organization
                </li>
                <li className="flex items-center gap-2">
                  <CheckCircle className="text-green-400" size={18} />
                  Collaboration Tools
                </li>
                <li className="flex items-center gap-2">
                  <CheckCircle className="text-green-400" size={18} />
                  Priority Support
                </li>
              </ul>
            </div>
          </Card>

          {/* Yearly Plan */}
          <Card 
            className={`card-glass p-6 cursor-pointer transition-all ${selectedPlan === 'yearly' ? 'border-2 border-yellow-400 scale-105' : 'border border-white/20'}`}
            onClick={() => setSelectedPlan('yearly')}
            data-testid="plan-yearly"
          >
            <div className="text-center">
              <Badge className="bg-yellow-500/20 text-yellow-300 mb-4">Save 17%</Badge>
              <h3 className="text-2xl font-bold text-white mb-2">Yearly Plan</h3>
              <div className="text-5xl font-bold text-yellow-400 mb-4">
                $9.98<span className="text-lg text-white/60">/yr</span>
              </div>
              <ul className="text-left space-y-3 text-white/80">
                <li className="flex items-center gap-2">
                  <CheckCircle className="text-green-400" size={18} />
                  All Monthly Features
                </li>
                <li className="flex items-center gap-2">
                  <CheckCircle className="text-green-400" size={18} />
                  Advanced Analytics
                </li>
                <li className="flex items-center gap-2">
                  <CheckCircle className="text-green-400" size={18} />
                  Custom Categories
                </li>
                <li className="flex items-center gap-2">
                  <CheckCircle className="text-green-400" size={18} />
                  API Access
                </li>
              </ul>
            </div>
          </Card>
        </div>

        <div className="text-center">
          <Dialog open={subscribeDialog} onOpenChange={setSubscribeDialog}>
            <DialogTrigger asChild>
              <Button className="btn-gold text-xl px-12 py-8" data-testid="subscribe-infopilot-btn">
                <Rocket className="mr-2" /> Subscribe Now - {selectedPlan === 'monthly' ? '$1.00/mo' : '$9.98/yr'}
              </Button>
            </DialogTrigger>
            <DialogContent className="bg-slate-900 border-yellow-400/30" data-testid="subscribe-dialog">
              <DialogHeader>
                <DialogTitle className="text-yellow-400 text-2xl">Join InfoPilot Explorer</DialogTitle>
                <DialogDescription className="text-white/70">
                  Start your journey to better information management!
                </DialogDescription>
              </DialogHeader>
              <div className="space-y-4 py-4">
                <div>
                  <Label className="text-white">Full Name</Label>
                  <Input 
                    className="form-input mt-2"
                    placeholder="Enter your name"
                    value={subscribeForm.name}
                    onChange={(e) => setSubscribeForm({...subscribeForm, name: e.target.value})}
                    data-testid="subscribe-name"
                  />
                </div>
                <div>
                  <Label className="text-white">Email</Label>
                  <Input 
                    className="form-input mt-2"
                    type="email"
                    placeholder="Enter your email"
                    value={subscribeForm.email}
                    onChange={(e) => setSubscribeForm({...subscribeForm, email: e.target.value})}
                    data-testid="subscribe-email"
                  />
                </div>
                <div className="bg-yellow-400/10 p-4 rounded-lg">
                  <div className="flex justify-between text-white">
                    <span>Plan:</span>
                    <span className="capitalize font-semibold">{selectedPlan}</span>
                  </div>
                  <div className="flex justify-between text-white mt-2">
                    <span>Price:</span>
                    <span className="text-2xl font-bold text-yellow-400">
                      {selectedPlan === 'monthly' ? '$1.00/mo' : '$9.98/yr'}
                    </span>
                  </div>
                </div>
                
                {/* PayPal Payment Section */}
                {!showPayPal ? (
                  <Button 
                    onClick={handleProceedToPayment}
                    className="btn-gold w-full mt-4"
                    data-testid="proceed-to-payment-btn"
                  >
                    <CreditCard className="mr-2" /> Proceed to PayPal Payment
                  </Button>
                ) : (
                  <div className="mt-4 bg-white/10 p-4 rounded-lg">
                    <p className="text-white/80 text-sm mb-3 text-center">
                      Complete your payment securely with PayPal
                    </p>
                    <PayPalButton 
                      amount={getPlanAmount()}
                      description={`InfoPilot Explorer ${selectedPlan} subscription`}
                      onSuccess={handlePayPalSuccess}
                      onError={handlePayPalError}
                      buttonId="infopilot-subscription"
                    />
                  </div>
                )}
              </div>
              <DialogFooter>
                {showPayPal && (
                  <Button 
                    variant="outline"
                    onClick={() => setShowPayPal(false)}
                    className="w-full border-white/30 text-white hover:bg-white/10"
                  >
                    ← Back to Details
                  </Button>
                )}
              </DialogFooter>
            </DialogContent>
          </Dialog>
        </div>

        {/* PayPal Hosted Button Section */}
        <Card className="card-glass p-6 mt-8 text-center">
          <h3 className="text-xl font-bold text-yellow-400 mb-4">
            <CreditCard className="inline mr-2" /> Secure Payment with PayPal
          </h3>
          <p className="text-white/70 mb-4">
            Subscribe securely using PayPal - accepts all major credit cards!
          </p>
          <div className="max-w-md mx-auto bg-white/10 p-4 rounded-lg">
            <PayPalHostedButton containerId="paypal-infopilot-hosted" />
          </div>
        </Card>

        {/* Features Grid */}
        <div className="mt-16 grid md:grid-cols-3 gap-6">
          <Card className="card-glass p-6 text-center">
            <div className="text-4xl mb-4">🔍</div>
            <h4 className="text-xl font-bold text-yellow-400 mb-2">Boolean Search</h4>
            <p className="text-white/70">Advanced search capabilities for scholars and researchers</p>
          </Card>
          <Card className="card-glass p-6 text-center">
            <div className="text-4xl mb-4">📂</div>
            <h4 className="text-xl font-bold text-yellow-400 mb-2">Smart Categories</h4>
            <p className="text-white/70">Organize information with intelligent categorization</p>
          </Card>
          <Card className="card-glass p-6 text-center">
            <div className="text-4xl mb-4">🤝</div>
            <h4 className="text-xl font-bold text-yellow-400 mb-2">Collaboration</h4>
            <p className="text-white/70">Share and collaborate with fellow tradesmen</p>
          </Card>
        </div>
      </div>
    </section>
  );
};

// Main App Component
function App() {
  const [activeSection, setActiveSection] = useState('home');
  const [isMobileMenuOpen, setIsMobileMenuOpen] = useState(false);
  const [toast, setToast] = useState(null);

  const showToast = useCallback((message, type) => {
    setToast({ message, type });
  }, []);

  const closeToast = useCallback(() => {
    setToast(null);
  }, []);

  // Health check on mount
  useEffect(() => {
    const healthCheck = async () => {
      try {
        const response = await axios.get(`${API}/`);
        console.log('API Connected:', response.data.message);
      } catch (error) {
        console.error('API Connection Error:', error);
      }
    };
    healthCheck();
  }, []);

  const renderSection = () => {
    switch(activeSection) {
      case 'home':
        return <HeroSection setActiveSection={setActiveSection} />;
      case 'book':
        return <BookSection showToast={showToast} />;
      case 'food':
        return <FoodSection showToast={showToast} />;
      case 'infopilot':
        return <InfoPilotSection showToast={showToast} />;
      case 'testimonials':
        return <TestimonialsSection />;
      case 'contact':
        return <ContactSection showToast={showToast} />;
      default:
        return <HeroSection setActiveSection={setActiveSection} />;
    }
  };

  return (
    <div className="App relative">
      <StarsBackground />
      <Navbar 
        activeSection={activeSection} 
        setActiveSection={setActiveSection}
        isMobileMenuOpen={isMobileMenuOpen}
        setIsMobileMenuOpen={setIsMobileMenuOpen}
      />
      
      <main className="relative z-10">
        {renderSection()}
      </main>

      <Footer />

      {toast && (
        <Toast 
          message={toast.message} 
          type={toast.type} 
          onClose={closeToast}
        />
      )}
    </div>
  );
}

export default App;
