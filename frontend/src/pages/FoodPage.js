import React from 'react';
import StarsBackground from '../components/StarsBackground';
import { Card, CardHeader, CardTitle, CardDescription, CardContent } from '../components/ui/card';
import { Button } from '../components/ui/button';
import { Badge } from '../components/ui/badge';
import { Utensils, MapPin, Phone, Clock } from 'lucide-react';

const menuItems = [
  { name: "German Beef Rouladen", price: 18.99, desc: "Traditional rolled beef with bacon, onions, mustard", tagline: "So good, your stepmother might try to claim she invented it!" },
  { name: "Vegetable Rouladen", price: 15.99, desc: "Vegetarian version with seasonal vegetables", tagline: "Even my stepmother couldnt mess this up... probably!" },
  { name: "Maestro Fish Chowder", price: 12.99, desc: "Creamy New England style with fresh Maine seafood", tagline: "Fresher than my stepmothers excuses!" }
];

const FoodPage = () => {
  return (
    <div className="min-h-screen pt-20 px-4">
      <StarsBackground />
      <div className="max-w-5xl mx-auto">
        <div className="text-center mb-8">
          <Badge className="mb-4 bg-green-500/20 text-green-300">Brunswick, Maine</Badge>
          <h1 className="text-4xl font-bold text-gradient-gold mb-2">Maestro Bistro</h1>
          <p className="text-white/60">Authentic German Cuisine Food Truck</p>
        </div>
        
        <div className="grid md:grid-cols-3 gap-4 mb-8">
          <Card className="card-glass p-4 text-center">
            <MapPin className="mx-auto text-green-400 mb-2" size={24} />
            <p className="text-white text-sm">Brunswick, Maine</p>
          </Card>
          <Card className="card-glass p-4 text-center">
            <Phone className="mx-auto text-green-400 mb-2" size={24} />
            <p className="text-white text-sm">207-522-0894</p>
          </Card>
          <Card className="card-glass p-4 text-center">
            <Clock className="mx-auto text-green-400 mb-2" size={24} />
            <p className="text-white text-sm">11am - 7pm</p>
          </Card>
        </div>
        
        <h2 className="text-2xl font-bold text-white mb-6">Menu</h2>
        <div className="grid md:grid-cols-3 gap-6">
          {menuItems.map((item, i) => (
            <Card key={i} className="card-glass overflow-hidden">
              <div className="h-32 bg-gradient-to-br from-green-600/50 to-emerald-800/50 flex items-center justify-center">
                <Utensils className="text-white/50" size={48} />
              </div>
              <CardHeader>
                <div className="flex items-center justify-between">
                  <CardTitle className="text-white">{item.name}</CardTitle>
                  <Badge className="bg-green-500/20 text-green-300 text-lg">${item.price}</Badge>
                </div>
                <CardDescription className="text-yellow-300/80 italic">&quot;{item.tagline}&quot;</CardDescription>
              </CardHeader>
              <CardContent>
                <p className="text-white/60 text-sm">{item.desc}</p>
                <Button className="w-full mt-4 bg-green-600 hover:bg-green-500">Add to Cart</Button>
              </CardContent>
            </Card>
          ))}
        </div>
      </div>
    </div>
  );
};
export default FoodPage;
