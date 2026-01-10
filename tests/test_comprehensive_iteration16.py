"""
Comprehensive API Tests for InfoPilot Explorer - Iteration 16
Tests all major features: Auth, Categories, Search, Social, Messaging, Marketplace, Admin, Badges
"""
import pytest
import requests
import os
import time
from datetime import datetime

BASE_URL = os.environ.get('REACT_APP_BACKEND_URL', '').rstrip('/')

# Test credentials
ADMIN_EMAIL = "john@infojet.com"
ADMIN_PASSWORD = "password123"
TEST_EMAIL = "testuser@example.com"
TEST_PASSWORD = "password123"

class TestConfig:
    """Shared test configuration and fixtures"""
    admin_token = None
    test_user_token = None
    test_category_id = None
    test_group_id = None
    test_page_id = None
    test_user_id = None
    admin_user_id = None


@pytest.fixture(scope="module")
def api_client():
    """Shared requests session"""
    session = requests.Session()
    session.headers.update({"Content-Type": "application/json"})
    return session


@pytest.fixture(scope="module")
def admin_auth(api_client):
    """Get admin authentication token"""
    response = api_client.post(f"{BASE_URL}/api/auth/login", json={
        "email": ADMIN_EMAIL,
        "password": ADMIN_PASSWORD
    })
    if response.status_code == 200:
        data = response.json()
        TestConfig.admin_token = data.get("access_token")
        TestConfig.admin_user_id = data.get("user", {}).get("id")
        return TestConfig.admin_token
    pytest.skip(f"Admin authentication failed: {response.status_code}")


@pytest.fixture(scope="module")
def test_user_auth(api_client):
    """Get test user authentication token"""
    response = api_client.post(f"{BASE_URL}/api/auth/login", json={
        "email": TEST_EMAIL,
        "password": TEST_PASSWORD
    })
    if response.status_code == 200:
        data = response.json()
        TestConfig.test_user_token = data.get("access_token")
        TestConfig.test_user_id = data.get("user", {}).get("id")
        return TestConfig.test_user_token
    pytest.skip(f"Test user authentication failed: {response.status_code}")


# ============================================
# HEALTH & ROOT TESTS
# ============================================

class TestHealthEndpoints:
    """Health check and root endpoint tests"""
    
    def test_root_endpoint(self, api_client):
        """Test root API endpoint"""
        response = api_client.get(f"{BASE_URL}/api/")
        assert response.status_code == 200
        data = response.json()
        assert "message" in data or "status" in data
        print(f"Root endpoint: {data}")
    
    def test_health_check(self, api_client):
        """Test health check endpoint"""
        response = api_client.get(f"{BASE_URL}/api/health")
        assert response.status_code == 200
        data = response.json()
        assert "status" in data
        print(f"Health check: {data}")


# ============================================
# AUTHENTICATION TESTS
# ============================================

class TestAuthentication:
    """Authentication endpoint tests"""
    
    def test_login_admin_success(self, api_client):
        """Test admin login with valid credentials"""
        response = api_client.post(f"{BASE_URL}/api/auth/login", json={
            "email": ADMIN_EMAIL,
            "password": ADMIN_PASSWORD
        })
        assert response.status_code == 200
        data = response.json()
        assert "access_token" in data
        assert "user" in data
        assert data["user"]["email"] == ADMIN_EMAIL
        assert data["user"]["is_admin"] == True
        TestConfig.admin_token = data["access_token"]
        TestConfig.admin_user_id = data["user"]["id"]
        print(f"Admin login successful: {data['user']['username']}")
    
    def test_login_test_user_success(self, api_client):
        """Test regular user login"""
        response = api_client.post(f"{BASE_URL}/api/auth/login", json={
            "email": TEST_EMAIL,
            "password": TEST_PASSWORD
        })
        assert response.status_code == 200
        data = response.json()
        assert "access_token" in data
        assert "user" in data
        TestConfig.test_user_token = data["access_token"]
        TestConfig.test_user_id = data["user"]["id"]
        print(f"Test user login successful: {data['user']['username']}")
    
    def test_login_invalid_credentials(self, api_client):
        """Test login with invalid credentials"""
        response = api_client.post(f"{BASE_URL}/api/auth/login", json={
            "email": "wrong@example.com",
            "password": "wrongpassword"
        })
        assert response.status_code in [401, 400]
        print("Invalid credentials correctly rejected")
    
    def test_get_current_user(self, api_client, admin_auth):
        """Test getting current user info"""
        response = api_client.get(
            f"{BASE_URL}/api/auth/me",
            headers={"Authorization": f"Bearer {admin_auth}"}
        )
        assert response.status_code == 200
        data = response.json()
        assert "email" in data
        assert data["email"] == ADMIN_EMAIL
        print(f"Current user: {data['username']}")
    
    def test_register_duplicate_email(self, api_client):
        """Test registration with existing email fails"""
        response = api_client.post(f"{BASE_URL}/api/auth/register", json={
            "email": ADMIN_EMAIL,
            "password": "newpassword123",
            "username": "newuser"
        })
        assert response.status_code in [400, 409]
        print("Duplicate email registration correctly rejected")


# ============================================
# CATEGORIES/PROTOCOLS TESTS
# ============================================

class TestCategories:
    """Category CRUD and protocol tests"""
    
    def test_create_category(self, api_client, admin_auth):
        """Test creating a new category/protocol"""
        response = api_client.post(
            f"{BASE_URL}/api/categories",
            headers={"Authorization": f"Bearer {admin_auth}"},
            json={
                "name": "TEST_Protocol_Iteration16",
                "protocol_string": "test|protocol|string",
                "is_public": False
            }
        )
        assert response.status_code in [200, 201]
        data = response.json()
        assert "id" in data
        assert data["name"] == "TEST_Protocol_Iteration16"
        TestConfig.test_category_id = data["id"]
        print(f"Created category: {data['name']} (ID: {data['id']})")
    
    def test_get_categories(self, api_client, admin_auth):
        """Test getting user's categories"""
        response = api_client.get(
            f"{BASE_URL}/api/categories",
            headers={"Authorization": f"Bearer {admin_auth}"}
        )
        assert response.status_code == 200
        data = response.json()
        assert isinstance(data, list)
        print(f"Retrieved {len(data)} categories")
    
    def test_get_category_by_id(self, api_client, admin_auth):
        """Test getting a specific category"""
        if not TestConfig.test_category_id:
            pytest.skip("No test category created")
        
        response = api_client.get(
            f"{BASE_URL}/api/categories/{TestConfig.test_category_id}",
            headers={"Authorization": f"Bearer {admin_auth}"}
        )
        assert response.status_code == 200
        data = response.json()
        assert data["id"] == TestConfig.test_category_id
        print(f"Retrieved category: {data['name']}")
    
    def test_update_category(self, api_client, admin_auth):
        """Test updating a category"""
        if not TestConfig.test_category_id:
            pytest.skip("No test category created")
        
        response = api_client.put(
            f"{BASE_URL}/api/categories/{TestConfig.test_category_id}",
            headers={"Authorization": f"Bearer {admin_auth}"},
            json={
                "name": "TEST_Protocol_Updated",
                "protocol_string": "updated|protocol|string"
            }
        )
        assert response.status_code == 200
        data = response.json()
        assert data["name"] == "TEST_Protocol_Updated"
        print(f"Updated category: {data['name']}")
    
    def test_update_category_visibility(self, api_client, admin_auth):
        """Test toggling category visibility"""
        if not TestConfig.test_category_id:
            pytest.skip("No test category created")
        
        response = api_client.put(
            f"{BASE_URL}/api/categories/{TestConfig.test_category_id}/visibility?is_public=true",
            headers={"Authorization": f"Bearer {admin_auth}"}
        )
        assert response.status_code == 200
        print("Category visibility updated to public")
    
    def test_get_categories_with_counts(self, api_client, admin_auth):
        """Test getting categories with result counts"""
        response = api_client.get(
            f"{BASE_URL}/api/categories/with-counts",
            headers={"Authorization": f"Bearer {admin_auth}"}
        )
        assert response.status_code == 200
        data = response.json()
        assert isinstance(data, list)
        print(f"Categories with counts: {len(data)} items")
    
    def test_get_categories_tree(self, api_client, admin_auth):
        """Test getting category tree structure"""
        response = api_client.get(
            f"{BASE_URL}/api/categories/tree",
            headers={"Authorization": f"Bearer {admin_auth}"}
        )
        assert response.status_code == 200
        data = response.json()
        assert isinstance(data, list)
        print(f"Category tree: {len(data)} root categories")
    
    def test_copy_category(self, api_client, admin_auth):
        """Test copying a category/protocol"""
        if not TestConfig.test_category_id:
            pytest.skip("No test category created")
        
        response = api_client.post(
            f"{BASE_URL}/api/categories/{TestConfig.test_category_id}/copy",
            headers={"Authorization": f"Bearer {admin_auth}"}
        )
        assert response.status_code in [200, 201]
        data = response.json()
        assert "id" in data
        # Clean up copied category
        api_client.delete(
            f"{BASE_URL}/api/categories/{data['id']}",
            headers={"Authorization": f"Bearer {admin_auth}"}
        )
        print(f"Copied and cleaned up category")


# ============================================
# ULTIMATE SEARCH TESTS
# ============================================

class TestUltimateSearch:
    """Ultimate Search functionality tests"""
    
    def test_get_search_filters(self, api_client, admin_auth):
        """Test getting search filters"""
        response = api_client.get(
            f"{BASE_URL}/api/ultimate-search/filters",
            headers={"Authorization": f"Bearer {admin_auth}"}
        )
        assert response.status_code == 200
        data = response.json()
        assert "categories" in data or isinstance(data, dict)
        print(f"Search filters retrieved")
    
    def test_get_search_sessions(self, api_client, admin_auth):
        """Test getting search sessions"""
        response = api_client.get(
            f"{BASE_URL}/api/ultimate-search/sessions",
            headers={"Authorization": f"Bearer {admin_auth}"}
        )
        assert response.status_code == 200
        data = response.json()
        assert isinstance(data, list)
        print(f"Search sessions: {len(data)} sessions")
    
    def test_get_user_stats(self, api_client, admin_auth):
        """Test getting user search stats"""
        response = api_client.get(
            f"{BASE_URL}/api/ultimate-search/user-stats",
            headers={"Authorization": f"Bearer {admin_auth}"}
        )
        assert response.status_code == 200
        data = response.json()
        print(f"User stats retrieved: {data}")
    
    def test_get_page_settings(self, api_client, admin_auth):
        """Test getting page settings"""
        response = api_client.get(
            f"{BASE_URL}/api/ultimate-search/page-settings",
            headers={"Authorization": f"Bearer {admin_auth}"}
        )
        assert response.status_code == 200
        data = response.json()
        print(f"Page settings retrieved")
    
    def test_get_map_data(self, api_client, admin_auth):
        """Test getting map data for search results"""
        response = api_client.get(
            f"{BASE_URL}/api/ultimate-search/map-data",
            headers={"Authorization": f"Bearer {admin_auth}"}
        )
        assert response.status_code == 200
        data = response.json()
        print(f"Map data retrieved")


# ============================================
# GLOBAL DATABASE TESTS
# ============================================

class TestGlobalDatabase:
    """Global Database and Research Database tests"""
    
    def test_get_global_database(self, api_client, admin_auth):
        """Test getting global database entries"""
        response = api_client.get(
            f"{BASE_URL}/api/global-database",
            headers={"Authorization": f"Bearer {admin_auth}"}
        )
        assert response.status_code == 200
        data = response.json()
        print(f"Global database retrieved")
    
    def test_get_research_resources(self, api_client, admin_auth):
        """Test getting research resources"""
        response = api_client.get(
            f"{BASE_URL}/api/research-database/resources",
            headers={"Authorization": f"Bearer {admin_auth}"}
        )
        assert response.status_code == 200
        data = response.json()
        assert "resources" in data or isinstance(data, list)
        print(f"Research resources retrieved")
    
    def test_get_trending_topics(self, api_client, admin_auth):
        """Test getting trending topics"""
        response = api_client.get(
            f"{BASE_URL}/api/research-database/trending",
            headers={"Authorization": f"Bearer {admin_auth}"}
        )
        assert response.status_code == 200
        data = response.json()
        print(f"Trending topics retrieved")
    
    def test_get_top_contributors(self, api_client, admin_auth):
        """Test getting top contributors"""
        response = api_client.get(
            f"{BASE_URL}/api/research-database/contributors",
            headers={"Authorization": f"Bearer {admin_auth}"}
        )
        assert response.status_code == 200
        data = response.json()
        assert isinstance(data, list)
        print(f"Top contributors: {len(data)} contributors")
    
    def test_get_research_map_data(self, api_client, admin_auth):
        """Test getting research map data"""
        response = api_client.get(
            f"{BASE_URL}/api/research-database/map-data",
            headers={"Authorization": f"Bearer {admin_auth}"}
        )
        assert response.status_code == 200
        data = response.json()
        print(f"Research map data retrieved")
    
    def test_get_research_stats(self, api_client, admin_auth):
        """Test getting research database stats"""
        response = api_client.get(
            f"{BASE_URL}/api/research-database/stats",
            headers={"Authorization": f"Bearer {admin_auth}"}
        )
        assert response.status_code == 200
        data = response.json()
        print(f"Research stats: {data}")


# ============================================
# SOCIAL FEATURES - FRIENDS TESTS
# ============================================

class TestFriends:
    """Friends functionality tests"""
    
    def test_get_friends(self, api_client, admin_auth):
        """Test getting friends list"""
        response = api_client.get(
            f"{BASE_URL}/api/friends",
            headers={"Authorization": f"Bearer {admin_auth}"}
        )
        assert response.status_code == 200
        data = response.json()
        assert isinstance(data, list)
        print(f"Friends list: {len(data)} friends")
    
    def test_get_friend_requests(self, api_client, admin_auth):
        """Test getting friend requests"""
        response = api_client.get(
            f"{BASE_URL}/api/friends/requests",
            headers={"Authorization": f"Bearer {admin_auth}"}
        )
        assert response.status_code == 200
        data = response.json()
        assert isinstance(data, list)
        print(f"Friend requests: {len(data)} requests")


# ============================================
# SOCIAL FEATURES - GROUPS TESTS
# ============================================

class TestGroups:
    """Groups functionality tests"""
    
    def test_get_groups(self, api_client, admin_auth):
        """Test getting groups list"""
        response = api_client.get(
            f"{BASE_URL}/api/groups",
            headers={"Authorization": f"Bearer {admin_auth}"}
        )
        assert response.status_code == 200
        data = response.json()
        assert isinstance(data, list)
        print(f"Groups list: {len(data)} groups")
    
    def test_create_group(self, api_client, admin_auth):
        """Test creating a new group"""
        response = api_client.post(
            f"{BASE_URL}/api/groups",
            headers={"Authorization": f"Bearer {admin_auth}"},
            json={
                "name": "TEST_Group_Iteration16",
                "description": "Test group for iteration 16 testing"
            }
        )
        assert response.status_code in [200, 201]
        data = response.json()
        assert "id" in data
        TestConfig.test_group_id = data["id"]
        print(f"Created group: {data['name']} (ID: {data['id']})")
    
    def test_get_group_by_id(self, api_client, admin_auth):
        """Test getting a specific group"""
        if not TestConfig.test_group_id:
            pytest.skip("No test group created")
        
        response = api_client.get(
            f"{BASE_URL}/api/groups/{TestConfig.test_group_id}",
            headers={"Authorization": f"Bearer {admin_auth}"}
        )
        assert response.status_code == 200
        data = response.json()
        assert data["id"] == TestConfig.test_group_id
        print(f"Retrieved group: {data['name']}")
    
    def test_update_group(self, api_client, admin_auth):
        """Test updating a group"""
        if not TestConfig.test_group_id:
            pytest.skip("No test group created")
        
        response = api_client.put(
            f"{BASE_URL}/api/groups/{TestConfig.test_group_id}",
            headers={"Authorization": f"Bearer {admin_auth}"},
            json={
                "name": "TEST_Group_Updated",
                "description": "Updated description"
            }
        )
        assert response.status_code == 200
        data = response.json()
        assert data["name"] == "TEST_Group_Updated"
        print(f"Updated group: {data['name']}")
    
    def test_post_in_group(self, api_client, admin_auth):
        """Test posting in a group"""
        if not TestConfig.test_group_id:
            pytest.skip("No test group created")
        
        response = api_client.post(
            f"{BASE_URL}/api/groups/{TestConfig.test_group_id}/posts",
            headers={"Authorization": f"Bearer {admin_auth}"},
            json={
                "content": "Test post in group for iteration 16"
            }
        )
        assert response.status_code in [200, 201]
        print("Posted in group successfully")


# ============================================
# SOCIAL FEATURES - PAGES TESTS
# ============================================

class TestPages:
    """Pages functionality tests"""
    
    def test_get_pages(self, api_client, admin_auth):
        """Test getting pages list"""
        response = api_client.get(
            f"{BASE_URL}/api/pages",
            headers={"Authorization": f"Bearer {admin_auth}"}
        )
        assert response.status_code == 200
        data = response.json()
        assert isinstance(data, list)
        print(f"Pages list: {len(data)} pages")
    
    def test_create_page(self, api_client, admin_auth):
        """Test creating a new page"""
        response = api_client.post(
            f"{BASE_URL}/api/pages",
            headers={"Authorization": f"Bearer {admin_auth}"},
            json={
                "name": "TEST_Page_Iteration16",
                "description": "Test page for iteration 16 testing"
            }
        )
        assert response.status_code in [200, 201]
        data = response.json()
        assert "id" in data
        TestConfig.test_page_id = data["id"]
        print(f"Created page: {data['name']} (ID: {data['id']})")
    
    def test_get_page_by_id(self, api_client, admin_auth):
        """Test getting a specific page"""
        if not TestConfig.test_page_id:
            pytest.skip("No test page created")
        
        response = api_client.get(
            f"{BASE_URL}/api/pages/{TestConfig.test_page_id}",
            headers={"Authorization": f"Bearer {admin_auth}"}
        )
        assert response.status_code == 200
        data = response.json()
        assert data["id"] == TestConfig.test_page_id
        print(f"Retrieved page: {data['name']}")
    
    def test_update_page(self, api_client, admin_auth):
        """Test updating a page"""
        if not TestConfig.test_page_id:
            pytest.skip("No test page created")
        
        response = api_client.put(
            f"{BASE_URL}/api/pages/{TestConfig.test_page_id}",
            headers={"Authorization": f"Bearer {admin_auth}"},
            json={
                "name": "TEST_Page_Updated",
                "description": "Updated description"
            }
        )
        assert response.status_code == 200
        data = response.json()
        assert data["name"] == "TEST_Page_Updated"
        print(f"Updated page: {data['name']}")
    
    def test_post_on_page(self, api_client, admin_auth):
        """Test posting on a page"""
        if not TestConfig.test_page_id:
            pytest.skip("No test page created")
        
        response = api_client.post(
            f"{BASE_URL}/api/pages/{TestConfig.test_page_id}/posts",
            headers={"Authorization": f"Bearer {admin_auth}"},
            json={
                "content": "Test post on page for iteration 16"
            }
        )
        assert response.status_code in [200, 201]
        print("Posted on page successfully")


# ============================================
# PRIVATE MESSAGING TESTS
# ============================================

class TestMessaging:
    """Private messaging tests"""
    
    def test_get_conversations(self, api_client, admin_auth):
        """Test getting conversations list"""
        response = api_client.get(
            f"{BASE_URL}/api/messages/conversations",
            headers={"Authorization": f"Bearer {admin_auth}"}
        )
        assert response.status_code == 200
        data = response.json()
        assert isinstance(data, list)
        print(f"Conversations: {len(data)} conversations")
    
    def test_get_unread_count(self, api_client, admin_auth):
        """Test getting unread message count"""
        response = api_client.get(
            f"{BASE_URL}/api/messages/unread-count",
            headers={"Authorization": f"Bearer {admin_auth}"}
        )
        assert response.status_code == 200
        data = response.json()
        print(f"Unread count: {data}")
    
    def test_send_message(self, api_client, admin_auth, test_user_auth):
        """Test sending a message"""
        if not TestConfig.test_user_id:
            pytest.skip("No test user available")
        
        response = api_client.post(
            f"{BASE_URL}/api/messages/send",
            headers={"Authorization": f"Bearer {admin_auth}"},
            json={
                "recipient_id": TestConfig.test_user_id,
                "content": "Test message from iteration 16 testing"
            }
        )
        assert response.status_code in [200, 201]
        print("Message sent successfully")
    
    def test_get_conversation_with_user(self, api_client, admin_auth, test_user_auth):
        """Test getting conversation with specific user"""
        if not TestConfig.test_user_id:
            pytest.skip("No test user available")
        
        response = api_client.get(
            f"{BASE_URL}/api/messages/conversation/{TestConfig.test_user_id}",
            headers={"Authorization": f"Bearer {admin_auth}"}
        )
        assert response.status_code == 200
        data = response.json()
        assert isinstance(data, list)
        print(f"Conversation messages: {len(data)} messages")


# ============================================
# MARKETPLACE TESTS
# ============================================

class TestMarketplace:
    """Marketplace functionality tests"""
    
    def test_get_protocols_for_sale(self, api_client, admin_auth):
        """Test getting protocols for sale"""
        response = api_client.get(
            f"{BASE_URL}/api/marketplace/protocols",
            headers={"Authorization": f"Bearer {admin_auth}"}
        )
        assert response.status_code == 200
        data = response.json()
        assert isinstance(data, list)
        print(f"Protocols for sale: {len(data)} protocols")
    
    def test_get_my_purchases(self, api_client, admin_auth):
        """Test getting user's purchases"""
        response = api_client.get(
            f"{BASE_URL}/api/marketplace/my-purchases",
            headers={"Authorization": f"Bearer {admin_auth}"}
        )
        assert response.status_code == 200
        data = response.json()
        assert isinstance(data, list)
        print(f"My purchases: {len(data)} purchases")
    
    def test_get_my_sales(self, api_client, admin_auth):
        """Test getting user's sales"""
        response = api_client.get(
            f"{BASE_URL}/api/marketplace/my-sales",
            headers={"Authorization": f"Bearer {admin_auth}"}
        )
        assert response.status_code == 200
        data = response.json()
        assert isinstance(data, list)
        print(f"My sales: {len(data)} sales")


# ============================================
# BADGES & GAMIFICATION TESTS
# ============================================

class TestBadges:
    """Badges and gamification tests"""
    
    def test_get_my_badges(self, api_client, admin_auth):
        """Test getting user's badges"""
        response = api_client.get(
            f"{BASE_URL}/api/badges/my-badges",
            headers={"Authorization": f"Bearer {admin_auth}"}
        )
        assert response.status_code == 200
        data = response.json()
        assert isinstance(data, list)
        print(f"My badges: {len(data)} badges")
    
    def test_check_new_badges(self, api_client, admin_auth):
        """Test checking for new badges"""
        response = api_client.post(
            f"{BASE_URL}/api/badges/check-new",
            headers={"Authorization": f"Bearer {admin_auth}"}
        )
        assert response.status_code == 200
        data = response.json()
        print(f"New badges check: {data}")
    
    def test_get_leaderboard(self, api_client, admin_auth):
        """Test getting badges leaderboard"""
        response = api_client.get(
            f"{BASE_URL}/api/badges/leaderboard",
            headers={"Authorization": f"Bearer {admin_auth}"}
        )
        assert response.status_code == 200
        data = response.json()
        assert isinstance(data, list)
        print(f"Leaderboard: {len(data)} entries")


# ============================================
# ADMIN PANEL TESTS
# ============================================

class TestAdminPanel:
    """Admin panel functionality tests"""
    
    def test_get_admin_settings(self, api_client, admin_auth):
        """Test getting admin settings"""
        response = api_client.get(
            f"{BASE_URL}/api/admin/settings",
            headers={"Authorization": f"Bearer {admin_auth}"}
        )
        assert response.status_code == 200
        data = response.json()
        print(f"Admin settings retrieved")
    
    def test_get_admin_users(self, api_client, admin_auth):
        """Test getting all users (admin)"""
        response = api_client.get(
            f"{BASE_URL}/api/admin/users",
            headers={"Authorization": f"Bearer {admin_auth}"}
        )
        assert response.status_code == 200
        data = response.json()
        assert isinstance(data, list)
        print(f"Admin users: {len(data)} users")
    
    def test_get_database_limits(self, api_client, admin_auth):
        """Test getting database limits"""
        response = api_client.get(
            f"{BASE_URL}/api/admin/database-limits",
            headers={"Authorization": f"Bearer {admin_auth}"}
        )
        assert response.status_code == 200
        data = response.json()
        print(f"Database limits: {data}")
    
    def test_get_search_pages_config(self, api_client, admin_auth):
        """Test getting search pages config"""
        response = api_client.get(
            f"{BASE_URL}/api/admin/search-pages-config",
            headers={"Authorization": f"Bearer {admin_auth}"}
        )
        assert response.status_code == 200
        data = response.json()
        print(f"Search pages config retrieved")
    
    def test_get_subscriptions(self, api_client, admin_auth):
        """Test getting subscriptions info"""
        response = api_client.get(
            f"{BASE_URL}/api/admin/subscriptions",
            headers={"Authorization": f"Bearer {admin_auth}"}
        )
        assert response.status_code == 200
        data = response.json()
        print(f"Subscriptions info retrieved")
    
    def test_get_moderation_dashboard(self, api_client, admin_auth):
        """Test getting moderation dashboard"""
        response = api_client.get(
            f"{BASE_URL}/api/admin/moderation/dashboard",
            headers={"Authorization": f"Bearer {admin_auth}"}
        )
        assert response.status_code == 200
        data = response.json()
        print(f"Moderation dashboard: {data}")
    
    def test_get_moderation_groups(self, api_client, admin_auth):
        """Test getting moderation groups list"""
        response = api_client.get(
            f"{BASE_URL}/api/admin/moderation/groups",
            headers={"Authorization": f"Bearer {admin_auth}"}
        )
        assert response.status_code == 200
        data = response.json()
        assert isinstance(data, list)
        print(f"Moderation groups: {len(data)} groups")
    
    def test_get_moderation_pages(self, api_client, admin_auth):
        """Test getting moderation pages list"""
        response = api_client.get(
            f"{BASE_URL}/api/admin/moderation/pages",
            headers={"Authorization": f"Bearer {admin_auth}"}
        )
        assert response.status_code == 200
        data = response.json()
        assert isinstance(data, list)
        print(f"Moderation pages: {len(data)} pages")
    
    def test_get_moderation_users(self, api_client, admin_auth):
        """Test getting moderation users list"""
        response = api_client.get(
            f"{BASE_URL}/api/admin/moderation/users",
            headers={"Authorization": f"Bearer {admin_auth}"}
        )
        assert response.status_code == 200
        data = response.json()
        assert isinstance(data, list)
        print(f"Moderation users: {len(data)} users")
    
    def test_get_email_digest_config(self, api_client, admin_auth):
        """Test getting email digest config"""
        response = api_client.get(
            f"{BASE_URL}/api/admin/email-digest/config",
            headers={"Authorization": f"Bearer {admin_auth}"}
        )
        assert response.status_code == 200
        data = response.json()
        print(f"Email digest config: {data}")


# ============================================
# LEGAL & SUBSCRIPTION TESTS
# ============================================

class TestLegalAndSubscription:
    """Legal pages and subscription tests"""
    
    def test_get_privacy_policy(self, api_client):
        """Test getting privacy policy"""
        response = api_client.get(f"{BASE_URL}/api/legal/privacy-policy")
        assert response.status_code == 200
        data = response.json()
        print(f"Privacy policy retrieved")
    
    def test_get_terms_of_service(self, api_client):
        """Test getting terms of service"""
        response = api_client.get(f"{BASE_URL}/api/legal/terms-of-service")
        assert response.status_code == 200
        data = response.json()
        print(f"Terms of service retrieved")
    
    def test_get_subscription_config(self, api_client, admin_auth):
        """Test getting subscription config"""
        response = api_client.get(
            f"{BASE_URL}/api/subscription/config",
            headers={"Authorization": f"Bearer {admin_auth}"}
        )
        assert response.status_code == 200
        data = response.json()
        print(f"Subscription config: {data}")
    
    def test_get_subscription_status(self, api_client, admin_auth):
        """Test getting subscription status"""
        response = api_client.get(
            f"{BASE_URL}/api/subscription/status",
            headers={"Authorization": f"Bearer {admin_auth}"}
        )
        assert response.status_code == 200
        data = response.json()
        print(f"Subscription status: {data}")
    
    def test_get_subscription_info(self, api_client):
        """Test getting subscription info"""
        response = api_client.get(f"{BASE_URL}/api/subscription/info")
        assert response.status_code == 200
        data = response.json()
        print(f"Subscription info retrieved")


# ============================================
# STATISTICS TESTS
# ============================================

class TestStatistics:
    """Statistics endpoint tests"""
    
    def test_get_statistics(self, api_client, admin_auth):
        """Test getting user statistics"""
        response = api_client.get(
            f"{BASE_URL}/api/statistics",
            headers={"Authorization": f"Bearer {admin_auth}"}
        )
        assert response.status_code == 200
        data = response.json()
        print(f"Statistics: {data}")
    
    def test_get_popular_protocols(self, api_client, admin_auth):
        """Test getting popular protocols"""
        response = api_client.get(
            f"{BASE_URL}/api/statistics/popular-protocols",
            headers={"Authorization": f"Bearer {admin_auth}"}
        )
        assert response.status_code == 200
        data = response.json()
        assert isinstance(data, list)
        print(f"Popular protocols: {len(data)} protocols")
    
    def test_get_global_statistics(self, api_client, admin_auth):
        """Test getting global statistics"""
        response = api_client.get(
            f"{BASE_URL}/api/statistics/global",
            headers={"Authorization": f"Bearer {admin_auth}"}
        )
        assert response.status_code == 200
        data = response.json()
        print(f"Global statistics: {data}")


# ============================================
# PAYMENTS TESTS
# ============================================

class TestPayments:
    """Payment configuration tests"""
    
    def test_get_stripe_config(self, api_client):
        """Test getting Stripe config"""
        response = api_client.get(f"{BASE_URL}/api/payments/config")
        assert response.status_code == 200
        data = response.json()
        assert "publishable_key" in data
        print(f"Stripe config retrieved")
    
    def test_get_payment_history(self, api_client, admin_auth):
        """Test getting payment history"""
        response = api_client.get(
            f"{BASE_URL}/api/payments/history",
            headers={"Authorization": f"Bearer {admin_auth}"}
        )
        assert response.status_code == 200
        data = response.json()
        assert isinstance(data, list)
        print(f"Payment history: {len(data)} payments")


# ============================================
# USER SEARCH TESTS
# ============================================

class TestUserSearch:
    """User search tests"""
    
    def test_search_users(self, api_client, admin_auth):
        """Test searching for users"""
        response = api_client.get(
            f"{BASE_URL}/api/users/search?q=john",
            headers={"Authorization": f"Bearer {admin_auth}"}
        )
        assert response.status_code == 200
        data = response.json()
        assert isinstance(data, list)
        print(f"User search results: {len(data)} users")


# ============================================
# SAFETY TESTS
# ============================================

class TestSafety:
    """URL safety check tests"""
    
    def test_get_safety_status(self, api_client):
        """Test getting safety API status"""
        response = api_client.get(f"{BASE_URL}/api/safety/status")
        assert response.status_code == 200
        data = response.json()
        print(f"Safety status: {data}")


# ============================================
# CLEANUP TESTS (Run Last)
# ============================================

class TestCleanup:
    """Cleanup test data"""
    
    def test_delete_test_page(self, api_client, admin_auth):
        """Delete test page"""
        if not TestConfig.test_page_id:
            pytest.skip("No test page to delete")
        
        response = api_client.delete(
            f"{BASE_URL}/api/pages/{TestConfig.test_page_id}",
            headers={"Authorization": f"Bearer {admin_auth}"}
        )
        assert response.status_code in [200, 204]
        print(f"Deleted test page: {TestConfig.test_page_id}")
    
    def test_delete_test_group(self, api_client, admin_auth):
        """Delete test group"""
        if not TestConfig.test_group_id:
            pytest.skip("No test group to delete")
        
        response = api_client.delete(
            f"{BASE_URL}/api/groups/{TestConfig.test_group_id}",
            headers={"Authorization": f"Bearer {admin_auth}"}
        )
        assert response.status_code in [200, 204]
        print(f"Deleted test group: {TestConfig.test_group_id}")
    
    def test_delete_test_category(self, api_client, admin_auth):
        """Delete test category"""
        if not TestConfig.test_category_id:
            pytest.skip("No test category to delete")
        
        response = api_client.delete(
            f"{BASE_URL}/api/categories/{TestConfig.test_category_id}",
            headers={"Authorization": f"Bearer {admin_auth}"}
        )
        assert response.status_code in [200, 204]
        print(f"Deleted test category: {TestConfig.test_category_id}")


if __name__ == "__main__":
    pytest.main([__file__, "-v", "--tb=short"])
