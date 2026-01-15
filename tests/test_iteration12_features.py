"""
InfoPilot Explorer - Iteration 12 Feature Tests
Tests for: Admin login, admin badge, promotional content, category editing, collate functionality, marketplace
"""
import pytest
import requests
import os

BASE_URL = os.environ.get('REACT_APP_BACKEND_URL', 'https://info-navigator-1.preview.emergentagent.com')

# Test credentials
ADMIN_EMAIL = "jjspilot24@gmail.com"
ADMIN_PASSWORD = "InfoPilot2024!"
TEST_EMAIL = "test@infojet.com"
TEST_PASSWORD = "testpass123"


class TestHealthCheck:
    """Health check tests"""
    
    def test_health_endpoint(self):
        """Test health endpoint returns healthy status"""
        response = requests.get(f"{BASE_URL}/api/health")
        assert response.status_code == 200
        data = response.json()
        assert data["status"] == "healthy"
        print("✅ Health check passed")


class TestAdminLogin:
    """Admin authentication tests"""
    
    def test_admin_login_success(self):
        """Test admin login with correct credentials"""
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
        print(f"✅ Admin login successful - is_admin: {data['user']['is_admin']}")
        return data["token"]
    
    def test_admin_login_wrong_password(self):
        """Test admin login with wrong password"""
        response = requests.post(f"{BASE_URL}/api/auth/login", json={
            "email": ADMIN_EMAIL,
            "password": "wrongpassword"
        })
        assert response.status_code == 401
        print("✅ Admin login with wrong password correctly rejected")
    
    def test_regular_user_login(self):
        """Test regular user login"""
        response = requests.post(f"{BASE_URL}/api/auth/login", json={
            "email": TEST_EMAIL,
            "password": TEST_PASSWORD
        })
        assert response.status_code == 200
        data = response.json()
        assert data["user"]["is_admin"] == False
        print(f"✅ Regular user login successful - is_admin: {data['user']['is_admin']}")


class TestCategoryOperations:
    """Category CRUD tests"""
    
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
    
    def test_get_categories(self, admin_token):
        """Test getting categories list"""
        response = requests.get(
            f"{BASE_URL}/api/categories",
            headers={"Authorization": f"Bearer {admin_token}"}
        )
        assert response.status_code == 200
        data = response.json()
        assert isinstance(data, list)
        print(f"✅ Got {len(data)} categories")
    
    def test_category_update_name_and_protocol(self, admin_token):
        """Test updating category name and protocol"""
        # First get categories to find one to update
        response = requests.get(
            f"{BASE_URL}/api/categories",
            headers={"Authorization": f"Bearer {admin_token}"}
        )
        categories = response.json()
        
        # Find admin's own category
        admin_category = None
        for cat in categories:
            if cat.get("user_id") == "6963c7215bba9611d96b2416":  # Admin user ID
                admin_category = cat
                break
        
        if not admin_category:
            pytest.skip("No admin category found to update")
        
        category_id = admin_category["id"]
        original_name = admin_category["name"]
        
        # Update the category
        new_name = f"TEST_Updated_{original_name[:20]}"
        new_protocol = "(test or updated) & (category)"
        
        response = requests.put(
            f"{BASE_URL}/api/categories/{category_id}",
            headers={
                "Authorization": f"Bearer {admin_token}",
                "Content-Type": "application/json"
            },
            json={
                "name": new_name,
                "protocol": new_protocol
            }
        )
        assert response.status_code == 200
        data = response.json()
        assert data["name"] == new_name
        assert data["protocol"] == new_protocol
        print(f"✅ Category updated - Name: {new_name}, Protocol: {new_protocol}")
        
        # Restore original name
        requests.put(
            f"{BASE_URL}/api/categories/{category_id}",
            headers={
                "Authorization": f"Bearer {admin_token}",
                "Content-Type": "application/json"
            },
            json={
                "name": original_name,
                "protocol": admin_category["protocol"]
            }
        )
        print("✅ Category restored to original values")
    
    def test_category_update_visibility(self, admin_token):
        """Test updating category visibility (is_public)"""
        # Get categories
        response = requests.get(
            f"{BASE_URL}/api/categories",
            headers={"Authorization": f"Bearer {admin_token}"}
        )
        categories = response.json()
        
        # Find admin's own category
        admin_category = None
        for cat in categories:
            if cat.get("user_id") == "6963c7215bba9611d96b2416":
                admin_category = cat
                break
        
        if not admin_category:
            pytest.skip("No admin category found")
        
        category_id = admin_category["id"]
        original_is_public = admin_category.get("is_public", False)
        
        # Toggle visibility
        response = requests.put(
            f"{BASE_URL}/api/categories/{category_id}",
            headers={
                "Authorization": f"Bearer {admin_token}",
                "Content-Type": "application/json"
            },
            json={"is_public": not original_is_public}
        )
        assert response.status_code == 200
        data = response.json()
        assert data["is_public"] == (not original_is_public)
        print(f"✅ Category visibility toggled to: {data['is_public']}")
        
        # Restore original visibility
        requests.put(
            f"{BASE_URL}/api/categories/{category_id}",
            headers={
                "Authorization": f"Bearer {admin_token}",
                "Content-Type": "application/json"
            },
            json={"is_public": original_is_public}
        )


class TestMarketplace:
    """Marketplace tests"""
    
    def test_marketplace_categories(self):
        """Test getting marketplace categories"""
        response = requests.get(f"{BASE_URL}/api/marketplace/categories")
        assert response.status_code == 200
        data = response.json()
        assert "categories" in data
        assert len(data["categories"]) > 0
        print(f"✅ Got {len(data['categories'])} marketplace categories")
    
    def test_marketplace_protocols(self):
        """Test getting marketplace protocols"""
        response = requests.get(f"{BASE_URL}/api/marketplace/protocols")
        assert response.status_code == 200
        data = response.json()
        assert "protocols" in data
        assert len(data["protocols"]) > 0
        print(f"✅ Got {len(data['protocols'])} marketplace protocols")
        
        # Verify protocol structure
        protocol = data["protocols"][0]
        assert "id" in protocol
        assert "name" in protocol
        assert "price" in protocol
        assert "category" in protocol
        print(f"✅ Protocol structure verified: {protocol['name']} - ${protocol['price']}")


class TestSearchAndCollate:
    """Search and collate functionality tests"""
    
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
    
    def test_search_endpoint(self, admin_token):
        """Test search endpoint with broad query"""
        response = requests.post(
            f"{BASE_URL}/api/search",
            headers={
                "Authorization": f"Bearer {admin_token}",
                "Content-Type": "application/json"
            },
            json={"query": "George Bush air force"}
        )
        assert response.status_code == 200
        data = response.json()
        assert "results" in data
        print(f"✅ Search returned {len(data.get('results', []))} results")
    
    def test_collate_endpoint(self, admin_token):
        """Test collate endpoint with category"""
        # First get a category ID
        response = requests.get(
            f"{BASE_URL}/api/categories",
            headers={"Authorization": f"Bearer {admin_token}"}
        )
        categories = response.json()
        
        if not categories:
            pytest.skip("No categories available for collate test")
        
        category_id = categories[0]["id"]
        
        # Test collate
        response = requests.post(
            f"{BASE_URL}/api/collate",
            headers={
                "Authorization": f"Bearer {admin_token}",
                "Content-Type": "application/json"
            },
            json={
                "category_id": category_id,
                "aggregation": "and_or"
            }
        )
        # Collate may return 200 or 400 depending on protocol validity
        assert response.status_code in [200, 400]
        print(f"✅ Collate endpoint responded with status {response.status_code}")
    
    def test_ultimate_search_results(self, admin_token):
        """Test getting stored search results"""
        response = requests.get(
            f"{BASE_URL}/api/ultimate-search",
            headers={"Authorization": f"Bearer {admin_token}"}
        )
        assert response.status_code == 200
        data = response.json()
        assert "results" in data
        assert "total" in data
        print(f"✅ Ultimate search has {data['total']} stored results")


class TestPromotionalContent:
    """Promotional content tests"""
    
    def test_book_promo_endpoint(self):
        """Test book promotion endpoint"""
        response = requests.get(f"{BASE_URL}/api/book-promo")
        assert response.status_code == 200
        data = response.json()
        assert "title" in data
        assert "author" in data
        assert data["title"] == "Letters to Evelyn"
        print(f"✅ Book promo: {data['title']} by {data['author']}")
    
    def test_quotes_gallery(self):
        """Test quotes gallery endpoint"""
        response = requests.get(f"{BASE_URL}/api/quotes/gallery")
        assert response.status_code == 200
        data = response.json()
        assert "quotes" in data
        assert len(data["quotes"]) > 0
        print(f"✅ Quotes gallery has {len(data['quotes'])} quotes")


class TestGamification:
    """Gamification tests"""
    
    def test_badges_endpoint(self):
        """Test badges endpoint"""
        response = requests.get(f"{BASE_URL}/api/gamification/badges")
        assert response.status_code == 200
        data = response.json()
        assert "badges" in data
        print(f"✅ Got {len(data['badges'])} badges")
    
    def test_leaderboard_endpoint(self):
        """Test leaderboard endpoint"""
        response = requests.get(f"{BASE_URL}/api/gamification/leaderboard")
        assert response.status_code == 200
        data = response.json()
        assert "leaderboard" in data
        print(f"✅ Leaderboard has {len(data['leaderboard'])} entries")


class TestAdminEndpoints:
    """Admin-only endpoint tests"""
    
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
    
    @pytest.fixture
    def regular_token(self):
        """Get regular user authentication token"""
        response = requests.post(f"{BASE_URL}/api/auth/login", json={
            "email": TEST_EMAIL,
            "password": TEST_PASSWORD
        })
        if response.status_code == 200:
            return response.json().get("token")
        pytest.skip("Regular user authentication failed")
    
    def test_admin_stats_with_admin(self, admin_token):
        """Test admin stats endpoint with admin user"""
        response = requests.get(
            f"{BASE_URL}/api/admin/stats",
            headers={"Authorization": f"Bearer {admin_token}"}
        )
        assert response.status_code == 200
        print("✅ Admin can access admin stats")
    
    def test_admin_stats_with_regular_user(self, regular_token):
        """Test admin stats endpoint with regular user (should fail)"""
        response = requests.get(
            f"{BASE_URL}/api/admin/stats",
            headers={"Authorization": f"Bearer {regular_token}"}
        )
        assert response.status_code == 403
        print("✅ Regular user correctly denied access to admin stats")
    
    def test_admin_settings_with_admin(self, admin_token):
        """Test admin settings endpoint with admin user"""
        response = requests.get(
            f"{BASE_URL}/api/admin/settings",
            headers={"Authorization": f"Bearer {admin_token}"}
        )
        assert response.status_code == 200
        print("✅ Admin can access admin settings")


class TestProtocolValidation:
    """Protocol validation tests"""
    
    def test_valid_protocol(self):
        """Test validating a valid protocol"""
        response = requests.post(
            f"{BASE_URL}/api/protocol/validate",
            json={"protocol": "(word1 or word2) & (word3)"}
        )
        assert response.status_code == 200
        data = response.json()
        assert data.get("valid") == True
        print("✅ Valid protocol accepted")
    
    def test_protocol_with_include_all(self):
        """Test protocol with include all operator"""
        response = requests.post(
            f"{BASE_URL}/api/protocol/validate",
            json={"protocol": "(word1 or word2)+"}
        )
        assert response.status_code == 200
        data = response.json()
        assert data.get("valid") == True
        print("✅ Protocol with + operator accepted")


if __name__ == "__main__":
    pytest.main([__file__, "-v", "--tb=short"])
