"""
Iteration 33 Tests - Protocol Analytics Dashboard, Marketplace Protocol Forecast, 
Unified Chat Module, YouTube Tutorial Videos, and MarketplacePage Refactoring

Tests:
1. Protocol Analytics API - /api/protocol-analytics/my-protocols
2. Protocol Forecast API - /api/protocol-analytics/admin/marketplace-forecast
3. Top Creators API - /api/protocol-analytics/admin/top-creators
4. Unified Chat Module - /api/unified-chat/overview
5. YouTube Tutorial Videos - All 10 tutorials have video_url
6. Marketplace Protocols - Browse, Sell, Purchases, Earnings, Analytics tabs
"""

import pytest
import requests
import os
import time

BASE_URL = os.environ.get('REACT_APP_BACKEND_URL', '').rstrip('/')

# Test credentials
ADMIN_EMAIL = "jjspilot24@gmail.com"
ADMIN_PASSWORD = "InfoPilot2024!"
TEST_EMAIL = "testuser@example.com"
TEST_PASSWORD = "password123"


class TestHealthAndBasics:
    """Basic health and connectivity tests"""
    
    def test_health_endpoint(self):
        """Test API health endpoint"""
        response = requests.get(f"{BASE_URL}/api/health")
        assert response.status_code == 200
        data = response.json()
        assert data["status"] == "healthy"
        print("✓ Health endpoint working")


class TestProtocolAnalytics:
    """Protocol Analytics Dashboard API tests"""
    
    @pytest.fixture(autouse=True)
    def setup(self):
        """Login as admin for analytics tests"""
        response = requests.post(f"{BASE_URL}/api/auth/login", json={
            "email": ADMIN_EMAIL,
            "password": ADMIN_PASSWORD
        })
        assert response.status_code == 200
        self.token = response.json()["token"]
        self.headers = {"Authorization": f"Bearer {self.token}"}
    
    def test_my_protocols_analytics(self):
        """Test /api/protocol-analytics/my-protocols endpoint"""
        response = requests.get(
            f"{BASE_URL}/api/protocol-analytics/my-protocols?days=30",
            headers=self.headers
        )
        assert response.status_code == 200
        data = response.json()
        
        # Verify response structure
        assert data["success"] == True
        assert "total_protocols" in data
        assert "period_days" in data
        assert "analytics" in data
        assert "summary" in data
        
        # Verify summary structure
        summary = data["summary"]
        assert "total_views" in summary
        assert "total_copies" in summary
        assert "total_sales" in summary
        assert "total_revenue" in summary
        assert "avg_rating" in summary
        assert "avg_conversion_rate" in summary
        
        # Verify analytics array structure
        if data["analytics"]:
            protocol = data["analytics"][0]
            assert "id" in protocol
            assert "name" in protocol
            assert "category" in protocol
            assert "views" in protocol
            assert "copies" in protocol
            assert "sales" in protocol
            assert "revenue" in protocol
            assert "conversion_rate" in protocol
        
        print(f"✓ Protocol analytics returned {data['total_protocols']} protocols")
    
    def test_my_protocols_analytics_different_periods(self):
        """Test analytics with different time periods"""
        for days in [7, 30, 90]:
            response = requests.get(
                f"{BASE_URL}/api/protocol-analytics/my-protocols?days={days}",
                headers=self.headers
            )
            assert response.status_code == 200
            data = response.json()
            assert data["period_days"] == days
        print("✓ Analytics works with different time periods (7, 30, 90 days)")
    
    def test_my_forecast(self):
        """Test /api/protocol-analytics/my-forecast endpoint"""
        response = requests.get(
            f"{BASE_URL}/api/protocol-analytics/my-forecast?days=30",
            headers=self.headers
        )
        assert response.status_code == 200
        data = response.json()
        
        assert "forecast" in data
        forecast = data["forecast"]
        assert "next_week_revenue" in forecast
        assert "next_month_revenue" in forecast
        assert "daily_average_copies" in forecast
        
        print("✓ Protocol forecast endpoint working")
    
    def test_analytics_requires_auth(self):
        """Test that analytics requires authentication"""
        response = requests.get(f"{BASE_URL}/api/protocol-analytics/my-protocols")
        assert response.status_code in [401, 403]
        print("✓ Analytics requires authentication")


class TestMarketplaceProtocolForecast:
    """Marketplace Protocol Forecast API tests (Admin only)"""
    
    @pytest.fixture(autouse=True)
    def setup(self):
        """Login as admin for forecast tests"""
        response = requests.post(f"{BASE_URL}/api/auth/login", json={
            "email": ADMIN_EMAIL,
            "password": ADMIN_PASSWORD
        })
        assert response.status_code == 200
        self.token = response.json()["token"]
        self.headers = {"Authorization": f"Bearer {self.token}"}
    
    def test_marketplace_forecast(self):
        """Test /api/protocol-analytics/admin/marketplace-forecast endpoint"""
        response = requests.get(
            f"{BASE_URL}/api/protocol-analytics/admin/marketplace-forecast",
            headers=self.headers
        )
        assert response.status_code == 200
        data = response.json()
        
        assert data["success"] == True
        assert "marketplace_forecast" in data
        
        forecast = data["marketplace_forecast"]
        assert "week_sales" in forecast
        assert "week_revenue" in forecast
        assert "month_sales" in forecast
        assert "month_revenue" in forecast
        assert "projected_next_month" in forecast
        assert "wow_growth_percent" in forecast
        assert "top_performing_protocols" in forecast
        
        print(f"✓ Marketplace forecast: {forecast['week_sales']} sales this week, ${forecast['week_revenue']} revenue")
    
    def test_top_creators(self):
        """Test /api/protocol-analytics/admin/top-creators endpoint"""
        response = requests.get(
            f"{BASE_URL}/api/protocol-analytics/admin/top-creators",
            headers=self.headers
        )
        assert response.status_code == 200
        data = response.json()
        
        assert data["success"] == True
        assert "top_creators" in data
        assert isinstance(data["top_creators"], list)
        
        print(f"✓ Top creators endpoint returned {len(data['top_creators'])} creators")
    
    def test_marketplace_forecast_requires_admin(self):
        """Test that marketplace forecast requires admin access"""
        # Login as regular user
        response = requests.post(f"{BASE_URL}/api/auth/login", json={
            "email": TEST_EMAIL,
            "password": TEST_PASSWORD
        })
        if response.status_code == 200:
            user_token = response.json()["token"]
            user_headers = {"Authorization": f"Bearer {user_token}"}
            
            response = requests.get(
                f"{BASE_URL}/api/protocol-analytics/admin/marketplace-forecast",
                headers=user_headers
            )
            assert response.status_code in [401, 403]
            print("✓ Marketplace forecast requires admin access")
        else:
            pytest.skip("Test user not available")


class TestUnifiedChatModule:
    """Unified Chat Module API tests"""
    
    @pytest.fixture(autouse=True)
    def setup(self):
        """Login for chat tests"""
        response = requests.post(f"{BASE_URL}/api/auth/login", json={
            "email": ADMIN_EMAIL,
            "password": ADMIN_PASSWORD
        })
        assert response.status_code == 200
        self.token = response.json()["token"]
        self.headers = {"Authorization": f"Bearer {self.token}"}
    
    def test_unified_chat_overview(self):
        """Test /api/unified-chat/overview endpoint"""
        response = requests.get(
            f"{BASE_URL}/api/unified-chat/overview",
            headers=self.headers
        )
        assert response.status_code == 200
        data = response.json()
        
        assert data["success"] == True
        assert "total_unread" in data
        assert "group_chats" in data
        assert "direct_messages" in data
        assert "online_status" in data
        
        # Verify group_chats structure
        group_chats = data["group_chats"]
        assert "count" in group_chats
        assert "chats" in group_chats
        
        # Verify direct_messages structure
        dm = data["direct_messages"]
        assert "count" in dm
        assert "conversations" in dm
        
        # Verify online_status structure
        online = data["online_status"]
        assert "total_online_users" in online
        assert "you_are_online" in online
        
        print(f"✓ Unified chat overview: {group_chats['count']} group chats, {dm['count']} DM conversations")
    
    def test_unified_chat_requires_auth(self):
        """Test that unified chat requires authentication"""
        response = requests.get(f"{BASE_URL}/api/unified-chat/overview")
        assert response.status_code in [401, 403]
        print("✓ Unified chat requires authentication")


class TestYouTubeTutorialVideos:
    """YouTube Tutorial Videos tests"""
    
    def test_all_tutorials_have_videos(self):
        """Test that all 10 tutorials have video_url populated"""
        response = requests.get(f"{BASE_URL}/api/tutorials")
        assert response.status_code == 200
        data = response.json()
        
        assert "tutorials" in data
        tutorials = data["tutorials"]
        assert len(tutorials) == 10, f"Expected 10 tutorials, got {len(tutorials)}"
        
        tutorials_with_videos = 0
        for tutorial in tutorials:
            assert "video_url" in tutorial
            if tutorial["video_url"]:
                tutorials_with_videos += 1
                assert "youtube.com" in tutorial["video_url"] or "youtu.be" in tutorial["video_url"]
        
        assert tutorials_with_videos == 10, f"Expected all 10 tutorials to have videos, got {tutorials_with_videos}"
        print(f"✓ All 10 tutorials have YouTube video URLs")
    
    def test_tutorial_video_structure(self):
        """Test tutorial video data structure"""
        response = requests.get(f"{BASE_URL}/api/tutorials")
        assert response.status_code == 200
        data = response.json()
        
        for tutorial in data["tutorials"]:
            assert "id" in tutorial
            assert "title" in tutorial
            assert "description" in tutorial
            assert "video_url" in tutorial
            assert "video_id" in tutorial
            assert "category" in tutorial
        
        print("✓ Tutorial video structure is correct")


class TestMarketplacePageTabs:
    """Marketplace Page tabs functionality tests"""
    
    @pytest.fixture(autouse=True)
    def setup(self):
        """Login for marketplace tests"""
        response = requests.post(f"{BASE_URL}/api/auth/login", json={
            "email": ADMIN_EMAIL,
            "password": ADMIN_PASSWORD
        })
        assert response.status_code == 200
        self.token = response.json()["token"]
        self.headers = {"Authorization": f"Bearer {self.token}"}
    
    def test_browse_protocols(self):
        """Test Browse FREE tab - marketplace protocols endpoint"""
        response = requests.get(
            f"{BASE_URL}/api/marketplace/protocols?sort=popular",
            headers=self.headers
        )
        assert response.status_code == 200
        data = response.json()
        
        assert "protocols" in data
        print(f"✓ Browse tab: {len(data['protocols'])} protocols available")
    
    def test_marketplace_categories(self):
        """Test marketplace categories for Browse tab"""
        response = requests.get(f"{BASE_URL}/api/marketplace/categories")
        assert response.status_code == 200
        data = response.json()
        
        assert "categories" in data
        print(f"✓ Marketplace has {len(data['categories'])} categories")
    
    def test_seller_dashboard(self):
        """Test My Earnings tab - seller dashboard endpoint"""
        response = requests.get(
            f"{BASE_URL}/api/marketplace/seller/dashboard",
            headers=self.headers
        )
        assert response.status_code == 200
        data = response.json()
        
        assert "total_earnings" in data
        assert "total_sales" in data
        assert "total_listings" in data  # API uses total_listings not protocol_count
        
        print(f"✓ Seller dashboard: ${data['total_earnings']} earnings, {data['total_sales']} sales")
    
    def test_purchases(self):
        """Test My Purchases tab - purchases endpoint"""
        response = requests.get(
            f"{BASE_URL}/api/marketplace/purchases",
            headers=self.headers
        )
        assert response.status_code == 200
        data = response.json()
        
        assert "purchases" in data
        print(f"✓ Purchases tab: {len(data['purchases'])} purchases")


class TestAdminProtocolForecastTab:
    """Admin Panel Protocol Forecast tab tests"""
    
    @pytest.fixture(autouse=True)
    def setup(self):
        """Login as admin"""
        response = requests.post(f"{BASE_URL}/api/auth/login", json={
            "email": ADMIN_EMAIL,
            "password": ADMIN_PASSWORD
        })
        assert response.status_code == 200
        self.token = response.json()["token"]
        self.headers = {"Authorization": f"Bearer {self.token}"}
    
    def test_revenue_forecast_summary(self):
        """Test revenue forecast summary for admin"""
        response = requests.get(
            f"{BASE_URL}/api/revenue-forecast/summary",
            headers=self.headers
        )
        assert response.status_code == 200
        data = response.json()
        
        # API uses weekly/monthly instead of this_week/this_month
        assert "weekly" in data or "this_week" in data
        assert "monthly" in data or "this_month" in data
        assert "projected_monthly" in data
        
        weekly_key = "weekly" if "weekly" in data else "this_week"
        monthly_key = "monthly" if "monthly" in data else "this_month"
        
        print(f"✓ Revenue forecast: Weekly ${data[weekly_key]['revenue']}, Monthly ${data[monthly_key]['revenue']}")
    
    def test_admin_panel_tabs_count(self):
        """Verify admin has access to admin features"""
        # Test admin settings endpoint
        response = requests.get(
            f"{BASE_URL}/api/admin/settings",
            headers=self.headers
        )
        assert response.status_code == 200
        print("✓ Admin panel accessible")


class TestCodeQuality:
    """Code quality and refactoring verification"""
    
    def test_marketplace_page_refactored(self):
        """Verify MarketplacePage.js is refactored (should be ~570 lines)"""
        import os
        marketplace_path = "/app/frontend/src/pages/MarketplacePage.js"
        
        if os.path.exists(marketplace_path):
            with open(marketplace_path, 'r') as f:
                lines = len(f.readlines())
            
            # Should be around 570 lines after refactoring (was 1394)
            assert lines < 700, f"MarketplacePage.js has {lines} lines, expected ~570 after refactoring"
            print(f"✓ MarketplacePage.js refactored: {lines} lines (was 1394)")
        else:
            pytest.skip("MarketplacePage.js not found")
    
    def test_protocol_analytics_dashboard_exists(self):
        """Verify ProtocolAnalyticsDashboard component exists"""
        import os
        component_path = "/app/frontend/src/components/Admin/ProtocolAnalyticsDashboard.js"
        
        assert os.path.exists(component_path), "ProtocolAnalyticsDashboard.js not found"
        
        with open(component_path, 'r') as f:
            content = f.read()
        
        # Verify key elements
        assert "protocol-analytics-dashboard" in content.lower() or "ProtocolAnalyticsDashboard" in content
        print("✓ ProtocolAnalyticsDashboard component exists")
    
    def test_marketplace_protocol_forecast_exists(self):
        """Verify MarketplaceProtocolForecast component exists"""
        import os
        component_path = "/app/frontend/src/components/Admin/MarketplaceProtocolForecast.js"
        
        assert os.path.exists(component_path), "MarketplaceProtocolForecast.js not found"
        
        with open(component_path, 'r') as f:
            content = f.read()
        
        assert "MarketplaceProtocolForecast" in content
        print("✓ MarketplaceProtocolForecast component exists")
    
    def test_unified_chat_router_exists(self):
        """Verify unified_chat router exists"""
        import os
        router_path = "/app/backend/routes/unified_chat.py"
        
        assert os.path.exists(router_path), "unified_chat.py not found"
        
        with open(router_path, 'r') as f:
            content = f.read()
        
        assert "unified_chat_router" in content or "APIRouter" in content
        print("✓ Unified chat router exists")


if __name__ == "__main__":
    pytest.main([__file__, "-v", "--tb=short"])
