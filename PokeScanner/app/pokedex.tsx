import React, { useState, useEffect } from "react";
import {
    View,
    Text,
    StyleSheet,
    TouchableOpacity,
    ActivityIndicator,
    Image,
    FlatList,
    TextInput,
    Modal,
    ScrollView,
    RefreshControl,
    Platform
} from 'react-native';
import { router, useLocalSearchParams } from 'expo-router';  // Add useLocalSearchParams
import { SafeAreaView } from 'react-native-safe-area-context';

interface Pokemon {
    pokemon_id: number;
    national_dex_number: number;
    pokemon_name: string;
    pokemon_speed: number;
    generation_id: number;
    image_url: string;
    types: string[];
}

export default function PokedexScreen() {
    const params = useLocalSearchParams();  // Get navigation params
    const [pokemon, setPokemon] = useState<Pokemon[]>([]);
    const [loading, setLoading] = useState(true);
    const [refreshing, setRefreshing] = useState(false);
    const [searchQuery, setSearchQuery] = useState('');
    const [selectedPokemon, setSelectedPokemon] = useState<Pokemon | null>(null);
    const [modalVisible, setModalVisible] = useState(false);
    const [sortBy, setSortBy] = useState<'number' | 'name' | 'speed'>('number');
    const [sortOrder, setSortOrder] = useState<'asc' | 'desc'>('asc');
    const [evolutions, setEvolutions] = useState<any[]>([]);
    const [loadingEvolutions, setLoadingEvolutions] = useState(false);
    const [damageRelations, setDamageRelations] = useState<any>(null);
    const [loadingDamage, setLoadingDamage] = useState(false);

    const getApiUrl = () => {
        if (Platform.OS === 'web') {
            return 'http://localhost:5000';
        }
        if (Platform.OS === 'ios' && !Platform.isPad) {
            return 'http://localhost:5000';
        } 
        if (Platform.OS === 'android') {
            return 'http://10.0.2.2:5000';
        }
        return 'http://100.66.101.40:5000';
    };

    const API_BASE_URL = getApiUrl();

    useEffect(() => {
        fetchPokemon();
    }, []);

    // Handle params from scanner
    useEffect(() => {
        console.log('Params received:', params);
        
        if (params.selectedPokemon && params.autoOpenModal === 'true') {
            try {
                const pokemonData = JSON.parse(params.selectedPokemon as string);
                console.log('Opening modal for Pokemon:', pokemonData.pokemon_name);
                
                setSelectedPokemon(pokemonData);
                fetchEvolutions(pokemonData.pokemon_id);
                fetchDamageRelations(pokemonData.pokemon_id);
                setModalVisible(true);
                
                // Clear params to prevent re-opening on refresh
                router.setParams({ selectedPokemon: undefined, autoOpenModal: undefined });
            } catch (error) {
                console.error('Error parsing selected Pokemon:', error);
            }
        }
    }, [params.selectedPokemon, params.autoOpenModal]);

    const fetchPokemon = async () => {
        try {
            const response = await fetch(`${API_BASE_URL}/api/pokemon`);
            const data = await response.json();
            setPokemon(data);
        } catch (error) {
            console.error('Error fetching Pokemon:', error);
        } finally {
            setLoading(false);
            setRefreshing(false);
        }
    };

    const onRefresh = () => {
        setRefreshing(true);
        fetchPokemon();
    };

    const getSortedAndFilteredPokemon = () => {
        let filtered = [...pokemon];
        
        if (searchQuery) {
            filtered = filtered.filter(p =>
                p.pokemon_name.toLowerCase().includes(searchQuery.toLowerCase())
            );
        }
        
        filtered.sort((a, b) => {
            let comparison = 0;
            if (sortBy === 'number') {
                comparison = a.national_dex_number - b.national_dex_number;
            } else if (sortBy === 'name') {
                comparison = a.pokemon_name.localeCompare(b.pokemon_name);
            } else if (sortBy === 'speed') {
                comparison = a.pokemon_speed - b.pokemon_speed;
            }
            return sortOrder === 'asc' ? comparison : -comparison;
        });
        
        return filtered;
    };

    const filteredPokemon = getSortedAndFilteredPokemon();

    const renderPokemonCard = ({ item }: { item: Pokemon }) => (
        <TouchableOpacity
            style={styles.card}
            onPress={() => {
                setSelectedPokemon(item);
                fetchEvolutions(item.pokemon_id);
                fetchDamageRelations(item.pokemon_id);
                setModalVisible(true);
            }}
            activeOpacity={0.7}
        >
            <Image
                source={{ uri: item.image_url }}
                style={styles.cardImage}
            />
            <Text style={styles.cardNumber}>#{item.national_dex_number}</Text>
            <Text style={styles.cardName}>{item.pokemon_name}</Text>
            <View style={styles.typeContainer}>
                {item.types.map((type, index) => (
                    <View key={index} style={[styles.typeBadge, getTypeStyle(type)]}>
                        <Text style={styles.typeText}>{type}</Text>
                    </View>
                ))}
            </View>
        </TouchableOpacity>
    );

    const getTypeStyle = (type: string) => {
        const typeColors: { [key: string]: any } = {
            normal: { backgroundColor: '#A8A878' },
            fire: { backgroundColor: '#F08030' },
            water: { backgroundColor: '#6890F0' },
            electric: { backgroundColor: '#F8D030' },
            grass: { backgroundColor: '#78C850' },
            poison: { backgroundColor: '#A040A0' },
            psychic: { backgroundColor: '#F85888' },
            ice: { backgroundColor: '#98D8D8' },
            dragon: { backgroundColor: '#7038F8' },
            dark: { backgroundColor: '#705848' },
            fairy: { backgroundColor: '#EE99AC' },
            fighting: { backgroundColor: '#C03028' },
            flying: { backgroundColor: '#A890F0' },
            ground: { backgroundColor: '#E0C068' },
            rock: { backgroundColor: '#B8A038' },
            bug: { backgroundColor: '#A8B820' },
            ghost: { backgroundColor: '#705898' },
            steel: { backgroundColor: '#B8B8D0' },
        };
        return typeColors[type] || { backgroundColor: '#68A090' };
    };

    const fetchEvolutions = async (pokemonId: number) => {
        setLoadingEvolutions(true);
        try {
            const response = await fetch(`${API_BASE_URL}/api/pokemon/${pokemonId}/evolutions`);
            const data = await response.json();
            setEvolutions(data.evolutions || []);
        } catch (error) {
            console.error('Error fetching evolutions:', error);
            setEvolutions([]);
        } finally {
            setLoadingEvolutions(false);
        }
    };

    const fetchDamageRelations = async (pokemonId: number) => {
        setLoadingDamage(true);
        try {
            const response = await fetch(`${API_BASE_URL}/api/pokemon/${pokemonId}/damage`);
            const data = await response.json();
            setDamageRelations(data);
        } catch (error) {
            console.error('Error fetching damage relations:', error);
            setDamageRelations(null);
        } finally {
            setLoadingDamage(false);
        }
    };

    const getSortIcon = () => {
        if (sortOrder === 'asc') return '↑';
        return '↓';
    };

    if (loading) {
        return (
            <View style={styles.centerContainer}>
                <ActivityIndicator size="large" color="#e74c3c" />
                <Text style={styles.loadingText}>Loading Pokédex...</Text>
            </View>
        );
    }

    return (
        <SafeAreaView style={styles.container}>
            {/* Header */}
            <View style={styles.header}>
                <TouchableOpacity
                    style={styles.backButton}
                    onPress={() => router.back()}
                >
                    <Text style={styles.backButtonText}>←</Text>
                </TouchableOpacity>
                <Text style={styles.headerTitle}>Pokédex</Text>
                <Text style={styles.pokemonCount}>{filteredPokemon.length}</Text>
            </View>

            {/* Search Bar */}
            <View style={styles.searchContainer}>
                <TextInput
                    style={styles.searchInput}
                    placeholder="Search Pokémon..."
                    placeholderTextColor="#999"
                    value={searchQuery}
                    onChangeText={setSearchQuery}
                />
            </View>

            {/* Sorting Options */}
            <View style={styles.sortContainer}>
                <Text style={styles.sortLabel}>Sort by:</Text>
                <TouchableOpacity
                    style={[styles.sortButton, sortBy === 'number' && styles.sortButtonActive]}
                    onPress={() => {
                        if (sortBy === 'number') {
                            setSortOrder(sortOrder === 'asc' ? 'desc' : 'asc');
                        } else {
                            setSortBy('number');
                            setSortOrder('asc');
                        }
                    }}
                >
                    <Text style={[styles.sortButtonText, sortBy === 'number' && styles.sortButtonTextActive]}>
                        #{getSortIcon()} Number
                    </Text>
                </TouchableOpacity>
                
                <TouchableOpacity
                    style={[styles.sortButton, sortBy === 'name' && styles.sortButtonActive]}
                    onPress={() => {
                        if (sortBy === 'name') {
                            setSortOrder(sortOrder === 'asc' ? 'desc' : 'asc');
                        } else {
                            setSortBy('name');
                            setSortOrder('asc');
                        }
                    }}
                >
                    <Text style={[styles.sortButtonText, sortBy === 'name' && styles.sortButtonTextActive]}>
                        {getSortIcon()} Name
                    </Text>
                </TouchableOpacity>
                
                <TouchableOpacity
                    style={[styles.sortButton, sortBy === 'speed' && styles.sortButtonActive]}
                    onPress={() => {
                        if (sortBy === 'speed') {
                            setSortOrder(sortOrder === 'asc' ? 'desc' : 'asc');
                        } else {
                            setSortBy('speed');
                            setSortOrder('asc');
                        }
                    }}
                >
                    <Text style={[styles.sortButtonText, sortBy === 'speed' && styles.sortButtonTextActive]}>
                        {getSortIcon()} Speed
                    </Text>
                </TouchableOpacity>
            </View>

            {/* Pokemon Grid */}
            <FlatList
                data={filteredPokemon}
                renderItem={renderPokemonCard}
                keyExtractor={(item) => item.pokemon_id.toString()}
                numColumns={2}
                contentContainerStyle={styles.listContainer}
                showsVerticalScrollIndicator={false}
                refreshControl={
                    <RefreshControl refreshing={refreshing} onRefresh={onRefresh} />
                }
                ListEmptyComponent={
                    <View style={styles.emptyContainer}>
                        <Text style={styles.emptyText}>No Pokémon found</Text>
                    </View>
                }
            />

            {/* Pokemon Detail Modal */}
            <Modal
                visible={modalVisible}
                animationType="slide"
                transparent={false}
                onRequestClose={() => setModalVisible(false)}
            >
                {selectedPokemon && (
                    <ScrollView style={styles.modalContainer}>
                        <TouchableOpacity
                            style={styles.modalCloseButton}
                            onPress={() => setModalVisible(false)}
                        >
                            <Text style={styles.modalCloseText}>✕</Text>
                        </TouchableOpacity>

                        <Image
                            source={{ uri: selectedPokemon.image_url }}
                            style={styles.modalImage}
                        />

                        <Text style={styles.modalNumber}>
                            #{selectedPokemon.national_dex_number}
                        </Text>
                        <Text style={styles.modalName}>
                            {selectedPokemon.pokemon_name}
                        </Text>

                        <View style={styles.modalTypes}>
                            {selectedPokemon.types.map((type, index) => (
                                <View key={index} style={[styles.modalTypeBadge, getTypeStyle(type)]}>
                                    <Text style={styles.modalTypeText}>{type}</Text>
                                </View>
                            ))}
                        </View>

                        {/* Stats */}
                        <View style={styles.statsContainer}>
                            <View style={styles.statCard}>
                                <Text style={styles.statValue}>{selectedPokemon.pokemon_speed}</Text>
                                <Text style={styles.statLabel}>Speed</Text>
                            </View>
                            <View style={styles.statCard}>
                                <Text style={styles.statValue}>Gen {selectedPokemon.generation_id}</Text>
                                <Text style={styles.statLabel}>Generation</Text>
                            </View>
                        </View>

                        {/* Evolution Chain */}
                        <Text style={styles.sectionTitle}>Evolution Chain</Text>
                        {loadingEvolutions ? (
                            <ActivityIndicator size="small" color="#e74c3c" style={styles.evolutionLoader} />
                        ) : evolutions.length > 1 ? (
                            <View style={styles.evolutionContainer}>
                                {evolutions.map((evo, index) => (
                                    <React.Fragment key={evo.pokemon_id}>
                                        <TouchableOpacity 
                                            style={styles.evolutionCard}
                                            onPress={async () => {
                                                try {
                                                    const response = await fetch(`${API_BASE_URL}/api/pokemon/${evo.pokemon_id}`);
                                                    const evoData = await response.json();
                                                    setSelectedPokemon(evoData);
                                                    await fetchEvolutions(evo.pokemon_id);
                                                    await fetchDamageRelations(evo.pokemon_id);
                                                } catch (error) {
                                                    console.error('Error loading evolution:', error);
                                                }
                                            }}
                                        >
                                            <Image
                                                source={{ uri: `${API_BASE_URL}/api/images/pokemon/${evo.pokemon_id}` }}
                                                style={styles.evolutionImage}
                                            />
                                            <Text style={styles.evolutionNumber}>#{evo.national_dex_number}</Text>
                                            <Text style={styles.evolutionName}>{evo.pokemon_name}</Text>
                                        </TouchableOpacity>
                                        {index < evolutions.length - 1 && (
                                            <View style={styles.evolutionArrow}>
                                                <Text style={styles.arrowText}>→</Text>
                                            </View>
                                        )}
                                    </React.Fragment>
                                ))}
                            </View>
                        ) : (
                            <Text style={styles.noEvolution}>This Pokémon does not evolve</Text>
                        )}

                        {/* Damage Relations */}
                        <Text style={styles.sectionTitle}>Type Effectiveness</Text>
                        {loadingDamage ? (
                            <ActivityIndicator size="small" color="#e74c3c" style={styles.damageLoader} />
                        ) : damageRelations ? (
                            <View style={styles.damageContainer}>
                                {damageRelations.takes_double_damage_from?.length > 0 && (
                                    <View style={styles.damageRow}>
                                        <Text style={styles.damageLabel}>Weak to (2x):</Text>
                                        <View style={styles.damageTypesContainer}>
                                            {damageRelations.takes_double_damage_from.map((type: string, idx: number) => (
                                                <View key={idx} style={[styles.damageTypeBadge, getTypeStyle(type)]}>
                                                    <Text style={styles.damageTypeText}>{type}</Text>
                                                </View>
                                            ))}
                                        </View>
                                    </View>
                                )}
                                
                                {damageRelations.takes_half_damage_from?.length > 0 && (
                                    <View style={styles.damageRow}>
                                        <Text style={styles.damageLabel}>Resists (0.5x):</Text>
                                        <View style={styles.damageTypesContainer}>
                                            {damageRelations.takes_half_damage_from.map((type: string, idx: number) => (
                                                <View key={idx} style={[styles.damageTypeBadge, getTypeStyle(type)]}>
                                                    <Text style={styles.damageTypeText}>{type}</Text>
                                                </View>
                                            ))}
                                        </View>
                                    </View>
                                )}
                                
                                {damageRelations.takes_no_damage_from?.length > 0 && (
                                    <View style={styles.damageRow}>
                                        <Text style={styles.damageLabel}>Immune to:</Text>
                                        <View style={styles.damageTypesContainer}>
                                            {damageRelations.takes_no_damage_from.map((type: string, idx: number) => (
                                                <View key={idx} style={[styles.damageTypeBadge, getTypeStyle(type)]}>
                                                    <Text style={styles.damageTypeText}>{type}</Text>
                                                </View>
                                            ))}
                                        </View>
                                    </View>
                                )}
                            </View>
                        ) : (
                            <Text style={styles.noDamage}>No damage data available</Text>
                        )}
                        
                        {/* Add bottom padding */}
                        <View style={{ height: 40 }} />
                    </ScrollView>
                )}
            </Modal>
        </SafeAreaView>
    );
}

const styles = StyleSheet.create({
    container: {
        flex: 1,
        backgroundColor: '#f5f5f5',
    },
    header: {
        flexDirection: 'row',
        justifyContent: 'space-between',
        alignItems: 'center',
        paddingHorizontal: 20,
        paddingVertical: 15,
        backgroundColor: '#fff',
        borderBottomWidth: 1,
        borderBottomColor: '#e0e0e0',
    },
    backButton: {
        padding: 8,
    },
    backButtonText: {
        fontSize: 28,
        color: '#e74c3c',
    },
    headerTitle: {
        fontSize: 24,
        fontWeight: 'bold',
        color: '#2c3e50',
    },
    pokemonCount: {
        fontSize: 14,
        color: '#999',
        fontWeight: '500',
    },
    searchContainer: {
        paddingHorizontal: 16,
        paddingVertical: 12,
        backgroundColor: '#fff',
    },
    searchInput: {
        backgroundColor: '#f0f0f0',
        borderRadius: 12,
        paddingHorizontal: 16,
        paddingVertical: 12,
        fontSize: 16,
        color: '#333',
    },
    sortContainer: {
        flexDirection: 'row',
        alignItems: 'center',
        paddingHorizontal: 16,
        paddingVertical: 10,
        backgroundColor: '#fff',
        borderBottomWidth: 1,
        borderBottomColor: '#e0e0e0',
    },
    sortLabel: {
        fontSize: 14,
        color: '#666',
        marginRight: 12,
        fontWeight: '500',
    },
    sortButton: {
        paddingHorizontal: 14,
        paddingVertical: 6,
        borderRadius: 16,
        backgroundColor: '#f0f0f0',
        marginRight: 8,
    },
    sortButtonActive: {
        backgroundColor: '#3498db',
    },
    sortButtonText: {
        fontSize: 12,
        color: '#666',
        fontWeight: '500',
    },
    sortButtonTextActive: {
        color: '#fff',
    },
    listContainer: {
        padding: 8,
    },
    card: {
        flex: 1,
        margin: 8,
        backgroundColor: '#fff',
        borderRadius: 16,
        padding: 12,
        alignItems: 'center',
        shadowColor: '#000',
        shadowOffset: { width: 0, height: 2 },
        shadowOpacity: 0.1,
        shadowRadius: 4,
        elevation: 3,
    },
    cardImage: {
        width: 100,
        height: 100,
        marginBottom: 8,
    },
    cardNumber: {
        fontSize: 12,
        color: '#999',
        marginBottom: 4,
    },
    cardName: {
        fontSize: 16,
        fontWeight: '600',
        color: '#2c3e50',
        marginBottom: 6,
        textAlign: 'center',
        textTransform: 'capitalize',
    },
    typeContainer: {
        flexDirection: 'row',
        flexWrap: 'wrap',
        justifyContent: 'center',
        gap: 4,
    },
    typeBadge: {
        paddingHorizontal: 8,
        paddingVertical: 2,
        borderRadius: 12,
    },
    typeText: {
        fontSize: 10,
        color: '#fff',
        fontWeight: '600',
    },
    centerContainer: {
        flex: 1,
        justifyContent: 'center',
        alignItems: 'center',
        backgroundColor: '#f5f5f5',
    },
    loadingText: {
        marginTop: 12,
        fontSize: 16,
        color: '#666',
    },
    emptyContainer: {
        flex: 1,
        justifyContent: 'center',
        alignItems: 'center',
        paddingTop: 100,
    },
    emptyText: {
        fontSize: 16,
        color: '#999',
    },
    modalContainer: {
        flex: 1,
        backgroundColor: '#f5f5f5',
    },
    modalCloseButton: {
        position: 'absolute',
        top: 50,
        right: 20,
        zIndex: 1,
        backgroundColor: 'rgba(0,0,0,0.5)',
        width: 40,
        height: 40,
        borderRadius: 20,
        justifyContent: 'center',
        alignItems: 'center',
    },
    modalCloseText: {
        color: '#fff',
        fontSize: 20,
        fontWeight: 'bold',
    },
    modalImage: {
        width: 250,
        height: 250,
        alignSelf: 'center',
        marginTop: 60,
        marginBottom: 20,
    },
    modalNumber: {
        textAlign: 'center',
        fontSize: 18,
        color: '#999',
        marginBottom: 8,
    },
    modalName: {
        textAlign: 'center',
        fontSize: 32,
        fontWeight: 'bold',
        color: '#2c3e50',
        marginBottom: 16,
        textTransform: 'capitalize',
    },
    modalTypes: {
        flexDirection: 'row',
        justifyContent: 'center',
        gap: 12,
        marginBottom: 24,
    },
    modalTypeBadge: {
        paddingHorizontal: 16,
        paddingVertical: 6,
        borderRadius: 20,
    },
    modalTypeText: {
        fontSize: 14,
        color: '#fff',
        fontWeight: '600',
    },
    statsContainer: {
        flexDirection: 'row',
        justifyContent: 'space-around',
        paddingHorizontal: 40,
        marginBottom: 32,
    },
    statCard: {
        alignItems: 'center',
        backgroundColor: '#fff',
        paddingHorizontal: 24,
        paddingVertical: 16,
        borderRadius: 12,
        shadowColor: '#000',
        shadowOffset: { width: 0, height: 2 },
        shadowOpacity: 0.05,
        shadowRadius: 4,
        elevation: 2,
    },
    statValue: {
        fontSize: 24,
        fontWeight: 'bold',
        color: '#e74c3c',
    },
    statLabel: {
        fontSize: 14,
        color: '#999',
        marginTop: 4,
    },
    sectionTitle: {
        fontSize: 20,
        fontWeight: '600',
        color: '#2c3e50',
        marginHorizontal: 20,
        marginBottom: 12,
    },
    comingSoon: {
        fontSize: 16,
        color: '#999',
        textAlign: 'center',
        marginHorizontal: 20,
        paddingVertical: 20,
    },
    evolutionLoader: {
    marginTop: 20,
    marginBottom: 20,
},
    evolutionContainer: {
        flexDirection: 'row',
        flexWrap: 'wrap',
        justifyContent: 'center',
        alignItems: 'center',
        paddingHorizontal: 20,
        marginBottom: 20,
    },
    evolutionCard: {
        alignItems: 'center',
        backgroundColor: '#fff',
        borderRadius: 12,
        padding: 12,
        minWidth: 100,
        shadowColor: '#000',
        shadowOffset: { width: 0, height: 2 },
        shadowOpacity: 0.05,
        shadowRadius: 4,
        elevation: 2,
    },
    evolutionImage: {
        width: 80,
        height: 80,
        marginBottom: 8,
    },
    evolutionNumber: {
        fontSize: 12,
        color: '#999',
        marginBottom: 4,
    },
    evolutionName: {
        fontSize: 14,
        fontWeight: '600',
        color: '#2c3e50',
        textTransform: 'capitalize',
    },
    evolutionArrow: {
        marginHorizontal: 8,
    },
    arrowText: {
        fontSize: 24,
        color: '#e74c3c',
        fontWeight: 'bold',
    },
    noEvolution: {
        fontSize: 16,
        color: '#999',
        textAlign: 'center',
        marginHorizontal: 20,
        paddingVertical: 20,
    },
    damageLoader: {
    marginTop: 10,
    marginBottom: 10,
},
    damageContainer: {
        paddingHorizontal: 20,
        marginBottom: 24,
    },
    damageRow: {
        marginBottom: 16,
    },
    damageLabel: {
        fontSize: 14,
        fontWeight: '600',
        color: '#2c3e50',
        marginBottom: 8,
    },
    damageTypesContainer: {
        flexDirection: 'row',
        flexWrap: 'wrap',
        gap: 8,
    },
    damageTypeBadge: {
        paddingHorizontal: 12,
        paddingVertical: 4,
        borderRadius: 16,
    },
    damageTypeText: {
        fontSize: 12,
        color: '#fff',
        fontWeight: '600',
    },
    noDamage: {
        fontSize: 14,
        color: '#999',
        textAlign: 'center',
        marginHorizontal: 20,
        marginBottom: 20,
    },
});