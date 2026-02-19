"""
Iteration 54 Tests - Admin Panel UI for Price Controls and Document Type Settings
Tests:
1. Admin login
2. Global Price Controls API (GET/PUT)
3. Document Type Settings API (GET/PUT) - 15 doc types
4. Personal Reports API (GET)
5. Unpaid Price Controls API (GET)
"""
import pytest
import requests
import os

BASE_URL = os.environ.get('REACT_APP_BACKEND_URL', 'https://infopilot-explorer-3.preview.emergentagent.com')

# Admin credentials
ADMIN_EMAIL = "jjspilot24@gmail.com"
ADMIN_PASSWORD = "InfoPilot2024!"


class TestIteration54Features:
    """Test suite for Iteration 54 - Admin Panel Price Controls and Doc Type Settings"""
    
    @pytest.fixture(autouse=True)
    def setup(self):
        """Setup test session"""
        self.session = requests.Session()
        self.session.headers.update({"Content-Type": "application/json"})
        self.token = None
    
    def get_auth_token(self):
        """Get authentication token for admin user"""
        if self.token:
            return self.token
        
        response = self.session.post(
            f"{BASE_URL}/api/auth/login",
            json={"email": ADMIN_EMAIL, "password": ADMIN_PASSWORD}
        )
        
        if response.status_code == 200:
            data = response.json()
            self.token = data.get("token")
            return self.token
        return None
    
    # ==================== HEALTH CHECK ====================
    
    def test_01_health_endpoint(self):
        """Test health endpoint is accessible"""
        response = self.session.get(f"{BASE_URL}/api/health")
        assert response.status_code == 200
        data = response.json()
        assert data.get("status") == "healthy"
        print(f"✅ Health check passed: {data}")
    
    # ==================== AUTHENTICATION ====================
    
    def test_02_admin_login(self):
        """Test admin login with valid credentials"""
        response = self.session.post(
            f"{BASE_URL}/api/auth/login",
            json={"email": ADMIN_EMAIL, "password": ADMIN_PASSWORD}
        )
        assert response.status_code == 200
        data = response.json()
        assert "token" in data
        assert "user" in data
        assert data["user"]["email"].lower() == ADMIN_EMAIL.lower()
        print(f"✅ Admin login successful: {data['user']['email']}")
    
    def test_03_invalid_login_rejected(self):
        """Test invalid credentials are rejected"""
        response = self.session.post(
            f"{BASE_URL}/api/auth/login",
            json={"email": "invalid@test.com", "password": "wrongpassword"}
        )
        assert response.status_code in [401, 404]
        print(f"✅ Invalid login correctly rejected with status {response.status_code}")
    
    # ==================== GLOBAL PRICE CONTROLS ====================
    
    def test_04_global_price_controls_get(self):
        """Test GET /api/admin/global-price-controls returns settings"""
        token = self.get_auth_token()
        assert token, "Failed to get auth token"
        
        response = self.session.get(
            f"{BASE_URL}/api/admin/global-price-controls",
            headers={"Authorization": f"Bearer {token}"}
        )
        assert response.status_code == 200
        data = response.json()
        
        # Verify response structure
        assert "settings" in data
        settings = data["settings"]
        
        # Verify all expected keys are present
        expected_keys = [
            "global_price_control_enabled",
            "global_max_protocol_price",
            "global_max_bundle_price",
            "global_min_protocol_price"
        ]
        for key in expected_keys:
            assert key in settings, f"Missing key: {key}"
        
        print(f"✅ Global Price Controls GET: {settings}")
    
    def test_05_global_price_controls_put(self):
        """Test PUT /api/admin/global-price-controls updates settings"""
        token = self.get_auth_token()
        assert token, "Failed to get auth token"
        
        # First get current settings
        get_response = self.session.get(
            f"{BASE_URL}/api/admin/global-price-controls",
            headers={"Authorization": f"Bearer {token}"}
        )
        original_settings = get_response.json()["settings"]
        
        # Update with test values
        test_update = {
            "global_max_protocol_price": 88.88
        }
        
        response = self.session.put(
            f"{BASE_URL}/api/admin/global-price-controls",
            headers={"Authorization": f"Bearer {token}"},
            json=test_update
        )
        assert response.status_code == 200
        data = response.json()
        assert data.get("success") == True
        print(f"✅ Global Price Controls PUT successful: {data}")
        
        # Restore original value
        restore_update = {
            "global_max_protocol_price": original_settings.get("global_max_protocol_price", 99.99)
        }
        self.session.put(
            f"{BASE_URL}/api/admin/global-price-controls",
            headers={"Authorization": f"Bearer {token}"},
            json=restore_update
        )
    
    # ==================== DOCUMENT TYPE SETTINGS ====================
    
    def test_06_doctype_settings_get(self):
        """Test GET /api/admin/doctype-settings returns 15 document types"""
        token = self.get_auth_token()
        assert token, "Failed to get auth token"
        
        response = self.session.get(
            f"{BASE_URL}/api/admin/doctype-settings",
            headers={"Authorization": f"Bearer {token}"}
        )
        assert response.status_code == 200
        data = response.json()
        
        # Verify response structure
        assert "settings" in data
        assert "document_types" in data
        
        # Verify 15 document types
        doc_types = data["document_types"]
        assert len(doc_types) == 15, f"Expected 15 document types, got {len(doc_types)}"
        
        # Verify expected document types are present
        expected_types = [
            "PhD Informative",
            "Informative",
            "InfoPilot Exclusive",
            "InfoBook Exclusive",
            "News Article",
            "Blog Post",
            "Forum",
            "Personal Report (Organic)",
            "Personal Report (Collected)",
            "Academic Paper",
            "Government",
            "Wiki",
            "Video",
            "PDF Document",
            "Webpage"
        ]
        
        actual_types = [dt["type"] for dt in doc_types]
        for expected in expected_types:
            assert expected in actual_types, f"Missing document type: {expected}"
        
        # Verify settings contain InfoJet 2.0 protocols
        settings = data["settings"]
        assert "doctype_informative_protocol" in settings
        assert "doctype_phd_protocol" in settings
        assert "doctype_news_protocol" in settings
        
        print(f"✅ Document Type Settings GET: {len(doc_types)} types found")
        print(f"   Document types: {actual_types}")
    
    def test_07_doctype_settings_put(self):
        """Test PUT /api/admin/doctype-settings updates protocols"""
        token = self.get_auth_token()
        assert token, "Failed to get auth token"
        
        # First get current settings
        get_response = self.session.get(
            f"{BASE_URL}/api/admin/doctype-settings",
            headers={"Authorization": f"Bearer {token}"}
        )
        original_settings = get_response.json()["settings"]
        
        # Update with test value
        test_update = {
            "doctype_phd_min_words": 1600
        }
        
        response = self.session.put(
            f"{BASE_URL}/api/admin/doctype-settings",
            headers={"Authorization": f"Bearer {token}"},
            json=test_update
        )
        assert response.status_code == 200
        data = response.json()
        assert data.get("success") == True
        print(f"✅ Document Type Settings PUT successful: {data}")
        
        # Verify the update
        verify_response = self.session.get(
            f"{BASE_URL}/api/admin/doctype-settings",
            headers={"Authorization": f"Bearer {token}"}
        )
        verify_data = verify_response.json()
        assert verify_data["settings"]["doctype_phd_min_words"] == 1600
        print(f"✅ Verified update: doctype_phd_min_words = 1600")
        
        # Restore original value
        restore_update = {
            "doctype_phd_min_words": original_settings.get("doctype_phd_min_words", 1500)
        }
        self.session.put(
            f"{BASE_URL}/api/admin/doctype-settings",
            headers={"Authorization": f"Bearer {token}"},
            json=restore_update
        )
    
    # ==================== PERSONAL REPORTS ====================
    
    def test_08_personal_reports_get(self):
        """Test GET /api/personal-reports returns user's personal reports"""
        token = self.get_auth_token()
        assert token, "Failed to get auth token"
        
        response = self.session.get(
            f"{BASE_URL}/api/personal-reports",
            headers={"Authorization": f"Bearer {token}"}
        )
        assert response.status_code == 200
        data = response.json()
        
        # Response can be a list or object with 'reports' key
        if isinstance(data, list):
            reports = data
        else:
            assert "reports" in data, "Expected 'reports' key in response"
            reports = data["reports"]
        
        assert isinstance(reports, list), "Expected list of personal reports"
        print(f"✅ Personal Reports GET: {len(reports)} reports found")
    
    # ==================== UNPAID PRICE CONTROLS ====================
    
    def test_09_unpaid_price_controls_get(self):
        """Test GET /api/admin/unpaid-price-controls returns settings"""
        token = self.get_auth_token()
        assert token, "Failed to get auth token"
        
        response = self.session.get(
            f"{BASE_URL}/api/admin/unpaid-price-controls",
            headers={"Authorization": f"Bearer {token}"}
        )
        assert response.status_code == 200
        data = response.json()
        
        # Verify response structure
        assert "settings" in data
        settings = data["settings"]
        
        # Verify expected keys
        expected_keys = [
            "unpaid_price_control_enabled",
            "unpaid_max_protocol_price",
            "unpaid_max_bundle_price",
            "unpaid_can_sell"
        ]
        for key in expected_keys:
            assert key in settings, f"Missing key: {key}"
        
        print(f"✅ Unpaid Price Controls GET: {settings}")
    
    # ==================== ADMIN SETTINGS ====================
    
    def test_10_admin_settings_get(self):
        """Test GET /api/admin/settings returns admin settings"""
        token = self.get_auth_token()
        assert token, "Failed to get auth token"
        
        response = self.session.get(
            f"{BASE_URL}/api/admin/settings",
            headers={"Authorization": f"Bearer {token}"}
        )
        assert response.status_code == 200
        data = response.json()
        
        # Settings can be array or object
        if isinstance(data, list):
            print(f"✅ Admin Settings GET: {len(data)} settings found (array format)")
        else:
            print(f"✅ Admin Settings GET: {len(data.keys())} settings found (object format)")
    
    # ==================== ARTICLE TYPES ====================
    
    def test_11_article_types_get(self):
        """Test GET /api/article-types returns document types"""
        response = self.session.get(f"{BASE_URL}/api/article-types")
        assert response.status_code == 200
        data = response.json()
        
        # Response can be a list or object with 'types' key
        if isinstance(data, list):
            types = data
        else:
            assert "types" in data, "Expected 'types' key in response"
            types = data["types"]
        
        # Verify we have document types
        assert len(types) >= 10, f"Expected at least 10 article types, got {len(types)}"
        print(f"✅ Article Types GET: {len(types)} types found")


if __name__ == "__main__":
    pytest.main([__file__, "-v", "--tb=short"])
