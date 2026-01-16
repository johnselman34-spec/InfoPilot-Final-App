"""
Test suite for Iteration 72 - Quality Score Analytics feature
Tests the new /api/analytics/quality-scores endpoint and Admin Panel integration
"""
import pytest
import requests
import os

BASE_URL = os.environ.get('REACT_APP_BACKEND_URL', '').rstrip('/')

# Test credentials
ADMIN_EMAIL = "jjspilot24@gmail.com"
ADMIN_PASSWORD = "InfoPilot2024!"
TEST_EMAIL = "testuser@example.com"
TEST_PASSWORD = "password123"


class TestHealthAndBasics:
    """Basic health checks to ensure API is running"""
    
    def test_health_endpoint(self):
        """Test health endpoint returns 200"""
        response = requests.get(f"{BASE_URL}/api/health")
        assert response.status_code == 200
        data = response.json()
        assert data.get("status") == "healthy"
        print(f"✅ Health check passed: {data}")


class TestAuthentication:
    """Authentication tests"""
    
    def test_admin_login(self):
        """Test admin login returns token"""
        response = requests.post(f"{BASE_URL}/api/auth/login", json={
            "email": ADMIN_EMAIL,
            "password": ADMIN_PASSWORD
        })
        assert response.status_code == 200
        data = response.json()
        assert "token" in data
        assert data.get("user", {}).get("is_admin") == True
        print(f"✅ Admin login successful, is_admin: {data.get('user', {}).get('is_admin')}")
        return data["token"]


class TestQualityScoreAnalyticsAPI:
    """Tests for the new Quality Score Analytics API endpoint"""
    
    @pytest.fixture
    def admin_token(self):
        """Get admin authentication token"""
        response = requests.post(f"{BASE_URL}/api/auth/login", json={
            "email": ADMIN_EMAIL,
            "password": ADMIN_PASSWORD
        })
        if response.status_code == 200:
            return response.json().get("token")
        pytest.skip("Admin authentication failed")
    
    def test_quality_scores_endpoint_exists(self, admin_token):
        """Test that /api/analytics/quality-scores endpoint exists and returns 200"""
        response = requests.get(
            f"{BASE_URL}/api/analytics/quality-scores",
            headers={"Authorization": f"Bearer {admin_token}"}
        )
        assert response.status_code == 200
        print(f"✅ Quality scores endpoint exists and returns 200")
    
    def test_quality_scores_response_structure(self, admin_token):
        """Test that response has all required fields"""
        response = requests.get(
            f"{BASE_URL}/api/analytics/quality-scores",
            headers={"Authorization": f"Bearer {admin_token}"}
        )
        assert response.status_code == 200
        data = response.json()
        
        # Check required top-level fields
        required_fields = [
            "total_results",
            "average_score",
            "distribution",
            "top_quality_domains",
            "improvement_opportunities",
            "quality_trend",
            "article_type_quality",
            "insights",
            "last_updated"
        ]
        
        for field in required_fields:
            assert field in data, f"Missing required field: {field}"
        
        print(f"✅ Response has all required fields: {list(data.keys())}")
    
    def test_quality_scores_distribution_structure(self, admin_token):
        """Test that distribution has 5 quality ranges with correct structure"""
        response = requests.get(
            f"{BASE_URL}/api/analytics/quality-scores",
            headers={"Authorization": f"Bearer {admin_token}"}
        )
        assert response.status_code == 200
        data = response.json()
        
        distribution = data.get("distribution", [])
        assert len(distribution) == 5, f"Expected 5 quality ranges, got {len(distribution)}"
        
        # Check expected range names
        expected_names = ["Premium", "High Quality", "Good", "Below Average", "Low Quality"]
        actual_names = [d["name"] for d in distribution]
        assert actual_names == expected_names, f"Expected {expected_names}, got {actual_names}"
        
        # Check each range has required fields
        for range_item in distribution:
            assert "name" in range_item
            assert "emoji" in range_item
            assert "min_score" in range_item
            assert "max_score" in range_item
            assert "color" in range_item
            assert "count" in range_item
            assert "percentage" in range_item
        
        print(f"✅ Distribution has 5 ranges: {actual_names}")
        print(f"   Counts: {[d['count'] for d in distribution]}")
    
    def test_quality_scores_distribution_ranges(self, admin_token):
        """Test that distribution ranges are correct (Premium 80-100, High Quality 65-79, etc.)"""
        response = requests.get(
            f"{BASE_URL}/api/analytics/quality-scores",
            headers={"Authorization": f"Bearer {admin_token}"}
        )
        assert response.status_code == 200
        data = response.json()
        
        distribution = data.get("distribution", [])
        
        expected_ranges = [
            {"name": "Premium", "min": 80, "max": 100},
            {"name": "High Quality", "min": 65, "max": 79},
            {"name": "Good", "min": 50, "max": 64},
            {"name": "Below Average", "min": 25, "max": 49},
            {"name": "Low Quality", "min": 0, "max": 24}
        ]
        
        for i, expected in enumerate(expected_ranges):
            actual = distribution[i]
            assert actual["name"] == expected["name"], f"Range {i} name mismatch"
            assert actual["min_score"] == expected["min"], f"Range {i} min_score mismatch"
            assert actual["max_score"] == expected["max"], f"Range {i} max_score mismatch"
        
        print(f"✅ All distribution ranges have correct min/max scores")
    
    def test_quality_scores_average_score(self, admin_token):
        """Test that average_score is a valid number"""
        response = requests.get(
            f"{BASE_URL}/api/analytics/quality-scores",
            headers={"Authorization": f"Bearer {admin_token}"}
        )
        assert response.status_code == 200
        data = response.json()
        
        avg_score = data.get("average_score")
        assert isinstance(avg_score, (int, float)), f"average_score should be a number, got {type(avg_score)}"
        assert 0 <= avg_score <= 100, f"average_score should be 0-100, got {avg_score}"
        
        print(f"✅ Average score: {avg_score}")
    
    def test_quality_scores_top_domains_structure(self, admin_token):
        """Test that top_quality_domains has correct structure"""
        response = requests.get(
            f"{BASE_URL}/api/analytics/quality-scores",
            headers={"Authorization": f"Bearer {admin_token}"}
        )
        assert response.status_code == 200
        data = response.json()
        
        top_domains = data.get("top_quality_domains", [])
        assert isinstance(top_domains, list), "top_quality_domains should be a list"
        
        if len(top_domains) > 0:
            for domain in top_domains:
                assert "domain" in domain
                assert "avg_score" in domain
                assert "count" in domain
            print(f"✅ Top quality domains: {len(top_domains)} domains found")
            print(f"   Top 3: {[d['domain'] for d in top_domains[:3]]}")
        else:
            print(f"⚠️ No top quality domains found (may need more data)")
    
    def test_quality_scores_improvement_opportunities(self, admin_token):
        """Test that improvement_opportunities has correct structure"""
        response = requests.get(
            f"{BASE_URL}/api/analytics/quality-scores",
            headers={"Authorization": f"Bearer {admin_token}"}
        )
        assert response.status_code == 200
        data = response.json()
        
        improvement = data.get("improvement_opportunities", [])
        assert isinstance(improvement, list), "improvement_opportunities should be a list"
        
        if len(improvement) > 0:
            for domain in improvement:
                assert "domain" in domain
                assert "avg_score" in domain
                assert "count" in domain
            print(f"✅ Improvement opportunities: {len(improvement)} domains found")
        else:
            print(f"⚠️ No improvement opportunities found (may need more data)")
    
    def test_quality_scores_article_type_quality(self, admin_token):
        """Test that article_type_quality has correct structure"""
        response = requests.get(
            f"{BASE_URL}/api/analytics/quality-scores",
            headers={"Authorization": f"Bearer {admin_token}"}
        )
        assert response.status_code == 200
        data = response.json()
        
        article_types = data.get("article_type_quality", [])
        assert isinstance(article_types, list), "article_type_quality should be a list"
        
        if len(article_types) > 0:
            for article_type in article_types:
                assert "type" in article_type
                assert "avg_score" in article_type
                assert "count" in article_type
            print(f"✅ Article type quality: {len(article_types)} types found")
            print(f"   Types: {[a['type'] for a in article_types[:5]]}")
        else:
            print(f"⚠️ No article type quality data found")
    
    def test_quality_scores_insights(self, admin_token):
        """Test that insights has correct structure"""
        response = requests.get(
            f"{BASE_URL}/api/analytics/quality-scores",
            headers={"Authorization": f"Bearer {admin_token}"}
        )
        assert response.status_code == 200
        data = response.json()
        
        insights = data.get("insights", {})
        assert isinstance(insights, dict), "insights should be a dict"
        
        # Check required insight fields
        assert "premium_percentage" in insights
        assert "high_quality_percentage" in insights
        assert "needs_improvement_count" in insights
        
        print(f"✅ Insights: premium={insights.get('premium_percentage')}%, high_quality={insights.get('high_quality_percentage')}%, needs_improvement={insights.get('needs_improvement_count')}")
    
    def test_quality_scores_requires_admin(self):
        """Test that endpoint requires admin authentication"""
        # Test without auth
        response = requests.get(f"{BASE_URL}/api/analytics/quality-scores")
        assert response.status_code in [401, 403], f"Expected 401/403 without auth, got {response.status_code}"
        print(f"✅ Endpoint correctly requires authentication (status: {response.status_code})")
    
    def test_quality_scores_non_admin_forbidden(self):
        """Test that non-admin users get 403"""
        # Try to login as test user
        response = requests.post(f"{BASE_URL}/api/auth/login", json={
            "email": TEST_EMAIL,
            "password": TEST_PASSWORD
        })
        
        if response.status_code != 200:
            pytest.skip("Test user login failed - user may not exist")
        
        token = response.json().get("token")
        
        # Try to access quality scores
        response = requests.get(
            f"{BASE_URL}/api/analytics/quality-scores",
            headers={"Authorization": f"Bearer {token}"}
        )
        assert response.status_code == 403, f"Expected 403 for non-admin, got {response.status_code}"
        print(f"✅ Non-admin users correctly get 403 Forbidden")


class TestAdminPanelTabs:
    """Tests for Admin Panel tab configuration"""
    
    @pytest.fixture
    def admin_token(self):
        """Get admin authentication token"""
        response = requests.post(f"{BASE_URL}/api/auth/login", json={
            "email": ADMIN_EMAIL,
            "password": ADMIN_PASSWORD
        })
        if response.status_code == 200:
            return response.json().get("token")
        pytest.skip("Admin authentication failed")
    
    def test_admin_settings_endpoint(self, admin_token):
        """Test admin settings endpoint works"""
        response = requests.get(
            f"{BASE_URL}/api/admin/settings",
            headers={"Authorization": f"Bearer {admin_token}"}
        )
        assert response.status_code == 200
        print(f"✅ Admin settings endpoint works")
    
    def test_admin_stats_endpoint(self, admin_token):
        """Test admin stats endpoint works"""
        response = requests.get(
            f"{BASE_URL}/api/admin/stats",
            headers={"Authorization": f"Bearer {admin_token}"}
        )
        assert response.status_code == 200
        print(f"✅ Admin stats endpoint works")


class TestPreviousFeaturesStability:
    """Tests to ensure previous features still work"""
    
    @pytest.fixture
    def admin_token(self):
        """Get admin authentication token"""
        response = requests.post(f"{BASE_URL}/api/auth/login", json={
            "email": ADMIN_EMAIL,
            "password": ADMIN_PASSWORD
        })
        if response.status_code == 200:
            return response.json().get("token")
        pytest.skip("Admin authentication failed")
    
    def test_categories_endpoint(self, admin_token):
        """Test categories endpoint still works"""
        response = requests.get(
            f"{BASE_URL}/api/categories",
            headers={"Authorization": f"Bearer {admin_token}"}
        )
        assert response.status_code == 200
        print(f"✅ Categories endpoint works")
    
    def test_marketplace_leaderboard(self, admin_token):
        """Test marketplace leaderboard still works"""
        response = requests.get(
            f"{BASE_URL}/api/marketplace/leaderboard",
            headers={"Authorization": f"Bearer {admin_token}"}
        )
        assert response.status_code == 200
        print(f"✅ Marketplace leaderboard works")
    
    def test_newsletter_history(self, admin_token):
        """Test newsletter history still works"""
        response = requests.get(
            f"{BASE_URL}/api/newsletter/history",
            headers={"Authorization": f"Bearer {admin_token}"}
        )
        assert response.status_code == 200
        print(f"✅ Newsletter history works")
    
    def test_category_analytics(self, admin_token):
        """Test category analytics still works"""
        response = requests.get(
            f"{BASE_URL}/api/analytics/categories",
            headers={"Authorization": f"Bearer {admin_token}"}
        )
        assert response.status_code == 200
        print(f"✅ Category analytics works")


if __name__ == "__main__":
    pytest.main([__file__, "-v", "--tb=short"])
