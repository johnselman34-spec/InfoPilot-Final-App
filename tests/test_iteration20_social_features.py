"""
Iteration 20 - Social Features, Direct Messaging, Newsletter, Voice Search Tests
Tests for: Friends, Groups, Pages, Posts, Reactions, DM Conversations, Newsletter APIs
"""
import pytest
import requests
import os
import time

BASE_URL = os.environ.get('REACT_APP_BACKEND_URL', 'https://info-pilot.preview.emergentagent.com')

# Test credentials
ADMIN_EMAIL = "jjspilot24@gmail.com"
ADMIN_PASSWORD = "InfoPilot2024!"
TEST_EMAIL = "testuser@example.com"
TEST_PASSWORD = "password123"


class TestAuthentication:
    """Authentication tests"""
    
    @pytest.fixture(scope="class")
    def admin_token(self):
        """Get admin auth token"""
        response = requests.post(f"{BASE_URL}/api/auth/login", json={
            "email": ADMIN_EMAIL,
            "password": ADMIN_PASSWORD
        })
        if response.status_code == 200:
            return response.json().get("token")
        pytest.skip("Admin authentication failed")
    
    def test_admin_login(self):
        """Test admin login"""
        response = requests.post(f"{BASE_URL}/api/auth/login", json={
            "email": ADMIN_EMAIL,
            "password": ADMIN_PASSWORD
        })
        assert response.status_code == 200
        data = response.json()
        assert "token" in data
        assert "user" in data


class TestFriendsAPI:
    """Friends system API tests"""
    
    @pytest.fixture(scope="class")
    def auth_token(self):
        """Get auth token"""
        response = requests.post(f"{BASE_URL}/api/auth/login", json={
            "email": ADMIN_EMAIL,
            "password": ADMIN_PASSWORD
        })
        if response.status_code == 200:
            return response.json().get("token")
        pytest.skip("Authentication failed")
    
    def test_get_friends_list(self, auth_token):
        """Test GET /api/friends - returns friends list"""
        response = requests.get(
            f"{BASE_URL}/api/friends",
            headers={"Authorization": f"Bearer {auth_token}"}
        )
        assert response.status_code == 200
        data = response.json()
        assert "friends" in data
        assert isinstance(data["friends"], list)
    
    def test_get_friend_requests(self, auth_token):
        """Test GET /api/friends/requests - returns pending requests"""
        response = requests.get(
            f"{BASE_URL}/api/friends/requests",
            headers={"Authorization": f"Bearer {auth_token}"}
        )
        assert response.status_code == 200
        data = response.json()
        assert "incoming" in data
        assert "outgoing" in data
    
    def test_search_users(self, auth_token):
        """Test GET /api/friends/search - search for users"""
        response = requests.get(
            f"{BASE_URL}/api/friends/search?q=test",
            headers={"Authorization": f"Bearer {auth_token}"}
        )
        assert response.status_code == 200
        data = response.json()
        assert "users" in data
        assert isinstance(data["users"], list)


class TestGroupsAPI:
    """Groups API tests"""
    
    @pytest.fixture(scope="class")
    def auth_token(self):
        """Get auth token"""
        response = requests.post(f"{BASE_URL}/api/auth/login", json={
            "email": ADMIN_EMAIL,
            "password": ADMIN_PASSWORD
        })
        if response.status_code == 200:
            return response.json().get("token")
        pytest.skip("Authentication failed")
    
    def test_get_groups_list(self, auth_token):
        """Test GET /api/groups - returns groups list"""
        response = requests.get(
            f"{BASE_URL}/api/groups",
            headers={"Authorization": f"Bearer {auth_token}"}
        )
        assert response.status_code == 200
        data = response.json()
        assert "groups" in data
        assert isinstance(data["groups"], list)
    
    def test_create_group(self, auth_token):
        """Test POST /api/groups - create a new group"""
        response = requests.post(
            f"{BASE_URL}/api/groups",
            headers={
                "Authorization": f"Bearer {auth_token}",
                "Content-Type": "application/json"
            },
            json={
                "name": f"TEST_Group_{int(time.time())}",
                "description": "Test group for iteration 20",
                "is_private": False
            }
        )
        assert response.status_code == 200
        data = response.json()
        assert "id" in data
        assert "name" in data
        
        # Store group ID for cleanup
        return data["id"]
    
    def test_get_groups_returns_created_group(self, auth_token):
        """Verify created group appears in list"""
        # Create a group first
        create_response = requests.post(
            f"{BASE_URL}/api/groups",
            headers={
                "Authorization": f"Bearer {auth_token}",
                "Content-Type": "application/json"
            },
            json={
                "name": f"TEST_Verify_Group_{int(time.time())}",
                "description": "Verification test group",
                "is_private": False
            }
        )
        assert create_response.status_code == 200
        group_id = create_response.json()["id"]
        
        # Verify it appears in list
        list_response = requests.get(
            f"{BASE_URL}/api/groups",
            headers={"Authorization": f"Bearer {auth_token}"}
        )
        assert list_response.status_code == 200
        groups = list_response.json()["groups"]
        group_ids = [g["id"] for g in groups]
        assert group_id in group_ids


class TestPagesAPI:
    """Pages API tests"""
    
    @pytest.fixture(scope="class")
    def auth_token(self):
        """Get auth token"""
        response = requests.post(f"{BASE_URL}/api/auth/login", json={
            "email": ADMIN_EMAIL,
            "password": ADMIN_PASSWORD
        })
        if response.status_code == 200:
            return response.json().get("token")
        pytest.skip("Authentication failed")
    
    def test_get_pages_list(self, auth_token):
        """Test GET /api/pages - returns pages list"""
        response = requests.get(
            f"{BASE_URL}/api/pages",
            headers={"Authorization": f"Bearer {auth_token}"}
        )
        assert response.status_code == 200
        data = response.json()
        assert "pages" in data
        assert isinstance(data["pages"], list)
    
    def test_create_page(self, auth_token):
        """Test POST /api/pages - create a new page"""
        response = requests.post(
            f"{BASE_URL}/api/pages",
            headers={
                "Authorization": f"Bearer {auth_token}",
                "Content-Type": "application/json"
            },
            json={
                "name": f"TEST_Page_{int(time.time())}",
                "description": "Test page for iteration 20",
                "category": "Technology"
            }
        )
        assert response.status_code == 200
        data = response.json()
        assert "id" in data
        assert "name" in data
    
    def test_get_pages_returns_created_page(self, auth_token):
        """Verify created page appears in list"""
        # Create a page first
        create_response = requests.post(
            f"{BASE_URL}/api/pages",
            headers={
                "Authorization": f"Bearer {auth_token}",
                "Content-Type": "application/json"
            },
            json={
                "name": f"TEST_Verify_Page_{int(time.time())}",
                "description": "Verification test page",
                "category": "General"
            }
        )
        assert create_response.status_code == 200
        page_id = create_response.json()["id"]
        
        # Verify it appears in list
        list_response = requests.get(
            f"{BASE_URL}/api/pages",
            headers={"Authorization": f"Bearer {auth_token}"}
        )
        assert list_response.status_code == 200
        pages = list_response.json()["pages"]
        page_ids = [p["id"] for p in pages]
        assert page_id in page_ids


class TestFeedAPI:
    """Feed/Posts API tests"""
    
    @pytest.fixture(scope="class")
    def auth_token(self):
        """Get auth token"""
        response = requests.post(f"{BASE_URL}/api/auth/login", json={
            "email": ADMIN_EMAIL,
            "password": ADMIN_PASSWORD
        })
        if response.status_code == 200:
            return response.json().get("token")
        pytest.skip("Authentication failed")
    
    def test_get_feed(self, auth_token):
        """Test GET /api/feed - returns feed posts"""
        response = requests.get(
            f"{BASE_URL}/api/feed",
            headers={"Authorization": f"Bearer {auth_token}"}
        )
        assert response.status_code == 200
        data = response.json()
        assert "posts" in data
        assert isinstance(data["posts"], list)
    
    def test_create_post(self, auth_token):
        """Test POST /api/posts - create a new post"""
        response = requests.post(
            f"{BASE_URL}/api/posts",
            headers={
                "Authorization": f"Bearer {auth_token}",
                "Content-Type": "application/json"
            },
            json={
                "content": f"TEST_Post content for iteration 20 - {int(time.time())}"
            }
        )
        assert response.status_code == 200
        data = response.json()
        assert "id" in data
    
    def test_get_posts(self, auth_token):
        """Test GET /api/posts - returns posts list"""
        response = requests.get(
            f"{BASE_URL}/api/posts",
            headers={"Authorization": f"Bearer {auth_token}"}
        )
        assert response.status_code == 200
        data = response.json()
        assert "posts" in data


class TestDirectMessagesAPI:
    """Direct Messages API tests"""
    
    @pytest.fixture(scope="class")
    def auth_token(self):
        """Get auth token"""
        response = requests.post(f"{BASE_URL}/api/auth/login", json={
            "email": ADMIN_EMAIL,
            "password": ADMIN_PASSWORD
        })
        if response.status_code == 200:
            return response.json().get("token")
        pytest.skip("Authentication failed")
    
    def test_get_dm_conversations(self, auth_token):
        """Test GET /api/dm/conversations - returns DM conversations"""
        response = requests.get(
            f"{BASE_URL}/api/dm/conversations",
            headers={"Authorization": f"Bearer {auth_token}"}
        )
        assert response.status_code == 200
        data = response.json()
        assert "conversations" in data
        assert isinstance(data["conversations"], list)
    
    def test_get_online_friends(self, auth_token):
        """Test GET /api/dm/online - returns online friends"""
        response = requests.get(
            f"{BASE_URL}/api/dm/online",
            headers={"Authorization": f"Bearer {auth_token}"}
        )
        assert response.status_code == 200
        data = response.json()
        assert "online_friends" in data


class TestNewsletterAPI:
    """Newsletter API tests (admin only)"""
    
    @pytest.fixture(scope="class")
    def admin_token(self):
        """Get admin auth token"""
        response = requests.post(f"{BASE_URL}/api/auth/login", json={
            "email": ADMIN_EMAIL,
            "password": ADMIN_PASSWORD
        })
        if response.status_code == 200:
            return response.json().get("token")
        pytest.skip("Admin authentication failed")
    
    def test_get_newsletter_subscribers(self, admin_token):
        """Test GET /api/newsletter/subscribers - admin only"""
        response = requests.get(
            f"{BASE_URL}/api/newsletter/subscribers",
            headers={"Authorization": f"Bearer {admin_token}"}
        )
        assert response.status_code == 200
        data = response.json()
        assert "subscribers" in data
        assert "total" in data
    
    def test_get_newsletter_drafts(self, admin_token):
        """Test GET /api/newsletter/drafts - admin only"""
        response = requests.get(
            f"{BASE_URL}/api/newsletter/drafts",
            headers={"Authorization": f"Bearer {admin_token}"}
        )
        assert response.status_code == 200
        data = response.json()
        assert "drafts" in data
    
    def test_get_newsletter_campaigns(self, admin_token):
        """Test GET /api/newsletter/campaigns - admin only"""
        response = requests.get(
            f"{BASE_URL}/api/newsletter/campaigns",
            headers={"Authorization": f"Bearer {admin_token}"}
        )
        assert response.status_code == 200
        data = response.json()
        assert "campaigns" in data


class TestVoiceSearchAPI:
    """Voice Search API tests"""
    
    @pytest.fixture(scope="class")
    def auth_token(self):
        """Get auth token"""
        response = requests.post(f"{BASE_URL}/api/auth/login", json={
            "email": ADMIN_EMAIL,
            "password": ADMIN_PASSWORD
        })
        if response.status_code == 200:
            return response.json().get("token")
        pytest.skip("Authentication failed")
    
    def test_get_voice_history(self, auth_token):
        """Test GET /api/voice/history - returns voice search history"""
        response = requests.get(
            f"{BASE_URL}/api/voice/history",
            headers={"Authorization": f"Bearer {auth_token}"}
        )
        assert response.status_code == 200
        data = response.json()
        assert "searches" in data


class TestCollaborateAPI:
    """Collaborative Protocol Editing API tests"""
    
    @pytest.fixture(scope="class")
    def auth_token(self):
        """Get auth token"""
        response = requests.post(f"{BASE_URL}/api/auth/login", json={
            "email": ADMIN_EMAIL,
            "password": ADMIN_PASSWORD
        })
        if response.status_code == 200:
            return response.json().get("token")
        pytest.skip("Authentication failed")
    
    def test_get_collaborate_sessions(self, auth_token):
        """Test GET /api/collaborate/sessions - returns collaboration sessions"""
        response = requests.get(
            f"{BASE_URL}/api/collaborate/sessions",
            headers={"Authorization": f"Bearer {auth_token}"}
        )
        # May return 200 or 404 if no sessions exist
        assert response.status_code in [200, 404]


class TestHealthAndBasicEndpoints:
    """Basic health and endpoint tests"""
    
    def test_health_endpoint(self):
        """Test /api/health endpoint"""
        response = requests.get(f"{BASE_URL}/api/health")
        assert response.status_code == 200
        data = response.json()
        assert data.get("status") == "healthy"
    
    def test_book_promo_endpoint(self):
        """Test /api/book-promo endpoint"""
        response = requests.get(f"{BASE_URL}/api/book-promo")
        assert response.status_code == 200
        data = response.json()
        assert "title" in data


class TestPostReactions:
    """Post reactions API tests"""
    
    @pytest.fixture(scope="class")
    def auth_token(self):
        """Get auth token"""
        response = requests.post(f"{BASE_URL}/api/auth/login", json={
            "email": ADMIN_EMAIL,
            "password": ADMIN_PASSWORD
        })
        if response.status_code == 200:
            return response.json().get("token")
        pytest.skip("Authentication failed")
    
    def test_create_post_and_react(self, auth_token):
        """Test creating a post and adding a reaction"""
        # Create a post
        create_response = requests.post(
            f"{BASE_URL}/api/posts",
            headers={
                "Authorization": f"Bearer {auth_token}",
                "Content-Type": "application/json"
            },
            json={
                "content": f"TEST_Reaction_Post_{int(time.time())}"
            }
        )
        assert create_response.status_code == 200
        post_id = create_response.json()["id"]
        
        # Add a reaction
        react_response = requests.post(
            f"{BASE_URL}/api/posts/{post_id}/react?reaction_type=like",
            headers={"Authorization": f"Bearer {auth_token}"}
        )
        assert react_response.status_code == 200
        data = react_response.json()
        assert data.get("success") == True
        assert data.get("reaction") == "like"


if __name__ == "__main__":
    pytest.main([__file__, "-v", "--tb=short"])
