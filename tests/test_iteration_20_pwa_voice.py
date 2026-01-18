"""
Test Suite for Iteration 20: PWA and Voice Search Features
Tests:
- PWA manifest.json accessibility and validity
- Service worker accessibility
- App icons accessibility
- Voice search UI elements (tested via frontend)
- Existing features still working (marketplace, chat, admin)
"""

import pytest
import requests
import os

BASE_URL = os.environ.get('REACT_APP_BACKEND_URL', '').rstrip('/')

class TestPWAManifest:
    """Test PWA manifest.json is valid and accessible"""
    
    def test_manifest_accessible(self):
        """Test manifest.json is accessible via HTTP"""
        response = requests.get(f"{BASE_URL}/manifest.json")
        assert response.status_code == 200, f"Manifest not accessible: {response.status_code}"
        print("✓ manifest.json is accessible")
    
    def test_manifest_valid_json(self):
        """Test manifest.json is valid JSON"""
        response = requests.get(f"{BASE_URL}/manifest.json")
        assert response.status_code == 200
        manifest = response.json()
        assert isinstance(manifest, dict), "Manifest is not a valid JSON object"
        print("✓ manifest.json is valid JSON")
    
    def test_manifest_required_fields(self):
        """Test manifest.json has required PWA fields"""
        response = requests.get(f"{BASE_URL}/manifest.json")
        manifest = response.json()
        
        required_fields = ['name', 'short_name', 'start_url', 'display', 'icons']
        for field in required_fields:
            assert field in manifest, f"Missing required field: {field}"
        
        print(f"✓ Manifest has all required fields: {required_fields}")
    
    def test_manifest_icons_array(self):
        """Test manifest.json has icons array with proper structure"""
        response = requests.get(f"{BASE_URL}/manifest.json")
        manifest = response.json()
        
        assert 'icons' in manifest, "Missing icons array"
        assert isinstance(manifest['icons'], list), "Icons is not an array"
        assert len(manifest['icons']) > 0, "Icons array is empty"
        
        # Check first icon has required properties
        icon = manifest['icons'][0]
        assert 'src' in icon, "Icon missing src"
        assert 'sizes' in icon, "Icon missing sizes"
        assert 'type' in icon, "Icon missing type"
        
        print(f"✓ Manifest has {len(manifest['icons'])} icons with proper structure")
    
    def test_manifest_display_mode(self):
        """Test manifest has standalone display mode for PWA"""
        response = requests.get(f"{BASE_URL}/manifest.json")
        manifest = response.json()
        
        assert manifest.get('display') == 'standalone', f"Display mode is {manifest.get('display')}, expected 'standalone'"
        print("✓ Manifest has standalone display mode")


class TestServiceWorker:
    """Test service worker is accessible"""
    
    def test_service_worker_accessible(self):
        """Test service-worker.js is accessible"""
        response = requests.get(f"{BASE_URL}/service-worker.js")
        assert response.status_code == 200, f"Service worker not accessible: {response.status_code}"
        print("✓ service-worker.js is accessible")
    
    def test_service_worker_content_type(self):
        """Test service worker has correct content type"""
        response = requests.get(f"{BASE_URL}/service-worker.js")
        content_type = response.headers.get('content-type', '')
        assert 'javascript' in content_type or 'text' in content_type, f"Unexpected content type: {content_type}"
        print(f"✓ Service worker content type: {content_type}")
    
    def test_service_worker_has_install_event(self):
        """Test service worker has install event listener"""
        response = requests.get(f"{BASE_URL}/service-worker.js")
        content = response.text
        assert "addEventListener('install'" in content or 'addEventListener("install"' in content, "Missing install event listener"
        print("✓ Service worker has install event listener")
    
    def test_service_worker_has_fetch_event(self):
        """Test service worker has fetch event listener"""
        response = requests.get(f"{BASE_URL}/service-worker.js")
        content = response.text
        assert "addEventListener('fetch'" in content or 'addEventListener("fetch"' in content, "Missing fetch event listener"
        print("✓ Service worker has fetch event listener")


class TestAppIcons:
    """Test PWA app icons are accessible"""
    
    @pytest.mark.parametrize("size", ["72x72", "96x96", "128x128", "144x144", "152x152", "192x192", "384x384", "512x512"])
    def test_icon_accessible(self, size):
        """Test each icon size is accessible"""
        response = requests.get(f"{BASE_URL}/icons/icon-{size}.png")
        assert response.status_code == 200, f"Icon {size} not accessible: {response.status_code}"
        print(f"✓ Icon {size} is accessible")
    
    def test_icon_192_content_type(self):
        """Test 192x192 icon has correct content type"""
        response = requests.get(f"{BASE_URL}/icons/icon-192x192.png")
        content_type = response.headers.get('content-type', '')
        assert 'image/png' in content_type, f"Unexpected content type: {content_type}"
        print(f"✓ Icon 192x192 content type: {content_type}")


class TestExistingFeatures:
    """Test existing features still work"""
    
    @pytest.fixture(autouse=True)
    def setup(self):
        """Setup test user authentication"""
        self.session = requests.Session()
        # Login as test user
        login_response = self.session.post(f"{BASE_URL}/api/auth/login", json={
            "email": "testuser_new@example.com",
            "password": "password123"
        })
        if login_response.status_code == 200:
            self.token = login_response.json().get('token')
            self.session.headers.update({"Authorization": f"Bearer {self.token}"})
        else:
            pytest.skip("Could not authenticate test user")
    
    def test_search_engines_endpoint(self):
        """Test search engines endpoint works"""
        response = self.session.get(f"{BASE_URL}/api/search/engines")
        assert response.status_code == 200, f"Search engines endpoint failed: {response.status_code}"
        data = response.json()
        assert 'engines' in data, "Missing engines in response"
        print(f"✓ Search engines endpoint working - {len(data['engines'])} engines available")
    
    def test_categories_endpoint(self):
        """Test categories endpoint works"""
        response = self.session.get(f"{BASE_URL}/api/categories")
        assert response.status_code == 200, f"Categories endpoint failed: {response.status_code}"
        data = response.json()
        assert 'categories' in data, "Missing categories in response"
        print(f"✓ Categories endpoint working - {len(data['categories'])} categories")
    
    def test_marketplace_endpoint(self):
        """Test marketplace endpoint works"""
        response = self.session.get(f"{BASE_URL}/api/marketplace/protocols")
        assert response.status_code == 200, f"Marketplace endpoint failed: {response.status_code}"
        data = response.json()
        assert 'protocols' in data, "Missing protocols in response"
        print(f"✓ Marketplace endpoint working - {len(data['protocols'])} protocols")
    
    def test_templates_endpoint(self):
        """Test templates endpoint works"""
        response = self.session.get(f"{BASE_URL}/api/templates")
        assert response.status_code == 200, f"Templates endpoint failed: {response.status_code}"
        print("✓ Templates endpoint working")
    
    def test_chat_rooms_endpoint(self):
        """Test chat rooms endpoint works"""
        response = self.session.get(f"{BASE_URL}/api/chat/rooms")
        assert response.status_code == 200, f"Chat rooms endpoint failed: {response.status_code}"
        data = response.json()
        assert 'rooms' in data, "Missing rooms in response"
        print(f"✓ Chat rooms endpoint working - {len(data['rooms'])} rooms")
    
    def test_copy_protection_my_purchases(self):
        """Test copy protection my-purchases endpoint works"""
        response = self.session.get(f"{BASE_URL}/api/marketplace/my-purchases")
        assert response.status_code == 200, f"My purchases endpoint failed: {response.status_code}"
        data = response.json()
        assert 'purchased_protocol_ids' in data, "Missing purchased_protocol_ids"
        assert 'owned_protocol_ids' in data, "Missing owned_protocol_ids"
        print("✓ Copy protection my-purchases endpoint working")


class TestAdminFeatures:
    """Test admin features still work"""
    
    @pytest.fixture(autouse=True)
    def setup(self):
        """Setup admin authentication"""
        self.session = requests.Session()
        # Login as admin
        login_response = self.session.post(f"{BASE_URL}/api/auth/login", json={
            "email": "admin@infopilot.com",
            "password": "admin123"
        })
        if login_response.status_code == 200:
            self.token = login_response.json().get('token')
            self.session.headers.update({"Authorization": f"Bearer {self.token}"})
        else:
            pytest.skip("Could not authenticate admin user")
    
    def test_admin_stats_endpoint(self):
        """Test admin system-status endpoint works"""
        response = self.session.get(f"{BASE_URL}/api/admin/system-status")
        assert response.status_code == 200, f"Admin system-status endpoint failed: {response.status_code}"
        data = response.json()
        assert 'services' in data, "Missing services in response"
        assert 'database' in data.get('services', {}), "Missing database in services"
        print(f"✓ Admin system-status endpoint working - status: {data.get('overall_status')}")
    
    def test_admin_users_endpoint(self):
        """Test admin users endpoint works"""
        response = self.session.get(f"{BASE_URL}/api/admin/users")
        # Admin users endpoint may not exist, check for 200 or 404
        if response.status_code == 200:
            data = response.json()
            print(f"✓ Admin users endpoint working")
        elif response.status_code == 404:
            pytest.skip("Admin users endpoint not implemented")
        else:
            assert False, f"Admin users endpoint failed: {response.status_code}"


if __name__ == "__main__":
    pytest.main([__file__, "-v", "--tb=short"])
