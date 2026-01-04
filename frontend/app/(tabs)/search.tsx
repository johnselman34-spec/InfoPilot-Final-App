import React, { useState, useEffect } from 'react';
import { View, Text, StyleSheet, ScrollView, TouchableOpacity, Alert, ActivityIndicator } from 'react-native';
import { SafeAreaView } from 'react-native-safe-area-context';
import { Ionicons } from '@expo/vector-icons';
import { colors } from '../../src/utils/colors';
import { CustomInput } from '../../src/components/CustomInput';
import { CustomButton } from '../../src/components/CustomButton';
import { useCategoryStore } from '../../src/store/categoryStore';
import { searchAPI } from '../../src/services/api';
import axios from 'axios';

export default function SearchScreen() {
  const { categories, fetchCategories } = useCategoryStore();
  const [searchQuery, setSearchQuery] = useState('');
  const [selectedCategories, setSelectedCategories] = useState<string[]>([]);
  const [searching, setSearching] = useState(false);
  const [collating, setCollating] = useState(false);
  const [googleResults, setGoogleResults] = useState<any[]>([]);

  useEffect(() => {
    fetchCategories();
  }, []);

  const handleGoogleSearch = async () => {
    if (!searchQuery) {
      Alert.alert('Error', 'Please enter a search query');
      return;
    }

    try {
      setSearching(true);
      // Perform Google search via backend (which uses SerpAPI)
      const response = await axios.get(`${process.env.EXPO_PUBLIC_BACKEND_URL}/api/search/google`, {
        params: { q: searchQuery }
      });
      
      setGoogleResults(response.data.results || []);
      
      if (response.data.results?.length === 0) {
        Alert.alert('No Results', 'No search results found. Try different keywords.');
      }
    } catch (error: any) {
      console.error('Search error:', error);
      Alert.alert('Search Error', error.response?.data?.detail || 'Failed to search. Please try again.');
    } finally {
      setSearching(false);
    }
  };

  const handleCollateAll = async () => {
    if (selectedCategories.length === 0) {
      Alert.alert('Error', 'Please select at least one category to collate results into');
      return;
    }

    if (googleResults.length === 0) {
      Alert.alert('Error', 'No search results to collate. Search first!');
      return;
    }

    try {
      setCollating(true);
      
      // Collate results for each selected category
      const promises = selectedCategories.map(categoryId =>
        searchAPI.collate({
          category_id: categoryId,
          search_query: searchQuery,
        })
      );
      
      await Promise.all(promises);
      
      Alert.alert(
        'Success!', 
        `Collated ${googleResults.length} search results into ${selectedCategories.length} ${selectedCategories.length === 1 ? 'category' : 'categories'}`
      );
      
      // Reset
      setGoogleResults([]);
      setSearchQuery('');
      setSelectedCategories([]);
    } catch (error: any) {
      Alert.alert('Error', error.response?.data?.detail || 'Failed to collate search results');
    } finally {
      setCollating(false);
    }
  };

  const toggleCategory = (categoryId: string) => {
    if (selectedCategories.includes(categoryId)) {
      setSelectedCategories(selectedCategories.filter(id => id !== categoryId));
    } else {
      setSelectedCategories([...selectedCategories, categoryId]);
    }
  };

  return (
    <SafeAreaView style={styles.container} edges={['bottom']}>
      <ScrollView contentContainerStyle={styles.content}>
        <View style={styles.header}>
          <Text style={styles.title}>InfoPilot Search</Text>
          <Text style={styles.subtitle}>Search Google, then collate results into your categories</Text>
        </View>

        {/* Step 1: Google Search */}
        <View style={styles.searchSection}>
          <View style={styles.stepHeader}>
            <View style={styles.stepBadge}>
              <Text style={styles.stepBadgeText}>1</Text>
            </View>
            <Text style={styles.stepTitle}>Search Google</Text>
          </View>

          <CustomInput
            label="Enter your search query"
            value={searchQuery}
            onChangeText={setSearchQuery}
            placeholder="e.g., American Civil War heroes"
          />

          <CustomButton
            title={searching ? "Searching..." : "Search Google"}
            onPress={handleGoogleSearch}
            loading={searching}
            style={styles.searchButton}
          />
        </View>

        {/* Search Results */}
        {googleResults.length > 0 && (
          <View style={styles.resultsSection}>
            <View style={styles.resultsHeader}>
              <Text style={styles.resultsTitle}>
                {googleResults.length} Search Results
              </Text>
              <Text style={styles.resultsSubtitle}>
                Review results, then select categories to collate
              </Text>
            </View>

            <ScrollView style={styles.resultsList} nestedScrollEnabled>
              {googleResults.slice(0, 10).map((result: any, index: number) => (
                <View key={index} style={styles.resultCard}>
                  <Text style={styles.resultTitle} numberOfLines={2}>
                    {result.title}
                  </Text>
                  <Text style={styles.resultSnippet} numberOfLines={3}>
                    {result.snippet}
                  </Text>
                  <Text style={styles.resultUrl} numberOfLines={1}>
                    {result.link}
                  </Text>
                </View>
              ))}
            </ScrollView>
          </View>
        )}

        {/* Step 2: Select Categories */}
        {googleResults.length > 0 && (
          <View style={styles.categoriesSection}>
            <View style={styles.stepHeader}>
              <View style={styles.stepBadge}>
                <Text style={styles.stepBadgeText}>2</Text>
              </View>
              <Text style={styles.stepTitle}>Select Categories</Text>
            </View>

            {categories.length === 0 ? (
              <View style={styles.emptyCategory}>
                <Ionicons name="folder-open-outline" size={48} color={colors.gray} />
                <Text style={styles.emptyCategoryText}>
                  No categories yet. Create categories first!
                </Text>
              </View>
            ) : (
              <View style={styles.categoriesGrid}>
                {categories.map((category) => (
                  <TouchableOpacity
                    key={category.id}
                    style={[
                      styles.categoryChip,
                      selectedCategories.includes(category.id) && styles.categoryChipSelected,
                    ]}
                    onPress={() => toggleCategory(category.id)}
                  >
                    <Ionicons
                      name={selectedCategories.includes(category.id) ? "checkbox" : "square-outline"}
                      size={20}
                      color={selectedCategories.includes(category.id) ? colors.white : colors.primary}
                    />
                    <Text
                      style={[
                        styles.categoryChipText,
                        selectedCategories.includes(category.id) && styles.categoryChipTextSelected,
                      ]}
                    >
                      {category.name}
                    </Text>
                  </TouchableOpacity>
                ))}
              </View>
            )}
          </View>
        )}

        {/* Step 3: Collate Button */}
        {googleResults.length > 0 && selectedCategories.length > 0 && (
          <View style={styles.collateSection}>
            <View style={styles.stepHeader}>
              <View style={styles.stepBadge}>
                <Text style={styles.stepBadgeText}>3</Text>
              </View>
              <Text style={styles.stepTitle}>Collate Results</Text>
            </View>

            <CustomButton
              title={collating ? "Collating..." : `Collate All ${googleResults.length} Results`}
              onPress={handleCollateAll}
              loading={collating}
              style={styles.collateButton}
            />
            
            <Text style={styles.collateInfo}>
              Results will be categorized into {selectedCategories.length} {selectedCategories.length === 1 ? 'category' : 'categories'} using InfoPilot 2.0 protocols
            </Text>
          </View>
        )}

        {/* Info Section */}
        {googleResults.length === 0 && (
          <View style={styles.infoSection}>
            <Text style={styles.infoTitle}>How InfoPilot Works</Text>
            <View style={styles.stepItem}>
              <View style={styles.stepNumber}>
                <Text style={styles.stepNumberText}>1</Text>
              </View>
              <Text style={styles.stepText}>
                Enter your search query and click "Search Google"
              </Text>
            </View>
            <View style={styles.stepItem}>
              <View style={styles.stepNumber}>
                <Text style={styles.stepNumberText}>2</Text>
              </View>
              <Text style={styles.stepText}>
                Review the Google search results
              </Text>
            </View>
            <View style={styles.stepItem}>
              <View style={styles.stepNumber}>
                <Text style={styles.stepNumberText}>3</Text>
              </View>
              <Text style={styles.stepText}>
                Select categories with InfoPilot 2.0 protocols
              </Text>
            </View>
            <View style={styles.stepItem}>
              <View style={styles.stepNumber}>
                <Text style={styles.stepNumberText}>4</Text>
              </View>
              <Text style={styles.stepText}>
                Click "Collate All" to automatically categorize results using AI
              </Text>
            </View>
          </View>
        )}
      </ScrollView>
    </SafeAreaView>
  );
}

const styles = StyleSheet.create({
  container: {
    flex: 1,
    backgroundColor: colors.background,
  },
  content: {
    padding: 20,
  },
  header: {
    marginBottom: 24,
  },
  title: {
    fontSize: 28,
    fontWeight: 'bold',
    color: colors.text,
  },
  subtitle: {
    fontSize: 14,
    color: colors.textLight,
    marginTop: 4,
  },
  searchSection: {
    backgroundColor: colors.white,
    padding: 20,
    borderRadius: 12,
    marginBottom: 24,
    shadowColor: colors.black,
    shadowOffset: { width: 0, height: 2 },
    shadowOpacity: 0.1,
    shadowRadius: 4,
    elevation: 3,
  },
  label: {
    fontSize: 14,
    fontWeight: '600',
    color: colors.text,
    marginBottom: 12,
  },
  emptyCategory: {
    padding: 32,
    backgroundColor: colors.lightGray,
    borderRadius: 8,
    alignItems: 'center',
  },
  emptyCategoryText: {
    fontSize: 14,
    color: colors.textLight,
    textAlign: 'center',
    marginTop: 12,
  },
  categoriesGrid: {
    flexDirection: 'row',
    flexWrap: 'wrap',
    gap: 12,
  },
  categoryChip: {
    flexDirection: 'row',
    alignItems: 'center',
    gap: 8,
    paddingHorizontal: 16,
    paddingVertical: 10,
    borderRadius: 20,
    backgroundColor: colors.lightGray,
    borderWidth: 2,
    borderColor: colors.border,
  },
  categoryChipSelected: {
    backgroundColor: colors.primary,
    borderColor: colors.primary,
  },
  categoryChipText: {
    fontSize: 14,
    fontWeight: '600',
    color: colors.text,
  },
  categoryChipTextSelected: {
    color: colors.white,
  },
  collateButton: {
    marginBottom: 12,
  },
  resultsSection: {
    backgroundColor: colors.white,
    padding: 20,
    borderRadius: 12,
    marginBottom: 24,
    maxHeight: 400,
    shadowColor: colors.black,
    shadowOffset: { width: 0, height: 2 },
    shadowOpacity: 0.1,
    shadowRadius: 4,
    elevation: 3,
  },
  resultsTitle: {
    fontSize: 20,
    fontWeight: 'bold',
    color: colors.text,
  },
  resultCard: {
    backgroundColor: colors.white,
    padding: 16,
    borderRadius: 12,
    marginBottom: 12,
    shadowColor: colors.black,
    shadowOffset: { width: 0, height: 1 },
    shadowOpacity: 0.1,
    shadowRadius: 2,
    elevation: 2,
  },
  resultTitle: {
    fontSize: 16,
    fontWeight: '600',
    color: colors.primary,
    marginBottom: 8,
  },
  resultSnippet: {
    fontSize: 14,
    color: colors.text,
    lineHeight: 20,
    marginBottom: 8,
  },
  resultMeta: {
    flexDirection: 'row',
    justifyContent: 'space-between',
  },
  resultDomain: {
    fontSize: 12,
    color: colors.textLight,
  },
  resultType: {
    fontSize: 12,
    fontWeight: '600',
    color: colors.secondary,
  },
  infoSection: {
    backgroundColor: colors.lightGray,
    padding: 20,
    borderRadius: 12,
  },
  infoTitle: {
    fontSize: 18,
    fontWeight: 'bold',
    color: colors.text,
    marginBottom: 16,
  },
  stepItem: {
    flexDirection: 'row',
    alignItems: 'flex-start',
    marginBottom: 16,
  },
  stepNumber: {
    width: 28,
    height: 28,
    borderRadius: 14,
    backgroundColor: colors.primary,
    justifyContent: 'center',
    alignItems: 'center',
    marginRight: 12,
  },
  stepNumberText: {
    fontSize: 14,
    fontWeight: 'bold',
    color: colors.white,
  },
  stepText: {
    flex: 1,
    fontSize: 14,
    color: colors.text,
    lineHeight: 20,
    paddingTop: 4,
  },
  stepHeader: {
    flexDirection: 'row',
    alignItems: 'center',
    marginBottom: 16,
  },
  stepBadge: {
    width: 32,
    height: 32,
    borderRadius: 16,
    backgroundColor: colors.primary,
    justifyContent: 'center',
    alignItems: 'center',
    marginRight: 12,
  },
  stepBadgeText: {
    fontSize: 16,
    fontWeight: 'bold',
    color: colors.white,
  },
  stepTitle: {
    fontSize: 18,
    fontWeight: 'bold',
    color: colors.text,
  },
  searchButton: {
    marginTop: 16,
  },
  resultsHeader: {
    marginBottom: 16,
  },
  resultsSubtitle: {
    fontSize: 14,
    color: colors.textLight,
    marginTop: 4,
  },
  resultsList: {
    maxHeight: 300,
    marginBottom: 16,
  },
  resultUrl: {
    fontSize: 12,
    color: colors.textLight,
    marginTop: 4,
  },
  categoriesSection: {
    backgroundColor: colors.white,
    padding: 20,
    borderRadius: 12,
    marginBottom: 24,
    shadowColor: colors.black,
    shadowOffset: { width: 0, height: 2 },
    shadowOpacity: 0.1,
    shadowRadius: 4,
    elevation: 3,
  },
  collateSection: {
    backgroundColor: colors.white,
    padding: 20,
    borderRadius: 12,
    marginBottom: 24,
    shadowColor: colors.black,
    shadowOffset: { width: 0, height: 2 },
    shadowOpacity: 0.1,
    shadowRadius: 4,
    elevation: 3,
  },
  collateInfo: {
    fontSize: 14,
    color: colors.textLight,
    textAlign: 'center',
    marginTop: 12,
    lineHeight: 20,
  },
});
