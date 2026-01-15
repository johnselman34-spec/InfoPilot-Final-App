import React, { useState, useEffect } from 'react';
import {
  View,
  Text,
  StyleSheet,
  TouchableOpacity,
  TextInput,
  Alert,
  ActivityIndicator,
  Linking,
  Dimensions,
  Platform,
  FlatList,
} from 'react-native';
import { Ionicons } from '@expo/vector-icons';
import { colors } from '../../src/utils/colors';
import { marketplaceAPI } from '../../src/services/api';

const { width } = Dimensions.get('window');

interface Protocol {
  id: string;
  name: string;
  protocol_string: string;
  user_id: string;
  username: string;
  price: number;
  is_for_sale: boolean;
  category_id?: string;
  description?: string;
  purchase_count: number;
  location?: {
    latitude: number;
    longitude: number;
    city?: string;
    country?: string;
  };
}

// Funny marketing messages
const FUNNY_MESSAGES = [
  "🚀 Welcome to the GALAXY'S GREATEST Protocol Marketplace!",
  "💰 Where Search Wizards Become MILLIONAIRES* (*in knowledge)",
  "🎰 Better odds than Vegas, more fun than a barrel of monkeys!",
  "🏆 Home of Protocols So Good, Your Grandma Will Want One!",
  "✨ Protocols So Powerful, They Should Be Illegal (but they're not!)",
];

const PURCHASE_JOKES = [
  "Side effects may include: excessive productivity and smug satisfaction.",
  "Warning: May cause uncontrollable urges to organize everything.",
  "Caution: Your search skills will become the envy of your friends.",
  "Alert: Your brain's RAM may experience significant upgrades.",
  "Notice: Results so good, your cat might get jealous.",
];

export default function MarketplaceScreen() {
  const [protocols, setProtocols] = useState<Protocol[]>([]);
  const [loading, setLoading] = useState(true);
  const [searchQuery, setSearchQuery] = useState('');
  const [selectedCategories, setSelectedCategories] = useState<Set<string>>(new Set());
  const [priceRange] = useState({ min: 0, max: 99.00 }); // Updated: $0 to $99
  const [sortBy, setSortBy] = useState<'price' | 'popularity' | 'recent'>('popularity');
  const [viewMode, setViewMode] = useState<'map' | 'list'>('list');
  const [selectedProtocol, setSelectedProtocol] = useState<Protocol | null>(null);
  const [funnyMessage, setFunnyMessage] = useState(FUNNY_MESSAGES[0]);

  useEffect(() => {
    loadMarketplace();
    // Rotate funny messages
    const interval = setInterval(() => {
      setFunnyMessage(FUNNY_MESSAGES[Math.floor(Math.random() * FUNNY_MESSAGES.length)]);
    }, 5000);
    return () => clearInterval(interval);
  }, [sortBy]);

  const loadMarketplace = async () => {
    try {
      setLoading(true);
      const response = await marketplaceAPI.getProtocols({
        sort: sortBy,
        min_price: priceRange.min,
        max_price: priceRange.max,
      });
      
      // Use data from backend (includes auto-listed public categories now!)
      const protocolsWithLocation = (response.data?.protocols || response.protocols || []).map((p: Protocol, index: number) => ({
        ...p,
        location: p.location || generateMockLocation(index),
      }));
      
      setProtocols(protocolsWithLocation);
      
      // Select all categories by default
      const allCategoryIds = new Set(protocolsWithLocation.map((p: Protocol) => p.category_id).filter(Boolean) as string[]);
      setSelectedCategories(allCategoryIds);
    } catch (error) {
      console.error('Load marketplace error:', error);
      // Show demo data if API fails
      setProtocols(getDemoProtocols());
    } finally {
      setLoading(false);
    }
  };

  const generateMockLocation = (index: number) => {
    const locations = [
      { latitude: 40.7128, longitude: -74.0060, city: 'New York', country: 'USA' },
      { latitude: 51.5074, longitude: -0.1278, city: 'London', country: 'UK' },
      { latitude: 48.8566, longitude: 2.3522, city: 'Paris', country: 'France' },
      { latitude: 35.6762, longitude: 139.6503, city: 'Tokyo', country: 'Japan' },
      { latitude: -33.8688, longitude: 151.2093, city: 'Sydney', country: 'Australia' },
      { latitude: 55.7558, longitude: 37.6173, city: 'Moscow', country: 'Russia' },
      { latitude: -22.9068, longitude: -43.1729, city: 'Rio de Janeiro', country: 'Brazil' },
      { latitude: 1.3521, longitude: 103.8198, city: 'Singapore', country: 'Singapore' },
    ];
    return locations[index % locations.length];
  };

  const getDemoProtocols = (): Protocol[] => [
    {
      id: '1',
      name: 'Ultimate History Research',
      protocol_string: '(William OR George) & (War OR Battle)',
      user_id: 'demo1',
      username: 'HistoryBuff42',
      price: 1.99,
      is_for_sale: true,
      purchase_count: 156,
      description: 'Find ANY historical figure or event with laser precision!',
      location: { latitude: 40.7128, longitude: -74.0060, city: 'New York', country: 'USA' },
    },
    {
      id: '2', 
      name: 'Science Discovery Engine',
      protocol_string: '(quantum OR physics) & (discovery OR breakthrough)',
      user_id: 'demo2',
      username: 'ScienceNinja',
      price: 2.49,
      is_for_sale: true,
      purchase_count: 89,
      description: 'Unlock the secrets of the universe, one search at a time!',
      location: { latitude: 51.5074, longitude: -0.1278, city: 'London', country: 'UK' },
    },
    {
      id: '3',
      name: 'Business Intelligence Pro',
      protocol_string: '(startup OR company) & (funding OR revenue)',
      user_id: 'demo3',
      username: 'BizWizard',
      price: 2.99,
      is_for_sale: true,
      purchase_count: 234,
      description: 'Make your competitors cry with this protocol!',
      location: { latitude: 37.7749, longitude: -122.4194, city: 'San Francisco', country: 'USA' },
    },
  ];

  const handlePurchase = async (protocol: Protocol) => {
    const joke = PURCHASE_JOKES[Math.floor(Math.random() * PURCHASE_JOKES.length)];
    
    Alert.alert(
      '💰 KA-CHING! 💰',
      `You're about to unlock the SECRET SAUCE protocol "${protocol.name}" for just $${protocol.price}!\n\n` +
      `This protocol has made ${protocol.purchase_count} other users FILTHY RICH* in information!\n\n` +
      `${joke}\n\n` +
      `*Results may vary. Side effects include: excessive knowledge and an overwhelming urge to organize everything.`,
      [
        { text: 'Wait, I need more money first 😅', style: 'cancel' },
        {
          text: '💸 TAKE MY MONEY! 💸',
          onPress: async () => {
            try {
              const response = await marketplaceAPI.purchaseProtocol({
                protocol_id: protocol.id,
              });
              
              Alert.alert(
                '🚀 Redirecting to PayPal...',
                `You'll pay $${protocol.price}:\n` +
                `• Creator gets: $${(protocol.price * 0.9).toFixed(2)} (90%) 💪\n` +
                `• Platform fee: $${(protocol.price * 0.1).toFixed(2)} (10%) 🎩\n\n` +
                `(Don't worry, we promise not to spend it all on coffee... probably.)`,
                [
                  {
                    text: '💳 Open PayPal',
                    onPress: () => {
                      if (response.data.paypal_url) {
                        Linking.openURL(response.data.paypal_url);
                      }
                    },
                  },
                  { text: 'Maybe Later', style: 'cancel' },
                ]
              );
            } catch (error) {
              Alert.alert('Oops! 😬', 'Something went wrong. Our hamsters are working on it!');
            }
          },
        },
      ]
    );
  };

  const filteredProtocols = protocols.filter(p => {
    const matchesSearch = p.name.toLowerCase().includes(searchQuery.toLowerCase()) ||
                         p.username.toLowerCase().includes(searchQuery.toLowerCase()) ||
                         p.protocol_string.toLowerCase().includes(searchQuery.toLowerCase());
    const matchesCategory = !p.category_id || selectedCategories.has(p.category_id) || selectedCategories.size === 0;
    return matchesSearch && matchesCategory;
  });

  const renderProtocolCard = ({ item: protocol }: { item: Protocol }) => {
    const isFree = protocol.price === 0 || protocol.pay_what_you_want;
    
    return (
      <TouchableOpacity 
        style={styles.protocolCard}
        onPress={() => setSelectedProtocol(protocol)}
      >
        <View style={styles.cardHeader}>
          {isFree ? (
            <View style={styles.freeBadge}>
              <Ionicons name="gift" size={14} color={colors.white} />
              <Text style={styles.freeText}>FREE TO COPY!</Text>
            </View>
          ) : (
            <View style={styles.priceTag}>
              <Text style={styles.priceText}>${protocol.price.toFixed(2)}</Text>
            </View>
          )}
          <View style={styles.purchaseCount}>
            <Ionicons name="flame" size={14} color={colors.primary} />
            <Text style={styles.purchaseText}>{protocol.purchase_count} sold</Text>
          </View>
        </View>
        
        {/* Pay What You Want Badge */}
        {protocol.pay_what_you_want && (
          <View style={styles.payWhatYouWantBadge}>
            <Text style={styles.payWhatYouWantText}>🎁 PAY WHAT YOU WANT!</Text>
          </View>
        )}
        
        <Text style={styles.protocolName}>{protocol.name}</Text>
        <Text style={styles.creatorName}>by @{protocol.username}</Text>
        
        {protocol.description && (
          <Text style={styles.description} numberOfLines={2}>{protocol.description}</Text>
        )}
        
        <View style={styles.protocolPreview}>
          <Text style={styles.previewLabel}>Protocol Preview:</Text>
          <Text style={styles.previewText} numberOfLines={1}>{protocol.protocol_string}</Text>
        </View>
        
        {protocol.location && (
          <View style={styles.locationRow}>
            <Ionicons name="location" size={14} color={colors.accent} />
            <Text style={styles.locationText}>
              {protocol.location.city}, {protocol.location.country}
            </Text>
          </View>
        )}
        
        {isFree ? (
          <TouchableOpacity 
            style={styles.copyButton}
            onPress={() => handleCopyProtocol(protocol)}
          >
            <Ionicons name="copy" size={18} color={colors.white} />
            <Text style={styles.copyButtonText}>COPY PROTOCOL FREE!</Text>
          </TouchableOpacity>
        ) : (
          <TouchableOpacity 
            style={styles.buyButton}
            onPress={() => handlePurchase(protocol)}
          >
            <Ionicons name="cart" size={18} color={colors.white} />
            <Text style={styles.buyButtonText}>GET THIS PROTOCOL!</Text>
          </TouchableOpacity>
        )}
      </TouchableOpacity>
    );
  };
  
  const handleCopyProtocol = async (protocol: Protocol) => {
    // Copy protocol to clipboard
    try {
      // Use Clipboard API if available
      if (typeof navigator !== 'undefined' && navigator.clipboard) {
        await navigator.clipboard.writeText(protocol.protocol_string);
      }
      
      Alert.alert(
        '📋 Protocol Copied!',
        `"${protocol.name}" has been copied to your clipboard!\n\n` +
        `Protocol: ${protocol.protocol_string}\n\n` +
        `💡 Pro tip: Paste this into your own categories to use it!\n\n` +
        `📚 Enjoying InfoPilot? Check out "Letters to Evelyn" by John Selman - the supernatural thriller comedy that inspired this app!`,
        [
          { text: 'Awesome! 🎉', style: 'default' },
          { 
            text: '📖 Get the Book!', 
            onPress: () => Linking.openURL('https://www.amazon.com/dp/your-book-id')
          },
        ]
      );
    } catch (error) {
      // Fallback - just show the protocol
      Alert.alert(
        '📋 Copy This Protocol!',
        `${protocol.protocol_string}\n\n` +
        `Long-press and copy the above text to use this protocol!\n\n` +
        `Created by @${protocol.username} - support them by leaving a tip! 💰`
      );
    }
  };

  // World Map Component (Web-compatible using emoji markers)
  const renderWorldMap = () => (
    <View style={styles.mapContainer}>
      <View style={styles.mapPlaceholder}>
        <Text style={styles.mapTitle}>🌍 World Protocol Map 🌍</Text>
        <Text style={styles.mapSubtitle}>Protocols from around the globe!</Text>
        
        {/* Simple visual representation of protocols by region */}
        <View style={styles.regionGrid}>
          {['🇺🇸 Americas', '🇬🇧 Europe', '🇯🇵 Asia', '🇦🇺 Oceania'].map((region, index) => {
            const regionProtocols = filteredProtocols.slice(index * 2, (index * 2) + 2);
            return (
              <TouchableOpacity 
                key={region} 
                style={styles.regionCard}
                onPress={() => regionProtocols[0] && setSelectedProtocol(regionProtocols[0])}
              >
                <Text style={styles.regionEmoji}>{region.split(' ')[0]}</Text>
                <Text style={styles.regionName}>{region.split(' ')[1]}</Text>
                <Text style={styles.regionCount}>{regionProtocols.length} protocols</Text>
              </TouchableOpacity>
            );
          })}
        </View>
        
        <Text style={styles.mapHint}>
          📱 Use the mobile app for full interactive map with clustering!
        </Text>
      </View>
      
      {/* Floating Protocol Count */}
      <View style={styles.floatingCount}>
        <Text style={styles.floatingCountText}>
          {filteredProtocols.length} Protocols Worldwide! 🌍
        </Text>
      </View>
    </View>
  );

  if (loading) {
    return (
      <View style={styles.loadingContainer}>
        <ActivityIndicator size="large" color={colors.primary} />
        <Text style={styles.loadingText}>Loading the World's Greatest Protocols...</Text>
        <Text style={styles.loadingSubtext}>☕ Grab some coffee, this is worth the wait!</Text>
      </View>
    );
  }

  return (
    <View style={styles.container}>
      {/* Header with rotating funny message */}
      <View style={styles.header}>
        <Text style={styles.funnyBanner}>{funnyMessage}</Text>
        
        {/* FREE App Banner */}
        <View style={styles.freeBanner}>
          <Ionicons name="gift" size={20} color={colors.marketplaceGold} />
          <Text style={styles.freeText}>
            🎉 THIS APP IS 100% FREE! 🎉
          </Text>
          <Ionicons name="gift" size={20} color={colors.marketplaceGold} />
        </View>
        
        <Text style={styles.freeSubtext}>
          "Why pay for an app when the REAL treasure is the protocols you buy along the way?" 
          - Ancient InfoPilot Proverb
        </Text>
      </View>

      {/* Search and Filter Bar */}
      <View style={styles.searchContainer}>
        <View style={styles.searchBar}>
          <Ionicons name="search" size={20} color={colors.gray} />
          <TextInput
            style={styles.searchInput}
            placeholder="Search protocols, users, or keywords..."
            placeholderTextColor={colors.gray}
            value={searchQuery}
            onChangeText={setSearchQuery}
          />
          {searchQuery.length > 0 && (
            <TouchableOpacity onPress={() => setSearchQuery('')}>
              <Ionicons name="close-circle" size={20} color={colors.gray} />
            </TouchableOpacity>
          )}
        </View>
        
        {/* View Toggle */}
        <View style={styles.viewToggle}>
          <TouchableOpacity
            style={[styles.toggleButton, viewMode === 'map' && styles.toggleActive]}
            onPress={() => setViewMode('map')}
          >
            <Ionicons name="map" size={20} color={viewMode === 'map' ? colors.white : colors.primary} />
          </TouchableOpacity>
          <TouchableOpacity
            style={[styles.toggleButton, viewMode === 'list' && styles.toggleActive]}
            onPress={() => setViewMode('list')}
          >
            <Ionicons name="list" size={20} color={viewMode === 'list' ? colors.white : colors.primary} />
          </TouchableOpacity>
        </View>
      </View>

      {/* Sort Options */}
      <View style={styles.sortContainer}>
        <Text style={styles.sortLabel}>Sort by:</Text>
        {(['popularity', 'price', 'recent'] as const).map((sort) => (
          <TouchableOpacity
            key={sort}
            style={[styles.sortButton, sortBy === sort && styles.sortActive]}
            onPress={() => setSortBy(sort)}
          >
            <Text style={[styles.sortText, sortBy === sort && styles.sortTextActive]}>
              {sort === 'popularity' ? '🔥 Hot' : sort === 'price' ? '💰 Price' : '⏰ New'}
            </Text>
          </TouchableOpacity>
        ))}
      </View>

      {/* Main Content */}
      {viewMode === 'map' ? (
        renderWorldMap()
      ) : (
        <FlatList
          data={filteredProtocols}
          renderItem={renderProtocolCard}
          keyExtractor={(item) => item.id}
          contentContainerStyle={styles.listContainer}
          showsVerticalScrollIndicator={false}
          ListEmptyComponent={
            <View style={styles.emptyContainer}>
              <Ionicons name="sad-outline" size={60} color={colors.gray} />
              <Text style={styles.emptyText}>No protocols found!</Text>
              <Text style={styles.emptySubtext}>
                Be the FIRST to list one and become a legend! 🏆
              </Text>
            </View>
          }
        />
      )}

      {/* Selected Protocol Modal */}
      {selectedProtocol && (
        <TouchableOpacity 
          style={styles.modalOverlay}
          activeOpacity={1}
          onPress={() => setSelectedProtocol(null)}
        >
          <View style={styles.modalContent}>
            <TouchableOpacity 
              style={styles.closeModal}
              onPress={() => setSelectedProtocol(null)}
            >
              <Ionicons name="close" size={24} color={colors.white} />
            </TouchableOpacity>
            
            <View style={styles.modalPriceTag}>
              <Text style={styles.modalPrice}>${selectedProtocol.price.toFixed(2)}</Text>
            </View>
            
            <Text style={styles.modalTitle}>{selectedProtocol.name}</Text>
            <Text style={styles.modalCreator}>Created by @{selectedProtocol.username}</Text>
            
            {selectedProtocol.description && (
              <Text style={styles.modalDescription}>{selectedProtocol.description}</Text>
            )}
            
            <View style={styles.modalStats}>
              <View style={styles.statItem}>
                <Ionicons name="flame" size={24} color={colors.primary} />
                <Text style={styles.statValue}>{selectedProtocol.purchase_count}</Text>
                <Text style={styles.statLabel}>Sales</Text>
              </View>
              {selectedProtocol.location && (
                <View style={styles.statItem}>
                  <Ionicons name="location" size={24} color={colors.accent} />
                  <Text style={styles.statValue}>{selectedProtocol.location.city}</Text>
                  <Text style={styles.statLabel}>{selectedProtocol.location.country}</Text>
                </View>
              )}
            </View>
            
            <View style={styles.modalProtocol}>
              <Text style={styles.modalProtocolLabel}>Full Protocol:</Text>
              <Text style={styles.modalProtocolText}>{selectedProtocol.protocol_string}</Text>
            </View>
            
            <TouchableOpacity 
              style={styles.modalBuyButton}
              onPress={() => handlePurchase(selectedProtocol)}
            >
              <Ionicons name="cart" size={24} color={colors.white} />
              <Text style={styles.modalBuyText}>BUY NOW FOR ${selectedProtocol.price.toFixed(2)}</Text>
            </TouchableOpacity>
            
            <Text style={styles.revenueNote}>
              90% goes to the creator • 10% keeps our servers running ☕
            </Text>
          </View>
        </TouchableOpacity>
      )}

      {/* Book Promotion Footer */}
      <TouchableOpacity 
        style={styles.bookPromo}
        onPress={() => Linking.openURL('https://www.amazon.com/dp/your-book-id')}
      >
        <Text style={styles.bookPromoText}>
          📚 Check out "Letters to Evelyn" - The book that started it all! 📚
        </Text>
      </TouchableOpacity>
    </View>
  );
}

const styles = StyleSheet.create({
  container: {
    flex: 1,
    backgroundColor: colors.background,
  },
  loadingContainer: {
    flex: 1,
    justifyContent: 'center',
    alignItems: 'center',
    backgroundColor: colors.background,
  },
  loadingText: {
    color: colors.text,
    fontSize: 18,
    fontWeight: 'bold',
    marginTop: 16,
  },
  loadingSubtext: {
    color: colors.textMuted,
    fontSize: 14,
    marginTop: 8,
  },
  header: {
    padding: 16,
    backgroundColor: colors.cardBackground,
    borderBottomWidth: 1,
    borderBottomColor: colors.cardBorder,
  },
  funnyBanner: {
    color: colors.primary,
    fontSize: 14,
    fontWeight: 'bold',
    textAlign: 'center',
    marginBottom: 8,
  },
  freeBanner: {
    flexDirection: 'row',
    justifyContent: 'center',
    alignItems: 'center',
    backgroundColor: colors.secondary,
    paddingVertical: 8,
    paddingHorizontal: 16,
    borderRadius: 20,
    marginBottom: 8,
  },
  freeText: {
    color: colors.marketplaceGold,
    fontSize: 16,
    fontWeight: 'bold',
    marginHorizontal: 8,
  },
  freeSubtext: {
    color: colors.textMuted,
    fontSize: 12,
    textAlign: 'center',
    fontStyle: 'italic',
  },
  searchContainer: {
    flexDirection: 'row',
    padding: 12,
    alignItems: 'center',
  },
  searchBar: {
    flex: 1,
    flexDirection: 'row',
    alignItems: 'center',
    backgroundColor: colors.cardBackground,
    borderRadius: 12,
    paddingHorizontal: 12,
    paddingVertical: 10,
    borderWidth: 1,
    borderColor: colors.cardBorder,
  },
  searchInput: {
    flex: 1,
    color: colors.text,
    fontSize: 16,
    marginLeft: 8,
  },
  viewToggle: {
    flexDirection: 'row',
    marginLeft: 12,
    borderRadius: 12,
    overflow: 'hidden',
    borderWidth: 1,
    borderColor: colors.primary,
  },
  toggleButton: {
    padding: 10,
    backgroundColor: 'transparent',
  },
  toggleActive: {
    backgroundColor: colors.primary,
  },
  sortContainer: {
    flexDirection: 'row',
    paddingHorizontal: 12,
    paddingBottom: 8,
    alignItems: 'center',
  },
  sortLabel: {
    color: colors.textMuted,
    fontSize: 14,
    marginRight: 8,
  },
  sortButton: {
    paddingHorizontal: 12,
    paddingVertical: 6,
    borderRadius: 16,
    marginRight: 8,
    backgroundColor: colors.cardBackground,
    borderWidth: 1,
    borderColor: colors.cardBorder,
  },
  sortActive: {
    backgroundColor: colors.primary,
    borderColor: colors.primary,
  },
  sortText: {
    color: colors.textMuted,
    fontSize: 12,
    fontWeight: '600',
  },
  sortTextActive: {
    color: colors.white,
  },
  mapContainer: {
    flex: 1,
    position: 'relative',
  },
  mapPlaceholder: {
    flex: 1,
    backgroundColor: colors.cardBackground,
    margin: 12,
    borderRadius: 16,
    padding: 20,
    alignItems: 'center',
    justifyContent: 'center',
  },
  mapTitle: {
    fontSize: 24,
    fontWeight: 'bold',
    color: colors.text,
    marginBottom: 8,
  },
  mapSubtitle: {
    fontSize: 14,
    color: colors.textMuted,
    marginBottom: 24,
  },
  regionGrid: {
    flexDirection: 'row',
    flexWrap: 'wrap',
    justifyContent: 'center',
    gap: 12,
    marginBottom: 24,
  },
  regionCard: {
    backgroundColor: colors.background,
    padding: 16,
    borderRadius: 12,
    alignItems: 'center',
    minWidth: 120,
    borderWidth: 1,
    borderColor: colors.cardBorder,
  },
  regionEmoji: {
    fontSize: 32,
    marginBottom: 8,
  },
  regionName: {
    fontSize: 14,
    fontWeight: 'bold',
    color: colors.text,
  },
  regionCount: {
    fontSize: 12,
    color: colors.primary,
    marginTop: 4,
  },
  mapHint: {
    fontSize: 12,
    color: colors.textMuted,
    fontStyle: 'italic',
    textAlign: 'center',
  },
  floatingCount: {
    position: 'absolute',
    top: 24,
    left: 24,
    right: 24,
    backgroundColor: colors.cardBackground,
    paddingVertical: 8,
    paddingHorizontal: 16,
    borderRadius: 20,
    alignItems: 'center',
  },
  floatingCountText: {
    color: colors.text,
    fontSize: 14,
    fontWeight: 'bold',
  },
  listContainer: {
    padding: 12,
  },
  protocolCard: {
    backgroundColor: colors.cardBackground,
    borderRadius: 16,
    padding: 16,
    marginBottom: 12,
    borderWidth: 1,
    borderColor: colors.cardBorder,
  },
  cardHeader: {
    flexDirection: 'row',
    justifyContent: 'space-between',
    alignItems: 'center',
    marginBottom: 12,
  },
  priceTag: {
    backgroundColor: colors.priceTag,
    paddingHorizontal: 12,
    paddingVertical: 6,
    borderRadius: 16,
  },
  priceText: {
    color: colors.background,
    fontSize: 18,
    fontWeight: 'bold',
  },
  purchaseCount: {
    flexDirection: 'row',
    alignItems: 'center',
  },
  purchaseText: {
    color: colors.textMuted,
    fontSize: 14,
    marginLeft: 4,
  },
  protocolName: {
    color: colors.text,
    fontSize: 20,
    fontWeight: 'bold',
    marginBottom: 4,
  },
  creatorName: {
    color: colors.accent,
    fontSize: 14,
    marginBottom: 8,
  },
  description: {
    color: colors.textLight,
    fontSize: 14,
    marginBottom: 12,
  },
  protocolPreview: {
    backgroundColor: colors.background,
    padding: 10,
    borderRadius: 8,
    marginBottom: 12,
  },
  previewLabel: {
    color: colors.textMuted,
    fontSize: 10,
    marginBottom: 4,
  },
  previewText: {
    color: colors.primary,
    fontSize: 12,
    fontFamily: Platform.OS === 'ios' ? 'Courier' : 'monospace',
  },
  locationRow: {
    flexDirection: 'row',
    alignItems: 'center',
    marginBottom: 12,
  },
  locationText: {
    color: colors.textMuted,
    fontSize: 12,
    marginLeft: 4,
  },
  buyButton: {
    flexDirection: 'row',
    backgroundColor: colors.primary,
    paddingVertical: 12,
    borderRadius: 12,
    justifyContent: 'center',
    alignItems: 'center',
  },
  buyButtonText: {
    color: colors.white,
    fontSize: 16,
    fontWeight: 'bold',
    marginLeft: 8,
  },
  emptyContainer: {
    alignItems: 'center',
    padding: 40,
  },
  emptyText: {
    color: colors.text,
    fontSize: 18,
    fontWeight: 'bold',
    marginTop: 16,
  },
  emptySubtext: {
    color: colors.textMuted,
    fontSize: 14,
    marginTop: 8,
    textAlign: 'center',
  },
  modalOverlay: {
    position: 'absolute',
    top: 0,
    left: 0,
    right: 0,
    bottom: 0,
    backgroundColor: 'rgba(0,0,0,0.8)',
    justifyContent: 'center',
    alignItems: 'center',
    padding: 20,
  },
  modalContent: {
    backgroundColor: colors.cardBackground,
    borderRadius: 20,
    padding: 20,
    width: '100%',
    maxHeight: '80%',
    borderWidth: 2,
    borderColor: colors.primary,
  },
  closeModal: {
    position: 'absolute',
    top: 12,
    right: 12,
    zIndex: 1,
  },
  modalPriceTag: {
    backgroundColor: colors.priceTag,
    alignSelf: 'flex-start',
    paddingHorizontal: 16,
    paddingVertical: 8,
    borderRadius: 20,
    marginBottom: 12,
  },
  modalPrice: {
    color: colors.background,
    fontSize: 24,
    fontWeight: 'bold',
  },
  modalTitle: {
    color: colors.text,
    fontSize: 24,
    fontWeight: 'bold',
    marginBottom: 4,
  },
  modalCreator: {
    color: colors.accent,
    fontSize: 16,
    marginBottom: 12,
  },
  modalDescription: {
    color: colors.textLight,
    fontSize: 14,
    marginBottom: 16,
    lineHeight: 20,
  },
  modalStats: {
    flexDirection: 'row',
    justifyContent: 'space-around',
    marginBottom: 16,
  },
  statItem: {
    alignItems: 'center',
  },
  statValue: {
    color: colors.text,
    fontSize: 18,
    fontWeight: 'bold',
    marginTop: 4,
  },
  statLabel: {
    color: colors.textMuted,
    fontSize: 12,
  },
  modalProtocol: {
    backgroundColor: colors.background,
    padding: 12,
    borderRadius: 12,
    marginBottom: 16,
  },
  modalProtocolLabel: {
    color: colors.textMuted,
    fontSize: 12,
    marginBottom: 4,
  },
  modalProtocolText: {
    color: colors.primary,
    fontSize: 14,
    fontFamily: Platform.OS === 'ios' ? 'Courier' : 'monospace',
  },
  modalBuyButton: {
    flexDirection: 'row',
    backgroundColor: colors.primary,
    paddingVertical: 16,
    borderRadius: 16,
    justifyContent: 'center',
    alignItems: 'center',
    marginBottom: 8,
  },
  modalBuyText: {
    color: colors.white,
    fontSize: 18,
    fontWeight: 'bold',
    marginLeft: 8,
  },
  revenueNote: {
    color: colors.textMuted,
    fontSize: 11,
    textAlign: 'center',
  },
  bookPromo: {
    backgroundColor: colors.secondary,
    padding: 12,
    alignItems: 'center',
  },
  bookPromoText: {
    color: colors.marketplaceGold,
    fontSize: 14,
    fontWeight: 'bold',
  },
  // FREE badge and copy button styles
  freeBadge: {
    flexDirection: 'row',
    alignItems: 'center',
    backgroundColor: colors.success,
    paddingHorizontal: 12,
    paddingVertical: 6,
    borderRadius: 16,
    gap: 4,
  },
  freeText: {
    color: colors.white,
    fontSize: 12,
    fontWeight: 'bold',
  },
  payWhatYouWantBadge: {
    backgroundColor: colors.marketplaceGold,
    paddingHorizontal: 12,
    paddingVertical: 6,
    borderRadius: 12,
    alignSelf: 'flex-start',
    marginBottom: 8,
  },
  payWhatYouWantText: {
    color: colors.background,
    fontSize: 12,
    fontWeight: 'bold',
  },
  copyButton: {
    flexDirection: 'row',
    backgroundColor: colors.success,
    paddingVertical: 12,
    borderRadius: 12,
    justifyContent: 'center',
    alignItems: 'center',
  },
  copyButtonText: {
    color: colors.white,
    fontSize: 16,
    fontWeight: 'bold',
    marginLeft: 8,
  },
});
