import psycopg2
import os
import re

def update_images_in_exact_order(conn, image_folder="PokemonImagesDB"):
    """Update Pokemon with images in exact order (1st image to 1st Pokemon, etc.)"""
    
    # Check if folder exists
    if not os.path.exists(image_folder):
        print(f"✗ Folder '{image_folder}' not found!")
        return
    
    # Get all image files in order (sorted by the number prefix)
    image_files = []
    for file in os.listdir(image_folder):
        if file.endswith(".png"):
            # Extract the number from filename
            match = re.match(r"^(\d+)_", file)
            if match:
                seq_num = int(match.group(1))
                image_files.append((seq_num, file))
    
    # Sort by the sequential number
    image_files.sort(key=lambda x: x[0])
    
    print(f"Found {len(image_files)} images in order")
    print("="*60)
    
    with conn.cursor() as cur:
        # Get ALL Pokemon in the order they were inserted (by pokemon_id)
        # This assumes you inserted them in the order you want
        cur.execute("""
            SELECT pokemon_id, national_dex_number, pokemon_name 
            FROM Pokemon 
            WHERE generation_id IN (1, 2, 3)
            ORDER BY pokemon_id
        """)
        
        pokemon_list = cur.fetchall()
        
        if len(image_files) != len(pokemon_list):
            print(f"⚠ Warning: {len(image_files)} images but {len(pokemon_list)} Pokemon")
            print(f"  Using min of both: {min(len(image_files), len(pokemon_list))}")
        
        updated = 0
        # Match by position (1st image to 1st Pokemon, 2nd to 2nd, etc.)
        for i, ((seq_num, filename), (pokemon_id, national_id, name)) in enumerate(zip(image_files, pokemon_list)):
            image_path = os.path.abspath(os.path.join(image_folder, filename))
            
            cur.execute("""
                UPDATE Pokemon 
                SET image_url = %s 
                WHERE pokemon_id = %s
            """, (image_path, pokemon_id))
            
            updated += 1
            print(f"✓ Position {i+1:3d}: Image {seq_num:3d} ({filename}) -> Pokemon #{national_id:3d}: {name}")
        
        conn.commit()
        
        print("\n" + "="*60)
        print(f"✅ Updated {updated} Pokemon with images (in exact order)")

if __name__ == "__main__":
    try:
        conn = psycopg2.connect(
            host="localhost",
            port="5433",
            database="PokemonScanner",
            user="postgres",
            password="admin",
        )
        print("Connected to database!")
        print("="*60)
        
        # Update images in exact order
        update_images_in_exact_order(conn, image_folder="PokemonImagesDB")
        
        conn.close()
        
    except Exception as e:
        print(f"Error: {e}")
        if conn:
            conn.rollback()
            conn.close()