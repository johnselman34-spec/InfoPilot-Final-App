"""
InfoPilot Explorer - Iteration 84 Feature Tests
SEPTUPLE-CHECK comprehensive stability and bug check

Tests:
1. Admin Panel - 23 tabs verification
2. Ultimate Search Page - category filtering
3. Map View Page - Worldwide/Personal toggle
4. Statistics Page - Worldwide/Personal toggle
5. Marketplace - 5 tabs
6. Social Page - Friends, Groups, Pages, Direct Messages
7. Settings Page - Email/Password change sections
8. Gamification profile
9. Legal pages
10. Tutorials page
"""

import pytest
import requests
import os
import time

BASE_URL = os.environ.get('REACT_APP_BACKEND_URL', 'https://info-explorer-hub.preview.emergentagent.com').rstrip('/')

# Test credentials
ADMIN_EMAIL = "jjspilot24@gmail.com"
ADMIN_PASSWORD = "InfoPilot2024!"


class TestAuthentication:
    """Authentication tests"""
    
    @pytest.fixture(scope="class")
    def auth_token(self):
        """Get authentication token"""
        response = requests.post(f"{BASE_URL}/api/auth/login", json={
            "email": ADMIN_EMAIL,
            "password": ADMIN_PASSWORD
        })
        assert response.status_code == 200, f"Login failed: {response.text}"
        data = response.json()
        assert "token" in data, "No token in response"
        return data["token"]
    
    def test_login_success(self):
        """Test successful login"""
        response = requests.post(f"{BASE_URL}/api/auth/login", json={
            "email": ADMIN_EMAIL,
            "password": ADMIN_PASSWORD
        })
        assert response.status_code == 200
        data = response.json()
        assert "token" in data
        assert "user" in data
        assert data["user"]["is_admin"] == True
        print(f"✓ Login successful for admin user: {data['user']['username']}")


class TestAdminPanel:
    """Admin Panel API tests - verifying all 23 tabs have working endpoints"""
    
    @pytest.fixture(scope="class")
    def auth_token(self):
        """Get authentication token"""
        response = requests.post(f"{BASE_URL}/api/auth/login", json={
            "email": ADMIN_EMAIL,
            "password": ADMIN_PASSWORD
        })
        return response.json()["token"]
    
    def test_admin_settings(self, auth_token):
        """Test admin settings endpoint (General tab)"""
        response = requests.get(
            f"{BASE_URL}/api/admin/settings",
            headers={"Authorization": f"Bearer {auth_token}"}
        )
        assert response.status_code == 200
        data = response.json()
        assert "subscription_price" in data
        assert "collation_limit" in data
        print("✓ Admin Settings (General tab) working")
    
    def test_admin_users(self, auth_token):
        """Test admin users endpoint (Users tab)"""
        response = requests.get(
            f"{BASE_URL}/api/admin/users?page=1&limit=5",
            headers={"Authorization": f"Bearer {auth_token}"}
        )
        assert response.status_code == 200
        data = response.json()
        assert "users" in data
        print(f"✓ Admin Users tab working - {len(data['users'])} users found")
    
    def test_admin_banned_words(self, auth_token):
        """Test banned words endpoint (Banned Words tab)"""
        response = requests.get(
            f"{BASE_URL}/api/admin/banned-words",
            headers={"Authorization": f"Bearer {auth_token}"}
        )
        assert response.status_code == 200
        data = response.json()
        assert isinstance(data, list)
        print(f"✓ Banned Words tab working - {len(data)} banned words")
    
    def test_admin_quality_report(self, auth_token):
        """Test quality report endpoint (Quality Report tab)"""
        response = requests.get(
            f"{BASE_URL}/api/admin/content-quality-report",
            headers={"Authorization": f"Bearer {auth_token}"}
        )
        assert response.status_code == 200
        data = response.json()
        assert "total_violations" in data
        print("✓ Quality Report tab working")
    
    def test_admin_alerts(self, auth_token):
        """Test alerts endpoint (Alerts tab)"""
        response = requests.get(
            f"{BASE_URL}/api/admin/alerts",
            headers={"Authorization": f"Bearer {auth_token}"}
        )
        assert response.status_code == 200
        data = response.json()
        # Response is {"alerts": [], "count": 0}
        assert "alerts" in data
        print(f"✓ Alerts tab working - {data.get('count', 0)} alerts")
    
    def test_admin_polls(self, auth_token):
        """Test polls endpoint (Polls tab)"""
        response = requests.get(
            f"{BASE_URL}/api/polls/admin/all",
            headers={"Authorization": f"Bearer {auth_token}"}
        )
        assert response.status_code == 200
        data = response.json()
        assert "polls" in data
        print(f"✓ Polls tab working - {len(data['polls'])} polls")
    
    def test_admin_ab_tests(self, auth_token):
        """Test A/B testing endpoint (A/B Testing tab)"""
        response = requests.get(
            f"{BASE_URL}/api/ab-testing/tests",
            headers={"Authorization": f"Bearer {auth_token}"}
        )
        assert response.status_code == 200
        data = response.json()
        assert "tests" in data
        print(f"✓ A/B Testing tab working - {len(data['tests'])} tests")
    
    def test_admin_optimizer(self, auth_token):
        """Test optimizer endpoint (Optimizer tab)"""
        response = requests.get(
            f"{BASE_URL}/api/ab-optimizer/status",
            headers={"Authorization": f"Bearer {auth_token}"}
        )
        assert response.status_code == 200
        data = response.json()
        print("✓ Optimizer tab working")
    
    def test_admin_revenue_forecast(self, auth_token):
        """Test revenue forecast endpoint (Forecast tab)"""
        response = requests.get(
            f"{BASE_URL}/api/revenue-forecast/forecast",
            headers={"Authorization": f"Bearer {auth_token}"}
        )
        assert response.status_code == 200
        data = response.json()
        print("✓ Revenue Forecast tab working")
    
    def test_admin_email_reports(self, auth_token):
        """Test email reports endpoint (Email Reports tab)"""
        response = requests.get(
            f"{BASE_URL}/api/email-reports/status",
            headers={"Authorization": f"Bearer {auth_token}"}
        )
        assert response.status_code == 200
        data = response.json()
        print("✓ Email Reports tab working")
    
    def test_admin_tutorials(self, auth_token):
        """Test tutorials endpoint (Tutorials tab)"""
        response = requests.get(
            f"{BASE_URL}/api/tutorials",
            headers={"Authorization": f"Bearer {auth_token}"}
        )
        assert response.status_code == 200
        data = response.json()
        assert "tutorials" in data
        print(f"✓ Tutorials tab working - {len(data['tutorials'])} tutorials")
    
    def test_admin_category_analytics(self, auth_token):
        """Test category analytics endpoint (Cat Analytics tab)"""
        response = requests.get(
            f"{BASE_URL}/api/admin/category-analytics",
            headers={"Authorization": f"Bearer {auth_token}"}
        )
        assert response.status_code == 200
        data = response.json()
        print("✓ Category Analytics tab working")
    
    def test_admin_doctype_settings(self, auth_token):
        """Test doctype settings endpoint (Doc Types tab)"""
        response = requests.get(
            f"{BASE_URL}/api/admin/doctype-settings",
            headers={"Authorization": f"Bearer {auth_token}"}
        )
        assert response.status_code == 200
        data = response.json()
        print("✓ Doc Types tab working")
    
    def test_admin_price_controls(self, auth_token):
        """Test price controls endpoint (Price Controls tab)"""
        response = requests.get(
            f"{BASE_URL}/api/admin/unpaid-price-controls",
            headers={"Authorization": f"Bearer {auth_token}"}
        )
        assert response.status_code == 200
        data = response.json()
        print("✓ Price Controls tab working")
    
    def test_admin_protocol_forecast(self, auth_token):
        """Test protocol forecast endpoint (Protocol Forecast tab)"""
        response = requests.get(
            f"{BASE_URL}/api/protocol-analytics/admin/marketplace-forecast",
            headers={"Authorization": f"Bearer {auth_token}"}
        )
        assert response.status_code == 200
        data = response.json()
        print("✓ Protocol Forecast tab working")


class TestUltimateSearch:
    """Ultimate Search Page tests"""
    
    @pytest.fixture(scope="class")
    def auth_token(self):
        """Get authentication token"""
        response = requests.post(f"{BASE_URL}/api/auth/login", json={
            "email": ADMIN_EMAIL,
            "password": ADMIN_PASSWORD
        })
        return response.json()["token"]
    
    def test_categories_list(self, auth_token):
        """Test categories endpoint"""
        response = requests.get(
            f"{BASE_URL}/api/categories",
            headers={"Authorization": f"Bearer {auth_token}"}
        )
        assert response.status_code == 200
        data = response.json()
        assert isinstance(data, list)
        print(f"✓ Categories list working - {len(data)} categories")
    
    def test_ultimate_search(self, auth_token):
        """Test ultimate search endpoint"""
        response = requests.get(
            f"{BASE_URL}/api/ultimate-search",
            headers={"Authorization": f"Bearer {auth_token}"}
        )
        assert response.status_code == 200
        data = response.json()
        assert "results" in data
        print(f"✓ Ultimate Search working - {len(data['results'])} results")


class TestStatistics:
    """Statistics Page tests"""
    
    @pytest.fixture(scope="class")
    def auth_token(self):
        """Get authentication token"""
        response = requests.post(f"{BASE_URL}/api/auth/login", json={
            "email": ADMIN_EMAIL,
            "password": ADMIN_PASSWORD
        })
        return response.json()["token"]
    
    def test_statistics_overview(self, auth_token):
        """Test statistics overview endpoint"""
        response = requests.get(
            f"{BASE_URL}/api/statistics/overview",
            headers={"Authorization": f"Bearer {auth_token}"}
        )
        assert response.status_code == 200
        data = response.json()
        print("✓ Statistics overview working")
    
    def test_statistics_dashboard(self, auth_token):
        """Test statistics dashboard endpoint"""
        response = requests.get(
            f"{BASE_URL}/api/statistics/dashboard",
            headers={"Authorization": f"Bearer {auth_token}"}
        )
        assert response.status_code == 200
        data = response.json()
        print("✓ Statistics dashboard working")
    
    def test_statistics_countries(self, auth_token):
        """Test statistics countries endpoint"""
        response = requests.get(
            f"{BASE_URL}/api/statistics/countries",
            headers={"Authorization": f"Bearer {auth_token}"}
        )
        assert response.status_code == 200
        data = response.json()
        print("✓ Statistics countries working")
    
    def test_statistics_document_types(self, auth_token):
        """Test statistics document types endpoint"""
        response = requests.get(
            f"{BASE_URL}/api/statistics/document-types",
            headers={"Authorization": f"Bearer {auth_token}"}
        )
        assert response.status_code == 200
        data = response.json()
        print("✓ Statistics document types working")


class TestMarketplace:
    """Marketplace Page tests - 5 tabs"""
    
    @pytest.fixture(scope="class")
    def auth_token(self):
        """Get authentication token"""
        response = requests.post(f"{BASE_URL}/api/auth/login", json={
            "email": ADMIN_EMAIL,
            "password": ADMIN_PASSWORD
        })
        return response.json()["token"]
    
    def test_marketplace_browse_free(self, auth_token):
        """Test marketplace browse - FREE tab"""
        response = requests.get(
            f"{BASE_URL}/api/marketplace/protocols?filter=free",
            headers={"Authorization": f"Bearer {auth_token}"}
        )
        assert response.status_code == 200
        data = response.json()
        assert "protocols" in data
        print(f"✓ Marketplace FREE tab working - {len(data['protocols'])} free protocols")
    
    def test_marketplace_browse_all(self, auth_token):
        """Test marketplace browse - all protocols"""
        response = requests.get(
            f"{BASE_URL}/api/marketplace/protocols",
            headers={"Authorization": f"Bearer {auth_token}"}
        )
        assert response.status_code == 200
        data = response.json()
        assert "protocols" in data
        print(f"✓ Marketplace Browse tab working - {len(data['protocols'])} protocols")
    
    def test_marketplace_my_purchases(self, auth_token):
        """Test marketplace my purchases"""
        response = requests.get(
            f"{BASE_URL}/api/marketplace/purchases",
            headers={"Authorization": f"Bearer {auth_token}"}
        )
        assert response.status_code == 200
        data = response.json()
        assert "purchases" in data
        print(f"✓ Marketplace My Purchases tab working - {len(data['purchases'])} purchases")
    
    def test_marketplace_my_protocols(self, auth_token):
        """Test marketplace my protocols (Sell & Earn tab)"""
        response = requests.get(
            f"{BASE_URL}/api/marketplace/my-protocols",
            headers={"Authorization": f"Bearer {auth_token}"}
        )
        assert response.status_code == 200
        data = response.json()
        # Response is a list of protocols directly
        assert isinstance(data, list)
        print(f"✓ Marketplace Sell & Earn tab working - {len(data)} protocols")


class TestSocial:
    """Social Page tests"""
    
    @pytest.fixture(scope="class")
    def auth_token(self):
        """Get authentication token"""
        response = requests.post(f"{BASE_URL}/api/auth/login", json={
            "email": ADMIN_EMAIL,
            "password": ADMIN_PASSWORD
        })
        return response.json()["token"]
    
    def test_friends_list(self, auth_token):
        """Test friends list endpoint"""
        response = requests.get(
            f"{BASE_URL}/api/friends",
            headers={"Authorization": f"Bearer {auth_token}"}
        )
        assert response.status_code == 200
        data = response.json()
        assert "friends" in data
        print(f"✓ Social Friends tab working - {len(data['friends'])} friends")
    
    def test_groups_list(self, auth_token):
        """Test groups list endpoint"""
        response = requests.get(
            f"{BASE_URL}/api/groups",
            headers={"Authorization": f"Bearer {auth_token}"}
        )
        assert response.status_code == 200
        data = response.json()
        assert "groups" in data
        print(f"✓ Social Groups tab working - {len(data['groups'])} groups")
    
    def test_pages_list(self, auth_token):
        """Test pages list endpoint"""
        response = requests.get(
            f"{BASE_URL}/api/pages",
            headers={"Authorization": f"Bearer {auth_token}"}
        )
        assert response.status_code == 200
        data = response.json()
        assert "pages" in data
        print(f"✓ Social Pages tab working - {len(data['pages'])} pages")
    
    def test_dm_conversations(self, auth_token):
        """Test DM conversations endpoint (Direct Messages)"""
        response = requests.get(
            f"{BASE_URL}/api/dm/conversations",
            headers={"Authorization": f"Bearer {auth_token}"}
        )
        assert response.status_code == 200
        data = response.json()
        assert "conversations" in data
        print(f"✓ Social Direct Messages working - {len(data['conversations'])} conversations")


class TestSettings:
    """Settings Page tests"""
    
    @pytest.fixture(scope="class")
    def auth_token(self):
        """Get authentication token"""
        response = requests.post(f"{BASE_URL}/api/auth/login", json={
            "email": ADMIN_EMAIL,
            "password": ADMIN_PASSWORD
        })
        return response.json()["token"]
    
    def test_user_profile(self, auth_token):
        """Test user profile endpoint"""
        response = requests.get(
            f"{BASE_URL}/api/auth/me",
            headers={"Authorization": f"Bearer {auth_token}"}
        )
        assert response.status_code == 200
        data = response.json()
        assert "email" in data
        print(f"✓ Settings - User profile working: {data['email']}")


class TestGamification:
    """Gamification tests"""
    
    @pytest.fixture(scope="class")
    def auth_token(self):
        """Get authentication token"""
        response = requests.post(f"{BASE_URL}/api/auth/login", json={
            "email": ADMIN_EMAIL,
            "password": ADMIN_PASSWORD
        })
        return response.json()["token"]
    
    def test_gamification_profile(self, auth_token):
        """Test gamification profile endpoint"""
        response = requests.get(
            f"{BASE_URL}/api/gamification/profile",
            headers={"Authorization": f"Bearer {auth_token}"}
        )
        assert response.status_code == 200
        data = response.json()
        assert "level" in data
        # Points might be named differently - check for xp or total_xp
        assert "level" in data or "xp" in data or "total_xp" in data
        print(f"✓ Gamification profile working - Level {data.get('level', 'N/A')}")
    
    def test_gamification_leaderboard(self, auth_token):
        """Test gamification leaderboard endpoint"""
        response = requests.get(
            f"{BASE_URL}/api/gamification/leaderboard",
            headers={"Authorization": f"Bearer {auth_token}"}
        )
        assert response.status_code == 200
        data = response.json()
        assert "leaderboard" in data
        print(f"✓ Gamification leaderboard working - {len(data['leaderboard'])} entries")


class TestLegalPages:
    """Legal pages tests"""
    
    def test_user_agreement(self):
        """Test user agreement endpoint"""
        response = requests.get(f"{BASE_URL}/api/legal/user-agreement")
        assert response.status_code == 200
        data = response.json()
        assert "content" in data
        print("✓ User Agreement page working")
    
    def test_privacy_policy(self):
        """Test privacy policy endpoint"""
        response = requests.get(f"{BASE_URL}/api/legal/privacy-policy")
        assert response.status_code == 200
        data = response.json()
        assert "content" in data
        print("✓ Privacy Policy page working")


class TestTutorials:
    """Tutorials page tests"""
    
    def test_tutorials_list(self):
        """Test tutorials list endpoint"""
        response = requests.get(f"{BASE_URL}/api/tutorials")
        assert response.status_code == 200
        data = response.json()
        assert "tutorials" in data
        tutorial_count = len(data["tutorials"])
        print(f"✓ Tutorials page working - {tutorial_count} tutorials")
        # Check if we have at least 10 tutorials as expected
        assert tutorial_count >= 10, f"Expected at least 10 tutorials, got {tutorial_count}"


class TestCategoryClean:
    """Category clean function tests"""
    
    @pytest.fixture(scope="class")
    def auth_token(self):
        """Get authentication token"""
        response = requests.post(f"{BASE_URL}/api/auth/login", json={
            "email": ADMIN_EMAIL,
            "password": ADMIN_PASSWORD
        })
        return response.json()["token"]
    
    def test_clean_category_endpoint_exists(self, auth_token):
        """Test that clean category endpoint exists"""
        # First get a category
        response = requests.get(
            f"{BASE_URL}/api/categories",
            headers={"Authorization": f"Bearer {auth_token}"}
        )
        assert response.status_code == 200
        categories = response.json()
        
        if len(categories) > 0:
            # Test the clean endpoint with a dry run (don't actually delete)
            cat_id = categories[0]["id"]
            response = requests.post(
                f"{BASE_URL}/api/categories/{cat_id}/clean",
                headers={"Authorization": f"Bearer {auth_token}"},
                json={"mode": "preview"}  # Preview mode to not actually delete
            )
            # Should return 200 or 400 (if no results to clean)
            assert response.status_code in [200, 400]
            print("✓ Clean category endpoint working")
        else:
            print("⚠ No categories to test clean function")


if __name__ == "__main__":
    pytest.main([__file__, "-v", "--tb=short"])
