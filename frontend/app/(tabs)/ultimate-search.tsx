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
  FlatList,
  Linking,
} from 'react-native';
import { SafeAreaView } from 'react-native-safe-area-context';
import { Ionicons } from '@expo/vector-icons';
import { colors } from '../../src/utils/colors';
import { api } from '../../src/services/api';

const { width } = Dimensions.get('window');

interface SearchResult {
  id: string;
  title: string;
  url: string;
  snippet: string;
  source: string;
  category_ids: string[];
  reactions: {
    like: number;
    love: number;
    funny: number;
    sad: number;
    caution: number;
    spam: number;
    best: number;
  };
  classification?: string;
  year?: number;
  country?: string;
  location?: {
    latitude: number;
    longitude: number;
    city?: string;
  };
}

interface Category {
  id: string;
  name: string;
  protocol: string;
  is_public: boolean;
  selected?: boolean;
  expanded?: boolean;
  children?: Category[];
}

interface FilterState {
  years: { from: number; to: number };
  domains: string[];
  countries: string[];
  contentTypes: string[];
}

const CONTENT_TYPES = ['PhD', 'Blog', 'News', 'Forum', 'Academic', 'Wiki', 'Government'];
const POPULAR_COUNTRIES = ['USA', 'UK', 'Canada', 'Australia', 'Germany', 'France', 'Japan'];

export default function UltimateSearchScreen() {
  const [searchQuery, setSearchQuery] = useState('');
  const [results, setResults] = useState<SearchResult[]>([]);
  const [categories, setCategories] = useState<Category[]>([]);
  const [loading, setLoading] = useState(false);
  const [viewMode, setViewMode] = useState<'list' | 'map'>('list');
  const [showFilters, setShowFilters] = useState(false);
  const [selectedCategories, setSelectedCategories] = useState<Set<string>>(new Set());
  const [expandedCategories, setExpandedCategories] = useState<Set<string>>(new Set());
  const [filters, setFilters] = useState<FilterState>({
    years: { from: 1900, to: new Date().getFullYear() },
    domains: [],
    countries: [],
    contentTypes: [],
  });

  useEffect(() => {
    loadCategories();
  }, []);

  const loadCategories = async () => {
    try {
      const response = await api.get('/categories');
      const cats = response.categories || [];
      // Initialize with all selected
      setCategories(cats);
      setSelectedCategories(new Set(cats.map((c: Category) => c.id)));
    } catch (error) {
      console.error('Load categories error:', error);
    }
  };

  const handleSearch = async () => {
    if (!searchQuery.trim()) {
      Alert.alert('Oops! 🤔', 'Please enter something to search for!');
      return;
    }

    setLoading(true);
    try {
      // Get search results from Google
      const searchResponse = await api.googleSearch(searchQuery, 100);
      
      // Collate results with selected categories
      const selectedCatIds = Array.from(selectedCategories);
      const collateResponse = await api.collateResults(
        searchQuery,
        searchResponse.results || [],
        selectedCatIds.length > 0 ? selectedCatIds : undefined
      );

      // Add mock locations for map view (in real app, these would be geolocated)
      const resultsWithLocations = (collateResponse.results || []).map((r: SearchResult, index: number) => ({
        ...r,
        location: r.location || generateMockLocation(index),
        classification: classifyContent(r.url, r.snippet),
        year: extractYear(r.snippet),
      }));

      setResults(resultsWithLocations);
      
      if (resultsWithLocations.length === 0) {
        Alert.alert(
          '🔍 No Results Found',
          'Try broadening your search or adjusting your protocol filters. Remember: (word1 or word2) & (word3) gives the best results!'
        );
      }
    } catch (error) {
      console.error('Search error:', error);
      Alert.alert('Search Failed', 'Something went wrong. Our hamsters are investigating! 🐹');
    } finally {
      setLoading(false);
    }
  };

  const generateMockLocation = (index: number) => {
    const locations = [
      { latitude: 40.7128, longitude: -74.0060, city: 'New York' },
      { latitude: 51.5074, longitude: -0.1278, city: 'London' },
      { latitude: 48.8566, longitude: 2.3522, city: 'Paris' },
      { latitude: 35.6762, longitude: 139.6503, city: 'Tokyo' },
      { latitude: -33.8688, longitude: 151.2093, city: 'Sydney' },
    ];
    return locations[index % locations.length];
  };

  const classifyContent = (url: string, snippet: string): string => {
    const urlLower = url.toLowerCase();
    const snippetLower = snippet.toLowerCase();
    
    if (urlLower.includes('.edu') || snippetLower.includes('phd') || snippetLower.includes('dissertation')) return 'PhD';
    if (urlLower.includes('blog') || urlLower.includes('medium.com')) return 'Blog';
    if (urlLower.includes('news') || urlLower.includes('cnn') || urlLower.includes('bbc')) return 'News';
    if (urlLower.includes('forum') || urlLower.includes('reddit') || urlLower.includes('quora')) return 'Forum';
    if (urlLower.includes('wikipedia')) return 'Wiki';
    if (urlLower.includes('.gov')) return 'Government';
    if (urlLower.includes('journal') || urlLower.includes('academic') || urlLower.includes('research')) return 'Academic';
    return 'Web';
  };

  const extractYear = (text: string): number | undefined => {
    const match = text.match(/\b(19|20)\d{2}\b/);
    return match ? parseInt(match[0]) : undefined;
  };

  const toggleCategory = (categoryId: string) => {
    const newSelected = new Set(selectedCategories);
    if (newSelected.has(categoryId)) {
      newSelected.delete(categoryId);
    } else {
      newSelected.add(categoryId);
    }
    setSelectedCategories(newSelected);
  };

  const toggleExpand = (categoryId: string) => {
    const newExpanded = new Set(expandedCategories);
    if (newExpanded.has(categoryId)) {
      newExpanded.delete(categoryId);
    } else {
      newExpanded.add(categoryId);
    }
    setExpandedCategories(newExpanded);
  };

  const handleReaction = async (resultId: string, reactionType: string) => {
    try {
      await api.post(`/search/results/${resultId}/react`, { reaction_type: reactionType });
      // Update local state
      setResults(prev => prev.map(r => {
        if (r.id === resultId) {
          return {
            ...r,
            reactions: {
              ...r.reactions,
              [reactionType]: (r.reactions?.[reactionType as keyof typeof r.reactions] || 0) + 1
            }
          };
        }
        return r;
      }));
    } catch (error) {
      console.error('Reaction error:', error);
    }
  };

  const filteredResults = results.filter(r => {
    // Filter by year
    if (r.year && (r.year < filters.years.from || r.year > filters.years.to)) return false;
    
    // Filter by content type
    if (filters.contentTypes.length > 0 && !filters.contentTypes.includes(r.classification || '')) return false;
    
    // Filter by country
    if (filters.countries.length > 0 && r.location?.city) {
      // Simple check - in real app would be more sophisticated
      const hasMatch = filters.countries.some(c => 
        r.location?.city?.toLowerCase().includes(c.toLowerCase())
      );
      if (!hasMatch) return false;
    }
    
    return true;
  });

  const renderCategoryItem = (category: Category, level: number = 0) => {
    const isSelected = selectedCategories.has(category.id);
    const isExpanded = expandedCategories.has(category.id);
    const hasChildren = category.children && category.children.length > 0;

    return (
      <View key={category.id} style={{ marginLeft: level * 16 }}>
        <View style={styles.categoryRow}>
          {hasChildren && (
            <TouchableOpacity onPress={() => toggleExpand(category.id)} style={styles.expandButton}>
              <Ionicons 
                name={isExpanded ? "remove-circle" : "add-circle"} 
                size={20} 
                color={colors.primary} 
              />
            </TouchableOpacity>
          )}
          <TouchableOpacity 
            style={[styles.categoryCheckbox, isSelected && styles.categoryCheckboxSelected]}
            onPress={() => toggleCategory(category.id)}
          >
            {isSelected && <Ionicons name="checkmark" size={14} color={colors.white} />}
          </TouchableOpacity>
          <Text style={styles.categoryName} numberOfLines={1}>{category.name}</Text>
        </View>
        {isExpanded && hasChildren && category.children?.map(child => renderCategoryItem(child, level + 1))}
      </View>
    );
  };

  const renderResultCard = ({ item }: { item: SearchResult }) => (
    <TouchableOpacity 
      style={styles.resultCard}
      onPress={() => Linking.openURL(item.url)}
    >
      <View style={styles.resultHeader}>
        {item.classification && (
          <View style={[styles.classificationBadge, getClassificationStyle(item.classification)]}>
            <Text style={styles.classificationText}>{item.classification}</Text>
          </View>
        )}
        {item.year && (
          <View style={styles.yearBadge}>
            <Ionicons name="calendar" size={12} color={colors.accent} />
            <Text style={styles.yearText}>{item.year}</Text>
          </View>
        )}
      </View>
      
      <Text style={styles.resultTitle} numberOfLines={2}>{item.title}</Text>
      <Text style={styles.resultSnippet} numberOfLines={3}>{item.snippet}</Text>
      <Text style={styles.resultUrl} numberOfLines={1}>{item.source || new URL(item.url).hostname}</Text>
      
      {item.location && (
        <View style={styles.locationBadge}>
          <Ionicons name="location" size={12} color={colors.accent} />
          <Text style={styles.locationText}>{item.location.city}</Text>
        </View>
      )}
      
      {/* Reaction Buttons */}
      <View style={styles.reactionsRow}>
        {[
          { key: 'like', icon: 'thumbs-up', color: colors.like },
          { key: 'love', icon: 'heart', color: colors.love },
          { key: 'funny', icon: 'happy', color: colors.funny },
          { key: 'caution', icon: 'warning', color: colors.caution },
          { key: 'best', icon: 'trophy', color: colors.best },
        ].map(reaction => (
          <TouchableOpacity 
            key={reaction.key}
            style={styles.reactionButton}
            onPress={() => handleReaction(item.id, reaction.key)}
          >
            <Ionicons name={reaction.icon as any} size={16} color={reaction.color} />
            <Text style={styles.reactionCount}>
              {item.reactions?.[reaction.key as keyof typeof item.reactions] || 0}
            </Text>
          </TouchableOpacity>
        ))}
      </View>
    </TouchableOpacity>
  );

  const getClassificationStyle = (classification: string) => {
    const styles: Record<string, any> = {
      'PhD': { backgroundColor: '#9D00FF' },
      'Academic': { backgroundColor: '#4169E1' },
      'News': { backgroundColor: '#FF6B6B' },
      'Blog': { backgroundColor: '#4ECDC4' },
      'Forum': { backgroundColor: '#FFE66D' },
      'Wiki': { backgroundColor: '#A8E6CF' },
      'Government': { backgroundColor: '#6C5CE7' },
    };
    return styles[classification] || { backgroundColor: colors.gray };
  };

  // World Map View
  const renderMapView = () => (
    <View style={styles.mapContainer}>
      <View style={styles.mapPlaceholder}>
        <Text style={styles.mapTitle}>🌍 Search Results Map 🌍</Text>
        <Text style={styles.mapSubtitle}>{filteredResults.length} results found worldwide!</Text>
        
        {/* Region breakdown */}
        <View style={styles.regionStats}>
          {['Americas', 'Europe', 'Asia', 'Other'].map((region, index) => {
            const count = Math.floor(filteredResults.length / 4) + (index < filteredResults.length % 4 ? 1 : 0);
            return (
              <View key={region} style={styles.regionStat}>
                <Text style={styles.regionIcon}>
                  {region === 'Americas' ? '🌎' : region === 'Europe' ? '🌍' : region === 'Asia' ? '🌏' : '🗺️'}
                </Text>
                <Text style={styles.regionName}>{region}</Text>
                <Text style={styles.regionCount}>{count} results</Text>
              </View>
            );
          })}
        </View>
        
        <Text style={styles.mapHint}>
          📱 Full interactive map with clustering available in mobile app!
        </Text>
      </View>
      
      {/* Quick result list under map */}
      <FlatList
        data={filteredResults.slice(0, 5)}
        renderItem={renderResultCard}
        keyExtractor={(item) => item.id}
        style={styles.mapResultsList}
      />
    </View>
  );

  return (
    <SafeAreaView style={styles.container} edges={['bottom']}>
      {/* Search Header */}
      <View style={styles.header}>
        <Text style={styles.headerTitle}>🔍 Ultimate Search</Text>
        <Text style={styles.headerSubtitle}>
          "The search engine so good, Google is jealous!" 😎
        </Text>
      </View>

      {/* Search Bar */}
      <View style={styles.searchContainer}>
        <View style={styles.searchBar}>
          <Ionicons name="search" size={20} color={colors.gray} />
          <TextInput
            style={styles.searchInput}
            placeholder="Enter your search query..."
            placeholderTextColor={colors.gray}
            value={searchQuery}
            onChangeText={setSearchQuery}
            onSubmitEditing={handleSearch}
          />
          {searchQuery.length > 0 && (
            <TouchableOpacity onPress={() => setSearchQuery('')}>
              <Ionicons name="close-circle" size={20} color={colors.gray} />
            </TouchableOpacity>
          )}
        </View>
        <TouchableOpacity style={styles.searchButton} onPress={handleSearch}>
          <Ionicons name="rocket" size={20} color={colors.white} />
        </TouchableOpacity>
      </View>

      {/* Controls Bar */}
      <View style={styles.controlsBar}>
        <TouchableOpacity 
          style={[styles.controlButton, showFilters && styles.controlButtonActive]}
          onPress={() => setShowFilters(!showFilters)}
        >
          <Ionicons name="filter" size={18} color={showFilters ? colors.white : colors.primary} />
          <Text style={[styles.controlText, showFilters && styles.controlTextActive]}>Filters</Text>
        </TouchableOpacity>
        
        <View style={styles.viewToggle}>
          <TouchableOpacity
            style={[styles.toggleButton, viewMode === 'list' && styles.toggleActive]}
            onPress={() => setViewMode('list')}
          >
            <Ionicons name="list" size={18} color={viewMode === 'list' ? colors.white : colors.primary} />
          </TouchableOpacity>
          <TouchableOpacity
            style={[styles.toggleButton, viewMode === 'map' && styles.toggleActive]}
            onPress={() => setViewMode('map')}
          >
            <Ionicons name="map" size={18} color={viewMode === 'map' ? colors.white : colors.primary} />
          </TouchableOpacity>
        </View>
        
        <Text style={styles.resultsCount}>{filteredResults.length} results</Text>
      </View>

      {/* Filters Panel */}
      {showFilters && (
        <ScrollView style={styles.filtersPanel} horizontal={false}>
          {/* Category Checkboxes */}
          <Text style={styles.filterSectionTitle}>📁 Categories</Text>
          <View style={styles.categoriesList}>
            {categories.map(cat => renderCategoryItem(cat))}
          </View>
          
          {/* Content Type Filter */}
          <Text style={styles.filterSectionTitle}>📋 Content Type</Text>
          <View style={styles.filterChips}>
            {CONTENT_TYPES.map(type => (
              <TouchableOpacity
                key={type}
                style={[
                  styles.filterChip,
                  filters.contentTypes.includes(type) && styles.filterChipActive
                ]}
                onPress={() => {
                  const newTypes = filters.contentTypes.includes(type)
                    ? filters.contentTypes.filter(t => t !== type)
                    : [...filters.contentTypes, type];
                  setFilters({ ...filters, contentTypes: newTypes });
                }}
              >
                <Text style={[
                  styles.filterChipText,
                  filters.contentTypes.includes(type) && styles.filterChipTextActive
                ]}>{type}</Text>
              </TouchableOpacity>
            ))}
          </View>
          
          {/* Year Range */}
          <Text style={styles.filterSectionTitle}>📅 Year Range</Text>
          <View style={styles.yearRange}>
            <TextInput
              style={styles.yearInput}
              placeholder="From"
              placeholderTextColor={colors.gray}
              keyboardType="numeric"
              value={String(filters.years.from)}
              onChangeText={(v) => setFilters({
                ...filters,
                years: { ...filters.years, from: parseInt(v) || 1900 }
              })}
            />
            <Text style={styles.yearSeparator}>to</Text>
            <TextInput
              style={styles.yearInput}
              placeholder="To"
              placeholderTextColor={colors.gray}
              keyboardType="numeric"
              value={String(filters.years.to)}
              onChangeText={(v) => setFilters({
                ...filters,
                years: { ...filters.years, to: parseInt(v) || new Date().getFullYear() }
              })}
            />
          </View>
        </ScrollView>
      )}

      {/* Results */}
      {loading ? (
        <View style={styles.loadingContainer}>
          <ActivityIndicator size="large" color={colors.primary} />
          <Text style={styles.loadingText}>Searching the universe... 🚀</Text>
          <Text style={styles.loadingSubtext}>This might take a few seconds. Worth the wait!</Text>
        </View>
      ) : viewMode === 'map' ? (
        renderMapView()
      ) : (
        <FlatList
          data={filteredResults}
          renderItem={renderResultCard}
          keyExtractor={(item) => item.id}
          contentContainerStyle={styles.resultsList}
          showsVerticalScrollIndicator={false}
          ListEmptyComponent={
            <View style={styles.emptyContainer}>
              <Ionicons name="telescope" size={60} color={colors.gray} />
              <Text style={styles.emptyText}>No results yet!</Text>
              <Text style={styles.emptySubtext}>
                Enter a search query above and hit that rocket button! 🚀
              </Text>
            </View>
          }
        />
      )}
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
  headerTitle: {
    fontSize: 24,
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
  searchContainer: {
    flexDirection: 'row',
    padding: 12,
    alignItems: 'center',
  },
  searchBar: {
    flex: 1,
    flexDirection: 'row',
    alignItems: 'center',
    backgroundColor: colors.cardBackground,
    borderRadius: 12,
    paddingHorizontal: 12,
    paddingVertical: 10,
    borderWidth: 1,
    borderColor: colors.cardBorder,
  },
  searchInput: {
    flex: 1,
    color: colors.text,
    fontSize: 16,
    marginLeft: 8,
  },
  searchButton: {
    backgroundColor: colors.primary,
    padding: 12,
    borderRadius: 12,
    marginLeft: 8,
  },
  controlsBar: {
    flexDirection: 'row',
    alignItems: 'center',
    paddingHorizontal: 12,
    paddingBottom: 8,
  },
  controlButton: {
    flexDirection: 'row',
    alignItems: 'center',
    paddingHorizontal: 12,
    paddingVertical: 6,
    borderRadius: 16,
    backgroundColor: colors.cardBackground,
    borderWidth: 1,
    borderColor: colors.cardBorder,
    marginRight: 8,
  },
  controlButtonActive: {
    backgroundColor: colors.primary,
    borderColor: colors.primary,
  },
  controlText: {
    color: colors.primary,
    marginLeft: 4,
    fontSize: 12,
    fontWeight: '600',
  },
  controlTextActive: {
    color: colors.white,
  },
  viewToggle: {
    flexDirection: 'row',
    borderRadius: 12,
    overflow: 'hidden',
    borderWidth: 1,
    borderColor: colors.primary,
  },
  toggleButton: {
    padding: 8,
    backgroundColor: 'transparent',
  },
  toggleActive: {
    backgroundColor: colors.primary,
  },
  resultsCount: {
    color: colors.textMuted,
    fontSize: 12,
    marginLeft: 'auto',
  },
  filtersPanel: {
    maxHeight: 250,
    backgroundColor: colors.cardBackground,
    padding: 12,
    borderBottomWidth: 1,
    borderBottomColor: colors.cardBorder,
  },
  filterSectionTitle: {
    color: colors.text,
    fontSize: 14,
    fontWeight: 'bold',
    marginBottom: 8,
    marginTop: 12,
  },
  categoriesList: {
    marginBottom: 8,
  },
  categoryRow: {
    flexDirection: 'row',
    alignItems: 'center',
    paddingVertical: 6,
  },
  expandButton: {
    marginRight: 8,
  },
  categoryCheckbox: {
    width: 20,
    height: 20,
    borderRadius: 4,
    borderWidth: 2,
    borderColor: colors.primary,
    marginRight: 8,
    alignItems: 'center',
    justifyContent: 'center',
  },
  categoryCheckboxSelected: {
    backgroundColor: colors.primary,
  },
  categoryName: {
    color: colors.text,
    fontSize: 14,
    flex: 1,
  },
  filterChips: {
    flexDirection: 'row',
    flexWrap: 'wrap',
    gap: 8,
  },
  filterChip: {
    paddingHorizontal: 12,
    paddingVertical: 6,
    borderRadius: 16,
    backgroundColor: colors.background,
    borderWidth: 1,
    borderColor: colors.cardBorder,
  },
  filterChipActive: {
    backgroundColor: colors.primary,
    borderColor: colors.primary,
  },
  filterChipText: {
    color: colors.textMuted,
    fontSize: 12,
  },
  filterChipTextActive: {
    color: colors.white,
  },
  yearRange: {
    flexDirection: 'row',
    alignItems: 'center',
  },
  yearInput: {
    backgroundColor: colors.background,
    borderRadius: 8,
    padding: 8,
    width: 80,
    color: colors.text,
    textAlign: 'center',
    borderWidth: 1,
    borderColor: colors.cardBorder,
  },
  yearSeparator: {
    color: colors.textMuted,
    marginHorizontal: 12,
  },
  loadingContainer: {
    flex: 1,
    justifyContent: 'center',
    alignItems: 'center',
  },
  loadingText: {
    color: colors.text,
    fontSize: 18,
    fontWeight: 'bold',
    marginTop: 16,
  },
  loadingSubtext: {
    color: colors.textMuted,
    fontSize: 14,
    marginTop: 8,
  },
  resultsList: {
    padding: 12,
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
  },
  classificationBadge: {
    paddingHorizontal: 8,
    paddingVertical: 2,
    borderRadius: 8,
  },
  classificationText: {
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
  resultTitle: {
    color: colors.text,
    fontSize: 16,
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
  locationBadge: {
    flexDirection: 'row',
    alignItems: 'center',
    gap: 4,
    marginBottom: 8,
  },
  locationText: {
    color: colors.textMuted,
    fontSize: 12,
  },
  reactionsRow: {
    flexDirection: 'row',
    borderTopWidth: 1,
    borderTopColor: colors.cardBorder,
    paddingTop: 8,
    gap: 12,
  },
  reactionButton: {
    flexDirection: 'row',
    alignItems: 'center',
    gap: 4,
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
  },
  mapContainer: {
    flex: 1,
  },
  mapPlaceholder: {
    backgroundColor: colors.cardBackground,
    margin: 12,
    borderRadius: 16,
    padding: 20,
    alignItems: 'center',
  },
  mapTitle: {
    fontSize: 20,
    fontWeight: 'bold',
    color: colors.text,
    marginBottom: 8,
  },
  mapSubtitle: {
    fontSize: 14,
    color: colors.primary,
    marginBottom: 16,
  },
  regionStats: {
    flexDirection: 'row',
    flexWrap: 'wrap',
    justifyContent: 'center',
    gap: 16,
    marginBottom: 16,
  },
  regionStat: {
    alignItems: 'center',
    minWidth: 70,
  },
  regionIcon: {
    fontSize: 28,
    marginBottom: 4,
  },
  regionName: {
    color: colors.text,
    fontSize: 12,
    fontWeight: '600',
  },
  regionCount: {
    color: colors.primary,
    fontSize: 11,
  },
  mapHint: {
    color: colors.textMuted,
    fontSize: 12,
    fontStyle: 'italic',
  },
  mapResultsList: {
    maxHeight: 300,
    padding: 12,
  },
});
