import React, { useState } from "react";
import { Link, useLocation } from "react-router-dom";
import { 
  Home, Map, BarChart3, Users, Globe, ShoppingBag,
  Settings, LogOut, Menu, X, MessageCircle, BookOpen,
  Egg, Award, Activity, Layout, Share2
} from "lucide-react";
import { Button } from "@/components/ui/button";
import { ScrollArea } from "@/components/ui/scroll-area";
import { useAuth } from "../contexts/AuthContext";

const DashboardLayout = ({ children }) => {
  const { user, logout } = useAuth();
  const [sidebarOpen, setSidebarOpen] = useState(true);
  const location = useLocation();

  const navItems = [
    { path: "/dashboard", icon: Home, label: "Ultimate Search" },
    { path: "/map", icon: Map, label: "Map View" },
    { path: "/stats", icon: BarChart3, label: "Statistics" },
    { path: "/heatmaps", icon: Activity, label: "Heatmaps" },
    { path: "/global", icon: Globe, label: "Global Research" },
    { path: "/marketplace", icon: ShoppingBag, label: "Marketplace" },
    { path: "/templates", icon: Layout, label: "Protocol Templates" },
    { path: "/collab", icon: Share2, label: "Collaborative Sessions" },
    { path: "/leaderboard", icon: Award, label: "Leaderboard" },
    { path: "/friends", icon: Users, label: "Friends" },
    { path: "/groups", icon: Users, label: "Groups" },
    { path: "/chat", icon: MessageCircle, label: "Messages" },
    { path: "/reports", icon: BookOpen, label: "Personal Reports" },
    { path: "/easter-eggs", icon: Egg, label: "Easter Eggs" },
    { path: "/quotes", icon: BookOpen, label: "Quote Gallery" },
    { path: "/themes", icon: Settings, label: "Themes" },
    { path: "/book", icon: BookOpen, label: "Letters to Evelyn" },
    { path: "/settings", icon: Settings, label: "Settings" },
  ];

  if (user?.is_admin) {
    navItems.push({ path: "/admin", icon: Settings, label: "Admin Panel" });
  }

  return (
    <div className="min-h-screen bg-[#FFFFF0] flex">
      {/* Sidebar */}
      <aside className={`fixed left-0 top-0 h-full bg-white border-r border-gray-100 transition-all duration-300 z-40 ${sidebarOpen ? 'w-64' : 'w-20'}`}>
        <div className="p-4 flex items-center justify-between border-b border-gray-100">
          {sidebarOpen && (
            <div className="flex items-center gap-2">
              <Globe className="w-8 h-8 text-[#007AFF]" />
              <span className="font-bold font-['Outfit']">InfoPilot</span>
            </div>
          )}
          <Button variant="ghost" size="icon" onClick={() => setSidebarOpen(!sidebarOpen)} data-testid="toggle-sidebar">
            {sidebarOpen ? <X className="w-5 h-5" /> : <Menu className="w-5 h-5" />}
          </Button>
        </div>

        <ScrollArea className="h-[calc(100vh-140px)]">
          <nav className="p-4 space-y-2">
            {navItems.map((item) => (
              <Link
                key={item.path}
                to={item.path}
                className={`sidebar-link ${location.pathname === item.path ? 'active' : ''}`}
                data-testid={`nav-${item.label.toLowerCase().replace(' ', '-')}`}
              >
                <item.icon className="w-5 h-5 flex-shrink-0" />
                {sidebarOpen && <span className="ml-3">{item.label}</span>}
              </Link>
            ))}
          </nav>
        </ScrollArea>

        <div className="absolute bottom-0 left-0 right-0 p-4 border-t border-gray-100">
          <div className={`flex items-center ${sidebarOpen ? 'gap-3' : 'justify-center'}`}>
            <img 
              src={user?.picture || "https://via.placeholder.com/40"} 
              alt={user?.name}
              className="w-10 h-10 rounded-full"
            />
            {sidebarOpen && (
              <div className="flex-1 min-w-0">
                <p className="font-medium truncate">{user?.name}</p>
                <p className="text-sm text-gray-500 truncate">Level {user?.level || 1}</p>
              </div>
            )}
            {sidebarOpen && (
              <Button variant="ghost" size="icon" onClick={logout} data-testid="logout-btn">
                <LogOut className="w-5 h-5" />
              </Button>
            )}
          </div>
        </div>
      </aside>

      {/* Main Content */}
      <main className={`flex-1 transition-all duration-300 ${sidebarOpen ? 'ml-64' : 'ml-20'}`}>
        {children}
      </main>
    </div>
  );
};

export default DashboardLayout;
