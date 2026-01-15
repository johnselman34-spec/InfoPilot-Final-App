"""
InfoPilot Explorer API Tests - Iteration 5
Tests for: FREE APP MODEL - No subscription required
CRITICAL CHANGES:
1) App is now FREE - no subscription required
2) All payment/subscription UI removed
3) User status shows 'FULL ACCESS' instead of FREE TIER/PREMIUM
4) Book 'Letters to Evelyn' promoted throughout app
5) Subscribe page now shows 'APP IS FREE' message with book promo
6) Backend payment restrictions removed - all users get full access
"""
import pytest
import requests
import os
import uuid

BASE_URL = os.environ.get('REACT_APP_BACKEND_URL', 'https://social-research.preview.emergentagent.com')

# Test credentials
ADMIN_EMAIL = "john@infojet.com"
ADMIN_PASSWORD = "password123"
TEST_EMAIL = "testbuyer@example.com"
TEST_PASSWORD = "test1234"


class TestBrandingVerification:
    """CRITICAL: Verify app branding shows 'InfoPilot Explorer' everywhere"""
    
    def test_health_returns_infopilot_explorer(self):
        """Test /api/health returns service: 'InfoPilot Explorer'"""
        response = requests.get(f"{BASE_URL}/api/health")
        assert response.status_code == 200
        data = response.json()
        assert data["status"] == "operational"
        assert data["service"] == "InfoPilot Explorer", f"Expected 'InfoPilot Explorer', got '{data.get('service')}'"
        assert data["mode"] == "tactical"
    
    def test_root_endpoint_mentions_infopilot_explorer(self):
        """Test /api/ returns message with InfoPilot Explorer"""
        response = requests.get(f"{BASE_URL}/api/")
        assert response.status_code == 200
        data = response.json()
        assert "InfoPilot Explorer" in data["message"], f"Expected 'InfoPilot Explorer' in message, got: {data['message']}"


class TestFreeAppModel:
    """Tests for FREE app model - no subscription required"""
    
    @pytest.fixture
    def auth_token(self):
        """Get authentication token for admin user"""
        response = requests.post(f"{BASE_URL}/api/auth/login", json={
            "email": ADMIN_EMAIL,
            "password": ADMIN_PASSWORD
        })
        return response.json()["access_token"]
    
    def test_user_has_full_access(self, auth_token):
        """Test that user has full access (is_paid should be True for admin)"""
        response = requests.get(f"{BASE_URL}/api/auth/me", headers={
            "Authorization": f"Bearer {auth_token}"
        })
        assert response.status_code == 200
        data = response.json()
        # Admin user should have is_paid=True
        assert data["is_admin"] == True
        assert data["is_paid"] == True
    
    def test_categories_work_without_payment(self, auth_token):
        """Test that category CRUD works without payment restrictions"""
        # Create category
        unique_name = f"TEST_FreeApp_{uuid.uuid4().hex[:6]}"
        create_response = requests.post(f"{BASE_URL}/api/categories", 
            headers={"Authorization": f"Bearer {auth_token}"},
            json={
                "name": unique_name,
                "protocol": {"protocol_string": "(free or app)"},
                "is_public": True
            }
        )
        assert create_response.status_code == 200, f"Category creation failed: {create_response.text}"
        category_id = create_response.json()["id"]
        
        # Cleanup
        requests.delete(f"{BASE_URL}/api/categories/{category_id}", headers={
            "Authorization": f"Bearer {auth_token}"
        })
    
    def test_search_collate_works_without_payment(self, auth_token):
        """Test that search/collate works without payment restrictions"""
        response = requests.post(f"{BASE_URL}/api/search/collate",
            headers={"Authorization": f"Bearer {auth_token}"},
            json={
                "search_query": "test query",
                "max_results": 5
            }
        )
        # Should not return 403 (payment required)
        assert response.status_code != 403, "Search should work without payment"
        # May return 200 or other status depending on search results
        assert response.status_code in [200, 400, 404], f"Unexpected status: {response.status_code}"
    
    def test_ultimate_search_works_without_payment(self, auth_token):
        """Test that Ultimate Search features work without payment"""
        # Get page settings
        response = requests.get(f"{BASE_URL}/api/ultimate-search/page-settings",
            headers={"Authorization": f"Bearer {auth_token}"})
        assert response.status_code == 200
        
        # Get map data
        response = requests.get(f"{BASE_URL}/api/ultimate-search/map-data",
            headers={"Authorization": f"Bearer {auth_token}"})
        assert response.status_code == 200
        
        # Get filters
        response = requests.get(f"{BASE_URL}/api/ultimate-search/filters",
            headers={"Authorization": f"Bearer {auth_token}"})
        assert response.status_code == 200


class TestBookPromotion:
    """Tests for book promotion throughout the app"""
    
    def test_book_info_returns_letters_to_evelyn(self):
        """Test /api/book/info returns correct book details"""
        response = requests.get(f"{BASE_URL}/api/book/info")
        assert response.status_code == 200
        data = response.json()
        assert data["title"] == "Letters to Evelyn"
        assert data["author"] == "John Selman"
        assert data["price"] == 2.99
        assert data["rating"] == 5.0
        assert "amazon_url" in data
        assert "official_url" in data
        assert "readers_favorite_url" in data


class TestSafeBrowsingAPI:
    """Safe Browsing API tests"""
    
    def test_safety_status_returns_working(self):
        """Test /api/safety/status returns working: true"""
        response = requests.get(f"{BASE_URL}/api/safety/status")
        assert response.status_code == 200
        data = response.json()
        assert data["working"] == True, f"Safe Browsing API not working: {data}"
        assert data["enabled"] == True


class TestAuthentication:
    """Authentication endpoint tests"""
    
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
    
    def test_login_validation(self):
        """Test login form validation"""
        # Empty email
        response = requests.post(f"{BASE_URL}/api/auth/login", json={
            "email": "",
            "password": "test123"
        })
        assert response.status_code in [400, 422]
        
        # Invalid email format
        response = requests.post(f"{BASE_URL}/api/auth/login", json={
            "email": "notanemail",
            "password": "test123"
        })
        assert response.status_code in [400, 422]
    
    def test_registration_endpoint_exists(self):
        """Test registration endpoint exists"""
        unique_email = f"test_{uuid.uuid4().hex[:8]}@example.com"
        response = requests.post(f"{BASE_URL}/api/auth/register", json={
            "username": f"testuser_{uuid.uuid4().hex[:6]}",
            "email": unique_email,
            "password": "testpass123"
        })
        # Should return 200 for successful registration or 400 if email exists
        assert response.status_code in [200, 400]
    
    def test_get_current_user(self):
        """Test /api/auth/me returns user info"""
        login_response = requests.post(f"{BASE_URL}/api/auth/login", json={
            "email": ADMIN_EMAIL,
            "password": ADMIN_PASSWORD
        })
        token = login_response.json()["access_token"]
        
        response = requests.get(f"{BASE_URL}/api/auth/me", headers={
            "Authorization": f"Bearer {token}"
        })
        assert response.status_code == 200
        data = response.json()
        assert data["email"] == ADMIN_EMAIL
    
    def test_unauthorized_access(self):
        """Test accessing protected endpoint without token"""
        response = requests.get(f"{BASE_URL}/api/auth/me")
        assert response.status_code == 401


class TestCategoryManagement:
    """Category CRUD tests - should work without payment"""
    
    @pytest.fixture
    def auth_token(self):
        """Get authentication token"""
        response = requests.post(f"{BASE_URL}/api/auth/login", json={
            "email": ADMIN_EMAIL,
            "password": ADMIN_PASSWORD
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
        
        # Cleanup
        category_id = data["id"]
        requests.delete(f"{BASE_URL}/api/categories/{category_id}", headers={
            "Authorization": f"Bearer {auth_token}"
        })
    
    def test_update_category(self, auth_token):
        """Test updating a category"""
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
    
    def test_update_page_name(self, auth_token):
        """Test updating page name (RENAME PAGE feature)"""
        new_name = f"My Custom Search Page {uuid.uuid4().hex[:4]}"
        response = requests.put(f"{BASE_URL}/api/ultimate-search/page-settings",
            headers={"Authorization": f"Bearer {auth_token}"},
            json={"page_name": new_name})
        assert response.status_code == 200
        data = response.json()
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
    
    def test_get_photos(self, auth_token):
        """Test getting photos for Ultimate Search page"""
        response = requests.get(f"{BASE_URL}/api/ultimate-search/photos",
            headers={"Authorization": f"Bearer {auth_token}"})
        assert response.status_code == 200
        data = response.json()
        assert "photos" in data
        assert "max_allowed" in data


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
    
    def test_get_admin_settings(self, auth_token):
        """Test getting admin settings"""
        response = requests.get(f"{BASE_URL}/api/admin/settings",
            headers={"Authorization": f"Bearer {auth_token}"})
        assert response.status_code == 200
        data = response.json()
        assert "results_per_page" in data
        assert "blocked_words" in data


class TestNavigationEndpoints:
    """Test all navigation-related endpoints"""
    
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
    
    def test_global_database_categories(self, auth_token):
        """Test global database public categories"""
        response = requests.get(f"{BASE_URL}/api/categories?include_public=true",
            headers={"Authorization": f"Bearer {auth_token}"})
        assert response.status_code == 200


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
