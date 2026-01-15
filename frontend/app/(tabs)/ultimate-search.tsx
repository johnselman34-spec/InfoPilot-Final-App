import React, { useState, useEffect, useCallback } from 'react';
import {
  View,
  Text,
  StyleSheet,
  ScrollView,
  TouchableOpacity,
  TextInput,
  Alert,
  ActivityIndicator,
  Dimensions,
  Platform,
  Linking,
  Modal,
} from 'react-native';
import { SafeAreaView } from 'react-native-safe-area-context';
import { Ionicons } from '@expo/vector-icons';
import { colors } from '../../src/utils/colors';
import { searchAPI, categoryAPI } from '../../src/services/api';
import AsyncStorage from '@react-native-async-storage/async-storage';

const { width } = Dimensions.get('window');

interface SearchResult {
  id: string;
  title: string;
  url: string;
  snippet: string;
  article_type?: string;
  root_domain?: string;
  year?: number;
  category_ids?: string[];
  likes?: number;
  loves?: number;
  location?: {
    latitude: number;
    longitude: number;
    city?: string;
    country?: string;
  };
}

interface Category {
  id: string;
  name: string;
  protocol: string;
  is_public: boolean;
  level?: number;
}

type CombineMode = 'or' | 'and';

// World locations for map visualization
const WORLD_LOCATIONS = [
  { city: 'New York', country: 'USA', lat: 40.7128, lng: -74.0060, emoji: '🗽' },
  { city: 'London', country: 'UK', lat: 51.5074, lng: -0.1278, emoji: '🇬🇧' },
  { city: 'Paris', country: 'France', lat: 48.8566, lng: 2.3522, emoji: '🗼' },
  { city: 'Tokyo', country: 'Japan', lat: 35.6762, lng: 139.6503, emoji: '🗾' },
  { city: 'Sydney', country: 'Australia', lat: -33.8688, lng: 151.2093, emoji: '🦘' },
  { city: 'Berlin', country: 'Germany', lat: 52.5200, lng: 13.4050, emoji: '🇩🇪' },
  { city: 'Moscow', country: 'Russia', lat: 55.7558, lng: 37.6173, emoji: '🇷🇺' },
  { city: 'Dubai', country: 'UAE', lat: 25.2048, lng: 55.2708, emoji: '🏜️' },
  { city: 'Singapore', country: 'Singapore', lat: 1.3521, lng: 103.8198, emoji: '🇸🇬' },
  { city: 'São Paulo', country: 'Brazil', lat: -23.5505, lng: -46.6333, emoji: '🇧🇷' },
  { city: 'Toronto', country: 'Canada', lat: 43.6532, lng: -79.3832, emoji: '🍁' },
  { city: 'Mumbai', country: 'India', lat: 19.0760, lng: 72.8777, emoji: '🇮🇳' },
];

// Page name storage key
const PAGE_NAME_KEY = 'ultimate_search_page_name';
const DEFAULT_PAGE_NAME = 'Ultimate Search';

export default function UltimateSearchScreen() {
  // Page customization
  const [pageName, setPageName] = useState(DEFAULT_PAGE_NAME);
  const [isEditingName, setIsEditingName] = useState(false);
  const [tempPageName, setTempPageName] = useState('');
  
  // Search state
  const [searchQuery, setSearchQuery] = useState('');
  const [results, setResults] = useState<SearchResult[]>([]);
  const [loading, setLoading] = useState(false);
  const [loadingResults, setLoadingResults] = useState(false);
  
  // Category state
  const [categories, setCategories] = useState<Category[]>([]);
  const [selectedCategoryIds, setSelectedCategoryIds] = useState<Set<string>>(new Set());
  const [combineMode, setCombineMode] = useState<CombineMode>('or');
  
  // View state
  const [viewMode, setViewMode] = useState<'list' | 'map'>('map');
  const [showFilters, setShowFilters] = useState(false);
  
  // Map data
  const [mapLocations, setMapLocations] = useState<typeof WORLD_LOCATIONS>([]);

  // Load saved page name
  useEffect(() => {
    loadPageName();
    loadCategories();
  }, []);

  // Load results when categories change
  useEffect(() => {
    if (selectedCategoryIds.size > 0) {
      loadSearchResults();
    }
  }, [selectedCategoryIds, combineMode]);

  // Update map when results change
  useEffect(() => {
    updateMapLocations();
  }, [results]);

  const loadPageName = async () => {
    try {
      const savedName = await AsyncStorage.getItem(PAGE_NAME_KEY);
      if (savedName) {
        setPageName(savedName);
      }
    } catch (error) {
      console.error('Error loading page name:', error);
    }
  };

  const savePageName = async (name: string) => {
    try {
      await AsyncStorage.setItem(PAGE_NAME_KEY, name);
      setPageName(name);
      setIsEditingName(false);
      Alert.alert('Success! 🎉', `Page renamed to "${name}"`);
    } catch (error) {
      console.error('Error saving page name:', error);
    }
  };

  const loadCategories = async () => {
    try {
      const response = await categoryAPI.getAll();
      const cats = response.data?.categories || [];
      setCategories(cats);
      // Select all by default
      setSelectedCategoryIds(new Set(cats.map((c: Category) => c.id)));
    } catch (error) {
      console.error('Load categories error:', error);
    }
  };

  const loadSearchResults = async () => {
    if (selectedCategoryIds.size === 0) {
      setResults([]);
      return;
    }

    try {
      setLoadingResults(true);
      const categoryIdsParam = Array.from(selectedCategoryIds).join(',');
      
      const response = await searchAPI.getResults({
        category_ids: categoryIdsParam,
        page: 1,
      });

      if (response.data) {
        // Add locations to results that don't have them
        const resultsWithLocations = (response.data.results || []).map((r: SearchResult, index: number) => ({
          ...r,
          location: r.location || generateLocation(index),
        }));
        setResults(resultsWithLocations);
      }
    } catch (error) {
      console.error('Load search results error:', error);
      setResults([]);
    } finally {
      setLoadingResults(false);
    }
  };

  const generateLocation = (index: number) => {
    const loc = WORLD_LOCATIONS[index % WORLD_LOCATIONS.length];
    return {
      latitude: loc.lat,
      longitude: loc.lng,
      city: loc.city,
      country: loc.country,
    };
  };

  const updateMapLocations = () => {
    // Group results by location
    const locationCounts: Record<string, { location: typeof WORLD_LOCATIONS[0]; count: number; results: SearchResult[] }> = {};
    
    results.forEach((result, index) => {
      const loc = result.location || generateLocation(index);
      const key = loc.city || `loc_${index}`;
      
      if (!locationCounts[key]) {
        const worldLoc = WORLD_LOCATIONS.find(w => w.city === loc.city) || WORLD_LOCATIONS[index % WORLD_LOCATIONS.length];
        locationCounts[key] = {
          location: worldLoc,
          count: 0,
          results: [],
        };
      }
      locationCounts[key].count++;
      locationCounts[key].results.push(result);
    });

    setMapLocations(Object.values(locationCounts).map(lc => ({
      ...lc.location,
      resultCount: lc.count,
      results: lc.results,
    })) as any);
  };

  const toggleCategorySelection = (categoryId: string) => {
    const newSelected = new Set(selectedCategoryIds);
    if (newSelected.has(categoryId)) {
      newSelected.delete(categoryId);
    } else {
      newSelected.add(categoryId);
    }
    setSelectedCategoryIds(newSelected);
  };

  const selectAllCategories = () => {
    setSelectedCategoryIds(new Set(categories.map(c => c.id)));
  };

  const clearAllSelections = () => {
    setSelectedCategoryIds(new Set());
    setResults([]);
  };

  const handleReaction = async (resultId: string, reactionType: string) => {
    try {
      await searchAPI.react(resultId, reactionType);
      setResults(prev => prev.map(r => {
        if (r.id === resultId) {
          const key = reactionType + 's' as keyof SearchResult;
          return { ...r, [key]: ((r as any)[key] || 0) + 1 };
        }
        return r;
      }));
    } catch (error) {
      console.error('Reaction error:', error);
    }
  };

  // Render search result card
  const renderResultCard = (result: SearchResult) => (
    <TouchableOpacity 
      key={result.id}
      style={styles.resultCard}
      onPress={() => Linking.openURL(result.url)}
    >
      <View style={styles.resultHeader}>
        {result.article_type && (
          <View style={[styles.typeBadge, getTypeBadgeStyle(result.article_type)]}>
            <Text style={styles.typeBadgeText}>{result.article_type}</Text>
          </View>
        )}
        {result.year && (
          <View style={styles.yearBadge}>
            <Ionicons name="calendar" size={12} color={colors.accent} />
            <Text style={styles.yearText}>{result.year}</Text>
          </View>
        )}
        {result.location && (
          <View style={styles.locationBadge}>
            <Ionicons name="location" size={12} color={colors.primary} />
            <Text style={styles.locationText}>{result.location.city}</Text>
          </View>
        )}
      </View>
      
      <Text style={styles.resultTitle} numberOfLines={2}>{result.title}</Text>
      <Text style={styles.resultSnippet} numberOfLines={3}>{result.snippet}</Text>
      <Text style={styles.resultUrl} numberOfLines={1}>🔗 {result.root_domain || result.url}</Text>
      
      {/* Reaction Buttons */}
      <View style={styles.reactionsRow}>
        {[
          { key: 'likes', icon: 'thumbs-up', label: '👍' },
          { key: 'loves', icon: 'heart', label: '❤️' },
          { key: 'funnys', icon: 'happy', label: '😂' },
          { key: 'cautions', icon: 'warning', label: '⚠️' },
          { key: 'bests', icon: 'trophy', label: '🏆' },
        ].map(reaction => (
          <TouchableOpacity 
            key={reaction.key}
            style={styles.reactionButton}
            onPress={() => handleReaction(result.id, reaction.key.slice(0, -1))}
          >
            <Text style={styles.reactionEmoji}>{reaction.label}</Text>
            <Text style={styles.reactionCount}>
              {(result as any)[reaction.key] || 0}
            </Text>
          </TouchableOpacity>
        ))}
      </View>
    </TouchableOpacity>
  );

  const getTypeBadgeStyle = (type: string) => {
    const typeStyles: Record<string, any> = {
      'PhD': { backgroundColor: '#9D00FF' },
      'Academic': { backgroundColor: '#4169E1' },
      'News': { backgroundColor: '#FF6B6B' },
      'Blog': { backgroundColor: '#4ECDC4' },
      'Forum': { backgroundColor: '#FFE66D' },
      'Wiki': { backgroundColor: '#A8E6CF' },
      'Government': { backgroundColor: '#6C5CE7' },
    };
    return typeStyles[type] || { backgroundColor: colors.gray };
  };

  // Render interactive world map
  const renderWorldMap = () => {
    // Group results by region
    const regions = {
      'Americas': { emoji: '🌎', count: 0, results: [] as SearchResult[] },
      'Europe': { emoji: '🌍', count: 0, results: [] as SearchResult[] },
      'Asia': { emoji: '🌏', count: 0, results: [] as SearchResult[] },
      'Oceania': { emoji: '🏝️', count: 0, results: [] as SearchResult[] },
    };

    results.forEach((result, index) => {
      const loc = result.location || generateLocation(index);
      const city = loc.city || '';
      
      // Simple region detection
      if (['New York', 'Toronto', 'São Paulo', 'Los Angeles', 'San Francisco'].some(c => city.includes(c))) {
        regions.Americas.count++;
        regions.Americas.results.push(result);
      } else if (['London', 'Paris', 'Berlin', 'Moscow'].some(c => city.includes(c))) {
        regions.Europe.count++;
        regions.Europe.results.push(result);
      } else if (['Tokyo', 'Singapore', 'Mumbai', 'Dubai'].some(c => city.includes(c))) {
        regions.Asia.count++;
        regions.Asia.results.push(result);
      } else {
        regions.Oceania.count++;
        regions.Oceania.results.push(result);
      }
    });

    return (
      <ScrollView style={styles.mapScrollView} contentContainerStyle={styles.mapScrollContent}>
        {/* Map Header */}
        <View style={styles.mapHeader}>
          <Text style={styles.mapTitle}>🗺️ World Results Map</Text>
          <Text style={styles.mapSubtitle}>
            {results.length} results from {selectedCategoryIds.size} categories
          </Text>
          <Text style={styles.mapCombineMode}>
            Mode: {combineMode === 'or' ? '✅ OR (Any match)' : '🔗 AND (All match)'}
          </Text>
        </View>

        {/* Interactive Region Grid */}
        <View style={styles.regionGrid}>
          {Object.entries(regions).map(([name, data]) => (
            <TouchableOpacity 
              key={name}
              style={[styles.regionCard, data.count > 0 && styles.regionCardActive]}
              onPress={() => {
                if (data.results.length > 0) {
                  Alert.alert(
                    `${data.emoji} ${name}`,
                    `${data.count} results found!\n\nTop result: "${data.results[0]?.title?.slice(0, 50)}..."`,
                    [
                      { text: 'Close', style: 'cancel' },
                      { 
                        text: 'View All', 
                        onPress: () => setViewMode('list')
                      },
                    ]
                  );
                }
              }}
            >
              <Text style={styles.regionEmoji}>{data.emoji}</Text>
              <Text style={styles.regionName}>{name}</Text>
              <View style={[styles.regionCountBadge, data.count > 0 && styles.regionCountBadgeActive]}>
                <Text style={styles.regionCount}>{data.count}</Text>
              </View>
            </TouchableOpacity>
          ))}
        </View>

        {/* Location Pins */}
        <View style={styles.locationsSection}>
          <Text style={styles.locationsSectionTitle}>📍 Location Breakdown</Text>
          <View style={styles.locationPins}>
            {WORLD_LOCATIONS.map((loc, index) => {
              const resultCount = results.filter((r, i) => {
                const resLoc = r.location || generateLocation(i);
                return resLoc.city === loc.city;
              }).length;
              
              return (
                <TouchableOpacity 
                  key={loc.city}
                  style={[styles.locationPin, resultCount > 0 && styles.locationPinActive]}
                  onPress={() => {
                    const locResults = results.filter((r, i) => {
                      const resLoc = r.location || generateLocation(i);
                      return resLoc.city === loc.city;
                    });
                    if (locResults.length > 0) {
                      Alert.alert(
                        `${loc.emoji} ${loc.city}`,
                        `${resultCount} results from ${loc.country}`,
                        [{ text: 'OK' }]
                      );
                    }
                  }}
                >
                  <Text style={styles.pinEmoji}>{loc.emoji}</Text>
                  <Text style={styles.pinCity}>{loc.city}</Text>
                  <Text style={styles.pinCount}>{resultCount}</Text>
                </TouchableOpacity>
              );
            })}
          </View>
        </View>

        {/* Recent Results Preview */}
        {results.length > 0 && (
          <View style={styles.recentResults}>
            <Text style={styles.recentResultsTitle}>📋 Recent Results</Text>
            {results.slice(0, 3).map(renderResultCard)}
            {results.length > 3 && (
              <TouchableOpacity 
                style={styles.viewAllButton}
                onPress={() => setViewMode('list')}
              >
                <Text style={styles.viewAllText}>
                  View All {results.length} Results →
                </Text>
              </TouchableOpacity>
            )}
          </View>
        )}
      </ScrollView>
    );
  };

  return (
    <SafeAreaView style={styles.container} edges={['bottom']}>
      {/* Header with Editable Title */}
      <View style={styles.header}>
        <TouchableOpacity 
          style={styles.titleContainer}
          onPress={() => {
            setTempPageName(pageName);
            setIsEditingName(true);
          }}
        >
          <Text style={styles.headerTitle}>🔍 {pageName}</Text>
          <Ionicons name="pencil" size={16} color={colors.textMuted} />
        </TouchableOpacity>
        <Text style={styles.headerSubtitle}>
          "The search that finds what Google can't!" 🎯
        </Text>
      </View>

      {/* Category Selection with Checkboxes */}
      <View style={styles.categorySection}>
        <View style={styles.categorySectionHeader}>
          <Text style={styles.categorySectionTitle}>
            📁 Categories ({selectedCategoryIds.size}/{categories.length})
          </Text>
          <View style={styles.categoryButtons}>
            <TouchableOpacity style={styles.selectAllBtn} onPress={selectAllCategories}>
              <Text style={styles.selectAllText}>All</Text>
            </TouchableOpacity>
            <TouchableOpacity style={styles.clearBtn} onPress={clearAllSelections}>
              <Text style={styles.clearText}>Clear</Text>
            </TouchableOpacity>
          </View>
        </View>

        {/* Category Checkboxes */}
        <ScrollView horizontal showsHorizontalScrollIndicator={false} style={styles.categoryScroll}>
          {categories.map((category) => {
            const isSelected = selectedCategoryIds.has(category.id);
            return (
              <TouchableOpacity
                key={category.id}
                style={[styles.categoryChip, isSelected && styles.categoryChipSelected]}
                onPress={() => toggleCategorySelection(category.id)}
              >
                <Ionicons 
                  name={isSelected ? 'checkbox' : 'square-outline'} 
                  size={18} 
                  color={isSelected ? colors.white : colors.primary} 
                />
                <Text style={[styles.categoryChipText, isSelected && styles.categoryChipTextSelected]}>
                  {category.name}
                </Text>
              </TouchableOpacity>
            );
          })}
        </ScrollView>

        {/* AND/OR Radio Buttons */}
        {selectedCategoryIds.size > 1 && (
          <View style={styles.combineModeSection}>
            <Text style={styles.combineModeLabel}>Combine with:</Text>
            <View style={styles.radioGroup}>
              <TouchableOpacity
                style={[styles.radioBtn, combineMode === 'or' && styles.radioBtnActive]}
                onPress={() => setCombineMode('or')}
              >
                <View style={[styles.radioCircle, combineMode === 'or' && styles.radioCircleActive]} />
                <Text style={[styles.radioLabel, combineMode === 'or' && styles.radioLabelActive]}>
                  OR
                </Text>
              </TouchableOpacity>
              <TouchableOpacity
                style={[styles.radioBtn, combineMode === 'and' && styles.radioBtnActive]}
                onPress={() => setCombineMode('and')}
              >
                <View style={[styles.radioCircle, combineMode === 'and' && styles.radioCircleActive]} />
                <Text style={[styles.radioLabel, combineMode === 'and' && styles.radioLabelActive]}>
                  AND
                </Text>
              </TouchableOpacity>
            </View>
          </View>
        )}
      </View>

      {/* View Toggle */}
      <View style={styles.viewControls}>
        <View style={styles.viewToggle}>
          <TouchableOpacity
            style={[styles.toggleBtn, viewMode === 'map' && styles.toggleBtnActive]}
            onPress={() => setViewMode('map')}
          >
            <Ionicons name="map" size={18} color={viewMode === 'map' ? colors.white : colors.primary} />
            <Text style={[styles.toggleText, viewMode === 'map' && styles.toggleTextActive]}>Map</Text>
          </TouchableOpacity>
          <TouchableOpacity
            style={[styles.toggleBtn, viewMode === 'list' && styles.toggleBtnActive]}
            onPress={() => setViewMode('list')}
          >
            <Ionicons name="list" size={18} color={viewMode === 'list' ? colors.white : colors.primary} />
            <Text style={[styles.toggleText, viewMode === 'list' && styles.toggleTextActive]}>List</Text>
          </TouchableOpacity>
        </View>
        <Text style={styles.resultCount}>
          {loadingResults ? 'Loading...' : `${results.length} results`}
        </Text>
      </View>

      {/* Main Content */}
      {loadingResults ? (
        <View style={styles.loadingContainer}>
          <ActivityIndicator size="large" color={colors.primary} />
          <Text style={styles.loadingText}>Finding amazing results... 🔍</Text>
        </View>
      ) : viewMode === 'map' ? (
        renderWorldMap()
      ) : (
        <ScrollView style={styles.listScrollView} contentContainerStyle={styles.listContent}>
          {results.length === 0 ? (
            <View style={styles.emptyContainer}>
              <Ionicons name="telescope" size={60} color={colors.gray} />
              <Text style={styles.emptyText}>No results yet!</Text>
              <Text style={styles.emptySubtext}>
                Select categories above to see their search results.{'\n'}
                Go to Search tab to collate new results!
              </Text>
            </View>
          ) : (
            <>
              {results.map(renderResultCard)}
              <View style={styles.listFooter}>
                <Text style={styles.listFooterText}>
                  📚 "Letters to Evelyn" - The book that inspired InfoPilot! 📚
                </Text>
              </View>
            </>
          )}
        </ScrollView>
      )}

      {/* Edit Page Name Modal */}
      <Modal
        visible={isEditingName}
        animationType="fade"
        transparent={true}
        onRequestClose={() => setIsEditingName(false)}
      >
        <View style={styles.modalOverlay}>
          <View style={styles.modalContent}>
            <Text style={styles.modalTitle}>✏️ Rename Page</Text>
            <TextInput
              style={styles.modalInput}
              value={tempPageName}
              onChangeText={setTempPageName}
              placeholder="Enter new page name"
              placeholderTextColor={colors.gray}
              autoFocus
            />
            <View style={styles.modalButtons}>
              <TouchableOpacity 
                style={styles.modalCancelBtn}
                onPress={() => setIsEditingName(false)}
              >
                <Text style={styles.modalCancelText}>Cancel</Text>
              </TouchableOpacity>
              <TouchableOpacity 
                style={styles.modalSaveBtn}
                onPress={() => savePageName(tempPageName)}
              >
                <Text style={styles.modalSaveText}>Save</Text>
              </TouchableOpacity>
            </View>
          </View>
        </View>
      </Modal>
    </SafeAreaView>
  );
}

const styles = StyleSheet.create({
  container: {
    flex: 1,
    backgroundColor: colors.background,
  },
  header: {
    padding: 16,
    backgroundColor: colors.cardBackground,
    borderBottomWidth: 1,
    borderBottomColor: colors.cardBorder,
  },
  titleContainer: {
    flexDirection: 'row',
    alignItems: 'center',
    justifyContent: 'center',
    gap: 8,
  },
  headerTitle: {
    fontSize: 22,
    fontWeight: 'bold',
    color: colors.text,
    textAlign: 'center',
  },
  headerSubtitle: {
    fontSize: 12,
    color: colors.textMuted,
    textAlign: 'center',
    marginTop: 4,
    fontStyle: 'italic',
  },
  // Category Section
  categorySection: {
    backgroundColor: colors.cardBackground,
    padding: 12,
    borderBottomWidth: 1,
    borderBottomColor: colors.cardBorder,
  },
  categorySectionHeader: {
    flexDirection: 'row',
    justifyContent: 'space-between',
    alignItems: 'center',
    marginBottom: 10,
  },
  categorySectionTitle: {
    fontSize: 14,
    fontWeight: '600',
    color: colors.text,
  },
  categoryButtons: {
    flexDirection: 'row',
    gap: 8,
  },
  selectAllBtn: {
    backgroundColor: colors.primary,
    paddingHorizontal: 10,
    paddingVertical: 4,
    borderRadius: 10,
  },
  selectAllText: {
    color: colors.white,
    fontSize: 12,
    fontWeight: '600',
  },
  clearBtn: {
    backgroundColor: colors.gray,
    paddingHorizontal: 10,
    paddingVertical: 4,
    borderRadius: 10,
  },
  clearText: {
    color: colors.white,
    fontSize: 12,
    fontWeight: '600',
  },
  categoryScroll: {
    marginBottom: 10,
  },
  categoryChip: {
    flexDirection: 'row',
    alignItems: 'center',
    backgroundColor: colors.background,
    paddingHorizontal: 12,
    paddingVertical: 8,
    borderRadius: 20,
    marginRight: 8,
    borderWidth: 1,
    borderColor: colors.primary,
    gap: 6,
  },
  categoryChipSelected: {
    backgroundColor: colors.primary,
  },
  categoryChipText: {
    color: colors.primary,
    fontSize: 13,
    fontWeight: '500',
  },
  categoryChipTextSelected: {
    color: colors.white,
  },
  // Combine Mode
  combineModeSection: {
    flexDirection: 'row',
    alignItems: 'center',
    paddingTop: 10,
    borderTopWidth: 1,
    borderTopColor: colors.cardBorder,
  },
  combineModeLabel: {
    fontSize: 13,
    color: colors.textMuted,
    marginRight: 12,
  },
  radioGroup: {
    flexDirection: 'row',
    gap: 16,
  },
  radioBtn: {
    flexDirection: 'row',
    alignItems: 'center',
    paddingHorizontal: 12,
    paddingVertical: 6,
    borderRadius: 16,
    borderWidth: 2,
    borderColor: colors.cardBorder,
    gap: 6,
  },
  radioBtnActive: {
    borderColor: colors.primary,
    backgroundColor: colors.primary + '20',
  },
  radioCircle: {
    width: 14,
    height: 14,
    borderRadius: 7,
    borderWidth: 2,
    borderColor: colors.gray,
  },
  radioCircleActive: {
    borderColor: colors.primary,
    backgroundColor: colors.primary,
  },
  radioLabel: {
    fontSize: 13,
    color: colors.textMuted,
    fontWeight: '600',
  },
  radioLabelActive: {
    color: colors.primary,
  },
  // View Controls
  viewControls: {
    flexDirection: 'row',
    justifyContent: 'space-between',
    alignItems: 'center',
    paddingHorizontal: 12,
    paddingVertical: 8,
  },
  viewToggle: {
    flexDirection: 'row',
    borderRadius: 20,
    overflow: 'hidden',
    borderWidth: 1,
    borderColor: colors.primary,
  },
  toggleBtn: {
    flexDirection: 'row',
    alignItems: 'center',
    paddingHorizontal: 14,
    paddingVertical: 6,
    gap: 4,
  },
  toggleBtnActive: {
    backgroundColor: colors.primary,
  },
  toggleText: {
    color: colors.primary,
    fontSize: 12,
    fontWeight: '600',
  },
  toggleTextActive: {
    color: colors.white,
  },
  resultCount: {
    fontSize: 13,
    color: colors.textMuted,
  },
  // Loading
  loadingContainer: {
    flex: 1,
    justifyContent: 'center',
    alignItems: 'center',
  },
  loadingText: {
    color: colors.text,
    fontSize: 16,
    marginTop: 12,
  },
  // Map View
  mapScrollView: {
    flex: 1,
  },
  mapScrollContent: {
    padding: 12,
    paddingBottom: 40,
  },
  mapHeader: {
    backgroundColor: colors.cardBackground,
    padding: 16,
    borderRadius: 16,
    marginBottom: 16,
    alignItems: 'center',
  },
  mapTitle: {
    fontSize: 20,
    fontWeight: 'bold',
    color: colors.text,
  },
  mapSubtitle: {
    fontSize: 14,
    color: colors.primary,
    marginTop: 4,
  },
  mapCombineMode: {
    fontSize: 12,
    color: colors.textMuted,
    marginTop: 8,
    fontStyle: 'italic',
  },
  regionGrid: {
    flexDirection: 'row',
    flexWrap: 'wrap',
    justifyContent: 'space-between',
    marginBottom: 16,
  },
  regionCard: {
    width: (width - 40) / 2,
    backgroundColor: colors.cardBackground,
    borderRadius: 16,
    padding: 16,
    alignItems: 'center',
    marginBottom: 12,
    borderWidth: 2,
    borderColor: colors.cardBorder,
  },
  regionCardActive: {
    borderColor: colors.primary,
  },
  regionEmoji: {
    fontSize: 36,
    marginBottom: 8,
  },
  regionName: {
    fontSize: 14,
    fontWeight: '600',
    color: colors.text,
    marginBottom: 4,
  },
  regionCountBadge: {
    backgroundColor: colors.gray,
    paddingHorizontal: 12,
    paddingVertical: 4,
    borderRadius: 12,
  },
  regionCountBadgeActive: {
    backgroundColor: colors.primary,
  },
  regionCount: {
    fontSize: 14,
    fontWeight: 'bold',
    color: colors.white,
  },
  locationsSection: {
    backgroundColor: colors.cardBackground,
    borderRadius: 16,
    padding: 16,
    marginBottom: 16,
  },
  locationsSectionTitle: {
    fontSize: 16,
    fontWeight: 'bold',
    color: colors.text,
    marginBottom: 12,
  },
  locationPins: {
    flexDirection: 'row',
    flexWrap: 'wrap',
    gap: 8,
  },
  locationPin: {
    alignItems: 'center',
    backgroundColor: colors.background,
    paddingHorizontal: 10,
    paddingVertical: 8,
    borderRadius: 12,
    minWidth: 70,
    borderWidth: 1,
    borderColor: colors.cardBorder,
  },
  locationPinActive: {
    borderColor: colors.primary,
    backgroundColor: colors.primary + '10',
  },
  pinEmoji: {
    fontSize: 20,
  },
  pinCity: {
    fontSize: 10,
    color: colors.textMuted,
    marginTop: 2,
  },
  pinCount: {
    fontSize: 12,
    fontWeight: 'bold',
    color: colors.primary,
  },
  recentResults: {
    backgroundColor: colors.cardBackground,
    borderRadius: 16,
    padding: 16,
  },
  recentResultsTitle: {
    fontSize: 16,
    fontWeight: 'bold',
    color: colors.text,
    marginBottom: 12,
  },
  viewAllButton: {
    backgroundColor: colors.primary,
    padding: 12,
    borderRadius: 12,
    alignItems: 'center',
    marginTop: 8,
  },
  viewAllText: {
    color: colors.white,
    fontSize: 14,
    fontWeight: '600',
  },
  // List View
  listScrollView: {
    flex: 1,
  },
  listContent: {
    padding: 12,
    paddingBottom: 40,
  },
  resultCard: {
    backgroundColor: colors.cardBackground,
    borderRadius: 12,
    padding: 14,
    marginBottom: 12,
    borderWidth: 1,
    borderColor: colors.cardBorder,
  },
  resultHeader: {
    flexDirection: 'row',
    alignItems: 'center',
    marginBottom: 8,
    gap: 8,
    flexWrap: 'wrap',
  },
  typeBadge: {
    paddingHorizontal: 8,
    paddingVertical: 3,
    borderRadius: 8,
  },
  typeBadgeText: {
    color: colors.white,
    fontSize: 10,
    fontWeight: 'bold',
  },
  yearBadge: {
    flexDirection: 'row',
    alignItems: 'center',
    gap: 4,
  },
  yearText: {
    color: colors.accent,
    fontSize: 12,
  },
  locationBadge: {
    flexDirection: 'row',
    alignItems: 'center',
    gap: 4,
  },
  locationText: {
    color: colors.primary,
    fontSize: 12,
  },
  resultTitle: {
    color: colors.text,
    fontSize: 15,
    fontWeight: 'bold',
    marginBottom: 6,
  },
  resultSnippet: {
    color: colors.textLight,
    fontSize: 13,
    marginBottom: 6,
    lineHeight: 18,
  },
  resultUrl: {
    color: colors.accent,
    fontSize: 11,
    marginBottom: 8,
  },
  reactionsRow: {
    flexDirection: 'row',
    borderTopWidth: 1,
    borderTopColor: colors.cardBorder,
    paddingTop: 8,
    gap: 16,
  },
  reactionButton: {
    flexDirection: 'row',
    alignItems: 'center',
    gap: 4,
  },
  reactionEmoji: {
    fontSize: 16,
  },
  reactionCount: {
    color: colors.textMuted,
    fontSize: 12,
  },
  emptyContainer: {
    alignItems: 'center',
    padding: 40,
  },
  emptyText: {
    color: colors.text,
    fontSize: 18,
    fontWeight: 'bold',
    marginTop: 16,
  },
  emptySubtext: {
    color: colors.textMuted,
    fontSize: 14,
    marginTop: 8,
    textAlign: 'center',
    lineHeight: 20,
  },
  listFooter: {
    backgroundColor: colors.secondary,
    padding: 16,
    borderRadius: 12,
    marginTop: 8,
    alignItems: 'center',
  },
  listFooterText: {
    color: colors.marketplaceGold,
    fontSize: 14,
    fontWeight: 'bold',
  },
  // Modal
  modalOverlay: {
    flex: 1,
    backgroundColor: 'rgba(0,0,0,0.7)',
    justifyContent: 'center',
    alignItems: 'center',
    padding: 20,
  },
  modalContent: {
    backgroundColor: colors.cardBackground,
    borderRadius: 16,
    padding: 24,
    width: '100%',
    maxWidth: 320,
  },
  modalTitle: {
    fontSize: 20,
    fontWeight: 'bold',
    color: colors.text,
    textAlign: 'center',
    marginBottom: 16,
  },
  modalInput: {
    backgroundColor: colors.background,
    borderRadius: 12,
    padding: 14,
    fontSize: 16,
    color: colors.text,
    borderWidth: 1,
    borderColor: colors.cardBorder,
    marginBottom: 16,
  },
  modalButtons: {
    flexDirection: 'row',
    gap: 12,
  },
  modalCancelBtn: {
    flex: 1,
    padding: 12,
    borderRadius: 12,
    backgroundColor: colors.gray,
    alignItems: 'center',
  },
  modalCancelText: {
    color: colors.white,
    fontSize: 14,
    fontWeight: '600',
  },
  modalSaveBtn: {
    flex: 1,
    padding: 12,
    borderRadius: 12,
    backgroundColor: colors.primary,
    alignItems: 'center',
  },
  modalSaveText: {
    color: colors.white,
    fontSize: 14,
    fontWeight: '600',
  },
});
