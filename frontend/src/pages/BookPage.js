import React from 'react';
import StarsBackground from '../components/StarsBackground';
import { Card } from '../components/ui/card';
import { Button } from '../components/ui/button';
import { Badge } from '../components/ui/badge';
import { Book, Star, ExternalLink } from 'lucide-react';
import { AMAZON_BOOK_LINK, PAYPAL_BOOK_LINK } from '../utils/api';

const BookPage = () => {
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
                <div className="flex justify-center gap-2 mb-4">
                  {['Supernatural', 'Thriller', 'Comedy', 'Navy Memoir'].map(g => (
                    <Badge key={g} className="bg-white/10">{g}</Badge>
                  ))}
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
                <p className="text-white/60 text-sm italic">An exceptional blend of supernatural elements with genuine humor...</p>
              </div>
              
              <div className="flex gap-4">
                <a href={AMAZON_BOOK_LINK} target="_blank" rel="noopener noreferrer" className="flex-1">
                  <Button className="w-full bg-orange-500 hover:bg-orange-400">
                    <ExternalLink className="mr-2" size={16} /> Amazon
                  </Button>
                </a>
                <a href={PAYPAL_BOOK_LINK} target="_blank" rel="noopener noreferrer" className="flex-1">
                  <Button className="w-full btn-gold">
                    <ExternalLink className="mr-2" size={16} /> PayPal
                  </Button>
                </a>
              </div>
            </div>
          </div>
        </Card>
      </div>
    </div>
  );
};
export default BookPage;
