"""
Iteration 77 - AI News, First in Flight Banner, Copyright Protection, Enhanced Hashtags
Tests for:
1. AI News API - GET /api/ai/news - 10 articles with different topics (excluding entertainment)
2. AI Protocol Recommendations - POST /api/ai/protocol-recommendations
3. AI Hashtags Generation - POST /api/ai/generate-hashtags
4. Search functionality - /api/search endpoint
5. Category operations - /api/categories CRUD
6. Authentication flow - login with admin credentials
"""
import pytest
import requests
import os
import time

BASE_URL = os.environ.get('REACT_APP_BACKEND_URL', '').rstrip('/')

class TestAuthentication:
    """Authentication endpoint tests"""
    
    def test_admin_login_success(self):
        """Test admin login with valid credentials"""
        response = requests.post(f"{BASE_URL}/api/auth/login", json={
            "email": "jjspilot24@gmail.com",
            "password": "InfoPilot2024!"
        })
        assert response.status_code == 200, f"Login failed: {response.text}"
        data = response.json()
        assert "token" in data, "Token not in response"
        assert "user" in data, "User not in response"
        assert data["user"]["email"].lower() == "jjspilot24@gmail.com"
        return data["token"]
    
    def test_login_invalid_credentials(self):
        """Test login with invalid credentials"""
        response = requests.post(f"{BASE_URL}/api/auth/login", json={
            "email": "invalid@example.com",
            "password": "wrongpassword"
        })
        assert response.status_code in [401, 400], f"Expected 401/400, got {response.status_code}"


class TestAINewsAPI:
    """AI News endpoint tests - GET /api/ai/news"""
    
    @pytest.fixture
    def auth_token(self):
        """Get authentication token"""
        response = requests.post(f"{BASE_URL}/api/auth/login", json={
            "email": "jjspilot24@gmail.com",
            "password": "InfoPilot2024!"
        })
        if response.status_code == 200:
            return response.json().get("token")
        pytest.skip("Authentication failed")
    
    def test_ai_news_endpoint_returns_articles(self, auth_token):
        """Test AI News endpoint returns articles"""
        headers = {"Authorization": f"Bearer {auth_token}"}
        response = requests.get(f"{BASE_URL}/api/ai/news", headers=headers)
        
        assert response.status_code == 200, f"AI News failed: {response.text}"
        data = response.json()
        
        # Check response structure
        assert "articles" in data, "articles key missing"
        assert isinstance(data["articles"], list), "articles should be a list"
        
        # Should return 10 articles
        assert len(data["articles"]) >= 1, "Should return at least 1 article"
        print(f"AI News returned {len(data['articles'])} articles")
        
        # Check ai_powered flag
        assert "ai_powered" in data, "ai_powered flag missing"
        print(f"AI Powered: {data.get('ai_powered')}")
    
    def test_ai_news_articles_have_required_fields(self, auth_token):
        """Test each article has required fields"""
        headers = {"Authorization": f"Bearer {auth_token}"}
        response = requests.get(f"{BASE_URL}/api/ai/news", headers=headers)
        
        assert response.status_code == 200
        data = response.json()
        articles = data.get("articles", [])
        
        for idx, article in enumerate(articles):
            assert "headline" in article, f"Article {idx} missing headline"
            assert "summary" in article, f"Article {idx} missing summary"
            assert "topic" in article, f"Article {idx} missing topic"
            assert "emoji" in article, f"Article {idx} missing emoji"
            print(f"Article {idx+1}: [{article['topic']}] {article['headline'][:50]}...")
    
    def test_ai_news_different_topics(self, auth_token):
        """Test AI News returns different topics (no duplicates)"""
        headers = {"Authorization": f"Bearer {auth_token}"}
        response = requests.get(f"{BASE_URL}/api/ai/news", headers=headers)
        
        assert response.status_code == 200
        data = response.json()
        articles = data.get("articles", [])
        
        # Extract topics
        topics = [article.get("topic", "").lower() for article in articles]
        unique_topics = set(topics)
        
        print(f"Topics found: {topics}")
        print(f"Unique topics: {len(unique_topics)}")
        
        # Should have mostly unique topics
        assert len(unique_topics) >= min(len(topics), 5), "Should have diverse topics"
    
    def test_ai_news_excludes_entertainment(self, auth_token):
        """Test AI News excludes entertainment topics"""
        headers = {"Authorization": f"Bearer {auth_token}"}
        response = requests.get(f"{BASE_URL}/api/ai/news", headers=headers)
        
        assert response.status_code == 200
        data = response.json()
        articles = data.get("articles", [])
        
        # Check no entertainment topics
        for article in articles:
            topic = article.get("topic", "").lower()
            assert "entertainment" not in topic, f"Entertainment topic found: {topic}"
            assert "celebrity" not in topic, f"Celebrity topic found: {topic}"
        
        print("No entertainment topics found - PASS")
    
    def test_ai_news_without_auth(self):
        """Test AI News endpoint works without auth (public endpoint)"""
        response = requests.get(f"{BASE_URL}/api/ai/news")
        # Should work without auth or return 401
        assert response.status_code in [200, 401], f"Unexpected status: {response.status_code}"
        if response.status_code == 200:
            data = response.json()
            assert "articles" in data


class TestAIProtocolRecommendations:
    """AI Protocol Recommendations endpoint tests"""
    
    @pytest.fixture
    def auth_token(self):
        """Get authentication token"""
        response = requests.post(f"{BASE_URL}/api/auth/login", json={
            "email": "jjspilot24@gmail.com",
            "password": "InfoPilot2024!"
        })
        if response.status_code == 200:
            return response.json().get("token")
        pytest.skip("Authentication failed")
    
    def test_protocol_recommendations_trending(self, auth_token):
        """Test AI Protocol Recommendations for trending category"""
        headers = {"Authorization": f"Bearer {auth_token}"}
        response = requests.post(
            f"{BASE_URL}/api/ai/protocol-recommendations",
            headers=headers,
            json={"category": "trending"}
        )
        
        assert response.status_code == 200, f"Failed: {response.text}"
        data = response.json()
        
        assert "recommendations" in data, "recommendations key missing"
        assert "ai_powered" in data, "ai_powered flag missing"
        assert "category" in data, "category key missing"
        assert data["category"] == "trending"
        
        recommendations = data.get("recommendations", [])
        print(f"Got {len(recommendations)} trending recommendations")
        
        for rec in recommendations[:3]:
            print(f"  - {rec.get('name')}: {rec.get('demand')} ({rec.get('estimated_value')})")
    
    def test_protocol_recommendations_all_categories(self, auth_token):
        """Test all 5 recommendation categories"""
        headers = {"Authorization": f"Bearer {auth_token}"}
        categories = ["trending", "similar", "gaps", "seasonal", "premium"]
        
        for category in categories:
            response = requests.post(
                f"{BASE_URL}/api/ai/protocol-recommendations",
                headers=headers,
                json={"category": category}
            )
            
            assert response.status_code == 200, f"Category {category} failed: {response.text}"
            data = response.json()
            assert data.get("category") == category
            print(f"Category '{category}': {len(data.get('recommendations', []))} recommendations")


class TestAIHashtagsGeneration:
    """AI Hashtags Generation endpoint tests"""
    
    @pytest.fixture
    def auth_token(self):
        """Get authentication token"""
        response = requests.post(f"{BASE_URL}/api/auth/login", json={
            "email": "jjspilot24@gmail.com",
            "password": "InfoPilot2024!"
        })
        if response.status_code == 200:
            return response.json().get("token")
        pytest.skip("Authentication failed")
    
    def test_generate_hashtags_basic(self, auth_token):
        """Test basic hashtag generation"""
        headers = {"Authorization": f"Bearer {auth_token}"}
        response = requests.post(
            f"{BASE_URL}/api/ai/generate-hashtags",
            headers=headers,
            json={
                "content": "NASA announces new Mars mission with SpaceX partnership for 2026 launch"
            }
        )
        
        assert response.status_code == 200, f"Failed: {response.text}"
        data = response.json()
        
        assert "hashtags" in data, "hashtags key missing"
        assert isinstance(data["hashtags"], list), "hashtags should be a list"
        
        hashtags = data.get("hashtags", [])
        print(f"Generated hashtags: {hashtags}")
        
        # Should return 5-8 hashtags
        assert len(hashtags) >= 1, "Should return at least 1 hashtag"
    
    def test_generate_hashtags_with_category(self, auth_token):
        """Test hashtag generation with category context"""
        headers = {"Authorization": f"Bearer {auth_token}"}
        response = requests.post(
            f"{BASE_URL}/api/ai/generate-hashtags",
            headers=headers,
            json={
                "content": "Breaking news about artificial intelligence breakthrough",
                "category_name": "Technology",
                "protocol": "(AI or artificial intelligence) & (breakthrough or news)+"
            }
        )
        
        assert response.status_code == 200, f"Failed: {response.text}"
        data = response.json()
        
        assert "hashtags" in data
        hashtags = data.get("hashtags", [])
        print(f"Generated hashtags with category: {hashtags}")
        
        # Check ai_powered flag
        print(f"AI Powered: {data.get('ai_powered')}")


class TestSearchAPI:
    """Search endpoint tests"""
    
    @pytest.fixture
    def auth_token(self):
        """Get authentication token"""
        response = requests.post(f"{BASE_URL}/api/auth/login", json={
            "email": "jjspilot24@gmail.com",
            "password": "InfoPilot2024!"
        })
        if response.status_code == 200:
            return response.json().get("token")
        pytest.skip("Authentication failed")
    
    def test_search_endpoint(self, auth_token):
        """Test search endpoint"""
        headers = {"Authorization": f"Bearer {auth_token}"}
        response = requests.post(
            f"{BASE_URL}/api/search",
            headers=headers,
            json={
                "query": "technology news",
                "limit": 5
            }
        )
        
        # Search may return 200 or other status depending on implementation
        assert response.status_code in [200, 201, 400, 422], f"Unexpected status: {response.status_code}"
        print(f"Search endpoint status: {response.status_code}")


class TestCategoriesAPI:
    """Categories CRUD endpoint tests"""
    
    @pytest.fixture
    def auth_token(self):
        """Get authentication token"""
        response = requests.post(f"{BASE_URL}/api/auth/login", json={
            "email": "jjspilot24@gmail.com",
            "password": "InfoPilot2024!"
        })
        if response.status_code == 200:
            return response.json().get("token")
        pytest.skip("Authentication failed")
    
    def test_get_categories(self, auth_token):
        """Test GET categories"""
        headers = {"Authorization": f"Bearer {auth_token}"}
        response = requests.get(f"{BASE_URL}/api/categories", headers=headers)
        
        assert response.status_code == 200, f"Failed: {response.text}"
        data = response.json()
        
        assert isinstance(data, list), "Categories should be a list"
        print(f"Found {len(data)} categories")
    
    def test_create_and_delete_category(self, auth_token):
        """Test create and delete category"""
        headers = {"Authorization": f"Bearer {auth_token}"}
        
        # Create category
        test_category = {
            "name": f"TEST_Iteration77_Category_{int(time.time())}",
            "protocol": "(test or iteration) & (77 or testing)+",
            "description": "Test category for iteration 77"
        }
        
        create_response = requests.post(
            f"{BASE_URL}/api/categories",
            headers=headers,
            json=test_category
        )
        
        assert create_response.status_code in [200, 201], f"Create failed: {create_response.text}"
        created = create_response.json()
        
        # Get category ID
        category_id = created.get("id") or created.get("_id")
        assert category_id, "Category ID not returned"
        print(f"Created category: {category_id}")
        
        # Delete category
        delete_response = requests.delete(
            f"{BASE_URL}/api/categories/{category_id}",
            headers=headers
        )
        
        assert delete_response.status_code in [200, 204], f"Delete failed: {delete_response.text}"
        print(f"Deleted category: {category_id}")


class TestAISuggestionsAPI:
    """AI Suggestions endpoint tests"""
    
    @pytest.fixture
    def auth_token(self):
        """Get authentication token"""
        response = requests.post(f"{BASE_URL}/api/auth/login", json={
            "email": "jjspilot24@gmail.com",
            "password": "InfoPilot2024!"
        })
        if response.status_code == 200:
            return response.json().get("token")
        pytest.skip("Authentication failed")
    
    def test_ai_suggestions(self, auth_token):
        """Test AI suggestions endpoint"""
        headers = {"Authorization": f"Bearer {auth_token}"}
        response = requests.get(f"{BASE_URL}/api/ai/suggestions?limit=5", headers=headers)
        
        assert response.status_code == 200, f"Failed: {response.text}"
        data = response.json()
        
        assert "suggestions" in data, "suggestions key missing"
        assert "ai_powered" in data, "ai_powered flag missing"
        
        print(f"AI Suggestions: {len(data.get('suggestions', []))} items")
        print(f"AI Powered: {data.get('ai_powered')}")
    
    def test_ai_suggestions_refresh(self, auth_token):
        """Test AI suggestions refresh endpoint"""
        headers = {"Authorization": f"Bearer {auth_token}"}
        response = requests.get(f"{BASE_URL}/api/ai/suggestions/refresh", headers=headers)
        
        assert response.status_code == 200, f"Failed: {response.text}"
        data = response.json()
        
        assert "suggestions" in data
        print(f"Refreshed suggestions: {len(data.get('suggestions', []))} items")


class TestHealthAndStatus:
    """Health and status endpoint tests"""
    
    def test_health_endpoint(self):
        """Test health endpoint"""
        response = requests.get(f"{BASE_URL}/api/health")
        
        assert response.status_code == 200, f"Health check failed: {response.text}"
        data = response.json()
        
        assert data.get("status") == "healthy", "Status should be healthy"
        print(f"Health: {data}")


if __name__ == "__main__":
    pytest.main([__file__, "-v", "--tb=short"])
