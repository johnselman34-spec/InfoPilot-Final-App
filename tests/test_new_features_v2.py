"""
Test suite for InfoPilot Explorer new features:
1. DuckDuckGo search integration
2. Image upload for Personal Reports
3. Groups feature (create, join, leave)
4. Pages feature (create, follow)
5. Revenue Dashboard PDF export
"""
import pytest
import requests
import os
import io

BASE_URL = os.environ.get('REACT_APP_BACKEND_URL', 'https://infojethub.preview.emergentagent.com').rstrip('/')

# Test credentials
TEST_EMAIL = "test@example.com"
TEST_PASSWORD = "password123"
TEST_USERNAME = "testuser_v2"


class TestAuth:
    """Authentication tests"""
    
    @pytest.fixture(scope="class")
    def auth_token(self):
        """Get or create test user and return auth token"""
        # Try login first
        response = requests.post(f"{BASE_URL}/api/auth/login", json={
            "email": TEST_EMAIL,
            "password": TEST_PASSWORD
        })
        
        if response.status_code == 200:
            return response.json()["token"]
        
        # If login fails, register new user
        response = requests.post(f"{BASE_URL}/api/auth/register", json={
            "email": TEST_EMAIL,
            "password": TEST_PASSWORD,
            "username": TEST_USERNAME
        })
        
        if response.status_code == 200:
            return response.json()["token"]
        
        pytest.skip(f"Could not authenticate: {response.text}")
    
    def test_login_success(self):
        """Test login with valid credentials"""
        response = requests.post(f"{BASE_URL}/api/auth/login", json={
            "email": TEST_EMAIL,
            "password": TEST_PASSWORD
        })
        
        # If user doesn't exist, register first
        if response.status_code == 401:
            reg_response = requests.post(f"{BASE_URL}/api/auth/register", json={
                "email": TEST_EMAIL,
                "password": TEST_PASSWORD,
                "username": TEST_USERNAME
            })
            if reg_response.status_code == 200:
                response = requests.post(f"{BASE_URL}/api/auth/login", json={
                    "email": TEST_EMAIL,
                    "password": TEST_PASSWORD
                })
        
        assert response.status_code == 200
        data = response.json()
        assert "token" in data
        assert "user" in data


class TestDuckDuckGoSearch:
    """Test DuckDuckGo search integration"""
    
    @pytest.fixture(scope="class")
    def auth_token(self):
        """Get auth token for search tests"""
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
        
        # Verify response structure
        assert "results" in data
        assert "total_searched" in data
        assert "message" in data
        
        # Should have results (either real or mock fallback)
        assert len(data["results"]) > 0
        
        # Verify result structure
        first_result = data["results"][0]
        assert "url" in first_result
        assert "title" in first_result
        assert "snippet" in first_result
        
        print(f"Search returned {len(data['results'])} results")
        print(f"First result: {first_result['title'][:50]}...")
    
    def test_search_collate_with_different_query(self, auth_token):
        """Test search with different query"""
        headers = {"Authorization": f"Bearer {auth_token}"}
        response = requests.post(
            f"{BASE_URL}/api/search/collate",
            json={"query": "climate change news"},
            headers=headers
        )
        
        assert response.status_code == 200
        data = response.json()
        assert len(data["results"]) > 0


class TestImageUpload:
    """Test image upload for Personal Reports"""
    
    @pytest.fixture(scope="class")
    def auth_token(self):
        """Get auth token for upload tests"""
        response = requests.post(f"{BASE_URL}/api/auth/login", json={
            "email": TEST_EMAIL,
            "password": TEST_PASSWORD
        })
        if response.status_code == 200:
            return response.json()["token"]
        pytest.skip("Authentication failed")
    
    def test_upload_image_success(self, auth_token):
        """Test POST /api/upload/image with valid image"""
        headers = {"Authorization": f"Bearer {auth_token}"}
        
        # Create a simple test image (1x1 pixel PNG)
        png_data = bytes([
            0x89, 0x50, 0x4E, 0x47, 0x0D, 0x0A, 0x1A, 0x0A,  # PNG signature
            0x00, 0x00, 0x00, 0x0D, 0x49, 0x48, 0x44, 0x52,  # IHDR chunk
            0x00, 0x00, 0x00, 0x01, 0x00, 0x00, 0x00, 0x01,  # 1x1 dimensions
            0x08, 0x02, 0x00, 0x00, 0x00, 0x90, 0x77, 0x53,
            0xDE, 0x00, 0x00, 0x00, 0x0C, 0x49, 0x44, 0x41,  # IDAT chunk
            0x54, 0x08, 0xD7, 0x63, 0xF8, 0xFF, 0xFF, 0x3F,
            0x00, 0x05, 0xFE, 0x02, 0xFE, 0xDC, 0xCC, 0x59,
            0xE7, 0x00, 0x00, 0x00, 0x00, 0x49, 0x45, 0x4E,  # IEND chunk
            0x44, 0xAE, 0x42, 0x60, 0x82
        ])
        
        files = {"file": ("test_image.png", io.BytesIO(png_data), "image/png")}
        response = requests.post(
            f"{BASE_URL}/api/upload/image",
            files=files,
            headers=headers
        )
        
        assert response.status_code == 200
        data = response.json()
        
        # Verify response structure
        assert "url" in data
        assert "filename" in data
        assert "size" in data
        
        # URL should be in correct format
        assert data["url"].startswith("/api/uploads/")
        
        print(f"Image uploaded: {data['url']}")
        return data["url"]
    
    def test_upload_image_invalid_type(self, auth_token):
        """Test upload with invalid file type"""
        headers = {"Authorization": f"Bearer {auth_token}"}
        
        # Create a text file
        files = {"file": ("test.txt", io.BytesIO(b"This is not an image"), "text/plain")}
        response = requests.post(
            f"{BASE_URL}/api/upload/image",
            files=files,
            headers=headers
        )
        
        assert response.status_code == 400
        assert "Invalid file type" in response.json().get("detail", "")
    
    def test_get_uploaded_image(self, auth_token):
        """Test GET /api/uploads/{filename} retrieves uploaded image"""
        headers = {"Authorization": f"Bearer {auth_token}"}
        
        # First upload an image
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
        
        files = {"file": ("test_retrieve.png", io.BytesIO(png_data), "image/png")}
        upload_response = requests.post(
            f"{BASE_URL}/api/upload/image",
            files=files,
            headers=headers
        )
        
        assert upload_response.status_code == 200
        filename = upload_response.json()["filename"]
        
        # Now retrieve the image
        get_response = requests.get(f"{BASE_URL}/api/uploads/{filename}")
        
        assert get_response.status_code == 200
        assert get_response.headers.get("content-type", "").startswith("image/")
    
    def test_get_nonexistent_image(self):
        """Test GET /api/uploads/{filename} with non-existent file"""
        response = requests.get(f"{BASE_URL}/api/uploads/nonexistent_file_12345.png")
        assert response.status_code == 404


class TestGroups:
    """Test Groups feature"""
    
    @pytest.fixture(scope="class")
    def auth_token(self):
        """Get auth token for groups tests"""
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
        
        response = requests.post(
            f"{BASE_URL}/api/groups",
            json=group_data,
            headers=headers
        )
        
        assert response.status_code == 200
        data = response.json()
        
        # Verify response structure
        assert "id" in data
        assert data["name"] == group_data["name"]
        assert data["description"] == group_data["description"]
        assert data["is_public"] == True
        assert "members" in data
        assert "creator_id" in data
        
        print(f"Group created: {data['name']} (ID: {data['id']})")
        return data["id"]
    
    def test_get_groups(self, auth_token):
        """Test GET /api/groups returns list of groups"""
        headers = {"Authorization": f"Bearer {auth_token}"}
        
        response = requests.get(f"{BASE_URL}/api/groups", headers=headers)
        
        assert response.status_code == 200
        data = response.json()
        
        assert "groups" in data
        assert isinstance(data["groups"], list)
        
        print(f"Found {len(data['groups'])} groups")
    
    def test_join_group(self, auth_token):
        """Test POST /api/groups/{id}/join"""
        headers = {"Authorization": f"Bearer {auth_token}"}
        
        # First create a group
        group_data = {
            "name": "TEST_Join Test Group",
            "description": "Group for testing join",
            "is_public": True
        }
        create_response = requests.post(
            f"{BASE_URL}/api/groups",
            json=group_data,
            headers=headers
        )
        
        assert create_response.status_code == 200
        group_id = create_response.json()["id"]
        
        # Join the group
        join_response = requests.post(
            f"{BASE_URL}/api/groups/{group_id}/join",
            headers=headers
        )
        
        assert join_response.status_code == 200
        assert "message" in join_response.json()
    
    def test_leave_group(self, auth_token):
        """Test POST /api/groups/{id}/leave"""
        headers = {"Authorization": f"Bearer {auth_token}"}
        
        # First create a group
        group_data = {
            "name": "TEST_Leave Test Group",
            "description": "Group for testing leave",
            "is_public": True
        }
        create_response = requests.post(
            f"{BASE_URL}/api/groups",
            json=group_data,
            headers=headers
        )
        
        assert create_response.status_code == 200
        group_id = create_response.json()["id"]
        
        # Leave the group
        leave_response = requests.post(
            f"{BASE_URL}/api/groups/{group_id}/leave",
            headers=headers
        )
        
        assert leave_response.status_code == 200
        assert "message" in leave_response.json()
    
    def test_join_nonexistent_group(self, auth_token):
        """Test joining a non-existent group"""
        headers = {"Authorization": f"Bearer {auth_token}"}
        
        response = requests.post(
            f"{BASE_URL}/api/groups/nonexistent_group_id/join",
            headers=headers
        )
        
        assert response.status_code == 404


class TestPages:
    """Test Pages feature"""
    
    @pytest.fixture(scope="class")
    def auth_token(self):
        """Get auth token for pages tests"""
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
            "description": "Latest technology news and updates",
            "category": "Technology"
        }
        
        response = requests.post(
            f"{BASE_URL}/api/pages",
            json=page_data,
            headers=headers
        )
        
        assert response.status_code == 200
        data = response.json()
        
        # Verify response structure
        assert "id" in data
        assert data["name"] == page_data["name"]
        assert data["description"] == page_data["description"]
        assert data["category"] == page_data["category"]
        assert "followers" in data
        assert "owner_id" in data
        
        print(f"Page created: {data['name']} (ID: {data['id']})")
        return data["id"]
    
    def test_get_pages(self):
        """Test GET /api/pages returns list of pages"""
        response = requests.get(f"{BASE_URL}/api/pages")
        
        assert response.status_code == 200
        data = response.json()
        
        assert "pages" in data
        assert isinstance(data["pages"], list)
        
        print(f"Found {len(data['pages'])} pages")
    
    def test_follow_page(self, auth_token):
        """Test POST /api/pages/{id}/follow"""
        headers = {"Authorization": f"Bearer {auth_token}"}
        
        # First create a page
        page_data = {
            "name": "TEST_Follow Test Page",
            "description": "Page for testing follow",
            "category": "Testing"
        }
        create_response = requests.post(
            f"{BASE_URL}/api/pages",
            json=page_data,
            headers=headers
        )
        
        assert create_response.status_code == 200
        page_id = create_response.json()["id"]
        
        # Follow the page
        follow_response = requests.post(
            f"{BASE_URL}/api/pages/{page_id}/follow",
            headers=headers
        )
        
        assert follow_response.status_code == 200
        assert "message" in follow_response.json()
    
    def test_follow_nonexistent_page(self, auth_token):
        """Test following a non-existent page"""
        headers = {"Authorization": f"Bearer {auth_token}"}
        
        response = requests.post(
            f"{BASE_URL}/api/pages/nonexistent_page_id/follow",
            headers=headers
        )
        
        assert response.status_code == 404


class TestRevenueDashboard:
    """Test Revenue Dashboard and PDF export"""
    
    @pytest.fixture(scope="class")
    def auth_token(self):
        """Get auth token for revenue tests"""
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
        
        # Verify response structure
        assert "total_revenue" in data
        assert "total_sales" in data
        assert "monthly_revenue" in data
        assert "top_protocols" in data
        assert "wallet_balance" in data
        
        # Verify data types
        assert isinstance(data["total_revenue"], (int, float))
        assert isinstance(data["total_sales"], int)
        assert isinstance(data["monthly_revenue"], dict)
        assert isinstance(data["top_protocols"], list)
        
        print(f"Revenue Dashboard: ${data['total_revenue']:.2f} total, {data['total_sales']} sales")
    
    def test_export_revenue_pdf(self, auth_token):
        """Test GET /api/revenue/export?format=pdf returns PDF file"""
        headers = {"Authorization": f"Bearer {auth_token}"}
        
        response = requests.get(
            f"{BASE_URL}/api/revenue/export?format=pdf",
            headers=headers
        )
        
        assert response.status_code == 200
        
        # Verify it's a PDF
        content_type = response.headers.get("content-type", "")
        assert "application/pdf" in content_type
        
        # Verify PDF header
        assert response.content[:4] == b'%PDF'
        
        print(f"PDF export successful, size: {len(response.content)} bytes")
    
    def test_export_revenue_csv(self, auth_token):
        """Test GET /api/revenue/export?format=csv returns CSV file"""
        headers = {"Authorization": f"Bearer {auth_token}"}
        
        response = requests.get(
            f"{BASE_URL}/api/revenue/export?format=csv",
            headers=headers
        )
        
        assert response.status_code == 200
        
        # Verify it's a CSV
        content_type = response.headers.get("content-type", "")
        assert "text/csv" in content_type
        
        # Verify CSV content
        content = response.text
        assert "Date,Protocol,Price" in content
        
        print(f"CSV export successful, size: {len(content)} bytes")


class TestPersonalReports:
    """Test Personal Reports with image upload"""
    
    @pytest.fixture(scope="class")
    def auth_token(self):
        """Get auth token for reports tests"""
        response = requests.post(f"{BASE_URL}/api/auth/login", json={
            "email": TEST_EMAIL,
            "password": TEST_PASSWORD
        })
        if response.status_code == 200:
            return response.json()["token"]
        pytest.skip("Authentication failed")
    
    def test_create_report_with_images(self, auth_token):
        """Test creating a personal report with images"""
        headers = {"Authorization": f"Bearer {auth_token}"}
        
        # First upload an image
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
        
        files = {"file": ("report_image.png", io.BytesIO(png_data), "image/png")}
        upload_response = requests.post(
            f"{BASE_URL}/api/upload/image",
            files=files,
            headers=headers
        )
        
        assert upload_response.status_code == 200
        image_url = upload_response.json()["url"]
        
        # Create report with the uploaded image
        report_data = {
            "title": "TEST_My Test Report",
            "content": "This is a test personal report with an image attached.",
            "images": [image_url],
            "location": {"lat": 40.7128, "lng": -74.0060},
            "category_ids": []
        }
        
        response = requests.post(
            f"{BASE_URL}/api/reports",
            json=report_data,
            headers=headers
        )
        
        assert response.status_code == 200
        data = response.json()
        
        # Verify response structure
        assert "id" in data
        assert data["title"] == report_data["title"]
        assert data["content"] == report_data["content"]
        assert len(data["images"]) == 1
        assert data["images"][0] == image_url
        
        print(f"Report created with image: {data['title']}")
    
    def test_get_reports(self, auth_token):
        """Test GET /api/reports returns user's reports"""
        headers = {"Authorization": f"Bearer {auth_token}"}
        
        response = requests.get(f"{BASE_URL}/api/reports", headers=headers)
        
        assert response.status_code == 200
        data = response.json()
        
        assert "reports" in data
        assert isinstance(data["reports"], list)
        
        print(f"Found {len(data['reports'])} reports")
    
    def test_create_report_max_images(self, auth_token):
        """Test that reports are limited to 3 images"""
        headers = {"Authorization": f"Bearer {auth_token}"}
        
        report_data = {
            "title": "TEST_Too Many Images Report",
            "content": "This report has too many images",
            "images": ["/api/uploads/1.png", "/api/uploads/2.png", "/api/uploads/3.png", "/api/uploads/4.png"],
            "category_ids": []
        }
        
        response = requests.post(
            f"{BASE_URL}/api/reports",
            json=report_data,
            headers=headers
        )
        
        assert response.status_code == 400
        assert "Maximum 3 images" in response.json().get("detail", "")


if __name__ == "__main__":
    pytest.main([__file__, "-v", "--tb=short"])
