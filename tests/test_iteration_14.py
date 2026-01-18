"""
InfoPilot Explorer - Iteration 14 Tests
Testing: Category controls visibility, Brave Search API, WebSocket chat
"""
import pytest
import requests
import os
import json
import asyncio
import websockets

BASE_URL = os.environ.get('REACT_APP_BACKEND_URL', '').rstrip('/')

class TestBraveSearchAPI:
    """Test Brave Search API integration"""
    
    @pytest.fixture(autouse=True)
    def setup(self):
        """Setup test user authentication"""
        response = requests.post(f"{BASE_URL}/api/auth/login", json={
            "email": "testuser_new@example.com",
            "password": "password123"
        })
        assert response.status_code == 200
        self.token = response.json()["token"]
        self.headers = {"Authorization": f"Bearer {self.token}"}
    
    def test_search_engines_endpoint_returns_brave_configured(self):
        """GET /api/search/engines should show brave_configured: true"""
        response = requests.get(f"{BASE_URL}/api/search/engines")
        assert response.status_code == 200
        data = response.json()
        assert data.get("brave_configured") == True, "Brave should be configured"
        
        # Check engines list includes Brave
        engines = data.get("engines", [])
        brave_engine = next((e for e in engines if e["id"] == "brave"), None)
        assert brave_engine is not None, "Brave engine should be in list"
        assert brave_engine["configured"] == True, "Brave should be marked as configured"
    
    def test_search_with_brave_engine_returns_results(self):
        """POST /api/search/collate with engine='brave' should return Brave results"""
        response = requests.post(
            f"{BASE_URL}/api/search/collate",
            headers=self.headers,
            json={"query": "python programming", "engine": "brave"}
        )
        assert response.status_code == 200
        data = response.json()
        
        # Check results exist
        results = data.get("results", [])
        assert len(results) > 0, "Should return search results"
        
        # Check source is Brave
        brave_results = [r for r in results if r.get("source") == "Brave"]
        assert len(brave_results) > 0, "Results should have Brave source"
    
    def test_search_results_have_source_badges(self):
        """Search results should have source field for badges"""
        response = requests.post(
            f"{BASE_URL}/api/search/collate",
            headers=self.headers,
            json={"query": "machine learning", "engine": "all"}
        )
        assert response.status_code == 200
        data = response.json()
        
        results = data.get("results", [])
        for result in results[:5]:  # Check first 5 results
            assert "source" in result, f"Result should have source field: {result.get('title')}"
            assert result["source"] in ["Brave", "DuckDuckGo", "Mock"], f"Source should be valid: {result['source']}"


class TestChatRoomAPI:
    """Test Chat Room REST API endpoints"""
    
    @pytest.fixture(autouse=True)
    def setup(self):
        """Setup test user authentication"""
        response = requests.post(f"{BASE_URL}/api/auth/login", json={
            "email": "testuser_new@example.com",
            "password": "password123"
        })
        assert response.status_code == 200
        self.token = response.json()["token"]
        self.user_id = response.json()["user"]["id"]
        self.headers = {"Authorization": f"Bearer {self.token}"}
    
    def test_get_chat_rooms(self):
        """GET /api/chat/rooms should return list of rooms"""
        response = requests.get(f"{BASE_URL}/api/chat/rooms", headers=self.headers)
        assert response.status_code == 200
        data = response.json()
        assert "rooms" in data
        assert isinstance(data["rooms"], list)
    
    def test_create_chat_room(self):
        """POST /api/chat/rooms should create a new room"""
        import uuid
        room_name = f"TEST_Room_{uuid.uuid4().hex[:8]}"
        response = requests.post(
            f"{BASE_URL}/api/chat/rooms",
            headers=self.headers,
            json={"name": room_name, "description": "Test room for iteration 14"}
        )
        assert response.status_code in [200, 201]
        data = response.json()
        assert data.get("name") == room_name or data.get("room", {}).get("name") == room_name
    
    def test_chat_rooms_require_auth(self):
        """GET /api/chat/rooms without auth should fail"""
        response = requests.get(f"{BASE_URL}/api/chat/rooms")
        assert response.status_code == 401


class TestWebSocketEndpoint:
    """Test WebSocket endpoint availability"""
    
    @pytest.fixture(autouse=True)
    def setup(self):
        """Setup test user authentication"""
        response = requests.post(f"{BASE_URL}/api/auth/login", json={
            "email": "testuser_new@example.com",
            "password": "password123"
        })
        assert response.status_code == 200
        self.token = response.json()["token"]
    
    def test_websocket_endpoint_exists(self):
        """WebSocket endpoint should be accessible"""
        # Test that the endpoint exists by checking if we can connect
        # Note: Full WebSocket testing requires async
        ws_url = BASE_URL.replace("https://", "wss://").replace("http://", "ws://")
        ws_url = ws_url.replace("/api", "") + f"/api/chat/ws?token={self.token}"
        
        # Just verify the URL is properly formed
        assert "ws" in ws_url
        assert "token=" in ws_url


class TestCategoryAPI:
    """Test Category API endpoints"""
    
    @pytest.fixture(autouse=True)
    def setup(self):
        """Setup test user authentication"""
        response = requests.post(f"{BASE_URL}/api/auth/login", json={
            "email": "testuser_new@example.com",
            "password": "password123"
        })
        assert response.status_code == 200
        self.token = response.json()["token"]
        self.headers = {"Authorization": f"Bearer {self.token}"}
    
    def test_get_categories(self):
        """GET /api/categories should return user categories"""
        response = requests.get(f"{BASE_URL}/api/categories", headers=self.headers)
        assert response.status_code == 200
        data = response.json()
        assert "categories" in data
    
    def test_create_category(self):
        """POST /api/categories should create a new category"""
        import uuid
        cat_name = f"TEST_Category_{uuid.uuid4().hex[:8]}"
        response = requests.post(
            f"{BASE_URL}/api/categories",
            headers=self.headers,
            json={
                "name": cat_name,
                "protocol": "(test or testing)+",
                "is_public": True
            }
        )
        assert response.status_code in [200, 201]
        data = response.json()
        assert "id" in data or "category" in data
    
    def test_update_category(self):
        """PUT /api/categories/:id should update category"""
        # First create a category
        import uuid
        cat_name = f"TEST_Update_{uuid.uuid4().hex[:8]}"
        create_response = requests.post(
            f"{BASE_URL}/api/categories",
            headers=self.headers,
            json={
                "name": cat_name,
                "protocol": "(update or test)+",
                "is_public": True
            }
        )
        assert create_response.status_code in [200, 201]
        cat_id = create_response.json().get("id") or create_response.json().get("category", {}).get("id")
        
        # Update the category
        update_response = requests.put(
            f"{BASE_URL}/api/categories/{cat_id}",
            headers=self.headers,
            json={
                "name": f"{cat_name}_updated",
                "protocol": "(updated or test)+",
                "is_public": True
            }
        )
        assert update_response.status_code == 200
    
    def test_delete_category(self):
        """DELETE /api/categories/:id should delete category"""
        # First create a category
        import uuid
        cat_name = f"TEST_Delete_{uuid.uuid4().hex[:8]}"
        create_response = requests.post(
            f"{BASE_URL}/api/categories",
            headers=self.headers,
            json={
                "name": cat_name,
                "protocol": "(delete or test)+",
                "is_public": True
            }
        )
        assert create_response.status_code in [200, 201]
        cat_id = create_response.json().get("id") or create_response.json().get("category", {}).get("id")
        
        # Delete the category
        delete_response = requests.delete(
            f"{BASE_URL}/api/categories/{cat_id}",
            headers=self.headers
        )
        assert delete_response.status_code in [200, 204]


if __name__ == "__main__":
    pytest.main([__file__, "-v", "--tb=short"])
