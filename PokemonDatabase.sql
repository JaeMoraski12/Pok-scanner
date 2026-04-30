CREATE DATABASE PokemonScanner;

CREATE TABLE GenerationChart (
    generation_id SERIAL PRIMARY KEY,
    generation_name VARCHAR(50)
);

CREATE TABLE TypeChart (
    type_id SERIAL PRIMARY KEY,
    type_name VARCHAR(50) UNIQUE NOT NULL
);

-- CREATE TABLE LocationChart (
--     location_id SERIAL PRIMARY KEY,
--     location_name VARCHAR(50) NOT NULL
-- );

CREATE TABLE Pokemon (
    pokemon_id SERIAL PRIMARY KEY,
    national_dex_number INT UNIQUE NOT NULL,  
    pokemon_name VARCHAR(50) UNIQUE NOT NULL,                                                                                                            
    pokemon_speed INT NOT NULL,
    generation_id INTEGER NOT NULL REFERENCES GenerationChart(generation_id),
    image_URL VARCHAR(500)                          
);

CREATE TABLE DoubleDamageFromChart (
    pokemon_id INTEGER REFERENCES Pokemon(pokemon_id),
    type_id INTEGER REFERENCES TypeChart(type_id),
    PRIMARY KEY (pokemon_id, type_id)
);

CREATE TABLE DoubleDamageToChart (
    pokemon_id INTEGER REFERENCES Pokemon(pokemon_id),
    type_id INTEGER REFERENCES TypeChart(type_id),
    PRIMARY KEY (pokemon_id, type_id)
);

CREATE TABLE HalfDamageFromChart (
    pokemon_id INTEGER REFERENCES Pokemon(pokemon_id),
    type_id INTEGER REFERENCES TypeChart(type_id),
    PRIMARY KEY (pokemon_id, type_id)
);

CREATE TABLE HalfDamageToChart (
    pokemon_id INTEGER REFERENCES Pokemon(pokemon_id),
    type_id INTEGER REFERENCES TypeChart(type_id),
    PRIMARY KEY (pokemon_id, type_id)
);

CREATE TABLE NoDamageToChart (
    pokemon_id INTEGER REFERENCES Pokemon(pokemon_id),
    type_id INTEGER REFERENCES TypeChart(type_id),
    PRIMARY KEY (pokemon_id, type_id)
);

CREATE TABLE NoDamageFromChart (
    pokemon_id INTEGER REFERENCES Pokemon(pokemon_id),
    type_id INTEGER REFERENCES TypeChart(type_id),
    PRIMARY KEY (pokemon_id, type_id)
);

CREATE TABLE PokemonTypes (
    pokemon_id INTEGER REFERENCES Pokemon(pokemon_id),
    type_id INTEGER REFERENCES TypeChart(type_id),
    PRIMARY KEY (pokemon_id, type_id)
);

-- CREATE TABLE PokemonLocationChart (
--     pokemon_id INTEGER REFERENCES Pokemon(pokemon_id),
--     location_id INTEGER REFERENCES LocationChart(location_id),
--     PRIMARY KEY (pokemon_id, location_id)
-- );

CREATE TABLE PokemonEvolutions (
    evolution_id SERIAL PRIMARY KEY,
    pokemon_id INTEGER NOT NULL REFERENCES Pokemon(pokemon_id),
    evolves_from_id INTEGER REFERENCES Pokemon(pokemon_id),
    evolves_to_id INTEGER REFERENCES Pokemon(pokemon_id),
    evolution_stage INTEGER,
    UNIQUE(pokemon_id, evolves_to_id)
);

CREATE INDEX idx_evolutions_pokemon ON PokemonEvolutions(pokemon_id);
CREATE INDEX idx_evolutions_to ON PokemonEvolutions(evolves_to_id);

-- CREATE TABLE GamesChart (
--     game_id SERIAL PRIMARY KEY,
--     game_name VARCHAR(50) NOT NULL
-- );

-- CREATE TABLE GameAllocation (
--     pokemon_id INTEGER REFERENCES Pokemon(pokemon_id),
--     game_id INTEGER REFERENCES GamesChart(game_id),
--     PRIMARY KEY (pokemon_id, game_id)
-- );

CREATE TABLE AiImagesChart (
    ai_image_id SERIAL PRIMARY KEY,
    image_name VARCHAR(500) NOT NULL
);

CREATE TABLE AiImageAllocation (
    pokemon_id INTEGER REFERENCES Pokemon(pokemon_id),
    ai_image_id INTEGER REFERENCES AiImagesChart(ai_image_id),
    generation_id INTEGER REFERENCES GenerationChart(generation_id),
    PRIMARY KEY (pokemon_id, ai_image_id, generation_id)
);


