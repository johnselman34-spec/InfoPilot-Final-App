import React, { useEffect, useState } from 'react';
import { View, Text, StyleSheet, ScrollView, TouchableOpacity, RefreshControl, Modal, Alert } from 'react-native';
import { SafeAreaView } from 'react-native-safe-area-context';
import { Ionicons } from '@expo/vector-icons';
import { useAuthStore } from '../../src/store/authStore';
import { useCategoryStore } from '../../src/store/categoryStore';
import { colors } from '../../src/utils/colors';
import { useRouter } from 'expo-router';
import { userAPI } from '../../src/services/api';
import { CustomButton } from '../../src/components/CustomButton';

export default function HomeScreen() {
  const router = useRouter();
  const { user, updateUser } = useAuthStore();
  const { categories, fetchCategories, isLoading } = useCategoryStore();
  const [refreshing, setRefreshing] = useState(false);
  const [upgradeModalVisible, setUpgradeModalVisible] = useState(false);
  const [upgrading, setUpgrading] = useState(false);

  useEffect(() => {
    fetchCategories();
  }, []);

  const onRefresh = async () => {
    setRefreshing(true);
    await fetchCategories();
    setRefreshing(false);
  };

  const handleUpgrade = async () => {
    try {
      setUpgrading(true);
      // Call backend to mark user as subscribed
      await userAPI.subscribe();
      
      // Update local user state
      if (user) {
        updateUser({ ...user, subscription_status: 'paid' });
      }
      
      Alert.alert(
        'Subscription Activated!',
        'You now have unlimited access to all InfoPilot features!',
        [{ text: 'OK', onPress: () => setUpgradeModalVisible(false) }]
      );
    } catch (error: any) {
      Alert.alert('Error', error.response?.data?.detail || 'Failed to upgrade. Please try again.');
    } finally {
      setUpgrading(false);
    }
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
          <Text style={styles.greeting}>Welcome back,</Text>
          <Text style={styles.username}>{user?.username}!</Text>
          <Text style={styles.subtitle}>Your Ultimate Search Page</Text>
        </View>

        <View style={styles.statsContainer}>
          <StatCard
            icon="folder-open"
            title="Categories"
            value={categories.length.toString()}
            color={colors.primary}
          />
          <StatCard
            icon="search"
            title="Searches"
            value="0"
            color={colors.secondary}
          />
        </View>

        <View style={styles.section}>
          <View style={styles.sectionHeader}>
            <Text style={styles.sectionTitle}>Your Categories</Text>
            <TouchableOpacity onPress={() => router.push('/(tabs)/categories')}>
              <Text style={styles.seeAll}>See All</Text>
            </TouchableOpacity>
          </View>

          {categories.length === 0 ? (
            <View style={styles.emptyState}>
              <Ionicons name="folder-open-outline" size={64} color={colors.gray} />
              <Text style={styles.emptyText}>No categories yet</Text>
              <Text style={styles.emptySubtext}>Create your first category to get started</Text>
              <TouchableOpacity
                style={styles.createButton}
                onPress={() => router.push('/(tabs)/categories')}
              >
                <Text style={styles.createButtonText}>Create Category</Text>
              </TouchableOpacity>
            </View>
          ) : (
            <View style={styles.categoriesList}>
              {categories.slice(0, 5).map((category) => (
                <View key={category.id} style={styles.categoryCard}>
                  <View style={styles.categoryHeader}>
                    <Ionicons name="folder" size={24} color={colors.primary} />
                    <View style={styles.categoryInfo}>
                      <Text style={styles.categoryName}>{category.name}</Text>
                      <Text style={styles.categoryMeta} numberOfLines={1}>
                        Level {category.level} • {category.is_public ? 'Public' : 'Private'}
                      </Text>
                    </View>
                  </View>
                </View>
              ))}
            </View>
          )}
        </View>

        {user?.subscription_status === 'free' && (
          <View style={styles.subscriptionCard}>
            <View style={styles.subscriptionContent}>
              <Ionicons name="star" size={32} color={colors.accent} />
              <View style={styles.subscriptionText}>
                <Text style={styles.subscriptionTitle}>Upgrade to Premium</Text>
                <Text style={styles.subscriptionSubtitle}>
                  Unlimited searches, all features, $0.99/month
                </Text>
              </View>
            </View>
            <TouchableOpacity 
              style={styles.upgradeButton}
              onPress={() => setUpgradeModalVisible(true)}
            >
              <Text style={styles.upgradeButtonText}>Upgrade</Text>
            </TouchableOpacity>
          </View>
        )}

        {/* Upgrade Modal */}
        <Modal
          visible={upgradeModalVisible}
          animationType="slide"
          presentationStyle="pageSheet"
          onRequestClose={() => setUpgradeModalVisible(false)}
        >
          <SafeAreaView style={styles.modalContainer}>
            <View style={styles.modalHeader}>
              <Text style={styles.modalTitle}>Upgrade to Premium</Text>
              <TouchableOpacity onPress={() => setUpgradeModalVisible(false)}>
                <Ionicons name="close" size={28} color={colors.text} />
              </TouchableOpacity>
            </View>

            <ScrollView style={styles.modalContent}>
              <View style={styles.pricingCard}>
                <Ionicons name="star" size={64} color={colors.accent} />
                <Text style={styles.pricingTitle}>Premium Plan</Text>
                <Text style={styles.pricingPrice}>$0.99</Text>
                <Text style={styles.pricingPeriod}>per month</Text>
              </View>

              <View style={styles.featuresList}>
                <Text style={styles.featuresTitle}>Premium Features:</Text>
                
                <View style={styles.featureItem}>
                  <Ionicons name="checkmark-circle" size={24} color={colors.secondary} />
                  <Text style={styles.featureText}>Unlimited search results (no 1-page limit)</Text>
                </View>

                <View style={styles.featureItem}>
                  <Ionicons name="checkmark-circle" size={24} color={colors.secondary} />
                  <Text style={styles.featureText}>Unlimited categories and protocols</Text>
                </View>

                <View style={styles.featureItem}>
                  <Ionicons name="checkmark-circle" size={24} color={colors.secondary} />
                  <Text style={styles.featureText}>Advanced AI categorization</Text>
                </View>

                <View style={styles.featureItem}>
                  <Ionicons name="checkmark-circle" size={24} color={colors.secondary} />
                  <Text style={styles.featureText}>Priority search speed</Text>
                </View>

                <View style={styles.featureItem}>
                  <Ionicons name="checkmark-circle" size={24} color={colors.secondary} />
                  <Text style={styles.featureText}>Export and share categories</Text>
                </View>

                <View style={styles.featureItem}>
                  <Ionicons name="checkmark-circle" size={24} color={colors.secondary} />
                  <Text style={styles.featureText}>Ad-free experience</Text>
                </View>
              </View>

              <CustomButton
                title="Subscribe Now - $0.99/month"
                onPress={handleUpgrade}
                loading={upgrading}
                style={styles.subscribeButton}
              />

              <Text style={styles.disclaimer}>
                For demo purposes, clicking Subscribe will activate premium features immediately. 
                In production, this would integrate with Google Play Billing.
              </Text>
            </ScrollView>
          </SafeAreaView>
        </Modal>
      </ScrollView>
    </SafeAreaView>
  );
}

const StatCard = ({ icon, title, value, color }: any) => (
  <View style={styles.statCard}>
    <Ionicons name={icon} size={32} color={color} />
    <Text style={styles.statValue}>{value}</Text>
    <Text style={styles.statTitle}>{title}</Text>
  </View>
);

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
  greeting: {
    fontSize: 16,
    color: colors.textLight,
  },
  username: {
    fontSize: 28,
    fontWeight: 'bold',
    color: colors.text,
    marginBottom: 4,
  },
  subtitle: {
    fontSize: 14,
    color: colors.secondary,
    fontWeight: '600',
  },
  statsContainer: {
    flexDirection: 'row',
    justifyContent: 'space-between',
    marginBottom: 24,
    gap: 16,
  },
  statCard: {
    flex: 1,
    backgroundColor: colors.white,
    padding: 20,
    borderRadius: 12,
    alignItems: 'center',
    shadowColor: colors.black,
    shadowOffset: { width: 0, height: 2 },
    shadowOpacity: 0.1,
    shadowRadius: 4,
    elevation: 3,
  },
  statValue: {
    fontSize: 28,
    fontWeight: 'bold',
    color: colors.text,
    marginTop: 8,
  },
  statTitle: {
    fontSize: 12,
    color: colors.textLight,
    marginTop: 4,
  },
  section: {
    marginBottom: 24,
  },
  sectionHeader: {
    flexDirection: 'row',
    justifyContent: 'space-between',
    alignItems: 'center',
    marginBottom: 16,
  },
  sectionTitle: {
    fontSize: 20,
    fontWeight: 'bold',
    color: colors.text,
  },
  seeAll: {
    fontSize: 14,
    color: colors.primary,
    fontWeight: '600',
  },
  emptyState: {
    backgroundColor: colors.white,
    padding: 40,
    borderRadius: 12,
    alignItems: 'center',
  },
  emptyText: {
    fontSize: 18,
    fontWeight: '600',
    color: colors.text,
    marginTop: 16,
  },
  emptySubtext: {
    fontSize: 14,
    color: colors.textLight,
    marginTop: 8,
    textAlign: 'center',
  },
  createButton: {
    marginTop: 20,
    backgroundColor: colors.primary,
    paddingHorizontal: 24,
    paddingVertical: 12,
    borderRadius: 8,
  },
  createButtonText: {
    color: colors.white,
    fontWeight: '600',
    fontSize: 14,
  },
  categoriesList: {
    gap: 12,
  },
  categoryCard: {
    backgroundColor: colors.white,
    padding: 16,
    borderRadius: 12,
    shadowColor: colors.black,
    shadowOffset: { width: 0, height: 1 },
    shadowOpacity: 0.1,
    shadowRadius: 2,
    elevation: 2,
  },
  categoryHeader: {
    flexDirection: 'row',
    alignItems: 'center',
  },
  categoryInfo: {
    flex: 1,
    marginLeft: 12,
  },
  categoryName: {
    fontSize: 16,
    fontWeight: '600',
    color: colors.text,
  },
  categoryMeta: {
    fontSize: 12,
    color: colors.textLight,
    marginTop: 2,
  },
  subscriptionCard: {
    backgroundColor: colors.white,
    padding: 20,
    borderRadius: 12,
    borderWidth: 2,
    borderColor: colors.accent,
    shadowColor: colors.black,
    shadowOffset: { width: 0, height: 2 },
    shadowOpacity: 0.1,
    shadowRadius: 4,
    elevation: 3,
  },
  subscriptionContent: {
    flexDirection: 'row',
    alignItems: 'center',
    marginBottom: 16,
  },
  subscriptionText: {
    flex: 1,
    marginLeft: 16,
  },
  subscriptionTitle: {
    fontSize: 18,
    fontWeight: 'bold',
    color: colors.text,
  },
  subscriptionSubtitle: {
    fontSize: 14,
    color: colors.textLight,
    marginTop: 4,
  },
  upgradeButton: {
    backgroundColor: colors.accent,
    paddingVertical: 12,
    borderRadius: 8,
    alignItems: 'center',
  },
  upgradeButtonText: {
    color: colors.white,
    fontSize: 16,
    fontWeight: '600',
  },
  modalContainer: {
    flex: 1,
    backgroundColor: colors.background,
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
  pricingCard: {
    alignItems: 'center',
    backgroundColor: colors.white,
    padding: 40,
    borderRadius: 16,
    marginBottom: 32,
    shadowColor: colors.black,
    shadowOffset: { width: 0, height: 4 },
    shadowOpacity: 0.1,
    shadowRadius: 8,
    elevation: 5,
  },
  pricingTitle: {
    fontSize: 24,
    fontWeight: 'bold',
    color: colors.text,
    marginTop: 16,
  },
  pricingPrice: {
    fontSize: 48,
    fontWeight: 'bold',
    color: colors.primary,
    marginTop: 8,
  },
  pricingPeriod: {
    fontSize: 16,
    color: colors.textLight,
  },
  featuresList: {
    marginBottom: 32,
  },
  featuresTitle: {
    fontSize: 20,
    fontWeight: 'bold',
    color: colors.text,
    marginBottom: 20,
  },
  featureItem: {
    flexDirection: 'row',
    alignItems: 'center',
    marginBottom: 16,
  },
  featureText: {
    flex: 1,
    fontSize: 16,
    color: colors.text,
    marginLeft: 12,
  },
  subscribeButton: {
    marginBottom: 20,
  },
  disclaimer: {
    fontSize: 12,
    color: colors.textLight,
    textAlign: 'center',
    fontStyle: 'italic',
    marginBottom: 20,
  },
});
