import requests
import psycopg2
from psycopg2 import sql
import time
from typing import Optional, Dict, List, Tuple, Set

class PokemonEvolutionChecker:
    def __init__(self, db_params: Dict):
        """
        Initialize the evolution checker with database parameters.
        
        Args:
            db_params: Dictionary containing database connection parameters
                      (dbname, user, password, host, port)
        """
        self.db_params = db_params
        self.conn = None
        self.cursor = None
        self.known_pokemon_names: Set[str] = set()  # Cache of Pokémon names in database
        
    def connect_to_db(self):
        """Establish database connection."""
        try:
            self.conn = psycopg2.connect(**self.db_params)
            self.cursor = self.conn.cursor()
            print("✓ Connected to database successfully")
            
            # Load all Pokémon names into cache for quick lookup
            self.cursor.execute("SELECT LOWER(pokemon_name) FROM Pokemon")
            self.known_pokemon_names = {row[0] for row in self.cursor.fetchall()}
            print(f"✓ Loaded {len(self.known_pokemon_names)} Pokémon names into cache")
            
        except Exception as e:
            print(f"✗ Failed to connect to database: {e}")
            raise
    
    def disconnect_from_db(self):
        """Close database connection."""
        if self.cursor:
            self.cursor.close()
        if self.conn:
            self.conn.close()
            print("✓ Database connection closed")
    
    def is_pokemon_in_database(self, pokemon_name: str) -> bool:
        """Check if a Pokémon exists in the database."""
        return pokemon_name.lower() in self.known_pokemon_names
    
    def get_pokemon_from_db(self, generation_id: int = None) -> List[Tuple[int, str]]:
        """
        Retrieve Pokémon from the database, optionally filtered by generation.
        
        Args:
            generation_id: Optional generation ID to filter by (1-3)
            
        Returns:
            List of tuples containing (pokemon_id, pokemon_name)
        """
        try:
            if generation_id:
                query = """
                    SELECT p.pokemon_id, p.pokemon_name 
                    FROM Pokemon p
                    WHERE p.generation_id = %s
                    ORDER BY p.pokemon_id
                """
                self.cursor.execute(query, (generation_id,))
            else:
                query = """
                    SELECT pokemon_id, pokemon_name 
                    FROM Pokemon 
                    ORDER BY pokemon_id
                """
                self.cursor.execute(query)
            
            pokemon_list = self.cursor.fetchall()
            print(f"✓ Retrieved {len(pokemon_list)} Pokémon from database" + 
                  (f" (Generation {generation_id})" if generation_id else ""))
            return pokemon_list
        except Exception as e:
            print(f"✗ Failed to retrieve Pokémon from database: {e}")
            return []
    
    def fetch_evolution_chain_from_api(self, pokemon_name: str) -> Optional[Dict]:
        """
        Fetch evolution chain data from PokeAPI for a specific Pokémon.
        
        Args:
            pokemon_name: Name of the Pokémon
            
        Returns:
            Evolution chain data or None if not found
        """
        try:
            # First, get the Pokémon species data
            species_url = f"https://pokeapi.co/api/v2/pokemon-species/{pokemon_name.lower()}"
            species_response = requests.get(species_url)
            
            if species_response.status_code != 200:
                print(f"  ⚠ Could not fetch species data for {pokemon_name}")
                return None
            
            species_data = species_response.json()
            
            # Get the evolution chain URL
            evolution_chain_url = species_data.get('evolution_chain', {}).get('url')
            if not evolution_chain_url:
                print(f"  ℹ No evolution chain URL found for {pokemon_name}")
                return None
            
            # Fetch the evolution chain
            evolution_response = requests.get(evolution_chain_url)
            if evolution_response.status_code != 200:
                print(f"  ⚠ Could not fetch evolution chain for {pokemon_name}")
                return None
            
            return evolution_response.json()
            
        except Exception as e:
            print(f"  ✗ Error fetching evolution data for {pokemon_name}: {e}")
            return None
    
    def find_pokemon_in_evolution_chain(self, evolution_chain: Dict, target_name: str) -> Optional[Dict]:
        """
        Recursively search for a Pokémon in the evolution chain and get its evolution info.
        Filters out Pokémon not in the database.
        
        Args:
            evolution_chain: Evolution chain data from PokeAPI
            target_name: Name of the Pokémon to find
            
        Returns:
            Dictionary containing evolution information for the target Pokémon
        """
        def search_chain(chain_link: Dict, target: str, chain: List[str] = None):
            if chain is None:
                chain = []
            
            current_species = chain_link.get('species', {})
            current_name = current_species.get('name', '')
            
            # Add current Pokémon to the chain
            current_chain = chain + [current_name]
            
            if current_name == target:
                # Found the target Pokémon - now filter evolutions that exist in DB
                evolves_from = current_chain[-2] if len(current_chain) > 1 else None
                
                # Filter evolves_to to only include Pokémon in database
                evolves_to_list = []
                for evo in chain_link.get('evolves_to', []):
                    evo_name = evo['species']['name']
                    if self.is_pokemon_in_database(evo_name):
                        evolves_to_list.append(evo_name)
                    else:
                        print(f"    ⚠ Skipping evolution '{evo_name}' - not in database")
                
                # Also check if evolves_from exists in database
                if evolves_from and not self.is_pokemon_in_database(evolves_from):
                    print(f"    ⚠ Skipping evolves_from '{evolves_from}' - not in database")
                    evolves_from = None
                
                return {
                    'pokemon_name': target,
                    'evolution_stage': len(current_chain),
                    'evolves_from': evolves_from,
                    'evolves_to': evolves_to_list
                }
            
            # Search through evolutions
            for evolution in chain_link.get('evolves_to', []):
                result = search_chain(evolution, target, current_chain)
                if result:
                    return result
            
            return None
        
        return search_chain(evolution_chain, target_name.lower())
    
    def check_evolution_exists(self, pokemon_id: int) -> bool:
        """
        Check if a Pokémon already has evolution records in the database.
        
        Args:
            pokemon_id: ID of the Pokémon
            
        Returns:
            True if evolution records exist, False otherwise
        """
        try:
            query = """
                SELECT COUNT(*) 
                FROM PokemonEvolutions 
                WHERE pokemon_id = %s
            """
            self.cursor.execute(query, (pokemon_id,))
            count = self.cursor.fetchone()[0]
            return count > 0
        except Exception as e:
            print(f"  ✗ Error checking existing evolution records: {e}")
            return True  # Assume exists to avoid errors
    
    def delete_existing_evolution_records(self, pokemon_id: int):
        """
        Delete existing evolution records for a Pokémon.
        
        Args:
            pokemon_id: ID of the Pokémon
        """
        try:
            query = "DELETE FROM PokemonEvolutions WHERE pokemon_id = %s"
            self.cursor.execute(query, (pokemon_id,))
            self.conn.commit()
            return True
        except Exception as e:
            print(f"  ✗ Error deleting evolution records: {e}")
            self.conn.rollback()
            return False
    
    def update_evolution_record(self, pokemon_id: int, evolution_info: Dict):
        """
        Update or insert evolution record for a Pokémon.
        
        Args:
            pokemon_id: Pokémon ID in database
            evolution_info: Evolution information from API
        """
        try:
            # Get the IDs for evolves_from and evolves_to if they exist (and are in DB)
            evolves_from_id = None
            evolves_to_id = None
            
            if evolution_info.get('evolves_from'):
                evolves_from_id = self.get_pokemon_id_by_name(evolution_info['evolves_from'])
                if not evolves_from_id:
                    print(f"    ⚠ Could not find ID for evolves_from: {evolution_info['evolves_from']}")
            
            if evolution_info.get('evolves_to') and len(evolution_info['evolves_to']) > 0:
                # For simplicity, we'll take the first evolution if multiple exist
                first_evolution = evolution_info['evolves_to'][0]
                evolves_to_id = self.get_pokemon_id_by_name(first_evolution)
                if not evolves_to_id:
                    print(f"    ⚠ Could not find ID for evolves_to: {first_evolution}")
            
            # First, delete existing records
            delete_query = "DELETE FROM PokemonEvolutions WHERE pokemon_id = %s"
            self.cursor.execute(delete_query, (pokemon_id,))
            
            # Insert new record (even if both evolves_from_id and evolves_to_id are None,
            # this marks that we've checked this Pokémon)
            insert_query = """
                INSERT INTO PokemonEvolutions 
                (pokemon_id, evolves_from_id, evolves_to_id, evolution_stage)
                VALUES (%s, %s, %s, %s)
            """
            self.cursor.execute(insert_query, (
                pokemon_id, evolves_from_id, evolves_to_id,
                evolution_info.get('evolution_stage')
            ))
            
            self.conn.commit()
            return True
            
        except Exception as e:
            print(f"  ✗ Error updating evolution record: {e}")
            self.conn.rollback()
            return False
    
    def get_pokemon_id_by_name(self, name: str) -> Optional[int]:
        """
        Get Pokémon ID from database by name.
        
        Args:
            name: Pokémon name
            
        Returns:
            Pokémon ID or None if not found
        """
        try:
            query = "SELECT pokemon_id FROM Pokemon WHERE LOWER(pokemon_name) = LOWER(%s)"
            self.cursor.execute(query, (name,))
            result = self.cursor.fetchone()
            return result[0] if result else None
        except Exception as e:
            print(f"  ✗ Error getting Pokémon ID for {name}: {e}")
            return None
    
    def process_pokemon(self, pokemon_id: int, pokemon_name: str, force_reload: bool = False) -> bool:
        """
        Process a single Pokémon to check and update its evolution information.
        
        Args:
            pokemon_id: Pokémon ID from database
            pokemon_name: Name of the Pokémon
            force_reload: If True, delete existing records and reload from API
            
        Returns:
            True if successful, False otherwise
        """
        print(f"\n📊 Processing: {pokemon_name} (ID: {pokemon_id})")
        
        # Check if evolution already exists in database
        if not force_reload and self.check_evolution_exists(pokemon_id):
            print(f"  ✓ Evolution record already exists for {pokemon_name}")
            return True
        
        # Delete existing records if force_reload is True
        if force_reload and self.check_evolution_exists(pokemon_id):
            print(f"  🔄 Deleting existing evolution records for {pokemon_name}")
            self.delete_existing_evolution_records(pokemon_id)
        
        print(f"  🔍 Fetching evolution data from PokeAPI...")
        
        # Fetch evolution chain from API
        evolution_chain = self.fetch_evolution_chain_from_api(pokemon_name)
        
        if not evolution_chain:
            print(f"  ℹ No evolution data found for {pokemon_name}")
            # Still create a record to mark that we've checked it
            evolution_info = {
                'pokemon_name': pokemon_name,
                'evolution_stage': 1,
                'evolves_from': None,
                'evolves_to': []
            }
            self.update_evolution_record(pokemon_id, evolution_info)
            return True
        
        # Find the Pokémon in the evolution chain
        evolution_info = self.find_pokemon_in_evolution_chain(evolution_chain, pokemon_name)
        
        if evolution_info:
            has_evolution = bool(evolution_info.get('evolves_to')) or bool(evolution_info.get('evolves_from'))
            
            if has_evolution:
                print(f"  🔄 Evolution found for {pokemon_name}:")
                if evolution_info.get('evolves_from'):
                    print(f"    • Evolves from: {evolution_info['evolves_from']}")
                if evolution_info.get('evolves_to'):
                    print(f"    • Evolves to: {', '.join(evolution_info['evolves_to'])}")
                print(f"    • Evolution stage: {evolution_info.get('evolution_stage')}")
                
                # Update database with evolution information
                if self.update_evolution_record(pokemon_id, evolution_info):
                    print(f"  ✓ Evolution record updated successfully for {pokemon_name}")
                else:
                    print(f"  ✗ Failed to update evolution record for {pokemon_name}")
                    return False
            else:
                print(f"  ℹ {pokemon_name} has no evolutions")
                # Still create a record to mark that we've checked it
                self.update_evolution_record(pokemon_id, evolution_info)
        else:
            print(f"  ⚠ Could not find {pokemon_name} in evolution chain")
            return False
        
        return True
    
    def run_evolution_check(self, generation_id: int = None, force_reload: bool = False, 
                           delay_between_requests: float = 0.5):
        """
        Main method to check evolutions for Pokémon in the database.
        
        Args:
            generation_id: Optional generation ID to filter (1-3)
            force_reload: If True, delete existing records and reload from API
            delay_between_requests: Delay in seconds between API requests
        """
        print("\n" + "="*60)
        print("🚀 POKÉMON EVOLUTION CHECKER")
        print("="*60)
        if force_reload:
            print("⚠️  FORCE RELOAD MODE: Will delete and reload all evolution records")
        print("="*60)
        
        # Connect to database
        self.connect_to_db()
        
        # Get Pokémon from database (optionally filtered by generation)
        pokemon_list = self.get_pokemon_from_db(generation_id)
        
        if not pokemon_list:
            print("✗ No Pokémon found in database")
            self.disconnect_from_db()
            return
        
        # Process each Pokémon
        successful = 0
        failed = 0
        
        for pokemon_id, pokemon_name in pokemon_list:
            try:
                if self.process_pokemon(pokemon_id, pokemon_name, force_reload):
                    successful += 1
                else:
                    failed += 1
                
                # Add delay to respect PokeAPI rate limits
                time.sleep(delay_between_requests)
                
            except Exception as e:
                print(f"  ✗ Unexpected error processing {pokemon_name}: {e}")
                failed += 1
        
        # Print summary
        print("\n" + "="*60)
        print("📊 EVOLUTION CHECK COMPLETE")
        print("="*60)
        print(f"✓ Successfully processed: {successful}")
        print(f"✗ Failed to process: {failed}")
        print(f"📝 Total Pokémon processed: {len(pokemon_list)}")
        print("="*60)
        
        # Disconnect from database
        self.disconnect_from_db()
    
    def cleanup_invalid_evolutions(self):
        """
        Clean up any evolution records that reference Pokémon not in the database.
        """
        print("\n" + "="*60)
        print("🧹 CLEANING UP INVALID EVOLUTION RECORDS")
        print("="*60)
        
        self.connect_to_db()
        
        try:
            # Find and delete records where evolves_from_id points to non-existent Pokémon
            query_invalid_from = """
                DELETE FROM PokemonEvolutions 
                WHERE evolves_from_id IS NOT NULL 
                AND evolves_from_id NOT IN (SELECT pokemon_id FROM Pokemon)
            """
            self.cursor.execute(query_invalid_from)
            deleted_from = self.cursor.rowcount
            
            # Find and delete records where evolves_to_id points to non-existent Pokémon
            query_invalid_to = """
                DELETE FROM PokemonEvolutions 
                WHERE evolves_to_id IS NOT NULL 
                AND evolves_to_id NOT IN (SELECT pokemon_id FROM Pokemon)
            """
            self.cursor.execute(query_invalid_to)
            deleted_to = self.cursor.rowcount
            
            self.conn.commit()
            
            print(f"✓ Deleted {deleted_from} records with invalid 'evolves_from' references")
            print(f"✓ Deleted {deleted_to} records with invalid 'evolves_to' references")
            
        except Exception as e:
            print(f"✗ Error cleaning up invalid records: {e}")
            self.conn.rollback()
        
        self.disconnect_from_db()


def main():
    """
    Main function to run the Pokémon evolution checker.
    """
    # Database configuration - UPDATE THESE VALUES
    db_params = {
        'dbname': 'PokemonScanner',      # Database name
        'user': 'postgres',         # Your PostgreSQL username
        'password': 'admin',     # Your PostgreSQL password
        'host': 'localhost',             # Database host
        'port': '5433'                   # Database port (default PostgreSQL port)
    }
    
    # Create evolution checker instance
    checker = PokemonEvolutionChecker(db_params)
    
    # Option 1: First, clean up any invalid evolution records
    print("\n🔧 STEP 1: Cleaning up invalid evolution records...")
    checker.cleanup_invalid_evolutions()
    
    # Option 2: Force reload evolutions for Gen 1-3 (delete existing and recreate)
    print("\n🔄 STEP 2: Reloading evolution data for Generations 1-3...")
    checker.run_evolution_check(
        generation_id=None,  # Set to 1, 2, or 3 for specific generation, or None for all
        force_reload=True,   # This will delete and re-add evolution records
        delay_between_requests=0.5  # Be respectful to the API
    )
    
    # Option 3: If you only want to process missing ones without force reload:
    # checker.run_evolution_check(
    #     generation_id=None,  # Process all generations
    #     force_reload=False,  # Only add missing records
    #     delay_between_requests=0.5
    # )


if __name__ == "__main__":
    main()