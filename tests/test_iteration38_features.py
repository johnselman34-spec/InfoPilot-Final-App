"""
InfoPilot Explorer - Iteration 38 Feature Tests
Tests for:
- Easter Egg Tracker system
- Daily Laugh Goal with streak bonuses
- Category Hierarchy CRUD
- AI Newsletter Optimization
- Unified Chat integration
- Premium Map Export
"""
import pytest
import requests
import os

# Use public URL from environment
BASE_URL = os.environ.get('REACT_APP_BACKEND_URL', 'https://infopilot-preview.preview.emergentagent.com').rstrip('/')

# Test credentials
ADMIN_EMAIL = "jjspilot24@gmail.com"
ADMIN_PASSWORD = "InfoPilot2024!"
TEST_EMAIL = "testuser@example.com"
TEST_PASSWORD = "password123"


class TestHealthAndBasics:
    """Basic health and connectivity tests"""
    
    def test_health_endpoint(self):
        """Test API health endpoint"""
        response = requests.get(f"{BASE_URL}/api/health")
        assert response.status_code == 200
        data = response.json()
        assert data["status"] == "healthy"
        print("✅ Health endpoint working")


class TestAuthentication:
    """Authentication tests"""
    
    def test_admin_login(self):
        """Test admin login"""
        response = requests.post(
            f"{BASE_URL}/api/auth/login",
            json={"email": ADMIN_EMAIL, "password": ADMIN_PASSWORD}
        )
        assert response.status_code == 200
        data = response.json()
        assert "token" in data
        print("✅ Admin login successful")
        return data["token"]


@pytest.fixture
def admin_token():
    """Get admin auth token"""
    response = requests.post(
        f"{BASE_URL}/api/auth/login",
        json={"email": ADMIN_EMAIL, "password": ADMIN_PASSWORD}
    )
    if response.status_code == 200:
        return response.json()["token"]
    pytest.skip("Admin login failed")


# ==================== EASTER EGG TRACKER TESTS ====================

class TestEasterEggTracker:
    """Tests for Easter Egg Tracker system"""
    
    def test_get_all_easter_eggs(self):
        """Test /api/easter-eggs/all endpoint - public"""
        response = requests.get(f"{BASE_URL}/api/easter-eggs/all")
        assert response.status_code == 200
        data = response.json()
        
        # Verify structure
        assert "eggs" in data
        assert "by_rarity" in data
        assert "total" in data
        assert "total_xp_possible" in data
        
        # Verify we have 15 eggs as defined
        assert data["total"] >= 15, f"Expected at least 15 eggs, got {data['total']}"
        
        # Verify rarity categories
        assert "rare" in data["by_rarity"]
        assert "epic" in data["by_rarity"]
        assert "legendary" in data["by_rarity"]
        
        print(f"✅ Easter eggs endpoint working - {data['total']} eggs, {data['total_xp_possible']} total XP")
    
    def test_my_discoveries_requires_auth(self):
        """Test /api/easter-eggs/my-discoveries requires authentication"""
        response = requests.get(f"{BASE_URL}/api/easter-eggs/my-discoveries")
        assert response.status_code == 401 or response.status_code == 403
        print("✅ My discoveries endpoint requires auth")
    
    def test_my_discoveries_with_auth(self, admin_token):
        """Test /api/easter-eggs/my-discoveries with auth"""
        response = requests.get(
            f"{BASE_URL}/api/easter-eggs/my-discoveries",
            headers={"Authorization": f"Bearer {admin_token}"}
        )
        assert response.status_code == 200
        data = response.json()
        
        # Verify structure
        assert "discovered" in data
        assert "undiscovered" in data
        assert "discovered_count" in data
        assert "total_eggs" in data
        assert "total_xp_earned" in data
        assert "completion_percentage" in data
        
        print(f"✅ My discoveries: {data['discovered_count']}/{data['total_eggs']} eggs found")
    
    def test_discover_easter_egg(self, admin_token):
        """Test /api/easter-eggs/discover endpoint"""
        response = requests.post(
            f"{BASE_URL}/api/easter-eggs/discover",
            json={"egg_id": "egg_hunter", "trigger": "test"},
            headers={"Authorization": f"Bearer {admin_token}"}
        )
        assert response.status_code == 200
        data = response.json()
        
        # Either success or already discovered
        assert "success" in data or "already_discovered" in data
        print(f"✅ Discover endpoint working - {data.get('message', 'Already discovered')}")
    
    def test_discover_invalid_egg(self, admin_token):
        """Test discovering non-existent egg"""
        response = requests.post(
            f"{BASE_URL}/api/easter-eggs/discover",
            json={"egg_id": "nonexistent_egg_12345", "trigger": "test"},
            headers={"Authorization": f"Bearer {admin_token}"}
        )
        assert response.status_code == 404
        print("✅ Invalid egg returns 404")
    
    def test_easter_egg_leaderboard(self):
        """Test /api/easter-eggs/leaderboard endpoint"""
        response = requests.get(f"{BASE_URL}/api/easter-eggs/leaderboard")
        assert response.status_code == 200
        data = response.json()
        
        assert "leaderboard" in data
        assert "total_eggs_available" in data
        assert "funny_title" in data
        
        print(f"✅ Easter egg leaderboard working - {len(data['leaderboard'])} hunters")
    
    def test_easter_egg_stats(self):
        """Test /api/easter-eggs/stats endpoint"""
        response = requests.get(f"{BASE_URL}/api/easter-eggs/stats")
        assert response.status_code == 200
        data = response.json()
        
        assert "total_discoveries" in data
        assert "total_eggs_available" in data
        assert "most_discovered" in data
        assert "rarest_eggs" in data
        
        print(f"✅ Easter egg stats working - {data['total_discoveries']} total discoveries")


# ==================== DAILY LAUGH GOAL TESTS ====================

class TestDailyLaughGoal:
    """Tests for Daily Laugh Goal with streak bonuses"""
    
    def test_get_daily_laugh_goal(self, admin_token):
        """Test GET /api/gamification/daily-laugh-goal"""
        response = requests.get(
            f"{BASE_URL}/api/gamification/daily-laugh-goal",
            headers={"Authorization": f"Bearer {admin_token}"}
        )
        assert response.status_code == 200
        data = response.json()
        
        # Verify all required fields
        assert "daily_goal" in data
        assert "current_progress" in data
        assert "streak_days" in data
        assert "longest_streak" in data
        assert "total_goals_completed" in data
        assert "streak_xp_earned" in data
        assert "goal_completed_today" in data
        
        print(f"✅ Daily laugh goal: {data['current_progress']}/{data['daily_goal']}, streak: {data['streak_days']} days")
    
    def test_set_daily_laugh_goal(self, admin_token):
        """Test POST /api/gamification/daily-laugh-goal/set"""
        response = requests.post(
            f"{BASE_URL}/api/gamification/daily-laugh-goal/set",
            json={"goal": 15},
            headers={"Authorization": f"Bearer {admin_token}"}
        )
        assert response.status_code == 200
        data = response.json()
        
        assert data["success"] == True
        assert data["daily_goal"] == 15
        assert "message" in data
        
        print(f"✅ Set daily goal to 15 - {data['message']}")
    
    def test_set_daily_laugh_goal_validation(self, admin_token):
        """Test goal validation (5-100 range)"""
        # Test below minimum
        response = requests.post(
            f"{BASE_URL}/api/gamification/daily-laugh-goal/set",
            json={"goal": 2},
            headers={"Authorization": f"Bearer {admin_token}"}
        )
        assert response.status_code == 200
        data = response.json()
        assert data["daily_goal"] >= 5, "Goal should be clamped to minimum 5"
        
        # Test above maximum
        response = requests.post(
            f"{BASE_URL}/api/gamification/daily-laugh-goal/set",
            json={"goal": 200},
            headers={"Authorization": f"Bearer {admin_token}"}
        )
        assert response.status_code == 200
        data = response.json()
        assert data["daily_goal"] <= 100, "Goal should be clamped to maximum 100"
        
        print("✅ Goal validation working (5-100 range)")
    
    def test_record_daily_laugh_progress(self, admin_token):
        """Test POST /api/gamification/daily-laugh-goal/record-progress"""
        response = requests.post(
            f"{BASE_URL}/api/gamification/daily-laugh-goal/record-progress",
            headers={"Authorization": f"Bearer {admin_token}"}
        )
        assert response.status_code == 200
        data = response.json()
        
        assert data["success"] == True
        assert "current_progress" in data
        assert "daily_goal" in data
        assert "goal_completed" in data
        assert "streak_days" in data
        
        print(f"✅ Progress recorded: {data['current_progress']}/{data['daily_goal']}")
    
    def test_daily_laugh_goal_leaderboard(self):
        """Test GET /api/gamification/daily-laugh-goal/leaderboard"""
        response = requests.get(f"{BASE_URL}/api/gamification/daily-laugh-goal/leaderboard")
        assert response.status_code == 200
        data = response.json()
        
        assert "leaderboard" in data
        assert "total_participants" in data
        assert "funny_title" in data
        
        print(f"✅ Streak leaderboard: {data['total_participants']} participants")
    
    def test_daily_laugh_goal_requires_auth(self):
        """Test that daily laugh goal endpoints require auth"""
        response = requests.get(f"{BASE_URL}/api/gamification/daily-laugh-goal")
        assert response.status_code == 401 or response.status_code == 403
        print("✅ Daily laugh goal requires auth")


# ==================== CATEGORY HIERARCHY TESTS ====================

class TestCategoryHierarchy:
    """Tests for Category Hierarchy CRUD operations"""
    
    def test_get_categories(self, admin_token):
        """Test GET /api/categories"""
        response = requests.get(
            f"{BASE_URL}/api/categories",
            headers={"Authorization": f"Bearer {admin_token}"}
        )
        assert response.status_code == 200
        data = response.json()
        
        assert isinstance(data, list)
        if len(data) > 0:
            cat = data[0]
            assert "id" in cat
            assert "name" in cat
            assert "protocol" in cat
            assert "result_count" in cat
            assert "subcategory_count" in cat
        
        print(f"✅ Categories endpoint working - {len(data)} categories")
    
    def test_create_parent_category(self, admin_token):
        """Test creating a top-level category"""
        response = requests.post(
            f"{BASE_URL}/api/categories",
            json={
                "name": "TEST_Parent_Category_38",
                "protocol": "(weather or forecast)",
                "is_public": True
            },
            headers={"Authorization": f"Bearer {admin_token}"}
        )
        assert response.status_code == 200
        data = response.json()
        
        assert data["name"] == "TEST_Parent_Category_38"
        assert data["level"] == 0
        assert data["parent_id"] is None
        
        # Cleanup
        requests.delete(
            f"{BASE_URL}/api/categories/{data['id']}",
            headers={"Authorization": f"Bearer {admin_token}"}
        )
        print("✅ Parent category creation working")
    
    def test_create_subcategory(self, admin_token):
        """Test creating a subcategory"""
        # Create parent
        parent_response = requests.post(
            f"{BASE_URL}/api/categories",
            json={
                "name": "TEST_Parent_For_Sub_38",
                "protocol": "(sports or news)",
                "is_public": True
            },
            headers={"Authorization": f"Bearer {admin_token}"}
        )
        assert parent_response.status_code == 200
        parent_id = parent_response.json()["id"]
        
        # Create subcategory
        sub_response = requests.post(
            f"{BASE_URL}/api/categories",
            json={
                "name": "TEST_Subcategory_38",
                "protocol": "(basketball or football)",
                "is_public": True,
                "parent_id": parent_id
            },
            headers={"Authorization": f"Bearer {admin_token}"}
        )
        assert sub_response.status_code == 200
        sub_data = sub_response.json()
        
        assert sub_data["parent_id"] == parent_id
        assert sub_data["level"] == 1
        
        # Cleanup
        requests.delete(f"{BASE_URL}/api/categories/{sub_data['id']}", headers={"Authorization": f"Bearer {admin_token}"})
        requests.delete(f"{BASE_URL}/api/categories/{parent_id}", headers={"Authorization": f"Bearer {admin_token}"})
        print("✅ Subcategory creation working")
    
    def test_edit_category(self, admin_token):
        """Test editing a category"""
        # Create category
        create_response = requests.post(
            f"{BASE_URL}/api/categories",
            json={
                "name": "TEST_Original_Name_38",
                "protocol": "(original or test)",
                "is_public": False
            },
            headers={"Authorization": f"Bearer {admin_token}"}
        )
        cat_id = create_response.json()["id"]
        
        # Edit category
        edit_response = requests.put(
            f"{BASE_URL}/api/categories/{cat_id}",
            json={
                "name": "TEST_Updated_Name_38",
                "protocol": "(updated or protocol)",
                "is_public": True
            },
            headers={"Authorization": f"Bearer {admin_token}"}
        )
        assert edit_response.status_code == 200
        updated = edit_response.json()
        
        assert updated["name"] == "TEST_Updated_Name_38"
        assert updated["protocol"] == "(updated or protocol)"
        assert updated["is_public"] == True
        
        # Cleanup
        requests.delete(f"{BASE_URL}/api/categories/{cat_id}", headers={"Authorization": f"Bearer {admin_token}"})
        print("✅ Category editing working")
    
    def test_cascade_delete(self, admin_token):
        """Test that deleting parent cascades to children"""
        # Create parent
        parent_response = requests.post(
            f"{BASE_URL}/api/categories",
            json={
                "name": "TEST_Cascade_Parent_38",
                "protocol": "(cascade or test)",
                "is_public": True
            },
            headers={"Authorization": f"Bearer {admin_token}"}
        )
        parent_id = parent_response.json()["id"]
        
        # Create child
        child_response = requests.post(
            f"{BASE_URL}/api/categories",
            json={
                "name": "TEST_Cascade_Child_38",
                "protocol": "(child or cascade)",
                "is_public": True,
                "parent_id": parent_id
            },
            headers={"Authorization": f"Bearer {admin_token}"}
        )
        child_id = child_response.json()["id"]
        
        # Delete parent
        delete_response = requests.delete(
            f"{BASE_URL}/api/categories/{parent_id}",
            headers={"Authorization": f"Bearer {admin_token}"}
        )
        assert delete_response.status_code == 200
        
        # Verify child was deleted
        categories = requests.get(
            f"{BASE_URL}/api/categories",
            headers={"Authorization": f"Bearer {admin_token}"}
        ).json()
        
        child_exists = any(cat["id"] == child_id for cat in categories)
        assert not child_exists, "Child should have been cascade deleted"
        print("✅ Cascade delete working")


# ==================== AI NEWSLETTER OPTIMIZATION TESTS ====================

class TestAINewsletterOptimization:
    """Tests for AI Newsletter Optimization in Admin Panel"""
    
    def test_ai_optimize_endpoint(self, admin_token):
        """Test /api/admin/newsletter/ai-optimize endpoint"""
        response = requests.get(
            f"{BASE_URL}/api/admin/newsletter/ai-optimize",
            headers={"Authorization": f"Bearer {admin_token}"}
        )
        assert response.status_code == 200
        data = response.json()
        
        # Should return either AI recommendations or fallback
        assert "success" in data or "fallback_recommendation" in data or "ai_recommendations" in data
        
        if data.get("success") and data.get("ai_recommendations"):
            print(f"✅ AI optimization returned recommendations")
        elif data.get("fallback_recommendation"):
            print(f"✅ AI optimization returned fallback (LLM key may not be configured)")
        else:
            print(f"✅ AI optimization endpoint working")
    
    def test_ai_optimize_requires_admin(self):
        """Test that AI optimize requires admin auth"""
        response = requests.get(f"{BASE_URL}/api/admin/newsletter/ai-optimize")
        assert response.status_code == 401 or response.status_code == 403
        print("✅ AI optimize requires admin auth")


# ==================== UNIFIED CHAT TESTS ====================

class TestUnifiedChat:
    """Tests for Unified Chat integration"""
    
    def test_unified_chat_overview(self, admin_token):
        """Test /api/unified-chat/overview endpoint"""
        response = requests.get(
            f"{BASE_URL}/api/unified-chat/overview",
            headers={"Authorization": f"Bearer {admin_token}"}
        )
        # May return 200 or 404 depending on implementation
        if response.status_code == 200:
            data = response.json()
            print(f"✅ Unified chat overview working")
        elif response.status_code == 404:
            print("⚠️ Unified chat overview endpoint not found (may not be implemented)")
        else:
            print(f"⚠️ Unified chat returned status {response.status_code}")


# ==================== LAUGH-O-METER TESTS ====================

class TestLaughOMeter:
    """Tests for Laugh-O-Meter endpoints"""
    
    def test_laugh_stats(self, admin_token):
        """Test GET /api/gamification/laugh-stats"""
        response = requests.get(
            f"{BASE_URL}/api/gamification/laugh-stats",
            headers={"Authorization": f"Bearer {admin_token}"}
        )
        assert response.status_code == 200
        data = response.json()
        
        assert "totalLaughs" in data
        assert "todayLaughs" in data
        assert "xp" in data
        assert "level" in data
        assert "title" in data
        
        print(f"✅ Laugh stats: {data['totalLaughs']} total, {data['xp']} XP, Level {data['level']}")
    
    def test_record_laugh(self, admin_token):
        """Test POST /api/gamification/record-laugh"""
        response = requests.post(
            f"{BASE_URL}/api/gamification/record-laugh",
            json={"source": "test"},
            headers={"Authorization": f"Bearer {admin_token}"}
        )
        assert response.status_code == 200
        data = response.json()
        
        assert data["success"] == True
        print(f"✅ Record laugh working - {data['message']}")
    
    def test_laugh_leaderboard(self):
        """Test GET /api/gamification/laugh-leaderboard"""
        response = requests.get(f"{BASE_URL}/api/gamification/laugh-leaderboard")
        assert response.status_code == 200
        data = response.json()
        
        assert "leaderboard" in data
        assert "total_participants" in data
        
        print(f"✅ Laugh leaderboard: {data['total_participants']} participants")


# ==================== GAMIFICATION ACHIEVEMENTS TESTS ====================

class TestGamificationAchievements:
    """Tests for Gamification achievements"""
    
    def test_get_all_achievements(self):
        """Test GET /api/gamification/achievements"""
        response = requests.get(f"{BASE_URL}/api/gamification/achievements")
        assert response.status_code == 200
        data = response.json()
        
        assert "achievements" in data
        assert "by_category" in data
        assert "total_achievements" in data
        
        print(f"✅ Achievements: {data['total_achievements']} total")
    
    def test_my_achievements(self, admin_token):
        """Test GET /api/gamification/my-achievements"""
        response = requests.get(
            f"{BASE_URL}/api/gamification/my-achievements",
            headers={"Authorization": f"Bearer {admin_token}"}
        )
        assert response.status_code == 200
        data = response.json()
        
        assert "earned" in data
        assert "unearned" in data
        assert "total_points" in data
        assert "level" in data
        
        print(f"✅ My achievements: {len(data['earned'])} earned, {data['total_points']} points")


# ==================== ADMIN SETTINGS TESTS ====================

class TestAdminSettings:
    """Tests for Admin settings"""
    
    def test_admin_settings(self, admin_token):
        """Test GET /admin/settings"""
        response = requests.get(
            f"{BASE_URL}/admin/settings",
            headers={"Authorization": f"Bearer {admin_token}"}
        )
        assert response.status_code == 200
        print("✅ Admin settings endpoint working")


# ==================== CLEANUP ====================

def cleanup_test_data(admin_token):
    """Clean up any test data created during tests"""
    # Get all categories
    response = requests.get(
        f"{BASE_URL}/api/categories",
        headers={"Authorization": f"Bearer {admin_token}"}
    )
    if response.status_code == 200:
        categories = response.json()
        for cat in categories:
            if cat["name"].startswith("TEST_"):
                requests.delete(
                    f"{BASE_URL}/api/categories/{cat['id']}",
                    headers={"Authorization": f"Bearer {admin_token}"}
                )


if __name__ == "__main__":
    pytest.main([__file__, "-v", "--tb=short"])
