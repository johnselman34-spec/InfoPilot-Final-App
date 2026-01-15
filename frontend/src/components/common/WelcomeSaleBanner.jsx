/**
 * Welcome Sale Banner Component
 * Promotes the book on various pages
 */
import React from 'react';
import { useNavigate } from 'react-router-dom';
import { Book, Sparkles, ShoppingCart } from 'lucide-react';
import { useAuth } from '../../contexts/AuthContext';
import { IMAGES } from '../../utils/constants';

export const WelcomeSaleBanner = ({ onUpgrade, compact }) => {
  const { user } = useAuth();
  const navigate = useNavigate();
  
  // App is now free - promote the book instead
  if (compact) {
    return (
      <div className="p-3 bg-gradient-to-r from-pink-900/30 to-purple-900/30 rounded-lg border border-pink-500/30 flex items-center justify-between">
        <div className="flex items-center gap-3">
          <img src={IMAGES.bookCoverMain} alt="Letters to Evelyn" className="w-12 h-16 object-cover rounded shadow-lg" />
          <div>
            <p className="text-pink-400 font-mono text-sm font-bold">📚 NEW BOOK!</p>
            <p className="text-purple-300 font-mono text-xs">Letters to Evelyn - $2.99</p>
          </div>
        </div>
        <button onClick={() => navigate("/book")} className="px-4 py-2 bg-gradient-to-r from-pink-600 to-purple-600 text-white font-mono text-sm rounded hover:scale-105 transition-transform">
          GET BOOK
        </button>
      </div>
    );
  }
  
  return (
    <div className="p-6 bg-gradient-to-r from-pink-900/40 via-purple-900/40 to-blue-900/40 rounded-xl border-2 border-pink-500/50">
      <div className="flex items-center justify-center gap-3 mb-4">
        <Book className="w-8 h-8 text-pink-400" />
        <Sparkles className="w-6 h-6 text-yellow-400 animate-pulse" />
      </div>
      <div className="text-center">
        <div className="bg-gradient-to-r from-pink-500 to-purple-500 text-white px-4 py-1 rounded-full text-sm font-bold inline-block mb-3">📖 FEATURED BOOK</div>
        <h3 className="text-2xl font-bold text-transparent bg-clip-text bg-gradient-to-r from-pink-400 to-purple-400 font-mono mb-2">LETTERS TO EVELYN</h3>
        <p className="text-purple-300/80 font-mono text-sm mb-1">A True Supernatural Thriller Comedy</p>
        <p className="text-pink-300 font-mono text-lg font-bold">Only $2.99</p>
        <p className="text-yellow-400 font-mono text-xs mb-4">⭐⭐⭐⭐⭐ 19 Five-Star Reviews</p>
        <button onClick={() => navigate("/book")} className="px-8 py-3 bg-gradient-to-r from-pink-600 via-purple-600 to-blue-600 text-white font-bold font-mono tracking-wider rounded-lg hover:scale-105 transition-transform flex items-center justify-center gap-2 mx-auto">
          <ShoppingCart className="w-5 h-5" /> VIEW BOOK
        </button>
      </div>
    </div>
  );
};

export default WelcomeSaleBanner;
