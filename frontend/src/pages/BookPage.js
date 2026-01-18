import React, { useState } from 'react';
import axios from 'axios';
import StarsBackground from '../components/StarsBackground';
import { Card } from '../components/ui/card';
import { Button } from '../components/ui/button';
import { Badge } from '../components/ui/badge';
import { Book, Star, ExternalLink, CreditCard, Loader2 } from 'lucide-react';
import { API, AMAZON_BOOK_LINK } from '../utils/api';
import { useToast } from '../context/ToastContext';

const BookPage = () => {
  const [loading, setLoading] = useState(false);
  const showToast = useToast();

  const handleStripeCheckout = async () => {
    setLoading(true);
    try {
      const response = await axios.post(`${API}/stripe/create-checkout`, {
        package_type: 'book',
        origin_url: window.location.origin
      });
      
      if (response.data.checkout_url) {
        window.location.href = response.data.checkout_url;
      }
    } catch (err) {
      showToast(err.response?.data?.detail || 'Failed to start checkout', 'error');
    } finally {
      setLoading(false);
    }
  };

  return (
    <div className="min-h-screen pt-20 px-4">
      <StarsBackground />
      <div className="max-w-4xl mx-auto">
        <Card className="card-glass p-8">
          <div className="text-center mb-8">
            <Badge className="mb-4 bg-purple-500/20 text-purple-300">A True Story</Badge>
            <h1 className="text-4xl font-bold text-gradient-gold mb-2">Letters to Evelyn</h1>
            <p className="text-white/60">A True Supernatural Thriller Comedy by John Selman</p>
          </div>
          
          <div className="grid md:grid-cols-2 gap-8">
            <div>
              <div className="bg-gradient-to-br from-purple-900/50 to-blue-900/50 rounded-xl p-8 text-center">
                <Book className="mx-auto text-purple-400 mb-4" size={80} />
                <div className="flex flex-wrap justify-center gap-2 mb-4">
                  {['Supernatural', 'Thriller', 'Comedy', 'Navy Memoir'].map(g => (
                    <Badge key={g} className="bg-white/10">{g}</Badge>
                  ))}
                </div>
                <div className="mt-4 p-4 bg-white/5 rounded-lg">
                  <p className="text-3xl font-bold text-gradient-gold">$9.98</p>
                  <p className="text-white/50 text-sm">Digital eBook</p>
                </div>
              </div>
            </div>
            
            <div className="space-y-4">
              <h3 className="text-xl font-bold text-white">About the Book</h3>
              <p className="text-white/70">Based on true events, this supernatural thriller comedy follows the incredible journey of survival, faith, and the unexplainable.</p>
              
              <div className="bg-white/5 rounded-lg p-4">
                <div className="flex items-center gap-2 mb-2">
                  <Star className="text-yellow-400" size={20} />
                  <span className="text-white font-bold">5 Stars</span>
                  <span className="text-white/50">- Readers Favorite</span>
                </div>
                <p className="text-white/60 text-sm italic">&ldquo;An exceptional blend of supernatural elements with genuine humor...&rdquo;</p>
              </div>
              
              <div className="flex flex-col gap-3">
                <a href={AMAZON_BOOK_LINK} target="_blank" rel="noopener noreferrer" className="block">
                  <Button className="w-full bg-orange-500 hover:bg-orange-400" data-testid="amazon-book-btn">
                    <ExternalLink className="mr-2" size={16} /> Buy on Amazon
                  </Button>
                </a>
                <Button 
                  onClick={handleStripeCheckout} 
                  className="w-full btn-gold"
                  disabled={loading}
                  data-testid="stripe-book-btn"
                >
                  {loading ? (
                    <><Loader2 className="mr-2 animate-spin" size={16} /> Processing...</>
                  ) : (
                    <><CreditCard className="mr-2" size={16} /> Buy with Card - $9.98</>
                  )}
                </Button>
                <p className="text-center text-white/40 text-xs">Secure payment powered by Stripe</p>
              </div>
            </div>
          </div>
        </Card>
      </div>
    </div>
  );
};
export default BookPage;
