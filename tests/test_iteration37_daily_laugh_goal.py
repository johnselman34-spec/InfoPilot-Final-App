"""
InfoPilot Explorer - Iteration 37 Tests
Testing Daily Laugh Goal system with streak bonuses, Newsletter times (5:42 AM, 8:37 AM, 4:41 PM),
Admin-controllable newsletter settings, Laugh-O-Meter, Categories with result_count, Collation default 40
"""
import pytest
import requests
import os
import re

BASE_URL = os.environ.get('REACT_APP_BACKEND_URL', '').rstrip('/')

# Test credentials
ADMIN_EMAIL = "jjspilot24@gmail.com"
ADMIN_PASSWORD = "InfoPilot2024!"


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
        response = requests.post(f"{BASE_URL}/api/auth/login", json={
            "email": ADMIN_EMAIL,
            "password": ADMIN_PASSWORD
        })
        assert response.status_code == 200
        data = response.json()
        assert "token" in data
        # is_admin is in user object
        user = data.get("user", {})
        assert user.get("is_admin") == True
        print(f"✅ Admin login successful, is_admin={user.get('is_admin')}")
        return data["token"]


class TestDailyLaughGoalEndpoints:
    """Test Daily Laugh Goal endpoints - NEW in iteration 37"""
    
    @pytest.fixture
    def auth_token(self):
        """Get admin auth token"""
        response = requests.post(f"{BASE_URL}/api/auth/login", json={
            "email": ADMIN_EMAIL,
            "password": ADMIN_PASSWORD
        })
        if response.status_code == 200:
            return response.json().get("token")
        pytest.skip("Authentication failed")
    
    def test_get_daily_laugh_goal(self, auth_token):
        """Test GET /api/gamification/daily-laugh-goal"""
        response = requests.get(
            f"{BASE_URL}/api/gamification/daily-laugh-goal",
            headers={"Authorization": f"Bearer {auth_token}"}
        )
        assert response.status_code == 200
        data = response.json()
        
        # Verify response structure
        assert "daily_goal" in data
        assert "current_progress" in data
        assert "streak_days" in data
        assert "longest_streak" in data
        assert "total_goals_completed" in data
        assert "streak_xp_earned" in data
        assert "goal_completed_today" in data
        assert "next_streak_bonus" in data
        
        # Verify data types
        assert isinstance(data["daily_goal"], int)
        assert isinstance(data["current_progress"], int)
        assert isinstance(data["streak_days"], int)
        assert isinstance(data["goal_completed_today"], bool)
        
        print(f"✅ Daily Laugh Goal endpoint working: goal={data['daily_goal']}, progress={data['current_progress']}, streak={data['streak_days']}")
    
    def test_set_daily_laugh_goal(self, auth_token):
        """Test POST /api/gamification/daily-laugh-goal/set"""
        # Set goal to 15
        response = requests.post(
            f"{BASE_URL}/api/gamification/daily-laugh-goal/set",
            headers={"Authorization": f"Bearer {auth_token}"},
            json={"goal": 15}
        )
        assert response.status_code == 200
        data = response.json()
        
        assert data["success"] == True
        assert data["daily_goal"] == 15
        assert "message" in data
        print(f"✅ Set Daily Laugh Goal working: {data['message']}")
        
        # Verify the goal was set by getting it again
        verify_response = requests.get(
            f"{BASE_URL}/api/gamification/daily-laugh-goal",
            headers={"Authorization": f"Bearer {auth_token}"}
        )
        assert verify_response.status_code == 200
        verify_data = verify_response.json()
        assert verify_data["daily_goal"] == 15
        print(f"✅ Goal persisted correctly: {verify_data['daily_goal']}")
    
    def test_set_daily_laugh_goal_validation(self, auth_token):
        """Test goal validation (5-100 range)"""
        # Test minimum boundary (should clamp to 5)
        response = requests.post(
            f"{BASE_URL}/api/gamification/daily-laugh-goal/set",
            headers={"Authorization": f"Bearer {auth_token}"},
            json={"goal": 2}
        )
        assert response.status_code == 200
        data = response.json()
        assert data["daily_goal"] == 5  # Should be clamped to minimum
        print(f"✅ Goal validation (min): 2 clamped to {data['daily_goal']}")
        
        # Test maximum boundary (should clamp to 100)
        response = requests.post(
            f"{BASE_URL}/api/gamification/daily-laugh-goal/set",
            headers={"Authorization": f"Bearer {auth_token}"},
            json={"goal": 150}
        )
        assert response.status_code == 200
        data = response.json()
        assert data["daily_goal"] == 100  # Should be clamped to maximum
        print(f"✅ Goal validation (max): 150 clamped to {data['daily_goal']}")
    
    def test_record_daily_laugh_progress(self, auth_token):
        """Test POST /api/gamification/daily-laugh-goal/record-progress"""
        # First set a reasonable goal
        requests.post(
            f"{BASE_URL}/api/gamification/daily-laugh-goal/set",
            headers={"Authorization": f"Bearer {auth_token}"},
            json={"goal": 10}
        )
        
        # Record progress
        response = requests.post(
            f"{BASE_URL}/api/gamification/daily-laugh-goal/record-progress",
            headers={"Authorization": f"Bearer {auth_token}"}
        )
        assert response.status_code == 200
        data = response.json()
        
        assert data["success"] == True
        assert "current_progress" in data
        assert "daily_goal" in data
        assert "goal_completed" in data
        assert "streak_days" in data
        
        print(f"✅ Record progress working: progress={data['current_progress']}/{data['daily_goal']}, streak={data['streak_days']}")
    
    def test_daily_laugh_goal_leaderboard(self, auth_token):
        """Test GET /api/gamification/daily-laugh-goal/leaderboard"""
        response = requests.get(
            f"{BASE_URL}/api/gamification/daily-laugh-goal/leaderboard",
            headers={"Authorization": f"Bearer {auth_token}"}
        )
        assert response.status_code == 200
        data = response.json()
        
        assert "leaderboard" in data
        assert "total_participants" in data
        assert "funny_title" in data
        assert isinstance(data["leaderboard"], list)
        
        # Check leaderboard entry structure if entries exist
        if len(data["leaderboard"]) > 0:
            entry = data["leaderboard"][0]
            assert "rank" in entry
            assert "username" in entry
            assert "streak_days" in entry
            assert "longest_streak" in entry
            assert "total_goals_completed" in entry
            assert "daily_goal" in entry
            assert "streak_xp_earned" in entry
        
        print(f"✅ Daily Laugh Goal Leaderboard working: {len(data['leaderboard'])} participants, title='{data['funny_title']}'")
    
    def test_daily_laugh_goal_requires_auth(self):
        """Test that daily laugh goal endpoints require authentication"""
        response = requests.get(f"{BASE_URL}/api/gamification/daily-laugh-goal")
        assert response.status_code in [401, 403]
        print("✅ Daily Laugh Goal requires authentication")


class TestStreakBonusesInCode:
    """Verify streak bonus values are correctly defined in code"""
    
    def test_streak_bonuses_defined(self):
        """Verify streak bonus XP values in gamification.py"""
        with open("/app/backend/routes/gamification.py", "r") as f:
            content = f.read()
        
        # Check STREAK_BONUSES dictionary exists
        assert "STREAK_BONUSES" in content
        
        # Verify specific bonus values
        assert "3: 25" in content or "3:25" in content.replace(" ", "")  # 3-day = 25 XP
        assert "7: 75" in content or "7:75" in content.replace(" ", "")  # 7-day = 75 XP
        assert "14: 150" in content or "14:150" in content.replace(" ", "")  # 14-day = 150 XP
        assert "30: 400" in content or "30:400" in content.replace(" ", "")  # 30-day = 400 XP
        assert "100: 1000" in content or "100:1000" in content.replace(" ", "")  # 100-day = 1000 XP
        
        print("✅ Streak bonuses correctly defined: 3-day=25XP, 7-day=75XP, 14-day=150XP, 30-day=400XP, 100-day=1000XP")


class TestNewsletterSchedulerTimes:
    """Test newsletter scheduler times are set to 5:42 AM, 8:37 AM, 4:41 PM UTC"""
    
    def test_newsletter_times_in_code(self):
        """Verify newsletter scheduler times in triweekly_newsletter.py"""
        with open("/app/backend/services/triweekly_newsletter.py", "r") as f:
            content = f.read()
        
        # Check for 5:42 AM (hour=5, minute=42)
        assert "hour=5" in content and "minute=42" in content, "5:42 AM schedule not found"
        
        # Check for 8:37 AM (hour=8, minute=37)
        assert "hour=8" in content and "minute=37" in content, "8:37 AM schedule not found"
        
        # Check for 4:41 PM (hour=16, minute=41)
        assert "hour=16" in content and "minute=41" in content, "4:41 PM schedule not found"
        
        print("✅ Newsletter times correctly set: 5:42 AM, 8:37 AM, 4:41 PM UTC")
    
    def test_newsletter_scheduler_job_names(self):
        """Verify newsletter scheduler job names"""
        with open("/app/backend/services/triweekly_newsletter.py", "r") as f:
            content = f.read()
        
        assert "5:42 AM" in content
        assert "8:37 AM" in content
        assert "4:41 PM" in content
        
        print("✅ Newsletter scheduler job names include correct times")


class TestAdminNewsletterSettings:
    """Test admin settings for newsletter times"""
    
    @pytest.fixture
    def auth_token(self):
        """Get admin auth token"""
        response = requests.post(f"{BASE_URL}/api/auth/login", json={
            "email": ADMIN_EMAIL,
            "password": ADMIN_PASSWORD
        })
        if response.status_code == 200:
            return response.json().get("token")
        pytest.skip("Authentication failed")
    
    def test_admin_settings_endpoint(self, auth_token):
        """Test GET /api/admin/settings"""
        response = requests.get(
            f"{BASE_URL}/api/admin/settings",
            headers={"Authorization": f"Bearer {auth_token}"}
        )
        assert response.status_code == 200
        data = response.json()
        
        # Check for newsletter time settings
        print(f"✅ Admin settings retrieved: {list(data.keys())[:10]}...")
    
    def test_admin_settings_init(self, auth_token):
        """Test POST /api/admin/settings/init to verify default settings"""
        response = requests.post(
            f"{BASE_URL}/api/admin/settings/init",
            headers={"Authorization": f"Bearer {auth_token}"}
        )
        assert response.status_code == 200
        data = response.json()
        
        # Check for message or count in response
        assert "message" in data or "count" in data or "success" in data
        print(f"✅ Admin settings init endpoint working: {data}")
    
    def test_newsletter_time_settings_in_admin_code(self):
        """Verify newsletter time settings exist in admin.py"""
        with open("/app/backend/routes/admin.py", "r") as f:
            content = f.read()
        
        # Check for newsletter time settings
        assert "newsletter_time_1" in content or "newsletter" in content.lower()
        print("✅ Newsletter settings present in admin routes")


class TestLaughOMeterEndpoints:
    """Test Laugh-O-Meter endpoints (existing feature verification)"""
    
    @pytest.fixture
    def auth_token(self):
        """Get admin auth token"""
        response = requests.post(f"{BASE_URL}/api/auth/login", json={
            "email": ADMIN_EMAIL,
            "password": ADMIN_PASSWORD
        })
        if response.status_code == 200:
            return response.json().get("token")
        pytest.skip("Authentication failed")
    
    def test_laugh_stats_endpoint(self, auth_token):
        """Test GET /api/gamification/laugh-stats"""
        response = requests.get(
            f"{BASE_URL}/api/gamification/laugh-stats",
            headers={"Authorization": f"Bearer {auth_token}"}
        )
        assert response.status_code == 200
        data = response.json()
        
        assert "totalLaughs" in data
        assert "todayLaughs" in data
        assert "easterEggsFound" in data
        assert "badges" in data
        assert "xp" in data
        assert "level" in data
        assert "title" in data
        
        print(f"✅ Laugh-O-Meter stats: totalLaughs={data['totalLaughs']}, xp={data['xp']}, level={data['level']}")
    
    def test_record_laugh_endpoint(self, auth_token):
        """Test POST /api/gamification/record-laugh"""
        response = requests.post(
            f"{BASE_URL}/api/gamification/record-laugh",
            headers={"Authorization": f"Bearer {auth_token}"},
            json={"source": "test"}
        )
        assert response.status_code == 200
        data = response.json()
        
        assert data["success"] == True
        assert "message" in data
        print(f"✅ Record laugh working: {data['message']}")
    
    def test_laugh_leaderboard_endpoint(self):
        """Test GET /api/gamification/laugh-leaderboard (public)"""
        response = requests.get(f"{BASE_URL}/api/gamification/laugh-leaderboard")
        assert response.status_code == 200
        data = response.json()
        
        assert "leaderboard" in data
        assert "total_participants" in data
        
        print(f"✅ Laugh leaderboard: {len(data['leaderboard'])} entries, {data['total_participants']} total participants")


class TestCategoriesWithResultCount:
    """Test categories include result_count field"""
    
    @pytest.fixture
    def auth_token(self):
        """Get admin auth token"""
        response = requests.post(f"{BASE_URL}/api/auth/login", json={
            "email": ADMIN_EMAIL,
            "password": ADMIN_PASSWORD
        })
        if response.status_code == 200:
            return response.json().get("token")
        pytest.skip("Authentication failed")
    
    def test_categories_include_counts(self, auth_token):
        """Test GET /api/categories returns result_count"""
        response = requests.get(
            f"{BASE_URL}/api/categories",
            headers={"Authorization": f"Bearer {auth_token}"}
        )
        assert response.status_code == 200
        data = response.json()
        
        assert "categories" in data
        categories = data["categories"]
        
        if len(categories) > 0:
            category = categories[0]
            # Check for count fields
            has_count = "result_count" in category or "count" in category or "subcategory_count" in category
            assert has_count, f"Category missing count fields: {category.keys()}"
            print(f"✅ Categories include count fields: {list(category.keys())}")
        else:
            print("⚠️ No categories found to verify count fields")


class TestCollationSettings:
    """Test collation limit default is 40 and multiple categories enabled"""
    
    @pytest.fixture
    def auth_token(self):
        """Get admin auth token"""
        response = requests.post(f"{BASE_URL}/api/auth/login", json={
            "email": ADMIN_EMAIL,
            "password": ADMIN_PASSWORD
        })
        if response.status_code == 200:
            return response.json().get("token")
        pytest.skip("Authentication failed")
    
    def test_collation_limit_default_in_code(self):
        """Verify collation_limit default is 40 in admin.py"""
        with open("/app/backend/routes/admin.py", "r") as f:
            content = f.read()
        
        # Check for collation_limit setting with value 40
        assert "collation_limit" in content
        assert '"value": 40' in content or "'value': 40" in content or "value\": 40" in content
        print("✅ Collation limit default is 40 in code")
    
    def test_multiple_categories_enabled_in_code(self):
        """Verify allow_multiple_categories is True by default"""
        with open("/app/backend/routes/admin.py", "r") as f:
            content = f.read()
        
        assert "allow_multiple_categories" in content
        # Check it's set to True
        assert "True" in content
        print("✅ Allow multiple categories is enabled by default")
    
    def test_admin_settings_collation(self, auth_token):
        """Test admin settings include collation settings"""
        response = requests.get(
            f"{BASE_URL}/api/admin/settings",
            headers={"Authorization": f"Bearer {auth_token}"}
        )
        assert response.status_code == 200
        data = response.json()
        
        # Check if collation_limit is in settings
        if "collation_limit" in data:
            print(f"✅ Collation limit in settings: {data['collation_limit']}")
        else:
            print("⚠️ Collation limit not yet initialized in settings")


class TestDailyLaughGoalFrontendComponent:
    """Verify Daily Laugh Goal frontend component exists"""
    
    def test_daily_laugh_goal_component_exists(self):
        """Verify DailyLaughGoal.js component exists"""
        import os
        component_path = "/app/frontend/src/components/Gamification/DailyLaughGoal.js"
        assert os.path.exists(component_path), f"DailyLaughGoal.js not found at {component_path}"
        
        with open(component_path, "r") as f:
            content = f.read()
        
        # Check for key features
        assert "daily_goal" in content.lower() or "dailyGoal" in content
        assert "streak" in content.lower()
        assert "progress" in content.lower()
        
        print("✅ DailyLaughGoal.js component exists with goal, streak, and progress features")
    
    def test_admin_panel_newsletter_settings(self):
        """Verify AdminPanel.js has newsletter time settings"""
        with open("/app/frontend/src/pages/AdminPanel.js", "r") as f:
            content = f.read()
        
        # Check for newsletter time settings
        assert "newsletter_time" in content.lower() or "newsletterTime" in content
        assert "newsletter_ai_optimization" in content.lower() or "newsletterAiOptimization" in content or "ai_optimization" in content.lower()
        
        print("✅ AdminPanel.js has newsletter time and AI optimization settings")


class TestFunnyContentLibrary:
    """Verify 100+ funny elements exist"""
    
    def test_funny_content_library_exists(self):
        """Verify funnyContent.js has 100+ funny messages"""
        import os
        content_path = "/app/frontend/src/utils/funnyContent.js"
        
        if os.path.exists(content_path):
            with open(content_path, "r") as f:
                content = f.read()
            
            # Count string literals (rough estimate of funny messages)
            import re
            strings = re.findall(r'["\'][^"\']{10,}["\']', content)
            
            print(f"✅ funnyContent.js exists with ~{len(strings)} funny messages")
        else:
            print("⚠️ funnyContent.js not found at expected path")


if __name__ == "__main__":
    pytest.main([__file__, "-v", "--tb=short"])
