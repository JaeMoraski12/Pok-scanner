import psycopg2
from psycopg2.extras import execute_values
import requests
import time
from typing import Dict, List, Set

def get_pokemon_using_generation(gen = int):
    url = f" https://pokeapi.co/api/v2/generation/{gen}/"
    response = requests.get(url)
    if response.status_code == 200:
        data = response.json()
        pokemon_species = data.get("pokemon_species", []) 
        for species in pokemon_species:
            print(species["name"])
            time.sleep(0.5)  # To avoid hitting API rate limits
            get_national_id(species["name"])
            time.sleep(0.5)
            get_type(species["name"])
    else:
        print(f"Failed to retrieve data for generation {gen}. Status code: {response.status_code}")


def get_national_id(pokemon_name: str) -> int:
    url = f"https://pokeapi.co/api/v2/pokemon/{pokemon_name.lower()}/"
    response = requests.get(url)
    if response.status_code == 200:
        data = response.json()
        print(f"National ID for {pokemon_name}: {data.get('id')}")
        return data.get("id")
    else:
        print(f"Failed to retrieve data for {pokemon_name}. Status code: {response.status_code}")
        return -1

def get_type(pokemon_name: str) -> List[str]:
    url = f"https://pokeapi.co/api/v2/pokemon/{pokemon_name.lower()}/"
    response = requests.get(url)
    if response.status_code == 200:
        data = response.json()
        types = [t['type']['name'] for t in data.get('types', [])]
        print(f"Types for {pokemon_name}: {types}")
        for t in types:
            time.sleep(0.5)
            double_from = get_type_double_damage_from(t)
            time.sleep(0.5)
            double_to = get_type_double_damage_to(t)
            time.sleep(0.5)
            half_from = get_type_half_damage_from(t)
            time.sleep(0.5)
            half_to = get_type_half_damage_to(t)
            time.sleep(0.5)
            no_from = get_type_no_damage_from(t)
            time.sleep(0.5)
            no_to = get_type_no_damage_to(t)
            time.sleep(0.5)
            evolution = get_evolution_chain(pokemon_name)
            time.sleep(0.5) 
            
        return types
    else:
        print(f"Failed to retrieve data for {pokemon_name}. Status code: {response.status_code}")
        return []

def get_type_double_damage_from(type_name: str) -> List[str]:
    url = f"https://pokeapi.co/api/v2/type/{type_name.lower()}/"
    response = requests.get(url)
    if response.status_code == 200:
        data = response.json()
        double_damage_from = [d['name'] for d in data.get('damage_relations', {}).get('double_damage_from', [])]
        print(f"Double damage from for {type_name}: {double_damage_from}")
        return double_damage_from
    else:
        print(f"Failed to retrieve data for type {type_name}. Status code: {response.status_code}")
        return []
    
def get_type_double_damage_to(type_name: str) -> List[str]:
    url = f"https://pokeapi.co/api/v2/type/{type_name.lower()}/"
    response = requests.get(url)
    if response.status_code == 200:
        data = response.json()
        double_damage_to = [d['name'] for d in data.get('damage_relations', {}).get('double_damage_to', [])]
        print(f"Double damage to for {type_name}: {double_damage_to}")
        return double_damage_to
    else:
        print(f"Failed to retrieve data for type {type_name}. Status code: {response.status_code}")
        return []
    
def get_type_half_damage_from(type_name: str) -> List[str]:
    url = f"https://pokeapi.co/api/v2/type/{type_name.lower()}/"
    response = requests.get(url)
    if response.status_code == 200:
        data = response.json()
        half_damage_from = [d['name'] for d in data.get('damage_relations', {}).get('half_damage_from', [])]
        print(f"Half damage from for {type_name}: {half_damage_from}")
        return half_damage_from
    else:
        print(f"Failed to retrieve data for type {type_name}. Status code: {response.status_code}")
        return []
    
def get_type_half_damage_to(type_name: str) -> List[str]:
    url = f"https://pokeapi.co/api/v2/type/{type_name.lower()}/"
    response = requests.get(url)
    if response.status_code == 200:
        data = response.json()
        half_damage_to = [d['name'] for d in data.get('damage_relations', {}).get('half_damage_to', [])]
        print(f"Half damage to for {type_name}: {half_damage_to}")
        return half_damage_to
    else:
        print(f"Failed to retrieve data for type {type_name}. Status code: {response.status_code}")
        return []
    
def get_type_no_damage_from(type_name: str) -> List[str]:
    url = f"https://pokeapi.co/api/v2/type/{type_name.lower()}/"
    response = requests.get(url)
    if response.status_code == 200:
        data = response.json()
        no_damage_from = [d['name'] for d in data.get('damage_relations', {}).get('no_damage_from', [])]
        if no_damage_from:
            print(f"No damage from for {type_name}: {no_damage_from}")
        else:
            print(f"No damage from for {type_name}: None")
        return no_damage_from
    else:
        print(f"Failed to retrieve data for type {type_name}. Status code: {response.status_code}")
        return []
    
def get_type_no_damage_to(type_name: str) -> List[str]:
    url = f"https://pokeapi.co/api/v2/type/{type_name.lower()}/"
    response = requests.get(url)
    if response.status_code == 200:
        data = response.json()
        no_damage_to = [d['name'] for d in data.get('damage_relations', {}).get('no_damage_to', [])]
        if no_damage_to:
            print(f"No damage to for {type_name}: {no_damage_to}")
        else:
            print(f"No damage to for {type_name}: None")
        return no_damage_to
    else:
        print(f"Failed to retrieve data for type {type_name}. Status code: {response.status_code}")
        return []
    
def get_evolution_chain(pokemon_name: str) -> List[str]:
    url = f"https://pokeapi.co/api/v2/pokemon-species/{pokemon_name.lower()}/"
    response = requests.get(url)
    if response.status_code == 200:
        data = response.json()
        url = data.get('evolution_chain', {}).get('url')
        if url: 
            response = requests.get(url)
            if response.status_code == 200:
                data = response.json()
                chain = data.get('chain', {})
                evolutions = []
                def traverse_chain(node):
                    species_name = node.get('species', {}).get('name')
                    if species_name:
                        evolutions.append(species_name)
                    for evo in node.get('evolves_to', []):
                        traverse_chain(evo)
                traverse_chain(chain)
                print(f"Evolution chain for {pokemon_name}: {evolutions}")
                return evolutions
            else:
                print(f"Failed to retrieve evolution chain for {pokemon_name}. Status code: {response.status_code}")
                return []

def insert_pokemon_data(conn, pokemon_data):
    with conn.cursor() as cur:
        insert_query = """
            INSERT INTO Pokemon (national_dex_number, pokemon_name, pokemon_speed, generation_id)
            VALUES %s
            ON CONFLICT (national_dex_number) DO NOTHING
        """
        execute_values(cur, insert_query, pokemon_data)
    conn.commit()
    
    
if __name__ == "__main__":
    try:
        conn = psycopg2.connect(
            host="localhost",
            port = "5433",
            database="postgres",
            user="postgres",
            password="admin",
        )
        print("Connected to the database successfully!")
        conn.close()
    except Exception as e:
        print("Error connecting to the database:", e)
    get_pokemon_using_generation(2)

