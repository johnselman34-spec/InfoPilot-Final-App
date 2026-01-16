"""
Iteration 68 - Backend API Tests
Testing MarketplacePage refactoring, CommunityLeaderboard, ProtocolRecommendationEngine
"""
import pytest
import requests
import os

BASE_URL = os.environ.get('REACT_APP_BACKEND_URL', 'https://insightshare-app.preview.emergentagent.com').rstrip('/')

# Test credentials
ADMIN_EMAIL = "jjspilot24@gmail.com"
ADMIN_PASSWORD = "InfoPilot2024!"


class TestHealthAndBasics:
    """Basic health check tests"""
    
    def test_health_endpoint(self):
        """Test health endpoint"""
        response = requests.get(f"{BASE_URL}/api/health")
        assert response.status_code == 200
        data = response.json()
        assert data["status"] == "healthy"
        print("✓ Health endpoint working")


class TestAuthentication:
    """Authentication tests"""
    
    def test_admin_login(self):
        """Test admin login"""
        response = requests.post(f"{BASE_URL}/api/auth/login", json={
            "email": ADMIN_EMAIL,
            "password": ADMIN_PASSWORD
        })
        assert response.status_code == 200
        data = response.json()
        assert "token" in data
        assert "user" in data
        print(f"✓ Admin login successful: {data['user'].get('email')}")
        return data["token"]


class TestMarketplaceLeaderboard:
    """Tests for the new /api/marketplace/leaderboard endpoint"""
    
    def test_leaderboard_all_time(self):
        """Test leaderboard with all time range"""
        response = requests.get(f"{BASE_URL}/api/marketplace/leaderboard?timeRange=all")
        assert response.status_code == 200
        data = response.json()
        
        # Verify structure
        assert "topCreators" in data
        assert "topProtocols" in data
        assert "risingStars" in data
        assert "monthlyChampions" in data
        assert "timeRange" in data
        assert data["timeRange"] == "all"
        
        # Verify topCreators structure
        if data["topCreators"]:
            creator = data["topCreators"][0]
            assert "rank" in creator
            assert "username" in creator
            assert "protocols" in creator
            assert "downloads" in creator
            assert "revenue" in creator
            assert "badge" in creator
        
        # Verify topProtocols structure
        if data["topProtocols"]:
            protocol = data["topProtocols"][0]
            assert "rank" in protocol
            assert "name" in protocol
            assert "creator" in protocol
            assert "downloads" in protocol
            assert "rating" in protocol
            assert "price" in protocol
        
        print(f"✓ Leaderboard all-time: {len(data['topCreators'])} creators, {len(data['topProtocols'])} protocols")
    
    def test_leaderboard_month(self):
        """Test leaderboard with month time range"""
        response = requests.get(f"{BASE_URL}/api/marketplace/leaderboard?timeRange=month")
        assert response.status_code == 200
        data = response.json()
        assert data["timeRange"] == "month"
        print("✓ Leaderboard month range working")
    
    def test_leaderboard_week(self):
        """Test leaderboard with week time range"""
        response = requests.get(f"{BASE_URL}/api/marketplace/leaderboard?timeRange=week")
        assert response.status_code == 200
        data = response.json()
        assert data["timeRange"] == "week"
        print("✓ Leaderboard week range working")


class TestMarketplaceSalesLeaderboard:
    """Tests for /api/marketplace/leaderboard/sales endpoint"""
    
    def test_sales_leaderboard(self):
        """Test sales leaderboard"""
        response = requests.get(f"{BASE_URL}/api/marketplace/leaderboard/sales")
        assert response.status_code == 200
        data = response.json()
        
        assert "leaderboard" in data
        assert "type" in data
        assert data["type"] == "sales"
        
        if data["leaderboard"]:
            entry = data["leaderboard"][0]
            assert "rank" in entry
            assert "creator_name" in entry
            assert "total_sales" in entry
            assert "protocol_count" in entry
        
        print(f"✓ Sales leaderboard: {len(data['leaderboard'])} entries")


class TestMarketplaceRevenueLeaderboard:
    """Tests for /api/marketplace/leaderboard/revenue endpoint"""
    
    def test_revenue_leaderboard(self):
        """Test revenue leaderboard"""
        response = requests.get(f"{BASE_URL}/api/marketplace/leaderboard/revenue")
        assert response.status_code == 200
        data = response.json()
        
        assert "leaderboard" in data
        assert "type" in data
        assert data["type"] == "revenue"
        
        if data["leaderboard"]:
            entry = data["leaderboard"][0]
            assert "rank" in entry
            assert "creator_name" in entry
            assert "total_revenue" in entry
        
        print(f"✓ Revenue leaderboard: {len(data['leaderboard'])} entries")


class TestMarketplaceProtocols:
    """Tests for marketplace protocols endpoints"""
    
    def test_get_protocols(self):
        """Test getting marketplace protocols"""
        response = requests.get(f"{BASE_URL}/api/marketplace/protocols?sort=popular")
        assert response.status_code == 200
        data = response.json()
        
        assert "protocols" in data
        print(f"✓ Marketplace protocols: {len(data['protocols'])} protocols found")
    
    def test_get_categories(self):
        """Test getting marketplace categories"""
        response = requests.get(f"{BASE_URL}/api/marketplace/categories")
        assert response.status_code == 200
        data = response.json()
        
        assert "categories" in data
        print(f"✓ Marketplace categories: {len(data['categories'])} categories found")


class TestMarketplaceAuthenticatedEndpoints:
    """Tests for authenticated marketplace endpoints"""
    
    @pytest.fixture
    def auth_token(self):
        """Get authentication token"""
        response = requests.post(f"{BASE_URL}/api/auth/login", json={
            "email": ADMIN_EMAIL,
            "password": ADMIN_PASSWORD
        })
        if response.status_code == 200:
            return response.json().get("token")
        pytest.skip("Authentication failed")
    
    def test_seller_dashboard(self, auth_token):
        """Test seller dashboard endpoint"""
        headers = {"Authorization": f"Bearer {auth_token}"}
        response = requests.get(f"{BASE_URL}/api/marketplace/seller/dashboard", headers=headers)
        assert response.status_code == 200
        data = response.json()
        
        # Dashboard should have earnings info
        assert "total_earnings" in data or "protocols" in data
        print("✓ Seller dashboard working")
    
    def test_purchases(self, auth_token):
        """Test purchases endpoint"""
        headers = {"Authorization": f"Bearer {auth_token}"}
        response = requests.get(f"{BASE_URL}/api/marketplace/purchases", headers=headers)
        assert response.status_code == 200
        data = response.json()
        
        assert "purchases" in data
        print(f"✓ Purchases endpoint: {len(data['purchases'])} purchases")
    
    def test_admin_revenue_settings(self, auth_token):
        """Test admin revenue settings endpoint"""
        headers = {"Authorization": f"Bearer {auth_token}"}
        response = requests.get(f"{BASE_URL}/api/marketplace/admin/revenue-settings", headers=headers)
        assert response.status_code == 200
        data = response.json()
        
        assert "admin_percent" in data or "platform_fee" in data
        print("✓ Admin revenue settings working")


class TestBundlesEndpoints:
    """Tests for bundles endpoints"""
    
    def test_featured_bundles(self):
        """Test featured bundles endpoint"""
        response = requests.get(f"{BASE_URL}/api/bundles/featured")
        assert response.status_code == 200
        data = response.json()
        
        # Should return bundle data
        assert isinstance(data, (dict, list))
        print("✓ Featured bundles endpoint working")


class TestAISuggestions:
    """Tests for AI suggestions endpoints"""
    
    @pytest.fixture
    def auth_token(self):
        """Get authentication token"""
        response = requests.post(f"{BASE_URL}/api/auth/login", json={
            "email": ADMIN_EMAIL,
            "password": ADMIN_PASSWORD
        })
        if response.status_code == 200:
            return response.json().get("token")
        pytest.skip("Authentication failed")
    
    def test_ai_suggestions(self, auth_token):
        """Test AI suggestions endpoint"""
        headers = {"Authorization": f"Bearer {auth_token}"}
        response = requests.get(f"{BASE_URL}/api/ai/suggestions?limit=5", headers=headers)
        assert response.status_code == 200
        data = response.json()
        
        # Should return suggestions
        assert isinstance(data, (dict, list))
        print("✓ AI suggestions endpoint working")


class TestGamificationLeaderboards:
    """Tests for gamification leaderboard endpoints"""
    
    def test_xp_leaderboard(self):
        """Test XP leaderboard"""
        response = requests.get(f"{BASE_URL}/api/gamification/leaderboard")
        assert response.status_code == 200
        data = response.json()
        
        assert "leaderboard" in data
        print(f"✓ XP leaderboard: {len(data['leaderboard'])} entries")
    
    def test_weekly_leaderboard(self):
        """Test weekly leaderboard"""
        response = requests.get(f"{BASE_URL}/api/gamification/leaderboard/weekly")
        assert response.status_code == 200
        data = response.json()
        
        assert "leaderboard" in data
        assert "period" in data
        print("✓ Weekly leaderboard working")
    
    def test_monthly_leaderboard(self):
        """Test monthly leaderboard"""
        response = requests.get(f"{BASE_URL}/api/gamification/leaderboard/monthly")
        assert response.status_code == 200
        data = response.json()
        
        assert "leaderboard" in data
        assert "period" in data
        print("✓ Monthly leaderboard working")


if __name__ == "__main__":
    pytest.main([__file__, "-v", "--tb=short"])
