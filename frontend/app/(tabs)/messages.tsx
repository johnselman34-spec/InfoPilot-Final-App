import React, { useState, useEffect, useRef } from 'react';
import {
  View,
  Text,
  StyleSheet,
  ScrollView,
  TouchableOpacity,
  TextInput,
  ActivityIndicator,
  KeyboardAvoidingView,
  Platform,
  Image,
  Alert,
} from 'react-native';
import { SafeAreaView } from 'react-native-safe-area-context';
import { Ionicons } from '@expo/vector-icons';
import { colors } from '../../src/utils/colors';
import { api } from '../../src/services/api';
import * as ImagePicker from 'expo-image-picker';

interface Message {
  id: string;
  sender_id: string;
  sender_username: string;
  content: string;
  image_url?: string;
  timestamp: string;
  read: boolean;
  is_mine: boolean;
}

interface Conversation {
  id: string;
  participant: {
    id: string;
    username: string;
    profile_photo?: string;
    is_online?: boolean;
  };
  last_message?: string;
  last_message_time?: string;
  unread_count: number;
  is_typing?: boolean;
}

type ViewMode = 'conversations' | 'chat';

// Maximum image size: 6.9MB
const MAX_IMAGE_SIZE = 6.9 * 1024 * 1024;

export default function MessagesScreen() {
  const [viewMode, setViewMode] = useState<ViewMode>('conversations');
  const [loading, setLoading] = useState(false);
  const [conversations, setConversations] = useState<Conversation[]>([]);
  const [activeConversation, setActiveConversation] = useState<Conversation | null>(null);
  const [messages, setMessages] = useState<Message[]>([]);
  const [newMessage, setNewMessage] = useState('');
  const [isTyping, setIsTyping] = useState(false);
  const [otherUserTyping, setOtherUserTyping] = useState(false);
  const [selectedImage, setSelectedImage] = useState<string | null>(null);
  
  const scrollViewRef = useRef<ScrollView>(null);
  const typingTimeoutRef = useRef<NodeJS.Timeout | null>(null);

  useEffect(() => {
    loadConversations();
    
    // Simulate real-time updates
    const interval = setInterval(() => {
      if (activeConversation) {
        // Simulate typing indicator
        setOtherUserTyping(Math.random() > 0.8);
      }
    }, 3000);

    return () => clearInterval(interval);
  }, []);

  useEffect(() => {
    if (activeConversation) {
      loadMessages(activeConversation.id);
    }
  }, [activeConversation]);

  const loadConversations = async () => {
    setLoading(true);
    try {
      const response = await api.get('/messages/conversations');
      setConversations(response.conversations || []);
    } catch (error) {
      // Use mock data
      setConversations(getMockConversations());
    } finally {
      setLoading(false);
    }
  };

  const loadMessages = async (conversationId: string) => {
    try {
      const response = await api.get(`/messages/${conversationId}`);
      setMessages(response.messages || []);
      // Mark as read
      await api.post(`/messages/${conversationId}/read`);
    } catch (error) {
      setMessages(getMockMessages());
    }
  };

  const getMockConversations = (): Conversation[] => [
    {
      id: '1',
      participant: { id: 'admin', username: 'JJSPilot24', is_online: true },
      last_message: 'Welcome to InfoPilot! Let me know if you need help! 🚀',
      last_message_time: new Date().toISOString(),
      unread_count: 1,
    },
    {
      id: '2',
      participant: { id: '2', username: 'ProtocolMaster', is_online: false },
      last_message: 'Great protocol! Where did you find those sources?',
      last_message_time: new Date(Date.now() - 3600000).toISOString(),
      unread_count: 0,
    },
    {
      id: '3',
      participant: { id: '3', username: 'ResearchGuru', is_online: true },
      last_message: 'Thanks for sharing! That was super helpful 📚',
      last_message_time: new Date(Date.now() - 7200000).toISOString(),
      unread_count: 0,
    },
  ];

  const getMockMessages = (): Message[] => [
    {
      id: '1',
      sender_id: 'admin',
      sender_username: 'JJSPilot24',
      content: 'Welcome to InfoPilot! 🎉 I\'m so glad you\'re here!',
      timestamp: new Date(Date.now() - 3600000).toISOString(),
      read: true,
      is_mine: false,
    },
    {
      id: '2',
      sender_id: 'admin',
      sender_username: 'JJSPilot24',
      content: 'Feel free to ask me anything about creating protocols or using the marketplace.',
      timestamp: new Date(Date.now() - 3500000).toISOString(),
      read: true,
      is_mine: false,
    },
    {
      id: '3',
      sender_id: 'me',
      sender_username: 'Me',
      content: 'Thanks! This app is amazing! How do I create my first protocol?',
      timestamp: new Date(Date.now() - 3400000).toISOString(),
      read: true,
      is_mine: true,
    },
    {
      id: '4',
      sender_id: 'admin',
      sender_username: 'JJSPilot24',
      content: 'Great question! Go to Categories > Create Category, then enter your protocol using the InfoJet 2.0 format. For example: (American Civil War) & (heroes or leadership)+',
      timestamp: new Date(Date.now() - 3300000).toISOString(),
      read: true,
      is_mine: false,
    },
    {
      id: '5',
      sender_id: 'admin',
      sender_username: 'JJSPilot24',
      content: 'And don\'t forget to check out my book "Letters to Evelyn" for more tips! 📚',
      timestamp: new Date(Date.now() - 3200000).toISOString(),
      read: true,
      is_mine: false,
    },
  ];

  const handleSendMessage = async () => {
    if (!newMessage.trim() && !selectedImage) return;

    const messageContent = newMessage.trim();
    const messageImage = selectedImage;

    // Optimistically add message
    const newMsg: Message = {
      id: Date.now().toString(),
      sender_id: 'me',
      sender_username: 'Me',
      content: messageContent,
      image_url: messageImage || undefined,
      timestamp: new Date().toISOString(),
      read: false,
      is_mine: true,
    };

    setMessages(prev => [...prev, newMsg]);
    setNewMessage('');
    setSelectedImage(null);

    // Scroll to bottom
    setTimeout(() => {
      scrollViewRef.current?.scrollToEnd({ animated: true });
    }, 100);

    try {
      await api.post(`/messages/${activeConversation?.id}/send`, {
        content: messageContent,
        image_url: messageImage,
      });
    } catch (error) {
      console.error('Send message error:', error);
    }

    // Simulate response
    setTimeout(() => {
      const responses = [
        'That\'s awesome! 🎉',
        'Great to hear from you!',
        'Let me know if you need anything else!',
        'Happy researching! 📚',
        'Keep up the great protocol work! 💪',
      ];
      
      const responseMsg: Message = {
        id: (Date.now() + 1).toString(),
        sender_id: activeConversation?.participant.id || 'other',
        sender_username: activeConversation?.participant.username || 'User',
        content: responses[Math.floor(Math.random() * responses.length)],
        timestamp: new Date().toISOString(),
        read: false,
        is_mine: false,
      };
      
      setMessages(prev => [...prev, responseMsg]);
      setTimeout(() => {
        scrollViewRef.current?.scrollToEnd({ animated: true });
      }, 100);
    }, 2000);
  };

  const handleTyping = (text: string) => {
    setNewMessage(text);
    
    if (!isTyping) {
      setIsTyping(true);
      // Send typing indicator
    }

    // Clear existing timeout
    if (typingTimeoutRef.current) {
      clearTimeout(typingTimeoutRef.current);
    }

    // Set new timeout
    typingTimeoutRef.current = setTimeout(() => {
      setIsTyping(false);
    }, 1000);
  };

  const handlePickImage = async () => {
    try {
      const result = await ImagePicker.launchImageLibraryAsync({
        mediaTypes: ImagePicker.MediaTypeOptions.Images,
        allowsEditing: true,
        quality: 0.7,
        base64: true,
      });

      if (!result.canceled && result.assets[0]) {
        const asset = result.assets[0];
        
        // Check file size (approximate from base64)
        if (asset.base64) {
          const sizeInBytes = (asset.base64.length * 3) / 4;
          if (sizeInBytes > MAX_IMAGE_SIZE) {
            Alert.alert('Image Too Large', `Please select an image under 6.9MB. Your image is ${(sizeInBytes / (1024 * 1024)).toFixed(1)}MB.`);
            return;
          }
        }

        setSelectedImage(asset.uri);
      }
    } catch (error) {
      Alert.alert('Error', 'Failed to pick image');
    }
  };

  const openConversation = (conversation: Conversation) => {
    setActiveConversation(conversation);
    setViewMode('chat');
  };

  const backToConversations = () => {
    setViewMode('conversations');
    setActiveConversation(null);
    setMessages([]);
  };

  const formatTime = (timestamp: string) => {
    const date = new Date(timestamp);
    const now = new Date();
    const diff = now.getTime() - date.getTime();
    
    if (diff < 60000) return 'Just now';
    if (diff < 3600000) return `${Math.floor(diff / 60000)}m ago`;
    if (diff < 86400000) return date.toLocaleTimeString([], { hour: '2-digit', minute: '2-digit' });
    return date.toLocaleDateString();
  };

  // Conversations List View
  const renderConversations = () => (
    <ScrollView style={styles.conversationsList}>
      {conversations.length === 0 ? (
        <View style={styles.emptyState}>
          <Ionicons name="chatbubbles-outline" size={64} color={colors.gray} />
          <Text style={styles.emptyTitle}>No Messages Yet</Text>
          <Text style={styles.emptySubtitle}>
            Start a conversation by finding friends in the Social tab!
          </Text>
        </View>
      ) : (
        conversations.map(conv => (
          <TouchableOpacity
            key={conv.id}
            style={[styles.conversationItem, conv.unread_count > 0 && styles.unreadConversation]}
            onPress={() => openConversation(conv)}
          >
            <View style={styles.avatarContainer}>
              <View style={styles.avatar}>
                <Ionicons name="person-circle" size={48} color={colors.primary} />
              </View>
              {conv.participant.is_online && <View style={styles.onlineIndicator} />}
            </View>
            
            <View style={styles.conversationInfo}>
              <View style={styles.conversationHeader}>
                <Text style={[styles.participantName, conv.unread_count > 0 && styles.unreadText]}>
                  @{conv.participant.username}
                </Text>
                <Text style={styles.messageTime}>
                  {conv.last_message_time ? formatTime(conv.last_message_time) : ''}
                </Text>
              </View>
              <View style={styles.conversationPreview}>
                <Text 
                  style={[styles.lastMessage, conv.unread_count > 0 && styles.unreadText]}
                  numberOfLines={1}
                >
                  {conv.last_message || 'Start chatting!'}
                </Text>
                {conv.unread_count > 0 && (
                  <View style={styles.unreadBadge}>
                    <Text style={styles.unreadCount}>{conv.unread_count}</Text>
                  </View>
                )}
              </View>
            </View>
          </TouchableOpacity>
        ))
      )}
    </ScrollView>
  );

  // Chat View
  const renderChat = () => (
    <KeyboardAvoidingView 
      style={styles.chatContainer}
      behavior={Platform.OS === 'ios' ? 'padding' : 'height'}
      keyboardVerticalOffset={90}
    >
      {/* Chat Header */}
      <View style={styles.chatHeader}>
        <TouchableOpacity onPress={backToConversations} style={styles.backButton}>
          <Ionicons name="arrow-back" size={24} color={colors.primary} />
        </TouchableOpacity>
        <View style={styles.chatHeaderInfo}>
          <Text style={styles.chatHeaderName}>
            @{activeConversation?.participant.username}
          </Text>
          <Text style={styles.chatHeaderStatus}>
            {activeConversation?.participant.is_online ? '🟢 Online' : '⚫ Offline'}
          </Text>
        </View>
        <TouchableOpacity style={styles.chatHeaderAction}>
          <Ionicons name="ellipsis-vertical" size={20} color={colors.text} />
        </TouchableOpacity>
      </View>

      {/* Messages */}
      <ScrollView 
        ref={scrollViewRef}
        style={styles.messagesContainer}
        contentContainerStyle={styles.messagesContent}
        onContentSizeChange={() => scrollViewRef.current?.scrollToEnd({ animated: false })}
      >
        {messages.map(msg => (
          <View 
            key={msg.id} 
            style={[
              styles.messageBubble,
              msg.is_mine ? styles.myMessage : styles.theirMessage
            ]}
          >
            {msg.image_url && (
              <Image source={{ uri: msg.image_url }} style={styles.messageImage} />
            )}
            {msg.content && (
              <Text style={[
                styles.messageText,
                msg.is_mine ? styles.myMessageText : styles.theirMessageText
              ]}>
                {msg.content}
              </Text>
            )}
            <View style={styles.messageFooter}>
              <Text style={[
                styles.messageTime,
                msg.is_mine ? styles.myMessageTime : styles.theirMessageTime
              ]}>
                {formatTime(msg.timestamp)}
              </Text>
              {msg.is_mine && (
                <Text style={styles.readReceipt}>
                  {msg.read ? '✓✓' : '✓'}
                </Text>
              )}
            </View>
          </View>
        ))}
        
        {/* Typing Indicator */}
        {otherUserTyping && (
          <View style={[styles.messageBubble, styles.theirMessage, styles.typingBubble]}>
            <Text style={styles.typingText}>
              {activeConversation?.participant.username} is typing...
            </Text>
            <View style={styles.typingDots}>
              <View style={[styles.typingDot, styles.typingDot1]} />
              <View style={[styles.typingDot, styles.typingDot2]} />
              <View style={[styles.typingDot, styles.typingDot3]} />
            </View>
          </View>
        )}
      </ScrollView>

      {/* Selected Image Preview */}
      {selectedImage && (
        <View style={styles.imagePreview}>
          <Image source={{ uri: selectedImage }} style={styles.previewImage} />
          <TouchableOpacity 
            style={styles.removeImageButton}
            onPress={() => setSelectedImage(null)}
          >
            <Ionicons name="close-circle" size={24} color={colors.error} />
          </TouchableOpacity>
        </View>
      )}

      {/* Input Area */}
      <View style={styles.inputContainer}>
        <TouchableOpacity style={styles.attachButton} onPress={handlePickImage}>
          <Ionicons name="image" size={24} color={colors.primary} />
        </TouchableOpacity>
        <TextInput
          style={styles.textInput}
          placeholder="Type a message..."
          placeholderTextColor={colors.gray}
          value={newMessage}
          onChangeText={handleTyping}
          multiline
          maxLength={1000}
        />
        <TouchableOpacity 
          style={[styles.sendButton, (!newMessage.trim() && !selectedImage) && styles.sendButtonDisabled]}
          onPress={handleSendMessage}
          disabled={!newMessage.trim() && !selectedImage}
        >
          <Ionicons 
            name="send" 
            size={20} 
            color={(!newMessage.trim() && !selectedImage) ? colors.gray : colors.white} 
          />
        </TouchableOpacity>
      </View>
    </KeyboardAvoidingView>
  );

  return (
    <SafeAreaView style={styles.container} edges={['bottom']}>
      {viewMode === 'conversations' ? (
        <>
          <View style={styles.header}>
            <Text style={styles.headerTitle}>💬 Messages</Text>
            <Text style={styles.headerSubtitle}>
              "Where protocols meet conversations!" 📚
            </Text>
          </View>
          {loading ? (
            <View style={styles.loadingContainer}>
              <ActivityIndicator size="large" color={colors.primary} />
              <Text style={styles.loadingText}>Loading messages... 📨</Text>
            </View>
          ) : (
            renderConversations()
          )}
        </>
      ) : (
        renderChat()
      )}
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
    fontStyle: 'italic',
  },
  loadingContainer: {
    flex: 1,
    justifyContent: 'center',
    alignItems: 'center',
  },
  loadingText: {
    color: colors.textMuted,
    marginTop: 12,
  },
  // Conversations List
  conversationsList: {
    flex: 1,
  },
  emptyState: {
    flex: 1,
    alignItems: 'center',
    justifyContent: 'center',
    padding: 40,
  },
  emptyTitle: {
    fontSize: 18,
    fontWeight: 'bold',
    color: colors.text,
    marginTop: 16,
  },
  emptySubtitle: {
    fontSize: 14,
    color: colors.textMuted,
    textAlign: 'center',
    marginTop: 8,
  },
  conversationItem: {
    flexDirection: 'row',
    padding: 16,
    borderBottomWidth: 1,
    borderBottomColor: colors.cardBorder,
    backgroundColor: colors.cardBackground,
  },
  unreadConversation: {
    backgroundColor: colors.primary + '10',
  },
  avatarContainer: {
    position: 'relative',
    marginRight: 12,
  },
  avatar: {},
  onlineIndicator: {
    position: 'absolute',
    bottom: 2,
    right: 2,
    width: 14,
    height: 14,
    borderRadius: 7,
    backgroundColor: colors.success,
    borderWidth: 2,
    borderColor: colors.cardBackground,
  },
  conversationInfo: {
    flex: 1,
  },
  conversationHeader: {
    flexDirection: 'row',
    justifyContent: 'space-between',
    marginBottom: 4,
  },
  participantName: {
    fontSize: 15,
    fontWeight: '600',
    color: colors.text,
  },
  unreadText: {
    fontWeight: 'bold',
  },
  messageTime: {
    fontSize: 12,
    color: colors.textMuted,
  },
  conversationPreview: {
    flexDirection: 'row',
    justifyContent: 'space-between',
    alignItems: 'center',
  },
  lastMessage: {
    fontSize: 13,
    color: colors.textMuted,
    flex: 1,
  },
  unreadBadge: {
    backgroundColor: colors.primary,
    borderRadius: 10,
    paddingHorizontal: 8,
    paddingVertical: 2,
    marginLeft: 8,
  },
  unreadCount: {
    fontSize: 12,
    fontWeight: 'bold',
    color: colors.white,
  },
  // Chat View
  chatContainer: {
    flex: 1,
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
  },
  chatHeaderInfo: {
    flex: 1,
    marginLeft: 8,
  },
  chatHeaderName: {
    fontSize: 16,
    fontWeight: 'bold',
    color: colors.text,
  },
  chatHeaderStatus: {
    fontSize: 12,
    color: colors.textMuted,
  },
  chatHeaderAction: {
    padding: 8,
  },
  messagesContainer: {
    flex: 1,
    backgroundColor: colors.background,
  },
  messagesContent: {
    padding: 16,
    paddingBottom: 20,
  },
  messageBubble: {
    maxWidth: '80%',
    padding: 12,
    borderRadius: 16,
    marginBottom: 8,
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
  },
  messageImage: {
    width: 200,
    height: 150,
    borderRadius: 8,
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
    justifyContent: 'flex-end',
    alignItems: 'center',
    marginTop: 4,
  },
  myMessageTime: {
    color: 'rgba(255,255,255,0.7)',
    fontSize: 10,
  },
  theirMessageTime: {
    color: colors.textMuted,
    fontSize: 10,
  },
  readReceipt: {
    color: 'rgba(255,255,255,0.7)',
    fontSize: 10,
    marginLeft: 4,
  },
  typingBubble: {
    backgroundColor: colors.cardBackground,
  },
  typingText: {
    fontSize: 12,
    color: colors.textMuted,
    fontStyle: 'italic',
  },
  typingDots: {
    flexDirection: 'row',
    marginTop: 4,
    gap: 4,
  },
  typingDot: {
    width: 8,
    height: 8,
    borderRadius: 4,
    backgroundColor: colors.primary,
    opacity: 0.5,
  },
  typingDot1: {
    opacity: 0.3,
  },
  typingDot2: {
    opacity: 0.6,
  },
  typingDot3: {
    opacity: 1,
  },
  imagePreview: {
    padding: 8,
    backgroundColor: colors.cardBackground,
    borderTopWidth: 1,
    borderTopColor: colors.cardBorder,
    flexDirection: 'row',
    alignItems: 'center',
  },
  previewImage: {
    width: 60,
    height: 60,
    borderRadius: 8,
  },
  removeImageButton: {
    marginLeft: 8,
  },
  inputContainer: {
    flexDirection: 'row',
    alignItems: 'flex-end',
    padding: 12,
    backgroundColor: colors.cardBackground,
    borderTopWidth: 1,
    borderTopColor: colors.cardBorder,
  },
  attachButton: {
    padding: 8,
    marginRight: 8,
  },
  textInput: {
    flex: 1,
    backgroundColor: colors.background,
    borderRadius: 20,
    paddingHorizontal: 16,
    paddingVertical: 10,
    fontSize: 14,
    color: colors.text,
    maxHeight: 100,
    borderWidth: 1,
    borderColor: colors.cardBorder,
  },
  sendButton: {
    backgroundColor: colors.primary,
    width: 40,
    height: 40,
    borderRadius: 20,
    justifyContent: 'center',
    alignItems: 'center',
    marginLeft: 8,
  },
  sendButtonDisabled: {
    backgroundColor: colors.cardBackground,
  },
});
