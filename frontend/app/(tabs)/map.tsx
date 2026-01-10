import React, { useState, useEffect } from 'react';
import {
  View,
  Text,
  StyleSheet,
  ScrollView,
  TouchableOpacity,
  TextInput,
  Alert,
  ActivityIndicator,
  FlatList,
  Dimensions,
} from 'react-native';
import { SafeAreaView } from 'react-native-safe-area-context';
import { Ionicons } from '@expo/vector-icons';
import { useAuth } from '../../src/context/AuthContext';
import { api } from '../../src/services/api';

interface MapMarker {
  id: string;
  latitude: number;
  longitude: number;
  title: string;
  url: string;
  categories: string[];
}

export default function MapScreen() {
  const { user } = useAuth();
  const [markers, setMarkers] = useState<MapMarker[]>([]);
  const [loading, setLoading] = useState(true);
  const [selectedMarker, setSelectedMarker] = useState<MapMarker | null>(null);

  useEffect(() => {
    loadMapData();
  }, []);

  const loadMapData = async () => {
    try {
      const data = await api.get('/map-data');
      setMarkers(data.markers || []);
    } catch (error: any) {
      if (error.response?.status === 403) {
        // User not premium
      }
    } finally {
      setLoading(false);
    }
  };

  if (!user?.is_paid) {
    return (
      <SafeAreaView style={styles.container} edges={['top']}>
        <View style={styles.header}>
          <Ionicons name="map" size={28} color="#2196F3" />
          <Text style={styles.headerTitle}>World Map</Text>
        </View>
        <View style={styles.premiumRequired}>
          <Ionicons name="lock-closed" size={64} color="#ccc" />
          <Text style={styles.premiumTitle}>Premium Feature</Text>
          <Text style={styles.premiumText}>
            The interactive world map showing your collated search results
            is available for premium subscribers.
          </Text>
          <TouchableOpacity style={styles.upgradeButton}>
            <Ionicons name="star" size={20} color="#fff" />
            <Text style={styles.upgradeText}>Upgrade for $0.99</Text>
          </TouchableOpacity>
        </View>
      </SafeAreaView>
    );
  }

  return (
    <SafeAreaView style={styles.container} edges={['top']}>
      <View style={styles.header}>
        <Ionicons name="map" size={28} color="#2196F3" />
        <Text style={styles.headerTitle}>World Map</Text>
      </View>

      {loading ? (
        <ActivityIndicator size="large" color="#2196F3" style={styles.loader} />
      ) : markers.length === 0 ? (
        <View style={styles.emptyState}>
          <Ionicons name="location-outline" size={64} color="#ccc" />
          <Text style={styles.emptyTitle}>No Location Data Yet</Text>
          <Text style={styles.emptyText}>
            Search and collate web content to see location markers on the map.
            Location data is automatically extracted from articles when available.
          </Text>
        </View>
      ) : (
        <View style={styles.mapContainer}>
          {/* Simple map visualization */}
          <View style={styles.mapPlaceholder}>
            <View style={styles.worldMapBg}>
              <Text style={styles.mapLabel}>World Map View</Text>
              <Text style={styles.markerCount}>{markers.length} locations found</Text>
            </View>
            
            {/* Markers list */}
            <ScrollView style={styles.markersList}>
              <Text style={styles.markersTitle}>Location Markers</Text>
              {markers.map((marker) => (
                <TouchableOpacity
                  key={marker.id}
                  style={styles.markerCard}
                  onPress={() => setSelectedMarker(marker)}
                >
                  <View style={styles.markerIcon}>
                    <Ionicons name="location" size={24} color="#f44336" />
                  </View>
                  <View style={styles.markerInfo}>
                    <Text style={styles.markerTitle} numberOfLines={1}>
                      {marker.title}
                    </Text>
                    <Text style={styles.markerCoords}>
                      {marker.latitude.toFixed(4)}, {marker.longitude.toFixed(4)}
                    </Text>
                    <View style={styles.markerCategories}>
                      {marker.categories.slice(0, 2).map((cat, idx) => (
                        <View key={idx} style={styles.categoryBadge}>
                          <Text style={styles.categoryText}>{cat}</Text>
                        </View>
                      ))}
                    </View>
                  </View>
                </TouchableOpacity>
              ))}
            </ScrollView>
          </View>
        </View>
      )}

      {/* Selected Marker Modal */}
      {selectedMarker && (
        <View style={styles.modalOverlay}>
          <View style={styles.modalContent}>
            <TouchableOpacity
              style={styles.modalClose}
              onPress={() => setSelectedMarker(null)}
            >
              <Ionicons name="close" size={24} color="#666" />
            </TouchableOpacity>
            <Ionicons name="location" size={40} color="#f44336" />
            <Text style={styles.modalTitle}>{selectedMarker.title}</Text>
            <Text style={styles.modalCoords}>
              Lat: {selectedMarker.latitude.toFixed(6)}, Long: {selectedMarker.longitude.toFixed(6)}
            </Text>
            <View style={styles.modalCategories}>
              {selectedMarker.categories.map((cat, idx) => (
                <View key={idx} style={styles.modalCategoryBadge}>
                  <Text style={styles.modalCategoryText}>{cat}</Text>
                </View>
              ))}
            </View>
            <TouchableOpacity style={styles.openLinkButton}>
              <Ionicons name="open-outline" size={18} color="#fff" />
              <Text style={styles.openLinkText}>Open Article</Text>
            </TouchableOpacity>
          </View>
        </View>
      )}
    </SafeAreaView>
  );
}

const styles = StyleSheet.create({
  container: {
    flex: 1,
    backgroundColor: '#FFFFF0',
  },
  header: {
    flexDirection: 'row',
    alignItems: 'center',
    paddingHorizontal: 16,
    paddingVertical: 12,
    backgroundColor: '#fff',
    borderBottomWidth: 1,
    borderBottomColor: '#E0E0E0',
  },
  headerTitle: {
    fontSize: 20,
    fontWeight: 'bold',
    color: '#333',
    marginLeft: 10,
  },
  loader: {
    marginTop: 40,
  },
  premiumRequired: {
    flex: 1,
    alignItems: 'center',
    justifyContent: 'center',
    padding: 32,
  },
  premiumTitle: {
    fontSize: 20,
    fontWeight: '600',
    color: '#333',
    marginTop: 16,
  },
  premiumText: {
    fontSize: 14,
    color: '#666',
    textAlign: 'center',
    marginTop: 8,
    lineHeight: 20,
  },
  upgradeButton: {
    flexDirection: 'row',
    alignItems: 'center',
    backgroundColor: '#4CAF50',
    paddingHorizontal: 24,
    paddingVertical: 12,
    borderRadius: 24,
    marginTop: 24,
  },
  upgradeText: {
    color: '#fff',
    fontSize: 16,
    fontWeight: '600',
    marginLeft: 8,
  },
  emptyState: {
    flex: 1,
    alignItems: 'center',
    justifyContent: 'center',
    padding: 32,
  },
  emptyTitle: {
    fontSize: 18,
    fontWeight: '600',
    color: '#333',
    marginTop: 16,
  },
  emptyText: {
    fontSize: 14,
    color: '#666',
    textAlign: 'center',
    marginTop: 8,
    lineHeight: 20,
  },
  mapContainer: {
    flex: 1,
  },
  mapPlaceholder: {
    flex: 1,
  },
  worldMapBg: {
    height: 200,
    backgroundColor: '#E3F2FD',
    alignItems: 'center',
    justifyContent: 'center',
    borderBottomWidth: 1,
    borderBottomColor: '#BBDEFB',
  },
  mapLabel: {
    fontSize: 18,
    fontWeight: '600',
    color: '#1976D2',
  },
  markerCount: {
    fontSize: 14,
    color: '#666',
    marginTop: 8,
  },
  markersList: {
    flex: 1,
    padding: 16,
  },
  markersTitle: {
    fontSize: 16,
    fontWeight: '600',
    color: '#333',
    marginBottom: 12,
  },
  markerCard: {
    flexDirection: 'row',
    backgroundColor: '#fff',
    borderRadius: 12,
    padding: 12,
    marginBottom: 10,
    borderWidth: 1,
    borderColor: '#E0E0E0',
  },
  markerIcon: {
    width: 44,
    height: 44,
    borderRadius: 22,
    backgroundColor: '#FFEBEE',
    alignItems: 'center',
    justifyContent: 'center',
    marginRight: 12,
  },
  markerInfo: {
    flex: 1,
  },
  markerTitle: {
    fontSize: 14,
    fontWeight: '600',
    color: '#333',
  },
  markerCoords: {
    fontSize: 12,
    color: '#666',
    marginTop: 2,
  },
  markerCategories: {
    flexDirection: 'row',
    marginTop: 6,
  },
  categoryBadge: {
    backgroundColor: '#E3F2FD',
    paddingHorizontal: 8,
    paddingVertical: 2,
    borderRadius: 8,
    marginRight: 6,
  },
  categoryText: {
    fontSize: 10,
    color: '#1976D2',
  },
  modalOverlay: {
    position: 'absolute',
    top: 0,
    left: 0,
    right: 0,
    bottom: 0,
    backgroundColor: 'rgba(0,0,0,0.5)',
    alignItems: 'center',
    justifyContent: 'center',
  },
  modalContent: {
    backgroundColor: '#fff',
    borderRadius: 16,
    padding: 24,
    width: '85%',
    alignItems: 'center',
  },
  modalClose: {
    position: 'absolute',
    top: 12,
    right: 12,
  },
  modalTitle: {
    fontSize: 16,
    fontWeight: '600',
    color: '#333',
    textAlign: 'center',
    marginTop: 12,
  },
  modalCoords: {
    fontSize: 12,
    color: '#666',
    marginTop: 8,
  },
  modalCategories: {
    flexDirection: 'row',
    flexWrap: 'wrap',
    justifyContent: 'center',
    marginTop: 12,
  },
  modalCategoryBadge: {
    backgroundColor: '#E3F2FD',
    paddingHorizontal: 10,
    paddingVertical: 4,
    borderRadius: 12,
    margin: 3,
  },
  modalCategoryText: {
    fontSize: 12,
    color: '#1976D2',
  },
  openLinkButton: {
    flexDirection: 'row',
    alignItems: 'center',
    backgroundColor: '#2196F3',
    paddingHorizontal: 20,
    paddingVertical: 10,
    borderRadius: 20,
    marginTop: 16,
  },
  openLinkText: {
    color: '#fff',
    fontSize: 14,
    fontWeight: '600',
    marginLeft: 6,
  },
});
