"""
InfoPilot Explorer - Category Creation Tests
Tests for: Category creation with Google OAuth, sub-categories, complex protocols, token persistence
Bug fix verification: Network error when creating categories after Google OAuth login
"""
import pytest
import requests
import os
import uuid

BASE_URL = "https://protocol-market.preview.emergentagent.com"

# Test credentials
ADMIN_EMAIL = "john@infojet.com"
ADMIN_PASSWORD = "password123"

# Google OAuth test user (from review request)
GOOGLE_USER_EMAIL = "turbomentor33@gmail.com"
GOOGLE_USER_ID = "111835474350288495210"
GOOGLE_USER_NAME = "John Selman"


class TestHealthAndBasics:
    """Basic health checks before testing category creation"""
    
    def test_api_health(self):
        """Test API health endpoint"""
        response = requests.get(f"{BASE_URL}/api/health")
        assert response.status_code == 200
        data = response.json()
        assert data["status"] == "healthy"
        print(f"✓ Health check passed: {data}")
    
    def test_categories_endpoint_exists(self):
        """Test that categories endpoint exists (requires auth)"""
        response = requests.get(f"{BASE_URL}/api/categories")
        assert response.status_code == 401  # Should require auth
        print("✓ Categories endpoint exists and requires authentication")


class TestGoogleOAuthCategoryCreation:
    """
    Tests for the original bug: Network error when creating categories after Google OAuth login
    """
    
    @pytest.fixture
    def google_auth_token(self):
        """Simulate Google OAuth login and get token"""
        # Use the Google OAuth endpoint to authenticate
        response = requests.post(f"{BASE_URL}/api/auth/google", json={
            "email": GOOGLE_USER_EMAIL,
            "google_id": GOOGLE_USER_ID,
            "name": GOOGLE_USER_NAME,
            "picture": None
        })
        assert response.status_code == 200, f"Google auth failed: {response.text}"
        data = response.json()
        assert "token" in data
        print(f"✓ Google OAuth login successful for {GOOGLE_USER_EMAIL}")
        return data["token"]
    
    def test_google_oauth_then_create_simple_category(self, google_auth_token):
        """Test creating a simple category after Google OAuth login - original bug scenario"""
        unique_name = f"TEST_GoogleOAuth_Simple_{uuid.uuid4().hex[:8]}"
        
        response = requests.post(f"{BASE_URL}/api/categories",
            json={
                "name": unique_name,
                "protocol": "(test or example)",
                "is_public": False
            },
            headers={"Authorization": f"Bearer {google_auth_token}"}
        )
        
        assert response.status_code == 200, f"Category creation failed: {response.text}"
        data = response.json()
        assert data["name"] == unique_name
        assert "id" in data
        print(f"✓ Category created after Google OAuth: {data['name']} (ID: {data['id']})")
        
        # Cleanup
        requests.delete(f"{BASE_URL}/api/categories/{data['id']}",
            headers={"Authorization": f"Bearer {google_auth_token}"}
        )
        print(f"✓ Cleanup: Deleted test category")
    
    def test_google_oauth_then_create_complex_protocol_category(self, google_auth_token):
        """Test creating category with complex protocol (special characters) after Google OAuth"""
        unique_name = f"TEST_GoogleOAuth_Complex_{uuid.uuid4().hex[:8]}"
        
        # Complex protocol from the review request
        complex_protocol = "(President George Bush or President Bush) & (pilot or F-102 or air force) & (how to fly or flying)+ & (early childhood or wanted to be a pilot)"
        
        response = requests.post(f"{BASE_URL}/api/categories",
            json={
                "name": unique_name,
                "protocol": complex_protocol,
                "is_public": False
            },
            headers={"Authorization": f"Bearer {google_auth_token}"}
        )
        
        assert response.status_code == 200, f"Complex protocol category creation failed: {response.text}"
        data = response.json()
        assert data["name"] == unique_name
        assert data["protocol"] == complex_protocol
        print(f"✓ Complex protocol category created: {data['name']}")
        print(f"  Protocol: {complex_protocol[:60]}...")
        
        # Cleanup
        requests.delete(f"{BASE_URL}/api/categories/{data['id']}",
            headers={"Authorization": f"Bearer {google_auth_token}"}
        )
    
    def test_google_oauth_token_persistence(self, google_auth_token):
        """Test that token from Google OAuth works for multiple requests"""
        # First request - get categories
        response1 = requests.get(f"{BASE_URL}/api/categories",
            headers={"Authorization": f"Bearer {google_auth_token}"}
        )
        assert response1.status_code == 200
        print(f"✓ First request with Google OAuth token: success")
        
        # Second request - get auth/me
        response2 = requests.get(f"{BASE_URL}/api/auth/me",
            headers={"Authorization": f"Bearer {google_auth_token}"}
        )
        assert response2.status_code == 200
        user_data = response2.json()
        assert user_data["email"].lower() == GOOGLE_USER_EMAIL.lower()
        print(f"✓ Second request with Google OAuth token: success (user: {user_data['username']})")
        
        # Third request - create and delete category
        unique_name = f"TEST_TokenPersistence_{uuid.uuid4().hex[:8]}"
        response3 = requests.post(f"{BASE_URL}/api/categories",
            json={"name": unique_name, "protocol": "(test)", "is_public": False},
            headers={"Authorization": f"Bearer {google_auth_token}"}
        )
        assert response3.status_code == 200
        cat_id = response3.json()["id"]
        print(f"✓ Third request with Google OAuth token: category created")
        
        # Cleanup
        requests.delete(f"{BASE_URL}/api/categories/{cat_id}",
            headers={"Authorization": f"Bearer {google_auth_token}"}
        )


class TestSubCategoryCreation:
    """Tests for sub-category creation with parent_id"""
    
    @pytest.fixture
    def auth_token(self):
        """Get auth token for protected endpoints"""
        response = requests.post(f"{BASE_URL}/api/auth/login", json={
            "email": ADMIN_EMAIL,
            "password": ADMIN_PASSWORD
        })
        return response.json()["token"]
    
    def test_create_parent_then_subcategory(self, auth_token):
        """Test creating a parent category and then a sub-category"""
        # Create parent category
        parent_name = f"TEST_Parent_{uuid.uuid4().hex[:8]}"
        parent_res = requests.post(f"{BASE_URL}/api/categories",
            json={
                "name": parent_name,
                "protocol": "(parent or main)",
                "is_public": False
            },
            headers={"Authorization": f"Bearer {auth_token}"}
        )
        assert parent_res.status_code == 200
        parent_data = parent_res.json()
        parent_id = parent_data["id"]
        print(f"✓ Parent category created: {parent_name} (ID: {parent_id})")
        
        # Create sub-category with parent_id (avoid blocked words like 'child')
        nested_name = f"TEST_Nested_{uuid.uuid4().hex[:8]}"
        nested_res = requests.post(f"{BASE_URL}/api/categories",
            json={
                "name": nested_name,
                "protocol": "(nested or secondary)",
                "parent_id": parent_id,
                "is_public": False
            },
            headers={"Authorization": f"Bearer {auth_token}"}
        )
        assert nested_res.status_code == 200, f"Sub-category creation failed: {nested_res.text}"
        nested_data = nested_res.json()
        assert nested_data["parent_id"] == parent_id
        assert nested_data["level"] == 1  # Should be level 1 (parent is level 0)
        print(f"✓ Sub-category created: {nested_name} (parent_id: {parent_id}, level: {nested_data['level']})")
        
        # Cleanup - delete nested first, then parent
        requests.delete(f"{BASE_URL}/api/categories/{nested_data['id']}",
            headers={"Authorization": f"Bearer {auth_token}"}
        )
        requests.delete(f"{BASE_URL}/api/categories/{parent_id}",
            headers={"Authorization": f"Bearer {auth_token}"}
        )
        print(f"✓ Cleanup: Deleted test categories")
    
    def test_create_nested_subcategories(self, auth_token):
        """Test creating multiple levels of nested sub-categories"""
        categories = []
        
        # Create 3 levels of nested categories
        parent_id = None
        for level in range(3):
            name = f"TEST_Level{level}_{uuid.uuid4().hex[:8]}"
            res = requests.post(f"{BASE_URL}/api/categories",
                json={
                    "name": name,
                    "protocol": f"(level{level})",
                    "parent_id": parent_id,
                    "is_public": False
                },
                headers={"Authorization": f"Bearer {auth_token}"}
            )
            assert res.status_code == 200, f"Failed to create level {level}: {res.text}"
            data = res.json()
            assert data["level"] == level
            categories.append(data)
            parent_id = data["id"]
            print(f"✓ Level {level} category created: {name}")
        
        # Cleanup - delete in reverse order
        for cat in reversed(categories):
            requests.delete(f"{BASE_URL}/api/categories/{cat['id']}",
                headers={"Authorization": f"Bearer {auth_token}"}
            )
        print(f"✓ Cleanup: Deleted {len(categories)} nested categories")


class TestComplexProtocols:
    """Tests for category creation with complex protocols containing special characters"""
    
    @pytest.fixture
    def auth_token(self):
        """Get auth token for protected endpoints"""
        response = requests.post(f"{BASE_URL}/api/auth/login", json={
            "email": ADMIN_EMAIL,
            "password": ADMIN_PASSWORD
        })
        return response.json()["token"]
    
    def test_protocol_with_parentheses_and_operators(self, auth_token):
        """Test protocol with parentheses and boolean operators"""
        unique_name = f"TEST_Protocol1_{uuid.uuid4().hex[:8]}"
        protocol = "(civil war or battle) & (general or commander)"
        
        response = requests.post(f"{BASE_URL}/api/categories",
            json={"name": unique_name, "protocol": protocol, "is_public": False},
            headers={"Authorization": f"Bearer {auth_token}"}
        )
        assert response.status_code == 200
        data = response.json()
        assert data["protocol"] == protocol
        print(f"✓ Protocol with parentheses and operators: {protocol}")
        
        # Cleanup
        requests.delete(f"{BASE_URL}/api/categories/{data['id']}",
            headers={"Authorization": f"Bearer {auth_token}"}
        )
    
    def test_protocol_with_plus_modifier(self, auth_token):
        """Test protocol with + modifier (must contain)"""
        unique_name = f"TEST_Protocol2_{uuid.uuid4().hex[:8]}"
        protocol = "(William or Gamble)+ & (civil war or general)"
        
        response = requests.post(f"{BASE_URL}/api/categories",
            json={"name": unique_name, "protocol": protocol, "is_public": False},
            headers={"Authorization": f"Bearer {auth_token}"}
        )
        assert response.status_code == 200
        data = response.json()
        assert data["protocol"] == protocol
        print(f"✓ Protocol with + modifier: {protocol}")
        
        # Cleanup
        requests.delete(f"{BASE_URL}/api/categories/{data['id']}",
            headers={"Authorization": f"Bearer {auth_token}"}
        )
    
    def test_protocol_with_caret_modifier(self, auth_token):
        """Test protocol with ^ modifier (must not contain)"""
        unique_name = f"TEST_Protocol3_{uuid.uuid4().hex[:8]}"
        protocol = "(civil war or general)+ & (confederate)^"
        
        response = requests.post(f"{BASE_URL}/api/categories",
            json={"name": unique_name, "protocol": protocol, "is_public": False},
            headers={"Authorization": f"Bearer {auth_token}"}
        )
        assert response.status_code == 200
        data = response.json()
        assert data["protocol"] == protocol
        print(f"✓ Protocol with ^ modifier: {protocol}")
        
        # Cleanup
        requests.delete(f"{BASE_URL}/api/categories/{data['id']}",
            headers={"Authorization": f"Bearer {auth_token}"}
        )
    
    def test_protocol_with_hyphen_and_numbers(self, auth_token):
        """Test protocol with hyphens and numbers (F-102)"""
        unique_name = f"TEST_Protocol4_{uuid.uuid4().hex[:8]}"
        protocol = "(pilot or F-102 or air force)"
        
        response = requests.post(f"{BASE_URL}/api/categories",
            json={"name": unique_name, "protocol": protocol, "is_public": False},
            headers={"Authorization": f"Bearer {auth_token}"}
        )
        assert response.status_code == 200
        data = response.json()
        assert data["protocol"] == protocol
        print(f"✓ Protocol with hyphen and numbers: {protocol}")
        
        # Cleanup
        requests.delete(f"{BASE_URL}/api/categories/{data['id']}",
            headers={"Authorization": f"Bearer {auth_token}"}
        )
    
    def test_full_complex_protocol_from_bug_report(self, auth_token):
        """Test the exact complex protocol from the bug report"""
        unique_name = f"TEST_BugReport_{uuid.uuid4().hex[:8]}"
        # Exact protocol from the review request
        protocol = "(President George Bush or President Bush) & (pilot or F-102 or air force) & (how to fly or flying)+ & (early childhood or wanted to be a pilot)"
        
        response = requests.post(f"{BASE_URL}/api/categories",
            json={"name": unique_name, "protocol": protocol, "is_public": False},
            headers={"Authorization": f"Bearer {auth_token}"}
        )
        assert response.status_code == 200, f"Failed: {response.text}"
        data = response.json()
        assert data["protocol"] == protocol
        print(f"✓ Full complex protocol from bug report created successfully")
        print(f"  Protocol: {protocol}")
        
        # Cleanup
        requests.delete(f"{BASE_URL}/api/categories/{data['id']}",
            headers={"Authorization": f"Bearer {auth_token}"}
        )


class TestErrorHandling:
    """Tests for error handling in category creation"""
    
    @pytest.fixture
    def auth_token(self):
        """Get auth token for protected endpoints"""
        response = requests.post(f"{BASE_URL}/api/auth/login", json={
            "email": ADMIN_EMAIL,
            "password": ADMIN_PASSWORD
        })
        return response.json()["token"]
    
    def test_create_category_without_auth(self):
        """Test that category creation fails without authentication"""
        response = requests.post(f"{BASE_URL}/api/categories",
            json={"name": "TEST_NoAuth", "protocol": "(test)", "is_public": False}
        )
        assert response.status_code == 401
        print("✓ Category creation without auth correctly rejected (401)")
    
    def test_create_category_with_invalid_token(self):
        """Test that category creation fails with invalid token"""
        response = requests.post(f"{BASE_URL}/api/categories",
            json={"name": "TEST_InvalidToken", "protocol": "(test)", "is_public": False},
            headers={"Authorization": "Bearer invalid_token_12345"}
        )
        assert response.status_code == 401
        print("✓ Category creation with invalid token correctly rejected (401)")
    
    def test_create_category_missing_name(self, auth_token):
        """Test that category creation fails without name"""
        response = requests.post(f"{BASE_URL}/api/categories",
            json={"protocol": "(test)", "is_public": False},
            headers={"Authorization": f"Bearer {auth_token}"}
        )
        assert response.status_code == 422  # Validation error
        print("✓ Category creation without name correctly rejected (422)")
    
    def test_create_category_missing_protocol(self, auth_token):
        """Test that category creation fails without protocol"""
        response = requests.post(f"{BASE_URL}/api/categories",
            json={"name": "TEST_NoProtocol", "is_public": False},
            headers={"Authorization": f"Bearer {auth_token}"}
        )
        assert response.status_code == 422  # Validation error
        print("✓ Category creation without protocol correctly rejected (422)")
    
    def test_create_category_invalid_parent_id(self, auth_token):
        """Test that category creation fails with invalid parent_id"""
        response = requests.post(f"{BASE_URL}/api/categories",
            json={
                "name": "TEST_InvalidParent",
                "protocol": "(test)",
                "parent_id": "000000000000000000000000",  # Non-existent ID
                "is_public": False
            },
            headers={"Authorization": f"Bearer {auth_token}"}
        )
        assert response.status_code == 404  # Parent not found
        print("✓ Category creation with invalid parent_id correctly rejected (404)")


class TestTokenValidation:
    """Tests for token validation and auth/me endpoint"""
    
    def test_auth_me_with_admin_token(self):
        """Test /auth/me with admin token"""
        # Login
        login_res = requests.post(f"{BASE_URL}/api/auth/login", json={
            "email": ADMIN_EMAIL,
            "password": ADMIN_PASSWORD
        })
        token = login_res.json()["token"]
        
        # Get user info
        response = requests.get(f"{BASE_URL}/api/auth/me",
            headers={"Authorization": f"Bearer {token}"}
        )
        assert response.status_code == 200
        data = response.json()
        assert data["email"] == ADMIN_EMAIL
        assert data["is_admin"] == True
        print(f"✓ Auth/me with admin token: {data['username']} (admin: {data['is_admin']})")
    
    def test_auth_me_with_google_oauth_token(self):
        """Test /auth/me with Google OAuth token"""
        # Google OAuth login
        auth_res = requests.post(f"{BASE_URL}/api/auth/google", json={
            "email": GOOGLE_USER_EMAIL,
            "google_id": GOOGLE_USER_ID,
            "name": GOOGLE_USER_NAME,
            "picture": None
        })
        token = auth_res.json()["token"]
        
        # Get user info
        response = requests.get(f"{BASE_URL}/api/auth/me",
            headers={"Authorization": f"Bearer {token}"}
        )
        assert response.status_code == 200
        data = response.json()
        assert data["email"].lower() == GOOGLE_USER_EMAIL.lower()
        print(f"✓ Auth/me with Google OAuth token: {data['username']} (email: {data['email']})")


if __name__ == "__main__":
    pytest.main([__file__, "-v", "--tb=short"])
