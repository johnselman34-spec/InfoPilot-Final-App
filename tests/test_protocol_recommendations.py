"""
Protocol Recommendations Feature Tests - InfoPilot Explorer
Tests for the new protocol recommendation feature that allows users to suggest changes to public protocols.

Test Flow:
1. User A creates a public category/protocol
2. User B submits a recommendation for that public category
3. User A views and manages recommendations (accept/reject/delete)
"""

import pytest
import requests
import os
import uuid

BASE_URL = os.environ.get('REACT_APP_BACKEND_URL', '').rstrip('/')

# Test credentials
USER_1 = {"email": "john@infojet.com", "password": "password123"}  # Admin user (owner)
USER_2 = {"email": "testuser@example.com", "password": "password123"}  # Regular user (recommender)


class TestProtocolRecommendations:
    """Protocol Recommendations API Tests"""
    
    @pytest.fixture(autouse=True)
    def setup(self):
        """Setup test session and authenticate users"""
        self.session = requests.Session()
        self.session.headers.update({"Content-Type": "application/json"})
        
        # Login as User 1 (admin/owner)
        self.user1_token = self._login(USER_1["email"], USER_1["password"])
        
        # Login as User 2 (recommender)
        self.user2_token = self._login(USER_2["email"], USER_2["password"])
        
        # Store created resources for cleanup
        self.created_categories = []
        self.created_recommendations = []
        
        yield
        
        # Cleanup
        self._cleanup()
    
    def _login(self, email, password):
        """Login and return token"""
        response = self.session.post(f"{BASE_URL}/api/auth/login", json={
            "email": email,
            "password": password
        })
        if response.status_code == 200:
            return response.json().get("access_token")
        return None
    
    def _get_headers(self, token):
        """Get headers with auth token"""
        return {
            "Content-Type": "application/json",
            "Authorization": f"Bearer {token}"
        }
    
    def _cleanup(self):
        """Cleanup test data"""
        # Delete created categories
        for cat_id in self.created_categories:
            try:
                self.session.delete(
                    f"{BASE_URL}/api/categories/{cat_id}",
                    headers=self._get_headers(self.user1_token)
                )
            except:
                pass
        
        # Delete created recommendations
        for rec_id in self.created_recommendations:
            try:
                self.session.delete(
                    f"{BASE_URL}/api/recommendations/{rec_id}",
                    headers=self._get_headers(self.user1_token)
                )
            except:
                pass
    
    # ============================================
    # AUTHENTICATION TESTS
    # ============================================
    
    def test_01_login_user1_admin(self):
        """Test login for User 1 (admin/owner)"""
        response = self.session.post(f"{BASE_URL}/api/auth/login", json=USER_1)
        assert response.status_code == 200, f"Login failed: {response.text}"
        data = response.json()
        assert "access_token" in data
        assert data["user"]["email"] == USER_1["email"]
        print(f"✓ User 1 (admin) login successful: {data['user']['username']}")
    
    def test_02_login_user2_regular(self):
        """Test login for User 2 (regular user)"""
        response = self.session.post(f"{BASE_URL}/api/auth/login", json=USER_2)
        assert response.status_code == 200, f"Login failed: {response.text}"
        data = response.json()
        assert "access_token" in data
        assert data["user"]["email"] == USER_2["email"]
        print(f"✓ User 2 (regular) login successful: {data['user']['username']}")
    
    # ============================================
    # CATEGORY CREATION TESTS
    # ============================================
    
    def test_03_create_public_category_for_recommendations(self):
        """Create a public category that can receive recommendations"""
        unique_name = f"TEST_RecommendationTarget_{uuid.uuid4().hex[:8]}"
        response = self.session.post(
            f"{BASE_URL}/api/categories",
            headers=self._get_headers(self.user1_token),
            json={
                "name": unique_name,
                "protocol": {"protocol_string": "(test or sample) & (data)"},
                "is_public": True
            }
        )
        assert response.status_code == 200, f"Create category failed: {response.text}"
        data = response.json()
        assert data["name"] == unique_name
        assert data["is_public"] == True
        self.created_categories.append(data["id"])
        print(f"✓ Created public category: {unique_name} (ID: {data['id']})")
        return data
    
    def test_04_create_private_category(self):
        """Create a private category (should not accept recommendations)"""
        unique_name = f"TEST_PrivateCategory_{uuid.uuid4().hex[:8]}"
        response = self.session.post(
            f"{BASE_URL}/api/categories",
            headers=self._get_headers(self.user1_token),
            json={
                "name": unique_name,
                "protocol": {"protocol_string": "(private or secret)"},
                "is_public": False
            }
        )
        assert response.status_code == 200, f"Create private category failed: {response.text}"
        data = response.json()
        assert data["is_public"] == False
        self.created_categories.append(data["id"])
        print(f"✓ Created private category: {unique_name}")
        return data
    
    # ============================================
    # SUBMIT RECOMMENDATION TESTS
    # ============================================
    
    def test_05_submit_recommendation_success(self):
        """User 2 submits a recommendation for User 1's public category"""
        # First create a public category as User 1
        unique_name = f"TEST_RecTarget_{uuid.uuid4().hex[:8]}"
        cat_response = self.session.post(
            f"{BASE_URL}/api/categories",
            headers=self._get_headers(self.user1_token),
            json={
                "name": unique_name,
                "protocol": {"protocol_string": "(original or test)"},
                "is_public": True
            }
        )
        assert cat_response.status_code == 200
        category = cat_response.json()
        self.created_categories.append(category["id"])
        
        # User 2 submits a recommendation
        rec_response = self.session.post(
            f"{BASE_URL}/api/categories/{category['id']}/recommendations",
            headers=self._get_headers(self.user2_token),
            json={
                "original_protocol": "(original or test)",
                "suggested_protocol": "(improved or better or test)",
                "reason": "Adding more keywords for better search coverage"
            }
        )
        assert rec_response.status_code == 200, f"Submit recommendation failed: {rec_response.text}"
        data = rec_response.json()
        assert "recommendation" in data
        assert data["recommendation"]["status"] == "pending"
        self.created_recommendations.append(data["recommendation"]["id"])
        print(f"✓ Recommendation submitted successfully (ID: {data['recommendation']['id']})")
        return data["recommendation"]
    
    def test_06_cannot_recommend_own_protocol(self):
        """User cannot recommend changes to their own protocol"""
        # Create a category as User 1
        unique_name = f"TEST_OwnCategory_{uuid.uuid4().hex[:8]}"
        cat_response = self.session.post(
            f"{BASE_URL}/api/categories",
            headers=self._get_headers(self.user1_token),
            json={
                "name": unique_name,
                "protocol": {"protocol_string": "(my or own)"},
                "is_public": True
            }
        )
        assert cat_response.status_code == 200
        category = cat_response.json()
        self.created_categories.append(category["id"])
        
        # User 1 tries to recommend on their own category - should fail with 400
        rec_response = self.session.post(
            f"{BASE_URL}/api/categories/{category['id']}/recommendations",
            headers=self._get_headers(self.user1_token),
            json={
                "original_protocol": "(my or own)",
                "suggested_protocol": "(my or own or updated)",
                "reason": "Self improvement"
            }
        )
        assert rec_response.status_code == 400, f"Expected 400, got {rec_response.status_code}"
        assert "own protocol" in rec_response.json().get("detail", "").lower()
        print("✓ Correctly rejected self-recommendation with 400")
    
    def test_07_cannot_recommend_private_protocol(self):
        """User cannot recommend changes to a private protocol"""
        # Create a private category as User 1
        unique_name = f"TEST_PrivateRec_{uuid.uuid4().hex[:8]}"
        cat_response = self.session.post(
            f"{BASE_URL}/api/categories",
            headers=self._get_headers(self.user1_token),
            json={
                "name": unique_name,
                "protocol": {"protocol_string": "(private or hidden)"},
                "is_public": False
            }
        )
        assert cat_response.status_code == 200
        category = cat_response.json()
        self.created_categories.append(category["id"])
        
        # User 2 tries to recommend on private category - should fail with 403
        rec_response = self.session.post(
            f"{BASE_URL}/api/categories/{category['id']}/recommendations",
            headers=self._get_headers(self.user2_token),
            json={
                "original_protocol": "(private or hidden)",
                "suggested_protocol": "(private or hidden or exposed)",
                "reason": "Want to add more keywords"
            }
        )
        assert rec_response.status_code == 403, f"Expected 403, got {rec_response.status_code}"
        assert "private" in rec_response.json().get("detail", "").lower()
        print("✓ Correctly rejected recommendation on private protocol with 403")
    
    def test_08_recommendation_on_nonexistent_category(self):
        """Recommendation on non-existent category returns 404"""
        fake_id = str(uuid.uuid4())
        rec_response = self.session.post(
            f"{BASE_URL}/api/categories/{fake_id}/recommendations",
            headers=self._get_headers(self.user2_token),
            json={
                "original_protocol": "(test)",
                "suggested_protocol": "(test or new)",
                "reason": "Testing"
            }
        )
        assert rec_response.status_code == 404
        print("✓ Correctly returned 404 for non-existent category")
    
    # ============================================
    # GET RECOMMENDATIONS TESTS
    # ============================================
    
    def test_09_get_category_recommendations_owner_only(self):
        """Only owner can view recommendations for their category"""
        # Create category and recommendation
        unique_name = f"TEST_ViewRecs_{uuid.uuid4().hex[:8]}"
        cat_response = self.session.post(
            f"{BASE_URL}/api/categories",
            headers=self._get_headers(self.user1_token),
            json={
                "name": unique_name,
                "protocol": {"protocol_string": "(view or test)"},
                "is_public": True
            }
        )
        category = cat_response.json()
        self.created_categories.append(category["id"])
        
        # User 2 submits recommendation
        self.session.post(
            f"{BASE_URL}/api/categories/{category['id']}/recommendations",
            headers=self._get_headers(self.user2_token),
            json={
                "original_protocol": "(view or test)",
                "suggested_protocol": "(view or test or improved)",
                "reason": "Better coverage"
            }
        )
        
        # User 1 (owner) can view recommendations
        owner_response = self.session.get(
            f"{BASE_URL}/api/categories/{category['id']}/recommendations",
            headers=self._get_headers(self.user1_token)
        )
        assert owner_response.status_code == 200
        data = owner_response.json()
        assert "recommendations" in data
        assert len(data["recommendations"]) >= 1
        print(f"✓ Owner can view recommendations (count: {data['count']})")
        
        # User 2 (non-owner) cannot view recommendations
        non_owner_response = self.session.get(
            f"{BASE_URL}/api/categories/{category['id']}/recommendations",
            headers=self._get_headers(self.user2_token)
        )
        assert non_owner_response.status_code == 403
        print("✓ Non-owner correctly denied access with 403")
    
    def test_10_get_my_protocol_recommendations(self):
        """Get all recommendations across user's protocols"""
        # Create category and recommendation
        unique_name = f"TEST_MyRecs_{uuid.uuid4().hex[:8]}"
        cat_response = self.session.post(
            f"{BASE_URL}/api/categories",
            headers=self._get_headers(self.user1_token),
            json={
                "name": unique_name,
                "protocol": {"protocol_string": "(my or recs)"},
                "is_public": True
            }
        )
        category = cat_response.json()
        self.created_categories.append(category["id"])
        
        # User 2 submits recommendation
        rec_response = self.session.post(
            f"{BASE_URL}/api/categories/{category['id']}/recommendations",
            headers=self._get_headers(self.user2_token),
            json={
                "original_protocol": "(my or recs)",
                "suggested_protocol": "(my or recs or all)",
                "reason": "Adding keywords"
            }
        )
        rec_data = rec_response.json()
        if "recommendation" in rec_data:
            self.created_recommendations.append(rec_data["recommendation"]["id"])
        
        # User 1 gets all recommendations for their protocols
        response = self.session.get(
            f"{BASE_URL}/api/recommendations/my-protocols",
            headers=self._get_headers(self.user1_token)
        )
        assert response.status_code == 200
        data = response.json()
        assert "total_count" in data
        assert "pending_count" in data
        assert "by_category" in data
        print(f"✓ Got my-protocols recommendations (total: {data['total_count']}, pending: {data['pending_count']})")
    
    def test_11_get_recommendation_count(self):
        """Get recommendation count for a category"""
        # Create category and recommendation
        unique_name = f"TEST_CountRecs_{uuid.uuid4().hex[:8]}"
        cat_response = self.session.post(
            f"{BASE_URL}/api/categories",
            headers=self._get_headers(self.user1_token),
            json={
                "name": unique_name,
                "protocol": {"protocol_string": "(count or test)"},
                "is_public": True
            }
        )
        category = cat_response.json()
        self.created_categories.append(category["id"])
        
        # User 2 submits recommendation
        rec_response = self.session.post(
            f"{BASE_URL}/api/categories/{category['id']}/recommendations",
            headers=self._get_headers(self.user2_token),
            json={
                "original_protocol": "(count or test)",
                "suggested_protocol": "(count or test or more)",
                "reason": "More keywords"
            }
        )
        rec_data = rec_response.json()
        if "recommendation" in rec_data:
            self.created_recommendations.append(rec_data["recommendation"]["id"])
        
        # Owner gets count
        count_response = self.session.get(
            f"{BASE_URL}/api/categories/{category['id']}/recommendations/count",
            headers=self._get_headers(self.user1_token)
        )
        assert count_response.status_code == 200
        data = count_response.json()
        assert "count" in data
        assert "pending" in data
        assert data["count"] >= 1
        assert data["pending"] >= 1
        print(f"✓ Got recommendation count (total: {data['count']}, pending: {data['pending']})")
        
        # Non-owner gets 0 count (not error)
        non_owner_count = self.session.get(
            f"{BASE_URL}/api/categories/{category['id']}/recommendations/count",
            headers=self._get_headers(self.user2_token)
        )
        assert non_owner_count.status_code == 200
        non_owner_data = non_owner_count.json()
        assert non_owner_data["count"] == 0
        print("✓ Non-owner correctly sees 0 count")
    
    # ============================================
    # UPDATE RECOMMENDATION STATUS TESTS
    # ============================================
    
    def test_12_accept_recommendation(self):
        """Owner can accept a recommendation"""
        # Create category and recommendation
        unique_name = f"TEST_AcceptRec_{uuid.uuid4().hex[:8]}"
        cat_response = self.session.post(
            f"{BASE_URL}/api/categories",
            headers=self._get_headers(self.user1_token),
            json={
                "name": unique_name,
                "protocol": {"protocol_string": "(accept or test)"},
                "is_public": True
            }
        )
        category = cat_response.json()
        self.created_categories.append(category["id"])
        
        # User 2 submits recommendation
        rec_response = self.session.post(
            f"{BASE_URL}/api/categories/{category['id']}/recommendations",
            headers=self._get_headers(self.user2_token),
            json={
                "original_protocol": "(accept or test)",
                "suggested_protocol": "(accept or test or approved)",
                "reason": "Better keywords"
            }
        )
        rec_id = rec_response.json()["recommendation"]["id"]
        self.created_recommendations.append(rec_id)
        
        # Owner accepts recommendation
        accept_response = self.session.put(
            f"{BASE_URL}/api/recommendations/{rec_id}/status?status=accepted",
            headers=self._get_headers(self.user1_token)
        )
        assert accept_response.status_code == 200
        data = accept_response.json()
        assert data["status"] == "accepted"
        print(f"✓ Recommendation accepted successfully")
    
    def test_13_reject_recommendation(self):
        """Owner can reject a recommendation"""
        # Create category and recommendation
        unique_name = f"TEST_RejectRec_{uuid.uuid4().hex[:8]}"
        cat_response = self.session.post(
            f"{BASE_URL}/api/categories",
            headers=self._get_headers(self.user1_token),
            json={
                "name": unique_name,
                "protocol": {"protocol_string": "(reject or test)"},
                "is_public": True
            }
        )
        category = cat_response.json()
        self.created_categories.append(category["id"])
        
        # User 2 submits recommendation
        rec_response = self.session.post(
            f"{BASE_URL}/api/categories/{category['id']}/recommendations",
            headers=self._get_headers(self.user2_token),
            json={
                "original_protocol": "(reject or test)",
                "suggested_protocol": "(reject or test or denied)",
                "reason": "Not a good change"
            }
        )
        rec_id = rec_response.json()["recommendation"]["id"]
        self.created_recommendations.append(rec_id)
        
        # Owner rejects recommendation
        reject_response = self.session.put(
            f"{BASE_URL}/api/recommendations/{rec_id}/status?status=rejected",
            headers=self._get_headers(self.user1_token)
        )
        assert reject_response.status_code == 200
        data = reject_response.json()
        assert data["status"] == "rejected"
        print(f"✓ Recommendation rejected successfully")
    
    def test_14_invalid_status_update(self):
        """Invalid status value returns 400"""
        # Create category and recommendation
        unique_name = f"TEST_InvalidStatus_{uuid.uuid4().hex[:8]}"
        cat_response = self.session.post(
            f"{BASE_URL}/api/categories",
            headers=self._get_headers(self.user1_token),
            json={
                "name": unique_name,
                "protocol": {"protocol_string": "(invalid or status)"},
                "is_public": True
            }
        )
        category = cat_response.json()
        self.created_categories.append(category["id"])
        
        # User 2 submits recommendation
        rec_response = self.session.post(
            f"{BASE_URL}/api/categories/{category['id']}/recommendations",
            headers=self._get_headers(self.user2_token),
            json={
                "original_protocol": "(invalid or status)",
                "suggested_protocol": "(invalid or status or bad)",
                "reason": "Testing invalid status"
            }
        )
        rec_id = rec_response.json()["recommendation"]["id"]
        self.created_recommendations.append(rec_id)
        
        # Try invalid status
        invalid_response = self.session.put(
            f"{BASE_URL}/api/recommendations/{rec_id}/status?status=invalid_status",
            headers=self._get_headers(self.user1_token)
        )
        assert invalid_response.status_code == 400
        print("✓ Invalid status correctly rejected with 400")
    
    def test_15_non_owner_cannot_update_status(self):
        """Non-owner cannot update recommendation status"""
        # Create category and recommendation
        unique_name = f"TEST_NonOwnerStatus_{uuid.uuid4().hex[:8]}"
        cat_response = self.session.post(
            f"{BASE_URL}/api/categories",
            headers=self._get_headers(self.user1_token),
            json={
                "name": unique_name,
                "protocol": {"protocol_string": "(nonowner or status)"},
                "is_public": True
            }
        )
        category = cat_response.json()
        self.created_categories.append(category["id"])
        
        # User 2 submits recommendation
        rec_response = self.session.post(
            f"{BASE_URL}/api/categories/{category['id']}/recommendations",
            headers=self._get_headers(self.user2_token),
            json={
                "original_protocol": "(nonowner or status)",
                "suggested_protocol": "(nonowner or status or hack)",
                "reason": "Testing non-owner"
            }
        )
        rec_id = rec_response.json()["recommendation"]["id"]
        self.created_recommendations.append(rec_id)
        
        # User 2 (non-owner) tries to update status
        non_owner_response = self.session.put(
            f"{BASE_URL}/api/recommendations/{rec_id}/status?status=accepted",
            headers=self._get_headers(self.user2_token)
        )
        assert non_owner_response.status_code == 403
        print("✓ Non-owner correctly denied status update with 403")
    
    # ============================================
    # DELETE RECOMMENDATION TESTS
    # ============================================
    
    def test_16_owner_can_delete_recommendation(self):
        """Owner can delete a recommendation"""
        # Create category and recommendation
        unique_name = f"TEST_OwnerDelete_{uuid.uuid4().hex[:8]}"
        cat_response = self.session.post(
            f"{BASE_URL}/api/categories",
            headers=self._get_headers(self.user1_token),
            json={
                "name": unique_name,
                "protocol": {"protocol_string": "(owner or delete)"},
                "is_public": True
            }
        )
        category = cat_response.json()
        self.created_categories.append(category["id"])
        
        # User 2 submits recommendation
        rec_response = self.session.post(
            f"{BASE_URL}/api/categories/{category['id']}/recommendations",
            headers=self._get_headers(self.user2_token),
            json={
                "original_protocol": "(owner or delete)",
                "suggested_protocol": "(owner or delete or removed)",
                "reason": "Testing delete"
            }
        )
        rec_id = rec_response.json()["recommendation"]["id"]
        
        # Owner deletes recommendation
        delete_response = self.session.delete(
            f"{BASE_URL}/api/recommendations/{rec_id}",
            headers=self._get_headers(self.user1_token)
        )
        assert delete_response.status_code == 200
        print("✓ Owner successfully deleted recommendation")
    
    def test_17_submitter_can_delete_own_recommendation(self):
        """Submitter can delete their own recommendation"""
        # Create category and recommendation
        unique_name = f"TEST_SubmitterDelete_{uuid.uuid4().hex[:8]}"
        cat_response = self.session.post(
            f"{BASE_URL}/api/categories",
            headers=self._get_headers(self.user1_token),
            json={
                "name": unique_name,
                "protocol": {"protocol_string": "(submitter or delete)"},
                "is_public": True
            }
        )
        category = cat_response.json()
        self.created_categories.append(category["id"])
        
        # User 2 submits recommendation
        rec_response = self.session.post(
            f"{BASE_URL}/api/categories/{category['id']}/recommendations",
            headers=self._get_headers(self.user2_token),
            json={
                "original_protocol": "(submitter or delete)",
                "suggested_protocol": "(submitter or delete or self)",
                "reason": "Testing self delete"
            }
        )
        rec_id = rec_response.json()["recommendation"]["id"]
        
        # Submitter (User 2) deletes their own recommendation
        delete_response = self.session.delete(
            f"{BASE_URL}/api/recommendations/{rec_id}",
            headers=self._get_headers(self.user2_token)
        )
        assert delete_response.status_code == 200
        print("✓ Submitter successfully deleted their own recommendation")
    
    def test_18_delete_nonexistent_recommendation(self):
        """Delete non-existent recommendation returns 404"""
        fake_id = str(uuid.uuid4())
        delete_response = self.session.delete(
            f"{BASE_URL}/api/recommendations/{fake_id}",
            headers=self._get_headers(self.user1_token)
        )
        assert delete_response.status_code == 404
        print("✓ Correctly returned 404 for non-existent recommendation")


# Run tests if executed directly
if __name__ == "__main__":
    pytest.main([__file__, "-v", "--tb=short"])
