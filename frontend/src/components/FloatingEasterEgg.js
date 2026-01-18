/**
 * InfoPilot Explorer - Floating Easter Egg Component
 * Can be disabled via localStorage or user settings
 */
import React, { useState, useEffect, useCallback } from 'react';
import axios from 'axios';
import { Egg, X, EyeOff } from 'lucide-react';
import { API } from '../utils/api';
import { useAuth } from '../context/AuthContext';
import { useToast } from '../context/ToastContext';
import { Button } from '../components/ui/button';

// Check if Easter Eggs are disabled
const isEasterEggsDisabled = () => {
  if (typeof window === 'undefined') return false;
  return localStorage.getItem('easter-eggs-disabled') === 'true';
};

const FloatingEasterEgg = () => {
  const { user } = useAuth();
  const showToast = useToast();
  const [egg, setEgg] = useState(null);
  const [position, setPosition] = useState({ x: 0, y: 0 });
  const [visible, setVisible] = useState(false);
  const [disabled, setDisabled] = useState(isEasterEggsDisabled);

  const showEgg = useCallback(() => {
    if (!user || disabled) return;
    
    axios.get(`${API}/easter-eggs/random`)
      .then(res => {
        setEgg(res.data.egg);
        setPosition({
          x: Math.random() * (window.innerWidth - 300),
          y: Math.random() * (window.innerHeight - 400) + 100
        });
        setVisible(true);
      })
      .catch(() => {});
  }, [user, disabled]);

  useEffect(() => {
    if (disabled) return;

    // Show egg randomly every 30-60 seconds
    const interval = setInterval(() => {
      if (Math.random() > 0.5) showEgg();
    }, 30000);

    // Show first egg after 10 seconds
    const timeout = setTimeout(showEgg, 10000);

    return () => {
      clearInterval(interval);
      clearTimeout(timeout);
    };
  }, [user, disabled, showEgg]);

  const catchEgg = async () => {
    if (!egg) return;
    
    try {
      const res = await axios.post(`${API}/laughter-points/catch`, { egg_id: egg.id || "random" });
      showToast(res.data.message, "success");
      setVisible(false);
    } catch (err) {
      // If unauthorized, just hide the egg silently
      if (err.response?.status === 401) {
        setVisible(false);
        return;
      }
      showToast("Failed to catch egg!", "error");
      setVisible(false);
    }
  };

  const disableEasterEggs = () => {
    localStorage.setItem('easter-eggs-disabled', 'true');
    setDisabled(true);
    setVisible(false);
    showToast("Easter Eggs disabled. You can re-enable them in Settings/Themes.", "success");
  };

  if (!visible || !egg || !user || disabled) return null;

  return (
    <div 
      className="fixed z-50 animate-bounce-slow"
      style={{ left: position.x, top: position.y }}
      data-testid="floating-easter-egg"
    >
      <div className="bg-gradient-to-br from-yellow-400 to-orange-500 rounded-2xl p-4 shadow-2xl max-w-xs border-2 border-yellow-300">
        <div className="flex items-center justify-between mb-2">
          <div className="flex items-center gap-2">
            <Egg className="text-white" size={24} />
            <span className="text-white font-bold">Easter Egg!</span>
          </div>
          <div className="flex items-center gap-1">
            <button 
              onClick={disableEasterEggs} 
              className="text-white/70 hover:text-white p-1" 
              title="Disable Easter Eggs"
              data-testid="disable-easter-eggs-btn"
            >
              <EyeOff size={16} />
            </button>
            <button 
              onClick={() => setVisible(false)} 
              className="text-white/70 hover:text-white p-1"
              title="Close"
            >
              <X size={18} />
            </button>
          </div>
        </div>
        
        <p className="text-white text-sm mb-3">{egg.joke}</p>
        
        <div className="bg-white/20 rounded-lg p-2 mb-3">
          <p className="text-white/90 text-xs font-semibold">Protocol Idea:</p>
          <p className="text-white/80 text-xs font-mono">{egg.protocol_idea}</p>
        </div>
        
        <div className="flex items-center justify-between">
          <span className="text-white/80 text-xs">{egg.pricing_suggestion}</span>
          <Button onClick={catchEgg} size="sm" className="bg-white text-orange-600 hover:bg-white/90" data-testid="catch-egg-btn">
            Catch! 🎉
          </Button>
        </div>
      </div>
    </div>
  );
};

export default FloatingEasterEgg;
