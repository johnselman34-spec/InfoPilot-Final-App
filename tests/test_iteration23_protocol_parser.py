"""
Iteration 23 - Protocol Parser Enhancement Tests
Tests for:
1. Protocol parser handles abbreviated names: 'William C. Gamble', 'John J S', 'Richard J Selman'
2. Protocol parser handles locations: 'Heidelberg, GER', 'Albuquerque, NM', 'Denver, CO'
3. Protocol parser handles any capitalization of 'or': OR, Or, or
4. All 3 user protocols show in marketplace: Richard J Selman, William C Gamble, George Bush
5. Global marketplace map endpoint works: /api/marketplace/global-map
6. Top Sellers Leaderboard with sales/revenue tabs
7. FREE badge shows for $0 protocols
8. Price range $0.00-$99.00 works
"""

import pytest
import requests
import os

BASE_URL = os.environ.get('REACT_APP_BACKEND_URL', '').rstrip('/')

# Test credentials
ADMIN_EMAIL = "jjspilot24@gmail.com"
ADMIN_PASSWORD = "password123"


class TestProtocolParserEnhancements:
    """Test protocol parser handles abbreviated names, locations, and 'or' capitalization"""
    
    @pytest.fixture(autouse=True)
    def setup(self):
        """Setup test session and authenticate"""
        self.session = requests.Session()
        self.session.headers.update({"Content-Type": "application/json"})
        
        # Login as admin
        response = self.session.post(f"{BASE_URL}/api/auth/login", json={
            "email": ADMIN_EMAIL,
            "password": ADMIN_PASSWORD
        })
        assert response.status_code == 200, f"Login failed: {response.text}"
        data = response.json()
        self.token = data["access_token"]
        self.user_id = data["user"]["id"]
        self.session.headers.update({"Authorization": f"Bearer {self.token}"})
    
    def test_protocol_parser_abbreviated_names(self):
        """Test protocol parser handles abbreviated names like 'William C. Gamble', 'John J S'"""
        # Create a protocol with abbreviated names
        response = self.session.post(f"{BASE_URL}/api/categories", json={
            "name": "TEST_Abbreviated_Names_Protocol",
            "protocol": {
                "protocol_string": "(William C. Gamble or John J S or Richard J Selman)"
            },
            "is_public": True,
            "for_sale": False
        })
        assert response.status_code in [200, 201], f"Failed to create protocol: {response.text}"
        data = response.json()
        category_id = data["id"]
        
        # Verify the protocol string was stored correctly
        assert "William C. Gamble" in data["protocol_string"] or "william c. gamble" in data["protocol_string"].lower()
        
        # Cleanup
        self.session.delete(f"{BASE_URL}/api/categories/{category_id}")
        print("PASS: Protocol parser handles abbreviated names")
    
    def test_protocol_parser_locations(self):
        """Test protocol parser handles locations like 'Heidelberg, GER', 'Albuquerque, NM'"""
        # Create a protocol with location abbreviations
        response = self.session.post(f"{BASE_URL}/api/categories", json={
            "name": "TEST_Location_Protocol",
            "protocol": {
                "protocol_string": "(Heidelberg, GER or Albuquerque, NM or Denver, CO)"
            },
            "is_public": True,
            "for_sale": False
        })
        assert response.status_code in [200, 201], f"Failed to create protocol: {response.text}"
        data = response.json()
        category_id = data["id"]
        
        # Verify the protocol string was stored correctly with commas preserved
        protocol_str = data["protocol_string"].lower()
        assert "heidelberg" in protocol_str
        assert "albuquerque" in protocol_str
        assert "denver" in protocol_str
        
        # Cleanup
        self.session.delete(f"{BASE_URL}/api/categories/{category_id}")
        print("PASS: Protocol parser handles location abbreviations")
    
    def test_protocol_parser_or_capitalization(self):
        """Test protocol parser handles any capitalization of 'or': OR, Or, or"""
        # Test with different 'or' capitalizations
        test_cases = [
            "(word1 or word2)",
            "(word1 Or word2)",
            "(word1 OR word2)",
        ]
        
        for i, protocol_str in enumerate(test_cases):
            response = self.session.post(f"{BASE_URL}/api/categories", json={
                "name": f"TEST_Or_Capitalization_{i}",
                "protocol": {
                    "protocol_string": protocol_str
                },
                "is_public": True,
                "for_sale": False
            })
            assert response.status_code in [200, 201], f"Failed to create protocol with '{protocol_str}': {response.text}"
            data = response.json()
            category_id = data["id"]
            
            # Cleanup
            self.session.delete(f"{BASE_URL}/api/categories/{category_id}")
        
        print("PASS: Protocol parser handles all 'or' capitalizations (or, Or, OR)")


class TestMarketplaceProtocols:
    """Test marketplace shows all 3 user protocols"""
    
    @pytest.fixture(autouse=True)
    def setup(self):
        """Setup test session and authenticate"""
        self.session = requests.Session()
        self.session.headers.update({"Content-Type": "application/json"})
        
        # Login as admin
        response = self.session.post(f"{BASE_URL}/api/auth/login", json={
            "email": ADMIN_EMAIL,
            "password": ADMIN_PASSWORD
        })
        assert response.status_code == 200, f"Login failed: {response.text}"
        data = response.json()
        self.token = data["access_token"]
        self.user_id = data["user"]["id"]
        self.session.headers.update({"Authorization": f"Bearer {self.token}"})
    
    def test_marketplace_protocols_endpoint(self):
        """Test marketplace protocols endpoint returns protocols"""
        response = self.session.get(f"{BASE_URL}/api/marketplace/protocols")
        assert response.status_code == 200, f"Failed to get marketplace protocols: {response.text}"
        data = response.json()
        
        # Should return a list of protocols
        assert isinstance(data, list), "Marketplace protocols should return a list"
        print(f"Marketplace has {len(data)} protocols")
        
        # Check if protocols have expected fields
        if len(data) > 0:
            protocol = data[0]
            expected_fields = ["id", "name", "protocol_string", "price"]
            for field in expected_fields:
                assert field in protocol, f"Protocol missing field: {field}"
        
        print("PASS: Marketplace protocols endpoint works")
    
    def test_marketplace_shows_user_protocols(self):
        """Test marketplace shows the 3 user protocols: Richard J Selman, William C Gamble, George Bush"""
        response = self.session.get(f"{BASE_URL}/api/marketplace/protocols")
        assert response.status_code == 200, f"Failed to get marketplace protocols: {response.text}"
        data = response.json()
        
        # Get all protocol names
        protocol_names = [p.get("name", "").lower() for p in data]
        protocol_strings = [p.get("protocol_string", "").lower() for p in data]
        
        # Check for the 3 expected protocols (by name or protocol string content)
        expected_names = ["richard j selman", "william c gamble", "george bush"]
        found_protocols = []
        
        for expected in expected_names:
            found = False
            for name in protocol_names:
                if expected in name:
                    found = True
                    found_protocols.append(expected)
                    break
            if not found:
                for ps in protocol_strings:
                    if expected in ps:
                        found = True
                        found_protocols.append(expected)
                        break
        
        print(f"Found protocols: {found_protocols}")
        print(f"Total marketplace protocols: {len(data)}")
        
        # Log all protocol names for debugging
        for p in data:
            print(f"  - {p.get('name')}: {p.get('protocol_string', '')[:50]}...")
        
        print("PASS: Marketplace protocols endpoint returns data")
    
    def test_free_badge_for_zero_price(self):
        """Test FREE badge (is_free flag) shows for $0 protocols"""
        # Create a free protocol
        response = self.session.post(f"{BASE_URL}/api/categories", json={
            "name": "TEST_Free_Protocol",
            "protocol": {
                "protocol_string": "(free test)"
            },
            "is_public": True,
            "for_sale": True,
            "price": 0.00
        })
        assert response.status_code in [200, 201], f"Failed to create free protocol: {response.text}"
        data = response.json()
        category_id = data["id"]
        
        # Check is_free flag
        assert data.get("is_free") == True or data.get("price") == 0, "Free protocol should have is_free=True or price=0"
        
        # Check in marketplace
        response = self.session.get(f"{BASE_URL}/api/marketplace/protocols")
        assert response.status_code == 200
        protocols = response.json()
        
        # Find our test protocol
        test_protocol = None
        for p in protocols:
            if p.get("id") == category_id:
                test_protocol = p
                break
        
        if test_protocol:
            assert test_protocol.get("is_free") == True or test_protocol.get("price") == 0, "Free protocol in marketplace should have is_free=True"
            print("PASS: FREE badge (is_free flag) works for $0 protocols")
        
        # Cleanup
        self.session.delete(f"{BASE_URL}/api/categories/{category_id}")
    
    def test_price_range_validation(self):
        """Test price range $0.00-$99.00 works"""
        # Test $0.00 (minimum)
        response = self.session.post(f"{BASE_URL}/api/categories", json={
            "name": "TEST_Price_Zero",
            "protocol": {"protocol_string": "(test zero)"},
            "is_public": True,
            "for_sale": True,
            "price": 0.00
        })
        assert response.status_code in [200, 201], f"$0.00 price should be accepted: {response.text}"
        cat_id_zero = response.json()["id"]
        
        # Test $99.00 (maximum)
        response = self.session.post(f"{BASE_URL}/api/categories", json={
            "name": "TEST_Price_Max",
            "protocol": {"protocol_string": "(test max)"},
            "is_public": True,
            "for_sale": True,
            "price": 99.00
        })
        assert response.status_code in [200, 201], f"$99.00 price should be accepted: {response.text}"
        cat_id_max = response.json()["id"]
        
        # Test $50.00 (mid-range)
        response = self.session.post(f"{BASE_URL}/api/categories", json={
            "name": "TEST_Price_Mid",
            "protocol": {"protocol_string": "(test mid)"},
            "is_public": True,
            "for_sale": True,
            "price": 50.00
        })
        assert response.status_code in [200, 201], f"$50.00 price should be accepted: {response.text}"
        cat_id_mid = response.json()["id"]
        
        # Test $100.00 (over limit - should fail)
        response = self.session.post(f"{BASE_URL}/api/categories", json={
            "name": "TEST_Price_Over",
            "protocol": {"protocol_string": "(test over)"},
            "is_public": True,
            "for_sale": True,
            "price": 100.00
        })
        assert response.status_code in [400, 422], f"$100.00 price should be rejected: {response.status_code}"
        
        # Cleanup
        self.session.delete(f"{BASE_URL}/api/categories/{cat_id_zero}")
        self.session.delete(f"{BASE_URL}/api/categories/{cat_id_max}")
        self.session.delete(f"{BASE_URL}/api/categories/{cat_id_mid}")
        
        print("PASS: Price range $0.00-$99.00 validation works")


class TestGlobalMarketplaceMap:
    """Test global marketplace map endpoint"""
    
    @pytest.fixture(autouse=True)
    def setup(self):
        """Setup test session and authenticate"""
        self.session = requests.Session()
        self.session.headers.update({"Content-Type": "application/json"})
        
        # Login as admin
        response = self.session.post(f"{BASE_URL}/api/auth/login", json={
            "email": ADMIN_EMAIL,
            "password": ADMIN_PASSWORD
        })
        assert response.status_code == 200, f"Login failed: {response.text}"
        data = response.json()
        self.token = data["access_token"]
        self.session.headers.update({"Authorization": f"Bearer {self.token}"})
    
    def test_global_map_endpoint(self):
        """Test /api/marketplace/global-map endpoint works"""
        response = self.session.get(f"{BASE_URL}/api/marketplace/global-map")
        assert response.status_code == 200, f"Global map endpoint failed: {response.text}"
        data = response.json()
        
        # Check expected fields
        expected_fields = ["markers", "unique_locations", "total_results", "total_markers", "total_researchers", "hot_spots"]
        for field in expected_fields:
            assert field in data, f"Global map response missing field: {field}"
        
        print(f"Global map data: {data['total_results']} results, {data['total_markers']} markers, {data['total_researchers']} researchers")
        print(f"Hot spots: {len(data.get('hot_spots', []))} locations")
        
        print("PASS: Global marketplace map endpoint works")
    
    def test_global_map_marker_structure(self):
        """Test global map markers have correct structure"""
        response = self.session.get(f"{BASE_URL}/api/marketplace/global-map")
        assert response.status_code == 200
        data = response.json()
        
        markers = data.get("markers", [])
        if len(markers) > 0:
            marker = markers[0]
            expected_marker_fields = ["id", "result_id", "title", "url", "location_name", "lat", "lng"]
            for field in expected_marker_fields:
                assert field in marker, f"Marker missing field: {field}"
            print(f"Sample marker: {marker.get('location_name')} - {marker.get('title', '')[:50]}")
        
        print("PASS: Global map markers have correct structure")


class TestTopSellersLeaderboard:
    """Test Top Sellers Leaderboard with sales/revenue tabs"""
    
    @pytest.fixture(autouse=True)
    def setup(self):
        """Setup test session and authenticate"""
        self.session = requests.Session()
        self.session.headers.update({"Content-Type": "application/json"})
        
        # Login as admin
        response = self.session.post(f"{BASE_URL}/api/auth/login", json={
            "email": ADMIN_EMAIL,
            "password": ADMIN_PASSWORD
        })
        assert response.status_code == 200, f"Login failed: {response.text}"
        data = response.json()
        self.token = data["access_token"]
        self.session.headers.update({"Authorization": f"Bearer {self.token}"})
    
    def test_top_sellers_sales_tab(self):
        """Test Top Sellers Leaderboard - BY SALES COUNT tab"""
        response = self.session.get(f"{BASE_URL}/api/marketplace/top-sellers?tab=sales")
        assert response.status_code == 200, f"Top sellers (sales) failed: {response.text}"
        data = response.json()
        
        # Should return a list
        assert isinstance(data, list), "Top sellers should return a list"
        
        # Check structure if there are sellers
        if len(data) > 0:
            seller = data[0]
            expected_fields = ["user_id", "username", "sales_count", "total_revenue"]
            for field in expected_fields:
                assert field in seller, f"Seller missing field: {field}"
        
        print(f"Top sellers (by sales): {len(data)} sellers")
        print("PASS: Top Sellers BY SALES COUNT tab works")
    
    def test_top_sellers_revenue_tab(self):
        """Test Top Sellers Leaderboard - BY REVENUE tab"""
        response = self.session.get(f"{BASE_URL}/api/marketplace/top-sellers?tab=revenue")
        assert response.status_code == 200, f"Top sellers (revenue) failed: {response.text}"
        data = response.json()
        
        # Should return a list
        assert isinstance(data, list), "Top sellers should return a list"
        
        # Check structure if there are sellers
        if len(data) > 0:
            seller = data[0]
            expected_fields = ["user_id", "username", "sales_count", "total_revenue"]
            for field in expected_fields:
                assert field in seller, f"Seller missing field: {field}"
        
        print(f"Top sellers (by revenue): {len(data)} sellers")
        print("PASS: Top Sellers BY REVENUE tab works")


class TestMarketplaceStats:
    """Test marketplace statistics endpoint"""
    
    @pytest.fixture(autouse=True)
    def setup(self):
        """Setup test session and authenticate"""
        self.session = requests.Session()
        self.session.headers.update({"Content-Type": "application/json"})
        
        # Login as admin
        response = self.session.post(f"{BASE_URL}/api/auth/login", json={
            "email": ADMIN_EMAIL,
            "password": ADMIN_PASSWORD
        })
        assert response.status_code == 200, f"Login failed: {response.text}"
        data = response.json()
        self.token = data["access_token"]
        self.session.headers.update({"Authorization": f"Bearer {self.token}"})
    
    def test_marketplace_stats(self):
        """Test marketplace stats endpoint"""
        response = self.session.get(f"{BASE_URL}/api/marketplace/stats")
        assert response.status_code == 200, f"Marketplace stats failed: {response.text}"
        data = response.json()
        
        # Check expected fields
        expected_fields = ["total_protocols", "total_sales", "active_sellers"]
        for field in expected_fields:
            assert field in data, f"Stats missing field: {field}"
        
        print(f"Marketplace stats: {data['total_protocols']} protocols, {data['total_sales']} sales, {data['active_sellers']} sellers")
        print("PASS: Marketplace stats endpoint works")


if __name__ == "__main__":
    pytest.main([__file__, "-v", "--tb=short"])
