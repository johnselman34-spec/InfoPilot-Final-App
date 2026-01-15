import React, { useState, useEffect } from 'react';
import {
  View,
  Text,
  StyleSheet,
  ScrollView,
  TouchableOpacity,
  ActivityIndicator,
  Dimensions,
  RefreshControl,
} from 'react-native';
import { SafeAreaView } from 'react-native-safe-area-context';
import { Ionicons } from '@expo/vector-icons';
import { colors } from '../../src/utils/colors';
import { api } from '../../src/services/api';
import { LineChart, BarChart, PieChart, ProgressChart } from 'react-native-chart-kit';

const { width } = Dimensions.get('window');
const chartWidth = width - 40;

interface StatisticsData {
  overview: {
    total_users: number;
    total_protocols: number;
    total_searches: number;
    total_categories: number;
    total_transactions: number;
    total_revenue: number;
  };
  top_categories: Array<{ name: string; count: number }>;
  top_words: Array<{ word: string; count: number }>;
  top_protocol_words: Array<{ word: string; count: number }>;
  document_types: Array<{ type: string; count: number }>;
  countries: Array<{ country: string; count: number }>;
  states: Array<{ state: string; count: number }>;
}

interface LeaderboardEntry {
  rank: number;
  username: string;
  sales_count: number;
  revenue: number;
}

type ChartType = 'overview' | 'categories' | 'words' | 'documents' | 'geography' | 'leaderboard' | 'clipboard' | 'achievements';
type LeaderboardTab = 'sales' | 'revenue';

interface ClipboardLeader {
  protocol_id: string;
  protocol_name: string;
  creator: string;
  copy_count: number;
  price: number;
}

interface Achievement {
  id: string;
  name: string;
  description: string;
  funny_tagline: string;
  icon: string;
  category: string;
  rarity: string;
  earned: boolean;
  progress: number;
}

export default function StatisticsScreen() {
  const [loading, setLoading] = useState(true);
  const [refreshing, setRefreshing] = useState(false);
  const [stats, setStats] = useState<StatisticsData | null>(null);
  const [leaderboard, setLeaderboard] = useState<LeaderboardEntry[]>([]);
  const [clipboardLeaders, setClipboardLeaders] = useState<ClipboardLeader[]>([]);
  const [achievements, setAchievements] = useState<Achievement[]>([]);
  const [activeChart, setActiveChart] = useState<ChartType>('overview');
  const [leaderboardTab, setLeaderboardTab] = useState<LeaderboardTab>('sales');
  const [funnyMessage, setFunnyMessage] = useState('');

  useEffect(() => {
    loadData();
    loadClipboardLeaders();
    loadAchievements();
  }, []);

  useEffect(() => {
    loadLeaderboard();
  }, [leaderboardTab]);

  const loadData = async () => {
    try {
      setLoading(true);
      const response = await api.get('/statistics');
      setStats(response);
      setFunnyMessage(response.funny_message || getRandomFunnyMessage());
    } catch (error) {
      console.error('Load statistics error:', error);
      // Use mock data for demo
      setStats(getMockStats());
      setFunnyMessage(getRandomFunnyMessage());
    } finally {
      setLoading(false);
    }
  };

  const loadClipboardLeaders = async () => {
    try {
      const response = await api.get('/statistics/clipboard-leaders');
      setClipboardLeaders(response.leaders || []);
    } catch (error) {
      // Use mock data
      setClipboardLeaders(getMockClipboardLeaders());
    }
  };

  const loadAchievements = async () => {
    try {
      const response = await api.get('/achievements/all');
      setAchievements(response.achievements || []);
    } catch (error) {
      setAchievements(getMockAchievements());
    }
  };

  const getMockClipboardLeaders = (): ClipboardLeader[] => [
    { protocol_id: '1', protocol_name: 'George Bush Research', creator: 'JohnSelman', copy_count: 1247, price: 0 },
    { protocol_id: '2', protocol_name: 'William C. Gamble Historical', creator: 'JohnSelman', copy_count: 892, price: 9.99 },
    { protocol_id: '3', protocol_name: 'Richard J. Selman Research', creator: 'JohnSelman', copy_count: 654, price: 4.99 },
    { protocol_id: '4', protocol_name: 'American Civil War Heroes', creator: 'ProtocolMaster', copy_count: 543, price: 2.99 },
    { protocol_id: '5', protocol_name: 'Technology Research', creator: 'DataWizard', copy_count: 432, price: 0 },
  ];

  const getMockAchievements = (): Achievement[] => [
    { id: '1', name: 'Protocol Pioneer', description: 'Created first protocol', funny_tagline: 'Baby steps!', icon: '🎯', category: 'protocols', rarity: 'common', earned: false, progress: 0 },
    { id: '2', name: 'Money Maker', description: 'Made first sale', funny_tagline: 'Cha-ching!', icon: '💰', category: 'sales', rarity: 'common', earned: false, progress: 0 },
    { id: '3', name: 'Social Butterfly', description: 'Made 10 friends', funny_tagline: 'Popular!', icon: '🦋', category: 'social', rarity: 'common', earned: false, progress: 0 },
  ];

  const loadLeaderboard = async () => {
    try {
      const response = await api.get('/leaderboard/sellers', { tab: leaderboardTab });
      setLeaderboard(response.leaderboard || []);
    } catch (error) {
      console.error('Load leaderboard error:', error);
      setLeaderboard(getMockLeaderboard());
    }
  };

  const onRefresh = async () => {
    setRefreshing(true);
    await loadData();
    await loadLeaderboard();
    setRefreshing(false);
  };

  const getRandomFunnyMessage = () => {
    const messages = [
      "📊 Numbers so impressive, even calculators are jealous!",
      "🚀 These stats are out of this world - literally sending them to NASA!",
      "💡 Fun fact: 73% of statistics are made up. But not these ones!",
      "🎯 Our data is so accurate, fortune tellers are asking for tips!",
      "📈 Growth so strong, our charts need protein shakes!",
      "🔥 These numbers are hotter than a jalapeño in a sauna!",
      "🎪 Step right up! See the greatest show in data!",
    ];
    return messages[Math.floor(Math.random() * messages.length)];
  };

  const getMockStats = (): StatisticsData => ({
    overview: {
      total_users: 1247,
      total_protocols: 892,
      total_searches: 15632,
      total_categories: 156,
      total_transactions: 2891,
      total_revenue: 8945.50,
    },
    top_categories: [
      { name: 'American Civil War', count: 234 },
      { name: 'Technology Research', count: 198 },
      { name: 'World History', count: 167 },
      { name: 'Science & Medicine', count: 145 },
      { name: 'Business Strategy', count: 121 },
    ],
    top_words: [
      { word: 'research', count: 1234 },
      { word: 'history', count: 1089 },
      { word: 'technology', count: 956 },
      { word: 'science', count: 823 },
      { word: 'business', count: 712 },
      { word: 'education', count: 645 },
      { word: 'innovation', count: 589 },
      { word: 'strategy', count: 534 },
      { word: 'development', count: 478 },
      { word: 'analysis', count: 423 },
    ],
    top_protocol_words: [
      { word: 'civil war', count: 456 },
      { word: 'heroes', count: 389 },
      { word: 'leadership', count: 312 },
      { word: 'military', count: 278 },
      { word: 'George Bush', count: 234 },
      { word: 'William C. Gamble', count: 198 },
      { word: 'battle', count: 167 },
      { word: 'strategy', count: 145 },
      { word: 'victory', count: 123 },
      { word: 'generals', count: 112 },
    ],
    document_types: [
      { type: 'Academic', count: 3456 },
      { type: 'News', count: 2891 },
      { type: 'Blog', count: 2234 },
      { type: 'Wiki', count: 1876 },
      { type: 'Forum', count: 1234 },
      { type: 'PhD', count: 892 },
      { type: 'Government', count: 567 },
    ],
    countries: [
      { country: 'United States', count: 5678 },
      { country: 'United Kingdom', count: 2345 },
      { country: 'Germany', count: 1234 },
      { country: 'Canada', count: 987 },
      { country: 'Australia', count: 765 },
      { country: 'France', count: 654 },
      { country: 'Japan', count: 543 },
    ],
    states: [
      { state: 'California', count: 1234 },
      { state: 'New York', count: 1098 },
      { state: 'Texas', count: 876 },
      { state: 'Florida', count: 765 },
      { state: 'New Mexico', count: 543 },
    ],
  });

  const getMockLeaderboard = (): LeaderboardEntry[] => [
    { rank: 1, username: 'JohnSelman', sales_count: 156, revenue: 2345.50 },
    { rank: 2, username: 'ProtocolMaster', sales_count: 134, revenue: 1987.25 },
    { rank: 3, username: 'ResearchGuru', sales_count: 112, revenue: 1654.00 },
    { rank: 4, username: 'DataWizard', sales_count: 98, revenue: 1432.75 },
    { rank: 5, username: 'InfoPilotPro', sales_count: 87, revenue: 1298.50 },
  ];

  const chartConfig = {
    backgroundColor: colors.cardBackground,
    backgroundGradientFrom: colors.cardBackground,
    backgroundGradientTo: colors.background,
    decimalPlaces: 0,
    color: (opacity = 1) => `rgba(147, 51, 234, ${opacity})`,
    labelColor: (opacity = 1) => `rgba(255, 255, 255, ${opacity})`,
    style: {
      borderRadius: 16,
    },
    propsForDots: {
      r: '6',
      strokeWidth: '2',
      stroke: colors.primary,
    },
  };

  const pieChartColors = [
    '#9333EA', '#EC4899', '#F97316', '#10B981', '#3B82F6', '#EAB308', '#6366F1'
  ];

  // Render Overview Cards
  const renderOverviewCards = () => {
    if (!stats) return null;
    
    const cards = [
      { icon: 'people', label: 'Total Users', value: stats.overview.total_users, color: '#9333EA' },
      { icon: 'document-text', label: 'Protocols', value: stats.overview.total_protocols, color: '#EC4899' },
      { icon: 'search', label: 'Searches', value: stats.overview.total_searches, color: '#3B82F6' },
      { icon: 'folder', label: 'Categories', value: stats.overview.total_categories, color: '#10B981' },
      { icon: 'cart', label: 'Transactions', value: stats.overview.total_transactions, color: '#F97316' },
      { icon: 'cash', label: 'Revenue', value: `$${stats.overview.total_revenue.toFixed(2)}`, color: '#EAB308' },
    ];

    return (
      <View style={styles.overviewGrid}>
        {cards.map((card, index) => (
          <View key={index} style={[styles.overviewCard, { borderLeftColor: card.color }]}>
            <View style={[styles.cardIconContainer, { backgroundColor: card.color + '20' }]}>
              <Ionicons name={card.icon as any} size={24} color={card.color} />
            </View>
            <Text style={styles.cardValue}>{card.value}</Text>
            <Text style={styles.cardLabel}>{card.label}</Text>
          </View>
        ))}
      </View>
    );
  };

  // Render Category Bar Chart
  const renderCategoryChart = () => {
    if (!stats || !stats.top_categories.length) return null;

    const data = {
      labels: stats.top_categories.slice(0, 5).map(c => c.name.substring(0, 10)),
      datasets: [{
        data: stats.top_categories.slice(0, 5).map(c => c.count),
      }],
    };

    return (
      <View style={styles.chartContainer}>
        <Text style={styles.chartTitle}>📊 Top Categories</Text>
        <BarChart
          data={data}
          width={chartWidth}
          height={220}
          chartConfig={chartConfig}
          verticalLabelRotation={15}
          style={styles.chart}
          yAxisLabel=""
          yAxisSuffix=""
        />
      </View>
    );
  };

  // Render Top Words Lists
  const renderTopWords = () => {
    if (!stats) return null;

    return (
      <View style={styles.wordsContainer}>
        <View style={styles.wordsList}>
          <Text style={styles.wordsTitle}>🔤 Top 10 Most Used Words</Text>
          {stats.top_words.slice(0, 10).map((item, index) => (
            <View key={index} style={styles.wordItem}>
              <Text style={styles.wordRank}>#{index + 1}</Text>
              <Text style={styles.wordText}>{item.word}</Text>
              <Text style={styles.wordCount}>{item.count}</Text>
            </View>
          ))}
        </View>

        <View style={styles.wordsList}>
          <Text style={styles.wordsTitle}>🎯 Top 10 Protocol Words</Text>
          {stats.top_protocol_words.slice(0, 10).map((item, index) => (
            <View key={index} style={styles.wordItem}>
              <Text style={styles.wordRank}>#{index + 1}</Text>
              <Text style={styles.wordText}>{item.word}</Text>
              <Text style={styles.wordCount}>{item.count}</Text>
            </View>
          ))}
        </View>
      </View>
    );
  };

  // Render Document Type Pie Chart
  const renderDocumentTypeChart = () => {
    if (!stats || !stats.document_types.length) return null;

    const pieData = stats.document_types.slice(0, 7).map((item, index) => ({
      name: item.type,
      population: item.count,
      color: pieChartColors[index % pieChartColors.length],
      legendFontColor: colors.text,
      legendFontSize: 12,
    }));

    return (
      <View style={styles.chartContainer}>
        <Text style={styles.chartTitle}>📋 Document Types Breakdown</Text>
        <PieChart
          data={pieData}
          width={chartWidth}
          height={220}
          chartConfig={chartConfig}
          accessor="population"
          backgroundColor="transparent"
          paddingLeft="15"
          style={styles.chart}
        />
      </View>
    );
  };

  // Render Geography Stats
  const renderGeographyStats = () => {
    if (!stats) return null;

    return (
      <View style={styles.geographyContainer}>
        <Text style={styles.chartTitle}>🌍 Geographic Distribution</Text>
        
        <View style={styles.geoSection}>
          <Text style={styles.geoSectionTitle}>🏳️ Top Countries</Text>
          {stats.countries.slice(0, 5).map((item, index) => (
            <View key={index} style={styles.geoItem}>
              <Text style={styles.geoRank}>#{index + 1}</Text>
              <View style={styles.geoBarContainer}>
                <View 
                  style={[
                    styles.geoBar, 
                    { 
                      width: `${(item.count / stats.countries[0].count) * 100}%`,
                      backgroundColor: pieChartColors[index % pieChartColors.length],
                    }
                  ]} 
                />
              </View>
              <Text style={styles.geoName}>{item.country}</Text>
              <Text style={styles.geoCount}>{item.count}</Text>
            </View>
          ))}
        </View>

        <View style={styles.geoSection}>
          <Text style={styles.geoSectionTitle}>🏛️ Top US States</Text>
          {stats.states.slice(0, 5).map((item, index) => (
            <View key={index} style={styles.geoItem}>
              <Text style={styles.geoRank}>#{index + 1}</Text>
              <View style={styles.geoBarContainer}>
                <View 
                  style={[
                    styles.geoBar, 
                    { 
                      width: `${(item.count / stats.states[0].count) * 100}%`,
                      backgroundColor: pieChartColors[(index + 3) % pieChartColors.length],
                    }
                  ]} 
                />
              </View>
              <Text style={styles.geoName}>{item.state}</Text>
              <Text style={styles.geoCount}>{item.count}</Text>
            </View>
          ))}
        </View>
      </View>
    );
  };

  // Render Leaderboard
  const renderLeaderboard = () => {
    return (
      <View style={styles.leaderboardContainer}>
        <Text style={styles.chartTitle}>👑 Top Sellers Leaderboard</Text>
        
        <View style={styles.leaderboardTabs}>
          <TouchableOpacity
            style={[styles.tabButton, leaderboardTab === 'sales' && styles.tabButtonActive]}
            onPress={() => setLeaderboardTab('sales')}
          >
            <Text style={[styles.tabText, leaderboardTab === 'sales' && styles.tabTextActive]}>
              📦 By Sales
            </Text>
          </TouchableOpacity>
          <TouchableOpacity
            style={[styles.tabButton, leaderboardTab === 'revenue' && styles.tabButtonActive]}
            onPress={() => setLeaderboardTab('revenue')}
          >
            <Text style={[styles.tabText, leaderboardTab === 'revenue' && styles.tabTextActive]}>
              💰 By Revenue
            </Text>
          </TouchableOpacity>
        </View>

        {leaderboard.length === 0 ? (
          <View style={styles.emptyLeaderboard}>
            <Text style={styles.emptyText}>No sellers yet - be the first! 🏆</Text>
          </View>
        ) : (
          leaderboard.map((entry, index) => (
            <View 
              key={index} 
              style={[
                styles.leaderboardItem, 
                index === 0 && styles.leaderboardFirst,
                index === 1 && styles.leaderboardSecond,
                index === 2 && styles.leaderboardThird,
              ]}
            >
              <View style={styles.leaderboardRank}>
                <Text style={styles.rankText}>
                  {index === 0 ? '🥇' : index === 1 ? '🥈' : index === 2 ? '🥉' : `#${entry.rank}`}
                </Text>
              </View>
              <View style={styles.leaderboardInfo}>
                <Text style={styles.leaderboardUsername}>@{entry.username}</Text>
                <Text style={styles.leaderboardStats}>
                  {entry.sales_count} sales • ${entry.revenue.toFixed(2)}
                </Text>
              </View>
              <View style={styles.leaderboardBadge}>
                <Text style={styles.badgeText}>
                  {leaderboardTab === 'sales' ? entry.sales_count : `$${entry.revenue.toFixed(0)}`}
                </Text>
              </View>
            </View>
          ))
        )}
      </View>
    );
  };

  // Navigation tabs for different chart views
  const chartTabs: { key: ChartType; label: string; icon: string }[] = [
    { key: 'overview', label: 'Overview', icon: 'grid' },
    { key: 'categories', label: 'Categories', icon: 'folder' },
    { key: 'words', label: 'Words', icon: 'text' },
    { key: 'documents', label: 'Docs', icon: 'document' },
    { key: 'geography', label: 'Geo', icon: 'globe' },
    { key: 'leaderboard', label: 'Leaders', icon: 'trophy' },
  ];

  if (loading) {
    return (
      <SafeAreaView style={styles.container} edges={['bottom']}>
        <View style={styles.loadingContainer}>
          <ActivityIndicator size="large" color={colors.primary} />
          <Text style={styles.loadingText}>Crunching the numbers... 🔢</Text>
          <Text style={styles.loadingSubtext}>Our hamsters are working overtime!</Text>
        </View>
      </SafeAreaView>
    );
  }

  return (
    <SafeAreaView style={styles.container} edges={['bottom']}>
      {/* Header */}
      <View style={styles.header}>
        <Text style={styles.headerTitle}>📊 Statistics</Text>
        <Text style={styles.funnyMessage}>{funnyMessage}</Text>
      </View>

      {/* Chart Type Tabs */}
      <ScrollView 
        horizontal 
        showsHorizontalScrollIndicator={false} 
        style={styles.tabsScroll}
        contentContainerStyle={styles.tabsContent}
      >
        {chartTabs.map((tab) => (
          <TouchableOpacity
            key={tab.key}
            style={[styles.chartTab, activeChart === tab.key && styles.chartTabActive]}
            onPress={() => setActiveChart(tab.key)}
          >
            <Ionicons 
              name={tab.icon as any} 
              size={18} 
              color={activeChart === tab.key ? colors.white : colors.primary} 
            />
            <Text style={[styles.chartTabText, activeChart === tab.key && styles.chartTabTextActive]}>
              {tab.label}
            </Text>
          </TouchableOpacity>
        ))}
      </ScrollView>

      {/* Chart Content */}
      <ScrollView 
        style={styles.contentScroll}
        contentContainerStyle={styles.contentContainer}
        refreshControl={
          <RefreshControl refreshing={refreshing} onRefresh={onRefresh} tintColor={colors.primary} />
        }
      >
        {activeChart === 'overview' && renderOverviewCards()}
        {activeChart === 'categories' && renderCategoryChart()}
        {activeChart === 'words' && renderTopWords()}
        {activeChart === 'documents' && renderDocumentTypeChart()}
        {activeChart === 'geography' && renderGeographyStats()}
        {activeChart === 'leaderboard' && renderLeaderboard()}

        {/* Book Promotion */}
        <View style={styles.bookPromo}>
          <Text style={styles.bookPromoText}>
            📚 "Letters to Evelyn" - The book with MORE stats than this page! 📚
          </Text>
        </View>
      </ScrollView>
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
    fontSize: 24,
    fontWeight: 'bold',
    color: colors.text,
    textAlign: 'center',
  },
  funnyMessage: {
    fontSize: 12,
    color: colors.primary,
    textAlign: 'center',
    marginTop: 4,
    fontStyle: 'italic',
  },
  tabsScroll: {
    backgroundColor: colors.cardBackground,
    borderBottomWidth: 1,
    borderBottomColor: colors.cardBorder,
  },
  tabsContent: {
    paddingHorizontal: 12,
    paddingVertical: 10,
    gap: 8,
  },
  chartTab: {
    flexDirection: 'row',
    alignItems: 'center',
    paddingHorizontal: 14,
    paddingVertical: 8,
    borderRadius: 20,
    backgroundColor: colors.background,
    borderWidth: 1,
    borderColor: colors.primary,
    marginRight: 8,
    gap: 6,
  },
  chartTabActive: {
    backgroundColor: colors.primary,
  },
  chartTabText: {
    color: colors.primary,
    fontSize: 12,
    fontWeight: '600',
  },
  chartTabTextActive: {
    color: colors.white,
  },
  contentScroll: {
    flex: 1,
  },
  contentContainer: {
    padding: 16,
    paddingBottom: 40,
  },
  // Overview Cards
  overviewGrid: {
    flexDirection: 'row',
    flexWrap: 'wrap',
    justifyContent: 'space-between',
  },
  overviewCard: {
    width: (width - 48) / 2,
    backgroundColor: colors.cardBackground,
    borderRadius: 12,
    padding: 16,
    marginBottom: 12,
    borderLeftWidth: 4,
    alignItems: 'center',
  },
  cardIconContainer: {
    width: 48,
    height: 48,
    borderRadius: 24,
    justifyContent: 'center',
    alignItems: 'center',
    marginBottom: 8,
  },
  cardValue: {
    fontSize: 24,
    fontWeight: 'bold',
    color: colors.text,
  },
  cardLabel: {
    fontSize: 12,
    color: colors.textMuted,
    marginTop: 4,
  },
  // Charts
  chartContainer: {
    backgroundColor: colors.cardBackground,
    borderRadius: 16,
    padding: 16,
    marginBottom: 16,
  },
  chartTitle: {
    fontSize: 18,
    fontWeight: 'bold',
    color: colors.text,
    marginBottom: 16,
    textAlign: 'center',
  },
  chart: {
    borderRadius: 16,
  },
  // Words Lists
  wordsContainer: {
    gap: 16,
  },
  wordsList: {
    backgroundColor: colors.cardBackground,
    borderRadius: 16,
    padding: 16,
  },
  wordsTitle: {
    fontSize: 16,
    fontWeight: 'bold',
    color: colors.text,
    marginBottom: 12,
  },
  wordItem: {
    flexDirection: 'row',
    alignItems: 'center',
    paddingVertical: 8,
    borderBottomWidth: 1,
    borderBottomColor: colors.cardBorder,
  },
  wordRank: {
    width: 30,
    fontSize: 12,
    fontWeight: 'bold',
    color: colors.primary,
  },
  wordText: {
    flex: 1,
    fontSize: 14,
    color: colors.text,
  },
  wordCount: {
    fontSize: 14,
    fontWeight: '600',
    color: colors.accent,
  },
  // Geography
  geographyContainer: {
    backgroundColor: colors.cardBackground,
    borderRadius: 16,
    padding: 16,
  },
  geoSection: {
    marginBottom: 20,
  },
  geoSectionTitle: {
    fontSize: 14,
    fontWeight: 'bold',
    color: colors.text,
    marginBottom: 12,
  },
  geoItem: {
    flexDirection: 'row',
    alignItems: 'center',
    marginBottom: 10,
  },
  geoRank: {
    width: 30,
    fontSize: 12,
    fontWeight: 'bold',
    color: colors.primary,
  },
  geoBarContainer: {
    width: 80,
    height: 8,
    backgroundColor: colors.background,
    borderRadius: 4,
    marginRight: 10,
    overflow: 'hidden',
  },
  geoBar: {
    height: '100%',
    borderRadius: 4,
  },
  geoName: {
    flex: 1,
    fontSize: 13,
    color: colors.text,
  },
  geoCount: {
    fontSize: 13,
    fontWeight: '600',
    color: colors.accent,
  },
  // Leaderboard
  leaderboardContainer: {
    backgroundColor: colors.cardBackground,
    borderRadius: 16,
    padding: 16,
  },
  leaderboardTabs: {
    flexDirection: 'row',
    marginBottom: 16,
    gap: 12,
  },
  tabButton: {
    flex: 1,
    paddingVertical: 10,
    borderRadius: 12,
    backgroundColor: colors.background,
    alignItems: 'center',
    borderWidth: 1,
    borderColor: colors.cardBorder,
  },
  tabButtonActive: {
    backgroundColor: colors.primary,
    borderColor: colors.primary,
  },
  tabText: {
    fontSize: 13,
    fontWeight: '600',
    color: colors.textMuted,
  },
  tabTextActive: {
    color: colors.white,
  },
  emptyLeaderboard: {
    padding: 40,
    alignItems: 'center',
  },
  emptyText: {
    color: colors.textMuted,
    fontSize: 14,
  },
  leaderboardItem: {
    flexDirection: 'row',
    alignItems: 'center',
    paddingVertical: 12,
    paddingHorizontal: 12,
    borderRadius: 12,
    marginBottom: 8,
    backgroundColor: colors.background,
  },
  leaderboardFirst: {
    backgroundColor: '#FFD70020',
    borderWidth: 1,
    borderColor: '#FFD700',
  },
  leaderboardSecond: {
    backgroundColor: '#C0C0C020',
    borderWidth: 1,
    borderColor: '#C0C0C0',
  },
  leaderboardThird: {
    backgroundColor: '#CD7F3220',
    borderWidth: 1,
    borderColor: '#CD7F32',
  },
  leaderboardRank: {
    width: 40,
  },
  rankText: {
    fontSize: 18,
  },
  leaderboardInfo: {
    flex: 1,
  },
  leaderboardUsername: {
    fontSize: 14,
    fontWeight: 'bold',
    color: colors.text,
  },
  leaderboardStats: {
    fontSize: 12,
    color: colors.textMuted,
    marginTop: 2,
  },
  leaderboardBadge: {
    backgroundColor: colors.primary,
    paddingHorizontal: 12,
    paddingVertical: 6,
    borderRadius: 12,
  },
  badgeText: {
    color: colors.white,
    fontSize: 12,
    fontWeight: 'bold',
  },
  // Book Promo
  bookPromo: {
    backgroundColor: colors.secondary,
    padding: 16,
    borderRadius: 12,
    marginTop: 16,
    alignItems: 'center',
  },
  bookPromoText: {
    color: colors.marketplaceGold,
    fontSize: 14,
    fontWeight: 'bold',
    textAlign: 'center',
  },
});
