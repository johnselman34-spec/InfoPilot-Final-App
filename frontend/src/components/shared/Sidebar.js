import React, { useState } from 'react';
import { useAuth } from '../../contexts/AuthContext';
import { useTheme, ThemeToggle } from '../../contexts/ThemeContext';
import { ThemePresetGallery, ThemePreviewMode } from '../Theme';
import Icons from './Icons';
import NotificationBell from './NotificationBell';

const Sidebar = ({ currentPage, setCurrentPage, showToast }) => {
  const { user, logout } = useAuth();
  const { isDarkMode } = useTheme();
  const [isMobileMenuOpen, setIsMobileMenuOpen] = useState(false);
  const [showThemeGallery, setShowThemeGallery] = useState(false);
  const [showThemePreview, setShowThemePreview] = useState(false);

  const navItems = [
    { id: 'search', label: 'Ultimate Search', icon: Icons.Search },
    { id: 'marketplace', label: 'Marketplace', icon: Icons.Shop },
    { id: 'statistics', label: '📊 Statistics', icon: Icons.Chart },
    { id: 'chat', label: '💬 Chat', icon: Icons.Message },
    { id: 'achievements', label: 'Achievements', icon: Icons.Trophy },
    { id: 'social', label: 'Social', icon: Icons.Users },
    { id: 'map', label: 'Map View', icon: Icons.Map },
    { id: 'quotes', label: 'Quote Gallery', icon: Icons.Quote },
    { id: 'messages', label: 'Messages', icon: Icons.Message },
    { id: 'tutorials', label: '🎬 Tutorials', icon: Icons.Play },
    { id: 'settings', label: 'Settings', icon: Icons.Settings },
  ];

  const handleNavClick = (pageId) => {
    setCurrentPage(pageId);
    setIsMobileMenuOpen(false);
  };

  return (
    <>
      {/* Mobile Header */}
      <div className="md:hidden fixed top-0 left-0 right-0 z-50 bg-gray-900 border-b border-gray-700 px-4 py-3 flex items-center justify-between">
        <button
          onClick={() => setIsMobileMenuOpen(!isMobileMenuOpen)}
          className="p-2 text-gray-400 hover:text-white"
          data-testid="mobile-menu-btn"
        >
          <svg className="w-6 h-6" fill="none" stroke="currentColor" viewBox="0 0 24 24">
            <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d={isMobileMenuOpen ? "M6 18L18 6M6 6l12 12" : "M4 6h16M4 12h16M4 18h16"} />
          </svg>
        </button>
        <h1 className="text-lg font-bold bg-gradient-to-r from-purple-400 to-pink-400 bg-clip-text text-transparent">InfoPilot</h1>
        <NotificationBell showToast={showToast} />
      </div>

      {/* Mobile Menu Overlay */}
      {isMobileMenuOpen && (
        <div 
          className="md:hidden fixed inset-0 bg-black/50 z-40"
          onClick={() => setIsMobileMenuOpen(false)}
        />
      )}

      {/* Sidebar */}
      <div className={`sidebar ${isMobileMenuOpen ? 'mobile-open' : ''}`} data-testid="sidebar">
        <div className="sidebar-logo flex items-center justify-between">
          <div>
            <h1>InfoPilot</h1>
            <p>Information Exchange Network</p>
          </div>
          {/* Desktop Notification Bell */}
          <div className="hidden md:block">
            <NotificationBell showToast={showToast} />
          </div>
        </div>
        
        <div className="sidebar-user">
          <div className="sidebar-user-avatar">
            {user?.username?.[0]?.toUpperCase() || 'U'}
          </div>
          <div className="sidebar-user-info">
            <h3>
              {user?.username}
              {user?.is_admin && <span className="admin-badge">ADMIN</span>}
              {!user?.is_admin && user?.is_paid && <span className="full-access-badge">FULL ACCESS</span>}
            </h3>
            <p>{user?.email}</p>
          </div>
        </div>

        <nav className="sidebar-nav">
          {/* ADMIN CONTROL - Bright Sticker - Only for Admin */}
          {user?.is_admin && (
            <div
              className={`sidebar-nav-item admin-control-link ${currentPage === 'admin' ? 'active' : ''}`}
              onClick={() => handleNavClick('admin')}
              data-testid="admin-nav-item"
            >
              Admin Control
            </div>
          )}
          
          {/* Analytics - Admin Only */}
          {user?.is_admin && (
            <div
              className={`sidebar-nav-item ${currentPage === 'analytics' ? 'active' : ''}`}
              onClick={() => handleNavClick('analytics')}
              data-testid="nav-analytics"
              style={{
                background: currentPage === 'analytics' 
                  ? 'linear-gradient(135deg, rgba(59, 130, 246, 0.3), rgba(16, 185, 129, 0.2))' 
                  : 'transparent',
                borderLeft: currentPage === 'analytics' ? '3px solid #3b82f6' : 'none'
              }}
            >
              <Icons.Chart />
              <span>📊 Analytics</span>
            </div>
          )}

          {navItems.map(item => (
            <div
              key={item.id}
              className={`sidebar-nav-item ${currentPage === item.id ? 'active' : ''}`}
              onClick={() => handleNavClick(item.id)}
              data-testid={`nav-${item.id}`}
            >
              <item.icon />
              {item.label}
            </div>
          ))}

          <div className="sidebar-nav-item" onClick={logout} style={{ marginTop: 'auto' }} data-testid="logout-btn">
            <Icons.LogOut />
            Logout
          </div>
          
          {/* Theme Controls - Dark Mode + Accent Color */}
          <div style={{ padding: '10px 0', borderTop: '1px solid rgba(124, 58, 237, 0.2)', marginTop: 10 }}>
            <ThemeToggle showColorPicker={true} />
          </div>
        </nav>

        {/* Book Promo - Enhanced */}
        <div style={{ marginTop: 20, padding: 15, background: 'linear-gradient(135deg, rgba(236, 72, 153, 0.25), rgba(124, 58, 237, 0.25))', borderRadius: 12, border: '2px solid rgba(236, 72, 153, 0.5)' }}>
          <div style={{ fontSize: '0.85rem', color: '#fbbf24', fontWeight: 800, marginBottom: 8, textAlign: 'center' }}>
            🎬 OPTIONED FOR FILM! 🎬
          </div>
          <div style={{ fontSize: '0.9rem', color: '#f472b6', marginBottom: 6, textAlign: 'center', fontWeight: 700 }}>
            "Letters to Evelyn"
          </div>
          <div style={{ fontSize: '0.7rem', color: '#a78bfa', marginBottom: 8, fontStyle: 'italic', textAlign: 'center' }}>
            Supernatural Thriller Comedy
          </div>
          <div style={{ fontSize: '0.65rem', color: '#10b981', marginBottom: 6, textAlign: 'center', fontWeight: 600 }}>
            ⭐ 19 Five-Star Professional Reviews
          </div>
          <div style={{ fontSize: '0.6rem', color: '#a1a1aa', marginBottom: 10, fontStyle: 'italic', textAlign: 'center', lineHeight: 1.3 }}>
            "Comedy that creeps into your mind!"
          </div>
          <a 
            href="https://www.amazon.com/Letters-Evelyn-John-Selman-ebook/dp/B0CQZ8R191" 
            target="_blank" 
            rel="noopener noreferrer"
            className="btn btn-primary"
            style={{ fontSize: '0.8rem', padding: '10px 12px', display: 'block', textAlign: 'center', textDecoration: 'none', background: 'linear-gradient(135deg, #ec4899, #f97316)', boxShadow: '0 0 15px rgba(236, 72, 153, 0.5)' }}
            data-testid="sidebar-book-link"
          >
            🛒 GET IT - Only $2.99!
          </a>
        </div>
      </div>
    </>
  );
};

export default Sidebar;
