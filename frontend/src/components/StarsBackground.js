/**
 * InfoPilot Explorer - Stars Background Component
 * Uses pre-generated star positions for render purity
 */
import React, { useMemo } from 'react';

// Generate stars once using a seed-based approach for consistency
const generateStars = (count) => {
  const stars = [];
  for (let i = 0; i < count; i++) {
    // Use deterministic pseudo-random based on index
    const seed1 = (i * 9301 + 49297) % 233280;
    const seed2 = (i * 49297 + 233280) % 9301;
    const seed3 = (i * 233280 + 9301) % 49297;
    const seed4 = (i * 12345 + 67890) % 100000;
    const seed5 = (i * 67890 + 12345) % 100000;
    
    stars.push({
      left: `${(seed1 / 233280) * 100}%`,
      top: `${(seed2 / 9301) * 100}%`,
      animationDelay: `${(seed3 / 49297) * 3}s`,
      width: `${(seed4 / 100000) * 3 + 1}px`,
      height: `${(seed5 / 100000) * 3 + 1}px`
    });
  }
  return stars;
};

// Pre-generate stars at module level
const STARS = generateStars(50);

const StarsBackground = () => {
  // Memoize to prevent unnecessary recalculations
  const stars = useMemo(() => STARS, []);
  
  return (
    <div className="stars-container">
      {stars.map((style, i) => (
        <div key={i} className="star" style={style} />
      ))}
    </div>
  );
};

export default StarsBackground;
