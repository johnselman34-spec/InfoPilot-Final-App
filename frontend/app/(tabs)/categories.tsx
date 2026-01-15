import React, { useEffect, useState, useCallback } from 'react';
import { 
  View, Text, StyleSheet, ScrollView, TouchableOpacity, RefreshControl, 
  Alert, Modal, KeyboardAvoidingView, Platform, ActivityIndicator, Linking 
} from 'react-native';
import { SafeAreaView } from 'react-native-safe-area-context';
import { Ionicons } from '@expo/vector-icons';
import { useCategoryStore } from '../../src/store/categoryStore';
import { colors } from '../../src/utils/colors';
import { CustomInput } from '../../src/components/CustomInput';
import { CustomButton } from '../../src/components/CustomButton';
import { searchAPI } from '../../src/services/api';

// Types
interface SearchResult {
  id: string;
  url: string;
  title: string;
  snippet: string;
  article_type?: string;
  root_domain?: string;
  year?: number;
  created_at?: string;
  likes?: number;
  category_ids?: string[];
}

type CombineMode = 'or' | 'and';

export default function CategoriesScreen() {
  const { categories, fetchCategories, createCategory, deleteCategory, isLoading } = useCategoryStore();
  
  // State management
  const [refreshing, setRefreshing] = useState(false);
  const [modalVisible, setModalVisible] = useState(false);
  const [categoryName, setCategoryName] = useState('');
  const [protocol, setProtocol] = useState('');
  const [isPublic, setIsPublic] = useState(true);
  const [loading, setLoading] = useState(false);
  
  // Category selection & search results state
  const [selectedCategoryIds, setSelectedCategoryIds] = useState<Set<string>>(new Set());
  const [combineMode, setCombineMode] = useState<CombineMode>('or');
  const [searchResults, setSearchResults] = useState<SearchResult[]>([]);
  const [loadingResults, setLoadingResults] = useState(false);
  const [resultsVisible, setResultsVisible] = useState(false);
  const [currentPage, setCurrentPage] = useState(1);
  const [totalPages, setTotalPages] = useState(1);

  useEffect(() => {
    fetchCategories();
  }, []);

  // Fetch search results when selected categories change
  useEffect(() => {
    if (selectedCategoryIds.size > 0) {
      loadSearchResults();
    } else {
      setSearchResults([]);
      setResultsVisible(false);
    }
  }, [selectedCategoryIds, combineMode, currentPage]);

  const loadSearchResults = async () => {
    if (selectedCategoryIds.size === 0) return;
    
    try {
      setLoadingResults(true);
      
      // Build category IDs string based on combine mode
      const categoryIdsArray = Array.from(selectedCategoryIds);
      const categoryIdsParam = categoryIdsArray.join(',');
      
      const response = await searchAPI.getResults({
        category_ids: categoryIdsParam,
        page: currentPage,
      });
      
      if (response.data) {
        setSearchResults(response.data.results || []);
        setTotalPages(response.data.total_pages || 1);
        setResultsVisible(true);
      }
    } catch (error) {
      console.error('Load search results error:', error);
      // Show empty state instead of error
      setSearchResults([]);
    } finally {
      setLoadingResults(false);
    }
  };

  const onRefresh = async () => {
    setRefreshing(true);
    await fetchCategories();
    if (selectedCategoryIds.size > 0) {
      await loadSearchResults();
    }
    setRefreshing(false);
  };

  const handleCreateCategory = async () => {
    if (!categoryName || !protocol) {
      Alert.alert('Error', 'Please fill in all fields');
      return;
    }

    try {
      setLoading(true);
      await createCategory({
        name: categoryName,
        protocol,
        is_public: isPublic,
      });
      Alert.alert('Success', 'Category created successfully! 🎉');
      setModalVisible(false);
      setCategoryName('');
      setProtocol('');
      setIsPublic(true);
    } catch (error: any) {
      Alert.alert('Error', error.message);
    } finally {
      setLoading(false);
    }
  };

  const handleDeleteCategory = (id: string, name: string) => {
    Alert.alert(
      'Delete Category',
      `Are you sure you want to delete "${name}"? This will also delete all associated search results.`,
      [
        { text: 'Cancel', style: 'cancel' },
        {
          text: 'Delete',
          style: 'destructive',
          onPress: async () => {
            try {
              await deleteCategory(id);
              // Remove from selected if it was selected
              if (selectedCategoryIds.has(id)) {
                const newSelected = new Set(selectedCategoryIds);
                newSelected.delete(id);
                setSelectedCategoryIds(newSelected);
              }
              Alert.alert('Success', 'Category deleted');
            } catch (error: any) {
              Alert.alert('Error', error.message);
            }
          },
        },
      ]
    );
  };

  // Toggle category selection (checkbox behavior)
  const toggleCategorySelection = (categoryId: string) => {
    const newSelected = new Set(selectedCategoryIds);
    if (newSelected.has(categoryId)) {
      newSelected.delete(categoryId);
    } else {
      newSelected.add(categoryId);
    }
    setSelectedCategoryIds(newSelected);
    setCurrentPage(1); // Reset to first page
  };

  // Select all categories
  const selectAllCategories = () => {
    const allIds = new Set(categories.map(c => c.id));
    setSelectedCategoryIds(allIds);
  };

  // Clear all selections
  const clearAllSelections = () => {
    setSelectedCategoryIds(new Set());
  };

  // Handle viewing a single category's results
  const handleViewCategory = (categoryId: string) => {
    setSelectedCategoryIds(new Set([categoryId]));
  };

  // Render search result card
  const renderSearchResult = (result: SearchResult) => (
    <TouchableOpacity 
      key={result.id} 
      style={styles.resultCard}
      onPress={() => Linking.openURL(result.url)}
    >
      <View style={styles.resultHeader}>
        {result.article_type && (
          <View style={styles.typeBadge}>
            <Text style={styles.typeBadgeText}>{result.article_type}</Text>
          </View>
        )}
        {result.year && (
          <Text style={styles.yearText}>{result.year}</Text>
        )}
      </View>
      
      <Text style={styles.resultTitle} numberOfLines={2}>{result.title}</Text>
      <Text style={styles.resultSnippet} numberOfLines={3}>{result.snippet}</Text>
      
      <View style={styles.resultFooter}>
        <Text style={styles.resultDomain} numberOfLines={1}>
          🔗 {result.root_domain || result.url}
        </Text>
        <View style={styles.resultActions}>
          <TouchableOpacity style={styles.actionButton}>
            <Ionicons name="heart-outline" size={16} color={colors.primary} />
            <Text style={styles.actionText}>{result.likes || 0}</Text>
          </TouchableOpacity>
        </View>
      </View>
    </TouchableOpacity>
  );

  return (
    <SafeAreaView style={styles.container} edges={['bottom']}>
      <ScrollView
        contentContainerStyle={styles.content}
        refreshControl={
          <RefreshControl refreshing={refreshing} onRefresh={onRefresh} tintColor={colors.primary} />
        }
      >
        <View style={styles.header}>
          <Text style={styles.title}>My Categories</Text>
          <TouchableOpacity
            style={styles.addButton}
            onPress={() => setModalVisible(true)}
          >
            <Ionicons name="add" size={24} color={colors.white} />
          </TouchableOpacity>
        </View>

        <View style={styles.infoCard}>
          <Ionicons name="information-circle" size={24} color={colors.primary} />
          <Text style={styles.infoText}>
            Select categories with checkboxes to view their search results. Use AND/OR to combine!
          </Text>
        </View>

        {/* Category Selection Controls */}
        {categories.length > 0 && (
          <View style={styles.selectionControls}>
            <View style={styles.selectionHeader}>
              <Text style={styles.selectionTitle}>
                {selectedCategoryIds.size} of {categories.length} selected
              </Text>
              <View style={styles.selectionButtons}>
                <TouchableOpacity 
                  style={styles.selectAllButton}
                  onPress={selectAllCategories}
                >
                  <Text style={styles.selectAllText}>Select All</Text>
                </TouchableOpacity>
                <TouchableOpacity 
                  style={styles.clearButton}
                  onPress={clearAllSelections}
                >
                  <Text style={styles.clearText}>Clear</Text>
                </TouchableOpacity>
              </View>
            </View>

            {/* AND/OR Radio Buttons */}
            {selectedCategoryIds.size > 1 && (
              <View style={styles.combineModeContainer}>
                <Text style={styles.combineModeLabel}>Combine results with:</Text>
                <View style={styles.radioGroup}>
                  <TouchableOpacity 
                    style={[styles.radioButton, combineMode === 'or' && styles.radioButtonActive]}
                    onPress={() => setCombineMode('or')}
                  >
                    <View style={[styles.radioCircle, combineMode === 'or' && styles.radioCircleActive]} />
                    <Text style={[styles.radioText, combineMode === 'or' && styles.radioTextActive]}>
                      OR (Any category)
                    </Text>
                  </TouchableOpacity>
                  <TouchableOpacity 
                    style={[styles.radioButton, combineMode === 'and' && styles.radioButtonActive]}
                    onPress={() => setCombineMode('and')}
                  >
                    <View style={[styles.radioCircle, combineMode === 'and' && styles.radioCircleActive]} />
                    <Text style={[styles.radioText, combineMode === 'and' && styles.radioTextActive]}>
                      AND (All categories)
                    </Text>
                  </TouchableOpacity>
                </View>
              </View>
            )}
          </View>
        )}

        {/* Categories List with Checkboxes */}
        {categories.length === 0 ? (
          <View style={styles.emptyState}>
            <Ionicons name="folder-open-outline" size={80} color={colors.gray} />
            <Text style={styles.emptyText}>No Categories Yet</Text>
            <Text style={styles.emptySubtext}>
              Create your first category using InfoPilot 2.0 protocol format
            </Text>
            <CustomButton
              title="Create Category"
              onPress={() => setModalVisible(true)}
              style={styles.emptyButton}
            />
          </View>
        ) : (
          <View style={styles.categoriesList}>
            {categories.map((category) => {
              const isSelected = selectedCategoryIds.has(category.id);
              return (
                <View 
                  key={category.id} 
                  style={[styles.categoryCard, isSelected && styles.categoryCardSelected]}
                >
                  <View style={styles.categoryHeader}>
                    {/* Checkbox */}
                    <TouchableOpacity
                      style={styles.checkbox}
                      onPress={() => toggleCategorySelection(category.id)}
                    >
                      <Ionicons
                        name={isSelected ? 'checkbox' : 'square-outline'}
                        size={24}
                        color={isSelected ? colors.primary : colors.gray}
                      />
                    </TouchableOpacity>
                    
                    {/* Category Title - Clickable */}
                    <TouchableOpacity 
                      style={styles.categoryTitleRow}
                      onPress={() => handleViewCategory(category.id)}
                    >
                      <Ionicons
                        name={category.is_public ? 'globe' : 'lock-closed'}
                        size={20}
                        color={category.is_public ? colors.secondary : colors.gray}
                      />
                      <Text style={styles.categoryName}>{category.name}</Text>
                    </TouchableOpacity>
                    
                    {/* Delete Button */}
                    <TouchableOpacity
                      onPress={() => handleDeleteCategory(category.id, category.name)}
                    >
                      <Ionicons name="trash-outline" size={20} color={colors.error} />
                    </TouchableOpacity>
                  </View>
                  
                  <TouchableOpacity onPress={() => handleViewCategory(category.id)}>
                    <Text style={styles.protocolLabel}>Protocol:</Text>
                    <Text style={styles.protocolText} numberOfLines={2}>
                      {category.protocol}
                    </Text>
                    <View style={styles.categoryFooter}>
                      <Text style={styles.levelText}>Level {category.level}</Text>
                      <Text style={styles.statusText}>
                        {category.is_public ? 'Public' : 'Private'}
                      </Text>
                      <TouchableOpacity 
                        style={styles.viewResultsButton}
                        onPress={() => handleViewCategory(category.id)}
                      >
                        <Ionicons name="search" size={14} color={colors.white} />
                        <Text style={styles.viewResultsText}>View Results</Text>
                      </TouchableOpacity>
                    </View>
                  </TouchableOpacity>
                </View>
              );
            })}
          </View>
        )}

        {/* Search Results Section */}
        {resultsVisible && (
          <View style={styles.resultsSection}>
            <View style={styles.resultsHeader}>
              <Text style={styles.resultsTitle}>
                📊 Search Results ({searchResults.length})
              </Text>
              <Text style={styles.resultsSubtitle}>
                {selectedCategoryIds.size === 1 
                  ? `Results from 1 category`
                  : `Combined from ${selectedCategoryIds.size} categories (${combineMode.toUpperCase()})`
                }
              </Text>
            </View>

            {loadingResults ? (
              <View style={styles.loadingContainer}>
                <ActivityIndicator size="large" color={colors.primary} />
                <Text style={styles.loadingText}>Loading search results...</Text>
              </View>
            ) : searchResults.length === 0 ? (
              <View style={styles.noResults}>
                <Ionicons name="document-outline" size={48} color={colors.gray} />
                <Text style={styles.noResultsText}>No search results found</Text>
                <Text style={styles.noResultsSubtext}>
                  Go to the Search tab to collate results into this category!
                </Text>
              </View>
            ) : (
              <>
                {searchResults.map(renderSearchResult)}
                
                {/* Pagination */}
                {totalPages > 1 && (
                  <View style={styles.pagination}>
                    <TouchableOpacity 
                      style={[styles.pageButton, currentPage === 1 && styles.pageButtonDisabled]}
                      onPress={() => currentPage > 1 && setCurrentPage(currentPage - 1)}
                      disabled={currentPage === 1}
                    >
                      <Ionicons name="chevron-back" size={20} color={currentPage === 1 ? colors.gray : colors.primary} />
                    </TouchableOpacity>
                    <Text style={styles.pageText}>
                      Page {currentPage} of {totalPages}
                    </Text>
                    <TouchableOpacity 
                      style={[styles.pageButton, currentPage === totalPages && styles.pageButtonDisabled]}
                      onPress={() => currentPage < totalPages && setCurrentPage(currentPage + 1)}
                      disabled={currentPage === totalPages}
                    >
                      <Ionicons name="chevron-forward" size={20} color={currentPage === totalPages ? colors.gray : colors.primary} />
                    </TouchableOpacity>
                  </View>
                )}
              </>
            )}
          </View>
        )}
      </ScrollView>

      {/* Create Category Modal */}
      <Modal
        visible={modalVisible}
        animationType="slide"
        presentationStyle="pageSheet"
        onRequestClose={() => setModalVisible(false)}
      >
        <SafeAreaView style={styles.modalContainer}>
          <KeyboardAvoidingView
            behavior={Platform.OS === 'ios' ? 'padding' : 'height'}
            style={styles.keyboardView}
          >
            <View style={styles.modalHeader}>
              <Text style={styles.modalTitle}>Create Category</Text>
              <TouchableOpacity onPress={() => setModalVisible(false)}>
                <Ionicons name="close" size={28} color={colors.text} />
              </TouchableOpacity>
            </View>

            <ScrollView style={styles.modalContent}>
              <CustomInput
                label="Category Name"
                value={categoryName}
                onChangeText={setCategoryName}
                placeholder="e.g., American Civil War"
              />

              <CustomInput
                label="InfoPilot 2.0 Protocol"
                value={protocol}
                onChangeText={setProtocol}
                placeholder="(word1 or word2) & (word3 or word4)"
                multiline
                numberOfLines={4}
              />

              <Text style={styles.exampleLabel}>Example Protocol:</Text>
              <View style={styles.exampleBox}>
                <Text style={styles.exampleText}>
                  (American civil war) & (heroes or leadership)+ & (wasn't)^
                </Text>
              </View>
              
              <Text style={styles.infoLabel}>InfoPilot 2.0 Format:</Text>
              <Text style={styles.infoTextDetail}>
                • Use (word1 or word2) for OR within groups{'\n'}
                • Use & between groups for AND logic{'\n'}
                • Add + after () to require ALL terms{'\n'}
                • Add ^ after () to exclude ALL terms
              </Text>

              <TouchableOpacity
                style={styles.checkboxRow}
                onPress={() => setIsPublic(!isPublic)}
              >
                <Ionicons
                  name={isPublic ? 'checkbox' : 'square-outline'}
                  size={24}
                  color={colors.primary}
                />
                <Text style={styles.checkboxLabel}>Make this category public (list on Marketplace)</Text>
              </TouchableOpacity>

              <CustomButton
                title="Create Category"
                onPress={handleCreateCategory}
                loading={loading}
                style={styles.createButton}
              />
            </ScrollView>
          </KeyboardAvoidingView>
        </SafeAreaView>
      </Modal>
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
    paddingBottom: 40,
  },
  header: {
    flexDirection: 'row',
    justifyContent: 'space-between',
    alignItems: 'center',
    marginBottom: 20,
  },
  title: {
    fontSize: 28,
    fontWeight: 'bold',
    color: colors.text,
  },
  addButton: {
    backgroundColor: colors.primary,
    width: 44,
    height: 44,
    borderRadius: 22,
    justifyContent: 'center',
    alignItems: 'center',
  },
  infoCard: {
    flexDirection: 'row',
    backgroundColor: colors.cardBackground,
    padding: 16,
    borderRadius: 12,
    marginBottom: 20,
    borderWidth: 1,
    borderColor: colors.cardBorder,
  },
  infoText: {
    flex: 1,
    marginLeft: 12,
    fontSize: 14,
    color: colors.textLight,
  },
  // Selection Controls
  selectionControls: {
    backgroundColor: colors.cardBackground,
    padding: 16,
    borderRadius: 12,
    marginBottom: 20,
    borderWidth: 1,
    borderColor: colors.primary,
  },
  selectionHeader: {
    flexDirection: 'row',
    justifyContent: 'space-between',
    alignItems: 'center',
  },
  selectionTitle: {
    fontSize: 14,
    fontWeight: '600',
    color: colors.text,
  },
  selectionButtons: {
    flexDirection: 'row',
    gap: 12,
  },
  selectAllButton: {
    paddingHorizontal: 12,
    paddingVertical: 6,
    backgroundColor: colors.primary,
    borderRadius: 12,
  },
  selectAllText: {
    color: colors.white,
    fontSize: 12,
    fontWeight: '600',
  },
  clearButton: {
    paddingHorizontal: 12,
    paddingVertical: 6,
    backgroundColor: colors.gray,
    borderRadius: 12,
  },
  clearText: {
    color: colors.white,
    fontSize: 12,
    fontWeight: '600',
  },
  // AND/OR Radio Buttons
  combineModeContainer: {
    marginTop: 16,
    paddingTop: 16,
    borderTopWidth: 1,
    borderTopColor: colors.cardBorder,
  },
  combineModeLabel: {
    fontSize: 13,
    fontWeight: '600',
    color: colors.textMuted,
    marginBottom: 12,
  },
  radioGroup: {
    flexDirection: 'row',
    gap: 12,
  },
  radioButton: {
    flexDirection: 'row',
    alignItems: 'center',
    paddingHorizontal: 12,
    paddingVertical: 8,
    borderRadius: 20,
    borderWidth: 2,
    borderColor: colors.cardBorder,
    flex: 1,
  },
  radioButtonActive: {
    borderColor: colors.primary,
    backgroundColor: colors.primary + '20',
  },
  radioCircle: {
    width: 16,
    height: 16,
    borderRadius: 8,
    borderWidth: 2,
    borderColor: colors.gray,
    marginRight: 8,
  },
  radioCircleActive: {
    borderColor: colors.primary,
    backgroundColor: colors.primary,
  },
  radioText: {
    fontSize: 11,
    color: colors.textMuted,
    flex: 1,
  },
  radioTextActive: {
    color: colors.primary,
    fontWeight: '600',
  },
  // Categories List
  emptyState: {
    alignItems: 'center',
    paddingVertical: 60,
  },
  emptyText: {
    fontSize: 22,
    fontWeight: 'bold',
    color: colors.text,
    marginTop: 20,
  },
  emptySubtext: {
    fontSize: 16,
    color: colors.textLight,
    textAlign: 'center',
    marginTop: 8,
    paddingHorizontal: 40,
  },
  emptyButton: {
    marginTop: 24,
  },
  categoriesList: {
    gap: 16,
  },
  categoryCard: {
    backgroundColor: colors.cardBackground,
    padding: 16,
    borderRadius: 12,
    borderWidth: 2,
    borderColor: colors.cardBorder,
  },
  categoryCardSelected: {
    borderColor: colors.primary,
    backgroundColor: colors.primary + '10',
  },
  categoryHeader: {
    flexDirection: 'row',
    alignItems: 'center',
    marginBottom: 12,
  },
  checkbox: {
    marginRight: 8,
  },
  categoryTitleRow: {
    flexDirection: 'row',
    alignItems: 'center',
    flex: 1,
  },
  categoryName: {
    fontSize: 18,
    fontWeight: '600',
    color: colors.text,
    marginLeft: 8,
  },
  protocolLabel: {
    fontSize: 12,
    fontWeight: '600',
    color: colors.textMuted,
    marginBottom: 4,
  },
  protocolText: {
    fontSize: 14,
    color: colors.text,
    backgroundColor: colors.background,
    padding: 8,
    borderRadius: 6,
    fontFamily: Platform.OS === 'ios' ? 'Menlo' : 'monospace',
  },
  categoryFooter: {
    flexDirection: 'row',
    justifyContent: 'space-between',
    alignItems: 'center',
    marginTop: 12,
  },
  levelText: {
    fontSize: 12,
    color: colors.textMuted,
  },
  statusText: {
    fontSize: 12,
    fontWeight: '600',
    color: colors.secondary,
  },
  viewResultsButton: {
    flexDirection: 'row',
    alignItems: 'center',
    backgroundColor: colors.primary,
    paddingHorizontal: 12,
    paddingVertical: 6,
    borderRadius: 12,
    gap: 4,
  },
  viewResultsText: {
    color: colors.white,
    fontSize: 12,
    fontWeight: '600',
  },
  // Search Results Section
  resultsSection: {
    marginTop: 24,
    backgroundColor: colors.cardBackground,
    padding: 16,
    borderRadius: 12,
    borderWidth: 1,
    borderColor: colors.cardBorder,
  },
  resultsHeader: {
    marginBottom: 16,
    paddingBottom: 12,
    borderBottomWidth: 1,
    borderBottomColor: colors.cardBorder,
  },
  resultsTitle: {
    fontSize: 20,
    fontWeight: 'bold',
    color: colors.text,
  },
  resultsSubtitle: {
    fontSize: 13,
    color: colors.textMuted,
    marginTop: 4,
  },
  loadingContainer: {
    alignItems: 'center',
    paddingVertical: 40,
  },
  loadingText: {
    color: colors.textMuted,
    marginTop: 12,
  },
  noResults: {
    alignItems: 'center',
    paddingVertical: 40,
  },
  noResultsText: {
    fontSize: 16,
    fontWeight: '600',
    color: colors.text,
    marginTop: 12,
  },
  noResultsSubtext: {
    fontSize: 14,
    color: colors.textMuted,
    textAlign: 'center',
    marginTop: 8,
    paddingHorizontal: 20,
  },
  resultCard: {
    backgroundColor: colors.background,
    padding: 14,
    borderRadius: 10,
    marginBottom: 12,
    borderWidth: 1,
    borderColor: colors.cardBorder,
  },
  resultHeader: {
    flexDirection: 'row',
    alignItems: 'center',
    marginBottom: 8,
  },
  typeBadge: {
    backgroundColor: colors.secondary,
    paddingHorizontal: 8,
    paddingVertical: 3,
    borderRadius: 8,
    marginRight: 8,
  },
  typeBadgeText: {
    fontSize: 10,
    fontWeight: '600',
    color: colors.white,
  },
  yearText: {
    fontSize: 12,
    color: colors.textMuted,
  },
  resultTitle: {
    fontSize: 15,
    fontWeight: '600',
    color: colors.primary,
    marginBottom: 6,
  },
  resultSnippet: {
    fontSize: 13,
    color: colors.textLight,
    lineHeight: 18,
    marginBottom: 8,
  },
  resultFooter: {
    flexDirection: 'row',
    justifyContent: 'space-between',
    alignItems: 'center',
  },
  resultDomain: {
    fontSize: 11,
    color: colors.textMuted,
    flex: 1,
  },
  resultActions: {
    flexDirection: 'row',
    gap: 12,
  },
  actionButton: {
    flexDirection: 'row',
    alignItems: 'center',
    gap: 4,
  },
  actionText: {
    fontSize: 12,
    color: colors.primary,
  },
  // Pagination
  pagination: {
    flexDirection: 'row',
    justifyContent: 'center',
    alignItems: 'center',
    marginTop: 16,
    gap: 16,
  },
  pageButton: {
    padding: 8,
    borderRadius: 8,
    backgroundColor: colors.background,
  },
  pageButtonDisabled: {
    opacity: 0.5,
  },
  pageText: {
    fontSize: 14,
    color: colors.text,
  },
  // Modal Styles
  modalContainer: {
    flex: 1,
    backgroundColor: colors.background,
  },
  keyboardView: {
    flex: 1,
  },
  modalHeader: {
    flexDirection: 'row',
    justifyContent: 'space-between',
    alignItems: 'center',
    padding: 20,
    borderBottomWidth: 1,
    borderBottomColor: colors.cardBorder,
  },
  modalTitle: {
    fontSize: 24,
    fontWeight: 'bold',
    color: colors.text,
  },
  modalContent: {
    flex: 1,
    padding: 20,
  },
  exampleLabel: {
    fontSize: 14,
    fontWeight: '600',
    color: colors.text,
    marginBottom: 8,
  },
  exampleBox: {
    backgroundColor: colors.cardBackground,
    padding: 12,
    borderRadius: 8,
    marginBottom: 16,
    borderWidth: 1,
    borderColor: colors.cardBorder,
  },
  exampleText: {
    fontSize: 14,
    color: colors.text,
    fontFamily: Platform.OS === 'ios' ? 'Menlo' : 'monospace',
  },
  infoLabel: {
    fontSize: 13,
    fontWeight: '600',
    color: colors.primary,
    marginBottom: 8,
  },
  infoTextDetail: {
    fontSize: 12,
    color: colors.textMuted,
    lineHeight: 18,
    marginBottom: 20,
  },
  checkboxRow: {
    flexDirection: 'row',
    alignItems: 'center',
    marginBottom: 24,
  },
  checkboxLabel: {
    fontSize: 16,
    color: colors.text,
    marginLeft: 12,
    flex: 1,
  },
  createButton: {
    marginBottom: 20,
  },
});
