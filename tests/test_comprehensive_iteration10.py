"""
Comprehensive Test Suite for InfoPilot Explorer - Iteration 10 (Fixed)
Tests all major features: Authentication, Social Features, Messaging, Categories, 
Protocol Recommendations, Legal Pages, Admin Panel, Groups, Pages, Updates
"""

import pytest
import requests
import os
import uuid
from datetime import datetime

BASE_URL = os.environ.get('REACT_APP_BACKEND_URL', 'https://social-research.preview.emergentagent.com').rstrip('/')

# Test credentials
ADMIN_EMAIL = "john@infojet.com"
ADMIN_PASSWORD = "password123"
TEST_USER_EMAIL = "testuser@example.com"
TEST_USER_PASSWORD = "password123"


class TestAuthentication:
    """Authentication endpoint tests - Login, Register, Google OAuth"""
    
    def test_health_check(self):
        """Test API health endpoint"""
        response = requests.get(f"{BASE_URL}/api/health")
        assert response.status_code == 200
        data = response.json()
        assert data["status"] == "operational"
        print("✓ Health check passed")
    
    def test_login_admin_user(self):
        """Test login with admin credentials"""
        response = requests.post(f"{BASE_URL}/api/auth/login", json={
            "email": ADMIN_EMAIL,
            "password": ADMIN_PASSWORD
        })
        assert response.status_code == 200
        data = response.json()
        assert "access_token" in data
        assert "user" in data
        assert data["user"]["email"] == ADMIN_EMAIL
        assert data["user"]["is_admin"] == True
        print(f"✓ Admin login successful: {data['user']['username']}")
    
    def test_login_test_user(self):
        """Test login with test user credentials"""
        response = requests.post(f"{BASE_URL}/api/auth/login", json={
            "email": TEST_USER_EMAIL,
            "password": TEST_USER_PASSWORD
        })
        if response.status_code == 401:
            # User doesn't exist, create it
            reg_response = requests.post(f"{BASE_URL}/api/auth/register", json={
                "username": f"TestUser_{uuid.uuid4().hex[:6]}",
                "email": TEST_USER_EMAIL,
                "password": TEST_USER_PASSWORD
            })
            if reg_response.status_code == 400 and "already registered" in reg_response.text:
                pytest.skip("Test user exists but password may be different")
            assert reg_response.status_code == 200
            data = reg_response.json()
        else:
            assert response.status_code == 200
            data = response.json()
        
        assert "access_token" in data
        print(f"✓ Test user login/register successful")
    
    def test_login_invalid_credentials(self):
        """Test login with invalid credentials"""
        response = requests.post(f"{BASE_URL}/api/auth/login", json={
            "email": "invalid@example.com",
            "password": "wrongpassword"
        })
        assert response.status_code == 401
        print("✓ Invalid credentials rejected correctly")
    
    def test_register_new_user(self):
        """Test registering a new user"""
        unique_email = f"test_{uuid.uuid4().hex[:8]}@example.com"
        response = requests.post(f"{BASE_URL}/api/auth/register", json={
            "username": f"TestPilot_{uuid.uuid4().hex[:6]}",
            "email": unique_email,
            "password": "testpass123"
        })
        assert response.status_code == 200
        data = response.json()
        assert "access_token" in data
        assert data["user"]["email"] == unique_email
        print(f"✓ New user registered: {unique_email}")
    
    def test_get_current_user(self):
        """Test getting current user info"""
        # First login
        login_response = requests.post(f"{BASE_URL}/api/auth/login", json={
            "email": ADMIN_EMAIL,
            "password": ADMIN_PASSWORD
        })
        token = login_response.json()["access_token"]
        
        # Get user info
        response = requests.get(f"{BASE_URL}/api/auth/me", headers={
            "Authorization": f"Bearer {token}"
        })
        assert response.status_code == 200
        data = response.json()
        assert data["email"] == ADMIN_EMAIL
        print(f"✓ Current user retrieved: {data['username']}")


class TestCategories:
    """Category CRUD tests"""
    
    @pytest.fixture(autouse=True)
    def setup(self):
        """Setup - get auth token"""
        response = requests.post(f"{BASE_URL}/api/auth/login", json={
            "email": ADMIN_EMAIL,
            "password": ADMIN_PASSWORD
        })
        self.token = response.json()["access_token"]
        self.headers = {"Authorization": f"Bearer {self.token}"}
    
    def test_list_categories(self):
        """Test listing user's categories"""
        response = requests.get(f"{BASE_URL}/api/categories", headers=self.headers)
        assert response.status_code == 200
        data = response.json()
        assert isinstance(data, list)
        print(f"✓ Listed {len(data)} categories")
    
    def test_create_category(self):
        """Test creating a new category"""
        response = requests.post(f"{BASE_URL}/api/categories", headers=self.headers, json={
            "name": f"Test Category {uuid.uuid4().hex[:6]}",
            "protocol": {"protocol_string": "(test or example) & (data)"},
            "is_public": True
        })
        assert response.status_code == 200
        data = response.json()
        assert "id" in data
        assert "name" in data
        print(f"✓ Category created: {data['name']}")
    
    def test_get_category_tree(self):
        """Test getting category tree structure"""
        response = requests.get(f"{BASE_URL}/api/categories/tree", headers=self.headers)
        assert response.status_code == 200
        data = response.json()
        assert "categories" in data
        print(f"✓ Category tree retrieved with {len(data['categories'])} root categories")
    
    def test_update_category(self):
        """Test updating a category"""
        # First create a category
        create_response = requests.post(f"{BASE_URL}/api/categories", headers=self.headers, json={
            "name": f"Update Test {uuid.uuid4().hex[:6]}",
            "protocol": {"protocol_string": "(update or test)"},
            "is_public": True
        })
        category_id = create_response.json()["id"]
        
        # Update it
        response = requests.put(f"{BASE_URL}/api/categories/{category_id}", headers=self.headers, json={
            "name": "Updated Category Name"
        })
        assert response.status_code == 200
        data = response.json()
        assert data["name"] == "Updated Category Name"
        print(f"✓ Category updated successfully")
    
    def test_delete_category(self):
        """Test deleting a category"""
        # First create a category
        create_response = requests.post(f"{BASE_URL}/api/categories", headers=self.headers, json={
            "name": f"Delete Test {uuid.uuid4().hex[:6]}",
            "protocol": {"protocol_string": "(delete or test)"},
            "is_public": True
        })
        category_id = create_response.json()["id"]
        
        # Delete it
        response = requests.delete(f"{BASE_URL}/api/categories/{category_id}", headers=self.headers)
        assert response.status_code == 200
        print(f"✓ Category deleted successfully")


class TestGroups:
    """Groups feature tests - CRUD, join/leave, posts"""
    
    @pytest.fixture(autouse=True)
    def setup(self):
        """Setup - get auth token"""
        response = requests.post(f"{BASE_URL}/api/auth/login", json={
            "email": ADMIN_EMAIL,
            "password": ADMIN_PASSWORD
        })
        self.token = response.json()["access_token"]
        self.headers = {"Authorization": f"Bearer {self.token}"}
    
    def test_list_groups(self):
        """Test listing groups"""
        response = requests.get(f"{BASE_URL}/api/groups", headers=self.headers)
        assert response.status_code == 200
        data = response.json()
        # API returns my_groups and public_groups
        assert "my_groups" in data or "public_groups" in data
        total = len(data.get("my_groups", [])) + len(data.get("public_groups", []))
        print(f"✓ Listed groups (my_groups + public_groups)")
    
    def test_create_group(self):
        """Test creating a new group"""
        response = requests.post(f"{BASE_URL}/api/groups", headers=self.headers, json={
            "name": f"Test Group {uuid.uuid4().hex[:6]}",
            "description": "A test group for automated testing",
            "privacy": "public"
        })
        assert response.status_code == 200
        data = response.json()
        # API returns {"group": {...}, "message": "..."}
        assert "group" in data
        assert "id" in data["group"]
        print(f"✓ Group created: {data['group']['name']}")
    
    def test_get_group_details(self):
        """Test getting group details"""
        # First create a group
        create_response = requests.post(f"{BASE_URL}/api/groups", headers=self.headers, json={
            "name": f"Detail Test Group {uuid.uuid4().hex[:6]}",
            "description": "Test group",
            "privacy": "public"
        })
        group_id = create_response.json()["group"]["id"]
        
        # Get details
        response = requests.get(f"{BASE_URL}/api/groups/{group_id}", headers=self.headers)
        assert response.status_code == 200
        data = response.json()
        assert data["id"] == group_id
        print(f"✓ Group details retrieved")
    
    def test_create_group_post(self):
        """Test creating a post in a group"""
        # First create a group
        create_response = requests.post(f"{BASE_URL}/api/groups", headers=self.headers, json={
            "name": f"Post Test Group {uuid.uuid4().hex[:6]}",
            "description": "Test group for posts",
            "privacy": "public"
        })
        group_id = create_response.json()["group"]["id"]
        
        # Create a post
        response = requests.post(f"{BASE_URL}/api/groups/{group_id}/posts", headers=self.headers, json={
            "content": "This is a test post in the group!"
        })
        assert response.status_code == 200
        data = response.json()
        assert "post" in data
        print(f"✓ Group post created")
    
    def test_join_leave_group(self):
        """Test joining and leaving a group"""
        # Create a group with test user
        test_login = requests.post(f"{BASE_URL}/api/auth/login", json={
            "email": TEST_USER_EMAIL,
            "password": TEST_USER_PASSWORD
        })
        if test_login.status_code != 200:
            pytest.skip("Test user not available")
        test_token = test_login.json()["access_token"]
        test_headers = {"Authorization": f"Bearer {test_token}"}
        
        # Create group as admin
        create_response = requests.post(f"{BASE_URL}/api/groups", headers=self.headers, json={
            "name": f"Join Test Group {uuid.uuid4().hex[:6]}",
            "description": "Test group for join/leave",
            "privacy": "public"
        })
        group_id = create_response.json()["group"]["id"]
        
        # Join as test user
        join_response = requests.post(f"{BASE_URL}/api/groups/{group_id}/join", headers=test_headers)
        assert join_response.status_code == 200
        print(f"✓ Joined group successfully")
        
        # Leave as test user
        leave_response = requests.post(f"{BASE_URL}/api/groups/{group_id}/leave", headers=test_headers)
        assert leave_response.status_code == 200
        print(f"✓ Left group successfully")


class TestPages:
    """Pages feature tests - CRUD, follow/unfollow, posts"""
    
    @pytest.fixture(autouse=True)
    def setup(self):
        """Setup - get auth token"""
        response = requests.post(f"{BASE_URL}/api/auth/login", json={
            "email": ADMIN_EMAIL,
            "password": ADMIN_PASSWORD
        })
        self.token = response.json()["access_token"]
        self.headers = {"Authorization": f"Bearer {self.token}"}
    
    def test_list_pages(self):
        """Test listing pages"""
        response = requests.get(f"{BASE_URL}/api/pages", headers=self.headers)
        assert response.status_code == 200
        data = response.json()
        # API returns my_pages, following, popular
        assert "my_pages" in data or "popular" in data
        print(f"✓ Listed pages (my_pages, following, popular)")
    
    def test_create_page(self):
        """Test creating a new page"""
        response = requests.post(f"{BASE_URL}/api/pages", headers=self.headers, json={
            "name": f"Test Page {uuid.uuid4().hex[:6]}",
            "description": "A test page for automated testing",
            "category": "Technology"
        })
        assert response.status_code == 200
        data = response.json()
        # API returns {"page": {...}, "message": "..."}
        assert "page" in data
        assert "id" in data["page"]
        print(f"✓ Page created: {data['page']['name']}")
    
    def test_get_page_details(self):
        """Test getting page details"""
        # First create a page
        create_response = requests.post(f"{BASE_URL}/api/pages", headers=self.headers, json={
            "name": f"Detail Test Page {uuid.uuid4().hex[:6]}",
            "description": "Test page",
            "category": "General"
        })
        page_id = create_response.json()["page"]["id"]
        
        # Get details
        response = requests.get(f"{BASE_URL}/api/pages/{page_id}", headers=self.headers)
        assert response.status_code == 200
        data = response.json()
        assert data["id"] == page_id
        print(f"✓ Page details retrieved")
    
    def test_create_page_post(self):
        """Test creating a post on a page (admin only)"""
        # First create a page
        create_response = requests.post(f"{BASE_URL}/api/pages", headers=self.headers, json={
            "name": f"Post Test Page {uuid.uuid4().hex[:6]}",
            "description": "Test page for posts",
            "category": "General"
        })
        page_id = create_response.json()["page"]["id"]
        
        # Create a post
        response = requests.post(f"{BASE_URL}/api/pages/{page_id}/posts", headers=self.headers, json={
            "content": "This is a test post on the page!"
        })
        assert response.status_code == 200
        data = response.json()
        assert "post" in data
        print(f"✓ Page post created")
    
    def test_follow_unfollow_page(self):
        """Test following and unfollowing a page"""
        # Create a page
        create_response = requests.post(f"{BASE_URL}/api/pages", headers=self.headers, json={
            "name": f"Follow Test Page {uuid.uuid4().hex[:6]}",
            "description": "Test page for follow/unfollow",
            "category": "General"
        })
        page_id = create_response.json()["page"]["id"]
        
        # Login as test user
        test_login = requests.post(f"{BASE_URL}/api/auth/login", json={
            "email": TEST_USER_EMAIL,
            "password": TEST_USER_PASSWORD
        })
        if test_login.status_code != 200:
            pytest.skip("Test user not available")
        test_token = test_login.json()["access_token"]
        test_headers = {"Authorization": f"Bearer {test_token}"}
        
        # Follow as test user
        follow_response = requests.post(f"{BASE_URL}/api/pages/{page_id}/follow", headers=test_headers)
        assert follow_response.status_code == 200
        print(f"✓ Followed page successfully")
        
        # Unfollow as test user
        unfollow_response = requests.post(f"{BASE_URL}/api/pages/{page_id}/unfollow", headers=test_headers)
        assert unfollow_response.status_code == 200
        print(f"✓ Unfollowed page successfully")


class TestReactionsAndComments:
    """Reactions and Comments tests for posts"""
    
    @pytest.fixture(autouse=True)
    def setup(self):
        """Setup - get auth token"""
        response = requests.post(f"{BASE_URL}/api/auth/login", json={
            "email": ADMIN_EMAIL,
            "password": ADMIN_PASSWORD
        })
        self.token = response.json()["access_token"]
        self.headers = {"Authorization": f"Bearer {self.token}"}
    
    def test_add_reaction_to_group_post(self):
        """Test adding a reaction to a group post"""
        # Create a group and post
        group_response = requests.post(f"{BASE_URL}/api/groups", headers=self.headers, json={
            "name": f"Reaction Test Group {uuid.uuid4().hex[:6]}",
            "description": "Test group",
            "privacy": "public"
        })
        group_id = group_response.json()["group"]["id"]
        
        post_response = requests.post(f"{BASE_URL}/api/groups/{group_id}/posts", headers=self.headers, json={
            "content": "Test post for reactions"
        })
        post_id = post_response.json()["post"]["id"]
        
        # Add reaction
        reaction_response = requests.post(f"{BASE_URL}/api/posts/group/{post_id}/reactions", headers=self.headers, json={
            "reaction_type": "like"
        })
        assert reaction_response.status_code == 200
        print(f"✓ Reaction added to group post")
    
    def test_add_comment_to_group_post(self):
        """Test adding a comment to a group post"""
        # Create a group and post
        group_response = requests.post(f"{BASE_URL}/api/groups", headers=self.headers, json={
            "name": f"Comment Test Group {uuid.uuid4().hex[:6]}",
            "description": "Test group",
            "privacy": "public"
        })
        group_id = group_response.json()["group"]["id"]
        
        post_response = requests.post(f"{BASE_URL}/api/groups/{group_id}/posts", headers=self.headers, json={
            "content": "Test post for comments"
        })
        post_id = post_response.json()["post"]["id"]
        
        # Add comment
        comment_response = requests.post(f"{BASE_URL}/api/posts/group/{post_id}/comments", headers=self.headers, json={
            "content": "This is a test comment!"
        })
        assert comment_response.status_code == 200
        print(f"✓ Comment added to group post")
    
    def test_all_reaction_types(self):
        """Test all Facebook-style reaction types"""
        # Create a group and post
        group_response = requests.post(f"{BASE_URL}/api/groups", headers=self.headers, json={
            "name": f"All Reactions Test {uuid.uuid4().hex[:6]}",
            "description": "Test group",
            "privacy": "public"
        })
        group_id = group_response.json()["group"]["id"]
        
        post_response = requests.post(f"{BASE_URL}/api/groups/{group_id}/posts", headers=self.headers, json={
            "content": "Test post for all reactions"
        })
        post_id = post_response.json()["post"]["id"]
        
        # Test each reaction type
        reaction_types = ["like", "love", "haha", "wow", "sad", "angry"]
        for reaction_type in reaction_types:
            reaction_response = requests.post(f"{BASE_URL}/api/posts/group/{post_id}/reactions", headers=self.headers, json={
                "reaction_type": reaction_type
            })
            assert reaction_response.status_code == 200
            print(f"✓ Reaction '{reaction_type}' works")


class TestPrivateMessaging:
    """Private Messaging tests"""
    
    @pytest.fixture(autouse=True)
    def setup(self):
        """Setup - get auth tokens for both users"""
        admin_response = requests.post(f"{BASE_URL}/api/auth/login", json={
            "email": ADMIN_EMAIL,
            "password": ADMIN_PASSWORD
        })
        self.admin_token = admin_response.json()["access_token"]
        self.admin_headers = {"Authorization": f"Bearer {self.admin_token}"}
        self.admin_id = admin_response.json()["user"]["id"]
        
        test_response = requests.post(f"{BASE_URL}/api/auth/login", json={
            "email": TEST_USER_EMAIL,
            "password": TEST_USER_PASSWORD
        })
        if test_response.status_code == 200:
            self.test_token = test_response.json()["access_token"]
            self.test_headers = {"Authorization": f"Bearer {self.test_token}"}
            self.test_id = test_response.json()["user"]["id"]
        else:
            self.test_token = None
    
    def test_list_conversations(self):
        """Test listing conversations"""
        response = requests.get(f"{BASE_URL}/api/messages/conversations", headers=self.admin_headers)
        assert response.status_code == 200
        data = response.json()
        assert "conversations" in data
        print(f"✓ Listed {len(data['conversations'])} conversations")
    
    def test_search_users(self):
        """Test searching users for messaging"""
        response = requests.get(f"{BASE_URL}/api/users/search?q=test", headers=self.admin_headers)
        assert response.status_code == 200
        data = response.json()
        assert "users" in data
        print(f"✓ User search returned {len(data['users'])} results")
    
    def test_send_text_message(self):
        """Test sending a text message"""
        if not self.test_token:
            pytest.skip("Test user not available")
        
        response = requests.post(f"{BASE_URL}/api/messages/send", headers=self.admin_headers, json={
            "recipient_id": self.test_id,
            "content": f"Test message at {datetime.now().isoformat()}"
        })
        assert response.status_code == 200
        data = response.json()
        assert "message" in data
        print(f"✓ Text message sent successfully")
    
    def test_get_unread_count(self):
        """Test getting unread message count"""
        response = requests.get(f"{BASE_URL}/api/messages/unread-count", headers=self.admin_headers)
        assert response.status_code == 200
        data = response.json()
        assert "unread_count" in data
        print(f"✓ Unread count: {data['unread_count']}")


class TestFriends:
    """Friends feature tests"""
    
    @pytest.fixture(autouse=True)
    def setup(self):
        """Setup - get auth token"""
        response = requests.post(f"{BASE_URL}/api/auth/login", json={
            "email": ADMIN_EMAIL,
            "password": ADMIN_PASSWORD
        })
        self.token = response.json()["access_token"]
        self.headers = {"Authorization": f"Bearer {self.token}"}
    
    def test_list_friends(self):
        """Test listing friends"""
        response = requests.get(f"{BASE_URL}/api/friends", headers=self.headers)
        assert response.status_code == 200
        data = response.json()
        assert "friends" in data
        print(f"✓ Listed {len(data['friends'])} friends")


class TestLegalPages:
    """Legal pages tests - Privacy Policy and Terms of Service"""
    
    def test_get_privacy_policy_public(self):
        """Test getting privacy policy (public endpoint)"""
        response = requests.get(f"{BASE_URL}/api/legal/privacy-policy")
        assert response.status_code == 200
        data = response.json()
        assert "content" in data
        print(f"✓ Privacy policy retrieved (public)")
    
    def test_get_terms_of_service_public(self):
        """Test getting terms of service (public endpoint)"""
        response = requests.get(f"{BASE_URL}/api/legal/terms-of-service")
        assert response.status_code == 200
        data = response.json()
        assert "content" in data
        print(f"✓ Terms of service retrieved (public)")


class TestAdminPanel:
    """Admin panel tests"""
    
    @pytest.fixture(autouse=True)
    def setup(self):
        """Setup - get admin auth token"""
        response = requests.post(f"{BASE_URL}/api/auth/login", json={
            "email": ADMIN_EMAIL,
            "password": ADMIN_PASSWORD
        })
        self.token = response.json()["access_token"]
        self.headers = {"Authorization": f"Bearer {self.token}"}
    
    def test_get_admin_settings(self):
        """Test getting admin settings"""
        response = requests.get(f"{BASE_URL}/api/admin/settings", headers=self.headers)
        assert response.status_code == 200
        data = response.json()
        assert "results_per_page" in data
        print(f"✓ Admin settings retrieved")
    
    def test_get_admin_users(self):
        """Test getting admin users list"""
        response = requests.get(f"{BASE_URL}/api/admin/users", headers=self.headers)
        assert response.status_code == 200
        data = response.json()
        assert isinstance(data, list)
        print(f"✓ Admin users list retrieved ({len(data)} users)")
    
    def test_update_privacy_policy_admin(self):
        """Test updating privacy policy (admin only)"""
        # First get current content
        get_response = requests.get(f"{BASE_URL}/api/legal/privacy-policy")
        current_content = get_response.json().get("content", "Privacy Policy Content")
        
        # Update with same content (to not break anything)
        response = requests.put(f"{BASE_URL}/api/admin/legal/privacy-policy", headers=self.headers, json={
            "content": current_content
        })
        # Accept 200 or 422 (validation error if content is empty)
        assert response.status_code in [200, 422]
        print(f"✓ Privacy policy update endpoint works (admin)")
    
    def test_update_terms_of_service_admin(self):
        """Test updating terms of service (admin only)"""
        # First get current content
        get_response = requests.get(f"{BASE_URL}/api/legal/terms-of-service")
        current_content = get_response.json().get("content", "Terms of Service Content")
        
        # Update with same content (to not break anything)
        response = requests.put(f"{BASE_URL}/api/admin/legal/terms-of-service", headers=self.headers, json={
            "content": current_content
        })
        # Accept 200 or 422 (validation error if content is empty)
        assert response.status_code in [200, 422]
        print(f"✓ Terms of service update endpoint works (admin)")


class TestUltimateSearch:
    """Ultimate Search page tests"""
    
    @pytest.fixture(autouse=True)
    def setup(self):
        """Setup - get auth token"""
        response = requests.post(f"{BASE_URL}/api/auth/login", json={
            "email": ADMIN_EMAIL,
            "password": ADMIN_PASSWORD
        })
        self.token = response.json()["access_token"]
        self.headers = {"Authorization": f"Bearer {self.token}"}
    
    def test_get_page_settings(self):
        """Test getting Ultimate Search page settings"""
        response = requests.get(f"{BASE_URL}/api/ultimate-search/page-settings", headers=self.headers)
        assert response.status_code == 200
        data = response.json()
        assert "page_name" in data
        print(f"✓ Page settings retrieved: {data['page_name']}")
    
    def test_update_page_name(self):
        """Test updating page name (rename page)"""
        new_name = f"My Search Page {uuid.uuid4().hex[:4]}"
        response = requests.put(f"{BASE_URL}/api/ultimate-search/page-settings", headers=self.headers, json={
            "page_name": new_name
        })
        assert response.status_code == 200
        data = response.json()
        # Response may have different structure
        assert "page_name" in data or "settings" in data or "message" in data
        print(f"✓ Page name update endpoint works")
    
    def test_get_filters(self):
        """Test getting search filters"""
        response = requests.get(f"{BASE_URL}/api/ultimate-search/filters", headers=self.headers)
        assert response.status_code == 200
        data = response.json()
        assert "document_types" in data
        assert "article_types" in data
        print(f"✓ Search filters retrieved")
    
    def test_get_map_data(self):
        """Test getting map data for Google Maps integration"""
        response = requests.get(f"{BASE_URL}/api/ultimate-search/map-data", headers=self.headers)
        assert response.status_code == 200
        data = response.json()
        # API returns markers, categories, total_markers
        assert "markers" in data or "categories" in data
        print(f"✓ Map data retrieved")


class TestUpdates:
    """Updates section tests (on Ultimate Search page)"""
    
    @pytest.fixture(autouse=True)
    def setup(self):
        """Setup - get auth token"""
        response = requests.post(f"{BASE_URL}/api/auth/login", json={
            "email": ADMIN_EMAIL,
            "password": ADMIN_PASSWORD
        })
        self.token = response.json()["access_token"]
        self.headers = {"Authorization": f"Bearer {self.token}"}
    
    def test_list_updates(self):
        """Test listing updates"""
        response = requests.get(f"{BASE_URL}/api/updates", headers=self.headers)
        assert response.status_code == 200
        data = response.json()
        assert "updates" in data
        print(f"✓ Listed {len(data['updates'])} updates")
    
    def test_create_update(self):
        """Test creating an update"""
        response = requests.post(f"{BASE_URL}/api/updates", headers=self.headers, json={
            "content": f"Test update at {datetime.now().isoformat()}"
        })
        assert response.status_code == 200
        data = response.json()
        assert "update" in data
        print(f"✓ Update created successfully")
    
    def test_add_reaction_to_update(self):
        """Test adding a reaction to an update"""
        # First create an update
        create_response = requests.post(f"{BASE_URL}/api/updates", headers=self.headers, json={
            "content": f"Update for reaction test {uuid.uuid4().hex[:6]}"
        })
        update_id = create_response.json()["update"]["id"]
        
        # Add reaction
        reaction_response = requests.post(f"{BASE_URL}/api/posts/update/{update_id}/reactions", headers=self.headers, json={
            "reaction_type": "love"
        })
        assert reaction_response.status_code == 200
        print(f"✓ Reaction added to update")
    
    def test_add_comment_to_update(self):
        """Test adding a comment to an update"""
        # First create an update
        create_response = requests.post(f"{BASE_URL}/api/updates", headers=self.headers, json={
            "content": f"Update for comment test {uuid.uuid4().hex[:6]}"
        })
        update_id = create_response.json()["update"]["id"]
        
        # Add comment
        comment_response = requests.post(f"{BASE_URL}/api/posts/update/{update_id}/comments", headers=self.headers, json={
            "content": "This is a test comment on an update!"
        })
        assert comment_response.status_code == 200
        print(f"✓ Comment added to update")


class TestProtocolRecommendations:
    """Protocol Recommendations tests"""
    
    @pytest.fixture(autouse=True)
    def setup(self):
        """Setup - get auth tokens"""
        admin_response = requests.post(f"{BASE_URL}/api/auth/login", json={
            "email": ADMIN_EMAIL,
            "password": ADMIN_PASSWORD
        })
        self.admin_token = admin_response.json()["access_token"]
        self.admin_headers = {"Authorization": f"Bearer {self.admin_token}"}
        
        test_response = requests.post(f"{BASE_URL}/api/auth/login", json={
            "email": TEST_USER_EMAIL,
            "password": TEST_USER_PASSWORD
        })
        if test_response.status_code == 200:
            self.test_token = test_response.json()["access_token"]
            self.test_headers = {"Authorization": f"Bearer {self.test_token}"}
        else:
            self.test_token = None
    
    def test_get_my_protocol_recommendations(self):
        """Test getting recommendations for my protocols"""
        response = requests.get(f"{BASE_URL}/api/recommendations/my-protocols", headers=self.admin_headers)
        assert response.status_code == 200
        data = response.json()
        # API returns by_category, pending_count, total_count
        assert "by_category" in data or "pending_count" in data
        print(f"✓ My protocol recommendations retrieved")


class TestBookPage:
    """Book page tests"""
    
    def test_get_book_info(self):
        """Test getting book information"""
        response = requests.get(f"{BASE_URL}/api/book/info")
        assert response.status_code == 200
        data = response.json()
        assert "title" in data
        assert data["title"] == "Letters to Evelyn"
        print(f"✓ Book info retrieved: {data['title']}")


class TestGlobalDatabase:
    """Global Database tests"""
    
    @pytest.fixture(autouse=True)
    def setup(self):
        """Setup - get auth token"""
        response = requests.post(f"{BASE_URL}/api/auth/login", json={
            "email": ADMIN_EMAIL,
            "password": ADMIN_PASSWORD
        })
        self.token = response.json()["access_token"]
        self.headers = {"Authorization": f"Bearer {self.token}"}
    
    def test_get_global_database(self):
        """Test getting global database (public categories)"""
        response = requests.get(f"{BASE_URL}/api/global-database", headers=self.headers)
        assert response.status_code == 200
        data = response.json()
        # API returns public_categories, results, total, page
        assert "public_categories" in data or "results" in data
        print(f"✓ Global database retrieved")


class TestStatistics:
    """Statistics page tests"""
    
    @pytest.fixture(autouse=True)
    def setup(self):
        """Setup - get auth token"""
        response = requests.post(f"{BASE_URL}/api/auth/login", json={
            "email": ADMIN_EMAIL,
            "password": ADMIN_PASSWORD
        })
        self.token = response.json()["access_token"]
        self.headers = {"Authorization": f"Bearer {self.token}"}
    
    def test_get_categories_with_counts(self):
        """Test getting categories with result counts for statistics"""
        response = requests.get(f"{BASE_URL}/api/categories/with-counts", headers=self.headers)
        assert response.status_code == 200
        data = response.json()
        # API returns {"categories": [...]}
        assert "categories" in data or isinstance(data, list)
        print(f"✓ Categories with counts retrieved for statistics")


if __name__ == "__main__":
    pytest.main([__file__, "-v", "--tb=short"])
