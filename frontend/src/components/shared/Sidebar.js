import React from 'react';
import { useAuth } from '../../contexts/AuthContext';
import Icons from './Icons';

const Sidebar = ({ currentPage, setCurrentPage }) => {
  const { user, logout } = useAuth();

  const navItems = [
    { id: 'search', label: 'Ultimate Search', icon: Icons.Search },
    { id: 'marketplace', label: 'Marketplace', icon: Icons.Shop },
    { id: 'achievements', label: 'Achievements', icon: Icons.Trophy },
    { id: 'social', label: 'Social', icon: Icons.Users },
    { id: 'map', label: 'Map View', icon: Icons.Map },
    { id: 'quotes', label: 'Quote Gallery', icon: Icons.Quote },
    { id: 'messages', label: 'Messages', icon: Icons.Message },
    { id: 'settings', label: 'Settings', icon: Icons.Settings },
  ];

  return (
    <div className="sidebar" data-testid="sidebar">
      <div className="sidebar-logo">
        <h1>InfoPilot</h1>
        <p>Information Exchange Network</p>
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
            onClick={() => setCurrentPage('admin')}
            data-testid="admin-nav-item"
          >
            Admin Control
          </div>
        )}
        
        {/* Analytics - Admin Only */}
        {user?.is_admin && (
          <div
            className={`sidebar-nav-item ${currentPage === 'analytics' ? 'active' : ''}`}
            onClick={() => setCurrentPage('analytics')}
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
            onClick={() => setCurrentPage(item.id)}
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
  );
};

export default Sidebar;
