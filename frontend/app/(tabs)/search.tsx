import React, { useState } from 'react';
import { View, Text, StyleSheet, ScrollView, TouchableOpacity, Alert } from 'react-native';
import { SafeAreaView } from 'react-native-safe-area-context';
import { Ionicons } from '@expo/vector-icons';
import { colors } from '../../src/utils/colors';
import { CustomInput } from '../../src/components/CustomInput';
import { CustomButton } from '../../src/components/CustomButton';
import { useCategoryStore } from '../../src/store/categoryStore';
import { searchAPI } from '../../src/services/api';

export default function SearchScreen() {
  const { categories } = useCategoryStore();
  const [searchQuery, setSearchQuery] = useState('');
  const [selectedCategory, setSelectedCategory] = useState<string | null>(null);
  const [loading, setLoading] = useState(false);
  const [results, setResults] = useState<any[]>([]);

  const handleCollate = async () => {
    if (!searchQuery || !selectedCategory) {
      Alert.alert('Error', 'Please enter a search query and select a category');
      return;
    }

    try {
      setLoading(true);
      const response = await searchAPI.collate({
        category_id: selectedCategory,
        search_query: searchQuery,
      });
      Alert.alert('Success', response.data.message);
      setSearchQuery('');
      // Fetch results
      const resultsResponse = await searchAPI.getResults({ category_ids: selectedCategory });
      setResults(resultsResponse.data.results);
    } catch (error: any) {
      Alert.alert('Error', error.response?.data?.detail || 'Failed to collate search results');
    } finally {
      setLoading(false);
    }
  };

  return (
    <SafeAreaView style={styles.container} edges={['bottom']}>
      <ScrollView contentContainerStyle={styles.content}>
        <View style={styles.header}>
          <Text style={styles.title}>InfoJet Search</Text>
          <Text style={styles.subtitle}>Collate search results using your protocols</Text>
        </View>

        <View style={styles.searchSection}>
          <CustomInput
            label="Search Query"
            value={searchQuery}
            onChangeText={setSearchQuery}
            placeholder="Enter your Google search query"
          />

          <Text style={styles.label}>Select Category</Text>
          {categories.length === 0 ? (
            <View style={styles.emptyCategory}>
              <Text style={styles.emptyCategoryText}>
                No categories yet. Create a category first!
              </Text>
            </View>
          ) : (
            <View style={styles.categoriesGrid}>
              {categories.map((category) => (
                <TouchableOpacity
                  key={category.id}
                  style={[
                    styles.categoryChip,
                    selectedCategory === category.id && styles.categoryChipSelected,
                  ]}
                  onPress={() => setSelectedCategory(category.id)}
                >
                  <Text
                    style={[
                      styles.categoryChipText,
                      selectedCategory === category.id && styles.categoryChipTextSelected,
                    ]}
                  >
                    {category.name}
                  </Text>
                </TouchableOpacity>
              ))}
            </View>
          )}

          <CustomButton
            title="Collate Results"
            onPress={handleCollate}
            loading={loading}
            disabled={!searchQuery || !selectedCategory}
            style={styles.collateButton}
          />
        </View>

        {results.length > 0 && (
          <View style={styles.resultsSection}>
            <Text style={styles.resultsTitle}>Recent Results</Text>
            {results.map((result, index) => (
              <View key={index} style={styles.resultCard}>
                <Text style={styles.resultTitle} numberOfLines={2}>
                  {result.title}
                </Text>
                <Text style={styles.resultSnippet} numberOfLines={3}>
                  {result.snippet}
                </Text>
                <View style={styles.resultMeta}>
                  <Text style={styles.resultDomain}>{result.root_domain}</Text>
                  <Text style={styles.resultType}>{result.article_type}</Text>
                </View>
              </View>
            ))}
          </View>
        )}

        <View style={styles.infoSection}>
          <Text style={styles.infoTitle}>How InfoJet Works</Text>
          <View style={styles.stepItem}>
            <View style={styles.stepNumber}>
              <Text style={styles.stepNumberText}>1</Text>
            </View>
            <Text style={styles.stepText}>
              Enter your Google search query above
            </Text>
          </View>
          <View style={styles.stepItem}>
            <View style={styles.stepNumber}>
              <Text style={styles.stepNumberText}>2</Text>
            </View>
            <Text style={styles.stepText}>
              Select a category with an InfoJet 2.0 protocol
            </Text>
          </View>
          <View style={styles.stepItem}>
            <View style={styles.stepNumber}>
              <Text style={styles.stepNumberText}>3</Text>
            </View>
            <Text style={styles.stepText}>
              Click Collate to search Google and categorize results
            </Text>
          </View>
          <View style={styles.stepItem}>
            <View style={styles.stepNumber}>
              <Text style={styles.stepNumberText}>4</Text>
            </View>
            <Text style={styles.stepText}>
              AI classifies articles and filters inappropriate content
            </Text>
          </View>
        </View>
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
    padding: 20,
    backgroundColor: colors.lightGray,
    borderRadius: 8,
    marginBottom: 16,
  },
  emptyCategoryText: {
    fontSize: 14,
    color: colors.textLight,
    textAlign: 'center',
  },
  categoriesGrid: {
    flexDirection: 'row',
    flexWrap: 'wrap',
    gap: 12,
    marginBottom: 20,
  },
  categoryChip: {
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
    marginTop: 4,
  },
  resultsSection: {
    marginBottom: 24,
  },
  resultsTitle: {
    fontSize: 20,
    fontWeight: 'bold',
    color: colors.text,
    marginBottom: 16,
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
});
