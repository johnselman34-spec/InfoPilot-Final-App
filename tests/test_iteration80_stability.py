"""
InfoPilot Explorer - Iteration 80 Final Stability Check
Comprehensive testing of all core features:
- Authentication (login/logout)
- Categories CRUD
- Search functionality
- AI Features (News, Smart Suggestions, Protocol Recommendations)
- A/B Testing Tracking
- Revenue Dashboard
- Admin Panel
- Marketplace
- Chat functionality
"""
import pytest
import requests
import os
from datetime import datetime

BASE_URL = os.environ.get('REACT_APP_BACKEND_URL', '').rstrip('/')

# Test credentials
ADMIN_EMAIL = "jjspilot24@gmail.com"
ADMIN_PASSWORD = "InfoPilot2024!"
TEST_EMAIL = "testuser@example.com"
TEST_PASSWORD = "password123"


class TestHealthAndBasics:
    """Basic health and connectivity tests"""
    
    def test_health_endpoint(self):
        """Test API health endpoint"""
        response = requests.get(f"{BASE_URL}/api/health")
        assert response.status_code == 200
        data = response.json()
        assert data["status"] == "healthy"
        print(f"✅ Health check passed: {data}")
    
    def test_subscription_info(self):
        """Test public subscription info endpoint"""
        response = requests.get(f"{BASE_URL}/api/subscription-info")
        assert response.status_code == 200
        data = response.json()
        assert "price" in data
        assert "features" in data
        print(f"✅ Subscription info: price=${data['price']}, features={len(data['features'])}")


class TestAuthentication:
    """Authentication flow tests"""
    
    def test_admin_login(self):
        """Test admin user login"""
        response = requests.post(f"{BASE_URL}/api/auth/login", json={
            "email": ADMIN_EMAIL,
            "password": ADMIN_PASSWORD
        })
        assert response.status_code == 200
        data = response.json()
        assert "token" in data
        assert "user" in data
        assert data["user"]["is_admin"] == True
        print(f"✅ Admin login successful: {data['user']['email']}")
        return data["token"]
    
    def test_test_user_login(self):
        """Test regular user login"""
        response = requests.post(f"{BASE_URL}/api/auth/login", json={
            "email": TEST_EMAIL,
            "password": TEST_PASSWORD
        })
        assert response.status_code == 200
        data = response.json()
        assert "token" in data
        assert "user" in data
        print(f"✅ Test user login successful: {data['user']['email']}")
        return data["token"]
    
    def test_invalid_login(self):
        """Test login with invalid credentials"""
        response = requests.post(f"{BASE_URL}/api/auth/login", json={
            "email": "invalid@example.com",
            "password": "wrongpassword"
        })
        assert response.status_code == 401
        print("✅ Invalid login correctly rejected")
    
    def test_get_current_user(self):
        """Test getting current user profile"""
        token = self.test_admin_login()
        response = requests.get(f"{BASE_URL}/api/auth/me", headers={
            "Authorization": f"Bearer {token}"
        })
        assert response.status_code == 200
        data = response.json()
        assert "email" in data
        print(f"✅ Current user retrieved: {data['email']}")


class TestCategories:
    """Categories CRUD tests"""
    
    @pytest.fixture
    def auth_token(self):
        """Get authentication token"""
        response = requests.post(f"{BASE_URL}/api/auth/login", json={
            "email": ADMIN_EMAIL,
            "password": ADMIN_PASSWORD
        })
        return response.json()["token"]
    
    def test_list_categories(self, auth_token):
        """Test listing categories"""
        response = requests.get(f"{BASE_URL}/api/categories", headers={
            "Authorization": f"Bearer {auth_token}"
        })
        assert response.status_code == 200
        data = response.json()
        assert isinstance(data, list)
        print(f"✅ Categories listed: {len(data)} categories found")
    
    def test_create_category(self, auth_token):
        """Test creating a new category"""
        test_category = {
            "name": f"TEST_Category_{datetime.now().timestamp()}",
            "protocol": "(test or testing) & (automation or pytest)+",
            "description": "Test category for iteration 80"
        }
        response = requests.post(f"{BASE_URL}/api/categories", 
            json=test_category,
            headers={"Authorization": f"Bearer {auth_token}"}
        )
        assert response.status_code in [200, 201]
        data = response.json()
        assert "id" in data or "_id" in data
        print(f"✅ Category created: {test_category['name']}")
        return data.get("id") or data.get("_id")
    
    def test_update_category(self, auth_token):
        """Test updating a category"""
        # First create a category
        category_id = self.test_create_category(auth_token)
        
        # Update it
        update_data = {
            "name": f"TEST_Updated_{datetime.now().timestamp()}",
            "protocol": "(updated or modified) & (test)+",
            "description": "Updated test category"
        }
        response = requests.put(f"{BASE_URL}/api/categories/{category_id}",
            json=update_data,
            headers={"Authorization": f"Bearer {auth_token}"}
        )
        assert response.status_code == 200
        print(f"✅ Category updated: {category_id}")


class TestSearch:
    """Search functionality tests"""
    
    @pytest.fixture
    def auth_token(self):
        """Get authentication token"""
        response = requests.post(f"{BASE_URL}/api/auth/login", json={
            "email": ADMIN_EMAIL,
            "password": ADMIN_PASSWORD
        })
        return response.json()["token"]
    
    def test_search_endpoint(self, auth_token):
        """Test POST /api/search"""
        response = requests.post(f"{BASE_URL}/api/search",
            json={"query": "artificial intelligence news"},
            headers={"Authorization": f"Bearer {auth_token}"}
        )
        assert response.status_code == 200
        data = response.json()
        assert "results" in data
        assert "count" in data
        print(f"✅ Search returned {data['count']} results")
    
    def test_search_engines_status(self, auth_token):
        """Test search engines availability"""
        response = requests.get(f"{BASE_URL}/api/search/engines",
            headers={"Authorization": f"Bearer {auth_token}"}
        )
        assert response.status_code == 200
        data = response.json()
        assert "engines" in data
        print(f"✅ Search engines status: {data.get('total_available', 0)} engines available")


class TestAIFeatures:
    """AI-powered features tests"""
    
    @pytest.fixture
    def auth_token(self):
        """Get authentication token"""
        response = requests.post(f"{BASE_URL}/api/auth/login", json={
            "email": ADMIN_EMAIL,
            "password": ADMIN_PASSWORD
        })
        return response.json()["token"]
    
    def test_ai_news_headlines(self):
        """Test GET /api/ai/news - AI News Headlines"""
        response = requests.get(f"{BASE_URL}/api/ai/news")
        assert response.status_code == 200
        data = response.json()
        assert "articles" in data
        assert isinstance(data["articles"], list)
        print(f"✅ AI News: {len(data['articles'])} articles, ai_powered={data.get('ai_powered', False)}")
    
    def test_ai_smart_suggestions(self, auth_token):
        """Test GET /api/ai/smart-suggestions"""
        response = requests.get(f"{BASE_URL}/api/ai/smart-suggestions?query=technology",
            headers={"Authorization": f"Bearer {auth_token}"}
        )
        assert response.status_code == 200
        data = response.json()
        assert "suggestions" in data
        print(f"✅ Smart Suggestions: {len(data['suggestions'])} suggestions, ai_powered={data.get('ai_powered', False)}")
    
    def test_ai_protocol_recommendations(self, auth_token):
        """Test POST /api/ai/protocol-recommendations"""
        response = requests.post(f"{BASE_URL}/api/ai/protocol-recommendations",
            json={"category": "trending"},
            headers={"Authorization": f"Bearer {auth_token}"}
        )
        assert response.status_code == 200
        data = response.json()
        assert "recommendations" in data
        print(f"✅ Protocol Recommendations: {len(data['recommendations'])} recommendations, ai_powered={data.get('ai_powered', False)}")
    
    def test_ai_suggestions(self, auth_token):
        """Test GET /api/ai/suggestions"""
        response = requests.get(f"{BASE_URL}/api/ai/suggestions",
            headers={"Authorization": f"Bearer {auth_token}"}
        )
        assert response.status_code == 200
        data = response.json()
        assert "suggestions" in data
        print(f"✅ AI Suggestions: {len(data['suggestions'])} suggestions")


class TestABTesting:
    """A/B Testing tracking tests"""
    
    @pytest.fixture
    def auth_token(self):
        """Get authentication token"""
        response = requests.post(f"{BASE_URL}/api/auth/login", json={
            "email": ADMIN_EMAIL,
            "password": ADMIN_PASSWORD
        })
        return response.json()["token"]
    
    def test_track_recommendation_view(self, auth_token):
        """Test tracking view action"""
        response = requests.post(f"{BASE_URL}/api/ai/recommendations/track",
            json={"category": "trending", "action": "view", "recommendation_name": "Test Protocol"},
            headers={"Authorization": f"Bearer {auth_token}"}
        )
        assert response.status_code == 200
        data = response.json()
        assert data["success"] == True
        print("✅ A/B Testing: View action tracked")
    
    def test_track_recommendation_copy(self, auth_token):
        """Test tracking copy action"""
        response = requests.post(f"{BASE_URL}/api/ai/recommendations/track",
            json={"category": "trending", "action": "copy", "recommendation_name": "Test Protocol"},
            headers={"Authorization": f"Bearer {auth_token}"}
        )
        assert response.status_code == 200
        data = response.json()
        assert data["success"] == True
        print("✅ A/B Testing: Copy action tracked")
    
    def test_track_recommendation_create(self, auth_token):
        """Test tracking create action"""
        response = requests.post(f"{BASE_URL}/api/ai/recommendations/track",
            json={"category": "gaps", "action": "create", "recommendation_name": "New Protocol"},
            headers={"Authorization": f"Bearer {auth_token}"}
        )
        assert response.status_code == 200
        data = response.json()
        assert data["success"] == True
        print("✅ A/B Testing: Create action tracked")
    
    def test_track_recommendation_purchase(self, auth_token):
        """Test tracking purchase action"""
        response = requests.post(f"{BASE_URL}/api/ai/recommendations/track",
            json={"category": "premium", "action": "purchase", "recommendation_name": "Premium Protocol"},
            headers={"Authorization": f"Bearer {auth_token}"}
        )
        assert response.status_code == 200
        data = response.json()
        assert data["success"] == True
        print("✅ A/B Testing: Purchase action tracked")
    
    def test_recommendation_analytics(self, auth_token):
        """Test getting recommendation analytics (admin only)"""
        response = requests.get(f"{BASE_URL}/api/ai/recommendations/analytics",
            headers={"Authorization": f"Bearer {auth_token}"}
        )
        assert response.status_code == 200
        data = response.json()
        assert "categories" in data
        print(f"✅ A/B Testing Analytics: {len(data['categories'])} categories tracked")


class TestRevenueDashboard:
    """Revenue Dashboard tests"""
    
    @pytest.fixture
    def admin_token(self):
        """Get admin authentication token"""
        response = requests.post(f"{BASE_URL}/api/auth/login", json={
            "email": ADMIN_EMAIL,
            "password": ADMIN_PASSWORD
        })
        return response.json()["token"]
    
    def test_revenue_dashboard_7d(self, admin_token):
        """Test Revenue Dashboard - 7 days"""
        response = requests.get(f"{BASE_URL}/api/admin/revenue-dashboard?days=7",
            headers={"Authorization": f"Bearer {admin_token}"}
        )
        assert response.status_code == 200
        data = response.json()
        assert "summary" in data
        assert "protocol_sales" in data
        assert "subscriptions" in data
        assert "ab_testing" in data
        print(f"✅ Revenue Dashboard (7d): Total revenue=${data['summary']['total_revenue']:.2f}")
    
    def test_revenue_dashboard_30d(self, admin_token):
        """Test Revenue Dashboard - 30 days"""
        response = requests.get(f"{BASE_URL}/api/admin/revenue-dashboard?days=30",
            headers={"Authorization": f"Bearer {admin_token}"}
        )
        assert response.status_code == 200
        data = response.json()
        assert "summary" in data
        print(f"✅ Revenue Dashboard (30d): Total revenue=${data['summary']['total_revenue']:.2f}")
    
    def test_revenue_dashboard_90d(self, admin_token):
        """Test Revenue Dashboard - 90 days"""
        response = requests.get(f"{BASE_URL}/api/admin/revenue-dashboard?days=90",
            headers={"Authorization": f"Bearer {admin_token}"}
        )
        assert response.status_code == 200
        data = response.json()
        assert "summary" in data
        print(f"✅ Revenue Dashboard (90d): Total revenue=${data['summary']['total_revenue']:.2f}")
    
    def test_revenue_dashboard_365d(self, admin_token):
        """Test Revenue Dashboard - 365 days"""
        response = requests.get(f"{BASE_URL}/api/admin/revenue-dashboard?days=365",
            headers={"Authorization": f"Bearer {admin_token}"}
        )
        assert response.status_code == 200
        data = response.json()
        assert "summary" in data
        print(f"✅ Revenue Dashboard (365d): Total revenue=${data['summary']['total_revenue']:.2f}")


class TestMarketplace:
    """Marketplace tests"""
    
    @pytest.fixture
    def auth_token(self):
        """Get authentication token"""
        response = requests.post(f"{BASE_URL}/api/auth/login", json={
            "email": ADMIN_EMAIL,
            "password": ADMIN_PASSWORD
        })
        return response.json()["token"]
    
    def test_browse_marketplace(self, auth_token):
        """Test browsing marketplace protocols"""
        response = requests.get(f"{BASE_URL}/api/marketplace",
            headers={"Authorization": f"Bearer {auth_token}"}
        )
        assert response.status_code == 200
        data = response.json()
        assert "protocols" in data or isinstance(data, list)
        protocols = data.get("protocols", data) if isinstance(data, dict) else data
        print(f"✅ Marketplace: {len(protocols)} protocols available")
    
    def test_marketplace_featured(self, auth_token):
        """Test featured marketplace protocols"""
        response = requests.get(f"{BASE_URL}/api/marketplace/featured",
            headers={"Authorization": f"Bearer {auth_token}"}
        )
        # Featured might return 200 or 404 if no featured protocols
        assert response.status_code in [200, 404]
        if response.status_code == 200:
            data = response.json()
            print(f"✅ Marketplace Featured: {len(data.get('protocols', []))} featured protocols")
        else:
            print("✅ Marketplace Featured: No featured protocols (expected)")


class TestChat:
    """Chat functionality tests"""
    
    @pytest.fixture
    def auth_token(self):
        """Get authentication token"""
        response = requests.post(f"{BASE_URL}/api/auth/login", json={
            "email": ADMIN_EMAIL,
            "password": ADMIN_PASSWORD
        })
        return response.json()["token"]
    
    def test_list_chat_rooms(self, auth_token):
        """Test listing chat rooms"""
        response = requests.get(f"{BASE_URL}/api/chat/rooms",
            headers={"Authorization": f"Bearer {auth_token}"}
        )
        assert response.status_code == 200
        data = response.json()
        assert isinstance(data, list) or "rooms" in data
        rooms = data if isinstance(data, list) else data.get("rooms", [])
        print(f"✅ Chat Rooms: {len(rooms)} rooms found")


class TestAdminFeatures:
    """Admin-specific features tests"""
    
    @pytest.fixture
    def admin_token(self):
        """Get admin authentication token"""
        response = requests.post(f"{BASE_URL}/api/auth/login", json={
            "email": ADMIN_EMAIL,
            "password": ADMIN_PASSWORD
        })
        return response.json()["token"]
    
    def test_admin_settings(self, admin_token):
        """Test getting admin settings"""
        response = requests.get(f"{BASE_URL}/api/admin/settings",
            headers={"Authorization": f"Bearer {admin_token}"}
        )
        assert response.status_code == 200
        data = response.json()
        assert isinstance(data, dict) or isinstance(data, list)
        print(f"✅ Admin Settings: Retrieved successfully")
    
    def test_admin_statistics(self, admin_token):
        """Test getting admin statistics"""
        response = requests.get(f"{BASE_URL}/api/statistics/overview",
            headers={"Authorization": f"Bearer {admin_token}"}
        )
        assert response.status_code == 200
        data = response.json()
        print(f"✅ Admin Statistics: Retrieved successfully")


class TestABTestDashboard:
    """A/B Test Dashboard tests"""
    
    @pytest.fixture
    def admin_token(self):
        """Get admin authentication token"""
        response = requests.post(f"{BASE_URL}/api/auth/login", json={
            "email": ADMIN_EMAIL,
            "password": ADMIN_PASSWORD
        })
        return response.json()["token"]
    
    def test_ab_test_list(self, admin_token):
        """Test listing A/B tests"""
        response = requests.get(f"{BASE_URL}/api/ab-testing/tests",
            headers={"Authorization": f"Bearer {admin_token}"}
        )
        assert response.status_code == 200
        data = response.json()
        print(f"✅ A/B Tests: {len(data.get('tests', []))} tests found")
    
    def test_ab_test_analytics(self, admin_token):
        """Test A/B test analytics"""
        response = requests.get(f"{BASE_URL}/api/ab-testing/analytics",
            headers={"Authorization": f"Bearer {admin_token}"}
        )
        assert response.status_code == 200
        data = response.json()
        print(f"✅ A/B Test Analytics: Retrieved successfully")


if __name__ == "__main__":
    pytest.main([__file__, "-v", "--tb=short"])
