/**
 * Book Sales Banner Component
 * Multi-variant promotional banner for "Letters to Evelyn"
 */
import React, { useState, useEffect } from 'react';
import { Star, ShoppingCart, Gift } from 'lucide-react';
import { IMAGES, BOOK_INFO } from '../../utils/constants';

export const BookSalesBanner = ({ variant = "full" }) => {
  const [currentImage, setCurrentImage] = useState(0);
  const [currentQuote, setCurrentQuote] = useState(0);
  const bookImages = [IMAGES.bookCoverMain, IMAGES.bookCover1, IMAGES.bookCover2, IMAGES.bookCover3, IMAGES.bookCover4];
  
  // Hilarious taglines that rotate
  const funnyTaglines = [
    "The Navy Taught Me to Fly Jets. The Universe Taught Me Everything Else.",
    "Get yourself giggling in disoriented, stupefying hee-haw laughter!",
    "Hurricane-force winds of laughter from the most skeptical of minds!",
    "Finally, an easy-to-read novella that flows - you won't be able to put it down!",
    "50+ zingers in succession. Bat-shit insane? Maybe. Unforgettable? Definitely.",
    "Written by a U.S. Naval Officer who graduated FIRST in his class!"
  ];
  
  useEffect(() => {
    const timer = setInterval(() => {
      setCurrentImage((prev) => (prev + 1) % bookImages.length);
    }, 4000);
    return () => clearInterval(timer);
  }, [bookImages.length]);
  
  useEffect(() => {
    const quoteTimer = setInterval(() => {
      setCurrentQuote((prev) => (prev + 1) % funnyTaglines.length);
    }, 6000);
    return () => clearInterval(quoteTimer);
  }, [funnyTaglines.length]);
  
  const openAmazon = () => window.open(BOOK_INFO.amazonUrl, '_blank');
  
  // Mini variant for sidebars and small spaces
  if (variant === "mini") {
    return (
      <div className="bg-gradient-to-r from-pink-500/20 to-purple-500/20 border border-pink-500/50 rounded-lg p-3 cursor-pointer hover:scale-[1.02] transition-transform" onClick={openAmazon}>
        <p className="text-pink-400 font-mono text-xs text-center font-bold">
          📚 NEW: Letters to Evelyn
        </p>
        <p className="text-purple-400/60 font-mono text-xs text-center">Only $2.99!</p>
        <p className="text-yellow-400/80 font-mono text-[10px] text-center mt-1">⭐⭐⭐⭐⭐ 19 Reviews</p>
      </div>
    );
  }
  
  if (variant === "compact") {
    return (
      <div className="bg-gradient-to-r from-purple-900/40 to-blue-900/40 border border-purple-500/50 rounded-lg p-4 cursor-pointer hover:scale-[1.02] transition-transform" onClick={openAmazon}>
        <div className="flex items-center gap-4">
          <img src={IMAGES.bookCoverMain} alt="Letters to Evelyn" className="w-20 h-28 object-cover rounded-lg shadow-lg shadow-purple-500/30" />
          <div className="flex-1">
            <div className="flex items-center gap-2">
              <h3 className="text-pink-400 font-mono font-bold">LETTERS TO EVELYN</h3>
              <div className="flex">
                {[...Array(5)].map((_, i) => <Star key={i} className="w-3 h-3 fill-yellow-400 text-yellow-400" />)}
              </div>
            </div>
            <p className="text-purple-300 text-xs font-mono">19 Five-Star Reviews • Supernatural Thriller Comedy</p>
            <p className="text-blue-300/70 text-xs font-mono italic mt-1 line-clamp-1">"{funnyTaglines[currentQuote]}"</p>
            <p className="text-yellow-400/60 text-[10px] font-mono mt-1">By World Record Navy Pilot John Selman</p>
          </div>
          <button className="px-4 py-2 bg-gradient-to-r from-purple-600 to-pink-600 text-white font-mono text-sm rounded hover:scale-105 transition-transform flex items-center gap-1">
            <ShoppingCart className="w-4 h-4" />
            $2.99
          </button>
        </div>
      </div>
    );
  }
  
  // Hero variant for special pages
  if (variant === "hero") {
    return (
      <div className="relative overflow-hidden bg-gradient-to-br from-purple-900 via-pink-900/80 to-blue-900 border-2 border-pink-500 rounded-2xl">
        <div className="absolute inset-0 bg-[url('data:image/svg+xml;base64,PHN2ZyB3aWR0aD0iNjAiIGhlaWdodD0iNjAiIHhtbG5zPSJodHRwOi8vd3d3LnczLm9yZy8yMDAwL3N2ZyI+PGRlZnM+PHBhdHRlcm4gaWQ9InN0YXJzIiB3aWR0aD0iNjAiIGhlaWdodD0iNjAiIHBhdHRlcm5Vbml0cz0idXNlclNwYWNlT25Vc2UiPjxjaXJjbGUgY3g9IjMwIiBjeT0iMzAiIHI9IjEiIGZpbGw9IiNmZmYiIGZpbGwtb3BhY2l0eT0iMC4zIi8+PGNpcmNsZSBjeD0iMTAiIGN5PSI1MCIgcj0iMC41IiBmaWxsPSIjZmZmIiBmaWxsLW9wYWNpdHk9IjAuMiIvPjxjaXJjbGUgY3g9IjUwIiBjeT0iMTAiIHI9IjAuNSIgZmlsbD0iI2ZmZiIgZmlsbC1vcGFjaXR5PSIwLjIiLz48L3BhdHRlcm4+PC9kZWZzPjxyZWN0IHdpZHRoPSIxMDAlIiBoZWlnaHQ9IjEwMCUiIGZpbGw9InVybCgjc3RhcnMpIi8+PC9zdmc+')] opacity-50"></div>
        <div className="relative p-8">
          <div className="text-center mb-6">
            <span className="inline-block px-4 py-1 bg-yellow-500/20 border border-yellow-500/50 rounded-full text-yellow-400 font-mono text-sm mb-4 animate-pulse">
              🏆 OPTIONED FOR FILM • 19 FIVE-STAR REVIEWS
            </span>
            <h2 className="text-4xl md:text-5xl font-bold text-transparent bg-clip-text bg-gradient-to-r from-pink-400 via-purple-400 to-blue-400 font-mono tracking-wider mb-2">
              LETTERS TO EVELYN
            </h2>
            <p className="text-xl text-pink-300 font-mono">A True Supernatural Thriller Comedy</p>
            <p className="text-purple-300/70 font-mono text-sm">By World Record Aviation Holder <span className="text-yellow-400 font-bold">John Selman</span></p>
          </div>
          
          <div className="flex flex-col md:flex-row items-center gap-8">
            <div className="md:w-1/3 flex justify-center">
              <img 
                src={bookImages[currentImage]} 
                alt="Letters to Evelyn" 
                className="w-48 h-auto rounded-lg shadow-2xl shadow-pink-500/40 hover:scale-105 transition-transform cursor-pointer"
                onClick={openAmazon}
              />
            </div>
            <div className="md:w-2/3 text-center md:text-left">
              <p className="text-2xl text-purple-200 font-mono italic mb-6 min-h-[60px] transition-all">
                "{funnyTaglines[currentQuote]}"
              </p>
              
              <div className="bg-black/30 rounded-lg p-4 mb-6">
                <p className="text-purple-200/90 font-mono text-sm italic">
                  "A profound and unforgettable literary piece... The author's imagination is off the charts!"
                </p>
                <p className="text-pink-400 font-mono text-xs mt-2">— Readers' Favorite ⭐⭐⭐⭐⭐</p>
              </div>
              
              <div className="flex flex-wrap justify-center md:justify-start gap-3">
                <a href={BOOK_INFO.amazonUrl} target="_blank" rel="noopener noreferrer" className="px-8 py-4 bg-gradient-to-r from-yellow-500 to-orange-500 text-black font-bold font-mono rounded-lg hover:scale-105 transition-transform shadow-lg flex items-center gap-2 text-lg">
                  <ShoppingCart className="w-6 h-6" />
                  BUY NOW - $2.99
                </a>
                <a href={BOOK_INFO.googleDriveUrl} target="_blank" rel="noopener noreferrer" className="px-6 py-4 bg-gradient-to-r from-green-600 to-emerald-600 text-white font-mono rounded-lg hover:scale-105 transition-transform flex items-center gap-2">
                  <Gift className="w-5 h-5" />
                  FREE PREVIEW
                </a>
              </div>
            </div>
          </div>
        </div>
      </div>
    );
  }
  
  // Full variant (default)
  return (
    <div className="bg-gradient-to-br from-purple-900/50 via-blue-900/40 to-pink-900/50 border-2 border-purple-500 rounded-xl overflow-hidden">
      <div className="p-6">
        <div className="flex flex-col lg:flex-row gap-6">
          {/* Book Images Gallery */}
          <div className="lg:w-1/3 flex flex-col items-center gap-4">
            <div className="relative group cursor-pointer" onClick={openAmazon}>
              <img 
                src={bookImages[currentImage]} 
                alt="Letters to Evelyn" 
                className="w-full max-w-xs rounded-lg shadow-2xl shadow-purple-500/40 group-hover:scale-105 transition-transform"
              />
              <div className="absolute top-2 right-2 bg-gradient-to-r from-yellow-500 to-orange-500 text-black px-2 py-1 rounded font-bold text-xs">
                ⭐ 19 FIVE-STAR REVIEWS
              </div>
              <div className="absolute bottom-2 left-2 bg-pink-500/90 text-white px-2 py-1 rounded font-bold text-xs">
                🎬 OPTIONED FOR FILM
              </div>
            </div>
            {/* Thumbnail Gallery */}
            <div className="flex gap-2">
              {bookImages.map((img, idx) => (
                <button 
                  key={idx} 
                  onClick={() => setCurrentImage(idx)}
                  className={`w-12 h-16 rounded overflow-hidden border-2 transition-all ${currentImage === idx ? 'border-pink-500 scale-110' : 'border-purple-500/30 opacity-60 hover:opacity-100'}`}
                >
                  <img src={img} alt={`Book cover ${idx + 1}`} className="w-full h-full object-cover" />
                </button>
              ))}
            </div>
          </div>
          
          {/* Book Info */}
          <div className="lg:w-2/3">
            <div className="flex items-center gap-2 mb-2">
              <h2 className="text-3xl font-bold text-transparent bg-clip-text bg-gradient-to-r from-pink-400 via-purple-400 to-blue-400 font-mono">
                LETTERS TO EVELYN
              </h2>
            </div>
            
            <p className="text-purple-300 font-mono mb-2">By World Record Aviation Holder <span className="text-pink-400 font-bold">John Selman</span></p>
            <p className="text-yellow-400/60 font-mono text-xs mb-2">A Top Pilot Enterprises, Inc. Publication</p>
            
            <div className="flex items-center gap-4 mb-4">
              <div className="flex">
                {[...Array(5)].map((_, i) => <Star key={i} className="w-5 h-5 fill-yellow-400 text-yellow-400" />)}
              </div>
              <span className="text-yellow-400 font-mono font-bold">5.0 / 5.0</span>
              <span className="text-purple-300 font-mono text-sm">(19 Professional Reviews)</span>
            </div>
            
            <p className="text-xl text-pink-300 font-mono italic mb-4 min-h-[50px]">
              "{funnyTaglines[currentQuote]}"
            </p>
            
            <p className="text-purple-300/80 font-mono text-sm mb-4">
              {BOOK_INFO.genre} • {BOOK_INFO.years}
            </p>
            
            {/* Review Quote */}
            <div className="bg-slate-900/50 rounded-lg p-4 mb-4 border-l-4 border-pink-500">
              <p className="text-purple-200/90 font-mono text-sm italic">
                "{BOOK_INFO.quotes[0].text}"
              </p>
              <p className="text-pink-400 font-mono text-xs mt-2">— {BOOK_INFO.quotes[0].author}</p>
            </div>
            
            {/* CTA Buttons */}
            <div className="flex flex-wrap gap-3">
              <a
                href={BOOK_INFO.amazonUrl}
                target="_blank"
                rel="noopener noreferrer"
                className="px-6 py-3 bg-gradient-to-r from-yellow-500 to-orange-500 text-black font-bold font-mono rounded-lg hover:scale-105 transition-transform shadow-lg flex items-center gap-2"
              >
                <ShoppingCart className="w-5 h-5" />
                BUY ON AMAZON - $2.99
              </a>
              <a
                href={BOOK_INFO.googleDriveUrl}
                target="_blank"
                rel="noopener noreferrer"
                className="px-6 py-3 bg-gradient-to-r from-green-600 to-emerald-600 text-white font-mono rounded-lg hover:scale-105 transition-transform flex items-center gap-2"
              >
                <Gift className="w-5 h-5" />
                FREE PREVIEW
              </a>
              <a
                href={BOOK_INFO.readersFavoriteUrl}
                target="_blank"
                rel="noopener noreferrer"
                className="px-6 py-3 border border-purple-500 text-purple-400 font-mono rounded-lg hover:bg-purple-500/20 transition-colors flex items-center gap-2"
              >
                <Star className="w-5 h-5" />
                READ REVIEWS
              </a>
            </div>
          </div>
        </div>
      </div>
    </div>
  );
};

export default BookSalesBanner;
