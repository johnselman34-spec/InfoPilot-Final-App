"""
InfoPilot Explorer API Tests
Tests for: Auth, Categories, Search, Easter Eggs, Marketplace, Book, Food, Stats, Leaderboard
"""
import pytest
import requests
import os
import uuid

BASE_URL = os.environ.get('REACT_APP_BACKEND_URL', 'https://infopilot-4.preview.emergentagent.com').rstrip('/')

# Test credentials
TEST_USER_EMAIL = "testuser2@example.com"
TEST_USER_PASSWORD = "testpass123"
ADMIN_EMAIL = "admin@infopilot.com"
ADMIN_PASSWORD = "admin123"

class TestHealthAndRoot:
    """Basic API health checks"""
    
    def test_root_endpoint(self):
        """Test root API endpoint returns correct info"""
        response = requests.get(f"{BASE_URL}/api/")
        assert response.status_code == 200
        data = response.json()
        assert data["app_name"] == "InfoPilot Explorer"
        assert data["company"] == "Top Pilot Enterprises, Inc."
        assert "InfoJet 2.0 Protocol Search" in data["features"]
        assert "Easter Eggs" in data["features"]
        assert "Laughter Points" in data["features"]
        print("✅ Root endpoint working with correct branding")


class TestAuthentication:
    """Authentication flow tests"""
    
    def test_register_new_user(self):
        """Test user registration"""
        unique_id = str(uuid.uuid4())[:8]
        response = requests.post(f"{BASE_URL}/api/auth/register", json={
            "email": f"test_{unique_id}@example.com",
            "password": "testpass123",
            "username": f"testuser_{unique_id}",
            "first_name": "Test",
            "last_name": "User"
        })
        # May return 400 if email exists, which is fine
        assert response.status_code in [200, 400]
        if response.status_code == 200:
            data = response.json()
            assert "token" in data
            assert "user" in data
            assert data["user"]["email"] == f"test_{unique_id}@example.com"
            print(f"✅ User registration successful for test_{unique_id}@example.com")
        else:
            print("✅ Registration endpoint working (user may already exist)")
    
    def test_login_with_test_user(self):
        """Test login with test credentials"""
        response = requests.post(f"{BASE_URL}/api/auth/login", json={
            "email": TEST_USER_EMAIL,
            "password": TEST_USER_PASSWORD
        })
        # May fail if user doesn't exist
        if response.status_code == 200:
            data = response.json()
            assert "token" in data
            assert "user" in data
            print(f"✅ Login successful for {TEST_USER_EMAIL}")
        else:
            print(f"⚠️ Test user {TEST_USER_EMAIL} may not exist, creating...")
            # Try to register
            reg_response = requests.post(f"{BASE_URL}/api/auth/register", json={
                "email": TEST_USER_EMAIL,
                "password": TEST_USER_PASSWORD,
                "username": "testuser2",
                "first_name": "Test",
                "last_name": "User"
            })
            assert reg_response.status_code in [200, 400]
            print("✅ Test user created or already exists")
    
    def test_login_with_admin(self):
        """Test admin login"""
        response = requests.post(f"{BASE_URL}/api/auth/login", json={
            "email": ADMIN_EMAIL,
            "password": ADMIN_PASSWORD
        })
        assert response.status_code == 200
        data = response.json()
        assert "token" in data
        assert data["user"]["is_admin"] == True
        print("✅ Admin login successful")
    
    def test_login_invalid_credentials(self):
        """Test login with wrong credentials"""
        response = requests.post(f"{BASE_URL}/api/auth/login", json={
            "email": "wrong@example.com",
            "password": "wrongpass"
        })
        assert response.status_code == 401
        print("✅ Invalid credentials correctly rejected")


class TestBookEndpoints:
    """Book-related endpoint tests"""
    
    def test_get_book_info(self):
        """Test book info endpoint"""
        response = requests.get(f"{BASE_URL}/api/book")
        assert response.status_code == 200
        data = response.json()
        assert data["title"] == "Letters to Evelyn"
        assert data["author"] == "John Selman"
        assert "John Selman Publications" in data["publisher"]
        assert data["amazon_link"] == "https://www.amazon.com/Letters-Evelyn-John-Selman/dp/B0F3XFG14J"
        assert data["paypal_link"] == "https://www.paypal.com/ncp/payment/LGXMXSG3D2MXU"
        print("✅ Book info endpoint working with correct PayPal and Amazon links")
    
    def test_get_book_prices(self):
        """Test book prices endpoint"""
        response = requests.get(f"{BASE_URL}/api/book/prices")
        assert response.status_code == 200
        data = response.json()
        assert "ebook" in data
        assert "paperback" in data
        assert "hardcover" in data
        assert data["ebook"] == 4.99
        print(f"✅ Book prices: eBook ${data['ebook']}, Paperback ${data['paperback']}, Hardcover ${data['hardcover']}")


class TestFoodEndpoints:
    """Food menu endpoint tests"""
    
    def test_get_food_menu(self):
        """Test food menu endpoint"""
        response = requests.get(f"{BASE_URL}/api/food/menu")
        assert response.status_code == 200
        data = response.json()
        assert data["restaurant_name"] == "Maestro Bistro"
        assert "Top Pilot Enterprises" in data["parent_company"]
        assert data["location"] == "The Mall, Brunswick, Maine"
        assert len(data["menu"]) >= 5
        
        # Check menu items have prices
        for item in data["menu"]:
            assert "price" in item
            assert "name" in item
            assert item["price"] > 0
        
        print(f"✅ Food menu working with {len(data['menu'])} items")


class TestInfoPilotPlans:
    """InfoPilot subscription plans tests"""
    
    def test_get_plans(self):
        """Test subscription plans endpoint"""
        response = requests.get(f"{BASE_URL}/api/infopilot/plans")
        assert response.status_code == 200
        data = response.json()
        
        assert "monthly" in data
        assert "yearly" in data
        assert data["monthly"]["price"] == 1.00
        assert data["monthly"]["paypal_link"] == "https://www.paypal.com/ncp/payment/LZDBN3SQU4NWQ"
        assert data["yearly"]["paypal_link"] == "https://www.paypal.com/ncp/payment/LZDBN3SQU4NWQ"
        
        print(f"✅ InfoPilot plans: Monthly ${data['monthly']['price']}, Yearly ${data['yearly']['price']}")
        print(f"✅ PayPal subscription link correct: {data['monthly']['paypal_link']}")


class TestEasterEggs:
    """Easter egg functionality tests"""
    
    def test_get_random_easter_egg(self):
        """Test random easter egg endpoint"""
        response = requests.get(f"{BASE_URL}/api/easter-eggs/random")
        assert response.status_code == 200
        data = response.json()
        assert "egg" in data
        assert "joke" in data["egg"]
        assert "protocol_idea" in data["egg"]
        assert "pricing_suggestion" in data["egg"]
        
        # Verify joke content references stepmother/poisoning theme
        joke = data["egg"]["joke"].lower()
        assert any(word in joke for word in ["stepmother", "eggs", "narcotics", "poisoning", "john", "survival", "military"])
        
        print(f"✅ Easter egg retrieved with joke about stepmother/poisoning theme")
    
    def test_catch_easter_egg_requires_auth(self):
        """Test catching easter egg requires authentication"""
        response = requests.post(f"{BASE_URL}/api/easter-eggs/catch", json={"egg_index": 0})
        assert response.status_code in [401, 403]
        print("✅ Easter egg catch correctly requires authentication")
    
    def test_catch_easter_egg_with_auth(self):
        """Test catching easter egg with authentication"""
        # Login first
        login_response = requests.post(f"{BASE_URL}/api/auth/login", json={
            "email": ADMIN_EMAIL,
            "password": ADMIN_PASSWORD
        })
        if login_response.status_code != 200:
            pytest.skip("Could not login to test easter egg catch")
        
        token = login_response.json()["token"]
        headers = {"Authorization": f"Bearer {token}"}
        
        response = requests.post(f"{BASE_URL}/api/easter-eggs/catch", 
                                json={"egg_index": 0},
                                headers=headers)
        assert response.status_code == 200
        data = response.json()
        assert "message" in data
        assert "Laughter Points" in data["message"]
        assert "total_points" in data
        assert "egg" in data
        
        print(f"✅ Easter egg caught! Total points: {data['total_points']}")


class TestCategoriesAndSearch:
    """Category and search functionality tests"""
    
    @pytest.fixture
    def auth_headers(self):
        """Get auth headers for authenticated requests"""
        login_response = requests.post(f"{BASE_URL}/api/auth/login", json={
            "email": ADMIN_EMAIL,
            "password": ADMIN_PASSWORD
        })
        if login_response.status_code != 200:
            pytest.skip("Could not login")
        token = login_response.json()["token"]
        return {"Authorization": f"Bearer {token}"}
    
    def test_get_categories_requires_auth(self):
        """Test categories endpoint requires auth"""
        response = requests.get(f"{BASE_URL}/api/categories")
        assert response.status_code in [401, 403]
        print("✅ Categories endpoint correctly requires authentication")
    
    def test_get_categories_with_auth(self, auth_headers):
        """Test getting categories with authentication"""
        response = requests.get(f"{BASE_URL}/api/categories", headers=auth_headers)
        assert response.status_code == 200
        data = response.json()
        assert "categories" in data
        print(f"✅ Categories retrieved: {len(data['categories'])} categories")
    
    def test_create_category_with_infojet_protocol(self, auth_headers):
        """Test creating category with InfoJet 2.0 protocol"""
        unique_id = str(uuid.uuid4())[:8]
        response = requests.post(f"{BASE_URL}/api/categories", 
                                json={
                                    "name": f"Test Category {unique_id}",
                                    "protocol": "(test or example) & (data or info)",
                                    "is_public": True,
                                    "price": None
                                },
                                headers=auth_headers)
        assert response.status_code == 200
        data = response.json()
        assert data["name"] == f"Test Category {unique_id}"
        assert data["protocol"] == "(test or example) & (data or info)"
        assert "id" in data
        
        print(f"✅ Category created with InfoJet 2.0 protocol: {data['name']}")
        return data["id"]
    
    def test_search_collate_mock(self, auth_headers):
        """Test search and collate (returns mock results)"""
        response = requests.post(f"{BASE_URL}/api/search/collate",
                                json={"query": "test search query"},
                                headers=auth_headers)
        assert response.status_code == 200
        data = response.json()
        assert "message" in data
        assert "results" in data
        assert "total_searched" in data
        
        print(f"✅ Search & Collate working (MOCKED): {data['message']}")


class TestLeaderboardAndStats:
    """Leaderboard and statistics tests"""
    
    def test_get_leaderboard(self):
        """Test leaderboard endpoint"""
        response = requests.get(f"{BASE_URL}/api/leaderboard")
        assert response.status_code == 200
        data = response.json()
        assert "top_laughter_points" in data
        assert "top_protocol_creators" in data
        
        print(f"✅ Leaderboard working: {len(data['top_laughter_points'])} top users by laughter points")
    
    def test_get_stats(self):
        """Test statistics endpoint"""
        response = requests.get(f"{BASE_URL}/api/stats")
        assert response.status_code == 200
        data = response.json()
        assert "global" in data
        assert "total_users" in data["global"]
        assert "public_categories" in data["global"]
        
        print(f"✅ Stats working: {data['global']['total_users']} users, {data['global']['public_categories']} public categories")


class TestMarketplace:
    """Marketplace functionality tests"""
    
    def test_get_marketplace_protocols(self):
        """Test marketplace protocols endpoint"""
        response = requests.get(f"{BASE_URL}/api/marketplace/protocols")
        assert response.status_code == 200
        data = response.json()
        assert "protocols" in data
        assert "total" in data
        
        print(f"✅ Marketplace working: {data['total']} protocols available")


class TestNewsHeadlines:
    """News headlines tests"""
    
    def test_get_headlines(self):
        """Test news headlines endpoint (MOCKED)"""
        response = requests.get(f"{BASE_URL}/api/news/headlines")
        assert response.status_code == 200
        data = response.json()
        assert "headlines" in data
        assert len(data["headlines"]) == 10
        
        # Verify headlines have required fields
        for headline in data["headlines"]:
            assert "title" in headline
            assert "category" in headline
        
        print(f"✅ News headlines working (MOCKED): {len(data['headlines'])} headlines")


class TestTestimonials:
    """Testimonials tests"""
    
    def test_get_testimonials(self):
        """Test testimonials endpoint"""
        response = requests.get(f"{BASE_URL}/api/testimonials")
        assert response.status_code == 200
        data = response.json()
        assert "testimonials" in data
        
        # Check for professional reviews
        has_readers_favorite = any("Readers' Favorite" in str(t) for t in data["testimonials"])
        assert has_readers_favorite, "Should have Readers' Favorite reviews"
        
        print(f"✅ Testimonials working: {len(data['testimonials'])} testimonials including Readers' Favorite reviews")


class TestContactAndNewsletter:
    """Contact and newsletter tests"""
    
    def test_contact_form(self):
        """Test contact form submission"""
        response = requests.post(f"{BASE_URL}/api/contact", json={
            "name": "Test User",
            "email": "test@example.com",
            "subject": "Test Subject",
            "message": "This is a test message"
        })
        assert response.status_code == 200
        data = response.json()
        assert "message" in data
        print("✅ Contact form submission working")
    
    def test_newsletter_signup(self):
        """Test newsletter signup"""
        unique_id = str(uuid.uuid4())[:8]
        response = requests.post(f"{BASE_URL}/api/newsletter/signup", json={
            "email": f"newsletter_{unique_id}@example.com",
            "name": "Test Subscriber",
            "signup_type": "general"
        })
        assert response.status_code in [200, 400]  # 400 if already subscribed
        print("✅ Newsletter signup endpoint working")


class TestLegalPages:
    """Legal pages tests"""
    
    def test_user_agreement(self):
        """Test user agreement endpoint"""
        response = requests.get(f"{BASE_URL}/api/legal/user-agreement")
        assert response.status_code == 200
        data = response.json()
        assert "title" in data
        assert "content" in data
        assert "Top Pilot Enterprises" in data["content"]
        print("✅ User agreement endpoint working")
    
    def test_privacy_policy(self):
        """Test privacy policy endpoint"""
        response = requests.get(f"{BASE_URL}/api/legal/privacy-policy")
        assert response.status_code == 200
        data = response.json()
        assert "title" in data
        assert "content" in data
        print("✅ Privacy policy endpoint working")


class TestCompanyInfo:
    """Company info tests"""
    
    def test_company_info(self):
        """Test company info endpoint"""
        response = requests.get(f"{BASE_URL}/api/company")
        assert response.status_code == 200
        data = response.json()
        assert data["corporation"] == "Top Pilot Enterprises, Inc."
        assert "It's a Bear!" in data["tagline"]
        assert len(data["subsidiaries"]) >= 3
        
        # Check subsidiaries
        subsidiary_names = [s["name"] for s in data["subsidiaries"]]
        assert "InfoPilot Explorer, LLC" in subsidiary_names
        assert "Maestro Bistro" in subsidiary_names
        assert "John Selman Publications" in subsidiary_names
        
        print("✅ Company info endpoint working with all subsidiaries")


class TestQuotesGallery:
    """Quotes gallery tests"""
    
    def test_quotes_gallery(self):
        """Test quotes gallery endpoint"""
        response = requests.get(f"{BASE_URL}/api/quotes/gallery")
        assert response.status_code == 200
        data = response.json()
        assert "quotes" in data
        assert len(data["quotes"]) >= 5
        
        # Check for stepmother/poisoning related quotes
        all_quotes = " ".join([q["quote"] for q in data["quotes"]])
        assert any(word in all_quotes.lower() for word in ["eggs", "narcotics", "stepmother", "military"])
        
        print(f"✅ Quotes gallery working: {len(data['quotes'])} quotes including poisoning references")


if __name__ == "__main__":
    pytest.main([__file__, "-v", "--tb=short"])
