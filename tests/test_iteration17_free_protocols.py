"""
InfoPilot Explorer - Iteration 17 Tests
Testing FREE protocols ($0.00), Copy endpoint, Newsletter, Statistics, Leaderboard
"""
import pytest
import requests
import os

BASE_URL = os.environ.get('REACT_APP_BACKEND_URL', 'https://infopilot-hub.preview.emergentagent.com')

# Test credentials
ADMIN_EMAIL = "jjspilot24@gmail.com"
ADMIN_PASSWORD = "InfoPilot2024!"


class TestFreeProtocols:
    """Test FREE protocol functionality"""
    
    @pytest.fixture(scope="class")
    def auth_token(self):
        """Get authentication token"""
        response = requests.post(f"{BASE_URL}/api/auth/login", json={
            "email": ADMIN_EMAIL,
            "password": ADMIN_PASSWORD
        })
        if response.status_code == 200:
            return response.json().get("token")
        pytest.skip("Authentication failed")
    
    def test_marketplace_protocols_list(self):
        """Test that marketplace protocols list returns all 12 protocols"""
        response = requests.get(f"{BASE_URL}/api/marketplace/protocols")
        assert response.status_code == 200
        
        data = response.json()
        assert "protocols" in data
        assert len(data["protocols"]) >= 12, f"Expected at least 12 protocols, got {len(data['protocols'])}"
        
        # Check for specific protocols
        protocol_names = [p["name"] for p in data["protocols"]]
        assert any("George Bush" in name for name in protocol_names), "George Bush protocol not found"
        assert any("William C. Gamble" in name for name in protocol_names), "William C. Gamble protocol not found"
        assert any("Richard J. Selman" in name for name in protocol_names), "Richard J. Selman protocol not found"
    
    def test_free_protocol_exists(self):
        """Test that FREE protocol ($0.00) exists in marketplace"""
        response = requests.get(f"{BASE_URL}/api/marketplace/protocols")
        assert response.status_code == 200
        
        data = response.json()
        free_protocols = [p for p in data["protocols"] if p["price"] == 0]
        
        assert len(free_protocols) >= 1, "No FREE protocols found"
        
        # Check is_free flag is present
        for fp in free_protocols:
            assert "is_free" in fp, f"is_free field missing for protocol: {fp['name']}"
            assert fp["is_free"] == True, f"is_free should be True for {fp['name']}"
    
    def test_free_protocol_has_correct_fields(self):
        """Test FREE protocol has all required fields"""
        response = requests.get(f"{BASE_URL}/api/marketplace/protocols")
        assert response.status_code == 200
        
        data = response.json()
        free_protocols = [p for p in data["protocols"] if p["price"] == 0]
        
        if free_protocols:
            fp = free_protocols[0]
            required_fields = ["id", "name", "description", "price", "category", "creator_name", "is_free"]
            for field in required_fields:
                assert field in fp, f"Missing field: {field}"
    
    def test_copy_free_protocol_without_auth(self):
        """Test copying FREE protocol without authentication"""
        # First get a FREE protocol ID
        response = requests.get(f"{BASE_URL}/api/marketplace/protocols")
        assert response.status_code == 200
        
        data = response.json()
        free_protocols = [p for p in data["protocols"] if p["price"] == 0]
        
        if not free_protocols:
            pytest.skip("No FREE protocols available")
        
        free_protocol_id = free_protocols[0]["id"]
        
        # Try to copy without auth
        copy_response = requests.post(f"{BASE_URL}/api/marketplace/protocols/{free_protocol_id}/copy")
        assert copy_response.status_code == 200, f"Copy failed: {copy_response.text}"
        
        copy_data = copy_response.json()
        assert copy_data["success"] == True
        assert "protocol" in copy_data
        assert copy_data["is_free"] == True
    
    def test_copy_paid_protocol_without_auth_fails(self):
        """Test that copying paid protocol without auth fails"""
        response = requests.get(f"{BASE_URL}/api/marketplace/protocols")
        assert response.status_code == 200
        
        data = response.json()
        paid_protocols = [p for p in data["protocols"] if p["price"] > 0]
        
        if not paid_protocols:
            pytest.skip("No paid protocols available")
        
        paid_protocol_id = paid_protocols[0]["id"]
        
        # Try to copy without auth - should fail
        copy_response = requests.post(f"{BASE_URL}/api/marketplace/protocols/{paid_protocol_id}/copy")
        assert copy_response.status_code == 401, "Should require auth for paid protocols"


class TestCreateFreeProtocol:
    """Test creating FREE protocols"""
    
    @pytest.fixture(scope="class")
    def auth_token(self):
        """Get authentication token"""
        response = requests.post(f"{BASE_URL}/api/auth/login", json={
            "email": ADMIN_EMAIL,
            "password": ADMIN_PASSWORD
        })
        if response.status_code == 200:
            return response.json().get("token")
        pytest.skip("Authentication failed")
    
    def test_create_free_protocol(self, auth_token):
        """Test creating a FREE protocol with price=0"""
        import time
        unique_name = f"TEST_FREE_Protocol_{int(time.time())}"
        
        response = requests.post(
            f"{BASE_URL}/api/marketplace/protocols",
            headers={"Authorization": f"Bearer {auth_token}"},
            json={
                "name": unique_name,
                "description": "A test FREE protocol for testing",
                "protocol": "(test or example) site:example.com",  # Valid protocol format
                "price": 0.0,
                "category": "General",
                "tags": ["test", "free"]
            }
        )
        
        assert response.status_code == 200, f"Create failed: {response.text}"
        
        data = response.json()
        assert data["is_free"] == True
        assert data["price"] == 0.0
        assert "FREE" in data["message"] or "free" in data["message"].lower()
    
    def test_price_validation_allows_zero(self, auth_token):
        """Test that price validation allows $0.00"""
        import time
        unique_name = f"TEST_Zero_Price_{int(time.time())}"
        
        response = requests.post(
            f"{BASE_URL}/api/marketplace/protocols",
            headers={"Authorization": f"Bearer {auth_token}"},
            json={
                "name": unique_name,
                "description": "Testing zero price",
                "protocol": "(zero or price) site:test.com",  # Valid protocol format
                "price": 0.00,
                "category": "General",
                "tags": []
            }
        )
        
        assert response.status_code == 200, f"Zero price should be allowed: {response.text}"
    
    def test_price_validation_max_limit(self, auth_token):
        """Test that price validation enforces max $99.99"""
        import time
        unique_name = f"TEST_Max_Price_{int(time.time())}"
        
        response = requests.post(
            f"{BASE_URL}/api/marketplace/protocols",
            headers={"Authorization": f"Bearer {auth_token}"},
            json={
                "name": unique_name,
                "description": "Testing max price",
                "protocol": "(max or price) site:test.com",  # Valid protocol format
                "price": 100.00,  # Over limit
                "category": "General",
                "tags": []
            }
        )
        
        # 400 or 422 are both valid rejection codes
        assert response.status_code in [400, 422], f"Price over $99.99 should be rejected, got {response.status_code}"


class TestStatisticsDashboard:
    """Test Statistics Dashboard API"""
    
    def test_statistics_dashboard_endpoint(self):
        """Test GET /api/statistics/dashboard"""
        response = requests.get(f"{BASE_URL}/api/statistics/dashboard")
        assert response.status_code == 200
        
        data = response.json()
        
        # Check required sections
        assert "overview" in data
        assert "countries" in data
        assert "us_states" in data
        assert "document_types" in data
        assert "top_words" in data
        
        # Check overview has required fields
        overview = data["overview"]
        assert "total_users" in overview
        assert "total_protocols" in overview
        assert "total_searches" in overview
    
    def test_statistics_overview_endpoint(self):
        """Test GET /api/statistics/overview"""
        response = requests.get(f"{BASE_URL}/api/statistics/overview")
        assert response.status_code == 200
        
        data = response.json()
        assert "total_users" in data
        assert "total_protocols" in data
        assert data["total_protocols"] >= 12, "Should have at least 12 protocols"
    
    def test_statistics_countries_endpoint(self):
        """Test GET /api/statistics/countries"""
        response = requests.get(f"{BASE_URL}/api/statistics/countries")
        assert response.status_code == 200
        
        data = response.json()
        assert "countries" in data
        assert len(data["countries"]) > 0
    
    def test_statistics_us_states_endpoint(self):
        """Test GET /api/statistics/us-states"""
        response = requests.get(f"{BASE_URL}/api/statistics/us-states")
        assert response.status_code == 200
        
        data = response.json()
        assert "states" in data
        # Check Maine is included (Brunswick connection)
        state_names = [s["name"] for s in data["states"]]
        assert "Maine" in state_names, "Maine should be in US states"


class TestLeaderboard:
    """Test Top Sellers Leaderboard APIs"""
    
    def test_leaderboard_sales_endpoint(self):
        """Test GET /api/marketplace/leaderboard/sales"""
        response = requests.get(f"{BASE_URL}/api/marketplace/leaderboard/sales")
        assert response.status_code == 200
        
        data = response.json()
        assert "leaderboard" in data
        assert "type" in data
        assert data["type"] == "sales"
        
        if data["leaderboard"]:
            first = data["leaderboard"][0]
            assert "rank" in first
            assert "creator_name" in first
            assert "total_sales" in first
            assert "badge" in first
            assert "title" in first
    
    def test_leaderboard_revenue_endpoint(self):
        """Test GET /api/marketplace/leaderboard/revenue"""
        response = requests.get(f"{BASE_URL}/api/marketplace/leaderboard/revenue")
        assert response.status_code == 200
        
        data = response.json()
        assert "leaderboard" in data
        assert "type" in data
        assert data["type"] == "revenue"
        
        if data["leaderboard"]:
            first = data["leaderboard"][0]
            assert "rank" in first
            assert "creator_name" in first
            assert "total_revenue" in first
            assert "badge" in first
            assert "title" in first
    
    def test_leaderboard_has_funny_titles(self):
        """Test that leaderboard has funny titles"""
        response = requests.get(f"{BASE_URL}/api/marketplace/leaderboard/sales")
        assert response.status_code == 200
        
        data = response.json()
        if data["leaderboard"]:
            titles = [l["title"] for l in data["leaderboard"]]
            # Check for expected funny titles
            funny_keywords = ["Overlord", "Searcher", "Boolean", "Wizard", "Dynamo", "Pioneer"]
            has_funny = any(any(kw in t for kw in funny_keywords) for t in titles)
            assert has_funny, f"Expected funny titles, got: {titles}"


class TestNewsletterGeneration:
    """Test Newsletter Generation API"""
    
    @pytest.fixture(scope="class")
    def auth_token(self):
        """Get authentication token"""
        response = requests.post(f"{BASE_URL}/api/auth/login", json={
            "email": ADMIN_EMAIL,
            "password": ADMIN_PASSWORD
        })
        if response.status_code == 200:
            return response.json().get("token")
        pytest.skip("Authentication failed")
    
    def test_newsletter_generate_endpoint(self, auth_token):
        """Test POST /api/admin/newsletter/generate"""
        response = requests.post(
            f"{BASE_URL}/api/admin/newsletter/generate",
            headers={"Authorization": f"Bearer {auth_token}"}
        )
        assert response.status_code == 200
        
        data = response.json()
        assert "content" in data
        
        content = data["content"]
        # Check for funny/supernatural comedy elements
        assert len(content) > 100, "Newsletter content should be substantial"
        
        # Check for expected elements
        content_lower = content.lower()
        has_book_promo = "letters to evelyn" in content_lower or "book" in content_lower
        has_marketplace = "marketplace" in content_lower or "protocol" in content_lower
        
        assert has_book_promo or has_marketplace, "Newsletter should mention book or marketplace"
    
    def test_newsletter_requires_admin(self):
        """Test that newsletter generation requires admin auth"""
        response = requests.post(f"{BASE_URL}/api/admin/newsletter/generate")
        assert response.status_code in [401, 403], "Should require authentication"


class TestMarketplaceProtocolsComplete:
    """Test all 12 marketplace protocols are present"""
    
    def test_all_protocols_present(self):
        """Verify all 12 protocols including George Bush, William C. Gamble, Richard J. Selman"""
        response = requests.get(f"{BASE_URL}/api/marketplace/protocols")
        assert response.status_code == 200
        
        data = response.json()
        protocols = data["protocols"]
        
        assert len(protocols) >= 12, f"Expected at least 12 protocols, got {len(protocols)}"
        
        # Check for specific required protocols
        protocol_names = [p["name"].lower() for p in protocols]
        
        # George Bush
        assert any("george bush" in name for name in protocol_names), "George Bush protocol missing"
        
        # William C. Gamble
        assert any("william" in name and "gamble" in name for name in protocol_names), "William C. Gamble protocol missing"
        
        # Richard J. Selman
        assert any("richard" in name and "selman" in name for name in protocol_names), "Richard J. Selman protocol missing"
        
        # FREE protocol
        free_protocols = [p for p in protocols if p["price"] == 0]
        assert len(free_protocols) >= 1, "FREE protocol missing"
    
    def test_protocol_price_range(self):
        """Test that protocol prices are in valid range $0.00 - $99.99"""
        response = requests.get(f"{BASE_URL}/api/marketplace/protocols")
        assert response.status_code == 200
        
        data = response.json()
        for p in data["protocols"]:
            assert 0 <= p["price"] <= 99.99, f"Invalid price for {p['name']}: ${p['price']}"


if __name__ == "__main__":
    pytest.main([__file__, "-v", "--tb=short"])
