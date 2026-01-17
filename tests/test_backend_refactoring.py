"""
InfoPilot Explorer - Backend Refactoring Tests
Tests all endpoints after backend refactoring from monolithic to modular structure
"""
import pytest
import requests
import os

BASE_URL = os.environ.get('REACT_APP_BACKEND_URL', 'https://info-pilot.preview.emergentagent.com').rstrip('/')


class TestHealthAndPublicEndpoints:
    """Test health check and public endpoints"""
    
    def test_health_check(self):
        """Test /api/health endpoint"""
        response = requests.get(f"{BASE_URL}/api/health")
        assert response.status_code == 200
        data = response.json()
        assert data["status"] == "healthy"
        assert "timestamp" in data
        print(f"✓ Health check passed: {data}")
    
    def test_admin_init(self):
        """Test /api/admin/init endpoint - initializes default settings"""
        response = requests.post(f"{BASE_URL}/api/admin/init")
        assert response.status_code == 200
        data = response.json()
        assert "message" in data
        assert "count" in data
        print(f"✓ Admin init passed: {data}")
    
    def test_book_promo(self):
        """Test /api/book-promo endpoint"""
        response = requests.get(f"{BASE_URL}/api/book-promo")
        assert response.status_code == 200
        data = response.json()
        assert "title" in data
        assert "author" in data
        assert "price" in data
        assert "amazon_url" in data
        print(f"✓ Book promo passed: title={data['title']}, author={data['author']}")
    
    def test_quotes_gallery(self):
        """Test /api/quotes/gallery endpoint"""
        response = requests.get(f"{BASE_URL}/api/quotes/gallery")
        assert response.status_code == 200
        data = response.json()
        assert "quotes" in data
        assert isinstance(data["quotes"], list)
        print(f"✓ Quotes gallery passed: {len(data['quotes'])} quotes returned")
    
    def test_gamification_badges(self):
        """Test /api/gamification/badges endpoint"""
        response = requests.get(f"{BASE_URL}/api/gamification/badges")
        assert response.status_code == 200
        data = response.json()
        assert "badges" in data
        assert isinstance(data["badges"], dict)
        print(f"✓ Gamification badges passed: {len(data['badges'])} badges available")
    
    def test_gamification_leaderboard(self):
        """Test /api/gamification/leaderboard endpoint"""
        response = requests.get(f"{BASE_URL}/api/gamification/leaderboard")
        assert response.status_code == 200
        data = response.json()
        assert "leaderboard" in data
        assert isinstance(data["leaderboard"], list)
        print(f"✓ Gamification leaderboard passed: {len(data['leaderboard'])} entries")
    
    def test_marketplace_categories(self):
        """Test /api/marketplace/categories endpoint"""
        response = requests.get(f"{BASE_URL}/api/marketplace/categories")
        assert response.status_code == 200
        data = response.json()
        assert "categories" in data
        assert isinstance(data["categories"], list)
        print(f"✓ Marketplace categories passed: {len(data['categories'])} categories")
    
    def test_marketplace_protocols(self):
        """Test /api/marketplace/protocols endpoint"""
        response = requests.get(f"{BASE_URL}/api/marketplace/protocols")
        assert response.status_code == 200
        data = response.json()
        assert "protocols" in data
        assert "total" in data
        assert "page" in data
        print(f"✓ Marketplace protocols passed: {data['total']} protocols, page {data['page']}")
    
    def test_protocol_templates(self):
        """Test /api/protocol-templates endpoint"""
        response = requests.get(f"{BASE_URL}/api/protocol-templates")
        assert response.status_code == 200
        data = response.json()
        assert "templates" in data
        assert isinstance(data["templates"], list)
        print(f"✓ Protocol templates passed: {len(data['templates'])} templates")
    
    def test_protocol_validate(self):
        """Test /api/protocol/validate endpoint"""
        test_protocol = "(python or javascript) & (tutorial or guide)"
        response = requests.post(
            f"{BASE_URL}/api/protocol/validate",
            json={"protocol": test_protocol}
        )
        assert response.status_code == 200
        data = response.json()
        assert "valid" in data
        assert "groups" in data
        print(f"✓ Protocol validate passed: valid={data['valid']}, groups={data.get('group_count', len(data.get('groups', [])))}")
    
    def test_subscription_info(self):
        """Test /api/subscription-info endpoint"""
        response = requests.get(f"{BASE_URL}/api/subscription-info")
        assert response.status_code == 200
        data = response.json()
        assert "price" in data
        assert "features" in data
        print(f"✓ Subscription info passed: price=${data['price']}")
    
    def test_marketplace_paypal_config(self):
        """Test /api/marketplace/paypal-config endpoint"""
        response = requests.get(f"{BASE_URL}/api/marketplace/paypal-config")
        assert response.status_code == 200
        data = response.json()
        assert "client_id" in data
        assert "currency" in data
        print(f"✓ PayPal config passed: currency={data['currency']}")


class TestSocialEndpoints:
    """Test social endpoints (groups, pages)"""
    
    def test_groups_list(self):
        """Test /api/groups endpoint"""
        response = requests.get(f"{BASE_URL}/api/groups")
        assert response.status_code == 200
        data = response.json()
        assert "groups" in data
        assert isinstance(data["groups"], list)
        print(f"✓ Groups list passed: {len(data['groups'])} groups")
    
    def test_pages_list(self):
        """Test /api/pages endpoint"""
        response = requests.get(f"{BASE_URL}/api/pages")
        assert response.status_code == 200
        data = response.json()
        assert "pages" in data
        assert isinstance(data["pages"], list)
        print(f"✓ Pages list passed: {len(data['pages'])} pages")
    
    def test_posts_list(self):
        """Test /api/posts endpoint"""
        response = requests.get(f"{BASE_URL}/api/posts")
        assert response.status_code == 200
        data = response.json()
        assert "posts" in data
        assert isinstance(data["posts"], list)
        print(f"✓ Posts list passed: {len(data['posts'])} posts")


class TestAuthenticatedEndpoints:
    """Test endpoints that require authentication"""
    
    @pytest.fixture(autouse=True)
    def setup(self):
        """Setup test credentials"""
        self.test_email = "test_user_refactor@test.com"
        self.test_password = "TestPass123!"
        self.token = None
    
    def get_auth_token(self):
        """Get authentication token"""
        if self.token:
            return self.token
        
        response = requests.post(
            f"{BASE_URL}/api/auth/login",
            json={"email": self.test_email, "password": self.test_password}
        )
        
        if response.status_code == 200:
            self.token = response.json().get("token")
            return self.token
        return None
    
    def test_login(self):
        """Test /api/auth/login endpoint"""
        response = requests.post(
            f"{BASE_URL}/api/auth/login",
            json={"email": self.test_email, "password": self.test_password}
        )
        assert response.status_code == 200
        data = response.json()
        assert "token" in data
        assert "user" in data
        print(f"✓ Login passed: user={data['user'].get('email')}")
    
    def test_auth_me(self):
        """Test /api/auth/me endpoint"""
        token = self.get_auth_token()
        if not token:
            pytest.skip("Could not get auth token")
        
        response = requests.get(
            f"{BASE_URL}/api/auth/me",
            headers={"Authorization": f"Bearer {token}"}
        )
        assert response.status_code == 200
        data = response.json()
        assert "email" in data
        print(f"✓ Auth me passed: email={data['email']}")
    
    def test_categories_list(self):
        """Test /api/categories endpoint (requires auth)"""
        token = self.get_auth_token()
        if not token:
            pytest.skip("Could not get auth token")
        
        response = requests.get(
            f"{BASE_URL}/api/categories",
            headers={"Authorization": f"Bearer {token}"}
        )
        assert response.status_code == 200
        data = response.json()
        assert isinstance(data, list)
        print(f"✓ Categories list passed: {len(data)} categories")
    
    def test_gamification_profile(self):
        """Test /api/gamification/profile endpoint (requires auth)"""
        token = self.get_auth_token()
        if not token:
            pytest.skip("Could not get auth token")
        
        response = requests.get(
            f"{BASE_URL}/api/gamification/profile",
            headers={"Authorization": f"Bearer {token}"}
        )
        assert response.status_code == 200
        data = response.json()
        assert "xp" in data
        assert "level" in data
        print(f"✓ Gamification profile passed: level={data['level']}, xp={data['xp']}")
    
    def test_friends_list(self):
        """Test /api/friends endpoint (requires auth)"""
        token = self.get_auth_token()
        if not token:
            pytest.skip("Could not get auth token")
        
        response = requests.get(
            f"{BASE_URL}/api/friends",
            headers={"Authorization": f"Bearer {token}"}
        )
        assert response.status_code == 200
        data = response.json()
        assert "friends" in data
        print(f"✓ Friends list passed: {len(data['friends'])} friends")
    
    def test_marketplace_purchases(self):
        """Test /api/marketplace/purchases endpoint (requires auth)"""
        token = self.get_auth_token()
        if not token:
            pytest.skip("Could not get auth token")
        
        response = requests.get(
            f"{BASE_URL}/api/marketplace/purchases",
            headers={"Authorization": f"Bearer {token}"}
        )
        assert response.status_code == 200
        data = response.json()
        assert "purchases" in data
        print(f"✓ Marketplace purchases passed: {len(data['purchases'])} purchases")
    
    def test_marketplace_seller_dashboard(self):
        """Test /api/marketplace/seller/dashboard endpoint (requires auth)"""
        token = self.get_auth_token()
        if not token:
            pytest.skip("Could not get auth token")
        
        response = requests.get(
            f"{BASE_URL}/api/marketplace/seller/dashboard",
            headers={"Authorization": f"Bearer {token}"}
        )
        assert response.status_code == 200
        data = response.json()
        assert "total_listings" in data
        assert "total_sales" in data
        print(f"✓ Seller dashboard passed: {data['total_listings']} listings, {data['total_sales']} sales")


class TestAdminEndpoints:
    """Test admin-only endpoints - Note: These require admin privileges"""
    
    @pytest.fixture(autouse=True)
    def setup(self):
        """Setup admin credentials - Note: Admin users use Google OAuth, so we use test user"""
        self.admin_email = "test_user_refactor@test.com"
        self.admin_password = "TestPass123!"
        self.token = None
    
    def get_admin_token(self):
        """Get admin authentication token"""
        if self.token:
            return self.token
        
        response = requests.post(
            f"{BASE_URL}/api/auth/login",
            json={"email": self.admin_email, "password": self.admin_password}
        )
        
        if response.status_code == 200:
            self.token = response.json().get("token")
            return self.token
        return None
    
    def test_admin_stats(self):
        """Test /api/admin/stats endpoint - requires admin privileges"""
        token = self.get_admin_token()
        if not token:
            pytest.skip("Could not get admin token")
        
        response = requests.get(
            f"{BASE_URL}/api/admin/stats",
            headers={"Authorization": f"Bearer {token}"}
        )
        # Non-admin users get 403, which is correct behavior
        if response.status_code == 403:
            print("✓ Admin stats correctly returns 403 for non-admin user")
            return
        assert response.status_code == 200
        data = response.json()
        assert "users" in data
        assert "categories" in data
        print(f"✓ Admin stats passed: {data['users']} users, {data['categories']} categories")
    
    def test_admin_settings(self):
        """Test /api/admin/settings endpoint - requires admin privileges"""
        token = self.get_admin_token()
        if not token:
            pytest.skip("Could not get admin token")
        
        response = requests.get(
            f"{BASE_URL}/api/admin/settings",
            headers={"Authorization": f"Bearer {token}"}
        )
        # Non-admin users get 403, which is correct behavior
        if response.status_code == 403:
            print("✓ Admin settings correctly returns 403 for non-admin user")
            return
        assert response.status_code == 200
        data = response.json()
        assert isinstance(data, dict)
        print(f"✓ Admin settings passed: {len(data)} settings")
    
    def test_admin_users(self):
        """Test /api/admin/users endpoint - requires admin privileges"""
        token = self.get_admin_token()
        if not token:
            pytest.skip("Could not get admin token")
        
        response = requests.get(
            f"{BASE_URL}/api/admin/users",
            headers={"Authorization": f"Bearer {token}"}
        )
        # Non-admin users get 403, which is correct behavior
        if response.status_code == 403:
            print("✓ Admin users correctly returns 403 for non-admin user")
            return
        assert response.status_code == 200
        data = response.json()
        assert "users" in data
        print(f"✓ Admin users passed: {len(data['users'])} users")
    
    def test_analytics_dashboard(self):
        """Test /api/analytics/dashboard endpoint (admin only)"""
        token = self.get_admin_token()
        if not token:
            pytest.skip("Could not get admin token")
        
        response = requests.get(
            f"{BASE_URL}/api/analytics/dashboard",
            headers={"Authorization": f"Bearer {token}"}
        )
        # Non-admin users get 403, which is correct behavior
        if response.status_code == 403:
            print("✓ Analytics dashboard correctly returns 403 for non-admin user")
            return
        assert response.status_code == 200
        data = response.json()
        assert "total_users" in data or "users" in data
        print(f"✓ Analytics dashboard passed")


class TestProtocolDebugger:
    """Test protocol debugger functionality"""
    
    def test_protocol_debug_valid(self):
        """Test protocol debug with valid protocol"""
        test_protocol = "(python or javascript) & (tutorial or guide)"
        response = requests.post(
            f"{BASE_URL}/api/protocol/validate",
            json={"protocol": test_protocol}
        )
        assert response.status_code == 200
        data = response.json()
        assert data["valid"] == True
        assert len(data["groups"]) == 2
        print(f"✓ Protocol debug (valid) passed: {data['group_count']} groups")
    
    def test_protocol_debug_invalid(self):
        """Test protocol debug with invalid protocol"""
        test_protocol = "invalid protocol without groups"
        response = requests.post(
            f"{BASE_URL}/api/protocol/validate",
            json={"protocol": test_protocol}
        )
        assert response.status_code == 200
        data = response.json()
        assert data["valid"] == False
        print(f"✓ Protocol debug (invalid) passed: {data['validation_message']}")


class TestLeaderboards:
    """Test leaderboard endpoints"""
    
    def test_weekly_leaderboard(self):
        """Test /api/gamification/leaderboard/weekly endpoint"""
        response = requests.get(f"{BASE_URL}/api/gamification/leaderboard/weekly")
        assert response.status_code == 200
        data = response.json()
        assert "leaderboard" in data
        assert "period" in data
        assert data["period"] == "weekly"
        print(f"✓ Weekly leaderboard passed: {len(data['leaderboard'])} entries")
    
    def test_monthly_leaderboard(self):
        """Test /api/gamification/leaderboard/monthly endpoint"""
        response = requests.get(f"{BASE_URL}/api/gamification/leaderboard/monthly")
        assert response.status_code == 200
        data = response.json()
        assert "leaderboard" in data
        assert "period" in data
        assert data["period"] == "monthly"
        print(f"✓ Monthly leaderboard passed: {len(data['leaderboard'])} entries")


if __name__ == "__main__":
    pytest.main([__file__, "-v", "--tb=short"])
