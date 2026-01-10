/**
 * Futuristic Frame Component
 */
import React from 'react';

export const FuturisticFrame = ({ children, title, className = "", color = "purple" }) => {
  const colors = {
    purple: { border: "border-purple-500/50", text: "text-purple-400", glow: "shadow-purple-500/20" },
    pink: { border: "border-pink-500/50", text: "text-pink-400", glow: "shadow-pink-500/20" },
    blue: { border: "border-blue-500/50", text: "text-blue-400", glow: "shadow-blue-500/20" },
    red: { border: "border-red-500/50", text: "text-red-400", glow: "shadow-red-500/20" },
    green: { border: "border-green-500/50", text: "text-green-400", glow: "shadow-green-500/20" },
    yellow: { border: "border-yellow-500/50", text: "text-yellow-400", glow: "shadow-yellow-500/20" },
  };
  const c = colors[color] || colors.purple;
  
  return (
    <div className={`relative ${className}`}>
      <div className={`absolute top-0 left-0 w-4 h-4 border-t-2 border-l-2 ${c.border} pointer-events-none`}></div>
      <div className={`absolute top-0 right-0 w-4 h-4 border-t-2 border-r-2 ${c.border} pointer-events-none`}></div>
      <div className={`absolute bottom-0 left-0 w-4 h-4 border-b-2 border-l-2 ${c.border} pointer-events-none`}></div>
      <div className={`absolute bottom-0 right-0 w-4 h-4 border-b-2 border-r-2 ${c.border} pointer-events-none`}></div>
      {title && (
        <div className="absolute -top-3 left-6 bg-slate-950 px-2 pointer-events-none">
          <span className={`${c.text} text-xs font-mono tracking-wider`}>{title}</span>
        </div>
      )}
      <div className="p-4 relative z-10">{children}</div>
    </div>
  );
};

export default FuturisticFrame;
