/**
 * InfoPilot Explorer - Navbar Component
 */
import React, { useState } from 'react';
import { Link, useNavigate } from 'react-router-dom';
import { useAuth } from '../context/AuthContext';
import { 
  Sparkles, LogOut, Settings, Home, BarChart3, Map, Store, 
  MessageCircle, Users, Layers, Book, Utensils, Search, User, ChevronDown, Menu, X
} from 'lucide-react';
import { Badge } from '../components/ui/badge';
import { Button } from '../components/ui/button';

const Navbar = () => {
  const { user, logout } = useAuth();
  const navigate = useNavigate();
  const [mobileOpen, setMobileOpen] = useState(false);
  const [dropdownOpen, setDropdownOpen] = useState(false);

  const navItems = user ? [
    { path: "/", label: "Home", icon: <Home size={18} /> },
    { path: "/search", label: "Search", icon: <Search size={18} /> },
    { path: "/map", label: "Map", icon: <Map size={18} /> },
    { path: "/stats", label: "Stats", icon: <BarChart3 size={18} /> },
    { path: "/marketplace", label: "Market", icon: <Store size={18} /> },
    { path: "/chat", label: "Chat", icon: <MessageCircle size={18} /> },
    { path: "/groups", label: "Groups", icon: <Users size={18} /> },
    { path: "/pages", label: "Pages", icon: <Layers size={18} /> },
  ] : [
    { path: "/book", label: "Book", icon: <Book size={18} /> },
    { path: "/food", label: "Food", icon: <Utensils size={18} /> },
    { path: "/infopilot", label: "InfoPilot", icon: <Sparkles size={18} /> },
  ];

  const handleLogout = () => {
    logout();
    navigate('/');
  };

  return (
    <nav className="fixed top-0 left-0 right-0 z-40 bg-gradient-to-r from-slate-900/95 via-slate-800/95 to-slate-900/95 backdrop-blur-lg border-b border-yellow-400/20 shadow-lg">
      <div className="max-w-7xl mx-auto px-4">
        <div className="flex items-center justify-between h-16">
          {/* Logo */}
          <Link to="/" className="flex items-center gap-2 hover:opacity-90 transition">
            <div className="w-10 h-10 rounded-full bg-gradient-to-br from-yellow-400 to-orange-500 flex items-center justify-center">
              <Sparkles className="text-slate-900" size={24} />
            </div>
            <span className="text-xl font-bold text-gradient-gold hidden sm:block">InfoPilot</span>
          </Link>

          {/* Desktop Nav */}
          <div className="hidden md:flex items-center gap-1">
            {navItems.map(item => (
              <Link key={item.path} to={item.path} className="nav-link flex items-center gap-1 px-3 py-2 rounded-lg text-white/80 hover:text-white hover:bg-white/10 transition">
                {item.icon}
                <span className="text-sm">{item.label}</span>
              </Link>
            ))}
          </div>

          {/* User Section */}
          <div className="flex items-center gap-3">
            {user ? (
              <>
                {/* Laughter Points */}
                <Badge className="hidden sm:flex bg-yellow-400/20 text-yellow-400 border-yellow-400/30 gap-1" data-testid="laughter-points">
                  😂 {user.laughter_points || 0}
                </Badge>
                
                {/* User Dropdown */}
                <div className="relative">
                  <button onClick={() => setDropdownOpen(!dropdownOpen)} className="flex items-center gap-2 px-3 py-2 rounded-lg bg-white/5 hover:bg-white/10 transition">
                    <div className="w-8 h-8 rounded-full bg-gradient-to-br from-purple-500 to-blue-500 flex items-center justify-center text-white font-bold text-sm">
                      {user.username?.charAt(0).toUpperCase()}
                    </div>
                    <span className="text-white/90 text-sm hidden sm:block">{user.username}</span>
                    <ChevronDown size={16} className="text-white/50" />
                  </button>
                  
                  {dropdownOpen && (
                    <div className="absolute right-0 top-12 w-48 bg-slate-800 rounded-lg shadow-xl border border-white/10 py-2">
                      <Link to="/reports" onClick={() => setDropdownOpen(false)} className="flex items-center gap-2 px-4 py-2 text-white/80 hover:bg-white/10">
                        <User size={16} /> My Reports
                      </Link>
                      <Link to="/revenue" onClick={() => setDropdownOpen(false)} className="flex items-center gap-2 px-4 py-2 text-white/80 hover:bg-white/10">
                        <BarChart3 size={16} /> Revenue
                      </Link>
                      <Link to="/themes" onClick={() => setDropdownOpen(false)} className="flex items-center gap-2 px-4 py-2 text-white/80 hover:bg-white/10">
                        <Settings size={16} /> Themes
                      </Link>
                      <hr className="my-2 border-white/10" />
                      <button onClick={handleLogout} className="flex items-center gap-2 px-4 py-2 text-red-400 hover:bg-white/10 w-full">
                        <LogOut size={16} /> Logout
                      </button>
                    </div>
                  )}
                </div>
              </>
            ) : (
              <Link to="/login">
                <Button className="btn-gold" data-testid="login-btn">Login</Button>
              </Link>
            )}

            {/* Mobile Menu Toggle */}
            <button onClick={() => setMobileOpen(!mobileOpen)} className="md:hidden p-2 text-white">
              {mobileOpen ? <X size={24} /> : <Menu size={24} />}
            </button>
          </div>
        </div>

        {/* Mobile Nav */}
        {mobileOpen && (
          <div className="md:hidden py-4 border-t border-white/10">
            <div className="flex flex-col gap-1">
              {navItems.map(item => (
                <Link key={item.path} to={item.path} onClick={() => setMobileOpen(false)} className="flex items-center gap-2 px-4 py-3 text-white/80 hover:bg-white/10 rounded-lg">
                  {item.icon}
                  <span>{item.label}</span>
                </Link>
              ))}
            </div>
          </div>
        )}
      </div>
    </nav>
  );
};

export default Navbar;
