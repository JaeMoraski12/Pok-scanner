import { Stack } from "expo-router";

export default function RootLayout() {
  return(
    <Stack
      screenOptions={{
        headerStyle: {
          backgroundColor: '#f5f5f5',
        },
        headerTintColor: '#2c3e50',
        headerTitleStyle: {
          fontWeight: 'bold',
        },
      }}
    >
      <Stack.Screen
        name="index"
        options={{
          title: 'Pokémon AI Scanner',
          headerTitleAlign: 'center',
          headerShown: true,
        }}
      />
      <Stack.Screen
        name="scanner"
        options={{
          title: 'AI Scanner',
          headerShown: true,
          headerBackTitle: 'Back',
        }}
      />
      <Stack.Screen
        name="pokedex"
        options={{
          title: 'Pokédex',
          headerShown: false, 
        }}
      />
    </Stack>
  );
}