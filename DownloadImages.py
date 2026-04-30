from psycopg2.extras import execute_values
import time
from typing import Dict, List, Set, Tuple
import requests
import os
from pathlib import Path

def download_pokemon_pics(generations=(1, 2, 3)):
    """Download one picture per Pokemon"""
    
    pokemon_list = []
    
    for gen in generations:
        url = f"https://pokeapi.co/api/v2/generation/{gen}/"
        response = requests.get(url)
        
        if response.status_code == 200:
            data = response.json()
            for species in data.get("pokemon_species", []):
                # Get the national ID
                species_url = species["url"]
                species_response = requests.get(species_url)
                if species_response.status_code == 200:
                    species_data = species_response.json()
                    national_id = species_data.get("id")
                    name = species["name"]
                    pokemon_list.append((national_id, name))
                    print(f"Found: {name}")
    
    print(f"\nDownloading {len(pokemon_list)} pictures...")
    
    counter = 1
    for national_id, name in pokemon_list:
        url = f"https://raw.githubusercontent.com/PokeAPI/sprites/master/sprites/pokemon/other/official-artwork/{national_id}.png"
        
        try:
            response = requests.get(url)
            if response.status_code == 200:
                clean_name = name.lower().replace(" ", "_").replace(".", "").replace("'", "")
                filename = f"PokemonImagesDB/{counter}_{clean_name}.png"
                
                with open(filename, 'wb') as f:
                    f.write(response.content)
                
                print(f"✓ Downloaded: {name}")
            else:
                fallback_url = f"https://raw.githubusercontent.com/PokeAPI/sprites/master/sprites/pokemon/{national_id}.png"
                response = requests.get(fallback_url)
                if response.status_code == 200:
                    clean_name = name.lower().replace(" ", "_")
                    filename = f"PokemonImagesDB/{counter}_{clean_name}.png"
                    with open(filename, 'wb') as f:
                        f.write(response.content)
                    print(f"✓ Downloaded (fallback): {name}")
                else:
                    print(f"✗ Failed: {name}")
            counter += 1
            
            time.sleep(0.2)
            
        except Exception as e:
            print(f"✗ Error: {name} - {e}")
    
    print(f"\nDone! Pictures saved to 'pokemon_pics' folder")

# Run it
if __name__ == "__main__":
    download_pokemon_pics()