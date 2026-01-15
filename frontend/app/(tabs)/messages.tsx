import React, { useState, useEffect, useRef } from 'react';
import {
  View,
  Text,
  StyleSheet,
  TouchableOpacity,
  TextInput,
  FlatList,
  Image,
  KeyboardAvoidingView,
  Platform,
  Alert,
} from 'react-native';
import { SafeAreaView } from 'react-native-safe-area-context';
import { Ionicons } from '@expo/vector-icons';
import { colors } from '../../src/utils/colors';
import { api } from '../../src/services/api';

interface Message {
  id: string;
  sender_id: string;
  receiver_id: string;
  content: string;
  image_url?: string;
  created_at: string;
  is_read: boolean;
  is_mine: boolean;
}

interface Conversation {
  id: string;
  user: {
    id: string;
    username: string;
    profile_photo?: string;
    is_online?: boolean;
  };
  last_message: string;
  last_message_time: string;
  unread_count: number;
}

export default function MessagesScreen() {
  const [conversations, setConversations] = useState<Conversation[]>([]);
  const [selectedConversation, setSelectedConversation] = useState<Conversation | null>(null);
  const [messages, setMessages] = useState<Message[]>([]);
  const [newMessage, setNewMessage] = useState('');
  const [loading, setLoading] = useState(false);
  const flatListRef = useRef<FlatList>(null);

  useEffect(() => {
    loadConversations();
  }, []);

  useEffect(() => {
    if (selectedConversation) {
      loadMessages(selectedConversation.id);
    }
  }, [selectedConversation]);

  const loadConversations = async () => {
    setLoading(true);
    try {
      const response = await api.get('/messages/conversations');
      setConversations(response.conversations || []);
    } catch (error) {
      // Demo data
      setConversations([
        {
          id: 'c1',
          user: { id: 'u1', username: 'SearchMaster42', profile_photo: 'https://i.pravatar.cc/150?img=1', is_online: true },
          last_message: 'Hey! Love your new protocol! 🔥',
          last_message_time: '2 min ago',
          unread_count: 2,
        },
        {
          id: 'c2',
          user: { id: 'u2', username: 'DataNinja', profile_photo: 'https://i.pravatar.cc/150?img=2', is_online: false },
          last_message: 'Did you read Letters to Evelyn yet?',
          last_message_time: '1 hour ago',
          unread_count: 0,
        },
        {
          id: 'c3',
          user: { id: 'u3', username: 'ProtocolPro', profile_photo: 'https://i.pravatar.cc/150?img=3', is_online: true },
          last_message: 'Thanks for the tip on the marketplace!',
          last_message_time: 'Yesterday',
          unread_count: 0,
        },
      ]);
    } finally {
      setLoading(false);
    }
  };

  const loadMessages = async (conversationId: string) => {
    try {
      const response = await api.get(`/messages/${conversationId}`);
      setMessages(response.messages || []);
    } catch (error) {
      // Demo messages
      setMessages([
        { id: 'm1', sender_id: 'u1', receiver_id: 'me', content: 'Hey there! 👋', created_at: '10:30 AM', is_read: true, is_mine: false },
        { id: 'm2', sender_id: 'me', receiver_id: 'u1', content: 'Hi! What\'s up?', created_at: '10:31 AM', is_read: true, is_mine: true },
        { id: 'm3', sender_id: 'u1', receiver_id: 'me', content: 'I just listed my first protocol on the marketplace! So excited! 🎉', created_at: '10:32 AM', is_read: true, is_mine: false },
        { id: 'm4', sender_id: 'me', receiver_id: 'u1', content: 'That\'s awesome! What kind of protocol is it?', created_at: '10:33 AM', is_read: true, is_mine: true },
        { id: 'm5', sender_id: 'u1', receiver_id: 'me', content: 'It\'s for finding historical documents. Check it out!', created_at: '10:34 AM', is_read: true, is_mine: false },
        { id: 'm6', sender_id: 'u1', receiver_id: 'me', content: 'Love your new protocol! 🔥', created_at: '10:35 AM', is_read: false, is_mine: false },
      ]);
    }
  };

  const handleSendMessage = async () => {
    if (!newMessage.trim() || !selectedConversation) return;
    
    const tempMessage: Message = {
      id: Date.now().toString(),
      sender_id: 'me',
      receiver_id: selectedConversation.user.id,
      content: newMessage,
      created_at: 'Just now',
      is_read: false,
      is_mine: true,
    };
    
    setMessages(prev => [...prev, tempMessage]);
    setNewMessage('');
    
    // Scroll to bottom
    setTimeout(() => {
      flatListRef.current?.scrollToEnd({ animated: true });
    }, 100);
    
    try {
      await api.post('/messages/send', {
        receiver_id: selectedConversation.user.id,
        content: tempMessage.content,
      });
    } catch (error) {
      console.error('Send message error:', error);
    }
  };

  const handleSendImage = () => {
    Alert.alert(
      '📸 Send Image',
      'Image sending feature coming soon!',
      [{ text: 'OK', style: 'default' }]
    );
  };

  const renderConversationItem = ({ item }: { item: Conversation }) => (
    <TouchableOpacity 
      style={[
        styles.conversationItem,
        selectedConversation?.id === item.id && styles.conversationItemActive
      ]}
      onPress={() => setSelectedConversation(item)}
    >
      <View style={styles.avatarContainer}>
        <Image 
          source={{ uri: item.user.profile_photo || 'https://i.pravatar.cc/150' }}
          style={styles.conversationAvatar}
        />
        {item.user.is_online && <View style={styles.onlineIndicator} />}
      </View>
      
      <View style={styles.conversationInfo}>
        <Text style={styles.conversationName}>{item.user.username}</Text>
        <Text style={styles.lastMessage} numberOfLines={1}>{item.last_message}</Text>
      </View>
      
      <View style={styles.conversationMeta}>
        <Text style={styles.messageTime}>{item.last_message_time}</Text>
        {item.unread_count > 0 && (
          <View style={styles.unreadBadge}>
            <Text style={styles.unreadCount}>{item.unread_count}</Text>
          </View>
        )}
      </View>
    </TouchableOpacity>
  );

  const renderMessage = ({ item }: { item: Message }) => (
    <View style={[
      styles.messageContainer,
      item.is_mine ? styles.myMessage : styles.theirMessage
    ]}>
      {item.image_url && (
        <Image 
          source={{ uri: item.image_url }}
          style={styles.messageImage}
          resizeMode="cover"
        />
      )}
      <Text style={[
        styles.messageText,
        item.is_mine ? styles.myMessageText : styles.theirMessageText
      ]}>
        {item.content}
      </Text>
      <View style={styles.messageFooter}>
        <Text style={[
          styles.messageTime,
          item.is_mine && styles.myMessageTime
        ]}>
          {item.created_at}
        </Text>
        {item.is_mine && (
          <Ionicons 
            name={item.is_read ? "checkmark-done" : "checkmark"} 
            size={14} 
            color={item.is_read ? colors.accent : colors.textMuted} 
          />
        )}
      </View>
    </View>
  );

  // Conversation List View
  if (!selectedConversation) {
    return (
      <SafeAreaView style={styles.container} edges={['bottom']}>
        <View style={styles.header}>
          <Text style={styles.headerTitle}>💬 Messages</Text>
          <Text style={styles.headerSubtitle}>
            "Where great conversations happen!" 🗣️
          </Text>
        </View>
        
        {conversations.length === 0 ? (
          <View style={styles.emptyContainer}>
            <Ionicons name="chatbubbles-outline" size={60} color={colors.gray} />
            <Text style={styles.emptyText}>No conversations yet!</Text>
            <Text style={styles.emptySubtext}>
              Start a conversation by finding friends in the Social Hub! 🤝
            </Text>
          </View>
        ) : (
          <FlatList
            data={conversations}
            renderItem={renderConversationItem}
            keyExtractor={(item) => item.id}
            contentContainerStyle={styles.conversationList}
          />
        )}
      </SafeAreaView>
    );
  }

  // Chat View
  return (
    <SafeAreaView style={styles.container} edges={['bottom']}>
      {/* Chat Header */}
      <View style={styles.chatHeader}>
        <TouchableOpacity 
          style={styles.backButton}
          onPress={() => setSelectedConversation(null)}
        >
          <Ionicons name="arrow-back" size={24} color={colors.text} />
        </TouchableOpacity>
        
        <Image 
          source={{ uri: selectedConversation.user.profile_photo || 'https://i.pravatar.cc/150' }}
          style={styles.chatAvatar}
        />
        
        <View style={styles.chatUserInfo}>
          <Text style={styles.chatUsername}>{selectedConversation.user.username}</Text>
          <Text style={styles.chatStatus}>
            {selectedConversation.user.is_online ? '🟢 Online' : '⚪ Offline'}
          </Text>
        </View>
        
        <TouchableOpacity style={styles.headerAction}>
          <Ionicons name="call" size={22} color={colors.primary} />
        </TouchableOpacity>
        
        <TouchableOpacity style={styles.headerAction}>
          <Ionicons name="videocam" size={22} color={colors.primary} />
        </TouchableOpacity>
      </View>
      
      {/* Messages List */}
      <FlatList
        ref={flatListRef}
        data={messages}
        renderItem={renderMessage}
        keyExtractor={(item) => item.id}
        contentContainerStyle={styles.messagesList}
        showsVerticalScrollIndicator={false}
        onContentSizeChange={() => flatListRef.current?.scrollToEnd({ animated: false })}
      />
      
      {/* Input Bar */}
      <KeyboardAvoidingView 
        behavior={Platform.OS === 'ios' ? 'padding' : 'height'}
        keyboardVerticalOffset={Platform.OS === 'ios' ? 90 : 0}
      >
        <View style={styles.inputContainer}>
          <TouchableOpacity 
            style={styles.attachButton}
            onPress={handleSendImage}
          >
            <Ionicons name="image" size={24} color={colors.primary} />
          </TouchableOpacity>
          
          <TextInput
            style={styles.messageInput}
            placeholder="Type a message..."
            placeholderTextColor={colors.gray}
            value={newMessage}
            onChangeText={setNewMessage}
            multiline
            maxLength={500}
          />
          
          <TouchableOpacity 
            style={[styles.sendButton, !newMessage.trim() && styles.sendButtonDisabled]}
            onPress={handleSendMessage}
            disabled={!newMessage.trim()}
          >
            <Ionicons 
              name="send" 
              size={20} 
              color={newMessage.trim() ? colors.white : colors.gray} 
            />
          </TouchableOpacity>
        </View>
      </KeyboardAvoidingView>
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
  conversationList: {
    padding: 12,
  },
  conversationItem: {
    flexDirection: 'row',
    alignItems: 'center',
    backgroundColor: colors.cardBackground,
    padding: 14,
    borderRadius: 12,
    marginBottom: 8,
    borderWidth: 1,
    borderColor: colors.cardBorder,
  },
  conversationItemActive: {
    borderColor: colors.primary,
  },
  avatarContainer: {
    position: 'relative',
  },
  conversationAvatar: {
    width: 50,
    height: 50,
    borderRadius: 25,
  },
  onlineIndicator: {
    position: 'absolute',
    bottom: 2,
    right: 2,
    width: 12,
    height: 12,
    borderRadius: 6,
    backgroundColor: colors.success,
    borderWidth: 2,
    borderColor: colors.cardBackground,
  },
  conversationInfo: {
    flex: 1,
    marginLeft: 12,
  },
  conversationName: {
    color: colors.text,
    fontWeight: 'bold',
    fontSize: 15,
    marginBottom: 4,
  },
  lastMessage: {
    color: colors.textMuted,
    fontSize: 13,
  },
  conversationMeta: {
    alignItems: 'flex-end',
  },
  messageTime: {
    color: colors.textMuted,
    fontSize: 11,
    marginBottom: 4,
  },
  unreadBadge: {
    backgroundColor: colors.primary,
    paddingHorizontal: 8,
    paddingVertical: 2,
    borderRadius: 10,
  },
  unreadCount: {
    color: colors.white,
    fontSize: 11,
    fontWeight: 'bold',
  },
  emptyContainer: {
    flex: 1,
    justifyContent: 'center',
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
  chatHeader: {
    flexDirection: 'row',
    alignItems: 'center',
    padding: 12,
    backgroundColor: colors.cardBackground,
    borderBottomWidth: 1,
    borderBottomColor: colors.cardBorder,
  },
  backButton: {
    padding: 8,
    marginRight: 8,
  },
  chatAvatar: {
    width: 40,
    height: 40,
    borderRadius: 20,
  },
  chatUserInfo: {
    flex: 1,
    marginLeft: 12,
  },
  chatUsername: {
    color: colors.text,
    fontWeight: 'bold',
    fontSize: 16,
  },
  chatStatus: {
    color: colors.textMuted,
    fontSize: 12,
  },
  headerAction: {
    padding: 8,
    marginLeft: 4,
  },
  messagesList: {
    padding: 12,
    paddingBottom: 20,
  },
  messageContainer: {
    maxWidth: '75%',
    marginBottom: 12,
    padding: 12,
    borderRadius: 16,
  },
  myMessage: {
    alignSelf: 'flex-end',
    backgroundColor: colors.primary,
    borderBottomRightRadius: 4,
  },
  theirMessage: {
    alignSelf: 'flex-start',
    backgroundColor: colors.cardBackground,
    borderBottomLeftRadius: 4,
    borderWidth: 1,
    borderColor: colors.cardBorder,
  },
  messageImage: {
    width: 200,
    height: 150,
    borderRadius: 12,
    marginBottom: 8,
  },
  messageText: {
    fontSize: 14,
    lineHeight: 20,
  },
  myMessageText: {
    color: colors.white,
  },
  theirMessageText: {
    color: colors.text,
  },
  messageFooter: {
    flexDirection: 'row',
    alignItems: 'center',
    justifyContent: 'flex-end',
    marginTop: 4,
    gap: 4,
  },
  myMessageTime: {
    color: 'rgba(255,255,255,0.7)',
  },
  inputContainer: {
    flexDirection: 'row',
    alignItems: 'center',
    padding: 12,
    backgroundColor: colors.cardBackground,
    borderTopWidth: 1,
    borderTopColor: colors.cardBorder,
  },
  attachButton: {
    padding: 8,
  },
  messageInput: {
    flex: 1,
    backgroundColor: colors.background,
    borderRadius: 20,
    paddingHorizontal: 16,
    paddingVertical: 10,
    marginHorizontal: 8,
    color: colors.text,
    maxHeight: 100,
    borderWidth: 1,
    borderColor: colors.cardBorder,
  },
  sendButton: {
    width: 40,
    height: 40,
    borderRadius: 20,
    backgroundColor: colors.primary,
    alignItems: 'center',
    justifyContent: 'center',
  },
  sendButtonDisabled: {
    backgroundColor: colors.cardBackground,
  },
});
