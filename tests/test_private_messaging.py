"""
Private Messaging Feature Tests
Tests for: conversations, messages, user search, image attachments, email notifications
"""
import pytest
import requests
import os
import base64

BASE_URL = os.environ.get('REACT_APP_BACKEND_URL', '').rstrip('/')

# Test credentials
TEST_USER_1 = {"email": "john@infojet.com", "password": "password123"}
TEST_USER_2 = {"email": "testuser@example.com", "password": "password123"}
NEW_TEST_USER = {"username": "msgtest_user", "email": "msgtest@example.com", "password": "password123"}


class TestPrivateMessaging:
    """Private Messaging API Tests"""
    
    token_user1 = None
    token_user2 = None
    user1_id = None
    user2_id = None
    test_message_id = None
    test_conversation_id = None
    
    # ============================================
    # AUTHENTICATION TESTS
    # ============================================
    
    def test_01_login_user1(self):
        """Login as admin user (john@infojet.com)"""
        response = requests.post(f"{BASE_URL}/api/auth/login", json=TEST_USER_1)
        assert response.status_code == 200, f"Login failed: {response.text}"
        data = response.json()
        assert "access_token" in data
        TestPrivateMessaging.token_user1 = data["access_token"]
        TestPrivateMessaging.user1_id = data["user"]["id"]
        print(f"✓ User 1 logged in: {data['user']['username']} (ID: {data['user']['id']})")
    
    def test_02_login_or_create_user2(self):
        """Login or create second test user"""
        # Try login first
        response = requests.post(f"{BASE_URL}/api/auth/login", json=TEST_USER_2)
        if response.status_code == 200:
            data = response.json()
            TestPrivateMessaging.token_user2 = data["access_token"]
            TestPrivateMessaging.user2_id = data["user"]["id"]
            print(f"✓ User 2 logged in: {data['user']['username']} (ID: {data['user']['id']})")
            return
        
        # Create new user if login fails
        response = requests.post(f"{BASE_URL}/api/auth/register", json=NEW_TEST_USER)
        if response.status_code == 200:
            data = response.json()
            TestPrivateMessaging.token_user2 = data["access_token"]
            TestPrivateMessaging.user2_id = data["user"]["id"]
            print(f"✓ User 2 created: {data['user']['username']} (ID: {data['user']['id']})")
        else:
            # Try login with new user credentials
            response = requests.post(f"{BASE_URL}/api/auth/login", json={
                "email": NEW_TEST_USER["email"],
                "password": NEW_TEST_USER["password"]
            })
            assert response.status_code == 200, f"Failed to login/create user 2: {response.text}"
            data = response.json()
            TestPrivateMessaging.token_user2 = data["access_token"]
            TestPrivateMessaging.user2_id = data["user"]["id"]
            print(f"✓ User 2 logged in: {data['user']['username']} (ID: {data['user']['id']})")
    
    # ============================================
    # USER SEARCH TESTS
    # ============================================
    
    def test_03_search_users(self):
        """Test user search endpoint - GET /api/users/search"""
        headers = {"Authorization": f"Bearer {TestPrivateMessaging.token_user1}"}
        response = requests.get(f"{BASE_URL}/api/users/search?q=test", headers=headers)
        assert response.status_code == 200, f"User search failed: {response.text}"
        data = response.json()
        assert "users" in data
        print(f"✓ User search returned {len(data['users'])} users")
    
    def test_04_search_users_excludes_self(self):
        """Verify user search excludes the current user"""
        headers = {"Authorization": f"Bearer {TestPrivateMessaging.token_user1}"}
        response = requests.get(f"{BASE_URL}/api/users/search?q=john", headers=headers)
        assert response.status_code == 200
        data = response.json()
        # Current user should not appear in search results
        user_ids = [u["id"] for u in data["users"]]
        assert TestPrivateMessaging.user1_id not in user_ids, "Current user should not appear in search results"
        print("✓ User search correctly excludes current user")
    
    def test_05_search_users_requires_auth(self):
        """Verify user search requires authentication"""
        response = requests.get(f"{BASE_URL}/api/users/search?q=test")
        assert response.status_code == 401, "User search should require authentication"
        print("✓ User search correctly requires authentication")
    
    # ============================================
    # SEND MESSAGE TESTS
    # ============================================
    
    def test_06_send_message_text_only(self):
        """Test sending a text message - POST /api/messages/send"""
        headers = {"Authorization": f"Bearer {TestPrivateMessaging.token_user1}"}
        payload = {
            "recipient_id": TestPrivateMessaging.user2_id,
            "content": "TEST_Hello from messaging test! This is a test message."
        }
        response = requests.post(f"{BASE_URL}/api/messages/send", json=payload, headers=headers)
        assert response.status_code == 200, f"Send message failed: {response.text}"
        data = response.json()
        assert "data" in data
        assert data["data"]["content"] == payload["content"]
        assert data["data"]["sender_id"] == TestPrivateMessaging.user1_id
        assert data["data"]["recipient_id"] == TestPrivateMessaging.user2_id
        TestPrivateMessaging.test_message_id = data["data"]["id"]
        TestPrivateMessaging.test_conversation_id = data["data"]["conversation_id"]
        print(f"✓ Text message sent successfully (ID: {data['data']['id']})")
    
    def test_07_send_message_with_small_image(self):
        """Test sending a message with a small image (base64)"""
        headers = {"Authorization": f"Bearer {TestPrivateMessaging.token_user1}"}
        # Create a small test image (1x1 pixel PNG)
        small_image_base64 = "data:image/png;base64,iVBORw0KGgoAAAANSUhEUgAAAAEAAAABCAYAAAAfFcSJAAAADUlEQVR42mNk+M9QDwADhgGAWjR9awAAAABJRU5ErkJggg=="
        payload = {
            "recipient_id": TestPrivateMessaging.user2_id,
            "content": "TEST_Message with image attachment",
            "image_url": small_image_base64
        }
        response = requests.post(f"{BASE_URL}/api/messages/send", json=payload, headers=headers)
        assert response.status_code == 200, f"Send message with image failed: {response.text}"
        data = response.json()
        assert data["data"]["image_url"] == small_image_base64
        print("✓ Message with small image sent successfully")
    
    def test_08_send_message_image_too_large(self):
        """Test that images > 8MB are rejected"""
        headers = {"Authorization": f"Bearer {TestPrivateMessaging.token_user1}"}
        # Create a large fake base64 string (> 8MB)
        # 8MB = 8 * 1024 * 1024 = 8388608 bytes
        # Base64 encoding increases size by ~33%, so we need ~6.3MB of raw data
        large_data = "A" * (9 * 1024 * 1024)  # ~9MB of base64 data
        large_image_base64 = f"data:image/png;base64,{large_data}"
        payload = {
            "recipient_id": TestPrivateMessaging.user2_id,
            "content": "TEST_Message with large image",
            "image_url": large_image_base64
        }
        response = requests.post(f"{BASE_URL}/api/messages/send", json=payload, headers=headers)
        assert response.status_code == 400, f"Large image should be rejected: {response.text}"
        print("✓ Large image (>8MB) correctly rejected")
    
    def test_09_cannot_message_self(self):
        """Test that users cannot message themselves"""
        headers = {"Authorization": f"Bearer {TestPrivateMessaging.token_user1}"}
        payload = {
            "recipient_id": TestPrivateMessaging.user1_id,  # Same as sender
            "content": "TEST_Message to self"
        }
        response = requests.post(f"{BASE_URL}/api/messages/send", json=payload, headers=headers)
        assert response.status_code == 400, f"Should not be able to message self: {response.text}"
        assert "yourself" in response.json().get("detail", "").lower()
        print("✓ Cannot message self - correctly returns 400")
    
    def test_10_cannot_message_nonexistent_user(self):
        """Test messaging a non-existent user"""
        headers = {"Authorization": f"Bearer {TestPrivateMessaging.token_user1}"}
        payload = {
            "recipient_id": "nonexistent-user-id-12345",
            "content": "TEST_Message to nobody"
        }
        response = requests.post(f"{BASE_URL}/api/messages/send", json=payload, headers=headers)
        assert response.status_code == 404, f"Should return 404 for nonexistent user: {response.text}"
        print("✓ Messaging nonexistent user correctly returns 404")
    
    # ============================================
    # GET CONVERSATIONS TESTS
    # ============================================
    
    def test_11_get_conversations_list(self):
        """Test getting conversations list - GET /api/messages/conversations"""
        headers = {"Authorization": f"Bearer {TestPrivateMessaging.token_user1}"}
        response = requests.get(f"{BASE_URL}/api/messages/conversations", headers=headers)
        assert response.status_code == 200, f"Get conversations failed: {response.text}"
        data = response.json()
        assert "conversations" in data
        assert len(data["conversations"]) > 0, "Should have at least one conversation"
        
        # Verify conversation structure
        conv = data["conversations"][0]
        assert "id" in conv
        assert "participants" in conv
        assert "participant_usernames" in conv
        assert "last_message" in conv
        print(f"✓ Got {len(data['conversations'])} conversations")
    
    def test_12_get_conversation_messages(self):
        """Test getting messages in a conversation - GET /api/messages/conversation/{other_user_id}"""
        headers = {"Authorization": f"Bearer {TestPrivateMessaging.token_user1}"}
        response = requests.get(
            f"{BASE_URL}/api/messages/conversation/{TestPrivateMessaging.user2_id}",
            headers=headers
        )
        assert response.status_code == 200, f"Get conversation messages failed: {response.text}"
        data = response.json()
        assert "messages" in data
        assert "other_user" in data
        assert "conversation_id" in data
        assert len(data["messages"]) > 0, "Should have at least one message"
        print(f"✓ Got {len(data['messages'])} messages in conversation")
    
    # ============================================
    # UNREAD COUNT TESTS
    # ============================================
    
    def test_13_get_unread_count(self):
        """Test getting unread message count - GET /api/messages/unread-count"""
        headers = {"Authorization": f"Bearer {TestPrivateMessaging.token_user2}"}
        response = requests.get(f"{BASE_URL}/api/messages/unread-count", headers=headers)
        assert response.status_code == 200, f"Get unread count failed: {response.text}"
        data = response.json()
        assert "unread_count" in data
        assert isinstance(data["unread_count"], int)
        print(f"✓ Unread count for user 2: {data['unread_count']}")
    
    # ============================================
    # MARK AS READ TESTS
    # ============================================
    
    def test_14_mark_conversation_as_read(self):
        """Test marking conversation as read - PUT /api/messages/mark-read/{conversation_id}"""
        headers = {"Authorization": f"Bearer {TestPrivateMessaging.token_user2}"}
        response = requests.put(
            f"{BASE_URL}/api/messages/mark-read/{TestPrivateMessaging.test_conversation_id}",
            headers=headers
        )
        assert response.status_code == 200, f"Mark as read failed: {response.text}"
        data = response.json()
        assert "count" in data
        print(f"✓ Marked {data['count']} messages as read")
    
    # ============================================
    # DELETE MESSAGE TESTS
    # ============================================
    
    def test_15_delete_own_message(self):
        """Test deleting own message - DELETE /api/messages/{message_id}"""
        # First send a message to delete
        headers = {"Authorization": f"Bearer {TestPrivateMessaging.token_user1}"}
        payload = {
            "recipient_id": TestPrivateMessaging.user2_id,
            "content": "TEST_Message to be deleted"
        }
        response = requests.post(f"{BASE_URL}/api/messages/send", json=payload, headers=headers)
        assert response.status_code == 200
        message_id = response.json()["data"]["id"]
        
        # Now delete it
        response = requests.delete(f"{BASE_URL}/api/messages/{message_id}", headers=headers)
        assert response.status_code == 200, f"Delete message failed: {response.text}"
        print("✓ Successfully deleted own message")
    
    def test_16_cannot_delete_others_message(self):
        """Test that users cannot delete others' messages"""
        # User 2 tries to delete User 1's message
        headers = {"Authorization": f"Bearer {TestPrivateMessaging.token_user2}"}
        response = requests.delete(
            f"{BASE_URL}/api/messages/{TestPrivateMessaging.test_message_id}",
            headers=headers
        )
        assert response.status_code == 403, f"Should not be able to delete others' messages: {response.text}"
        print("✓ Cannot delete others' messages - correctly returns 403")
    
    def test_17_delete_nonexistent_message(self):
        """Test deleting a non-existent message"""
        headers = {"Authorization": f"Bearer {TestPrivateMessaging.token_user1}"}
        response = requests.delete(
            f"{BASE_URL}/api/messages/nonexistent-message-id",
            headers=headers
        )
        assert response.status_code == 404, f"Should return 404 for nonexistent message: {response.text}"
        print("✓ Deleting nonexistent message correctly returns 404")
    
    # ============================================
    # BIDIRECTIONAL MESSAGING TESTS
    # ============================================
    
    def test_18_user2_can_reply(self):
        """Test that user 2 can reply to user 1"""
        headers = {"Authorization": f"Bearer {TestPrivateMessaging.token_user2}"}
        payload = {
            "recipient_id": TestPrivateMessaging.user1_id,
            "content": "TEST_Reply from user 2!"
        }
        response = requests.post(f"{BASE_URL}/api/messages/send", json=payload, headers=headers)
        assert response.status_code == 200, f"User 2 reply failed: {response.text}"
        data = response.json()
        # Should use same conversation ID
        assert data["data"]["conversation_id"] == TestPrivateMessaging.test_conversation_id
        print("✓ User 2 can reply in same conversation")
    
    def test_19_conversation_shows_both_users_messages(self):
        """Verify conversation contains messages from both users"""
        headers = {"Authorization": f"Bearer {TestPrivateMessaging.token_user1}"}
        response = requests.get(
            f"{BASE_URL}/api/messages/conversation/{TestPrivateMessaging.user2_id}",
            headers=headers
        )
        assert response.status_code == 200
        data = response.json()
        
        # Check for messages from both users
        sender_ids = set(msg["sender_id"] for msg in data["messages"])
        assert TestPrivateMessaging.user1_id in sender_ids, "Should have messages from user 1"
        assert TestPrivateMessaging.user2_id in sender_ids, "Should have messages from user 2"
        print("✓ Conversation contains messages from both users")
    
    # ============================================
    # AUTHENTICATION REQUIRED TESTS
    # ============================================
    
    def test_20_endpoints_require_auth(self):
        """Verify all messaging endpoints require authentication"""
        endpoints = [
            ("GET", f"{BASE_URL}/api/messages/conversations"),
            ("GET", f"{BASE_URL}/api/messages/conversation/some-id"),
            ("POST", f"{BASE_URL}/api/messages/send"),
            ("GET", f"{BASE_URL}/api/messages/unread-count"),
            ("PUT", f"{BASE_URL}/api/messages/mark-read/some-id"),
            ("DELETE", f"{BASE_URL}/api/messages/some-id"),
        ]
        
        for method, url in endpoints:
            if method == "GET":
                response = requests.get(url)
            elif method == "POST":
                response = requests.post(url, json={"recipient_id": "x", "content": "x"})
            elif method == "PUT":
                response = requests.put(url)
            elif method == "DELETE":
                response = requests.delete(url)
            
            assert response.status_code == 401, f"{method} {url} should require auth"
        
        print("✓ All messaging endpoints require authentication")


# Run tests
if __name__ == "__main__":
    pytest.main([__file__, "-v", "--tb=short"])
