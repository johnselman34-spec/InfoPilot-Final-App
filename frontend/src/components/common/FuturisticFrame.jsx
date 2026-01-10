/**
 * Futuristic Frame Component
 */
import React from 'react';

const FuturisticFrame = ({ children, title, className = "", color = "purple" }) => {
  const colorClasses = {
    purple: "border-purple-500/30 from-purple-500/5 to-pink-500/5",
    pink: "border-pink-500/30 from-pink-500/5 to-purple-500/5",
    blue: "border-blue-500/30 from-blue-500/5 to-purple-500/5",
    green: "border-green-500/30 from-green-500/5 to-blue-500/5",
  };

  return (
    <div className={`relative rounded-lg border ${colorClasses[color]} bg-gradient-to-br backdrop-blur ${className}`}>
      {title && (
        <div className="absolute -top-3 left-4 px-2 bg-slate-950">
          <span className={`text-xs font-mono tracking-wider ${color === 'pink' ? 'text-pink-400' : color === 'blue' ? 'text-blue-400' : color === 'green' ? 'text-green-400' : 'text-purple-400'}`}>
            {title}
          </span>
        </div>
      )}
      <div className="p-6 pt-4">
        {children}
      </div>
    </div>
  );
};

export default FuturisticFrame;
