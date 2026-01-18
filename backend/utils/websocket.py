"""
InfoPilot Explorer - WebSocket Manager
Real-time chat using Socket.IO
"""
import socketio
import logging
from datetime import datetime, timezone
import uuid
import jwt
import os

from utils.db import db

logger = logging.getLogger(__name__)

# Create Socket.IO server with CORS
sio = socketio.AsyncServer(
    async_mode='asgi',
    cors_allowed_origins='*',
    logger=True,
    engineio_logger=False
)

# Connection tracking
connected_users = {}  # sid -> {user_id, username, room_id}
room_users = {}  # room_id -> set of sids


async def authenticate_token(token: str) -> dict:
    """Authenticate JWT token and return user data."""
    if not token:
        return None
    
    try:
        SECRET_KEY = os.environ.get("JWT_SECRET", "infopilot_secret_key_2024")
        payload = jwt.decode(token, SECRET_KEY, algorithms=["HS256"])
        user_id = payload.get("user_id")
        
        if user_id:
            user = await db.users.find_one({"id": user_id}, {"_id": 0, "password": 0})
            return user
    except Exception as e:
        logger.error(f"Token auth error: {e}")
    
    return None


@sio.event
async def connect(sid, environ, auth):
    """Handle client connection."""
    logger.info(f"Client connecting: {sid}")
    
    # Get token from auth or query string
    token = None
    if auth and isinstance(auth, dict):
        token = auth.get('token')
    
    if not token:
        # Try query string
        query_string = environ.get('QUERY_STRING', '')
        for param in query_string.split('&'):
            if param.startswith('token='):
                token = param.split('=')[1]
                break
    
    user = await authenticate_token(token)
    if not user:
        logger.warning(f"Authentication failed for {sid}")
        await sio.disconnect(sid)
        return False
    
    connected_users[sid] = {
        'user_id': user['id'],
        'username': user.get('username', 'Unknown'),
        'room_id': None
    }
    
    logger.info(f"User {user['username']} connected with sid {sid}")
    await sio.emit('connected', {'user_id': user['id'], 'username': user['username']}, to=sid)
    return True


@sio.event
async def disconnect(sid):
    """Handle client disconnection."""
    user_data = connected_users.pop(sid, None)
    if user_data:
        room_id = user_data.get('room_id')
        if room_id and room_id in room_users:
            room_users[room_id].discard(sid)
            
            # Notify room that user left
            await sio.emit('user_left', {
                'user_id': user_data['user_id'],
                'username': user_data['username']
            }, room=room_id)
        
        logger.info(f"User {user_data['username']} disconnected")


@sio.event
async def join_room(sid, data):
    """Handle user joining a chat room."""
    room_id = data.get('room_id')
    if not room_id:
        return {'error': 'Room ID required'}
    
    user_data = connected_users.get(sid)
    if not user_data:
        return {'error': 'Not authenticated'}
    
    # Leave previous room if any
    old_room = user_data.get('room_id')
    if old_room:
        sio.leave_room(sid, old_room)
        if old_room in room_users:
            room_users[old_room].discard(sid)
    
    # Join new room
    sio.enter_room(sid, room_id)
    user_data['room_id'] = room_id
    
    if room_id not in room_users:
        room_users[room_id] = set()
    room_users[room_id].add(sid)
    
    # Update room membership in DB
    await db.chat_rooms.update_one(
        {"id": room_id},
        {"$addToSet": {"members": user_data['user_id']}}
    )
    
    # Get recent messages
    messages = await db.chat_messages.find(
        {"room_id": room_id},
        {"_id": 0}
    ).sort("created_at", -1).limit(50).to_list(50)
    
    # Get room users count
    online_count = len(room_users.get(room_id, set()))
    
    # Notify room that user joined
    await sio.emit('user_joined', {
        'user_id': user_data['user_id'],
        'username': user_data['username'],
        'online_count': online_count
    }, room=room_id, skip_sid=sid)
    
    logger.info(f"User {user_data['username']} joined room {room_id}")
    
    return {
        'success': True,
        'room_id': room_id,
        'messages': list(reversed(messages)),
        'online_count': online_count
    }


@sio.event
async def leave_room(sid, data):
    """Handle user leaving a chat room."""
    room_id = data.get('room_id')
    user_data = connected_users.get(sid)
    
    if user_data and room_id:
        sio.leave_room(sid, room_id)
        user_data['room_id'] = None
        
        if room_id in room_users:
            room_users[room_id].discard(sid)
        
        await sio.emit('user_left', {
            'user_id': user_data['user_id'],
            'username': user_data['username'],
            'online_count': len(room_users.get(room_id, set()))
        }, room=room_id)
    
    return {'success': True}


@sio.event
async def send_message(sid, data):
    """Handle sending a message to a room."""
    content = data.get('content', '').strip()
    room_id = data.get('room_id')
    
    if not content:
        return {'error': 'Message content required'}
    
    user_data = connected_users.get(sid)
    if not user_data:
        return {'error': 'Not authenticated'}
    
    # Use current room if not specified
    if not room_id:
        room_id = user_data.get('room_id')
    
    if not room_id:
        return {'error': 'Not in a room'}
    
    # Create message
    message = {
        "id": str(uuid.uuid4()),
        "room_id": room_id,
        "user_id": user_data['user_id'],
        "username": user_data['username'],
        "content": content,
        "created_at": datetime.now(timezone.utc).isoformat()
    }
    
    # Save to database
    await db.chat_messages.insert_one(message)
    
    # Remove MongoDB _id before sending
    message_data = {k: v for k, v in message.items() if k != "_id"}
    
    # Broadcast to room
    await sio.emit('new_message', message_data, room=room_id)
    
    logger.info(f"Message from {user_data['username']} in room {room_id}: {content[:50]}...")
    
    return {'success': True, 'message': message_data}


@sio.event
async def typing(sid, data):
    """Handle typing indicator."""
    room_id = data.get('room_id')
    user_data = connected_users.get(sid)
    
    if user_data and room_id:
        await sio.emit('user_typing', {
            'user_id': user_data['user_id'],
            'username': user_data['username'],
            'is_typing': data.get('is_typing', True)
        }, room=room_id, skip_sid=sid)


@sio.event
async def get_online_users(sid, data):
    """Get list of online users in a room."""
    room_id = data.get('room_id')
    
    if not room_id or room_id not in room_users:
        return {'users': [], 'count': 0}
    
    users = []
    for user_sid in room_users[room_id]:
        user_data = connected_users.get(user_sid)
        if user_data:
            users.append({
                'user_id': user_data['user_id'],
                'username': user_data['username']
            })
    
    return {'users': users, 'count': len(users)}


# Create ASGI app for Socket.IO
socket_app = socketio.ASGIApp(sio, socketio_path='socket.io')
