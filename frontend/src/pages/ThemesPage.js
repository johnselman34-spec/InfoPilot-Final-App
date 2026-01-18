import React, { useState, useEffect } from 'react';
import { Navigate } from 'react-router-dom';
import axios from 'axios';
import { useAuth } from '../context/AuthContext';
import { useTheme } from '../context/ThemeContext';
import { useToast } from '../context/ToastContext';
import StarsBackground from '../components/StarsBackground';
import { Card } from '../components/ui/card';
import { Button } from '../components/ui/button';
import { Badge } from '../components/ui/badge';
import { Switch } from '../components/ui/switch';
import { Moon, Sun, Egg } from 'lucide-react';
import { API } from '../utils/api';

const ThemesPage = () => {
  const { user } = useAuth();
  const { theme, setTheme, themes } = useTheme();
  const showToast = useToast();
  const [easterEggsEnabled, setEasterEggsEnabled] = useState(true);

  // Load Easter Eggs preference
  useEffect(() => {
    const disabled = localStorage.getItem('easter-eggs-disabled') === 'true';
    setEasterEggsEnabled(!disabled);
  }, []);

  // Toggle Easter Eggs
  const toggleEasterEggs = (enabled) => {
    setEasterEggsEnabled(enabled);
    if (enabled) {
      localStorage.removeItem('easter-eggs-disabled');
      showToast("Easter Eggs enabled! 🥚", "success");
    } else {
      localStorage.setItem('easter-eggs-disabled', 'true');
      showToast("Easter Eggs disabled", "success");
    }
  };

  if (!user) return <Navigate to="/login" />;

  const darkThemes = [
    { id: "cosmic", name: "Cosmic Gold", emoji: "🌌" },
    { id: "royal", name: "Royal Purple", emoji: "👑" },
    { id: "hot", name: "Hot Red", emoji: "🔥" },
    { id: "ocean", name: "Ocean Blue", emoji: "🌊" },
    { id: "forest", name: "Forest Green", emoji: "🌲" },
    { id: "sunset", name: "Sunset Pink", emoji: "🌅" },
    { id: "ruby", name: "Ruby Red", emoji: "💎" },
    { id: "midnight", name: "Midnight", emoji: "🌙" },
    { id: "gold", name: "Pure Gold", emoji: "⭐" },
    { id: "cyber", name: "Cyberpunk", emoji: "🤖" }
  ];

  const lightThemes = [
    { id: "light", name: "Light Mode", emoji: "☀️" },
    { id: "cream", name: "Cream", emoji: "🍦" }
  ];

  const applyTheme = (preset) => {
    const isLight = preset === "light" || preset === "cream";
    setTheme({ mode: isLight ? "light" : "dark", preset });
    showToast(`Theme changed to ${themes[preset]?.name || preset}! ✨`, "success");
    axios.put(`${API}/users/theme`, { mode: isLight ? "light" : "dark", preset }).catch(() => {});
  };

  return (
    <div className="min-h-screen pt-20 px-4">
      <StarsBackground />
      <div className="max-w-5xl mx-auto">
        <div className="text-center mb-8">
          <h1 className="text-3xl font-bold text-gradient-gold mb-2">Theme Gallery</h1>
          <p className="text-white/60">Customize your InfoPilot experience with 12 unique color schemes</p>
        </div>

        {/* Dark/Light Toggle */}
        <div className="flex justify-center gap-4 mb-8" data-testid="theme-mode-toggle">
          <Button 
            onClick={() => setTheme(prev => ({ ...prev, mode: "dark" }))} 
            className={`px-6 py-3 ${theme.mode === "dark" ? "bg-gradient-to-r from-purple-600 to-blue-600 text-white" : "bg-slate-700 text-white/70"}`}
          >
            <Moon className="mr-2" size={18} /> Dark Mode
          </Button>
          <Button 
            onClick={() => setTheme(prev => ({ ...prev, mode: "light" }))} 
            className={`px-6 py-3 ${theme.mode === "light" ? "bg-gradient-to-r from-yellow-400 to-orange-400 text-black" : "bg-slate-200 text-slate-700"}`}
          >
            <Sun className="mr-2" size={18} /> Light Mode
          </Button>
        </div>

        {/* Dark Themes */}
        <h3 className="text-xl font-bold text-white mb-4 flex items-center gap-2"><Moon size={20} /> Dark Themes</h3>
        <div className="grid grid-cols-2 sm:grid-cols-3 md:grid-cols-5 gap-4 mb-8">
          {darkThemes.map(p => (
            <Card
              key={p.id}
              onClick={() => applyTheme(p.id)}
              className={`p-4 cursor-pointer transition-all hover:scale-105 hover:-translate-y-1 ${theme.preset === p.id ? 'ring-2 ring-yellow-400 shadow-lg shadow-yellow-400/20' : 'bg-slate-800/50 hover:bg-slate-700/50'}`}
              style={{ borderColor: themes[p.id]?.primary, borderWidth: theme.preset === p.id ? '2px' : '1px' }}
              data-testid={`theme-${p.id}`}
            >
              <div className="text-center">
                <span className="text-3xl mb-2 block">{p.emoji}</span>
                <p className="text-white font-semibold text-sm">{p.name}</p>
                <div className="flex justify-center gap-1 mt-2">
                  <div className="w-5 h-5 rounded-full shadow-inner" style={{ backgroundColor: themes[p.id]?.primary }} />
                  <div className="w-5 h-5 rounded-full shadow-inner" style={{ backgroundColor: themes[p.id]?.secondary }} />
                  <div className="w-5 h-5 rounded-full shadow-inner border border-white/20" style={{ backgroundColor: themes[p.id]?.background }} />
                </div>
              </div>
            </Card>
          ))}
        </div>

        {/* Light Themes */}
        <h3 className="text-xl font-bold text-white mb-4 flex items-center gap-2"><Sun size={20} /> Light Themes</h3>
        <div className="grid grid-cols-2 sm:grid-cols-3 md:grid-cols-5 gap-4 mb-8">
          {lightThemes.map(p => (
            <Card
              key={p.id}
              onClick={() => applyTheme(p.id)}
              className={`p-4 cursor-pointer transition-all hover:scale-105 hover:-translate-y-1 ${theme.preset === p.id ? 'ring-2 ring-yellow-400 shadow-lg shadow-yellow-400/20' : 'bg-slate-200/90 hover:bg-slate-100'}`}
              style={{ borderColor: themes[p.id]?.primary, borderWidth: theme.preset === p.id ? '2px' : '1px' }}
              data-testid={`theme-${p.id}`}
            >
              <div className="text-center">
                <span className="text-3xl mb-2 block">{p.emoji}</span>
                <p className="text-slate-800 font-semibold text-sm">{p.name}</p>
                <div className="flex justify-center gap-1 mt-2">
                  <div className="w-5 h-5 rounded-full shadow" style={{ backgroundColor: themes[p.id]?.primary }} />
                  <div className="w-5 h-5 rounded-full shadow" style={{ backgroundColor: themes[p.id]?.secondary }} />
                  <div className="w-5 h-5 rounded-full shadow border border-slate-300" style={{ backgroundColor: themes[p.id]?.background }} />
                </div>
              </div>
            </Card>
          ))}
        </div>

        {/* Current Theme Preview */}
        <Card className="card-glass p-6" data-testid="theme-preview">
          <h3 className="text-xl font-bold text-yellow-400 mb-4">Current Theme: {themes[theme.preset]?.name || theme.preset}</h3>
          <div className="grid grid-cols-3 gap-4">
            <div className="p-4 rounded-lg text-center border border-white/10" style={{ backgroundColor: themes[theme.preset]?.background }}>
              <p className={`text-xs ${theme.mode === 'light' ? 'text-slate-500' : 'text-white/60'}`}>Background</p>
              <p className={`font-mono text-sm ${theme.mode === 'light' ? 'text-slate-700' : 'text-white'}`}>{themes[theme.preset]?.background}</p>
            </div>
            <div className="p-4 rounded-lg text-center" style={{ backgroundColor: themes[theme.preset]?.primary }}>
              <p className="text-black/60 text-xs">Primary</p>
              <p className="text-black font-mono text-sm">{themes[theme.preset]?.primary}</p>
            </div>
            <div className="p-4 rounded-lg text-center" style={{ backgroundColor: themes[theme.preset]?.secondary }}>
              <p className="text-white/60 text-xs">Secondary</p>
              <p className="text-white font-mono text-sm">{themes[theme.preset]?.secondary}</p>
            </div>
          </div>
          
          {/* Preview Components */}
          <div className="mt-6 p-4 rounded-lg" style={{ backgroundColor: themes[theme.preset]?.background }}>
            <h4 className={`font-bold mb-3 ${theme.mode === 'light' ? 'text-slate-800' : 'text-white'}`}>Preview Components</h4>
            <div className="flex flex-wrap gap-3">
              <Button style={{ backgroundColor: themes[theme.preset]?.primary, color: 'black' }}>Primary Button</Button>
              <Button style={{ backgroundColor: themes[theme.preset]?.secondary, color: 'white' }}>Secondary Button</Button>
              <Badge style={{ backgroundColor: `${themes[theme.preset]?.primary}30`, color: themes[theme.preset]?.primary }}>Badge</Badge>
            </div>
          </div>
        </Card>

        {/* Easter Eggs Settings */}
        <Card className="card-glass p-6 mt-6" data-testid="easter-eggs-settings">
          <div className="flex items-center justify-between">
            <div className="flex items-center gap-3">
              <div className="w-12 h-12 rounded-full bg-gradient-to-br from-yellow-400 to-orange-500 flex items-center justify-center">
                <Egg className="text-white" size={24} />
              </div>
              <div>
                <h3 className="text-lg font-bold text-white">Easter Eggs</h3>
                <p className="text-white/60 text-sm">Fun surprises that appear while you browse</p>
              </div>
            </div>
            <div className="flex items-center gap-3">
              <span className={`text-sm ${easterEggsEnabled ? 'text-green-400' : 'text-white/50'}`}>
                {easterEggsEnabled ? 'Enabled' : 'Disabled'}
              </span>
              <Switch 
                checked={easterEggsEnabled}
                onCheckedChange={toggleEasterEggs}
                data-testid="easter-eggs-toggle"
              />
            </div>
          </div>
          <p className="text-white/40 text-xs mt-3">
            When enabled, you&apos;ll occasionally see floating Easter Eggs with jokes and protocol ideas. 
            Catch them to earn Laughter Points!
          </p>
        </Card>
      </div>
    </div>
  );
};

export default ThemesPage;
