import React, { useEffect, useState } from 'react';
import { Stack } from 'expo-router';
import { useAuthStore } from '../src/store/authStore';
import { ActivityIndicator, View, Text } from 'react-native';
import { colors } from '../src/utils/colors';

export default function RootLayout() {
  const [showContent, setShowContent] = useState(false);

  useEffect(() => {
    // FORCE the app to show content after 2 seconds no matter what
    const forceTimeout = setTimeout(() => {
      console.log('FORCE TIMEOUT: Showing content now');
      setShowContent(true);
    }, 2000);

    // Try to load user but don't wait for it
    useAuthStore.getState().loadUser().catch(err => {
      console.error('Load user error:', err);
    }).finally(() => {
      setShowContent(true);
      clearTimeout(forceTimeout);
    });

    // Cleanup
    return () => {
      clearTimeout(forceTimeout);
      setShowContent(true); // Ensure we show content on unmount
    };
  }, []);

  // Always show content after component mounts or 2 seconds
  if (!showContent) {
    return (
      <View style={{ flex: 1, justifyContent: 'center', alignItems: 'center', backgroundColor: colors.background }}>
        <ActivityIndicator size="large" color={colors.primary} />
        <Text style={{ marginTop: 16, color: colors.text }}>Loading...</Text>
      </View>
    );
  }

  return (
    <Stack
      screenOptions={{
        headerStyle: {
          backgroundColor: colors.primary,
        },
        headerTintColor: colors.white,
        headerTitleStyle: {
          fontWeight: 'bold',
        },
      }}
    >
      <Stack.Screen name="index" options={{ headerShown: false }} />
      <Stack.Screen name="auth/login" options={{ title: 'Login', headerShown: false }} />
      <Stack.Screen name="auth/register" options={{ title: 'Register', headerShown: false }} />
      <Stack.Screen name="(tabs)" options={{ headerShown: false }} />
    </Stack>
  );
}
