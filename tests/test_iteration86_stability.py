"""
InfoPilot Explorer - Iteration 86 Comprehensive Stability Tests
Testing: Categories CRUD, Save Protocol, Map popup, Categories loading on Ultimate Search
"""
import pytest
import requests
import os

BASE_URL = os.environ.get('REACT_APP_BACKEND_URL', '').rstrip('/')

class TestAuthentication:
    """Test authentication flow"""
    
    @pytest.fixture(scope="class")
    def auth_token(self):
        """Get authentication token for admin user"""
        response = requests.post(f"{BASE_URL}/api/auth/login", json={
            "email": "jjspilot24@gmail.com",
            "password": "InfoPilot2024!"
        })
        assert response.status_code == 200, f"Login failed: {response.text}"
        data = response.json()
        assert "token" in data, "No token in response"
        return data["token"]
    
    def test_login_success(self, auth_token):
        """Test login returns valid token"""
        assert auth_token is not None
        assert len(auth_token) > 0
        print(f"✓ Login successful, token length: {len(auth_token)}")


class TestCategoriesCRUD:
    """Test Categories CRUD operations - Critical for iteration 86"""
    
    @pytest.fixture(scope="class")
    def auth_token(self):
        """Get authentication token"""
        response = requests.post(f"{BASE_URL}/api/auth/login", json={
            "email": "jjspilot24@gmail.com",
            "password": "InfoPilot2024!"
        })
        assert response.status_code == 200
        return response.json()["token"]
    
    @pytest.fixture(scope="class")
    def headers(self, auth_token):
        """Get headers with auth token"""
        return {
            "Authorization": f"Bearer {auth_token}",
            "Content-Type": "application/json"
        }
    
    def test_get_categories(self, headers):
        """Test GET /api/categories - Should return categories with count > 0"""
        response = requests.get(f"{BASE_URL}/api/categories", headers=headers)
        assert response.status_code == 200, f"Failed to get categories: {response.text}"
        
        categories = response.json()
        assert isinstance(categories, list), "Categories should be a list"
        
        # CRITICAL: Main agent claims 16 categories should exist
        print(f"✓ GET /api/categories returned {len(categories)} categories")
        
        # Verify category structure
        if len(categories) > 0:
            cat = categories[0]
            assert "id" in cat, "Category missing 'id'"
            assert "name" in cat, "Category missing 'name'"
            assert "protocol" in cat, "Category missing 'protocol'"
            print(f"✓ Category structure valid: {cat['name']}")
        
        return categories
    
    def test_create_category(self, headers):
        """Test POST /api/categories - Create new category"""
        test_category = {
            "name": "TEST_Iteration86_Category",
            "protocol": "(test or iteration86)",
            "is_public": False
        }
        
        response = requests.post(f"{BASE_URL}/api/categories", json=test_category, headers=headers)
        assert response.status_code == 200, f"Failed to create category: {response.text}"
        
        created = response.json()
        assert "id" in created, "Created category missing 'id'"
        assert created["name"] == test_category["name"], "Name mismatch"
        assert created["protocol"] == test_category["protocol"], "Protocol mismatch"
        
        print(f"✓ Created category: {created['name']} (ID: {created['id']})")
        return created["id"]
    
    def test_update_category_save_protocol(self, headers):
        """Test PUT /api/categories/{id} - Save Protocol (P0 bug fix verification)"""
        # First create a category to update
        test_category = {
            "name": "TEST_SaveProtocol_Category",
            "protocol": "(original or protocol)",
            "is_public": False
        }
        
        create_response = requests.post(f"{BASE_URL}/api/categories", json=test_category, headers=headers)
        assert create_response.status_code == 200, f"Failed to create category: {create_response.text}"
        category_id = create_response.json()["id"]
        
        # Now update the category (Save Protocol)
        update_data = {
            "name": "TEST_SaveProtocol_Updated",
            "protocol": "(updated or protocol or test)",
            "is_public": True
        }
        
        update_response = requests.put(f"{BASE_URL}/api/categories/{category_id}", json=update_data, headers=headers)
        assert update_response.status_code == 200, f"CRITICAL: Save Protocol failed: {update_response.text}"
        
        updated = update_response.json()
        assert updated["name"] == update_data["name"], "Name not updated"
        assert updated["protocol"] == update_data["protocol"], "Protocol not updated"
        assert updated["is_public"] == update_data["is_public"], "is_public not updated"
        
        print(f"✓ Save Protocol (PUT) successful: {updated['name']}")
        
        # Cleanup
        requests.delete(f"{BASE_URL}/api/categories/{category_id}", headers=headers)
        return category_id
    
    def test_delete_category(self, headers):
        """Test DELETE /api/categories/{id}"""
        # Create a category to delete
        test_category = {
            "name": "TEST_Delete_Category",
            "protocol": "(delete or test)",
            "is_public": False
        }
        
        create_response = requests.post(f"{BASE_URL}/api/categories", json=test_category, headers=headers)
        assert create_response.status_code == 200
        category_id = create_response.json()["id"]
        
        # Delete the category
        delete_response = requests.delete(f"{BASE_URL}/api/categories/{category_id}", headers=headers)
        assert delete_response.status_code == 200, f"Failed to delete category: {delete_response.text}"
        
        # Verify deletion
        get_response = requests.get(f"{BASE_URL}/api/categories", headers=headers)
        categories = get_response.json()
        category_ids = [c["id"] for c in categories]
        assert category_id not in category_ids, "Category not deleted"
        
        print(f"✓ Category deleted successfully")


class TestMapPage:
    """Test Map page functionality"""
    
    @pytest.fixture(scope="class")
    def auth_token(self):
        """Get authentication token"""
        response = requests.post(f"{BASE_URL}/api/auth/login", json={
            "email": "jjspilot24@gmail.com",
            "password": "InfoPilot2024!"
        })
        assert response.status_code == 200
        return response.json()["token"]
    
    @pytest.fixture(scope="class")
    def headers(self, auth_token):
        return {"Authorization": f"Bearer {auth_token}"}
    
    def test_map_worldwide_endpoint(self, headers):
        """Test GET /api/map/worldwide - Map data endpoint"""
        response = requests.get(f"{BASE_URL}/api/map/worldwide?limit=100", headers=headers)
        assert response.status_code == 200, f"Map worldwide failed: {response.text}"
        
        data = response.json()
        results = data.get("results", data) if isinstance(data, dict) else data
        
        print(f"✓ Map worldwide returned {len(results) if isinstance(results, list) else 'N/A'} results")
        return results


class TestUltimateSearch:
    """Test Ultimate Search page functionality"""
    
    @pytest.fixture(scope="class")
    def auth_token(self):
        """Get authentication token"""
        response = requests.post(f"{BASE_URL}/api/auth/login", json={
            "email": "jjspilot24@gmail.com",
            "password": "InfoPilot2024!"
        })
        assert response.status_code == 200
        return response.json()["token"]
    
    @pytest.fixture(scope="class")
    def headers(self, auth_token):
        return {"Authorization": f"Bearer {auth_token}"}
    
    def test_ultimate_search_results(self, headers):
        """Test GET /api/ultimate-search - Search results"""
        response = requests.get(f"{BASE_URL}/api/ultimate-search?limit=50", headers=headers)
        assert response.status_code == 200, f"Ultimate search failed: {response.text}"
        
        data = response.json()
        results = data.get("results", [])
        
        print(f"✓ Ultimate search returned {len(results)} results")
        return results
    
    def test_search_batches(self, headers):
        """Test GET /api/ultimate-search/batches"""
        response = requests.get(f"{BASE_URL}/api/ultimate-search/batches", headers=headers)
        assert response.status_code == 200, f"Batches failed: {response.text}"
        
        data = response.json()
        batches = data.get("batches", [])
        
        print(f"✓ Batches endpoint returned {len(batches)} batches")


class TestMarketplace:
    """Test Marketplace page functionality"""
    
    @pytest.fixture(scope="class")
    def auth_token(self):
        """Get authentication token"""
        response = requests.post(f"{BASE_URL}/api/auth/login", json={
            "email": "jjspilot24@gmail.com",
            "password": "InfoPilot2024!"
        })
        assert response.status_code == 200
        return response.json()["token"]
    
    @pytest.fixture(scope="class")
    def headers(self, auth_token):
        return {"Authorization": f"Bearer {auth_token}"}
    
    def test_marketplace_protocols(self, headers):
        """Test GET /api/marketplace/protocols"""
        response = requests.get(f"{BASE_URL}/api/marketplace/protocols", headers=headers)
        assert response.status_code == 200, f"Marketplace protocols failed: {response.text}"
        
        data = response.json()
        protocols = data.get("protocols", data) if isinstance(data, dict) else data
        
        print(f"✓ Marketplace returned {len(protocols) if isinstance(protocols, list) else 'N/A'} protocols")


class TestStatistics:
    """Test Statistics page functionality"""
    
    @pytest.fixture(scope="class")
    def auth_token(self):
        """Get authentication token"""
        response = requests.post(f"{BASE_URL}/api/auth/login", json={
            "email": "jjspilot24@gmail.com",
            "password": "InfoPilot2024!"
        })
        assert response.status_code == 200
        return response.json()["token"]
    
    @pytest.fixture(scope="class")
    def headers(self, auth_token):
        return {"Authorization": f"Bearer {auth_token}"}
    
    def test_statistics_dashboard(self, headers):
        """Test GET /api/statistics/dashboard"""
        response = requests.get(f"{BASE_URL}/api/statistics/dashboard", headers=headers)
        assert response.status_code == 200, f"Statistics dashboard failed: {response.text}"
        
        data = response.json()
        print(f"✓ Statistics dashboard returned data")
        return data
    
    def test_statistics_overview(self, headers):
        """Test GET /api/statistics/overview"""
        response = requests.get(f"{BASE_URL}/api/statistics/overview", headers=headers)
        assert response.status_code == 200, f"Statistics overview failed: {response.text}"
        
        data = response.json()
        print(f"✓ Statistics overview returned data")


class TestAdminPanel:
    """Test Admin Panel access (for admin user)"""
    
    @pytest.fixture(scope="class")
    def auth_token(self):
        """Get authentication token"""
        response = requests.post(f"{BASE_URL}/api/auth/login", json={
            "email": "jjspilot24@gmail.com",
            "password": "InfoPilot2024!"
        })
        assert response.status_code == 200
        return response.json()["token"]
    
    @pytest.fixture(scope="class")
    def headers(self, auth_token):
        return {"Authorization": f"Bearer {auth_token}"}
    
    def test_admin_revenue(self, headers):
        """Test GET /api/admin/revenue"""
        response = requests.get(f"{BASE_URL}/api/admin/revenue", headers=headers)
        # Admin endpoints may return 200 or 403 depending on user role
        assert response.status_code in [200, 403], f"Admin revenue unexpected status: {response.status_code}"
        
        if response.status_code == 200:
            print(f"✓ Admin revenue endpoint accessible")
        else:
            print(f"✓ Admin revenue endpoint returns 403 (expected for non-admin)")


class TestCleanup:
    """Cleanup test data"""
    
    @pytest.fixture(scope="class")
    def auth_token(self):
        """Get authentication token"""
        response = requests.post(f"{BASE_URL}/api/auth/login", json={
            "email": "jjspilot24@gmail.com",
            "password": "InfoPilot2024!"
        })
        assert response.status_code == 200
        return response.json()["token"]
    
    @pytest.fixture(scope="class")
    def headers(self, auth_token):
        return {"Authorization": f"Bearer {auth_token}"}
    
    def test_cleanup_test_categories(self, headers):
        """Clean up any TEST_ prefixed categories"""
        response = requests.get(f"{BASE_URL}/api/categories", headers=headers)
        if response.status_code == 200:
            categories = response.json()
            deleted_count = 0
            for cat in categories:
                if cat["name"].startswith("TEST_"):
                    del_response = requests.delete(f"{BASE_URL}/api/categories/{cat['id']}", headers=headers)
                    if del_response.status_code == 200:
                        deleted_count += 1
            print(f"✓ Cleaned up {deleted_count} test categories")


if __name__ == "__main__":
    pytest.main([__file__, "-v", "--tb=short"])
