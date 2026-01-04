import React, { useState } from 'react';
import {
  View,
  Text,
  StyleSheet,
  ScrollView,
  TouchableOpacity,
  Switch,
  Alert,
  Linking,
} from 'react-native';
import { SafeAreaView } from 'react-native-safe-area-context';
import { Ionicons } from '@expo/vector-icons';
import { useRouter } from 'expo-router';
import { useAuth } from '../../src/context/AuthContext';
import { api } from '../../src/services/api';

const PAYPAL_LINK = 'https://py.pl/vdf9TkEwfV1ngxIsu9JzlQ';

export default function SettingsScreen() {
  const router = useRouter();
  const { user, logout, refreshUser } = useAuth();
  const [ultimateSearchPublic, setUltimateSearchPublic] = useState(
    user?.ultimate_search_public || false
  );
  const [friendsVisible, setFriendsVisible] = useState(
    user?.friends_visible || false
  );
  const [saving, setSaving] = useState(false);

  const handleToggle = async (setting: string, value: boolean) => {
    setSaving(true);
    try {
      const params: any = {};
      if (setting === 'ultimate_search_public') {
        params.ultimate_search_public = value;
        setUltimateSearchPublic(value);
      } else if (setting === 'friends_visible') {
        params.friends_visible = value;
        setFriendsVisible(value);
      }
      
      await api.put('/users/settings', params);
      await refreshUser();
    } catch (error) {
      Alert.alert('Error', 'Could not update setting');
      if (setting === 'ultimate_search_public') setUltimateSearchPublic(!value);
      if (setting === 'friends_visible') setFriendsVisible(!value);
    } finally {
      setSaving(false);
    }
  };

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

  const handleSubscribe = async () => {
    Alert.alert(
      'Subscribe to InfoPilot Premium',
      'Get full access to InfoJet for only $0.99!\n\n• Unlimited search result pages\n• Interactive world map\n• All premium features\n• Support development',
      [
        { text: 'Maybe Later', style: 'cancel' },
        {
          text: 'Subscribe via PayPal',
          onPress: async () => {
            try {
              await Linking.openURL(PAYPAL_LINK);
              // After returning, ask if payment was completed
              setTimeout(() => {
                Alert.alert(
                  'Payment Complete?',
                  'Did you complete your PayPal payment?',
                  [
                    { text: 'No', style: 'cancel' },
                    {
                      text: 'Yes, Activate Premium',
                      onPress: async () => {
                        try {
                          await api.post('/payment/activate', {});
                          await refreshUser();
                          Alert.alert('Success!', 'Welcome to InfoJet Premium!');
                        } catch (error) {
                          Alert.alert('Error', 'Could not activate premium');
                        }
                      },
                    },
                  ]
                );
              }, 2000);
            } catch (error) {
              Alert.alert('Error', 'Could not open PayPal');
            }
          },
        },
      ]
    );
  };

  return (
    <SafeAreaView style={styles.container} edges={['top']}>
      {/* Header */}
      <View style={styles.header}>
        <Text style={styles.headerTitle}>Settings</Text>
      </View>

      <ScrollView style={styles.content}>
        {/* Profile Section */}
        <View style={styles.section}>
          <Text style={styles.sectionTitle}>Profile</Text>
          <View style={styles.profileCard}>
            <View style={styles.profileAvatar}>
              <Text style={styles.profileInitial}>
                {user?.username?.[0]?.toUpperCase() || 'U'}
              </Text>
            </View>
            <View style={styles.profileInfo}>
              <Text style={styles.profileName}>@{user?.username}</Text>
              <Text style={styles.profileEmail}>{user?.email}</Text>
              <View style={styles.statusRow}>
                {user?.is_paid ? (
                  <View style={styles.premiumBadge}>
                    <Ionicons name="star" size={12} color="#FFD700" />
                    <Text style={styles.premiumText}>Premium</Text>
                  </View>
                ) : (
                  <View style={styles.freeBadge}>
                    <Text style={styles.freeText}>Free Plan</Text>
                  </View>
                )}
                {user?.is_admin && (
                  <View style={styles.adminBadge}>
                    <Ionicons name="shield" size={12} color="#fff" />
                    <Text style={styles.adminText}>Admin</Text>
                  </View>
                )}
              </View>
            </View>
          </View>
        </View>

        {/* Subscription */}
        {!user?.is_paid && (
          <View style={styles.section}>
            <Text style={styles.sectionTitle}>Subscription</Text>
            <TouchableOpacity style={styles.subscribeCard} onPress={handleSubscribe}>
              <View style={styles.subscribeContent}>
                <Ionicons name="rocket" size={32} color="#2196F3" />
                <View style={styles.subscribeText}>
                  <Text style={styles.subscribeTitle}>Upgrade to Premium</Text>
                  <Text style={styles.subscribeDesc}>
                    Unlimited pages, world map, all features
                  </Text>
                  <View style={styles.priceRow}>
                    <Text style={styles.priceText}>Only $0.99</Text>
                    <View style={styles.paypalBadge}>
                      <Text style={styles.paypalText}>PayPal</Text>
                    </View>
                  </View>
                </View>
              </View>
              <Ionicons name="chevron-forward" size={24} color="#2196F3" />
            </TouchableOpacity>
          </View>
        )}

        {/* Premium Active */}
        {user?.is_paid && (
          <View style={styles.section}>
            <View style={styles.premiumActiveCard}>
              <Ionicons name="checkmark-circle" size={32} color="#4CAF50" />
              <View style={styles.premiumActiveText}>
                <Text style={styles.premiumActiveTitle}>Premium Active</Text>
                <Text style={styles.premiumActiveDesc}>
                  Thank you for supporting InfoJet!
                </Text>
              </View>
            </View>
          </View>
        )}

        {/* Privacy Settings */}
        <View style={styles.section}>
          <Text style={styles.sectionTitle}>Privacy</Text>
          
          <View style={styles.settingItem}>
            <View style={styles.settingInfo}>
              <Ionicons name="globe-outline" size={22} color="#666" />
              <View style={styles.settingText}>
                <Text style={styles.settingLabel}>Public Ultimate Search</Text>
                <Text style={styles.settingDesc}>
                  Allow others to view your Ultimate Search Page
                </Text>
              </View>
            </View>
            <Switch
              value={ultimateSearchPublic}
              onValueChange={(value) => handleToggle('ultimate_search_public', value)}
              trackColor={{ false: '#E0E0E0', true: '#81C784' }}
              thumbColor={ultimateSearchPublic ? '#4CAF50' : '#f4f3f4'}
            />
          </View>

          <View style={styles.settingItem}>
            <View style={styles.settingInfo}>
              <Ionicons name="people-outline" size={22} color="#666" />
              <View style={styles.settingText}>
                <Text style={styles.settingLabel}>Show Friends List</Text>
                <Text style={styles.settingDesc}>
                  Allow others to see your friends
                </Text>
              </View>
            </View>
            <Switch
              value={friendsVisible}
              onValueChange={(value) => handleToggle('friends_visible', value)}
              trackColor={{ false: '#E0E0E0', true: '#81C784' }}
              thumbColor={friendsVisible ? '#4CAF50' : '#f4f3f4'}
            />
          </View>

          <View style={styles.privacyNotice}>
            <Ionicons name="shield-checkmark" size={18} color="#4CAF50" />
            <Text style={styles.privacyText}>
              We encourage you to keep your Ultimate Search Page private for security.
            </Text>
          </View>
        </View>

        {/* About */}
        <View style={styles.section}>
          <Text style={styles.sectionTitle}>About</Text>
          
          <TouchableOpacity style={styles.aboutItem}>
            <Ionicons name="information-circle-outline" size={22} color="#666" />
            <Text style={styles.aboutText}>About InfoPilot</Text>
            <Ionicons name="chevron-forward" size={20} color="#ccc" />
          </TouchableOpacity>

          <TouchableOpacity style={styles.aboutItem}>
            <Ionicons name="play-circle-outline" size={22} color="#666" />
            <Text style={styles.aboutText}>Tutorial Video</Text>
            <Ionicons name="chevron-forward" size={20} color="#ccc" />
          </TouchableOpacity>

          <TouchableOpacity style={styles.aboutItem}>
            <Ionicons name="document-text-outline" size={22} color="#666" />
            <Text style={styles.aboutText}>Terms of Service</Text>
            <Ionicons name="chevron-forward" size={20} color="#ccc" />
          </TouchableOpacity>

          <TouchableOpacity style={styles.aboutItem}>
            <Ionicons name="shield-outline" size={22} color="#666" />
            <Text style={styles.aboutText}>Privacy Policy</Text>
            <Ionicons name="chevron-forward" size={20} color="#ccc" />
          </TouchableOpacity>
        </View>

        {/* Logout */}
        <TouchableOpacity style={styles.logoutButton} onPress={handleLogout}>
          <Ionicons name="log-out-outline" size={22} color="#f44336" />
          <Text style={styles.logoutText}>Logout</Text>
        </TouchableOpacity>

        {/* Footer */}
        <View style={styles.footer}>
          <Text style={styles.footerText}>InfoPilot v1.0.0</Text>
          <Text style={styles.footerText}>Top Pilot Enterprises | Brunswick, Maine</Text>
          <Text style={styles.footerText}>© 2025 John Selman</Text>
          <Text style={styles.footerText}>john.1976.selman@gmail.com</Text>
        </View>
      </ScrollView>
    </SafeAreaView>
  );
}

const styles = StyleSheet.create({
  container: {
    flex: 1,
    backgroundColor: '#FFFFF0',
  },
  header: {
    paddingHorizontal: 16,
    paddingVertical: 14,
    backgroundColor: '#fff',
    borderBottomWidth: 1,
    borderBottomColor: '#E0E0E0',
  },
  headerTitle: {
    fontSize: 20,
    fontWeight: 'bold',
    color: '#333',
  },
  content: {
    flex: 1,
  },
  section: {
    paddingHorizontal: 16,
    paddingTop: 20,
  },
  sectionTitle: {
    fontSize: 13,
    fontWeight: '600',
    color: '#666',
    textTransform: 'uppercase',
    marginBottom: 12,
  },
  profileCard: {
    flexDirection: 'row',
    alignItems: 'center',
    backgroundColor: '#fff',
    borderRadius: 12,
    padding: 16,
    borderWidth: 1,
    borderColor: '#E0E0E0',
  },
  profileAvatar: {
    width: 56,
    height: 56,
    borderRadius: 28,
    backgroundColor: '#2196F3',
    alignItems: 'center',
    justifyContent: 'center',
  },
  profileInitial: {
    fontSize: 24,
    fontWeight: 'bold',
    color: '#fff',
  },
  profileInfo: {
    flex: 1,
    marginLeft: 14,
  },
  profileName: {
    fontSize: 17,
    fontWeight: '600',
    color: '#333',
  },
  profileEmail: {
    fontSize: 13,
    color: '#666',
    marginTop: 2,
  },
  statusRow: {
    flexDirection: 'row',
    marginTop: 8,
  },
  premiumBadge: {
    flexDirection: 'row',
    alignItems: 'center',
    backgroundColor: '#FFF8E1',
    paddingHorizontal: 8,
    paddingVertical: 4,
    borderRadius: 12,
    marginRight: 8,
  },
  premiumText: {
    fontSize: 11,
    color: '#F9A825',
    fontWeight: '600',
    marginLeft: 4,
  },
  freeBadge: {
    backgroundColor: '#F5F5F5',
    paddingHorizontal: 8,
    paddingVertical: 4,
    borderRadius: 12,
    marginRight: 8,
  },
  freeText: {
    fontSize: 11,
    color: '#666',
  },
  adminBadge: {
    flexDirection: 'row',
    alignItems: 'center',
    backgroundColor: '#7C4DFF',
    paddingHorizontal: 8,
    paddingVertical: 4,
    borderRadius: 12,
  },
  adminText: {
    fontSize: 11,
    color: '#fff',
    fontWeight: '600',
    marginLeft: 4,
  },
  subscribeCard: {
    flexDirection: 'row',
    alignItems: 'center',
    justifyContent: 'space-between',
    backgroundColor: '#E3F2FD',
    borderRadius: 12,
    padding: 16,
    borderWidth: 1,
    borderColor: '#BBDEFB',
  },
  subscribeContent: {
    flexDirection: 'row',
    alignItems: 'center',
    flex: 1,
  },
  subscribeText: {
    marginLeft: 14,
    flex: 1,
  },
  subscribeTitle: {
    fontSize: 16,
    fontWeight: '600',
    color: '#1976D2',
  },
  subscribeDesc: {
    fontSize: 12,
    color: '#666',
    marginTop: 2,
  },
  priceRow: {
    flexDirection: 'row',
    alignItems: 'center',
    marginTop: 6,
  },
  priceText: {
    fontSize: 14,
    fontWeight: 'bold',
    color: '#4CAF50',
  },
  paypalBadge: {
    backgroundColor: '#003087',
    paddingHorizontal: 8,
    paddingVertical: 2,
    borderRadius: 8,
    marginLeft: 8,
  },
  paypalText: {
    fontSize: 10,
    color: '#fff',
    fontWeight: '600',
  },
  premiumActiveCard: {
    flexDirection: 'row',
    alignItems: 'center',
    backgroundColor: '#E8F5E9',
    borderRadius: 12,
    padding: 16,
    borderWidth: 1,
    borderColor: '#C8E6C9',
  },
  premiumActiveText: {
    marginLeft: 14,
  },
  premiumActiveTitle: {
    fontSize: 16,
    fontWeight: '600',
    color: '#2E7D32',
  },
  premiumActiveDesc: {
    fontSize: 12,
    color: '#4CAF50',
    marginTop: 2,
  },
  settingItem: {
    flexDirection: 'row',
    alignItems: 'center',
    justifyContent: 'space-between',
    backgroundColor: '#fff',
    borderRadius: 12,
    padding: 14,
    marginBottom: 10,
    borderWidth: 1,
    borderColor: '#E0E0E0',
  },
  settingInfo: {
    flexDirection: 'row',
    alignItems: 'center',
    flex: 1,
  },
  settingText: {
    marginLeft: 12,
    flex: 1,
  },
  settingLabel: {
    fontSize: 15,
    color: '#333',
  },
  settingDesc: {
    fontSize: 12,
    color: '#999',
    marginTop: 2,
  },
  privacyNotice: {
    flexDirection: 'row',
    alignItems: 'center',
    backgroundColor: '#E8F5E9',
    padding: 12,
    borderRadius: 10,
    marginTop: 4,
  },
  privacyText: {
    flex: 1,
    fontSize: 12,
    color: '#4CAF50',
    marginLeft: 10,
    fontStyle: 'italic',
  },
  aboutItem: {
    flexDirection: 'row',
    alignItems: 'center',
    backgroundColor: '#fff',
    borderRadius: 12,
    padding: 14,
    marginBottom: 8,
    borderWidth: 1,
    borderColor: '#E0E0E0',
  },
  aboutText: {
    flex: 1,
    fontSize: 15,
    color: '#333',
    marginLeft: 12,
  },
  logoutButton: {
    flexDirection: 'row',
    alignItems: 'center',
    justifyContent: 'center',
    backgroundColor: '#FFEBEE',
    marginHorizontal: 16,
    marginTop: 24,
    borderRadius: 12,
    padding: 14,
  },
  logoutText: {
    fontSize: 16,
    color: '#f44336',
    fontWeight: '600',
    marginLeft: 8,
  },
  footer: {
    alignItems: 'center',
    paddingVertical: 24,
    paddingHorizontal: 16,
  },
  footerText: {
    fontSize: 12,
    color: '#999',
    marginBottom: 4,
  },
});
