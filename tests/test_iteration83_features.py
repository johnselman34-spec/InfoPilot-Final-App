"""
InfoPilot Explorer - Iteration 83 Feature Tests
Testing:
1. Clean Category function - POST /api/categories/{id}/clean?mode=delete_all
2. Marketplace Protocol Copy - copy free protocols
3. Map View data source toggle
4. Statistics Page data source toggle
5. Violation Alerts admin feature - GET/PUT /api/admin/violation-alerts/settings
6. Email change on Settings page - PUT /api/auth/update-email
7. Password change on Settings page - PUT /api/auth/change-password
8. Meta tags and Open Graph data in index.html
"""
import pytest
import requests
import os

BASE_URL = os.environ.get('REACT_APP_BACKEND_URL', 'https://info-explorer-hub.preview.emergentagent.com')

# Test credentials
ADMIN_EMAIL = "jjspilot24@gmail.com"
ADMIN_PASSWORD = "InfoPilot2024!"


class TestAuthentication:
    """Authentication tests"""
    
    @pytest.fixture(scope="class")
    def admin_token(self):
        """Get admin authentication token"""
        response = requests.post(f"{BASE_URL}/api/auth/login", json={
            "email": ADMIN_EMAIL,
            "password": ADMIN_PASSWORD
        })
        if response.status_code == 200:
            return response.json().get("token")
        pytest.skip("Admin authentication failed - skipping authenticated tests")
    
    def test_admin_login(self):
        """Test admin login works"""
        response = requests.post(f"{BASE_URL}/api/auth/login", json={
            "email": ADMIN_EMAIL,
            "password": ADMIN_PASSWORD
        })
        assert response.status_code == 200
        data = response.json()
        assert "token" in data
        assert "user" in data
        print(f"✅ Admin login successful - is_admin: {data['user'].get('is_admin')}")


class TestCleanCategoryFunction:
    """Test Clean Category function - POST /api/categories/{id}/clean?mode=delete_all"""
    
    @pytest.fixture(scope="class")
    def admin_token(self):
        """Get admin authentication token"""
        response = requests.post(f"{BASE_URL}/api/auth/login", json={
            "email": ADMIN_EMAIL,
            "password": ADMIN_PASSWORD
        })
        if response.status_code == 200:
            return response.json().get("token")
        pytest.skip("Admin authentication failed")
    
    def test_get_categories(self, admin_token):
        """Test getting categories list"""
        response = requests.get(f"{BASE_URL}/api/categories", headers={
            "Authorization": f"Bearer {admin_token}"
        })
        assert response.status_code == 200
        data = response.json()
        assert isinstance(data, list)
        print(f"✅ Got {len(data)} categories")
        return data
    
    def test_clean_category_endpoint_exists(self, admin_token):
        """Test that clean category endpoint exists and returns proper error for invalid ID"""
        # Test with invalid category ID to verify endpoint exists
        response = requests.post(
            f"{BASE_URL}/api/categories/invalid_id/clean?mode=delete_all",
            headers={"Authorization": f"Bearer {admin_token}"}
        )
        # Should return 404 or 422 (validation error), not 500
        assert response.status_code in [404, 422, 400]
        print(f"✅ Clean category endpoint exists - returns {response.status_code} for invalid ID")
    
    def test_clean_category_modes(self, admin_token):
        """Test clean category with different modes"""
        # First get a category
        categories_response = requests.get(f"{BASE_URL}/api/categories", headers={
            "Authorization": f"Bearer {admin_token}"
        })
        
        if categories_response.status_code == 200:
            categories = categories_response.json()
            if categories:
                cat_id = categories[0].get("id")
                
                # Test remove mode
                response = requests.post(
                    f"{BASE_URL}/api/categories/{cat_id}/clean?mode=remove",
                    headers={"Authorization": f"Bearer {admin_token}"}
                )
                assert response.status_code == 200
                data = response.json()
                assert "success" in data
                assert data.get("mode") == "remove"
                print(f"✅ Clean category (remove mode) works - affected {data.get('results_affected', 0)} results")
                
                # Test delete mode
                response = requests.post(
                    f"{BASE_URL}/api/categories/{cat_id}/clean?mode=delete",
                    headers={"Authorization": f"Bearer {admin_token}"}
                )
                assert response.status_code == 200
                data = response.json()
                assert "success" in data
                assert data.get("mode") == "delete"
                print(f"✅ Clean category (delete mode) works - deleted {data.get('results_deleted', 0)} results")
                
                # Test delete_all mode
                response = requests.post(
                    f"{BASE_URL}/api/categories/{cat_id}/clean?mode=delete_all",
                    headers={"Authorization": f"Bearer {admin_token}"}
                )
                assert response.status_code == 200
                data = response.json()
                assert "success" in data
                assert data.get("mode") == "delete_all"
                print(f"✅ Clean category (delete_all mode) works - deleted {data.get('results_deleted', 0)} results")
            else:
                print("⚠️ No categories found to test clean function")
        else:
            pytest.skip("Could not get categories")


class TestMarketplaceProtocolCopy:
    """Test Marketplace Protocol Copy functionality"""
    
    @pytest.fixture(scope="class")
    def admin_token(self):
        """Get admin authentication token"""
        response = requests.post(f"{BASE_URL}/api/auth/login", json={
            "email": ADMIN_EMAIL,
            "password": ADMIN_PASSWORD
        })
        if response.status_code == 200:
            return response.json().get("token")
        pytest.skip("Admin authentication failed")
    
    def test_get_marketplace_protocols(self, admin_token):
        """Test getting marketplace protocols"""
        response = requests.get(f"{BASE_URL}/api/marketplace/protocols", headers={
            "Authorization": f"Bearer {admin_token}"
        })
        assert response.status_code == 200
        data = response.json()
        assert "protocols" in data
        print(f"✅ Got {len(data.get('protocols', []))} marketplace protocols")
        return data.get("protocols", [])
    
    def test_copy_free_protocol(self, admin_token):
        """Test copying a free protocol"""
        # First get protocols
        protocols_response = requests.get(f"{BASE_URL}/api/marketplace/protocols", headers={
            "Authorization": f"Bearer {admin_token}"
        })
        
        if protocols_response.status_code == 200:
            protocols = protocols_response.json().get("protocols", [])
            # Find a free protocol
            free_protocols = [p for p in protocols if p.get("price", 0) == 0 or p.get("is_free")]
            
            if free_protocols:
                protocol_id = free_protocols[0].get("id")
                
                # Test copy endpoint
                response = requests.post(
                    f"{BASE_URL}/api/marketplace/protocols/{protocol_id}/copy",
                    headers={"Authorization": f"Bearer {admin_token}"}
                )
                assert response.status_code == 200
                data = response.json()
                assert "protocol" in data
                print(f"✅ Free protocol copy works - got protocol string")
            else:
                print("⚠️ No free protocols found to test copy function")
        else:
            pytest.skip("Could not get marketplace protocols")


class TestViolationAlertsAdmin:
    """Test Violation Alerts admin feature"""
    
    @pytest.fixture(scope="class")
    def admin_token(self):
        """Get admin authentication token"""
        response = requests.post(f"{BASE_URL}/api/auth/login", json={
            "email": ADMIN_EMAIL,
            "password": ADMIN_PASSWORD
        })
        if response.status_code == 200:
            return response.json().get("token")
        pytest.skip("Admin authentication failed")
    
    def test_get_violation_alerts_settings(self, admin_token):
        """Test GET /api/admin/violation-alerts/settings"""
        response = requests.get(
            f"{BASE_URL}/api/admin/violation-alerts/settings",
            headers={"Authorization": f"Bearer {admin_token}"}
        )
        assert response.status_code == 200
        data = response.json()
        # Check expected fields
        assert "enabled" in data
        assert "threshold" in data
        assert "time_window_hours" in data
        print(f"✅ Violation alerts settings: enabled={data.get('enabled')}, threshold={data.get('threshold')}")
    
    def test_update_violation_alerts_settings(self, admin_token):
        """Test PUT /api/admin/violation-alerts/settings"""
        # First get current settings
        get_response = requests.get(
            f"{BASE_URL}/api/admin/violation-alerts/settings",
            headers={"Authorization": f"Bearer {admin_token}"}
        )
        current_settings = get_response.json()
        
        # Update settings
        new_settings = {
            "enabled": True,
            "threshold": 15,
            "time_window_hours": 24,
            "email_notifications": True,
            "notification_emails": current_settings.get("notification_emails", [])
        }
        
        response = requests.put(
            f"{BASE_URL}/api/admin/violation-alerts/settings",
            headers={
                "Authorization": f"Bearer {admin_token}",
                "Content-Type": "application/json"
            },
            json=new_settings
        )
        assert response.status_code == 200
        data = response.json()
        assert data.get("success") == True
        print(f"✅ Violation alerts settings updated successfully")
    
    def test_check_violation_alerts(self, admin_token):
        """Test POST /api/admin/violation-alerts/check"""
        response = requests.post(
            f"{BASE_URL}/api/admin/violation-alerts/check",
            headers={"Authorization": f"Bearer {admin_token}"}
        )
        assert response.status_code == 200
        data = response.json()
        assert "message" in data
        print(f"✅ Violation alerts check: {data.get('message')}")


class TestAuthEmailPasswordChange:
    """Test email and password change functionality"""
    
    @pytest.fixture(scope="class")
    def admin_token(self):
        """Get admin authentication token"""
        response = requests.post(f"{BASE_URL}/api/auth/login", json={
            "email": ADMIN_EMAIL,
            "password": ADMIN_PASSWORD
        })
        if response.status_code == 200:
            return response.json().get("token")
        pytest.skip("Admin authentication failed")
    
    def test_update_email_endpoint_exists(self, admin_token):
        """Test PUT /api/auth/update-email endpoint exists"""
        # Test with missing fields to verify endpoint exists
        response = requests.put(
            f"{BASE_URL}/api/auth/update-email",
            headers={
                "Authorization": f"Bearer {admin_token}",
                "Content-Type": "application/json"
            },
            json={}
        )
        # Should return 400 (bad request for missing fields), not 404 or 500
        assert response.status_code == 400
        data = response.json()
        assert "detail" in data
        print(f"✅ Update email endpoint exists - returns validation error for missing fields")
    
    def test_change_password_endpoint_exists(self, admin_token):
        """Test PUT /api/auth/change-password endpoint exists"""
        # Test with missing fields to verify endpoint exists
        response = requests.put(
            f"{BASE_URL}/api/auth/change-password",
            headers={
                "Authorization": f"Bearer {admin_token}",
                "Content-Type": "application/json"
            },
            json={}
        )
        # Should return 400 (bad request for missing fields), not 404 or 500
        assert response.status_code == 400
        data = response.json()
        assert "detail" in data
        print(f"✅ Change password endpoint exists - returns validation error for missing fields")
    
    def test_change_password_wrong_current(self, admin_token):
        """Test change password with wrong current password"""
        response = requests.put(
            f"{BASE_URL}/api/auth/change-password",
            headers={
                "Authorization": f"Bearer {admin_token}",
                "Content-Type": "application/json"
            },
            json={
                "current_password": "wrong_password",
                "new_password": "NewPassword123!"
            }
        )
        # Should return 400 for incorrect password
        assert response.status_code == 400
        print(f"✅ Change password correctly rejects wrong current password")


class TestMapAndStatisticsDataSource:
    """Test Map View and Statistics Page data source toggle"""
    
    @pytest.fixture(scope="class")
    def admin_token(self):
        """Get admin authentication token"""
        response = requests.post(f"{BASE_URL}/api/auth/login", json={
            "email": ADMIN_EMAIL,
            "password": ADMIN_PASSWORD
        })
        if response.status_code == 200:
            return response.json().get("token")
        pytest.skip("Admin authentication failed")
    
    def test_map_worldwide_endpoint(self, admin_token):
        """Test GET /api/map/worldwide endpoint for worldwide data"""
        response = requests.get(
            f"{BASE_URL}/api/map/worldwide?limit=50",
            headers={"Authorization": f"Bearer {admin_token}"}
        )
        assert response.status_code == 200
        data = response.json()
        assert "results" in data
        print(f"✅ Map worldwide endpoint works - got {len(data.get('results', []))} results")
    
    def test_ultimate_search_endpoint(self, admin_token):
        """Test GET /api/ultimate-search endpoint for personal data"""
        response = requests.get(
            f"{BASE_URL}/api/ultimate-search?limit=50",
            headers={"Authorization": f"Bearer {admin_token}"}
        )
        assert response.status_code == 200
        data = response.json()
        # Should return results array
        assert isinstance(data, (list, dict))
        print(f"✅ Ultimate search endpoint works for personal data")
    
    def test_statistics_dashboard_endpoint(self, admin_token):
        """Test GET /api/statistics/dashboard endpoint"""
        response = requests.get(
            f"{BASE_URL}/api/statistics/dashboard",
            headers={"Authorization": f"Bearer {admin_token}"}
        )
        assert response.status_code == 200
        data = response.json()
        # Check for expected statistics fields
        assert "overview" in data or "countries" in data or "us_states" in data
        print(f"✅ Statistics dashboard endpoint works")


class TestMetaTags:
    """Test Meta tags and Open Graph data in index.html"""
    
    def test_index_html_meta_tags(self):
        """Test that index.html has proper meta tags"""
        response = requests.get(f"{BASE_URL}/")
        assert response.status_code == 200
        html = response.text
        
        # Check for essential meta tags
        assert '<meta name="title"' in html or '<title>' in html
        assert '<meta name="description"' in html
        assert '<meta property="og:title"' in html
        assert '<meta property="og:description"' in html
        assert '<meta property="og:type"' in html
        assert '<meta property="twitter:card"' in html
        print(f"✅ Index.html has proper meta tags and Open Graph data")
    
    def test_index_html_structured_data(self):
        """Test that index.html has structured data"""
        response = requests.get(f"{BASE_URL}/")
        assert response.status_code == 200
        html = response.text
        
        # Check for structured data
        assert 'application/ld+json' in html
        assert 'schema.org' in html
        print(f"✅ Index.html has structured data (JSON-LD)")


class TestAdminAlerts:
    """Test admin alerts endpoint"""
    
    @pytest.fixture(scope="class")
    def admin_token(self):
        """Get admin authentication token"""
        response = requests.post(f"{BASE_URL}/api/auth/login", json={
            "email": ADMIN_EMAIL,
            "password": ADMIN_PASSWORD
        })
        if response.status_code == 200:
            return response.json().get("token")
        pytest.skip("Admin authentication failed")
    
    def test_get_admin_alerts(self, admin_token):
        """Test GET /api/admin/alerts endpoint"""
        response = requests.get(
            f"{BASE_URL}/api/admin/alerts?limit=20",
            headers={"Authorization": f"Bearer {admin_token}"}
        )
        assert response.status_code == 200
        data = response.json()
        assert "alerts" in data
        print(f"✅ Admin alerts endpoint works - got {len(data.get('alerts', []))} alerts")


if __name__ == "__main__":
    pytest.main([__file__, "-v", "--tb=short"])
