import React from 'react';
import { Navigate } from 'react-router-dom';
import { useAuth } from '../context/AuthContext';
import StarsBackground from '../components/StarsBackground';
import { Card } from '../components/ui/card';
import { DollarSign } from 'lucide-react';

const RevenuePage = () => {
  const { user } = useAuth();
  if (!user) return <Navigate to="/login" />;
  return (
    <div className="min-h-screen pt-20 px-4">
      <StarsBackground />
      <div className="max-w-6xl mx-auto">
        <h1 className="text-3xl font-bold text-gradient-gold mb-8 text-center">Revenue Dashboard</h1>
        <Card className="card-glass p-8 text-center">
          <DollarSign className="mx-auto text-green-400 mb-4" size={64} />
          <p className="text-white/60">Revenue dashboard with PDF export. Full functionality available in the original App.js</p>
        </Card>
      </div>
    </div>
  );
};
export default RevenuePage;
