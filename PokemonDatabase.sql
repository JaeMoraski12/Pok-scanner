CREATE DATABASE PokemonReference;
USE PokemonReference;

CREATE TABLE GenerationChart (
    generation_id INTEGER PRIMARY KEY AUTO_INCREMENT,
    generation_name VARCHAR(50)
);

CREATE TABLE TypeChart (
    type_id INT PRIMARY KEY AUTO_INCREMENT,
    type_name VARCHAR(50)
);

CREATE TABLE LocationChart (
    location_id INT PRIMARY KEY AUTO_INCREMENT,
    location_name VARCHAR(50) NOT NULL
);

CREATE TABLE Pokemon (
    pokemon_id INT PRIMARY KEY AUTO_INCREMENT,
    national_dex_number INT UNIQUE NOT NULL,  
    pokemon_name VARCHAR(50) NOT NULL,                           
    pokemon_description TEXT,                                                                                  
    pokemon_speed INT,
    catch_rate INT,
    generation_id INTEGER REFERENCES GenerationChart(generation_id),
    image_URL VARCHAR(500)                          
);

CREATE TABLE WeaknessChart (
    pokemon_id INTEGER REFERENCES Pokemon(pokemon_id),
    type_id INTEGER REFERENCES TypeChart(type_id),
    PRIMARY KEY (pokemon_id, type_id)
);

CREATE TABLE ResistanceChart (
    pokemon_id INTEGER REFERENCES Pokemon(pokemon_id),
    type_id INTEGER REFERENCES TypeChart(type_id),
    PRIMARY KEY (pokemon_id, type_id)
);

CREATE TABLE ImmunityChart (
    pokemon_id INTEGER REFERENCES Pokemon(pokemon_id),
    type_id INTEGER REFERENCES TypeChart(type_id),
    PRIMARY KEY (pokemon_id, type_id)
);

CREATE TABLE PokemonLocationChart (
    pokemon_id INTEGER REFERENCES Pokemon(pokemon_id),
    location_id INTEGER REFERENCES LocationChart(location_id),
    PRIMARY KEY (pokemon_id, location_id)
);

CREATE TABLE Evolutions (
    from_pokemon_id INTEGER REFERENCES Pokemon(pokemon_id),
    to_pokemon_id INTEGER REFERENCES Pokemon(pokemon_id),
    PRIMARY KEY (from_pokemon_id, to_pokemon_id)
);


