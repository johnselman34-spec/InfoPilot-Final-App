/**
 * Book Page Component
 * Promotes "Letters to Evelyn" book with images, reviews, and purchase links
 */
import React, { useState, useEffect } from 'react';
import { ShoppingCart, ExternalLink, Globe, Star, BookOpen } from 'lucide-react';
import { Layout } from '../components/layout/Layout';
import { FuturisticFrame } from '../components/common/FuturisticFrame';
import { BookSalesBanner } from '../components/common';
import { IMAGES, BOOK_INFO } from '../utils/constants';

const BookPage = () => {
  const [currentImage, setCurrentImage] = useState(0);
  const [currentTagline, setCurrentTagline] = useState(0);
  const bookImages = [IMAGES.bookCoverMain, IMAGES.bookCover1, IMAGES.bookCover2, IMAGES.bookCover3, IMAGES.bookCover4];
  
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
      setCurrentTagline((prev) => (prev + 1) % funnyTaglines.length);
    }, 5000);
    return () => clearInterval(timer);
  }, [funnyTaglines.length]);
  
  return (
    <Layout>
      <div className="max-w-5xl mx-auto space-y-8">
        {/* Hero Banner */}
        <BookSalesBanner variant="hero" />
        
        {/* Hilarious Taglines Carousel */}
        <div className="bg-gradient-to-r from-pink-900/30 via-purple-900/30 to-blue-900/30 rounded-xl p-6 border border-pink-500/30 text-center">
          <p className="text-2xl text-pink-300 font-mono italic min-h-[60px] transition-all">
            "{funnyTaglines[currentTagline]}"
          </p>
          <div className="flex justify-center gap-2 mt-4">
            {funnyTaglines.map((_, i) => (
              <button
                key={i}
                onClick={() => setCurrentTagline(i)}
                className={`w-2 h-2 rounded-full transition-all ${currentTagline === i ? 'bg-pink-400 w-6' : 'bg-purple-500/50'}`}
              />
            ))}
          </div>
        </div>

        {/* Hero Section */}
        <div className="relative rounded-xl overflow-hidden">
          <img src={bookImages[currentImage]} alt="Letters to Evelyn" className="w-full h-64 md:h-96 object-cover" />
          <div className="absolute inset-0 bg-gradient-to-t from-slate-950 via-slate-950/50 to-transparent"></div>
          <div className="absolute bottom-0 left-0 right-0 p-6">
            <h1 className="text-4xl md:text-5xl font-bold text-transparent bg-clip-text bg-gradient-to-r from-pink-400 via-purple-400 to-blue-400 font-mono mb-2">LETTERS TO EVELYN</h1>
            <p className="text-xl text-purple-300 font-mono">{BOOK_INFO.genre}</p>
            <p className="text-yellow-400/70 font-mono text-sm mt-2">A Top Pilot Enterprises, Inc. Publication</p>
          </div>
        </div>
        
        {/* Image Gallery */}
        <div className="flex justify-center gap-4">
          {bookImages.map((img, idx) => (
            <button 
              key={idx} 
              onClick={() => setCurrentImage(idx)}
              className={`w-16 h-20 rounded overflow-hidden border-2 transition-all ${currentImage === idx ? 'border-pink-500 scale-110' : 'border-purple-500/30 opacity-60 hover:opacity-100'}`}
            >
              <img src={img} alt={`Book cover ${idx + 1}`} className="w-full h-full object-cover" />
            </button>
          ))}
        </div>

        {/* Rating Banner */}
        <div className="flex flex-col md:flex-row items-center justify-center gap-4 p-6 bg-gradient-to-r from-yellow-500/20 to-orange-500/20 rounded-lg border border-yellow-500">
          <div className="flex">{[...Array(5)].map((_, i) => <Star key={i} className="w-8 h-8 fill-yellow-400 text-yellow-400" />)}</div>
          <div className="text-center md:text-left">
            <span className="text-2xl font-bold text-yellow-400 font-mono">19 FIVE-STAR REVIEWS</span>
            <p className="text-purple-300/70 font-mono text-sm">From Readers' Favorite - Trusted Professional Reviews</p>
          </div>
          <span className="px-4 py-2 bg-pink-500/20 border border-pink-500 rounded-full text-pink-400 font-mono text-sm animate-pulse">
            🎬 OPTIONED FOR FILM
          </span>
        </div>

        {/* Author Section */}
        <FuturisticFrame title="ABOUT THE AUTHOR" color="pink" className="bg-slate-900/80 border border-pink-500/30 rounded-lg">
          <div className="flex flex-col md:flex-row gap-6 items-center">
            <img src={IMAGES.author} alt="John Selman" className="w-32 h-32 rounded-full border-4 border-pink-500 object-cover shadow-lg shadow-pink-500/30" />
            <div>
              <h2 className="text-2xl font-bold text-pink-400 font-mono">John Selman</h2>
              <p className="text-purple-300 font-mono mb-2">World Record Aviation Holder • U.S. Navy Pilot • Author</p>
              <p className="text-purple-400/80 font-mono text-sm italic">"{BOOK_INFO.tagline}"</p>
              <p className="text-yellow-400/60 font-mono text-xs mt-2">Graduated FIRST in his NROTC class at University of Maine</p>
              <p className="text-purple-300/60 font-mono text-xs">Flew 10 different aircraft types • Multiple world records</p>
            </div>
          </div>
        </FuturisticFrame>

        {/* Reviews */}
        <FuturisticFrame title="CRITICAL ACCLAIM" color="purple" className="bg-slate-900/80 border border-purple-500/30 rounded-lg">
          <div className="space-y-4">
            {BOOK_INFO.quotes.map((quote, idx) => (
              <div key={idx} className="bg-slate-950 p-4 rounded border-l-4 border-pink-500">
                <p className="text-purple-300/90 font-mono text-sm italic">"{quote.text}"</p>
                <p className="text-pink-400 font-mono text-xs mt-2">— {quote.author}</p>
              </div>
            ))}
          </div>
        </FuturisticFrame>

        {/* Purchase Links */}
        <FuturisticFrame title="GET YOUR COPY" color="blue" className="bg-slate-900/80 border border-blue-500/30 rounded-lg">
          <div className="grid md:grid-cols-2 gap-4">
            <a href={BOOK_INFO.amazonUrl} target="_blank" rel="noopener noreferrer" className="flex items-center gap-3 px-6 py-4 bg-gradient-to-r from-yellow-500 to-orange-500 text-black font-bold font-mono rounded-lg hover:scale-105 transition-transform">
              <ShoppingCart className="w-6 h-6" /> BUY ON AMAZON
            </a>
            <a href={BOOK_INFO.officialUrl} target="_blank" rel="noopener noreferrer" className="flex items-center gap-3 px-6 py-4 bg-gradient-to-r from-purple-600 to-pink-600 text-white font-mono rounded-lg hover:scale-105 transition-transform">
              <ExternalLink className="w-6 h-6" /> OFFICIAL WEBSITE
            </a>
            <a href={BOOK_INFO.sintraUrl} target="_blank" rel="noopener noreferrer" className="flex items-center gap-3 px-6 py-4 border border-purple-500 text-purple-400 font-mono rounded-lg hover:bg-purple-500/20 transition-colors">
              <Globe className="w-6 h-6" /> SINTRA SITE
            </a>
            <a href={BOOK_INFO.readersFavoriteUrl} target="_blank" rel="noopener noreferrer" className="flex items-center gap-3 px-6 py-4 border border-yellow-500 text-yellow-400 font-mono rounded-lg hover:bg-yellow-500/20 transition-colors">
              <Star className="w-6 h-6" /> READ ALL REVIEWS
            </a>
            <a href={BOOK_INFO.googleDriveUrl} target="_blank" rel="noopener noreferrer" className="flex items-center gap-3 px-6 py-4 border border-blue-500 text-blue-400 font-mono rounded-lg hover:bg-blue-500/20 transition-colors md:col-span-2">
              <BookOpen className="w-6 h-6" /> PREVIEW ON GOOGLE DRIVE
            </a>
          </div>
        </FuturisticFrame>
      </div>
    </Layout>
  );
};

export default BookPage;
