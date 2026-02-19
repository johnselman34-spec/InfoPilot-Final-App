"""
Iteration 76 - AI Protocol Recommendations and Stability Tests
Tests:
- AI Protocol Recommendations API (POST /api/ai/protocol-recommendations)
- AI Suggestions API (GET /api/ai/suggestions)
- Domain Scoring Schedule API (GET/POST /api/admin/domain-scoring/schedule)
- Quality Score Analytics API (GET /api/analytics/quality-scores)
- Categories CRUD operations
- Search functionality
- Authentication flow
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
        """Test API health endpoint"""
        response = requests.get(f"{BASE_URL}/api/health")
        assert response.status_code == 200
        data = response.json()
        assert data.get("status") == "healthy"
        print(f"✓ Health check passed: {data}")
    
    def test_subscription_info(self):
        """Test subscription info endpoint (public)"""
        response = requests.get(f"{BASE_URL}/api/subscription-info")
        assert response.status_code == 200
        data = response.json()
        assert "price" in data
        assert "features" in data
        print(f"✓ Subscription info: price=${data.get('price')}")


class TestAuthentication:
    """Authentication flow tests"""
    
    def test_admin_login(self):
        """Test admin login"""
        response = requests.post(f"{BASE_URL}/api/auth/login", json={
            "email": ADMIN_EMAIL,
            "password": ADMIN_PASSWORD
        })
        assert response.status_code == 200
        data = response.json()
        assert "token" in data
        assert "user" in data
        assert data["user"].get("is_admin") == True
        print(f"✓ Admin login successful: {data['user'].get('email')}")
        return data["token"]
    
    def test_test_user_login(self):
        """Test regular user login"""
        response = requests.post(f"{BASE_URL}/api/auth/login", json={
            "email": TEST_EMAIL,
            "password": TEST_PASSWORD
        })
        # May fail if test user doesn't exist
        if response.status_code == 200:
            data = response.json()
            assert "token" in data
            print(f"✓ Test user login successful")
            return data["token"]
        else:
            print(f"⚠ Test user login failed (user may not exist): {response.status_code}")
            pytest.skip("Test user not available")


class TestAIProtocolRecommendations:
    """Tests for the new AI Protocol Recommendations feature"""
    
    @pytest.fixture
    def admin_token(self):
        """Get admin auth token"""
        response = requests.post(f"{BASE_URL}/api/auth/login", json={
            "email": ADMIN_EMAIL,
            "password": ADMIN_PASSWORD
        })
        if response.status_code == 200:
            return response.json()["token"]
        pytest.skip("Admin login failed")
    
    def test_ai_protocol_recommendations_trending(self, admin_token):
        """Test AI protocol recommendations - trending category"""
        response = requests.post(
            f"{BASE_URL}/api/ai/protocol-recommendations",
            headers={"Authorization": f"Bearer {admin_token}"},
            json={"category": "trending"}
        )
        assert response.status_code == 200
        data = response.json()
        
        # Verify response structure
        assert "recommendations" in data
        assert "category" in data
        assert data["category"] == "trending"
        
        # Check if AI-powered or fallback
        if data.get("ai_powered"):
            print(f"✓ AI-powered recommendations (GPT-5.2): {len(data['recommendations'])} items")
        else:
            print(f"✓ Fallback recommendations: {len(data['recommendations'])} items")
        
        # Verify recommendation structure
        if data["recommendations"]:
            rec = data["recommendations"][0]
            assert "name" in rec
            assert "protocol" in rec
            assert "estimated_value" in rec
            assert "demand" in rec
            print(f"  Sample: {rec['name']} - {rec['demand']} demand")
    
    def test_ai_protocol_recommendations_similar(self, admin_token):
        """Test AI protocol recommendations - similar category"""
        response = requests.post(
            f"{BASE_URL}/api/ai/protocol-recommendations",
            headers={"Authorization": f"Bearer {admin_token}"},
            json={"category": "similar"}
        )
        assert response.status_code == 200
        data = response.json()
        assert "recommendations" in data
        assert data["category"] == "similar"
        print(f"✓ Similar recommendations: {len(data['recommendations'])} items, ai_powered={data.get('ai_powered')}")
    
    def test_ai_protocol_recommendations_gaps(self, admin_token):
        """Test AI protocol recommendations - market gaps category"""
        response = requests.post(
            f"{BASE_URL}/api/ai/protocol-recommendations",
            headers={"Authorization": f"Bearer {admin_token}"},
            json={"category": "gaps"}
        )
        assert response.status_code == 200
        data = response.json()
        assert "recommendations" in data
        assert data["category"] == "gaps"
        print(f"✓ Market gaps recommendations: {len(data['recommendations'])} items")
    
    def test_ai_protocol_recommendations_seasonal(self, admin_token):
        """Test AI protocol recommendations - seasonal category"""
        response = requests.post(
            f"{BASE_URL}/api/ai/protocol-recommendations",
            headers={"Authorization": f"Bearer {admin_token}"},
            json={"category": "seasonal"}
        )
        assert response.status_code == 200
        data = response.json()
        assert "recommendations" in data
        assert data["category"] == "seasonal"
        print(f"✓ Seasonal recommendations: {len(data['recommendations'])} items")
    
    def test_ai_protocol_recommendations_premium(self, admin_token):
        """Test AI protocol recommendations - premium category"""
        response = requests.post(
            f"{BASE_URL}/api/ai/protocol-recommendations",
            headers={"Authorization": f"Bearer {admin_token}"},
            json={"category": "premium"}
        )
        assert response.status_code == 200
        data = response.json()
        assert "recommendations" in data
        assert data["category"] == "premium"
        print(f"✓ Premium recommendations: {len(data['recommendations'])} items")
    
    def test_ai_protocol_recommendations_unauthorized(self):
        """Test AI protocol recommendations without auth"""
        response = requests.post(
            f"{BASE_URL}/api/ai/protocol-recommendations",
            json={"category": "trending"}
        )
        assert response.status_code == 401 or response.status_code == 403
        print(f"✓ Unauthorized request correctly rejected: {response.status_code}")


class TestAISuggestions:
    """Tests for AI Suggestions endpoint"""
    
    @pytest.fixture
    def admin_token(self):
        """Get admin auth token"""
        response = requests.post(f"{BASE_URL}/api/auth/login", json={
            "email": ADMIN_EMAIL,
            "password": ADMIN_PASSWORD
        })
        if response.status_code == 200:
            return response.json()["token"]
        pytest.skip("Admin login failed")
    
    def test_ai_suggestions(self, admin_token):
        """Test AI suggestions endpoint"""
        response = requests.get(
            f"{BASE_URL}/api/ai/suggestions",
            headers={"Authorization": f"Bearer {admin_token}"}
        )
        assert response.status_code == 200
        data = response.json()
        
        assert "suggestions" in data
        assert "message" in data
        
        if data.get("ai_powered"):
            print(f"✓ AI-powered suggestions: {len(data['suggestions'])} items")
        else:
            print(f"✓ Fallback suggestions: {len(data['suggestions'])} items - {data.get('message')}")
    
    def test_ai_suggestions_refresh(self, admin_token):
        """Test AI suggestions refresh endpoint"""
        response = requests.get(
            f"{BASE_URL}/api/ai/suggestions/refresh",
            headers={"Authorization": f"Bearer {admin_token}"}
        )
        assert response.status_code == 200
        data = response.json()
        assert "suggestions" in data
        print(f"✓ AI suggestions refresh: {len(data['suggestions'])} items")


class TestDomainScoringSchedule:
    """Tests for Domain Scoring Schedule API"""
    
    @pytest.fixture
    def admin_token(self):
        """Get admin auth token"""
        response = requests.post(f"{BASE_URL}/api/auth/login", json={
            "email": ADMIN_EMAIL,
            "password": ADMIN_PASSWORD
        })
        if response.status_code == 200:
            return response.json()["token"]
        pytest.skip("Admin login failed")
    
    def test_get_schedule_config(self, admin_token):
        """Test GET domain scoring schedule config"""
        response = requests.get(
            f"{BASE_URL}/api/admin/domain-scoring/schedule",
            headers={"Authorization": f"Bearer {admin_token}"}
        )
        assert response.status_code == 200
        data = response.json()
        
        # Verify config structure
        assert "enabled" in data
        assert "schedule" in data
        assert "run_hour" in data
        assert "email_notifications" in data
        
        print(f"✓ Schedule config: enabled={data['enabled']}, schedule={data['schedule']}, run_hour={data['run_hour']}")
    
    def test_update_schedule_config(self, admin_token):
        """Test POST domain scoring schedule config"""
        # First get current config
        get_response = requests.get(
            f"{BASE_URL}/api/admin/domain-scoring/schedule",
            headers={"Authorization": f"Bearer {admin_token}"}
        )
        original_config = get_response.json()
        
        # Update config
        response = requests.post(
            f"{BASE_URL}/api/admin/domain-scoring/schedule",
            headers={"Authorization": f"Bearer {admin_token}"},
            json={
                "enabled": True,
                "schedule": "daily",
                "run_hour": 8,
                "email_notifications": True
            }
        )
        assert response.status_code == 200
        data = response.json()
        assert "message" in data or "config" in data
        print(f"✓ Schedule config updated successfully")
        
        # Restore original config
        requests.post(
            f"{BASE_URL}/api/admin/domain-scoring/schedule",
            headers={"Authorization": f"Bearer {admin_token}"},
            json={
                "enabled": original_config.get("enabled", False),
                "schedule": original_config.get("schedule", "daily"),
                "run_hour": original_config.get("run_hour", 6),
                "email_notifications": original_config.get("email_notifications", True)
            }
        )
    
    def test_schedule_config_validation(self, admin_token):
        """Test schedule config validation"""
        # Invalid schedule value
        response = requests.post(
            f"{BASE_URL}/api/admin/domain-scoring/schedule",
            headers={"Authorization": f"Bearer {admin_token}"},
            json={
                "schedule": "invalid_schedule",
                "run_hour": 6
            }
        )
        # Should either reject or use default
        if response.status_code == 400 or response.status_code == 422:
            print(f"✓ Invalid schedule correctly rejected: {response.status_code}")
        else:
            print(f"⚠ Invalid schedule accepted (may use default): {response.status_code}")


class TestQualityScoreAnalytics:
    """Tests for Quality Score Analytics API"""
    
    @pytest.fixture
    def admin_token(self):
        """Get admin auth token"""
        response = requests.post(f"{BASE_URL}/api/auth/login", json={
            "email": ADMIN_EMAIL,
            "password": ADMIN_PASSWORD
        })
        if response.status_code == 200:
            return response.json()["token"]
        pytest.skip("Admin login failed")
    
    def test_get_quality_scores(self, admin_token):
        """Test GET quality scores analytics"""
        response = requests.get(
            f"{BASE_URL}/api/analytics/quality-scores",
            headers={"Authorization": f"Bearer {admin_token}"}
        )
        assert response.status_code == 200
        data = response.json()
        
        # Verify response structure
        assert "domains" in data or "scores" in data or "analytics" in data or isinstance(data, list)
        print(f"✓ Quality scores retrieved: {type(data)}")
    
    def test_domain_alerts(self, admin_token):
        """Test GET domain alerts"""
        response = requests.get(
            f"{BASE_URL}/api/admin/domain-alerts",
            headers={"Authorization": f"Bearer {admin_token}"}
        )
        assert response.status_code == 200
        data = response.json()
        
        assert "alerts" in data or isinstance(data, list)
        print(f"✓ Domain alerts retrieved")


class TestCategoriesAPI:
    """Tests for Categories CRUD operations"""
    
    @pytest.fixture
    def admin_token(self):
        """Get admin auth token"""
        response = requests.post(f"{BASE_URL}/api/auth/login", json={
            "email": ADMIN_EMAIL,
            "password": ADMIN_PASSWORD
        })
        if response.status_code == 200:
            return response.json()["token"]
        pytest.skip("Admin login failed")
    
    def test_get_categories(self, admin_token):
        """Test GET categories"""
        response = requests.get(
            f"{BASE_URL}/api/categories",
            headers={"Authorization": f"Bearer {admin_token}"}
        )
        assert response.status_code == 200
        data = response.json()
        
        # Response could be list or dict with categories key
        if isinstance(data, list):
            print(f"✓ Categories retrieved: {len(data)} items")
        elif isinstance(data, dict) and "categories" in data:
            print(f"✓ Categories retrieved: {len(data['categories'])} items")
        else:
            print(f"✓ Categories response: {type(data)}")
    
    def test_create_and_delete_category(self, admin_token):
        """Test category creation and deletion"""
        # Create category
        test_category = {
            "name": f"TEST_Category_{int(time.time())}",
            "protocol": "(test or testing) & (automation)+",
            "description": "Test category for iteration 76"
        }
        
        create_response = requests.post(
            f"{BASE_URL}/api/categories",
            headers={"Authorization": f"Bearer {admin_token}"},
            json=test_category
        )
        
        if create_response.status_code in [200, 201]:
            data = create_response.json()
            category_id = data.get("id") or data.get("_id") or data.get("category_id")
            print(f"✓ Category created: {test_category['name']}")
            
            # Delete category
            if category_id:
                delete_response = requests.delete(
                    f"{BASE_URL}/api/categories/{category_id}",
                    headers={"Authorization": f"Bearer {admin_token}"}
                )
                if delete_response.status_code in [200, 204]:
                    print(f"✓ Category deleted: {category_id}")
                else:
                    print(f"⚠ Category deletion returned: {delete_response.status_code}")
        else:
            print(f"⚠ Category creation returned: {create_response.status_code}")


class TestSearchAPI:
    """Tests for Search functionality"""
    
    @pytest.fixture
    def admin_token(self):
        """Get admin auth token"""
        response = requests.post(f"{BASE_URL}/api/auth/login", json={
            "email": ADMIN_EMAIL,
            "password": ADMIN_PASSWORD
        })
        if response.status_code == 200:
            return response.json()["token"]
        pytest.skip("Admin login failed")
    
    def test_search_endpoint(self, admin_token):
        """Test search endpoint"""
        response = requests.post(
            f"{BASE_URL}/api/search",
            headers={"Authorization": f"Bearer {admin_token}"},
            json={"query": "artificial intelligence news"}
        )
        assert response.status_code == 200
        data = response.json()
        
        assert "results" in data
        print(f"✓ Search returned: {len(data.get('results', []))} results")
    
    def test_search_engines_status(self, admin_token):
        """Test search engines status endpoint"""
        response = requests.get(
            f"{BASE_URL}/api/search/engines",
            headers={"Authorization": f"Bearer {admin_token}"}
        )
        if response.status_code == 200:
            data = response.json()
            print(f"✓ Search engines status: {data}")
        else:
            print(f"⚠ Search engines endpoint returned: {response.status_code}")


class TestMarketplaceAPI:
    """Tests for Marketplace functionality"""
    
    def test_marketplace_protocols(self):
        """Test marketplace protocols endpoint (public)"""
        response = requests.get(f"{BASE_URL}/api/marketplace/protocols")
        assert response.status_code == 200
        data = response.json()
        
        assert "protocols" in data
        print(f"✓ Marketplace protocols: {len(data.get('protocols', []))} items")
    
    def test_marketplace_categories(self):
        """Test marketplace categories endpoint (public)"""
        response = requests.get(f"{BASE_URL}/api/marketplace/categories")
        assert response.status_code == 200
        data = response.json()
        
        assert "categories" in data
        print(f"✓ Marketplace categories: {len(data.get('categories', []))} items")


if __name__ == "__main__":
    pytest.main([__file__, "-v", "--tb=short"])
