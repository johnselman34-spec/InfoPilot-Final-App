import React from 'react';
import { Tabs } from 'expo-router';
import { Ionicons } from '@expo/vector-icons';
import { Platform, View, Text } from 'react-native';
import { colors } from '../../src/utils/colors';

export default function TabLayout() {
  return (
    <Tabs
      screenOptions={{
        tabBarActiveTintColor: colors.primary,
        tabBarInactiveTintColor: colors.gray,
        tabBarStyle: {
          backgroundColor: colors.backgroundAlt,
          borderTopColor: colors.border,
          height: Platform.OS === 'ios' ? 90 : 70,
          paddingBottom: Platform.OS === 'ios' ? 25 : 10,
          paddingTop: 8,
        },
        tabBarLabelStyle: {
          fontSize: 9,
          fontWeight: '600',
        },
        headerStyle: {
          backgroundColor: colors.secondary,
        },
        headerTintColor: colors.white,
        headerTitleStyle: {
          fontWeight: 'bold',
          fontSize: 18,
        },
      }}
    >
      <Tabs.Screen
        name="home"
        options={{
          title: 'Home',
          tabBarIcon: ({ color, size }) => (
            <Ionicons name="home" size={size - 2} color={color} />
          ),
        }}
      />
      <Tabs.Screen
        name="ultimate-search"
        options={{
          title: 'Search',
          tabBarIcon: ({ color, size }) => (
            <Ionicons name="rocket" size={size - 2} color={color} />
          ),
        }}
      />
      <Tabs.Screen
        name="marketplace"
        options={{
          title: 'Market',
          tabBarIcon: ({ color, size }) => (
            <Ionicons name="storefront" size={size - 2} color={color} />
          ),
        }}
      />
      <Tabs.Screen
        name="social"
        options={{
          title: 'Social',
          tabBarIcon: ({ color, size }) => (
            <Ionicons name="people" size={size - 2} color={color} />
          ),
        }}
      />
      <Tabs.Screen
        name="statistics"
        options={{
          title: 'Stats',
          tabBarIcon: ({ color, size }) => (
            <Ionicons name="stats-chart" size={size - 2} color={color} />
          ),
        }}
      />
      <Tabs.Screen
        name="profile"
        options={{
          title: 'Profile',
          tabBarIcon: ({ color, size }) => (
            <Ionicons name="person" size={size - 2} color={color} />
          ),
        }}
      />
      {/* Hidden tabs - accessible but not in tab bar */}
      <Tabs.Screen
        name="search"
        options={{
          href: null, // Hide from tab bar
          title: 'Old Search',
        }}
      />
      <Tabs.Screen
        name="categories"
        options={{
          href: null, // Hide from tab bar
          title: 'Categories',
        }}
      />
      <Tabs.Screen
        name="messages"
        options={{
          href: null, // Hide from tab bar - accessible from Social
          title: 'Messages',
        }}
      />
    </Tabs>
  );
}
