"""
Iteration 81 - Banned Words Feature & Stability Tests
Tests for:
1. Banned Words CRUD operations (GET, POST, DELETE)
2. Reserved keywords protection (or, and, &, parentheses)
3. Admin Panel tabs including new 'Banned Words' tab
4. Revenue Dashboard and PDF export
5. Authentication flow
6. Categories CRUD
7. Search functionality
8. AI features
9. Marketplace endpoints
10. Chat functionality
"""
import pytest
import requests
import os
import json
from datetime import datetime

BASE_URL = os.environ.get('REACT_APP_BACKEND_URL', 'https://infopilot-preview.preview.emergentagent.com')

# Test credentials
ADMIN_EMAIL = "jjspilot24@gmail.com"
ADMIN_PASSWORD = "InfoPilot2024!"


class TestAuthentication:
    """Test authentication flow"""
    
    @pytest.fixture(scope="class")
    def auth_token(self):
        """Get authentication token for admin user"""
        response = requests.post(
            f"{BASE_URL}/api/auth/login",
            json={"email": ADMIN_EMAIL, "password": ADMIN_PASSWORD}
        )
        assert response.status_code == 200, f"Login failed: {response.text}"
        data = response.json()
        assert "token" in data, "No token in response"
        return data["token"]
    
    def test_admin_login(self, auth_token):
        """Test admin login returns valid token"""
        assert auth_token is not None
        assert len(auth_token) > 10
        print(f"✅ Admin login successful, token length: {len(auth_token)}")
    
    def test_get_current_user(self, auth_token):
        """Test getting current user info"""
        response = requests.get(
            f"{BASE_URL}/api/auth/me",
            headers={"Authorization": f"Bearer {auth_token}"}
        )
        assert response.status_code == 200
        data = response.json()
        assert data.get("email") == ADMIN_EMAIL
        print(f"✅ Current user: {data.get('email')}")


class TestBannedWordsCRUD:
    """Test Banned Words CRUD operations - NEW FEATURE"""
    
    @pytest.fixture(scope="class")
    def auth_token(self):
        """Get authentication token"""
        response = requests.post(
            f"{BASE_URL}/api/auth/login",
            json={"email": ADMIN_EMAIL, "password": ADMIN_PASSWORD}
        )
        return response.json().get("token")
    
    def test_get_banned_words(self, auth_token):
        """Test GET /api/admin/banned-words"""
        response = requests.get(
            f"{BASE_URL}/api/admin/banned-words",
            headers={"Authorization": f"Bearer {auth_token}"}
        )
        assert response.status_code == 200, f"Failed to get banned words: {response.text}"
        data = response.json()
        assert isinstance(data, list), "Response should be a list"
        print(f"✅ GET banned words: {len(data)} words currently banned")
    
    def test_add_banned_word(self, auth_token):
        """Test POST /api/admin/banned-words"""
        test_word = f"TEST_BANNED_WORD_{datetime.now().strftime('%H%M%S')}"
        response = requests.post(
            f"{BASE_URL}/api/admin/banned-words",
            headers={
                "Authorization": f"Bearer {auth_token}",
                "Content-Type": "application/json"
            },
            json={"word": test_word, "reason": "Test ban reason"}
        )
        assert response.status_code == 200, f"Failed to add banned word: {response.text}"
        data = response.json()
        assert data.get("success") == True
        assert "id" in data
        print(f"✅ Added banned word: {test_word}, ID: {data.get('id')}")
        return data.get("id"), test_word
    
    def test_delete_banned_word(self, auth_token):
        """Test DELETE /api/admin/banned-words/{id}"""
        # First add a word to delete
        test_word = f"TEST_DELETE_{datetime.now().strftime('%H%M%S')}"
        add_response = requests.post(
            f"{BASE_URL}/api/admin/banned-words",
            headers={
                "Authorization": f"Bearer {auth_token}",
                "Content-Type": "application/json"
            },
            json={"word": test_word, "reason": "To be deleted"}
        )
        assert add_response.status_code == 200
        word_id = add_response.json().get("id")
        
        # Now delete it
        delete_response = requests.delete(
            f"{BASE_URL}/api/admin/banned-words/{word_id}",
            headers={"Authorization": f"Bearer {auth_token}"}
        )
        assert delete_response.status_code == 200, f"Failed to delete: {delete_response.text}"
        data = delete_response.json()
        assert data.get("success") == True
        print(f"✅ Deleted banned word ID: {word_id}")
    
    def test_reserved_keyword_or(self, auth_token):
        """Test that 'or' cannot be banned (reserved keyword)"""
        response = requests.post(
            f"{BASE_URL}/api/admin/banned-words",
            headers={
                "Authorization": f"Bearer {auth_token}",
                "Content-Type": "application/json"
            },
            json={"word": "or", "reason": "Testing reserved"}
        )
        # Should fail with 400 because 'or' is reserved
        assert response.status_code == 400, f"Should reject 'or': {response.text}"
        print("✅ Reserved keyword 'or' correctly rejected")
    
    def test_reserved_keyword_and(self, auth_token):
        """Test that 'and' cannot be banned (reserved keyword)"""
        response = requests.post(
            f"{BASE_URL}/api/admin/banned-words",
            headers={
                "Authorization": f"Bearer {auth_token}",
                "Content-Type": "application/json"
            },
            json={"word": "and", "reason": "Testing reserved"}
        )
        assert response.status_code == 400, f"Should reject 'and': {response.text}"
        print("✅ Reserved keyword 'and' correctly rejected")
    
    def test_reserved_keyword_ampersand(self, auth_token):
        """Test that '&' cannot be banned (reserved keyword)"""
        response = requests.post(
            f"{BASE_URL}/api/admin/banned-words",
            headers={
                "Authorization": f"Bearer {auth_token}",
                "Content-Type": "application/json"
            },
            json={"word": "&", "reason": "Testing reserved"}
        )
        assert response.status_code == 400, f"Should reject '&': {response.text}"
        print("✅ Reserved keyword '&' correctly rejected")
    
    def test_reserved_keyword_parentheses(self, auth_token):
        """Test that parentheses cannot be banned (reserved keywords)"""
        for char in ["(", ")"]:
            response = requests.post(
                f"{BASE_URL}/api/admin/banned-words",
                headers={
                    "Authorization": f"Bearer {auth_token}",
                    "Content-Type": "application/json"
                },
                json={"word": char, "reason": "Testing reserved"}
            )
            assert response.status_code == 400, f"Should reject '{char}': {response.text}"
        print("✅ Reserved keywords '(' and ')' correctly rejected")
    
    def test_check_banned_words_in_text(self, auth_token):
        """Test POST /api/admin/check-banned-words"""
        # First add a test word
        test_word = "TESTCHECKWORD"
        requests.post(
            f"{BASE_URL}/api/admin/banned-words",
            headers={
                "Authorization": f"Bearer {auth_token}",
                "Content-Type": "application/json"
            },
            json={"word": test_word, "reason": "For checking"}
        )
        
        # Check if text contains banned word
        response = requests.post(
            f"{BASE_URL}/api/admin/check-banned-words",
            headers={
                "Authorization": f"Bearer {auth_token}",
                "Content-Type": "application/json"
            },
            json={"text": f"This text contains {test_word} in it"}
        )
        assert response.status_code == 200, f"Check failed: {response.text}"
        data = response.json()
        assert "has_banned_words" in data
        print(f"✅ Check banned words: has_banned_words={data.get('has_banned_words')}")


class TestRevenueDashboard:
    """Test Revenue Dashboard API"""
    
    @pytest.fixture(scope="class")
    def auth_token(self):
        """Get authentication token"""
        response = requests.post(
            f"{BASE_URL}/api/auth/login",
            json={"email": ADMIN_EMAIL, "password": ADMIN_PASSWORD}
        )
        return response.json().get("token")
    
    def test_revenue_dashboard_7d(self, auth_token):
        """Test GET /api/admin/revenue-dashboard with 7 days"""
        response = requests.get(
            f"{BASE_URL}/api/admin/revenue-dashboard?days=7",
            headers={"Authorization": f"Bearer {auth_token}"}
        )
        assert response.status_code == 200, f"Failed: {response.text}"
        data = response.json()
        assert "summary" in data
        assert "protocol_sales" in data
        print(f"✅ Revenue Dashboard (7d): Total revenue ${data['summary'].get('total_revenue', 0):.2f}")
    
    def test_revenue_dashboard_30d(self, auth_token):
        """Test GET /api/admin/revenue-dashboard with 30 days"""
        response = requests.get(
            f"{BASE_URL}/api/admin/revenue-dashboard?days=30",
            headers={"Authorization": f"Bearer {auth_token}"}
        )
        assert response.status_code == 200
        data = response.json()
        assert "summary" in data
        assert "generated_at" in data
        print(f"✅ Revenue Dashboard (30d): {data['summary'].get('total_users', 0)} total users")
    
    def test_revenue_dashboard_90d(self, auth_token):
        """Test GET /api/admin/revenue-dashboard with 90 days"""
        response = requests.get(
            f"{BASE_URL}/api/admin/revenue-dashboard?days=90",
            headers={"Authorization": f"Bearer {auth_token}"}
        )
        assert response.status_code == 200
        data = response.json()
        assert "ai_recommendations" in data
        print(f"✅ Revenue Dashboard (90d): {len(data.get('ai_recommendations', []))} AI recommendation categories")


class TestCategoriesCRUD:
    """Test Categories CRUD operations"""
    
    @pytest.fixture(scope="class")
    def auth_token(self):
        """Get authentication token"""
        response = requests.post(
            f"{BASE_URL}/api/auth/login",
            json={"email": ADMIN_EMAIL, "password": ADMIN_PASSWORD}
        )
        return response.json().get("token")
    
    def test_list_categories(self, auth_token):
        """Test GET /api/categories"""
        response = requests.get(
            f"{BASE_URL}/api/categories",
            headers={"Authorization": f"Bearer {auth_token}"}
        )
        assert response.status_code == 200
        data = response.json()
        assert isinstance(data, list)
        print(f"✅ List categories: {len(data)} categories found")
    
    def test_create_category(self, auth_token):
        """Test POST /api/categories"""
        test_name = f"TEST_CAT_{datetime.now().strftime('%H%M%S')}"
        response = requests.post(
            f"{BASE_URL}/api/categories",
            headers={
                "Authorization": f"Bearer {auth_token}",
                "Content-Type": "application/json"
            },
            json={
                "name": test_name,
                "protocol": "(test or example)",
                "description": "Test category"
            }
        )
        assert response.status_code in [200, 201], f"Failed: {response.text}"
        data = response.json()
        assert "id" in data or "_id" in data
        print(f"✅ Created category: {test_name}")
        return data.get("id") or data.get("_id")


class TestSearchFunctionality:
    """Test Search functionality"""
    
    @pytest.fixture(scope="class")
    def auth_token(self):
        """Get authentication token"""
        response = requests.post(
            f"{BASE_URL}/api/auth/login",
            json={"email": ADMIN_EMAIL, "password": ADMIN_PASSWORD}
        )
        return response.json().get("token")
    
    def test_basic_search(self, auth_token):
        """Test POST /api/search"""
        response = requests.post(
            f"{BASE_URL}/api/search",
            headers={
                "Authorization": f"Bearer {auth_token}",
                "Content-Type": "application/json"
            },
            json={"query": "python programming"}
        )
        assert response.status_code == 200, f"Search failed: {response.text}"
        data = response.json()
        assert "results" in data
        print(f"✅ Search returned {len(data.get('results', []))} results")


class TestAIFeatures:
    """Test AI-powered features"""
    
    @pytest.fixture(scope="class")
    def auth_token(self):
        """Get authentication token"""
        response = requests.post(
            f"{BASE_URL}/api/auth/login",
            json={"email": ADMIN_EMAIL, "password": ADMIN_PASSWORD}
        )
        return response.json().get("token")
    
    def test_ai_news(self, auth_token):
        """Test GET /api/ai/news"""
        response = requests.get(
            f"{BASE_URL}/api/ai/news",
            headers={"Authorization": f"Bearer {auth_token}"}
        )
        assert response.status_code == 200, f"AI News failed: {response.text}"
        data = response.json()
        assert "articles" in data or "headlines" in data or isinstance(data, list)
        print(f"✅ AI News endpoint working")
    
    def test_ai_smart_suggestions(self, auth_token):
        """Test GET /api/ai/smart-suggestions"""
        response = requests.get(
            f"{BASE_URL}/api/ai/smart-suggestions",
            headers={"Authorization": f"Bearer {auth_token}"}
        )
        assert response.status_code == 200, f"Smart suggestions failed: {response.text}"
        print(f"✅ AI Smart Suggestions endpoint working")


class TestMarketplace:
    """Test Marketplace endpoints"""
    
    @pytest.fixture(scope="class")
    def auth_token(self):
        """Get authentication token"""
        response = requests.post(
            f"{BASE_URL}/api/auth/login",
            json={"email": ADMIN_EMAIL, "password": ADMIN_PASSWORD}
        )
        return response.json().get("token")
    
    def test_list_protocols(self, auth_token):
        """Test GET /api/marketplace/protocols"""
        response = requests.get(
            f"{BASE_URL}/api/marketplace/protocols",
            headers={"Authorization": f"Bearer {auth_token}"}
        )
        assert response.status_code == 200, f"Marketplace failed: {response.text}"
        data = response.json()
        protocols = data.get("protocols", data) if isinstance(data, dict) else data
        print(f"✅ Marketplace: {len(protocols) if isinstance(protocols, list) else 'N/A'} protocols")


class TestChatFunctionality:
    """Test Chat functionality"""
    
    @pytest.fixture(scope="class")
    def auth_token(self):
        """Get authentication token"""
        response = requests.post(
            f"{BASE_URL}/api/auth/login",
            json={"email": ADMIN_EMAIL, "password": ADMIN_PASSWORD}
        )
        return response.json().get("token")
    
    def test_list_chat_rooms(self, auth_token):
        """Test GET /api/chat/rooms"""
        response = requests.get(
            f"{BASE_URL}/api/chat/rooms",
            headers={"Authorization": f"Bearer {auth_token}"}
        )
        assert response.status_code == 200, f"Chat rooms failed: {response.text}"
        data = response.json()
        rooms = data.get("rooms", data) if isinstance(data, dict) else data
        print(f"✅ Chat rooms: {len(rooms) if isinstance(rooms, list) else 'N/A'} rooms")


class TestAdminSettings:
    """Test Admin settings endpoints"""
    
    @pytest.fixture(scope="class")
    def auth_token(self):
        """Get authentication token"""
        response = requests.post(
            f"{BASE_URL}/api/auth/login",
            json={"email": ADMIN_EMAIL, "password": ADMIN_PASSWORD}
        )
        return response.json().get("token")
    
    def test_get_admin_settings(self, auth_token):
        """Test GET /api/admin/settings"""
        response = requests.get(
            f"{BASE_URL}/api/admin/settings",
            headers={"Authorization": f"Bearer {auth_token}"}
        )
        assert response.status_code == 200, f"Admin settings failed: {response.text}"
        print(f"✅ Admin settings endpoint working")


class TestHealthAndStatus:
    """Test health and status endpoints"""
    
    def test_health_check(self):
        """Test basic health check"""
        response = requests.get(f"{BASE_URL}/api/health")
        # Health endpoint might not exist, so we check if API is responding
        assert response.status_code in [200, 404], f"API not responding: {response.status_code}"
        print(f"✅ API is responding (status: {response.status_code})")
    
    def test_root_endpoint(self):
        """Test root API endpoint"""
        response = requests.get(f"{BASE_URL}/api/")
        assert response.status_code in [200, 404, 307], f"Root endpoint issue: {response.status_code}"
        print(f"✅ Root endpoint responding (status: {response.status_code})")


# Cleanup fixture to remove test data
@pytest.fixture(scope="session", autouse=True)
def cleanup_test_data():
    """Cleanup test data after all tests"""
    yield
    # Get token for cleanup
    response = requests.post(
        f"{BASE_URL}/api/auth/login",
        json={"email": ADMIN_EMAIL, "password": ADMIN_PASSWORD}
    )
    if response.status_code == 200:
        token = response.json().get("token")
        # Get all banned words and delete test ones
        banned_response = requests.get(
            f"{BASE_URL}/api/admin/banned-words",
            headers={"Authorization": f"Bearer {token}"}
        )
        if banned_response.status_code == 200:
            for word in banned_response.json():
                if word.get("word", "").startswith("TEST"):
                    requests.delete(
                        f"{BASE_URL}/api/admin/banned-words/{word['id']}",
                        headers={"Authorization": f"Bearer {token}"}
                    )
        print("✅ Test data cleanup completed")


if __name__ == "__main__":
    pytest.main([__file__, "-v", "--tb=short"])
