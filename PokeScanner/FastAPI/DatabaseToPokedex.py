from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import FileResponse
import psycopg2
from psycopg2.extras import RealDictCursor
from typing import List, Optional
import os
from pathlib import Path
import socket

app = FastAPI(title="Pokemon API")

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"], 
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

IMAGES_FOLDER = Path(r"C:\Users\jaeli\OneDrive\Documents\William and Mary\Junior\Spring 26\Fundamental of AI\Pokemon AI generator\Pok-scanner\PokemonImagesDB")

USE_LOCALHOST = True # Set to False when testing on phone
COMPUTER_IP = "XX.XX.XX.XX"  # Set your IP here

if USE_LOCALHOST:
    BASE_URL = "http://localhost:5000"
else:
    BASE_URL = f"http://{COMPUTER_IP}:5000"

def get_db_connection():
    return psycopg2.connect(
        host="localhost",
        port="5433",
        database="PokemonScanner",
        user="postgres",
        password="admin",
        cursor_factory=RealDictCursor
    )

@app.get("/api/images/{image_filename}")
async def get_pokemon_image(image_filename: str):
    """Serve Pokemon images from local folder"""
    safe_filename = os.path.basename(image_filename)
    img_path = IMAGES_FOLDER / safe_filename
    
    if img_path.exists() and img_path.is_file():
        return FileResponse(img_path)
    
    raise HTTPException(status_code=404, detail="Image not found")

@app.get("/api/images/pokemon/{pokemon_id}")
async def get_pokemon_image_by_id(pokemon_id: int):
    """Serve Pokemon image by Pokemon ID"""
    conn = get_db_connection()
    cur = conn.cursor()
    
    cur.execute("SELECT image_url FROM Pokemon WHERE pokemon_id = %s", (pokemon_id,))
    result = cur.fetchone()
    cur.close()
    conn.close()
    
    if not result or not result['image_url']:
        raise HTTPException(status_code=404, detail="Image not found")
    
    image_path = Path(result['image_url'])
    filename = image_path.name
    
    img_path = IMAGES_FOLDER / filename
    if img_path.exists() and img_path.is_file():
        return FileResponse(img_path)
    
    raise HTTPException(status_code=404, detail="Image file not found")

@app.get("/api/pokemon")
def get_all_pokemon():
    """Get all Pokemon from Generations 1-3"""
    conn = get_db_connection()
    cur = conn.cursor()
    
    cur.execute("""
        SELECT 
            p.pokemon_id,
            p.national_dex_number,
            p.pokemon_name,
            p.pokemon_speed,
            p.generation_id,
            p.image_url,
            ARRAY_AGG(t.type_name) as types
        FROM Pokemon p
        JOIN PokemonTypes pt ON p.pokemon_id = pt.pokemon_id
        JOIN TypeChart t ON pt.type_id = t.type_id
        WHERE p.generation_id IN (1, 2, 3)
        GROUP BY p.pokemon_id, p.national_dex_number, p.pokemon_name, 
                 p.pokemon_speed, p.generation_id, p.image_url
        ORDER BY p.national_dex_number
    """)
    
    pokemon = cur.fetchall()
    cur.close()
    conn.close()
    
    result = []
    for p in pokemon:
        p_dict = dict(p)
        p_dict['image_url'] = f"{BASE_URL}/api/images/pokemon/{p_dict['pokemon_id']}"
        result.append(p_dict)
    
    return result

@app.get("/api/pokemon/{pokemon_id}")
def get_pokemon_by_id(pokemon_id: int):
    """Get a specific Pokemon by ID"""
    conn = get_db_connection()
    cur = conn.cursor()
    
    cur.execute("""
        SELECT 
            p.pokemon_id,
            p.national_dex_number,
            p.pokemon_name,
            p.pokemon_speed,
            p.generation_id,
            p.image_url,
            ARRAY_AGG(DISTINCT t.type_name) as types
        FROM Pokemon p
        JOIN PokemonTypes pt ON p.pokemon_id = pt.pokemon_id
        JOIN TypeChart t ON pt.type_id = t.type_id
        WHERE p.pokemon_id = %s
        GROUP BY p.pokemon_id, p.national_dex_number, p.pokemon_name, 
                 p.pokemon_speed, p.generation_id, p.image_url
    """, (pokemon_id,))
    
    pokemon = cur.fetchone()
    cur.close()
    conn.close()
    
    if not pokemon:
        raise HTTPException(status_code=404, detail="Pokemon not found")
    
    # Update image URL to use API endpoint
    pokemon_dict = dict(pokemon)
    pokemon_dict['image_url'] = f"{BASE_URL}/api/images/pokemon/{pokemon_dict['pokemon_id']}"
    
    return pokemon_dict

@app.get("/api/pokemon/search/{name}")
def search_pokemon(name: str):
    """Search Pokemon by name"""
    conn = get_db_connection()
    cur = conn.cursor()
    
    cur.execute("""
        SELECT 
            p.pokemon_id,
            p.national_dex_number,
            p.pokemon_name,
            p.pokemon_speed,
            p.generation_id,
            p.image_url,
            ARRAY_AGG(t.type_name) as types
        FROM Pokemon p
        JOIN PokemonTypes pt ON p.pokemon_id = pt.pokemon_id
        JOIN TypeChart t ON pt.type_id = t.type_id
        WHERE p.pokemon_name ILIKE %s
        GROUP BY p.pokemon_id, p.national_dex_number, p.pokemon_name, 
                 p.pokemon_speed, p.generation_id, p.image_url
        ORDER BY p.national_dex_number
        LIMIT 20
    """, (f"%{name}%",))
    
    pokemon = cur.fetchall()
    cur.close()
    conn.close()
    
    result = []
    for p in pokemon:
        p_dict = dict(p)
        p_dict['image_url'] = f"{BASE_URL}/api/images/pokemon/{p_dict['pokemon_id']}"
        result.append(p_dict)
    
    return result

@app.get("/api/generations/{gen_id}")
def get_pokemon_by_generation(gen_id: int):
    """Get all Pokemon from a specific generation"""
    if gen_id not in [1, 2, 3]:
        raise HTTPException(status_code=400, detail="Only generations 1-3 are available")
    
    conn = get_db_connection()
    cur = conn.cursor()
    
    cur.execute("""
        SELECT 
            p.pokemon_id,
            p.national_dex_number,
            p.pokemon_name,
            p.pokemon_speed,
            p.generation_id,
            p.image_url,
            ARRAY_AGG(t.type_name) as types
        FROM Pokemon p
        JOIN PokemonTypes pt ON p.pokemon_id = pt.pokemon_id
        JOIN TypeChart t ON pt.type_id = t.type_id
        WHERE p.generation_id = %s
        GROUP BY p.pokemon_id, p.national_dex_number, p.pokemon_name, 
                 p.pokemon_speed, p.generation_id, p.image_url
        ORDER BY p.national_dex_number
    """, (gen_id,))
    
    pokemon = cur.fetchall()
    cur.close()
    conn.close()
    
    result = []
    for p in pokemon:
        p_dict = dict(p)
        p_dict['image_url'] = f"{BASE_URL}/api/images/pokemon/{p_dict['pokemon_id']}"
        result.append(p_dict)
    
    return result

@app.get("/api/images/direct/{filename}")
async def get_image_direct(filename: str):
    """Serve image directly by filename (e.g., 1_bulbasaur.png)"""
    safe_filename = os.path.basename(filename)
    img_path = IMAGES_FOLDER / safe_filename
    
    if img_path.exists() and img_path.is_file():
        return FileResponse(img_path)
    
    raise HTTPException(status_code=404, detail="Image not found")

@app.get("/")
def root():
    return {"message": "Pokemon API is running!"}

@app.get("/api/pokemon/{pokemon_id}/evolutions")
def get_pokemon_evolutions(pokemon_id: int):
    """Get evolution chain for a Pokemon"""
    conn = get_db_connection()
    cur = conn.cursor()
    
    cur.execute("""
        SELECT pokemon_name, national_dex_number 
        FROM Pokemon 
        WHERE pokemon_id = %s
    """, (pokemon_id,))
    
    pokemon = cur.fetchone()
    if not pokemon:
        raise HTTPException(status_code=404, detail="Pokemon not found")
    
    cur.execute("""
        WITH RECURSIVE evolution_chain AS (
            -- Start with this Pokemon
            SELECT 
                p.pokemon_id,
                p.pokemon_name,
                p.national_dex_number,
                p.image_url,
                0 as evolution_level,
                ARRAY[p.pokemon_id] as path
            FROM Pokemon p
            WHERE p.pokemon_id = %s
            
            UNION ALL
            
            -- Get Pokemon that evolve FROM the current Pokemon (next evolutions)
            SELECT 
                p.pokemon_id,
                p.pokemon_name,
                p.national_dex_number,
                p.image_url,
                ec.evolution_level + 1,
                ec.path || p.pokemon_id
            FROM evolution_chain ec
            JOIN PokemonEvolutions ev ON ec.pokemon_id = ev.pokemon_id
            JOIN Pokemon p ON ev.evolves_to_id = p.pokemon_id
            WHERE NOT p.pokemon_id = ANY(ec.path)
        )
        SELECT DISTINCT 
            pokemon_id,
            pokemon_name,
            national_dex_number,
            image_url,
            evolution_level
        FROM evolution_chain
        ORDER BY evolution_level, national_dex_number
    """, (pokemon_id,))
    
    forward_evolutions = cur.fetchall()
    
    cur.execute("""
        WITH RECURSIVE evolution_chain_back AS (
            -- Start with this Pokemon
            SELECT 
                p.pokemon_id,
                p.pokemon_name,
                p.national_dex_number,
                p.image_url,
                0 as evolution_level,
                ARRAY[p.pokemon_id] as path
            FROM Pokemon p
            WHERE p.pokemon_id = %s
            
            UNION ALL
            
            -- Get Pokemon that evolve TO the current Pokemon (previous evolutions)
            SELECT 
                p.pokemon_id,
                p.pokemon_name,
                p.national_dex_number,
                p.image_url,
                ec.evolution_level - 1,
                ec.path || p.pokemon_id
            FROM evolution_chain_back ec
            JOIN PokemonEvolutions ev ON ec.pokemon_id = ev.evolves_to_id
            JOIN Pokemon p ON ev.pokemon_id = p.pokemon_id
            WHERE NOT p.pokemon_id = ANY(ec.path)
        )
        SELECT DISTINCT 
            pokemon_id,
            pokemon_name,
            national_dex_number,
            image_url,
            evolution_level
        FROM evolution_chain_back
        ORDER BY evolution_level, national_dex_number
    """, (pokemon_id,))
    
    backward_evolutions = cur.fetchall()
    
    cur.close()
    conn.close()

    all_evolutions = {}
    
    for evo in backward_evolutions:
        all_evolutions[evo['pokemon_id']] = {
            "pokemon_id": evo['pokemon_id'],
            "pokemon_name": evo['pokemon_name'],
            "national_dex_number": evo['national_dex_number'],
            "image_url": f"{BASE_URL}/api/images/pokemon/{evo['pokemon_id']}",
            "evolution_stage": evo['evolution_level']
        }
    
    for evo in forward_evolutions:
        if evo['pokemon_id'] not in all_evolutions:
            all_evolutions[evo['pokemon_id']] = {
                "pokemon_id": evo['pokemon_id'],
                "pokemon_name": evo['pokemon_name'],
                "national_dex_number": evo['national_dex_number'],
                "image_url": f"{BASE_URL}/api/images/pokemon/{evo['pokemon_id']}",
                "evolution_stage": evo['evolution_level']
            }
    
    evolutions_list = list(all_evolutions.values())
    evolutions_list.sort(key=lambda x: x['evolution_stage'])
    
    return {
        "base_pokemon": {
            "id": pokemon_id,
            "name": pokemon['pokemon_name'],
            "national_id": pokemon['national_dex_number']
        },
        "evolutions": evolutions_list
    }

@app.get("/api/pokemon/{pokemon_id}/damage")
def get_damage_relations(pokemon_id: int):
    """Get damage relations for a Pokemon"""
    conn = get_db_connection()
    cur = conn.cursor()
    
    cur.execute("""
        SELECT 
            'double_from' as relation,
            ARRAY_AGG(DISTINCT t.type_name) as types
        FROM DoubleDamageFromChart d
        JOIN TypeChart t ON d.type_id = t.type_id
        WHERE d.pokemon_id = %s
        UNION ALL
        SELECT 
            'double_to',
            ARRAY_AGG(DISTINCT t.type_name)
        FROM DoubleDamageToChart d
        JOIN TypeChart t ON d.type_id = t.type_id
        WHERE d.pokemon_id = %s
        UNION ALL
        SELECT 
            'half_from',
            ARRAY_AGG(DISTINCT t.type_name)
        FROM HalfDamageFromChart d
        JOIN TypeChart t ON d.type_id = t.type_id
        WHERE d.pokemon_id = %s
        UNION ALL
        SELECT 
            'half_to',
            ARRAY_AGG(DISTINCT t.type_name)
        FROM HalfDamageToChart d
        JOIN TypeChart t ON d.type_id = t.type_id
        WHERE d.pokemon_id = %s
        UNION ALL
        SELECT 
            'no_from',
            ARRAY_AGG(DISTINCT t.type_name)
        FROM NoDamageFromChart d
        JOIN TypeChart t ON d.type_id = t.type_id
        WHERE d.pokemon_id = %s
        UNION ALL
        SELECT 
            'no_to',
            ARRAY_AGG(DISTINCT t.type_name)
        FROM NoDamageToChart d
        JOIN TypeChart t ON d.type_id = t.type_id
        WHERE d.pokemon_id = %s
    """, (pokemon_id, pokemon_id, pokemon_id, pokemon_id, pokemon_id, pokemon_id))
    
    damage = cur.fetchall()
    cur.close()
    conn.close()
    
    result = {
        "takes_double_damage_from": [],
        "deals_double_damage_to": [],
        "takes_half_damage_from": [],
        "deals_half_damage_to": [],
        "takes_no_damage_from": [],
        "deals_no_damage_to": []
    }
    
    for row in damage:
        if row['relation'] == 'double_from':
            result['takes_double_damage_from'] = row['types'] if row['types'] else []
        elif row['relation'] == 'double_to':
            result['deals_double_damage_to'] = row['types'] if row['types'] else []
        elif row['relation'] == 'half_from':
            result['takes_half_damage_from'] = row['types'] if row['types'] else []
        elif row['relation'] == 'half_to':
            result['deals_half_damage_to'] = row['types'] if row['types'] else []
        elif row['relation'] == 'no_from':
            result['takes_no_damage_from'] = row['types'] if row['types'] else []
        elif row['relation'] == 'no_to':
            result['deals_no_damage_to'] = row['types'] if row['types'] else []
    
    return result


if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=5000)