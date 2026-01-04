import React, { useEffect, useState } from 'react';
import { Stack } from 'expo-router';
import { useAuthStore } from '../src/store/authStore';
import { ActivityIndicator, View, Text } from 'react-native';
import { colors } from '../src/utils/colors';

export default function RootLayout() {
  const [isReady, setIsReady] = useState(false);

  useEffect(() => {
    let isMounted = true;

    const initializeApp = async () => {
      try {
        console.log('🚀 App initialization started');
        
        // Load user with a shorter timeout
        await useAuthStore.getState().loadUser();
        
        console.log('✅ User loaded successfully');
      } catch (err) {
        console.error('❌ Load user error:', err);
        // Continue anyway - user might not be logged in
      } finally {
        if (isMounted) {
          console.log('✅ App ready - showing content');
          setIsReady(true);
        }
      }
    };

    // Set a maximum timeout of 3 seconds
    const maxTimeout = setTimeout(() => {
      if (isMounted) {
        console.log('⏱️ Max timeout reached - forcing app to show');
        setIsReady(true);
      }
    }, 3000);

    initializeApp();

    return () => {
      isMounted = false;
      clearTimeout(maxTimeout);
    };
  }, []);

  if (!isReady) {
    return (
      <View style={{ flex: 1, justifyContent: 'center', alignItems: 'center', backgroundColor: colors.background }}>
        <ActivityIndicator size="large" color={colors.primary} />
        <Text style={{ marginTop: 16, color: colors.text }}>Loading InfoPilot...</Text>
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
