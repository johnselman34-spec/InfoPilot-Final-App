import React, { useState, useEffect } from "react";
import { Globe } from "lucide-react";
import { Button } from "@/components/ui/button";
import { Card, CardContent } from "@/components/ui/card";
import { Badge } from "@/components/ui/badge";
import { Dialog, DialogContent, DialogHeader, DialogTitle } from "@/components/ui/dialog";
import axios from "axios";

const BACKEND_URL = process.env.REACT_APP_BACKEND_URL;
const api = axios.create({
  baseURL: `${BACKEND_URL}/api`,
  withCredentials: true
});

const MapViewPage = () => {
  const [locations, setLocations] = useState([]);
  const [loading, setLoading] = useState(true);
  const [selectedLocation, setSelectedLocation] = useState(null);
  const [locationResults, setLocationResults] = useState([]);
  const [loadingResults, setLoadingResults] = useState(false);

  useEffect(() => {
    fetchMapData();
  }, []);

  const fetchMapData = async () => {
    try {
      const response = await api.get("/stats/map-data-detailed");
      setLocations(response.data.locations || []);
    } catch (error) {
      console.error("Error fetching map data:", error);
    } finally {
      setLoading(false);
    }
  };

  const handleLocationClick = async (location) => {
    setSelectedLocation(location);
    setLoadingResults(true);
    
    try {
      const loc = location.location;
      const locationKey = `${loc.country || ''}_${loc.state || ''}_${loc.city || ''}`;
      const response = await api.get(`/stats/map-location/${encodeURIComponent(locationKey)}`);
      setLocationResults(response.data.results || []);
    } catch (error) {
      console.error("Error fetching location results:", error);
      setLocationResults([]);
    } finally {
      setLoadingResults(false);
    }
  };

  const closeLocationModal = () => {
    setSelectedLocation(null);
    setLocationResults([]);
  };

  return (
    <div className="p-6" data-testid="map-view-page">
      <div className="max-w-7xl mx-auto">
        <h1 className="text-4xl font-bold font-['Outfit'] mb-2">Map View</h1>
        <p className="text-gray-600 mb-6">Click on any location dot to see all associated search results</p>
        
        <Card className="glass-card">
          <CardContent className="p-6">
            <div className="h-[600px] rounded-xl overflow-hidden bg-gradient-to-br from-blue-50 to-green-50">
              {loading ? (
                <div className="h-full flex items-center justify-center">
                  <div className="spinner"></div>
                </div>
              ) : locations.length > 0 ? (
                <div className="h-full relative">
                  {/* World Map Placeholder with Location Dots */}
                  <div className="absolute inset-0 flex items-center justify-center">
                    <Globe className="w-32 h-32 text-[#007AFF]/20" />
                  </div>
                  
                  {/* Location Dots Grid */}
                  <div className="absolute inset-0 p-8 overflow-auto">
                    <div className="grid grid-cols-2 md:grid-cols-3 lg:grid-cols-4 gap-4">
                      {locations.map((loc, index) => (
                        <button
                          key={index}
                          onClick={() => handleLocationClick(loc)}
                          className="group p-4 bg-white rounded-xl shadow-sm hover:shadow-lg transition-all border border-gray-100 hover:border-[#007AFF] text-left"
                          data-testid={`location-dot-${index}`}
                        >
                          <div className="flex items-center gap-3 mb-2">
                            <div className={`w-4 h-4 rounded-full ${
                              loc.count > 10 ? 'bg-[#FF6B6B]' : 
                              loc.count > 5 ? 'bg-[#FFD60A]' : 'bg-[#34C759]'
                            }`} />
                            <span className="font-medium text-sm">
                              {loc.location.city || loc.location.state || loc.location.country || 'Unknown'}
                            </span>
                          </div>
                          <p className="text-xs text-gray-500">
                            {loc.location.state && `${loc.location.state}, `}
                            {loc.location.country}
                          </p>
                          <p className="text-xs text-[#007AFF] mt-1">{loc.count} results</p>
                        </button>
                      ))}
                    </div>
                  </div>
                  
                  {/* Legend */}
                  <div className="absolute bottom-4 right-4 bg-white/90 backdrop-blur-sm rounded-lg p-3 shadow-lg">
                    <p className="text-xs font-medium mb-2">Results Count</p>
                    <div className="flex items-center gap-4 text-xs">
                      <div className="flex items-center gap-1">
                        <div className="w-3 h-3 rounded-full bg-[#34C759]" />
                        <span>1-5</span>
                      </div>
                      <div className="flex items-center gap-1">
                        <div className="w-3 h-3 rounded-full bg-[#FFD60A]" />
                        <span>6-10</span>
                      </div>
                      <div className="flex items-center gap-1">
                        <div className="w-3 h-3 rounded-full bg-[#FF6B6B]" />
                        <span>10+</span>
                      </div>
                    </div>
                  </div>
                </div>
              ) : (
                <div className="h-full flex flex-col items-center justify-center">
                  <Globe className="w-24 h-24 text-gray-300 mb-4" />
                  <p className="text-gray-500 text-center">
                    Search and collate results to see locations on the map
                  </p>
                </div>
              )}
            </div>
          </CardContent>
        </Card>
        
        {/* Location Results Dialog */}
        <Dialog open={!!selectedLocation} onOpenChange={(open) => !open && closeLocationModal()}>
          <DialogContent className="max-w-2xl max-h-[80vh] overflow-y-auto">
            <DialogHeader>
              <DialogTitle>
                Results from {selectedLocation?.location?.city || selectedLocation?.location?.state || selectedLocation?.location?.country || 'this location'}
              </DialogTitle>
            </DialogHeader>
            
            {loadingResults ? (
              <div className="py-8 text-center">
                <div className="spinner mx-auto"></div>
                <p className="text-gray-500 mt-4">Loading results...</p>
              </div>
            ) : (
              <div className="space-y-4 mt-4">
                <p className="text-sm text-gray-500">{locationResults.length} results found</p>
                
                {locationResults.map((result, idx) => (
                  <Card key={idx} className="hover:shadow-md transition-shadow">
                    <CardContent className="p-4">
                      <div className="flex items-start justify-between gap-4">
                        <div className="flex-1">
                          <Badge className="mb-2" variant="outline">{result.document_type}</Badge>
                          <h3 className="font-semibold text-sm mb-1">
                            <a href={result.url} target="_blank" rel="noopener noreferrer" className="hover:text-[#007AFF]">
                              {result.title}
                            </a>
                          </h3>
                          <p className="text-xs text-gray-500 line-clamp-2">{result.snippet}</p>
                        </div>
                      </div>
                    </CardContent>
                  </Card>
                ))}
                
                {locationResults.length === 0 && (
                  <p className="text-center text-gray-500 py-4">No results found for this location</p>
                )}
              </div>
            )}
          </DialogContent>
        </Dialog>
      </div>
    </div>
  );
};

export default MapViewPage;
