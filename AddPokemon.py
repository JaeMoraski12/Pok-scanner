import psycopg2
from psycopg2.extras import execute_values
import requests
import time
from typing import Dict, List, Set, Tuple

types_id = ['normal', 'fighting', 'flying', 'poison', 'ground', 'rock', 'bug', 'ghost', 'steel', 'fire', 'water', 'grass', 'electric', 'psychic', 'ice', 'dragon', 'dark', 'fairy', 'stellar', 'unknown']

def get_type_id(conn, type_name: str) -> int:
    """Get type_id from TypeChart table"""
    with conn.cursor() as cur:
        cur.execute("SELECT type_id FROM TypeChart WHERE type_name = %s", (type_name,))
        result = cur.fetchone()
        return result[0] if result else None

def pokemon_exists(conn, name: str = None, national_id: int = None) -> bool:
    """Check if a Pokemon already exists in the database"""
    with conn.cursor() as cur:
        if name:
            cur.execute("SELECT 1 FROM Pokemon WHERE pokemon_name = %s", (name,))
        elif national_id:
            cur.execute("SELECT 1 FROM Pokemon WHERE national_dex_number = %s", (national_id,))
        else:
            return False
        return cur.fetchone() is not None

def insert_pokemon(conn, national_id: int, name: str, speed: int, generation_id: int):
    """Insert Pokemon into Pokemon table"""
    with conn.cursor() as cur:
        cur.execute("""
            INSERT INTO Pokemon (national_dex_number, pokemon_name, pokemon_speed, generation_id)
            VALUES (%s, %s, %s, %s)
            ON CONFLICT (national_dex_number) DO UPDATE 
            SET pokemon_name = EXCLUDED.pokemon_name,
                pokemon_speed = EXCLUDED.pokemon_speed,
                generation_id = EXCLUDED.generation_id
            RETURNING pokemon_id
        """, (national_id, name, speed, generation_id))
        return cur.fetchone()[0]

def insert_type(conn):
    """Insert all Pokemon types into TypeChart table"""
    url = "https://pokeapi.co/api/v2/type/"
    response = requests.get(url)
    
    if response.status_code == 200:
        data = response.json()
        with conn.cursor() as cur:
            for type_data in data.get("results", []):
                type_name = type_data["name"]
                if type_name in types_id:  
                    cur.execute("""
                        INSERT INTO TypeChart (type_name)
                        VALUES (%s)
                        ON CONFLICT (type_name) DO NOTHING
                    """, (type_name,))
        conn.commit()
        print("Types inserted successfully!")
    else:
        print(f"Failed to retrieve types. Status code: {response.status_code}")

def insert_generation(conn):
    """Insert generations into GenerationChart table"""
    generations = [
        (1, "Generation I"),
        (2, "Generation II"),
        (3, "Generation III"),
        (4, "Generation IV"),
        (5, "Generation V"),
        (6, "Generation VI"),
        (7, "Generation VII"),
        (8, "Generation VIII"),
        (9, "Generation IX")
    ]
    
    with conn.cursor() as cur:
        for gen_id, gen_name in generations:
            cur.execute("""
                INSERT INTO GenerationChart (generation_id, generation_name)
                VALUES (%s, %s)
                ON CONFLICT (generation_id) DO NOTHING
            """, (gen_id, gen_name))
    conn.commit()

def insert_pokemon_types(conn, pokemon_id: int, type_names: List[str]):
    """Insert Pokemon type relationships"""
    with conn.cursor() as cur:
        for type_name in type_names:
            type_id = get_type_id(conn, type_name)
            if type_id:
                cur.execute("""
                    INSERT INTO PokemonTypes (pokemon_id, type_id)
                    VALUES (%s, %s)
                    ON CONFLICT (pokemon_id, type_id) DO NOTHING
                """, (pokemon_id, type_id))
    conn.commit()

def insert_damage_relations(conn, pokemon_id: int, damage_data: Tuple):
    """Insert all damage relation data"""
    double_from, double_to, half_from, half_to, no_from, no_to = damage_data
    
    
    damage_mappings = [
        ("DoubleDamageFromChart", double_from),
        ("DoubleDamageToChart", double_to),
        ("HalfDamageFromChart", half_from),
        ("HalfDamageToChart", half_to),
        ("NoDamageFromChart", no_from),
        ("NoDamageToChart", no_to)
    ]
    
    with conn.cursor() as cur:
        for table_name, damage_list in damage_mappings:
            for type_name in damage_list:
                type_id = get_type_id(conn, type_name)
                if type_id:
                    cur.execute(f"""
                        INSERT INTO {table_name} (pokemon_id, type_id)
                        VALUES (%s, %s)
                        ON CONFLICT (pokemon_id, type_id) DO NOTHING
                    """, (pokemon_id, type_id))
    conn.commit()

def get_pokemon_generation(pokemon_name: str) -> int:
    """Get the generation number for a Pokémon from the PokeAPI"""
    try:
        url = f"https://pokeapi.co/api/v2/pokemon-species/{pokemon_name.lower()}/"
        response = requests.get(url)
        if response.status_code == 200:
            data = response.json()
            # Get generation from the API response
            generation_url = data.get('generation', {}).get('url', '')
            if generation_url:
                # Extract generation number from URL (e.g., "https://pokeapi.co/api/v2/generation/1/")
                gen_num = int(generation_url.rstrip('/').split('/')[-1])
                return gen_num
        return None
    except Exception as e:
        print(f"Error getting generation for {pokemon_name}: {e}")
        return None

def filter_evolution_chain_by_generation(conn, evolution_chain: List[str], target_generations: Set[int]) -> List[str]:
    """
    Filter evolution chain to only include Pokémon from specified generations.
    
    Args:
        conn: Database connection
        evolution_chain: List of Pokémon names in evolution order
        target_generations: Set of generation numbers to keep (e.g., {1, 2, 3})
    
    Returns:
        Filtered list of Pokémon names that are in target generations
    """
    if not evolution_chain:
        return []
    
    filtered_chain = []
    skipped_pokemon = []
    
    for pokemon_name in evolution_chain:
        # First check if Pokémon is already in database
        if pokemon_exists(conn, name=pokemon_name):
            # If it exists, we need to get its generation from the database
            with conn.cursor() as cur:
                cur.execute("SELECT generation_id FROM Pokemon WHERE pokemon_name = %s", (pokemon_name,))
                result = cur.fetchone()
                if result and result[0] in target_generations:
                    filtered_chain.append(pokemon_name)
                else:
                    skipped_pokemon.append(f"{pokemon_name} (Gen {result[0] if result else 'Unknown'})")
        else:
            # Pokémon not in database yet, check its generation from API
            generation = get_pokemon_generation(pokemon_name)
            if generation and generation in target_generations:
                filtered_chain.append(pokemon_name)
            else:
                if generation:
                    skipped_pokemon.append(f"{pokemon_name} (Gen {generation})")
                else:
                    skipped_pokemon.append(f"{pokemon_name} (Generation Unknown)")
    
    if skipped_pokemon:
        print(f"  ⚠ Skipped Pokémon not in Generations {sorted(target_generations)}: {', '.join(skipped_pokemon)}")
    
    return filtered_chain

def insert_evolution_chain(conn, evolutions: List[str], target_generations: Set[int] = {1, 2, 3}):
    """
    Insert evolution relationships, filtering to only include Pokémon from target generations.
    
    Args:
        conn: Database connection
        evolutions: List of Pokémon names in evolution order
        target_generations: Set of generation numbers to include (default: {1, 2, 3})
    """
    if len(evolutions) < 2:
        return
    
    # Filter evolution chain to only include target generations
    filtered_evolutions = filter_evolution_chain_by_generation(conn, evolutions, target_generations)
    
    if len(filtered_evolutions) < 2:
        if filtered_evolutions:
            print(f"  ℹ Only 1 Pokémon from Generations {sorted(target_generations)} in chain: {filtered_evolutions[0]}")
        else:
            print(f"  ℹ No Pokémon from Generations {sorted(target_generations)} in evolution chain")
        return
    
    pokemon_ids = []
    with conn.cursor() as cur:
        for name in filtered_evolutions:
            cur.execute("SELECT pokemon_id, pokemon_name FROM Pokemon WHERE pokemon_name = %s", (name,))
            result = cur.fetchone()
            if result:
                pokemon_ids.append((result[0], result[1]))
            else:
                print(f"  ⚠ Warning: {name} not found in database yet, will skip this evolution link")
                return
    
    links_added = 0
    with conn.cursor() as cur:
        for i in range(len(pokemon_ids) - 1):
            current_id, current_name = pokemon_ids[i]
            next_id, next_name = pokemon_ids[i + 1]
            
            # Delete any existing link from current to next
            cur.execute("""
                DELETE FROM PokemonEvolutions 
                WHERE pokemon_id = %s AND evolves_to_id = %s
            """, (current_id, next_id))
            
            try:
                cur.execute("""
                    INSERT INTO PokemonEvolutions (pokemon_id, evolves_to_id, evolution_stage)
                    VALUES (%s, %s, %s)
                    ON CONFLICT (pokemon_id, evolves_to_id) DO NOTHING
                """, (current_id, next_id, i + 1))
                links_added += 1
                print(f"  ✓ Linked: {current_name} → {next_name}")
            except Exception as e:
                print(f"  ✗ Error linking {current_name} → {next_name}: {e}")
    
    conn.commit()
    if links_added > 0:
        evolution_path = ' → '.join(filtered_evolutions)
        print(f"  ✓ Added {links_added} evolution link(s) for chain: {evolution_path}")

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

def get_speed(pokemon_name: str) -> int:
    url = f"https://pokeapi.co/api/v2/pokemon/{pokemon_name.lower()}/"
    response = requests.get(url)
    if response.status_code == 200:
        data = response.json()
        for stat in data.get('stats', []):
            if stat['stat']['name'] == 'speed':
                print(f"Speed for {pokemon_name}: {stat['base_stat']}")
                return stat['base_stat']
        print(f"Speed for {pokemon_name}: Not found")
        return -1
    else:
        print(f"Failed to retrieve data for {pokemon_name}. Status code: {response.status_code}")
        return -1

def get_type(pokemon_name: str) -> Tuple[List[str], List[str], List[str], List[str], List[str], List[str]]:
    url = f"https://pokeapi.co/api/v2/pokemon/{pokemon_name.lower()}/"
    response = requests.get(url)
    if response.status_code == 200:
        data = response.json()
        types = [t['type']['name'] for t in data.get('types', [])]
        print(f"Types for {pokemon_name}: {types}")

        double_from = []
        double_to = []
        half_from = []
        half_to = []
        no_from = []
        no_to = []
        
        for t in types:
            time.sleep(0.5)
            double_from += get_type_double_damage_from(t)
            time.sleep(0.5)
            double_to += get_type_double_damage_to(t)
            time.sleep(0.5)
            half_from += get_type_half_damage_from(t)
            time.sleep(0.5)
            half_to += get_type_half_damage_to(t)
            time.sleep(0.5)
            no_from += get_type_no_damage_from(t)
            time.sleep(0.5)
            no_to += get_type_no_damage_to(t)
        
        # Remove duplicates
        return (list(set(double_from)), list(set(double_to)), 
                list(set(half_from)), list(set(half_to)), 
                list(set(no_from)), list(set(no_to)))
    else:
        print(f"Failed to retrieve data for {pokemon_name}. Status code: {response.status_code}")
        return ([], [], [], [], [], [])

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
    """Get the complete evolution chain for a Pokémon"""
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
                print(f"Complete evolution chain for {pokemon_name}: {evolutions}")
                return evolutions
            else:
                print(f"Failed to retrieve evolution chain for {pokemon_name}. Status code: {response.status_code}")
                return []
    return []

def process_generation(conn, gen_num: int, target_generations: Set[int] = {1, 2, 3}):
    """Process all Pokemon from a specific generation"""
    url = f"https://pokeapi.co/api/v2/generation/{gen_num}/"
    response = requests.get(url)
    
    if response.status_code == 200:
        data = response.json()
        pokemon_species = data.get("pokemon_species", [])
        
        # Track statistics
        total = len(pokemon_species)
        new_count = 0
        skipped_count = 0
        
        for species in pokemon_species:
            name = species["name"]
            
            # Check if Pokemon already exists in database
            if pokemon_exists(conn, name=name):
                print(f"\n📌 Skipping {name} - already in database")
                skipped_count += 1
                continue
            
            print(f"\n{'='*50}")
            print(f"Processing {name}...")
            print(f"{'='*50}")
            
            # Get Pokemon data
            national_id = get_national_id(name)
            time.sleep(0.5)
            
            if national_id == -1:
                continue
                
            speed = get_speed(name)
            time.sleep(0.5)
            
            if speed == -1:
                continue
                
            types = get_type(name)
            time.sleep(0.5)
            
            evolution_chain = get_evolution_chain(name)
            time.sleep(0.5)
            
            # Insert into database
            pokemon_id = insert_pokemon(conn, national_id, name, speed, gen_num)
            
            # Get the type names from the Pokemon
            url_pokemon = f"https://pokeapi.co/api/v2/pokemon/{name.lower()}/"
            pokemon_response = requests.get(url_pokemon)
            if pokemon_response.status_code == 200:
                pokemon_data = pokemon_response.json()
                type_names = [t['type']['name'] for t in pokemon_data.get('types', [])]
                insert_pokemon_types(conn, pokemon_id, type_names)
            
            # Insert damage relations
            insert_damage_relations(conn, pokemon_id, types)
            
            # Insert evolution chain with generation filtering
            print(f"\n  🔄 Processing evolution chain for {name}...")
            insert_evolution_chain(conn, evolution_chain, target_generations)
            
            print(f"\n✅ Successfully inserted {name}!")
            new_count += 1
        
        # Print generation summary
        print(f"\n{'='*50}")
        print(f"📊 Generation {gen_num} Summary:")
        print(f"{'='*50}")
        print(f"  Total Pokemon in generation: {total}")
        print(f"  Newly added: {new_count}")
        print(f"  Already existed (skipped): {skipped_count}")
        print(f"{'='*50}")
            
    else:
        print(f"Failed to retrieve data for generation {gen_num}. Status code: {response.status_code}")

if __name__ == "__main__":
    conn = None
    try:
        conn = psycopg2.connect(
            host="localhost",
            port="5433",
            database="PokemonScanner",
            user="postgres",
            password="admin",
        )
        print("✅ Connected to the database successfully!")
        
        # Initialize lookup tables
        insert_generation(conn)
        insert_type(conn)
        
        # Define which generations to include in evolution chains
        # Only include Pokémon from Generations 1, 2, and 3 in evolution relationships
        target_evolution_generations = {1, 2, 3}
        
        print(f"\n🎯 Evolution chains will only include Pokémon from Generations: {sorted(target_evolution_generations)}")
        print("   (Pokémon from later generations will be ignored in evolution links)\n")
        
        # Process generations 1-3
        for gen in range(1, 4):
            print(f"\n{'#'*50}")
            print(f"# PROCESSING GENERATION {gen}")
            print(f"{'#'*50}")
            process_generation(conn, gen, target_evolution_generations)
        
        conn.commit()
        print("\n🎉 All data inserted successfully!")
        
        # Print final summary
        print("\n" + "="*50)
        print("📊 FINAL SUMMARY")
        print("="*50)
        with conn.cursor() as cur:
            cur.execute("SELECT COUNT(*) FROM Pokemon")
            total_pokemon = cur.fetchone()[0]
            cur.execute("SELECT COUNT(*) FROM PokemonEvolutions")
            total_evolutions = cur.fetchone()[0]
            print(f"  Total Pokémon in database: {total_pokemon}")
            print(f"  Total evolution links: {total_evolutions}")
        print("="*50)
        
    except Exception as e:
        print(f"❌ Error: {e}")
        if conn:
            conn.rollback()
    finally:
        if conn:
            conn.close()
            print("\n🔌 Database connection closed.")