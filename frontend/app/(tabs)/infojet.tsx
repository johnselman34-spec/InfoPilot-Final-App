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
} from 'react-native';
import { SafeAreaView } from 'react-native-safe-area-context';
import { Ionicons } from '@expo/vector-icons';
import { useAuth } from '../../src/context/AuthContext';
import { api } from '../../src/services/api';

interface SearchResult {
  url: string;
  title: string;
  snippet: string;
  content?: string;
}

interface CollatedResult {
  id: string;
  url: string;
  title: string;
  snippet: string;
  article_type: string;
  matching_categories: string[];
}

const GOOGLE_OPERATORS = [
  { op: 'site:', desc: 'Limit to specific site' },
  { op: 'filetype:', desc: 'Specific file type' },
  { op: 'intitle:', desc: 'Word in title' },
  { op: 'inurl:', desc: 'Word in URL' },
  { op: 'intext:', desc: 'Word in text' },
  { op: '"..."', desc: 'Exact phrase' },
  { op: '-', desc: 'Exclude word' },
  { op: '*', desc: 'Wildcard' },
  { op: 'OR', desc: 'Either term' },
  { op: 'related:', desc: 'Related sites' },
];

export default function InfoJetScreen() {
  const { user } = useAuth();
  const [searchQuery, setSearchQuery] = useState('');
  const [searchResults, setSearchResults] = useState<SearchResult[]>([]);
  const [collatedResults, setCollatedResults] = useState<CollatedResult[]>([]);
  const [searching, setSearching] = useState(false);
  const [collating, setCollating] = useState(false);
  const [showOperators, setShowOperators] = useState(false);
  const [categoriesCount, setCategoriesCount] = useState(0);

  useEffect(() => {
    loadCategoriesCount();
  }, []);

  const loadCategoriesCount = async () => {
    try {
      const data = await api.get('/categories');
      setCategoriesCount(data.length);
    } catch (error) {
      console.error('Error loading categories:', error);
    }
  };

  const handleSearch = async () => {
    if (!searchQuery.trim()) {
      Alert.alert('Error', 'Please enter a search query');
      return;
    }

    setSearching(true);
    setSearchResults([]);
    setCollatedResults([]);

    try {
      const data = await api.post('/search', { query: searchQuery });
      setSearchResults(data.results);
    } catch (error: any) {
      Alert.alert('Search Error', error.response?.data?.detail || 'Search failed');
    } finally {
      setSearching(false);
    }
  };

  const handleCollate = async () => {
    if (searchResults.length === 0) {
      Alert.alert('Error', 'No search results to collate');
      return;
    }

    if (categoriesCount === 0) {
      Alert.alert(
        'No Categories',
        'Please create at least one category with a protocol before collating.',
        [{ text: 'OK' }]
      );
      return;
    }

    setCollating(true);

    try {
      const data = await api.post('/collate', { search_results: searchResults });
      setCollatedResults(data.results);
      
      if (data.collated_count === 0) {
        Alert.alert(
          'No Matches',
          'No search results matched your category protocols. Try adjusting your protocols or search query.'
        );
      } else {
        Alert.alert(
          'Collation Complete!',
          `${data.collated_count} results were categorized and saved to your database.`
        );
      }
    } catch (error: any) {
      if (error.response?.status === 429) {
        Alert.alert('Daily Limit Reached', error.response.data.detail);
      } else {
        Alert.alert('Collation Error', error.response?.data?.detail || 'Collation failed');
      }
    } finally {
      setCollating(false);
    }
  };

  const insertOperator = (op: string) => {
    setSearchQuery(prev => prev + (prev ? ' ' : '') + op);
  };

  const renderSearchResult = ({ item, index }: { item: SearchResult; index: number }) => (
    <View style={styles.resultCard}>
      <View style={styles.resultNumber}>
        <Text style={styles.resultNumberText}>{index + 1}</Text>
      </View>
      <View style={styles.resultContent}>
        <Text style={styles.resultTitle} numberOfLines={2}>
          {item.title}
        </Text>
        <Text style={styles.resultUrl} numberOfLines={1}>
          {item.url}
        </Text>
        <Text style={styles.resultSnippet} numberOfLines={3}>
          {item.snippet}
        </Text>
      </View>
    </View>
  );

  const renderCollatedResult = ({ item }: { item: CollatedResult }) => (
    <View style={styles.collatedCard}>
      <View style={styles.collatedHeader}>
        <Text style={styles.collatedTitle} numberOfLines={2}>
          {item.title}
        </Text>
        <View style={styles.articleTypeBadge}>
          <Text style={styles.articleTypeText}>{item.article_type}</Text>
        </View>
      </View>
      <View style={styles.categoriesRow}>
        <Ionicons name="folder" size={14} color="#4CAF50" />
        <Text style={styles.categoriesText}>
          {item.matching_categories.join(', ')}
        </Text>
      </View>
    </View>
  );

  return (
    <SafeAreaView style={styles.container} edges={['top']}>
      {/* Header */}
      <View style={styles.header}>
        <View style={styles.headerContent}>
          <Ionicons name="globe" size={28} color="#2196F3" />
          <Text style={styles.headerTitle}>InfoPilot Search</Text>
        </View>
        <TouchableOpacity
          style={styles.operatorsToggle}
          onPress={() => setShowOperators(!showOperators)}
        >
          <Ionicons name="code" size={20} color="#666" />
          <Text style={styles.operatorsToggleText}>Operators</Text>
        </TouchableOpacity>
      </View>

      {/* Google Operators Panel */}
      {showOperators && (
        <ScrollView horizontal style={styles.operatorsPanel} showsHorizontalScrollIndicator={false}>
          {GOOGLE_OPERATORS.map((item, idx) => (
            <TouchableOpacity
              key={idx}
              style={styles.operatorChip}
              onPress={() => insertOperator(item.op)}
            >
              <Text style={styles.operatorText}>{item.op}</Text>
              <Text style={styles.operatorDesc}>{item.desc}</Text>
            </TouchableOpacity>
          ))}
        </ScrollView>
      )}

      {/* Info Banner */}
      <View style={styles.infoBanner}>
        <Ionicons name="information-circle" size={18} color="#1976D2" />
        <Text style={styles.infoBannerText}>
          You have {categoriesCount} categories. Search the web and click "Collate" to automatically
          categorize results based on your protocols.
        </Text>
      </View>

      {/* Search Input */}
      <View style={styles.searchContainer}>
        <View style={styles.searchBar}>
          <Ionicons name="search" size={22} color="#999" />
          <TextInput
            style={styles.searchInput}
            placeholder="Enter your search query..."
            placeholderTextColor="#999"
            value={searchQuery}
            onChangeText={setSearchQuery}
            onSubmitEditing={handleSearch}
            multiline
          />
        </View>
        
        <View style={styles.buttonRow}>
          <TouchableOpacity
            style={[styles.searchButton, searching && styles.buttonDisabled]}
            onPress={handleSearch}
            disabled={searching}
          >
            {searching ? (
              <ActivityIndicator color="#fff" size="small" />
            ) : (
              <>
                <Ionicons name="search" size={18} color="#fff" />
                <Text style={styles.searchButtonText}>Search</Text>
              </>
            )}
          </TouchableOpacity>

          <TouchableOpacity
            style={[
              styles.collateButton,
              (collating || searchResults.length === 0) && styles.buttonDisabled,
            ]}
            onPress={handleCollate}
            disabled={collating || searchResults.length === 0}
          >
            {collating ? (
              <ActivityIndicator color="#fff" size="small" />
            ) : (
              <>
                <Ionicons name="layers" size={18} color="#fff" />
                <Text style={styles.collateButtonText}>Collate</Text>
              </>
            )}
          </TouchableOpacity>
        </View>
      </View>

      {/* Results */}
      <ScrollView style={styles.resultsContainer}>
        {/* Collated Results */}
        {collatedResults.length > 0 && (
          <View style={styles.section}>
            <View style={styles.sectionHeader}>
              <Ionicons name="checkmark-circle" size={20} color="#4CAF50" />
              <Text style={styles.sectionTitle}>Collated Results ({collatedResults.length})</Text>
            </View>
            <FlatList
              data={collatedResults}
              renderItem={renderCollatedResult}
              keyExtractor={(item, idx) => `collated-${idx}`}
              scrollEnabled={false}
            />
          </View>
        )}

        {/* Search Results */}
        {searchResults.length > 0 && (
          <View style={styles.section}>
            <View style={styles.sectionHeader}>
              <Ionicons name="list" size={20} color="#2196F3" />
              <Text style={styles.sectionTitle}>Search Results ({searchResults.length})</Text>
            </View>
            <FlatList
              data={searchResults}
              renderItem={renderSearchResult}
              keyExtractor={(item, idx) => `search-${idx}`}
              scrollEnabled={false}
            />
          </View>
        )}

        {/* Empty State */}
        {searchResults.length === 0 && !searching && (
          <View style={styles.emptyState}>
            <Ionicons name="globe-outline" size={64} color="#ccc" />
            <Text style={styles.emptyTitle}>Ready to Search</Text>
            <Text style={styles.emptyText}>
              Enter a search query above and press Search. Then click Collate to automatically
              categorize results using your InfoJet 2.0 protocols.
            </Text>
          </View>
        )}
      </ScrollView>
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
  headerContent: {
    flexDirection: 'row',
    alignItems: 'center',
  },
  headerTitle: {
    fontSize: 20,
    fontWeight: 'bold',
    color: '#333',
    marginLeft: 10,
  },
  operatorsToggle: {
    flexDirection: 'row',
    alignItems: 'center',
    paddingHorizontal: 10,
    paddingVertical: 6,
    backgroundColor: '#F5F5F5',
    borderRadius: 16,
  },
  operatorsToggleText: {
    fontSize: 12,
    color: '#666',
    marginLeft: 4,
  },
  operatorsPanel: {
    backgroundColor: '#F5F5F5',
    paddingVertical: 8,
    paddingHorizontal: 12,
  },
  operatorChip: {
    backgroundColor: '#fff',
    paddingHorizontal: 12,
    paddingVertical: 8,
    borderRadius: 8,
    marginRight: 8,
    borderWidth: 1,
    borderColor: '#E0E0E0',
  },
  operatorText: {
    fontSize: 13,
    fontWeight: '600',
    color: '#2196F3',
  },
  operatorDesc: {
    fontSize: 10,
    color: '#999',
    marginTop: 2,
  },
  infoBanner: {
    flexDirection: 'row',
    alignItems: 'center',
    backgroundColor: '#E3F2FD',
    paddingHorizontal: 12,
    paddingVertical: 10,
    marginHorizontal: 16,
    marginTop: 12,
    borderRadius: 8,
  },
  infoBannerText: {
    flex: 1,
    marginLeft: 8,
    fontSize: 12,
    color: '#1976D2',
    lineHeight: 16,
  },
  searchContainer: {
    padding: 16,
  },
  searchBar: {
    flexDirection: 'row',
    alignItems: 'flex-start',
    backgroundColor: '#fff',
    borderRadius: 12,
    paddingHorizontal: 14,
    paddingVertical: 12,
    borderWidth: 1,
    borderColor: '#E0E0E0',
    minHeight: 50,
  },
  searchInput: {
    flex: 1,
    marginLeft: 10,
    fontSize: 15,
    color: '#333',
    maxHeight: 80,
  },
  buttonRow: {
    flexDirection: 'row',
    marginTop: 12,
  },
  searchButton: {
    flex: 1,
    flexDirection: 'row',
    alignItems: 'center',
    justifyContent: 'center',
    backgroundColor: '#2196F3',
    borderRadius: 10,
    paddingVertical: 14,
    marginRight: 8,
  },
  searchButtonText: {
    color: '#fff',
    fontSize: 16,
    fontWeight: '600',
    marginLeft: 6,
  },
  collateButton: {
    flex: 1,
    flexDirection: 'row',
    alignItems: 'center',
    justifyContent: 'center',
    backgroundColor: '#4CAF50',
    borderRadius: 10,
    paddingVertical: 14,
    marginLeft: 8,
  },
  collateButtonText: {
    color: '#fff',
    fontSize: 16,
    fontWeight: '600',
    marginLeft: 6,
  },
  buttonDisabled: {
    opacity: 0.6,
  },
  resultsContainer: {
    flex: 1,
    paddingHorizontal: 16,
  },
  section: {
    marginBottom: 20,
  },
  sectionHeader: {
    flexDirection: 'row',
    alignItems: 'center',
    marginBottom: 10,
  },
  sectionTitle: {
    fontSize: 15,
    fontWeight: '600',
    color: '#333',
    marginLeft: 8,
  },
  resultCard: {
    flexDirection: 'row',
    backgroundColor: '#fff',
    borderRadius: 10,
    padding: 12,
    marginBottom: 10,
    borderWidth: 1,
    borderColor: '#E0E0E0',
  },
  resultNumber: {
    width: 28,
    height: 28,
    borderRadius: 14,
    backgroundColor: '#E3F2FD',
    alignItems: 'center',
    justifyContent: 'center',
    marginRight: 10,
  },
  resultNumberText: {
    fontSize: 12,
    fontWeight: '600',
    color: '#1976D2',
  },
  resultContent: {
    flex: 1,
  },
  resultTitle: {
    fontSize: 14,
    fontWeight: '600',
    color: '#333',
    marginBottom: 4,
  },
  resultUrl: {
    fontSize: 11,
    color: '#4CAF50',
    marginBottom: 4,
  },
  resultSnippet: {
    fontSize: 12,
    color: '#666',
    lineHeight: 16,
  },
  collatedCard: {
    backgroundColor: '#E8F5E9',
    borderRadius: 10,
    padding: 12,
    marginBottom: 10,
    borderWidth: 1,
    borderColor: '#C8E6C9',
  },
  collatedHeader: {
    flexDirection: 'row',
    justifyContent: 'space-between',
    alignItems: 'flex-start',
    marginBottom: 8,
  },
  collatedTitle: {
    flex: 1,
    fontSize: 14,
    fontWeight: '600',
    color: '#2E7D32',
    marginRight: 8,
  },
  articleTypeBadge: {
    backgroundColor: '#fff',
    paddingHorizontal: 8,
    paddingVertical: 3,
    borderRadius: 8,
  },
  articleTypeText: {
    fontSize: 10,
    color: '#4CAF50',
    fontWeight: '500',
  },
  categoriesRow: {
    flexDirection: 'row',
    alignItems: 'center',
  },
  categoriesText: {
    fontSize: 12,
    color: '#4CAF50',
    marginLeft: 6,
  },
  emptyState: {
    alignItems: 'center',
    paddingTop: 60,
    paddingHorizontal: 32,
  },
  emptyTitle: {
    fontSize: 18,
    fontWeight: '600',
    color: '#333',
    marginTop: 16,
    marginBottom: 8,
  },
  emptyText: {
    fontSize: 14,
    color: '#666',
    textAlign: 'center',
    lineHeight: 20,
  },
});
