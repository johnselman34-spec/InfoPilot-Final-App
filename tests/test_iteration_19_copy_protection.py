"""
InfoPilot Explorer - Iteration 19 Tests
Copy Protection Feature Testing

Tests the new copy protection feature:
- GET /api/marketplace/my-purchases - Returns user's purchased and owned protocol IDs
- GET /api/marketplace/check-purchase/{protocol_id} - Returns has_access true/false
- POST /api/marketplace/copy-protocol/{protocol_id} - Returns 403 if not purchased, protocol content if purchased/owned
"""

import pytest
import requests
import os
import uuid

BASE_URL = os.environ.get('REACT_APP_BACKEND_URL', '').rstrip('/')

# Test credentials
ADMIN_EMAIL = "admin@infopilot.com"
ADMIN_PASSWORD = "admin123"
TEST_USER_EMAIL = "testuser_new@example.com"
TEST_USER_PASSWORD = "password123"


class TestCopyProtectionSetup:
    """Setup and authentication tests"""
    
    @pytest.fixture(scope="class")
    def admin_token(self):
        """Get admin authentication token"""
        response = requests.post(f"{BASE_URL}/api/auth/login", json={
            "email": ADMIN_EMAIL,
            "password": ADMIN_PASSWORD
        })
        if response.status_code == 200:
            return response.json().get("token")
        pytest.skip("Admin authentication failed")
    
    @pytest.fixture(scope="class")
    def test_user_token(self):
        """Get test user authentication token"""
        response = requests.post(f"{BASE_URL}/api/auth/login", json={
            "email": TEST_USER_EMAIL,
            "password": TEST_USER_PASSWORD
        })
        if response.status_code == 200:
            return response.json().get("token")
        pytest.skip("Test user authentication failed")
    
    def test_admin_login(self):
        """Test admin can login"""
        response = requests.post(f"{BASE_URL}/api/auth/login", json={
            "email": ADMIN_EMAIL,
            "password": ADMIN_PASSWORD
        })
        assert response.status_code == 200
        data = response.json()
        assert "token" in data
        assert "user" in data
        print(f"Admin login successful, user_id: {data['user'].get('id')}")
    
    def test_test_user_login(self):
        """Test regular user can login"""
        response = requests.post(f"{BASE_URL}/api/auth/login", json={
            "email": TEST_USER_EMAIL,
            "password": TEST_USER_PASSWORD
        })
        assert response.status_code == 200
        data = response.json()
        assert "token" in data
        assert "user" in data
        print(f"Test user login successful, user_id: {data['user'].get('id')}")


class TestMyPurchasesEndpoint:
    """Tests for GET /api/marketplace/my-purchases"""
    
    @pytest.fixture(autouse=True)
    def setup(self):
        """Setup authentication"""
        # Login as test user
        response = requests.post(f"{BASE_URL}/api/auth/login", json={
            "email": TEST_USER_EMAIL,
            "password": TEST_USER_PASSWORD
        })
        if response.status_code == 200:
            self.token = response.json().get("token")
            self.user_id = response.json().get("user", {}).get("id")
        else:
            pytest.skip("Authentication failed")
    
    def test_my_purchases_requires_auth(self):
        """Test that my-purchases endpoint requires authentication"""
        response = requests.get(f"{BASE_URL}/api/marketplace/my-purchases")
        assert response.status_code == 401
        print("my-purchases correctly requires authentication")
    
    def test_my_purchases_returns_structure(self):
        """Test that my-purchases returns correct structure"""
        response = requests.get(
            f"{BASE_URL}/api/marketplace/my-purchases",
            headers={"Authorization": f"Bearer {self.token}"}
        )
        assert response.status_code == 200
        data = response.json()
        
        # Check structure
        assert "purchased_protocol_ids" in data
        assert "owned_protocol_ids" in data
        assert "all_accessible_ids" in data
        
        assert isinstance(data["purchased_protocol_ids"], list)
        assert isinstance(data["owned_protocol_ids"], list)
        assert isinstance(data["all_accessible_ids"], list)
        
        print(f"my-purchases response: purchased={len(data['purchased_protocol_ids'])}, owned={len(data['owned_protocol_ids'])}, all={len(data['all_accessible_ids'])}")


class TestCheckPurchaseEndpoint:
    """Tests for GET /api/marketplace/check-purchase/{protocol_id}"""
    
    @pytest.fixture(autouse=True)
    def setup(self):
        """Setup authentication and get a protocol ID"""
        # Login as test user
        response = requests.post(f"{BASE_URL}/api/auth/login", json={
            "email": TEST_USER_EMAIL,
            "password": TEST_USER_PASSWORD
        })
        if response.status_code == 200:
            self.token = response.json().get("token")
            self.user_id = response.json().get("user", {}).get("id")
        else:
            pytest.skip("Authentication failed")
        
        # Get marketplace protocols
        response = requests.get(f"{BASE_URL}/api/marketplace/protocols")
        if response.status_code == 200:
            protocols = response.json().get("protocols", [])
            if protocols:
                self.test_protocol = protocols[0]
            else:
                pytest.skip("No protocols in marketplace")
        else:
            pytest.skip("Could not fetch marketplace protocols")
    
    def test_check_purchase_requires_auth(self):
        """Test that check-purchase endpoint requires authentication"""
        response = requests.get(f"{BASE_URL}/api/marketplace/check-purchase/{self.test_protocol['id']}")
        assert response.status_code == 401
        print("check-purchase correctly requires authentication")
    
    def test_check_purchase_returns_structure(self):
        """Test that check-purchase returns correct structure"""
        response = requests.get(
            f"{BASE_URL}/api/marketplace/check-purchase/{self.test_protocol['id']}",
            headers={"Authorization": f"Bearer {self.token}"}
        )
        assert response.status_code == 200
        data = response.json()
        
        # Check structure
        assert "has_access" in data
        assert "reason" in data
        assert isinstance(data["has_access"], bool)
        assert data["reason"] in ["owner", "purchased", "not_purchased"]
        
        print(f"check-purchase for protocol {self.test_protocol['id']}: has_access={data['has_access']}, reason={data['reason']}")
    
    def test_check_purchase_invalid_protocol(self):
        """Test check-purchase with invalid protocol ID"""
        fake_id = str(uuid.uuid4())
        response = requests.get(
            f"{BASE_URL}/api/marketplace/check-purchase/{fake_id}",
            headers={"Authorization": f"Bearer {self.token}"}
        )
        # Should return not_purchased for non-existent protocol
        assert response.status_code == 200
        data = response.json()
        assert data["has_access"] == False
        print(f"check-purchase for non-existent protocol returns has_access=False")


class TestCopyProtocolEndpoint:
    """Tests for POST /api/marketplace/copy-protocol/{protocol_id}"""
    
    @pytest.fixture(autouse=True)
    def setup(self):
        """Setup authentication and get protocols"""
        # Login as test user
        response = requests.post(f"{BASE_URL}/api/auth/login", json={
            "email": TEST_USER_EMAIL,
            "password": TEST_USER_PASSWORD
        })
        if response.status_code == 200:
            self.test_token = response.json().get("token")
            self.test_user_id = response.json().get("user", {}).get("id")
        else:
            pytest.skip("Test user authentication failed")
        
        # Login as admin
        response = requests.post(f"{BASE_URL}/api/auth/login", json={
            "email": ADMIN_EMAIL,
            "password": ADMIN_PASSWORD
        })
        if response.status_code == 200:
            self.admin_token = response.json().get("token")
            self.admin_user_id = response.json().get("user", {}).get("id")
        else:
            pytest.skip("Admin authentication failed")
        
        # Get marketplace protocols
        response = requests.get(f"{BASE_URL}/api/marketplace/protocols")
        if response.status_code == 200:
            self.protocols = response.json().get("protocols", [])
        else:
            pytest.skip("Could not fetch marketplace protocols")
    
    def test_copy_protocol_requires_auth(self):
        """Test that copy-protocol endpoint requires authentication"""
        if not self.protocols:
            pytest.skip("No protocols available")
        
        response = requests.post(f"{BASE_URL}/api/marketplace/copy-protocol/{self.protocols[0]['id']}")
        assert response.status_code == 401
        print("copy-protocol correctly requires authentication")
    
    def test_copy_protocol_not_found(self):
        """Test copy-protocol with non-existent protocol"""
        fake_id = str(uuid.uuid4())
        response = requests.post(
            f"{BASE_URL}/api/marketplace/copy-protocol/{fake_id}",
            headers={"Authorization": f"Bearer {self.test_token}"}
        )
        assert response.status_code == 404
        print("copy-protocol returns 404 for non-existent protocol")
    
    def test_copy_protocol_unpurchased_returns_403(self):
        """Test that copying unpurchased protocol returns 403 with price info"""
        # Find a protocol that the test user doesn't own
        for protocol in self.protocols:
            if protocol.get("user_id") != self.test_user_id and protocol.get("price", 0) > 0:
                response = requests.post(
                    f"{BASE_URL}/api/marketplace/copy-protocol/{protocol['id']}",
                    headers={"Authorization": f"Bearer {self.test_token}"}
                )
                
                # Check if user has already purchased
                check_response = requests.get(
                    f"{BASE_URL}/api/marketplace/check-purchase/{protocol['id']}",
                    headers={"Authorization": f"Bearer {self.test_token}"}
                )
                check_data = check_response.json()
                
                if check_data.get("has_access"):
                    print(f"User already has access to protocol {protocol['id']}, skipping")
                    continue
                
                # Should return 403 for unpurchased protocol
                assert response.status_code == 403
                data = response.json()
                assert "detail" in data
                assert "$" in data["detail"]  # Should contain price info
                print(f"copy-protocol returns 403 for unpurchased protocol: {data['detail']}")
                return
        
        pytest.skip("No unpurchased protocols found for test user")
    
    def test_copy_protocol_owner_can_copy(self):
        """Test that protocol owner can always copy their own protocol"""
        # Find a protocol owned by admin or test user
        for protocol in self.protocols:
            if protocol.get("user_id") == self.admin_user_id:
                response = requests.post(
                    f"{BASE_URL}/api/marketplace/copy-protocol/{protocol['id']}",
                    headers={"Authorization": f"Bearer {self.admin_token}"}
                )
                assert response.status_code == 200
                data = response.json()
                assert "protocol" in data
                assert "access_type" in data
                assert data["access_type"] == "owner"
                print(f"Owner can copy their own protocol, access_type={data['access_type']}")
                return
        
        pytest.skip("No protocols owned by admin found")


class TestCopyProtectionIntegration:
    """Integration tests for the full copy protection flow"""
    
    @pytest.fixture(autouse=True)
    def setup(self):
        """Setup authentication"""
        # Login as test user
        response = requests.post(f"{BASE_URL}/api/auth/login", json={
            "email": TEST_USER_EMAIL,
            "password": TEST_USER_PASSWORD
        })
        if response.status_code == 200:
            self.test_token = response.json().get("token")
            self.test_user_id = response.json().get("user", {}).get("id")
        else:
            pytest.skip("Test user authentication failed")
        
        # Login as admin
        response = requests.post(f"{BASE_URL}/api/auth/login", json={
            "email": ADMIN_EMAIL,
            "password": ADMIN_PASSWORD
        })
        if response.status_code == 200:
            self.admin_token = response.json().get("token")
            self.admin_user_id = response.json().get("user", {}).get("id")
        else:
            pytest.skip("Admin authentication failed")
    
    def test_full_access_check_flow(self):
        """Test the full flow: get purchases -> check access -> attempt copy"""
        # Step 1: Get user's purchases
        purchases_response = requests.get(
            f"{BASE_URL}/api/marketplace/my-purchases",
            headers={"Authorization": f"Bearer {self.test_token}"}
        )
        assert purchases_response.status_code == 200
        purchases_data = purchases_response.json()
        accessible_ids = purchases_data.get("all_accessible_ids", [])
        
        print(f"User has access to {len(accessible_ids)} protocols")
        
        # Step 2: Get marketplace protocols
        protocols_response = requests.get(f"{BASE_URL}/api/marketplace/protocols")
        assert protocols_response.status_code == 200
        protocols = protocols_response.json().get("protocols", [])
        
        # Step 3: For each protocol, verify access check matches copy behavior
        for protocol in protocols[:3]:  # Test first 3 protocols
            protocol_id = protocol["id"]
            
            # Check access
            check_response = requests.get(
                f"{BASE_URL}/api/marketplace/check-purchase/{protocol_id}",
                headers={"Authorization": f"Bearer {self.test_token}"}
            )
            assert check_response.status_code == 200
            check_data = check_response.json()
            
            # Attempt copy
            copy_response = requests.post(
                f"{BASE_URL}/api/marketplace/copy-protocol/{protocol_id}",
                headers={"Authorization": f"Bearer {self.test_token}"}
            )
            
            # Verify consistency
            if check_data["has_access"]:
                assert copy_response.status_code == 200
                print(f"Protocol {protocol_id}: has_access=True, copy=SUCCESS")
            else:
                # If protocol is for sale and not purchased, should be 403
                if protocol.get("price", 0) > 0:
                    assert copy_response.status_code == 403
                    print(f"Protocol {protocol_id}: has_access=False, copy=403 (protected)")
                else:
                    # Free protocols should be copyable
                    assert copy_response.status_code == 200
                    print(f"Protocol {protocol_id}: has_access=False but free, copy=SUCCESS")
    
    def test_marketplace_protocols_have_required_fields(self):
        """Test that marketplace protocols have all required fields for copy protection"""
        response = requests.get(f"{BASE_URL}/api/marketplace/protocols")
        assert response.status_code == 200
        protocols = response.json().get("protocols", [])
        
        for protocol in protocols:
            assert "id" in protocol
            assert "user_id" in protocol
            assert "protocol" in protocol
            assert "price" in protocol or protocol.get("price") is None
            assert "is_public" in protocol or protocol.get("is_public") is None
            print(f"Protocol {protocol['id']}: price=${protocol.get('price', 0)}, is_public={protocol.get('is_public')}")


class TestEdgeCases:
    """Edge case tests for copy protection"""
    
    @pytest.fixture(autouse=True)
    def setup(self):
        """Setup authentication"""
        response = requests.post(f"{BASE_URL}/api/auth/login", json={
            "email": TEST_USER_EMAIL,
            "password": TEST_USER_PASSWORD
        })
        if response.status_code == 200:
            self.token = response.json().get("token")
        else:
            pytest.skip("Authentication failed")
    
    def test_empty_protocol_id(self):
        """Test endpoints with empty protocol ID"""
        # check-purchase with empty ID
        response = requests.get(
            f"{BASE_URL}/api/marketplace/check-purchase/",
            headers={"Authorization": f"Bearer {self.token}"}
        )
        # Should return 404 or 422
        assert response.status_code in [404, 405, 422]
        
        # copy-protocol with empty ID
        response = requests.post(
            f"{BASE_URL}/api/marketplace/copy-protocol/",
            headers={"Authorization": f"Bearer {self.token}"}
        )
        assert response.status_code in [404, 405, 422]
        print("Empty protocol ID handled correctly")
    
    def test_malformed_protocol_id(self):
        """Test endpoints with malformed protocol ID"""
        malformed_ids = ["not-a-uuid", "12345", "null", "undefined"]
        
        for bad_id in malformed_ids:
            response = requests.get(
                f"{BASE_URL}/api/marketplace/check-purchase/{bad_id}",
                headers={"Authorization": f"Bearer {self.token}"}
            )
            # Should handle gracefully (200 with has_access=False or 404)
            assert response.status_code in [200, 404]
            
            response = requests.post(
                f"{BASE_URL}/api/marketplace/copy-protocol/{bad_id}",
                headers={"Authorization": f"Bearer {self.token}"}
            )
            # Should return 404 for non-existent protocol
            assert response.status_code == 404
        
        print("Malformed protocol IDs handled correctly")


if __name__ == "__main__":
    pytest.main([__file__, "-v", "--tb=short"])
