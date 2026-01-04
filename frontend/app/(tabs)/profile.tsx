import React from 'react';
import {
  View,
  Text,
  TouchableOpacity,
  StyleSheet,
  ScrollView,
  Alert,
} from 'react-native';
import { Ionicons } from '@expo/vector-icons';
import { useAuthStore } from '../../store/authStore';
import { useRouter } from 'expo-router';

export default function ProfileScreen() {
  const { user, logout } = useAuthStore();
  const router = useRouter();

  const handleLogout = () => {
    Alert.alert('Logout', 'Are you sure you want to logout?', [
      { text: 'Cancel', style: 'cancel' },
      {
        text: 'Logout',
        style: 'destructive',
        onPress: async () => {
          await logout();
          router.replace('/(auth)/login');
        },
      },
    ]);
  };

  const handleUpgrade = async () => {
    if (user?.isPaid) {
      Alert.alert('Already Subscribed', 'You are already a Premium member!');
      return;
    }

    Alert.alert(
      '⭐ Upgrade to Premium',
      'Unlock all features for only $0.99/month\n\n' +
      'Premium Benefits:\n' +
      '✓ Unlimited search results\n' +
      '✓ 20 results per page (vs 10 for free)\n' +
      '✓ Advanced protocol features\n' +
      '✓ Priority support\n\n' +
      'Cancel anytime!',
      [
        { text: 'Maybe Later', style: 'cancel' },
        {
          text: 'Subscribe Now - $0.99/mo',
          onPress: async () => {
            try {
              // In production, this would integrate with Shopify
              // For now, we'll activate the subscription directly
              const response = await axios.post(
                `${API_URL}/api/subscription/activate`,
                {},
                { headers: { Authorization: `Bearer ${token}` } }
              );
              
              // Refresh user data
              const userResponse = await axios.get(
                `${API_URL}/api/auth/me`,
                { headers: { Authorization: `Bearer ${token}` } }
              );
              
              // Update stored user
              await AsyncStorage.setItem('user', JSON.stringify(userResponse.data));
              
              // Force re-render by navigating
              Alert.alert(
                '🎉 Welcome to Premium!',
                'Your subscription is now active. Enjoy unlimited access to all features!',
                [
                  {
                    text: 'Start Exploring',
                    onPress: () => {
                      router.push('/(tabs)/home');
                    },
                  },
                ]
              );
            } catch (error: any) {
              console.error('Upgrade error:', error);
              Alert.alert(
                'Subscription Error',
                error.response?.data?.detail || 'Unable to process subscription. Please try again.'
              );
            }
          },
        },
      ]
    );
  };

  return (
    <ScrollView style={styles.container}>
      {/* Header */}
      <View style={styles.header}>
        <View style={styles.avatarContainer}>
          <View style={styles.avatar}>
            <Text style={styles.avatarText}>
              {user?.username?.charAt(0).toUpperCase()}
            </Text>
          </View>
          {user?.isPaid && (
            <View style={styles.premiumBadge}>
              <Ionicons name="star" size={16} color="#FFF" />
            </View>
          )}
        </View>
        <Text style={styles.username}>{user?.username}</Text>
        {user?.email && <Text style={styles.email}>{user.email}</Text>}
        <View style={styles.statusBadge}>
          <Text style={styles.statusText}>
            {user?.isPaid ? '⭐ Premium Member' : '🆓 Free Account'}
          </Text>
        </View>
      </View>

      {/* Account Info */}
      <View style={styles.section}>
        <Text style={styles.sectionTitle}>Account Information</Text>

        <View style={styles.infoCard}>
          <View style={styles.infoRow}>
            <Text style={styles.infoLabel}>Username</Text>
            <Text style={styles.infoValue}>{user?.username}</Text>
          </View>

          {user?.email && (
            <View style={styles.infoRow}>
              <Text style={styles.infoLabel}>Email</Text>
              <Text style={styles.infoValue}>{user.email}</Text>
            </View>
          )}

          <View style={styles.infoRow}>
            <Text style={styles.infoLabel}>Account Type</Text>
            <Text style={styles.infoValue}>
              {user?.isPaid ? 'Premium' : 'Free'}
            </Text>
          </View>

          {user?.subscriptionStatus && (
            <View style={styles.infoRow}>
              <Text style={styles.infoLabel}>Subscription</Text>
              <Text style={styles.infoValue}>{user.subscriptionStatus}</Text>
            </View>
          )}
        </View>
      </View>

      {/* Subscription Section */}
      {!user?.isPaid && (
        <View style={styles.section}>
          <Text style={styles.sectionTitle}>Upgrade Your Account</Text>
          <TouchableOpacity style={styles.upgradeCard} onPress={handleUpgrade}>
            <View style={styles.upgradeContent}>
              <Ionicons name="star" size={32} color="#FF9800" />
              <View style={styles.upgradeText}>
                <Text style={styles.upgradeTitle}>Go Premium</Text>
                <Text style={styles.upgradeDescription}>
                  Unlimited searches • Full feature access • Priority support
                </Text>
                <Text style={styles.upgradePrice}>Only $0.99/month</Text>
              </View>
            </View>
            <Ionicons name="chevron-forward" size={24} color="#999" />
          </TouchableOpacity>
        </View>
      )}

      {/* Settings */}
      <View style={styles.section}>
        <Text style={styles.sectionTitle}>Settings</Text>

        <TouchableOpacity style={styles.settingItem}>
          <View style={styles.settingLeft}>
            <Ionicons name="notifications" size={24} color="#1E88E5" />
            <Text style={styles.settingText}>Notifications</Text>
          </View>
          <Ionicons name="chevron-forward" size={20} color="#999" />
        </TouchableOpacity>

        <TouchableOpacity style={styles.settingItem}>
          <View style={styles.settingLeft}>
            <Ionicons name="lock-closed" size={24} color="#1E88E5" />
            <Text style={styles.settingText}>Privacy</Text>
          </View>
          <Ionicons name="chevron-forward" size={20} color="#999" />
        </TouchableOpacity>

        <TouchableOpacity style={styles.settingItem}>
          <View style={styles.settingLeft}>
            <Ionicons name="help-circle" size={24} color="#1E88E5" />
            <Text style={styles.settingText}>Help & Support</Text>
          </View>
          <Ionicons name="chevron-forward" size={20} color="#999" />
        </TouchableOpacity>
      </View>

      {/* About */}
      <View style={styles.section}>
        <Text style={styles.sectionTitle}>About</Text>

        <View style={styles.aboutCard}>
          <Text style={styles.aboutTitle}>InfoPilot</Text>
          <Text style={styles.aboutDescription}>
            A worldwide web information exchange social network. We give our
            users a 3D view of the internet using InfoJet 2.0 Boolean protocol
            language.
          </Text>
          <Text style={styles.aboutVersion}>Version 1.0.0</Text>
        </View>
      </View>

      {/* Logout Button */}
      <TouchableOpacity style={styles.logoutButton} onPress={handleLogout}>
        <Ionicons name="log-out" size={20} color="#F44336" />
        <Text style={styles.logoutText}>Logout</Text>
      </TouchableOpacity>

      <View style={styles.footer}>
        <Text style={styles.footerText}>© 2025 InfoPilot Inc.</Text>
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
    alignItems: 'center',
    paddingTop: 60,
    paddingBottom: 32,
    backgroundColor: '#FFF',
    borderBottomWidth: 1,
    borderBottomColor: '#E0E0E0',
  },
  avatarContainer: {
    position: 'relative',
    marginBottom: 16,
  },
  avatar: {
    width: 80,
    height: 80,
    borderRadius: 40,
    backgroundColor: '#1E88E5',
    justifyContent: 'center',
    alignItems: 'center',
  },
  avatarText: {
    fontSize: 36,
    fontWeight: 'bold',
    color: '#FFF',
  },
  premiumBadge: {
    position: 'absolute',
    right: -4,
    bottom: -4,
    backgroundColor: '#FF9800',
    width: 28,
    height: 28,
    borderRadius: 14,
    justifyContent: 'center',
    alignItems: 'center',
    borderWidth: 2,
    borderColor: '#FFF',
  },
  username: {
    fontSize: 24,
    fontWeight: 'bold',
    color: '#212121',
  },
  email: {
    fontSize: 14,
    color: '#666',
    marginTop: 4,
  },
  statusBadge: {
    backgroundColor: '#E3F2FD',
    paddingHorizontal: 16,
    paddingVertical: 6,
    borderRadius: 16,
    marginTop: 12,
  },
  statusText: {
    fontSize: 14,
    color: '#1565C0',
    fontWeight: '600',
  },
  section: {
    padding: 16,
  },
  sectionTitle: {
    fontSize: 18,
    fontWeight: '600',
    color: '#212121',
    marginBottom: 12,
  },
  infoCard: {
    backgroundColor: '#FFF',
    borderRadius: 12,
    padding: 16,
    borderWidth: 1,
    borderColor: '#E0E0E0',
  },
  infoRow: {
    flexDirection: 'row',
    justifyContent: 'space-between',
    paddingVertical: 12,
    borderBottomWidth: 1,
    borderBottomColor: '#F5F5F5',
  },
  infoLabel: {
    fontSize: 14,
    color: '#666',
  },
  infoValue: {
    fontSize: 14,
    fontWeight: '600',
    color: '#212121',
  },
  upgradeCard: {
    backgroundColor: '#FFF',
    borderRadius: 12,
    padding: 16,
    flexDirection: 'row',
    justifyContent: 'space-between',
    alignItems: 'center',
    borderWidth: 2,
    borderColor: '#FF9800',
  },
  upgradeContent: {
    flexDirection: 'row',
    alignItems: 'center',
    flex: 1,
    gap: 12,
  },
  upgradeText: {
    flex: 1,
  },
  upgradeTitle: {
    fontSize: 18,
    fontWeight: 'bold',
    color: '#212121',
  },
  upgradeDescription: {
    fontSize: 12,
    color: '#666',
    marginTop: 4,
  },
  upgradePrice: {
    fontSize: 16,
    fontWeight: 'bold',
    color: '#FF9800',
    marginTop: 4,
  },
  settingItem: {
    backgroundColor: '#FFF',
    flexDirection: 'row',
    justifyContent: 'space-between',
    alignItems: 'center',
    padding: 16,
    borderRadius: 12,
    marginBottom: 8,
    borderWidth: 1,
    borderColor: '#E0E0E0',
  },
  settingLeft: {
    flexDirection: 'row',
    alignItems: 'center',
    gap: 12,
  },
  settingText: {
    fontSize: 16,
    color: '#212121',
  },
  aboutCard: {
    backgroundColor: '#FFF',
    borderRadius: 12,
    padding: 16,
    borderWidth: 1,
    borderColor: '#E0E0E0',
  },
  aboutTitle: {
    fontSize: 20,
    fontWeight: 'bold',
    color: '#1E88E5',
    marginBottom: 8,
  },
  aboutDescription: {
    fontSize: 14,
    color: '#666',
    lineHeight: 20,
    marginBottom: 12,
  },
  aboutVersion: {
    fontSize: 12,
    color: '#999',
  },
  logoutButton: {
    flexDirection: 'row',
    alignItems: 'center',
    justifyContent: 'center',
    backgroundColor: '#FFF',
    marginHorizontal: 16,
    padding: 16,
    borderRadius: 12,
    borderWidth: 1,
    borderColor: '#F44336',
    gap: 8,
  },
  logoutText: {
    fontSize: 16,
    fontWeight: '600',
    color: '#F44336',
  },
  footer: {
    alignItems: 'center',
    paddingVertical: 24,
  },
  footerText: {
    fontSize: 12,
    color: '#999',
  },
});
