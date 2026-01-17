"""
Iteration 85 - P0 Bug Fixes Testing
Tests for:
1. Save Protocol (PUT /api/categories/{id}) - fixed cat_oid bug
2. Category CRUD operations
3. Map popup functionality (tested via frontend)
4. Edit Category modal behavior (tested via frontend)
"""
import pytest
import requests
import os
import time

BASE_URL = os.environ.get('REACT_APP_BACKEND_URL', '').rstrip('/')

class TestCategoryPUTEndpoint:
    """Test the PUT /api/categories/{id} endpoint - the main P0 bug fix"""
    
    @pytest.fixture(autouse=True)
    def setup(self):
        """Setup test credentials and login"""
        self.admin_email = "jjspilot24@gmail.com"
        self.admin_password = "InfoPilot2024!"
        
        # Login as admin (use admin for all tests since test user doesn't exist)
        login_response = requests.post(f"{BASE_URL}/api/auth/login", json={
            "email": self.admin_email,
            "password": self.admin_password
        })
        if login_response.status_code == 200:
            self.admin_token = login_response.json().get("token")
            self.test_token = self.admin_token  # Use admin token for tests
        else:
            pytest.skip("Admin login failed")
    
    def test_create_category_success(self):
        """Test creating a new category"""
        headers = {"Authorization": f"Bearer {self.test_token}"}
        
        # Create a test category
        create_response = requests.post(f"{BASE_URL}/api/categories", json={
            "name": f"TEST_Category_{int(time.time())}",
            "protocol": "(test or example) & (data)",
            "is_public": False
        }, headers=headers)
        
        assert create_response.status_code in [200, 201], f"Create failed: {create_response.text}"
        data = create_response.json()
        assert "id" in data
        assert "name" in data
        assert "protocol" in data
        
        # Store for cleanup
        self.created_category_id = data["id"]
        return data["id"]
    
    def test_update_category_name_success(self):
        """Test updating category name - P0 bug fix verification"""
        headers = {"Authorization": f"Bearer {self.test_token}"}
        
        # First create a category
        create_response = requests.post(f"{BASE_URL}/api/categories", json={
            "name": f"TEST_UpdateName_{int(time.time())}",
            "protocol": "(update or test)",
            "is_public": False
        }, headers=headers)
        
        assert create_response.status_code in [200, 201]
        category_id = create_response.json()["id"]
        
        # Now update the name - THIS WAS THE P0 BUG
        new_name = f"TEST_UpdatedName_{int(time.time())}"
        update_response = requests.put(f"{BASE_URL}/api/categories/{category_id}", json={
            "name": new_name
        }, headers=headers)
        
        assert update_response.status_code == 200, f"Update name failed: {update_response.text}"
        updated_data = update_response.json()
        assert updated_data["name"] == new_name
        
        # Verify persistence with GET
        get_response = requests.get(f"{BASE_URL}/api/categories", headers=headers)
        assert get_response.status_code == 200
        categories = get_response.json()
        found = [c for c in categories if c["id"] == category_id]
        assert len(found) == 1
        assert found[0]["name"] == new_name
        
        # Cleanup
        requests.delete(f"{BASE_URL}/api/categories/{category_id}", headers=headers)
    
    def test_update_category_protocol_success(self):
        """Test updating category protocol - P0 bug fix verification"""
        headers = {"Authorization": f"Bearer {self.test_token}"}
        
        # First create a category
        create_response = requests.post(f"{BASE_URL}/api/categories", json={
            "name": f"TEST_UpdateProtocol_{int(time.time())}",
            "protocol": "(original or protocol)",
            "is_public": False
        }, headers=headers)
        
        assert create_response.status_code in [200, 201]
        category_id = create_response.json()["id"]
        
        # Now update the protocol - THIS WAS THE P0 BUG
        new_protocol = "(updated or new) & (protocol)"
        update_response = requests.put(f"{BASE_URL}/api/categories/{category_id}", json={
            "protocol": new_protocol
        }, headers=headers)
        
        assert update_response.status_code == 200, f"Update protocol failed: {update_response.text}"
        updated_data = update_response.json()
        assert updated_data["protocol"] == new_protocol
        
        # Cleanup
        requests.delete(f"{BASE_URL}/api/categories/{category_id}", headers=headers)
    
    def test_update_category_is_public_success(self):
        """Test updating category is_public flag - P0 bug fix verification"""
        headers = {"Authorization": f"Bearer {self.test_token}"}
        
        # First create a private category
        create_response = requests.post(f"{BASE_URL}/api/categories", json={
            "name": f"TEST_UpdatePublic_{int(time.time())}",
            "protocol": "(public or test)",
            "is_public": False
        }, headers=headers)
        
        assert create_response.status_code in [200, 201]
        category_id = create_response.json()["id"]
        original_is_public = create_response.json()["is_public"]
        assert original_is_public == False
        
        # Now update to public - THIS WAS THE P0 BUG
        update_response = requests.put(f"{BASE_URL}/api/categories/{category_id}", json={
            "is_public": True
        }, headers=headers)
        
        assert update_response.status_code == 200, f"Update is_public failed: {update_response.text}"
        updated_data = update_response.json()
        assert updated_data["is_public"] == True
        
        # Cleanup
        requests.delete(f"{BASE_URL}/api/categories/{category_id}", headers=headers)
    
    def test_update_category_all_fields_success(self):
        """Test updating all category fields at once - comprehensive P0 bug fix verification"""
        headers = {"Authorization": f"Bearer {self.test_token}"}
        
        # First create a category
        create_response = requests.post(f"{BASE_URL}/api/categories", json={
            "name": f"TEST_UpdateAll_{int(time.time())}",
            "protocol": "(all or fields)",
            "is_public": False
        }, headers=headers)
        
        assert create_response.status_code in [200, 201]
        category_id = create_response.json()["id"]
        
        # Now update ALL fields at once - THIS WAS THE P0 BUG
        new_name = f"TEST_AllUpdated_{int(time.time())}"
        new_protocol = "(completely or new) & (protocol)"
        update_response = requests.put(f"{BASE_URL}/api/categories/{category_id}", json={
            "name": new_name,
            "protocol": new_protocol,
            "is_public": True
        }, headers=headers)
        
        assert update_response.status_code == 200, f"Update all fields failed: {update_response.text}"
        updated_data = update_response.json()
        assert updated_data["name"] == new_name
        assert updated_data["protocol"] == new_protocol
        assert updated_data["is_public"] == True
        
        # Cleanup
        requests.delete(f"{BASE_URL}/api/categories/{category_id}", headers=headers)
    
    def test_update_category_invalid_id(self):
        """Test updating with invalid category ID"""
        headers = {"Authorization": f"Bearer {self.test_token}"}
        
        update_response = requests.put(f"{BASE_URL}/api/categories/invalid_id_123", json={
            "name": "Should Fail"
        }, headers=headers)
        
        assert update_response.status_code == 400, f"Expected 400 for invalid ID: {update_response.text}"
    
    def test_update_category_not_found(self):
        """Test updating non-existent category"""
        headers = {"Authorization": f"Bearer {self.test_token}"}
        
        # Use a valid ObjectId format but non-existent
        fake_id = "000000000000000000000000"
        update_response = requests.put(f"{BASE_URL}/api/categories/{fake_id}", json={
            "name": "Should Not Find"
        }, headers=headers)
        
        assert update_response.status_code == 404, f"Expected 404 for non-existent: {update_response.text}"
    
    def test_update_category_invalid_protocol(self):
        """Test updating with invalid protocol format"""
        headers = {"Authorization": f"Bearer {self.test_token}"}
        
        # First create a category
        create_response = requests.post(f"{BASE_URL}/api/categories", json={
            "name": f"TEST_InvalidProtocol_{int(time.time())}",
            "protocol": "(valid or protocol)",
            "is_public": False
        }, headers=headers)
        
        assert create_response.status_code in [200, 201]
        category_id = create_response.json()["id"]
        
        # Try to update with invalid protocol (unbalanced parentheses)
        update_response = requests.put(f"{BASE_URL}/api/categories/{category_id}", json={
            "protocol": "((invalid protocol"
        }, headers=headers)
        
        # Should return 400 for invalid protocol
        assert update_response.status_code == 400, f"Expected 400 for invalid protocol: {update_response.text}"
        
        # Cleanup
        requests.delete(f"{BASE_URL}/api/categories/{category_id}", headers=headers)


class TestCategoryFiltering:
    """Test category filtering on search results"""
    
    @pytest.fixture(autouse=True)
    def setup(self):
        """Setup test credentials and login"""
        self.admin_email = "jjspilot24@gmail.com"
        self.admin_password = "InfoPilot2024!"
        
        login_response = requests.post(f"{BASE_URL}/api/auth/login", json={
            "email": self.admin_email,
            "password": self.admin_password
        })
        if login_response.status_code == 200:
            self.token = login_response.json().get("token")
        else:
            pytest.skip("Login failed")
    
    def test_get_categories_with_counts(self):
        """Test getting categories with result counts"""
        headers = {"Authorization": f"Bearer {self.token}"}
        
        response = requests.get(f"{BASE_URL}/api/categories", headers=headers)
        assert response.status_code == 200
        
        categories = response.json()
        assert isinstance(categories, list)
        
        # Check that categories have expected fields
        if len(categories) > 0:
            cat = categories[0]
            assert "id" in cat
            assert "name" in cat
            assert "protocol" in cat
            # result_count should be present when include_counts=True (default)
            assert "result_count" in cat or "subcategory_count" in cat
    
    def test_ultimate_search_with_category_filter(self):
        """Test ultimate search endpoint with category filtering"""
        headers = {"Authorization": f"Bearer {self.token}"}
        
        # First get categories
        cat_response = requests.get(f"{BASE_URL}/api/categories", headers=headers)
        assert cat_response.status_code == 200
        categories = cat_response.json()
        
        if len(categories) > 0:
            # Test search with category filter
            category_id = categories[0]["id"]
            search_response = requests.get(
                f"{BASE_URL}/api/ultimate-search?category_ids={category_id}&limit=10",
                headers=headers
            )
            assert search_response.status_code == 200
            data = search_response.json()
            assert "results" in data or isinstance(data, list)


class TestMapEndpoints:
    """Test map-related endpoints"""
    
    @pytest.fixture(autouse=True)
    def setup(self):
        """Setup test credentials and login"""
        self.admin_email = "jjspilot24@gmail.com"
        self.admin_password = "InfoPilot2024!"
        
        login_response = requests.post(f"{BASE_URL}/api/auth/login", json={
            "email": self.admin_email,
            "password": self.admin_password
        })
        if login_response.status_code == 200:
            self.token = login_response.json().get("token")
        else:
            pytest.skip("Login failed")
    
    def test_worldwide_map_endpoint(self):
        """Test the worldwide map endpoint"""
        headers = {"Authorization": f"Bearer {self.token}"}
        
        response = requests.get(f"{BASE_URL}/api/map/worldwide?limit=500", headers=headers)
        assert response.status_code == 200
        
        data = response.json()
        # Should return results array
        assert "results" in data or isinstance(data, list)
    
    def test_personal_map_data(self):
        """Test getting personal map data via ultimate-search"""
        headers = {"Authorization": f"Bearer {self.token}"}
        
        response = requests.get(f"{BASE_URL}/api/ultimate-search?limit=100", headers=headers)
        assert response.status_code == 200
        
        data = response.json()
        assert "results" in data or isinstance(data, list)


class TestProtocolValidation:
    """Test protocol validation endpoint"""
    
    def test_validate_valid_protocol(self):
        """Test validating a valid protocol"""
        response = requests.post(f"{BASE_URL}/api/protocol/validate", json={
            "protocol": "(word1 or word2) & (word3)"
        })
        
        assert response.status_code == 200
        data = response.json()
        assert "is_valid" in data or "valid" in data or "groups" in data
    
    def test_validate_invalid_protocol(self):
        """Test validating an invalid protocol"""
        response = requests.post(f"{BASE_URL}/api/protocol/validate", json={
            "protocol": "((unbalanced"
        })
        
        assert response.status_code == 200
        data = response.json()
        # Should indicate invalid
        if "is_valid" in data:
            assert data["is_valid"] == False
        elif "valid" in data:
            assert data["valid"] == False


class TestCleanupTestData:
    """Cleanup any test data created during testing"""
    
    @pytest.fixture(autouse=True)
    def setup(self):
        """Setup test credentials and login"""
        self.test_email = "testuser@example.com"
        self.test_password = "password123"
        
        login_response = requests.post(f"{BASE_URL}/api/auth/login", json={
            "email": self.test_email,
            "password": self.test_password
        })
        if login_response.status_code == 200:
            self.token = login_response.json().get("token")
        else:
            pytest.skip("Test user login failed")
    
    def test_cleanup_test_categories(self):
        """Clean up any TEST_ prefixed categories"""
        headers = {"Authorization": f"Bearer {self.token}"}
        
        response = requests.get(f"{BASE_URL}/api/categories", headers=headers)
        if response.status_code == 200:
            categories = response.json()
            for cat in categories:
                if cat["name"].startswith("TEST_"):
                    delete_response = requests.delete(
                        f"{BASE_URL}/api/categories/{cat['id']}", 
                        headers=headers
                    )
                    print(f"Cleaned up category: {cat['name']}")
        
        assert True  # Cleanup always passes
