# InfoPilot Chat Architecture

## Overview

InfoPilot has two distinct real-time communication systems:

### 1. Group Chat (`/app/backend/routes/chat.py`)
- **Purpose**: Public/private chat rooms for groups
- **Endpoint**: `/api/chat/*`
- **WebSocket**: `/api/chat/ws/{room_id}`
- **Features**:
  - Room-based messaging
  - Multiple users in a room
  - User join/leave notifications
  - Typing indicators
  - Message history

### 2. Direct Messages (`/app/backend/routes/messages.py`)
- **Purpose**: Private 1-on-1 conversations
- **Endpoint**: `/api/dm/*`
- **WebSocket**: `/api/dm/ws`
- **Features**:
  - Private conversations
  - Image attachments (up to 6.9MB)
  - Read receipts
  - Typing indicators
  - Push notifications for offline users
  - Online status tracking

## Why Two Systems?

1. **Different Data Models**: Group chats have rooms with many members, while DMs are between two specific users
2. **Different Privacy**: Group chats can be public, DMs are always private
3. **Different Features**: DMs have read receipts and push notifications for offline users
4. **Scalability**: Separating allows independent scaling

## Key Differences

| Feature | Group Chat | Direct Messages |
|---------|-----------|-----------------|
| Participants | Many | 2 (private) |
| WebSocket | Per room | Per user |
| Read receipts | No | Yes |
| Push notifications | No | Yes |
| Image upload | No | Yes (6.9MB) |
| Typing indicators | Yes | Yes |

## Future Considerations

- Could unify the WebSocket infrastructure
- Could add push notifications to group chat
- Could add image uploads to group chat
