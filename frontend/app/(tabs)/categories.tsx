import React, { useState, useEffect } from 'react';
import {
  View,
  Text,
  TouchableOpacity,
  StyleSheet,
  FlatList,
  TextInput,
  Alert,
  ActivityIndicator,
  ScrollView,
} from 'react-native';
import { Ionicons } from '@expo/vector-icons';
import { useAuthStore } from '../../store/authStore';
import Modal from 'react-native-modal';
import axios from 'axios';

const API_URL = process.env.EXPO_PUBLIC_BACKEND_URL;

export default function CategoriesScreen() {
  const { user, token } = useAuthStore();
  const [categories, setCategories] = useState([]);
  const [protocols, setProtocols] = useState([]);
  const [loading, setLoading] = useState(false);
  const [showCategoryModal, setShowCategoryModal] = useState(false);
  const [showProtocolModal, setShowProtocolModal] = useState(false);
  const [selectedCategory, setSelectedCategory] = useState(null);
  
  // Form states
  const [categoryName, setCategoryName] = useState('');
  const [categoryLevel, setCategoryLevel] = useState(0);
  const [isPublic, setIsPublic] = useState(true);
  const [protocolName, setProtocolName] = useState('');
  const [protocolExpression, setProtocolExpression] = useState('');

  useEffect(() => {
    loadData();
  }, []);

  const loadData = async () => {
    setLoading(true);
    try {
      const headers = { Authorization: `Bearer ${token}` };
      const [catRes, protoRes] = await Promise.all([
        axios.get(`${API_URL}/api/categories`, { headers }),
        axios.get(`${API_URL}/api/protocols`, { headers }),
      ]);
      setCategories(catRes.data.categories || []);
      setProtocols(protoRes.data.protocols || []);
    } catch (error) {
      console.error('Load error:', error);
    }
    setLoading(false);
  };

  const handleCreateCategory = async () => {
    if (!categoryName.trim()) {
      Alert.alert('Error', 'Please enter a category name');
      return;
    }

    setLoading(true);
    try {
      await axios.post(
        `${API_URL}/api/categories`,
        {
          name: categoryName,
          level: categoryLevel,
          parentId: null,
          userId: user?.id,
          isPublic,
        },
        { headers: { Authorization: `Bearer ${token}` } }
      );
      Alert.alert('Success', 'Category created successfully');
      setCategoryName('');
      setCategoryLevel(0);
      setShowCategoryModal(false);
      loadData();
    } catch (error) {
      Alert.alert('Error', 'Failed to create category');
    }
    setLoading(false);
  };

  const handleCreateProtocol = async () => {
    if (!protocolName.trim() || !protocolExpression.trim()) {
      Alert.alert('Error', 'Please fill in all protocol fields');
      return;
    }

    if (!selectedCategory) {
      Alert.alert('Error', 'Please select a category first');
      return;
    }

    setLoading(true);
    try {
      await axios.post(
        `${API_URL}/api/protocols`,
        {
          name: protocolName,
          booleanExpression: protocolExpression,
          categoryId: selectedCategory.id,
          userId: user?.id,
          isPublic,
        },
        { headers: { Authorization: `Bearer ${token}` } }
      );
      Alert.alert('Success', 'Protocol created successfully');
      setProtocolName('');
      setProtocolExpression('');
      setShowProtocolModal(false);
      setSelectedCategory(null);
      loadData();
    } catch (error) {
      Alert.alert('Error', 'Failed to create protocol');
    }
    setLoading(false);
  };

  const handleDeleteCategory = (categoryId: string) => {
    Alert.alert(
      'Delete Category',
      'Are you sure you want to delete this category?',
      [
        { text: 'Cancel', style: 'cancel' },
        {
          text: 'Delete',
          style: 'destructive',
          onPress: async () => {
            try {
              await axios.delete(`${API_URL}/api/categories/${categoryId}`, {
                headers: { Authorization: `Bearer ${token}` },
              });
              loadData();
            } catch (error) {
              Alert.alert('Error', 'Failed to delete category');
            }
          },
        },
      ]
    );
  };

  const renderCategory = ({ item }: any) => {
    const categoryProtocol = protocols.find(p => p.categoryId === item.id);
    
    return (
      <View style={styles.categoryCard}>
        <View style={styles.categoryHeader}>
          <View style={styles.categoryLeft}>
            <Ionicons name="folder" size={24} color="#1E88E5" />
            <View style={styles.categoryInfo}>
              <Text style={styles.categoryName}>{item.name}</Text>
              <Text style={styles.categoryMeta}>
                Level {item.level} • {item.isPublic ? 'Public' : 'Private'}
              </Text>
            </View>
          </View>
          <TouchableOpacity
            onPress={() => handleDeleteCategory(item.id)}
            style={styles.deleteButton}
          >
            <Ionicons name="trash" size={20} color="#F44336" />
          </TouchableOpacity>
        </View>

        {categoryProtocol ? (
          <View style={styles.protocolInfo}>
            <Text style={styles.protocolLabel}>Protocol:</Text>
            <Text style={styles.protocolText} numberOfLines={2}>
              {categoryProtocol.booleanExpression}
            </Text>
          </View>
        ) : (
          <TouchableOpacity
            style={styles.addProtocolButton}
            onPress={() => {
              setSelectedCategory(item);
              setShowProtocolModal(true);
            }}
          >
            <Ionicons name="add" size={16} color="#1E88E5" />
            <Text style={styles.addProtocolText}>Add Protocol</Text>
          </TouchableOpacity>
        )}
      </View>
    );
  };

  return (
    <View style={styles.container}>
      {/* Header */}
      <View style={styles.header}>
        <Text style={styles.headerTitle}>My Categories</Text>
        <TouchableOpacity
          style={styles.addButton}
          onPress={() => setShowCategoryModal(true)}
        >
          <Ionicons name="add" size={24} color="#FFF" />
        </TouchableOpacity>
      </View>

      {/* Instructions */}
      <View style={styles.instructionCard}>
        <Ionicons name="information-circle" size={20} color="#1E88E5" />
        <Text style={styles.instructionText}>
          Create categories and define search protocols using InfoJet 2.0
          Boolean language
        </Text>
      </View>

      {/* Categories List */}
      {loading ? (
        <ActivityIndicator size="large" color="#1E88E5" style={styles.loader} />
      ) : (
        <FlatList
          data={categories}
          renderItem={renderCategory}
          keyExtractor={(item) => item.id}
          contentContainerStyle={styles.list}
          ListEmptyComponent=(
            <View style={styles.emptyState}>
              <Ionicons name="folder-open" size={64} color="#CCC" />
              <Text style={styles.emptyText}>No categories yet</Text>
              <Text style={styles.emptySubtext}>
                Tap the + button to create your first category
              </Text>
            </View>
          )
        />
      )}

      {/* Create Category Modal */}
      <Modal
        isVisible={showCategoryModal}
        onBackdropPress={() => setShowCategoryModal(false)}
        style={styles.modal}
      >
        <View style={styles.modalContent}>
          <Text style={styles.modalTitle}>Create Category</Text>

          <TextInput
            style={styles.input}
            placeholder="Category Name"
            value={categoryName}
            onChangeText={setCategoryName}
          />

          <TextInput
            style={styles.input}
            placeholder="Level (0 for root)"
            value={String(categoryLevel)}
            onChangeText={(text) => setCategoryLevel(Number(text) || 0)}
            keyboardType="numeric"
          />

          <TouchableOpacity
            style={styles.toggleButton}
            onPress={() => setIsPublic(!isPublic)}
          >
            <Ionicons
              name={isPublic ? 'checkbox' : 'square-outline'}
              size={24}
              color="#1E88E5"
            />
            <Text style={styles.toggleText}>Make Public</Text>
          </TouchableOpacity>

          <View style={styles.modalButtons}>
            <TouchableOpacity
              style={[styles.modalButton, styles.cancelButton]}
              onPress={() => setShowCategoryModal(false)}
            >
              <Text style={styles.cancelButtonText}>Cancel</Text>
            </TouchableOpacity>
            <TouchableOpacity
              style={[styles.modalButton, styles.createButton]}
              onPress={handleCreateCategory}
            >
              <Text style={styles.createButtonText}>Create</Text>
            </TouchableOpacity>
          </View>
        </View>
      </Modal>

      {/* Create Protocol Modal */}
      <Modal
        isVisible={showProtocolModal}
        onBackdropPress={() => setShowProtocolModal(false)}
        style={styles.modal}
      >
        <View style={styles.modalContent}>
          <Text style={styles.modalTitle}>Create Protocol</Text>
          <Text style={styles.modalSubtitle}>
            For: {selectedCategory?.name}
          </Text>

          <TextInput
            style={styles.input}
            placeholder="Protocol Name"
            value={protocolName}
            onChangeText={setProtocolName}
          />

          <TextInput
            style={[styles.input, styles.textArea]}
            placeholder="Boolean Expression&#10;Example: (AI or artificial intelligence) & (machine learning)+"
            value={protocolExpression}
            onChangeText={setProtocolExpression}
            multiline
            numberOfLines={4}
          />

          <View style={styles.protocolHelp}>
            <Text style={styles.protocolHelpTitle}>InfoJet 2.0 Syntax:</Text>
            <Text style={styles.protocolHelpText}>• Use ( ) for grouping</Text>
            <Text style={styles.protocolHelpText}>• Use 'or' between terms</Text>
            <Text style={styles.protocolHelpText}>• Use '&' to require all groups</Text>
            <Text style={styles.protocolHelpText}>• Use '+' for must include</Text>
            <Text style={styles.protocolHelpText}>• Use '^' for exclusion</Text>
          </View>

          <View style={styles.modalButtons}>
            <TouchableOpacity
              style={[styles.modalButton, styles.cancelButton]}
              onPress={() => {
                setShowProtocolModal(false);
                setSelectedCategory(null);
              }}
            >
              <Text style={styles.cancelButtonText}>Cancel</Text>
            </TouchableOpacity>
            <TouchableOpacity
              style={[styles.modalButton, styles.createButton]}
              onPress={handleCreateProtocol}
            >
              <Text style={styles.createButtonText}>Create</Text>
            </TouchableOpacity>
          </View>
        </View>
      </Modal>
    </View>
  );
}

const styles = StyleSheet.create({
  container: {
    flex: 1,
    backgroundColor: '#F5F9FC',
  },
  header: {
    flexDirection: 'row',
    justifyContent: 'space-between',
    alignItems: 'center',
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
  addButton: {
    backgroundColor: '#1E88E5',
    width: 44,
    height: 44,
    borderRadius: 22,
    justifyContent: 'center',
    alignItems: 'center',
  },
  instructionCard: {
    flexDirection: 'row',
    alignItems: 'center',
    backgroundColor: '#E3F2FD',
    padding: 12,
    marginHorizontal: 16,
    marginTop: 16,
    borderRadius: 12,
    gap: 8,
  },
  instructionText: {
    flex: 1,
    fontSize: 13,
    color: '#1565C0',
    lineHeight: 18,
  },
  list: {
    padding: 16,
  },
  loader: {
    marginTop: 40,
  },
  categoryCard: {
    backgroundColor: '#FFF',
    borderRadius: 12,
    padding: 16,
    marginBottom: 12,
    borderWidth: 1,
    borderColor: '#E0E0E0',
  },
  categoryHeader: {
    flexDirection: 'row',
    justifyContent: 'space-between',
    alignItems: 'center',
    marginBottom: 12,
  },
  categoryLeft: {
    flexDirection: 'row',
    alignItems: 'center',
    flex: 1,
    gap: 12,
  },
  categoryInfo: {
    flex: 1,
  },
  categoryName: {
    fontSize: 16,
    fontWeight: '600',
    color: '#212121',
  },
  categoryMeta: {
    fontSize: 12,
    color: '#999',
    marginTop: 2,
  },
  deleteButton: {
    padding: 8,
  },
  protocolInfo: {
    backgroundColor: '#F5F5F5',
    padding: 12,
    borderRadius: 8,
  },
  protocolLabel: {
    fontSize: 12,
    color: '#666',
    marginBottom: 4,
  },
  protocolText: {
    fontSize: 13,
    color: '#212121',
    fontFamily: Platform.OS === 'ios' ? 'Courier' : 'monospace',
  },
  addProtocolButton: {
    flexDirection: 'row',
    alignItems: 'center',
    justifyContent: 'center',
    padding: 8,
    gap: 4,
  },
  addProtocolText: {
    color: '#1E88E5',
    fontSize: 14,
    fontWeight: '600',
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
    paddingHorizontal: 40,
  },
  modal: {
    justifyContent: 'flex-end',
    margin: 0,
  },
  modalContent: {
    backgroundColor: '#FFF',
    borderTopLeftRadius: 20,
    borderTopRightRadius: 20,
    padding: 24,
    maxHeight: '80%',
  },
  modalTitle: {
    fontSize: 24,
    fontWeight: 'bold',
    color: '#212121',
    marginBottom: 8,
  },
  modalSubtitle: {
    fontSize: 14,
    color: '#666',
    marginBottom: 16,
  },
  input: {
    backgroundColor: '#F5F5F5',
    borderRadius: 12,
    padding: 16,
    fontSize: 16,
    marginBottom: 12,
  },
  textArea: {
    minHeight: 100,
    textAlignVertical: 'top',
  },
  toggleButton: {
    flexDirection: 'row',
    alignItems: 'center',
    paddingVertical: 12,
    gap: 8,
  },
  toggleText: {
    fontSize: 16,
    color: '#212121',
  },
  protocolHelp: {
    backgroundColor: '#F5F5F5',
    padding: 12,
    borderRadius: 8,
    marginBottom: 16,
  },
  protocolHelpTitle: {
    fontSize: 14,
    fontWeight: '600',
    color: '#212121',
    marginBottom: 8,
  },
  protocolHelpText: {
    fontSize: 12,
    color: '#666',
    lineHeight: 18,
  },
  modalButtons: {
    flexDirection: 'row',
    gap: 12,
  },
  modalButton: {
    flex: 1,
    padding: 16,
    borderRadius: 12,
    alignItems: 'center',
  },
  cancelButton: {
    backgroundColor: '#F5F5F5',
  },
  createButton: {
    backgroundColor: '#1E88E5',
  },
  cancelButtonText: {
    color: '#666',
    fontSize: 16,
    fontWeight: '600',
  },
  createButtonText: {
    color: '#FFF',
    fontSize: 16,
    fontWeight: '600',
  },
});
