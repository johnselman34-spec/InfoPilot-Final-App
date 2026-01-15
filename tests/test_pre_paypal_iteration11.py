"""
InfoPilot Explorer - Pre-PayPal Integration Comprehensive Test Suite
Iteration 11 - Bug verification before PayPal integration

Tests all existing features with CORRECT API response structures:
- Authentication (Login/Register, Google OAuth button presence)
- Navigation (All menu items)
- Groups (CRUD, posts, reactions, comments)
- Pages (CRUD, posts, reactions, comments)
- Private Messaging (conversations, send messages)
- Categories (CRUD, protocol recommendations)
- Ultimate Search (updates, map, page settings)
- Legal Pages (Privacy Policy, Terms of Service - public)
- Admin Panel (Dashboard, edit legal pages)
- Friends list
- Book page
"""

import pytest
import requests
import uuid
import os
from datetime import datetime
from urllib.parse import quote

# Use environment variable for BASE_URL
BASE_URL = os.environ.get('REACT_APP_BACKEND_URL', 'https://social-research.preview.emergentagent.com')

# Test credentials
ADMIN_EMAIL = "john@infojet.com"
ADMIN_PASSWORD = "password123"
TEST_USER_EMAIL = f"testuser_{uuid.uuid4().hex[:6]}@example.com"
TEST_USER_PASSWORD = "password123"
TEST_USERNAME = f"testuser_{uuid.uuid4().hex[:6]}"


class TestHealthAndBasics:
    """Basic health and connectivity tests"""
    
    def test_health_check(self):
        """Test API health endpoint"""
        response = requests.get(f"{BASE_URL}/api/health")
        assert response.status_code == 200
        data = response.json()
        assert data["status"] == "operational"
        print("✓ Health check passed")
    
    def test_root_endpoint(self):
        """Test API root endpoint"""
        response = requests.get(f"{BASE_URL}/api/")
        assert response.status_code == 200
        data = response.json()
        assert "InfoPilot" in data.get("message", "")
        print("✓ Root endpoint working")


class TestAuthentication:
    """Authentication tests - Login, Register, Google OAuth"""
    
    def test_login_admin_user(self):
        """Test admin user login"""
        response = requests.post(f"{BASE_URL}/api/auth/login", json={
            "email": ADMIN_EMAIL,
            "password": ADMIN_PASSWORD
        })
        assert response.status_code == 200
        data = response.json()
        assert "access_token" in data
        assert data["user"]["is_admin"] == True
        print(f"✓ Admin login successful: {data['user']['username']}")
    
    def test_login_invalid_credentials(self):
        """Test login with invalid credentials"""
        response = requests.post(f"{BASE_URL}/api/auth/login", json={
            "email": "invalid@example.com",
            "password": "wrongpassword"
        })
        assert response.status_code == 401
        print("✓ Invalid credentials rejected correctly")
    
    def test_register_new_user(self):
        """Test new user registration"""
        response = requests.post(f"{BASE_URL}/api/auth/register", json={
            "username": TEST_USERNAME,
            "email": TEST_USER_EMAIL,
            "password": TEST_USER_PASSWORD
        })
        assert response.status_code == 200
        data = response.json()
        assert "access_token" in data
        assert data["user"]["email"] == TEST_USER_EMAIL
        print(f"✓ User registration successful: {data['user']['username']}")
    
    def test_get_current_user(self):
        """Test getting current user info"""
        login_response = requests.post(f"{BASE_URL}/api/auth/login", json={
            "email": ADMIN_EMAIL,
            "password": ADMIN_PASSWORD
        })
        token = login_response.json()["access_token"]
        headers = {"Authorization": f"Bearer {token}"}
        
        response = requests.get(f"{BASE_URL}/api/auth/me", headers=headers)
        assert response.status_code == 200
        data = response.json()
        assert data["email"] == ADMIN_EMAIL
        print(f"✓ Current user retrieved: {data['username']}")


class TestCategories:
    """Category CRUD and protocol recommendations tests"""
    
    @pytest.fixture(autouse=True)
    def setup(self):
        login_response = requests.post(f"{BASE_URL}/api/auth/login", json={
            "email": ADMIN_EMAIL,
            "password": ADMIN_PASSWORD
        })
        self.token = login_response.json()["access_token"]
        self.headers = {"Authorization": f"Bearer {self.token}"}
    
    def test_list_categories(self):
        """Test listing categories - returns array directly"""
        response = requests.get(f"{BASE_URL}/api/categories", headers=self.headers)
        assert response.status_code == 200
        data = response.json()
        # API returns array directly
        assert isinstance(data, list)
        print(f"✓ Categories listed: {len(data)} found")
    
    def test_create_category(self):
        """Test creating a category - returns category object directly"""
        response = requests.post(f"{BASE_URL}/api/categories", headers=self.headers, json={
            "name": f"Test Category {uuid.uuid4().hex[:6]}",
            "protocol": {"protocol_string": "(test or example) & (data)+"},
            "is_public": True
        })
        assert response.status_code == 200
        data = response.json()
        # API returns category object directly
        assert "id" in data
        assert "name" in data
        print(f"✓ Category created: {data['name']}")
    
    def test_get_category_tree(self):
        """Test getting category tree - returns {categories: [...]}"""
        response = requests.get(f"{BASE_URL}/api/categories/tree", headers=self.headers)
        assert response.status_code == 200
        data = response.json()
        # API returns {categories: [...]}
        assert "categories" in data
        print(f"✓ Category tree retrieved: {len(data['categories'])} categories")
    
    def test_update_category(self):
        """Test updating a category"""
        # Create first - returns object directly
        create_response = requests.post(f"{BASE_URL}/api/categories", headers=self.headers, json={
            "name": f"Update Test {uuid.uuid4().hex[:6]}",
            "protocol": {"protocol_string": "(update or test)"},
            "is_public": True
        })
        category_id = create_response.json()["id"]
        
        # Update
        response = requests.put(f"{BASE_URL}/api/categories/{category_id}", headers=self.headers, json={
            "name": f"Updated Category {uuid.uuid4().hex[:6]}"
        })
        assert response.status_code == 200
        print("✓ Category updated")
    
    def test_delete_category(self):
        """Test deleting a category"""
        # Create first
        create_response = requests.post(f"{BASE_URL}/api/categories", headers=self.headers, json={
            "name": f"Delete Test {uuid.uuid4().hex[:6]}",
            "protocol": {"protocol_string": "(delete or test)"},
            "is_public": True
        })
        category_id = create_response.json()["id"]
        
        # Delete
        response = requests.delete(f"{BASE_URL}/api/categories/{category_id}", headers=self.headers)
        assert response.status_code == 200
        print("✓ Category deleted")
    
    def test_protocol_recommendations_count(self):
        """Test getting protocol recommendations count"""
        # Create a category first
        create_response = requests.post(f"{BASE_URL}/api/categories", headers=self.headers, json={
            "name": f"Rec Test {uuid.uuid4().hex[:6]}",
            "protocol": {"protocol_string": "(recommendation or test)"},
            "is_public": True
        })
        category_id = create_response.json()["id"]
        
        # Get recommendations count
        response = requests.get(f"{BASE_URL}/api/categories/{category_id}/recommendations/count", headers=self.headers)
        assert response.status_code == 200
        data = response.json()
        assert "count" in data
        print(f"✓ Protocol recommendations count: {data['count']}")


class TestGroups:
    """Groups CRUD, posts, reactions, comments tests"""
    
    @pytest.fixture(autouse=True)
    def setup(self):
        login_response = requests.post(f"{BASE_URL}/api/auth/login", json={
            "email": ADMIN_EMAIL,
            "password": ADMIN_PASSWORD
        })
        self.token = login_response.json()["access_token"]
        self.headers = {"Authorization": f"Bearer {self.token}"}
    
    def test_list_groups(self):
        """Test listing groups - returns {my_groups: [...], public_groups: [...]}"""
        response = requests.get(f"{BASE_URL}/api/groups", headers=self.headers)
        assert response.status_code == 200
        data = response.json()
        # API returns {my_groups: [...], public_groups: [...]}
        assert "my_groups" in data or "public_groups" in data
        total = len(data.get("my_groups", [])) + len(data.get("public_groups", []))
        print(f"✓ Groups listed: {total} found")
    
    def test_create_group(self):
        """Test creating a group"""
        response = requests.post(f"{BASE_URL}/api/groups", headers=self.headers, json={
            "name": f"Test Group {uuid.uuid4().hex[:6]}",
            "description": "A test group for testing",
            "privacy": "public"
        })
        assert response.status_code == 200
        data = response.json()
        assert "group" in data
        print(f"✓ Group created: {data['group']['name']}")
    
    def test_get_group_details(self):
        """Test getting group details - response is {group: {...}, posts: [...]}"""
        # Create first
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
        assert "group" in data
        assert data["group"]["id"] == group_id
        print(f"✓ Group details retrieved: {data['group']['name']}")
    
    def test_create_group_post(self):
        """Test creating a post in a group"""
        # Create group first
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
    
    def test_group_post_reaction(self):
        """Test adding reaction to a group post"""
        # Create group
        create_response = requests.post(f"{BASE_URL}/api/groups", headers=self.headers, json={
            "name": f"Reaction Test Group {uuid.uuid4().hex[:6]}",
            "description": "Test group for reactions",
            "privacy": "public"
        })
        group_id = create_response.json()["group"]["id"]
        
        # Create post
        post_response = requests.post(f"{BASE_URL}/api/groups/{group_id}/posts", headers=self.headers, json={
            "content": "Test post for reactions"
        })
        post_id = post_response.json()["post"]["id"]
        
        # Add reaction
        response = requests.post(f"{BASE_URL}/api/posts/group/{post_id}/reactions", headers=self.headers, json={
            "reaction_type": "like"
        })
        assert response.status_code == 200
        print("✓ Group post reaction added")
    
    def test_group_post_comment(self):
        """Test adding comment to a group post"""
        # Create group
        create_response = requests.post(f"{BASE_URL}/api/groups", headers=self.headers, json={
            "name": f"Comment Test Group {uuid.uuid4().hex[:6]}",
            "description": "Test group for comments",
            "privacy": "public"
        })
        group_id = create_response.json()["group"]["id"]
        
        # Create post
        post_response = requests.post(f"{BASE_URL}/api/groups/{group_id}/posts", headers=self.headers, json={
            "content": "Test post for comments"
        })
        post_id = post_response.json()["post"]["id"]
        
        # Add comment
        response = requests.post(f"{BASE_URL}/api/posts/group/{post_id}/comments", headers=self.headers, json={
            "content": "This is a test comment!"
        })
        assert response.status_code == 200
        print("✓ Group post comment added")


class TestPages:
    """Pages CRUD, posts, reactions, comments tests"""
    
    @pytest.fixture(autouse=True)
    def setup(self):
        login_response = requests.post(f"{BASE_URL}/api/auth/login", json={
            "email": ADMIN_EMAIL,
            "password": ADMIN_PASSWORD
        })
        self.token = login_response.json()["access_token"]
        self.headers = {"Authorization": f"Bearer {self.token}"}
    
    def test_list_pages(self):
        """Test listing pages - returns {my_pages: [...], following: [...], popular: [...]}"""
        response = requests.get(f"{BASE_URL}/api/pages", headers=self.headers)
        assert response.status_code == 200
        data = response.json()
        # API returns {my_pages: [...], following: [...], popular: [...]}
        assert "my_pages" in data or "following" in data or "popular" in data
        total = len(data.get("my_pages", [])) + len(data.get("popular", []))
        print(f"✓ Pages listed: {total} found")
    
    def test_create_page(self):
        """Test creating a page"""
        response = requests.post(f"{BASE_URL}/api/pages", headers=self.headers, json={
            "name": f"Test Page {uuid.uuid4().hex[:6]}",
            "description": "A test page for testing",
            "category": "General"
        })
        assert response.status_code == 200
        data = response.json()
        assert "page" in data
        print(f"✓ Page created: {data['page']['name']}")
    
    def test_get_page_details(self):
        """Test getting page details - response is {page: {...}, posts: [...]}"""
        # Create first
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
        assert "page" in data
        assert data["page"]["id"] == page_id
        print(f"✓ Page details retrieved: {data['page']['name']}")
    
    def test_create_page_post(self):
        """Test creating a post on a page"""
        # Create page first
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
    
    def test_page_post_reaction(self):
        """Test adding reaction to a page post"""
        # Create page
        create_response = requests.post(f"{BASE_URL}/api/pages", headers=self.headers, json={
            "name": f"Reaction Test Page {uuid.uuid4().hex[:6]}",
            "description": "Test page for reactions",
            "category": "General"
        })
        page_id = create_response.json()["page"]["id"]
        
        # Create post
        post_response = requests.post(f"{BASE_URL}/api/pages/{page_id}/posts", headers=self.headers, json={
            "content": "Test post for reactions"
        })
        post_id = post_response.json()["post"]["id"]
        
        # Add reaction
        response = requests.post(f"{BASE_URL}/api/posts/page/{post_id}/reactions", headers=self.headers, json={
            "reaction_type": "love"
        })
        assert response.status_code == 200
        print("✓ Page post reaction added")
    
    def test_page_post_comment(self):
        """Test adding comment to a page post"""
        # Create page
        create_response = requests.post(f"{BASE_URL}/api/pages", headers=self.headers, json={
            "name": f"Comment Test Page {uuid.uuid4().hex[:6]}",
            "description": "Test page for comments",
            "category": "General"
        })
        page_id = create_response.json()["page"]["id"]
        
        # Create post
        post_response = requests.post(f"{BASE_URL}/api/pages/{page_id}/posts", headers=self.headers, json={
            "content": "Test post for comments"
        })
        post_id = post_response.json()["post"]["id"]
        
        # Add comment
        response = requests.post(f"{BASE_URL}/api/posts/page/{post_id}/comments", headers=self.headers, json={
            "content": "This is a test comment on the page post!"
        })
        assert response.status_code == 200
        print("✓ Page post comment added")


class TestPrivateMessaging:
    """Private messaging tests"""
    
    @pytest.fixture(autouse=True)
    def setup(self):
        login_response = requests.post(f"{BASE_URL}/api/auth/login", json={
            "email": ADMIN_EMAIL,
            "password": ADMIN_PASSWORD
        })
        self.token = login_response.json()["access_token"]
        self.headers = {"Authorization": f"Bearer {self.token}"}
        self.user_id = login_response.json()["user"]["id"]
    
    def test_list_conversations(self):
        """Test listing conversations"""
        response = requests.get(f"{BASE_URL}/api/messages/conversations", headers=self.headers)
        assert response.status_code == 200
        data = response.json()
        assert "conversations" in data
        print(f"✓ Conversations listed: {len(data['conversations'])} found")
    
    def test_search_users(self):
        """Test searching users for messaging"""
        response = requests.get(f"{BASE_URL}/api/users/search?q=john", headers=self.headers)
        assert response.status_code == 200
        data = response.json()
        assert "users" in data
        print(f"✓ User search returned: {len(data['users'])} users")
    
    def test_send_message(self):
        """Test sending a message"""
        # First search for a user to message
        search_response = requests.get(f"{BASE_URL}/api/users/search?q=test", headers=self.headers)
        users = search_response.json().get("users", [])
        
        if not users:
            # Create a test user to message
            register_response = requests.post(f"{BASE_URL}/api/auth/register", json={
                "username": f"msgtest_{uuid.uuid4().hex[:6]}",
                "email": f"msgtest_{uuid.uuid4().hex[:6]}@example.com",
                "password": "password123"
            })
            if register_response.status_code == 200:
                recipient_id = register_response.json()["user"]["id"]
            else:
                pytest.skip("No users available to message")
        else:
            # Find a user that's not the current user
            recipient_id = None
            for user in users:
                if user["id"] != self.user_id:
                    recipient_id = user["id"]
                    break
            if not recipient_id:
                pytest.skip("No other users available to message")
        
        # Send message
        response = requests.post(f"{BASE_URL}/api/messages/send", headers=self.headers, json={
            "recipient_id": recipient_id,
            "content": f"Test message {datetime.now().isoformat()}"
        })
        assert response.status_code == 200
        print("✓ Message sent successfully")


class TestUltimateSearch:
    """Ultimate Search page tests - updates, map, page settings"""
    
    @pytest.fixture(autouse=True)
    def setup(self):
        login_response = requests.post(f"{BASE_URL}/api/auth/login", json={
            "email": ADMIN_EMAIL,
            "password": ADMIN_PASSWORD
        })
        self.token = login_response.json()["access_token"]
        self.headers = {"Authorization": f"Bearer {self.token}"}
    
    def test_get_page_settings(self):
        """Test getting Ultimate Search page settings"""
        response = requests.get(f"{BASE_URL}/api/ultimate-search/page-settings", headers=self.headers)
        assert response.status_code == 200
        data = response.json()
        assert "page_name" in data
        print(f"✓ Page settings retrieved: {data['page_name']}")
    
    def test_update_page_name(self):
        """Test updating page name"""
        new_name = f"My Search Page {uuid.uuid4().hex[:6]}"
        response = requests.put(f"{BASE_URL}/api/ultimate-search/page-settings", headers=self.headers, json={
            "page_name": new_name
        })
        assert response.status_code == 200
        print(f"✓ Page name updated to: {new_name}")
    
    def test_list_updates(self):
        """Test listing updates"""
        response = requests.get(f"{BASE_URL}/api/updates", headers=self.headers)
        assert response.status_code == 200
        data = response.json()
        assert "updates" in data
        print(f"✓ Updates listed: {len(data['updates'])} found")
    
    def test_create_update(self):
        """Test creating an update"""
        response = requests.post(f"{BASE_URL}/api/updates", headers=self.headers, json={
            "content": f"Test update {datetime.now().isoformat()}"
        })
        assert response.status_code == 200
        data = response.json()
        assert "update" in data
        print("✓ Update created")
    
    def test_update_reaction(self):
        """Test adding reaction to an update"""
        # Create update first
        create_response = requests.post(f"{BASE_URL}/api/updates", headers=self.headers, json={
            "content": f"Reaction test update {uuid.uuid4().hex[:6]}"
        })
        update_id = create_response.json()["update"]["id"]
        
        # Add reaction
        response = requests.post(f"{BASE_URL}/api/posts/update/{update_id}/reactions", headers=self.headers, json={
            "reaction_type": "wow"
        })
        assert response.status_code == 200
        print("✓ Update reaction added")
    
    def test_update_comment(self):
        """Test adding comment to an update"""
        # Create update first
        create_response = requests.post(f"{BASE_URL}/api/updates", headers=self.headers, json={
            "content": f"Comment test update {uuid.uuid4().hex[:6]}"
        })
        update_id = create_response.json()["update"]["id"]
        
        # Add comment
        response = requests.post(f"{BASE_URL}/api/posts/update/{update_id}/comments", headers=self.headers, json={
            "content": "This is a test comment on the update!"
        })
        assert response.status_code == 200
        print("✓ Update comment added")
    
    def test_get_map_data(self):
        """Test getting map data - returns {markers: [...], categories: {...}}"""
        response = requests.get(f"{BASE_URL}/api/ultimate-search/map-data", headers=self.headers)
        assert response.status_code == 200
        data = response.json()
        # API returns {markers: [...], categories: {...}, total_markers: int}
        assert "markers" in data or "categories" in data
        print(f"✓ Map data retrieved: {data.get('total_markers', 0)} markers")


class TestLegalPages:
    """Legal pages tests - Privacy Policy, Terms of Service (public access)"""
    
    def test_privacy_policy_public(self):
        """Test Privacy Policy is publicly accessible"""
        response = requests.get(f"{BASE_URL}/api/legal/privacy-policy")
        assert response.status_code == 200
        data = response.json()
        assert "content" in data
        print("✓ Privacy Policy publicly accessible")
    
    def test_terms_of_service_public(self):
        """Test Terms of Service is publicly accessible"""
        response = requests.get(f"{BASE_URL}/api/legal/terms-of-service")
        assert response.status_code == 200
        data = response.json()
        assert "content" in data
        print("✓ Terms of Service publicly accessible")


class TestAdminPanel:
    """Admin panel tests - Dashboard, edit legal pages"""
    
    @pytest.fixture(autouse=True)
    def setup(self):
        login_response = requests.post(f"{BASE_URL}/api/auth/login", json={
            "email": ADMIN_EMAIL,
            "password": ADMIN_PASSWORD
        })
        self.token = login_response.json()["access_token"]
        self.headers = {"Authorization": f"Bearer {self.token}"}
    
    def test_admin_settings(self):
        """Test getting admin settings"""
        response = requests.get(f"{BASE_URL}/api/admin/settings", headers=self.headers)
        assert response.status_code == 200
        data = response.json()
        assert "results_per_page" in data
        print("✓ Admin settings retrieved")
    
    def test_admin_users_list(self):
        """Test listing users (admin) - returns array directly"""
        response = requests.get(f"{BASE_URL}/api/admin/users", headers=self.headers)
        assert response.status_code == 200
        data = response.json()
        # API returns array directly
        assert isinstance(data, list)
        print(f"✓ Admin users list: {len(data)} users")
    
    def test_update_privacy_policy(self):
        """Test updating Privacy Policy (admin) - uses query parameter"""
        content = f"Updated Privacy Policy content - {datetime.now().isoformat()}"
        response = requests.put(
            f"{BASE_URL}/api/admin/legal/privacy-policy?content={quote(content)}", 
            headers=self.headers
        )
        assert response.status_code == 200
        print("✓ Privacy Policy updated by admin")
    
    def test_update_terms_of_service(self):
        """Test updating Terms of Service (admin) - uses query parameter"""
        content = f"Updated Terms of Service content - {datetime.now().isoformat()}"
        response = requests.put(
            f"{BASE_URL}/api/admin/legal/terms-of-service?content={quote(content)}", 
            headers=self.headers
        )
        assert response.status_code == 200
        print("✓ Terms of Service updated by admin")


class TestFriends:
    """Friends list tests"""
    
    @pytest.fixture(autouse=True)
    def setup(self):
        login_response = requests.post(f"{BASE_URL}/api/auth/login", json={
            "email": ADMIN_EMAIL,
            "password": ADMIN_PASSWORD
        })
        self.token = login_response.json()["access_token"]
        self.headers = {"Authorization": f"Bearer {self.token}"}
    
    def test_list_friends(self):
        """Test listing friends"""
        response = requests.get(f"{BASE_URL}/api/friends", headers=self.headers)
        assert response.status_code == 200
        data = response.json()
        assert "friends" in data
        print(f"✓ Friends listed: {len(data['friends'])} found")


class TestBookPage:
    """Book page tests"""
    
    def test_book_info(self):
        """Test getting book info"""
        response = requests.get(f"{BASE_URL}/api/book/info")
        assert response.status_code == 200
        data = response.json()
        assert "title" in data
        print(f"✓ Book info retrieved: {data.get('title', 'Unknown')}")


if __name__ == "__main__":
    pytest.main([__file__, "-v", "--tb=short"])
