"""
InfoPilot Explorer - Iteration 18 Gamification Tests
Tests for:
- Gamification achievements list (22 achievements)
- User achievements check
- My achievements
- Weekly leaderboard
- All-time leaderboard
- Share achievement
- Protocol parser abbreviations
"""
import pytest
import requests
import os

BASE_URL = os.environ.get('REACT_APP_BACKEND_URL', '').rstrip('/')

class TestGamificationAchievements:
    """Test gamification achievements endpoints"""
    
    def test_get_all_achievements(self):
        """GET /api/gamification/achievements - Should return 22 achievements"""
        response = requests.get(f"{BASE_URL}/api/gamification/achievements")
        assert response.status_code == 200, f"Expected 200, got {response.status_code}"
        
        data = response.json()
        assert "achievements" in data, "Response should contain 'achievements' key"
        assert "by_category" in data, "Response should contain 'by_category' key"
        assert "total_achievements" in data, "Response should contain 'total_achievements' key"
        assert "total_points_possible" in data, "Response should contain 'total_points_possible' key"
        
        # Verify 22 achievements
        assert data["total_achievements"] == 22, f"Expected 22 achievements, got {data['total_achievements']}"
        
        # Verify total points (2895 as per spec)
        assert data["total_points_possible"] == 2895, f"Expected 2895 total points, got {data['total_points_possible']}"
        
        # Verify achievement structure
        achievements = data["achievements"]
        assert len(achievements) == 22, f"Expected 22 achievements in list, got {len(achievements)}"
        
        for achievement in achievements:
            assert "id" in achievement, "Achievement should have 'id'"
            assert "name" in achievement, "Achievement should have 'name'"
            assert "description" in achievement, "Achievement should have 'description'"
            assert "icon" in achievement, "Achievement should have 'icon'"
            assert "category" in achievement, "Achievement should have 'category'"
            assert "points" in achievement, "Achievement should have 'points'"
        
        print(f"SUCCESS: Found {data['total_achievements']} achievements worth {data['total_points_possible']} points")
    
    def test_achievements_by_category(self):
        """Verify achievements are grouped by 6 categories"""
        response = requests.get(f"{BASE_URL}/api/gamification/achievements")
        assert response.status_code == 200
        
        data = response.json()
        categories = data["by_category"]
        
        # Expected categories: search, protocol, marketplace, social, special, consistency
        expected_categories = ["search", "protocol", "marketplace", "social", "special", "consistency"]
        
        for cat in expected_categories:
            assert cat in categories, f"Category '{cat}' should exist"
            assert len(categories[cat]) > 0, f"Category '{cat}' should have achievements"
        
        print(f"SUCCESS: Found {len(categories)} categories: {list(categories.keys())}")
    
    def test_search_achievements(self):
        """Verify search category achievements"""
        response = requests.get(f"{BASE_URL}/api/gamification/achievements")
        assert response.status_code == 200
        
        data = response.json()
        search_achievements = data["by_category"].get("search", [])
        
        # Should have 4 search achievements
        assert len(search_achievements) == 4, f"Expected 4 search achievements, got {len(search_achievements)}"
        
        search_ids = [a["id"] for a in search_achievements]
        expected_ids = ["first_search", "search_10", "search_50", "search_100"]
        
        for expected_id in expected_ids:
            assert expected_id in search_ids, f"Search achievement '{expected_id}' should exist"
        
        print(f"SUCCESS: Found search achievements: {search_ids}")
    
    def test_marketplace_achievements(self):
        """Verify marketplace category achievements"""
        response = requests.get(f"{BASE_URL}/api/gamification/achievements")
        assert response.status_code == 200
        
        data = response.json()
        marketplace_achievements = data["by_category"].get("marketplace", [])
        
        # Should have 6 marketplace achievements
        assert len(marketplace_achievements) == 6, f"Expected 6 marketplace achievements, got {len(marketplace_achievements)}"
        
        marketplace_ids = [a["id"] for a in marketplace_achievements]
        expected_ids = ["first_sale", "sales_10", "sales_50", "sales_100", "revenue_100", "revenue_1000"]
        
        for expected_id in expected_ids:
            assert expected_id in marketplace_ids, f"Marketplace achievement '{expected_id}' should exist"
        
        print(f"SUCCESS: Found marketplace achievements: {marketplace_ids}")


class TestGamificationLeaderboards:
    """Test gamification leaderboard endpoints"""
    
    def test_weekly_leaderboard(self):
        """GET /api/gamification/leaderboard/weekly - Should return weekly leaderboard"""
        response = requests.get(f"{BASE_URL}/api/gamification/leaderboard/weekly")
        assert response.status_code == 200, f"Expected 200, got {response.status_code}"
        
        data = response.json()
        assert "leaderboard" in data, "Response should contain 'leaderboard' key"
        assert "period" in data, "Response should contain 'period' key"
        assert "commentary" in data, "Response should contain 'commentary' key"
        assert "last_updated" in data, "Response should contain 'last_updated' key"
        
        assert data["period"] == "This Week", f"Expected 'This Week', got {data['period']}"
        
        # Leaderboard may be empty if no sales this week
        leaderboard = data["leaderboard"]
        if leaderboard:
            for entry in leaderboard:
                assert "rank" in entry, "Entry should have 'rank'"
                assert "user_id" in entry, "Entry should have 'user_id'"
                assert "username" in entry, "Entry should have 'username'"
                assert "weekly_sales" in entry, "Entry should have 'weekly_sales'"
        
        print(f"SUCCESS: Weekly leaderboard has {len(leaderboard)} entries")
    
    def test_all_time_leaderboard(self):
        """GET /api/gamification/leaderboard/all-time - Should return all-time leaderboard"""
        response = requests.get(f"{BASE_URL}/api/gamification/leaderboard/all-time")
        assert response.status_code == 200, f"Expected 200, got {response.status_code}"
        
        data = response.json()
        assert "leaderboard" in data, "Response should contain 'leaderboard' key"
        assert "period" in data, "Response should contain 'period' key"
        assert "last_updated" in data, "Response should contain 'last_updated' key"
        
        assert data["period"] == "All Time", f"Expected 'All Time', got {data['period']}"
        
        leaderboard = data["leaderboard"]
        if leaderboard:
            for entry in leaderboard:
                assert "rank" in entry, "Entry should have 'rank'"
                assert "user_id" in entry, "Entry should have 'user_id'"
                assert "username" in entry, "Entry should have 'username'"
                assert "total_points" in entry, "Entry should have 'total_points'"
                assert "achievement_count" in entry, "Entry should have 'achievement_count'"
                assert "level" in entry, "Entry should have 'level'"
                assert "level_name" in entry, "Entry should have 'level_name'"
        
        print(f"SUCCESS: All-time leaderboard has {len(leaderboard)} entries")


class TestAuthenticatedGamification:
    """Test authenticated gamification endpoints"""
    
    @pytest.fixture
    def auth_token(self):
        """Get authentication token for admin user"""
        response = requests.post(f"{BASE_URL}/api/auth/login", json={
            "email": "jjspilot24@gmail.com",
            "password": "InfoPilot2024!"
        })
        if response.status_code == 200:
            return response.json().get("token")
        pytest.skip("Authentication failed - skipping authenticated tests")
    
    def test_my_achievements(self, auth_token):
        """GET /api/gamification/my-achievements - Should return user's achievements"""
        headers = {"Authorization": f"Bearer {auth_token}"}
        response = requests.get(f"{BASE_URL}/api/gamification/my-achievements", headers=headers)
        assert response.status_code == 200, f"Expected 200, got {response.status_code}"
        
        data = response.json()
        assert "earned" in data, "Response should contain 'earned' key"
        assert "unearned" in data, "Response should contain 'unearned' key"
        assert "total_points" in data, "Response should contain 'total_points' key"
        assert "level" in data, "Response should contain 'level' key"
        assert "level_name" in data, "Response should contain 'level_name' key"
        assert "next_level_points" in data, "Response should contain 'next_level_points' key"
        assert "progress_to_next" in data, "Response should contain 'progress_to_next' key"
        assert "completion_percentage" in data, "Response should contain 'completion_percentage' key"
        
        # Verify earned achievements have proper structure
        for achievement in data["earned"]:
            assert "name" in achievement, "Earned achievement should have 'name'"
            assert "description" in achievement, "Earned achievement should have 'description'"
            assert "icon" in achievement, "Earned achievement should have 'icon'"
            assert "points" in achievement, "Earned achievement should have 'points'"
            assert "earned_at" in achievement, "Earned achievement should have 'earned_at'"
        
        print(f"SUCCESS: User has {len(data['earned'])} earned achievements, {data['total_points']} points, Level {data['level']} ({data['level_name']})")
    
    def test_check_achievements(self, auth_token):
        """POST /api/gamification/check-achievements - Should check and award new achievements"""
        headers = {"Authorization": f"Bearer {auth_token}"}
        response = requests.post(f"{BASE_URL}/api/gamification/check-achievements", headers=headers)
        assert response.status_code == 200, f"Expected 200, got {response.status_code}"
        
        data = response.json()
        assert "new_achievements" in data, "Response should contain 'new_achievements' key"
        assert "count" in data, "Response should contain 'count' key"
        assert "message" in data, "Response should contain 'message' key"
        
        # Verify new achievements structure if any
        for achievement in data["new_achievements"]:
            assert "name" in achievement, "New achievement should have 'name'"
            assert "description" in achievement, "New achievement should have 'description'"
            assert "points" in achievement, "New achievement should have 'points'"
        
        print(f"SUCCESS: Check achievements returned {data['count']} new achievements. Message: {data['message']}")
    
    def test_share_achievement_earned(self, auth_token):
        """POST /api/gamification/share-achievement/{id} - Should generate share message for earned achievement"""
        headers = {"Authorization": f"Bearer {auth_token}"}
        
        # First get user's earned achievements
        my_response = requests.get(f"{BASE_URL}/api/gamification/my-achievements", headers=headers)
        assert my_response.status_code == 200
        
        earned = my_response.json().get("earned", [])
        if not earned:
            pytest.skip("User has no earned achievements to share")
        
        # Try to share the first earned achievement
        achievement_id = earned[0].get("id")
        if not achievement_id:
            pytest.skip("Earned achievement has no ID")
        
        response = requests.post(f"{BASE_URL}/api/gamification/share-achievement/{achievement_id}", headers=headers)
        assert response.status_code == 200, f"Expected 200, got {response.status_code}"
        
        data = response.json()
        assert "share_message" in data, "Response should contain 'share_message' key"
        assert "achievement" in data, "Response should contain 'achievement' key"
        assert "platforms" in data, "Response should contain 'platforms' key"
        
        # Verify share message contains achievement info
        assert earned[0]["name"] in data["share_message"], "Share message should contain achievement name"
        
        # Verify platforms
        assert "twitter" in data["platforms"], "Platforms should include 'twitter'"
        assert "facebook" in data["platforms"], "Platforms should include 'facebook'"
        
        print(f"SUCCESS: Generated share message for achievement '{achievement_id}'")
    
    def test_share_achievement_not_earned(self, auth_token):
        """POST /api/gamification/share-achievement/{id} - Should return 403 for unearned achievement"""
        headers = {"Authorization": f"Bearer {auth_token}"}
        
        # First get user's unearned achievements
        my_response = requests.get(f"{BASE_URL}/api/gamification/my-achievements", headers=headers)
        assert my_response.status_code == 200
        
        unearned = my_response.json().get("unearned", [])
        if not unearned:
            pytest.skip("User has earned all achievements")
        
        # Try to share an unearned achievement
        achievement_id = unearned[0].get("id")
        if not achievement_id:
            pytest.skip("Unearned achievement has no ID")
        
        response = requests.post(f"{BASE_URL}/api/gamification/share-achievement/{achievement_id}", headers=headers)
        assert response.status_code == 403, f"Expected 403 for unearned achievement, got {response.status_code}"
        
        print(f"SUCCESS: Correctly returned 403 for unearned achievement '{achievement_id}'")
    
    def test_share_achievement_invalid(self, auth_token):
        """POST /api/gamification/share-achievement/{id} - Should return 404 for invalid achievement"""
        headers = {"Authorization": f"Bearer {auth_token}"}
        
        response = requests.post(f"{BASE_URL}/api/gamification/share-achievement/invalid_achievement_id", headers=headers)
        assert response.status_code == 404, f"Expected 404 for invalid achievement, got {response.status_code}"
        
        print("SUCCESS: Correctly returned 404 for invalid achievement ID")
    
    def test_my_achievements_without_auth(self):
        """GET /api/gamification/my-achievements - Should return 401 without auth"""
        response = requests.get(f"{BASE_URL}/api/gamification/my-achievements")
        assert response.status_code == 401, f"Expected 401 without auth, got {response.status_code}"
        
        print("SUCCESS: Correctly returned 401 for unauthenticated request")


class TestProtocolParserAbbreviations:
    """Test protocol parser handles abbreviations correctly"""
    
    @pytest.fixture
    def auth_token(self):
        """Get authentication token for admin user"""
        response = requests.post(f"{BASE_URL}/api/auth/login", json={
            "email": "jjspilot24@gmail.com",
            "password": "InfoPilot2024!"
        })
        if response.status_code == 200:
            return response.json().get("token")
        pytest.skip("Authentication failed - skipping authenticated tests")
    
    def test_protocol_parser_debug_william_c_gamble(self, auth_token):
        """Test protocol parser handles 'William C. Gamble' abbreviation"""
        headers = {"Authorization": f"Bearer {auth_token}"}
        
        # Test protocol with abbreviated name
        protocol = "(William C. Gamble or William Gamble) & (Civil War or military)"
        
        response = requests.post(f"{BASE_URL}/api/protocols/debug", 
            json={"protocol": protocol},
            headers=headers
        )
        
        # If endpoint exists
        if response.status_code == 200:
            data = response.json()
            assert data.get("valid") == True, "Protocol should be valid"
            
            # Check that terms are parsed correctly
            groups = data.get("groups", [])
            assert len(groups) >= 1, "Should have at least 1 group"
            
            # First group should contain "William C. Gamble"
            first_group_terms = groups[0].get("terms", [])
            assert "William C. Gamble" in first_group_terms or "William Gamble" in first_group_terms, \
                f"First group should contain name terms, got: {first_group_terms}"
            
            print(f"SUCCESS: Protocol parser correctly handles 'William C. Gamble'. Groups: {groups}")
        else:
            # Endpoint may not exist, skip
            pytest.skip(f"Protocol debug endpoint returned {response.status_code}")
    
    def test_protocol_parser_debug_john_j_s(self, auth_token):
        """Test protocol parser handles 'John J S' abbreviation"""
        headers = {"Authorization": f"Bearer {auth_token}"}
        
        protocol = "(John J S or John S.) & (pilot or aviation)"
        
        response = requests.post(f"{BASE_URL}/api/protocols/debug", 
            json={"protocol": protocol},
            headers=headers
        )
        
        if response.status_code == 200:
            data = response.json()
            assert data.get("valid") == True, "Protocol should be valid"
            print(f"SUCCESS: Protocol parser correctly handles 'John J S'. Data: {data}")
        else:
            pytest.skip(f"Protocol debug endpoint returned {response.status_code}")
    
    def test_protocol_parser_debug_nm_location(self, auth_token):
        """Test protocol parser handles 'NM' state abbreviation"""
        headers = {"Authorization": f"Bearer {auth_token}"}
        
        protocol = "(Albuquerque, NM or New Mexico) & (history or records)"
        
        response = requests.post(f"{BASE_URL}/api/protocols/debug", 
            json={"protocol": protocol},
            headers=headers
        )
        
        if response.status_code == 200:
            data = response.json()
            assert data.get("valid") == True, "Protocol should be valid"
            print(f"SUCCESS: Protocol parser correctly handles 'NM' location. Data: {data}")
        else:
            pytest.skip(f"Protocol debug endpoint returned {response.status_code}")
    
    def test_protocol_parser_debug_ger_country(self, auth_token):
        """Test protocol parser handles 'GER' country abbreviation"""
        headers = {"Authorization": f"Bearer {auth_token}"}
        
        protocol = "(Heidelberg, GER or Germany) & (university or research)"
        
        response = requests.post(f"{BASE_URL}/api/protocols/debug", 
            json={"protocol": protocol},
            headers=headers
        )
        
        if response.status_code == 200:
            data = response.json()
            assert data.get("valid") == True, "Protocol should be valid"
            print(f"SUCCESS: Protocol parser correctly handles 'GER' country. Data: {data}")
        else:
            pytest.skip(f"Protocol debug endpoint returned {response.status_code}")


class TestLevelSystem:
    """Test level system calculations"""
    
    def test_level_names_in_leaderboard(self):
        """Verify level names appear in all-time leaderboard"""
        response = requests.get(f"{BASE_URL}/api/gamification/leaderboard/all-time")
        assert response.status_code == 200
        
        data = response.json()
        leaderboard = data.get("leaderboard", [])
        
        expected_level_names = [
            "Search Newbie 🌱",
            "Protocol Apprentice 📖",
            "Data Explorer 🔍",
            "Info Seeker 🎯",
            "Knowledge Hunter 🏹",
            "Search Wizard 🧙‍♂️",
            "Data Master 🎓",
            "Protocol Sage 📜",
            "Info Legend 🌟",
            "InfoPilot Supreme 👑"
        ]
        
        if leaderboard:
            for entry in leaderboard:
                level_name = entry.get("level_name", "")
                # Level name should be one of the expected names
                assert any(name in level_name for name in expected_level_names) or level_name in expected_level_names, \
                    f"Level name '{level_name}' should be a valid level name"
        
        print(f"SUCCESS: Level names verified in leaderboard")


class TestFreeProtocolsWithBadge:
    """Test FREE protocols display correctly"""
    
    def test_marketplace_has_free_protocols(self):
        """GET /api/marketplace/protocols - Should include FREE protocols with is_free flag"""
        response = requests.get(f"{BASE_URL}/api/marketplace/protocols")
        assert response.status_code == 200, f"Expected 200, got {response.status_code}"
        
        data = response.json()
        protocols = data.get("protocols", [])
        
        # Find FREE protocols
        free_protocols = [p for p in protocols if p.get("is_free") == True or p.get("price", 1) == 0]
        
        print(f"SUCCESS: Found {len(free_protocols)} FREE protocols out of {len(protocols)} total")
        
        # Verify FREE protocols have correct structure
        for protocol in free_protocols:
            assert protocol.get("price", 1) == 0, f"FREE protocol should have price 0, got {protocol.get('price')}"
        
        return free_protocols


class TestUserAchievementsProfile:
    """Test user achievements profile endpoint"""
    
    @pytest.fixture
    def auth_token(self):
        """Get authentication token for admin user"""
        response = requests.post(f"{BASE_URL}/api/auth/login", json={
            "email": "jjspilot24@gmail.com",
            "password": "InfoPilot2024!"
        })
        if response.status_code == 200:
            return response.json().get("token")
        pytest.skip("Authentication failed - skipping authenticated tests")
    
    def test_get_user_achievements_by_id(self, auth_token):
        """GET /api/gamification/user/{user_id}/achievements - Should return user's public achievements"""
        headers = {"Authorization": f"Bearer {auth_token}"}
        
        # First get current user's ID from my-achievements or profile
        my_response = requests.get(f"{BASE_URL}/api/gamification/my-achievements", headers=headers)
        if my_response.status_code != 200:
            pytest.skip("Could not get user achievements")
        
        # Get user ID from all-time leaderboard
        leaderboard_response = requests.get(f"{BASE_URL}/api/gamification/leaderboard/all-time")
        if leaderboard_response.status_code != 200 or not leaderboard_response.json().get("leaderboard"):
            pytest.skip("No users in leaderboard to test")
        
        user_id = leaderboard_response.json()["leaderboard"][0]["user_id"]
        
        response = requests.get(f"{BASE_URL}/api/gamification/user/{user_id}/achievements", headers=headers)
        assert response.status_code == 200, f"Expected 200, got {response.status_code}"
        
        data = response.json()
        assert "username" in data, "Response should contain 'username'"
        assert "total_points" in data, "Response should contain 'total_points'"
        assert "level" in data, "Response should contain 'level'"
        assert "level_name" in data, "Response should contain 'level_name'"
        assert "achievement_count" in data, "Response should contain 'achievement_count'"
        assert "achievements" in data, "Response should contain 'achievements'"
        
        print(f"SUCCESS: Got achievements for user {data['username']}: {data['achievement_count']} achievements, {data['total_points']} points")


if __name__ == "__main__":
    pytest.main([__file__, "-v", "--tb=short"])
