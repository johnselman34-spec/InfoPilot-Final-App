import React, { useState, useEffect } from 'react';
import {
  View,
  Text,
  StyleSheet,
  ScrollView,
  TouchableOpacity,
  ActivityIndicator,
  Dimensions,
  Image,
} from 'react-native';
import { SafeAreaView } from 'react-native-safe-area-context';
import { Ionicons } from '@expo/vector-icons';
import { colors } from '../../src/utils/colors';
import { api } from '../../src/services/api';

const { width } = Dimensions.get('window');

interface Statistics {
  overview: {
    total_users: number;
    total_protocols: number;
    total_searches: number;
    total_sales: number;
    total_revenue: number;
  };
  country_breakdown: Record<string, number>;
  content_type_breakdown: Record<string, number>;
  top_protocol_words: Array<{ word: string; count: number }>;
}

interface LeaderboardEntry {
  rank: number;
  user_id: string;
  username: string;
  profile_photo?: string;
  sales_count: number;
  revenue: number;
  title: string;
}

interface Badge {
  id: string;
  name: string;
  description: string;
  icon: string;
  category: string;
  rarity: string;
  earned?: boolean;
  locked?: boolean;
}

type ViewMode = 'stats' | 'leaderboard' | 'badges';
type LeaderboardTab = 'sales' | 'revenue' | 'both';

// Colors for pie chart
const PIE_COLORS = [colors.primary, colors.secondary, colors.accent, colors.marketplaceGold, colors.success, colors.tertiary, '#FF6B6B', '#4ECDC4'];

export default function StatisticsScreen() {
  const [viewMode, setViewMode] = useState<ViewMode>('stats');
  const [loading, setLoading] = useState(true);
  const [statistics, setStatistics] = useState<Statistics | null>(null);
  const [leaderboard, setLeaderboard] = useState<LeaderboardEntry[]>([]);
  const [leaderboardTab, setLeaderboardTab] = useState<LeaderboardTab>('both');
  const [badges, setBadges] = useState<Badge[]>([]);
  const [userBadges, setUserBadges] = useState<Badge[]>([]);

  useEffect(() => {
    loadData();
  }, [viewMode, leaderboardTab]);

  const loadData = async () => {
    setLoading(true);
    try {
      if (viewMode === 'stats') {
        const response = await api.get('/statistics');
        setStatistics(response);
      } else if (viewMode === 'leaderboard') {
        const response = await api.get(`/leaderboard/sellers?tab=${leaderboardTab}`);
        setLeaderboard(response.leaderboard || []);
      } else if (viewMode === 'badges') {
        const allBadgesResponse = await api.get('/gamification/badges');
        setBadges(allBadgesResponse.badges || []);
        try {
          const userBadgesResponse = await api.get('/gamification/user-badges');
          setUserBadges(userBadgesResponse.badges || []);
        } catch {
          setUserBadges([]);
        }
      }
    } catch (error) {
      console.error('Load statistics error:', error);
      // Set demo data
      if (viewMode === 'stats') {
        setStatistics({
          overview: { total_users: 1234, total_protocols: 567, total_searches: 89012, total_sales: 345, total_revenue: 2456.78 },
          country_breakdown: { 'USA': 450, 'UK': 230, 'Germany': 180, 'France': 120, 'Japan': 100 },
          content_type_breakdown: { 'Web': 5000, 'News': 2500, 'Academic': 1800, 'Blog': 1200, 'Forum': 800 },
          top_protocol_words: [
            { word: 'history', count: 156 }, { word: 'research', count: 134 }, { word: 'science', count: 98 },
            { word: 'business', count: 87 }, { word: 'technology', count: 76 }, { word: 'education', count: 65 }
          ]
        });
      } else if (viewMode === 'leaderboard') {
        setLeaderboard([
          { rank: 1, user_id: 'u1', username: 'ProtocolKing', profile_photo: 'https://i.pravatar.cc/150?img=1', sales_count: 234, revenue: 567.89, title: '🏆 Protocol Tycoon' },
          { rank: 2, user_id: 'u2', username: 'SearchQueen', profile_photo: 'https://i.pravatar.cc/150?img=2', sales_count: 189, revenue: 432.10, title: '💎 Diamond Seller' },
          { rank: 3, user_id: 'u3', username: 'DataNinja', profile_photo: 'https://i.pravatar.cc/150?img=3', sales_count: 145, revenue: 298.50, title: '⭐ Star Seller' },
        ]);
      }
    } finally {
      setLoading(false);
    }
  };

  // Simple bar chart component
  const BarChart = ({ data, title }: { data: Record<string, number>; title: string }) => {
    const entries = Object.entries(data).slice(0, 6);
    const maxValue = Math.max(...entries.map(([, v]) => v));

    return (
      <View style={styles.chartContainer}>
        <Text style={styles.chartTitle}>{title}</Text>
        {entries.map(([label, value], index) => (
          <View key={label} style={styles.barRow}>
            <Text style={styles.barLabel} numberOfLines={1}>{label}</Text>
            <View style={styles.barContainer}>
              <View 
                style={[
                  styles.bar, 
                  { 
                    width: `${(value / maxValue) * 100}%`,
                    backgroundColor: PIE_COLORS[index % PIE_COLORS.length]
                  }
                ]} 
              />
            </View>
            <Text style={styles.barValue}>{value}</Text>
          </View>
        ))}
      </View>
    );
  };

  // Pie chart visualization (simplified)
  const PieChart = ({ data, title }: { data: Record<string, number>; title: string }) => {
    const entries = Object.entries(data).slice(0, 6);
    const total = entries.reduce((sum, [, v]) => sum + v, 0);

    return (
      <View style={styles.chartContainer}>
        <Text style={styles.chartTitle}>{title}</Text>
        <View style={styles.pieContainer}>
          <View style={styles.pieCircle}>
            {entries.map(([label, value], index) => {
              const percentage = Math.round((value / total) * 100);
              return (
                <View 
                  key={label} 
                  style={[
                    styles.pieSegment, 
                    { 
                      backgroundColor: PIE_COLORS[index % PIE_COLORS.length],
                      flex: value 
                    }
                  ]} 
                />
              );
            })}
          </View>
          <View style={styles.pieLegend}>
            {entries.map(([label, value], index) => (
              <View key={label} style={styles.legendItem}>
                <View style={[styles.legendColor, { backgroundColor: PIE_COLORS[index % PIE_COLORS.length] }]} />
                <Text style={styles.legendText}>{label}: {Math.round((value / total) * 100)}%</Text>
              </View>
            ))}
          </View>
        </View>
      </View>
    );
  };

  const renderStatistics = () => (
    <ScrollView showsVerticalScrollIndicator={false} contentContainerStyle={styles.scrollContent}>
      {/* Overview Cards */}
      <Text style={styles.sectionTitle}>📊 Overview - The Big Picture</Text>
      <View style={styles.overviewGrid}>
        {[
          { label: 'Total Users', value: statistics?.overview.total_users || 0, icon: 'people', color: colors.primary },
          { label: 'Protocols', value: statistics?.overview.total_protocols || 0, icon: 'code-working', color: colors.secondary },
          { label: 'Searches', value: statistics?.overview.total_searches || 0, icon: 'search', color: colors.accent },
          { label: 'Total Sales', value: statistics?.overview.total_sales || 0, icon: 'cart', color: colors.marketplaceGold },
          { label: 'Revenue', value: `$${statistics?.overview.total_revenue?.toFixed(2) || '0.00'}`, icon: 'cash', color: colors.success },
        ].map((stat, index) => (
          <View key={index} style={[styles.overviewCard, { borderLeftColor: stat.color }]}>
            <Ionicons name={stat.icon as any} size={24} color={stat.color} />
            <Text style={styles.overviewValue}>{stat.value}</Text>
            <Text style={styles.overviewLabel}>{stat.label}</Text>
          </View>
        ))}
      </View>

      {/* Country Breakdown */}
      {statistics?.country_breakdown && (
        <BarChart data={statistics.country_breakdown} title="🌍 Results by Country" />
      )}

      {/* Content Type Breakdown */}
      {statistics?.content_type_breakdown && (
        <PieChart data={statistics.content_type_breakdown} title="📄 Content Type Distribution" />
      )}

      {/* Top Protocol Words */}
      <View style={styles.chartContainer}>
        <Text style={styles.chartTitle}>🔤 Top Protocol Words</Text>
        <Text style={styles.chartSubtitle}>The words that make protocols POWERFUL!</Text>
        {statistics?.top_protocol_words?.map((item, index) => (
          <View key={item.word} style={styles.wordRow}>
            <Text style={styles.wordRank}>#{index + 1}</Text>
            <Text style={styles.wordText}>{item.word}</Text>
            <View style={styles.wordCountBadge}>
              <Text style={styles.wordCount}>{item.count} uses</Text>
            </View>
          </View>
        ))}
      </View>

      {/* Book Promo */}
      <View style={styles.promoCard}>
        <Text style={styles.promoTitle}>📚 Speaking of Statistics...</Text>
        <Text style={styles.promoText}>
          "Letters to Evelyn" by John Selman has been read by THOUSANDS! 
          (Okay, we don't have exact numbers, but trust us, it's a LOT.)
          Join the club and see what all the fuss is about!
        </Text>
        <TouchableOpacity style={styles.promoButton}>
          <Text style={styles.promoButtonText}>Get the Book on Amazon! 📖</Text>
        </TouchableOpacity>
      </View>
    </ScrollView>
  );

  const renderLeaderboard = () => (
    <ScrollView showsVerticalScrollIndicator={false} contentContainerStyle={styles.scrollContent}>
      {/* Tabs */}
      <View style={styles.leaderboardTabs}>
        {(['sales', 'revenue', 'both'] as LeaderboardTab[]).map((tab) => (
          <TouchableOpacity
            key={tab}
            style={[styles.leaderboardTab, leaderboardTab === tab && styles.leaderboardTabActive]}
            onPress={() => setLeaderboardTab(tab)}
          >
            <Text style={[styles.leaderboardTabText, leaderboardTab === tab && styles.leaderboardTabTextActive]}>
              {tab === 'sales' ? '📊 Sales' : tab === 'revenue' ? '💰 Revenue' : '🏆 Both'}
            </Text>
          </TouchableOpacity>
        ))}
      </View>

      <Text style={styles.leaderboardSubtitle}>
        {leaderboardTab === 'sales' ? 'Sorted by number of sales' : 
         leaderboardTab === 'revenue' ? 'Sorted by total earnings' : 
         'The complete picture!'}
      </Text>

      {/* Leaderboard Entries */}
      {leaderboard.map((entry) => (
        <View key={entry.user_id} style={[styles.leaderboardCard, entry.rank <= 3 && styles.topThreeCard]}>
          <View style={[styles.rankBadge, getRankStyle(entry.rank)]}>
            <Text style={styles.rankText}>{entry.rank}</Text>
          </View>
          
          <Image 
            source={{ uri: entry.profile_photo || 'https://i.pravatar.cc/150' }}
            style={styles.leaderboardAvatar}
          />
          
          <View style={styles.leaderboardInfo}>
            <Text style={styles.leaderboardUsername}>{entry.username}</Text>
            <Text style={styles.leaderboardTitle}>{entry.title}</Text>
          </View>
          
          <View style={styles.leaderboardStats}>
            <Text style={styles.statValue}>{entry.sales_count}</Text>
            <Text style={styles.statLabel}>Sales</Text>
            <Text style={styles.statValue}>${entry.revenue.toFixed(2)}</Text>
            <Text style={styles.statLabel}>Earned</Text>
          </View>
        </View>
      ))}

      {leaderboard.length === 0 && (
        <View style={styles.emptyLeaderboard}>
          <Text style={styles.emptyText}>No sellers yet!</Text>
          <Text style={styles.emptySubtext}>Be the first to claim the throne! 👑</Text>
        </View>
      )}

      {/* Marketplace Promo */}
      <View style={styles.promoCard}>
        <Text style={styles.promoTitle}>🎯 Want to be on this list?</Text>
        <Text style={styles.promoText}>
          List your protocols on the World Wide Marketplace and start climbing the ranks!
          Remember: 90% of every sale goes directly to YOU. We're basically just here to hold your crown. 👑
        </Text>
      </View>
    </ScrollView>
  );

  const renderBadges = () => (
    <ScrollView showsVerticalScrollIndicator={false} contentContainerStyle={styles.scrollContent}>
      <Text style={styles.sectionTitle}>🎖️ Achievement Badges</Text>
      <Text style={styles.sectionSubtitle}>Collect them all and become a Protocol Legend!</Text>
      
      <View style={styles.badgesGrid}>
        {(userBadges.length > 0 ? userBadges : badges).map((badge) => (
          <View 
            key={badge.id} 
            style={[
              styles.badgeCard, 
              badge.locked && styles.badgeCardLocked,
              badge.rarity === 'legendary' && styles.badgeLegendary,
              badge.rarity === 'epic' && styles.badgeEpic,
              badge.rarity === 'rare' && styles.badgeRare,
            ]}
          >
            <Text style={styles.badgeIcon}>{badge.icon}</Text>
            <Text style={[styles.badgeName, badge.locked && styles.badgeNameLocked]}>{badge.name}</Text>
            <Text style={[styles.badgeDesc, badge.locked && styles.badgeDescLocked]} numberOfLines={2}>
              {badge.description}
            </Text>
            <View style={[styles.rarityBadge, getRarityStyle(badge.rarity)]}>
              <Text style={styles.rarityText}>{badge.rarity.toUpperCase()}</Text>
            </View>
            {badge.locked && (
              <View style={styles.lockedOverlay}>
                <Ionicons name="lock-closed" size={24} color={colors.textMuted} />
              </View>
            )}
          </View>
        ))}
      </View>

      {/* Letters to Evelyn Badge Promo */}
      <View style={styles.promoCard}>
        <Text style={styles.promoTitle}>📚 The LEGENDARY Badge</Text>
        <Text style={styles.promoText}>
          Share "Letters to Evelyn" with a friend to unlock the rarest badge in the game!
          Only TRUE fans have this one. Are you a true fan? Prove it! 🏆
        </Text>
      </View>
    </ScrollView>
  );

  const getRankStyle = (rank: number) => {
    if (rank === 1) return { backgroundColor: colors.marketplaceGold };
    if (rank === 2) return { backgroundColor: '#C0C0C0' };
    if (rank === 3) return { backgroundColor: '#CD7F32' };
    return { backgroundColor: colors.cardBackground };
  };

  const getRarityStyle = (rarity: string) => {
    switch (rarity) {
      case 'legendary': return { backgroundColor: colors.marketplaceGold };
      case 'epic': return { backgroundColor: colors.secondary };
      case 'rare': return { backgroundColor: colors.accent };
      default: return { backgroundColor: colors.gray };
    }
  };

  if (loading) {
    return (
      <SafeAreaView style={styles.container} edges={['bottom']}>
        <View style={styles.loadingContainer}>
          <ActivityIndicator size="large" color={colors.primary} />
          <Text style={styles.loadingText}>Crunching numbers... 📊</Text>
          <Text style={styles.loadingSubtext}>Math is hard, but we're doing it for YOU!</Text>
        </View>
      </SafeAreaView>
    );
  }

  return (
    <SafeAreaView style={styles.container} edges={['bottom']}>
      <View style={styles.header}>
        <Text style={styles.headerTitle}>📈 Statistics & Leaderboards</Text>
        <Text style={styles.headerSubtitle}>
          "Numbers don't lie (but they do exaggerate sometimes)" 😉
        </Text>
      </View>

      {/* View Mode Tabs */}
      <View style={styles.viewTabs}>
        {[
          { mode: 'stats' as ViewMode, icon: 'stats-chart', label: 'Stats' },
          { mode: 'leaderboard' as ViewMode, icon: 'trophy', label: 'Leaders' },
          { mode: 'badges' as ViewMode, icon: 'medal', label: 'Badges' },
        ].map((tab) => (
          <TouchableOpacity
            key={tab.mode}
            style={[styles.viewTab, viewMode === tab.mode && styles.viewTabActive]}
            onPress={() => setViewMode(tab.mode)}
          >
            <Ionicons 
              name={tab.icon as any} 
              size={20} 
              color={viewMode === tab.mode ? colors.white : colors.primary} 
            />
            <Text style={[styles.viewTabText, viewMode === tab.mode && styles.viewTabTextActive]}>
              {tab.label}
            </Text>
          </TouchableOpacity>
        ))}
      </View>

      {/* Content */}
      {viewMode === 'stats' && renderStatistics()}
      {viewMode === 'leaderboard' && renderLeaderboard()}
      {viewMode === 'badges' && renderBadges()}
    </SafeAreaView>
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
  headerTitle: {
    fontSize: 22,
    fontWeight: 'bold',
    color: colors.text,
    textAlign: 'center',
  },
  headerSubtitle: {
    fontSize: 12,
    color: colors.textMuted,
    textAlign: 'center',
    marginTop: 4,
    fontStyle: 'italic',
  },
  viewTabs: {
    flexDirection: 'row',
    padding: 12,
    gap: 8,
  },
  viewTab: {
    flex: 1,
    flexDirection: 'row',
    alignItems: 'center',
    justifyContent: 'center',
    paddingVertical: 10,
    borderRadius: 12,
    backgroundColor: colors.cardBackground,
    borderWidth: 1,
    borderColor: colors.cardBorder,
    gap: 6,
  },
  viewTabActive: {
    backgroundColor: colors.primary,
    borderColor: colors.primary,
  },
  viewTabText: {
    color: colors.primary,
    fontSize: 13,
    fontWeight: '600',
  },
  viewTabTextActive: {
    color: colors.white,
  },
  scrollContent: {
    padding: 16,
    paddingBottom: 40,
  },
  sectionTitle: {
    fontSize: 18,
    fontWeight: 'bold',
    color: colors.text,
    marginBottom: 12,
  },
  sectionSubtitle: {
    fontSize: 13,
    color: colors.textMuted,
    marginBottom: 16,
  },
  overviewGrid: {
    flexDirection: 'row',
    flexWrap: 'wrap',
    gap: 12,
    marginBottom: 24,
  },
  overviewCard: {
    backgroundColor: colors.cardBackground,
    borderRadius: 12,
    padding: 16,
    width: (width - 56) / 2,
    borderLeftWidth: 4,
    alignItems: 'center',
  },
  overviewValue: {
    fontSize: 24,
    fontWeight: 'bold',
    color: colors.text,
    marginTop: 8,
  },
  overviewLabel: {
    fontSize: 12,
    color: colors.textMuted,
    marginTop: 4,
  },
  chartContainer: {
    backgroundColor: colors.cardBackground,
    borderRadius: 16,
    padding: 16,
    marginBottom: 16,
  },
  chartTitle: {
    fontSize: 16,
    fontWeight: 'bold',
    color: colors.text,
    marginBottom: 4,
  },
  chartSubtitle: {
    fontSize: 12,
    color: colors.textMuted,
    marginBottom: 12,
  },
  barRow: {
    flexDirection: 'row',
    alignItems: 'center',
    marginVertical: 6,
  },
  barLabel: {
    width: 70,
    fontSize: 12,
    color: colors.text,
  },
  barContainer: {
    flex: 1,
    height: 20,
    backgroundColor: colors.background,
    borderRadius: 10,
    overflow: 'hidden',
    marginHorizontal: 8,
  },
  bar: {
    height: '100%',
    borderRadius: 10,
  },
  barValue: {
    width: 40,
    fontSize: 12,
    color: colors.textMuted,
    textAlign: 'right',
  },
  pieContainer: {
    alignItems: 'center',
  },
  pieCircle: {
    flexDirection: 'row',
    width: width - 80,
    height: 30,
    borderRadius: 15,
    overflow: 'hidden',
    marginBottom: 16,
  },
  pieSegment: {
    height: '100%',
  },
  pieLegend: {
    flexDirection: 'row',
    flexWrap: 'wrap',
    justifyContent: 'center',
    gap: 12,
  },
  legendItem: {
    flexDirection: 'row',
    alignItems: 'center',
  },
  legendColor: {
    width: 12,
    height: 12,
    borderRadius: 6,
    marginRight: 4,
  },
  legendText: {
    fontSize: 11,
    color: colors.text,
  },
  wordRow: {
    flexDirection: 'row',
    alignItems: 'center',
    paddingVertical: 8,
    borderBottomWidth: 1,
    borderBottomColor: colors.cardBorder,
  },
  wordRank: {
    width: 30,
    fontSize: 14,
    fontWeight: 'bold',
    color: colors.primary,
  },
  wordText: {
    flex: 1,
    fontSize: 14,
    color: colors.text,
    textTransform: 'capitalize',
  },
  wordCountBadge: {
    backgroundColor: colors.background,
    paddingHorizontal: 8,
    paddingVertical: 2,
    borderRadius: 10,
  },
  wordCount: {
    fontSize: 11,
    color: colors.textMuted,
  },
  promoCard: {
    backgroundColor: colors.secondary,
    borderRadius: 16,
    padding: 20,
    marginTop: 16,
    borderWidth: 2,
    borderColor: colors.marketplaceGold,
  },
  promoTitle: {
    fontSize: 18,
    fontWeight: 'bold',
    color: colors.marketplaceGold,
    marginBottom: 8,
  },
  promoText: {
    fontSize: 14,
    color: colors.white,
    lineHeight: 20,
  },
  promoButton: {
    backgroundColor: colors.marketplaceGold,
    paddingVertical: 12,
    borderRadius: 10,
    marginTop: 12,
    alignItems: 'center',
  },
  promoButtonText: {
    color: colors.background,
    fontWeight: 'bold',
    fontSize: 14,
  },
  leaderboardTabs: {
    flexDirection: 'row',
    gap: 8,
    marginBottom: 12,
  },
  leaderboardTab: {
    flex: 1,
    paddingVertical: 10,
    borderRadius: 10,
    backgroundColor: colors.cardBackground,
    alignItems: 'center',
  },
  leaderboardTabActive: {
    backgroundColor: colors.primary,
  },
  leaderboardTabText: {
    color: colors.primary,
    fontWeight: '600',
    fontSize: 12,
  },
  leaderboardTabTextActive: {
    color: colors.white,
  },
  leaderboardSubtitle: {
    color: colors.textMuted,
    fontSize: 12,
    marginBottom: 16,
    textAlign: 'center',
  },
  leaderboardCard: {
    flexDirection: 'row',
    alignItems: 'center',
    backgroundColor: colors.cardBackground,
    borderRadius: 12,
    padding: 12,
    marginBottom: 10,
    borderWidth: 1,
    borderColor: colors.cardBorder,
  },
  topThreeCard: {
    borderColor: colors.marketplaceGold,
    borderWidth: 2,
  },
  rankBadge: {
    width: 32,
    height: 32,
    borderRadius: 16,
    alignItems: 'center',
    justifyContent: 'center',
  },
  rankText: {
    color: colors.white,
    fontWeight: 'bold',
    fontSize: 14,
  },
  leaderboardAvatar: {
    width: 44,
    height: 44,
    borderRadius: 22,
    marginLeft: 10,
  },
  leaderboardInfo: {
    flex: 1,
    marginLeft: 12,
  },
  leaderboardUsername: {
    color: colors.text,
    fontWeight: 'bold',
    fontSize: 14,
  },
  leaderboardTitle: {
    color: colors.textMuted,
    fontSize: 11,
    marginTop: 2,
  },
  leaderboardStats: {
    alignItems: 'center',
  },
  statValue: {
    color: colors.primary,
    fontWeight: 'bold',
    fontSize: 14,
  },
  statLabel: {
    color: colors.textMuted,
    fontSize: 10,
    marginBottom: 4,
  },
  emptyLeaderboard: {
    alignItems: 'center',
    padding: 40,
  },
  emptyText: {
    color: colors.text,
    fontSize: 18,
    fontWeight: 'bold',
  },
  emptySubtext: {
    color: colors.textMuted,
    fontSize: 14,
    marginTop: 8,
  },
  badgesGrid: {
    flexDirection: 'row',
    flexWrap: 'wrap',
    gap: 12,
  },
  badgeCard: {
    width: (width - 56) / 2,
    backgroundColor: colors.cardBackground,
    borderRadius: 16,
    padding: 16,
    alignItems: 'center',
    borderWidth: 2,
    borderColor: colors.cardBorder,
    position: 'relative',
  },
  badgeCardLocked: {
    opacity: 0.6,
  },
  badgeLegendary: {
    borderColor: colors.marketplaceGold,
  },
  badgeEpic: {
    borderColor: colors.secondary,
  },
  badgeRare: {
    borderColor: colors.accent,
  },
  badgeIcon: {
    fontSize: 36,
    marginBottom: 8,
  },
  badgeName: {
    color: colors.text,
    fontWeight: 'bold',
    fontSize: 13,
    textAlign: 'center',
  },
  badgeNameLocked: {
    color: colors.textMuted,
  },
  badgeDesc: {
    color: colors.textLight,
    fontSize: 11,
    textAlign: 'center',
    marginTop: 4,
  },
  badgeDescLocked: {
    color: colors.textMuted,
  },
  rarityBadge: {
    paddingHorizontal: 8,
    paddingVertical: 2,
    borderRadius: 8,
    marginTop: 8,
  },
  rarityText: {
    color: colors.white,
    fontSize: 9,
    fontWeight: 'bold',
  },
  lockedOverlay: {
    position: 'absolute',
    top: 8,
    right: 8,
  },
});
