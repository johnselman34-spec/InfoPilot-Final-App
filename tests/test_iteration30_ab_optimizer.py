"""
Iteration 30 - A/B Test Auto-Optimizer Feature Tests
Tests for the new A/B Test Auto-Optimizer that automatically disables losing variants
when statistical significance is reached.

Features tested:
- /api/ab-optimizer/status - Get optimizer config
- /api/ab-optimizer/analyze-all - Analyze all tests
- /api/ab-optimizer/enable - Enable optimizer
- /api/ab-optimizer/disable - Disable optimizer
- Admin Panel has 11 tabs including Optimizer
"""
import pytest
import requests
import os

BASE_URL = os.environ.get('REACT_APP_BACKEND_URL', '').rstrip('/')

# Test credentials
ADMIN_EMAIL = "jjspilot24@gmail.com"
ADMIN_PASSWORD = "InfoPilot2024!"


class TestABOptimizerAPI:
    """Test A/B Optimizer API endpoints"""
    
    @pytest.fixture(autouse=True)
    def setup(self):
        """Setup - get auth token"""
        self.session = requests.Session()
        self.session.headers.update({"Content-Type": "application/json"})
        
        # Login to get token
        login_response = self.session.post(
            f"{BASE_URL}/api/auth/login",
            json={"email": ADMIN_EMAIL, "password": ADMIN_PASSWORD}
        )
        if login_response.status_code == 200:
            data = login_response.json()
            self.token = data.get("token")
            self.session.headers.update({"Authorization": f"Bearer {self.token}"})
        else:
            pytest.skip("Authentication failed - skipping authenticated tests")
    
    def test_optimizer_status_endpoint(self):
        """Test /api/ab-optimizer/status returns config"""
        response = self.session.get(f"{BASE_URL}/api/ab-optimizer/status")
        assert response.status_code == 200, f"Expected 200, got {response.status_code}: {response.text}"
        
        data = response.json()
        # Verify response structure
        assert "enabled" in data, "Response should have 'enabled' field"
        assert "min_confidence" in data, "Response should have 'min_confidence' field"
        assert "min_sample_size" in data, "Response should have 'min_sample_size' field"
        assert "auto_disable_losers" in data, "Response should have 'auto_disable_losers' field"
        assert "notify_on_optimization" in data, "Response should have 'notify_on_optimization' field"
        assert "optimizations_this_month" in data, "Response should have 'optimizations_this_month' field"
        
        # Verify default values
        assert isinstance(data["enabled"], bool), "enabled should be boolean"
        assert isinstance(data["min_confidence"], (int, float)), "min_confidence should be numeric"
        assert data["min_confidence"] >= 0 and data["min_confidence"] <= 100, "min_confidence should be 0-100"
        assert isinstance(data["min_sample_size"], int), "min_sample_size should be integer"
        print(f"✅ Optimizer status: enabled={data['enabled']}, confidence={data['min_confidence']}%, sample_size={data['min_sample_size']}")
    
    def test_analyze_all_endpoint(self):
        """Test /api/ab-optimizer/analyze-all returns test analyses"""
        response = self.session.get(f"{BASE_URL}/api/ab-optimizer/analyze-all?days=30")
        assert response.status_code == 200, f"Expected 200, got {response.status_code}: {response.text}"
        
        data = response.json()
        # Verify response structure
        assert "total_tests" in data, "Response should have 'total_tests' field"
        assert "tests_with_winners" in data, "Response should have 'tests_with_winners' field"
        assert "tests_still_testing" in data, "Response should have 'tests_still_testing' field"
        assert "tests_no_data" in data, "Response should have 'tests_no_data' field"
        assert "analyses" in data, "Response should have 'analyses' field"
        
        # Verify data types
        assert isinstance(data["total_tests"], int), "total_tests should be integer"
        assert isinstance(data["analyses"], list), "analyses should be a list"
        
        print(f"✅ Analyze all: {data['total_tests']} tests, {data['tests_with_winners']} with winners, {data['tests_still_testing']} testing, {data['tests_no_data']} no data")
        
        # If there are analyses, verify structure
        if data["analyses"]:
            analysis = data["analyses"][0]
            assert "test_id" in analysis, "Analysis should have 'test_id'"
            assert "test_name" in analysis, "Analysis should have 'test_name'"
            assert "status" in analysis, "Analysis should have 'status'"
            print(f"   First test: {analysis['test_name']} - status: {analysis['status']}")
    
    def test_enable_optimizer(self):
        """Test /api/ab-optimizer/enable works"""
        response = self.session.post(f"{BASE_URL}/api/ab-optimizer/enable")
        assert response.status_code == 200, f"Expected 200, got {response.status_code}: {response.text}"
        
        data = response.json()
        assert data.get("success") == True, "Enable should return success=True"
        assert "message" in data, "Response should have message"
        print(f"✅ Enable optimizer: {data['message']}")
        
        # Verify it's actually enabled
        status_response = self.session.get(f"{BASE_URL}/api/ab-optimizer/status")
        assert status_response.status_code == 200
        status_data = status_response.json()
        assert status_data["enabled"] == True, "Optimizer should be enabled after enable call"
    
    def test_disable_optimizer(self):
        """Test /api/ab-optimizer/disable works"""
        response = self.session.post(f"{BASE_URL}/api/ab-optimizer/disable")
        assert response.status_code == 200, f"Expected 200, got {response.status_code}: {response.text}"
        
        data = response.json()
        assert data.get("success") == True, "Disable should return success=True"
        assert "message" in data, "Response should have message"
        print(f"✅ Disable optimizer: {data['message']}")
        
        # Verify it's actually disabled
        status_response = self.session.get(f"{BASE_URL}/api/ab-optimizer/status")
        assert status_response.status_code == 200
        status_data = status_response.json()
        assert status_data["enabled"] == False, "Optimizer should be disabled after disable call"
    
    def test_optimizer_config_update(self):
        """Test /api/ab-optimizer/config updates settings"""
        config = {
            "enabled": True,
            "min_confidence": 95.0,
            "min_sample_size": 100,
            "auto_disable_losers": True,
            "notify_on_optimization": True,
            "check_frequency_hours": 24
        }
        
        response = self.session.post(f"{BASE_URL}/api/ab-optimizer/config", json=config)
        assert response.status_code == 200, f"Expected 200, got {response.status_code}: {response.text}"
        
        data = response.json()
        assert data.get("success") == True, "Config update should return success=True"
        print(f"✅ Config update: {data['message']}")
        
        # Verify config was saved
        status_response = self.session.get(f"{BASE_URL}/api/ab-optimizer/status")
        assert status_response.status_code == 200
        status_data = status_response.json()
        assert status_data["min_confidence"] == 95.0, "min_confidence should be updated"
        assert status_data["min_sample_size"] == 100, "min_sample_size should be updated"
    
    def test_optimizer_history(self):
        """Test /api/ab-optimizer/history returns optimization logs"""
        response = self.session.get(f"{BASE_URL}/api/ab-optimizer/history?limit=20")
        assert response.status_code == 200, f"Expected 200, got {response.status_code}: {response.text}"
        
        data = response.json()
        assert "history" in data, "Response should have 'history' field"
        assert "total" in data, "Response should have 'total' field"
        assert isinstance(data["history"], list), "history should be a list"
        print(f"✅ Optimizer history: {data['total']} entries")
    
    def test_run_optimizer_preview(self):
        """Test /api/ab-optimizer/run-now with dry_run=true"""
        response = self.session.post(f"{BASE_URL}/api/ab-optimizer/run-now?dry_run=true")
        assert response.status_code == 200, f"Expected 200, got {response.status_code}: {response.text}"
        
        data = response.json()
        assert "success" in data, "Response should have 'success' field"
        assert "tests_checked" in data, "Response should have 'tests_checked' field"
        assert "dry_run" in data, "Response should have 'dry_run' field"
        assert data["dry_run"] == True, "dry_run should be True"
        print(f"✅ Run optimizer preview: checked {data['tests_checked']} tests, would optimize {data.get('tests_optimized', 0)}")
    
    def test_optimizer_requires_admin(self):
        """Test that optimizer endpoints require admin access"""
        # Create a new session without auth
        no_auth_session = requests.Session()
        no_auth_session.headers.update({"Content-Type": "application/json"})
        
        # Try to access status without auth
        response = no_auth_session.get(f"{BASE_URL}/api/ab-optimizer/status")
        assert response.status_code in [401, 403], f"Expected 401/403 without auth, got {response.status_code}"
        print("✅ Optimizer endpoints require authentication")


class TestAdminPanelTabs:
    """Test Admin Panel has 11 tabs including Optimizer"""
    
    def test_admin_panel_tabs_count(self):
        """Verify AdminPanel.js has 11 tabs"""
        with open('/app/frontend/src/pages/AdminPanel.js', 'r') as f:
            content = f.read()
        
        # Check for all 11 tabs in the tabs array
        expected_tabs = ['general', 'search', 'pricing', 'newsletter', 'users', 'content', 'polls', 'ab-testing', 'optimizer', 'email-reports', 'tutorials']
        
        for tab in expected_tabs:
            assert f"'{tab}'" in content, f"Tab '{tab}' should be in AdminPanel.js"
        
        print(f"✅ Admin Panel has all 11 tabs: {', '.join(expected_tabs)}")
    
    def test_optimizer_tab_renders_component(self):
        """Verify optimizer tab renders ABOptimizerAdmin component"""
        with open('/app/frontend/src/pages/AdminPanel.js', 'r') as f:
            content = f.read()
        
        # Check that ABOptimizerAdmin is imported
        assert "import ABOptimizerAdmin" in content, "ABOptimizerAdmin should be imported"
        
        # Check that optimizer tab renders the component
        assert "activeTab === 'optimizer'" in content, "Should check for optimizer tab"
        assert "<ABOptimizerAdmin" in content, "Should render ABOptimizerAdmin component"
        
        print("✅ Optimizer tab renders ABOptimizerAdmin component")


class TestABOptimizerService:
    """Test A/B Optimizer service functions"""
    
    def test_optimizer_service_exists(self):
        """Verify ab_optimizer.py service file exists and has required functions"""
        with open('/app/backend/services/ab_optimizer.py', 'r') as f:
            content = f.read()
        
        # Check for required functions
        required_functions = [
            'calculate_z_score',
            'z_score_to_confidence',
            'test_significance',
            'analyze_test',
            'get_ai_optimization_advice',
            'auto_optimize_test',
            'run_auto_optimizer',
            'get_optimization_history'
        ]
        
        for func in required_functions:
            assert f"def {func}" in content or f"async def {func}" in content, f"Function '{func}' should exist in ab_optimizer.py"
        
        print(f"✅ AB Optimizer service has all required functions: {', '.join(required_functions)}")
    
    def test_optimizer_uses_gpt52(self):
        """Verify optimizer uses GPT-5.2 for AI recommendations"""
        with open('/app/backend/services/ab_optimizer.py', 'r') as f:
            content = f.read()
        
        # Check for GPT-5.2 usage
        assert "ModelType.GPT_5_2" in content, "Should use GPT-5.2 for AI recommendations"
        assert "emergentintegrations.llm.chat" in content, "Should import from emergentintegrations"
        
        print("✅ AB Optimizer uses GPT-5.2 for AI recommendations")
    
    def test_optimizer_routes_exist(self):
        """Verify ab_optimizer.py routes file exists and has required endpoints"""
        with open('/app/backend/routes/ab_optimizer.py', 'r') as f:
            content = f.read()
        
        # Check for required endpoints
        required_endpoints = [
            '/status',
            '/config',
            '/analyze/',
            '/analyze-all',
            '/optimize',
            '/optimize-all',
            '/history',
            '/enable',
            '/disable',
            '/run-now'
        ]
        
        for endpoint in required_endpoints:
            assert endpoint in content, f"Endpoint '{endpoint}' should exist in ab_optimizer routes"
        
        print(f"✅ AB Optimizer routes has all required endpoints")


class TestRegressionBasicEndpoints:
    """Regression tests for basic endpoints"""
    
    @pytest.fixture(autouse=True)
    def setup(self):
        """Setup - get auth token"""
        self.session = requests.Session()
        self.session.headers.update({"Content-Type": "application/json"})
        
        # Login to get token
        login_response = self.session.post(
            f"{BASE_URL}/api/auth/login",
            json={"email": ADMIN_EMAIL, "password": ADMIN_PASSWORD}
        )
        if login_response.status_code == 200:
            data = login_response.json()
            self.token = data.get("token")
            self.session.headers.update({"Authorization": f"Bearer {self.token}"})
        else:
            pytest.skip("Authentication failed - skipping authenticated tests")
    
    def test_health_endpoint(self):
        """Test health endpoint"""
        response = requests.get(f"{BASE_URL}/api/health")
        assert response.status_code == 200, f"Health check failed: {response.status_code}"
        print("✅ Health endpoint working")
    
    def test_auth_login(self):
        """Test auth login works"""
        response = requests.post(
            f"{BASE_URL}/api/auth/login",
            json={"email": ADMIN_EMAIL, "password": ADMIN_PASSWORD}
        )
        assert response.status_code == 200, f"Login failed: {response.status_code}"
        data = response.json()
        assert "token" in data, "Login should return token"
        print("✅ Auth login working")
    
    def test_admin_settings(self):
        """Test admin settings endpoint"""
        response = self.session.get(f"{BASE_URL}/api/admin/settings")
        assert response.status_code == 200, f"Admin settings failed: {response.status_code}"
        print("✅ Admin settings endpoint working")
    
    def test_ab_tests_endpoint(self):
        """Test A/B tests endpoint still works"""
        response = self.session.get(f"{BASE_URL}/api/ab-tests")
        assert response.status_code == 200, f"A/B tests endpoint failed: {response.status_code}"
        print("✅ A/B tests endpoint working")
    
    def test_tutorials_endpoint(self):
        """Test tutorials endpoint still works"""
        response = requests.get(f"{BASE_URL}/api/tutorials")
        assert response.status_code == 200, f"Tutorials endpoint failed: {response.status_code}"
        print("✅ Tutorials endpoint working")
    
    def test_email_reports_status(self):
        """Test email reports status endpoint still works"""
        response = self.session.get(f"{BASE_URL}/api/email-reports/status")
        assert response.status_code == 200, f"Email reports status failed: {response.status_code}"
        print("✅ Email reports status endpoint working")


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
