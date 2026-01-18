import React from 'react';
import StarsBackground from '../components/StarsBackground';
import { Card } from '../components/ui/card';
import { BarChart3 } from 'lucide-react';

const StatsPage = () => {
  return (
    <div className="min-h-screen pt-20 px-4">
      <StarsBackground />
      <div className="max-w-6xl mx-auto">
        <h1 className="text-3xl font-bold text-gradient-gold mb-8 text-center">Statistics</h1>
        <Card className="card-glass p-8 text-center">
          <BarChart3 className="mx-auto text-cyan-400 mb-4" size={64} />
          <p className="text-white/60">Platform statistics and leaderboards. Full functionality in the original App.js</p>
        </Card>
      </div>
    </div>
  );
};
export default StatsPage;
