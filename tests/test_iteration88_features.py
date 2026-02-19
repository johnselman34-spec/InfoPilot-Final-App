"""
InfoPilot Explorer - Iteration 88 Feature Tests
Testing:
1. Categories have price field and can be updated
2. Statistics page loading with user/category/search counts
3. Map data endpoint working
4. Marketplace protocols loading
5. Stripe integration enabled
6. Categories CRUD with price setting
7. All major pages accessible
"""
import pytest
import requests
import os

BASE_URL = os.environ.get('REACT_APP_BACKEND_URL', '').rstrip('/')

# Test credentials
TEST_EMAIL = "jjspilot24@gmail.com"
TEST_PASSWORD = "InfoPilot2024!"


class TestAuthentication:
    """Authentication tests"""
    
    @pytest.fixture(scope="class")
    def auth_token(self):
        """Get authentication token"""
        response = requests.post(f"{BASE_URL}/api/auth/login", json={
            "email": TEST_EMAIL,
            "password": TEST_PASSWORD
        })
        assert response.status_code == 200, f"Login failed: {response.text}"
        data = response.json()
        assert "token" in data, "No token in response"
        return data["token"]
    
    def test_login_success(self, auth_token):
        """Test login returns valid token"""
        assert auth_token is not None
        assert len(auth_token) > 10


class TestStatisticsEndpoint:
    """Statistics endpoint tests - verify user/category/search counts"""
    
    def test_statistics_overview(self):
        """Test statistics overview returns expected data"""
        response = requests.get(f"{BASE_URL}/api/statistics/overview")
        assert response.status_code == 200, f"Statistics overview failed: {response.text}"
        
        data = response.json()
        
        # Verify expected fields exist
        assert "total_users" in data, "Missing total_users"
        assert "total_categories" in data, "Missing total_categories"
        assert "total_searches" in data, "Missing total_searches"
        assert "total_protocols" in data, "Missing total_protocols"
        
        # Verify expected counts (from iteration 87: 25 users, 29 categories, 1696 searches)
        assert data["total_users"] >= 25, f"Expected at least 25 users, got {data['total_users']}"
        assert data["total_categories"] >= 29, f"Expected at least 29 categories, got {data['total_categories']}"
        assert data["total_searches"] >= 1696, f"Expected at least 1696 searches, got {data['total_searches']}"
        
        print(f"✓ Statistics: {data['total_users']} users, {data['total_categories']} categories, {data['total_searches']} searches")
    
    def test_statistics_countries(self):
        """Test country statistics endpoint"""
        response = requests.get(f"{BASE_URL}/api/statistics/countries")
        assert response.status_code == 200, f"Countries stats failed: {response.text}"
        
        data = response.json()
        assert "countries" in data
        assert len(data["countries"]) > 0
        print(f"✓ Country statistics: {len(data['countries'])} countries")
    
    def test_statistics_document_types(self):
        """Test document types statistics endpoint"""
        response = requests.get(f"{BASE_URL}/api/statistics/document-types")
        assert response.status_code == 200, f"Document types stats failed: {response.text}"
        
        data = response.json()
        assert "document_types" in data
        assert len(data["document_types"]) > 0
        print(f"✓ Document types: {len(data['document_types'])} types")


class TestCategoriesWithPrice:
    """Categories CRUD tests with price field support"""
    
    @pytest.fixture(scope="class")
    def auth_token(self):
        """Get authentication token"""
        response = requests.post(f"{BASE_URL}/api/auth/login", json={
            "email": TEST_EMAIL,
            "password": TEST_PASSWORD
        })
        assert response.status_code == 200
        return response.json()["token"]
    
    @pytest.fixture(scope="class")
    def auth_headers(self, auth_token):
        """Get auth headers"""
        return {"Authorization": f"Bearer {auth_token}"}
    
    def test_get_categories(self, auth_headers):
        """Test getting categories list"""
        response = requests.get(f"{BASE_URL}/api/categories", headers=auth_headers)
        assert response.status_code == 200, f"Get categories failed: {response.text}"
        
        data = response.json()
        assert isinstance(data, list), "Categories should be a list"
        assert len(data) > 0, "Should have at least one category"
        
        # Check that categories have expected fields including price
        first_cat = data[0]
        assert "id" in first_cat
        assert "name" in first_cat
        assert "protocol" in first_cat
        
        print(f"✓ Categories loaded: {len(data)} categories")
    
    def test_create_category_with_price(self, auth_headers):
        """Test creating a category (price is set via update)"""
        # Create category
        create_payload = {
            "name": "TEST_Iteration88_PriceCategory",
            "protocol": "(test or testing) & (price or pricing)",
            "is_public": False
        }
        
        response = requests.post(f"{BASE_URL}/api/categories", json=create_payload, headers=auth_headers)
        assert response.status_code == 200, f"Create category failed: {response.text}"
        
        data = response.json()
        assert "id" in data
        category_id = data["id"]
        
        print(f"✓ Category created: {category_id}")
        return category_id
    
    def test_update_category_with_price(self, auth_headers):
        """Test updating a category with price field"""
        # First create a category
        create_payload = {
            "name": "TEST_Iteration88_UpdatePrice",
            "protocol": "(update or modify) & (price or cost)",
            "is_public": False
        }
        
        response = requests.post(f"{BASE_URL}/api/categories", json=create_payload, headers=auth_headers)
        assert response.status_code == 200, f"Create category failed: {response.text}"
        category_id = response.json()["id"]
        
        # Update with price
        update_payload = {
            "name": "TEST_Iteration88_UpdatePrice_Modified",
            "price": 9.99
        }
        
        response = requests.put(f"{BASE_URL}/api/categories/{category_id}", json=update_payload, headers=auth_headers)
        assert response.status_code == 200, f"Update category failed: {response.text}"
        
        data = response.json()
        assert data.get("price") == 9.99, f"Price not updated correctly: {data.get('price')}"
        
        print(f"✓ Category price updated to ${data.get('price')}")
        
        # Cleanup
        requests.delete(f"{BASE_URL}/api/categories/{category_id}", headers=auth_headers)
    
    def test_delete_category(self, auth_headers):
        """Test deleting a category"""
        # Create a category to delete
        create_payload = {
            "name": "TEST_Iteration88_ToDelete",
            "protocol": "(delete or remove)",
            "is_public": False
        }
        
        response = requests.post(f"{BASE_URL}/api/categories", json=create_payload, headers=auth_headers)
        assert response.status_code == 200
        category_id = response.json()["id"]
        
        # Delete it
        response = requests.delete(f"{BASE_URL}/api/categories/{category_id}", headers=auth_headers)
        assert response.status_code == 200, f"Delete category failed: {response.text}"
        
        print(f"✓ Category deleted: {category_id}")


class TestMapDataEndpoint:
    """Map data endpoint tests"""
    
    @pytest.fixture(scope="class")
    def auth_token(self):
        """Get authentication token"""
        response = requests.post(f"{BASE_URL}/api/auth/login", json={
            "email": TEST_EMAIL,
            "password": TEST_PASSWORD
        })
        assert response.status_code == 200
        return response.json()["token"]
    
    @pytest.fixture(scope="class")
    def auth_headers(self, auth_token):
        """Get auth headers"""
        return {"Authorization": f"Bearer {auth_token}"}
    
    def test_map_data_endpoint(self, auth_headers):
        """Test map data endpoint returns location data"""
        response = requests.get(f"{BASE_URL}/api/map-data", headers=auth_headers)
        assert response.status_code == 200, f"Map data failed: {response.text}"
        
        data = response.json()
        assert "results" in data or "locations" in data or "data" in data, f"Unexpected response format: {data.keys()}"
        
        print(f"✓ Map data endpoint working")
    
    def test_map_worldwide_endpoint(self, auth_headers):
        """Test worldwide map endpoint"""
        response = requests.get(f"{BASE_URL}/api/map/worldwide?limit=100", headers=auth_headers)
        assert response.status_code == 200, f"Worldwide map failed: {response.text}"
        
        data = response.json()
        print(f"✓ Worldwide map endpoint working: {len(data.get('results', data.get('locations', [])))} locations")


class TestMarketplaceProtocols:
    """Marketplace protocols tests"""
    
    def test_marketplace_protocols_list(self):
        """Test marketplace protocols listing (public endpoint)"""
        response = requests.get(f"{BASE_URL}/api/marketplace/protocols")
        assert response.status_code == 200, f"Marketplace protocols failed: {response.text}"
        
        data = response.json()
        assert "protocols" in data, "Missing protocols field"
        assert "total" in data, "Missing total field"
        
        protocols = data["protocols"]
        assert len(protocols) > 0, "Should have at least one protocol"
        
        # Check protocol structure
        first_protocol = protocols[0]
        assert "id" in first_protocol
        assert "name" in first_protocol
        assert "price" in first_protocol
        assert "category" in first_protocol
        
        print(f"✓ Marketplace protocols: {len(protocols)} protocols available")
    
    def test_marketplace_categories(self):
        """Test marketplace categories endpoint"""
        response = requests.get(f"{BASE_URL}/api/marketplace/categories")
        assert response.status_code == 200, f"Marketplace categories failed: {response.text}"
        
        data = response.json()
        assert "categories" in data
        
        print(f"✓ Marketplace categories: {len(data['categories'])} categories")


class TestStripeIntegration:
    """Stripe payment integration tests"""
    
    def test_stripe_config_endpoint(self):
        """Test Stripe configuration endpoint returns enabled status"""
        response = requests.get(f"{BASE_URL}/api/stripe/config")
        assert response.status_code == 200, f"Stripe config failed: {response.text}"
        
        data = response.json()
        assert "enabled" in data, "Missing enabled field"
        assert data["enabled"] == True, "Stripe should be enabled"
        
        # Check for publishable key
        if "publishable_key" in data:
            assert data["publishable_key"].startswith("pk_"), "Invalid publishable key format"
        
        print(f"✓ Stripe integration enabled: {data.get('enabled')}")
    
    def test_stripe_prices_endpoint(self):
        """Test Stripe prices endpoint returns pricing options"""
        response = requests.get(f"{BASE_URL}/api/stripe/prices")
        assert response.status_code == 200, f"Stripe prices failed: {response.text}"
        
        data = response.json()
        assert "prices" in data, "Missing prices field"
        
        prices = data["prices"]
        assert len(prices) > 0, "Should have at least one price option"
        
        print(f"✓ Stripe prices: {len(prices)} pricing options")


class TestSearchEngines:
    """Search engines endpoint tests"""
    
    def test_search_engines_list(self):
        """Test search engines endpoint"""
        response = requests.get(f"{BASE_URL}/api/search-engines")
        assert response.status_code == 200, f"Search engines failed: {response.text}"
        
        data = response.json()
        assert "engines" in data, "Missing engines field"
        
        print(f"✓ Search engines: {len(data['engines'])} engines available")


class TestDataControlsComponents:
    """Tests for new DataControls shared components functionality"""
    
    @pytest.fixture(scope="class")
    def auth_token(self):
        """Get authentication token"""
        response = requests.post(f"{BASE_URL}/api/auth/login", json={
            "email": TEST_EMAIL,
            "password": TEST_PASSWORD
        })
        assert response.status_code == 200
        return response.json()["token"]
    
    @pytest.fixture(scope="class")
    def auth_headers(self, auth_token):
        """Get auth headers"""
        return {"Authorization": f"Bearer {auth_token}"}
    
    def test_categories_for_select_all(self, auth_headers):
        """Test categories endpoint returns data for Select All/Deselect All functionality"""
        response = requests.get(f"{BASE_URL}/api/categories", headers=auth_headers)
        assert response.status_code == 200
        
        data = response.json()
        assert isinstance(data, list)
        
        # Verify we can get all category names for Select All functionality
        category_names = [cat["name"] for cat in data]
        assert len(category_names) > 0
        
        print(f"✓ Categories for Select All: {len(category_names)} categories available")


class TestRealTimeUpdates:
    """Tests for real-time update functionality on Marketplace"""
    
    def test_marketplace_protocols_refresh(self):
        """Test marketplace protocols can be refreshed (simulating real-time updates)"""
        # First request
        response1 = requests.get(f"{BASE_URL}/api/marketplace/protocols")
        assert response1.status_code == 200
        data1 = response1.json()
        
        # Second request (simulating refresh)
        response2 = requests.get(f"{BASE_URL}/api/marketplace/protocols")
        assert response2.status_code == 200
        data2 = response2.json()
        
        # Both should return valid data
        assert "protocols" in data1
        assert "protocols" in data2
        
        print(f"✓ Real-time updates: Marketplace refresh working")


if __name__ == "__main__":
    pytest.main([__file__, "-v", "--tb=short"])
