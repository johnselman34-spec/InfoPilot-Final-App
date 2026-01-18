import React from 'react';
import { Navigate } from 'react-router-dom';
import { useAuth } from '../context/AuthContext';
import StarsBackground from '../components/StarsBackground';
import { Card } from '../components/ui/card';
import { Map } from 'lucide-react';

const MapPage = () => {
  const { user } = useAuth();
  if (!user) return <Navigate to="/login" />;
  
  return (
    <div className="min-h-screen pt-20 px-4">
      <StarsBackground />
      <div className="max-w-6xl mx-auto">
        <h1 className="text-3xl font-bold text-gradient-gold mb-8 text-center">Interactive Map</h1>
        <Card className="card-glass p-8 text-center">
          <Map className="mx-auto text-yellow-400 mb-4" size={64} />
          <p className="text-white/60">Map view coming soon! Visualize your search results geographically.</p>
        </Card>
      </div>
    </div>
  );
};
export default MapPage;
