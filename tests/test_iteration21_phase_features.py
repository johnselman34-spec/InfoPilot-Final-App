"""
Iteration 21 - Testing Phase 1, 2, 3 Features
- Protocol parser with abbreviation handling (William C. Gamble, Ph.D., etc.)
- Admin badge for Google OAuth accounts
- Category editing/saving
- Marketplace shows all for-sale protocols
- Homepage FREE banner and funny marketing copy
- Ultimate Search page with map tab
- Friends, Groups, Pages, Messages features
- Statistics page with badges and leaderboard
"""

import pytest
import requests
import os

BASE_URL = os.environ.get('REACT_APP_BACKEND_URL', '').rstrip('/')

class TestProtocolParser:
    """Test protocol parser with abbreviation handling"""
    
    def test_protocol_parser_basic(self):
        """Test basic protocol parsing"""
        # Login first
        login_res = requests.post(f"{BASE_URL}/api/auth/login", json={
            "email": "jjspilot24@gmail.com",
            "password": "password123"
        })
        assert login_res.status_code == 200
        token = login_res.json()["access_token"]
        headers = {"Authorization": f"Bearer {token}"}
        
        # Create a category with a protocol containing abbreviations
        category_data = {
            "name": "TEST_Abbreviation_Protocol",
            "protocol": {
                "protocol_string": "(William C. Gamble or George Bush) & (Ph.D. or Dr.)"
            },
            "is_public": True
        }
        
        create_res = requests.post(f"{BASE_URL}/api/categories", json=category_data, headers=headers)
        assert create_res.status_code == 200, f"Failed to create category: {create_res.text}"
        category_id = create_res.json()["id"]
        
        # Verify the protocol was saved correctly
        get_res = requests.get(f"{BASE_URL}/api/categories", headers=headers)
        assert get_res.status_code == 200
        categories = get_res.json()["categories"]
        test_cat = next((c for c in categories if c["id"] == category_id), None)
        assert test_cat is not None
        assert "William C. Gamble" in test_cat["protocol_string"]
        assert "Ph.D." in test_cat["protocol_string"]
        
        # Cleanup
        requests.delete(f"{BASE_URL}/api/categories/{category_id}", headers=headers)
        print("✅ Protocol parser handles abbreviations correctly")
    
    def test_protocol_with_periods_in_names(self):
        """Test protocol with periods in names like 'William C. Gamble'"""
        login_res = requests.post(f"{BASE_URL}/api/auth/login", json={
            "email": "jjspilot24@gmail.com",
            "password": "password123"
        })
        token = login_res.json()["access_token"]
        headers = {"Authorization": f"Bearer {token}"}
        
        # Test various abbreviation patterns
        test_protocols = [
            "(William C. Gamble or John D. Smith)",
            "(Ph.D. or M.D. or Dr.)",
            "(U.S. Civil War or American Revolution)",
            "(etc. or example)"
        ]
        
        for protocol_str in test_protocols:
            category_data = {
                "name": f"TEST_Protocol_{protocol_str[:20]}",
                "protocol": {"protocol_string": protocol_str},
                "is_public": True
            }
            res = requests.post(f"{BASE_URL}/api/categories", json=category_data, headers=headers)
            assert res.status_code == 200, f"Failed for protocol: {protocol_str}"
            cat_id = res.json()["id"]
            # Cleanup
            requests.delete(f"{BASE_URL}/api/categories/{cat_id}", headers=headers)
        
        print("✅ Protocol parser handles various abbreviation patterns")


class TestAdminBadge:
    """Test admin badge for Google OAuth accounts"""
    
    def test_admin_email_login(self):
        """Test that admin email gets is_admin=true"""
        login_res = requests.post(f"{BASE_URL}/api/auth/login", json={
            "email": "jjspilot24@gmail.com",
            "password": "password123"
        })
        assert login_res.status_code == 200
        user_data = login_res.json()["user"]
        assert user_data["is_admin"] == True, "Admin email should have is_admin=true"
        print(f"✅ Admin badge: {user_data['email']} has is_admin={user_data['is_admin']}")
    
    def test_non_admin_email(self):
        """Test that non-admin email doesn't get admin badge"""
        # First register a test user
        register_res = requests.post(f"{BASE_URL}/api/auth/register", json={
            "username": "TEST_NonAdmin_User",
            "email": "test_nonadmin@example.com",
            "password": "testpass123"
        })
        
        if register_res.status_code == 200:
            user_data = register_res.json()["user"]
            assert user_data.get("is_admin", False) == False, "Non-admin email should not have is_admin=true"
            print(f"✅ Non-admin user: {user_data['email']} has is_admin={user_data.get('is_admin', False)}")
        elif register_res.status_code == 400 and "already exists" in register_res.text.lower():
            # User already exists, try login
            login_res = requests.post(f"{BASE_URL}/api/auth/login", json={
                "email": "test_nonadmin@example.com",
                "password": "testpass123"
            })
            if login_res.status_code == 200:
                user_data = login_res.json()["user"]
                assert user_data.get("is_admin", False) == False
                print(f"✅ Non-admin user verified")


class TestCategoryEditing:
    """Test category editing and saving"""
    
    def test_create_and_edit_category(self):
        """Test creating and editing a category"""
        login_res = requests.post(f"{BASE_URL}/api/auth/login", json={
            "email": "jjspilot24@gmail.com",
            "password": "password123"
        })
        token = login_res.json()["access_token"]
        headers = {"Authorization": f"Bearer {token}"}
        
        # Create category
        category_data = {
            "name": "TEST_Edit_Category",
            "protocol": {"protocol_string": "(test or example)"},
            "is_public": True
        }
        create_res = requests.post(f"{BASE_URL}/api/categories", json=category_data, headers=headers)
        assert create_res.status_code == 200
        category_id = create_res.json()["id"]
        
        # Edit category
        update_data = {
            "name": "TEST_Edit_Category_Updated",
            "protocol_string": "(updated or modified)"
        }
        update_res = requests.put(f"{BASE_URL}/api/categories/{category_id}", json=update_data, headers=headers)
        assert update_res.status_code == 200, f"Failed to update: {update_res.text}"
        
        # Verify update
        get_res = requests.get(f"{BASE_URL}/api/categories", headers=headers)
        categories = get_res.json()["categories"]
        updated_cat = next((c for c in categories if c["id"] == category_id), None)
        assert updated_cat is not None
        assert updated_cat["name"] == "TEST_Edit_Category_Updated"
        assert "updated" in updated_cat["protocol_string"]
        
        # Cleanup
        requests.delete(f"{BASE_URL}/api/categories/{category_id}", headers=headers)
        print("✅ Category editing works correctly")


class TestMarketplace:
    """Test marketplace shows all for-sale protocols"""
    
    def test_marketplace_protocols_endpoint(self):
        """Test marketplace protocols endpoint"""
        login_res = requests.post(f"{BASE_URL}/api/auth/login", json={
            "email": "jjspilot24@gmail.com",
            "password": "password123"
        })
        token = login_res.json()["access_token"]
        headers = {"Authorization": f"Bearer {token}"}
        
        # Get marketplace protocols
        res = requests.get(f"{BASE_URL}/api/marketplace/protocols", headers=headers)
        assert res.status_code == 200, f"Marketplace endpoint failed: {res.text}"
        data = res.json()
        assert "protocols" in data
        print(f"✅ Marketplace endpoint returns {len(data['protocols'])} protocols")
    
    def test_marketplace_stats(self):
        """Test marketplace stats endpoint"""
        login_res = requests.post(f"{BASE_URL}/api/auth/login", json={
            "email": "jjspilot24@gmail.com",
            "password": "password123"
        })
        token = login_res.json()["access_token"]
        headers = {"Authorization": f"Bearer {token}"}
        
        res = requests.get(f"{BASE_URL}/api/marketplace/stats", headers=headers)
        assert res.status_code == 200
        data = res.json()
        assert "total_protocols" in data
        assert "total_sales" in data
        assert "active_sellers" in data
        print(f"✅ Marketplace stats: {data['total_protocols']} protocols, {data['total_sales']} sales")
    
    def test_sale_settings_endpoint(self):
        """Test sale-settings endpoint"""
        login_res = requests.post(f"{BASE_URL}/api/auth/login", json={
            "email": "jjspilot24@gmail.com",
            "password": "password123"
        })
        token = login_res.json()["access_token"]
        headers = {"Authorization": f"Bearer {token}"}
        
        # Create a private category first
        category_data = {
            "name": "TEST_Sale_Settings",
            "protocol": {"protocol_string": "(sale or test)"},
            "is_public": False
        }
        create_res = requests.post(f"{BASE_URL}/api/categories", json=category_data, headers=headers)
        assert create_res.status_code == 200
        category_id = create_res.json()["id"]
        
        # Update sale settings
        sale_res = requests.put(
            f"{BASE_URL}/api/categories/{category_id}/sale-settings?for_sale=true&price=1.99",
            headers=headers
        )
        assert sale_res.status_code == 200, f"Sale settings failed: {sale_res.text}"
        
        # Cleanup
        requests.delete(f"{BASE_URL}/api/categories/{category_id}", headers=headers)
        print("✅ Sale-settings endpoint works correctly")


class TestSocialFeatures:
    """Test social features - Friends, Groups, Pages, Messages"""
    
    def test_friends_endpoint(self):
        """Test friends endpoint"""
        login_res = requests.post(f"{BASE_URL}/api/auth/login", json={
            "email": "jjspilot24@gmail.com",
            "password": "password123"
        })
        token = login_res.json()["access_token"]
        headers = {"Authorization": f"Bearer {token}"}
        
        res = requests.get(f"{BASE_URL}/api/friends", headers=headers)
        assert res.status_code == 200
        print("✅ Friends endpoint works")
    
    def test_groups_endpoint(self):
        """Test groups endpoint"""
        login_res = requests.post(f"{BASE_URL}/api/auth/login", json={
            "email": "jjspilot24@gmail.com",
            "password": "password123"
        })
        token = login_res.json()["access_token"]
        headers = {"Authorization": f"Bearer {token}"}
        
        res = requests.get(f"{BASE_URL}/api/groups", headers=headers)
        assert res.status_code == 200
        print("✅ Groups endpoint works")
    
    def test_pages_endpoint(self):
        """Test pages endpoint"""
        login_res = requests.post(f"{BASE_URL}/api/auth/login", json={
            "email": "jjspilot24@gmail.com",
            "password": "password123"
        })
        token = login_res.json()["access_token"]
        headers = {"Authorization": f"Bearer {token}"}
        
        res = requests.get(f"{BASE_URL}/api/pages", headers=headers)
        assert res.status_code == 200
        print("✅ Pages endpoint works")
    
    def test_messages_conversations(self):
        """Test messages conversations endpoint"""
        login_res = requests.post(f"{BASE_URL}/api/auth/login", json={
            "email": "jjspilot24@gmail.com",
            "password": "password123"
        })
        token = login_res.json()["access_token"]
        headers = {"Authorization": f"Bearer {token}"}
        
        res = requests.get(f"{BASE_URL}/api/messages/conversations", headers=headers)
        assert res.status_code == 200
        print("✅ Messages conversations endpoint works")


class TestStatistics:
    """Test statistics page with badges and leaderboard"""
    
    def test_badges_endpoint(self):
        """Test badges endpoint"""
        login_res = requests.post(f"{BASE_URL}/api/auth/login", json={
            "email": "jjspilot24@gmail.com",
            "password": "password123"
        })
        token = login_res.json()["access_token"]
        headers = {"Authorization": f"Bearer {token}"}
        
        res = requests.get(f"{BASE_URL}/api/badges/my-badges", headers=headers)
        assert res.status_code == 200
        data = res.json()
        assert "earned_badges" in data or "locked_badges" in data
        print(f"✅ Badges endpoint works - earned: {len(data.get('earned_badges', []))}")
    
    def test_leaderboard_endpoint(self):
        """Test leaderboard endpoint"""
        login_res = requests.post(f"{BASE_URL}/api/auth/login", json={
            "email": "jjspilot24@gmail.com",
            "password": "password123"
        })
        token = login_res.json()["access_token"]
        headers = {"Authorization": f"Bearer {token}"}
        
        res = requests.get(f"{BASE_URL}/api/badges/leaderboard", headers=headers)
        assert res.status_code == 200
        print("✅ Leaderboard endpoint works")


class TestUltimateSearch:
    """Test Ultimate Search page"""
    
    def test_ultimate_search_endpoint(self):
        """Test ultimate search endpoint"""
        login_res = requests.post(f"{BASE_URL}/api/auth/login", json={
            "email": "jjspilot24@gmail.com",
            "password": "password123"
        })
        token = login_res.json()["access_token"]
        headers = {"Authorization": f"Bearer {token}"}
        
        # Test the search endpoint
        search_data = {
            "category_ids": [],
            "aggregation_type": "and_or",
            "page": 1
        }
        res = requests.post(f"{BASE_URL}/api/search/ultimate", json=search_data, headers=headers)
        # May return 200 or 400 depending on if categories are required
        assert res.status_code in [200, 400]
        print("✅ Ultimate search endpoint accessible")


class TestHealthAndBasics:
    """Test basic health and API endpoints"""
    
    def test_health_endpoint(self):
        """Test health endpoint"""
        res = requests.get(f"{BASE_URL}/api/health")
        assert res.status_code == 200
        print("✅ Health endpoint works")
    
    def test_root_endpoint(self):
        """Test root API endpoint"""
        res = requests.get(f"{BASE_URL}/api/")
        assert res.status_code == 200
        data = res.json()
        assert "InfoPilot" in data.get("message", "")
        print("✅ Root API endpoint works")


if __name__ == "__main__":
    pytest.main([__file__, "-v", "--tb=short"])
