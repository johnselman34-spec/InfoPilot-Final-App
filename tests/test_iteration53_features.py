"""
Iteration 53 - Testing New Features:
1. Global Price Controls (for ALL users)
2. Document Type Classification Settings (Admin-controlled InfoJet 2.0 protocols)
3. Personal Report (Organic) CRUD endpoints
4. Quick Category Search filter in CollapsibleCategoryTree

Backend URL: https://infoshare-4.preview.emergentagent.com
Admin credentials: jjspilot24@gmail.com / InfoPilot2024!
"""

import pytest
import requests
import os
import time
from datetime import datetime

BASE_URL = os.environ.get('REACT_APP_BACKEND_URL', 'https://infoshare-4.preview.emergentagent.com').rstrip('/')


class TestHealthAndBasics:
    """Basic health and connectivity tests"""
    
    def test_health_endpoint(self):
        """Test health endpoint is accessible"""
        response = requests.get(f"{BASE_URL}/api/health")
        assert response.status_code == 200
        data = response.json()
        assert data.get("status") == "healthy"
        print(f"✓ Health endpoint: {data}")
    
    def test_article_types_endpoint(self):
        """Test article types endpoint returns document types"""
        response = requests.get(f"{BASE_URL}/api/article-types")
        assert response.status_code == 200
        data = response.json()
        assert "types" in data
        assert len(data["types"]) >= 10  # Should have at least 10 document types
        print(f"✓ Article types: {len(data['types'])} types available")


class TestAuthentication:
    """Authentication tests"""
    
    @pytest.fixture
    def admin_token(self):
        """Get admin authentication token"""
        response = requests.post(f"{BASE_URL}/api/auth/login", json={
            "email": "jjspilot24@gmail.com",
            "password": "InfoPilot2024!"
        })
        assert response.status_code == 200, f"Admin login failed: {response.text}"
        data = response.json()
        assert "token" in data
        return data["token"]
    
    def test_admin_login(self, admin_token):
        """Test admin login works"""
        assert admin_token is not None
        assert len(admin_token) > 10
        print(f"✓ Admin login successful, token length: {len(admin_token)}")
    
    def test_invalid_login_rejected(self):
        """Test invalid credentials are rejected"""
        response = requests.post(f"{BASE_URL}/api/auth/login", json={
            "email": "invalid@test.com",
            "password": "wrongpassword"
        })
        assert response.status_code in [401, 404]
        print("✓ Invalid login correctly rejected")


class TestGlobalPriceControls:
    """Test Global Price Controls (for ALL users) - NEW FEATURE"""
    
    @pytest.fixture
    def admin_headers(self):
        """Get admin authentication headers"""
        response = requests.post(f"{BASE_URL}/api/auth/login", json={
            "email": "jjspilot24@gmail.com",
            "password": "InfoPilot2024!"
        })
        assert response.status_code == 200
        token = response.json()["token"]
        return {"Authorization": f"Bearer {token}"}
    
    def test_get_global_price_controls(self, admin_headers):
        """Test GET /api/admin/global-price-controls returns settings"""
        response = requests.get(f"{BASE_URL}/api/admin/global-price-controls", headers=admin_headers)
        assert response.status_code == 200
        data = response.json()
        
        # Verify structure
        assert "settings" in data
        settings = data["settings"]
        
        # Verify required keys exist
        assert "global_price_control_enabled" in settings
        assert "global_max_protocol_price" in settings
        assert "global_max_bundle_price" in settings
        assert "global_min_protocol_price" in settings
        
        # Verify default values (OFF by default)
        assert settings["global_price_control_enabled"] == False, "Global price control should be OFF by default"
        
        # Verify descriptions exist
        assert "description" in data
        
        print(f"✓ Global price controls: enabled={settings['global_price_control_enabled']}, max_protocol=${settings['global_max_protocol_price']}, max_bundle=${settings['global_max_bundle_price']}")
    
    def test_update_global_price_controls(self, admin_headers):
        """Test PUT /api/admin/global-price-controls updates settings"""
        # First get current settings
        get_response = requests.get(f"{BASE_URL}/api/admin/global-price-controls", headers=admin_headers)
        original_settings = get_response.json()["settings"]
        
        # Update settings
        update_data = {
            "global_price_control_enabled": True,
            "global_max_protocol_price": 50.00,
            "global_max_bundle_price": 100.00,
            "global_min_protocol_price": 1.00
        }
        
        response = requests.put(f"{BASE_URL}/api/admin/global-price-controls", 
                               headers=admin_headers, json=update_data)
        assert response.status_code == 200
        data = response.json()
        assert data["success"] == True
        assert "updated" in data
        
        # Verify changes were applied
        verify_response = requests.get(f"{BASE_URL}/api/admin/global-price-controls", headers=admin_headers)
        new_settings = verify_response.json()["settings"]
        assert new_settings["global_price_control_enabled"] == True
        assert new_settings["global_max_protocol_price"] == 50.00
        
        # Restore original settings
        restore_data = {
            "global_price_control_enabled": original_settings["global_price_control_enabled"],
            "global_max_protocol_price": original_settings["global_max_protocol_price"],
            "global_max_bundle_price": original_settings["global_max_bundle_price"],
            "global_min_protocol_price": original_settings["global_min_protocol_price"]
        }
        requests.put(f"{BASE_URL}/api/admin/global-price-controls", headers=admin_headers, json=restore_data)
        
        print(f"✓ Global price controls update successful: {len(data['updated'])} fields updated")


class TestDoctypeSettings:
    """Test Document Type Classification Settings (InfoJet 2.0 protocols) - NEW FEATURE"""
    
    @pytest.fixture
    def admin_headers(self):
        """Get admin authentication headers"""
        response = requests.post(f"{BASE_URL}/api/auth/login", json={
            "email": "jjspilot24@gmail.com",
            "password": "InfoPilot2024!"
        })
        assert response.status_code == 200
        token = response.json()["token"]
        return {"Authorization": f"Bearer {token}"}
    
    def test_get_doctype_settings(self, admin_headers):
        """Test GET /api/admin/doctype-settings returns 15 document types and protocols"""
        response = requests.get(f"{BASE_URL}/api/admin/doctype-settings", headers=admin_headers)
        assert response.status_code == 200
        data = response.json()
        
        # Verify structure
        assert "settings" in data
        assert "document_types" in data
        assert "description" in data
        
        settings = data["settings"]
        document_types = data["document_types"]
        
        # Verify 15 document types
        assert len(document_types) == 15, f"Expected 15 document types, got {len(document_types)}"
        
        # Verify key settings exist
        assert "doctype_phd_min_words" in settings
        assert "doctype_phd_keyword_count" in settings
        assert "doctype_phd_protocol" in settings
        assert "doctype_informative_protocol" in settings
        assert "doctype_news_protocol" in settings
        assert "doctype_blog_protocol" in settings
        assert "doctype_forum_protocol" in settings
        assert "doctype_personal_collected_protocol" in settings
        assert "doctype_auto_categorize" in settings
        
        # Verify default values
        assert settings["doctype_phd_min_words"] == 1500
        assert settings["doctype_phd_keyword_count"] == 3
        
        # Verify document type names
        type_names = [dt["type"] for dt in document_types]
        expected_types = [
            "PhD Informative", "Informative", "InfoPilot Exclusive", "InfoBook Exclusive",
            "News Article", "Blog Post", "Forum", "Personal Report (Organic)",
            "Personal Report (Collected)", "Academic Paper", "Government", "Wiki",
            "Video", "PDF Document", "Webpage"
        ]
        for expected in expected_types:
            assert expected in type_names, f"Missing document type: {expected}"
        
        print(f"✓ Doctype settings: {len(document_types)} document types, {len(settings)} settings")
        print(f"  - PhD min words: {settings['doctype_phd_min_words']}")
        print(f"  - PhD keyword count: {settings['doctype_phd_keyword_count']}")
    
    def test_update_doctype_settings(self, admin_headers):
        """Test PUT /api/admin/doctype-settings updates classification settings"""
        # First get current settings
        get_response = requests.get(f"{BASE_URL}/api/admin/doctype-settings", headers=admin_headers)
        original_settings = get_response.json()["settings"]
        
        # Update settings
        update_data = {
            "doctype_phd_min_words": 2000,
            "doctype_phd_keyword_count": 4,
            "doctype_news_min_instances": 4
        }
        
        response = requests.put(f"{BASE_URL}/api/admin/doctype-settings", 
                               headers=admin_headers, json=update_data)
        assert response.status_code == 200
        data = response.json()
        assert data["success"] == True
        assert "updated" in data
        
        # Verify changes were applied
        verify_response = requests.get(f"{BASE_URL}/api/admin/doctype-settings", headers=admin_headers)
        new_settings = verify_response.json()["settings"]
        assert new_settings["doctype_phd_min_words"] == 2000
        assert new_settings["doctype_phd_keyword_count"] == 4
        
        # Restore original settings
        restore_data = {
            "doctype_phd_min_words": original_settings["doctype_phd_min_words"],
            "doctype_phd_keyword_count": original_settings["doctype_phd_keyword_count"],
            "doctype_news_min_instances": original_settings["doctype_news_min_instances"]
        }
        requests.put(f"{BASE_URL}/api/admin/doctype-settings", headers=admin_headers, json=restore_data)
        
        print(f"✓ Doctype settings update successful: {len(data['updated'])} fields updated")


class TestPersonalReportsCRUD:
    """Test Personal Report (Organic) CRUD endpoints - NEW FEATURE"""
    
    @pytest.fixture
    def admin_headers(self):
        """Get admin authentication headers"""
        response = requests.post(f"{BASE_URL}/api/auth/login", json={
            "email": "jjspilot24@gmail.com",
            "password": "InfoPilot2024!"
        })
        assert response.status_code == 200
        token = response.json()["token"]
        return {"Authorization": f"Bearer {token}"}
    
    @pytest.fixture
    def test_report_id(self, admin_headers):
        """Create a test report and return its ID for other tests"""
        report_data = {
            "title": f"TEST_Personal_Report_{datetime.now().strftime('%Y%m%d_%H%M%S')}",
            "content": "This is a test personal report content. I went to the location and observed many interesting things. I noticed that the area was very clean and well-maintained.",
            "topic": "Test Topic",
            "location_name": "Test Location, USA",
            "latitude": 40.7128,
            "longitude": -74.0060,
            "category_ids": []
        }
        
        response = requests.post(f"{BASE_URL}/api/personal-reports", 
                                headers=admin_headers, json=report_data)
        assert response.status_code == 200
        data = response.json()
        assert data["success"] == True
        return data["report_id"]
    
    def test_create_personal_report(self, admin_headers):
        """Test POST /api/personal-reports creates a new Personal Report (Organic)"""
        report_data = {
            "title": f"TEST_My_First_Report_{datetime.now().strftime('%Y%m%d_%H%M%S')}",
            "content": "This is my personal report about my experience. I visited the location and found it very interesting. I observed many details that others might have missed.",
            "topic": "Personal Experience",
            "location_name": "New York, NY",
            "latitude": 40.7128,
            "longitude": -74.0060,
            "category_ids": []
        }
        
        response = requests.post(f"{BASE_URL}/api/personal-reports", 
                                headers=admin_headers, json=report_data)
        assert response.status_code == 200
        data = response.json()
        
        # Verify response structure
        assert data["success"] == True
        assert "report_id" in data
        assert "message" in data
        assert "report" in data
        
        # Verify report data
        report = data["report"]
        assert report["title"] == report_data["title"]
        assert report["article_type"] == "Personal Report (Organic)"
        
        # Clean up - delete the test report
        report_id = data["report_id"]
        requests.delete(f"{BASE_URL}/api/personal-reports/{report_id}", headers=admin_headers)
        
        print(f"✓ Personal Report created: {report['title']}")
    
    def test_get_personal_reports_list(self, admin_headers):
        """Test GET /api/personal-reports returns list of personal reports"""
        response = requests.get(f"{BASE_URL}/api/personal-reports", headers=admin_headers)
        assert response.status_code == 200
        data = response.json()
        
        # Verify response structure
        assert "reports" in data
        assert "total" in data
        assert "skip" in data
        assert "limit" in data
        
        print(f"✓ Personal Reports list: {data['total']} total reports")
    
    def test_get_specific_personal_report(self, admin_headers, test_report_id):
        """Test GET /api/personal-reports/{id} returns specific report"""
        response = requests.get(f"{BASE_URL}/api/personal-reports/{test_report_id}", 
                               headers=admin_headers)
        assert response.status_code == 200
        data = response.json()
        
        # Verify response structure
        assert "report" in data
        report = data["report"]
        assert report["id"] == test_report_id
        assert report["article_type"] == "Personal Report (Organic)"
        assert "title" in report
        assert "content" in report
        assert "is_owner" in report
        
        print(f"✓ Get specific report: {report['title']}")
        
        # Clean up
        requests.delete(f"{BASE_URL}/api/personal-reports/{test_report_id}", headers=admin_headers)
    
    def test_update_personal_report(self, admin_headers, test_report_id):
        """Test PUT /api/personal-reports/{id} updates report"""
        update_data = {
            "title": "TEST_Updated_Report_Title",
            "content": "This is the updated content of my personal report. I added more details about my observations.",
            "topic": "Updated Topic"
        }
        
        response = requests.put(f"{BASE_URL}/api/personal-reports/{test_report_id}", 
                               headers=admin_headers, json=update_data)
        assert response.status_code == 200
        data = response.json()
        
        assert data["success"] == True
        assert "updated_fields" in data
        
        # Verify update was applied
        verify_response = requests.get(f"{BASE_URL}/api/personal-reports/{test_report_id}", 
                                       headers=admin_headers)
        updated_report = verify_response.json()["report"]
        assert updated_report["title"] == update_data["title"]
        
        print(f"✓ Personal Report updated: {data['updated_fields']}")
        
        # Clean up
        requests.delete(f"{BASE_URL}/api/personal-reports/{test_report_id}", headers=admin_headers)
    
    def test_delete_personal_report(self, admin_headers):
        """Test DELETE /api/personal-reports/{id} deletes report"""
        # First create a report to delete
        report_data = {
            "title": f"TEST_Report_To_Delete_{datetime.now().strftime('%Y%m%d_%H%M%S')}",
            "content": "This report will be deleted.",
            "topic": "Delete Test"
        }
        
        create_response = requests.post(f"{BASE_URL}/api/personal-reports", 
                                       headers=admin_headers, json=report_data)
        report_id = create_response.json()["report_id"]
        
        # Delete the report
        response = requests.delete(f"{BASE_URL}/api/personal-reports/{report_id}", 
                                  headers=admin_headers)
        assert response.status_code == 200
        data = response.json()
        assert data["success"] == True
        
        # Verify deletion
        verify_response = requests.get(f"{BASE_URL}/api/personal-reports/{report_id}", 
                                       headers=admin_headers)
        assert verify_response.status_code == 404
        
        print("✓ Personal Report deleted successfully")


class TestAdminSettings:
    """Test admin settings have correct values"""
    
    @pytest.fixture
    def admin_headers(self):
        """Get admin authentication headers"""
        response = requests.post(f"{BASE_URL}/api/auth/login", json={
            "email": "jjspilot24@gmail.com",
            "password": "InfoPilot2024!"
        })
        assert response.status_code == 200
        token = response.json()["token"]
        return {"Authorization": f"Bearer {token}"}
    
    def test_admin_settings_values(self, admin_headers):
        """Test admin settings have correct default values"""
        # Initialize settings first
        requests.post(f"{BASE_URL}/api/admin/settings/init", headers=admin_headers)
        
        response = requests.get(f"{BASE_URL}/api/admin/settings", headers=admin_headers)
        assert response.status_code == 200
        settings = response.json()
        
        # Verify collation_limit = 40
        assert settings.get("collation_limit") == 40, f"Expected collation_limit=40, got {settings.get('collation_limit')}"
        
        # Verify newsletter times
        assert settings.get("newsletter_time_1") == "05:46", f"Expected newsletter_time_1=05:46, got {settings.get('newsletter_time_1')}"
        assert settings.get("newsletter_time_2") == "09:42", f"Expected newsletter_time_2=09:42, got {settings.get('newsletter_time_2')}"
        assert settings.get("newsletter_time_3") == "16:20", f"Expected newsletter_time_3=16:20, got {settings.get('newsletter_time_3')}"
        
        print(f"✓ Admin settings verified:")
        print(f"  - collation_limit: {settings.get('collation_limit')}")
        print(f"  - newsletter_time_1: {settings.get('newsletter_time_1')}")
        print(f"  - newsletter_time_2: {settings.get('newsletter_time_2')}")
        print(f"  - newsletter_time_3: {settings.get('newsletter_time_3')}")


class TestUnpaidPriceControls:
    """Test Unpaid User Price Controls (existing feature)"""
    
    @pytest.fixture
    def admin_headers(self):
        """Get admin authentication headers"""
        response = requests.post(f"{BASE_URL}/api/auth/login", json={
            "email": "jjspilot24@gmail.com",
            "password": "InfoPilot2024!"
        })
        assert response.status_code == 200
        token = response.json()["token"]
        return {"Authorization": f"Bearer {token}"}
    
    def test_get_unpaid_price_controls(self, admin_headers):
        """Test GET /api/admin/unpaid-price-controls returns settings"""
        response = requests.get(f"{BASE_URL}/api/admin/unpaid-price-controls", headers=admin_headers)
        assert response.status_code == 200
        data = response.json()
        
        assert "settings" in data
        settings = data["settings"]
        
        # Verify required keys
        assert "unpaid_price_control_enabled" in settings
        assert "unpaid_max_protocol_price" in settings
        assert "unpaid_max_bundle_price" in settings
        assert "unpaid_can_sell" in settings
        
        # Verify OFF by default
        assert settings["unpaid_price_control_enabled"] == False
        
        print(f"✓ Unpaid price controls: enabled={settings['unpaid_price_control_enabled']}")


class TestCategoriesAndSearch:
    """Test categories and search functionality"""
    
    @pytest.fixture
    def admin_headers(self):
        """Get admin authentication headers"""
        response = requests.post(f"{BASE_URL}/api/auth/login", json={
            "email": "jjspilot24@gmail.com",
            "password": "InfoPilot2024!"
        })
        assert response.status_code == 200
        token = response.json()["token"]
        return {"Authorization": f"Bearer {token}"}
    
    def test_get_categories(self, admin_headers):
        """Test GET /api/categories returns user categories"""
        response = requests.get(f"{BASE_URL}/api/categories", headers=admin_headers)
        assert response.status_code == 200
        data = response.json()
        
        # API returns list directly or wrapped in categories key
        if isinstance(data, list):
            categories = data
        else:
            categories = data.get("categories", [])
        
        assert len(categories) >= 0  # Can be empty for new users
        print(f"✓ Categories: {len(categories)} categories found")
    
    def test_ultimate_search_stats(self, admin_headers):
        """Test GET /api/ultimate-search/stats returns statistics"""
        response = requests.get(f"{BASE_URL}/api/ultimate-search/stats", headers=admin_headers)
        assert response.status_code == 200
        data = response.json()
        
        assert "total_results" in data
        print(f"✓ Ultimate search stats: {data['total_results']} total results")


if __name__ == "__main__":
    pytest.main([__file__, "-v", "--tb=short"])
