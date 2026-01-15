import React, { useState, useEffect, useCallback } from 'react';
import {
  View,
  Text,
  StyleSheet,
  ScrollView,
  TouchableOpacity,
  TextInput,
  Alert,
  ActivityIndicator,
  Image,
  Modal,
  KeyboardAvoidingView,
  Platform,
  RefreshControl,
} from 'react-native';
import { SafeAreaView } from 'react-native-safe-area-context';
import { Ionicons } from '@expo/vector-icons';
import { useRouter } from 'expo-router';
import { colors } from '../../src/utils/colors';
import { api } from '../../src/services/api';

interface User {
  id: string;
  username: string;
  email?: string;
  profile_photo?: string;
  is_friend?: boolean;
  friend_request_sent?: boolean;
  friend_request_received?: boolean;
  location?: string;
  protocols_count?: number;
}

interface Group {
  id: string;
  name: string;
  description: string;
  cover_image?: string;
  member_count: number;
  is_member: boolean;
  is_admin: boolean;
  created_at: string;
}

interface Page {
  id: string;
  name: string;
  description: string;
  cover_image?: string;
  follower_count: number;
  is_following: boolean;
  is_owner: boolean;
  category: string;
}

interface Post {
  id: string;
  author: {
    id: string;
    username: string;
    profile_photo?: string;
  };
  content: string;
  images?: string[];
  reactions: {
    like: number;
    love: number;
    funny: number;
    sad: number;
    caution: number;
    spam: number;
    best: number;
  };
  comments_count: number;
  created_at: string;
  user_reaction?: string;
}

type TabType = 'feed' | 'friends' | 'groups' | 'pages';

// Default admin friend
const DEFAULT_ADMIN_FRIEND = {
  id: 'admin_jjspilot24',
  username: 'JJSPilot24',
  email: 'jjspilot24@gmail.com',
  is_friend: true,
  location: 'InfoPilot HQ',
  protocols_count: 100,
};

// Reaction types with emojis
const REACTIONS = [
  { key: 'like', emoji: '👍', label: 'Like' },
  { key: 'love', emoji: '❤️', label: 'Love' },
  { key: 'funny', emoji: '😂', label: 'Funny' },
  { key: 'sad', emoji: '😢', label: 'Sad' },
  { key: 'caution', emoji: '⚠️', label: 'Caution' },
  { key: 'spam', emoji: '🚫', label: 'Spam' },
  { key: 'best', emoji: '🏆', label: 'Best' },
];

export default function SocialScreen() {
  const router = useRouter();
  const [activeTab, setActiveTab] = useState<TabType>('feed');
  const [loading, setLoading] = useState(false);
  const [refreshing, setRefreshing] = useState(false);
  const [searchQuery, setSearchQuery] = useState('');
  
  // Data states
  const [posts, setPosts] = useState<Post[]>([]);
  const [friends, setFriends] = useState<User[]>([]);
  const [friendRequests, setFriendRequests] = useState<User[]>([]);
  const [searchResults, setSearchResults] = useState<User[]>([]);
  const [groups, setGroups] = useState<Group[]>([]);
  const [pages, setPages] = useState<Page[]>([]);
  
  // Modals
  const [showCreateGroup, setShowCreateGroup] = useState(false);
  const [showCreatePage, setShowCreatePage] = useState(false);
  const [showCreatePost, setShowCreatePost] = useState(false);
  const [showUserSearch, setShowUserSearch] = useState(false);
  const [showReactions, setShowReactions] = useState<string | null>(null);
  
  // Form states
  const [newGroupName, setNewGroupName] = useState('');
  const [newGroupDesc, setNewGroupDesc] = useState('');
  const [newPageName, setNewPageName] = useState('');
  const [newPageDesc, setNewPageDesc] = useState('');
  const [newPageCategory, setNewPageCategory] = useState('');
  const [newPostContent, setNewPostContent] = useState('');

  useEffect(() => {
    loadData();
  }, [activeTab]);

  const loadData = async () => {
    setLoading(true);
    try {
      switch (activeTab) {
        case 'feed':
          await loadFeed();
          break;
        case 'friends':
          await loadFriends();
          break;
        case 'groups':
          await loadGroups();
          break;
        case 'pages':
          await loadPages();
          break;
      }
    } catch (error) {
      console.error('Load data error:', error);
    } finally {
      setLoading(false);
    }
  };

  const loadFeed = async () => {
    try {
      const response = await api.get('/social/feed');
      setPosts(response.posts || []);
    } catch (error) {
      // Use mock data
      setPosts(getMockPosts());
    }
  };

  const loadFriends = async () => {
    try {
      const response = await api.get('/social/friends');
      // Ensure default admin friend is included
      const friendsList = response.friends || [];
      if (!friendsList.find((f: User) => f.username === 'JJSPilot24')) {
        friendsList.unshift(DEFAULT_ADMIN_FRIEND);
      }
      setFriends(friendsList);
      setFriendRequests(response.requests || []);
    } catch (error) {
      setFriends([DEFAULT_ADMIN_FRIEND, ...getMockFriends()]);
      setFriendRequests(getMockFriendRequests());
    }
  };

  const loadGroups = async () => {
    try {
      const response = await api.get('/social/groups');
      setGroups(response.groups || []);
    } catch (error) {
      setGroups(getMockGroups());
    }
  };

  const loadPages = async () => {
    try {
      const response = await api.get('/social/pages');
      setPages(response.pages || []);
    } catch (error) {
      setPages(getMockPages());
    }
  };

  const onRefresh = async () => {
    setRefreshing(true);
    await loadData();
    setRefreshing(false);
  };

  // Mock data generators
  const getMockPosts = (): Post[] => [
    {
      id: '1',
      author: { id: 'admin', username: 'JJSPilot24', profile_photo: undefined },
      content: '🚀 Welcome to InfoPilot Social! Share your protocols, connect with researchers, and discover amazing content! Remember: "The best protocol is the one that finds what you\'re looking for!" 📚',
      images: [],
      reactions: { like: 42, love: 28, funny: 15, sad: 0, caution: 0, spam: 0, best: 12 },
      comments_count: 23,
      created_at: new Date().toISOString(),
      user_reaction: undefined,
    },
    {
      id: '2',
      author: { id: '2', username: 'ProtocolMaster', profile_photo: undefined },
      content: 'Just created a new protocol for American Civil War research! Check out the marketplace - it\'s FREE to copy! 🎯 #InfoPilot #Research #History',
      images: [],
      reactions: { like: 89, love: 34, funny: 5, sad: 0, caution: 0, spam: 0, best: 21 },
      comments_count: 45,
      created_at: new Date(Date.now() - 3600000).toISOString(),
      user_reaction: undefined,
    },
    {
      id: '3',
      author: { id: '3', username: 'ResearchGuru', profile_photo: undefined },
      content: 'Pro tip: Use the AND/OR radio buttons on the Ultimate Search page to combine categories! It\'s like having a superpower for research! 💡',
      images: [],
      reactions: { like: 156, love: 78, funny: 23, sad: 0, caution: 0, spam: 0, best: 45 },
      comments_count: 67,
      created_at: new Date(Date.now() - 7200000).toISOString(),
      user_reaction: undefined,
    },
  ];

  const getMockFriends = (): User[] => [
    { id: '2', username: 'ProtocolMaster', is_friend: true, protocols_count: 45 },
    { id: '3', username: 'ResearchGuru', is_friend: true, protocols_count: 78 },
    { id: '4', username: 'DataWizard', is_friend: true, protocols_count: 32 },
  ];

  const getMockFriendRequests = (): User[] => [
    { id: '5', username: 'NewResearcher', friend_request_received: true, protocols_count: 5 },
  ];

  const getMockGroups = (): Group[] => [
    { id: '1', name: 'History Researchers', description: 'A group for history enthusiasts and researchers', member_count: 1234, is_member: true, is_admin: false, created_at: new Date().toISOString() },
    { id: '2', name: 'Protocol Masters', description: 'Share and discuss the best protocols', member_count: 892, is_member: false, is_admin: false, created_at: new Date().toISOString() },
    { id: '3', name: 'InfoPilot Tips & Tricks', description: 'Learn advanced techniques', member_count: 2156, is_member: true, is_admin: false, created_at: new Date().toISOString() },
  ];

  const getMockPages = (): Page[] => [
    { id: '1', name: 'Letters to Evelyn', description: 'Official page for the book that started it all!', follower_count: 5678, is_following: true, is_owner: false, category: 'Books' },
    { id: '2', name: 'Top Pilot Enterprises', description: 'Official company page', follower_count: 3456, is_following: true, is_owner: false, category: 'Business' },
    { id: '3', name: 'Protocol Academy', description: 'Learn to create amazing protocols', follower_count: 2345, is_following: false, is_owner: false, category: 'Education' },
  ];

  // Friend actions
  const handleSendFriendRequest = async (userId: string) => {
    try {
      await api.post('/social/friends/request', { user_id: userId });
      Alert.alert('Success! 🎉', 'Friend request sent!');
      setSearchResults(prev => prev.map(u => 
        u.id === userId ? { ...u, friend_request_sent: true } : u
      ));
    } catch (error) {
      Alert.alert('Error', 'Failed to send friend request');
    }
  };

  const handleAcceptFriendRequest = async (userId: string) => {
    try {
      await api.post('/social/friends/accept', { user_id: userId });
      Alert.alert('Success! 🤝', 'Friend request accepted!');
      setFriendRequests(prev => prev.filter(u => u.id !== userId));
      loadFriends();
    } catch (error) {
      Alert.alert('Error', 'Failed to accept friend request');
    }
  };

  const handleUnfriend = async (userId: string, username: string) => {
    Alert.alert(
      'Unfriend',
      `Are you sure you want to unfriend @${username}?`,
      [
        { text: 'Cancel', style: 'cancel' },
        {
          text: 'Unfriend',
          style: 'destructive',
          onPress: async () => {
            try {
              await api.post('/social/friends/unfriend', { user_id: userId });
              Alert.alert('Done', `You are no longer friends with @${username}`);
              setFriends(prev => prev.filter(f => f.id !== userId));
            } catch (error) {
              Alert.alert('Error', 'Failed to unfriend');
            }
          },
        },
      ]
    );
  };

  // Search users
  const handleSearchUsers = async () => {
    if (!searchQuery.trim()) return;
    
    try {
      const response = await api.get('/social/users/search', { q: searchQuery });
      setSearchResults(response.users || []);
    } catch (error) {
      // Mock search results
      setSearchResults([
        { id: '10', username: searchQuery + '_user', is_friend: false, protocols_count: 10 },
      ]);
    }
  };

  // Reactions
  const handleReaction = async (postId: string, reactionType: string) => {
    try {
      await api.post(`/social/posts/${postId}/react`, { reaction_type: reactionType });
      setPosts(prev => prev.map(p => {
        if (p.id === postId) {
          const newReactions = { ...p.reactions };
          // Remove old reaction if exists
          if (p.user_reaction) {
            newReactions[p.user_reaction as keyof typeof newReactions]--;
          }
          // Add new reaction
          newReactions[reactionType as keyof typeof newReactions]++;
          return { ...p, reactions: newReactions, user_reaction: reactionType };
        }
        return p;
      }));
    } catch (error) {
      console.error('Reaction error:', error);
    }
    setShowReactions(null);
  };

  // Create post
  const handleCreatePost = async () => {
    if (!newPostContent.trim()) {
      Alert.alert('Error', 'Please write something!');
      return;
    }

    try {
      await api.post('/social/posts', { content: newPostContent });
      Alert.alert('Success! 🎉', 'Your post has been published!');
      setNewPostContent('');
      setShowCreatePost(false);
      loadFeed();
    } catch (error) {
      Alert.alert('Error', 'Failed to create post');
    }
  };

  // Navigate to messages
  const handleOpenMessages = () => {
    router.push('/(tabs)/messages');
  };

  // Render tabs
  const tabs: { key: TabType; label: string; icon: string }[] = [
    { key: 'feed', label: 'Feed', icon: 'newspaper' },
    { key: 'friends', label: 'Friends', icon: 'people' },
    { key: 'groups', label: 'Groups', icon: 'people-circle' },
    { key: 'pages', label: 'Pages', icon: 'flag' },
  ];

  // Render post card
  const renderPost = (post: Post) => (
    <View key={post.id} style={styles.postCard}>
      <View style={styles.postHeader}>
        <View style={styles.postAuthorPhoto}>
          <Ionicons name="person-circle" size={40} color={colors.primary} />
        </View>
        <View style={styles.postAuthorInfo}>
          <Text style={styles.postAuthorName}>@{post.author.username}</Text>
          <Text style={styles.postTime}>
            {new Date(post.created_at).toLocaleDateString()}
          </Text>
        </View>
      </View>
      
      <Text style={styles.postContent}>{post.content}</Text>
      
      {/* Reactions Summary */}
      <View style={styles.reactionsSummary}>
        {Object.entries(post.reactions).filter(([_, count]) => count > 0).slice(0, 4).map(([type, count]) => {
          const reaction = REACTIONS.find(r => r.key === type);
          return reaction ? (
            <Text key={type} style={styles.reactionSummaryItem}>
              {reaction.emoji} {count}
            </Text>
          ) : null;
        })}
        <Text style={styles.commentsCount}>💬 {post.comments_count} comments</Text>
      </View>
      
      {/* Action Buttons */}
      <View style={styles.postActions}>
        <TouchableOpacity 
          style={styles.actionButton}
          onPress={() => setShowReactions(showReactions === post.id ? null : post.id)}
        >
          <Text style={styles.actionButtonText}>
            {post.user_reaction ? REACTIONS.find(r => r.key === post.user_reaction)?.emoji : '👍'} React
          </Text>
        </TouchableOpacity>
        <TouchableOpacity style={styles.actionButton}>
          <Text style={styles.actionButtonText}>💬 Comment</Text>
        </TouchableOpacity>
        <TouchableOpacity style={styles.actionButton}>
          <Text style={styles.actionButtonText}>↗️ Share</Text>
        </TouchableOpacity>
      </View>
      
      {/* Reactions Picker */}
      {showReactions === post.id && (
        <View style={styles.reactionsPicker}>
          {REACTIONS.map(reaction => (
            <TouchableOpacity
              key={reaction.key}
              style={styles.reactionOption}
              onPress={() => handleReaction(post.id, reaction.key)}
            >
              <Text style={styles.reactionEmoji}>{reaction.emoji}</Text>
            </TouchableOpacity>
          ))}
        </View>
      )}
    </View>
  );

  // Render friend card
  const renderFriend = (user: User, isRequest: boolean = false) => (
    <View key={user.id} style={styles.userCard}>
      <View style={styles.userPhoto}>
        <Ionicons name="person-circle" size={48} color={colors.primary} />
      </View>
      <View style={styles.userInfo}>
        <Text style={styles.userName}>@{user.username}</Text>
        <Text style={styles.userStats}>
          {user.protocols_count || 0} protocols
        </Text>
      </View>
      <View style={styles.userActions}>
        {isRequest ? (
          <>
            <TouchableOpacity 
              style={styles.acceptButton}
              onPress={() => handleAcceptFriendRequest(user.id)}
            >
              <Ionicons name="checkmark" size={18} color={colors.white} />
            </TouchableOpacity>
            <TouchableOpacity style={styles.declineButton}>
              <Ionicons name="close" size={18} color={colors.white} />
            </TouchableOpacity>
          </>
        ) : (
          <>
            <TouchableOpacity 
              style={styles.messageButton}
              onPress={handleOpenMessages}
            >
              <Ionicons name="chatbubble" size={18} color={colors.white} />
            </TouchableOpacity>
            <TouchableOpacity 
              style={styles.unfriendButton}
              onPress={() => handleUnfriend(user.id, user.username)}
            >
              <Ionicons name="person-remove" size={18} color={colors.white} />
            </TouchableOpacity>
          </>
        )}
      </View>
    </View>
  );

  // Render group card
  const renderGroup = (group: Group) => (
    <View key={group.id} style={styles.groupCard}>
      <View style={styles.groupIcon}>
        <Ionicons name="people-circle" size={48} color={colors.primary} />
      </View>
      <View style={styles.groupInfo}>
        <Text style={styles.groupName}>{group.name}</Text>
        <Text style={styles.groupDesc} numberOfLines={2}>{group.description}</Text>
        <Text style={styles.groupMembers}>👥 {group.member_count} members</Text>
      </View>
      <TouchableOpacity 
        style={[styles.joinButton, group.is_member && styles.joinedButton]}
      >
        <Text style={styles.joinButtonText}>
          {group.is_member ? 'Joined ✓' : 'Join'}
        </Text>
      </TouchableOpacity>
    </View>
  );

  // Render page card
  const renderPage = (page: Page) => (
    <View key={page.id} style={styles.pageCard}>
      <View style={styles.pageIcon}>
        <Ionicons name="flag" size={48} color={colors.accent} />
      </View>
      <View style={styles.pageInfo}>
        <Text style={styles.pageName}>{page.name}</Text>
        <Text style={styles.pageCategory}>{page.category}</Text>
        <Text style={styles.pageDesc} numberOfLines={2}>{page.description}</Text>
        <Text style={styles.pageFollowers}>❤️ {page.follower_count} followers</Text>
      </View>
      <TouchableOpacity 
        style={[styles.followButton, page.is_following && styles.followingButton]}
      >
        <Text style={styles.followButtonText}>
          {page.is_following ? 'Following ✓' : 'Follow'}
        </Text>
      </TouchableOpacity>
    </View>
  );

  return (
    <SafeAreaView style={styles.container} edges={['bottom']}>
      {/* Header */}
      <View style={styles.header}>
        <Text style={styles.headerTitle}>👥 Social</Text>
        <View style={styles.headerActions}>
          <TouchableOpacity style={styles.headerButton} onPress={handleOpenMessages}>
            <Ionicons name="chatbubbles" size={24} color={colors.primary} />
          </TouchableOpacity>
          <TouchableOpacity style={styles.headerButton} onPress={() => setShowUserSearch(true)}>
            <Ionicons name="person-add" size={24} color={colors.primary} />
          </TouchableOpacity>
        </View>
      </View>

      {/* Tabs */}
      <View style={styles.tabsContainer}>
        {tabs.map(tab => (
          <TouchableOpacity
            key={tab.key}
            style={[styles.tab, activeTab === tab.key && styles.tabActive]}
            onPress={() => setActiveTab(tab.key)}
          >
            <Ionicons 
              name={tab.icon as any} 
              size={20} 
              color={activeTab === tab.key ? colors.white : colors.primary} 
            />
            <Text style={[styles.tabText, activeTab === tab.key && styles.tabTextActive]}>
              {tab.label}
            </Text>
          </TouchableOpacity>
        ))}
      </View>

      {/* Content */}
      <ScrollView 
        style={styles.content}
        contentContainerStyle={styles.contentContainer}
        refreshControl={
          <RefreshControl refreshing={refreshing} onRefresh={onRefresh} tintColor={colors.primary} />
        }
      >
        {loading ? (
          <View style={styles.loadingContainer}>
            <ActivityIndicator size="large" color={colors.primary} />
            <Text style={styles.loadingText}>Loading social goodness... 🌟</Text>
          </View>
        ) : (
          <>
            {/* Feed Tab */}
            {activeTab === 'feed' && (
              <>
                <TouchableOpacity 
                  style={styles.createPostButton}
                  onPress={() => setShowCreatePost(true)}
                >
                  <Ionicons name="create" size={20} color={colors.white} />
                  <Text style={styles.createPostText}>What's on your mind?</Text>
                </TouchableOpacity>
                {posts.map(renderPost)}
              </>
            )}

            {/* Friends Tab */}
            {activeTab === 'friends' && (
              <>
                {friendRequests.length > 0 && (
                  <View style={styles.section}>
                    <Text style={styles.sectionTitle}>📨 Friend Requests</Text>
                    {friendRequests.map(user => renderFriend(user, true))}
                  </View>
                )}
                <View style={styles.section}>
                  <Text style={styles.sectionTitle}>👥 Your Friends ({friends.length})</Text>
                  {friends.length === 0 ? (
                    <Text style={styles.emptyText}>No friends yet. Search for users to connect!</Text>
                  ) : (
                    friends.map(user => renderFriend(user))
                  )}
                </View>
              </>
            )}

            {/* Groups Tab */}
            {activeTab === 'groups' && (
              <>
                <TouchableOpacity 
                  style={styles.createButton}
                  onPress={() => setShowCreateGroup(true)}
                >
                  <Ionicons name="add-circle" size={20} color={colors.white} />
                  <Text style={styles.createButtonText}>Create Group</Text>
                </TouchableOpacity>
                <View style={styles.section}>
                  <Text style={styles.sectionTitle}>🏠 Your Groups</Text>
                  {groups.filter(g => g.is_member).map(renderGroup)}
                </View>
                <View style={styles.section}>
                  <Text style={styles.sectionTitle}>🔍 Discover Groups</Text>
                  {groups.filter(g => !g.is_member).map(renderGroup)}
                </View>
              </>
            )}

            {/* Pages Tab */}
            {activeTab === 'pages' && (
              <>
                <TouchableOpacity 
                  style={styles.createButton}
                  onPress={() => setShowCreatePage(true)}
                >
                  <Ionicons name="add-circle" size={20} color={colors.white} />
                  <Text style={styles.createButtonText}>Create Page</Text>
                </TouchableOpacity>
                <View style={styles.section}>
                  <Text style={styles.sectionTitle}>⭐ Pages You Follow</Text>
                  {pages.filter(p => p.is_following).map(renderPage)}
                </View>
                <View style={styles.section}>
                  <Text style={styles.sectionTitle}>🔍 Discover Pages</Text>
                  {pages.filter(p => !p.is_following).map(renderPage)}
                </View>
              </>
            )}
          </>
        )}
      </ScrollView>

      {/* User Search Modal */}
      <Modal visible={showUserSearch} animationType="slide" presentationStyle="pageSheet">
        <SafeAreaView style={styles.modalContainer}>
          <View style={styles.modalHeader}>
            <Text style={styles.modalTitle}>🔍 Find Friends</Text>
            <TouchableOpacity onPress={() => setShowUserSearch(false)}>
              <Ionicons name="close" size={28} color={colors.text} />
            </TouchableOpacity>
          </View>
          <View style={styles.searchContainer}>
            <TextInput
              style={styles.searchInput}
              placeholder="Search by username..."
              placeholderTextColor={colors.gray}
              value={searchQuery}
              onChangeText={setSearchQuery}
              onSubmitEditing={handleSearchUsers}
            />
            <TouchableOpacity style={styles.searchButton} onPress={handleSearchUsers}>
              <Ionicons name="search" size={20} color={colors.white} />
            </TouchableOpacity>
          </View>
          <ScrollView style={styles.searchResults}>
            {searchResults.map(user => (
              <View key={user.id} style={styles.userCard}>
                <View style={styles.userPhoto}>
                  <Ionicons name="person-circle" size={48} color={colors.primary} />
                </View>
                <View style={styles.userInfo}>
                  <Text style={styles.userName}>@{user.username}</Text>
                  <Text style={styles.userStats}>{user.protocols_count || 0} protocols</Text>
                </View>
                <TouchableOpacity 
                  style={[
                    styles.addFriendButton,
                    (user.is_friend || user.friend_request_sent) && styles.addFriendButtonDisabled
                  ]}
                  onPress={() => handleSendFriendRequest(user.id)}
                  disabled={user.is_friend || user.friend_request_sent}
                >
                  <Text style={styles.addFriendText}>
                    {user.is_friend ? 'Friends ✓' : user.friend_request_sent ? 'Sent ✓' : 'Add Friend'}
                  </Text>
                </TouchableOpacity>
              </View>
            ))}
          </ScrollView>
        </SafeAreaView>
      </Modal>

      {/* Create Post Modal */}
      <Modal visible={showCreatePost} animationType="slide" presentationStyle="pageSheet">
        <SafeAreaView style={styles.modalContainer}>
          <KeyboardAvoidingView behavior={Platform.OS === 'ios' ? 'padding' : 'height'} style={{ flex: 1 }}>
            <View style={styles.modalHeader}>
              <Text style={styles.modalTitle}>✏️ Create Post</Text>
              <TouchableOpacity onPress={() => setShowCreatePost(false)}>
                <Ionicons name="close" size={28} color={colors.text} />
              </TouchableOpacity>
            </View>
            <TextInput
              style={styles.postInput}
              placeholder="What's on your mind? Share your protocol discoveries! 🚀"
              placeholderTextColor={colors.gray}
              multiline
              numberOfLines={6}
              value={newPostContent}
              onChangeText={setNewPostContent}
            />
            <TouchableOpacity style={styles.publishButton} onPress={handleCreatePost}>
              <Text style={styles.publishButtonText}>Publish 🚀</Text>
            </TouchableOpacity>
          </KeyboardAvoidingView>
        </SafeAreaView>
      </Modal>
    </SafeAreaView>
  );
}

const styles = StyleSheet.create({
  container: {
    flex: 1,
    backgroundColor: colors.background,
  },
  header: {
    flexDirection: 'row',
    justifyContent: 'space-between',
    alignItems: 'center',
    padding: 16,
    backgroundColor: colors.cardBackground,
    borderBottomWidth: 1,
    borderBottomColor: colors.cardBorder,
  },
  headerTitle: {
    fontSize: 24,
    fontWeight: 'bold',
    color: colors.text,
  },
  headerActions: {
    flexDirection: 'row',
    gap: 12,
  },
  headerButton: {
    padding: 8,
  },
  tabsContainer: {
    flexDirection: 'row',
    padding: 8,
    backgroundColor: colors.cardBackground,
    borderBottomWidth: 1,
    borderBottomColor: colors.cardBorder,
  },
  tab: {
    flex: 1,
    flexDirection: 'row',
    alignItems: 'center',
    justifyContent: 'center',
    paddingVertical: 10,
    borderRadius: 20,
    gap: 4,
  },
  tabActive: {
    backgroundColor: colors.primary,
  },
  tabText: {
    fontSize: 12,
    fontWeight: '600',
    color: colors.primary,
  },
  tabTextActive: {
    color: colors.white,
  },
  content: {
    flex: 1,
  },
  contentContainer: {
    padding: 12,
    paddingBottom: 40,
  },
  loadingContainer: {
    padding: 40,
    alignItems: 'center',
  },
  loadingText: {
    color: colors.textMuted,
    marginTop: 12,
  },
  // Posts
  createPostButton: {
    flexDirection: 'row',
    alignItems: 'center',
    backgroundColor: colors.primary,
    padding: 16,
    borderRadius: 12,
    marginBottom: 16,
    gap: 8,
  },
  createPostText: {
    color: colors.white,
    fontSize: 14,
    fontWeight: '600',
  },
  postCard: {
    backgroundColor: colors.cardBackground,
    borderRadius: 12,
    padding: 16,
    marginBottom: 12,
  },
  postHeader: {
    flexDirection: 'row',
    marginBottom: 12,
  },
  postAuthorPhoto: {
    marginRight: 12,
  },
  postAuthorInfo: {
    flex: 1,
  },
  postAuthorName: {
    fontSize: 14,
    fontWeight: 'bold',
    color: colors.text,
  },
  postTime: {
    fontSize: 12,
    color: colors.textMuted,
  },
  postContent: {
    fontSize: 14,
    color: colors.text,
    lineHeight: 20,
    marginBottom: 12,
  },
  reactionsSummary: {
    flexDirection: 'row',
    flexWrap: 'wrap',
    gap: 12,
    paddingBottom: 12,
    borderBottomWidth: 1,
    borderBottomColor: colors.cardBorder,
  },
  reactionSummaryItem: {
    fontSize: 13,
    color: colors.textMuted,
  },
  commentsCount: {
    fontSize: 13,
    color: colors.textMuted,
  },
  postActions: {
    flexDirection: 'row',
    justifyContent: 'space-around',
    paddingTop: 12,
  },
  actionButton: {
    padding: 8,
  },
  actionButtonText: {
    fontSize: 13,
    color: colors.primary,
    fontWeight: '600',
  },
  reactionsPicker: {
    flexDirection: 'row',
    justifyContent: 'center',
    paddingTop: 12,
    gap: 8,
    borderTopWidth: 1,
    borderTopColor: colors.cardBorder,
  },
  reactionOption: {
    padding: 8,
    backgroundColor: colors.background,
    borderRadius: 20,
  },
  reactionEmoji: {
    fontSize: 24,
  },
  // Users
  section: {
    marginBottom: 24,
  },
  sectionTitle: {
    fontSize: 16,
    fontWeight: 'bold',
    color: colors.text,
    marginBottom: 12,
  },
  userCard: {
    flexDirection: 'row',
    alignItems: 'center',
    backgroundColor: colors.cardBackground,
    borderRadius: 12,
    padding: 12,
    marginBottom: 8,
  },
  userPhoto: {
    marginRight: 12,
  },
  userInfo: {
    flex: 1,
  },
  userName: {
    fontSize: 14,
    fontWeight: 'bold',
    color: colors.text,
  },
  userStats: {
    fontSize: 12,
    color: colors.textMuted,
  },
  userActions: {
    flexDirection: 'row',
    gap: 8,
  },
  messageButton: {
    backgroundColor: colors.primary,
    padding: 10,
    borderRadius: 20,
  },
  unfriendButton: {
    backgroundColor: colors.error,
    padding: 10,
    borderRadius: 20,
  },
  acceptButton: {
    backgroundColor: colors.success,
    padding: 10,
    borderRadius: 20,
  },
  declineButton: {
    backgroundColor: colors.gray,
    padding: 10,
    borderRadius: 20,
  },
  addFriendButton: {
    backgroundColor: colors.primary,
    paddingHorizontal: 16,
    paddingVertical: 8,
    borderRadius: 20,
  },
  addFriendButtonDisabled: {
    backgroundColor: colors.gray,
  },
  addFriendText: {
    color: colors.white,
    fontSize: 12,
    fontWeight: '600',
  },
  // Groups
  createButton: {
    flexDirection: 'row',
    alignItems: 'center',
    justifyContent: 'center',
    backgroundColor: colors.primary,
    padding: 14,
    borderRadius: 12,
    marginBottom: 16,
    gap: 8,
  },
  createButtonText: {
    color: colors.white,
    fontSize: 14,
    fontWeight: '600',
  },
  groupCard: {
    flexDirection: 'row',
    alignItems: 'center',
    backgroundColor: colors.cardBackground,
    borderRadius: 12,
    padding: 12,
    marginBottom: 8,
  },
  groupIcon: {
    marginRight: 12,
  },
  groupInfo: {
    flex: 1,
  },
  groupName: {
    fontSize: 14,
    fontWeight: 'bold',
    color: colors.text,
  },
  groupDesc: {
    fontSize: 12,
    color: colors.textMuted,
    marginVertical: 4,
  },
  groupMembers: {
    fontSize: 11,
    color: colors.primary,
  },
  joinButton: {
    backgroundColor: colors.primary,
    paddingHorizontal: 16,
    paddingVertical: 8,
    borderRadius: 20,
  },
  joinedButton: {
    backgroundColor: colors.success,
  },
  joinButtonText: {
    color: colors.white,
    fontSize: 12,
    fontWeight: '600',
  },
  // Pages
  pageCard: {
    flexDirection: 'row',
    alignItems: 'center',
    backgroundColor: colors.cardBackground,
    borderRadius: 12,
    padding: 12,
    marginBottom: 8,
  },
  pageIcon: {
    marginRight: 12,
  },
  pageInfo: {
    flex: 1,
  },
  pageName: {
    fontSize: 14,
    fontWeight: 'bold',
    color: colors.text,
  },
  pageCategory: {
    fontSize: 10,
    color: colors.accent,
    fontWeight: '600',
  },
  pageDesc: {
    fontSize: 12,
    color: colors.textMuted,
    marginVertical: 4,
  },
  pageFollowers: {
    fontSize: 11,
    color: colors.primary,
  },
  followButton: {
    backgroundColor: colors.accent,
    paddingHorizontal: 16,
    paddingVertical: 8,
    borderRadius: 20,
  },
  followingButton: {
    backgroundColor: colors.success,
  },
  followButtonText: {
    color: colors.white,
    fontSize: 12,
    fontWeight: '600',
  },
  // Modals
  modalContainer: {
    flex: 1,
    backgroundColor: colors.background,
  },
  modalHeader: {
    flexDirection: 'row',
    justifyContent: 'space-between',
    alignItems: 'center',
    padding: 16,
    borderBottomWidth: 1,
    borderBottomColor: colors.cardBorder,
  },
  modalTitle: {
    fontSize: 20,
    fontWeight: 'bold',
    color: colors.text,
  },
  searchContainer: {
    flexDirection: 'row',
    padding: 16,
    gap: 8,
  },
  searchInput: {
    flex: 1,
    backgroundColor: colors.cardBackground,
    borderRadius: 12,
    padding: 12,
    fontSize: 14,
    color: colors.text,
    borderWidth: 1,
    borderColor: colors.cardBorder,
  },
  searchButton: {
    backgroundColor: colors.primary,
    padding: 12,
    borderRadius: 12,
  },
  searchResults: {
    flex: 1,
    padding: 16,
  },
  postInput: {
    flex: 1,
    backgroundColor: colors.cardBackground,
    margin: 16,
    padding: 16,
    borderRadius: 12,
    fontSize: 16,
    color: colors.text,
    textAlignVertical: 'top',
  },
  publishButton: {
    backgroundColor: colors.primary,
    margin: 16,
    padding: 16,
    borderRadius: 12,
    alignItems: 'center',
  },
  publishButtonText: {
    color: colors.white,
    fontSize: 16,
    fontWeight: 'bold',
  },
  emptyText: {
    color: colors.textMuted,
    fontSize: 14,
    textAlign: 'center',
    padding: 20,
  },
});
