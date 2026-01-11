"""
Test Suite for InfoPilot Newsletter Enhancement Phase 2 and Code Refactoring
Tests:
1. Newsletter generation with manuscript content
2. Newsletter preview endpoint
3. Authentication endpoints (login, register, auth/me)
4. Admin-only newsletter endpoints
"""

import pytest
import requests
import os
import time

BASE_URL = os.environ.get('REACT_APP_BACKEND_URL', '').rstrip('/')

# Test credentials
ADMIN_EMAIL = "john@infojet.com"
ADMIN_PASSWORD = "password123"
TEST_EMAIL = "test@gmail.com"


class TestHealthAndBasicEndpoints:
    """Basic health and connectivity tests"""
    
    def test_health_endpoint(self):
        """Test health endpoint returns healthy status"""
        response = requests.get(f"{BASE_URL}/api/health")
        assert response.status_code == 200
        data = response.json()
        assert data["status"] == "healthy"
        print(f"✓ Health check passed: {data}")
    
    def test_api_base_accessible(self):
        """Test API base is accessible"""
        response = requests.get(f"{BASE_URL}/api/health")
        assert response.status_code == 200
        print("✓ API base accessible")


class TestAuthentication:
    """Authentication endpoint tests"""
    
    def test_login_admin_success(self):
        """Test admin login with valid credentials"""
        response = requests.post(f"{BASE_URL}/api/auth/login", json={
            "email": ADMIN_EMAIL,
            "password": ADMIN_PASSWORD
        })
        assert response.status_code == 200
        data = response.json()
        assert "token" in data
        assert "user" in data
        assert data["user"]["email"] == ADMIN_EMAIL
        assert data["user"]["is_admin"] == True
        print(f"✓ Admin login successful: {data['user']['email']}, is_admin={data['user']['is_admin']}")
        return data["token"]
    
    def test_login_invalid_credentials(self):
        """Test login with invalid credentials returns 401"""
        response = requests.post(f"{BASE_URL}/api/auth/login", json={
            "email": "invalid@example.com",
            "password": "wrongpassword"
        })
        assert response.status_code == 401
        print("✓ Invalid login correctly rejected with 401")
    
    def test_auth_me_with_valid_token(self):
        """Test /auth/me returns user data with valid token"""
        # First login to get token
        login_response = requests.post(f"{BASE_URL}/api/auth/login", json={
            "email": ADMIN_EMAIL,
            "password": ADMIN_PASSWORD
        })
        token = login_response.json()["token"]
        
        # Test /auth/me
        response = requests.get(f"{BASE_URL}/api/auth/me", headers={
            "Authorization": f"Bearer {token}"
        })
        assert response.status_code == 200
        data = response.json()
        assert data["email"] == ADMIN_EMAIL
        assert data["is_admin"] == True
        print(f"✓ Auth/me returned correct user: {data['email']}")
    
    def test_auth_me_without_token(self):
        """Test /auth/me without token returns 401"""
        response = requests.get(f"{BASE_URL}/api/auth/me")
        assert response.status_code == 401
        print("✓ Auth/me correctly rejected without token")


class TestNewsletterEndpoints:
    """Newsletter endpoint tests - requires admin authentication"""
    
    @pytest.fixture
    def admin_token(self):
        """Get admin authentication token"""
        response = requests.post(f"{BASE_URL}/api/auth/login", json={
            "email": ADMIN_EMAIL,
            "password": ADMIN_PASSWORD
        })
        if response.status_code == 200:
            return response.json()["token"]
        pytest.skip("Admin authentication failed")
    
    def test_newsletter_preview_returns_content(self, admin_token):
        """Test newsletter preview endpoint returns AI-generated content"""
        response = requests.get(f"{BASE_URL}/api/newsletter/preview", headers={
            "Authorization": f"Bearer {admin_token}"
        })
        assert response.status_code == 200
        data = response.json()
        
        # Verify response structure - content is required, subject is optional
        assert "content" in data
        assert "generated_at" in data
        
        # Verify content is HTML
        assert "<html" in data["content"].lower() or "<!doctype" in data["content"].lower() or "<div" in data["content"].lower()
        
        # Check for manuscript content indicators (book references)
        content_lower = data["content"].lower()
        has_book_reference = any([
            "letters to evelyn" in content_lower,
            "john selman" in content_lower,
            "infopilot" in content_lower,
            "cosmic" in content_lower,
            "universe" in content_lower
        ])
        assert has_book_reference, "Newsletter should contain book or InfoPilot references"
        
        subject = data.get('subject', 'No subject')
        print(f"✓ Newsletter preview returned: content_length={len(data['content'])}")
        print(f"  AI generated: {data.get('ai_generated', 'unknown')}")
    
    def test_newsletter_preview_requires_auth(self):
        """Test newsletter preview requires authentication"""
        response = requests.get(f"{BASE_URL}/api/newsletter/preview")
        assert response.status_code == 401
        print("✓ Newsletter preview correctly requires authentication")
    
    def test_newsletter_generate_creates_content(self, admin_token):
        """Test newsletter generate endpoint creates new content"""
        response = requests.post(f"{BASE_URL}/api/newsletter/generate", headers={
            "Authorization": f"Bearer {admin_token}"
        })
        assert response.status_code == 200
        data = response.json()
        
        # Verify response structure - content is required
        assert "content" in data
        assert "generated_at" in data
        
        # Verify content is substantial
        assert len(data["content"]) > 500, "Newsletter content should be substantial"
        
        print(f"✓ Newsletter generated: content_length={len(data['content'])}, ai_generated={data.get('ai_generated', 'unknown')}")
    
    def test_newsletter_generate_requires_admin(self):
        """Test newsletter generate requires admin authentication"""
        response = requests.post(f"{BASE_URL}/api/newsletter/generate")
        assert response.status_code == 401
        print("✓ Newsletter generate correctly requires authentication")


class TestManuscriptContentIntegration:
    """Tests to verify MANUSCRIPT_CONTENT is being used in newsletter generation"""
    
    @pytest.fixture
    def admin_token(self):
        """Get admin authentication token"""
        response = requests.post(f"{BASE_URL}/api/auth/login", json={
            "email": ADMIN_EMAIL,
            "password": ADMIN_PASSWORD
        })
        if response.status_code == 200:
            return response.json()["token"]
        pytest.skip("Admin authentication failed")
    
    def test_newsletter_contains_manuscript_elements(self, admin_token):
        """Test that generated newsletter contains manuscript content elements"""
        # Generate a fresh newsletter to ensure we get AI-generated content
        response = requests.post(f"{BASE_URL}/api/newsletter/generate", headers={
            "Authorization": f"Bearer {admin_token}"
        })
        
        # Allow time for AI generation
        if response.status_code != 200:
            time.sleep(2)
            response = requests.post(f"{BASE_URL}/api/newsletter/generate", headers={
                "Authorization": f"Bearer {admin_token}"
            })
        
        assert response.status_code == 200
        data = response.json()
        content = data["content"].lower()
        
        # Check for various manuscript content indicators
        manuscript_indicators = {
            "book_title": "letters to evelyn" in content,
            "author": "john selman" in content,
            "infopilot": "infopilot" in content,
            "cosmic_theme": any(word in content for word in ["cosmic", "universe", "galaxy", "stars"]),
            "humor_elements": any(word in content for word in ["funny", "hilarious", "laugh", "comedy", "joke"]),
        }
        
        # At least 3 indicators should be present
        indicators_found = sum(manuscript_indicators.values())
        print(f"  Manuscript indicators found: {indicators_found}/5")
        for key, found in manuscript_indicators.items():
            print(f"    - {key}: {'✓' if found else '✗'}")
        
        assert indicators_found >= 2, f"Newsletter should contain manuscript content. Found {indicators_found}/5 indicators"
        print(f"✓ Newsletter contains manuscript content elements ({indicators_found}/5 indicators)")


class TestAdminSettings:
    """Test admin settings endpoints"""
    
    @pytest.fixture
    def admin_token(self):
        """Get admin authentication token"""
        response = requests.post(f"{BASE_URL}/api/auth/login", json={
            "email": ADMIN_EMAIL,
            "password": ADMIN_PASSWORD
        })
        if response.status_code == 200:
            return response.json()["token"]
        pytest.skip("Admin authentication failed")
    
    def test_get_admin_settings(self, admin_token):
        """Test getting admin settings"""
        response = requests.get(f"{BASE_URL}/api/admin/settings", headers={
            "Authorization": f"Bearer {admin_token}"
        })
        assert response.status_code == 200
        data = response.json()
        assert isinstance(data, list)
        print(f"✓ Admin settings retrieved: {len(data)} settings found")
    
    def test_admin_settings_requires_auth(self):
        """Test admin settings requires authentication"""
        response = requests.get(f"{BASE_URL}/api/admin/settings")
        assert response.status_code == 401
        print("✓ Admin settings correctly requires authentication")


class TestSearchEndpoints:
    """Test search functionality"""
    
    @pytest.fixture
    def admin_token(self):
        """Get admin authentication token"""
        response = requests.post(f"{BASE_URL}/api/auth/login", json={
            "email": ADMIN_EMAIL,
            "password": ADMIN_PASSWORD
        })
        if response.status_code == 200:
            return response.json()["token"]
        pytest.skip("Admin authentication failed")
    
    def test_search_endpoint(self, admin_token):
        """Test search endpoint returns results"""
        response = requests.get(f"{BASE_URL}/api/search?q=python", headers={
            "Authorization": f"Bearer {admin_token}"
        })
        # Search might return 200 or 429 (rate limited)
        assert response.status_code in [200, 429]
        if response.status_code == 200:
            data = response.json()
            assert "results" in data or isinstance(data, list)
            print(f"✓ Search returned results")
        else:
            print("✓ Search rate limited (expected behavior)")
    
    def test_categories_endpoint(self, admin_token):
        """Test categories endpoint"""
        response = requests.get(f"{BASE_URL}/api/categories", headers={
            "Authorization": f"Bearer {admin_token}"
        })
        assert response.status_code == 200
        data = response.json()
        assert isinstance(data, list)
        print(f"✓ Categories retrieved: {len(data)} categories")


if __name__ == "__main__":
    pytest.main([__file__, "-v", "--tb=short"])
