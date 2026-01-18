"""
Test suite for InfoPilot Explorer - Testing the 7 RESTORED pages APIs.
Tests: Reports, Revenue, Marketplace, Themes, Templates, Stats, Map
"""
import pytest
import requests
import os
import io

BASE_URL = os.environ.get('REACT_APP_BACKEND_URL', 'https://infojethub.preview.emergentagent.com').rstrip('/')

# Test credentials
TEST_EMAIL = "testuser_new@example.com"
TEST_PASSWORD = "password123"


@pytest.fixture(scope="module")
def auth_token():
    """Get auth token for authenticated requests"""
    response = requests.post(f"{BASE_URL}/api/auth/login", json={
        "email": TEST_EMAIL,
        "password": TEST_PASSWORD
    })
    if response.status_code == 200:
        return response.json()["token"]
    pytest.skip("Authentication failed - cannot proceed with tests")


class TestReportsAPI:
    """Test Reports API - ReportsPage functionality"""
    
    def test_create_report(self, auth_token):
        """POST /api/reports - Create a new report"""
        headers = {"Authorization": f"Bearer {auth_token}"}
        report_data = {
            "title": "TEST_Restored_Report",
            "content": "This is a test report to verify the restored ReportsPage functionality. " * 10,
            "images": [],
            "category_ids": []
        }
        
        response = requests.post(f"{BASE_URL}/api/reports", json=report_data, headers=headers)
        assert response.status_code == 200, f"Create report failed: {response.text}"
        data = response.json()
        
        assert "id" in data
        assert data["title"] == report_data["title"]
        assert "created_at" in data
        print(f"✓ Report created: {data['id']}")
        return data["id"]
    
    def test_get_reports(self, auth_token):
        """GET /api/reports - Get user's reports"""
        headers = {"Authorization": f"Bearer {auth_token}"}
        response = requests.get(f"{BASE_URL}/api/reports", headers=headers)
        
        assert response.status_code == 200, f"Get reports failed: {response.text}"
        data = response.json()
        
        assert "reports" in data
        assert isinstance(data["reports"], list)
        print(f"✓ Found {len(data['reports'])} reports")
    
    def test_delete_report(self, auth_token):
        """DELETE /api/reports/{id} - Delete a report"""
        headers = {"Authorization": f"Bearer {auth_token}"}
        
        # Create a report first
        create_response = requests.post(f"{BASE_URL}/api/reports", json={
            "title": "TEST_Delete_Report",
            "content": "Report to be deleted " * 10,
            "images": [],
            "category_ids": []
        }, headers=headers)
        
        assert create_response.status_code == 200
        report_id = create_response.json()["id"]
        
        # Delete it
        delete_response = requests.delete(f"{BASE_URL}/api/reports/{report_id}", headers=headers)
        assert delete_response.status_code == 200, f"Delete report failed: {delete_response.text}"
        print(f"✓ Report deleted: {report_id}")
    
    def test_image_upload(self, auth_token):
        """POST /api/upload/image - Upload image for report"""
        headers = {"Authorization": f"Bearer {auth_token}"}
        
        # Create a simple test image (1x1 pixel PNG)
        png_data = bytes([
            0x89, 0x50, 0x4E, 0x47, 0x0D, 0x0A, 0x1A, 0x0A,
            0x00, 0x00, 0x00, 0x0D, 0x49, 0x48, 0x44, 0x52,
            0x00, 0x00, 0x00, 0x01, 0x00, 0x00, 0x00, 0x01,
            0x08, 0x02, 0x00, 0x00, 0x00, 0x90, 0x77, 0x53,
            0xDE, 0x00, 0x00, 0x00, 0x0C, 0x49, 0x44, 0x41,
            0x54, 0x08, 0xD7, 0x63, 0xF8, 0xFF, 0xFF, 0x3F,
            0x00, 0x05, 0xFE, 0x02, 0xFE, 0xDC, 0xCC, 0x59,
            0xE7, 0x00, 0x00, 0x00, 0x00, 0x49, 0x45, 0x4E,
            0x44, 0xAE, 0x42, 0x60, 0x82
        ])
        
        files = {"file": ("test_image.png", io.BytesIO(png_data), "image/png")}
        response = requests.post(f"{BASE_URL}/api/upload/image", files=files, headers=headers)
        
        assert response.status_code == 200, f"Image upload failed: {response.text}"
        data = response.json()
        assert "url" in data
        print(f"✓ Image uploaded: {data['url']}")


class TestRevenueAPI:
    """Test Revenue API - RevenuePage functionality"""
    
    def test_get_revenue_dashboard(self, auth_token):
        """GET /api/revenue/dashboard - Get revenue dashboard data"""
        headers = {"Authorization": f"Bearer {auth_token}"}
        response = requests.get(f"{BASE_URL}/api/revenue/dashboard", headers=headers)
        
        assert response.status_code == 200, f"Revenue dashboard failed: {response.text}"
        data = response.json()
        
        assert "total_revenue" in data
        assert "total_sales" in data
        assert "monthly_revenue" in data
        assert "top_protocols" in data
        assert "wallet_balance" in data
        print(f"✓ Revenue Dashboard: ${data['total_revenue']:.2f} total, {data['total_sales']} sales")
    
    def test_export_pdf(self, auth_token):
        """GET /api/revenue/export?format=pdf - Export revenue as PDF"""
        headers = {"Authorization": f"Bearer {auth_token}"}
        response = requests.get(f"{BASE_URL}/api/revenue/export?format=pdf", headers=headers)
        
        assert response.status_code == 200, f"PDF export failed: {response.text}"
        assert "application/pdf" in response.headers.get("content-type", "")
        assert response.content[:4] == b'%PDF', "Response is not a valid PDF"
        print(f"✓ PDF export successful: {len(response.content)} bytes")
    
    def test_export_csv(self, auth_token):
        """GET /api/revenue/export?format=csv - Export revenue as CSV"""
        headers = {"Authorization": f"Bearer {auth_token}"}
        response = requests.get(f"{BASE_URL}/api/revenue/export?format=csv", headers=headers)
        
        assert response.status_code == 200, f"CSV export failed: {response.text}"
        assert "text/csv" in response.headers.get("content-type", "")
        assert "Date,Protocol,Price" in response.text, "CSV missing expected headers"
        print(f"✓ CSV export successful: {len(response.text)} bytes")


class TestMarketplaceAPI:
    """Test Marketplace API - MarketplacePage functionality"""
    
    def test_get_marketplace_protocols(self):
        """GET /api/marketplace/protocols - Get all marketplace protocols"""
        response = requests.get(f"{BASE_URL}/api/marketplace/protocols")
        
        assert response.status_code == 200, f"Get protocols failed: {response.text}"
        data = response.json()
        
        assert "protocols" in data
        assert "total" in data
        assert isinstance(data["protocols"], list)
        print(f"✓ Marketplace: {data['total']} protocols available")
    
    def test_get_marketplace_protocols_with_category_filter(self):
        """GET /api/marketplace/protocols?category=Technology - Filter by category"""
        response = requests.get(f"{BASE_URL}/api/marketplace/protocols", params={"category": "Technology"})
        
        assert response.status_code == 200, f"Get protocols with filter failed: {response.text}"
        data = response.json()
        
        assert "protocols" in data
        print(f"✓ Marketplace filtered: {len(data['protocols'])} Technology protocols")


class TestTemplatesAPI:
    """Test Templates API - TemplatesPage functionality"""
    
    def test_get_templates(self):
        """GET /api/templates - Get all templates"""
        response = requests.get(f"{BASE_URL}/api/templates")
        
        assert response.status_code == 200, f"Get templates failed: {response.text}"
        data = response.json()
        
        assert "official_templates" in data
        assert "community_templates" in data
        assert len(data["official_templates"]) > 0, "No official templates found"
        print(f"✓ Templates: {len(data['official_templates'])} official, {len(data['community_templates'])} community")
    
    def test_create_template(self, auth_token):
        """POST /api/templates - Create a new template"""
        headers = {"Authorization": f"Bearer {auth_token}"}
        template_data = {
            "name": "TEST_Restored_Template",
            "description": "A test template for restored TemplatesPage",
            "protocol": "(test) & (restored)",
            "category_suggestion": "Testing"
        }
        
        response = requests.post(f"{BASE_URL}/api/templates", json=template_data, headers=headers)
        assert response.status_code == 200, f"Create template failed: {response.text}"
        data = response.json()
        
        assert "id" in data
        assert data["name"] == template_data["name"]
        print(f"✓ Template created: {data['name']}")


class TestStatsAPI:
    """Test Stats API - StatsPage functionality"""
    
    def test_get_stats(self):
        """GET /api/stats - Get global statistics"""
        response = requests.get(f"{BASE_URL}/api/stats")
        
        assert response.status_code == 200, f"Get stats failed: {response.text}"
        data = response.json()
        
        assert "global" in data
        assert "total_users" in data["global"]
        assert "public_categories" in data["global"]
        assert "total_search_results" in data["global"]
        print(f"✓ Stats: {data['global']['total_users']} users, {data['global']['total_search_results']} results")
    
    def test_get_leaderboard(self):
        """GET /api/leaderboard - Get leaderboard data"""
        response = requests.get(f"{BASE_URL}/api/leaderboard")
        
        assert response.status_code == 200, f"Get leaderboard failed: {response.text}"
        data = response.json()
        
        assert "top_laughter_points" in data
        assert "top_protocol_creators" in data
        print(f"✓ Leaderboard: {len(data['top_laughter_points'])} top users")


class TestMapAPI:
    """Test Map API - MapPage functionality"""
    
    def test_get_map_data_personal(self, auth_token):
        """GET /api/map/data?scope=personal - Get personal map data"""
        headers = {"Authorization": f"Bearer {auth_token}"}
        response = requests.get(f"{BASE_URL}/api/map/data", params={"scope": "personal"}, headers=headers)
        
        assert response.status_code == 200, f"Get personal map data failed: {response.text}"
        data = response.json()
        
        assert "points" in data
        assert isinstance(data["points"], list)
        print(f"✓ Personal Map: {len(data['points'])} locations")
    
    def test_get_map_data_worldwide(self, auth_token):
        """GET /api/map/data?scope=worldwide - Get worldwide map data"""
        headers = {"Authorization": f"Bearer {auth_token}"}
        response = requests.get(f"{BASE_URL}/api/map/data", params={"scope": "worldwide"}, headers=headers)
        
        assert response.status_code == 200, f"Get worldwide map data failed: {response.text}"
        data = response.json()
        
        assert "points" in data
        print(f"✓ Worldwide Map: {len(data['points'])} locations")


if __name__ == "__main__":
    pytest.main([__file__, "-v", "--tb=short"])
