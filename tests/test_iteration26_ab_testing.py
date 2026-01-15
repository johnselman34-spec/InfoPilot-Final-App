"""
Iteration 26 - A/B Testing System Tests
Tests for:
1. GET /api/ab-testing/tests - List active tests
2. GET /api/ab-testing/variant/{test_name} - Get assigned variant
3. GET /api/ab-testing/variants/batch - Get multiple variants at once
4. POST /api/ab-testing/event - Track impression/click/conversion events
5. GET /api/ab-testing/results/{test_name} - Get test analytics (admin)
6. GET /api/ab-testing/dashboard - Get all test summaries (admin)
7. Documentation files verification
"""
import pytest
import requests
import os
import uuid

BASE_URL = os.environ.get('REACT_APP_BACKEND_URL', '').rstrip('/')

# Test credentials
ADMIN_EMAIL = "jjspilot24@gmail.com"
ADMIN_PASSWORD = "InfoPilot2024!"

# Default A/B tests that should exist
DEFAULT_TESTS = [
    "book_promo_headline",
    "book_promo_cta_button",
    "search_cta_style",
    "marketplace_cta",
    "signup_incentive"
]


@pytest.fixture(scope="module")
def admin_token():
    """Get admin authentication token"""
    response = requests.post(f"{BASE_URL}/api/auth/login", json={
        "email": ADMIN_EMAIL,
        "password": ADMIN_PASSWORD
    })
    if response.status_code == 200:
        return response.json().get("token")
    pytest.skip(f"Admin authentication failed: {response.status_code}")


@pytest.fixture
def session_id():
    """Generate unique session ID for testing"""
    return f"test_session_{uuid.uuid4().hex[:12]}"


class TestABTestingPublicEndpoints:
    """Tests for public A/B testing endpoints (no auth required)"""
    
    def test_get_active_tests(self):
        """GET /api/ab-testing/tests returns list of active tests"""
        response = requests.get(f"{BASE_URL}/api/ab-testing/tests")
        
        assert response.status_code == 200
        data = response.json()
        
        # Verify response structure
        assert "tests" in data
        assert "source" in data
        assert isinstance(data["tests"], list)
        
        # Verify default tests are present
        test_names = [t["name"] for t in data["tests"]]
        for default_test in DEFAULT_TESTS:
            assert default_test in test_names, f"Default test '{default_test}' not found"
        
        # Verify test structure
        for test in data["tests"]:
            assert "id" in test
            assert "name" in test
            assert "target_element" in test
            assert "variant_count" in test
            assert test["variant_count"] > 0
    
    def test_get_variant_book_promo_headline(self, session_id):
        """GET /api/ab-testing/variant/book_promo_headline returns assigned variant"""
        response = requests.get(
            f"{BASE_URL}/api/ab-testing/variant/book_promo_headline",
            headers={"X-Session-ID": session_id}
        )
        
        assert response.status_code == 200
        data = response.json()
        
        # Verify response structure
        assert data["test_name"] == "book_promo_headline"
        assert "variant_id" in data
        assert data["variant_id"] in ["A", "B", "C", "D"]
        assert "variant_name" in data
        assert "content" in data
        assert "user_hash" in data
        
        # Verify content structure for headline test
        content = data["content"]
        assert "headline" in content
        assert "subtext" in content
    
    def test_get_variant_book_promo_cta(self, session_id):
        """GET /api/ab-testing/variant/book_promo_cta_button returns CTA variant"""
        response = requests.get(
            f"{BASE_URL}/api/ab-testing/variant/book_promo_cta_button",
            headers={"X-Session-ID": session_id}
        )
        
        assert response.status_code == 200
        data = response.json()
        
        assert data["test_name"] == "book_promo_cta_button"
        assert data["variant_id"] in ["A", "B", "C"]
        
        # Verify CTA content structure
        content = data["content"]
        assert "text" in content
        assert "style" in content
    
    def test_get_variant_consistency(self, session_id):
        """Same session ID should get same variant (hash-based consistency)"""
        # Make multiple requests with same session ID
        variants = []
        for _ in range(3):
            response = requests.get(
                f"{BASE_URL}/api/ab-testing/variant/book_promo_headline",
                headers={"X-Session-ID": session_id}
            )
            assert response.status_code == 200
            variants.append(response.json()["variant_id"])
        
        # All variants should be the same
        assert len(set(variants)) == 1, "Variant assignment should be consistent for same session"
    
    def test_get_variant_not_found(self, session_id):
        """GET /api/ab-testing/variant/{invalid} returns 404"""
        response = requests.get(
            f"{BASE_URL}/api/ab-testing/variant/nonexistent_test",
            headers={"X-Session-ID": session_id}
        )
        
        assert response.status_code == 404
        assert "not found" in response.json()["detail"].lower()
    
    def test_get_batch_variants(self, session_id):
        """GET /api/ab-testing/variants/batch returns multiple variants at once"""
        test_names = "book_promo_headline,book_promo_cta_button,search_cta_style"
        
        response = requests.get(
            f"{BASE_URL}/api/ab-testing/variants/batch?test_names={test_names}",
            headers={"X-Session-ID": session_id}
        )
        
        assert response.status_code == 200
        data = response.json()
        
        # Verify response structure
        assert "variants" in data
        assert "user_hash" in data
        
        variants = data["variants"]
        assert "book_promo_headline" in variants
        assert "book_promo_cta_button" in variants
        assert "search_cta_style" in variants
        
        # Verify each variant has required fields
        for test_name, variant in variants.items():
            assert "variant_id" in variant
            assert "content" in variant
    
    def test_get_batch_variants_partial(self, session_id):
        """GET /api/ab-testing/variants/batch handles mix of valid/invalid tests"""
        test_names = "book_promo_headline,invalid_test,marketplace_cta"
        
        response = requests.get(
            f"{BASE_URL}/api/ab-testing/variants/batch?test_names={test_names}",
            headers={"X-Session-ID": session_id}
        )
        
        assert response.status_code == 200
        data = response.json()
        
        variants = data["variants"]
        # Valid tests should be present
        assert "book_promo_headline" in variants
        assert "marketplace_cta" in variants
        # Invalid test should not be present
        assert "invalid_test" not in variants


class TestABTestingEventTracking:
    """Tests for A/B testing event tracking"""
    
    def test_track_impression_event(self, session_id):
        """POST /api/ab-testing/event tracks impression event"""
        response = requests.post(
            f"{BASE_URL}/api/ab-testing/event",
            headers={"X-Session-ID": session_id},
            json={
                "test_id": "book_promo_headline",
                "variant_id": "A",
                "event_type": "impression",
                "metadata": {"page": "homepage"}
            }
        )
        
        assert response.status_code == 200
        data = response.json()
        assert data["success"] is True
        assert data["tracked"] == "impression"
    
    def test_track_click_event(self, session_id):
        """POST /api/ab-testing/event tracks click event"""
        response = requests.post(
            f"{BASE_URL}/api/ab-testing/event",
            headers={"X-Session-ID": session_id},
            json={
                "test_id": "book_promo_cta_button",
                "variant_id": "B",
                "event_type": "click",
                "metadata": {"button_text": "BUY NOW"}
            }
        )
        
        assert response.status_code == 200
        data = response.json()
        assert data["success"] is True
        assert data["tracked"] == "click"
    
    def test_track_conversion_event(self, session_id):
        """POST /api/ab-testing/event tracks conversion event"""
        response = requests.post(
            f"{BASE_URL}/api/ab-testing/event",
            headers={"X-Session-ID": session_id},
            json={
                "test_id": "book_promo_headline",
                "variant_id": "C",
                "event_type": "conversion",
                "metadata": {"purchase_amount": 2.99}
            }
        )
        
        assert response.status_code == 200
        data = response.json()
        assert data["success"] is True
        assert data["tracked"] == "conversion"
    
    def test_track_hover_event(self, session_id):
        """POST /api/ab-testing/event tracks hover event"""
        response = requests.post(
            f"{BASE_URL}/api/ab-testing/event",
            headers={"X-Session-ID": session_id},
            json={
                "test_id": "marketplace_cta",
                "variant_id": "A",
                "event_type": "hover"
            }
        )
        
        assert response.status_code == 200
        data = response.json()
        assert data["success"] is True
        assert data["tracked"] == "hover"
    
    def test_track_invalid_event_type(self, session_id):
        """POST /api/ab-testing/event rejects invalid event type"""
        response = requests.post(
            f"{BASE_URL}/api/ab-testing/event",
            headers={"X-Session-ID": session_id},
            json={
                "test_id": "book_promo_headline",
                "variant_id": "A",
                "event_type": "invalid_event"
            }
        )
        
        assert response.status_code == 400
        assert "Invalid event type" in response.json()["detail"]


class TestABTestingAdminEndpoints:
    """Tests for admin-only A/B testing endpoints"""
    
    def test_get_results_requires_auth(self):
        """GET /api/ab-testing/results/{test_name} requires authentication"""
        response = requests.get(f"{BASE_URL}/api/ab-testing/results/book_promo_headline")
        
        assert response.status_code == 401
    
    def test_get_results_requires_admin(self, admin_token):
        """GET /api/ab-testing/results/{test_name} returns test analytics for admin"""
        response = requests.get(
            f"{BASE_URL}/api/ab-testing/results/book_promo_headline?days=30",
            headers={"Authorization": f"Bearer {admin_token}"}
        )
        
        assert response.status_code == 200
        data = response.json()
        
        # Verify response structure
        assert data["test_name"] == "book_promo_headline"
        assert "description" in data
        assert "period_days" in data
        assert data["period_days"] == 30
        assert "variants" in data
        assert "total_impressions" in data
        assert "is_statistically_significant" in data
        assert "recommendation" in data
        
        # Verify variant structure
        for variant in data["variants"]:
            assert "variant_id" in variant
            assert "variant_name" in variant
            assert "impressions" in variant
            assert "clicks" in variant
            assert "conversions" in variant
            assert "click_rate" in variant
            assert "conversion_rate" in variant
    
    def test_get_results_not_found(self, admin_token):
        """GET /api/ab-testing/results/{invalid} returns 404"""
        response = requests.get(
            f"{BASE_URL}/api/ab-testing/results/nonexistent_test",
            headers={"Authorization": f"Bearer {admin_token}"}
        )
        
        assert response.status_code == 404
    
    def test_get_dashboard_requires_auth(self):
        """GET /api/ab-testing/dashboard requires authentication"""
        response = requests.get(f"{BASE_URL}/api/ab-testing/dashboard")
        
        assert response.status_code == 401
    
    def test_get_dashboard(self, admin_token):
        """GET /api/ab-testing/dashboard returns all test summaries for admin"""
        response = requests.get(
            f"{BASE_URL}/api/ab-testing/dashboard?days=30",
            headers={"Authorization": f"Bearer {admin_token}"}
        )
        
        assert response.status_code == 200
        data = response.json()
        
        # Verify response structure
        assert "period_days" in data
        assert data["period_days"] == 30
        assert "tests" in data
        assert "active_tests" in data
        assert "total_impressions" in data
        assert "total_conversions" in data
        assert "overall_conversion_rate" in data
        
        # Verify tests list
        assert isinstance(data["tests"], list)
        assert len(data["tests"]) >= len(DEFAULT_TESTS)
        
        # Verify test summary structure
        for test in data["tests"]:
            assert "name" in test
            assert "description" in test
            assert "target_element" in test
            assert "is_active" in test
            assert "variant_count" in test
            assert "total_events" in test
    
    def test_get_dashboard_different_periods(self, admin_token):
        """GET /api/ab-testing/dashboard works with different time periods"""
        for days in [7, 30, 90]:
            response = requests.get(
                f"{BASE_URL}/api/ab-testing/dashboard?days={days}",
                headers={"Authorization": f"Bearer {admin_token}"}
            )
            
            assert response.status_code == 200
            data = response.json()
            assert data["period_days"] == days


class TestDocumentationFiles:
    """Tests for documentation files existence and content"""
    
    def test_webstore_submission_guide_exists(self):
        """WEBSTORE_SUBMISSION_GUIDE.md exists and has content"""
        guide_path = "/app/browser-extension/WEBSTORE_SUBMISSION_GUIDE.md"
        
        assert os.path.exists(guide_path), f"File not found: {guide_path}"
        
        with open(guide_path, 'r') as f:
            content = f.read()
        
        # Verify key sections exist
        assert "Chrome Extension Web Store Submission Guide" in content
        assert "Prerequisites" in content
        assert "Google Developer Account" in content
        assert "Step-by-Step Submission Process" in content
        assert "Privacy Practices" in content
        assert "Post-Submission" in content
        assert len(content) > 3000, "Guide should be comprehensive"
    
    def test_mobile_build_guide_exists(self):
        """MOBILE_BUILD_GUIDE.md exists and has content"""
        guide_path = "/app/frontend/MOBILE_BUILD_GUIDE.md"
        
        assert os.path.exists(guide_path), f"File not found: {guide_path}"
        
        with open(guide_path, 'r') as f:
            content = f.read()
        
        # Verify key sections exist
        assert "Mobile App Build Guide" in content
        assert "Prerequisites" in content
        assert "Android Build" in content
        assert "iOS Build" in content
        assert "Capacitor" in content
        assert "Publishing" in content
        assert "Troubleshooting" in content
        assert len(content) > 5000, "Guide should be comprehensive"


class TestDefaultABTests:
    """Tests to verify all default A/B tests are properly configured"""
    
    def test_all_default_tests_exist(self):
        """All 5 default tests should be available"""
        response = requests.get(f"{BASE_URL}/api/ab-testing/tests")
        
        assert response.status_code == 200
        data = response.json()
        
        test_names = [t["name"] for t in data["tests"]]
        
        for expected_test in DEFAULT_TESTS:
            assert expected_test in test_names, f"Missing default test: {expected_test}"
    
    def test_book_promo_headline_variants(self, session_id):
        """book_promo_headline has 4 variants (A, B, C, D)"""
        response = requests.get(f"{BASE_URL}/api/ab-testing/tests")
        data = response.json()
        
        headline_test = next((t for t in data["tests"] if t["name"] == "book_promo_headline"), None)
        assert headline_test is not None
        assert headline_test["variant_count"] == 4
    
    def test_book_promo_cta_variants(self, session_id):
        """book_promo_cta_button has 3 variants (A, B, C)"""
        response = requests.get(f"{BASE_URL}/api/ab-testing/tests")
        data = response.json()
        
        cta_test = next((t for t in data["tests"] if t["name"] == "book_promo_cta_button"), None)
        assert cta_test is not None
        assert cta_test["variant_count"] == 3
    
    def test_search_cta_style_variants(self, session_id):
        """search_cta_style has 2 variants (A, B)"""
        response = requests.get(f"{BASE_URL}/api/ab-testing/tests")
        data = response.json()
        
        search_test = next((t for t in data["tests"] if t["name"] == "search_cta_style"), None)
        assert search_test is not None
        assert search_test["variant_count"] == 2
    
    def test_marketplace_cta_variants(self, session_id):
        """marketplace_cta has 2 variants (A, B)"""
        response = requests.get(f"{BASE_URL}/api/ab-testing/tests")
        data = response.json()
        
        marketplace_test = next((t for t in data["tests"] if t["name"] == "marketplace_cta"), None)
        assert marketplace_test is not None
        assert marketplace_test["variant_count"] == 2
    
    def test_signup_incentive_variants(self, session_id):
        """signup_incentive has 3 variants (A, B, C)"""
        response = requests.get(f"{BASE_URL}/api/ab-testing/tests")
        data = response.json()
        
        signup_test = next((t for t in data["tests"] if t["name"] == "signup_incentive"), None)
        assert signup_test is not None
        assert signup_test["variant_count"] == 3


if __name__ == "__main__":
    pytest.main([__file__, "-v", "--tb=short"])
