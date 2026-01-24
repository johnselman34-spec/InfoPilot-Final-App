import React, { useState, useEffect } from "react";
import { Egg, Trophy, Award, Star } from "lucide-react";
import { Button } from "@/components/ui/button";
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card";
import { Badge } from "@/components/ui/badge";
import axios from "axios";

const BACKEND_URL = process.env.REACT_APP_BACKEND_URL;
const api = axios.create({
  baseURL: `${BACKEND_URL}/api`,
  withCredentials: true
});

const EasterEggsPage = () => {
  const [eggs, setEggs] = useState([]);
  const [leaderboard, setLeaderboard] = useState(null);
  const [floatingEggs, setFloatingEggs] = useState([]);
  const [selectedEgg, setSelectedEgg] = useState(null);
  const [activeTab, setActiveTab] = useState("all");

  useEffect(() => {
    fetchEasterEggs();
    fetchLeaderboard();
  }, []);

  // Create floating T-Rex eggs animation
  useEffect(() => {
    const createFloatingEgg = () => {
      const colors = ["#FF6B6B", "#4ECDC4", "#FFE66D", "#95E1D3", "#F38181", "#AA96DA", "#74B9FF", "#FFEAA7"];
      const spots = ["#2C3E50", "#E74C3C", "#3498DB", "#9B59B6", "#F39C12"];
      const newEgg = {
        id: Date.now() + Math.random(),
        x: Math.random() * 100,
        color: colors[Math.floor(Math.random() * colors.length)],
        spotColor: spots[Math.floor(Math.random() * spots.length)],
        duration: 15 + Math.random() * 10,
        size: 40 + Math.random() * 30,
        delay: Math.random() * 5
      };
      setFloatingEggs(prev => [...prev.slice(-8), newEgg]);
    };
    
    createFloatingEgg();
    const interval = setInterval(createFloatingEgg, 4000);
    return () => clearInterval(interval);
  }, []);

  const fetchEasterEggs = async () => {
    try {
      const response = await api.get("/easter-eggs");
      setEggs(response.data.easter_eggs || []);
    } catch (error) {
      console.error("Error fetching easter eggs:", error);
    }
  };

  const fetchLeaderboard = async () => {
    try {
      const response = await api.get("/easter-eggs/laugh-leaderboard");
      setLeaderboard(response.data);
    } catch (error) {
      console.error("Error fetching leaderboard:", error);
    }
  };

  const submitLaugh = async (eggId, laughType) => {
    try {
      const response = await api.post("/easter-eggs/laugh-submit", {
        egg_id: eggId,
        rating: laughType === 'rofl' ? 10 : laughType === 'laugh' ? 7 : 4,
        laugh_type: laughType
      });
      alert(`You earned ${response.data.xp_earned} XP! 🦖`);
    } catch (error) {
      console.error("Error submitting laugh:", error);
    }
  };

  const handleFloatingEggClick = (egg) => {
    if (eggs.length > 0) {
      const randomEgg = eggs[Math.floor(Math.random() * eggs.length)];
      setSelectedEgg(randomEgg);
    }
  };

  const filteredEggs = activeTab === "all" ? eggs : eggs.filter(e => e.type === activeTab);

  // T-Rex Egg SVG Component
  const TRexEgg = ({ color, spotColor, size, onClick }) => (
    <svg 
      width={size} 
      height={size * 1.3} 
      viewBox="0 0 100 130" 
      className="cursor-pointer hover:scale-110 transition-transform drop-shadow-lg"
      onClick={onClick}
      style={{ filter: "drop-shadow(0 4px 8px rgba(0,0,0,0.3))" }}
    >
      <defs>
        <radialGradient id={`eggGrad-${color}`} cx="30%" cy="30%">
          <stop offset="0%" stopColor="white" stopOpacity="0.4" />
          <stop offset="100%" stopColor={color} stopOpacity="0.85" />
        </radialGradient>
        <filter id="sparkle">
          <feGaussianBlur stdDeviation="1" result="blur"/>
          <feMerge>
            <feMergeNode in="blur"/>
            <feMergeNode in="SourceGraphic"/>
          </feMerge>
        </filter>
      </defs>
      
      <ellipse cx="50" cy="65" rx="40" ry="55" fill={`url(#eggGrad-${color})`} stroke={spotColor} strokeWidth="2"/>
      
      <circle cx="30" cy="45" r="8" fill={spotColor} opacity="0.7"/>
      <circle cx="60" cy="35" r="6" fill={spotColor} opacity="0.6"/>
      <circle cx="70" cy="60" r="7" fill={spotColor} opacity="0.7"/>
      <circle cx="35" cy="80" r="5" fill={spotColor} opacity="0.5"/>
      <circle cx="55" cy="90" r="6" fill={spotColor} opacity="0.6"/>
      <circle cx="45" cy="55" r="4" fill={spotColor} opacity="0.4"/>
      
      <circle cx="25" cy="30" r="2" fill="white" opacity="0.9" filter="url(#sparkle)">
        <animate attributeName="opacity" values="0.9;0.3;0.9" dur="2s" repeatCount="indefinite"/>
      </circle>
      <circle cx="65" cy="25" r="1.5" fill="white" opacity="0.8" filter="url(#sparkle)">
        <animate attributeName="opacity" values="0.8;0.2;0.8" dur="1.5s" repeatCount="indefinite"/>
      </circle>
      
      <path d="M 35 20 Q 40 25 38 35" stroke={spotColor} strokeWidth="1.5" fill="none" opacity="0.4"/>
      <path d="M 62 18 Q 65 28 60 32" stroke={spotColor} strokeWidth="1" fill="none" opacity="0.3"/>
    </svg>
  );

  return (
    <div className="p-6 relative overflow-hidden min-h-screen" data-testid="easter-eggs-page">
      {/* Floating T-Rex Eggs Animation */}
      <div className="fixed inset-0 pointer-events-none overflow-hidden z-0">
        {floatingEggs.map((egg) => (
          <div
            key={egg.id}
            className="absolute pointer-events-auto"
            style={{
              left: `${egg.x}%`,
              animation: `floatUp ${egg.duration}s linear ${egg.delay}s forwards`,
              bottom: "-100px"
            }}
          >
            <TRexEgg 
              color={egg.color} 
              spotColor={egg.spotColor} 
              size={egg.size}
              onClick={() => handleFloatingEggClick(egg)}
            />
          </div>
        ))}
      </div>

      <style>{`
        @keyframes floatUp {
          0% { transform: translateY(0) rotate(0deg); opacity: 0; }
          5% { opacity: 1; }
          95% { opacity: 1; }
          100% { transform: translateY(-120vh) rotate(360deg); opacity: 0; }
        }
        .trex-egg-card {
          background: linear-gradient(135deg, rgba(255,255,255,0.9), rgba(255,255,255,0.7));
          backdrop-filter: blur(10px);
          border: 2px solid;
        }
      `}</style>

      <div className="max-w-6xl mx-auto relative z-10">
        <div className="text-center mb-8">
          <h1 className="text-5xl font-bold font-['Outfit'] mb-3 bg-gradient-to-r from-orange-500 via-red-500 to-purple-600 text-transparent bg-clip-text">
            🦖 Ancient T-Rex Eggs 🥚
          </h1>
          <p className="text-gray-600 text-lg">
            Click floating eggs or browse below! Discover jokes, protocol tips, cheat codes, earn XP!
          </p>
        </div>

        {/* Selected Egg Popup */}
        {selectedEgg && (
          <div className="fixed inset-0 bg-black/50 flex items-center justify-center z-50" onClick={() => setSelectedEgg(null)}>
            <Card className="max-w-lg mx-4 trex-egg-card" style={{ borderColor: selectedEgg.egg_color || "#FF6B6B" }} onClick={e => e.stopPropagation()}>
              <CardContent className="p-8 text-center">
                <div className="mb-4">
                  <TRexEgg color={selectedEgg.egg_color || "#FF6B6B"} spotColor={selectedEgg.egg_spots || "#2C3E50"} size={80} />
                </div>
                <Badge className="mb-4" variant={selectedEgg.type === "joke" ? "default" : selectedEgg.type === "tip" ? "secondary" : "outline"}>
                  {selectedEgg.type === "joke" ? "😂 Joke" : selectedEgg.type === "tip" ? "💡 Protocol Tip" : "🎮 Cheat Code"}
                </Badge>
                <p className="text-lg font-medium mb-6">{selectedEgg.content}</p>
                <div className="flex gap-2 justify-center flex-wrap">
                  <Button size="sm" onClick={() => { submitLaugh(selectedEgg.egg_id, 'chuckle'); setSelectedEgg(null); }}>
                    😏 Chuckle
                  </Button>
                  <Button size="sm" onClick={() => { submitLaugh(selectedEgg.egg_id, 'laugh'); setSelectedEgg(null); }}>
                    😂 Laugh
                  </Button>
                  <Button size="sm" onClick={() => { submitLaugh(selectedEgg.egg_id, 'rofl'); setSelectedEgg(null); }}>
                    🤣 ROFL
                  </Button>
                </div>
                <Button variant="ghost" className="mt-4" onClick={() => setSelectedEgg(null)}>Close</Button>
              </CardContent>
            </Card>
          </div>
        )}

        {/* Tab Navigation */}
        <div className="flex justify-center gap-2 mb-6">
          {[
            { id: "all", label: "All Eggs", icon: "🥚" },
            { id: "joke", label: "Jokes", icon: "😂" },
            { id: "tip", label: "Protocol Tips", icon: "💡" },
            { id: "cheat_code", label: "Cheat Codes", icon: "🎮" }
          ].map(tab => (
            <Button
              key={tab.id}
              variant={activeTab === tab.id ? "default" : "outline"}
              size="sm"
              onClick={() => setActiveTab(tab.id)}
              className="gap-1"
            >
              {tab.icon} {tab.label}
            </Button>
          ))}
        </div>

        <div className="grid grid-cols-1 lg:grid-cols-3 gap-6">
          {/* Eggs Grid */}
          <div className="lg:col-span-2 space-y-4">
            <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
              {filteredEggs.map((egg, i) => (
                <Card 
                  key={egg.egg_id || i} 
                  className="trex-egg-card hover:scale-102 transition-all cursor-pointer" 
                  style={{ borderColor: egg.egg_color || "#FF6B6B" }}
                  data-testid={`easter-egg-${i}`}
                  onClick={() => setSelectedEgg(egg)}
                >
                  <CardContent className="p-5">
                    <div className="flex items-start gap-4">
                      <div className="flex-shrink-0">
                        <TRexEgg color={egg.egg_color || "#FF6B6B"} spotColor={egg.egg_spots || "#2C3E50"} size={50} />
                      </div>
                      <div className="flex-1">
                        <Badge className="mb-2" variant={egg.type === "joke" ? "default" : egg.type === "tip" ? "secondary" : "outline"}>
                          {egg.type === "joke" ? "😂 Joke" : egg.type === "tip" ? "💡 Tip" : "🎮 Cheat"}
                        </Badge>
                        <p className="text-sm">{egg.content}</p>
                        <p className="text-xs text-gray-400 mt-2">+{egg.reward_amount} XP</p>
                      </div>
                    </div>
                  </CardContent>
                </Card>
              ))}
            </div>
          </div>

          {/* Leaderboard */}
          <div className="space-y-4">
            <Card className="glass-card">
              <CardHeader>
                <CardTitle className="flex items-center gap-2">
                  <Trophy className="w-5 h-5 text-yellow-500" />
                  Laugh-O-Meter Champions
                </CardTitle>
              </CardHeader>
              <CardContent>
                <div className="space-y-3">
                  {(leaderboard?.top_laughers || []).map((entry, i) => (
                    <div key={i} className="flex items-center gap-3">
                      <span className="w-8 h-8 rounded-full bg-yellow-100 text-yellow-800 font-bold flex items-center justify-center">
                        {i + 1}
                      </span>
                      <span className="flex-1">{entry.user?.name || "Anonymous"}</span>
                      <span className="text-sm">{entry.total_laughs} laughs</span>
                    </div>
                  ))}
                  {(!leaderboard?.top_laughers || leaderboard.top_laughers.length === 0) && (
                    <p className="text-gray-500 text-center py-4">No laughers yet! Be the first!</p>
                  )}
                </div>
              </CardContent>
            </Card>

            <Card className="glass-card">
              <CardHeader>
                <CardTitle className="flex items-center gap-2">
                  <Egg className="w-5 h-5 text-orange-500" />
                  T-Rex Egg Facts
                </CardTitle>
              </CardHeader>
              <CardContent className="text-sm text-gray-600 space-y-2">
                <p>• These ancient eggs have been preserved for 65 million years!</p>
                <p>• Each egg contains wisdom from the prehistoric internet</p>
                <p>• Click floating eggs to discover hidden content</p>
                <p>• Earn XP by laughing at jokes and learning tips</p>
              </CardContent>
            </Card>
          </div>
        </div>
      </div>
    </div>
  );
};

export default EasterEggsPage;
