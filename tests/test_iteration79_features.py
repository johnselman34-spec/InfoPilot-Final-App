"""
Iteration 79 - Revenue Dashboard, WebSocket Error Handling, and AI Features Testing
Tests:
- Revenue Dashboard API (GET /api/admin/revenue-dashboard)
- AI News Headlines (GET /api/ai/news)
- Smart Search Suggestions (GET /api/ai/smart-suggestions)
- AI Recommendations Tracking (POST /api/ai/recommendations/track)
- Authentication flow
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


class TestAuthentication:
    """Authentication endpoint tests"""
    
    def test_admin_login_success(self):
        """Test admin login with valid credentials"""
        response = requests.post(f"{BASE_URL}/api/auth/login", json={
            "email": ADMIN_EMAIL,
            "password": ADMIN_PASSWORD
        })
        assert response.status_code == 200, f"Admin login failed: {response.text}"
        data = response.json()
        assert "token" in data, "Token not in response"
        assert "user" in data, "User not in response"
        assert data["user"]["is_admin"] == True, "User should be admin"
        print(f"✅ Admin login successful - token received")
    
    def test_login_invalid_credentials(self):
        """Test login with invalid credentials"""
        response = requests.post(f"{BASE_URL}/api/auth/login", json={
            "email": "invalid@example.com",
            "password": "wrongpassword"
        })
        assert response.status_code in [401, 400], f"Expected 401/400, got {response.status_code}"
        print(f"✅ Invalid login correctly rejected with status {response.status_code}")


class TestRevenueDashboard:
    """Revenue Dashboard API tests"""
    
    @pytest.fixture(autouse=True)
    def setup(self):
        """Get admin token for authenticated requests"""
        response = requests.post(f"{BASE_URL}/api/auth/login", json={
            "email": ADMIN_EMAIL,
            "password": ADMIN_PASSWORD
        })
        if response.status_code == 200:
            self.token = response.json().get("token")
            self.headers = {"Authorization": f"Bearer {self.token}"}
        else:
            pytest.skip("Admin authentication failed")
    
    def test_revenue_dashboard_default_period(self):
        """Test revenue dashboard with default 30 day period"""
        response = requests.get(
            f"{BASE_URL}/api/admin/revenue-dashboard",
            headers=self.headers
        )
        assert response.status_code == 200, f"Revenue dashboard failed: {response.text}"
        data = response.json()
        
        # Verify response structure
        assert "period_days" in data, "Missing period_days"
        assert "generated_at" in data, "Missing generated_at"
        assert "summary" in data, "Missing summary"
        assert "protocol_sales" in data, "Missing protocol_sales"
        assert "subscriptions" in data, "Missing subscriptions"
        assert "ab_testing" in data, "Missing ab_testing"
        assert "ai_recommendations" in data, "Missing ai_recommendations"
        
        # Verify summary structure
        summary = data["summary"]
        assert "total_revenue" in summary, "Missing total_revenue in summary"
        assert "protocol_revenue" in summary, "Missing protocol_revenue in summary"
        assert "subscription_revenue" in summary, "Missing subscription_revenue in summary"
        assert "total_sales" in summary, "Missing total_sales in summary"
        assert "unique_buyers" in summary, "Missing unique_buyers in summary"
        assert "active_subscriptions" in summary, "Missing active_subscriptions in summary"
        assert "new_users" in summary, "Missing new_users in summary"
        assert "total_users" in summary, "Missing total_users in summary"
        assert "active_users" in summary, "Missing active_users in summary"
        
        print(f"✅ Revenue dashboard returned successfully")
        print(f"   Total Revenue: ${summary['total_revenue']}")
        print(f"   Protocol Revenue: ${summary['protocol_revenue']}")
        print(f"   Subscription Revenue: ${summary['subscription_revenue']}")
        print(f"   Total Users: {summary['total_users']}")
    
    def test_revenue_dashboard_7_day_period(self):
        """Test revenue dashboard with 7 day period"""
        response = requests.get(
            f"{BASE_URL}/api/admin/revenue-dashboard?days=7",
            headers=self.headers
        )
        assert response.status_code == 200, f"Revenue dashboard 7d failed: {response.text}"
        data = response.json()
        assert data["period_days"] == 7, "Period should be 7 days"
        print(f"✅ Revenue dashboard 7-day period works correctly")
    
    def test_revenue_dashboard_90_day_period(self):
        """Test revenue dashboard with 90 day period"""
        response = requests.get(
            f"{BASE_URL}/api/admin/revenue-dashboard?days=90",
            headers=self.headers
        )
        assert response.status_code == 200, f"Revenue dashboard 90d failed: {response.text}"
        data = response.json()
        assert data["period_days"] == 90, "Period should be 90 days"
        print(f"✅ Revenue dashboard 90-day period works correctly")
    
    def test_revenue_dashboard_365_day_period(self):
        """Test revenue dashboard with 365 day period"""
        response = requests.get(
            f"{BASE_URL}/api/admin/revenue-dashboard?days=365",
            headers=self.headers
        )
        assert response.status_code == 200, f"Revenue dashboard 365d failed: {response.text}"
        data = response.json()
        assert data["period_days"] == 365, "Period should be 365 days"
        print(f"✅ Revenue dashboard 365-day period works correctly")
    
    def test_revenue_dashboard_protocol_sales_structure(self):
        """Test protocol sales data structure"""
        response = requests.get(
            f"{BASE_URL}/api/admin/revenue-dashboard",
            headers=self.headers
        )
        assert response.status_code == 200
        data = response.json()
        
        protocol_sales = data["protocol_sales"]
        assert "total_revenue" in protocol_sales, "Missing total_revenue in protocol_sales"
        assert "total_sales" in protocol_sales, "Missing total_sales in protocol_sales"
        assert "by_day" in protocol_sales, "Missing by_day in protocol_sales"
        assert "top_sellers" in protocol_sales, "Missing top_sellers in protocol_sales"
        
        # Verify top_sellers structure if any exist
        if protocol_sales["top_sellers"]:
            seller = protocol_sales["top_sellers"][0]
            assert "name" in seller, "Missing name in top seller"
            assert "revenue" in seller, "Missing revenue in top seller"
            assert "sales" in seller, "Missing sales in top seller"
        
        print(f"✅ Protocol sales structure verified")
        print(f"   Top sellers count: {len(protocol_sales['top_sellers'])}")
    
    def test_revenue_dashboard_subscriptions_structure(self):
        """Test subscriptions data structure"""
        response = requests.get(
            f"{BASE_URL}/api/admin/revenue-dashboard",
            headers=self.headers
        )
        assert response.status_code == 200
        data = response.json()
        
        subscriptions = data["subscriptions"]
        assert "total_revenue" in subscriptions, "Missing total_revenue in subscriptions"
        assert "active_count" in subscriptions, "Missing active_count in subscriptions"
        assert "monthly_revenue" in subscriptions, "Missing monthly_revenue in subscriptions"
        assert "yearly_revenue" in subscriptions, "Missing yearly_revenue in subscriptions"
        assert "by_day" in subscriptions, "Missing by_day in subscriptions"
        
        print(f"✅ Subscriptions structure verified")
        print(f"   Active subscriptions: {subscriptions['active_count']}")
    
    def test_revenue_dashboard_requires_admin(self):
        """Test that revenue dashboard requires admin access"""
        # Try without auth
        response = requests.get(f"{BASE_URL}/api/admin/revenue-dashboard")
        assert response.status_code == 401, f"Expected 401 without auth, got {response.status_code}"
        print(f"✅ Revenue dashboard correctly requires authentication")


class TestAINews:
    """AI News Headlines API tests"""
    
    def test_ai_news_endpoint(self):
        """Test AI news headlines endpoint"""
        response = requests.get(f"{BASE_URL}/api/ai/news")
        assert response.status_code == 200, f"AI news failed: {response.text}"
        data = response.json()
        
        assert "articles" in data, "Missing articles in response"
        articles = data["articles"]
        assert len(articles) > 0, "No articles returned"
        
        # Verify article structure
        article = articles[0]
        assert "headline" in article, "Missing headline in article"
        assert "topic" in article, "Missing topic in article"
        
        print(f"✅ AI News returned {len(articles)} articles")
        for i, art in enumerate(articles[:3]):
            print(f"   {i+1}. [{art.get('topic', 'N/A')}] {art.get('headline', 'N/A')[:50]}...")


class TestSmartSearchSuggestions:
    """Smart Search Suggestions API tests"""
    
    @pytest.fixture(autouse=True)
    def setup(self):
        """Get token for authenticated requests"""
        response = requests.post(f"{BASE_URL}/api/auth/login", json={
            "email": ADMIN_EMAIL,
            "password": ADMIN_PASSWORD
        })
        if response.status_code == 200:
            self.token = response.json().get("token")
            self.headers = {"Authorization": f"Bearer {self.token}"}
        else:
            pytest.skip("Authentication failed")
    
    def test_smart_suggestions_endpoint(self):
        """Test smart search suggestions endpoint"""
        response = requests.get(
            f"{BASE_URL}/api/ai/smart-suggestions?query=health",
            headers=self.headers
        )
        assert response.status_code == 200, f"Smart suggestions failed: {response.text}"
        data = response.json()
        
        assert "suggestions" in data, "Missing suggestions in response"
        suggestions = data["suggestions"]
        
        if len(suggestions) > 0:
            suggestion = suggestions[0]
            assert "suggestion" in suggestion, "Missing suggestion field"
            print(f"✅ Smart suggestions returned {len(suggestions)} suggestions")
            for i, sug in enumerate(suggestions[:3]):
                print(f"   {i+1}. {sug.get('suggestion', 'N/A')}")
        else:
            print(f"✅ Smart suggestions endpoint works (no suggestions for query)")
    
    def test_smart_suggestions_different_query(self):
        """Test smart suggestions with different query"""
        response = requests.get(
            f"{BASE_URL}/api/ai/smart-suggestions?query=technology",
            headers=self.headers
        )
        assert response.status_code == 200, f"Smart suggestions failed: {response.text}"
        print(f"✅ Smart suggestions works with different queries")


class TestAIRecommendationsTracking:
    """AI Recommendations Tracking API tests"""
    
    @pytest.fixture(autouse=True)
    def setup(self):
        """Get admin token for authenticated requests"""
        response = requests.post(f"{BASE_URL}/api/auth/login", json={
            "email": ADMIN_EMAIL,
            "password": ADMIN_PASSWORD
        })
        if response.status_code == 200:
            self.token = response.json().get("token")
            self.headers = {"Authorization": f"Bearer {self.token}"}
        else:
            pytest.skip("Admin authentication failed")
    
    def test_track_view_action(self):
        """Test tracking view action"""
        response = requests.post(
            f"{BASE_URL}/api/ai/recommendations/track",
            headers=self.headers,
            json={
                "category": "Test Category",
                "action": "view"
            }
        )
        assert response.status_code == 200, f"Track view failed: {response.text}"
        data = response.json()
        assert data.get("success") == True, "Track view should succeed"
        print(f"✅ Track view action works")
    
    def test_track_copy_action(self):
        """Test tracking copy action"""
        response = requests.post(
            f"{BASE_URL}/api/ai/recommendations/track",
            headers=self.headers,
            json={
                "category": "Test Category",
                "action": "copy"
            }
        )
        assert response.status_code == 200, f"Track copy failed: {response.text}"
        data = response.json()
        assert data.get("success") == True, "Track copy should succeed"
        print(f"✅ Track copy action works")
    
    def test_track_create_action(self):
        """Test tracking create action"""
        response = requests.post(
            f"{BASE_URL}/api/ai/recommendations/track",
            headers=self.headers,
            json={
                "category": "Test Category",
                "action": "create"
            }
        )
        assert response.status_code == 200, f"Track create failed: {response.text}"
        data = response.json()
        assert data.get("success") == True, "Track create should succeed"
        print(f"✅ Track create action works")
    
    def test_track_purchase_action(self):
        """Test tracking purchase action"""
        response = requests.post(
            f"{BASE_URL}/api/ai/recommendations/track",
            headers=self.headers,
            json={
                "category": "Test Category",
                "action": "purchase"
            }
        )
        assert response.status_code == 200, f"Track purchase failed: {response.text}"
        data = response.json()
        assert data.get("success") == True, "Track purchase should succeed"
        print(f"✅ Track purchase action works")
    
    def test_recommendations_analytics(self):
        """Test AI recommendations analytics endpoint"""
        response = requests.get(
            f"{BASE_URL}/api/ai/recommendations/analytics",
            headers=self.headers
        )
        assert response.status_code == 200, f"Analytics failed: {response.text}"
        data = response.json()
        assert "categories" in data, "Missing categories in analytics"
        print(f"✅ AI recommendations analytics works")
        print(f"   Categories tracked: {len(data.get('categories', []))}")


class TestHealthAndBasicEndpoints:
    """Basic health and endpoint tests"""
    
    @pytest.fixture(autouse=True)
    def setup(self):
        """Get token for authenticated requests"""
        response = requests.post(f"{BASE_URL}/api/auth/login", json={
            "email": ADMIN_EMAIL,
            "password": ADMIN_PASSWORD
        })
        if response.status_code == 200:
            self.token = response.json().get("token")
            self.headers = {"Authorization": f"Bearer {self.token}"}
        else:
            pytest.skip("Authentication failed")
    
    def test_health_endpoint(self):
        """Test health endpoint"""
        response = requests.get(f"{BASE_URL}/api/health")
        assert response.status_code == 200, f"Health check failed: {response.text}"
        print(f"✅ Health endpoint works")
    
    def test_categories_endpoint(self):
        """Test categories endpoint"""
        response = requests.get(
            f"{BASE_URL}/api/categories",
            headers=self.headers
        )
        assert response.status_code == 200, f"Categories failed: {response.text}"
        data = response.json()
        # Categories endpoint returns a list directly or wrapped in "categories" key
        if isinstance(data, list):
            categories = data
        else:
            categories = data.get("categories", [])
        print(f"✅ Categories endpoint works - {len(categories)} categories")


if __name__ == "__main__":
    pytest.main([__file__, "-v", "--tb=short"])
