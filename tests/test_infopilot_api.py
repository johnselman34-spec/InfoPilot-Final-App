"""
InfoPilot Explorer API Tests
Tests for: Auth, Search, Protocol, Newsletter, Book Promo, Categories, Collation
"""
import pytest
import requests
import os

BASE_URL = "https://infopilot-explorer-3.preview.emergentagent.com"

# Test credentials
ADMIN_EMAIL = "john@infojet.com"
ADMIN_PASSWORD = "password123"

class TestHealthCheck:
    """Health check tests - run first"""
    
    def test_api_health(self):
        """Test API health endpoint"""
        response = requests.get(f"{BASE_URL}/api/health")
        assert response.status_code == 200
        data = response.json()
        assert data["status"] == "healthy"
        print(f"✓ Health check passed: {data}")
    
    def test_api_root(self):
        """Test API root endpoint"""
        response = requests.get(f"{BASE_URL}/api/")
        assert response.status_code == 200
        data = response.json()
        assert "InfoPilot" in data.get("message", "")
        print(f"✓ Root endpoint: {data}")


class TestAuthentication:
    """Authentication endpoint tests"""
    
    def test_login_admin_success(self):
        """Test admin login with valid credentials"""
        response = requests.post(f"{BASE_URL}/api/auth/login", json={
            "email": ADMIN_EMAIL,
            "password": ADMIN_PASSWORD
        })
        assert response.status_code == 200, f"Login failed: {response.text}"
        data = response.json()
        assert "token" in data
        assert "user" in data
        assert data["user"]["email"] == ADMIN_EMAIL
        assert data["user"]["is_admin"] == True
        print(f"✓ Admin login successful: {data['user']['username']}")
        return data["token"]
    
    def test_login_invalid_credentials(self):
        """Test login with invalid credentials"""
        response = requests.post(f"{BASE_URL}/api/auth/login", json={
            "email": "wrong@example.com",
            "password": "wrongpass"
        })
        assert response.status_code == 401
        print("✓ Invalid credentials rejected correctly")
    
    def test_auth_me_with_token(self):
        """Test /auth/me endpoint with valid token"""
        # First login
        login_res = requests.post(f"{BASE_URL}/api/auth/login", json={
            "email": ADMIN_EMAIL,
            "password": ADMIN_PASSWORD
        })
        token = login_res.json()["token"]
        
        # Then get user info
        response = requests.get(f"{BASE_URL}/api/auth/me", headers={
            "Authorization": f"Bearer {token}"
        })
        assert response.status_code == 200
        data = response.json()
        assert data["email"] == ADMIN_EMAIL
        assert data["is_admin"] == True
        print(f"✓ Auth/me returned user: {data['username']}")
    
    def test_auth_me_without_token(self):
        """Test /auth/me endpoint without token"""
        response = requests.get(f"{BASE_URL}/api/auth/me")
        assert response.status_code == 401
        print("✓ Unauthorized access rejected correctly")


class TestBookPromotion:
    """Book promotion endpoint tests"""
    
    def test_get_book_promo(self):
        """Test book promotion data endpoint"""
        response = requests.get(f"{BASE_URL}/api/book-promo")
        assert response.status_code == 200
        data = response.json()
        
        # Verify book data
        assert data["title"] == "Letters to Evelyn"
        assert data["author"] == "John Selman"
        assert data["price"] == "$2.99"
        assert data["review_count"] == 19
        assert "Divine Zape" in data["featured_review"]["reviewer"]
        assert len(data["images"]) == 4
        
        # Verify images are valid URLs
        for img in data["images"]:
            assert img.startswith("https://")
            assert "Letters%20to%20Evelyn" in img
        
        print(f"✓ Book promo data: {data['title']} by {data['author']}, {len(data['images'])} images")


class TestProtocolParser:
    """Protocol parsing and matching tests"""
    
    @pytest.fixture
    def auth_token(self):
        """Get auth token for protected endpoints"""
        response = requests.post(f"{BASE_URL}/api/auth/login", json={
            "email": ADMIN_EMAIL,
            "password": ADMIN_PASSWORD
        })
        return response.json()["token"]
    
    def test_protocol_validate_simple(self):
        """Test simple protocol validation"""
        response = requests.post(f"{BASE_URL}/api/protocol/validate", json={
            "protocol": "(civil war or battle)"
        })
        assert response.status_code == 200
        data = response.json()
        assert data["valid"] == True
        assert len(data["groups"]) == 1
        print(f"✓ Protocol validation: {data}")
    
    def test_protocol_validate_complex(self):
        """Test complex protocol with modifiers"""
        response = requests.post(f"{BASE_URL}/api/protocol/validate", json={
            "protocol": "(William or Gamble)+ & (civil war or general) & (confederate)^"
        })
        assert response.status_code == 200
        data = response.json()
        assert data["valid"] == True
        assert len(data["groups"]) == 3
        print(f"✓ Complex protocol validation: {len(data['groups'])} groups")
    
    def test_protocol_debug_william_gamble(self, auth_token):
        """Test protocol debug for 'William Gamble civil war general'"""
        test_text = "William Gamble was a Union Army general during the American Civil War. He commanded cavalry forces at Gettysburg."
        protocol = "(William or Gamble)+ & (civil war or general)"
        
        response = requests.post(f"{BASE_URL}/api/protocol/debug", 
            json={"text": test_text, "protocol": protocol},
            headers={"Authorization": f"Bearer {auth_token}"}
        )
        assert response.status_code == 200
        data = response.json()
        assert data["matched"] == True
        print(f"✓ Protocol debug for William Gamble: matched={data['matched']}")
        print(f"  Details: {data['match_details']}")


class TestSearch:
    """Search functionality tests"""
    
    @pytest.fixture
    def auth_token(self):
        """Get auth token for protected endpoints"""
        response = requests.post(f"{BASE_URL}/api/auth/login", json={
            "email": ADMIN_EMAIL,
            "password": ADMIN_PASSWORD
        })
        return response.json()["token"]
    
    def test_search_william_gamble(self, auth_token):
        """Test search for 'William Gamble civil war general'"""
        response = requests.post(f"{BASE_URL}/api/search",
            json={"query": "William Gamble civil war general"},
            headers={"Authorization": f"Bearer {auth_token}"},
            timeout=30
        )
        assert response.status_code == 200
        data = response.json()
        assert "results" in data
        assert data["total"] > 0
        print(f"✓ Search returned {data['total']} results for 'William Gamble civil war general'")
        
        # Check first result has expected fields
        if data["results"]:
            first = data["results"][0]
            assert "url" in first
            assert "title" in first
            print(f"  First result: {first.get('title', 'N/A')[:60]}...")
    
    def test_search_blocked_content(self, auth_token):
        """Test that blocked content is rejected"""
        response = requests.post(f"{BASE_URL}/api/search",
            json={"query": "child exploitation"},
            headers={"Authorization": f"Bearer {auth_token}"}
        )
        assert response.status_code == 400
        print("✓ Blocked content correctly rejected")


class TestCategories:
    """Category CRUD tests"""
    
    @pytest.fixture
    def auth_token(self):
        """Get auth token for protected endpoints"""
        response = requests.post(f"{BASE_URL}/api/auth/login", json={
            "email": ADMIN_EMAIL,
            "password": ADMIN_PASSWORD
        })
        return response.json()["token"]
    
    def test_create_category_with_protocol(self, auth_token):
        """Test creating a category with protocol"""
        response = requests.post(f"{BASE_URL}/api/categories",
            json={
                "name": "TEST_Civil_War_Generals",
                "protocol": "(civil war or general)+ & (confederate)^",
                "is_public": False
            },
            headers={"Authorization": f"Bearer {auth_token}"}
        )
        assert response.status_code == 200
        data = response.json()
        assert data["name"] == "TEST_Civil_War_Generals"
        assert "id" in data
        print(f"✓ Category created: {data['name']} (ID: {data['id']})")
        return data["id"]
    
    def test_get_categories(self, auth_token):
        """Test getting user categories"""
        response = requests.get(f"{BASE_URL}/api/categories",
            headers={"Authorization": f"Bearer {auth_token}"}
        )
        assert response.status_code == 200
        data = response.json()
        assert isinstance(data, list)
        print(f"✓ Retrieved {len(data)} categories")
    
    def test_delete_test_categories(self, auth_token):
        """Cleanup: Delete TEST_ prefixed categories"""
        # Get all categories
        response = requests.get(f"{BASE_URL}/api/categories",
            headers={"Authorization": f"Bearer {auth_token}"}
        )
        categories = response.json()
        
        deleted = 0
        for cat in categories:
            if cat["name"].startswith("TEST_"):
                del_res = requests.delete(f"{BASE_URL}/api/categories/{cat['id']}",
                    headers={"Authorization": f"Bearer {auth_token}"}
                )
                if del_res.status_code == 200:
                    deleted += 1
        
        print(f"✓ Cleaned up {deleted} test categories")


class TestCollation:
    """Collation (auto-categorization) tests"""
    
    @pytest.fixture
    def auth_token(self):
        """Get auth token for protected endpoints"""
        response = requests.post(f"{BASE_URL}/api/auth/login", json={
            "email": ADMIN_EMAIL,
            "password": ADMIN_PASSWORD
        })
        return response.json()["token"]
    
    def test_collate_results(self, auth_token):
        """Test collating search results into categories"""
        # First create a test category
        cat_res = requests.post(f"{BASE_URL}/api/categories",
            json={
                "name": "TEST_Collate_Category",
                "protocol": "(test or example)",
                "is_public": False
            },
            headers={"Authorization": f"Bearer {auth_token}"}
        )
        
        # Mock search results
        mock_results = [
            {"url": "https://example.com/test1", "title": "Test Article", "snippet": "This is a test example"},
            {"url": "https://example.com/test2", "title": "Another Test", "snippet": "Another example content"}
        ]
        
        response = requests.post(f"{BASE_URL}/api/collate",
            json={"search_results": mock_results},
            headers={"Authorization": f"Bearer {auth_token}"}
        )
        assert response.status_code == 200
        data = response.json()
        assert "collated_count" in data
        print(f"✓ Collation completed: {data['collated_count']} results collated")
        
        # Cleanup
        if cat_res.status_code == 200:
            cat_id = cat_res.json()["id"]
            requests.delete(f"{BASE_URL}/api/categories/{cat_id}",
                headers={"Authorization": f"Bearer {auth_token}"}
            )


class TestNewsletter:
    """Newsletter functionality tests (Admin only)"""
    
    @pytest.fixture
    def admin_token(self):
        """Get admin auth token"""
        response = requests.post(f"{BASE_URL}/api/auth/login", json={
            "email": ADMIN_EMAIL,
            "password": ADMIN_PASSWORD
        })
        return response.json()["token"]
    
    def test_generate_newsletter(self, admin_token):
        """Test newsletter generation"""
        response = requests.post(f"{BASE_URL}/api/newsletter/generate",
            headers={"Authorization": f"Bearer {admin_token}"},
            timeout=60  # AI generation may take time
        )
        assert response.status_code == 200
        data = response.json()
        assert "content" in data
        assert len(data["content"]) > 100  # Should have substantial content
        print(f"✓ Newsletter generated: {len(data['content'])} chars")
    
    def test_newsletter_history(self, admin_token):
        """Test getting newsletter history"""
        response = requests.get(f"{BASE_URL}/api/newsletter/history",
            headers={"Authorization": f"Bearer {admin_token}"}
        )
        assert response.status_code == 200
        data = response.json()
        assert isinstance(data, list)
        print(f"✓ Newsletter history: {len(data)} entries")
    
    def test_newsletter_requires_admin(self):
        """Test that newsletter endpoints require admin"""
        # Try without auth
        response = requests.post(f"{BASE_URL}/api/newsletter/generate")
        assert response.status_code == 401
        print("✓ Newsletter generation requires authentication")


class TestSubscription:
    """Subscription and payment tests"""
    
    def test_get_subscription_info(self):
        """Test getting subscription info (public endpoint)"""
        response = requests.get(f"{BASE_URL}/api/subscription-info")
        assert response.status_code == 200
        data = response.json()
        assert "subscription_price" in data
        assert "paypal_link" in data
        print(f"✓ Subscription info: ${data['subscription_price']}")
    
    @pytest.fixture
    def auth_token(self):
        """Get auth token"""
        response = requests.post(f"{BASE_URL}/api/auth/login", json={
            "email": ADMIN_EMAIL,
            "password": ADMIN_PASSWORD
        })
        return response.json()["token"]
    
    def test_get_payment_link(self, auth_token):
        """Test getting payment link"""
        response = requests.get(f"{BASE_URL}/api/payment/link",
            headers={"Authorization": f"Bearer {auth_token}"}
        )
        assert response.status_code == 200
        data = response.json()
        assert "payment_url" in data
        assert data["payment_url"].startswith("https://")
        print(f"✓ Payment link: {data['payment_url'][:50]}...")


class TestAdminEndpoints:
    """Admin-only endpoint tests"""
    
    @pytest.fixture
    def admin_token(self):
        """Get admin auth token"""
        response = requests.post(f"{BASE_URL}/api/auth/login", json={
            "email": ADMIN_EMAIL,
            "password": ADMIN_PASSWORD
        })
        return response.json()["token"]
    
    def test_get_admin_settings(self, admin_token):
        """Test getting admin settings"""
        response = requests.get(f"{BASE_URL}/api/admin/settings",
            headers={"Authorization": f"Bearer {admin_token}"}
        )
        assert response.status_code == 200
        data = response.json()
        assert isinstance(data, list)
        print(f"✓ Admin settings: {len(data)} settings retrieved")


if __name__ == "__main__":
    pytest.main([__file__, "-v", "--tb=short"])
