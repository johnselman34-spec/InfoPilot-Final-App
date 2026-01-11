"""
InfoPilot Explorer - Real-time Notifications with WebSockets
"""
from fastapi import APIRouter, WebSocket, WebSocketDisconnect, Depends, HTTPException
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
from datetime import datetime
from typing import Dict, List, Set
from bson import ObjectId
import asyncio
import json

from config import db, logger

router = APIRouter(tags=["Notifications"])
security = HTTPBearer(auto_error=False)


class ConnectionManager:
    """Manages WebSocket connections for real-time notifications"""
    
    def __init__(self):
        # Map user_id to set of WebSocket connections
        self.active_connections: Dict[str, Set[WebSocket]] = {}
        self.user_websockets: Dict[WebSocket, str] = {}
    
    async def connect(self, websocket: WebSocket, user_id: str):
        """Accept a new WebSocket connection"""
        await websocket.accept()
        
        if user_id not in self.active_connections:
            self.active_connections[user_id] = set()
        
        self.active_connections[user_id].add(websocket)
        self.user_websockets[websocket] = user_id
        logger.info(f"WebSocket connected for user {user_id}")
    
    def disconnect(self, websocket: WebSocket):
        """Remove a WebSocket connection"""
        user_id = self.user_websockets.get(websocket)
        if user_id and user_id in self.active_connections:
            self.active_connections[user_id].discard(websocket)
            if not self.active_connections[user_id]:
                del self.active_connections[user_id]
        
        if websocket in self.user_websockets:
            del self.user_websockets[websocket]
        
        logger.info(f"WebSocket disconnected for user {user_id}")
    
    async def send_to_user(self, user_id: str, message: dict):
        """Send a message to all connections of a specific user"""
        if user_id in self.active_connections:
            disconnected = set()
            for websocket in self.active_connections[user_id]:
                try:
                    await websocket.send_json(message)
                except Exception as e:
                    logger.error(f"Error sending to websocket: {e}")
                    disconnected.add(websocket)
            
            # Clean up disconnected sockets
            for ws in disconnected:
                self.disconnect(ws)
    
    async def broadcast_to_users(self, user_ids: List[str], message: dict):
        """Broadcast a message to multiple users"""
        for user_id in user_ids:
            await self.send_to_user(user_id, message)
    
    def get_online_users(self) -> List[str]:
        """Get list of currently online user IDs"""
        return list(self.active_connections.keys())


# Global connection manager
manager = ConnectionManager()


async def get_user_from_token(token: str):
    """Validate token and return user"""
    if not token:
        return None
    
    session = await db.sessions.find_one({"token": token})
    if not session:
        return None
    
    if session.get("expires_at") and session["expires_at"] < datetime.utcnow():
        return None
    
    user = await db.users.find_one({"_id": ObjectId(session["user_id"])})
    return user


@router.websocket("/ws/notifications")
async def websocket_notifications(websocket: WebSocket, token: str = None):
    """
    WebSocket endpoint for real-time notifications
    Connect with: ws://host/api/ws/notifications?token=YOUR_TOKEN
    """
    # Authenticate user
    user = await get_user_from_token(token)
    if not user:
        await websocket.close(code=4001, reason="Invalid or missing token")
        return
    
    user_id = str(user["_id"])
    
    await manager.connect(websocket, user_id)
    
    try:
        # Send initial connection success message
        await websocket.send_json({
            "type": "connected",
            "message": "Connected to notifications",
            "user_id": user_id,
            "timestamp": datetime.utcnow().isoformat()
        })
        
        # Send unread notification count on connect
        unread_count = await db.notifications.count_documents({
            "user_id": user_id,
            "read": False
        })
        await websocket.send_json({
            "type": "unread_count",
            "count": unread_count
        })
        
        # Keep connection alive and listen for messages
        while True:
            try:
                # Wait for messages (ping/pong or commands)
                data = await asyncio.wait_for(websocket.receive_text(), timeout=30)
                
                # Handle ping
                if data == "ping":
                    await websocket.send_text("pong")
                elif data.startswith("{"):
                    # Handle JSON commands
                    try:
                        cmd = json.loads(data)
                        if cmd.get("action") == "mark_read":
                            notification_id = cmd.get("notification_id")
                            if notification_id:
                                await db.notifications.update_one(
                                    {"_id": ObjectId(notification_id), "user_id": user_id},
                                    {"$set": {"read": True}}
                                )
                                await websocket.send_json({"type": "marked_read", "id": notification_id})
                        elif cmd.get("action") == "mark_all_read":
                            await db.notifications.update_many(
                                {"user_id": user_id, "read": False},
                                {"$set": {"read": True}}
                            )
                            await websocket.send_json({"type": "all_marked_read"})
                    except json.JSONDecodeError:
                        pass
                        
            except asyncio.TimeoutError:
                # Send ping to keep connection alive
                try:
                    await websocket.send_text("ping")
                except Exception:
                    break
                    
    except WebSocketDisconnect:
        manager.disconnect(websocket)
    except Exception as e:
        logger.error(f"WebSocket error: {e}")
        manager.disconnect(websocket)


# ==================== NOTIFICATION HELPERS ====================

async def create_notification(
    user_id: str,
    notification_type: str,
    title: str,
    message: str,
    link: str = None,
    data: dict = None
):
    """Create a notification and send it via WebSocket if user is online"""
    notification = {
        "user_id": user_id,
        "type": notification_type,
        "title": title,
        "message": message,
        "link": link,
        "data": data or {},
        "read": False,
        "created_at": datetime.utcnow()
    }
    
    result = await db.notifications.insert_one(notification)
    notification["id"] = str(result.inserted_id)
    if "_id" in notification:
        del notification["_id"]
    
    # Send via WebSocket if user is online
    ws_message = {
        "type": "notification",
        "notification": {
            "id": notification["id"],
            "type": notification_type,
            "title": title,
            "message": message,
            "link": link,
            "data": data or {},
            "created_at": notification["created_at"].isoformat()
        }
    }
    
    await manager.send_to_user(user_id, ws_message)
    
    return notification


async def notify_friend_request(from_user: dict, to_user_id: str):
    """Send notification for new friend request"""
    await create_notification(
        user_id=to_user_id,
        notification_type="friend_request",
        title="New Friend Request",
        message=f"{from_user.get('username', 'Someone')} sent you a friend request",
        link="/social",
        data={"from_user_id": str(from_user["_id"])}
    )


async def notify_friend_accepted(from_user: dict, to_user_id: str):
    """Send notification when friend request is accepted"""
    await create_notification(
        user_id=to_user_id,
        notification_type="friend_accepted",
        title="Friend Request Accepted",
        message=f"{from_user.get('username', 'Someone')} accepted your friend request",
        link="/social",
        data={"user_id": str(from_user["_id"])}
    )


async def notify_new_message(from_user: dict, to_user_id: str):
    """Send notification for new message"""
    await create_notification(
        user_id=to_user_id,
        notification_type="new_message",
        title="New Message",
        message=f"New message from {from_user.get('username', 'Someone')}",
        link="/messages",
        data={"from_user_id": str(from_user["_id"])}
    )


async def notify_post_like(liker: dict, post_author_id: str, post_id: str):
    """Send notification when someone likes a post"""
    if str(liker["_id"]) == post_author_id:
        return  # Don't notify self-likes
    
    await create_notification(
        user_id=post_author_id,
        notification_type="post_like",
        title="Post Liked",
        message=f"{liker.get('username', 'Someone')} liked your post",
        link="/social",
        data={"post_id": post_id, "liker_id": str(liker["_id"])}
    )


async def notify_post_comment(commenter: dict, post_author_id: str, post_id: str):
    """Send notification when someone comments on a post"""
    if str(commenter["_id"]) == post_author_id:
        return  # Don't notify self-comments
    
    await create_notification(
        user_id=post_author_id,
        notification_type="post_comment",
        title="New Comment",
        message=f"{commenter.get('username', 'Someone')} commented on your post",
        link="/social",
        data={"post_id": post_id, "commenter_id": str(commenter["_id"])}
    )


async def notify_group_join(joiner: dict, group: dict):
    """Send notification when someone joins a group"""
    creator_id = group.get("created_by")
    if creator_id and str(joiner["_id"]) != creator_id:
        await create_notification(
            user_id=creator_id,
            notification_type="group_join",
            title="New Group Member",
            message=f"{joiner.get('username', 'Someone')} joined your group '{group.get('name', 'your group')}'",
            link="/social",
            data={"group_id": str(group["_id"]), "joiner_id": str(joiner["_id"])}
        )


async def notify_protocol_purchase(buyer: dict, protocol: dict, seller_id: str):
    """Send notification when someone purchases a protocol"""
    await create_notification(
        user_id=seller_id,
        notification_type="protocol_sale",
        title="Protocol Sold!",
        message=f"{buyer.get('username', 'Someone')} purchased your protocol '{protocol.get('name', '')}'",
        link="/marketplace",
        data={"protocol_id": str(protocol["_id"]), "buyer_id": str(buyer["_id"])}
    )


async def notify_badge_earned(user_id: str, badge_name: str, badge_icon: str):
    """Send notification when user earns a badge"""
    await create_notification(
        user_id=user_id,
        notification_type="badge_earned",
        title="Badge Earned!",
        message=f"Congratulations! You earned the '{badge_name}' badge {badge_icon}",
        link="/achievements",
        data={"badge_name": badge_name}
    )


async def notify_level_up(user_id: str, new_level: int):
    """Send notification when user levels up"""
    await create_notification(
        user_id=user_id,
        notification_type="level_up",
        title="Level Up!",
        message=f"Congratulations! You reached Level {new_level}!",
        link="/achievements",
        data={"level": new_level}
    )


# ==================== REST API ENDPOINTS ====================

@router.get("/notifications")
async def get_notifications(
    limit: int = 50,
    unread_only: bool = False,
    credentials: HTTPAuthorizationCredentials = Depends(security)
):
    """Get user's notifications"""
    if not credentials:
        raise HTTPException(status_code=401, detail="Not authenticated")
    
    user = await get_user_from_token(credentials.credentials)
    if not user:
        raise HTTPException(status_code=401, detail="Invalid token")
    
    user_id = str(user["_id"])
    
    query = {"user_id": user_id}
    if unread_only:
        query["read"] = False
    
    notifications = await db.notifications.find(query).sort("created_at", -1).limit(limit).to_list(limit)
    
    return {
        "notifications": [{
            "id": str(n["_id"]),
            "type": n["type"],
            "title": n["title"],
            "message": n["message"],
            "link": n.get("link"),
            "data": n.get("data", {}),
            "read": n["read"],
            "created_at": n["created_at"].isoformat()
        } for n in notifications]
    }


@router.get("/notifications/unread-count")
async def get_unread_count(credentials: HTTPAuthorizationCredentials = Depends(security)):
    """Get count of unread notifications"""
    if not credentials:
        raise HTTPException(status_code=401, detail="Not authenticated")
    
    user = await get_user_from_token(credentials.credentials)
    if not user:
        raise HTTPException(status_code=401, detail="Invalid token")
    
    count = await db.notifications.count_documents({
        "user_id": str(user["_id"]),
        "read": False
    })
    
    return {"count": count}


@router.post("/notifications/{notification_id}/read")
async def mark_notification_read(
    notification_id: str,
    credentials: HTTPAuthorizationCredentials = Depends(security)
):
    """Mark a notification as read"""
    if not credentials:
        raise HTTPException(status_code=401, detail="Not authenticated")
    
    user = await get_user_from_token(credentials.credentials)
    if not user:
        raise HTTPException(status_code=401, detail="Invalid token")
    
    result = await db.notifications.update_one(
        {"_id": ObjectId(notification_id), "user_id": str(user["_id"])},
        {"$set": {"read": True}}
    )
    
    if result.modified_count == 0:
        raise HTTPException(status_code=404, detail="Notification not found")
    
    return {"success": True}


@router.post("/notifications/mark-all-read")
async def mark_all_read(credentials: HTTPAuthorizationCredentials = Depends(security)):
    """Mark all notifications as read"""
    if not credentials:
        raise HTTPException(status_code=401, detail="Not authenticated")
    
    user = await get_user_from_token(credentials.credentials)
    if not user:
        raise HTTPException(status_code=401, detail="Invalid token")
    
    result = await db.notifications.update_many(
        {"user_id": str(user["_id"]), "read": False},
        {"$set": {"read": True}}
    )
    
    return {"success": True, "marked_count": result.modified_count}


@router.delete("/notifications/{notification_id}")
async def delete_notification(
    notification_id: str,
    credentials: HTTPAuthorizationCredentials = Depends(security)
):
    """Delete a notification"""
    if not credentials:
        raise HTTPException(status_code=401, detail="Not authenticated")
    
    user = await get_user_from_token(credentials.credentials)
    if not user:
        raise HTTPException(status_code=401, detail="Invalid token")
    
    result = await db.notifications.delete_one({
        "_id": ObjectId(notification_id),
        "user_id": str(user["_id"])
    })
    
    if result.deleted_count == 0:
        raise HTTPException(status_code=404, detail="Notification not found")
    
    return {"success": True}


@router.get("/notifications/online-status")
async def get_online_status(user_ids: str = None):
    """Check which users are currently online (comma-separated IDs)"""
    if not user_ids:
        return {"online_users": []}
    
    requested_ids = user_ids.split(",")
    online_ids = manager.get_online_users()
    
    return {
        "online_users": [uid for uid in requested_ids if uid in online_ids]
    }


# ==================== PUSH NOTIFICATION ENDPOINTS ====================

class PushSubscriptionData(BaseModel):
    """Push subscription data from browser"""
    subscription: dict

@router.post("/push/subscribe")
async def subscribe_push(
    data: PushSubscriptionData,
    credentials: HTTPAuthorizationCredentials = Depends(security)
):
    """Subscribe to push notifications"""
    if not credentials:
        raise HTTPException(status_code=401, detail="Not authenticated")
    
    user = await get_user_from_token(credentials.credentials)
    if not user:
        raise HTTPException(status_code=401, detail="Invalid token")
    
    user_id = str(user["_id"])
    
    # Store or update push subscription
    await db.push_subscriptions.update_one(
        {"user_id": user_id},
        {
            "$set": {
                "user_id": user_id,
                "subscription": data.subscription,
                "updated_at": datetime.utcnow()
            }
        },
        upsert=True
    )
    
    return {"success": True, "message": "Push subscription saved"}


@router.post("/push/unsubscribe")
async def unsubscribe_push(credentials: HTTPAuthorizationCredentials = Depends(security)):
    """Unsubscribe from push notifications"""
    if not credentials:
        raise HTTPException(status_code=401, detail="Not authenticated")
    
    user = await get_user_from_token(credentials.credentials)
    if not user:
        raise HTTPException(status_code=401, detail="Invalid token")
    
    await db.push_subscriptions.delete_one({"user_id": str(user["_id"])})
    
    return {"success": True, "message": "Push subscription removed"}


@router.post("/push/test")
async def send_test_push(credentials: HTTPAuthorizationCredentials = Depends(security)):
    """Send a test push notification to the user"""
    if not credentials:
        raise HTTPException(status_code=401, detail="Not authenticated")
    
    user = await get_user_from_token(credentials.credentials)
    if not user:
        raise HTTPException(status_code=401, detail="Invalid token")
    
    # Create a test notification in the database
    await create_notification(
        user_id=str(user["_id"]),
        notification_type="test",
        title="Test Notification",
        message="Push notifications are working! You'll receive alerts for important updates.",
        link="/settings",
        data={"test": True}
    )
    
    return {"success": True, "message": "Test notification sent"}


@router.get("/push/status")
async def get_push_status(credentials: HTTPAuthorizationCredentials = Depends(security)):
    """Get user's push notification subscription status"""
    if not credentials:
        raise HTTPException(status_code=401, detail="Not authenticated")
    
    user = await get_user_from_token(credentials.credentials)
    if not user:
        raise HTTPException(status_code=401, detail="Invalid token")
    
    subscription = await db.push_subscriptions.find_one({"user_id": str(user["_id"])})
    
    return {
        "subscribed": subscription is not None,
        "updated_at": subscription["updated_at"].isoformat() if subscription else None
    }


from pydantic import BaseModel
