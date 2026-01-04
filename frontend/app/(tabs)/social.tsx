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
  FlatList,
  RefreshControl,
  Modal,
} from 'react-native';
import { SafeAreaView } from 'react-native-safe-area-context';
import { Ionicons } from '@expo/vector-icons';
import { useAuth } from '../../src/context/AuthContext';
import { api } from '../../src/services/api';

interface Friend {
  id: string;
  username: string;
  profile_picture?: string;
  ultimate_search_public: boolean;
}

interface PendingRequest {
  id: string;
  username: string;
  profile_picture?: string;
}

interface Message {
  id: string;
  sender_id: string;
  content: string;
  created_at: string;
  is_mine: boolean;
}

export default function SocialScreen() {
  const { user } = useAuth();
  const [friends, setFriends] = useState<Friend[]>([]);
  const [pendingRequests, setPendingRequests] = useState<PendingRequest[]>([]);
  const [loading, setLoading] = useState(true);
  const [refreshing, setRefreshing] = useState(false);
  const [selectedFriend, setSelectedFriend] = useState<Friend | null>(null);
  const [messages, setMessages] = useState<Message[]>([]);
  const [newMessage, setNewMessage] = useState('');
  const [messagesLoading, setMessagesLoading] = useState(false);
  const [unreadCount, setUnreadCount] = useState(0);

  useEffect(() => {
    loadFriends();
    loadUnreadCount();
  }, []);

  const loadFriends = async () => {
    try {
      const data = await api.get('/friends');
      setFriends(data.friends || []);
      setPendingRequests(data.pending_requests || []);
    } catch (error) {
      console.error('Error loading friends:', error);
    } finally {
      setLoading(false);
    }
  };

  const loadUnreadCount = async () => {
    try {
      const data = await api.get('/messages/unread/count');
      setUnreadCount(data.unread_count || 0);
    } catch (error) {
      console.error('Error loading unread count:', error);
    }
  };

  const onRefresh = useCallback(async () => {
    setRefreshing(true);
    await loadFriends();
    await loadUnreadCount();
    setRefreshing(false);
  }, []);

  const handleAcceptRequest = async (requesterId: string) => {
    try {
      await api.post('/friends/accept', { target_user_id: requesterId });
      Alert.alert('Success', 'Friend request accepted!');
      loadFriends();
    } catch (error: any) {
      Alert.alert('Error', error.response?.data?.detail || 'Could not accept request');
    }
  };

  const handleRejectRequest = async (requesterId: string) => {
    try {
      await api.post('/friends/reject', { target_user_id: requesterId });
      loadFriends();
    } catch (error: any) {
      Alert.alert('Error', error.response?.data?.detail || 'Could not reject request');
    }
  };

  const handleRemoveFriend = (friend: Friend) => {
    Alert.alert(
      'Remove Friend',
      `Are you sure you want to remove ${friend.username} from your friends?`,
      [
        { text: 'Cancel', style: 'cancel' },
        {
          text: 'Remove',
          style: 'destructive',
          onPress: async () => {
            try {
              await api.delete(`/friends/${friend.id}`);
              loadFriends();
            } catch (error) {
              Alert.alert('Error', 'Could not remove friend');
            }
          },
        },
      ]
    );
  };

  const openChat = async (friend: Friend) => {
    setSelectedFriend(friend);
    setMessagesLoading(true);
    try {
      const data = await api.get(`/messages/${friend.id}`);
      setMessages(data.messages || []);
      loadUnreadCount();
    } catch (error) {
      console.error('Error loading messages:', error);
    } finally {
      setMessagesLoading(false);
    }
  };

  const sendMessage = async () => {
    if (!newMessage.trim() || !selectedFriend) return;

    try {
      await api.post('/messages', {
        recipient_id: selectedFriend.id,
        content: newMessage.trim(),
      });
      setNewMessage('');
      // Reload messages
      const data = await api.get(`/messages/${selectedFriend.id}`);
      setMessages(data.messages || []);
    } catch (error: any) {
      Alert.alert('Error', error.response?.data?.detail || 'Could not send message');
    }
  };

  const renderFriend = ({ item }: { item: Friend }) => (
    <View style={styles.friendCard}>
      <View style={styles.friendAvatar}>
        <Text style={styles.friendInitial}>
          {item.username[0]?.toUpperCase()}
        </Text>
      </View>
      <View style={styles.friendInfo}>
        <Text style={styles.friendName}>@{item.username}</Text>
        {item.ultimate_search_public && (
          <View style={styles.publicBadge}>
            <Ionicons name="globe" size={10} color="#4CAF50" />
            <Text style={styles.publicText}>Public USP</Text>
          </View>
        )}
      </View>
      <View style={styles.friendActions}>
        <TouchableOpacity
          style={styles.chatButton}
          onPress={() => openChat(item)}
        >
          <Ionicons name="chatbubble" size={18} color="#2196F3" />
        </TouchableOpacity>
        <TouchableOpacity
          style={styles.removeButton}
          onPress={() => handleRemoveFriend(item)}
        >
          <Ionicons name="person-remove" size={18} color="#f44336" />
        </TouchableOpacity>
      </View>
    </View>
  );

  const renderPendingRequest = ({ item }: { item: PendingRequest }) => (
    <View style={styles.requestCard}>
      <View style={styles.requestAvatar}>
        <Text style={styles.requestInitial}>
          {item.username[0]?.toUpperCase()}
        </Text>
      </View>
      <Text style={styles.requestName}>@{item.username}</Text>
      <View style={styles.requestActions}>
        <TouchableOpacity
          style={styles.acceptButton}
          onPress={() => handleAcceptRequest(item.id)}
        >
          <Ionicons name="checkmark" size={20} color="#fff" />
        </TouchableOpacity>
        <TouchableOpacity
          style={styles.rejectButton}
          onPress={() => handleRejectRequest(item.id)}
        >
          <Ionicons name="close" size={20} color="#fff" />
        </TouchableOpacity>
      </View>
    </View>
  );

  return (
    <SafeAreaView style={styles.container} edges={['top']}>
      {/* Header */}
      <View style={styles.header}>
        <View style={styles.headerLeft}>
          <Ionicons name="people" size={28} color="#2196F3" />
          <Text style={styles.headerTitle}>Social</Text>
        </View>
        {unreadCount > 0 && (
          <View style={styles.unreadBadge}>
            <Text style={styles.unreadText}>{unreadCount}</Text>
          </View>
        )}
      </View>

      <ScrollView
        style={styles.content}
        refreshControl={
          <RefreshControl refreshing={refreshing} onRefresh={onRefresh} />
        }
      >
        {/* Pending Requests */}
        {pendingRequests.length > 0 && (
          <View style={styles.section}>
            <Text style={styles.sectionTitle}>
              Friend Requests ({pendingRequests.length})
            </Text>
            {pendingRequests.map((req) => (
              <View key={req.id}>
                {renderPendingRequest({ item: req })}
              </View>
            ))}
          </View>
        )}

        {/* Friends List */}
        <View style={styles.section}>
          <Text style={styles.sectionTitle}>
            Friends ({friends.length})
          </Text>
          {loading ? (
            <ActivityIndicator size="large" color="#2196F3" style={styles.loader} />
          ) : friends.length === 0 ? (
            <View style={styles.emptyState}>
              <Ionicons name="people-outline" size={48} color="#ccc" />
              <Text style={styles.emptyTitle}>No Friends Yet</Text>
              <Text style={styles.emptyText}>
                Make friends by reacting to search results on other users'
                public Ultimate Search Pages.
              </Text>
            </View>
          ) : (
            friends.map((friend) => (
              <View key={friend.id}>
                {renderFriend({ item: friend })}
              </View>
            ))
          )}
        </View>

        {/* Info Box */}
        <View style={styles.infoBox}>
          <Ionicons name="information-circle" size={20} color="#1976D2" />
          <Text style={styles.infoText}>
            Friend requests can be made by viewing other users' public Ultimate
            Search Pages and reacting to their content, or by seeing their
            reactions on search results.
          </Text>
        </View>
      </ScrollView>

      {/* Chat Modal */}
      <Modal
        visible={selectedFriend !== null}
        animationType="slide"
        presentationStyle="pageSheet"
        onRequestClose={() => setSelectedFriend(null)}
      >
        <SafeAreaView style={styles.chatContainer}>
          {/* Chat Header */}
          <View style={styles.chatHeader}>
            <TouchableOpacity onPress={() => setSelectedFriend(null)}>
              <Ionicons name="arrow-back" size={24} color="#333" />
            </TouchableOpacity>
            <View style={styles.chatHeaderInfo}>
              <View style={styles.chatAvatar}>
                <Text style={styles.chatAvatarText}>
                  {selectedFriend?.username[0]?.toUpperCase()}
                </Text>
              </View>
              <Text style={styles.chatHeaderName}>@{selectedFriend?.username}</Text>
            </View>
          </View>

          {/* Messages */}
          {messagesLoading ? (
            <ActivityIndicator size="large" color="#2196F3" style={styles.loader} />
          ) : (
            <FlatList
              data={messages}
              keyExtractor={(item) => item.id}
              renderItem={({ item }) => (
                <View
                  style={[
                    styles.messageBubble,
                    item.is_mine ? styles.myMessage : styles.theirMessage,
                  ]}
                >
                  <Text
                    style={[
                      styles.messageText,
                      item.is_mine ? styles.myMessageText : styles.theirMessageText,
                    ]}
                  >
                    {item.content}
                  </Text>
                  <Text style={styles.messageTime}>
                    {new Date(item.created_at).toLocaleTimeString([], {
                      hour: '2-digit',
                      minute: '2-digit',
                    })}
                  </Text>
                </View>
              )}
              contentContainerStyle={styles.messagesList}
              ListEmptyComponent={
                <View style={styles.noMessages}>
                  <Ionicons name="chatbubbles-outline" size={48} color="#ccc" />
                  <Text style={styles.noMessagesText}>No messages yet</Text>
                </View>
              }
            />
          )}

          {/* Message Input */}
          <View style={styles.inputContainer}>
            <TextInput
              style={styles.messageInput}
              placeholder="Type a message..."
              placeholderTextColor="#999"
              value={newMessage}
              onChangeText={setNewMessage}
              multiline
            />
            <TouchableOpacity
              style={[styles.sendButton, !newMessage.trim() && styles.sendButtonDisabled]}
              onPress={sendMessage}
              disabled={!newMessage.trim()}
            >
              <Ionicons name="send" size={20} color="#fff" />
            </TouchableOpacity>
          </View>
        </SafeAreaView>
      </Modal>
    </SafeAreaView>
  );
}

const styles = StyleSheet.create({
  container: {
    flex: 1,
    backgroundColor: '#FFFFF0',
  },
  header: {
    flexDirection: 'row',
    justifyContent: 'space-between',
    alignItems: 'center',
    paddingHorizontal: 16,
    paddingVertical: 12,
    backgroundColor: '#fff',
    borderBottomWidth: 1,
    borderBottomColor: '#E0E0E0',
  },
  headerLeft: {
    flexDirection: 'row',
    alignItems: 'center',
  },
  headerTitle: {
    fontSize: 20,
    fontWeight: 'bold',
    color: '#333',
    marginLeft: 10,
  },
  unreadBadge: {
    backgroundColor: '#f44336',
    paddingHorizontal: 10,
    paddingVertical: 4,
    borderRadius: 12,
  },
  unreadText: {
    color: '#fff',
    fontSize: 12,
    fontWeight: '600',
  },
  content: {
    flex: 1,
    padding: 16,
  },
  section: {
    marginBottom: 24,
  },
  sectionTitle: {
    fontSize: 16,
    fontWeight: '600',
    color: '#333',
    marginBottom: 12,
  },
  loader: {
    marginTop: 20,
  },
  emptyState: {
    alignItems: 'center',
    padding: 24,
    backgroundColor: '#fff',
    borderRadius: 12,
  },
  emptyTitle: {
    fontSize: 16,
    fontWeight: '600',
    color: '#333',
    marginTop: 12,
  },
  emptyText: {
    fontSize: 13,
    color: '#666',
    textAlign: 'center',
    marginTop: 8,
    lineHeight: 18,
  },
  friendCard: {
    flexDirection: 'row',
    alignItems: 'center',
    backgroundColor: '#fff',
    borderRadius: 12,
    padding: 12,
    marginBottom: 10,
    borderWidth: 1,
    borderColor: '#E0E0E0',
  },
  friendAvatar: {
    width: 48,
    height: 48,
    borderRadius: 24,
    backgroundColor: '#2196F3',
    alignItems: 'center',
    justifyContent: 'center',
  },
  friendInitial: {
    fontSize: 20,
    fontWeight: 'bold',
    color: '#fff',
  },
  friendInfo: {
    flex: 1,
    marginLeft: 12,
  },
  friendName: {
    fontSize: 15,
    fontWeight: '600',
    color: '#333',
  },
  publicBadge: {
    flexDirection: 'row',
    alignItems: 'center',
    marginTop: 4,
  },
  publicText: {
    fontSize: 11,
    color: '#4CAF50',
    marginLeft: 4,
  },
  friendActions: {
    flexDirection: 'row',
  },
  chatButton: {
    padding: 10,
    backgroundColor: '#E3F2FD',
    borderRadius: 20,
    marginRight: 8,
  },
  removeButton: {
    padding: 10,
    backgroundColor: '#FFEBEE',
    borderRadius: 20,
  },
  requestCard: {
    flexDirection: 'row',
    alignItems: 'center',
    backgroundColor: '#FFF3E0',
    borderRadius: 12,
    padding: 12,
    marginBottom: 10,
    borderWidth: 1,
    borderColor: '#FFE0B2',
  },
  requestAvatar: {
    width: 44,
    height: 44,
    borderRadius: 22,
    backgroundColor: '#FF9800',
    alignItems: 'center',
    justifyContent: 'center',
  },
  requestInitial: {
    fontSize: 18,
    fontWeight: 'bold',
    color: '#fff',
  },
  requestName: {
    flex: 1,
    fontSize: 15,
    fontWeight: '600',
    color: '#333',
    marginLeft: 12,
  },
  requestActions: {
    flexDirection: 'row',
  },
  acceptButton: {
    padding: 10,
    backgroundColor: '#4CAF50',
    borderRadius: 20,
    marginRight: 8,
  },
  rejectButton: {
    padding: 10,
    backgroundColor: '#f44336',
    borderRadius: 20,
  },
  infoBox: {
    flexDirection: 'row',
    alignItems: 'flex-start',
    backgroundColor: '#E3F2FD',
    padding: 12,
    borderRadius: 12,
    marginTop: 8,
  },
  infoText: {
    flex: 1,
    marginLeft: 8,
    fontSize: 12,
    color: '#1976D2',
    lineHeight: 16,
  },
  chatContainer: {
    flex: 1,
    backgroundColor: '#FFFFF0',
  },
  chatHeader: {
    flexDirection: 'row',
    alignItems: 'center',
    paddingHorizontal: 16,
    paddingVertical: 12,
    backgroundColor: '#fff',
    borderBottomWidth: 1,
    borderBottomColor: '#E0E0E0',
  },
  chatHeaderInfo: {
    flexDirection: 'row',
    alignItems: 'center',
    marginLeft: 16,
  },
  chatAvatar: {
    width: 36,
    height: 36,
    borderRadius: 18,
    backgroundColor: '#2196F3',
    alignItems: 'center',
    justifyContent: 'center',
  },
  chatAvatarText: {
    fontSize: 16,
    fontWeight: 'bold',
    color: '#fff',
  },
  chatHeaderName: {
    fontSize: 16,
    fontWeight: '600',
    color: '#333',
    marginLeft: 10,
  },
  messagesList: {
    padding: 16,
    flexGrow: 1,
  },
  noMessages: {
    alignItems: 'center',
    marginTop: 60,
  },
  noMessagesText: {
    fontSize: 14,
    color: '#999',
    marginTop: 12,
  },
  messageBubble: {
    maxWidth: '75%',
    padding: 12,
    borderRadius: 16,
    marginBottom: 8,
  },
  myMessage: {
    alignSelf: 'flex-end',
    backgroundColor: '#2196F3',
    borderBottomRightRadius: 4,
  },
  theirMessage: {
    alignSelf: 'flex-start',
    backgroundColor: '#fff',
    borderBottomLeftRadius: 4,
    borderWidth: 1,
    borderColor: '#E0E0E0',
  },
  messageText: {
    fontSize: 14,
    lineHeight: 18,
  },
  myMessageText: {
    color: '#fff',
  },
  theirMessageText: {
    color: '#333',
  },
  messageTime: {
    fontSize: 10,
    color: 'rgba(255,255,255,0.7)',
    marginTop: 4,
    textAlign: 'right',
  },
  inputContainer: {
    flexDirection: 'row',
    alignItems: 'flex-end',
    padding: 12,
    backgroundColor: '#fff',
    borderTopWidth: 1,
    borderTopColor: '#E0E0E0',
  },
  messageInput: {
    flex: 1,
    backgroundColor: '#F5F5F5',
    borderRadius: 20,
    paddingHorizontal: 16,
    paddingVertical: 10,
    fontSize: 15,
    maxHeight: 100,
    marginRight: 10,
  },
  sendButton: {
    width: 44,
    height: 44,
    borderRadius: 22,
    backgroundColor: '#2196F3',
    alignItems: 'center',
    justifyContent: 'center',
  },
  sendButtonDisabled: {
    backgroundColor: '#ccc',
  },
});
