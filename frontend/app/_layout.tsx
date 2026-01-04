import React, { useEffect, useState } from 'react';
import { Stack } from 'expo-router';
import { useAuthStore } from '../src/store/authStore';
import { ActivityIndicator, View } from 'react-native';
import { colors } from '../src/utils/colors';

export default function RootLayout() {
  const { isLoading, loadUser } = useAuthStore();
  const [initializing, setInitializing] = useState(true);

  useEffect(() => {
    // Set a maximum 3-second initialization time
    const timeout = setTimeout(() => {
      setInitializing(false);
    }, 3000);

    loadUser().finally(() => {
      clearTimeout(timeout);
      setInitializing(false);
    });

    return () => clearTimeout(timeout);
  }, []);

  if (initializing) {
    return (
      <View style={{ flex: 1, justifyContent: 'center', alignItems: 'center', backgroundColor: colors.background }}>
        <ActivityIndicator size="large" color={colors.primary} />
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
