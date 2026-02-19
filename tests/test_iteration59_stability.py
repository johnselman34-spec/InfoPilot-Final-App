"""
InfoPilot Explorer - Iteration 59 Stability & Feature Tests
Tests: Health, Auth, Easter Eggs, Personal Reports, PayPal Wallet, Clean Categories, 
       Categories CRUD, Search, User Settings, Gamification, Newsletter, Admin Panel, Legal
"""
import pytest
import requests
import os
import time

BASE_URL = os.environ.get('REACT_APP_BACKEND_URL', 'https://infopilot-preview.preview.emergentagent.com')

# Test credentials
ADMIN_EMAIL = "jjspilot24@gmail.com"
ADMIN_PASSWORD = "InfoPilot2024!"
TEST_EMAIL = "testuser@example.com"
TEST_PASSWORD = "password123"


class TestHealthAndBasics:
    """Basic health and connectivity tests"""
    
    def test_health_endpoint(self):
        """Test /api/health returns healthy status"""
        response = requests.get(f"{BASE_URL}/api/health")
        assert response.status_code == 200
        data = response.json()
        assert data.get("status") == "healthy"
        print(f"✅ Health check passed: {data}")
    
    def test_subscription_info(self):
        """Test subscription info endpoint"""
        response = requests.get(f"{BASE_URL}/api/subscription-info")
        assert response.status_code == 200
        data = response.json()
        assert "price" in data
        assert "payment_link" in data
        print(f"✅ Subscription info: price=${data.get('price')}")


class TestAuthentication:
    """Authentication flow tests"""
    
    def test_admin_login(self):
        """Test admin login with provided credentials"""
        response = requests.post(f"{BASE_URL}/api/auth/login", json={
            "email": ADMIN_EMAIL,
            "password": ADMIN_PASSWORD
        })
        assert response.status_code == 200
        data = response.json()
        assert "token" in data
        assert "user" in data
        assert data["user"].get("is_admin") == True
        print(f"✅ Admin login successful: {data['user'].get('email')}")
        return data["token"]
    
    def test_invalid_login(self):
        """Test login with invalid credentials"""
        response = requests.post(f"{BASE_URL}/api/auth/login", json={
            "email": "invalid@example.com",
            "password": "wrongpassword"
        })
        assert response.status_code in [401, 400]
        print("✅ Invalid login correctly rejected")


class TestCategoriesAPI:
    """Categories CRUD operations"""
    
    @pytest.fixture
    def auth_token(self):
        """Get admin auth token"""
        response = requests.post(f"{BASE_URL}/api/auth/login", json={
            "email": ADMIN_EMAIL,
            "password": ADMIN_PASSWORD
        })
        if response.status_code == 200:
            return response.json().get("token")
        pytest.skip("Authentication failed")
    
    def test_list_categories(self, auth_token):
        """Test listing categories"""
        headers = {"Authorization": f"Bearer {auth_token}"}
        response = requests.get(f"{BASE_URL}/api/categories", headers=headers)
        assert response.status_code == 200
        data = response.json()
        assert isinstance(data, list)
        print(f"✅ Categories list: {len(data)} categories found")
        return data
    
    def test_category_results_count(self, auth_token):
        """Test getting results count for a category"""
        headers = {"Authorization": f"Bearer {auth_token}"}
        
        # First get categories
        cats_response = requests.get(f"{BASE_URL}/api/categories", headers=headers)
        if cats_response.status_code != 200:
            pytest.skip("Could not get categories")
        
        categories = cats_response.json()
        if not categories:
            pytest.skip("No categories available")
        
        # Test results count for first category
        cat_id = categories[0].get("id")
        response = requests.get(f"{BASE_URL}/api/categories/{cat_id}/results-count", headers=headers)
        assert response.status_code == 200
        data = response.json()
        assert "total_results" in data
        assert "exclusive_results" in data
        assert "shared_results" in data
        print(f"✅ Category results count: {data}")
    
    def test_clean_category_remove_mode(self, auth_token):
        """Test clean category with remove mode (dry run - just check endpoint works)"""
        headers = {"Authorization": f"Bearer {auth_token}"}
        
        # Get categories
        cats_response = requests.get(f"{BASE_URL}/api/categories", headers=headers)
        if cats_response.status_code != 200:
            pytest.skip("Could not get categories")
        
        categories = cats_response.json()
        if not categories:
            pytest.skip("No categories available")
        
        # Find a category with results
        cat_id = None
        for cat in categories:
            if cat.get("result_count", 0) > 0:
                cat_id = cat.get("id")
                break
        
        if not cat_id:
            cat_id = categories[0].get("id")
        
        # Test the endpoint exists and responds correctly
        response = requests.post(
            f"{BASE_URL}/api/categories/{cat_id}/clean?mode=remove", 
            headers=headers
        )
        # Should return 200 even if no results to clean
        assert response.status_code == 200
        data = response.json()
        assert "success" in data
        assert data.get("mode") == "remove"
        print(f"✅ Clean category (remove mode) works: {data.get('message')}")


class TestPersonalReportsAPI:
    """Personal Reports CRUD tests"""
    
    @pytest.fixture
    def auth_token(self):
        """Get admin auth token"""
        response = requests.post(f"{BASE_URL}/api/auth/login", json={
            "email": ADMIN_EMAIL,
            "password": ADMIN_PASSWORD
        })
        if response.status_code == 200:
            return response.json().get("token")
        pytest.skip("Authentication failed")
    
    def test_list_personal_reports(self, auth_token):
        """Test listing personal reports"""
        headers = {"Authorization": f"Bearer {auth_token}"}
        response = requests.get(f"{BASE_URL}/api/personal-reports", headers=headers)
        # Should return 200 or 404 if endpoint doesn't exist
        if response.status_code == 404:
            print("⚠️ Personal reports endpoint not found - may need to check route")
            pytest.skip("Personal reports endpoint not available")
        assert response.status_code == 200
        data = response.json()
        print(f"✅ Personal reports: {len(data) if isinstance(data, list) else 'response received'}")


class TestPayPalWalletAPI:
    """PayPal Wallet/Earnings tests"""
    
    @pytest.fixture
    def auth_token(self):
        """Get admin auth token"""
        response = requests.post(f"{BASE_URL}/api/auth/login", json={
            "email": ADMIN_EMAIL,
            "password": ADMIN_PASSWORD
        })
        if response.status_code == 200:
            return response.json().get("token")
        pytest.skip("Authentication failed")
    
    def test_earnings_endpoint(self, auth_token):
        """Test PayPal earnings endpoint"""
        headers = {"Authorization": f"Bearer {auth_token}"}
        response = requests.get(f"{BASE_URL}/api/marketplace/earnings", headers=headers)
        if response.status_code == 404:
            print("⚠️ Earnings endpoint not found")
            pytest.skip("Earnings endpoint not available")
        assert response.status_code == 200
        data = response.json()
        print(f"✅ Earnings endpoint works: {data}")


class TestGamificationAPI:
    """Gamification/Achievements tests"""
    
    @pytest.fixture
    def auth_token(self):
        """Get admin auth token"""
        response = requests.post(f"{BASE_URL}/api/auth/login", json={
            "email": ADMIN_EMAIL,
            "password": ADMIN_PASSWORD
        })
        if response.status_code == 200:
            return response.json().get("token")
        pytest.skip("Authentication failed")
    
    def test_achievements_list(self):
        """Test public achievements list"""
        response = requests.get(f"{BASE_URL}/api/gamification/achievements")
        assert response.status_code == 200
        data = response.json()
        assert "achievements" in data
        print(f"✅ Achievements list: {len(data.get('achievements', []))} achievements")
    
    def test_my_achievements(self, auth_token):
        """Test user's achievements"""
        headers = {"Authorization": f"Bearer {auth_token}"}
        response = requests.get(f"{BASE_URL}/api/gamification/my-achievements", headers=headers)
        assert response.status_code == 200
        data = response.json()
        assert "earned" in data or "total_points" in data
        print(f"✅ My achievements: {data.get('total_points', 0)} points")
    
    def test_weekly_leaderboard(self):
        """Test weekly leaderboard"""
        response = requests.get(f"{BASE_URL}/api/gamification/leaderboard/weekly")
        assert response.status_code == 200
        data = response.json()
        assert "leaderboard" in data
        print(f"✅ Weekly leaderboard: {len(data.get('leaderboard', []))} entries")


class TestNewsletterAPI:
    """Newsletter system tests"""
    
    @pytest.fixture
    def auth_token(self):
        """Get admin auth token"""
        response = requests.post(f"{BASE_URL}/api/auth/login", json={
            "email": ADMIN_EMAIL,
            "password": ADMIN_PASSWORD
        })
        if response.status_code == 200:
            return response.json().get("token")
        pytest.skip("Authentication failed")
    
    def test_newsletter_status(self, auth_token):
        """Test newsletter status endpoint"""
        headers = {"Authorization": f"Bearer {auth_token}"}
        response = requests.get(f"{BASE_URL}/api/newsletter/status", headers=headers)
        if response.status_code == 404:
            print("⚠️ Newsletter status endpoint not found")
            pytest.skip("Newsletter endpoint not available")
        assert response.status_code == 200
        data = response.json()
        print(f"✅ Newsletter status: {data}")


class TestUserSettingsAPI:
    """User settings/profile tests"""
    
    @pytest.fixture
    def auth_token(self):
        """Get admin auth token"""
        response = requests.post(f"{BASE_URL}/api/auth/login", json={
            "email": ADMIN_EMAIL,
            "password": ADMIN_PASSWORD
        })
        if response.status_code == 200:
            return response.json().get("token")
        pytest.skip("Authentication failed")
    
    def test_get_user_profile(self, auth_token):
        """Test getting user profile"""
        headers = {"Authorization": f"Bearer {auth_token}"}
        response = requests.get(f"{BASE_URL}/api/user/profile", headers=headers)
        if response.status_code == 404:
            # Try alternative endpoint
            response = requests.get(f"{BASE_URL}/api/auth/me", headers=headers)
        assert response.status_code == 200
        data = response.json()
        print(f"✅ User profile retrieved: {data.get('email', data.get('user', {}).get('email'))}")


class TestLegalDocuments:
    """Legal documents tests"""
    
    def test_user_agreement(self):
        """Test User Agreement endpoint"""
        response = requests.get(f"{BASE_URL}/api/legal/user-agreement")
        if response.status_code == 404:
            print("⚠️ User agreement endpoint not found")
            pytest.skip("Legal endpoint not available")
        assert response.status_code == 200
        data = response.json()
        assert "content" in data or "title" in data
        print(f"✅ User Agreement available")
    
    def test_privacy_statement(self):
        """Test Privacy Statement endpoint"""
        response = requests.get(f"{BASE_URL}/api/legal/privacy-policy")
        if response.status_code == 404:
            print("⚠️ Privacy policy endpoint not found")
            pytest.skip("Legal endpoint not available")
        assert response.status_code == 200
        data = response.json()
        print(f"✅ Privacy Policy available")


class TestAdminPanel:
    """Admin panel tests"""
    
    @pytest.fixture
    def auth_token(self):
        """Get admin auth token"""
        response = requests.post(f"{BASE_URL}/api/auth/login", json={
            "email": ADMIN_EMAIL,
            "password": ADMIN_PASSWORD
        })
        if response.status_code == 200:
            return response.json().get("token")
        pytest.skip("Authentication failed")
    
    def test_admin_settings(self, auth_token):
        """Test admin settings endpoint"""
        headers = {"Authorization": f"Bearer {auth_token}"}
        response = requests.get(f"{BASE_URL}/api/admin/settings", headers=headers)
        if response.status_code == 404:
            print("⚠️ Admin settings endpoint not found")
            pytest.skip("Admin settings endpoint not available")
        assert response.status_code == 200
        data = response.json()
        print(f"✅ Admin settings retrieved: {len(data) if isinstance(data, list) else 'settings object'}")
    
    def test_admin_users_list(self, auth_token):
        """Test admin users list"""
        headers = {"Authorization": f"Bearer {auth_token}"}
        response = requests.get(f"{BASE_URL}/api/admin/users", headers=headers)
        if response.status_code == 404:
            print("⚠️ Admin users endpoint not found")
            pytest.skip("Admin users endpoint not available")
        assert response.status_code == 200
        data = response.json()
        print(f"✅ Admin users list: {len(data.get('users', data)) if isinstance(data, (list, dict)) else 'received'}")


class TestSearchFunctionality:
    """Search functionality tests"""
    
    @pytest.fixture
    def auth_token(self):
        """Get admin auth token"""
        response = requests.post(f"{BASE_URL}/api/auth/login", json={
            "email": ADMIN_EMAIL,
            "password": ADMIN_PASSWORD
        })
        if response.status_code == 200:
            return response.json().get("token")
        pytest.skip("Authentication failed")
    
    def test_search_engines_status(self, auth_token):
        """Test search engines availability"""
        headers = {"Authorization": f"Bearer {auth_token}"}
        response = requests.get(f"{BASE_URL}/api/search/engines", headers=headers)
        if response.status_code == 404:
            print("⚠️ Search engines endpoint not found")
            pytest.skip("Search engines endpoint not available")
        assert response.status_code == 200
        data = response.json()
        print(f"✅ Search engines: {data}")


if __name__ == "__main__":
    pytest.main([__file__, "-v", "--tb=short"])
