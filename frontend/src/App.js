import React, { useState, useEffect } from 'react';
import './App.css';
import { AuthProvider, useAuth } from './context/AuthContext';
import { api } from './services/api';

// Leaflet imports
import { MapContainer, TileLayer, Marker, Popup } from 'react-leaflet';
import L from 'leaflet';
import 'leaflet/dist/leaflet.css';

// Fix for default marker icons in react-leaflet
delete L.Icon.Default.prototype._getIconUrl;
L.Icon.Default.mergeOptions({
  iconRetinaUrl: 'https://cdnjs.cloudflare.com/ajax/libs/leaflet/1.9.4/images/marker-icon-2x.png',
  iconUrl: 'https://cdnjs.cloudflare.com/ajax/libs/leaflet/1.9.4/images/marker-icon.png',
  shadowUrl: 'https://cdnjs.cloudflare.com/ajax/libs/leaflet/1.9.4/images/marker-shadow.png',
});

// Create custom colored marker icon
const createColoredIcon = (color) => {
  return L.divIcon({
    className: 'custom-marker',
    html: `<svg viewBox="0 0 24 24" fill="${color}" stroke="white" stroke-width="1" style="width:32px;height:32px;filter:drop-shadow(0 2px 4px rgba(0,0,0,0.3))"><path d="M21 10c0 7-9 13-9 13s-9-6-9-13a9 9 0 0 1 18 0z"/><circle cx="12" cy="10" r="3" fill="white"/></svg>`,
    iconSize: [32, 32],
    iconAnchor: [16, 32],
    popupAnchor: [0, -32],
  });
};

// Custom marker icons by category
const categoryColors = [
  '#2196F3', '#4CAF50', '#FF9800', '#f44336', '#9C27B0', 
  '#00BCD4', '#795548', '#607D8B', '#E91E63', '#3F51B5'
];

// Icons Component
const Icons = {
  Search: () => <svg viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2"><circle cx="11" cy="11" r="8"/><path d="M21 21l-4.35-4.35"/></svg>,
  Globe: () => <svg viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2"><circle cx="12" cy="12" r="10"/><path d="M2 12h20M12 2a15.3 15.3 0 0 1 4 10 15.3 15.3 0 0 1-4 10 15.3 15.3 0 0 1-4-10 15.3 15.3 0 0 1 4-10z"/></svg>,
  Folder: () => <svg viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2"><path d="M22 19a2 2 0 0 1-2 2H4a2 2 0 0 1-2-2V5a2 2 0 0 1 2-2h5l2 3h9a2 2 0 0 1 2 2z"/></svg>,
  Map: () => <svg viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2"><path d="M21 10c0 7-9 13-9 13s-9-6-9-13a9 9 0 0 1 18 0z"/><circle cx="12" cy="10" r="3"/></svg>,
  People: () => <svg viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2"><path d="M17 21v-2a4 4 0 0 0-4-4H5a4 4 0 0 0-4 4v2"/><circle cx="9" cy="7" r="4"/><path d="M23 21v-2a4 4 0 0 0-3-3.87M16 3.13a4 4 0 0 1 0 7.75"/></svg>,
  Settings: () => <svg viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2"><circle cx="12" cy="12" r="3"/><path d="M19.4 15a1.65 1.65 0 0 0 .33 1.82l.06.06a2 2 0 0 1 0 2.83 2 2 0 0 1-2.83 0l-.06-.06a1.65 1.65 0 0 0-1.82-.33 1.65 1.65 0 0 0-1 1.51V21a2 2 0 0 1-2 2 2 2 0 0 1-2-2v-.09A1.65 1.65 0 0 0 9 19.4a1.65 1.65 0 0 0-1.82.33l-.06.06a2 2 0 0 1-2.83 0 2 2 0 0 1 0-2.83l.06-.06a1.65 1.65 0 0 0 .33-1.82 1.65 1.65 0 0 0-1.51-1H3a2 2 0 0 1-2-2 2 2 0 0 1 2-2h.09A1.65 1.65 0 0 0 4.6 9a1.65 1.65 0 0 0-.33-1.82l-.06-.06a2 2 0 0 1 0-2.83 2 2 0 0 1 2.83 0l.06.06a1.65 1.65 0 0 0 1.82.33H9a1.65 1.65 0 0 0 1-1.51V3a2 2 0 0 1 2-2 2 2 0 0 1 2 2v.09a1.65 1.65 0 0 0 1 1.51 1.65 1.65 0 0 0 1.82-.33l.06-.06a2 2 0 0 1 2.83 0 2 2 0 0 1 0 2.83l-.06.06a1.65 1.65 0 0 0-.33 1.82V9a1.65 1.65 0 0 0 1.51 1H21a2 2 0 0 1 2 2 2 2 0 0 1-2 2h-.09a1.65 1.65 0 0 0-1.51 1z"/></svg>,
  Mail: () => <svg viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2"><path d="M4 4h16c1.1 0 2 .9 2 2v12c0 1.1-.9 2-2 2H4c-1.1 0-2-.9-2-2V6c0-1.1.9-2 2-2z"/><polyline points="22,6 12,13 2,6"/></svg>,
  Lock: () => <svg viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2"><rect x="3" y="11" width="18" height="11" rx="2" ry="2"/><path d="M7 11V7a5 5 0 0 1 10 0v4"/></svg>,
  User: () => <svg viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2"><path d="M20 21v-2a4 4 0 0 0-4-4H8a4 4 0 0 0-4 4v2"/><circle cx="12" cy="7" r="4"/></svg>,
  Eye: () => <svg viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2"><path d="M1 12s4-8 11-8 11 8 11 8-4 8-11 8-11-8-11-8z"/><circle cx="12" cy="12" r="3"/></svg>,
  EyeOff: () => <svg viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2"><path d="M17.94 17.94A10.07 10.07 0 0 1 12 20c-7 0-11-8-11-8a18.45 18.45 0 0 1 5.06-5.94M9.9 4.24A9.12 9.12 0 0 1 12 4c7 0 11 8 11 8a18.5 18.5 0 0 1-2.16 3.19m-6.72-1.07a3 3 0 1 1-4.24-4.24"/><line x1="1" y1="1" x2="23" y2="23"/></svg>,
  Plus: () => <svg viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2"><line x1="12" y1="5" x2="12" y2="19"/><line x1="5" y1="12" x2="19" y2="12"/></svg>,
  X: () => <svg viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2"><line x1="18" y1="6" x2="6" y2="18"/><line x1="6" y1="6" x2="18" y2="18"/></svg>,
  Check: () => <svg viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2"><polyline points="20 6 9 17 4 12"/></svg>,
  Pencil: () => <svg viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2"><path d="M11 4H4a2 2 0 0 0-2 2v14a2 2 0 0 0 2 2h14a2 2 0 0 0 2-2v-7"/><path d="M18.5 2.5a2.121 2.121 0 0 1 3 3L12 15l-4 1 1-4 9.5-9.5z"/></svg>,
  Trash: () => <svg viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2"><polyline points="3 6 5 6 21 6"/><path d="M19 6v14a2 2 0 0 1-2 2H7a2 2 0 0 1-2-2V6m3 0V4a2 2 0 0 1 2-2h4a2 2 0 0 1 2 2v2"/></svg>,
  Layers: () => <svg viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2"><polygon points="12 2 2 7 12 12 22 7 12 2"/><polyline points="2 17 12 22 22 17"/><polyline points="2 12 12 17 22 12"/></svg>,
  Info: () => <svg viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2"><circle cx="12" cy="12" r="10"/><line x1="12" y1="16" x2="12" y2="12"/><line x1="12" y1="8" x2="12.01" y2="8"/></svg>,
  ThumbsUp: () => <svg viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2"><path d="M14 9V5a3 3 0 0 0-3-3l-4 9v11h11.28a2 2 0 0 0 2-1.7l1.38-9a2 2 0 0 0-2-2.3zM7 22H4a2 2 0 0 1-2-2v-7a2 2 0 0 1 2-2h3"/></svg>,
  Heart: () => <svg viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2"><path d="M20.84 4.61a5.5 5.5 0 0 0-7.78 0L12 5.67l-1.06-1.06a5.5 5.5 0 0 0-7.78 7.78l1.06 1.06L12 21.23l7.78-7.78 1.06-1.06a5.5 5.5 0 0 0 0-7.78z"/></svg>,
  Star: () => <svg viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2"><polygon points="12 2 15.09 8.26 22 9.27 17 14.14 18.18 21.02 12 17.77 5.82 21.02 7 14.14 2 9.27 8.91 8.26 12 2"/></svg>,
  Alert: () => <svg viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2"><circle cx="12" cy="12" r="10"/><line x1="12" y1="8" x2="12" y2="12"/><line x1="12" y1="16" x2="12.01" y2="16"/></svg>,
  Shield: () => <svg viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2"><path d="M12 22s8-4 8-10V5l-8-3-8 3v7c0 6 8 10 8 10z"/></svg>,
  Chat: () => <svg viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2"><path d="M21 15a2 2 0 0 1-2 2H7l-4 4V5a2 2 0 0 1 2-2h14a2 2 0 0 1 2 2z"/></svg>,
  Send: () => <svg viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2"><line x1="22" y1="2" x2="11" y2="13"/><polygon points="22 2 15 22 11 13 2 9 22 2"/></svg>,
  ChevronLeft: () => <svg viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2"><polyline points="15 18 9 12 15 6"/></svg>,
  ChevronRight: () => <svg viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2"><polyline points="9 18 15 12 9 6"/></svg>,
  LogOut: () => <svg viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2"><path d="M9 21H5a2 2 0 0 1-2-2V5a2 2 0 0 1 2-2h4"/><polyline points="16 17 21 12 16 7"/><line x1="21" y1="12" x2="9" y2="12"/></svg>,
  Rocket: () => <svg viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2"><path d="M4.5 16.5c-1.5 1.26-2 5-2 5s3.74-.5 5-2c.71-.84.7-2.13-.09-2.91a2.18 2.18 0 0 0-2.91-.09z"/><path d="M12 15l-3-3a22 22 0 0 1 2-3.95A12.88 12.88 0 0 1 22 2c0 2.72-.78 7.5-6 11a22.35 22.35 0 0 1-4 2z"/><path d="M9 12H4s.55-3.03 2-4c1.62-1.08 5 0 5 0"/><path d="M12 15v5s3.03-.55 4-2c1.08-1.62 0-5 0-5"/></svg>,
  Location: () => <svg viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2"><path d="M21 10c0 7-9 13-9 13s-9-6-9-13a9 9 0 0 1 18 0z"/><circle cx="12" cy="10" r="3"/></svg>,
  ExternalLink: () => <svg viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2"><path d="M18 13v6a2 2 0 0 1-2 2H5a2 2 0 0 1-2-2V8a2 2 0 0 1 2-2h6"/><polyline points="15 3 21 3 21 9"/><line x1="10" y1="14" x2="21" y2="3"/></svg>,
  Filter: () => <svg viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2"><polygon points="22 3 2 3 10 12.46 10 19 14 21 14 12.46 22 3"/></svg>,
  Code: () => <svg viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2"><polyline points="16 18 22 12 16 6"/><polyline points="8 6 2 12 8 18"/></svg>,
  Book: () => <svg viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2"><path d="M4 19.5A2.5 2.5 0 0 1 6.5 17H20"/><path d="M6.5 2H20v20H6.5A2.5 2.5 0 0 1 4 19.5v-15A2.5 2.5 0 0 1 6.5 2z"/></svg>,
  ShoppingCart: () => <svg viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2"><circle cx="9" cy="21" r="1"/><circle cx="20" cy="21" r="1"/><path d="M1 1h4l2.68 13.39a2 2 0 0 0 2 1.61h9.72a2 2 0 0 0 2-1.61L23 6H6"/></svg>,
};

// Book Images for promotional carousel
const bookImages = {
  cover: "https://customer-assets.emergentagent.com/job_b9531e7d-8be8-4b48-a8cb-04b5aa1b91c5/artifacts/2h5e2m0v_492184737_9796149057120753_8323589957375320957_n.jpg",
  promo1: "https://customer-assets.emergentagent.com/job_b9531e7d-8be8-4b48-a8cb-04b5aa1b91c5/artifacts/cg5rg41q_Letters%20to%20Evelyn%20advertisement%201.jpg",
  promo2: "https://customer-assets.emergentagent.com/job_b9531e7d-8be8-4b48-a8cb-04b5aa1b91c5/artifacts/hc8e1pgk_Letters%20to%20Evelyn%20advertisement%202.jpg",
  promo3: "https://customer-assets.emergentagent.com/job_b9531e7d-8be8-4b48-a8cb-04b5aa1b91c5/artifacts/tlenrvs0_Letters%20to%20Evelyn%20advertisement%203.jpg",
  promo4: "https://customer-assets.emergentagent.com/job_b9531e7d-8be8-4b48-a8cb-04b5aa1b91c5/artifacts/2l0nsrbt_Letters%20to%20Evelyn%20advertisement%204.jpg",
  cosmicGulper: "https://customer-assets.emergentagent.com/job_b9531e7d-8be8-4b48-a8cb-04b5aa1b91c5/artifacts/2l0nsrbt_Letters%20to%20Evelyn%20advertisement%204.jpg",
};

// Premium subscription promotional image
const premiumImage = "https://customer-assets.emergentagent.com/job_b9531e7d-8be8-4b48-a8cb-04b5aa1b91c5/artifacts/95v26r4c_global-network-world-globe-focusing-usa-symbolizing-data-transfer-worldwide-concept-data-transfer-global-connectivity-information-exchange-world-globe-usa-symbolism_918839-41653.jpg";

// Amazon book link
const AMAZON_BOOK_URL = "https://www.amazon.com/Letters-Evelyn-John-Selman-ebook/dp/B0CQZ8R191";

// Letters to Evelyn Book Promotion Component
function BookPromoSection({ variant = 'full' }) {
  const [currentImage, setCurrentImage] = useState(0);
  const promoImages = [bookImages.promo1, bookImages.promo2, bookImages.promo3, bookImages.promo4];
  
  useEffect(() => {
    const timer = setInterval(() => {
      setCurrentImage((prev) => (prev + 1) % promoImages.length);
    }, 4000); // Slightly faster rotation for more engagement
    return () => clearInterval(timer);
  }, [promoImages.length]);

  const handleBuyBook = () => {
    window.open(AMAZON_BOOK_URL, '_blank');
  };

  if (variant === 'compact') {
    return (
      <div 
        className="book-promo-compact" 
        onClick={handleBuyBook}
        style={{
          background: 'linear-gradient(135deg, rgba(139, 92, 246, 0.15) 0%, rgba(244, 63, 94, 0.15) 100%)',
          border: '1px solid rgba(244, 63, 94, 0.3)',
          borderRadius: '16px',
          padding: '16px',
          cursor: 'pointer',
          display: 'flex',
          alignItems: 'center',
          gap: '16px',
          marginBottom: '20px',
          transition: 'all 0.3s ease'
        }}
        data-testid="book-promo-compact"
      >
        <img 
          src={bookImages.cover} 
          alt="Letters to Evelyn" 
          style={{
            width: '60px',
            height: '80px',
            objectFit: 'cover',
            borderRadius: '8px',
            boxShadow: '0 4px 15px rgba(244, 63, 94, 0.3)'
          }}
        />
        <div style={{flex: 1}}>
          <div style={{
            fontFamily: "'Unbounded', sans-serif",
            fontSize: '14px',
            fontWeight: 700,
            background: 'linear-gradient(135deg, #F43F5E 0%, #8B5CF6 100%)',
            WebkitBackgroundClip: 'text',
            WebkitTextFillColor: 'transparent',
            marginBottom: '4px'
          }}>Letters to Evelyn</div>
          <div style={{fontSize: '12px', color: '#94A3B8'}}>A cosmic journey of love & discovery</div>
        </div>
        <Icons.ShoppingCart style={{width: 20, height: 20, color: '#F43F5E'}} />
      </div>
    );
  }

  return (
    <div 
      className="book-promo-section" 
      style={{
        background: 'linear-gradient(135deg, rgba(5, 5, 16, 0.9) 0%, rgba(15, 23, 42, 0.9) 100%)',
        border: '1px solid rgba(244, 63, 94, 0.3)',
        borderRadius: '24px',
        padding: '28px',
        marginBottom: '28px',
        position: 'relative',
        overflow: 'hidden'
      }}
      data-testid="book-promo-section"
    >
      {/* Cosmic glow effect */}
      <div style={{
        position: 'absolute',
        top: '-50%',
        right: '-30%',
        width: '80%',
        height: '200%',
        background: 'radial-gradient(circle, rgba(244, 63, 94, 0.2) 0%, transparent 50%)',
        pointerEvents: 'none',
        animation: 'rotate-glow 20s linear infinite'
      }} />
      
      <div style={{
        display: 'flex',
        gap: '28px',
        alignItems: 'center',
        position: 'relative',
        zIndex: 1,
        flexWrap: 'wrap'
      }}>
        {/* Book Cover */}
        <div style={{
          flexShrink: 0,
          position: 'relative'
        }}>
          <img 
            src={bookImages.cover} 
            alt="Letters to Evelyn - Book Cover" 
            style={{
              width: '140px',
              height: '200px',
              objectFit: 'cover',
              borderRadius: '12px',
              boxShadow: '0 10px 40px rgba(244, 63, 94, 0.4), 0 0 60px rgba(139, 92, 246, 0.2)',
              border: '2px solid rgba(255, 255, 255, 0.1)'
            }}
            data-testid="book-cover-image"
          />
          {/* Sparkle effect */}
          <div style={{
            position: 'absolute',
            top: '-5px',
            right: '-5px',
            width: '20px',
            height: '20px',
            background: 'radial-gradient(circle, #F43F5E 0%, transparent 70%)',
            borderRadius: '50%',
            animation: 'pulse-glow 2s ease-in-out infinite'
          }} />
        </div>
        
        {/* Book Info */}
        <div style={{flex: 1, minWidth: '200px'}}>
          <div style={{
            fontSize: '12px',
            color: '#F472B6',
            letterSpacing: '2px',
            textTransform: 'uppercase',
            marginBottom: '8px'
          }}>From the Creator of InfoPilot</div>
          
          <h3 style={{
            fontFamily: "'Unbounded', sans-serif",
            fontSize: '28px',
            fontWeight: 800,
            background: 'linear-gradient(135deg, #F43F5E 0%, #EC4899 50%, #8B5CF6 100%)',
            WebkitBackgroundClip: 'text',
            WebkitTextFillColor: 'transparent',
            marginBottom: '12px',
            lineHeight: 1.2
          }}>Letters to Evelyn</h3>
          
          <p style={{
            fontSize: '15px',
            color: '#94A3B8',
            lineHeight: 1.7,
            marginBottom: '20px'
          }}>
            A breathtaking journey through love, loss, and cosmic discovery. 
            When reality breaks, what truths remain?
          </p>
          
          {/* Promotional taglines */}
          <div style={{
            display: 'flex',
            flexWrap: 'wrap',
            gap: '8px',
            marginBottom: '20px'
          }}>
            {['I FLEW JETS THEN REALITY BROKE', 'UNIVERSE FACT-CHECKED IT'].map((tag, i) => (
              <span key={i} style={{
                background: 'rgba(244, 63, 94, 0.15)',
                border: '1px solid rgba(244, 63, 94, 0.3)',
                borderRadius: '20px',
                padding: '6px 14px',
                fontSize: '11px',
                fontWeight: 600,
                color: '#FB7185',
                letterSpacing: '0.5px'
              }}>{tag}</span>
            ))}
          </div>
          
          <button 
            onClick={handleBuyBook}
            className="btn btn-primary"
            style={{
              width: 'auto',
              padding: '14px 28px',
              fontSize: '14px'
            }}
            data-testid="buy-book-button"
          >
            <Icons.Book /> Get Your Copy on Amazon
          </button>
        </div>
        
        {/* Promotional Image Carousel */}
        <div style={{
          width: '200px',
          height: '200px',
          borderRadius: '16px',
          overflow: 'hidden',
          position: 'relative',
          boxShadow: '0 10px 40px rgba(0, 0, 0, 0.4)',
          border: '1px solid rgba(255, 255, 255, 0.1)',
          flexShrink: 0
        }}>
          {promoImages.map((img, idx) => (
            <img 
              key={idx}
              src={img} 
              alt={`Letters to Evelyn Promo ${idx + 1}`}
              style={{
                position: 'absolute',
                top: 0,
                left: 0,
                width: '100%',
                height: '100%',
                objectFit: 'cover',
                opacity: currentImage === idx ? 1 : 0,
                transition: 'opacity 1s ease-in-out'
              }}
            />
          ))}
          {/* Image indicator dots */}
          <div style={{
            position: 'absolute',
            bottom: '10px',
            left: '50%',
            transform: 'translateX(-50%)',
            display: 'flex',
            gap: '6px'
          }}>
            {promoImages.map((_, idx) => (
              <div 
                key={idx}
                onClick={() => setCurrentImage(idx)}
                style={{
                  width: '8px',
                  height: '8px',
                  borderRadius: '50%',
                  background: currentImage === idx ? '#F43F5E' : 'rgba(255, 255, 255, 0.3)',
                  cursor: 'pointer',
                  transition: 'background 0.3s ease'
                }}
              />
            ))}
          </div>
        </div>
      </div>
    </div>
  );
}

// Premium Subscription Promo Component - for non-premium users
function PremiumPromoSection({ onSubscribe }) {
  return (
    <div 
      className="premium-promo-section" 
      style={{
        background: 'linear-gradient(135deg, rgba(59, 130, 246, 0.15) 0%, rgba(139, 92, 246, 0.15) 100%)',
        border: '1px solid rgba(59, 130, 246, 0.3)',
        borderRadius: '20px',
        padding: '24px',
        marginBottom: '24px',
        display: 'flex',
        alignItems: 'center',
        gap: '24px',
        position: 'relative',
        overflow: 'hidden',
        cursor: 'pointer',
        transition: 'all 0.3s ease'
      }}
      onClick={onSubscribe}
      data-testid="premium-promo-section"
    >
      {/* Glowing background effect */}
      <div style={{
        position: 'absolute',
        top: '-50%',
        left: '-20%',
        width: '60%',
        height: '200%',
        background: 'radial-gradient(circle, rgba(59, 130, 246, 0.2) 0%, transparent 50%)',
        pointerEvents: 'none'
      }} />
      
      {/* Globe Image */}
      <div style={{
        width: '100px',
        height: '100px',
        borderRadius: '16px',
        overflow: 'hidden',
        flexShrink: 0,
        boxShadow: '0 8px 30px rgba(59, 130, 246, 0.3)',
        border: '2px solid rgba(59, 130, 246, 0.3)',
        position: 'relative',
        zIndex: 1
      }}>
        <img 
          src={premiumImage}
          alt="Global Network"
          style={{
            width: '100%',
            height: '100%',
            objectFit: 'cover'
          }}
        />
      </div>
      
      {/* Content */}
      <div style={{flex: 1, position: 'relative', zIndex: 1}}>
        <div style={{
          fontSize: '11px',
          color: '#60A5FA',
          letterSpacing: '2px',
          textTransform: 'uppercase',
          marginBottom: '6px',
          fontWeight: 600
        }}>Unlock the Full Power</div>
        
        <h4 style={{
          fontFamily: "'Outfit', sans-serif",
          fontSize: '20px',
          fontWeight: 700,
          background: 'linear-gradient(135deg, #3B82F6 0%, #8B5CF6 100%)',
          WebkitBackgroundClip: 'text',
          WebkitTextFillColor: 'transparent',
          marginBottom: '8px'
        }}>Go Premium - Only $0.99</h4>
        
        <div style={{
          display: 'flex',
          flexWrap: 'wrap',
          gap: '12px',
          fontSize: '13px',
          color: '#94A3B8'
        }}>
          <span style={{display: 'flex', alignItems: 'center', gap: '4px'}}>
            <Icons.Map style={{width: 14, height: 14, color: '#60A5FA'}} /> Interactive World Map
          </span>
          <span style={{display: 'flex', alignItems: 'center', gap: '4px'}}>
            <Icons.Search style={{width: 14, height: 14, color: '#60A5FA'}} /> Unlimited Search Pages
          </span>
          <span style={{display: 'flex', alignItems: 'center', gap: '4px'}}>
            <Icons.Star style={{width: 14, height: 14, color: '#60A5FA'}} /> All Premium Features
          </span>
        </div>
      </div>
      
      {/* CTA Arrow */}
      <div style={{
        background: 'linear-gradient(135deg, #3B82F6 0%, #8B5CF6 100%)',
        borderRadius: '50%',
        width: '44px',
        height: '44px',
        display: 'flex',
        alignItems: 'center',
        justifyContent: 'center',
        flexShrink: 0,
        boxShadow: '0 0 20px rgba(59, 130, 246, 0.4)',
        position: 'relative',
        zIndex: 1
      }}>
        <Icons.ChevronRight style={{width: 24, height: 24, color: 'white'}} />
      </div>
    </div>
  );
}

// Login Page
function LoginPage({ onNavigate }) {
  const { login } = useAuth();
  const [email, setEmail] = useState('');
  const [password, setPassword] = useState('');
  const [showPassword, setShowPassword] = useState(false);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState('');

  const handleSubmit = async (e) => {
    e.preventDefault();
    if (!email || !password) {
      setError('Please fill in all fields');
      return;
    }
    setLoading(true);
    setError('');
    try {
      await login(email, password);
    } catch (err) {
      setError(err.response?.data?.detail || 'Invalid credentials');
    } finally {
      setLoading(false);
    }
  };

  return (
    <div className="auth-container">
      <div className="auth-card">
        <div className="auth-logo">
          <div className="logo-circle">IP</div>
          <h1>InfoPilot</h1>
          <p>World Wide Web Information Exchange</p>
        </div>
        <h2 className="auth-title">Welcome Back!</h2>
        <p className="auth-subtitle">Sign in to access your Ultimate Search Page</p>
        
        {error && <div className="info-box" style={{background: '#FFEBEE', marginBottom: 16}}><Icons.Alert /><p style={{color: '#f44336'}}>{error}</p></div>}
        
        <form onSubmit={handleSubmit}>
          <div className="form-group">
            <label>Email</label>
            <div className="input-wrapper">
              <Icons.Mail />
              <input type="email" placeholder="Enter your email" value={email} onChange={(e) => setEmail(e.target.value)} />
            </div>
          </div>
          <div className="form-group">
            <label>Password</label>
            <div className="input-wrapper">
              <Icons.Lock />
              <input type={showPassword ? 'text' : 'password'} placeholder="Enter your password" value={password} onChange={(e) => setPassword(e.target.value)} />
              <button type="button" className="toggle-password" onClick={() => setShowPassword(!showPassword)}>
                {showPassword ? <Icons.EyeOff /> : <Icons.Eye />}
              </button>
            </div>
          </div>
          <button type="submit" className="btn btn-primary" disabled={loading}>
            {loading ? <div className="spinner" style={{width: 20, height: 20}}/> : 'Sign In'}
          </button>
        </form>
        
        <div className="auth-footer">
          <p>Don't have an account? <a href="#" onClick={(e) => { e.preventDefault(); onNavigate('register'); }}>Sign Up</a></p>
        </div>
      </div>
    </div>
  );
}

// Register Page
function RegisterPage({ onNavigate }) {
  const { register } = useAuth();
  const [email, setEmail] = useState('');
  const [username, setUsername] = useState('');
  const [password, setPassword] = useState('');
  const [confirmPassword, setConfirmPassword] = useState('');
  const [showPassword, setShowPassword] = useState(false);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState('');

  const handleSubmit = async (e) => {
    e.preventDefault();
    if (!email || !username || !password || !confirmPassword) {
      setError('Please fill in all fields');
      return;
    }
    if (password !== confirmPassword) {
      setError('Passwords do not match');
      return;
    }
    if (password.length < 6) {
      setError('Password must be at least 6 characters');
      return;
    }
    setLoading(true);
    setError('');
    try {
      await register(email, username, password);
    } catch (err) {
      setError(err.response?.data?.detail || 'Could not create account');
    } finally {
      setLoading(false);
    }
  };

  return (
    <div className="auth-container">
      <div className="auth-card">
        <div className="auth-logo">
          <div className="logo-circle" style={{background: 'linear-gradient(135deg, #4CAF50, #388E3C)'}}>IP</div>
          <h1>Join InfoPilot</h1>
          <p>Create your account</p>
        </div>
        
        <div className="info-box">
          <Icons.Info />
          <p>Get access to the #1 way to search for, categorize and share information!</p>
        </div>
        
        {error && <div className="info-box" style={{background: '#FFEBEE'}}><Icons.Alert /><p style={{color: '#f44336'}}>{error}</p></div>}
        
        <form onSubmit={handleSubmit}>
          <div className="form-group">
            <div className="input-wrapper"><Icons.Mail /><input type="email" placeholder="Email" value={email} onChange={(e) => setEmail(e.target.value)} /></div>
          </div>
          <div className="form-group">
            <div className="input-wrapper"><Icons.User /><input type="text" placeholder="Username" value={username} onChange={(e) => setUsername(e.target.value)} /></div>
          </div>
          <div className="form-group">
            <div className="input-wrapper">
              <Icons.Lock />
              <input type={showPassword ? 'text' : 'password'} placeholder="Password" value={password} onChange={(e) => setPassword(e.target.value)} />
              <button type="button" className="toggle-password" onClick={() => setShowPassword(!showPassword)}>
                {showPassword ? <Icons.EyeOff /> : <Icons.Eye />}
              </button>
            </div>
          </div>
          <div className="form-group">
            <div className="input-wrapper"><Icons.Shield /><input type={showPassword ? 'text' : 'password'} placeholder="Confirm Password" value={confirmPassword} onChange={(e) => setConfirmPassword(e.target.value)} /></div>
          </div>
          <button type="submit" className="btn btn-success" disabled={loading}>
            {loading ? <div className="spinner" style={{width: 20, height: 20}}/> : 'Create Account'}
          </button>
        </form>
        
        <p style={{textAlign: 'center', marginTop: 16, color: '#4CAF50', fontSize: 14}}>
          <Icons.Star /> Full access for only $0.99!
        </p>
        
        <div className="auth-footer">
          <p>Already have an account? <a href="#" onClick={(e) => { e.preventDefault(); onNavigate('login'); }}>Sign In</a></p>
        </div>
      </div>
    </div>
  );
}

// Ultimate Search Page
function UltimateSearchPage() {
  const { user } = useAuth();
  const [categories, setCategories] = useState([]);
  const [selectedCategories, setSelectedCategories] = useState([]);
  const [aggregation, setAggregation] = useState('and_or');
  const [searchQuery, setSearchQuery] = useState('');
  const [articleType, setArticleType] = useState(null);
  const [results, setResults] = useState([]);
  const [loading, setLoading] = useState(false);
  const [page, setPage] = useState(1);
  const [totalPages, setTotalPages] = useState(1);
  const [stats, setStats] = useState(null);
  const [showFilters, setShowFilters] = useState(false);

  const articleTypes = ['Informative Ph.D.', 'Informative', 'News Article', 'Blog', 'Forum', 'Personal Report (collected)', 'Personal Report (organic)'];

  useEffect(() => { loadCategories(); loadStats(); }, []);
  useEffect(() => { loadResults(); }, [selectedCategories, aggregation, articleType, page]);

  const loadCategories = async () => {
    try { const data = await api.get('/categories'); setCategories(data); } catch (e) { console.error(e); }
  };

  const loadStats = async () => {
    try { const data = await api.get('/ultimate-search/stats'); setStats(data); } catch (e) { console.error(e); }
  };

  const loadResults = async () => {
    setLoading(true);
    try {
      const params = { page, aggregation };
      if (selectedCategories.length > 0) params.category_ids = selectedCategories.join(',');
      if (articleType) params.article_type = articleType;
      if (searchQuery) params.search_query = searchQuery;
      const data = await api.get('/ultimate-search', params);
      setResults(data.results);
      setTotalPages(data.total_pages);
    } catch (e) {
      if (e.response?.status === 403) alert(e.response.data.detail);
    } finally { setLoading(false); }
  };

  const toggleCategory = (id) => {
    setSelectedCategories(prev => prev.includes(id) ? prev.filter(c => c !== id) : [...prev, id]);
    setPage(1);
  };

  const handleReaction = async (resultId, reactionType) => {
    try { await api.post('/reactions', { search_result_id: resultId, reaction_type: reactionType }); loadResults(); } catch (e) { alert('Could not add reaction'); }
  };

  return (
    <>
      <div className="page-header">
        <h1><Icons.Search /> Ultimate Search</h1>
        <button className="btn btn-outline" onClick={() => setShowFilters(!showFilters)} style={{width: 'auto', padding: '8px 16px'}}>
          <Icons.Filter /> Filters
        </button>
      </div>
      <div className="page-content">
        {stats && (
          <div className="stats-bar">
            <div className="stat-item"><div className="value">{stats.total_results}</div><div className="label">Results</div></div>
            <div className="stat-item"><div className="value">{categories.length}</div><div className="label">Categories</div></div>
            <div className="stat-item"><div className="value">{Object.keys(stats.article_type_breakdown || {}).length}</div><div className="label">Types</div></div>
          </div>
        )}

        {/* Book Promotion Section */}
        <BookPromoSection variant="full" />

        <div className="search-bar" style={{marginBottom: 20}}>
          <Icons.Search />
          <input type="text" placeholder="Search in your results..." value={searchQuery} onChange={(e) => setSearchQuery(e.target.value)} onKeyPress={(e) => e.key === 'Enter' && loadResults()} />
        </div>

        {showFilters && (
          <div className="filters-panel">
            <div className="filter-label">Search Aggregation:</div>
            <div className="filter-row">
              {['and_or', 'and', 'or'].map(agg => (
                <span key={agg} className={`chip ${aggregation === agg ? 'chip-selected' : 'chip-default'}`} onClick={() => { setAggregation(agg); setPage(1); }}>
                  {agg === 'and_or' ? 'And/Or' : agg.toUpperCase()}
                </span>
              ))}
            </div>
            <div className="filter-help">
              {aggregation === 'and_or' && 'Must have ALL selected categories (and possibly more)'}
              {aggregation === 'and' && 'Must have EXACTLY the selected categories'}
              {aggregation === 'or' && 'Must have ANY of the selected categories'}
            </div>
            <div className="filter-label">Article Type:</div>
            <div className="filter-row">
              <span className={`chip ${!articleType ? 'chip-selected' : 'chip-default'}`} onClick={() => { setArticleType(null); setPage(1); }}>All</span>
              {articleTypes.map(type => (
                <span key={type} className={`chip ${articleType === type ? 'chip-selected' : 'chip-default'}`} onClick={() => { setArticleType(type); setPage(1); }}>{type}</span>
              ))}
            </div>
          </div>
        )}

        <div className="section-title"><Icons.Folder /> Your Categories</div>
        <div className="category-chips">
          {categories.length === 0 ? <p style={{color: '#999', fontStyle: 'italic'}}>No categories yet. Create one in the Categories tab!</p> :
            categories.map(cat => (
              <span key={cat.id} className={`chip ${selectedCategories.includes(cat.id) ? 'chip-selected' : 'chip-default'}`} onClick={() => toggleCategory(cat.id)}>
                {cat.name} {cat.is_public && <Icons.Globe />}
              </span>
            ))
          }
        </div>

        <div className="section-title" style={{marginTop: 24}}>Search Results {results.length > 0 && `(Page ${page}/${totalPages})`}</div>
        
        {loading ? <div className="loading"><div className="spinner"/></div> :
          results.length === 0 ? (
            <div className="empty-state">
              <Icons.Folder />
              <h3>No results yet</h3>
              <p>Go to InfoJet tab to search and collate web results!</p>
            </div>
          ) : (
            <>
              {results.map(result => (
                <div key={result.id} className="result-card">
                  <div className="result-header">
                    <a href={result.url} target="_blank" rel="noopener noreferrer" className="result-title">{result.title}</a>
                    <span className="badge badge-success">{result.article_type}</span>
                  </div>
                  <div className="result-domain">{result.root_domain}</div>
                  <div className="result-snippet">{result.snippet}</div>
                  <div className="result-categories">
                    {result.categories?.map((cat, idx) => <span key={idx} className="badge badge-primary">{cat}</span>)}
                  </div>
                  <div className="reaction-bar">
                    {['Like', 'Love', 'Funny', 'Sad', 'Caution', 'Spam', 'Best'].map(reaction => (
                      <button key={reaction} className={`reaction-btn ${result.reactions?.[reaction]?.includes(user?.id) ? 'active' : ''}`} onClick={() => handleReaction(result.id, reaction)}>
                        {reaction === 'Like' && <Icons.ThumbsUp />}
                        {reaction === 'Love' && <Icons.Heart />}
                        {reaction === 'Best' && <Icons.Star />}
                        {reaction === 'Caution' && <Icons.Alert />}
                        {['Funny', 'Sad', 'Spam'].includes(reaction) && reaction.charAt(0)}
                        <span>{result.reactions?.[reaction]?.length || 0}</span>
                      </button>
                    ))}
                  </div>
                </div>
              ))}
              {totalPages > 1 && (
                <div className="pagination">
                  <button className="page-btn" disabled={page === 1} onClick={() => setPage(p => p - 1)}><Icons.ChevronLeft /></button>
                  <span className="page-text">{page} / {totalPages}</span>
                  <button className="page-btn" disabled={page === totalPages} onClick={() => setPage(p => p + 1)}><Icons.ChevronRight /></button>
                </div>
              )}
            </>
          )}
      </div>
    </>
  );
}

// InfoJet Page
function InfoJetPage() {
  const [searchQuery, setSearchQuery] = useState('');
  const [searchResults, setSearchResults] = useState([]);
  const [collatedResults, setCollatedResults] = useState([]);
  const [searching, setSearching] = useState(false);
  const [collating, setCollating] = useState(false);
  const [categoriesCount, setCategoriesCount] = useState(0);
  const [showOperators, setShowOperators] = useState(false);

  const operators = [
    { op: 'site:', desc: 'Limit to specific site' },
    { op: 'filetype:', desc: 'Specific file type' },
    { op: 'intitle:', desc: 'Word in title' },
    { op: 'inurl:', desc: 'Word in URL' },
    { op: '"..."', desc: 'Exact phrase' },
    { op: '-', desc: 'Exclude word' },
    { op: 'OR', desc: 'Either term' },
  ];

  useEffect(() => {
    api.get('/categories').then(data => setCategoriesCount(data.length)).catch(() => {});
  }, []);

  const handleSearch = async () => {
    if (!searchQuery.trim()) { alert('Please enter a search query'); return; }
    setSearching(true);
    setSearchResults([]);
    setCollatedResults([]);
    try {
      const data = await api.post('/search', { query: searchQuery });
      setSearchResults(data.results);
    } catch (e) {
      alert(e.response?.data?.detail || 'Search failed');
    } finally { setSearching(false); }
  };

  const handleCollate = async () => {
    if (searchResults.length === 0) { alert('No search results to collate'); return; }
    if (categoriesCount === 0) { alert('Please create at least one category with a protocol before collating.'); return; }
    setCollating(true);
    try {
      const data = await api.post('/collate', { search_results: searchResults });
      setCollatedResults(data.results);
      if (data.collated_count === 0) {
        alert('No search results matched your category protocols. Try adjusting your protocols or search query.');
      } else {
        alert(`${data.collated_count} results were categorized and saved to your database.`);
      }
    } catch (e) {
      if (e.response?.status === 429) alert(e.response.data.detail);
      else alert(e.response?.data?.detail || 'Collation failed');
    } finally { setCollating(false); }
  };

  return (
    <>
      <div className="page-header">
        <h1><Icons.Globe /> InfoPilot Search</h1>
        <button className="btn btn-outline" onClick={() => setShowOperators(!showOperators)} style={{width: 'auto', padding: '8px 16px'}}>
          <Icons.Code /> Operators
        </button>
      </div>
      <div className="page-content">
        {showOperators && (
          <div className="operators-panel">
            {operators.map((item, idx) => (
              <div key={idx} className="operator-chip" onClick={() => setSearchQuery(prev => prev + (prev ? ' ' : '') + item.op)}>
                <div className="op">{item.op}</div>
                <div className="desc">{item.desc}</div>
              </div>
            ))}
          </div>
        )}

        <div className="info-box">
          <Icons.Info />
          <p>You have {categoriesCount} categories. Search the web and click "Collate" to automatically categorize results based on your protocols.</p>
        </div>

        <div className="search-bar">
          <Icons.Search />
          <input type="text" placeholder="Enter your search query..." value={searchQuery} onChange={(e) => setSearchQuery(e.target.value)} onKeyPress={(e) => e.key === 'Enter' && handleSearch()} />
        </div>

        <div className="button-row">
          <button className="btn btn-primary" onClick={handleSearch} disabled={searching}>
            {searching ? <div className="spinner" style={{width: 20, height: 20}}/> : <><Icons.Search /> Search</>}
          </button>
          <button className="btn btn-success" onClick={handleCollate} disabled={collating || searchResults.length === 0}>
            {collating ? <div className="spinner" style={{width: 20, height: 20}}/> : <><Icons.Layers /> Collate</>}
          </button>
        </div>

        {collatedResults.length > 0 && (
          <div style={{marginTop: 24}}>
            <div className="section-title" style={{color: '#4CAF50'}}><Icons.Check /> Collated Results ({collatedResults.length})</div>
            {collatedResults.map((result, idx) => (
              <div key={idx} className="collated-card">
                <div className="collated-header">
                  <div className="collated-title">{result.title}</div>
                  <span className="badge badge-success">{result.article_type}</span>
                </div>
                <div className="categories-row"><Icons.Folder /> {result.matching_categories?.join(', ')}</div>
              </div>
            ))}
          </div>
        )}

        {searchResults.length > 0 && (
          <div style={{marginTop: 24}}>
            <div className="section-title"><Icons.Search /> Search Results ({searchResults.length})</div>
            {searchResults.map((result, idx) => (
              <div key={idx} className="result-card">
                <div style={{display: 'flex', gap: 12}}>
                  <div className="level-indicator">{idx + 1}</div>
                  <div style={{flex: 1}}>
                    <a href={result.url} target="_blank" rel="noopener noreferrer" className="result-title">{result.title}</a>
                    <div className="result-domain">{result.url}</div>
                    <div className="result-snippet">{result.snippet}</div>
                  </div>
                </div>
              </div>
            ))}
          </div>
        )}

        {searchResults.length === 0 && !searching && (
          <div className="empty-state">
            <Icons.Globe />
            <h3>Ready to Search</h3>
            <p>Enter a search query above and press Search. Then click Collate to automatically categorize results using your InfoPilot 2.0 protocols.</p>
          </div>
        )}
      </div>
    </>
  );
}

// Categories Page
function CategoriesPage() {
  const [categories, setCategories] = useState([]);
  const [loading, setLoading] = useState(true);
  const [modalOpen, setModalOpen] = useState(false);
  const [editingCategory, setEditingCategory] = useState(null);
  const [name, setName] = useState('');
  const [protocol, setProtocol] = useState('');
  const [isPublic, setIsPublic] = useState(false);
  const [parentId, setParentId] = useState(null);
  const [saving, setSaving] = useState(false);

  useEffect(() => { loadCategories(); }, []);

  const loadCategories = async () => {
    try { const data = await api.get('/categories'); setCategories(data); } catch (e) { console.error(e); } finally { setLoading(false); }
  };

  const openCreateModal = (parent) => {
    setEditingCategory(null);
    setName('');
    setProtocol('');
    setIsPublic(false);
    setParentId(parent?.id || null);
    setModalOpen(true);
  };

  const openEditModal = (category) => {
    setEditingCategory(category);
    setName(category.name);
    setProtocol(category.protocol);
    setIsPublic(category.is_public);
    setParentId(category.parent_id || null);
    setModalOpen(true);
  };

  const handleSave = async () => {
    if (!name.trim()) { alert('Please enter a category name'); return; }
    if (!protocol.trim()) { alert('Please enter a protocol'); return; }
    setSaving(true);
    try {
      if (editingCategory) {
        await api.put(`/categories/${editingCategory.id}`, { name: name.trim(), protocol: protocol.trim(), is_public: isPublic });
        alert('Category updated!');
      } else {
        await api.post('/categories', { name: name.trim(), protocol: protocol.trim(), is_public: isPublic, parent_id: parentId });
        alert('Category created!');
      }
      setModalOpen(false);
      loadCategories();
    } catch (e) {
      alert(e.response?.data?.detail || 'Could not save category');
    } finally { setSaving(false); }
  };

  const handleDelete = async (category) => {
    if (!window.confirm(`Delete "${category.name}" and all its subcategories?`)) return;
    try { await api.delete(`/categories/${category.id}`); loadCategories(); } catch (e) { alert(e.response?.data?.detail || 'Could not delete category'); }
  };

  const rootCategories = categories.filter(c => !c.parent_id);
  const getChildren = (parentId) => categories.filter(c => c.parent_id === parentId);

  const renderCategory = (category, depth = 0) => {
    const children = getChildren(category.id);
    return (
      <div key={category.id}>
        <div className="category-card" style={{marginLeft: depth * 20}}>
          <div className="category-header">
            <div className="category-info">
              <div className="level-indicator">L{category.level}</div>
              <div className="category-details">
                <div className="category-name-row">
                  <span className="category-name">{category.name}</span>
                  {category.is_public && <span className="badge badge-success"><Icons.Globe /> Public</span>}
                </div>
                <div className="protocol-text">{category.protocol}</div>
              </div>
            </div>
            <div className="category-actions">
              <button className="action-btn" onClick={() => openCreateModal(category)}><Icons.Plus /></button>
              <button className="action-btn" onClick={() => openEditModal(category)}><Icons.Pencil /></button>
              <button className="action-btn danger" onClick={() => handleDelete(category)}><Icons.Trash /></button>
            </div>
          </div>
        </div>
        {children.map(child => renderCategory(child, depth + 1))}
      </div>
    );
  };

  const parentName = parentId ? categories.find(c => c.id === parentId)?.name : null;

  return (
    <>
      <div className="page-header">
        <h1><Icons.Folder /> Categories & Protocols</h1>
        <button className="btn btn-primary" onClick={() => openCreateModal()} style={{width: 'auto', padding: '12px 20px'}}>
          <Icons.Plus /> New Category
        </button>
      </div>
      <div className="page-content">
        <div className="help-card">
          <h4>Protocol Format:</h4>
          <code>(word1 or word2) & (word3 or word4)+ & (exclude1)^</code>
          <p>• Words in parentheses with "or" = any match<br/>• & = AND (all groups must match)<br/>• + = Include ALL words in group<br/>• ^ = EXCLUDE all words in group</p>
        </div>

        {loading ? <div className="loading"><div className="spinner"/></div> :
          categories.length === 0 ? (
            <div className="empty-state">
              <Icons.Folder />
              <h3>No Categories Yet</h3>
              <p>Create your first category with an InfoPilot 2.0 protocol to start organizing your search results!</p>
              <button className="btn btn-primary" onClick={() => openCreateModal()} style={{width: 'auto', marginTop: 16}}>
                <Icons.Plus /> Create First Category
              </button>
            </div>
          ) : rootCategories.map(cat => renderCategory(cat))
        }
      </div>

      {modalOpen && (
        <div className="modal-overlay" onClick={() => setModalOpen(false)}>
          <div className="modal-content" onClick={(e) => e.stopPropagation()}>
            <div className="modal-header">
              <h3>{editingCategory ? 'Edit Category' : 'New Category'}</h3>
              <button className="modal-close" onClick={() => setModalOpen(false)}><Icons.X /></button>
            </div>
            <div className="modal-body">
              {parentName && (
                <div className="info-box success" style={{marginBottom: 16}}>
                  <Icons.Folder />
                  <p>Subcategory of: {parentName}</p>
                </div>
              )}
              <div className="form-group">
                <label>Category Name</label>
                <input type="text" placeholder="e.g., American Civil War" value={name} onChange={(e) => setName(e.target.value)} style={{width: '100%', padding: '12px 14px', border: '1px solid #E0E0E0', borderRadius: 10, fontSize: 15}} />
              </div>
              <div className="form-group">
                <label>Protocol (InfoPilot 2.0)</label>
                <textarea placeholder="(word1 or word2) & (word3)+ & (exclude)^" value={protocol} onChange={(e) => setProtocol(e.target.value)} />
              </div>
              <div className="examples-card">
                <h5>Examples:</h5>
                <div className="example-item" onClick={() => setProtocol("(American civil war) & (civil war) & (1860 or 1861 or 1862 or 1863 or 1864 or 1865)+")}>American Civil War - Basic</div>
                <div className="example-item" onClick={() => setProtocol("(heroically or hero or helped solve) & (good citizen or citizenship) & (Gettysburg or Princeton) & (isn't or wasn't)^")}>Heroes - With Exclusion</div>
              </div>
              <div className="checkbox-row" onClick={() => setIsPublic(!isPublic)}>
                <div className={`checkbox ${isPublic ? 'checked' : ''}`}>{isPublic && <Icons.Check />}</div>
                <div className="checkbox-label">
                  <div className="label">Make Public</div>
                  <div className="desc">Other users can see and use this category</div>
                </div>
              </div>
              <div className="info-box success" style={{marginTop: 16}}>
                <Icons.Shield />
                <p>We encourage you to keep your categories private for security.</p>
              </div>
              <button className="btn btn-primary" onClick={handleSave} disabled={saving} style={{marginTop: 20}}>
                {saving ? <div className="spinner" style={{width: 20, height: 20}}/> : 'Save Category'}
              </button>
            </div>
          </div>
        </div>
      )}
    </>
  );
}

// Map Page with Leaflet
function MapPage() {
  const { user } = useAuth();
  const [markers, setMarkers] = useState([]);
  const [loading, setLoading] = useState(true);
  const [selectedMarker, setSelectedMarker] = useState(null);
  const [categories, setCategories] = useState([]);
  const [selectedCategories, setSelectedCategories] = useState([]);

  useEffect(() => {
    loadData();
  }, []);

  useEffect(() => {
    // Reload markers when categories change
    if (selectedCategories.length > 0) {
      loadMapMarkers();
    }
  }, [selectedCategories]);

  const loadData = async () => {
    try {
      const [markersData, catsData] = await Promise.all([
        api.get('/map-data'),
        api.get('/categories')
      ]);
      setMarkers(markersData.markers || []);
      setCategories(catsData || []);
    } catch (e) {
      console.error(e);
    } finally {
      setLoading(false);
    }
  };

  const loadMapMarkers = async () => {
    try {
      const params = selectedCategories.length > 0 
        ? { category_ids: selectedCategories.join(',') }
        : {};
      const data = await api.get('/map-data', params);
      setMarkers(data.markers || []);
    } catch (e) {
      console.error(e);
    }
  };

  const toggleCategory = (catId) => {
    setSelectedCategories(prev => 
      prev.includes(catId) 
        ? prev.filter(id => id !== catId)
        : [...prev, catId]
    );
  };

  const getCategoryColor = (categoryName) => {
    const idx = categories.findIndex(c => c.name === categoryName);
    return categoryColors[idx % categoryColors.length];
  };

  const handleSubscribe = () => {
    if (window.confirm('Subscribe to InfoPilot Premium for $0.99?\n\n• Unlimited search result pages\n• Interactive world map\n• All premium features')) {
      window.open('https://py.pl/vdf9TkEwfV1ngxIsu9JzlQ', '_blank');
    }
  };

  if (!user?.is_paid) {
    return (
      <>
        <div className="page-header"><h1><Icons.Map /> World Map</h1></div>
        <div className="page-content">
          {/* Premium Upsell with Globe Image */}
          <div style={{
            background: 'linear-gradient(135deg, rgba(5, 5, 16, 0.95) 0%, rgba(15, 23, 42, 0.95) 100%)',
            border: '1px solid rgba(59, 130, 246, 0.3)',
            borderRadius: '24px',
            padding: '40px',
            textAlign: 'center',
            position: 'relative',
            overflow: 'hidden'
          }}>
            {/* Globe background */}
            <div style={{
              position: 'absolute',
              top: 0,
              left: 0,
              right: 0,
              bottom: 0,
              backgroundImage: `url(${premiumImage})`,
              backgroundSize: 'cover',
              backgroundPosition: 'center',
              opacity: 0.15,
              filter: 'blur(2px)'
            }} />
            
            <div style={{position: 'relative', zIndex: 1}}>
              <div style={{
                width: '120px',
                height: '120px',
                borderRadius: '50%',
                overflow: 'hidden',
                margin: '0 auto 24px',
                boxShadow: '0 0 40px rgba(59, 130, 246, 0.5)',
                border: '3px solid rgba(59, 130, 246, 0.5)'
              }}>
                <img 
                  src={premiumImage}
                  alt="Global Network"
                  style={{width: '100%', height: '100%', objectFit: 'cover'}}
                />
              </div>
              
              <h3 style={{
                fontFamily: "'Unbounded', sans-serif",
                fontSize: '28px',
                fontWeight: 800,
                background: 'linear-gradient(135deg, #3B82F6 0%, #8B5CF6 100%)',
                WebkitBackgroundClip: 'text',
                WebkitTextFillColor: 'transparent',
                marginBottom: '12px'
              }}>Unlock the World Map</h3>
              
              <p style={{
                fontSize: '16px',
                color: '#94A3B8',
                maxWidth: '400px',
                margin: '0 auto 24px',
                lineHeight: 1.7
              }}>
                Visualize your research on an interactive globe. See where your information comes from across the world.
              </p>
              
              <div style={{
                display: 'flex',
                justifyContent: 'center',
                gap: '16px',
                marginBottom: '24px',
                flexWrap: 'wrap'
              }}>
                {['Interactive Markers', 'Category Colors', 'One-Click Sources'].map((feature, i) => (
                  <span key={i} style={{
                    background: 'rgba(59, 130, 246, 0.15)',
                    border: '1px solid rgba(59, 130, 246, 0.3)',
                    borderRadius: '20px',
                    padding: '8px 16px',
                    fontSize: '12px',
                    fontWeight: 600,
                    color: '#60A5FA'
                  }}>{feature}</span>
                ))}
              </div>
              
              <button 
                className="btn btn-primary"
                onClick={handleSubscribe}
                style={{
                  width: 'auto',
                  padding: '16px 32px',
                  fontSize: '16px',
                  background: 'linear-gradient(135deg, #3B82F6 0%, #8B5CF6 100%)'
                }}
              >
                <Icons.Rocket /> Upgrade for Only $0.99
              </button>
            </div>
          </div>
          
          {/* Book promo below */}
          <div style={{marginTop: 24}}>
            <BookPromoSection variant="compact" />
          </div>
        </div>
      </>
    );
  }

  return (
    <>
      <div className="page-header"><h1><Icons.Map /> World Map</h1></div>
      <div className="page-content">
        {/* Category Filters */}
        {categories.length > 0 && (
          <div className="category-chips" style={{marginBottom: 16}}>
            {categories.map((cat, idx) => (
              <span 
                key={cat.id} 
                className={`chip ${selectedCategories.includes(cat.id) ? 'chip-selected' : 'chip-default'}`}
                style={{
                  borderLeft: `4px solid ${categoryColors[idx % categoryColors.length]}`,
                }}
                onClick={() => toggleCategory(cat.id)}
              >
                {cat.name}
              </span>
            ))}
          </div>
        )}

        {loading ? <div className="loading"><div className="spinner"/></div> : (
          <>
            {/* Interactive Leaflet Map */}
            <div style={{ height: '450px', borderRadius: '16px', overflow: 'hidden', marginBottom: '24px', border: '1px solid rgba(139, 92, 246, 0.3)', boxShadow: '0 0 30px rgba(139, 92, 246, 0.1)' }}>
              <MapContainer
                center={[20, 0]}
                zoom={2}
                style={{ height: '100%', width: '100%' }}
                scrollWheelZoom={true}
              >
                <TileLayer
                  attribution='&copy; <a href="https://www.openstreetmap.org/copyright">OpenStreetMap</a>'
                  url="https://{s}.basemaps.cartocdn.com/dark_all/{z}/{x}/{y}{r}.png"
                />
                {markers.filter(m => m.latitude && m.longitude).map((marker, idx) => (
                  <Marker 
                    key={marker.id || idx}
                    position={[marker.latitude, marker.longitude]}
                    icon={createColoredIcon(getCategoryColor(marker.categories?.[0]))}
                    eventHandlers={{
                      click: () => {
                        window.open(marker.url, '_blank');
                      }
                    }}
                  >
                    <Popup>
                      <div style={{minWidth: '200px'}}>
                        <h4 style={{margin: '0 0 8px 0', fontSize: '14px', color: '#333'}}>{marker.title}</h4>
                        <div style={{fontSize: '12px', color: '#666', marginBottom: '8px'}}>
                          {marker.categories?.map((cat, i) => (
                            <span key={i} style={{
                              display: 'inline-block',
                              background: getCategoryColor(cat),
                              color: 'white',
                              padding: '2px 8px',
                              borderRadius: '12px',
                              marginRight: '4px',
                              fontSize: '10px'
                            }}>{cat}</span>
                          ))}
                        </div>
                        <a href={marker.url} target="_blank" rel="noopener noreferrer" style={{color: '#8B5CF6', fontSize: '12px'}}>
                          Open Article →
                        </a>
                      </div>
                    </Popup>
                  </Marker>
                ))}
              </MapContainer>
            </div>

            {/* Stats */}
            <div className="stats-bar" style={{marginBottom: 20}}>
              <div className="stat-item">
                <div className="value">{markers.filter(m => m.latitude).length}</div>
                <div className="label">Locations</div>
              </div>
              <div className="stat-item">
                <div className="value">{markers.length}</div>
                <div className="label">Total Results</div>
              </div>
              <div className="stat-item">
                <div className="value">{new Set(markers.flatMap(m => m.categories || [])).size}</div>
                <div className="label">Categories</div>
              </div>
            </div>

            {/* Results List */}
            {markers.length === 0 ? (
              <div className="empty-state">
                <Icons.Location />
                <h3>No Location Data Yet</h3>
                <p>Search and collate web content to see location markers on the map. Location data is automatically extracted from articles when available.</p>
              </div>
            ) : (
              <>
                <div className="section-title">Location Results ({markers.length})</div>
                {markers.slice(0, 20).map((marker, idx) => (
                  <div key={marker.id || idx} className="marker-card" onClick={() => {
                    setSelectedMarker(marker);
                  }}>
                    <div className="marker-icon" style={{background: marker.latitude ? getCategoryColor(marker.categories?.[0]) : '#ccc'}}>
                      <Icons.Location />
                    </div>
                    <div className="marker-info">
                      <div className="marker-title">{marker.title}</div>
                      {marker.latitude && marker.longitude ? (
                        <div className="marker-coords">{marker.latitude?.toFixed(4)}, {marker.longitude?.toFixed(4)}</div>
                      ) : (
                        <div className="marker-coords" style={{color: '#999'}}>No coordinates available</div>
                      )}
                      <div className="result-categories">
                        {marker.categories?.slice(0, 2).map((cat, i) => (
                          <span key={i} className="badge badge-primary" style={{background: getCategoryColor(cat)}}>{cat}</span>
                        ))}
                      </div>
                    </div>
                    <a href={marker.url} target="_blank" rel="noopener noreferrer" onClick={(e) => e.stopPropagation()} style={{color: '#2196F3'}}>
                      <Icons.ExternalLink />
                    </a>
                  </div>
                ))}
              </>
            )}
          </>
        )}
      </div>

      {selectedMarker && (
        <div className="modal-overlay" onClick={() => setSelectedMarker(null)}>
          <div className="modal-content" onClick={(e) => e.stopPropagation()} style={{maxWidth: '500px'}}>
            <button className="modal-close" onClick={() => setSelectedMarker(null)} style={{position: 'absolute', right: 12, top: 12}}><Icons.X /></button>
            <div style={{textAlign: 'center', paddingTop: 20}}>
              <div style={{color: getCategoryColor(selectedMarker.categories?.[0]), marginBottom: 12}}>
                <Icons.Location style={{width: 48, height: 48}}/>
              </div>
              <h3>{selectedMarker.title}</h3>
              {selectedMarker.latitude && selectedMarker.longitude && (
                <p style={{color: '#666', fontSize: 12, marginTop: 8}}>
                  📍 {selectedMarker.latitude?.toFixed(6)}, {selectedMarker.longitude?.toFixed(6)}
                </p>
              )}
              <p style={{fontSize: 14, color: '#666', margin: '12px 0', lineHeight: 1.5}}>
                {selectedMarker.snippet}
              </p>
              <div style={{display: 'flex', gap: 8, justifyContent: 'center', flexWrap: 'wrap', marginTop: 12}}>
                {selectedMarker.categories?.map((cat, idx) => (
                  <span key={idx} className="badge badge-primary" style={{background: getCategoryColor(cat)}}>{cat}</span>
                ))}
              </div>
              <a href={selectedMarker.url} target="_blank" rel="noopener noreferrer" className="btn btn-primary" style={{marginTop: 20, width: 'auto', display: 'inline-flex'}}>
                <Icons.ExternalLink /> Open Article
              </a>
            </div>
          </div>
        </div>
      )}
    </>
  );
}

// Social Page with Groups, Pages, and Feed
function SocialPage() {
  const { user } = useAuth();
  const [activeTab, setActiveTab] = useState('feed');
  const [friends, setFriends] = useState([]);
  const [pendingRequests, setPendingRequests] = useState([]);
  const [groups, setGroups] = useState([]);
  const [pages, setPages] = useState([]);
  const [feed, setFeed] = useState([]);
  const [loading, setLoading] = useState(true);
  const [selectedFriend, setSelectedFriend] = useState(null);
  const [messages, setMessages] = useState([]);
  const [newMessage, setNewMessage] = useState('');
  const [unreadCount, setUnreadCount] = useState(0);
  const [showCreateModal, setShowCreateModal] = useState(null); // 'group', 'page', 'post'
  const [newContent, setNewContent] = useState({ name: '', description: '', content: '', isPublic: true });

  useEffect(() => { loadAllData(); }, []);

  const loadAllData = async () => {
    setLoading(true);
    try {
      const [friendsData, groupsData, pagesData, feedData, unreadData] = await Promise.all([
        api.get('/friends').catch(() => ({ friends: [], pending_requests: [] })),
        api.get('/groups').catch(() => []),
        api.get('/pages').catch(() => []),
        api.get('/feed').catch(() => []),
        api.get('/messages/unread/count').catch(() => ({ unread_count: 0 }))
      ]);
      setFriends(friendsData.friends || []);
      setPendingRequests(friendsData.pending_requests || []);
      setGroups(groupsData || []);
      setPages(pagesData || []);
      setFeed(feedData || []);
      setUnreadCount(unreadData.unread_count || 0);
    } catch (e) {
      console.error(e);
    } finally {
      setLoading(false);
    }
  };

  const handleAccept = async (id) => {
    try { 
      await api.post('/friends/accept', { target_user_id: id }); 
      alert('Friend request accepted!'); 
      loadAllData(); 
    } catch (e) { 
      alert(e.response?.data?.detail || 'Could not accept request'); 
    }
  };

  const handleReject = async (id) => {
    try { 
      await api.post('/friends/reject', { target_user_id: id }); 
      loadAllData(); 
    } catch (e) { 
      alert(e.response?.data?.detail || 'Could not reject request'); 
    }
  };

  const handleRemove = async (friend) => {
    if (!window.confirm(`Remove ${friend.username} from your friends?`)) return;
    try { 
      await api.delete(`/friends/${friend.id}`); 
      loadAllData(); 
    } catch (e) { 
      alert('Could not remove friend'); 
    }
  };

  const openChat = async (friend) => {
    setSelectedFriend(friend);
    try { 
      const data = await api.get(`/messages/${friend.id}`); 
      setMessages(data.messages || []); 
      loadAllData(); 
    } catch (e) { 
      console.error(e); 
    }
  };

  const sendMessage = async () => {
    if (!newMessage.trim() || !selectedFriend) return;
    try { 
      await api.post('/messages', { recipient_id: selectedFriend.id, content: newMessage.trim() }); 
      setNewMessage(''); 
      const data = await api.get(`/messages/${selectedFriend.id}`); 
      setMessages(data.messages || []); 
    } catch (e) { 
      alert(e.response?.data?.detail || 'Could not send message'); 
    }
  };

  const createGroup = async () => {
    try {
      await api.post('/groups', {
        name: newContent.name,
        description: newContent.description,
        is_public: newContent.isPublic
      });
      setShowCreateModal(null);
      setNewContent({ name: '', description: '', content: '', isPublic: true });
      loadAllData();
      alert('Group created!');
    } catch (e) {
      alert(e.response?.data?.detail || 'Could not create group');
    }
  };

  const createPage = async () => {
    try {
      await api.post('/pages', {
        name: newContent.name,
        description: newContent.description
      });
      setShowCreateModal(null);
      setNewContent({ name: '', description: '', content: '', isPublic: true });
      loadAllData();
      alert('Page created!');
    } catch (e) {
      alert(e.response?.data?.detail || 'Could not create page');
    }
  };

  const createPost = async () => {
    try {
      await api.post('/posts', {
        content: newContent.content
      });
      setShowCreateModal(null);
      setNewContent({ name: '', description: '', content: '', isPublic: true });
      loadAllData();
    } catch (e) {
      alert(e.response?.data?.detail || 'Could not create post');
    }
  };

  const joinGroup = async (groupId) => {
    try {
      await api.post(`/groups/${groupId}/join`);
      loadAllData();
    } catch (e) {
      alert(e.response?.data?.detail || 'Could not join group');
    }
  };

  const leaveGroup = async (groupId) => {
    try {
      await api.post(`/groups/${groupId}/leave`);
      loadAllData();
    } catch (e) {
      alert(e.response?.data?.detail || 'Could not leave group');
    }
  };

  const followPage = async (pageId) => {
    try {
      await api.post(`/pages/${pageId}/follow`);
      loadAllData();
    } catch (e) {
      alert(e.response?.data?.detail || 'Could not follow/unfollow page');
    }
  };

  const reactToPost = async (postId, reactionType) => {
    try {
      await api.post(`/posts/${postId}/react`, { reaction_type: reactionType });
      loadAllData();
    } catch (e) {
      console.error(e);
    }
  };

  const tabs = [
    { id: 'feed', label: 'Feed', icon: Icons.Layers },
    { id: 'friends', label: 'Friends', icon: Icons.People },
    { id: 'groups', label: 'Groups', icon: Icons.Folder },
    { id: 'pages', label: 'Pages', icon: Icons.Star },
  ];

  return (
    <>
      <div className="page-header">
        <h1><Icons.People /> Social</h1>
        {unreadCount > 0 && <span className="badge" style={{background: '#f44336', color: 'white', padding: '6px 12px'}}>{unreadCount} unread</span>}
      </div>
      <div className="page-content">
        {/* Tabs */}
        <div style={{display: 'flex', gap: 8, marginBottom: 20, overflowX: 'auto'}}>
          {tabs.map(tab => (
            <button 
              key={tab.id}
              className={`chip ${activeTab === tab.id ? 'chip-selected' : 'chip-default'}`}
              onClick={() => setActiveTab(tab.id)}
              style={{padding: '10px 16px', display: 'flex', alignItems: 'center', gap: 6}}
            >
              <tab.icon /> {tab.label}
            </button>
          ))}
        </div>

        {loading ? <div className="loading"><div className="spinner"/></div> : (
          <>
            {/* Feed Tab */}
            {activeTab === 'feed' && (
              <>
                {/* Create Post */}
                <div className="card" style={{marginBottom: 20}}>
                  <div className="card-body" style={{display: 'flex', gap: 12, alignItems: 'center'}}>
                    <div className="user-avatar">{user?.username?.[0]?.toUpperCase()}</div>
                    <input 
                      type="text" 
                      placeholder="What's on your mind?" 
                      style={{flex: 1, padding: '12px', border: '1px solid #E0E0E0', borderRadius: 20, fontSize: 14}}
                      onClick={() => setShowCreateModal('post')}
                      readOnly
                    />
                  </div>
                </div>

                {feed.length === 0 ? (
                  <div className="empty-state">
                    <Icons.Layers />
                    <h3>Your Feed is Empty</h3>
                    <p>Join groups, follow pages, and make friends to see posts here!</p>
                  </div>
                ) : feed.map(post => (
                  <PostCard key={post.id} post={post} onReact={reactToPost} currentUserId={user?.id} />
                ))}
              </>
            )}

            {/* Friends Tab */}
            {activeTab === 'friends' && (
              <>
                {pendingRequests.length > 0 && (
                  <div style={{marginBottom: 24}}>
                    <div className="section-title">Friend Requests ({pendingRequests.length})</div>
                    {pendingRequests.map(req => (
                      <div key={req.id} className="request-card">
                        <div className="request-avatar">{req.username[0]?.toUpperCase()}</div>
                        <div className="request-name">@{req.username}</div>
                        <div className="request-actions">
                          <button className="request-btn accept" onClick={() => handleAccept(req.id)}><Icons.Check /></button>
                          <button className="request-btn reject" onClick={() => handleReject(req.id)}><Icons.X /></button>
                        </div>
                      </div>
                    ))}
                  </div>
                )}

                <div className="section-title">Friends ({friends.length})</div>
                {friends.length === 0 ? (
                  <div className="empty-state">
                    <Icons.People />
                    <h3>No Friends Yet</h3>
                    <p>Make friends by reacting to search results on other users' public Ultimate Search Pages.</p>
                  </div>
                ) : friends.map(friend => (
                  <div key={friend.id} className="friend-card">
                    <div className="friend-avatar">{friend.username[0]?.toUpperCase()}</div>
                    <div className="friend-info">
                      <div className="friend-name">@{friend.username}</div>
                      {friend.ultimate_search_public && <span style={{fontSize: 11, color: '#4CAF50'}}><Icons.Globe /> Public USP</span>}
                    </div>
                    <div className="friend-actions">
                      <button className="friend-btn chat" onClick={() => openChat(friend)}><Icons.Chat /></button>
                      <button className="friend-btn remove" onClick={() => handleRemove(friend)}><Icons.Trash /></button>
                    </div>
                  </div>
                ))}
              </>
            )}

            {/* Groups Tab */}
            {activeTab === 'groups' && (
              <>
                <button className="btn btn-primary" onClick={() => setShowCreateModal('group')} style={{marginBottom: 20}}>
                  <Icons.Plus /> Create Group
                </button>

                {groups.length === 0 ? (
                  <div className="empty-state">
                    <Icons.Folder />
                    <h3>No Groups Yet</h3>
                    <p>Create or join groups to connect with others!</p>
                  </div>
                ) : groups.map(group => (
                  <div key={group.id} className="card" style={{marginBottom: 12}}>
                    <div className="card-body" style={{display: 'flex', alignItems: 'center', gap: 12}}>
                      <div style={{width: 50, height: 50, borderRadius: 10, background: '#E3F2FD', display: 'flex', alignItems: 'center', justifyContent: 'center', color: '#2196F3'}}>
                        <Icons.Folder />
                      </div>
                      <div style={{flex: 1}}>
                        <div style={{fontWeight: 600}}>{group.name}</div>
                        <div style={{fontSize: 12, color: '#666'}}>{group.member_count} members</div>
                        {group.description && <div style={{fontSize: 12, color: '#999', marginTop: 4}}>{group.description}</div>}
                      </div>
                      {group.is_member ? (
                        <button className="btn btn-outline" style={{width: 'auto', padding: '8px 16px'}} onClick={() => leaveGroup(group.id)}>
                          Leave
                        </button>
                      ) : (
                        <button className="btn btn-primary" style={{width: 'auto', padding: '8px 16px'}} onClick={() => joinGroup(group.id)}>
                          Join
                        </button>
                      )}
                    </div>
                  </div>
                ))}
              </>
            )}

            {/* Pages Tab */}
            {activeTab === 'pages' && (
              <>
                <button className="btn btn-success" onClick={() => setShowCreateModal('page')} style={{marginBottom: 20}}>
                  <Icons.Plus /> Create Page
                </button>

                {pages.length === 0 ? (
                  <div className="empty-state">
                    <Icons.Star />
                    <h3>No Pages Yet</h3>
                    <p>Create a page to share your interests!</p>
                  </div>
                ) : pages.map(page => (
                  <div key={page.id} className="card" style={{marginBottom: 12}}>
                    <div className="card-body" style={{display: 'flex', alignItems: 'center', gap: 12}}>
                      <div style={{width: 50, height: 50, borderRadius: '50%', background: '#FFF3E0', display: 'flex', alignItems: 'center', justifyContent: 'center', color: '#FF9800'}}>
                        <Icons.Star />
                      </div>
                      <div style={{flex: 1}}>
                        <div style={{fontWeight: 600}}>{page.name}</div>
                        <div style={{fontSize: 12, color: '#666'}}>{page.follower_count} followers</div>
                        {page.description && <div style={{fontSize: 12, color: '#999', marginTop: 4}}>{page.description}</div>}
                      </div>
                      <button 
                        className={`btn ${page.is_following ? 'btn-outline' : 'btn-primary'}`} 
                        style={{width: 'auto', padding: '8px 16px'}} 
                        onClick={() => followPage(page.id)}
                      >
                        {page.is_following ? 'Following' : 'Follow'}
                      </button>
                    </div>
                  </div>
                ))}
              </>
            )}
          </>
        )}

        <div className="info-box" style={{marginTop: 24}}>
          <Icons.Info />
          <p>Friend requests can be made by viewing other users' public Ultimate Search Pages and reacting to their content.</p>
        </div>
      </div>

      {/* Create Modal */}
      {showCreateModal && (
        <div className="modal-overlay" onClick={() => setShowCreateModal(null)}>
          <div className="modal-content" onClick={(e) => e.stopPropagation()}>
            <div className="modal-header">
              <h3>
                {showCreateModal === 'group' && 'Create Group'}
                {showCreateModal === 'page' && 'Create Page'}
                {showCreateModal === 'post' && 'Create Post'}
              </h3>
              <button className="modal-close" onClick={() => setShowCreateModal(null)}><Icons.X /></button>
            </div>
            <div className="modal-body">
              {(showCreateModal === 'group' || showCreateModal === 'page') && (
                <>
                  <div className="form-group">
                    <label>Name</label>
                    <input 
                      type="text" 
                      placeholder={`${showCreateModal === 'group' ? 'Group' : 'Page'} name`}
                      value={newContent.name}
                      onChange={(e) => setNewContent({...newContent, name: e.target.value})}
                      style={{width: '100%', padding: '12px', border: '1px solid #E0E0E0', borderRadius: 10}}
                    />
                  </div>
                  <div className="form-group">
                    <label>Description</label>
                    <textarea 
                      placeholder="Describe your group/page..."
                      value={newContent.description}
                      onChange={(e) => setNewContent({...newContent, description: e.target.value})}
                    />
                  </div>
                  {showCreateModal === 'group' && (
                    <div className="checkbox-row" onClick={() => setNewContent({...newContent, isPublic: !newContent.isPublic})}>
                      <div className={`checkbox ${newContent.isPublic ? 'checked' : ''}`}>{newContent.isPublic && <Icons.Check />}</div>
                      <div className="checkbox-label">
                        <div className="label">Public Group</div>
                        <div className="desc">Anyone can find and join this group</div>
                      </div>
                    </div>
                  )}
                  <button 
                    className="btn btn-primary" 
                    style={{marginTop: 20}}
                    onClick={showCreateModal === 'group' ? createGroup : createPage}
                  >
                    Create {showCreateModal === 'group' ? 'Group' : 'Page'}
                  </button>
                </>
              )}

              {showCreateModal === 'post' && (
                <>
                  <textarea 
                    placeholder="What's on your mind?"
                    value={newContent.content}
                    onChange={(e) => setNewContent({...newContent, content: e.target.value})}
                    style={{minHeight: 120}}
                    autoFocus
                  />
                  <button 
                    className="btn btn-primary" 
                    style={{marginTop: 20}}
                    onClick={createPost}
                    disabled={!newContent.content.trim()}
                  >
                    Post
                  </button>
                </>
              )}
            </div>
          </div>
        </div>
      )}

      {/* Chat Modal */}
      {selectedFriend && (
        <div className="modal-overlay" onClick={() => setSelectedFriend(null)}>
          <div className="modal-content" onClick={(e) => e.stopPropagation()} style={{maxWidth: 600, height: '80vh', display: 'flex', flexDirection: 'column'}}>
            <div className="modal-header">
              <div style={{display: 'flex', alignItems: 'center', gap: 12}}>
                <button style={{background: 'none', border: 'none', cursor: 'pointer'}} onClick={() => setSelectedFriend(null)}><Icons.ChevronLeft /></button>
                <div className="user-avatar">{selectedFriend.username[0]?.toUpperCase()}</div>
                <span style={{fontWeight: 600}}>@{selectedFriend.username}</span>
              </div>
            </div>
            <div className="messages-list" style={{flex: 1, overflowY: 'auto', padding: 20}}>
              {messages.length === 0 ? (
                <div className="empty-state"><Icons.Chat /><p>No messages yet</p></div>
              ) : messages.map(msg => (
                <div key={msg.id} className={`message-bubble ${msg.is_mine ? 'mine' : 'theirs'}`}>
                  <div>{msg.content}</div>
                  <div className="message-time">{new Date(msg.created_at).toLocaleTimeString([], { hour: '2-digit', minute: '2-digit' })}</div>
                </div>
              ))}
            </div>
            <div className="chat-input">
              <input type="text" placeholder="Type a message..." value={newMessage} onChange={(e) => setNewMessage(e.target.value)} onKeyPress={(e) => e.key === 'Enter' && sendMessage()} />
              <button onClick={sendMessage} disabled={!newMessage.trim()}><Icons.Send /></button>
            </div>
          </div>
        </div>
      )}
    </>
  );
}

// Post Card Component
function PostCard({ post, onReact, currentUserId }) {
  const [showComments, setShowComments] = useState(false);
  const [comments, setComments] = useState([]);
  const [newComment, setNewComment] = useState('');

  const reactions = [
    { type: 'Like', icon: '👍', label: 'Like' },
    { type: 'Love', icon: '❤️', label: 'Love' },
    { type: 'Funny', icon: '😂', label: 'Funny' },
    { type: 'Sad', icon: '😢', label: 'Sad' },
    { type: 'Caution', icon: '⚠️', label: 'Caution' },
    { type: 'Spam', icon: '🚫', label: 'Spam' },
    { type: 'Best', icon: '⭐', label: 'Best' },
  ];

  const loadComments = async () => {
    try {
      const data = await api.get('/comments', { post_id: post.id });
      setComments(data || []);
    } catch (e) {
      console.error(e);
    }
  };

  const submitComment = async () => {
    if (!newComment.trim()) return;
    try {
      await api.post('/comments', { post_id: post.id, content: newComment.trim() });
      setNewComment('');
      loadComments();
    } catch (e) {
      alert(e.response?.data?.detail || 'Could not post comment');
    }
  };

  const getTotalReactions = () => {
    return Object.values(post.reactions || {}).reduce((sum, arr) => sum + (arr?.length || 0), 0);
  };

  return (
    <div className="card" style={{marginBottom: 16}}>
      <div className="card-body">
        {/* Author */}
        <div style={{display: 'flex', alignItems: 'center', gap: 12, marginBottom: 12}}>
          <div className="user-avatar" style={{width: 44, height: 44, fontSize: 16}}>
            {post.author_username?.[0]?.toUpperCase()}
          </div>
          <div>
            <div style={{fontWeight: 600}}>@{post.author_username}</div>
            <div style={{fontSize: 11, color: '#999'}}>
              {new Date(post.created_at).toLocaleDateString()} at {new Date(post.created_at).toLocaleTimeString([], { hour: '2-digit', minute: '2-digit' })}
            </div>
          </div>
        </div>

        {/* Content */}
        <div style={{fontSize: 15, lineHeight: 1.5, marginBottom: 12}}>
          {post.content}
        </div>

        {/* Images */}
        {post.images?.length > 0 && (
          <div style={{display: 'flex', gap: 8, marginBottom: 12, flexWrap: 'wrap'}}>
            {post.images.map((img, idx) => (
              <img key={idx} src={img} alt="" style={{maxWidth: '100%', borderRadius: 8, maxHeight: 300}} />
            ))}
          </div>
        )}

        {/* Stats */}
        <div style={{display: 'flex', justifyContent: 'space-between', padding: '8px 0', borderTop: '1px solid #F0F0F0', borderBottom: '1px solid #F0F0F0', color: '#666', fontSize: 13}}>
          <span>{getTotalReactions()} reactions</span>
          <span onClick={() => { setShowComments(!showComments); if (!showComments) loadComments(); }} style={{cursor: 'pointer'}}>
            {post.comment_count || 0} comments
          </span>
        </div>

        {/* Reactions */}
        <div className="reaction-bar" style={{borderTop: 'none', paddingTop: 8}}>
          {reactions.map(r => {
            const count = post.reactions?.[r.type]?.length || 0;
            const isActive = post.reactions?.[r.type]?.includes(currentUserId);
            return (
              <button 
                key={r.type} 
                className={`reaction-btn ${isActive ? 'active' : ''}`}
                onClick={() => onReact(post.id, r.type)}
                title={r.label}
              >
                {r.icon} {count > 0 && count}
              </button>
            );
          })}
        </div>

        {/* Comments Section */}
        {showComments && (
          <div style={{marginTop: 12, paddingTop: 12, borderTop: '1px solid #F0F0F0'}}>
            {comments.map(comment => (
              <div key={comment.id} style={{display: 'flex', gap: 8, marginBottom: 12}}>
                <div className="user-avatar" style={{width: 32, height: 32, fontSize: 12}}>
                  {comment.author_username?.[0]?.toUpperCase()}
                </div>
                <div style={{flex: 1, background: '#F5F5F5', borderRadius: 12, padding: '8px 12px'}}>
                  <div style={{fontWeight: 600, fontSize: 13}}>@{comment.author_username}</div>
                  <div style={{fontSize: 14}}>{comment.content}</div>
                </div>
              </div>
            ))}
            <div style={{display: 'flex', gap: 8}}>
              <input 
                type="text" 
                placeholder="Write a comment..."
                value={newComment}
                onChange={(e) => setNewComment(e.target.value)}
                onKeyPress={(e) => e.key === 'Enter' && submitComment()}
                style={{flex: 1, padding: '10px 14px', border: '1px solid #E0E0E0', borderRadius: 20, fontSize: 14}}
              />
              <button 
                className="btn btn-primary" 
                style={{width: 'auto', padding: '10px 16px'}}
                onClick={submitComment}
                disabled={!newComment.trim()}
              >
                Post
              </button>
            </div>
          </div>
        )}
      </div>
    </div>
  );
}

// Settings Page
function SettingsPage() {
  const { user, logout, refreshUser } = useAuth();
  const [ultimateSearchPublic, setUltimateSearchPublic] = useState(user?.ultimate_search_public || false);
  const [friendsVisible, setFriendsVisible] = useState(user?.friends_visible || false);

  const handleToggle = async (setting, value) => {
    try {
      const params = {};
      if (setting === 'ultimate_search_public') { params.ultimate_search_public = value; setUltimateSearchPublic(value); }
      if (setting === 'friends_visible') { params.friends_visible = value; setFriendsVisible(value); }
      await api.put('/users/settings', params);
      await refreshUser();
    } catch (e) {
      alert('Could not update setting');
      if (setting === 'ultimate_search_public') setUltimateSearchPublic(!value);
      if (setting === 'friends_visible') setFriendsVisible(!value);
    }
  };

  const handleSubscribe = () => {
    if (window.confirm('Subscribe to InfoPilot Premium for $0.99?\n\n• Unlimited search result pages\n• Interactive world map\n• All premium features')) {
      window.open('https://py.pl/vdf9TkEwfV1ngxIsu9JzlQ', '_blank');
      setTimeout(() => {
        if (window.confirm('Did you complete your PayPal payment?')) {
          api.post('/payment/activate', {}).then(() => { refreshUser(); alert('Welcome to InfoPilot Premium!'); }).catch(() => alert('Could not activate premium'));
        }
      }, 2000);
    }
  };

  const handleLogout = () => {
    if (window.confirm('Are you sure you want to logout?')) {
      logout();
    }
  };

  return (
    <>
      <div className="page-header"><h1><Icons.Settings /> Settings</h1></div>
      <div className="page-content">
        <div className="section-title">Profile</div>
        <div className="profile-card" style={{marginBottom: 24}}>
          <div className="profile-avatar">{user?.username?.[0]?.toUpperCase() || 'U'}</div>
          <div className="profile-details">
            <h3>@{user?.username}</h3>
            <div className="email">{user?.email}</div>
            <div className="profile-badges">
              {user?.is_paid ? <span className="badge badge-premium"><Icons.Star /> Premium</span> : <span className="badge">Free Plan</span>}
              {user?.is_admin && <span className="badge" style={{background: '#7C4DFF', color: 'white'}}><Icons.Shield /> Admin</span>}
            </div>
          </div>
        </div>

        {!user?.is_paid && (
          <>
            <div className="section-title">Subscription</div>
            <div className="subscribe-card" onClick={handleSubscribe} style={{marginBottom: 24}}>
              <div className="subscribe-content">
                <Icons.Rocket />
                <div className="subscribe-text">
                  <h4>Upgrade to Premium</h4>
                  <p>Unlimited pages, world map, all features</p>
                  <div className="price-row"><span className="price-text">Only $0.99</span><span className="paypal-badge">PayPal</span></div>
                </div>
              </div>
              <Icons.ChevronRight />
            </div>
          </>
        )}

        {user?.is_paid && (
          <div className="premium-active-card" style={{marginBottom: 24}}>
            <Icons.Check />
            <div><h4>Premium Active</h4><p>Thank you for supporting InfoPilot!</p></div>
          </div>
        )}

        <div className="section-title">Privacy</div>
        <div className="toggle-row">
          <div className="toggle-info">
            <Icons.Globe />
            <div className="toggle-text"><div className="label">Public Ultimate Search</div><div className="desc">Allow others to view your Ultimate Search Page</div></div>
          </div>
          <div className={`toggle-switch ${ultimateSearchPublic ? 'active' : ''}`} onClick={() => handleToggle('ultimate_search_public', !ultimateSearchPublic)} />
        </div>
        <div className="toggle-row">
          <div className="toggle-info">
            <Icons.People />
            <div className="toggle-text"><div className="label">Show Friends List</div><div className="desc">Allow others to see your friends</div></div>
          </div>
          <div className={`toggle-switch ${friendsVisible ? 'active' : ''}`} onClick={() => handleToggle('friends_visible', !friendsVisible)} />
        </div>
        <div className="info-box success" style={{marginTop: 12}}>
          <Icons.Shield />
          <p>We encourage you to keep your Ultimate Search Page private for security.</p>
        </div>

        <div className="section-title" style={{marginTop: 24}}>From the Creator</div>
        <BookPromoSection variant="compact" />

        <div className="section-title">About</div>
        <div className="about-item"><Icons.Info /><span>About InfoPilot</span><Icons.ChevronRight /></div>
        <div className="about-item"><Icons.Globe /><span>Tutorial Video</span><Icons.ChevronRight /></div>
        <div className="about-item"><Icons.Shield /><span>Privacy Policy</span><Icons.ChevronRight /></div>

        <button className="btn btn-danger" onClick={handleLogout} style={{marginTop: 24}}>
          <Icons.LogOut /> Logout
        </button>

        <div className="footer">
          <p>InfoPilot v1.0.0</p>
          <p>Top Pilot Enterprises | Brunswick, Maine</p>
          <p>© 2025 John Selman</p>
        </div>
      </div>
    </>
  );
}

// Main Layout
function MainLayout({ currentPage, onNavigate }) {
  const { user, logout } = useAuth();

  const navItems = [
    { id: 'search', label: 'Search', icon: Icons.Search },
    { id: 'infojet', label: 'InfoJet', icon: Icons.Globe },
    { id: 'categories', label: 'Categories', icon: Icons.Folder },
    { id: 'map', label: 'Map', icon: Icons.Map },
    { id: 'social', label: 'Social', icon: Icons.People },
    { id: 'settings', label: 'Settings', icon: Icons.Settings },
  ];

  return (
    <div className="app-container">
      <aside className="sidebar">
        <div className="sidebar-header">
          <div className="logo-circle">IP</div>
          <div className="logo-text">
            <h1>InfoPilot</h1>
            <span>Your 3D View of the Internet</span>
          </div>
        </div>
        <nav className="sidebar-nav">
          {navItems.map(item => (
            <div key={item.id} className={`nav-item ${currentPage === item.id ? 'active' : ''}`} onClick={() => onNavigate(item.id)}>
              <item.icon />
              <span>{item.label}</span>
            </div>
          ))}
        </nav>
        <div className="sidebar-footer">
          <div className="user-card">
            <div className="user-avatar">{user?.username?.[0]?.toUpperCase() || 'U'}</div>
            <div className="user-info">
              <div className="name">@{user?.username}</div>
              <div className="email">{user?.email}</div>
            </div>
          </div>
        </div>
      </aside>
      <main className="main-content">
        {currentPage === 'search' && <UltimateSearchPage />}
        {currentPage === 'infojet' && <InfoJetPage />}
        {currentPage === 'categories' && <CategoriesPage />}
        {currentPage === 'map' && <MapPage />}
        {currentPage === 'social' && <SocialPage />}
        {currentPage === 'settings' && <SettingsPage />}
      </main>

      {/* Mobile Navigation */}
      <nav className="mobile-nav">
        {navItems.slice(0, 5).map(item => (
          <div key={item.id} className={`mobile-nav-item ${currentPage === item.id ? 'active' : ''}`} onClick={() => onNavigate(item.id)}>
            <item.icon />
            <span>{item.label}</span>
          </div>
        ))}
      </nav>
    </div>
  );
}

// App Root
function AppContent() {
  const { user, loading } = useAuth();
  const [currentPage, setCurrentPage] = useState('search');
  const [authPage, setAuthPage] = useState('login');

  if (loading) {
    return (
      <div className="splash-screen">
        <div className="logo-circle">IP</div>
        <h1>InfoPilot</h1>
        <p className="subtitle">World Wide Web Information Exchange</p>
        <p className="tagline">Your 3D View of the Internet</p>
        <div className="spinner" style={{marginTop: 24}}/>
        <p className="footer-text">Top Pilot Enterprises | Brunswick, Maine</p>
      </div>
    );
  }

  if (!user) {
    if (authPage === 'register') {
      return <RegisterPage onNavigate={setAuthPage} />;
    }
    return <LoginPage onNavigate={setAuthPage} />;
  }

  return <MainLayout currentPage={currentPage} onNavigate={setCurrentPage} />;
}

function App() {
  return (
    <AuthProvider>
      <AppContent />
    </AuthProvider>
  );
}

export default App;
