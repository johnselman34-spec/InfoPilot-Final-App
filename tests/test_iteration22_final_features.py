"""
Iteration 22 - Final Feature Testing
Tests for:
1. Price range $0.00-$99.00 (not just $0.75-$2.99)
2. FREE badge for $0 protocols (is_free flag)
3. Top Sellers Leaderboard with sales and revenue tabs
4. My Sales endpoint with statistics
5. Marketplace showing all for-sale protocols
6. Admin login with is_admin=true
7. Protocol parser abbreviation handling
"""

import pytest
import requests
import os

BASE_URL = os.environ.get('REACT_APP_BACKEND_URL', '').rstrip('/')

# Test credentials
ADMIN_EMAIL = "jjspilot24@gmail.com"
ADMIN_PASSWORD = "password123"


class TestAuthentication:
    """Test admin authentication and is_admin flag"""
    
    def test_admin_login_returns_is_admin_true(self):
        """Admin email should return is_admin=true"""
        response = requests.post(f"{BASE_URL}/api/auth/login", json={
            "email": ADMIN_EMAIL,
            "password": ADMIN_PASSWORD
        })
        assert response.status_code == 200, f"Login failed: {response.text}"
        data = response.json()
        
        # Verify is_admin flag
        assert "user" in data, "Response should contain user object"
        assert data["user"].get("is_admin") == True, f"Admin user should have is_admin=true, got: {data['user'].get('is_admin')}"
        assert "access_token" in data, "Response should contain access_token"
        print(f"✓ Admin login successful, is_admin={data['user'].get('is_admin')}")


class TestPriceRangeValidation:
    """Test price range $0.00-$99.00 for sale-settings endpoint"""
    
    @pytest.fixture
    def auth_token(self):
        """Get authentication token"""
        response = requests.post(f"{BASE_URL}/api/auth/login", json={
            "email": ADMIN_EMAIL,
            "password": ADMIN_PASSWORD
        })
        if response.status_code == 200:
            return response.json().get("access_token")
        pytest.skip("Authentication failed")
    
    @pytest.fixture
    def test_category(self, auth_token):
        """Create a test category for price testing"""
        headers = {"Authorization": f"Bearer {auth_token}"}
        response = requests.post(f"{BASE_URL}/api/categories", json={
            "name": "TEST_Price_Range_Category",
            "protocol": {"protocol_string": "(test price range)"},
            "is_public": False
        }, headers=headers)
        
        if response.status_code in [200, 201]:
            category = response.json()
            yield category
            # Cleanup
            requests.delete(f"{BASE_URL}/api/categories/{category['id']}", headers=headers)
        else:
            pytest.skip(f"Failed to create test category: {response.text}")
    
    def test_price_zero_allowed_for_free_protocol(self, auth_token, test_category):
        """Price $0.00 should be allowed for FREE protocols"""
        headers = {"Authorization": f"Bearer {auth_token}"}
        response = requests.put(
            f"{BASE_URL}/api/categories/{test_category['id']}/sale-settings",
            params={"for_sale": True, "price": 0.00},
            headers=headers
        )
        assert response.status_code == 200, f"Setting price to $0.00 failed: {response.text}"
        data = response.json()
        
        # Verify is_free flag is set
        assert data.get("is_free") == True, f"is_free should be True for $0.00 price, got: {data.get('is_free')}"
        assert data.get("price") == 0.00 or data.get("price") == 0, f"Price should be 0.00, got: {data.get('price')}"
        print(f"✓ Price $0.00 accepted, is_free={data.get('is_free')}")
    
    def test_price_max_99_allowed(self, auth_token, test_category):
        """Price $99.00 should be allowed (max)"""
        headers = {"Authorization": f"Bearer {auth_token}"}
        response = requests.put(
            f"{BASE_URL}/api/categories/{test_category['id']}/sale-settings",
            params={"for_sale": True, "price": 99.00},
            headers=headers
        )
        assert response.status_code == 200, f"Setting price to $99.00 failed: {response.text}"
        data = response.json()
        assert data.get("price") == 99.00, f"Price should be 99.00, got: {data.get('price')}"
        assert data.get("is_free") == False, f"is_free should be False for $99.00, got: {data.get('is_free')}"
        print(f"✓ Price $99.00 accepted, is_free={data.get('is_free')}")
    
    def test_price_mid_range_allowed(self, auth_token, test_category):
        """Price $50.00 should be allowed (mid-range)"""
        headers = {"Authorization": f"Bearer {auth_token}"}
        response = requests.put(
            f"{BASE_URL}/api/categories/{test_category['id']}/sale-settings",
            params={"for_sale": True, "price": 50.00},
            headers=headers
        )
        assert response.status_code == 200, f"Setting price to $50.00 failed: {response.text}"
        data = response.json()
        assert data.get("price") == 50.00, f"Price should be 50.00, got: {data.get('price')}"
        print(f"✓ Price $50.00 accepted")
    
    def test_price_over_99_rejected(self, auth_token, test_category):
        """Price over $99.00 should be rejected"""
        headers = {"Authorization": f"Bearer {auth_token}"}
        response = requests.put(
            f"{BASE_URL}/api/categories/{test_category['id']}/sale-settings",
            params={"for_sale": True, "price": 100.00},
            headers=headers
        )
        # Should return 400 or 422 for validation error
        assert response.status_code in [400, 422], f"Price $100.00 should be rejected, got status {response.status_code}"
        print(f"✓ Price $100.00 correctly rejected with status {response.status_code}")
    
    def test_negative_price_rejected(self, auth_token, test_category):
        """Negative price should be rejected"""
        headers = {"Authorization": f"Bearer {auth_token}"}
        response = requests.put(
            f"{BASE_URL}/api/categories/{test_category['id']}/sale-settings",
            params={"for_sale": True, "price": -1.00},
            headers=headers
        )
        # Should return 400 or 422 for validation error
        assert response.status_code in [400, 422], f"Negative price should be rejected, got status {response.status_code}"
        print(f"✓ Negative price correctly rejected with status {response.status_code}")


class TestTopSellersLeaderboard:
    """Test Top Sellers Leaderboard with sales and revenue tabs"""
    
    @pytest.fixture
    def auth_token(self):
        """Get authentication token"""
        response = requests.post(f"{BASE_URL}/api/auth/login", json={
            "email": ADMIN_EMAIL,
            "password": ADMIN_PASSWORD
        })
        if response.status_code == 200:
            return response.json().get("access_token")
        pytest.skip("Authentication failed")
    
    def test_top_sellers_sales_tab(self, auth_token):
        """Top sellers endpoint with tab=sales should work"""
        headers = {"Authorization": f"Bearer {auth_token}"}
        response = requests.get(
            f"{BASE_URL}/api/marketplace/top-sellers",
            params={"tab": "sales"},
            headers=headers
        )
        assert response.status_code == 200, f"Top sellers (sales) failed: {response.text}"
        data = response.json()
        
        assert "tab" in data, "Response should contain tab field"
        assert data["tab"] == "sales", f"Tab should be 'sales', got: {data['tab']}"
        assert "leaderboard" in data, "Response should contain leaderboard"
        assert "total_sellers" in data, "Response should contain total_sellers"
        print(f"✓ Top sellers (sales tab) returned {len(data['leaderboard'])} sellers")
    
    def test_top_sellers_revenue_tab(self, auth_token):
        """Top sellers endpoint with tab=revenue should work"""
        headers = {"Authorization": f"Bearer {auth_token}"}
        response = requests.get(
            f"{BASE_URL}/api/marketplace/top-sellers",
            params={"tab": "revenue"},
            headers=headers
        )
        assert response.status_code == 200, f"Top sellers (revenue) failed: {response.text}"
        data = response.json()
        
        assert "tab" in data, "Response should contain tab field"
        assert data["tab"] == "revenue", f"Tab should be 'revenue', got: {data['tab']}"
        assert "leaderboard" in data, "Response should contain leaderboard"
        print(f"✓ Top sellers (revenue tab) returned {len(data['leaderboard'])} sellers")
    
    def test_top_sellers_leaderboard_structure(self, auth_token):
        """Verify leaderboard entry structure"""
        headers = {"Authorization": f"Bearer {auth_token}"}
        response = requests.get(
            f"{BASE_URL}/api/marketplace/top-sellers",
            params={"tab": "sales"},
            headers=headers
        )
        assert response.status_code == 200
        data = response.json()
        
        if data["leaderboard"]:
            seller = data["leaderboard"][0]
            expected_fields = ["user_id", "username", "sales_count", "total_revenue", "earnings_after_split", "rank"]
            for field in expected_fields:
                assert field in seller, f"Seller entry should contain '{field}'"
            print(f"✓ Leaderboard entry structure verified: {list(seller.keys())}")
        else:
            print("✓ Leaderboard is empty (no sales yet)")


class TestMySalesEndpoint:
    """Test My Sales statistics endpoint"""
    
    @pytest.fixture
    def auth_token(self):
        """Get authentication token"""
        response = requests.post(f"{BASE_URL}/api/auth/login", json={
            "email": ADMIN_EMAIL,
            "password": ADMIN_PASSWORD
        })
        if response.status_code == 200:
            return response.json().get("access_token")
        pytest.skip("Authentication failed")
    
    def test_my_sales_endpoint_returns_statistics(self, auth_token):
        """My sales endpoint should return proper statistics"""
        headers = {"Authorization": f"Bearer {auth_token}"}
        response = requests.get(f"{BASE_URL}/api/marketplace/my-sales", headers=headers)
        
        assert response.status_code == 200, f"My sales endpoint failed: {response.text}"
        data = response.json()
        
        # Verify required fields
        expected_fields = ["total_sales", "total_revenue", "earnings_after_split", "pending_sales", "unique_buyers", "platform_fee_percentage"]
        for field in expected_fields:
            assert field in data, f"Response should contain '{field}'"
        
        # Verify platform fee is 10%
        assert data["platform_fee_percentage"] == 10, f"Platform fee should be 10%, got: {data['platform_fee_percentage']}"
        
        # Verify earnings calculation (90% of revenue)
        if data["total_revenue"] > 0:
            expected_earnings = round(data["total_revenue"] * 0.90, 2)
            assert abs(data["earnings_after_split"] - expected_earnings) < 0.01, \
                f"Earnings should be 90% of revenue. Expected {expected_earnings}, got {data['earnings_after_split']}"
        
        print(f"✓ My sales statistics: {data}")


class TestMarketplaceProtocols:
    """Test Marketplace showing all for-sale protocols"""
    
    @pytest.fixture
    def auth_token(self):
        """Get authentication token"""
        response = requests.post(f"{BASE_URL}/api/auth/login", json={
            "email": ADMIN_EMAIL,
            "password": ADMIN_PASSWORD
        })
        if response.status_code == 200:
            return response.json().get("access_token")
        pytest.skip("Authentication failed")
    
    def test_marketplace_protocols_endpoint(self, auth_token):
        """Marketplace protocols endpoint should return for-sale protocols"""
        headers = {"Authorization": f"Bearer {auth_token}"}
        response = requests.get(f"{BASE_URL}/api/marketplace/protocols", headers=headers)
        
        assert response.status_code == 200, f"Marketplace protocols failed: {response.text}"
        data = response.json()
        
        assert "protocols" in data, "Response should contain protocols"
        print(f"✓ Marketplace returned {len(data['protocols'])} protocols for sale")
        
        # Verify protocol structure if any exist
        if data["protocols"]:
            protocol = data["protocols"][0]
            expected_fields = ["id", "name", "price", "owner_username"]
            for field in expected_fields:
                assert field in protocol, f"Protocol should contain '{field}'"
            
            # Check is_free flag for $0 protocols
            if protocol.get("price") == 0 or protocol.get("price") == 0.00:
                assert protocol.get("is_free") == True, "Protocol with price $0 should have is_free=True"
                print(f"✓ FREE protocol found: {protocol['name']}")
    
    def test_marketplace_stats_endpoint(self, auth_token):
        """Marketplace stats endpoint should return statistics"""
        headers = {"Authorization": f"Bearer {auth_token}"}
        response = requests.get(f"{BASE_URL}/api/marketplace/stats", headers=headers)
        
        assert response.status_code == 200, f"Marketplace stats failed: {response.text}"
        data = response.json()
        
        expected_fields = ["total_protocols", "total_sales", "active_sellers"]
        for field in expected_fields:
            assert field in data, f"Stats should contain '{field}'"
        
        print(f"✓ Marketplace stats: {data}")


class TestProtocolParserAbbreviations:
    """Test protocol parser handles abbreviations correctly"""
    
    @pytest.fixture
    def auth_token(self):
        """Get authentication token"""
        response = requests.post(f"{BASE_URL}/api/auth/login", json={
            "email": ADMIN_EMAIL,
            "password": ADMIN_PASSWORD
        })
        if response.status_code == 200:
            return response.json().get("access_token")
        pytest.skip("Authentication failed")
    
    def test_protocol_with_name_abbreviation(self, auth_token):
        """Protocol with name like 'William C. Gamble' should be parsed correctly"""
        headers = {"Authorization": f"Bearer {auth_token}"}
        
        # Create category with abbreviation in protocol
        response = requests.post(f"{BASE_URL}/api/categories", json={
            "name": "TEST_Abbreviation_William_C_Gamble",
            "protocol": {"protocol_string": "(William C. Gamble or George Bush)"},
            "is_public": True
        }, headers=headers)
        
        assert response.status_code in [200, 201], f"Failed to create category: {response.text}"
        category = response.json()
        
        # Verify protocol was stored correctly
        assert "William C. Gamble" in category.get("protocol_string", ""), \
            f"Protocol should contain 'William C. Gamble', got: {category.get('protocol_string')}"
        
        print(f"✓ Protocol with abbreviation created: {category.get('protocol_string')}")
        
        # Cleanup
        requests.delete(f"{BASE_URL}/api/categories/{category['id']}", headers=headers)
    
    def test_protocol_with_phd_abbreviation(self, auth_token):
        """Protocol with 'Ph.D.' abbreviation should be parsed correctly"""
        headers = {"Authorization": f"Bearer {auth_token}"}
        
        response = requests.post(f"{BASE_URL}/api/categories", json={
            "name": "TEST_Abbreviation_PhD",
            "protocol": {"protocol_string": "(Ph.D. or Dr. or M.D.)"},
            "is_public": True
        }, headers=headers)
        
        assert response.status_code in [200, 201], f"Failed to create category: {response.text}"
        category = response.json()
        
        # Verify protocol was stored correctly
        assert "Ph.D." in category.get("protocol_string", ""), \
            f"Protocol should contain 'Ph.D.', got: {category.get('protocol_string')}"
        
        print(f"✓ Protocol with Ph.D. abbreviation created: {category.get('protocol_string')}")
        
        # Cleanup
        requests.delete(f"{BASE_URL}/api/categories/{category['id']}", headers=headers)
    
    def test_protocol_with_us_abbreviation(self, auth_token):
        """Protocol with 'U.S.' abbreviation should be parsed correctly"""
        headers = {"Authorization": f"Bearer {auth_token}"}
        
        response = requests.post(f"{BASE_URL}/api/categories", json={
            "name": "TEST_Abbreviation_US",
            "protocol": {"protocol_string": "(U.S. Civil War or American Revolution)"},
            "is_public": True
        }, headers=headers)
        
        assert response.status_code in [200, 201], f"Failed to create category: {response.text}"
        category = response.json()
        
        # Verify protocol was stored correctly
        assert "U.S." in category.get("protocol_string", ""), \
            f"Protocol should contain 'U.S.', got: {category.get('protocol_string')}"
        
        print(f"✓ Protocol with U.S. abbreviation created: {category.get('protocol_string')}")
        
        # Cleanup
        requests.delete(f"{BASE_URL}/api/categories/{category['id']}", headers=headers)


class TestFreeProtocolBadge:
    """Test FREE badge functionality for $0 protocols"""
    
    @pytest.fixture
    def auth_token(self):
        """Get authentication token"""
        response = requests.post(f"{BASE_URL}/api/auth/login", json={
            "email": ADMIN_EMAIL,
            "password": ADMIN_PASSWORD
        })
        if response.status_code == 200:
            return response.json().get("access_token")
        pytest.skip("Authentication failed")
    
    def test_free_protocol_has_is_free_flag(self, auth_token):
        """Protocol with $0 price should have is_free=True"""
        headers = {"Authorization": f"Bearer {auth_token}"}
        
        # Create a private category
        response = requests.post(f"{BASE_URL}/api/categories", json={
            "name": "TEST_Free_Protocol_Badge",
            "protocol": {"protocol_string": "(free test protocol)"},
            "is_public": False
        }, headers=headers)
        
        assert response.status_code in [200, 201], f"Failed to create category: {response.text}"
        category = response.json()
        
        # Set for sale at $0.00
        response = requests.put(
            f"{BASE_URL}/api/categories/{category['id']}/sale-settings",
            params={"for_sale": True, "price": 0.00},
            headers=headers
        )
        
        assert response.status_code == 200, f"Failed to set sale settings: {response.text}"
        data = response.json()
        
        assert data.get("is_free") == True, f"is_free should be True for $0 protocol, got: {data.get('is_free')}"
        assert data.get("for_sale") == True, f"for_sale should be True, got: {data.get('for_sale')}"
        
        print(f"✓ FREE protocol badge: is_free={data.get('is_free')}, price={data.get('price')}")
        
        # Cleanup
        requests.delete(f"{BASE_URL}/api/categories/{category['id']}", headers=headers)
    
    def test_marketplace_shows_free_protocols(self, auth_token):
        """Marketplace should show is_free flag for $0 protocols"""
        headers = {"Authorization": f"Bearer {auth_token}"}
        
        response = requests.get(f"{BASE_URL}/api/marketplace/protocols", headers=headers)
        assert response.status_code == 200
        data = response.json()
        
        # Check if any FREE protocols exist
        free_protocols = [p for p in data.get("protocols", []) if p.get("is_free") or p.get("price") == 0]
        
        if free_protocols:
            print(f"✓ Found {len(free_protocols)} FREE protocols in marketplace")
            for p in free_protocols[:3]:  # Show first 3
                print(f"  - {p.get('name')}: price={p.get('price')}, is_free={p.get('is_free')}")
        else:
            print("✓ No FREE protocols currently in marketplace (this is OK)")


if __name__ == "__main__":
    pytest.main([__file__, "-v", "--tb=short"])
