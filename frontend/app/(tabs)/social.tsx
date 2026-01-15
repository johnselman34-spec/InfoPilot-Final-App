import React, { useState, useEffect } from 'react';
import {
  View,
  Text,
  StyleSheet,
  ScrollView,
  TouchableOpacity,
  TextInput,
  Alert,
  ActivityIndicator,
  FlatList,
  Image,
  Modal,
  KeyboardAvoidingView,
  Platform,
} from 'react-native';
import { SafeAreaView } from 'react-native-safe-area-context';
import { Ionicons } from '@expo/vector-icons';
import { colors } from '../../src/utils/colors';
import { api } from '../../src/services/api';

interface User {
  id: string;
  username: string;
  email?: string;
  profile_photo?: string;
  is_friend?: boolean;
  friend_request_sent?: boolean;
  location?: string;
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

interface FeedPost {
  id: string;
  author: User;
  content: string;
  images?: string[];
  likes: number;
  comments: number;
  shares: number;
  created_at: string;
  is_liked: boolean;
}

type TabType = 'feed' | 'friends' | 'groups' | 'pages';

export default function SocialScreen() {
  const [activeTab, setActiveTab] = useState<TabType>('feed');
  const [loading, setLoading] = useState(false);
  const [searchQuery, setSearchQuery] = useState('');
  
  // Data states
  const [feedPosts, setFeedPosts] = useState<FeedPost[]>([]);
  const [friends, setFriends] = useState<User[]>([]);
  const [friendRequests, setFriendRequests] = useState<User[]>([]);
  const [searchResults, setSearchResults] = useState<User[]>([]);
  const [groups, setGroups] = useState<Group[]>([]);
  const [pages, setPages] = useState<Page[]>([]);
  
  // Modals
  const [showCreateGroup, setShowCreateGroup] = useState(false);
  const [showCreatePage, setShowCreatePage] = useState(false);
  const [showUserSearch, setShowUserSearch] = useState(false);
  
  // Create form states
  const [newGroupName, setNewGroupName] = useState('');
  const [newGroupDesc, setNewGroupDesc] = useState('');
  const [newPageName, setNewPageName] = useState('');
  const [newPageDesc, setNewPageDesc] = useState('');
  const [newPageCategory, setNewPageCategory] = useState('');

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
    // Demo feed data
    setFeedPosts([
      {
        id: '1',
        author: { id: 'u1', username: 'SearchMaster42', profile_photo: 'https://i.pravatar.cc/150?img=1' },
        content: "🔥 Just created an AMAZING protocol for finding historical documents! Check out my marketplace listing - it's got everything from ancient manuscripts to modern declassified documents! #InfoPilot #SearchPro",
        likes: 42,
        comments: 8,
        shares: 5,
        created_at: '2 hours ago',
        is_liked: false,
      },
      {
        id: '2',
        author: { id: 'u2', username: 'DataNinja', profile_photo: 'https://i.pravatar.cc/150?img=2' },
        content: "Finally finished reading 'Letters to Evelyn' by John Selman! 📚 Such an inspiring book about the journey of creating InfoPilot. If you haven't read it yet, you're missing out! Available on Amazon - go grab a copy! 💫",
        likes: 156,
        comments: 23,
        shares: 45,
        created_at: '5 hours ago',
        is_liked: true,
      },
      {
        id: '3',
        author: { id: 'u3', username: 'ProtocolPro', profile_photo: 'https://i.pravatar.cc/150?img=3' },
        content: "Pro tip: Use the (term1 or term2) & (term3)+ format for the BEST search results! The + modifier means 'prioritize these results' - game changer! 🎮",
        likes: 89,
        comments: 12,
        shares: 34,
        created_at: '1 day ago',
        is_liked: false,
      },
    ]);
  };

  const loadFriends = async () => {
    try {
      const response = await api.get('/social/friends');
      setFriends(response.friends || []);
      setFriendRequests(response.pending_requests || []);
    } catch (error) {
      // Demo data
      setFriends([
        { id: 'f1', username: 'JohnSearcher', profile_photo: 'https://i.pravatar.cc/150?img=4', location: 'New York, USA' },
        { id: 'f2', username: 'SarahResearch', profile_photo: 'https://i.pravatar.cc/150?img=5', location: 'London, UK' },
        { id: 'f3', username: 'MikeProtocol', profile_photo: 'https://i.pravatar.cc/150?img=6', location: 'Tokyo, Japan' },
      ]);
      setFriendRequests([
        { id: 'r1', username: 'NewUser123', profile_photo: 'https://i.pravatar.cc/150?img=7' },
      ]);
    }
  };

  const loadGroups = async () => {
    try {
      const response = await api.get('/social/groups');
      setGroups(response.groups || []);
    } catch (error) {
      // Demo data
      setGroups([
        { id: 'g1', name: 'History Protocol Masters', description: 'Share and discuss historical research protocols', member_count: 1234, is_member: true, is_admin: false, created_at: '2024-01-15' },
        { id: 'g2', name: 'Science Search Pros', description: 'For those who love finding scientific papers', member_count: 892, is_member: false, is_admin: false, created_at: '2024-02-20' },
        { id: 'g3', name: 'Business Intel Hub', description: 'Competitive intelligence and market research', member_count: 567, is_member: true, is_admin: true, created_at: '2024-03-10' },
      ]);
    }
  };

  const loadPages = async () => {
    try {
      const response = await api.get('/social/pages');
      setPages(response.pages || []);
    } catch (error) {
      // Demo data
      setPages([
        { id: 'p1', name: 'InfoPilot Official', description: 'Official page for InfoPilot updates and news', follower_count: 5432, is_following: true, is_owner: false, category: 'Technology' },
        { id: 'p2', name: 'Letters to Evelyn Fan Page', description: 'For fans of John Selman\'s amazing book!', follower_count: 2341, is_following: true, is_owner: false, category: 'Books' },
        { id: 'p3', name: 'Protocol Marketplace Tips', description: 'Tips for selling protocols and making money!', follower_count: 1876, is_following: false, is_owner: false, category: 'Business' },
      ]);
    }
  };

  const handleSearchUsers = async () => {
    if (!searchQuery.trim()) return;
    
    setLoading(true);
    try {
      const response = await api.get('/social/search-users', { query: searchQuery });
      setSearchResults(response.users || []);
    } catch (error) {
      // Demo search results
      setSearchResults([
        { id: 's1', username: searchQuery + '_user', profile_photo: 'https://i.pravatar.cc/150?img=10', location: 'Chicago, USA', is_friend: false },
        { id: 's2', username: searchQuery + '_pro', profile_photo: 'https://i.pravatar.cc/150?img=11', location: 'Berlin, Germany', is_friend: false },
      ]);
    } finally {
      setLoading(false);
    }
  };

  const handleSendFriendRequest = async (userId: string) => {
    try {
      await api.post('/social/friend-request', { user_id: userId });
      Alert.alert('🎉 Friend Request Sent!', 'They\'ll be notified. Fingers crossed! 🤞');
      setSearchResults(prev => prev.map(u => 
        u.id === userId ? { ...u, friend_request_sent: true } : u
      ));
    } catch (error) {
      Alert.alert('Oops!', 'Couldn\'t send friend request. Try again!');
    }
  };

  const handleAcceptFriendRequest = async (userId: string) => {
    try {
      await api.post('/social/accept-friend', { user_id: userId });
      Alert.alert('🎊 New Friend!', 'You\'re now connected!');
      setFriendRequests(prev => prev.filter(u => u.id !== userId));
      loadFriends();
    } catch (error) {
      Alert.alert('Oops!', 'Something went wrong.');
    }
  };

  const handleUnfriend = async (userId: string, username: string) => {
    Alert.alert(
      '😢 Unfriend?',
      `Are you sure you want to unfriend ${username}? This is like unfollowing but WORSE!`,
      [
        { text: 'Nope, keep them!', style: 'cancel' },
        { 
          text: 'Yes, unfriend', 
          style: 'destructive',
          onPress: async () => {
            try {
              await api.delete(`/social/friends/${userId}`);
              setFriends(prev => prev.filter(f => f.id !== userId));
            } catch (error) {
              console.error('Unfriend error:', error);
            }
          }
        },
      ]
    );
  };

  const handleJoinGroup = async (groupId: string) => {
    try {
      await api.post(`/social/groups/${groupId}/join`);
      setGroups(prev => prev.map(g => 
        g.id === groupId ? { ...g, is_member: true, member_count: g.member_count + 1 } : g
      ));
      Alert.alert('🎉 Welcome!', 'You\'re now a member of this group!');
    } catch (error) {
      Alert.alert('Oops!', 'Couldn\'t join the group.');
    }
  };

  const handleLeaveGroup = async (groupId: string) => {
    try {
      await api.post(`/social/groups/${groupId}/leave`);
      setGroups(prev => prev.map(g => 
        g.id === groupId ? { ...g, is_member: false, member_count: g.member_count - 1 } : g
      ));
    } catch (error) {
      console.error('Leave group error:', error);
    }
  };

  const handleFollowPage = async (pageId: string) => {
    try {
      await api.post(`/social/pages/${pageId}/follow`);
      setPages(prev => prev.map(p => 
        p.id === pageId ? { ...p, is_following: true, follower_count: p.follower_count + 1 } : p
      ));
    } catch (error) {
      console.error('Follow page error:', error);
    }
  };

  const handleLikePost = async (postId: string) => {
    setFeedPosts(prev => prev.map(p => 
      p.id === postId ? { ...p, is_liked: !p.is_liked, likes: p.is_liked ? p.likes - 1 : p.likes + 1 } : p
    ));
    try {
      await api.post(`/social/posts/${postId}/like`);
    } catch (error) {
      console.error('Like error:', error);
    }
  };

  const handleCreateGroup = async () => {
    if (!newGroupName.trim()) {
      Alert.alert('Oops!', 'Please enter a group name');
      return;
    }
    
    try {
      await api.post('/social/groups', {
        name: newGroupName,
        description: newGroupDesc,
      });
      Alert.alert('🎉 Group Created!', 'Your group is now live!');
      setShowCreateGroup(false);
      setNewGroupName('');
      setNewGroupDesc('');
      loadGroups();
    } catch (error) {
      Alert.alert('Oops!', 'Couldn\'t create the group.');
    }
  };

  const handleCreatePage = async () => {
    if (!newPageName.trim()) {
      Alert.alert('Oops!', 'Please enter a page name');
      return;
    }
    
    try {
      await api.post('/social/pages', {
        name: newPageName,
        description: newPageDesc,
        category: newPageCategory || 'General',
      });
      Alert.alert('🎉 Page Created!', 'Your page is now live!');
      setShowCreatePage(false);
      setNewPageName('');
      setNewPageDesc('');
      setNewPageCategory('');
      loadPages();
    } catch (error) {
      Alert.alert('Oops!', 'Couldn\'t create the page.');
    }
  };

  const renderFeedPost = ({ item }: { item: FeedPost }) => (
    <View style={styles.postCard}>
      <View style={styles.postHeader}>
        <Image 
          source={{ uri: item.author.profile_photo || 'https://i.pravatar.cc/150' }}
          style={styles.authorAvatar}
        />
        <View>
          <Text style={styles.authorName}>{item.author.username}</Text>
          <Text style={styles.postTime}>{item.created_at}</Text>
        </View>
      </View>
      
      <Text style={styles.postContent}>{item.content}</Text>
      
      <View style={styles.postActions}>
        <TouchableOpacity 
          style={styles.postAction}
          onPress={() => handleLikePost(item.id)}
        >
          <Ionicons 
            name={item.is_liked ? "heart" : "heart-outline"} 
            size={20} 
            color={item.is_liked ? colors.love : colors.textMuted} 
          />
          <Text style={styles.actionCount}>{item.likes}</Text>
        </TouchableOpacity>
        
        <TouchableOpacity style={styles.postAction}>
          <Ionicons name="chatbubble-outline" size={20} color={colors.textMuted} />
          <Text style={styles.actionCount}>{item.comments}</Text>
        </TouchableOpacity>
        
        <TouchableOpacity style={styles.postAction}>
          <Ionicons name="share-outline" size={20} color={colors.textMuted} />
          <Text style={styles.actionCount}>{item.shares}</Text>
        </TouchableOpacity>
      </View>
    </View>
  );

  const renderFriendItem = ({ item }: { item: User }) => (
    <View style={styles.friendCard}>
      <Image 
        source={{ uri: item.profile_photo || 'https://i.pravatar.cc/150' }}
        style={styles.friendAvatar}
      />
      <View style={styles.friendInfo}>
        <Text style={styles.friendName}>{item.username}</Text>
        {item.location && <Text style={styles.friendLocation}>📍 {item.location}</Text>}
      </View>
      <View style={styles.friendActions}>
        <TouchableOpacity 
          style={styles.messageButton}
          onPress={() => Alert.alert('💬 Coming Soon!', 'Direct messaging is being developed!')}
        >
          <Ionicons name="chatbubble" size={18} color={colors.primary} />
        </TouchableOpacity>
        <TouchableOpacity 
          style={styles.unfriendButton}
          onPress={() => handleUnfriend(item.id, item.username)}
        >
          <Ionicons name="person-remove" size={18} color={colors.error} />
        </TouchableOpacity>
      </View>
    </View>
  );

  const renderGroupItem = ({ item }: { item: Group }) => (
    <View style={styles.groupCard}>
      <View style={styles.groupHeader}>
        <Text style={styles.groupName}>{item.name}</Text>
        {item.is_admin && (
          <View style={styles.adminBadge}>
            <Text style={styles.adminBadgeText}>Admin</Text>
          </View>
        )}
      </View>
      <Text style={styles.groupDescription} numberOfLines={2}>{item.description}</Text>
      <View style={styles.groupFooter}>
        <Text style={styles.memberCount}>👥 {item.member_count} members</Text>
        {item.is_member ? (
          <TouchableOpacity 
            style={styles.leaveButton}
            onPress={() => handleLeaveGroup(item.id)}
          >
            <Text style={styles.leaveButtonText}>Leave</Text>
          </TouchableOpacity>
        ) : (
          <TouchableOpacity 
            style={styles.joinButton}
            onPress={() => handleJoinGroup(item.id)}
          >
            <Text style={styles.joinButtonText}>Join</Text>
          </TouchableOpacity>
        )}
      </View>
    </View>
  );

  const renderPageItem = ({ item }: { item: Page }) => (
    <View style={styles.pageCard}>
      <View style={styles.pageHeader}>
        <Text style={styles.pageName}>{item.name}</Text>
        <View style={styles.categoryBadge}>
          <Text style={styles.categoryBadgeText}>{item.category}</Text>
        </View>
      </View>
      <Text style={styles.pageDescription} numberOfLines={2}>{item.description}</Text>
      <View style={styles.pageFooter}>
        <Text style={styles.followerCount}>❤️ {item.follower_count} followers</Text>
        <TouchableOpacity 
          style={[styles.followButton, item.is_following && styles.followingButton]}
          onPress={() => handleFollowPage(item.id)}
        >
          <Text style={[styles.followButtonText, item.is_following && styles.followingButtonText]}>
            {item.is_following ? 'Following' : 'Follow'}
          </Text>
        </TouchableOpacity>
      </View>
    </View>
  );

  return (
    <SafeAreaView style={styles.container} edges={['bottom']}>
      {/* Header */}
      <View style={styles.header}>
        <Text style={styles.headerTitle}>🌐 Social Hub</Text>
        <Text style={styles.headerSubtitle}>
          "Making connections that matter!" 🤝
        </Text>
      </View>

      {/* Tabs */}
      <View style={styles.tabBar}>
        {(['feed', 'friends', 'groups', 'pages'] as TabType[]).map(tab => (
          <TouchableOpacity
            key={tab}
            style={[styles.tab, activeTab === tab && styles.tabActive]}
            onPress={() => setActiveTab(tab)}
          >
            <Ionicons 
              name={
                tab === 'feed' ? 'newspaper' :
                tab === 'friends' ? 'people' :
                tab === 'groups' ? 'person-add' :
                'flag'
              }
              size={18}
              color={activeTab === tab ? colors.white : colors.primary}
            />
            <Text style={[styles.tabText, activeTab === tab && styles.tabTextActive]}>
              {tab.charAt(0).toUpperCase() + tab.slice(1)}
            </Text>
          </TouchableOpacity>
        ))}
      </View>

      {/* Content */}
      {loading ? (
        <View style={styles.loadingContainer}>
          <ActivityIndicator size="large" color={colors.primary} />
          <Text style={styles.loadingText}>Loading awesome stuff... 🚀</Text>
        </View>
      ) : (
        <>
          {activeTab === 'feed' && (
            <FlatList
              data={feedPosts}
              renderItem={renderFeedPost}
              keyExtractor={(item) => item.id}
              contentContainerStyle={styles.listContent}
              showsVerticalScrollIndicator={false}
            />
          )}

          {activeTab === 'friends' && (
            <View style={styles.friendsContainer}>
              {/* Find Friends Button */}
              <TouchableOpacity 
                style={styles.findFriendsButton}
                onPress={() => setShowUserSearch(true)}
              >
                <Ionicons name="search" size={20} color={colors.white} />
                <Text style={styles.findFriendsText}>Find New Friends</Text>
              </TouchableOpacity>

              {/* Friend Requests */}
              {friendRequests.length > 0 && (
                <>
                  <Text style={styles.sectionTitle}>📬 Friend Requests ({friendRequests.length})</Text>
                  {friendRequests.map(req => (
                    <View key={req.id} style={styles.requestCard}>
                      <Image 
                        source={{ uri: req.profile_photo || 'https://i.pravatar.cc/150' }}
                        style={styles.friendAvatar}
                      />
                      <Text style={styles.friendName}>{req.username}</Text>
                      <TouchableOpacity 
                        style={styles.acceptButton}
                        onPress={() => handleAcceptFriendRequest(req.id)}
                      >
                        <Text style={styles.acceptButtonText}>Accept</Text>
                      </TouchableOpacity>
                    </View>
                  ))}
                </>
              )}

              {/* Friends List */}
              <Text style={styles.sectionTitle}>👥 My Friends ({friends.length})</Text>
              <FlatList
                data={friends}
                renderItem={renderFriendItem}
                keyExtractor={(item) => item.id}
                showsVerticalScrollIndicator={false}
              />
            </View>
          )}

          {activeTab === 'groups' && (
            <View style={styles.groupsContainer}>
              <TouchableOpacity 
                style={styles.createButton}
                onPress={() => setShowCreateGroup(true)}
              >
                <Ionicons name="add-circle" size={20} color={colors.white} />
                <Text style={styles.createButtonText}>Create Group</Text>
              </TouchableOpacity>
              
              <FlatList
                data={groups}
                renderItem={renderGroupItem}
                keyExtractor={(item) => item.id}
                contentContainerStyle={styles.listContent}
                showsVerticalScrollIndicator={false}
              />
            </View>
          )}

          {activeTab === 'pages' && (
            <View style={styles.pagesContainer}>
              <TouchableOpacity 
                style={styles.createButton}
                onPress={() => setShowCreatePage(true)}
              >
                <Ionicons name="add-circle" size={20} color={colors.white} />
                <Text style={styles.createButtonText}>Create Page</Text>
              </TouchableOpacity>
              
              <FlatList
                data={pages}
                renderItem={renderPageItem}
                keyExtractor={(item) => item.id}
                contentContainerStyle={styles.listContent}
                showsVerticalScrollIndicator={false}
              />
            </View>
          )}
        </>
      )}

      {/* User Search Modal */}
      <Modal visible={showUserSearch} animationType="slide" transparent>
        <View style={styles.modalOverlay}>
          <View style={styles.modalContent}>
            <View style={styles.modalHeader}>
              <Text style={styles.modalTitle}>🔍 Find Friends</Text>
              <TouchableOpacity onPress={() => setShowUserSearch(false)}>
                <Ionicons name="close" size={24} color={colors.text} />
              </TouchableOpacity>
            </View>
            
            <View style={styles.searchBar}>
              <TextInput
                style={styles.searchInput}
                placeholder="Search by name or location..."
                placeholderTextColor={colors.gray}
                value={searchQuery}
                onChangeText={setSearchQuery}
                onSubmitEditing={handleSearchUsers}
              />
              <TouchableOpacity onPress={handleSearchUsers}>
                <Ionicons name="search" size={20} color={colors.primary} />
              </TouchableOpacity>
            </View>
            
            <FlatList
              data={searchResults}
              keyExtractor={(item) => item.id}
              renderItem={({ item }) => (
                <View style={styles.searchResultCard}>
                  <Image 
                    source={{ uri: item.profile_photo || 'https://i.pravatar.cc/150' }}
                    style={styles.friendAvatar}
                  />
                  <View style={styles.friendInfo}>
                    <Text style={styles.friendName}>{item.username}</Text>
                    {item.location && <Text style={styles.friendLocation}>📍 {item.location}</Text>}
                  </View>
                  {item.friend_request_sent ? (
                    <Text style={styles.requestSentText}>Request Sent ✓</Text>
                  ) : (
                    <TouchableOpacity 
                      style={styles.addFriendButton}
                      onPress={() => handleSendFriendRequest(item.id)}
                    >
                      <Ionicons name="person-add" size={18} color={colors.white} />
                    </TouchableOpacity>
                  )}
                </View>
              )}
              ListEmptyComponent={
                <Text style={styles.emptySearchText}>
                  Search for users by name or location to find new friends! 🔎
                </Text>
              }
            />
          </View>
        </View>
      </Modal>

      {/* Create Group Modal */}
      <Modal visible={showCreateGroup} animationType="slide" transparent>
        <KeyboardAvoidingView 
          behavior={Platform.OS === 'ios' ? 'padding' : 'height'}
          style={styles.modalOverlay}
        >
          <View style={styles.modalContent}>
            <View style={styles.modalHeader}>
              <Text style={styles.modalTitle}>👥 Create Group</Text>
              <TouchableOpacity onPress={() => setShowCreateGroup(false)}>
                <Ionicons name="close" size={24} color={colors.text} />
              </TouchableOpacity>
            </View>
            
            <TextInput
              style={styles.modalInput}
              placeholder="Group Name"
              placeholderTextColor={colors.gray}
              value={newGroupName}
              onChangeText={setNewGroupName}
            />
            <TextInput
              style={[styles.modalInput, styles.textArea]}
              placeholder="Description"
              placeholderTextColor={colors.gray}
              value={newGroupDesc}
              onChangeText={setNewGroupDesc}
              multiline
            />
            
            <TouchableOpacity style={styles.submitButton} onPress={handleCreateGroup}>
              <Text style={styles.submitButtonText}>Create Group 🚀</Text>
            </TouchableOpacity>
          </View>
        </KeyboardAvoidingView>
      </Modal>

      {/* Create Page Modal */}
      <Modal visible={showCreatePage} animationType="slide" transparent>
        <KeyboardAvoidingView 
          behavior={Platform.OS === 'ios' ? 'padding' : 'height'}
          style={styles.modalOverlay}
        >
          <View style={styles.modalContent}>
            <View style={styles.modalHeader}>
              <Text style={styles.modalTitle}>📄 Create Page</Text>
              <TouchableOpacity onPress={() => setShowCreatePage(false)}>
                <Ionicons name="close" size={24} color={colors.text} />
              </TouchableOpacity>
            </View>
            
            <TextInput
              style={styles.modalInput}
              placeholder="Page Name"
              placeholderTextColor={colors.gray}
              value={newPageName}
              onChangeText={setNewPageName}
            />
            <TextInput
              style={[styles.modalInput, styles.textArea]}
              placeholder="Description"
              placeholderTextColor={colors.gray}
              value={newPageDesc}
              onChangeText={setNewPageDesc}
              multiline
            />
            <TextInput
              style={styles.modalInput}
              placeholder="Category (e.g., Technology, Books)"
              placeholderTextColor={colors.gray}
              value={newPageCategory}
              onChangeText={setNewPageCategory}
            />
            
            <TouchableOpacity style={styles.submitButton} onPress={handleCreatePage}>
              <Text style={styles.submitButtonText}>Create Page 🚀</Text>
            </TouchableOpacity>
          </View>
        </KeyboardAvoidingView>
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
  headerSubtitle: {
    fontSize: 12,
    color: colors.textMuted,
    textAlign: 'center',
    marginTop: 4,
  },
  tabBar: {
    flexDirection: 'row',
    padding: 12,
    gap: 8,
  },
  tab: {
    flex: 1,
    flexDirection: 'row',
    alignItems: 'center',
    justifyContent: 'center',
    paddingVertical: 10,
    borderRadius: 12,
    backgroundColor: colors.cardBackground,
    borderWidth: 1,
    borderColor: colors.cardBorder,
    gap: 4,
  },
  tabActive: {
    backgroundColor: colors.primary,
    borderColor: colors.primary,
  },
  tabText: {
    color: colors.primary,
    fontSize: 11,
    fontWeight: '600',
  },
  tabTextActive: {
    color: colors.white,
  },
  loadingContainer: {
    flex: 1,
    justifyContent: 'center',
    alignItems: 'center',
  },
  loadingText: {
    color: colors.text,
    marginTop: 16,
    fontSize: 16,
  },
  listContent: {
    padding: 12,
  },
  postCard: {
    backgroundColor: colors.cardBackground,
    borderRadius: 12,
    padding: 16,
    marginBottom: 12,
    borderWidth: 1,
    borderColor: colors.cardBorder,
  },
  postHeader: {
    flexDirection: 'row',
    alignItems: 'center',
    marginBottom: 12,
  },
  authorAvatar: {
    width: 40,
    height: 40,
    borderRadius: 20,
    marginRight: 12,
  },
  authorName: {
    color: colors.text,
    fontWeight: 'bold',
    fontSize: 14,
  },
  postTime: {
    color: colors.textMuted,
    fontSize: 12,
  },
  postContent: {
    color: colors.text,
    fontSize: 14,
    lineHeight: 20,
    marginBottom: 12,
  },
  postActions: {
    flexDirection: 'row',
    borderTopWidth: 1,
    borderTopColor: colors.cardBorder,
    paddingTop: 12,
    gap: 24,
  },
  postAction: {
    flexDirection: 'row',
    alignItems: 'center',
    gap: 6,
  },
  actionCount: {
    color: colors.textMuted,
    fontSize: 12,
  },
  friendsContainer: {
    flex: 1,
    padding: 12,
  },
  findFriendsButton: {
    flexDirection: 'row',
    alignItems: 'center',
    justifyContent: 'center',
    backgroundColor: colors.primary,
    paddingVertical: 12,
    borderRadius: 12,
    gap: 8,
    marginBottom: 16,
  },
  findFriendsText: {
    color: colors.white,
    fontWeight: 'bold',
  },
  sectionTitle: {
    color: colors.text,
    fontSize: 16,
    fontWeight: 'bold',
    marginBottom: 12,
    marginTop: 8,
  },
  friendCard: {
    flexDirection: 'row',
    alignItems: 'center',
    backgroundColor: colors.cardBackground,
    padding: 12,
    borderRadius: 12,
    marginBottom: 8,
  },
  friendAvatar: {
    width: 50,
    height: 50,
    borderRadius: 25,
    marginRight: 12,
  },
  friendInfo: {
    flex: 1,
  },
  friendName: {
    color: colors.text,
    fontWeight: 'bold',
    fontSize: 14,
  },
  friendLocation: {
    color: colors.textMuted,
    fontSize: 12,
    marginTop: 2,
  },
  friendActions: {
    flexDirection: 'row',
    gap: 8,
  },
  messageButton: {
    padding: 8,
    backgroundColor: colors.cardBackground,
    borderRadius: 8,
    borderWidth: 1,
    borderColor: colors.primary,
  },
  unfriendButton: {
    padding: 8,
    backgroundColor: colors.cardBackground,
    borderRadius: 8,
    borderWidth: 1,
    borderColor: colors.error,
  },
  requestCard: {
    flexDirection: 'row',
    alignItems: 'center',
    backgroundColor: colors.cardBackground,
    padding: 12,
    borderRadius: 12,
    marginBottom: 8,
    borderWidth: 1,
    borderColor: colors.primary,
  },
  acceptButton: {
    backgroundColor: colors.success,
    paddingHorizontal: 16,
    paddingVertical: 8,
    borderRadius: 8,
    marginLeft: 'auto',
  },
  acceptButtonText: {
    color: colors.white,
    fontWeight: 'bold',
    fontSize: 12,
  },
  groupsContainer: {
    flex: 1,
    padding: 12,
  },
  pagesContainer: {
    flex: 1,
    padding: 12,
  },
  createButton: {
    flexDirection: 'row',
    alignItems: 'center',
    justifyContent: 'center',
    backgroundColor: colors.primary,
    paddingVertical: 12,
    borderRadius: 12,
    gap: 8,
    marginBottom: 16,
  },
  createButtonText: {
    color: colors.white,
    fontWeight: 'bold',
  },
  groupCard: {
    backgroundColor: colors.cardBackground,
    borderRadius: 12,
    padding: 16,
    marginBottom: 12,
    borderWidth: 1,
    borderColor: colors.cardBorder,
  },
  groupHeader: {
    flexDirection: 'row',
    alignItems: 'center',
    marginBottom: 8,
  },
  groupName: {
    color: colors.text,
    fontWeight: 'bold',
    fontSize: 16,
    flex: 1,
  },
  adminBadge: {
    backgroundColor: colors.marketplaceGold,
    paddingHorizontal: 8,
    paddingVertical: 2,
    borderRadius: 8,
  },
  adminBadgeText: {
    color: colors.background,
    fontSize: 10,
    fontWeight: 'bold',
  },
  groupDescription: {
    color: colors.textLight,
    fontSize: 13,
    marginBottom: 12,
  },
  groupFooter: {
    flexDirection: 'row',
    alignItems: 'center',
    justifyContent: 'space-between',
  },
  memberCount: {
    color: colors.textMuted,
    fontSize: 12,
  },
  joinButton: {
    backgroundColor: colors.primary,
    paddingHorizontal: 16,
    paddingVertical: 8,
    borderRadius: 8,
  },
  joinButtonText: {
    color: colors.white,
    fontWeight: 'bold',
    fontSize: 12,
  },
  leaveButton: {
    backgroundColor: 'transparent',
    paddingHorizontal: 16,
    paddingVertical: 8,
    borderRadius: 8,
    borderWidth: 1,
    borderColor: colors.error,
  },
  leaveButtonText: {
    color: colors.error,
    fontWeight: 'bold',
    fontSize: 12,
  },
  pageCard: {
    backgroundColor: colors.cardBackground,
    borderRadius: 12,
    padding: 16,
    marginBottom: 12,
    borderWidth: 1,
    borderColor: colors.cardBorder,
  },
  pageHeader: {
    flexDirection: 'row',
    alignItems: 'center',
    marginBottom: 8,
  },
  pageName: {
    color: colors.text,
    fontWeight: 'bold',
    fontSize: 16,
    flex: 1,
  },
  categoryBadge: {
    backgroundColor: colors.secondary,
    paddingHorizontal: 8,
    paddingVertical: 2,
    borderRadius: 8,
  },
  categoryBadgeText: {
    color: colors.white,
    fontSize: 10,
    fontWeight: 'bold',
  },
  pageDescription: {
    color: colors.textLight,
    fontSize: 13,
    marginBottom: 12,
  },
  pageFooter: {
    flexDirection: 'row',
    alignItems: 'center',
    justifyContent: 'space-between',
  },
  followerCount: {
    color: colors.textMuted,
    fontSize: 12,
  },
  followButton: {
    backgroundColor: colors.primary,
    paddingHorizontal: 16,
    paddingVertical: 8,
    borderRadius: 8,
  },
  followingButton: {
    backgroundColor: 'transparent',
    borderWidth: 1,
    borderColor: colors.primary,
  },
  followButtonText: {
    color: colors.white,
    fontWeight: 'bold',
    fontSize: 12,
  },
  followingButtonText: {
    color: colors.primary,
  },
  modalOverlay: {
    flex: 1,
    backgroundColor: 'rgba(0,0,0,0.7)',
    justifyContent: 'flex-end',
  },
  modalContent: {
    backgroundColor: colors.cardBackground,
    borderTopLeftRadius: 20,
    borderTopRightRadius: 20,
    padding: 20,
    maxHeight: '80%',
  },
  modalHeader: {
    flexDirection: 'row',
    alignItems: 'center',
    justifyContent: 'space-between',
    marginBottom: 20,
  },
  modalTitle: {
    color: colors.text,
    fontSize: 20,
    fontWeight: 'bold',
  },
  searchBar: {
    flexDirection: 'row',
    alignItems: 'center',
    backgroundColor: colors.background,
    borderRadius: 12,
    paddingHorizontal: 12,
    paddingVertical: 10,
    marginBottom: 16,
  },
  searchInput: {
    flex: 1,
    color: colors.text,
    fontSize: 16,
  },
  searchResultCard: {
    flexDirection: 'row',
    alignItems: 'center',
    backgroundColor: colors.background,
    padding: 12,
    borderRadius: 12,
    marginBottom: 8,
  },
  addFriendButton: {
    backgroundColor: colors.primary,
    padding: 10,
    borderRadius: 8,
  },
  requestSentText: {
    color: colors.success,
    fontSize: 12,
    fontWeight: '600',
  },
  emptySearchText: {
    color: colors.textMuted,
    textAlign: 'center',
    padding: 20,
  },
  modalInput: {
    backgroundColor: colors.background,
    borderRadius: 12,
    padding: 14,
    color: colors.text,
    marginBottom: 12,
    borderWidth: 1,
    borderColor: colors.cardBorder,
  },
  textArea: {
    height: 100,
    textAlignVertical: 'top',
  },
  submitButton: {
    backgroundColor: colors.primary,
    paddingVertical: 14,
    borderRadius: 12,
    alignItems: 'center',
    marginTop: 8,
  },
  submitButtonText: {
    color: colors.white,
    fontWeight: 'bold',
    fontSize: 16,
  },
});
