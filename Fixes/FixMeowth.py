import psycopg2
from psycopg2.extras import RealDictCursor

def fix_meowth_evolution():
    """Add Meowth to Persian evolution link"""
    
    try:
        conn = psycopg2.connect(
            host="localhost",
            port="5433",
            database="PokemonScanner",
            user="postgres",
            password="admin",
            cursor_factory=RealDictCursor
        )
        
        with conn.cursor() as cur:
            # Get Meowth and Persian IDs
            cur.execute("""
                SELECT pokemon_id, pokemon_name, national_dex_number
                FROM Pokemon 
                WHERE pokemon_name IN ('meowth', 'persian')
                ORDER BY national_dex_number
            """)
            
            pokemon = cur.fetchall()
            if len(pokemon) < 2:
                print("❌ Meowth or Persian not found in database!")
                for p in pokemon:
                    print(f"   Found: {p['pokemon_name']}")
                return
            
            meowth = None
            persian = None
            for p in pokemon:
                if p['pokemon_name'] == 'meowth':
                    meowth = p
                elif p['pokemon_name'] == 'persian':
                    persian = p
            
            if not meowth or not persian:
                print("❌ Could not find both Meowth and Persian")
                return
            
            print(f"✅ Found Meowth: ID {meowth['pokemon_id']} (#{meowth['national_dex_number']})")
            print(f"✅ Found Persian: ID {persian['pokemon_id']} (#{persian['national_dex_number']})")
            
            # Check if evolution already exists
            cur.execute("""
                SELECT 1 FROM PokemonEvolutions 
                WHERE pokemon_id = %s AND evolves_to_id = %s
            """, (meowth['pokemon_id'], persian['pokemon_id']))
            
            if cur.fetchone():
                print("\n⚠️ Evolution already exists! Removing and re-adding...")
                cur.execute("""
                    DELETE FROM PokemonEvolutions 
                    WHERE pokemon_id = %s AND evolves_to_id = %s
                """, (meowth['pokemon_id'], persian['pokemon_id']))
            
            # Add evolution link
            cur.execute("""
                INSERT INTO PokemonEvolutions (pokemon_id, evolves_to_id, evolution_stage)
                VALUES (%s, %s, %s)
                ON CONFLICT (pokemon_id, evolves_to_id) DO NOTHING
            """, (meowth['pokemon_id'], persian['pokemon_id'], 1))
            
            conn.commit()
            print(f"\n✅ Added evolution: Meowth → Persian")
            
            # Also check for Alolan Meowth (if exists)
            cur.execute("""
                SELECT pokemon_id, pokemon_name 
                FROM Pokemon 
                WHERE pokemon_name ILIKE '%meowth%' AND pokemon_name != 'meowth'
            """)
            alolan_meowth = cur.fetchall()
            
            for am in alolan_meowth:
                print(f"\n📌 Found Alolan form: {am['pokemon_name']}")
                print("   Note: Alolan Meowth evolves into Alolan Persian (different evolution)")
            
            # Verify the evolution works
            print("\n" + "="*50)
            print("VERIFICATION:")
            print("="*50)
            cur.execute("""
                SELECT 
                    p1.pokemon_name as from_pokemon,
                    p2.pokemon_name as to_pokemon,
                    pe.evolution_stage
                FROM PokemonEvolutions pe
                JOIN Pokemon p1 ON pe.pokemon_id = p1.pokemon_id
                JOIN Pokemon p2 ON pe.evolves_to_id = p2.pokemon_id
                WHERE p1.pokemon_name = 'meowth'
            """)
            
            result = cur.fetchone()
            if result:
                print(f"✓ {result['from_pokemon']} → {result['to_pokemon']} (Stage {result['evolution_stage']})")
            else:
                print("✗ Evolution not found after insert")
            
        conn.close()
        
    except Exception as e:
        print(f"❌ Error: {e}")
        if conn:
            conn.rollback()
            conn.close()

if __name__ == "__main__":
    fix_meowth_evolution()