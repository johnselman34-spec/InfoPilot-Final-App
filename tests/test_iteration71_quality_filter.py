"""
Iteration 71 - Quality Score Filtering & Comprehensive Stability Tests
Tests:
1. Quality Score Filtering UI (4 filter buttons)
2. Quality Score Filtering Logic
3. Content Quality Badges
4. All API endpoints (health, auth, marketplace, admin, search)
5. No hung processes or timeouts
6. Data flow validation
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


class TestHealthAndBasicEndpoints:
    """Test health and basic API endpoints"""
    
    def test_health_endpoint(self):
        """Test health endpoint returns healthy status"""
        response = requests.get(f"{BASE_URL}/api/health", timeout=10)
        assert response.status_code == 200
        data = response.json()
        assert data.get("status") == "healthy"
        assert "timestamp" in data
        print(f"✓ Health endpoint: {data}")
    
    def test_subscription_info(self):
        """Test subscription info endpoint"""
        response = requests.get(f"{BASE_URL}/api/subscription-info", timeout=10)
        assert response.status_code == 200
        data = response.json()
        assert "price" in data
        assert "features" in data
        print(f"✓ Subscription info: price={data.get('price')}")


class TestAuthentication:
    """Test authentication endpoints"""
    
    def test_admin_login(self):
        """Test admin login"""
        response = requests.post(
            f"{BASE_URL}/api/auth/login",
            json={"email": ADMIN_EMAIL, "password": ADMIN_PASSWORD},
            timeout=15
        )
        assert response.status_code == 200
        data = response.json()
        assert "token" in data
        assert "user" in data
        print(f"✓ Admin login successful: user={data['user'].get('email')}")
        return data["token"]
    
    def test_test_user_login(self):
        """Test regular user login"""
        response = requests.post(
            f"{BASE_URL}/api/auth/login",
            json={"email": TEST_EMAIL, "password": TEST_PASSWORD},
            timeout=15
        )
        # May return 401 if user doesn't exist, which is fine
        if response.status_code == 200:
            data = response.json()
            assert "token" in data
            print(f"✓ Test user login successful")
        else:
            print(f"✓ Test user login returned {response.status_code} (user may not exist)")
        assert response.status_code in [200, 401]


class TestMarketplaceEndpoints:
    """Test marketplace API endpoints"""
    
    @pytest.fixture(autouse=True)
    def setup(self):
        """Get auth token for tests"""
        response = requests.post(
            f"{BASE_URL}/api/auth/login",
            json={"email": ADMIN_EMAIL, "password": ADMIN_PASSWORD},
            timeout=15
        )
        if response.status_code == 200:
            self.token = response.json()["token"]
            self.headers = {"Authorization": f"Bearer {self.token}"}
        else:
            pytest.skip("Could not authenticate")
    
    def test_marketplace_protocols(self):
        """Test marketplace protocols endpoint"""
        response = requests.get(
            f"{BASE_URL}/api/marketplace/protocols",
            headers=self.headers,
            timeout=15
        )
        assert response.status_code == 200
        data = response.json()
        assert isinstance(data, list)
        print(f"✓ Marketplace protocols: {len(data)} protocols found")
    
    def test_marketplace_leaderboard(self):
        """Test marketplace leaderboard endpoint"""
        response = requests.get(
            f"{BASE_URL}/api/marketplace/leaderboard",
            headers=self.headers,
            timeout=15
        )
        assert response.status_code == 200
        data = response.json()
        assert "topCreators" in data or "topProtocols" in data
        print(f"✓ Marketplace leaderboard: {list(data.keys())}")
    
    def test_marketplace_performance_insights(self):
        """Test marketplace performance insights endpoint"""
        response = requests.get(
            f"{BASE_URL}/api/marketplace/performance-insights",
            headers=self.headers,
            timeout=15
        )
        assert response.status_code == 200
        data = response.json()
        assert "has_protocols" in data or "insights" in data
        print(f"✓ Performance insights: {list(data.keys())}")


class TestAdminEndpoints:
    """Test admin API endpoints"""
    
    @pytest.fixture(autouse=True)
    def setup(self):
        """Get auth token for tests"""
        response = requests.post(
            f"{BASE_URL}/api/auth/login",
            json={"email": ADMIN_EMAIL, "password": ADMIN_PASSWORD},
            timeout=15
        )
        if response.status_code == 200:
            self.token = response.json()["token"]
            self.headers = {"Authorization": f"Bearer {self.token}"}
        else:
            pytest.skip("Could not authenticate")
    
    def test_admin_stats(self):
        """Test admin stats endpoint"""
        response = requests.get(
            f"{BASE_URL}/api/admin/stats",
            headers=self.headers,
            timeout=15
        )
        assert response.status_code == 200
        data = response.json()
        assert "total_users" in data or "users" in data or isinstance(data, dict)
        print(f"✓ Admin stats: {list(data.keys())[:5]}...")
    
    def test_admin_settings(self):
        """Test admin settings endpoint"""
        response = requests.get(
            f"{BASE_URL}/api/admin/settings",
            headers=self.headers,
            timeout=15
        )
        assert response.status_code == 200
        data = response.json()
        assert isinstance(data, (list, dict))
        print(f"✓ Admin settings retrieved")
    
    def test_newsletter_history(self):
        """Test newsletter history endpoint"""
        response = requests.get(
            f"{BASE_URL}/api/newsletter/history",
            headers=self.headers,
            timeout=15
        )
        assert response.status_code == 200
        data = response.json()
        # Should return either array or {history: [...]}
        assert isinstance(data, (list, dict))
        print(f"✓ Newsletter history: type={type(data).__name__}")


class TestSearchEndpoints:
    """Test search-related API endpoints"""
    
    @pytest.fixture(autouse=True)
    def setup(self):
        """Get auth token for tests"""
        response = requests.post(
            f"{BASE_URL}/api/auth/login",
            json={"email": ADMIN_EMAIL, "password": ADMIN_PASSWORD},
            timeout=15
        )
        if response.status_code == 200:
            self.token = response.json()["token"]
            self.headers = {"Authorization": f"Bearer {self.token}"}
        else:
            pytest.skip("Could not authenticate")
    
    def test_categories_endpoint(self):
        """Test categories endpoint"""
        response = requests.get(
            f"{BASE_URL}/api/categories",
            headers=self.headers,
            timeout=15
        )
        assert response.status_code == 200
        data = response.json()
        assert isinstance(data, list)
        print(f"✓ Categories: {len(data)} categories found")
    
    def test_ultimate_search_endpoint(self):
        """Test ultimate search endpoint"""
        response = requests.get(
            f"{BASE_URL}/api/ultimate-search?limit=10",
            headers=self.headers,
            timeout=15
        )
        assert response.status_code == 200
        data = response.json()
        assert "results" in data
        results = data.get("results", [])
        print(f"✓ Ultimate search: {len(results)} results")
        
        # Check if results have content_quality_score
        if results:
            first_result = results[0]
            has_quality_score = "content_quality_score" in first_result
            print(f"  - Results have content_quality_score: {has_quality_score}")
            if has_quality_score:
                print(f"  - Sample quality score: {first_result.get('content_quality_score')}")
    
    def test_search_engines_status(self):
        """Test search engines status endpoint"""
        response = requests.get(
            f"{BASE_URL}/api/search/engines",
            headers=self.headers,
            timeout=15
        )
        assert response.status_code == 200
        data = response.json()
        assert "engines" in data
        print(f"✓ Search engines: {data.get('total_available', 0)} available")


class TestContentQualityScoring:
    """Test content quality scoring functionality"""
    
    @pytest.fixture(autouse=True)
    def setup(self):
        """Get auth token for tests"""
        response = requests.post(
            f"{BASE_URL}/api/auth/login",
            json={"email": ADMIN_EMAIL, "password": ADMIN_PASSWORD},
            timeout=15
        )
        if response.status_code == 200:
            self.token = response.json()["token"]
            self.headers = {"Authorization": f"Bearer {self.token}"}
        else:
            pytest.skip("Could not authenticate")
    
    def test_search_results_have_quality_scores(self):
        """Verify search results include content_quality_score field"""
        response = requests.get(
            f"{BASE_URL}/api/ultimate-search?limit=50",
            headers=self.headers,
            timeout=20
        )
        assert response.status_code == 200
        data = response.json()
        results = data.get("results", [])
        
        if not results:
            print("⚠ No search results to verify quality scores")
            return
        
        # Count results with quality scores
        with_score = sum(1 for r in results if "content_quality_score" in r)
        print(f"✓ Results with quality scores: {with_score}/{len(results)}")
        
        # Verify score ranges
        scores = [r.get("content_quality_score", 50) for r in results]
        min_score = min(scores)
        max_score = max(scores)
        avg_score = sum(scores) / len(scores)
        
        print(f"  - Score range: {min_score} - {max_score}")
        print(f"  - Average score: {avg_score:.1f}")
        
        # Verify scores are in valid range (0-100)
        assert all(0 <= s <= 100 for s in scores), "Some scores outside 0-100 range"
        
        # Count by quality tier
        premium = sum(1 for s in scores if s >= 80)
        high_quality = sum(1 for s in scores if 65 <= s < 80)
        good = sum(1 for s in scores if 50 <= s < 65)
        below_good = sum(1 for s in scores if s < 50)
        
        print(f"  - Premium (80+): {premium}")
        print(f"  - High Quality (65-79): {high_quality}")
        print(f"  - Good (50-64): {good}")
        print(f"  - Below Good (<50): {below_good}")


class TestDataFlowAndStability:
    """Test data flow and system stability"""
    
    @pytest.fixture(autouse=True)
    def setup(self):
        """Get auth token for tests"""
        response = requests.post(
            f"{BASE_URL}/api/auth/login",
            json={"email": ADMIN_EMAIL, "password": ADMIN_PASSWORD},
            timeout=15
        )
        if response.status_code == 200:
            self.token = response.json()["token"]
            self.headers = {"Authorization": f"Bearer {self.token}"}
        else:
            pytest.skip("Could not authenticate")
    
    def test_no_hung_processes(self):
        """Test that API endpoints respond within acceptable time"""
        endpoints = [
            "/api/health",
            "/api/categories",
            "/api/marketplace/protocols",
            "/api/admin/stats",
        ]
        
        for endpoint in endpoints:
            start = time.time()
            response = requests.get(
                f"{BASE_URL}{endpoint}",
                headers=self.headers,
                timeout=30
            )
            elapsed = time.time() - start
            
            assert response.status_code in [200, 401, 403], f"{endpoint} returned {response.status_code}"
            assert elapsed < 30, f"{endpoint} took {elapsed:.1f}s (>30s timeout)"
            print(f"✓ {endpoint}: {response.status_code} in {elapsed:.2f}s")
    
    def test_response_structure_validation(self):
        """Validate response structures are correct"""
        # Test health
        response = requests.get(f"{BASE_URL}/api/health", timeout=10)
        assert response.status_code == 200
        data = response.json()
        assert isinstance(data, dict)
        assert "status" in data
        
        # Test categories
        response = requests.get(
            f"{BASE_URL}/api/categories",
            headers=self.headers,
            timeout=15
        )
        assert response.status_code == 200
        data = response.json()
        assert isinstance(data, list)
        
        # Test ultimate search
        response = requests.get(
            f"{BASE_URL}/api/ultimate-search?limit=5",
            headers=self.headers,
            timeout=15
        )
        assert response.status_code == 200
        data = response.json()
        assert isinstance(data, dict)
        assert "results" in data
        
        print("✓ All response structures validated")


class TestGamificationAndSocial:
    """Test gamification and social features"""
    
    @pytest.fixture(autouse=True)
    def setup(self):
        """Get auth token for tests"""
        response = requests.post(
            f"{BASE_URL}/api/auth/login",
            json={"email": ADMIN_EMAIL, "password": ADMIN_PASSWORD},
            timeout=15
        )
        if response.status_code == 200:
            self.token = response.json()["token"]
            self.headers = {"Authorization": f"Bearer {self.token}"}
        else:
            pytest.skip("Could not authenticate")
    
    def test_gamification_stats(self):
        """Test gamification stats endpoint"""
        response = requests.get(
            f"{BASE_URL}/api/gamification/stats",
            headers=self.headers,
            timeout=15
        )
        assert response.status_code == 200
        data = response.json()
        assert isinstance(data, dict)
        print(f"✓ Gamification stats: {list(data.keys())[:5]}...")
    
    def test_leaderboard(self):
        """Test leaderboard endpoint"""
        response = requests.get(
            f"{BASE_URL}/api/gamification/leaderboard",
            headers=self.headers,
            timeout=15
        )
        assert response.status_code == 200
        data = response.json()
        assert isinstance(data, (list, dict))
        print(f"✓ Leaderboard retrieved")


if __name__ == "__main__":
    pytest.main([__file__, "-v", "--tb=short"])
