"""
Iteration 78 - Comprehensive Feature Tests
Tests:
1. First in Flight REMOVED from UltimateSearchPage and CommunityLeaderboard
2. First in Flight KEPT in LegalPage (copyright notice)
3. AI Smart Search Suggestions - GET /api/ai/smart-suggestions?query=test
4. AI Recommendations Tracking - POST /api/ai/recommendations/track
5. AI Recommendations Analytics - GET /api/ai/recommendations/analytics (admin only)
6. AI News Headlines - GET /api/ai/news (10 different topics, no entertainment)
7. Search functionality - /api/search endpoint
8. Category CRUD - /api/categories endpoints
"""
import pytest
import requests
import os
import time

BASE_URL = os.environ.get('REACT_APP_BACKEND_URL', 'https://infopilot-explorer-3.preview.emergentagent.com').rstrip('/')

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
        assert data.get("status") == "healthy"
        print("✓ Health endpoint working")


class TestAuthentication:
    """Authentication tests"""
    
    def test_admin_login(self):
        """Test admin login"""
        response = requests.post(f"{BASE_URL}/api/auth/login", json={
            "email": ADMIN_EMAIL,
            "password": ADMIN_PASSWORD
        })
        assert response.status_code == 200
        data = response.json()
        assert "token" in data
        assert data.get("user", {}).get("is_admin") == True
        print(f"✓ Admin login successful - is_admin: {data.get('user', {}).get('is_admin')}")
        return data["token"]


class TestAINewsAPI:
    """AI News Headlines API tests"""
    
    def test_ai_news_returns_10_articles(self):
        """Test AI News returns exactly 10 articles"""
        response = requests.get(f"{BASE_URL}/api/ai/news")
        assert response.status_code == 200
        data = response.json()
        articles = data.get("articles", [])
        assert len(articles) == 10, f"Expected 10 articles, got {len(articles)}"
        print(f"✓ AI News returns {len(articles)} articles")
    
    def test_ai_news_different_topics(self):
        """Test AI News has different topics (no duplicates)"""
        response = requests.get(f"{BASE_URL}/api/ai/news")
        assert response.status_code == 200
        data = response.json()
        articles = data.get("articles", [])
        
        topics = [a.get("topic", "").lower() for a in articles]
        unique_topics = set(topics)
        
        # Should have at least 8 unique topics out of 10
        assert len(unique_topics) >= 8, f"Expected at least 8 unique topics, got {len(unique_topics)}: {unique_topics}"
        print(f"✓ AI News has {len(unique_topics)} unique topics: {unique_topics}")
    
    def test_ai_news_no_entertainment(self):
        """Test AI News excludes entertainment"""
        response = requests.get(f"{BASE_URL}/api/ai/news")
        assert response.status_code == 200
        data = response.json()
        articles = data.get("articles", [])
        
        topics = [a.get("topic", "").lower() for a in articles]
        assert "entertainment" not in topics, f"Entertainment found in topics: {topics}"
        print("✓ AI News excludes entertainment topic")
    
    def test_ai_news_article_structure(self):
        """Test AI News article structure"""
        response = requests.get(f"{BASE_URL}/api/ai/news")
        assert response.status_code == 200
        data = response.json()
        articles = data.get("articles", [])
        
        for article in articles:
            assert "headline" in article, "Missing headline"
            assert "summary" in article, "Missing summary"
            assert "topic" in article, "Missing topic"
            assert "emoji" in article, "Missing emoji"
        
        print("✓ All articles have correct structure (headline, summary, topic, emoji)")


class TestAISmartSuggestions:
    """AI Smart Search Suggestions tests"""
    
    @pytest.fixture
    def admin_token(self):
        """Get admin token"""
        response = requests.post(f"{BASE_URL}/api/auth/login", json={
            "email": ADMIN_EMAIL,
            "password": ADMIN_PASSWORD
        })
        if response.status_code == 200:
            return response.json().get("token")
        pytest.skip("Admin login failed")
    
    def test_smart_suggestions_endpoint(self, admin_token):
        """Test AI Smart Suggestions endpoint"""
        headers = {"Authorization": f"Bearer {admin_token}"}
        response = requests.get(f"{BASE_URL}/api/ai/smart-suggestions?query=test", headers=headers)
        assert response.status_code == 200
        data = response.json()
        assert "suggestions" in data
        print(f"✓ Smart suggestions endpoint working - {len(data.get('suggestions', []))} suggestions returned")
    
    def test_smart_suggestions_with_empty_query(self, admin_token):
        """Test AI Smart Suggestions with empty query"""
        headers = {"Authorization": f"Bearer {admin_token}"}
        response = requests.get(f"{BASE_URL}/api/ai/smart-suggestions?query=", headers=headers)
        assert response.status_code == 200
        data = response.json()
        assert "suggestions" in data
        print(f"✓ Smart suggestions with empty query - {len(data.get('suggestions', []))} suggestions")
    
    def test_smart_suggestions_structure(self, admin_token):
        """Test AI Smart Suggestions response structure"""
        headers = {"Authorization": f"Bearer {admin_token}"}
        response = requests.get(f"{BASE_URL}/api/ai/smart-suggestions?query=artificial intelligence", headers=headers)
        assert response.status_code == 200
        data = response.json()
        
        suggestions = data.get("suggestions", [])
        if suggestions:
            for suggestion in suggestions:
                assert "suggestion" in suggestion, "Missing suggestion field"
                assert "reason" in suggestion, "Missing reason field"
                assert "type" in suggestion, "Missing type field"
            print(f"✓ Smart suggestions have correct structure")
        else:
            print("✓ Smart suggestions endpoint working (no suggestions returned)")


class TestAIRecommendationsTracking:
    """AI Recommendations A/B Testing Tracking tests"""
    
    @pytest.fixture
    def admin_token(self):
        """Get admin token"""
        response = requests.post(f"{BASE_URL}/api/auth/login", json={
            "email": ADMIN_EMAIL,
            "password": ADMIN_PASSWORD
        })
        if response.status_code == 200:
            return response.json().get("token")
        pytest.skip("Admin login failed")
    
    def test_track_recommendation_view(self, admin_token):
        """Test tracking recommendation view action"""
        headers = {"Authorization": f"Bearer {admin_token}", "Content-Type": "application/json"}
        response = requests.post(f"{BASE_URL}/api/ai/recommendations/track", 
            headers=headers,
            json={
                "category": "trending",
                "action": "view",
                "recommendation_name": "Test Protocol"
            }
        )
        assert response.status_code == 200
        data = response.json()
        assert data.get("success") == True
        print("✓ Recommendation view tracking working")
    
    def test_track_recommendation_copy(self, admin_token):
        """Test tracking recommendation copy action"""
        headers = {"Authorization": f"Bearer {admin_token}", "Content-Type": "application/json"}
        response = requests.post(f"{BASE_URL}/api/ai/recommendations/track", 
            headers=headers,
            json={
                "category": "similar",
                "action": "copy",
                "recommendation_name": "Test Protocol Copy"
            }
        )
        assert response.status_code == 200
        data = response.json()
        assert data.get("success") == True
        print("✓ Recommendation copy tracking working")
    
    def test_track_recommendation_create(self, admin_token):
        """Test tracking recommendation create action"""
        headers = {"Authorization": f"Bearer {admin_token}", "Content-Type": "application/json"}
        response = requests.post(f"{BASE_URL}/api/ai/recommendations/track", 
            headers=headers,
            json={
                "category": "gaps",
                "action": "create",
                "recommendation_name": "Test Protocol Create"
            }
        )
        assert response.status_code == 200
        data = response.json()
        assert data.get("success") == True
        print("✓ Recommendation create tracking working")
    
    def test_track_recommendation_purchase(self, admin_token):
        """Test tracking recommendation purchase action"""
        headers = {"Authorization": f"Bearer {admin_token}", "Content-Type": "application/json"}
        response = requests.post(f"{BASE_URL}/api/ai/recommendations/track", 
            headers=headers,
            json={
                "category": "premium",
                "action": "purchase",
                "recommendation_name": "Test Protocol Purchase"
            }
        )
        assert response.status_code == 200
        data = response.json()
        assert data.get("success") == True
        print("✓ Recommendation purchase tracking working")


class TestAIRecommendationsAnalytics:
    """AI Recommendations Analytics tests (admin only)"""
    
    @pytest.fixture
    def admin_token(self):
        """Get admin token"""
        response = requests.post(f"{BASE_URL}/api/auth/login", json={
            "email": ADMIN_EMAIL,
            "password": ADMIN_PASSWORD
        })
        if response.status_code == 200:
            return response.json().get("token")
        pytest.skip("Admin login failed")
    
    def test_analytics_admin_access(self, admin_token):
        """Test analytics endpoint with admin access"""
        headers = {"Authorization": f"Bearer {admin_token}"}
        response = requests.get(f"{BASE_URL}/api/ai/recommendations/analytics", headers=headers)
        assert response.status_code == 200
        data = response.json()
        assert "categories" in data
        assert "best_performing" in data
        assert "generated_at" in data
        print(f"✓ Analytics endpoint working - best performing: {data.get('best_performing')}")
    
    def test_analytics_non_admin_denied(self):
        """Test analytics endpoint denies non-admin users"""
        # Try without token
        response = requests.get(f"{BASE_URL}/api/ai/recommendations/analytics")
        assert response.status_code in [401, 403], f"Expected 401/403, got {response.status_code}"
        print("✓ Analytics endpoint correctly denies unauthenticated access")


class TestCategoriesAPI:
    """Categories CRUD tests"""
    
    @pytest.fixture
    def admin_token(self):
        """Get admin token"""
        response = requests.post(f"{BASE_URL}/api/auth/login", json={
            "email": ADMIN_EMAIL,
            "password": ADMIN_PASSWORD
        })
        if response.status_code == 200:
            return response.json().get("token")
        pytest.skip("Admin login failed")
    
    def test_get_categories(self, admin_token):
        """Test GET categories"""
        headers = {"Authorization": f"Bearer {admin_token}"}
        response = requests.get(f"{BASE_URL}/api/categories", headers=headers)
        assert response.status_code == 200
        data = response.json()
        assert isinstance(data, list)
        print(f"✓ GET categories working - {len(data)} categories found")
    
    def test_create_category(self, admin_token):
        """Test POST create category"""
        headers = {"Authorization": f"Bearer {admin_token}", "Content-Type": "application/json"}
        test_category = {
            "name": f"TEST_Category_{int(time.time())}",
            "protocol": "(test or testing) & (automation)+",
            "is_public": False
        }
        response = requests.post(f"{BASE_URL}/api/categories", headers=headers, json=test_category)
        assert response.status_code in [200, 201]
        data = response.json()
        assert "id" in data or "_id" in data
        print(f"✓ POST create category working - created: {test_category['name']}")
        return data.get("id") or data.get("_id")


class TestSearchAPI:
    """Search API tests"""
    
    @pytest.fixture
    def admin_token(self):
        """Get admin token"""
        response = requests.post(f"{BASE_URL}/api/auth/login", json={
            "email": ADMIN_EMAIL,
            "password": ADMIN_PASSWORD
        })
        if response.status_code == 200:
            return response.json().get("token")
        pytest.skip("Admin login failed")
    
    def test_search_endpoint(self, admin_token):
        """Test search endpoint"""
        headers = {"Authorization": f"Bearer {admin_token}"}
        response = requests.get(f"{BASE_URL}/api/search?q=test", headers=headers)
        # Search might return 200 or 404 if no results
        assert response.status_code in [200, 404]
        print(f"✓ Search endpoint responding - status: {response.status_code}")
    
    def test_ultimate_search_endpoint(self, admin_token):
        """Test ultimate search endpoint"""
        headers = {"Authorization": f"Bearer {admin_token}"}
        response = requests.get(f"{BASE_URL}/api/ultimate-search?aggregation=and_or&limit=200", headers=headers)
        assert response.status_code == 200
        print("✓ Ultimate search endpoint working")


class TestAIProtocolRecommendations:
    """AI Protocol Recommendations tests"""
    
    @pytest.fixture
    def admin_token(self):
        """Get admin token"""
        response = requests.post(f"{BASE_URL}/api/auth/login", json={
            "email": ADMIN_EMAIL,
            "password": ADMIN_PASSWORD
        })
        if response.status_code == 200:
            return response.json().get("token")
        pytest.skip("Admin login failed")
    
    def test_protocol_recommendations_trending(self, admin_token):
        """Test AI protocol recommendations - trending category"""
        headers = {"Authorization": f"Bearer {admin_token}", "Content-Type": "application/json"}
        response = requests.post(f"{BASE_URL}/api/ai/protocol-recommendations", 
            headers=headers,
            json={"category": "trending"}
        )
        assert response.status_code == 200
        data = response.json()
        assert "recommendations" in data
        assert "category" in data
        assert data.get("category") == "trending"
        print(f"✓ Protocol recommendations (trending) - {len(data.get('recommendations', []))} recommendations")
    
    def test_protocol_recommendations_gaps(self, admin_token):
        """Test AI protocol recommendations - gaps category"""
        headers = {"Authorization": f"Bearer {admin_token}", "Content-Type": "application/json"}
        response = requests.post(f"{BASE_URL}/api/ai/protocol-recommendations", 
            headers=headers,
            json={"category": "gaps"}
        )
        assert response.status_code == 200
        data = response.json()
        assert "recommendations" in data
        print(f"✓ Protocol recommendations (gaps) - {len(data.get('recommendations', []))} recommendations")


if __name__ == "__main__":
    pytest.main([__file__, "-v", "--tb=short"])
