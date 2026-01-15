/**
 * Quick Action Card Component
 * Reusable action button card
 */
import React from 'react';

export const QuickActionCard = ({ title, icon: Icon, onClick, color = "purple" }) => {
  const colorClasses = { 
    purple: "border-purple-500/30 hover:border-purple-500 text-purple-400", 
    pink: "border-pink-500/30 hover:border-pink-500 text-pink-400", 
    blue: "border-blue-500/30 hover:border-blue-500 text-blue-400",
    yellow: "border-yellow-500/30 hover:border-yellow-500 text-yellow-400",
    green: "border-green-500/30 hover:border-green-500 text-green-400"
  };
  
  return (
    <button 
      onClick={onClick} 
      className={`bg-slate-900/80 border ${colorClasses[color]} rounded-lg p-6 text-center hover:scale-[1.02] transition-all cursor-pointer`}
    >
      <Icon className={`w-10 h-10 mx-auto mb-3 ${colorClasses[color].split(' ').pop()}`} />
      <h3 className="text-purple-300 font-mono font-bold text-sm tracking-wider">{title}</h3>
    </button>
  );
};

export default QuickActionCard;
