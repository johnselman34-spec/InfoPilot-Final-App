"""
PWA Features Test Suite - InfoPilot Explorer Iteration 13
Tests PWA manifest, service worker, icons, and Apple meta tags
"""

import pytest
import requests
import os

BASE_URL = os.environ.get('REACT_APP_BACKEND_URL', 'https://datascout-hub.preview.emergentagent.com')


class TestPWAManifest:
    """Test PWA manifest.json configuration"""
    
    def test_manifest_accessible(self):
        """Verify manifest.json is served at /manifest.json"""
        response = requests.get(f"{BASE_URL}/manifest.json")
        assert response.status_code == 200, f"manifest.json not accessible: {response.status_code}"
        print("PASS: manifest.json is accessible")
    
    def test_manifest_content_type(self):
        """Verify manifest.json has correct content type"""
        response = requests.get(f"{BASE_URL}/manifest.json")
        content_type = response.headers.get('content-type', '')
        assert 'json' in content_type.lower() or 'manifest' in content_type.lower(), f"Unexpected content type: {content_type}"
        print(f"PASS: manifest.json content type: {content_type}")
    
    def test_manifest_app_name(self):
        """Verify manifest has correct app name"""
        response = requests.get(f"{BASE_URL}/manifest.json")
        data = response.json()
        assert data.get('name') == 'InfoPilot Explorer', f"Wrong app name: {data.get('name')}"
        assert data.get('short_name') == 'InfoPilot', f"Wrong short name: {data.get('short_name')}"
        print(f"PASS: App name: {data.get('name')}, Short name: {data.get('short_name')}")
    
    def test_manifest_display_mode(self):
        """Verify manifest has standalone display mode for PWA"""
        response = requests.get(f"{BASE_URL}/manifest.json")
        data = response.json()
        assert data.get('display') == 'standalone', f"Wrong display mode: {data.get('display')}"
        print(f"PASS: Display mode: {data.get('display')}")
    
    def test_manifest_start_url(self):
        """Verify manifest has correct start URL"""
        response = requests.get(f"{BASE_URL}/manifest.json")
        data = response.json()
        assert data.get('start_url') == '/', f"Wrong start URL: {data.get('start_url')}"
        print(f"PASS: Start URL: {data.get('start_url')}")
    
    def test_manifest_theme_color(self):
        """Verify manifest has theme color"""
        response = requests.get(f"{BASE_URL}/manifest.json")
        data = response.json()
        assert data.get('theme_color') == '#007AFF', f"Wrong theme color: {data.get('theme_color')}"
        print(f"PASS: Theme color: {data.get('theme_color')}")
    
    def test_manifest_background_color(self):
        """Verify manifest has background color"""
        response = requests.get(f"{BASE_URL}/manifest.json")
        data = response.json()
        assert data.get('background_color') == '#FFFFF0', f"Wrong background color: {data.get('background_color')}"
        print(f"PASS: Background color: {data.get('background_color')}")
    
    def test_manifest_icons_array(self):
        """Verify manifest has icons array with required sizes"""
        response = requests.get(f"{BASE_URL}/manifest.json")
        data = response.json()
        icons = data.get('icons', [])
        assert len(icons) >= 2, f"Not enough icons: {len(icons)}"
        
        # Check for required sizes (192 and 512 are required for PWA)
        sizes = [icon.get('sizes') for icon in icons]
        assert '192x192' in sizes, "Missing 192x192 icon"
        assert '512x512' in sizes, "Missing 512x512 icon"
        print(f"PASS: Found {len(icons)} icons with sizes: {sizes}")


class TestPWAServiceWorker:
    """Test PWA service worker"""
    
    def test_service_worker_accessible(self):
        """Verify service-worker.js is accessible"""
        response = requests.get(f"{BASE_URL}/service-worker.js")
        assert response.status_code == 200, f"service-worker.js not accessible: {response.status_code}"
        print("PASS: service-worker.js is accessible")
    
    def test_service_worker_content(self):
        """Verify service worker has caching logic"""
        response = requests.get(f"{BASE_URL}/service-worker.js")
        content = response.text
        assert 'CACHE_NAME' in content or 'cache' in content.lower(), "Service worker missing cache logic"
        assert 'install' in content.lower(), "Service worker missing install event"
        assert 'fetch' in content.lower(), "Service worker missing fetch event"
        print("PASS: Service worker has caching logic")


class TestPWAIcons:
    """Test PWA icon files"""
    
    def test_icon_192_accessible(self):
        """Verify 192x192 icon is accessible"""
        response = requests.get(f"{BASE_URL}/icon-192.png")
        assert response.status_code == 200, f"icon-192.png not accessible: {response.status_code}"
        assert 'image' in response.headers.get('content-type', ''), "Wrong content type for icon"
        print("PASS: icon-192.png is accessible")
    
    def test_icon_512_accessible(self):
        """Verify 512x512 icon is accessible"""
        response = requests.get(f"{BASE_URL}/icon-512.png")
        assert response.status_code == 200, f"icon-512.png not accessible: {response.status_code}"
        assert 'image' in response.headers.get('content-type', ''), "Wrong content type for icon"
        print("PASS: icon-512.png is accessible")
    
    def test_icon_72_accessible(self):
        """Verify 72x72 icon is accessible"""
        response = requests.get(f"{BASE_URL}/icon-72.png")
        assert response.status_code == 200, f"icon-72.png not accessible: {response.status_code}"
        print("PASS: icon-72.png is accessible")
    
    def test_icon_144_accessible(self):
        """Verify 144x144 icon is accessible (for MS tiles)"""
        response = requests.get(f"{BASE_URL}/icon-144.png")
        assert response.status_code == 200, f"icon-144.png not accessible: {response.status_code}"
        print("PASS: icon-144.png is accessible")
    
    def test_icon_152_accessible(self):
        """Verify 152x152 icon is accessible (for iOS)"""
        response = requests.get(f"{BASE_URL}/icon-152.png")
        assert response.status_code == 200, f"icon-152.png not accessible: {response.status_code}"
        print("PASS: icon-152.png is accessible")
    
    def test_all_manifest_icons_accessible(self):
        """Verify all icons referenced in manifest are accessible"""
        manifest_response = requests.get(f"{BASE_URL}/manifest.json")
        manifest = manifest_response.json()
        
        for icon in manifest.get('icons', []):
            icon_src = icon.get('src')
            response = requests.get(f"{BASE_URL}/{icon_src}")
            assert response.status_code == 200, f"Icon {icon_src} not accessible: {response.status_code}"
            print(f"PASS: {icon_src} is accessible")


class TestHealthAndAPI:
    """Test API health and basic endpoints"""
    
    def test_health_endpoint(self):
        """Verify /api/health returns healthy status"""
        response = requests.get(f"{BASE_URL}/api/health")
        assert response.status_code == 200, f"Health check failed: {response.status_code}"
        data = response.json()
        assert data.get('status') == 'healthy', f"Unhealthy status: {data.get('status')}"
        print(f"PASS: Health check returned: {data}")
    
    def test_categories_endpoint(self):
        """Verify categories endpoint is accessible"""
        response = requests.get(f"{BASE_URL}/api/categories")
        assert response.status_code == 200, f"Categories endpoint failed: {response.status_code}"
        print("PASS: Categories endpoint accessible")
    
    def test_document_types_endpoint(self):
        """Verify document types endpoint is accessible"""
        response = requests.get(f"{BASE_URL}/api/document-types")
        assert response.status_code == 200, f"Document types endpoint failed: {response.status_code}"
        print("PASS: Document types endpoint accessible")


class TestPreviousBugFixes:
    """Verify previous bug fixes still work"""
    
    def test_cors_configuration(self):
        """Verify CORS is properly configured (not wildcard)"""
        response = requests.options(
            f"{BASE_URL}/api/health",
            headers={
                'Origin': 'https://datascout-hub.preview.emergentagent.com',
                'Access-Control-Request-Method': 'GET'
            }
        )
        # CORS should allow the specific origin
        allow_origin = response.headers.get('access-control-allow-origin', '')
        assert allow_origin != '*', "CORS should not use wildcard"
        print(f"PASS: CORS origin: {allow_origin}")
    
    def test_create_category_endpoint(self):
        """Verify create category endpoint works"""
        response = requests.post(
            f"{BASE_URL}/api/categories",
            json={
                "name": "TEST_PWA_Category",
                "protocol": "(test or pwa) & (category)+",
                "is_public": True
            }
        )
        # Should return 200 or 201 for success
        assert response.status_code in [200, 201], f"Create category failed: {response.status_code}"
        print(f"PASS: Create category returned: {response.status_code}")
    
    def test_easter_eggs_endpoint(self):
        """Verify easter eggs endpoint is accessible"""
        response = requests.get(f"{BASE_URL}/api/easter-eggs")
        assert response.status_code == 200, f"Easter eggs endpoint failed: {response.status_code}"
        print("PASS: Easter eggs endpoint accessible")


class TestIndexHTML:
    """Test index.html for PWA meta tags"""
    
    def test_index_html_accessible(self):
        """Verify index.html is accessible"""
        response = requests.get(f"{BASE_URL}/")
        assert response.status_code == 200, f"Index page not accessible: {response.status_code}"
        print("PASS: Index page is accessible")
    
    def test_manifest_link_in_html(self):
        """Verify manifest link is in index.html"""
        response = requests.get(f"{BASE_URL}/")
        content = response.text
        assert 'manifest.json' in content, "manifest.json link not found in index.html"
        print("PASS: manifest.json link found in index.html")
    
    def test_apple_meta_tags_in_html(self):
        """Verify Apple PWA meta tags are in index.html"""
        response = requests.get(f"{BASE_URL}/")
        content = response.text
        assert 'apple-mobile-web-app-capable' in content, "apple-mobile-web-app-capable meta tag not found"
        assert 'apple-touch-icon' in content, "apple-touch-icon link not found"
        print("PASS: Apple PWA meta tags found in index.html")
    
    def test_theme_color_meta_tag(self):
        """Verify theme-color meta tag is in index.html"""
        response = requests.get(f"{BASE_URL}/")
        content = response.text
        assert 'theme-color' in content, "theme-color meta tag not found"
        print("PASS: theme-color meta tag found in index.html")


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
