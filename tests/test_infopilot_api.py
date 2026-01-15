"""
InfoPilot API Backend Tests
Tests for: Authentication, Categories, Search, Safe Browsing, Book Info, Subscription
"""
import pytest
import requests
import os
import uuid

BASE_URL = os.environ.get('REACT_APP_BACKEND_URL', 'https://explorer-social.preview.emergentagent.com')

# Test credentials
TEST_EMAIL = "john@infojet.com"
TEST_PASSWORD = "password123"

class TestHealthEndpoints:
    """Health and status endpoint tests"""
    
    def test_health_check(self):
        """Test /api/health returns operational status"""
        response = requests.get(f"{BASE_URL}/api/health")
        assert response.status_code == 200
        data = response.json()
        assert data["status"] == "operational"
        assert data["service"] == "InfoPilot"
    
    def test_root_endpoint(self):
        """Test /api/ returns API info"""
        response = requests.get(f"{BASE_URL}/api/")
        assert response.status_code == 200
        data = response.json()
        assert "InfoPilot" in data["message"]


class TestSafeBrowsingAPI:
    """Safe Browsing API tests - CRITICAL"""
    
    def test_safety_status_returns_working(self):
        """Test /api/safety/status returns working: true"""
        response = requests.get(f"{BASE_URL}/api/safety/status")
        assert response.status_code == 200
        data = response.json()
        assert data["working"] == True, f"Safe Browsing API not working: {data}"
        assert data["enabled"] == True


class TestBookInfo:
    """Book info endpoint tests"""
    
    def test_book_info_returns_letters_to_evelyn(self):
        """Test /api/book/info returns correct book details"""
        response = requests.get(f"{BASE_URL}/api/book/info")
        assert response.status_code == 200
        data = response.json()
        assert data["title"] == "Letters to Evelyn"
        assert data["author"] == "John Selman"
        assert data["price"] == 2.99
        assert data["rating"] == 5.0


class TestSubscriptionInfo:
    """Subscription info endpoint tests"""
    
    def test_subscription_info_shows_sale_price(self):
        """Test /api/subscription/info shows $0.75 Welcome Sale"""
        response = requests.get(f"{BASE_URL}/api/subscription/info")
        assert response.status_code == 200
        data = response.json()
        assert data["price"] == 0.75, f"Expected $0.75 sale price, got {data['price']}"
        assert data["is_sale_active"] == True
        assert data["sale_name"] == "Welcome Sale"
        assert data["regular_price"] == 4.62


class TestAuthentication:
    """Authentication endpoint tests"""
    
    def test_login_with_valid_credentials(self):
        """Test login with john@infojet.com / password123"""
        response = requests.post(f"{BASE_URL}/api/auth/login", json={
            "email": TEST_EMAIL,
            "password": TEST_PASSWORD
        })
        assert response.status_code == 200
        data = response.json()
        assert "access_token" in data
        assert data["user"]["email"] == TEST_EMAIL
        assert data["user"]["is_admin"] == True
        assert data["user"]["is_paid"] == True
    
    def test_login_with_invalid_credentials(self):
        """Test login with wrong password returns 401"""
        response = requests.post(f"{BASE_URL}/api/auth/login", json={
            "email": TEST_EMAIL,
            "password": "wrongpassword"
        })
        assert response.status_code == 401
    
    def test_get_current_user(self):
        """Test /api/auth/me returns user info"""
        # First login to get token
        login_response = requests.post(f"{BASE_URL}/api/auth/login", json={
            "email": TEST_EMAIL,
            "password": TEST_PASSWORD
        })
        token = login_response.json()["access_token"]
        
        # Get current user
        response = requests.get(f"{BASE_URL}/api/auth/me", headers={
            "Authorization": f"Bearer {token}"
        })
        assert response.status_code == 200
        data = response.json()
        assert data["email"] == TEST_EMAIL


class TestCategoryManagement:
    """Category CRUD tests"""
    
    @pytest.fixture
    def auth_token(self):
        """Get authentication token"""
        response = requests.post(f"{BASE_URL}/api/auth/login", json={
            "email": TEST_EMAIL,
            "password": TEST_PASSWORD
        })
        return response.json()["access_token"]
    
    def test_get_categories(self, auth_token):
        """Test getting categories list"""
        response = requests.get(f"{BASE_URL}/api/categories", headers={
            "Authorization": f"Bearer {auth_token}"
        })
        assert response.status_code == 200
        assert isinstance(response.json(), list)
    
    def test_create_category(self, auth_token):
        """Test creating a new category"""
        unique_name = f"TEST_Category_{uuid.uuid4().hex[:6]}"
        response = requests.post(f"{BASE_URL}/api/categories", 
            headers={"Authorization": f"Bearer {auth_token}"},
            json={
                "name": unique_name,
                "protocol": {"protocol_string": "(test or example)"},
                "is_public": True
            }
        )
        assert response.status_code == 200
        data = response.json()
        assert data["name"] == unique_name
        
        # Cleanup - delete the category
        category_id = data["id"]
        requests.delete(f"{BASE_URL}/api/categories/{category_id}", headers={
            "Authorization": f"Bearer {auth_token}"
        })
    
    def test_update_category(self, auth_token):
        """Test updating a category"""
        # Create a category first
        unique_name = f"TEST_Update_{uuid.uuid4().hex[:6]}"
        create_response = requests.post(f"{BASE_URL}/api/categories", 
            headers={"Authorization": f"Bearer {auth_token}"},
            json={
                "name": unique_name,
                "protocol": {"protocol_string": "(update or test)"},
                "is_public": True
            }
        )
        category_id = create_response.json()["id"]
        
        # Update the category
        new_name = f"TEST_Updated_{uuid.uuid4().hex[:6]}"
        update_response = requests.put(f"{BASE_URL}/api/categories/{category_id}",
            headers={"Authorization": f"Bearer {auth_token}"},
            json={
                "name": new_name,
                "protocol_string": "(updated or modified)"
            }
        )
        assert update_response.status_code == 200
        assert update_response.json()["name"] == new_name
        
        # Cleanup
        requests.delete(f"{BASE_URL}/api/categories/{category_id}", headers={
            "Authorization": f"Bearer {auth_token}"
        })
    
    def test_delete_category(self, auth_token):
        """Test deleting a category"""
        # Create a category first
        unique_name = f"TEST_Delete_{uuid.uuid4().hex[:6]}"
        create_response = requests.post(f"{BASE_URL}/api/categories", 
            headers={"Authorization": f"Bearer {auth_token}"},
            json={
                "name": unique_name,
                "protocol": {"protocol_string": "(delete or test)"},
                "is_public": True
            }
        )
        category_id = create_response.json()["id"]
        
        # Delete the category
        delete_response = requests.delete(f"{BASE_URL}/api/categories/{category_id}",
            headers={"Authorization": f"Bearer {auth_token}"})
        assert delete_response.status_code == 200
        
        # Verify deletion
        get_response = requests.get(f"{BASE_URL}/api/categories/{category_id}",
            headers={"Authorization": f"Bearer {auth_token}"})
        assert get_response.status_code == 404


class TestUltimateSearch:
    """Ultimate Search page tests"""
    
    @pytest.fixture
    def auth_token(self):
        """Get authentication token"""
        response = requests.post(f"{BASE_URL}/api/auth/login", json={
            "email": TEST_EMAIL,
            "password": TEST_PASSWORD
        })
        return response.json()["access_token"]
    
    def test_get_page_settings(self, auth_token):
        """Test getting Ultimate Search page settings"""
        response = requests.get(f"{BASE_URL}/api/ultimate-search/page-settings",
            headers={"Authorization": f"Bearer {auth_token}"})
        assert response.status_code == 200
        data = response.json()
        assert "page_name" in data
    
    def test_update_page_name(self, auth_token):
        """Test updating page name (RENAME PAGE feature)"""
        new_name = f"My Custom Search Page {uuid.uuid4().hex[:4]}"
        response = requests.put(f"{BASE_URL}/api/ultimate-search/page-settings",
            headers={"Authorization": f"Bearer {auth_token}"},
            json={"page_name": new_name})
        assert response.status_code == 200
        data = response.json()
        # Response structure: {"message": "...", "settings": {"page_name": "..."}}
        assert data["settings"]["page_name"] == new_name
    
    def test_get_map_data(self, auth_token):
        """Test getting map data for Google Maps integration"""
        response = requests.get(f"{BASE_URL}/api/ultimate-search/map-data",
            headers={"Authorization": f"Bearer {auth_token}"})
        assert response.status_code == 200
        data = response.json()
        assert "markers" in data
        assert "categories" in data
    
    def test_get_filters(self, auth_token):
        """Test getting search filters"""
        response = requests.get(f"{BASE_URL}/api/ultimate-search/filters",
            headers={"Authorization": f"Bearer {auth_token}"})
        assert response.status_code == 200
        data = response.json()
        assert "document_types" in data
        assert "article_types" in data


class TestAdminPanel:
    """Admin panel tests"""
    
    @pytest.fixture
    def auth_token(self):
        """Get authentication token"""
        response = requests.post(f"{BASE_URL}/api/auth/login", json={
            "email": TEST_EMAIL,
            "password": TEST_PASSWORD
        })
        return response.json()["access_token"]
    
    def test_get_admin_settings(self, auth_token):
        """Test getting admin settings"""
        response = requests.get(f"{BASE_URL}/api/admin/settings",
            headers={"Authorization": f"Bearer {auth_token}"})
        assert response.status_code == 200
        data = response.json()
        assert "results_per_page" in data
        assert "blocked_words" in data


class TestPaymentConfig:
    """Payment configuration tests"""
    
    def test_get_stripe_config(self):
        """Test getting Stripe configuration"""
        response = requests.get(f"{BASE_URL}/api/payments/config")
        assert response.status_code == 200
        data = response.json()
        assert "publishable_key" in data
        assert data["sale_price"] == 0.75
        assert data["is_sale_active"] == True


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
