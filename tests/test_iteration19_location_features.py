"""
Iteration 19 - Testing location features for categories and marketplace
Tests:
1. Admin login (jjspilot24@gmail.com)
2. Categories page loads
3. Create category with location data
4. Edit category with location data
5. Marketplace protocols endpoint with location
"""

import pytest
import requests
import os
import uuid

BASE_URL = os.environ.get('REACT_APP_BACKEND_URL', '').rstrip('/')

# Test credentials
ADMIN_EMAIL = "jjspilot24@gmail.com"
ADMIN_PASSWORD = "password123"


class TestAdminLogin:
    """Test admin login functionality"""
    
    def test_admin_login_success(self):
        """Test admin login with correct credentials"""
        response = requests.post(f"{BASE_URL}/api/auth/login", json={
            "email": ADMIN_EMAIL,
            "password": ADMIN_PASSWORD
        })
        
        assert response.status_code == 200, f"Login failed: {response.text}"
        data = response.json()
        
        # Verify response structure
        assert "access_token" in data, "Missing access_token in response"
        assert "user" in data, "Missing user in response"
        
        # Verify user is admin
        user = data["user"]
        assert user["email"] == ADMIN_EMAIL, f"Email mismatch: {user['email']}"
        assert user.get("is_admin") == True, f"User is not admin: {user}"
        
        print(f"✓ Admin login successful for {ADMIN_EMAIL}")
        return data["access_token"]
    
    def test_login_invalid_credentials(self):
        """Test login with invalid credentials"""
        response = requests.post(f"{BASE_URL}/api/auth/login", json={
            "email": "invalid@example.com",
            "password": "wrongpassword"
        })
        
        assert response.status_code == 401, f"Expected 401, got {response.status_code}"
        print("✓ Invalid credentials correctly rejected")


class TestCategoriesAPI:
    """Test categories CRUD operations with location data"""
    
    @pytest.fixture
    def auth_token(self):
        """Get authentication token"""
        response = requests.post(f"{BASE_URL}/api/auth/login", json={
            "email": ADMIN_EMAIL,
            "password": ADMIN_PASSWORD
        })
        if response.status_code == 200:
            return response.json()["access_token"]
        pytest.skip("Authentication failed")
    
    @pytest.fixture
    def auth_headers(self, auth_token):
        """Get headers with auth token"""
        return {"Authorization": f"Bearer {auth_token}"}
    
    def test_get_categories(self, auth_headers):
        """Test fetching categories"""
        response = requests.get(f"{BASE_URL}/api/categories", headers=auth_headers)
        
        assert response.status_code == 200, f"Failed to get categories: {response.text}"
        data = response.json()
        
        # API returns list directly
        assert isinstance(data, list), f"Expected list, got {type(data)}"
        print(f"✓ Categories fetched successfully: {len(data)} categories")
    
    def test_create_category_with_location(self, auth_headers):
        """Test creating a category with location data for marketplace"""
        unique_id = str(uuid.uuid4())[:8]
        category_data = {
            "name": f"TEST_Location_Category_{unique_id}",
            "protocol": {
                "protocol_string": "(test or location) & (marketplace)"
            },
            "is_public": False,
            "for_sale": True,
            "price": 1.50,
            "location": {
                "city": "Denver",
                "state": "Colorado",
                "lat": 39.7392,
                "lng": -104.9903
            }
        }
        
        response = requests.post(f"{BASE_URL}/api/categories", json=category_data, headers=auth_headers)
        
        assert response.status_code == 200, f"Failed to create category: {response.text}"
        data = response.json()
        
        # Verify category was created
        assert "id" in data, "Missing id in response"
        assert data["name"] == category_data["name"], f"Name mismatch: {data['name']}"
        assert data.get("for_sale") == True, "Category should be for_sale"
        assert data.get("price") == 1.50, f"Price mismatch: {data.get('price')}"
        
        # Verify location data
        location = data.get("location")
        assert location is not None, "Missing location in response"
        assert location.get("city") == "Denver", f"City mismatch: {location}"
        assert location.get("state") == "Colorado", f"State mismatch: {location}"
        
        print(f"✓ Category created with location: {data['name']}")
        return data["id"]
    
    def test_update_category_with_location(self, auth_headers):
        """Test updating a category to add location data"""
        # First create a category without location
        unique_id = str(uuid.uuid4())[:8]
        create_data = {
            "name": f"TEST_Update_Location_{unique_id}",
            "protocol": {
                "protocol_string": "(update or test)"
            },
            "is_public": False,
            "for_sale": True,
            "price": 0.99
        }
        
        create_response = requests.post(f"{BASE_URL}/api/categories", json=create_data, headers=auth_headers)
        assert create_response.status_code == 200, f"Failed to create category: {create_response.text}"
        category_id = create_response.json()["id"]
        
        # Now update with location
        update_data = {
            "name": f"TEST_Update_Location_{unique_id}_Updated",
            "protocol_string": "(update or test) & (location)",
            "is_public": False,
            "for_sale": True,
            "price": 1.25,
            "location": {
                "city": "Seattle",
                "state": "Washington",
                "lat": 47.6062,
                "lng": -122.3321
            }
        }
        
        update_response = requests.put(f"{BASE_URL}/api/categories/{category_id}", json=update_data, headers=auth_headers)
        
        assert update_response.status_code == 200, f"Failed to update category: {update_response.text}"
        data = update_response.json()
        
        # Verify location was added
        location = data.get("location")
        assert location is not None, "Missing location after update"
        assert location.get("city") == "Seattle", f"City mismatch after update: {location}"
        assert location.get("state") == "Washington", f"State mismatch after update: {location}"
        
        print(f"✓ Category updated with location: {data['name']}")
        
        # Cleanup
        requests.delete(f"{BASE_URL}/api/categories/{category_id}", headers=auth_headers)


class TestMarketplaceAPI:
    """Test marketplace protocols endpoint"""
    
    @pytest.fixture
    def auth_token(self):
        """Get authentication token"""
        response = requests.post(f"{BASE_URL}/api/auth/login", json={
            "email": ADMIN_EMAIL,
            "password": ADMIN_PASSWORD
        })
        if response.status_code == 200:
            return response.json()["access_token"]
        pytest.skip("Authentication failed")
    
    @pytest.fixture
    def auth_headers(self, auth_token):
        """Get headers with auth token"""
        return {"Authorization": f"Bearer {auth_token}"}
    
    def test_marketplace_protocols_endpoint(self, auth_headers):
        """Test marketplace protocols endpoint returns location data"""
        response = requests.get(f"{BASE_URL}/api/marketplace/protocols", headers=auth_headers)
        
        assert response.status_code == 200, f"Failed to get marketplace protocols: {response.text}"
        data = response.json()
        
        assert "protocols" in data, "Missing protocols in response"
        protocols = data["protocols"]
        
        print(f"✓ Marketplace protocols fetched: {len(protocols)} protocols")
        
        # Check if any protocols have location data
        protocols_with_location = [p for p in protocols if p.get("location")]
        print(f"  - Protocols with location: {len(protocols_with_location)}")
        
        for p in protocols_with_location[:3]:  # Show first 3
            loc = p.get("location", {})
            print(f"    • {p['name']}: {loc.get('city', 'N/A')}, {loc.get('state', 'N/A')}")
    
    def test_marketplace_requires_auth(self):
        """Test marketplace endpoint requires authentication"""
        response = requests.get(f"{BASE_URL}/api/marketplace/protocols")
        
        # Should fail without auth
        assert response.status_code in [401, 403], f"Expected 401/403, got {response.status_code}"
        print("✓ Marketplace correctly requires authentication")


class TestCleanup:
    """Cleanup test data"""
    
    @pytest.fixture
    def auth_headers(self):
        """Get authentication token"""
        response = requests.post(f"{BASE_URL}/api/auth/login", json={
            "email": ADMIN_EMAIL,
            "password": ADMIN_PASSWORD
        })
        if response.status_code == 200:
            return {"Authorization": f"Bearer {response.json()['access_token']}"}
        pytest.skip("Authentication failed")
    
    def test_cleanup_test_categories(self, auth_headers):
        """Clean up TEST_ prefixed categories"""
        response = requests.get(f"{BASE_URL}/api/categories", headers=auth_headers)
        if response.status_code == 200:
            categories = response.json()  # API returns list directly
            if isinstance(categories, list):
                test_categories = [c for c in categories if c["name"].startswith("TEST_")]
                
                for cat in test_categories:
                    requests.delete(f"{BASE_URL}/api/categories/{cat['id']}", headers=auth_headers)
                
                print(f"✓ Cleaned up {len(test_categories)} test categories")


if __name__ == "__main__":
    pytest.main([__file__, "-v", "--tb=short"])
