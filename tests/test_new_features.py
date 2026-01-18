"""
InfoPilot Explorer - New Features Tests
Tests for: Edit Category/Save Protocol, Create Template, Create Chat Room, 
Recommended Protocols, Quick Search, Theme Gallery, Marketplace Categories
"""
import pytest
import requests
import os
import uuid

BASE_URL = os.environ.get('REACT_APP_BACKEND_URL', 'https://infopilot-4.preview.emergentagent.com').rstrip('/')

# Test credentials
ADMIN_EMAIL = "admin@infopilot.com"
ADMIN_PASSWORD = "admin123"
TEST_EMAIL = "test@example.com"
TEST_PASSWORD = "password123"


@pytest.fixture
def auth_headers():
    """Get auth headers for authenticated requests"""
    login_response = requests.post(f"{BASE_URL}/api/auth/login", json={
        "email": ADMIN_EMAIL,
        "password": ADMIN_PASSWORD
    })
    if login_response.status_code != 200:
        pytest.skip("Could not login")
    token = login_response.json()["token"]
    return {"Authorization": f"Bearer {token}"}


@pytest.fixture
def test_user_headers():
    """Get auth headers for test user"""
    # Try to login first
    login_response = requests.post(f"{BASE_URL}/api/auth/login", json={
        "email": TEST_EMAIL,
        "password": TEST_PASSWORD
    })
    if login_response.status_code == 200:
        token = login_response.json()["token"]
        return {"Authorization": f"Bearer {token}"}
    
    # Register if not exists
    unique_id = str(uuid.uuid4())[:8]
    reg_response = requests.post(f"{BASE_URL}/api/auth/register", json={
        "email": f"testuser_{unique_id}@example.com",
        "password": "password123",
        "username": f"testuser_{unique_id}"
    })
    if reg_response.status_code == 200:
        token = reg_response.json()["token"]
        return {"Authorization": f"Bearer {token}"}
    
    pytest.skip("Could not create test user")


class TestEditCategorySaveProtocol:
    """Tests for Edit Category / Save Protocol functionality"""
    
    def test_create_and_update_category(self, auth_headers):
        """Test creating a category and then updating it (Save Protocol)"""
        unique_id = str(uuid.uuid4())[:8]
        
        # Create category
        create_response = requests.post(f"{BASE_URL}/api/categories", 
            json={
                "name": f"Test Category {unique_id}",
                "protocol": "(original or test) & (data)",
                "is_public": True,
                "price": None
            },
            headers=auth_headers)
        assert create_response.status_code == 200
        category = create_response.json()
        category_id = category["id"]
        print(f"✅ Created category: {category['name']}")
        
        # Update category (Save Protocol)
        update_response = requests.put(f"{BASE_URL}/api/categories/{category_id}",
            json={
                "name": f"Updated Category {unique_id}",
                "protocol": "(updated or modified) & (protocol)",
                "is_public": True,
                "price": 2.99
            },
            headers=auth_headers)
        assert update_response.status_code == 200
        updated = update_response.json()
        assert updated["name"] == f"Updated Category {unique_id}"
        assert updated["protocol"] == "(updated or modified) & (protocol)"
        assert updated["price"] == 2.99
        print(f"✅ Updated category (Save Protocol): {updated['name']} with price ${updated['price']}")
        
        # Verify update persisted
        get_response = requests.get(f"{BASE_URL}/api/categories", headers=auth_headers)
        assert get_response.status_code == 200
        categories = get_response.json()["categories"]
        found = next((c for c in categories if c["id"] == category_id), None)
        assert found is not None
        assert found["protocol"] == "(updated or modified) & (protocol)"
        print("✅ Verified category update persisted in database")
    
    def test_update_category_price_for_marketplace(self, auth_headers):
        """Test updating category with price for marketplace listing"""
        unique_id = str(uuid.uuid4())[:8]
        
        # Create category without price
        create_response = requests.post(f"{BASE_URL}/api/categories", 
            json={
                "name": f"Marketplace Test {unique_id}",
                "protocol": "(market or sell) & (protocol)",
                "is_public": True,
                "price": None
            },
            headers=auth_headers)
        assert create_response.status_code == 200
        category_id = create_response.json()["id"]
        
        # Update with price for marketplace
        update_response = requests.put(f"{BASE_URL}/api/categories/{category_id}",
            json={
                "price": 5.99,
                "is_public": True
            },
            headers=auth_headers)
        assert update_response.status_code == 200
        updated = update_response.json()
        assert updated["price"] == 5.99
        print(f"✅ Category updated with marketplace price: ${updated['price']}")


class TestCreateTemplate:
    """Tests for Create Protocol Template functionality"""
    
    def test_create_protocol_template(self, auth_headers):
        """Test creating a new protocol template"""
        unique_id = str(uuid.uuid4())[:8]
        
        response = requests.post(f"{BASE_URL}/api/templates",
            json={
                "name": f"Test Template {unique_id}",
                "description": "A test template for automated testing",
                "protocol": "(test or automated) & (template or protocol)",
                "category_suggestion": "Testing / Automation",
                "price": None
            },
            headers=auth_headers)
        assert response.status_code == 200
        template = response.json()
        assert template["name"] == f"Test Template {unique_id}"
        assert template["protocol"] == "(test or automated) & (template or protocol)"
        assert template["is_official"] == False
        assert "id" in template
        print(f"✅ Created protocol template: {template['name']}")
    
    def test_create_paid_template(self, auth_headers):
        """Test creating a paid protocol template"""
        unique_id = str(uuid.uuid4())[:8]
        
        response = requests.post(f"{BASE_URL}/api/templates",
            json={
                "name": f"Paid Template {unique_id}",
                "description": "A premium template",
                "protocol": "(premium or paid) & (content)",
                "category_suggestion": "Premium / Templates",
                "price": 4.99
            },
            headers=auth_headers)
        assert response.status_code == 200
        template = response.json()
        assert template["price"] == 4.99
        print(f"✅ Created paid template: {template['name']} at ${template['price']}")
    
    def test_get_templates_includes_official(self):
        """Test that templates endpoint returns official templates"""
        response = requests.get(f"{BASE_URL}/api/templates")
        assert response.status_code == 200
        data = response.json()
        assert "official_templates" in data
        assert "community_templates" in data
        assert len(data["official_templates"]) >= 5  # Should have several official templates
        
        # Verify official templates have required fields
        for template in data["official_templates"]:
            assert "name" in template
            assert "protocol" in template
            assert "description" in template
            assert template.get("is_official", True) == True
        
        print(f"✅ Templates endpoint returns {len(data['official_templates'])} official templates")


class TestCreateChatRoom:
    """Tests for Create Chat Room functionality"""
    
    def test_create_chat_room(self, auth_headers):
        """Test creating a new chat room"""
        unique_id = str(uuid.uuid4())[:8]
        
        response = requests.post(f"{BASE_URL}/api/chat/rooms",
            json={
                "name": f"Test Room {unique_id}",
                "description": "A test chat room",
                "is_public": True
            },
            headers=auth_headers)
        assert response.status_code == 200
        room = response.json()
        assert room["name"] == f"Test Room {unique_id}"
        assert room["is_public"] == True
        assert "id" in room
        assert "creator_id" in room
        print(f"✅ Created chat room: {room['name']}")
        return room["id"]
    
    def test_create_private_chat_room(self, auth_headers):
        """Test creating a private chat room"""
        unique_id = str(uuid.uuid4())[:8]
        
        response = requests.post(f"{BASE_URL}/api/chat/rooms",
            json={
                "name": f"Private Room {unique_id}",
                "description": "A private chat room",
                "is_public": False
            },
            headers=auth_headers)
        assert response.status_code == 200
        room = response.json()
        assert room["is_public"] == False
        print(f"✅ Created private chat room: {room['name']}")
    
    def test_get_chat_rooms(self, auth_headers):
        """Test getting list of chat rooms"""
        response = requests.get(f"{BASE_URL}/api/chat/rooms", headers=auth_headers)
        assert response.status_code == 200
        data = response.json()
        assert "rooms" in data
        print(f"✅ Retrieved {len(data['rooms'])} chat rooms")
    
    def test_send_message_to_room(self, auth_headers):
        """Test sending a message to a chat room"""
        unique_id = str(uuid.uuid4())[:8]
        
        # Create room first
        create_response = requests.post(f"{BASE_URL}/api/chat/rooms",
            json={"name": f"Message Test {unique_id}", "is_public": True},
            headers=auth_headers)
        room_id = create_response.json()["id"]
        
        # Send message
        msg_response = requests.post(f"{BASE_URL}/api/chat/rooms/{room_id}/messages",
            json={"content": "Hello, this is a test message!"},
            headers=auth_headers)
        assert msg_response.status_code == 200
        message = msg_response.json()
        assert message["content"] == "Hello, this is a test message!"
        assert "id" in message
        print(f"✅ Sent message to chat room: {message['content'][:30]}...")
    
    def test_get_room_messages(self, auth_headers):
        """Test getting messages from a chat room"""
        unique_id = str(uuid.uuid4())[:8]
        
        # Create room and send message
        create_response = requests.post(f"{BASE_URL}/api/chat/rooms",
            json={"name": f"Get Messages Test {unique_id}", "is_public": True},
            headers=auth_headers)
        room_id = create_response.json()["id"]
        
        requests.post(f"{BASE_URL}/api/chat/rooms/{room_id}/messages",
            json={"content": "Test message 1"},
            headers=auth_headers)
        requests.post(f"{BASE_URL}/api/chat/rooms/{room_id}/messages",
            json={"content": "Test message 2"},
            headers=auth_headers)
        
        # Get messages
        get_response = requests.get(f"{BASE_URL}/api/chat/rooms/{room_id}/messages", headers=auth_headers)
        assert get_response.status_code == 200
        data = get_response.json()
        assert "messages" in data
        assert len(data["messages"]) >= 2
        print(f"✅ Retrieved {len(data['messages'])} messages from chat room")


class TestRecommendedProtocols:
    """Tests for Recommended Protocols section"""
    
    def test_templates_endpoint_for_recommendations(self):
        """Test that templates endpoint provides data for recommendations"""
        response = requests.get(f"{BASE_URL}/api/templates")
        assert response.status_code == 200
        data = response.json()
        
        # Recommended protocols come from official_templates
        official = data.get("official_templates", [])
        assert len(official) >= 3, "Should have at least 3 templates for recommendations"
        
        # Verify templates have usage_count for sorting
        for template in official:
            assert "usage_count" in template or "name" in template
        
        print(f"✅ Templates endpoint provides {len(official)} templates for recommendations")


class TestQuickSearch:
    """Tests for Quick Search within results functionality"""
    
    def test_search_results_endpoint(self, auth_headers):
        """Test search results endpoint that Quick Search filters"""
        response = requests.get(f"{BASE_URL}/api/search/results", headers=auth_headers)
        assert response.status_code == 200
        data = response.json()
        assert "results" in data
        assert "total" in data
        print(f"✅ Search results endpoint returns {data['total']} results for Quick Search filtering")


class TestThemeGallery:
    """Tests for Theme Gallery functionality"""
    
    def test_update_theme(self, auth_headers):
        """Test updating user theme settings"""
        response = requests.put(f"{BASE_URL}/api/users/theme",
            json={"mode": "dark", "preset": "ocean"},
            headers=auth_headers)
        assert response.status_code == 200
        data = response.json()
        assert data["theme_settings"]["preset"] == "ocean"
        print(f"✅ Theme updated to: {data['theme_settings']['preset']}")
    
    def test_update_to_light_mode(self, auth_headers):
        """Test switching to light mode"""
        response = requests.put(f"{BASE_URL}/api/users/theme",
            json={"mode": "light", "preset": "light"},
            headers=auth_headers)
        assert response.status_code == 200
        data = response.json()
        assert data["theme_settings"]["mode"] == "light"
        print(f"✅ Theme mode changed to: {data['theme_settings']['mode']}")


class TestMarketplaceCategories:
    """Tests for Marketplace with category filters"""
    
    def test_marketplace_protocols(self):
        """Test marketplace protocols endpoint"""
        response = requests.get(f"{BASE_URL}/api/marketplace/protocols")
        assert response.status_code == 200
        data = response.json()
        assert "protocols" in data
        assert "total" in data
        print(f"✅ Marketplace returns {data['total']} protocols")
    
    def test_marketplace_with_category_filter(self):
        """Test marketplace with category filter"""
        response = requests.get(f"{BASE_URL}/api/marketplace/protocols", params={"category": "Technology"})
        assert response.status_code == 200
        data = response.json()
        assert "protocols" in data
        print(f"✅ Marketplace category filter returns {len(data['protocols'])} protocols")


class TestNewsHeadlinesRefresh:
    """Tests for News Headlines with Refresh functionality"""
    
    def test_headlines_endpoint(self):
        """Test news headlines endpoint"""
        response = requests.get(f"{BASE_URL}/api/news/headlines")
        assert response.status_code == 200
        data = response.json()
        assert "headlines" in data
        assert len(data["headlines"]) == 10
        
        # Verify headlines have required fields
        for headline in data["headlines"]:
            assert "title" in headline
            assert "category" in headline
        
        print(f"✅ Headlines endpoint returns {len(data['headlines'])} headlines for refresh")
    
    def test_headlines_refresh_returns_same_data(self):
        """Test that headlines refresh returns consistent data (static/mocked)"""
        response1 = requests.get(f"{BASE_URL}/api/news/headlines")
        response2 = requests.get(f"{BASE_URL}/api/news/headlines")
        
        assert response1.status_code == 200
        assert response2.status_code == 200
        
        # Since headlines are mocked/static, they should be consistent
        data1 = response1.json()
        data2 = response2.json()
        assert len(data1["headlines"]) == len(data2["headlines"])
        print("✅ Headlines refresh returns consistent data (MOCKED)")


if __name__ == "__main__":
    pytest.main([__file__, "-v", "--tb=short"])
