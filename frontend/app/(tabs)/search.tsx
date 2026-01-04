import React, { useState, useEffect } from 'react';
import {
  View,
  Text,
  TextInput,
  TouchableOpacity,
  StyleSheet,
  FlatList,
  ActivityIndicator,
  Alert,
  Linking,
} from 'react-native';
import { Ionicons } from '@expo/vector-icons';
import { useAuthStore } from '../../store/authStore';
import axios from 'axios';

const API_URL = process.env.EXPO_PUBLIC_BACKEND_URL;

export default function SearchScreen() {
  const { user, token } = useAuthStore();
  const [query, setQuery] = useState('');
  const [results, setResults] = useState([]);
  const [loading, setLoading] = useState(false);
  const [page, setPage] = useState(1);
  const [totalResults, setTotalResults] = useState(0);

  const handleSearch = async (newPage = 1) => {
    if (!query.trim()) {
      Alert.alert('Error', 'Please enter a search query');
      return;
    }

    setLoading(true);
    try {
      const response = await axios.post(
        `${API_URL}/api/search`,
        { query, page: newPage, num: user?.isPaid ? 20 : 10 },
        { headers: { Authorization: `Bearer ${token}` } }
      );

      setResults(response.data.results);
      setTotalResults(response.data.totalResults);
      setPage(newPage);
    } catch (error) {
      console.error('Search error:', error);
      Alert.alert('Error', 'Failed to perform search. Make sure Google API credentials are configured.');
    }
    setLoading(false);
  };

  const handleCollate = async () => {
    if (!results.length) {
      Alert.alert('Info', 'Search first to get results to collate');
      return;
    }

    setLoading(true);
    try {
      const response = await axios.post(
        `${API_URL}/api/collate`,
        { query, userId: user?.id },
        { headers: { Authorization: `Bearer ${token}` } }
      );
      Alert.alert(
        'Success! ✅',
        `${response.data.message}\n\n` +
        `• Collated: ${response.data.categorized}/${response.data.total} results\n` +
        `• Using ${response.data.protocols_used} protocols\n\n` +
        `Results are automatically saved to your matching categories!`
      );
    } catch (error: any) {
      const errorMsg = error.response?.data?.detail || 'Failed to collate results';
      Alert.alert('Error', errorMsg);
    }
    setLoading(false);
  };

  const openURL = (url: string) => {
    Linking.openURL(url).catch(() => {
      Alert.alert('Error', 'Cannot open this URL');
    });
  };

  const renderResult = ({ item, index }: any) => (
    <TouchableOpacity
      style={styles.resultCard}
      onPress={() => openURL(item.url)}
    >
      <Text style={styles.resultTitle} numberOfLines={2}>
        {item.title}
      </Text>
      <Text style={styles.resultUrl} numberOfLines={1}>
        {item.displayLink}
      </Text>
      <Text style={styles.resultSnippet} numberOfLines={3}>
        {item.snippet}
      </Text>
    </TouchableOpacity>
  );

  return (
    <View style={styles.container}>
      {/* Header */}
      <View style={styles.header}>
        <Text style={styles.headerTitle}>Search</Text>
        <Text style={styles.headerSubtitle}>Powered by Google Custom Search</Text>
      </View>

      {/* Search Bar */}
      <View style={styles.searchContainer}>
        <View style={styles.searchBar}>
          <Ionicons name="search" size={20} color="#999" />
          <TextInput
            style={styles.searchInput}
            placeholder="Enter your search query..."
            value={query}
            onChangeText={setQuery}
            onSubmitEditing={() => handleSearch(1)}
            editable={!loading}
          />
          {query.length > 0 && (
            <TouchableOpacity onPress={() => setQuery('')}>
              <Ionicons name="close-circle" size={20} color="#999" />
            </TouchableOpacity>
          )}
        </View>
        <TouchableOpacity
          style={[styles.searchButton, loading && styles.buttonDisabled]}
          onPress={() => handleSearch(1)}
          disabled={loading}
        >
          {loading ? (
            <ActivityIndicator color="#FFF" />
          ) : (
            <Text style={styles.searchButtonText}>Search</Text>
          )}
        </TouchableOpacity>
      </View>

      {/* Results Info & Actions */}
      {results.length > 0 && (
        <View style={styles.resultsInfo}>
          <Text style={styles.resultsCount}>
            {totalResults.toLocaleString()} results found
          </Text>
          <TouchableOpacity
            style={styles.collateButton}
            onPress={handleCollate}
            disabled={loading}
          >
            <Ionicons name="folder" size={16} color="#1E88E5" />
            <Text style={styles.collateText}>Collate</Text>
          </TouchableOpacity>
        </View>
      )}

      {/* Results List */}
      <FlatList
        data={results}
        renderItem={renderResult}
        keyExtractor={(item, index) => `${item.url}-${index}`}
        contentContainerStyle={styles.resultsList}
        ListEmptyComponent={
          !loading ? (
            <View style={styles.emptyState}>
              <Ionicons name="search" size={64} color="#CCC" />
              <Text style={styles.emptyText}>No results yet</Text>
              <Text style={styles.emptySubtext}>
                Enter a query and tap Search to get started
              </Text>
            </View>
          ) : null
        }
      />

      {/* Pagination */}
      {results.length > 0 && totalResults > results.length && (
        <View style={styles.pagination}>
          <TouchableOpacity
            style={[
              styles.pageButton,
              page === 1 && styles.pageButtonDisabled,
            ]}
            onPress={() => handleSearch(page - 1)}
            disabled={page === 1 || loading}
          >
            <Ionicons name="chevron-back" size={20} color="#1E88E5" />
            <Text style={styles.pageButtonText}>Previous</Text>
          </TouchableOpacity>

          <Text style={styles.pageNumber}>Page {page}</Text>

          <TouchableOpacity
            style={[styles.pageButton, loading && styles.pageButtonDisabled]}
            onPress={() => handleSearch(page + 1)}
            disabled={loading}
          >
            <Text style={styles.pageButtonText}>Next</Text>
            <Ionicons name="chevron-forward" size={20} color="#1E88E5" />
          </TouchableOpacity>
        </View>
      )}

      {/* Upgrade Notice for Free Users */}
      {!user?.isPaid && results.length > 0 && (
        <View style={styles.upgradeNotice}>
          <Ionicons name="information-circle" size={20} color="#FF9800" />
          <Text style={styles.upgradeNoticeText}>
            Free users limited to 10 results. Upgrade for 20 results per page!
          </Text>
        </View>
      )}
    </View>
  );
}

const styles = StyleSheet.create({
  container: {
    flex: 1,
    backgroundColor: '#F5F9FC',
  },
  header: {
    paddingTop: 60,
    paddingHorizontal: 20,
    paddingBottom: 20,
    backgroundColor: '#FFF',
    borderBottomWidth: 1,
    borderBottomColor: '#E0E0E0',
  },
  headerTitle: {
    fontSize: 28,
    fontWeight: 'bold',
    color: '#212121',
  },
  headerSubtitle: {
    fontSize: 14,
    color: '#666',
    marginTop: 4,
  },
  searchContainer: {
    padding: 16,
    backgroundColor: '#FFF',
    borderBottomWidth: 1,
    borderBottomColor: '#E0E0E0',
  },
  searchBar: {
    flexDirection: 'row',
    alignItems: 'center',
    backgroundColor: '#F5F5F5',
    borderRadius: 12,
    paddingHorizontal: 12,
    marginBottom: 12,
    gap: 8,
  },
  searchInput: {
    flex: 1,
    paddingVertical: 12,
    fontSize: 16,
    color: '#212121',
  },
  searchButton: {
    backgroundColor: '#1E88E5',
    borderRadius: 12,
    padding: 14,
    alignItems: 'center',
  },
  buttonDisabled: {
    backgroundColor: '#B0BEC5',
  },
  searchButtonText: {
    color: '#FFF',
    fontSize: 16,
    fontWeight: '600',
  },
  resultsInfo: {
    flexDirection: 'row',
    justifyContent: 'space-between',
    alignItems: 'center',
    paddingHorizontal: 16,
    paddingVertical: 12,
    backgroundColor: '#FFF',
    borderBottomWidth: 1,
    borderBottomColor: '#E0E0E0',
  },
  resultsCount: {
    fontSize: 14,
    color: '#666',
  },
  collateButton: {
    flexDirection: 'row',
    alignItems: 'center',
    backgroundColor: '#E3F2FD',
    paddingHorizontal: 12,
    paddingVertical: 6,
    borderRadius: 16,
    gap: 4,
  },
  collateText: {
    color: '#1E88E5',
    fontSize: 14,
    fontWeight: '600',
  },
  resultsList: {
    padding: 16,
  },
  resultCard: {
    backgroundColor: '#FFF',
    padding: 16,
    borderRadius: 12,
    marginBottom: 12,
    borderWidth: 1,
    borderColor: '#E0E0E0',
  },
  resultTitle: {
    fontSize: 16,
    fontWeight: '600',
    color: '#1E88E5',
    marginBottom: 4,
  },
  resultUrl: {
    fontSize: 13,
    color: '#4CAF50',
    marginBottom: 8,
  },
  resultSnippet: {
    fontSize: 14,
    color: '#666',
    lineHeight: 20,
  },
  emptyState: {
    alignItems: 'center',
    justifyContent: 'center',
    paddingVertical: 60,
  },
  emptyText: {
    fontSize: 18,
    fontWeight: '600',
    color: '#999',
    marginTop: 16,
  },
  emptySubtext: {
    fontSize: 14,
    color: '#CCC',
    marginTop: 8,
    textAlign: 'center',
  },
  pagination: {
    flexDirection: 'row',
    justifyContent: 'space-between',
    alignItems: 'center',
    paddingHorizontal: 16,
    paddingVertical: 16,
    backgroundColor: '#FFF',
    borderTopWidth: 1,
    borderTopColor: '#E0E0E0',
  },
  pageButton: {
    flexDirection: 'row',
    alignItems: 'center',
    padding: 8,
    gap: 4,
  },
  pageButtonDisabled: {
    opacity: 0.3,
  },
  pageButtonText: {
    color: '#1E88E5',
    fontSize: 14,
    fontWeight: '600',
  },
  pageNumber: {
    fontSize: 14,
    color: '#666',
    fontWeight: '600',
  },
  upgradeNotice: {
    flexDirection: 'row',
    alignItems: 'center',
    backgroundColor: '#FFF3E0',
    padding: 12,
    gap: 8,
  },
  upgradeNoticeText: {
    flex: 1,
    fontSize: 12,
    color: '#E65100',
  },
});
