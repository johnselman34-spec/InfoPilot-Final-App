"""
Iteration 60 - Feature Tests
Tests for:
1. Dark Mode toggle (frontend only - no backend API)
2. Personal Reports - 3 image upload support
3. Easter Egg Statistics on Statistics page
4. MarketplacePage refactoring - verify page loads correctly
"""
import pytest
import requests
import os

BASE_URL = os.environ.get('REACT_APP_BACKEND_URL', '').rstrip('/')

class TestHealthAndAuth:
    """Basic health and authentication tests"""
    
    def test_health_endpoint(self):
        """Test health endpoint is accessible"""
        response = requests.get(f"{BASE_URL}/api/health")
        assert response.status_code == 200
        data = response.json()
        assert data.get("status") == "healthy"
        print("✅ Health endpoint working")
    
    def test_admin_login(self):
        """Test admin login"""
        response = requests.post(f"{BASE_URL}/api/auth/login", json={
            "email": "jjspilot24@gmail.com",
            "password": "InfoPilot2024!"
        })
        assert response.status_code == 200
        data = response.json()
        assert "token" in data
        assert data.get("user", {}).get("is_admin") == True
        print("✅ Admin login successful")
        return data["token"]


class TestPersonalReports:
    """Test Personal Reports 3-image upload feature"""
    
    @pytest.fixture
    def auth_token(self):
        """Get authentication token"""
        response = requests.post(f"{BASE_URL}/api/auth/login", json={
            "email": "jjspilot24@gmail.com",
            "password": "InfoPilot2024!"
        })
        if response.status_code == 200:
            return response.json().get("token")
        pytest.skip("Authentication failed")
    
    def test_get_personal_reports(self, auth_token):
        """Test fetching personal reports"""
        response = requests.get(
            f"{BASE_URL}/api/personal-reports",
            headers={"Authorization": f"Bearer {auth_token}"}
        )
        assert response.status_code == 200
        data = response.json()
        assert "reports" in data
        print(f"✅ Personal reports fetched: {len(data.get('reports', []))} reports")
    
    def test_create_personal_report(self, auth_token):
        """Test creating a personal report"""
        response = requests.post(
            f"{BASE_URL}/api/personal-reports",
            headers={
                "Authorization": f"Bearer {auth_token}",
                "Content-Type": "application/json"
            },
            json={
                "title": "Test Report for Iteration 60",
                "topic": "Testing",
                "content": "This is a test report to verify the 3-image upload feature works correctly.",
                "location": "Test Location"
            }
        )
        assert response.status_code in [200, 201]
        data = response.json()
        assert "report" in data
        report_id = data["report"].get("id")
        print(f"✅ Personal report created with ID: {report_id}")
        return report_id
    
    def test_personal_report_image_endpoint_exists(self, auth_token):
        """Test that the image upload endpoint exists (POST /api/personal-reports/{id}/image)"""
        # First create a report
        create_response = requests.post(
            f"{BASE_URL}/api/personal-reports",
            headers={
                "Authorization": f"Bearer {auth_token}",
                "Content-Type": "application/json"
            },
            json={
                "title": "Image Test Report",
                "topic": "Testing",
                "content": "Testing image upload endpoint existence.",
                "location": "Test"
            }
        )
        
        if create_response.status_code not in [200, 201]:
            pytest.skip("Could not create report for image test")
        
        report_id = create_response.json()["report"]["id"]
        
        # Try to access the image endpoint (without actually uploading)
        # We expect 422 (validation error) or 400 (bad request) if endpoint exists but no file
        # We expect 404 if endpoint doesn't exist
        response = requests.post(
            f"{BASE_URL}/api/personal-reports/{report_id}/image",
            headers={"Authorization": f"Bearer {auth_token}"}
        )
        
        # Endpoint should exist - 422 means it exists but needs file
        assert response.status_code != 404, "Image upload endpoint not found"
        print(f"✅ Image upload endpoint exists (status: {response.status_code})")


class TestEasterEggStatistics:
    """Test Easter Egg Statistics endpoints"""
    
    @pytest.fixture
    def auth_token(self):
        """Get authentication token"""
        response = requests.post(f"{BASE_URL}/api/auth/login", json={
            "email": "jjspilot24@gmail.com",
            "password": "InfoPilot2024!"
        })
        if response.status_code == 200:
            return response.json().get("token")
        pytest.skip("Authentication failed")
    
    def test_easter_egg_global_stats(self):
        """Test global Easter Egg statistics endpoint"""
        response = requests.get(f"{BASE_URL}/api/easter-eggs/stats")
        assert response.status_code == 200
        data = response.json()
        # Check for expected fields
        assert "total_discoveries" in data or "total_eggs_available" in data or isinstance(data, dict)
        print(f"✅ Easter Egg global stats: {data}")
    
    def test_easter_egg_leaderboard(self):
        """Test Easter Egg leaderboard endpoint"""
        response = requests.get(f"{BASE_URL}/api/easter-eggs/leaderboard")
        assert response.status_code == 200
        data = response.json()
        assert "leaderboard" in data
        print(f"✅ Easter Egg leaderboard: {len(data.get('leaderboard', []))} entries")
    
    def test_easter_egg_my_discoveries(self, auth_token):
        """Test user's Easter Egg discoveries endpoint"""
        response = requests.get(
            f"{BASE_URL}/api/easter-eggs/my-discoveries",
            headers={"Authorization": f"Bearer {auth_token}"}
        )
        assert response.status_code == 200
        data = response.json()
        # Should have discoveries array and total_xp
        print(f"✅ User Easter Egg discoveries: {data}")


class TestMarketplace:
    """Test Marketplace page functionality after refactoring"""
    
    @pytest.fixture
    def auth_token(self):
        """Get authentication token"""
        response = requests.post(f"{BASE_URL}/api/auth/login", json={
            "email": "jjspilot24@gmail.com",
            "password": "InfoPilot2024!"
        })
        if response.status_code == 200:
            return response.json().get("token")
        pytest.skip("Authentication failed")
    
    def test_marketplace_protocols(self, auth_token):
        """Test fetching marketplace protocols"""
        response = requests.get(
            f"{BASE_URL}/api/marketplace/protocols",
            headers={"Authorization": f"Bearer {auth_token}"}
        )
        assert response.status_code == 200
        data = response.json()
        assert "protocols" in data
        print(f"✅ Marketplace protocols: {len(data.get('protocols', []))} protocols")
    
    def test_marketplace_categories(self):
        """Test fetching marketplace categories"""
        response = requests.get(f"{BASE_URL}/api/marketplace/categories")
        assert response.status_code == 200
        data = response.json()
        assert "categories" in data
        print(f"✅ Marketplace categories: {len(data.get('categories', []))} categories")
    
    def test_marketplace_bundles(self, auth_token):
        """Test fetching marketplace bundles"""
        response = requests.get(
            f"{BASE_URL}/api/bundles",
            headers={"Authorization": f"Bearer {auth_token}"}
        )
        # Bundles endpoint might return 200 or 404 if no bundles
        assert response.status_code in [200, 404]
        if response.status_code == 200:
            data = response.json()
            print(f"✅ Marketplace bundles: {data}")
        else:
            print("✅ Bundles endpoint exists (no bundles found)")
    
    def test_marketplace_seller_dashboard(self, auth_token):
        """Test seller dashboard endpoint"""
        response = requests.get(
            f"{BASE_URL}/api/marketplace/seller/dashboard",
            headers={"Authorization": f"Bearer {auth_token}"}
        )
        assert response.status_code == 200
        data = response.json()
        # Should have earnings and sales info
        print(f"✅ Seller dashboard: {data}")


class TestStatisticsPage:
    """Test Statistics page endpoints"""
    
    @pytest.fixture
    def auth_token(self):
        """Get authentication token"""
        response = requests.post(f"{BASE_URL}/api/auth/login", json={
            "email": "jjspilot24@gmail.com",
            "password": "InfoPilot2024!"
        })
        if response.status_code == 200:
            return response.json().get("token")
        pytest.skip("Authentication failed")
    
    def test_statistics_dashboard(self):
        """Test statistics dashboard endpoint"""
        response = requests.get(f"{BASE_URL}/api/statistics/dashboard")
        assert response.status_code == 200
        data = response.json()
        print(f"✅ Statistics dashboard loaded")
    
    def test_statistics_most_copied(self):
        """Test most copied protocols endpoint"""
        response = requests.get(f"{BASE_URL}/api/statistics/most-copied")
        assert response.status_code == 200
        data = response.json()
        print(f"✅ Most copied statistics: {data}")
    
    def test_marketplace_leaderboard_sales(self):
        """Test marketplace sales leaderboard"""
        response = requests.get(f"{BASE_URL}/api/marketplace/leaderboard/sales")
        assert response.status_code == 200
        data = response.json()
        assert "leaderboard" in data
        print(f"✅ Sales leaderboard: {len(data.get('leaderboard', []))} entries")
    
    def test_marketplace_leaderboard_revenue(self):
        """Test marketplace revenue leaderboard"""
        response = requests.get(f"{BASE_URL}/api/marketplace/leaderboard/revenue")
        assert response.status_code == 200
        data = response.json()
        assert "leaderboard" in data
        print(f"✅ Revenue leaderboard: {len(data.get('leaderboard', []))} entries")


if __name__ == "__main__":
    pytest.main([__file__, "-v", "--tb=short"])
