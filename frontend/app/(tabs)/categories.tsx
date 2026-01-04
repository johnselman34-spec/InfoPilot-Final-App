import React, { useEffect, useState } from 'react';
import { View, Text, StyleSheet, ScrollView, TouchableOpacity, RefreshControl, Alert, Modal, KeyboardAvoidingView, Platform } from 'react-native';
import { SafeAreaView } from 'react-native-safe-area-context';
import { Ionicons } from '@expo/vector-icons';
import { useCategoryStore } from '../../src/store/categoryStore';
import { colors } from '../../src/utils/colors';
import { CustomInput } from '../../src/components/CustomInput';
import { CustomButton } from '../../src/components/CustomButton';

export default function CategoriesScreen() {
  const { categories, fetchCategories, createCategory, deleteCategory, isLoading } = useCategoryStore();
  const [refreshing, setRefreshing] = useState(false);
  const [modalVisible, setModalVisible] = useState(false);
  const [categoryName, setCategoryName] = useState('');
  const [protocol, setProtocol] = useState('');
  const [isPublic, setIsPublic] = useState(true);
  const [loading, setLoading] = useState(false);

  useEffect(() => {
    fetchCategories();
  }, []);

  const onRefresh = async () => {
    setRefreshing(true);
    await fetchCategories();
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
      Alert.alert('Success', 'Category created successfully');
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
              Alert.alert('Success', 'Category deleted');
            } catch (error: any) {
              Alert.alert('Error', error.message);
            }
          },
        },
      ]
    );
  };

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
            Create categories with InfoJet 2.0 protocols to organize your searches
          </Text>
        </View>

        {categories.length === 0 ? (
          <View style={styles.emptyState}>
            <Ionicons name="folder-open-outline" size={80} color={colors.gray} />
            <Text style={styles.emptyText}>No Categories Yet</Text>
            <Text style={styles.emptySubtext}>
              Create your first category using InfoJet 2.0 protocol format
            </Text>
            <CustomButton
              title="Create Category"
              onPress={() => setModalVisible(true)}
              style={styles.emptyButton}
            />
          </View>
        ) : (
          <View style={styles.categoriesList}>
            {categories.map((category) => (
              <View key={category.id} style={styles.categoryCard}>
                <View style={styles.categoryHeader}>
                  <View style={styles.categoryTitleRow}>
                    <Ionicons
                      name={category.is_public ? 'globe' : 'lock-closed'}
                      size={20}
                      color={category.is_public ? colors.secondary : colors.gray}
                    />
                    <Text style={styles.categoryName}>{category.name}</Text>
                  </View>
                  <TouchableOpacity
                    onPress={() => handleDeleteCategory(category.id, category.name)}
                  >
                    <Ionicons name="trash-outline" size={20} color={colors.error} />
                  </TouchableOpacity>
                </View>
                <Text style={styles.protocolLabel}>Protocol:</Text>
                <Text style={styles.protocolText} numberOfLines={2}>
                  {category.protocol}
                </Text>
                <View style={styles.categoryFooter}>
                  <Text style={styles.levelText}>Level {category.level}</Text>
                  <Text style={styles.statusText}>
                    {category.is_public ? 'Public' : 'Private'}
                  </Text>
                </View>
              </View>
            ))}
          </View>
        )}
      </ScrollView>

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
                <Text style={styles.checkboxLabel}>Make this category public</Text>
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
    backgroundColor: colors.lightGray,
    padding: 16,
    borderRadius: 12,
    marginBottom: 20,
  },
  infoText: {
    flex: 1,
    marginLeft: 12,
    fontSize: 14,
    color: colors.textLight,
  },
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
    backgroundColor: colors.white,
    padding: 16,
    borderRadius: 12,
    shadowColor: colors.black,
    shadowOffset: { width: 0, height: 2 },
    shadowOpacity: 0.1,
    shadowRadius: 4,
    elevation: 3,
  },
  categoryHeader: {
    flexDirection: 'row',
    justifyContent: 'space-between',
    alignItems: 'center',
    marginBottom: 12,
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
    color: colors.textLight,
    marginBottom: 4,
  },
  protocolText: {
    fontSize: 14,
    color: colors.text,
    backgroundColor: colors.lightGray,
    padding: 8,
    borderRadius: 6,
    fontFamily: Platform.OS === 'ios' ? 'Menlo' : 'monospace',
  },
  categoryFooter: {
    flexDirection: 'row',
    justifyContent: 'space-between',
    marginTop: 12,
  },
  levelText: {
    fontSize: 12,
    color: colors.textLight,
  },
  statusText: {
    fontSize: 12,
    fontWeight: '600',
    color: colors.secondary,
  },
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
    borderBottomColor: colors.border,
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
    backgroundColor: colors.lightGray,
    padding: 12,
    borderRadius: 8,
    marginBottom: 16,
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
    color: colors.textLight,
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
  },
  createButton: {
    marginBottom: 20,
  },
});
