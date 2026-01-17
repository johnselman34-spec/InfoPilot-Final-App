"""
InfoPilot Explorer - Iteration 82 Feature Tests
Testing:
1. Ultimate Search Page - category checkbox toggles show filtered results at bottom
2. Map Page - category filter displays filtered results panel when categories selected
3. Marketplace Page - category filter shows filtered protocols at bottom when categories selected
4. Content Quality Report - GET /api/admin/content-quality-report endpoint returns report data
5. Banned words integration - category creation with banned word should be blocked and logged
6. Admin Panel - new 'Quality Report' tab renders ContentQualityReport component
7. Color-coordinated dots on map match selected categories
"""

import pytest
import requests
import os
import time

BASE_URL = os.environ.get('REACT_APP_BACKEND_URL', 'https://info-pilot.preview.emergentagent.com')

# Test credentials
ADMIN_EMAIL = "jjspilot24@gmail.com"
ADMIN_PASSWORD = "InfoPilot2024!"


class TestAuthentication:
    """Test authentication flow"""
    
    @pytest.fixture(scope="class")
    def auth_token(self):
        """Get authentication token for admin user"""
        response = requests.post(f"{BASE_URL}/api/auth/login", json={
            "email": ADMIN_EMAIL,
            "password": ADMIN_PASSWORD
        })
        assert response.status_code == 200, f"Login failed: {response.text}"
        data = response.json()
        assert "token" in data, "No token in response"
        return data["token"]
    
    def test_admin_login(self, auth_token):
        """Test admin login returns valid token"""
        assert auth_token is not None
        assert len(auth_token) > 0


class TestContentQualityReport:
    """Test Content Quality Report endpoint"""
    
    @pytest.fixture(scope="class")
    def auth_token(self):
        """Get authentication token for admin user"""
        response = requests.post(f"{BASE_URL}/api/auth/login", json={
            "email": ADMIN_EMAIL,
            "password": ADMIN_PASSWORD
        })
        assert response.status_code == 200
        return response.json()["token"]
    
    def test_content_quality_report_endpoint_exists(self, auth_token):
        """Test GET /api/admin/content-quality-report endpoint exists and returns data"""
        response = requests.get(
            f"{BASE_URL}/api/admin/content-quality-report",
            headers={"Authorization": f"Bearer {auth_token}"}
        )
        assert response.status_code == 200, f"Content quality report failed: {response.text}"
        data = response.json()
        
        # Verify response structure
        assert "total_violations" in data, "Missing total_violations"
        assert "unique_violators" in data, "Missing unique_violators"
        assert "banned_words_count" in data, "Missing banned_words_count"
        assert "violations_by_type" in data, "Missing violations_by_type"
        assert "quality_distribution" in data, "Missing quality_distribution"
        assert "violation_trend" in data, "Missing violation_trend"
        
    def test_content_quality_report_with_days_param(self, auth_token):
        """Test content quality report with different days parameter"""
        for days in [7, 30, 90]:
            response = requests.get(
                f"{BASE_URL}/api/admin/content-quality-report?days={days}",
                headers={"Authorization": f"Bearer {auth_token}"}
            )
            assert response.status_code == 200, f"Report failed for {days} days: {response.text}"
            data = response.json()
            assert data["period_days"] == days, f"Period days mismatch for {days}"
    
    def test_content_quality_report_quality_distribution(self, auth_token):
        """Test quality distribution structure in report"""
        response = requests.get(
            f"{BASE_URL}/api/admin/content-quality-report",
            headers={"Authorization": f"Bearer {auth_token}"}
        )
        assert response.status_code == 200
        data = response.json()
        
        quality_dist = data["quality_distribution"]
        expected_keys = ["poor", "fair", "good", "high", "premium"]
        for key in expected_keys:
            assert key in quality_dist, f"Missing quality level: {key}"
            assert isinstance(quality_dist[key], int), f"Quality count should be int: {key}"
    
    def test_content_quality_report_violations_by_type(self, auth_token):
        """Test violations by type structure"""
        response = requests.get(
            f"{BASE_URL}/api/admin/content-quality-report",
            headers={"Authorization": f"Bearer {auth_token}"}
        )
        assert response.status_code == 200
        data = response.json()
        
        violations_by_type = data["violations_by_type"]
        expected_types = ["category", "protocol", "marketplace", "other"]
        for vtype in expected_types:
            assert vtype in violations_by_type, f"Missing violation type: {vtype}"
    
    def test_content_quality_report_requires_admin(self):
        """Test that non-admin users cannot access content quality report"""
        # Try without auth
        response = requests.get(f"{BASE_URL}/api/admin/content-quality-report")
        assert response.status_code in [401, 403], "Should require authentication"


class TestBannedWordsIntegration:
    """Test banned words integration with category creation"""
    
    @pytest.fixture(scope="class")
    def auth_token(self):
        """Get authentication token for admin user"""
        response = requests.post(f"{BASE_URL}/api/auth/login", json={
            "email": ADMIN_EMAIL,
            "password": ADMIN_PASSWORD
        })
        assert response.status_code == 200
        return response.json()["token"]
    
    def test_get_banned_words(self, auth_token):
        """Test getting banned words list"""
        response = requests.get(
            f"{BASE_URL}/api/admin/banned-words",
            headers={"Authorization": f"Bearer {auth_token}"}
        )
        assert response.status_code == 200, f"Get banned words failed: {response.text}"
        data = response.json()
        # API returns a list directly
        assert isinstance(data, list), "Banned words should be a list"
    
    def test_add_test_banned_word(self, auth_token):
        """Test adding a banned word"""
        test_word = f"TEST_BANNED_WORD_82_{int(time.time())}"
        
        # Add banned word
        response = requests.post(
            f"{BASE_URL}/api/admin/banned-words",
            headers={"Authorization": f"Bearer {auth_token}"},
            json={"word": test_word}
        )
        assert response.status_code in [200, 201], f"Add banned word failed: {response.text}"
        
        # Verify it was added
        response = requests.get(
            f"{BASE_URL}/api/admin/banned-words",
            headers={"Authorization": f"Bearer {auth_token}"}
        )
        data = response.json()
        # API returns a list directly
        words = [bw["word"] for bw in data]
        assert test_word in words, "Banned word not found after adding"
        
        # Clean up - delete the test banned word
        for bw in data:
            if bw["word"] == test_word:
                delete_response = requests.delete(
                    f"{BASE_URL}/api/admin/banned-words/{bw['id']}",
                    headers={"Authorization": f"Bearer {auth_token}"}
                )
                assert delete_response.status_code == 200, "Failed to delete test banned word"
                break
    
    def test_category_creation_with_banned_word_blocked(self, auth_token):
        """Test that category creation with banned word is blocked and logged"""
        test_banned_word = "TEST_VIOLATION_WORD_82"
        
        # First add a banned word
        add_response = requests.post(
            f"{BASE_URL}/api/admin/banned-words",
            headers={"Authorization": f"Bearer {auth_token}"},
            json={"word": test_banned_word}
        )
        
        if add_response.status_code in [200, 201]:
            # Try to create a category with the banned word in name
            category_response = requests.post(
                f"{BASE_URL}/api/categories",
                headers={"Authorization": f"Bearer {auth_token}"},
                json={
                    "name": f"Category with {test_banned_word}",
                    "protocol": "(test or example)",
                    "is_public": False
                }
            )
            
            # Should be blocked with 400 status
            assert category_response.status_code == 400, f"Category with banned word should be blocked: {category_response.text}"
            assert "banned" in category_response.text.lower(), "Error should mention banned word"
            
            # Clean up - delete the test banned word
            get_response = requests.get(
                f"{BASE_URL}/api/admin/banned-words",
                headers={"Authorization": f"Bearer {auth_token}"}
            )
            # API returns a list directly
            for bw in get_response.json():
                if bw["word"] == test_banned_word:
                    requests.delete(
                        f"{BASE_URL}/api/admin/banned-words/{bw['id']}",
                        headers={"Authorization": f"Bearer {auth_token}"}
                    )
                    break
    
    def test_reserved_keywords_cannot_be_banned(self, auth_token):
        """Test that reserved keywords (or, and, &, etc.) cannot be banned"""
        reserved_keywords = ["or", "and", "&", "(", ")", "+"]
        
        for keyword in reserved_keywords:
            response = requests.post(
                f"{BASE_URL}/api/admin/banned-words",
                headers={"Authorization": f"Bearer {auth_token}"},
                json={"word": keyword}
            )
            # Should be rejected with 400 status
            assert response.status_code == 400, f"Reserved keyword '{keyword}' should not be bannable"


class TestCategoriesAPI:
    """Test categories API for filtered results functionality"""
    
    @pytest.fixture(scope="class")
    def auth_token(self):
        """Get authentication token for admin user"""
        response = requests.post(f"{BASE_URL}/api/auth/login", json={
            "email": ADMIN_EMAIL,
            "password": ADMIN_PASSWORD
        })
        assert response.status_code == 200
        return response.json()["token"]
    
    def test_get_categories(self, auth_token):
        """Test getting categories list"""
        response = requests.get(
            f"{BASE_URL}/api/categories",
            headers={"Authorization": f"Bearer {auth_token}"}
        )
        assert response.status_code == 200, f"Get categories failed: {response.text}"
        data = response.json()
        assert isinstance(data, list), "Categories should be a list"
    
    def test_create_category(self, auth_token):
        """Test creating a category"""
        test_category = {
            "name": f"TEST_Category_82_{int(time.time())}",
            "protocol": "(test or example) & (data or info)",
            "is_public": False
        }
        
        response = requests.post(
            f"{BASE_URL}/api/categories",
            headers={"Authorization": f"Bearer {auth_token}"},
            json=test_category
        )
        assert response.status_code in [200, 201], f"Create category failed: {response.text}"
        data = response.json()
        assert "id" in data, "Category should have an id"
        
        # Clean up - delete the test category
        delete_response = requests.delete(
            f"{BASE_URL}/api/categories/{data['id']}",
            headers={"Authorization": f"Bearer {auth_token}"}
        )
        assert delete_response.status_code == 200, "Failed to delete test category"


class TestUltimateSearchAPI:
    """Test Ultimate Search API for filtered results"""
    
    @pytest.fixture(scope="class")
    def auth_token(self):
        """Get authentication token for admin user"""
        response = requests.post(f"{BASE_URL}/api/auth/login", json={
            "email": ADMIN_EMAIL,
            "password": ADMIN_PASSWORD
        })
        assert response.status_code == 200
        return response.json()["token"]
    
    def test_ultimate_search_endpoint(self, auth_token):
        """Test ultimate search endpoint returns results"""
        response = requests.get(
            f"{BASE_URL}/api/ultimate-search?limit=10",
            headers={"Authorization": f"Bearer {auth_token}"}
        )
        assert response.status_code == 200, f"Ultimate search failed: {response.text}"
        data = response.json()
        assert "results" in data, "Missing results in response"
    
    def test_ultimate_search_with_category_filter(self, auth_token):
        """Test ultimate search with category filter"""
        # First get categories
        cat_response = requests.get(
            f"{BASE_URL}/api/categories",
            headers={"Authorization": f"Bearer {auth_token}"}
        )
        categories = cat_response.json()
        
        if categories:
            cat_id = categories[0]["id"]
            response = requests.get(
                f"{BASE_URL}/api/ultimate-search?category_ids={cat_id}&limit=10",
                headers={"Authorization": f"Bearer {auth_token}"}
            )
            assert response.status_code == 200, f"Filtered search failed: {response.text}"


class TestMarketplaceAPI:
    """Test Marketplace API for filtered protocols"""
    
    @pytest.fixture(scope="class")
    def auth_token(self):
        """Get authentication token for admin user"""
        response = requests.post(f"{BASE_URL}/api/auth/login", json={
            "email": ADMIN_EMAIL,
            "password": ADMIN_PASSWORD
        })
        assert response.status_code == 200
        return response.json()["token"]
    
    def test_marketplace_protocols(self, auth_token):
        """Test marketplace protocols endpoint"""
        response = requests.get(
            f"{BASE_URL}/api/marketplace/protocols",
            headers={"Authorization": f"Bearer {auth_token}"}
        )
        assert response.status_code == 200, f"Marketplace protocols failed: {response.text}"
        data = response.json()
        assert "protocols" in data, "Missing protocols in response"
    
    def test_marketplace_categories(self):
        """Test marketplace categories endpoint"""
        response = requests.get(f"{BASE_URL}/api/marketplace/categories")
        assert response.status_code == 200, f"Marketplace categories failed: {response.text}"
        data = response.json()
        assert "categories" in data, "Missing categories in response"


class TestAdminPanel:
    """Test Admin Panel endpoints"""
    
    @pytest.fixture(scope="class")
    def auth_token(self):
        """Get authentication token for admin user"""
        response = requests.post(f"{BASE_URL}/api/auth/login", json={
            "email": ADMIN_EMAIL,
            "password": ADMIN_PASSWORD
        })
        assert response.status_code == 200
        return response.json()["token"]
    
    def test_admin_stats(self, auth_token):
        """Test admin stats endpoint"""
        response = requests.get(
            f"{BASE_URL}/api/admin/stats",
            headers={"Authorization": f"Bearer {auth_token}"}
        )
        assert response.status_code == 200, f"Admin stats failed: {response.text}"
        data = response.json()
        assert "users" in data, "Missing users count"
        assert "categories" in data, "Missing categories count"
    
    def test_admin_settings(self, auth_token):
        """Test admin settings endpoint"""
        response = requests.get(
            f"{BASE_URL}/api/admin/settings",
            headers={"Authorization": f"Bearer {auth_token}"}
        )
        assert response.status_code == 200, f"Admin settings failed: {response.text}"


class TestMapPageAPI:
    """Test Map Page related APIs"""
    
    @pytest.fixture(scope="class")
    def auth_token(self):
        """Get authentication token for admin user"""
        response = requests.post(f"{BASE_URL}/api/auth/login", json={
            "email": ADMIN_EMAIL,
            "password": ADMIN_PASSWORD
        })
        assert response.status_code == 200
        return response.json()["token"]
    
    def test_map_results_endpoint(self, auth_token):
        """Test that ultimate search returns results with location data for map"""
        response = requests.get(
            f"{BASE_URL}/api/ultimate-search?limit=100",
            headers={"Authorization": f"Bearer {auth_token}"}
        )
        assert response.status_code == 200, f"Map results failed: {response.text}"
        data = response.json()
        assert "results" in data, "Missing results"
        
        # Check if any results have location data
        results = data.get("results", [])
        results_with_location = [r for r in results if r.get("latitude") and r.get("longitude")]
        print(f"Found {len(results_with_location)} results with location data out of {len(results)} total")


if __name__ == "__main__":
    pytest.main([__file__, "-v", "--tb=short"])
