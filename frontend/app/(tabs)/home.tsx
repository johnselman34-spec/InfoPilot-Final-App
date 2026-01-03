import React, { useEffect, useState } from 'react';
import {
  View,
  Text,
  StyleSheet,
  ScrollView,
  TouchableOpacity,
  RefreshControl,
  Alert,
} from 'react-native';
import { useAuthStore } from '../../store/authStore';
import { Ionicons } from '@expo/vector-icons';
import { useRouter } from 'expo-router';
import axios from 'axios';

const API_URL = process.env.EXPO_PUBLIC_BACKEND_URL;

export default function HomeScreen() {
  const { user, token } = useAuthStore();
  const router = useRouter();
  const [refreshing, setRefreshing] = useState(false);
  const [stats, setStats] = useState({
    categories: 0,
    protocols: 0,
    savedResults: 0,
  });

  const loadStats = async () => {
    try {
      if (!token) return;

      const headers = { Authorization: `Bearer ${token}` };
      
      const [categoriesRes, protocolsRes, resultsRes] = await Promise.all([
        axios.get(`${API_URL}/api/categories`, { headers }),
        axios.get(`${API_URL}/api/protocols`, { headers }),
        axios.get(`${API_URL}/api/results`, { headers }),
      ]);

      setStats({
        categories: categoriesRes.data.categories?.length || 0,
        protocols: protocolsRes.data.protocols?.length || 0,
        savedResults: resultsRes.data.results?.length || 0,
      });
    } catch (error) {
      console.error('Load stats error:', error);
    }
  };

  useEffect(() => {
    loadStats();
  }, []);

  const onRefresh = async () => {
    setRefreshing(true);
    await loadStats();
    setRefreshing(false);
  };

  const handleUpgrade = () => {
    Alert.alert(
      'Upgrade to Premium',
      'Get unlimited search results and access to all features for only $0.99/month',
      [
        { text: 'Maybe Later', style: 'cancel' },
        {
          text: 'Upgrade Now',
          onPress: async () => {
            try {
              if (!token) return;
              await axios.post(
                `${API_URL}/api/subscription/activate`,
                {},
                { headers: { Authorization: `Bearer ${token}` } }
              );
              Alert.alert('Success', 'Subscription activated!');
            } catch (error) {
              Alert.alert('Error', 'Failed to activate subscription');
            }
          },
        },
      ]
    );
  };

  return (
    <ScrollView
      style={styles.container}
      refreshControl={
        <RefreshControl refreshing={refreshing} onRefresh={onRefresh} />
      }
    >
      {/* Header */}
      <View style={styles.header}>
        <View>
          <Text style={styles.greeting}>Welcome back,</Text>
          <Text style={styles.username}>{user?.username}</Text>
        </View>
        {!user?.isPaid && (
          <TouchableOpacity
            style={styles.upgradeButton}
            onPress={handleUpgrade}
          >
            <Ionicons name="star" size={16} color="#FFF" />
            <Text style={styles.upgradeText}>Upgrade</Text>
          </TouchableOpacity>
        )}
      </View>

      {/* Subscription Status */}
      <View style={styles.card}>
        <View style={styles.cardHeader}>
          <Ionicons
            name={user?.isPaid ? 'checkmark-circle' : 'information-circle'}
            size={24}
            color={user?.isPaid ? '#4CAF50' : '#FF9800'}
          />
          <Text style={styles.cardTitle}>
            {user?.isPaid ? 'Premium Account' : 'Free Account'}
          </Text>
        </View>
        <Text style={styles.cardDescription}>
          {user?.isPaid
            ? 'Unlimited searches and full feature access'
            : 'Limited to 20 results per search. Upgrade for unlimited access!'}
        </Text>
      </View>

      {/* Stats Cards */}
      <View style={styles.statsContainer}>
        <View style={styles.statCard}>
          <Ionicons name="folder" size={32} color="#1E88E5" />
          <Text style={styles.statNumber}>{stats.categories}</Text>
          <Text style={styles.statLabel}>Categories</Text>
        </View>

        <View style={styles.statCard}>
          <Ionicons name="code" size={32} color="#1E88E5" />
          <Text style={styles.statNumber}>{stats.protocols}</Text>
          <Text style={styles.statLabel}>Protocols</Text>
        </View>

        <View style={styles.statCard}>
          <Ionicons name="bookmark" size={32} color="#1E88E5" />
          <Text style={styles.statNumber}>{stats.savedResults}</Text>
          <Text style={styles.statLabel}>Saved Results</Text>
        </View>
      </View>

      {/* Quick Actions */}
      <View style={styles.section}>
        <Text style={styles.sectionTitle}>Quick Actions</Text>
        
        <TouchableOpacity
          style={styles.actionCard}
          onPress={() => router.push('/(tabs)/search')}
        >
          <View style={styles.actionLeft}>
            <Ionicons name="search" size={24} color="#1E88E5" />
            <Text style={styles.actionTitle}>Start Searching</Text>
          </View>
          <Ionicons name="chevron-forward" size={24} color="#999" />
        </TouchableOpacity>

        <TouchableOpacity
          style={styles.actionCard}
          onPress={() => router.push('/(tabs)/categories')}
        >
          <View style={styles.actionLeft}>
            <Ionicons name="add-circle" size={24} color="#1E88E5" />
            <Text style={styles.actionTitle}>Create Category</Text>
          </View>
          <Ionicons name="chevron-forward" size={24} color="#999" />
        </TouchableOpacity>
      </View>

      {/* About InfoJet 2.0 */}
      <View style={styles.section}>
        <Text style={styles.sectionTitle}>About InfoJet 2.0</Text>
        <View style={styles.infoCard}>
          <Text style={styles.infoText}>
            InfoJet 2.0 uses Boolean protocol language to help you create
            powerful search queries. Use parentheses, 'or', '&', '+' and '^'
            to build custom search protocols.
          </Text>
          <Text style={styles.infoExample}>
            Example: (AI or artificial intelligence) & (machine learning)+
          </Text>
        </View>
      </View>
    </ScrollView>
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
    padding: 20,
    paddingTop: 60,
    backgroundColor: '#FFF',
    borderBottomWidth: 1,
    borderBottomColor: '#E0E0E0',
  },
  greeting: {
    fontSize: 14,
    color: '#666',
  },
  username: {
    fontSize: 24,
    fontWeight: 'bold',
    color: '#212121',
  },
  upgradeButton: {
    flexDirection: 'row',
    alignItems: 'center',
    backgroundColor: '#FF9800',
    paddingHorizontal: 16,
    paddingVertical: 8,
    borderRadius: 20,
    gap: 4,
  },
  upgradeText: {
    color: '#FFF',
    fontWeight: '600',
    fontSize: 14,
  },
  card: {
    backgroundColor: '#FFF',
    margin: 16,
    padding: 16,
    borderRadius: 12,
    borderWidth: 1,
    borderColor: '#E0E0E0',
  },
  cardHeader: {
    flexDirection: 'row',
    alignItems: 'center',
    marginBottom: 8,
    gap: 8,
  },
  cardTitle: {
    fontSize: 18,
    fontWeight: '600',
    color: '#212121',
  },
  cardDescription: {
    fontSize: 14,
    color: '#666',
    lineHeight: 20,
  },
  statsContainer: {
    flexDirection: 'row',
    justifyContent: 'space-between',
    paddingHorizontal: 16,
    marginBottom: 16,
    gap: 8,
  },
  statCard: {
    flex: 1,
    backgroundColor: '#FFF',
    padding: 16,
    borderRadius: 12,
    alignItems: 'center',
    borderWidth: 1,
    borderColor: '#E0E0E0',
  },
  statNumber: {
    fontSize: 24,
    fontWeight: 'bold',
    color: '#212121',
    marginTop: 8,
  },
  statLabel: {
    fontSize: 12,
    color: '#666',
    marginTop: 4,
  },
  section: {
    paddingHorizontal: 16,
    marginBottom: 24,
  },
  sectionTitle: {
    fontSize: 20,
    fontWeight: '600',
    color: '#212121',
    marginBottom: 12,
  },
  actionCard: {
    flexDirection: 'row',
    justifyContent: 'space-between',
    alignItems: 'center',
    backgroundColor: '#FFF',
    padding: 16,
    borderRadius: 12,
    marginBottom: 8,
    borderWidth: 1,
    borderColor: '#E0E0E0',
  },
  actionLeft: {
    flexDirection: 'row',
    alignItems: 'center',
    gap: 12,
  },
  actionTitle: {
    fontSize: 16,
    fontWeight: '500',
    color: '#212121',
  },
  infoCard: {
    backgroundColor: '#E3F2FD',
    padding: 16,
    borderRadius: 12,
  },
  infoText: {
    fontSize: 14,
    color: '#1565C0',
    lineHeight: 20,
    marginBottom: 8,
  },
  infoExample: {
    fontSize: 13,
    color: '#0D47A1',
    fontFamily: Platform.OS === 'ios' ? 'Courier' : 'monospace',
    backgroundColor: '#FFF',
    padding: 8,
    borderRadius: 6,
  },
});
