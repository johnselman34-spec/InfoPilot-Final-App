import React, { useState, useEffect, useCallback } from 'react';
import {
  View,
  Text,
  StyleSheet,
  ScrollView,
  TouchableOpacity,
  TextInput,
  FlatList,
  Alert,
  ActivityIndicator,
  RefreshControl,
  Linking,
} from 'react-native';
import { SafeAreaView } from 'react-native-safe-area-context';
import { Ionicons } from '@expo/vector-icons';
import { useAuth } from '../../src/context/AuthContext';
import { api } from '../../src/services/api';

interface Category {
  id: string;
  name: string;
  protocol: string;
  is_public: boolean;
  level: number;
  parent_id?: string;
}

interface SearchResult {
  id: string;
  url: string;
  title: string;
  snippet: string;
  article_type: string;
  root_domain: string;
  categories: string[];
  reactions: Record<string, string[]>;
  collated_at: string;
}

type AggregationType = 'and_or' | 'and' | 'or';

export default function UltimateSearchScreen() {
  const { user } = useAuth();
  const [categories, setCategories] = useState<Category[]>([]);
  const [selectedCategories, setSelectedCategories] = useState<string[]>([]);
  const [aggregation, setAggregation] = useState<AggregationType>('and_or');
  const [searchQuery, setSearchQuery] = useState('');
  const [articleType, setArticleType] = useState<string | null>(null);
  const [results, setResults] = useState<SearchResult[]>([]);
  const [loading, setLoading] = useState(false);
  const [refreshing, setRefreshing] = useState(false);
  const [page, setPage] = useState(1);
  const [totalPages, setTotalPages] = useState(1);
  const [stats, setStats] = useState<any>(null);
  const [showFilters, setShowFilters] = useState(false);

  const articleTypes = [
    'Informative Ph.D.',
    'Informative',
    'News Article',
    'Blog',
    'Forum',
    'Personal Report (collected)',
    'Personal Report (organic)',
  ];

  useEffect(() => {
    loadCategories();
    loadStats();
  }, []);

  useEffect(() => {
    if (categories.length > 0) {
      loadResults();
    }
  }, [selectedCategories, aggregation, articleType, page]);

  const loadCategories = async () => {
    try {
      const data = await api.get('/categories');
      setCategories(data);
    } catch (error) {
      console.error('Error loading categories:', error);
    }
  };

  const loadStats = async () => {
    try {
      const data = await api.get('/ultimate-search/stats');
      setStats(data);
    } catch (error) {
      console.error('Error loading stats:', error);
    }
  };

  const loadResults = async () => {
    setLoading(true);
    try {
      const params: any = {
        page,
        aggregation,
      };
      
      if (selectedCategories.length > 0) {
        params.category_ids = selectedCategories.join(',');
      }
      if (articleType) {
        params.article_type = articleType;
      }
      if (searchQuery) {
        params.search_query = searchQuery;
      }

      const data = await api.get('/ultimate-search', params);
      setResults(data.results);
      setTotalPages(data.total_pages);
    } catch (error: any) {
      if (error.response?.status === 403) {
        Alert.alert('Subscription Required', error.response.data.detail);
      }
    } finally {
      setLoading(false);
    }
  };

  const onRefresh = useCallback(async () => {
    setRefreshing(true);
    await loadCategories();
    await loadResults();
    await loadStats();
    setRefreshing(false);
  }, [selectedCategories, aggregation, articleType]);

  const toggleCategory = (categoryId: string) => {
    setSelectedCategories(prev =>
      prev.includes(categoryId)
        ? prev.filter(id => id !== categoryId)
        : [...prev, categoryId]
    );
    setPage(1);
  };

  const handleSearch = () => {
    setPage(1);
    loadResults();
  };

  const handleReaction = async (resultId: string, reactionType: string) => {
    try {
      await api.post('/reactions', {
        search_result_id: resultId,
        reaction_type: reactionType,
      });
      loadResults();
    } catch (error) {
      Alert.alert('Error', 'Could not add reaction');
    }
  };

  const openUrl = (url: string) => {
    Linking.openURL(url);
  };

  const renderCategoryItem = ({ item }: { item: Category }) => (
    <TouchableOpacity
      style={[
        styles.categoryChip,
        selectedCategories.includes(item.id) && styles.categoryChipSelected,
        { marginLeft: item.level * 8 },
      ]}
      onPress={() => toggleCategory(item.id)}
    >
      <Text
        style={[
          styles.categoryChipText,
          selectedCategories.includes(item.id) && styles.categoryChipTextSelected,
        ]}
      >
        {item.name}
      </Text>
      {item.is_public && (
        <Ionicons name="globe-outline" size={12} color={selectedCategories.includes(item.id) ? '#fff' : '#4CAF50'} />
      )}
    </TouchableOpacity>
  );

  const renderResultItem = ({ item }: { item: SearchResult }) => (
    <TouchableOpacity style={styles.resultCard} onPress={() => openUrl(item.url)}>
      <View style={styles.resultHeader}>
        <Text style={styles.resultTitle} numberOfLines={2}>
          {item.title}
        </Text>
        <View style={styles.articleTypeBadge}>
          <Text style={styles.articleTypeText}>{item.article_type}</Text>
        </View>
      </View>
      <Text style={styles.resultDomain}>{item.root_domain}</Text>
      <Text style={styles.resultSnippet} numberOfLines={3}>
        {item.snippet}
      </Text>
      <View style={styles.resultCategories}>
        {item.categories.map((cat, idx) => (
          <View key={idx} style={styles.resultCategoryBadge}>
            <Text style={styles.resultCategoryText}>{cat}</Text>
          </View>
        ))}
      </View>
      <View style={styles.reactionBar}>
        {['Like', 'Love', 'Funny', 'Sad', 'Caution', 'Spam', 'Best'].map(reaction => (
          <TouchableOpacity
            key={reaction}
            style={styles.reactionButton}
            onPress={() => handleReaction(item.id, reaction)}
          >
            <Ionicons
              name={getReactionIcon(reaction)}
              size={16}
              color={item.reactions?.[reaction]?.includes(user?.id || '') ? '#2196F3' : '#999'}
            />
            <Text style={styles.reactionCount}>
              {item.reactions?.[reaction]?.length || 0}
            </Text>
          </TouchableOpacity>
        ))}
      </View>
    </TouchableOpacity>
  );

  const getReactionIcon = (reaction: string): any => {
    const icons: Record<string, string> = {
      Like: 'thumbs-up-outline',
      Love: 'heart-outline',
      Funny: 'happy-outline',
      Sad: 'sad-outline',
      Caution: 'warning-outline',
      Spam: 'alert-circle-outline',
      Best: 'star-outline',
    };
    return icons[reaction] || 'ellipse-outline';
  };

  return (
    <SafeAreaView style={styles.container} edges={['top']}>
      {/* Header */}
      <View style={styles.header}>
        <View style={styles.headerLeft}>
          <View style={styles.profileCircle}>
            <Text style={styles.profileInitial}>
              {user?.username?.[0]?.toUpperCase() || 'U'}
            </Text>
          </View>
          <View>
            <Text style={styles.headerTitle}>Ultimate Search</Text>
            <Text style={styles.headerSubtitle}>@{user?.username}</Text>
          </View>
        </View>
        <TouchableOpacity
          style={styles.filterButton}
          onPress={() => setShowFilters(!showFilters)}
        >
          <Ionicons name="options" size={24} color="#2196F3" />
        </TouchableOpacity>
      </View>

      {/* Stats Bar */}
      {stats && (
        <View style={styles.statsBar}>
          <View style={styles.statItem}>
            <Text style={styles.statValue}>{stats.total_results}</Text>
            <Text style={styles.statLabel}>Results</Text>
          </View>
          <View style={styles.statItem}>
            <Text style={styles.statValue}>{categories.length}</Text>
            <Text style={styles.statLabel}>Categories</Text>
          </View>
          <View style={styles.statItem}>
            <Text style={styles.statValue}>{Object.keys(stats.article_type_breakdown || {}).length}</Text>
            <Text style={styles.statLabel}>Types</Text>
          </View>
        </View>
      )}

      {/* Search Bar */}
      <View style={styles.searchContainer}>
        <View style={styles.searchBar}>
          <Ionicons name="search" size={20} color="#999" />
          <TextInput
            style={styles.searchInput}
            placeholder="Search in your results..."
            placeholderTextColor="#999"
            value={searchQuery}
            onChangeText={setSearchQuery}
            onSubmitEditing={handleSearch}
          />
          {searchQuery ? (
            <TouchableOpacity onPress={() => { setSearchQuery(''); handleSearch(); }}>
              <Ionicons name="close-circle" size={20} color="#999" />
            </TouchableOpacity>
          ) : null}
        </View>
      </View>

      {/* Filters Panel */}
      {showFilters && (
        <View style={styles.filtersPanel}>
          {/* Aggregation */}
          <Text style={styles.filterLabel}>Search Aggregation:</Text>
          <View style={styles.aggregationRow}>
            {(['and_or', 'and', 'or'] as AggregationType[]).map(agg => (
              <TouchableOpacity
                key={agg}
                style={[
                  styles.aggregationButton,
                  aggregation === agg && styles.aggregationButtonActive,
                ]}
                onPress={() => { setAggregation(agg); setPage(1); }}
              >
                <Text
                  style={[
                    styles.aggregationText,
                    aggregation === agg && styles.aggregationTextActive,
                  ]}
                >
                  {agg === 'and_or' ? 'And/Or' : agg.toUpperCase()}
                </Text>
              </TouchableOpacity>
            ))}
          </View>
          <Text style={styles.aggregationHelp}>
            {aggregation === 'and_or' && 'Must have ALL selected categories (and possibly more)'}
            {aggregation === 'and' && 'Must have EXACTLY the selected categories'}
            {aggregation === 'or' && 'Must have ANY of the selected categories'}
          </Text>

          {/* Article Type */}
          <Text style={styles.filterLabel}>Article Type:</Text>
          <ScrollView horizontal showsHorizontalScrollIndicator={false}>
            <TouchableOpacity
              style={[
                styles.articleTypeChip,
                !articleType && styles.articleTypeChipSelected,
              ]}
              onPress={() => { setArticleType(null); setPage(1); }}
            >
              <Text style={[styles.articleTypeChipText, !articleType && styles.articleTypeChipTextSelected]}>
                All
              </Text>
            </TouchableOpacity>
            {articleTypes.map(type => (
              <TouchableOpacity
                key={type}
                style={[
                  styles.articleTypeChip,
                  articleType === type && styles.articleTypeChipSelected,
                ]}
                onPress={() => { setArticleType(type); setPage(1); }}
              >
                <Text style={[styles.articleTypeChipText, articleType === type && styles.articleTypeChipTextSelected]}>
                  {type}
                </Text>
              </TouchableOpacity>
            ))}
          </ScrollView>
        </View>
      )}

      {/* Categories */}
      <View style={styles.categoriesSection}>
        <Text style={styles.sectionTitle}>Your Categories</Text>
        {categories.length === 0 ? (
          <Text style={styles.emptyText}>No categories yet. Create one in the Categories tab!</Text>
        ) : (
          <FlatList
            data={categories}
            renderItem={renderCategoryItem}
            keyExtractor={item => item.id}
            horizontal
            showsHorizontalScrollIndicator={false}
            contentContainerStyle={styles.categoriesList}
          />
        )}
      </View>

      {/* Results */}
      <View style={styles.resultsSection}>
        <Text style={styles.sectionTitle}>
          Search Results {results.length > 0 && `(Page ${page}/${totalPages})`}
        </Text>
        
        {loading ? (
          <ActivityIndicator size="large" color="#2196F3" style={styles.loader} />
        ) : results.length === 0 ? (
          <View style={styles.emptyResults}>
            <Ionicons name="document-text-outline" size={48} color="#ccc" />
            <Text style={styles.emptyResultsText}>
              No results yet. Go to InfoJet tab to search and collate!
            </Text>
          </View>
        ) : (
          <FlatList
            data={results}
            renderItem={renderResultItem}
            keyExtractor={item => item.id}
            refreshControl={
              <RefreshControl refreshing={refreshing} onRefresh={onRefresh} />
            }
            contentContainerStyle={styles.resultsList}
            ListFooterComponent={
              totalPages > 1 ? (
                <View style={styles.pagination}>
                  <TouchableOpacity
                    style={[styles.pageButton, page === 1 && styles.pageButtonDisabled]}
                    onPress={() => setPage(p => Math.max(1, p - 1))}
                    disabled={page === 1}
                  >
                    <Ionicons name="chevron-back" size={20} color={page === 1 ? '#ccc' : '#2196F3'} />
                  </TouchableOpacity>
                  <Text style={styles.pageText}>{page} / {totalPages}</Text>
                  <TouchableOpacity
                    style={[styles.pageButton, page === totalPages && styles.pageButtonDisabled]}
                    onPress={() => setPage(p => Math.min(totalPages, p + 1))}
                    disabled={page === totalPages}
                  >
                    <Ionicons name="chevron-forward" size={20} color={page === totalPages ? '#ccc' : '#2196F3'} />
                  </TouchableOpacity>
                </View>
              ) : null
            }
          />
        )}
      </View>
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
    justifyContent: 'space-between',
    alignItems: 'center',
    paddingHorizontal: 16,
    paddingVertical: 12,
    backgroundColor: '#fff',
    borderBottomWidth: 1,
    borderBottomColor: '#E0E0E0',
  },
  headerLeft: {
    flexDirection: 'row',
    alignItems: 'center',
  },
  profileCircle: {
    width: 44,
    height: 44,
    borderRadius: 22,
    backgroundColor: '#2196F3',
    alignItems: 'center',
    justifyContent: 'center',
    marginRight: 12,
  },
  profileInitial: {
    fontSize: 18,
    fontWeight: 'bold',
    color: '#fff',
  },
  headerTitle: {
    fontSize: 18,
    fontWeight: 'bold',
    color: '#333',
  },
  headerSubtitle: {
    fontSize: 12,
    color: '#666',
  },
  filterButton: {
    padding: 8,
  },
  statsBar: {
    flexDirection: 'row',
    backgroundColor: '#E3F2FD',
    paddingVertical: 8,
    paddingHorizontal: 16,
  },
  statItem: {
    flex: 1,
    alignItems: 'center',
  },
  statValue: {
    fontSize: 18,
    fontWeight: 'bold',
    color: '#1976D2',
  },
  statLabel: {
    fontSize: 11,
    color: '#666',
  },
  searchContainer: {
    padding: 12,
  },
  searchBar: {
    flexDirection: 'row',
    alignItems: 'center',
    backgroundColor: '#fff',
    borderRadius: 12,
    paddingHorizontal: 12,
    height: 44,
    borderWidth: 1,
    borderColor: '#E0E0E0',
  },
  searchInput: {
    flex: 1,
    marginLeft: 8,
    fontSize: 15,
    color: '#333',
  },
  filtersPanel: {
    backgroundColor: '#fff',
    paddingHorizontal: 16,
    paddingVertical: 12,
    borderBottomWidth: 1,
    borderBottomColor: '#E0E0E0',
  },
  filterLabel: {
    fontSize: 13,
    fontWeight: '600',
    color: '#666',
    marginBottom: 8,
  },
  aggregationRow: {
    flexDirection: 'row',
    marginBottom: 4,
  },
  aggregationButton: {
    paddingHorizontal: 16,
    paddingVertical: 8,
    borderRadius: 20,
    backgroundColor: '#F5F5F5',
    marginRight: 8,
  },
  aggregationButtonActive: {
    backgroundColor: '#2196F3',
  },
  aggregationText: {
    fontSize: 13,
    color: '#666',
  },
  aggregationTextActive: {
    color: '#fff',
    fontWeight: '600',
  },
  aggregationHelp: {
    fontSize: 11,
    color: '#999',
    fontStyle: 'italic',
    marginBottom: 12,
  },
  articleTypeChip: {
    paddingHorizontal: 12,
    paddingVertical: 6,
    borderRadius: 16,
    backgroundColor: '#F5F5F5',
    marginRight: 8,
  },
  articleTypeChipSelected: {
    backgroundColor: '#4CAF50',
  },
  articleTypeChipText: {
    fontSize: 12,
    color: '#666',
  },
  articleTypeChipTextSelected: {
    color: '#fff',
    fontWeight: '600',
  },
  categoriesSection: {
    paddingHorizontal: 16,
    paddingVertical: 8,
  },
  sectionTitle: {
    fontSize: 14,
    fontWeight: '600',
    color: '#333',
    marginBottom: 8,
  },
  emptyText: {
    fontSize: 13,
    color: '#999',
    fontStyle: 'italic',
  },
  categoriesList: {
    paddingVertical: 4,
  },
  categoryChip: {
    flexDirection: 'row',
    alignItems: 'center',
    paddingHorizontal: 12,
    paddingVertical: 8,
    borderRadius: 16,
    backgroundColor: '#fff',
    marginRight: 8,
    borderWidth: 1,
    borderColor: '#E0E0E0',
  },
  categoryChipSelected: {
    backgroundColor: '#2196F3',
    borderColor: '#2196F3',
  },
  categoryChipText: {
    fontSize: 13,
    color: '#333',
    marginRight: 4,
  },
  categoryChipTextSelected: {
    color: '#fff',
  },
  resultsSection: {
    flex: 1,
    paddingHorizontal: 16,
  },
  loader: {
    marginTop: 40,
  },
  emptyResults: {
    alignItems: 'center',
    marginTop: 40,
  },
  emptyResultsText: {
    fontSize: 14,
    color: '#999',
    textAlign: 'center',
    marginTop: 12,
  },
  resultsList: {
    paddingBottom: 20,
  },
  resultCard: {
    backgroundColor: '#fff',
    borderRadius: 12,
    padding: 14,
    marginBottom: 12,
    borderWidth: 1,
    borderColor: '#E0E0E0',
  },
  resultHeader: {
    flexDirection: 'row',
    justifyContent: 'space-between',
    alignItems: 'flex-start',
    marginBottom: 4,
  },
  resultTitle: {
    flex: 1,
    fontSize: 15,
    fontWeight: '600',
    color: '#1976D2',
    marginRight: 8,
  },
  articleTypeBadge: {
    backgroundColor: '#E8F5E9',
    paddingHorizontal: 8,
    paddingVertical: 3,
    borderRadius: 8,
  },
  articleTypeText: {
    fontSize: 10,
    color: '#4CAF50',
    fontWeight: '500',
  },
  resultDomain: {
    fontSize: 11,
    color: '#999',
    marginBottom: 6,
  },
  resultSnippet: {
    fontSize: 13,
    color: '#555',
    lineHeight: 18,
    marginBottom: 8,
  },
  resultCategories: {
    flexDirection: 'row',
    flexWrap: 'wrap',
    marginBottom: 8,
  },
  resultCategoryBadge: {
    backgroundColor: '#E3F2FD',
    paddingHorizontal: 8,
    paddingVertical: 3,
    borderRadius: 8,
    marginRight: 6,
    marginBottom: 4,
  },
  resultCategoryText: {
    fontSize: 10,
    color: '#1976D2',
  },
  reactionBar: {
    flexDirection: 'row',
    justifyContent: 'space-around',
    borderTopWidth: 1,
    borderTopColor: '#F0F0F0',
    paddingTop: 8,
  },
  reactionButton: {
    flexDirection: 'row',
    alignItems: 'center',
  },
  reactionCount: {
    fontSize: 11,
    color: '#999',
    marginLeft: 3,
  },
  pagination: {
    flexDirection: 'row',
    justifyContent: 'center',
    alignItems: 'center',
    paddingVertical: 16,
  },
  pageButton: {
    padding: 8,
  },
  pageButtonDisabled: {
    opacity: 0.5,
  },
  pageText: {
    fontSize: 14,
    color: '#666',
    marginHorizontal: 16,
  },
});
