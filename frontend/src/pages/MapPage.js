import React, { useState } from 'react';
import { Navigate } from 'react-router-dom';
import { useQuery } from '@tanstack/react-query';
import axios from 'axios';
import { MapContainer, TileLayer, CircleMarker, Popup } from 'react-leaflet';
import 'leaflet/dist/leaflet.css';
import { useAuth } from '../context/AuthContext';
import StarsBackground from '../components/StarsBackground';
import { Card } from '../components/ui/card';
import { Badge } from '../components/ui/badge';
import { Select, SelectContent, SelectItem, SelectTrigger, SelectValue } from '../components/ui/select';
import { MapPin, FileText, Layers, Globe, RefreshCw } from 'lucide-react';

const API = process.env.REACT_APP_BACKEND_URL + '/api';

const MapPage = () => {
  const { user } = useAuth();
  const [scope, setScope] = useState("personal");
  const { data: mapData, isLoading } = useQuery({
    queryKey: ["map-data", scope],
    queryFn: () => axios.get(`${API}/map/data`, { params: { scope } }).then(r => r.data),
    enabled: !!user
  });
  const { data: categoriesData } = useQuery({
    queryKey: ["categories"],
    queryFn: () => axios.get(`${API}/categories`).then(r => r.data),
    enabled: !!user
  });

  if (!user) return <Navigate to="/login" />;

  const categories = categoriesData?.categories || [];
  const points = mapData?.points || [];

  return (
    <div className="min-h-screen pt-20 px-4">
      <StarsBackground />
      <div className="max-w-7xl mx-auto">
        <div className="flex items-center justify-between mb-6">
          <div>
            <h1 className="text-3xl font-bold text-gradient-gold">Interactive Map View</h1>
            <p className="text-white/60">Explore search results plotted on a global map</p>
          </div>
          <div className="flex items-center gap-4">
            <Select value={scope} onValueChange={setScope}>
              <SelectTrigger className="form-input w-40">
                <SelectValue />
              </SelectTrigger>
              <SelectContent className="bg-slate-800">
                <SelectItem value="personal">My Results</SelectItem>
                <SelectItem value="worldwide">Worldwide</SelectItem>
              </SelectContent>
            </Select>
          </div>
        </div>

        <Card className="card-glass overflow-hidden" data-testid="map-container">
          {isLoading ? (
            <div className="h-[600px] flex items-center justify-center"><RefreshCw className="animate-spin text-yellow-400" size={48} /></div>
          ) : (
            <MapContainer center={[40, -40]} zoom={2} style={{ height: "600px", width: "100%" }} className="rounded-lg">
              <TileLayer
                url="https://{s}.basemaps.cartocdn.com/dark_all/{z}/{x}/{y}{r}.png"
                attribution='&copy; <a href="https://www.openstreetmap.org/copyright">OpenStreetMap</a>'
              />
              {points.map((point, idx) => (
                <CircleMarker
                  key={idx}
                  center={[point.lat, point.lng]}
                  radius={Math.min(8 + point.result_count * 2, 20)}
                  fillColor={point.color}
                  color={point.color}
                  weight={2}
                  opacity={0.8}
                  fillOpacity={0.6}
                >
                  <Popup className="custom-popup">
                    <div className="bg-slate-900 p-3 rounded-lg min-w-[250px]">
                      <div className="flex items-center justify-between mb-2">
                        <Badge className="bg-blue-500/20 text-blue-300">{point.result_count} results</Badge>
                        <span className="text-xs text-white/60">{point.category_count} categories</span>
                      </div>
                      <div className="space-y-2 max-h-48 overflow-y-auto">
                        {point.results?.map((r, i) => (
                          <div key={i} className="p-2 bg-white/5 rounded">
                            <a href={r.url} target="_blank" rel="noopener noreferrer" className="text-yellow-400 text-sm hover:underline font-semibold block truncate">{r.title}</a>
                            <p className="text-white/60 text-xs mt-1 line-clamp-2">{r.snippet}</p>
                            <Badge className="text-xs mt-1">{r.document_type}</Badge>
                          </div>
                        ))}
                      </div>
                    </div>
                  </Popup>
                </CircleMarker>
              ))}
            </MapContainer>
          )}
        </Card>

        <div className="mt-6 grid md:grid-cols-4 gap-4">
          <Card className="card-glass p-4 text-center">
            <MapPin className="mx-auto text-yellow-400 mb-2" size={24} />
            <p className="text-2xl font-bold text-white">{points.length}</p>
            <p className="text-white/60 text-sm">Locations</p>
          </Card>
          <Card className="card-glass p-4 text-center">
            <FileText className="mx-auto text-blue-400 mb-2" size={24} />
            <p className="text-2xl font-bold text-white">{points.reduce((a, p) => a + p.result_count, 0)}</p>
            <p className="text-white/60 text-sm">Total Results</p>
          </Card>
          <Card className="card-glass p-4 text-center">
            <Layers className="mx-auto text-green-400 mb-2" size={24} />
            <p className="text-2xl font-bold text-white">{categories.length}</p>
            <p className="text-white/60 text-sm">Categories</p>
          </Card>
          <Card className="card-glass p-4 text-center">
            <Globe className="mx-auto text-purple-400 mb-2" size={24} />
            <p className="text-2xl font-bold text-white">{scope === "personal" ? "Personal" : "Worldwide"}</p>
            <p className="text-white/60 text-sm">View Scope</p>
          </Card>
        </div>
      </div>
    </div>
  );
};

export default MapPage;
