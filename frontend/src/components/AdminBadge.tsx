import React from 'react';
import { View, Text, StyleSheet } from 'react-native';
import { Ionicons } from '@expo/vector-icons';
import { colors } from '../utils/colors';

interface AdminBadgeProps {
  isAdmin: boolean;
  style?: any;
}

export const AdminBadge: React.FC<AdminBadgeProps> = ({ isAdmin, style }) => {
  if (!isAdmin) return null;

  return (
    <View style={[styles.badge, style]}>
      <Ionicons name="shield-checkmark" size={16} color={colors.marketplaceGold} />
      <Text style={styles.badgeText}>ADMIN</Text>
    </View>
  );
};

const styles = StyleSheet.create({
  badge: {
    flexDirection: 'row',
    alignItems: 'center',
    backgroundColor: colors.secondary, // Electric purple
    paddingHorizontal: 12,
    paddingVertical: 6,
    borderRadius: 20,
    borderWidth: 2,
    borderColor: colors.marketplaceGold, // Gold border
    shadowColor: colors.marketplaceGold,
    shadowOffset: { width: 0, height: 2 },
    shadowOpacity: 0.5,
    shadowRadius: 4,
    elevation: 5,
  },
  badgeText: {
    color: colors.marketplaceGold,
    fontSize: 12,
    fontWeight: 'bold',
    marginLeft: 4,
    letterSpacing: 1,
  },
});
