/**
 * Sidebar Navigation Component - Futuristic Theme
 */
import React from 'react';
import { useNavigate, useLocation } from 'react-router-dom';
import {
  Home, Radar, Target, FolderTree, ShoppingCart, MessageCircle,
  Users, FileText, BarChart3, Globe, Book, Shield, Plane, X,
  LogOut, Check
} from 'lucide-react';
import { useAuth } from '../../contexts/AuthContext';

const Sidebar = ({ isOpen, setIsOpen }) => {
  const { user, logout } = useAuth();
  const navigate = useNavigate();
  const location = useLocation();

  // Build menu items - Admin Control at TOP if user is admin
  const menuItems = [];
  
  // Add Admin Control FIRST if user is admin
  if (user?.is_admin || user?.role === 'admin') {
    menuItems.push({ path: "/admin", icon: Shield, label: "⚙️ ADMIN CONTROL", highlight: true, isAdmin: true });
  }
  
  // Add all other menu items
  menuItems.push(
    { path: "/", icon: Home, label: "COMMAND CENTER" },
    { path: "/infopilot", icon: Radar, label: "INFOPILOT SEARCH" },
    { path: "/ultimate-search", icon: Target, label: "ULTIMATE SEARCH" },
    { path: "/categories", icon: FolderTree, label: "CATEGORIES" },
    { path: "/marketplace", icon: ShoppingCart, label: "MARKETPLACE", highlight: true },
    { path: "/messages", icon: MessageCircle, label: "MESSAGES" },
    { path: "/friends", icon: Users, label: "FRIENDS" },
    { path: "/groups", icon: Users, label: "GROUPS" },
    { path: "/pages", icon: FileText, label: "PAGES" },
    { path: "/statistics", icon: BarChart3, label: "INTEL STATS" },
    { path: "/global-database", icon: Globe, label: "GLOBAL DATABASE" },
    { path: "/book", icon: Book, label: "📚 GET THE BOOK", highlight: true },
  );

  return (
    <>
      {isOpen && <div className="fixed inset-0 bg-black/70 z-40 lg:hidden" onClick={() => setIsOpen(false)} />}
      
      <aside className={`fixed top-0 left-0 h-full bg-gradient-to-b from-slate-950 via-purple-950/50 to-slate-950 border-r border-purple-500/30 z-50 transition-transform duration-300 w-72 flex flex-col ${isOpen ? "translate-x-0" : "-translate-x-full lg:translate-x-0"}`}>
        {/* Header - Fixed */}
        <div className="p-6 border-b border-purple-500/30 flex-shrink-0">
          <div className="flex items-center justify-between">
            <div className="flex items-center gap-3">
              <div className="w-12 h-12 bg-gradient-to-br from-pink-500/20 to-purple-500/20 border-2 border-pink-500 rounded-lg flex items-center justify-center relative">
                <Plane className="w-7 h-7 text-pink-400" />
                <div className="absolute -top-1 -right-1 w-3 h-3 bg-blue-400 rounded-full animate-pulse"></div>
              </div>
              <div>
                <h1 className="text-xl font-bold text-transparent bg-clip-text bg-gradient-to-r from-pink-400 to-purple-400 font-mono tracking-wider">INFOPILOT EXPLORER</h1>
                <p className="text-xs text-purple-400/60 font-mono">TACTICAL SEARCH v2.0</p>
              </div>
            </div>
            <button className="lg:hidden text-purple-400" onClick={() => setIsOpen(false)}>
              <X className="w-6 h-6" />
            </button>
          </div>
        </div>

        {/* Scrollable Navigation */}
        <nav className="flex-1 overflow-y-auto p-4 space-y-1 scrollbar-thin scrollbar-thumb-purple-500/30 scrollbar-track-transparent">
          {menuItems.map((item) => (
            <button
              key={item.path}
              onClick={() => { navigate(item.path); setIsOpen(false); }}
              className={`w-full flex items-center gap-3 px-4 py-3 rounded transition-all font-mono text-sm
                ${item.isAdmin
                  ? "bg-gradient-to-r from-pink-600/30 to-purple-600/30 text-yellow-400 border-2 border-yellow-500/50 hover:border-yellow-400 animate-pulse"
                  : location.pathname === item.path
                    ? "bg-purple-500/20 text-pink-400 border border-pink-500/50"
                    : item.highlight
                      ? "text-pink-400 hover:bg-pink-500/10 border border-pink-500/30"
                      : "text-purple-300/70 hover:bg-purple-500/10 hover:text-purple-300 border border-transparent"
                }`}
              data-testid={`nav-${item.path.replace('/', '') || 'home'}`}
            >
              <item.icon className={`w-5 h-5 ${item.isAdmin ? 'text-yellow-400' : ''}`} />
              <span className="tracking-wider">{item.label}</span>
            </button>
          ))}
          
          {/* Sidebar Book Promo - Inside scrollable area */}
          <div className="mt-4 p-3 bg-gradient-to-r from-pink-500/20 to-purple-500/20 rounded-lg border border-pink-500/50">
            <p className="text-pink-400 font-mono text-xs text-center">
              📚 NEW: <span className="font-bold">Letters to Evelyn</span>
            </p>
            <p className="text-purple-400/60 font-mono text-xs text-center mt-1">Only $2.99!</p>
          </div>
        </nav>

        {/* User Section - Fixed at bottom */}
        <div className="p-4 border-t border-purple-500/30 bg-slate-950/90 flex-shrink-0">
          <div className="flex items-center gap-3 mb-4">
            <div className="w-10 h-10 bg-gradient-to-br from-purple-500/20 to-pink-500/20 border border-purple-500 rounded-full flex items-center justify-center text-pink-400 font-bold font-mono">
              {user?.username?.[0]?.toUpperCase() || "P"}
            </div>
            <div className="flex-1 min-w-0">
              <p className="font-mono text-purple-300 text-sm truncate">{user?.username}</p>
              {/* Show admin badge if user is admin */}
              {user?.is_admin ? (
                <span className="px-2 py-0.5 rounded text-xs font-mono bg-pink-500/20 border border-pink-500/50 text-pink-400 flex items-center gap-1">
                  <Shield className="w-3 h-3" /> ADMIN
                </span>
              ) : (
                <span className="px-2 py-0.5 rounded text-xs font-mono bg-green-500/20 border border-green-500/50 text-green-400 flex items-center gap-1">
                  <Check className="w-3 h-3" /> FULL ACCESS
                </span>
              )}
            </div>
          </div>
          <button
            onClick={logout}
            className="w-full flex items-center justify-center gap-2 px-4 py-2 text-red-400 hover:bg-red-500/10 rounded transition-colors font-mono text-sm border border-red-500/30"
          >
            <LogOut className="w-4 h-4" />
            <span>DISCONNECT</span>
          </button>
        </div>
      </aside>
    </>
  );
};

export default Sidebar;
