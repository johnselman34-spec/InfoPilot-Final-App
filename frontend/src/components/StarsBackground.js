/**
 * InfoPilot Explorer - Stars Background Component
 */
import React from 'react';

const StarsBackground = () => (
  <div className="stars-container">
    {[...Array(50)].map((_, i) => (
      <div key={i} className="star" style={{
        left: `${Math.random() * 100}%`,
        top: `${Math.random() * 100}%`,
        animationDelay: `${Math.random() * 3}s`,
        width: `${Math.random() * 3 + 1}px`,
        height: `${Math.random() * 3 + 1}px`
      }} />
    ))}
  </div>
);

export default StarsBackground;
