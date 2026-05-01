import React from 'react';
import { 
  View,          
  Text,          
  TouchableOpacity, 
  StyleSheet    
} from 'react-native';
import { SafeAreaView } from 'react-native-safe-area-context';

import { router } from 'expo-router';

export default function StartScreen() {
  const goToPokedex = () => {
    router.push('/pokedex'); 
  };

  const goToAIScanner = () => {
    router.push('/scanner'); 
  };

  return (
    <SafeAreaView style={styles.container}>
      
      <View style={styles.titleContainer}>
        <Text style={styles.title}>Pokémon AI Scanner</Text>
        <Text style={styles.subtitle}>Choose your adventure</Text>
      </View>

      <View style={styles.buttonContainer}>
        {/* Pokedex Button - TOP */}
        <TouchableOpacity 
          style={[styles.button, styles.pokedexButton]}
          onPress={goToPokedex}
          activeOpacity={0.7}
        >
          <Text style={styles.buttonText}>📖 View Pokédex</Text>
        </TouchableOpacity>

        {/* AI Scanner Button - BOTTOM */}
        <TouchableOpacity 
          style={[styles.button, styles.aiButton]}
          onPress={goToAIScanner}
          activeOpacity={0.7}
        >
          <Text style={styles.buttonText}>🤖 AI Scanner</Text>
        </TouchableOpacity>
      </View>
      
    </SafeAreaView>
  );
}

// --- Styles ---
const styles = StyleSheet.create({
  container: {
    flex: 1,
    justifyContent: 'center',
    alignItems: 'center',
    backgroundColor: '#f5f5f5',
    paddingHorizontal: 20,
  },
  titleContainer: {
    alignItems: 'center',
    marginBottom: 60,
  },
  title: {
    fontSize: 28,
    fontWeight: 'bold',
    color: '#2c3e50',
    marginBottom: 10,
  },
  subtitle: {
    fontSize: 16,
    color: '#7f8c8d',
  },
  buttonContainer: {
    width: '100%',
    gap: 20,
  },
  button: {
    paddingVertical: 15,
    paddingHorizontal: 30,
    borderRadius: 12,
    alignItems: 'center',
    width: '100%',
  },
  pokedexButton: {
    backgroundColor: '#3498db',
  },
  aiButton: {
    backgroundColor: '#e74c3c',
  },
  buttonText: {
    color: 'white',
    fontSize: 18,
    fontWeight: '600',
  },
});