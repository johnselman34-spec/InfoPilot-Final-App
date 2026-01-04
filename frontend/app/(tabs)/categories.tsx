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
  Modal,
} from 'react-native';
import { SafeAreaView } from 'react-native-safe-area-context';
import { Ionicons } from '@expo/vector-icons';
import { api } from '../../src/services/api';

interface Category {
  id: string;
  name: string;
  protocol: string;
  is_public: boolean;
  level: number;
  parent_id?: string;
}

export default function CategoriesScreen() {
  const [categories, setCategories] = useState<Category[]>([]);
  const [loading, setLoading] = useState(true);
  const [modalVisible, setModalVisible] = useState(false);
  const [editingCategory, setEditingCategory] = useState<Category | null>(null);
  const [name, setName] = useState('');
  const [protocol, setProtocol] = useState('');
  const [isPublic, setIsPublic] = useState(false);
  const [parentId, setParentId] = useState<string | null>(null);
  const [saving, setSaving] = useState(false);

  useEffect(() => {
    loadCategories();
  }, []);

  const loadCategories = async () => {
    try {
      const data = await api.get('/categories');
      setCategories(data);
    } catch (error) {
      console.error('Error loading categories:', error);
    } finally {
      setLoading(false);
    }
  };

  const openCreateModal = (parent?: Category) => {
    setEditingCategory(null);
    setName('');
    setProtocol('');
    setIsPublic(false);
    setParentId(parent?.id || null);
    setModalVisible(true);
  };

  const openEditModal = (category: Category) => {
    setEditingCategory(category);
    setName(category.name);
    setProtocol(category.protocol);
    setIsPublic(category.is_public);
    setParentId(category.parent_id || null);
    setModalVisible(true);
  };

  const handleSave = async () => {
    if (!name.trim()) {
      Alert.alert('Error', 'Please enter a category name');
      return;
    }
    if (!protocol.trim()) {
      Alert.alert('Error', 'Please enter a protocol');
      return;
    }

    setSaving(true);
    try {
      if (editingCategory) {
        await api.put(`/categories/${editingCategory.id}`, {
          name: name.trim(),
          protocol: protocol.trim(),
          is_public: isPublic,
        });
        Alert.alert('Success', 'Category updated!');
      } else {
        await api.post('/categories', {
          name: name.trim(),
          protocol: protocol.trim(),
          is_public: isPublic,
          parent_id: parentId,
        });
        Alert.alert('Success', 'Category created!');
      }
      setModalVisible(false);
      loadCategories();
    } catch (error: any) {
      Alert.alert('Error', error.response?.data?.detail || 'Could not save category');
    } finally {
      setSaving(false);
    }
  };

  const handleDelete = (category: Category) => {
    Alert.alert(
      'Delete Category',
      `Are you sure you want to delete "${category.name}" and all its subcategories?`,
      [
        { text: 'Cancel', style: 'cancel' },
        {
          text: 'Delete',
          style: 'destructive',
          onPress: async () => {
            try {
              await api.delete(`/categories/${category.id}`);
              loadCategories();
            } catch (error: any) {
              Alert.alert('Error', error.response?.data?.detail || 'Could not delete category');
            }
          },
        },
      ]
    );
  };

  const buildHierarchy = (cats: Category[]): Category[] => {
    const rootCats = cats.filter(c => !c.parent_id);
    return rootCats.sort((a, b) => a.name.localeCompare(b.name));
  };

  const getChildren = (parentId: string): Category[] => {
    return categories.filter(c => c.parent_id === parentId).sort((a, b) => a.name.localeCompare(b.name));
  };

  const renderCategory = (category: Category, depth: number = 0) => {
    const children = getChildren(category.id);
    
    return (
      <View key={category.id}>
        <View style={[styles.categoryCard, { marginLeft: depth * 16 }]}>
          <View style={styles.categoryHeader}>
            <View style={styles.categoryInfo}>
              <View style={styles.levelIndicator}>
                <Text style={styles.levelText}>L{category.level}</Text>
              </View>
              <View style={styles.categoryDetails}>
                <View style={styles.categoryNameRow}>
                  <Text style={styles.categoryName}>{category.name}</Text>
                  {category.is_public && (
                    <View style={styles.publicBadge}>
                      <Ionicons name="globe" size={10} color="#4CAF50" />
                      <Text style={styles.publicText}>Public</Text>
                    </View>
                  )}
                </View>
                <Text style={styles.protocolText} numberOfLines={2}>
                  {category.protocol}
                </Text>
              </View>
            </View>
            <View style={styles.categoryActions}>
              <TouchableOpacity
                style={styles.actionButton}
                onPress={() => openCreateModal(category)}
              >
                <Ionicons name="add" size={18} color="#2196F3" />
              </TouchableOpacity>
              <TouchableOpacity
                style={styles.actionButton}
                onPress={() => openEditModal(category)}
              >
                <Ionicons name="pencil" size={16} color="#666" />
              </TouchableOpacity>
              <TouchableOpacity
                style={styles.actionButton}
                onPress={() => handleDelete(category)}
              >
                <Ionicons name="trash" size={16} color="#f44336" />
              </TouchableOpacity>
            </View>
          </View>
        </View>
        {children.map(child => renderCategory(child, depth + 1))}
      </View>
    );
  };

  const parentName = parentId
    ? categories.find(c => c.id === parentId)?.name
    : null;

  return (
    <SafeAreaView style={styles.container} edges={['top']}>
      {/* Header */}
      <View style={styles.header}>
        <View>
          <Text style={styles.headerTitle}>Categories & Protocols</Text>
          <Text style={styles.sectionTitle}>InfoPilot 2.0 Boolean Language</Text>
        </View>
        <TouchableOpacity
          style={styles.addButton}
          onPress={() => openCreateModal()}
        >
          <Ionicons name="add" size={24} color="#fff" />
        </TouchableOpacity>
      </View>

      {/* Protocol Help */}
      <View style={styles.helpCard}>
        <Text style={styles.helpTitle}>Protocol Format:</Text>
        <Text style={styles.helpText}>
          (word1 or word2) & (word3 or word4){`+`} & (exclude1)^
        </Text>
        <Text style={styles.helpDesc}>
          • Words in parentheses with "or" = any match{"\n"}
          • & = AND (all groups must match){"\n"}
          • + = Include ALL words in group{"\n"}
          • ^ = EXCLUDE all words in group
        </Text>
      </View>

      {/* Categories List */}
      <ScrollView style={styles.categoriesList}>
        {loading ? (
          <ActivityIndicator size="large" color="#2196F3" style={styles.loader} />
        ) : categories.length === 0 ? (
          <View style={styles.emptyState}>
            <Ionicons name="folder-open-outline" size={64} color="#ccc" />
            <Text style={styles.emptyTitle}>No Categories Yet</Text>
            <Text style={styles.emptyText}>
              Create your first category with an InfoJet 2.0 protocol to start
              organizing your search results!
            </Text>
            <TouchableOpacity style={styles.createFirstButton} onPress={() => openCreateModal()}>
              <Ionicons name="add" size={20} color="#fff" />
              <Text style={styles.createFirstText}>Create First Category</Text>
            </TouchableOpacity>
          </View>
        ) : (
          buildHierarchy(categories).map(cat => renderCategory(cat))
        )}
      </ScrollView>

      {/* Create/Edit Modal */}
      <Modal
        visible={modalVisible}
        animationType="slide"
        presentationStyle="pageSheet"
        onRequestClose={() => setModalVisible(false)}
      >
        <SafeAreaView style={styles.modalContainer}>
          <View style={styles.modalHeader}>
            <TouchableOpacity onPress={() => setModalVisible(false)}>
              <Text style={styles.cancelText}>Cancel</Text>
            </TouchableOpacity>
            <Text style={styles.modalTitle}>
              {editingCategory ? 'Edit Category' : 'New Category'}
            </Text>
            <TouchableOpacity onPress={handleSave} disabled={saving}>
              {saving ? (
                <ActivityIndicator size="small" color="#2196F3" />
              ) : (
                <Text style={styles.saveText}>Save</Text>
              )}
            </TouchableOpacity>
          </View>

          <ScrollView style={styles.modalContent}>
            {parentName && (
              <View style={styles.parentInfo}>
                <Ionicons name="folder" size={16} color="#666" />
                <Text style={styles.parentText}>Subcategory of: {parentName}</Text>
              </View>
            )}

            <Text style={styles.label}>Category Name</Text>
            <TextInput
              style={styles.input}
              placeholder="e.g., American Civil War"
              placeholderTextColor="#999"
              value={name}
              onChangeText={setName}
            />

            <Text style={styles.label}>Protocol (InfoJet 2.0)</Text>
            <TextInput
              style={[styles.input, styles.protocolInput]}
              placeholder="(word1 or word2) & (word3)+ & (exclude)^"
              placeholderTextColor="#999"
              value={protocol}
              onChangeText={setProtocol}
              multiline
            />

            {/* Protocol Examples */}
            <View style={styles.examplesCard}>
              <Text style={styles.examplesTitle}>Examples:</Text>
              <TouchableOpacity
                style={styles.exampleItem}
                onPress={() =>
                  setProtocol(
                    '(American civil war) & (civil war) & (1860 or 1861 or 1862 or 1863 or 1864 or 1865)+'
                  )
                }
              >
                <Text style={styles.exampleText}>
                  American Civil War - Basic
                </Text>
              </TouchableOpacity>
              <TouchableOpacity
                style={styles.exampleItem}
                onPress={() =>
                  setProtocol(
                    '(heroically or hero or helped solve) & (good citizen or citizenship) & (Gettysburg or Princeton) & (isn\'t or wasn\'t)^'
                  )
                }
              >
                <Text style={styles.exampleText}>
                  Heroes - With Exclusion
                </Text>
              </TouchableOpacity>
              <TouchableOpacity
                style={styles.exampleItem}
                onPress={() =>
                  setProtocol(
                    '(William Gamble or General Gamble) & (Civil War or 1863) & (U.S. Army or army) & (Gettysburg)+'
                  )
                }
              >
                <Text style={styles.exampleText}>
                  Specific Person - With Inclusion
                </Text>
              </TouchableOpacity>
            </View>

            {/* Public Toggle */}
            <TouchableOpacity
              style={styles.publicToggle}
              onPress={() => setIsPublic(!isPublic)}
            >
              <View style={[styles.checkbox, isPublic && styles.checkboxChecked]}>
                {isPublic && <Ionicons name="checkmark" size={14} color="#fff" />}
              </View>
              <View style={styles.publicToggleText}>
                <Text style={styles.publicToggleLabel}>Make Public</Text>
                <Text style={styles.publicToggleDesc}>
                  Other users can see and use this category
                </Text>
              </View>
            </TouchableOpacity>

            {/* Privacy Notice */}
            <View style={styles.privacyNotice}>
              <Ionicons name="shield-checkmark" size={16} color="#4CAF50" />
              <Text style={styles.privacyText}>
                We encourage you to keep your categories private for security.
              </Text>
            </View>
          </ScrollView>
        </SafeAreaView>
      </Modal>
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
  headerTitle: {
    fontSize: 20,
    fontWeight: 'bold',
    color: '#333',
  },
  headerSubtitle: {
    fontSize: 12,
    color: '#4CAF50',
    marginTop: 2,
  },
  addButton: {
    width: 44,
    height: 44,
    borderRadius: 22,
    backgroundColor: '#2196F3',
    alignItems: 'center',
    justifyContent: 'center',
  },
  helpCard: {
    backgroundColor: '#E3F2FD',
    marginHorizontal: 16,
    marginTop: 12,
    borderRadius: 12,
    padding: 12,
  },
  helpTitle: {
    fontSize: 13,
    fontWeight: '600',
    color: '#1976D2',
    marginBottom: 4,
  },
  helpText: {
    fontSize: 12,
    fontFamily: 'monospace',
    color: '#1976D2',
    backgroundColor: '#fff',
    padding: 8,
    borderRadius: 6,
    marginBottom: 8,
  },
  helpDesc: {
    fontSize: 11,
    color: '#666',
    lineHeight: 16,
  },
  categoriesList: {
    flex: 1,
    padding: 16,
  },
  loader: {
    marginTop: 40,
  },
  emptyState: {
    alignItems: 'center',
    paddingTop: 40,
    paddingHorizontal: 32,
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
  createFirstButton: {
    flexDirection: 'row',
    alignItems: 'center',
    backgroundColor: '#2196F3',
    paddingHorizontal: 20,
    paddingVertical: 12,
    borderRadius: 24,
    marginTop: 20,
  },
  createFirstText: {
    color: '#fff',
    fontSize: 15,
    fontWeight: '600',
    marginLeft: 8,
  },
  categoryCard: {
    backgroundColor: '#fff',
    borderRadius: 12,
    padding: 12,
    marginBottom: 10,
    borderWidth: 1,
    borderColor: '#E0E0E0',
  },
  categoryHeader: {
    flexDirection: 'row',
    justifyContent: 'space-between',
  },
  categoryInfo: {
    flex: 1,
    flexDirection: 'row',
  },
  levelIndicator: {
    width: 28,
    height: 28,
    borderRadius: 14,
    backgroundColor: '#E3F2FD',
    alignItems: 'center',
    justifyContent: 'center',
    marginRight: 10,
  },
  levelText: {
    fontSize: 10,
    fontWeight: '600',
    color: '#1976D2',
  },
  categoryDetails: {
    flex: 1,
  },
  categoryNameRow: {
    flexDirection: 'row',
    alignItems: 'center',
    flexWrap: 'wrap',
  },
  categoryName: {
    fontSize: 15,
    fontWeight: '600',
    color: '#333',
    marginRight: 8,
  },
  publicBadge: {
    flexDirection: 'row',
    alignItems: 'center',
    backgroundColor: '#E8F5E9',
    paddingHorizontal: 6,
    paddingVertical: 2,
    borderRadius: 8,
  },
  publicText: {
    fontSize: 10,
    color: '#4CAF50',
    marginLeft: 3,
  },
  protocolText: {
    fontSize: 11,
    color: '#666',
    marginTop: 4,
    fontFamily: 'monospace',
  },
  categoryActions: {
    flexDirection: 'row',
  },
  actionButton: {
    padding: 6,
    marginLeft: 4,
  },
  modalContainer: {
    flex: 1,
    backgroundColor: '#FFFFF0',
  },
  modalHeader: {
    flexDirection: 'row',
    justifyContent: 'space-between',
    alignItems: 'center',
    paddingHorizontal: 16,
    paddingVertical: 14,
    borderBottomWidth: 1,
    borderBottomColor: '#E0E0E0',
    backgroundColor: '#fff',
  },
  cancelText: {
    fontSize: 16,
    color: '#666',
  },
  modalTitle: {
    fontSize: 17,
    fontWeight: '600',
    color: '#333',
  },
  saveText: {
    fontSize: 16,
    color: '#2196F3',
    fontWeight: '600',
  },
  modalContent: {
    flex: 1,
    padding: 16,
  },
  parentInfo: {
    flexDirection: 'row',
    alignItems: 'center',
    backgroundColor: '#F5F5F5',
    padding: 10,
    borderRadius: 8,
    marginBottom: 16,
  },
  parentText: {
    fontSize: 13,
    color: '#666',
    marginLeft: 8,
  },
  label: {
    fontSize: 14,
    fontWeight: '600',
    color: '#333',
    marginBottom: 8,
  },
  input: {
    backgroundColor: '#fff',
    borderRadius: 10,
    paddingHorizontal: 14,
    paddingVertical: 12,
    fontSize: 15,
    color: '#333',
    borderWidth: 1,
    borderColor: '#E0E0E0',
    marginBottom: 16,
  },
  protocolInput: {
    minHeight: 80,
    textAlignVertical: 'top',
  },
  examplesCard: {
    backgroundColor: '#F5F5F5',
    borderRadius: 10,
    padding: 12,
    marginBottom: 16,
  },
  examplesTitle: {
    fontSize: 13,
    fontWeight: '600',
    color: '#666',
    marginBottom: 8,
  },
  exampleItem: {
    backgroundColor: '#fff',
    padding: 10,
    borderRadius: 8,
    marginBottom: 6,
  },
  exampleText: {
    fontSize: 12,
    color: '#2196F3',
  },
  publicToggle: {
    flexDirection: 'row',
    alignItems: 'center',
    marginBottom: 16,
  },
  checkbox: {
    width: 24,
    height: 24,
    borderRadius: 6,
    borderWidth: 2,
    borderColor: '#2196F3',
    alignItems: 'center',
    justifyContent: 'center',
    marginRight: 12,
  },
  checkboxChecked: {
    backgroundColor: '#2196F3',
  },
  publicToggleText: {
    flex: 1,
  },
  publicToggleLabel: {
    fontSize: 15,
    fontWeight: '500',
    color: '#333',
  },
  publicToggleDesc: {
    fontSize: 12,
    color: '#666',
    marginTop: 2,
  },
  privacyNotice: {
    flexDirection: 'row',
    alignItems: 'center',
    backgroundColor: '#E8F5E9',
    padding: 12,
    borderRadius: 10,
  },
  privacyText: {
    flex: 1,
    fontSize: 12,
    color: '#4CAF50',
    marginLeft: 8,
    fontStyle: 'italic',
  },
});
