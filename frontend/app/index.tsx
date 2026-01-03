import React, { useEffect } from 'react';
import { View, Text, ActivityIndicator, StyleSheet } from 'react-native';
import { useRouter } from 'expo-router';
import { useAuthStore } from '../store/authStore';

export default function IndexScreen() {
  const router = useRouter();
  const { user, checkAuth } = useAuthStore();

  useEffect(() => {
    const init = async () => {
      await checkAuth();
      setTimeout(() => {
        if (user) {
          router.replace('/(tabs)/home');
        } else {
          router.replace('/(auth)/login');
        }
      }, 500);
    };
    init();
  }, []);

  return (
    <View style={styles.container}>
      <Text style={styles.title}>InfoPilot</Text>
      <ActivityIndicator size="large" color="#1E88E5" style={styles.loader} />
    </View>
  );
}

const styles = StyleSheet.create({
  container: {
    flex: 1,
    justifyContent: 'center',
    alignItems: 'center',
    backgroundColor: '#F5F9FC',
  },
  title: {
    fontSize: 42,
    fontWeight: 'bold',
    color: '#1E88E5',
    marginBottom: 24,
  },
  loader: {
    marginTop: 16,
  },
});
