import psycopg2
from psycopg2.extras import RealDictCursor

def add_deoxys_complete():
    """Complete setup for Deoxys - adds Pokemon, type, and all damage relations"""
    
    conn = None
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
            print("="*60)
            print("STARTING COMPLETE DEOXYS SETUP")
            print("="*60)
            
            # Step 1: Check if Deoxys exists, add if not
            print("\n📝 Step 1: Checking for Deoxys in database...")
            cur.execute("SELECT pokemon_id FROM Pokemon WHERE national_dex_number = 386")
            exists = cur.fetchone()
            
            if not exists:
                print("   Deoxys not found. Adding to database...")
                cur.execute("""
                    INSERT INTO Pokemon (national_dex_number, pokemon_name, pokemon_speed, generation_id)
                    VALUES (386, 'Deoxys', 150, 3)
                    ON CONFLICT (national_dex_number) DO NOTHING
                    RETURNING pokemon_id
                """)
                
                result = cur.fetchone()
                if result:
                    deoxys_id = result['pokemon_id']
                    print(f"   ✅ Added Deoxys with ID: {deoxys_id}")
                else:
                    print("   ❌ Failed to add Deoxys!")
                    return
            else:
                deoxys_id = exists['pokemon_id']
                print(f"   ✅ Deoxys already exists with ID: {deoxys_id}")
            
            # Step 2: Ensure Psychic type is assigned
            print("\n📝 Step 2: Assigning Psychic type to Deoxys...")
            cur.execute("SELECT type_id FROM TypeChart WHERE type_name = 'psychic'")
            type_result = cur.fetchone()
            
            if not type_result:
                print("   ❌ Psychic type not found in TypeChart!")
                print("   Please ensure TypeChart has the 'psychic' type")
                return
            
            psychic_id = type_result['type_id']
            
            # Clear existing types
            cur.execute("DELETE FROM PokemonTypes WHERE pokemon_id = %s", (deoxys_id,))
            print(f"   ✅ Cleared existing types for Deoxys")
            
            # Add Psychic type
            cur.execute("""
                INSERT INTO PokemonTypes (pokemon_id, type_id)
                VALUES (%s, %s)
                ON CONFLICT (pokemon_id, type_id) DO NOTHING
            """, (deoxys_id, psychic_id))
            print(f"   ✅ Assigned Psychic type (ID: {psychic_id}) to Deoxys")
            
            # Step 3: Get all necessary type IDs
            print("\n📝 Step 3: Loading type data from TypeChart...")
            cur.execute("""
                SELECT type_id, type_name 
                FROM TypeChart 
                WHERE type_name IN (
                    'bug', 'dark', 'ghost', 'fighting', 'psychic', 
                    'poison', 'steel'
                )
            """)
            types = {row['type_name']: row['type_id'] for row in cur.fetchall()}
            
            # Check for missing types
            required_types = ['bug', 'dark', 'ghost', 'fighting', 'psychic', 'poison', 'steel']
            missing_types = [t for t in required_types if t not in types]
            if missing_types:
                print(f"   ⚠️ Warning: Missing types in TypeChart: {', '.join(missing_types)}")
                print("   These damage relations will be skipped")
            else:
                print("   ✅ All required type IDs loaded:")
                for type_name, type_id in types.items():
                    print(f"     - {type_name}: {type_id}")
            
            # Step 4: Clear existing damage relations
            print("\n📝 Step 4: Clearing existing damage relations...")
            tables = [
                'DoubleDamageFromChart', 'DoubleDamageToChart',
                'HalfDamageFromChart', 'HalfDamageToChart',
                'NoDamageFromChart', 'NoDamageToChart'
            ]
            for table in tables:
                cur.execute(f"DELETE FROM {table} WHERE pokemon_id = %s", (deoxys_id,))
                print(f"   ✅ Cleared {table}")
            
            # Step 5: Add weaknesses (2x damage FROM)
            print("\n📝 Step 5: Adding weaknesses (2x damage from)...")
            weaknesses = ['bug', 'dark', 'ghost']
            for weakness in weaknesses:
                if weakness in types:
                    cur.execute("""
                        INSERT INTO DoubleDamageFromChart (pokemon_id, type_id)
                        VALUES (%s, %s)
                        ON CONFLICT (pokemon_id, type_id) DO NOTHING
                    """, (deoxys_id, types[weakness]))
                    print(f"   ✅ Deoxys takes 2x damage from {weakness}")
                else:
                    print(f"   ⚠️ Skipping {weakness} - type not found in TypeChart")
            
            # Step 6: Add strengths (2x damage TO)
            print("\n📝 Step 6: Adding strengths (2x damage to)...")
            strengths = ['fighting', 'poison']
            for strength in strengths:
                if strength in types:
                    cur.execute("""
                        INSERT INTO DoubleDamageToChart (pokemon_id, type_id)
                        VALUES (%s, %s)
                        ON CONFLICT (pokemon_id, type_id) DO NOTHING
                    """, (deoxys_id, types[strength]))
                    print(f"   ✅ Deoxys deals 2x damage to {strength}")
                else:
                    print(f"   ⚠️ Skipping {strength} - type not found in TypeChart")
            
            # Step 7: Add resistances (0.5x damage FROM)
            print("\n📝 Step 7: Adding resistances (0.5x damage from)...")
            resistances = ['fighting', 'psychic']
            for resistance in resistances:
                if resistance in types:
                    cur.execute("""
                        INSERT INTO HalfDamageFromChart (pokemon_id, type_id)
                        VALUES (%s, %s)
                        ON CONFLICT (pokemon_id, type_id) DO NOTHING
                    """, (deoxys_id, types[resistance]))
                    print(f"   ✅ Deoxys takes 0.5x damage from {resistance}")
                else:
                    print(f"   ⚠️ Skipping {resistance} - type not found in TypeChart")
            
            # Step 8: Add not very effective (0.5x damage TO)
            print("\n📝 Step 8: Adding not very effective (0.5x damage to)...")
            not_effective = ['psychic', 'steel']
            for ineffective in not_effective:
                if ineffective in types:
                    cur.execute("""
                        INSERT INTO HalfDamageToChart (pokemon_id, type_id)
                        VALUES (%s, %s)
                        ON CONFLICT (pokemon_id, type_id) DO NOTHING
                    """, (deoxys_id, types[ineffective]))
                    print(f"   ✅ Deoxys deals 0.5x damage to {ineffective}")
                else:
                    print(f"   ⚠️ Skipping {ineffective} - type not found in TypeChart")
            
            # Step 9: No immunities for Psychic type
            print("\n📝 Step 9: Immunities...")
            print("   ⚪ Psychic type has no immunities (0x damage from or to)")
            
            # Commit all changes
            conn.commit()
            print("\n✅ All changes committed to database!")
            
            # Step 10: Verification
            print("\n" + "="*60)
            print("VERIFICATION - Deoxys Complete Setup")
            print("="*60)
            
            # Verify Pokemon data
            cur.execute("""
                SELECT p.pokemon_name, p.national_dex_number, p.pokemon_speed, p.generation_id,
                       t.type_name
                FROM Pokemon p
                JOIN PokemonTypes pt ON p.pokemon_id = pt.pokemon_id
                JOIN TypeChart t ON pt.type_id = t.type_id
                WHERE p.national_dex_number = 386
            """)
            pokemon_data = cur.fetchone()
            
            if pokemon_data:
                print(f"\n📊 Pokemon Data:")
                print(f"   Name: {pokemon_data['pokemon_name']}")
                print(f"   National Dex #: {pokemon_data['national_dex_number']}")
                print(f"   Speed: {pokemon_data['pokemon_speed']}")
                print(f"   Generation: {pokemon_data['generation_id']}")
                print(f"   Type: {pokemon_data['type_name']}")
            else:
                print("\n⚠️ Could not verify Pokemon data!")
            
            # Verify damage relations
            print(f"\n📊 Damage Relations for Deoxys:")
            print("-"*40)
            
            verification_tables = [
                ('DoubleDamageFromChart', 'Weaknesses (2x from):'),
                ('DoubleDamageToChart', 'Strengths (2x to):'),
                ('HalfDamageFromChart', 'Resistances (0.5x from):'),
                ('HalfDamageToChart', 'Not Very Effective (0.5x to):'),
            ]
            
            for table, label in verification_tables:
                cur.execute(f"""
                    SELECT ARRAY_AGG(t.type_name ORDER BY t.type_name) as type_array
                    FROM {table} d
                    JOIN TypeChart t ON d.type_id = t.type_id
                    WHERE d.pokemon_id = %s
                """, (deoxys_id,))
                result = cur.fetchone()
                if result and result['type_array']:
                    types_list = ', '.join(result['type_array'])
                    print(f"   {label} {types_list}")
                else:
                    print(f"   {label} (none)")
            
            print("\n" + "="*60)
            print("✅ DEOXYS SETUP COMPLETE!")
            print("="*60)
            
    except Exception as e:
        print(f"\n❌ Error: {e}")
        if conn:
            conn.rollback()
        import traceback
        traceback.print_exc()
    finally:
        if conn:
            conn.close()
            print("\n🔌 Database connection closed.")

if __name__ == "__main__":
    add_deoxys_complete()