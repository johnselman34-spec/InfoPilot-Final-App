"""
InfoPilot Explorer API Tests - Iteration 6
Tests for: 
- BLOCKED WORDS: Word boundary matching (association allowed, standalone ass blocked)
- SOCIAL FEATURES: Friends, Groups, Pages (Facebook-like)
- AUTH: Registration with admin as first friend
- CATEGORIES: Case-insensitivity note in protocol help
"""
import pytest
import requests
import os
import uuid
import time

BASE_URL = os.environ.get('REACT_APP_BACKEND_URL', 'https://explorer-social.preview.emergentagent.com')

# Test credentials
ADMIN_EMAIL = "john@infojet.com"
ADMIN_PASSWORD = "password123"


class TestBlockedWordsFilter:
    """CRITICAL: Test blocked words filter uses word boundaries"""
    
    @pytest.fixture
    def auth_token(self):
        """Get authentication token"""
        response = requests.post(f"{BASE_URL}/api/auth/login", json={
            "email": ADMIN_EMAIL,
            "password": ADMIN_PASSWORD
        })
        return response.json()["access_token"]
    
    def test_association_allowed(self, auth_token):
        """Test 'association' is allowed (contains 'ass' as substring but not standalone)"""
        unique_name = f"TEST_Association_{uuid.uuid4().hex[:6]}"
        response = requests.post(f"{BASE_URL}/api/categories",
            headers={"Authorization": f"Bearer {auth_token}"},
            json={
                "name": unique_name,
                "protocol": {"protocol_string": "(association or organization)"},
                "is_public": True
            })
        assert response.status_code == 200, f"Expected 200, got {response.status_code}: {response.text}"
        data = response.json()
        assert data["name"] == unique_name
        
        # Cleanup
        requests.delete(f"{BASE_URL}/api/categories/{data['id']}", 
            headers={"Authorization": f"Bearer {auth_token}"})
    
    def test_class_allowed(self, auth_token):
        """Test 'class' is allowed (contains 'ass' as substring but not standalone)"""
        unique_name = f"TEST_Class_{uuid.uuid4().hex[:6]}"
        response = requests.post(f"{BASE_URL}/api/categories",
            headers={"Authorization": f"Bearer {auth_token}"},
            json={
                "name": unique_name,
                "protocol": {"protocol_string": "(class or classroom)"},
                "is_public": True
            })
        assert response.status_code == 200, f"Expected 200, got {response.status_code}: {response.text}"
        data = response.json()
        assert data["name"] == unique_name
        
        # Cleanup
        requests.delete(f"{BASE_URL}/api/categories/{data['id']}", 
            headers={"Authorization": f"Bearer {auth_token}"})
    
    def test_assistant_allowed(self, auth_token):
        """Test 'assistant' is allowed (contains 'ass' as substring but not standalone)"""
        unique_name = f"TEST_Assistant_{uuid.uuid4().hex[:6]}"
        response = requests.post(f"{BASE_URL}/api/categories",
            headers={"Authorization": f"Bearer {auth_token}"},
            json={
                "name": unique_name,
                "protocol": {"protocol_string": "(assistant or helper)"},
                "is_public": True
            })
        assert response.status_code == 200, f"Expected 200, got {response.status_code}: {response.text}"
        data = response.json()
        assert data["name"] == unique_name
        
        # Cleanup
        requests.delete(f"{BASE_URL}/api/categories/{data['id']}", 
            headers={"Authorization": f"Bearer {auth_token}"})
    
    def test_standalone_ass_blocked(self, auth_token):
        """Test standalone 'ass' is blocked"""
        unique_name = f"TEST_Bad_{uuid.uuid4().hex[:6]}"
        response = requests.post(f"{BASE_URL}/api/categories",
            headers={"Authorization": f"Bearer {auth_token}"},
            json={
                "name": unique_name,
                "protocol": {"protocol_string": "(ass or bad)"},
                "is_public": True
            })
        assert response.status_code == 400, f"Expected 400, got {response.status_code}: {response.text}"
        data = response.json()
        assert "blocked" in data["detail"].lower()
    
    def test_bass_allowed(self, auth_token):
        """Test 'bass' is allowed (contains 'ass' as substring but not standalone)"""
        unique_name = f"TEST_Bass_{uuid.uuid4().hex[:6]}"
        response = requests.post(f"{BASE_URL}/api/categories",
            headers={"Authorization": f"Bearer {auth_token}"},
            json={
                "name": unique_name,
                "protocol": {"protocol_string": "(bass or music)"},
                "is_public": True
            })
        assert response.status_code == 200, f"Expected 200, got {response.status_code}: {response.text}"
        data = response.json()
        assert data["name"] == unique_name
        
        # Cleanup
        requests.delete(f"{BASE_URL}/api/categories/{data['id']}", 
            headers={"Authorization": f"Bearer {auth_token}"})


class TestFriendsFeature:
    """Friends feature tests"""
    
    @pytest.fixture
    def auth_token(self):
        """Get authentication token"""
        response = requests.post(f"{BASE_URL}/api/auth/login", json={
            "email": ADMIN_EMAIL,
            "password": ADMIN_PASSWORD
        })
        return response.json()["access_token"]
    
    def test_get_friends_list(self, auth_token):
        """Test /api/friends returns friends list"""
        response = requests.get(f"{BASE_URL}/api/friends",
            headers={"Authorization": f"Bearer {auth_token}"})
        assert response.status_code == 200
        data = response.json()
        assert "friends" in data
        assert "count" in data
    
    def test_registration_adds_admin_as_first_friend(self):
        """Test new user registration adds admin as first friend"""
        unique_id = str(uuid.uuid4().hex[:8])
        
        # Register new user
        register_response = requests.post(f"{BASE_URL}/api/auth/register", json={
            "username": f"TEST_Friend_{unique_id}",
            "email": f"testfriend_{unique_id}@example.com",
            "password": "testpass123"
        })
        assert register_response.status_code == 200
        new_token = register_response.json()["access_token"]
        
        # Check friends list
        friends_response = requests.get(f"{BASE_URL}/api/friends",
            headers={"Authorization": f"Bearer {new_token}"})
        assert friends_response.status_code == 200
        data = friends_response.json()
        
        # Should have admin as first friend
        assert data["count"] >= 1, "New user should have at least 1 friend (admin)"
        admin_found = any(f.get("is_admin") == True for f in data["friends"])
        assert admin_found, "Admin should be in new user's friends list"


class TestGroupsFeature:
    """Groups feature tests"""
    
    @pytest.fixture
    def auth_token(self):
        """Get authentication token"""
        response = requests.post(f"{BASE_URL}/api/auth/login", json={
            "email": ADMIN_EMAIL,
            "password": ADMIN_PASSWORD
        })
        return response.json()["access_token"]
    
    def test_get_groups_list(self, auth_token):
        """Test /api/groups returns groups list"""
        response = requests.get(f"{BASE_URL}/api/groups",
            headers={"Authorization": f"Bearer {auth_token}"})
        assert response.status_code == 200
        data = response.json()
        assert "my_groups" in data
        assert "public_groups" in data
    
    def test_create_public_group(self, auth_token):
        """Test creating a public group"""
        unique_name = f"TEST_Public_Group_{uuid.uuid4().hex[:6]}"
        response = requests.post(f"{BASE_URL}/api/groups",
            headers={"Authorization": f"Bearer {auth_token}"},
            json={
                "name": unique_name,
                "description": "A test public group",
                "privacy": "public"
            })
        assert response.status_code == 200
        data = response.json()
        assert data["group"]["name"] == unique_name
        assert data["group"]["privacy"] == "public"
        assert data["group"]["member_count"] == 1
    
    def test_create_private_group(self, auth_token):
        """Test creating a private group"""
        unique_name = f"TEST_Private_Group_{uuid.uuid4().hex[:6]}"
        response = requests.post(f"{BASE_URL}/api/groups",
            headers={"Authorization": f"Bearer {auth_token}"},
            json={
                "name": unique_name,
                "description": "A test private group",
                "privacy": "private"
            })
        assert response.status_code == 200
        data = response.json()
        assert data["group"]["name"] == unique_name
        assert data["group"]["privacy"] == "private"
    
    def test_create_secret_group(self, auth_token):
        """Test creating a secret group"""
        unique_name = f"TEST_Secret_Group_{uuid.uuid4().hex[:6]}"
        response = requests.post(f"{BASE_URL}/api/groups",
            headers={"Authorization": f"Bearer {auth_token}"},
            json={
                "name": unique_name,
                "description": "A test secret group",
                "privacy": "secret"
            })
        assert response.status_code == 200
        data = response.json()
        assert data["group"]["name"] == unique_name
        assert data["group"]["privacy"] == "secret"
    
    def test_get_group_detail(self, auth_token):
        """Test getting group detail page"""
        # First create a group
        unique_name = f"TEST_Detail_Group_{uuid.uuid4().hex[:6]}"
        create_response = requests.post(f"{BASE_URL}/api/groups",
            headers={"Authorization": f"Bearer {auth_token}"},
            json={
                "name": unique_name,
                "description": "A test group for detail",
                "privacy": "public"
            })
        group_id = create_response.json()["group"]["id"]
        
        # Get group detail - response is nested under "group" key
        detail_response = requests.get(f"{BASE_URL}/api/groups/{group_id}",
            headers={"Authorization": f"Bearer {auth_token}"})
        assert detail_response.status_code == 200
        data = detail_response.json()
        assert data["group"]["name"] == unique_name


class TestPagesFeature:
    """Pages feature tests"""
    
    @pytest.fixture
    def auth_token(self):
        """Get authentication token"""
        response = requests.post(f"{BASE_URL}/api/auth/login", json={
            "email": ADMIN_EMAIL,
            "password": ADMIN_PASSWORD
        })
        return response.json()["access_token"]
    
    def test_get_pages_list(self, auth_token):
        """Test /api/pages returns pages list"""
        response = requests.get(f"{BASE_URL}/api/pages",
            headers={"Authorization": f"Bearer {auth_token}"})
        assert response.status_code == 200
        data = response.json()
        assert "my_pages" in data
        assert "following" in data
        assert "popular" in data
    
    def test_create_page_with_category(self, auth_token):
        """Test creating a page with category selection"""
        unique_name = f"TEST_Business_Page_{uuid.uuid4().hex[:6]}"
        response = requests.post(f"{BASE_URL}/api/pages",
            headers={"Authorization": f"Bearer {auth_token}"},
            json={
                "name": unique_name,
                "description": "A test business page",
                "category": "Business"
            })
        assert response.status_code == 200
        data = response.json()
        assert data["page"]["name"] == unique_name
        assert data["page"]["category"] == "Business"
    
    def test_create_community_page(self, auth_token):
        """Test creating a community page"""
        unique_name = f"TEST_Community_Page_{uuid.uuid4().hex[:6]}"
        response = requests.post(f"{BASE_URL}/api/pages",
            headers={"Authorization": f"Bearer {auth_token}"},
            json={
                "name": unique_name,
                "description": "A test community page",
                "category": "Community"
            })
        assert response.status_code == 200
        data = response.json()
        assert data["page"]["name"] == unique_name
        assert data["page"]["category"] == "Community"
    
    def test_get_page_detail(self, auth_token):
        """Test getting page detail"""
        # First create a page
        unique_name = f"TEST_Detail_Page_{uuid.uuid4().hex[:6]}"
        create_response = requests.post(f"{BASE_URL}/api/pages",
            headers={"Authorization": f"Bearer {auth_token}"},
            json={
                "name": unique_name,
                "description": "A test page for detail",
                "category": "General"
            })
        page_id = create_response.json()["page"]["id"]
        
        # Get page detail - response is nested under "page" key
        detail_response = requests.get(f"{BASE_URL}/api/pages/{page_id}",
            headers={"Authorization": f"Bearer {auth_token}"})
        assert detail_response.status_code == 200
        data = detail_response.json()
        assert data["page"]["name"] == unique_name


class TestAuthentication:
    """Authentication tests"""
    
    def test_login_with_admin_credentials(self):
        """Test login with john@infojet.com / password123"""
        response = requests.post(f"{BASE_URL}/api/auth/login", json={
            "email": ADMIN_EMAIL,
            "password": ADMIN_PASSWORD
        })
        assert response.status_code == 200
        data = response.json()
        assert "access_token" in data
        assert data["user"]["email"] == ADMIN_EMAIL
        assert data["user"]["is_admin"] == True
    
    def test_login_with_invalid_credentials(self):
        """Test login with wrong password returns 401"""
        response = requests.post(f"{BASE_URL}/api/auth/login", json={
            "email": ADMIN_EMAIL,
            "password": "wrongpassword"
        })
        assert response.status_code == 401
    
    def test_registration_creates_new_user(self):
        """Test registration creates new user"""
        unique_id = str(uuid.uuid4().hex[:8])
        response = requests.post(f"{BASE_URL}/api/auth/register", json={
            "username": f"TEST_Reg_{unique_id}",
            "email": f"testreg_{unique_id}@example.com",
            "password": "testpass123"
        })
        assert response.status_code == 200
        data = response.json()
        assert "access_token" in data
        assert data["user"]["username"] == f"TEST_Reg_{unique_id}"


class TestCategoryProtocol:
    """Category protocol tests"""
    
    @pytest.fixture
    def auth_token(self):
        """Get authentication token"""
        response = requests.post(f"{BASE_URL}/api/auth/login", json={
            "email": ADMIN_EMAIL,
            "password": ADMIN_PASSWORD
        })
        return response.json()["access_token"]
    
    def test_create_category_with_protocol(self, auth_token):
        """Test creating category with protocol"""
        unique_name = f"TEST_Protocol_{uuid.uuid4().hex[:6]}"
        response = requests.post(f"{BASE_URL}/api/categories",
            headers={"Authorization": f"Bearer {auth_token}"},
            json={
                "name": unique_name,
                "protocol": {"protocol_string": "(science or technology) & (research)+"},
                "is_public": True
            })
        assert response.status_code == 200
        data = response.json()
        assert data["name"] == unique_name
        assert "(science or technology)" in data["protocol_string"]
        
        # Cleanup
        requests.delete(f"{BASE_URL}/api/categories/{data['id']}", 
            headers={"Authorization": f"Bearer {auth_token}"})
    
    def test_update_category(self, auth_token):
        """Test updating category"""
        # Create category
        unique_name = f"TEST_Update_{uuid.uuid4().hex[:6]}"
        create_response = requests.post(f"{BASE_URL}/api/categories",
            headers={"Authorization": f"Bearer {auth_token}"},
            json={
                "name": unique_name,
                "protocol": {"protocol_string": "(test or example)"},
                "is_public": True
            })
        category_id = create_response.json()["id"]
        
        # Update category
        new_name = f"TEST_Updated_{uuid.uuid4().hex[:6]}"
        update_response = requests.put(f"{BASE_URL}/api/categories/{category_id}",
            headers={"Authorization": f"Bearer {auth_token}"},
            json={
                "name": new_name,
                "protocol_string": "(updated or modified)"
            })
        assert update_response.status_code == 200
        assert update_response.json()["name"] == new_name
        
        # Cleanup
        requests.delete(f"{BASE_URL}/api/categories/{category_id}", 
            headers={"Authorization": f"Bearer {auth_token}"})
    
    def test_delete_category(self, auth_token):
        """Test deleting category"""
        # Create category
        unique_name = f"TEST_Delete_{uuid.uuid4().hex[:6]}"
        create_response = requests.post(f"{BASE_URL}/api/categories",
            headers={"Authorization": f"Bearer {auth_token}"},
            json={
                "name": unique_name,
                "protocol": {"protocol_string": "(delete or test)"},
                "is_public": True
            })
        category_id = create_response.json()["id"]
        
        # Delete category
        delete_response = requests.delete(f"{BASE_URL}/api/categories/{category_id}",
            headers={"Authorization": f"Bearer {auth_token}"})
        assert delete_response.status_code == 200
        
        # Verify deletion
        get_response = requests.get(f"{BASE_URL}/api/categories/{category_id}",
            headers={"Authorization": f"Bearer {auth_token}"})
        assert get_response.status_code == 404


class TestHealthAndStatus:
    """Health and status endpoint tests"""
    
    def test_health_endpoint(self):
        """Test /api/health returns operational"""
        response = requests.get(f"{BASE_URL}/api/health")
        assert response.status_code == 200
        data = response.json()
        assert data["status"] == "operational"
        assert data["service"] == "InfoPilot Explorer"
    
    def test_root_endpoint(self):
        """Test /api/ returns API info"""
        response = requests.get(f"{BASE_URL}/api/")
        assert response.status_code == 200
        data = response.json()
        assert "InfoPilot Explorer" in data["message"]


class TestUltimateSearch:
    """Ultimate Search page tests"""
    
    @pytest.fixture
    def auth_token(self):
        """Get authentication token"""
        response = requests.post(f"{BASE_URL}/api/auth/login", json={
            "email": ADMIN_EMAIL,
            "password": ADMIN_PASSWORD
        })
        return response.json()["access_token"]
    
    def test_get_page_settings(self, auth_token):
        """Test getting Ultimate Search page settings"""
        response = requests.get(f"{BASE_URL}/api/ultimate-search/page-settings",
            headers={"Authorization": f"Bearer {auth_token}"})
        assert response.status_code == 200
        data = response.json()
        assert "page_name" in data
    
    def test_rename_page(self, auth_token):
        """Test RENAME PAGE feature"""
        new_name = f"My Custom Search {uuid.uuid4().hex[:4]}"
        response = requests.put(f"{BASE_URL}/api/ultimate-search/page-settings",
            headers={"Authorization": f"Bearer {auth_token}"},
            json={"page_name": new_name})
        assert response.status_code == 200
        data = response.json()
        assert data["settings"]["page_name"] == new_name
    
    def test_get_map_data(self, auth_token):
        """Test Google Maps data endpoint"""
        response = requests.get(f"{BASE_URL}/api/ultimate-search/map-data",
            headers={"Authorization": f"Bearer {auth_token}"})
        assert response.status_code == 200
        data = response.json()
        assert "markers" in data
        assert "categories" in data


class TestBookPage:
    """Book page tests"""
    
    def test_book_info_endpoint(self):
        """Test /api/book/info returns Letters to Evelyn info"""
        response = requests.get(f"{BASE_URL}/api/book/info")
        assert response.status_code == 200
        data = response.json()
        assert data["title"] == "Letters to Evelyn"
        assert data["author"] == "John Selman"
        assert data["price"] == 2.99
        assert data["rating"] == 5.0


class TestIntelStats:
    """Intel Stats page tests"""
    
    @pytest.fixture
    def auth_token(self):
        """Get authentication token"""
        response = requests.post(f"{BASE_URL}/api/auth/login", json={
            "email": ADMIN_EMAIL,
            "password": ADMIN_PASSWORD
        })
        return response.json()["access_token"]
    
    def test_statistics_endpoint(self, auth_token):
        """Test statistics endpoint"""
        response = requests.get(f"{BASE_URL}/api/statistics",
            headers={"Authorization": f"Bearer {auth_token}"})
        assert response.status_code == 200


class TestGlobalDatabase:
    """Global Database page tests"""
    
    @pytest.fixture
    def auth_token(self):
        """Get authentication token"""
        response = requests.post(f"{BASE_URL}/api/auth/login", json={
            "email": ADMIN_EMAIL,
            "password": ADMIN_PASSWORD
        })
        return response.json()["access_token"]
    
    def test_global_database_endpoint(self, auth_token):
        """Test global database endpoint"""
        response = requests.get(f"{BASE_URL}/api/global-database",
            headers={"Authorization": f"Bearer {auth_token}"})
        assert response.status_code == 200
        data = response.json()
        assert "public_categories" in data
        assert "results" in data
        assert "total" in data


class TestAdminPanel:
    """Admin panel tests"""
    
    @pytest.fixture
    def auth_token(self):
        """Get authentication token"""
        response = requests.post(f"{BASE_URL}/api/auth/login", json={
            "email": ADMIN_EMAIL,
            "password": ADMIN_PASSWORD
        })
        return response.json()["access_token"]
    
    def test_admin_settings(self, auth_token):
        """Test admin settings endpoint"""
        response = requests.get(f"{BASE_URL}/api/admin/settings",
            headers={"Authorization": f"Bearer {auth_token}"})
        assert response.status_code == 200
        data = response.json()
        assert "blocked_words" in data


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
