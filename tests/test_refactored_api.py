"""
Test suite for InfoPilot Explorer POST-REFACTORING regression tests.
Tests all API endpoints after the modular architecture refactoring.
"""
import pytest
import requests
import os
import io

BASE_URL = os.environ.get('REACT_APP_BACKEND_URL', 'https://infojethub.preview.emergentagent.com').rstrip('/')

# Test credentials - using new test user
TEST_EMAIL = "testuser_new@example.com"
TEST_PASSWORD = "password123"
TEST_USERNAME = "testuser_new"


class TestHealthAndRoot:
    """Test basic health and root endpoints"""
    
    def test_root_endpoint(self):
        """Test GET / returns API info"""
        response = requests.get(f"{BASE_URL}/")
        assert response.status_code == 200
        data = response.json()
        assert data["name"] == "InfoPilot Explorer API"
        assert data["version"] == "3.0.0"
        assert data["status"] == "operational"
        print(f"Root endpoint: {data['name']} v{data['version']}")
    
    def test_health_endpoint(self):
        """Test GET /health returns healthy status"""
        response = requests.get(f"{BASE_URL}/health")
        assert response.status_code == 200
        data = response.json()
        assert data["status"] == "healthy"
        print(f"Health check: {data['status']}")


class TestAuth:
    """Authentication tests"""
    
    def test_login_success(self):
        """Test login with valid credentials"""
        response = requests.post(f"{BASE_URL}/api/auth/login", json={
            "email": TEST_EMAIL,
            "password": TEST_PASSWORD
        })
        
        assert response.status_code == 200
        data = response.json()
        assert "token" in data
        assert "user" in data
        assert data["user"]["email"] == TEST_EMAIL
        print(f"Login successful for {TEST_EMAIL}")
    
    def test_login_invalid_credentials(self):
        """Test login with invalid credentials"""
        response = requests.post(f"{BASE_URL}/api/auth/login", json={
            "email": "wrong@example.com",
            "password": "wrongpass"
        })
        assert response.status_code == 401
    
    def test_get_me(self):
        """Test GET /api/auth/me returns current user"""
        # Login first
        login_response = requests.post(f"{BASE_URL}/api/auth/login", json={
            "email": TEST_EMAIL,
            "password": TEST_PASSWORD
        })
        token = login_response.json()["token"]
        
        # Get current user
        response = requests.get(f"{BASE_URL}/api/auth/me", headers={"Authorization": f"Bearer {token}"})
        assert response.status_code == 200
        data = response.json()
        assert data["email"] == TEST_EMAIL
        print(f"Get me: {data['username']}")


class TestCategories:
    """Category CRUD tests"""
    
    @pytest.fixture(scope="class")
    def auth_token(self):
        """Get auth token"""
        response = requests.post(f"{BASE_URL}/api/auth/login", json={
            "email": TEST_EMAIL,
            "password": TEST_PASSWORD
        })
        if response.status_code == 200:
            return response.json()["token"]
        pytest.skip("Authentication failed")
    
    def test_create_category(self, auth_token):
        """Test POST /api/categories creates a new category"""
        headers = {"Authorization": f"Bearer {auth_token}"}
        
        category_data = {
            "name": "TEST_Tech News",
            "protocol": "(technology or tech) & (news or update)",
            "is_public": True,
            "price": None
        }
        
        response = requests.post(f"{BASE_URL}/api/categories", json=category_data, headers=headers)
        assert response.status_code == 200
        data = response.json()
        assert data["name"] == category_data["name"]
        assert data["protocol"] == category_data["protocol"]
        assert "id" in data
        print(f"Category created: {data['name']}")
    
    def test_get_categories(self, auth_token):
        """Test GET /api/categories returns user's categories"""
        headers = {"Authorization": f"Bearer {auth_token}"}
        response = requests.get(f"{BASE_URL}/api/categories", headers=headers)
        assert response.status_code == 200
        data = response.json()
        assert "categories" in data
        print(f"Found {len(data['categories'])} categories")
    
    def test_update_category(self, auth_token):
        """Test PUT /api/categories/{id} updates a category"""
        headers = {"Authorization": f"Bearer {auth_token}"}
        
        # Create a category first
        create_response = requests.post(f"{BASE_URL}/api/categories", json={
            "name": "TEST_Update Category",
            "protocol": "(test) & (update)",
            "is_public": True
        }, headers=headers)
        
        assert create_response.status_code == 200
        category_id = create_response.json()["id"]
        
        # Update it
        update_response = requests.put(f"{BASE_URL}/api/categories/{category_id}", json={
            "name": "TEST_Updated Category Name"
        }, headers=headers)
        
        assert update_response.status_code == 200
        assert update_response.json()["name"] == "TEST_Updated Category Name"
        print(f"Category updated: {category_id}")
    
    def test_delete_category(self, auth_token):
        """Test DELETE /api/categories/{id} deletes a category"""
        headers = {"Authorization": f"Bearer {auth_token}"}
        
        # Create a category first
        create_response = requests.post(f"{BASE_URL}/api/categories", json={
            "name": "TEST_Delete Category",
            "protocol": "(test) & (delete)",
            "is_public": True
        }, headers=headers)
        
        assert create_response.status_code == 200
        category_id = create_response.json()["id"]
        
        # Delete it
        delete_response = requests.delete(f"{BASE_URL}/api/categories/{category_id}", headers=headers)
        assert delete_response.status_code == 200
        print(f"Category deleted: {category_id}")


class TestDuckDuckGoSearch:
    """Test DuckDuckGo search integration"""
    
    @pytest.fixture(scope="class")
    def auth_token(self):
        """Get auth token"""
        response = requests.post(f"{BASE_URL}/api/auth/login", json={
            "email": TEST_EMAIL,
            "password": TEST_PASSWORD
        })
        if response.status_code == 200:
            return response.json()["token"]
        pytest.skip("Authentication failed")
    
    def test_search_collate_returns_results(self, auth_token):
        """Test POST /api/search/collate returns real search results"""
        headers = {"Authorization": f"Bearer {auth_token}"}
        response = requests.post(
            f"{BASE_URL}/api/search/collate",
            json={"query": "Python programming"},
            headers=headers
        )
        
        assert response.status_code == 200
        data = response.json()
        
        assert "results" in data
        assert "total_searched" in data
        assert "message" in data
        assert len(data["results"]) > 0
        
        first_result = data["results"][0]
        assert "url" in first_result
        assert "title" in first_result
        assert "snippet" in first_result
        
        print(f"Search returned {len(data['results'])} results")
    
    def test_get_search_results(self, auth_token):
        """Test GET /api/search/results returns stored results"""
        headers = {"Authorization": f"Bearer {auth_token}"}
        response = requests.get(f"{BASE_URL}/api/search/results", headers=headers)
        
        assert response.status_code == 200
        data = response.json()
        assert "results" in data
        assert "total" in data
        print(f"Found {data['total']} stored results")


class TestGroups:
    """Test Groups feature"""
    
    @pytest.fixture(scope="class")
    def auth_token(self):
        """Get auth token"""
        response = requests.post(f"{BASE_URL}/api/auth/login", json={
            "email": TEST_EMAIL,
            "password": TEST_PASSWORD
        })
        if response.status_code == 200:
            return response.json()["token"]
        pytest.skip("Authentication failed")
    
    def test_create_group(self, auth_token):
        """Test POST /api/groups creates a new group"""
        headers = {"Authorization": f"Bearer {auth_token}"}
        
        group_data = {
            "name": "TEST_Python Developers",
            "description": "A group for Python enthusiasts",
            "is_public": True
        }
        
        response = requests.post(f"{BASE_URL}/api/groups", json=group_data, headers=headers)
        assert response.status_code == 200
        data = response.json()
        
        assert "id" in data
        assert data["name"] == group_data["name"]
        assert "members" in data
        print(f"Group created: {data['name']}")
    
    def test_get_groups(self, auth_token):
        """Test GET /api/groups returns list of groups"""
        headers = {"Authorization": f"Bearer {auth_token}"}
        response = requests.get(f"{BASE_URL}/api/groups", headers=headers)
        
        assert response.status_code == 200
        data = response.json()
        assert "groups" in data
        print(f"Found {len(data['groups'])} groups")
    
    def test_join_and_leave_group(self, auth_token):
        """Test POST /api/groups/{id}/join and /leave"""
        headers = {"Authorization": f"Bearer {auth_token}"}
        
        # Create a group
        create_response = requests.post(f"{BASE_URL}/api/groups", json={
            "name": "TEST_Join Leave Group",
            "description": "Group for testing join/leave",
            "is_public": True
        }, headers=headers)
        
        assert create_response.status_code == 200
        group_id = create_response.json()["id"]
        
        # Join the group
        join_response = requests.post(f"{BASE_URL}/api/groups/{group_id}/join", headers=headers)
        assert join_response.status_code == 200
        
        # Leave the group
        leave_response = requests.post(f"{BASE_URL}/api/groups/{group_id}/leave", headers=headers)
        assert leave_response.status_code == 200
        print(f"Join/Leave group: {group_id}")


class TestPages:
    """Test Pages feature"""
    
    @pytest.fixture(scope="class")
    def auth_token(self):
        """Get auth token"""
        response = requests.post(f"{BASE_URL}/api/auth/login", json={
            "email": TEST_EMAIL,
            "password": TEST_PASSWORD
        })
        if response.status_code == 200:
            return response.json()["token"]
        pytest.skip("Authentication failed")
    
    def test_create_page(self, auth_token):
        """Test POST /api/pages creates a new page"""
        headers = {"Authorization": f"Bearer {auth_token}"}
        
        page_data = {
            "name": "TEST_Tech News Page",
            "description": "Latest technology news",
            "category": "Technology"
        }
        
        response = requests.post(f"{BASE_URL}/api/pages", json=page_data, headers=headers)
        assert response.status_code == 200
        data = response.json()
        
        assert "id" in data
        assert data["name"] == page_data["name"]
        assert "followers" in data
        print(f"Page created: {data['name']}")
    
    def test_get_pages(self):
        """Test GET /api/pages returns list of pages"""
        response = requests.get(f"{BASE_URL}/api/pages")
        
        assert response.status_code == 200
        data = response.json()
        assert "pages" in data
        print(f"Found {len(data['pages'])} pages")
    
    def test_follow_page(self, auth_token):
        """Test POST /api/pages/{id}/follow"""
        headers = {"Authorization": f"Bearer {auth_token}"}
        
        # Create a page
        create_response = requests.post(f"{BASE_URL}/api/pages", json={
            "name": "TEST_Follow Page",
            "description": "Page for testing follow",
            "category": "Testing"
        }, headers=headers)
        
        assert create_response.status_code == 200
        page_id = create_response.json()["id"]
        
        # Follow the page
        follow_response = requests.post(f"{BASE_URL}/api/pages/{page_id}/follow", headers=headers)
        assert follow_response.status_code == 200
        print(f"Followed page: {page_id}")


class TestReports:
    """Test Personal Reports feature"""
    
    @pytest.fixture(scope="class")
    def auth_token(self):
        """Get auth token"""
        response = requests.post(f"{BASE_URL}/api/auth/login", json={
            "email": TEST_EMAIL,
            "password": TEST_PASSWORD
        })
        if response.status_code == 200:
            return response.json()["token"]
        pytest.skip("Authentication failed")
    
    def test_create_report(self, auth_token):
        """Test POST /api/reports creates a personal report"""
        headers = {"Authorization": f"Bearer {auth_token}"}
        
        report_data = {
            "title": "TEST_My Test Report",
            "content": "This is a test personal report.",
            "images": [],
            "category_ids": []
        }
        
        response = requests.post(f"{BASE_URL}/api/reports", json=report_data, headers=headers)
        assert response.status_code == 200
        data = response.json()
        
        assert "id" in data
        assert data["title"] == report_data["title"]
        print(f"Report created: {data['title']}")
    
    def test_get_reports(self, auth_token):
        """Test GET /api/reports returns user's reports"""
        headers = {"Authorization": f"Bearer {auth_token}"}
        response = requests.get(f"{BASE_URL}/api/reports", headers=headers)
        
        assert response.status_code == 200
        data = response.json()
        assert "reports" in data
        print(f"Found {len(data['reports'])} reports")
    
    def test_create_report_max_images(self, auth_token):
        """Test that reports are limited to 3 images"""
        headers = {"Authorization": f"Bearer {auth_token}"}
        
        report_data = {
            "title": "TEST_Too Many Images",
            "content": "This report has too many images",
            "images": ["/api/uploads/1.png", "/api/uploads/2.png", "/api/uploads/3.png", "/api/uploads/4.png"],
            "category_ids": []
        }
        
        response = requests.post(f"{BASE_URL}/api/reports", json=report_data, headers=headers)
        assert response.status_code == 400
        assert "Maximum 3 images" in response.json().get("detail", "")


class TestImageUpload:
    """Test image upload functionality"""
    
    @pytest.fixture(scope="class")
    def auth_token(self):
        """Get auth token"""
        response = requests.post(f"{BASE_URL}/api/auth/login", json={
            "email": TEST_EMAIL,
            "password": TEST_PASSWORD
        })
        if response.status_code == 200:
            return response.json()["token"]
        pytest.skip("Authentication failed")
    
    def test_upload_image(self, auth_token):
        """Test POST /api/reports/upload/image"""
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
        response = requests.post(f"{BASE_URL}/api/reports/upload/image", files=files, headers=headers)
        
        assert response.status_code == 200
        data = response.json()
        assert "url" in data
        assert "filename" in data
        print(f"Image uploaded: {data['url']}")


class TestRevenueDashboard:
    """Test Revenue Dashboard and exports"""
    
    @pytest.fixture(scope="class")
    def auth_token(self):
        """Get auth token"""
        response = requests.post(f"{BASE_URL}/api/auth/login", json={
            "email": TEST_EMAIL,
            "password": TEST_PASSWORD
        })
        if response.status_code == 200:
            return response.json()["token"]
        pytest.skip("Authentication failed")
    
    def test_get_revenue_dashboard(self, auth_token):
        """Test GET /api/revenue/dashboard returns dashboard data"""
        headers = {"Authorization": f"Bearer {auth_token}"}
        response = requests.get(f"{BASE_URL}/api/revenue/dashboard", headers=headers)
        
        assert response.status_code == 200
        data = response.json()
        
        assert "total_revenue" in data
        assert "total_sales" in data
        assert "monthly_revenue" in data
        assert "top_protocols" in data
        print(f"Revenue Dashboard: ${data['total_revenue']:.2f} total, {data['total_sales']} sales")
    
    def test_export_revenue_pdf(self, auth_token):
        """Test GET /api/revenue/export?format=pdf returns PDF"""
        headers = {"Authorization": f"Bearer {auth_token}"}
        response = requests.get(f"{BASE_URL}/api/revenue/export?format=pdf", headers=headers)
        
        assert response.status_code == 200
        assert "application/pdf" in response.headers.get("content-type", "")
        assert response.content[:4] == b'%PDF'
        print(f"PDF export successful, size: {len(response.content)} bytes")
    
    def test_export_revenue_csv(self, auth_token):
        """Test GET /api/revenue/export?format=csv returns CSV"""
        headers = {"Authorization": f"Bearer {auth_token}"}
        response = requests.get(f"{BASE_URL}/api/revenue/export?format=csv", headers=headers)
        
        assert response.status_code == 200
        assert "text/csv" in response.headers.get("content-type", "")
        assert "Date,Protocol,Price" in response.text
        print(f"CSV export successful, size: {len(response.text)} bytes")


class TestChat:
    """Test Chat rooms feature"""
    
    @pytest.fixture(scope="class")
    def auth_token(self):
        """Get auth token"""
        response = requests.post(f"{BASE_URL}/api/auth/login", json={
            "email": TEST_EMAIL,
            "password": TEST_PASSWORD
        })
        if response.status_code == 200:
            return response.json()["token"]
        pytest.skip("Authentication failed")
    
    def test_create_chat_room(self, auth_token):
        """Test POST /api/chat/rooms creates a chat room"""
        headers = {"Authorization": f"Bearer {auth_token}"}
        
        room_data = {
            "name": "TEST_General Chat",
            "description": "General discussion room",
            "is_public": True
        }
        
        response = requests.post(f"{BASE_URL}/api/chat/rooms", json=room_data, headers=headers)
        assert response.status_code == 200
        data = response.json()
        
        assert "id" in data
        assert data["name"] == room_data["name"]
        print(f"Chat room created: {data['name']}")
    
    def test_get_chat_rooms(self, auth_token):
        """Test GET /api/chat/rooms returns list of rooms"""
        headers = {"Authorization": f"Bearer {auth_token}"}
        response = requests.get(f"{BASE_URL}/api/chat/rooms", headers=headers)
        
        assert response.status_code == 200
        data = response.json()
        assert "rooms" in data
        print(f"Found {len(data['rooms'])} chat rooms")


class TestTemplates:
    """Test Protocol Templates feature"""
    
    @pytest.fixture(scope="class")
    def auth_token(self):
        """Get auth token"""
        response = requests.post(f"{BASE_URL}/api/auth/login", json={
            "email": TEST_EMAIL,
            "password": TEST_PASSWORD
        })
        if response.status_code == 200:
            return response.json()["token"]
        pytest.skip("Authentication failed")
    
    def test_get_templates(self):
        """Test GET /api/templates returns templates"""
        response = requests.get(f"{BASE_URL}/api/templates")
        
        assert response.status_code == 200
        data = response.json()
        
        assert "official_templates" in data
        assert "community_templates" in data
        assert len(data["official_templates"]) > 0
        print(f"Found {len(data['official_templates'])} official templates")
    
    def test_create_template(self, auth_token):
        """Test POST /api/templates creates a template"""
        headers = {"Authorization": f"Bearer {auth_token}"}
        
        template_data = {
            "name": "TEST_Custom Template",
            "description": "A custom search template",
            "protocol": "(test) & (template)",
            "category_suggestion": "Testing"
        }
        
        response = requests.post(f"{BASE_URL}/api/templates", json=template_data, headers=headers)
        assert response.status_code == 200
        data = response.json()
        
        assert "id" in data
        assert data["name"] == template_data["name"]
        print(f"Template created: {data['name']}")


class TestMarketplace:
    """Test Marketplace feature"""
    
    def test_get_marketplace_protocols(self):
        """Test GET /api/marketplace/protocols returns protocols"""
        response = requests.get(f"{BASE_URL}/api/marketplace/protocols")
        
        assert response.status_code == 200
        data = response.json()
        
        assert "protocols" in data
        assert "total" in data
        print(f"Found {data['total']} marketplace protocols")


if __name__ == "__main__":
    pytest.main([__file__, "-v", "--tb=short"])
