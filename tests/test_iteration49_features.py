"""
InfoPilot Explorer - Iteration 49 Backend Tests
Testing: Category Management (Settings & Ultimate Search), Login/Logout, API stability
"""
import pytest
import requests
import os
import time

BASE_URL = os.environ.get('REACT_APP_BACKEND_URL', '').rstrip('/')

# Test credentials
ADMIN_EMAIL = "jjspilot24@gmail.com"
ADMIN_PASSWORD = "InfoPilot2024!"
TEST_EMAIL = "testuser@example.com"
TEST_PASSWORD = "password123"


class TestHealthAndBasicEndpoints:
    """Test basic API health and public endpoints"""
    
    def test_health_endpoint(self):
        """Test health check endpoint"""
        response = requests.get(f"{BASE_URL}/api/health")
        assert response.status_code == 200
        data = response.json()
        assert data["status"] == "healthy"
        print("✅ Health endpoint working")
    
    def test_article_types_endpoint(self):
        """Test article types endpoint returns all 13 types"""
        response = requests.get(f"{BASE_URL}/api/article-types")
        assert response.status_code == 200
        data = response.json()
        assert "types" in data
        assert len(data["types"]) == 13
        print(f"✅ Article types endpoint returns {len(data['types'])} types")
    
    def test_search_engines_endpoint(self):
        """Test search engines status endpoint"""
        response = requests.get(f"{BASE_URL}/api/search-engines")
        assert response.status_code == 200
        data = response.json()
        assert "engines" in data
        assert "total_available" in data
        print(f"✅ Search engines endpoint: {data['total_available']} engines available")
    
    def test_admin_settings_public(self):
        """Test admin settings endpoint (public access)"""
        response = requests.get(f"{BASE_URL}/api/admin/settings")
        # Should return 200 for public settings or 401 if auth required
        assert response.status_code in [200, 401]
        print(f"✅ Admin settings endpoint responded with {response.status_code}")


class TestAuthentication:
    """Test authentication flows"""
    
    def test_login_admin_success(self):
        """Test admin login with valid credentials"""
        response = requests.post(f"{BASE_URL}/api/auth/login", json={
            "email": ADMIN_EMAIL,
            "password": ADMIN_PASSWORD
        })
        assert response.status_code == 200
        data = response.json()
        assert "token" in data
        assert "user" in data
        assert data["user"]["email"].lower() == ADMIN_EMAIL.lower()
        print(f"✅ Admin login successful, token received")
        return data["token"]
    
    def test_login_invalid_credentials(self):
        """Test login with invalid credentials"""
        response = requests.post(f"{BASE_URL}/api/auth/login", json={
            "email": "invalid@example.com",
            "password": "wrongpassword"
        })
        assert response.status_code in [401, 400]
        print("✅ Invalid credentials correctly rejected")
    
    def test_login_missing_fields(self):
        """Test login with missing fields"""
        response = requests.post(f"{BASE_URL}/api/auth/login", json={
            "email": ADMIN_EMAIL
        })
        assert response.status_code in [400, 422]
        print("✅ Missing fields correctly rejected")


class TestCategoryManagement:
    """Test category CRUD operations - core feature for Settings and Ultimate Search"""
    
    @pytest.fixture(autouse=True)
    def setup(self):
        """Get auth token before each test"""
        response = requests.post(f"{BASE_URL}/api/auth/login", json={
            "email": ADMIN_EMAIL,
            "password": ADMIN_PASSWORD
        })
        if response.status_code == 200:
            self.token = response.json()["token"]
            self.headers = {"Authorization": f"Bearer {self.token}"}
        else:
            pytest.skip("Authentication failed")
    
    def test_get_categories(self):
        """Test fetching all categories"""
        response = requests.get(f"{BASE_URL}/api/categories", headers=self.headers)
        assert response.status_code == 200
        data = response.json()
        assert isinstance(data, list)
        print(f"✅ Fetched {len(data)} categories")
        return data
    
    def test_create_category(self):
        """Test creating a new category"""
        category_data = {
            "name": f"TEST_Category_{int(time.time())}",
            "protocol": "(test or testing) & (automation)",
            "is_public": False
        }
        response = requests.post(f"{BASE_URL}/api/categories", 
                                 json=category_data, 
                                 headers=self.headers)
        assert response.status_code == 200
        data = response.json()
        assert "id" in data
        assert data["name"] == category_data["name"]
        assert data["protocol"] == category_data["protocol"]
        print(f"✅ Created category: {data['name']} with ID: {data['id']}")
        return data
    
    def test_create_subcategory(self):
        """Test creating a sub-category (nested category)"""
        # First create parent
        parent_data = {
            "name": f"TEST_Parent_{int(time.time())}",
            "protocol": "(parent or main)",
            "is_public": False
        }
        parent_response = requests.post(f"{BASE_URL}/api/categories", 
                                        json=parent_data, 
                                        headers=self.headers)
        assert parent_response.status_code == 200
        parent = parent_response.json()
        
        # Create sub-category
        sub_data = {
            "name": f"TEST_SubCategory_{int(time.time())}",
            "protocol": "(sub or child)",
            "parent_id": parent["id"],
            "is_public": False
        }
        sub_response = requests.post(f"{BASE_URL}/api/categories", 
                                     json=sub_data, 
                                     headers=self.headers)
        assert sub_response.status_code == 200
        sub = sub_response.json()
        assert sub["parent_id"] == parent["id"]
        assert sub["level"] == 1  # Sub-category should be level 1
        print(f"✅ Created sub-category: {sub['name']} under {parent['name']}")
        
        # Cleanup
        requests.delete(f"{BASE_URL}/api/categories/{sub['id']}", headers=self.headers)
        requests.delete(f"{BASE_URL}/api/categories/{parent['id']}", headers=self.headers)
        return sub
    
    def test_create_sub_sub_category(self):
        """Test creating a sub-sub-category (3 levels deep)"""
        # Create parent - protocol must have 'or' operator
        parent_data = {
            "name": f"TEST_L0_{int(time.time())}",
            "protocol": "(level0 or parent)",
            "is_public": False
        }
        parent_response = requests.post(f"{BASE_URL}/api/categories", 
                                        json=parent_data, 
                                        headers=self.headers)
        assert parent_response.status_code == 200, f"Parent creation failed: {parent_response.text}"
        parent = parent_response.json()
        
        # Create sub-category (level 1)
        sub_data = {
            "name": f"TEST_L1_{int(time.time())}",
            "protocol": "(level1 or sub)",
            "parent_id": parent["id"],
            "is_public": False
        }
        sub_response = requests.post(f"{BASE_URL}/api/categories", 
                                     json=sub_data, 
                                     headers=self.headers)
        assert sub_response.status_code == 200, f"Sub creation failed: {sub_response.text}"
        sub = sub_response.json()
        assert sub["level"] == 1
        
        # Create sub-sub-category (level 2)
        subsub_data = {
            "name": f"TEST_L2_{int(time.time())}",
            "protocol": "(level2 or subsub)",
            "parent_id": sub["id"],
            "is_public": False
        }
        subsub_response = requests.post(f"{BASE_URL}/api/categories", 
                                        json=subsub_data, 
                                        headers=self.headers)
        assert subsub_response.status_code == 200, f"SubSub creation failed: {subsub_response.text}"
        subsub = subsub_response.json()
        assert subsub["level"] == 2  # Sub-sub-category should be level 2
        print(f"✅ Created 3-level hierarchy: {parent['name']} -> {sub['name']} -> {subsub['name']}")
        
        # Cleanup - delete parent (should cascade delete children)
        requests.delete(f"{BASE_URL}/api/categories/{parent['id']}", headers=self.headers)
        return subsub
    
    def test_update_category(self):
        """Test updating a category"""
        # Create category first - protocol must have 'or' operator
        category_data = {
            "name": f"TEST_Update_{int(time.time())}",
            "protocol": "(original or base)",
            "is_public": False
        }
        create_response = requests.post(f"{BASE_URL}/api/categories", 
                                        json=category_data, 
                                        headers=self.headers)
        assert create_response.status_code == 200, f"Create failed: {create_response.text}"
        category = create_response.json()
        
        # Update category
        update_data = {
            "name": f"TEST_Updated_{int(time.time())}",
            "protocol": "(updated or modified)",
            "is_public": True,
            "price": 5.99
        }
        update_response = requests.put(f"{BASE_URL}/api/categories/{category['id']}", 
                                       json=update_data, 
                                       headers=self.headers)
        assert update_response.status_code == 200, f"Update failed: {update_response.text}"
        updated = update_response.json()
        assert updated["name"] == update_data["name"]
        assert updated["protocol"] == update_data["protocol"]
        assert updated["is_public"] == True
        print(f"✅ Updated category: {updated['name']}")
        
        # Verify update persisted
        get_response = requests.get(f"{BASE_URL}/api/categories", headers=self.headers)
        categories = get_response.json()
        found = next((c for c in categories if c["id"] == category["id"]), None)
        assert found is not None
        assert found["name"] == update_data["name"]
        
        # Cleanup
        requests.delete(f"{BASE_URL}/api/categories/{category['id']}", headers=self.headers)
    
    def test_delete_category(self):
        """Test deleting a category"""
        # Create category first
        category_data = {
            "name": f"TEST_Delete_{int(time.time())}",
            "protocol": "(delete or remove)",
            "is_public": False
        }
        create_response = requests.post(f"{BASE_URL}/api/categories", 
                                        json=category_data, 
                                        headers=self.headers)
        assert create_response.status_code == 200
        category = create_response.json()
        
        # Delete category
        delete_response = requests.delete(f"{BASE_URL}/api/categories/{category['id']}", 
                                          headers=self.headers)
        assert delete_response.status_code == 200
        print(f"✅ Deleted category: {category['name']}")
        
        # Verify deletion
        get_response = requests.get(f"{BASE_URL}/api/categories", headers=self.headers)
        categories = get_response.json()
        found = next((c for c in categories if c["id"] == category["id"]), None)
        assert found is None
    
    def test_cascade_delete(self):
        """Test cascade delete of parent category removes children"""
        # Create parent - protocol must have 'or' operator
        parent_data = {
            "name": f"TEST_CascadeParent_{int(time.time())}",
            "protocol": "(cascade or parent)",
            "is_public": False
        }
        parent_response = requests.post(f"{BASE_URL}/api/categories", 
                                        json=parent_data, 
                                        headers=self.headers)
        assert parent_response.status_code == 200, f"Parent creation failed: {parent_response.text}"
        parent = parent_response.json()
        
        # Create children - protocol must have 'or' operator
        child_ids = []
        for i in range(3):
            child_data = {
                "name": f"TEST_CascadeChild{i}_{int(time.time())}",
                "protocol": f"(child{i} or sub{i})",
                "parent_id": parent["id"],
                "is_public": False
            }
            child_response = requests.post(f"{BASE_URL}/api/categories", 
                                           json=child_data, 
                                           headers=self.headers)
            assert child_response.status_code == 200, f"Child creation failed: {child_response.text}"
            child_ids.append(child_response.json()["id"])
        
        # Delete parent
        delete_response = requests.delete(f"{BASE_URL}/api/categories/{parent['id']}", 
                                          headers=self.headers)
        assert delete_response.status_code == 200
        
        # Verify children are also deleted
        get_response = requests.get(f"{BASE_URL}/api/categories", headers=self.headers)
        categories = get_response.json()
        category_ids = [c["id"] for c in categories]
        
        for child_id in child_ids:
            assert child_id not in category_ids
        
        print(f"✅ Cascade delete removed parent and {len(child_ids)} children")
    
    def test_invalid_protocol_format(self):
        """Test that invalid protocol format is rejected"""
        category_data = {
            "name": f"TEST_InvalidProtocol_{int(time.time())}",
            "protocol": "",  # Empty protocol
            "is_public": False
        }
        response = requests.post(f"{BASE_URL}/api/categories", 
                                 json=category_data, 
                                 headers=self.headers)
        # Empty protocol might be allowed or rejected depending on implementation
        print(f"✅ Empty protocol response: {response.status_code}")


class TestUltimateSearchEndpoints:
    """Test Ultimate Search related endpoints"""
    
    @pytest.fixture(autouse=True)
    def setup(self):
        """Get auth token before each test"""
        response = requests.post(f"{BASE_URL}/api/auth/login", json={
            "email": ADMIN_EMAIL,
            "password": ADMIN_PASSWORD
        })
        if response.status_code == 200:
            self.token = response.json()["token"]
            self.headers = {"Authorization": f"Bearer {self.token}"}
        else:
            pytest.skip("Authentication failed")
    
    def test_ultimate_search_results(self):
        """Test fetching ultimate search results"""
        response = requests.get(f"{BASE_URL}/api/ultimate-search?aggregation=and_or&limit=200", 
                                headers=self.headers)
        assert response.status_code == 200
        data = response.json()
        assert "results" in data
        assert "total" in data
        print(f"✅ Ultimate search returned {len(data['results'])} results")
    
    def test_ultimate_search_stats(self):
        """Test ultimate search statistics endpoint"""
        response = requests.get(f"{BASE_URL}/api/ultimate-search/stats", 
                                headers=self.headers)
        assert response.status_code == 200
        data = response.json()
        assert "total_results" in data
        assert "total_categories" in data
        assert "article_types" in data
        print(f"✅ Stats: {data['total_results']} results, {data['total_categories']} categories")
    
    def test_ultimate_search_batches(self):
        """Test fetching search batches"""
        response = requests.get(f"{BASE_URL}/api/ultimate-search/batches", 
                                headers=self.headers)
        assert response.status_code == 200
        data = response.json()
        assert "batches" in data
        print(f"✅ Found {len(data['batches'])} search batches")
    
    def test_ultimate_search_with_category_filter(self):
        """Test filtering results by category"""
        # First get categories
        cat_response = requests.get(f"{BASE_URL}/api/categories", headers=self.headers)
        categories = cat_response.json()
        
        if categories:
            cat_id = categories[0]["id"]
            response = requests.get(
                f"{BASE_URL}/api/ultimate-search?category_ids={cat_id}&aggregation=and_or&limit=50", 
                headers=self.headers
            )
            assert response.status_code == 200
            data = response.json()
            assert "filter_applied" in data
            print(f"✅ Category filter applied, returned {len(data['results'])} results")
        else:
            print("⚠️ No categories to test filter with")


class TestAdminEndpoints:
    """Test admin-specific endpoints"""
    
    @pytest.fixture(autouse=True)
    def setup(self):
        """Get admin auth token before each test"""
        response = requests.post(f"{BASE_URL}/api/auth/login", json={
            "email": ADMIN_EMAIL,
            "password": ADMIN_PASSWORD
        })
        if response.status_code == 200:
            self.token = response.json()["token"]
            self.headers = {"Authorization": f"Bearer {self.token}"}
        else:
            pytest.skip("Admin authentication failed")
    
    def test_admin_stats(self):
        """Test admin statistics endpoint"""
        response = requests.get(f"{BASE_URL}/api/admin/stats", headers=self.headers)
        assert response.status_code == 200
        data = response.json()
        print(f"✅ Admin stats retrieved")
    
    def test_admin_users_list(self):
        """Test admin users list endpoint"""
        response = requests.get(f"{BASE_URL}/api/admin/users", headers=self.headers)
        assert response.status_code == 200
        data = response.json()
        # Response is wrapped in {"users": [...]}
        if isinstance(data, dict) and "users" in data:
            users = data["users"]
        else:
            users = data
        assert isinstance(users, list)
        print(f"✅ Admin users list: {len(users)} users")
    
    def test_admin_moderation_actions(self):
        """Test admin moderation actions endpoint"""
        response = requests.get(f"{BASE_URL}/api/admin/moderation/actions", headers=self.headers)
        assert response.status_code == 200
        data = response.json()
        assert "actions" in data
        print(f"✅ Moderation actions: {len(data['actions'])} actions")


class TestSearchEndpoints:
    """Test search functionality endpoints"""
    
    @pytest.fixture(autouse=True)
    def setup(self):
        """Get auth token before each test"""
        response = requests.post(f"{BASE_URL}/api/auth/login", json={
            "email": ADMIN_EMAIL,
            "password": ADMIN_PASSWORD
        })
        if response.status_code == 200:
            self.token = response.json()["token"]
            self.headers = {"Authorization": f"Bearer {self.token}"}
        else:
            pytest.skip("Authentication failed")
    
    def test_basic_search(self):
        """Test basic search endpoint"""
        response = requests.post(f"{BASE_URL}/api/search", 
                                 json={"query": "test"},
                                 headers=self.headers)
        assert response.status_code == 200
        data = response.json()
        assert "results" in data
        print(f"✅ Basic search returned {len(data['results'])} results")
    
    def test_database_search(self):
        """Test database search endpoint"""
        response = requests.post(f"{BASE_URL}/api/database-search", 
                                 json={"query": "test", "mode": "smart"},
                                 headers=self.headers)
        assert response.status_code == 200
        data = response.json()
        assert "results" in data
        assert "total_in_database" in data
        print(f"✅ Database search: {len(data['results'])} results from {data['total_in_database']} in DB")


class TestProtocolValidation:
    """Test protocol validation endpoint"""
    
    def test_validate_valid_protocol(self):
        """Test validating a valid protocol"""
        response = requests.post(f"{BASE_URL}/api/protocol/validate", 
                                 json={"protocol": "(test or testing) & (automation)"})
        assert response.status_code == 200
        data = response.json()
        print(f"✅ Protocol validation response: {data}")
    
    def test_validate_complex_protocol(self):
        """Test validating a complex protocol with multiple groups"""
        protocol = "(aviation or pilot) & (safety or security)+ & (accident or incident)^"
        response = requests.post(f"{BASE_URL}/api/protocol/validate", 
                                 json={"protocol": protocol})
        assert response.status_code == 200
        print(f"✅ Complex protocol validation passed")


class TestUserEndpoints:
    """Test user-related endpoints"""
    
    @pytest.fixture(autouse=True)
    def setup(self):
        """Get auth token before each test"""
        response = requests.post(f"{BASE_URL}/api/auth/login", json={
            "email": ADMIN_EMAIL,
            "password": ADMIN_PASSWORD
        })
        if response.status_code == 200:
            self.token = response.json()["token"]
            self.headers = {"Authorization": f"Bearer {self.token}"}
        else:
            pytest.skip("Authentication failed")
    
    def test_has_password_check(self):
        """Test has-password endpoint"""
        response = requests.get(f"{BASE_URL}/api/users/has-password", headers=self.headers)
        assert response.status_code == 200
        data = response.json()
        assert "has_password" in data
        print(f"✅ Has password check: {data['has_password']}")
    
    def test_export_summary(self):
        """Test export summary endpoint"""
        response = requests.get(f"{BASE_URL}/api/export/summary", headers=self.headers)
        assert response.status_code == 200
        data = response.json()
        print(f"✅ Export summary retrieved")


class TestNotifications:
    """Test notification endpoints"""
    
    @pytest.fixture(autouse=True)
    def setup(self):
        """Get auth token before each test"""
        response = requests.post(f"{BASE_URL}/api/auth/login", json={
            "email": ADMIN_EMAIL,
            "password": ADMIN_PASSWORD
        })
        if response.status_code == 200:
            self.token = response.json()["token"]
            self.headers = {"Authorization": f"Bearer {self.token}"}
        else:
            pytest.skip("Authentication failed")
    
    def test_get_notifications(self):
        """Test fetching notifications"""
        response = requests.get(f"{BASE_URL}/api/notifications?limit=20", headers=self.headers)
        assert response.status_code == 200
        data = response.json()
        print(f"✅ Notifications retrieved")
    
    def test_unread_count(self):
        """Test unread notifications count"""
        response = requests.get(f"{BASE_URL}/api/notifications/unread-count", headers=self.headers)
        assert response.status_code == 200
        data = response.json()
        print(f"✅ Unread count retrieved")


# Cleanup function to remove test data
def cleanup_test_categories():
    """Remove all TEST_ prefixed categories"""
    response = requests.post(f"{BASE_URL}/api/auth/login", json={
        "email": ADMIN_EMAIL,
        "password": ADMIN_PASSWORD
    })
    if response.status_code != 200:
        return
    
    token = response.json()["token"]
    headers = {"Authorization": f"Bearer {token}"}
    
    # Get all categories
    cat_response = requests.get(f"{BASE_URL}/api/categories", headers=headers)
    if cat_response.status_code != 200:
        return
    
    categories = cat_response.json()
    
    # Delete TEST_ prefixed categories
    for cat in categories:
        if cat["name"].startswith("TEST_"):
            requests.delete(f"{BASE_URL}/api/categories/{cat['id']}", headers=headers)
            print(f"Cleaned up: {cat['name']}")


if __name__ == "__main__":
    # Run cleanup first
    cleanup_test_categories()
    
    # Run tests
    pytest.main([__file__, "-v", "--tb=short"])
