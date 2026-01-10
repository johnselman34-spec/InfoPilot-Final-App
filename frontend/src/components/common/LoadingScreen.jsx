/**
 * Common loading screen component
 */
import React from 'react';
import { Loader2 } from 'lucide-react';

const LoadingScreen = () => (
  <div className="min-h-screen bg-gradient-to-br from-slate-950 via-purple-950/30 to-slate-950 flex items-center justify-center">
    <div className="text-center">
      <Loader2 className="w-12 h-12 text-pink-400 animate-spin mx-auto mb-4" />
      <p className="text-purple-400 font-mono">INITIALIZING SYSTEMS...</p>
    </div>
  </div>
);

export default LoadingScreen;
