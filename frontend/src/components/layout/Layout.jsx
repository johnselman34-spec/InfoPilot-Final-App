/**
 * Main Layout Component
 */
import React, { useState } from 'react';
import { Menu, Plane } from 'lucide-react';
import Sidebar from './Sidebar';

export const Layout = ({ children }) => {
  const [sidebarOpen, setSidebarOpen] = useState(false);

  return (
    <div className="min-h-screen bg-gradient-to-br from-slate-950 via-purple-950/30 to-slate-950">
      <Sidebar isOpen={sidebarOpen} setIsOpen={setSidebarOpen} />
      <header className="lg:hidden fixed top-0 left-0 right-0 h-16 bg-slate-950/90 border-b border-purple-500/30 z-30 flex items-center px-4 backdrop-blur">
        <button onClick={() => setSidebarOpen(true)} className="p-2 text-purple-400">
          <Menu className="w-6 h-6" />
        </button>
        <div className="flex items-center gap-2 ml-4">
          <Plane className="w-6 h-6 text-pink-400" />
          <span className="font-bold text-lg text-transparent bg-clip-text bg-gradient-to-r from-pink-400 to-purple-400 font-mono">INFOPILOT EXPLORER</span>
        </div>
      </header>
      <main className="lg:ml-72 pt-16 lg:pt-0 min-h-screen">
        <div className="p-4 lg:p-8">{children}</div>
      </main>
    </div>
  );
};

export default Layout;
