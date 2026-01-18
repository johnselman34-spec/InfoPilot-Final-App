/**
 * InfoPilot Explorer - Theme Context
 */
import React, { createContext, useContext, useState, useEffect } from 'react';

const ThemeContext = createContext(null);
export const useTheme = () => useContext(ThemeContext);

const themes = {
  cosmic: { primary: "#fbbf24", secondary: "#8b5cf6", background: "#0f172a", name: "Cosmic Gold" },
  royal: { primary: "#818cf8", secondary: "#4f46e5", background: "#0f0f23", name: "Royal Purple" },
  hot: { primary: "#ef4444", secondary: "#f97316", background: "#18181b", name: "Hot Red" },
  ocean: { primary: "#22d3ee", secondary: "#0284c7", background: "#042f2e", name: "Ocean Blue" },
  forest: { primary: "#4ade80", secondary: "#15803d", background: "#052e16", name: "Forest Green" },
  sunset: { primary: "#fb923c", secondary: "#db2777", background: "#27272a", name: "Sunset Pink" },
  ruby: { primary: "#f43f5e", secondary: "#9f1239", background: "#1c1917", name: "Ruby Red" },
  midnight: { primary: "#a78bfa", secondary: "#7c3aed", background: "#020617", name: "Midnight" },
  gold: { primary: "#eab308", secondary: "#ca8a04", background: "#1a1a1a", name: "Pure Gold" },
  cyber: { primary: "#00ff88", secondary: "#00ccff", background: "#0a0a0a", name: "Cyberpunk" },
  light: { primary: "#2563eb", secondary: "#7c3aed", background: "#f8fafc", name: "Light Mode" },
  cream: { primary: "#d97706", secondary: "#92400e", background: "#fef3c7", name: "Cream" }
};

export const ThemeProvider = ({ children }) => {
  const [theme, setTheme] = useState(() => {
    const saved = localStorage.getItem("theme");
    return saved ? JSON.parse(saved) : { mode: "dark", preset: "cosmic" };
  });

  // eslint-disable-next-line react-hooks/exhaustive-deps
  useEffect(() => {
    localStorage.setItem("theme", JSON.stringify(theme));
    const colors = themes[theme.preset] || themes.cosmic;
    document.documentElement.style.setProperty("--color-primary", colors.primary);
    document.documentElement.style.setProperty("--color-secondary", colors.secondary);
    document.documentElement.style.setProperty("--color-background", colors.background);
    document.body.className = theme.mode === "light" ? "light-mode" : "";
  }, [theme]);

  return (
    <ThemeContext.Provider value={{ theme, setTheme, themes }}>
      {children}
    </ThemeContext.Provider>
  );
};

export default ThemeProvider;
