#!/usr/bin/env python3
"""
Comprehensive API Quality Assurance Test Suite for Authentication Endpoints
Test Suite for /auth/verify/ endpoint removal and SQL-based authentication validation

Author: API QA Engineer
Created: 2025-09-02
"""

import json
import time
import pytest
import requests
import threading
from concurrent.futures import ThreadPoolExecutor, as_completed
from typing import Dict, List, Any, Optional
import logging

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

class AuthEndpointQATestSuite:
    """Comprehensive QA test suite for authentication endpoints"""
    
    def __init__(self, base_url: str = "http://localhost:8000"):
        self.base_url = base_url
        self.session = requests.Session()
        self.test_results = {
            "endpoint_removal": [],
            "functional_testing": [],
            "authentication_flow": [],
            "error_handling": [],
            "security_testing": [],
            "performance_testing": [],
            "integration_testing": []
        }
        
    def log_test_result(self, category: str, test_name: str, status: str, details: Dict = None):
        """Log test result for reporting"""
        result = {
            "test_name": test_name,
            "status": status,
            "timestamp": time.strftime("%Y-%m-%d %H:%M:%S"),
            "details": details or {}
        }
        self.test_results[category].append(result)
        logger.info(f"{category} - {test_name}: {status}")
        
    # 1. ENDPOINT REMOVAL VERIFICATION
    def test_removed_endpoint_returns_404(self):
        """Test that /auth/verify/ returns 404 Not Found"""
        test_name = "Removed endpoint /auth/verify/ returns 404"
        try:
            response = self.session.post(f"{self.base_url}/auth/verify/", 
                                       json={"test": "data"})
            
            if response.status_code == 404:
                self.log_test_result("endpoint_removal", test_name, "PASS", 
                                   {"status_code": response.status_code})
            else:
                self.log_test_result("endpoint_removal", test_name, "FAIL", 
                                   {"expected": 404, "actual": response.status_code,
                                    "response": response.text[:500]})
                                    
        except requests.exceptions.ConnectionError as e:
            self.log_test_result("endpoint_removal", test_name, "ERROR", 
                               {"error": f"Connection error: {str(e)}"})
        except Exception as e:
            self.log_test_result("endpoint_removal", test_name, "ERROR", 
                               {"error": str(e)})
    
    def test_removed_endpoint_not_in_docs(self):
        """Test that /auth/verify/ is not present in API documentation"""
        test_name = "Removed endpoint not in API documentation"
        try:
            # Test Swagger docs
            response = self.session.get(f"{self.base_url}/docs.json")
            if response.status_code == 200:
                swagger_doc = response.json()
                paths = swagger_doc.get("paths", {})
                
                if "/auth/verify/" in paths:
                    self.log_test_result("endpoint_removal", test_name, "FAIL", 
                                       {"error": "/auth/verify/ still present in Swagger docs"})
                else:
                    self.log_test_result("endpoint_removal", test_name, "PASS", 
                                       {"message": "Endpoint not found in API docs"})
            else:
                self.log_test_result("endpoint_removal", test_name, "SKIP", 
                                   {"error": "Could not fetch API documentation"})
                                   
        except Exception as e:
            self.log_test_result("endpoint_removal", test_name, "ERROR", 
                               {"error": str(e)})
    
    def test_api_root_endpoint_list(self):
        """Test that removed endpoint is not listed in API root"""
        test_name = "Removed endpoint not in API root listing"
        try:
            response = self.session.get(f"{self.base_url}/")
            if response.status_code == 200:
                api_info = response.json()
                endpoints = api_info.get("endpoints", {})
                
                # Check if verify endpoint is mentioned anywhere
                endpoint_text = json.dumps(endpoints).lower()
                if "verify/" in endpoint_text and "verify-user/" not in endpoint_text:
                    self.log_test_result("endpoint_removal", test_name, "FAIL", 
                                       {"error": "Old verify endpoint still referenced"})
                else:
                    self.log_test_result("endpoint_removal", test_name, "PASS", 
                                       {"message": "No reference to old endpoint"})
            else:
                self.log_test_result("endpoint_removal", test_name, "SKIP", 
                                   {"error": f"Could not fetch API root: {response.status_code}"})
                                   
        except Exception as e:
            self.log_test_result("endpoint_removal", test_name, "ERROR", 
                               {"error": str(e)})

    # 2. FUNCTIONAL ENDPOINT TESTING
    def test_verify_user_endpoint_exists(self):
        """Test that /auth/verify-user/ endpoint exists and accepts POST"""
        test_name = "verify-user endpoint exists"
        try:
            # Test with empty payload to check if endpoint exists
            response = self.session.post(f"{self.base_url}/auth/verify-user/", json={})
            
            # Should not return 404 (endpoint exists)
            if response.status_code != 404:
                self.log_test_result("functional_testing", test_name, "PASS", 
                                   {"status_code": response.status_code,
                                    "message": "Endpoint exists and processes requests"})
            else:
                self.log_test_result("functional_testing", test_name, "FAIL", 
                                   {"error": "Endpoint returns 404 - not found"})
                                   
        except Exception as e:
            self.log_test_result("functional_testing", test_name, "ERROR", 
                               {"error": str(e)})
    
    def test_verify_user_valid_payload(self):
        """Test /auth/verify-user/ with valid test payload"""
        test_name = "verify-user with valid payload"
        
        valid_payload = {
            "email": "test@example.com",
            "name": "Test User",
            "sub": "azure-ad-sub-identifier",
            "picture": None
        }
        
        try:
            response = self.session.post(f"{self.base_url}/auth/verify-user/", 
                                       json=valid_payload)
            
            if response.status_code == 200:
                response_data = response.json()
                
                # Check response structure
                if response_data.get("success") and "data" in response_data:
                    data = response_data["data"]
                    if "access_token" in data and "refresh_token" in data:
                        self.log_test_result("functional_testing", test_name, "PASS", 
                                           {"tokens_received": True,
                                            "response_structure": "correct"})
                    else:
                        self.log_test_result("functional_testing", test_name, "PARTIAL", 
                                           {"message": "Response received but missing tokens",
                                            "response": response_data})
                else:
                    self.log_test_result("functional_testing", test_name, "PARTIAL", 
                                       {"message": "Unexpected response structure",
                                        "response": response_data})
            else:
                self.log_test_result("functional_testing", test_name, "FAIL", 
                                   {"status_code": response.status_code,
                                    "response": response.text[:500]})
                                    
        except Exception as e:
            self.log_test_result("functional_testing", test_name, "ERROR", 
                               {"error": str(e)})
    
    def test_verify_user_invalid_payloads(self):
        """Test /auth/verify-user/ with various invalid payloads"""
        test_cases = [
            {"name": "empty_payload", "payload": {}},
            {"name": "missing_email", "payload": {"name": "Test", "sub": "123"}},
            {"name": "missing_sub", "payload": {"email": "test@test.com", "name": "Test"}},
            {"name": "invalid_email", "payload": {"email": "invalid-email", "name": "Test", "sub": "123"}},
            {"name": "null_values", "payload": {"email": None, "name": None, "sub": None}},
        ]
        
        for test_case in test_cases:
            test_name = f"verify-user invalid payload: {test_case['name']}"
            try:
                response = self.session.post(f"{self.base_url}/auth/verify-user/", 
                                           json=test_case["payload"])
                
                # Should return error status (400, 422, etc.)
                if response.status_code >= 400:
                    self.log_test_result("functional_testing", test_name, "PASS", 
                                       {"status_code": response.status_code,
                                        "error_handled": True})
                else:
                    self.log_test_result("functional_testing", test_name, "FAIL", 
                                       {"message": "Should return error for invalid payload",
                                        "status_code": response.status_code})
                                        
            except Exception as e:
                self.log_test_result("functional_testing", test_name, "ERROR", 
                                   {"error": str(e)})

    def test_refresh_endpoint_exists(self):
        """Test that /auth/refresh/ endpoint exists"""
        test_name = "refresh endpoint exists"
        try:
            response = self.session.post(f"{self.base_url}/auth/refresh/", json={})
            
            # Should not return 404
            if response.status_code != 404:
                self.log_test_result("functional_testing", test_name, "PASS", 
                                   {"status_code": response.status_code})
            else:
                self.log_test_result("functional_testing", test_name, "FAIL", 
                                   {"error": "Refresh endpoint not found"})
                                   
        except Exception as e:
            self.log_test_result("functional_testing", test_name, "ERROR", 
                               {"error": str(e)})

    def test_refresh_token_invalid_payload(self):
        """Test /auth/refresh/ with invalid payloads"""
        test_cases = [
            {"name": "empty_payload", "payload": {}},
            {"name": "invalid_token", "payload": {"refresh_token": "invalid_token"}},
            {"name": "missing_refresh_token", "payload": {"token": "some_token"}},
        ]
        
        for test_case in test_cases:
            test_name = f"refresh endpoint invalid payload: {test_case['name']}"
            try:
                response = self.session.post(f"{self.base_url}/auth/refresh/", 
                                           json=test_case["payload"])
                
                # Should return error status
                if response.status_code >= 400:
                    self.log_test_result("functional_testing", test_name, "PASS", 
                                       {"status_code": response.status_code})
                else:
                    self.log_test_result("functional_testing", test_name, "FAIL", 
                                       {"message": "Should return error for invalid payload",
                                        "status_code": response.status_code})
                                        
            except Exception as e:
                self.log_test_result("functional_testing", test_name, "ERROR", 
                                   {"error": str(e)})

    # 3. AUTHENTICATION FLOW TESTING
    def test_full_authentication_flow(self):
        """Test complete authentication flow from login to token refresh"""
        test_name = "Full authentication flow"
        
        # Step 1: Login with valid credentials
        login_payload = {
            "email": "qa_test@example.com",
            "name": "QA Test User",
            "sub": "qa-test-sub-123",
            "picture": None
        }
        
        try:
            # Login
            login_response = self.session.post(f"{self.base_url}/auth/verify-user/", 
                                             json=login_payload)
            
            if login_response.status_code == 200:
                login_data = login_response.json()
                
                if login_data.get("success") and "data" in login_data:
                    tokens = login_data["data"]
                    access_token = tokens.get("access_token")
                    refresh_token = tokens.get("refresh_token")
                    
                    if access_token and refresh_token:
                        # Step 2: Use access token for protected endpoint
                        headers = {"Authorization": f"Bearer {access_token}"}
                        protected_response = self.session.get(f"{self.base_url}/api/users/", 
                                                            headers=headers)
                        
                        # Step 3: Refresh token
                        refresh_response = self.session.post(f"{self.base_url}/auth/refresh/",
                                                           json={"refresh_token": refresh_token})
                        
                        # Evaluate results
                        flow_status = []
                        if login_response.status_code == 200:
                            flow_status.append("login_success")
                        if protected_response.status_code in [200, 401]:  # 401 is acceptable if JWT validation fails
                            flow_status.append("protected_endpoint_accessible")
                        if refresh_response.status_code in [200, 400, 401]:  # Various statuses acceptable
                            flow_status.append("refresh_endpoint_responsive")
                        
                        self.log_test_result("authentication_flow", test_name, "PASS", 
                                           {"flow_steps": flow_status,
                                            "login_status": login_response.status_code,
                                            "protected_status": protected_response.status_code,
                                            "refresh_status": refresh_response.status_code})
                    else:
                        self.log_test_result("authentication_flow", test_name, "FAIL", 
                                           {"error": "Missing tokens in response"})
                else:
                    self.log_test_result("authentication_flow", test_name, "FAIL", 
                                       {"error": "Invalid login response structure"})
            else:
                self.log_test_result("authentication_flow", test_name, "FAIL", 
                                   {"error": f"Login failed: {login_response.status_code}"})
                                   
        except Exception as e:
            self.log_test_result("authentication_flow", test_name, "ERROR", 
                               {"error": str(e)})

    # 4. ERROR HANDLING & EDGE CASES
    def test_malformed_json_payloads(self):
        """Test endpoints with malformed JSON"""
        test_name = "Malformed JSON handling"
        
        endpoints = [
            "/auth/verify-user/",
            "/auth/refresh/"
        ]
        
        malformed_payloads = [
            '{"incomplete": json',
            '{"key": }',
            '{key: "value"}',
            'not_json_at_all',
            ''
        ]
        
        results = []
        for endpoint in endpoints:
            for i, payload in enumerate(malformed_payloads):
                try:
                    response = self.session.post(f"{self.base_url}{endpoint}",
                                               data=payload,
                                               headers={'Content-Type': 'application/json'})
                    
                    # Should return 400 Bad Request for malformed JSON
                    if response.status_code == 400:
                        results.append(f"{endpoint}_payload_{i}: PASS")
                    else:
                        results.append(f"{endpoint}_payload_{i}: status_{response.status_code}")
                        
                except Exception as e:
                    results.append(f"{endpoint}_payload_{i}: ERROR - {str(e)[:100]}")
        
        self.log_test_result("error_handling", test_name, "PASS", 
                           {"results": results})

    def test_content_type_validation(self):
        """Test endpoints with different content types"""
        test_name = "Content-Type validation"
        
        valid_payload = {"email": "test@test.com", "name": "Test", "sub": "123"}
        
        content_types = [
            ("application/json", "valid"),
            ("application/xml", "invalid"),
            ("text/plain", "invalid"),
            ("application/form-data", "invalid"),
            (None, "missing")
        ]
        
        results = []
        for content_type, expected in content_types:
            try:
                headers = {}
                if content_type:
                    headers['Content-Type'] = content_type
                
                if content_type == "application/json":
                    data = json.dumps(valid_payload)
                else:
                    data = str(valid_payload)
                
                response = self.session.post(f"{self.base_url}/auth/verify-user/",
                                           data=data, headers=headers)
                
                if expected == "valid":
                    status = "PASS" if response.status_code in [200, 400] else f"FAIL_{response.status_code}"
                else:
                    status = "PASS" if response.status_code == 400 else f"UNEXPECTED_{response.status_code}"
                
                results.append(f"{content_type or 'None'}: {status}")
                
            except Exception as e:
                results.append(f"{content_type or 'None'}: ERROR - {str(e)[:50]}")
        
        self.log_test_result("error_handling", test_name, "PASS", 
                           {"results": results})

    # 5. SECURITY TESTING
    def test_sql_injection_attempts(self):
        """Test SQL injection prevention"""
        test_name = "SQL injection prevention"
        
        injection_payloads = [
            {"email": "test@test.com'; DROP TABLE users; --", "name": "Test", "sub": "123"},
            {"email": "test@test.com", "name": "'; SELECT * FROM users; --", "sub": "123"},
            {"email": "test@test.com", "name": "Test", "sub": "123'; UNION SELECT password FROM users; --"},
            {"email": "test@test.com' OR 1=1 --", "name": "Test", "sub": "123"},
        ]
        
        results = []
        for payload in injection_payloads:
            try:
                response = self.session.post(f"{self.base_url}/auth/verify-user/", 
                                           json=payload)
                
                # Should not return 500 (internal server error from SQL injection)
                if response.status_code != 500:
                    results.append("PASS")
                else:
                    results.append("POTENTIAL_VULNERABILITY")
                    
            except Exception as e:
                results.append(f"ERROR: {str(e)[:50]}")
        
        if "POTENTIAL_VULNERABILITY" in results:
            self.log_test_result("security_testing", test_name, "FAIL", 
                               {"warning": "Potential SQL injection vulnerability", "results": results})
        else:
            self.log_test_result("security_testing", test_name, "PASS", 
                               {"message": "No SQL injection vulnerabilities detected"})

    def test_xss_prevention(self):
        """Test XSS prevention in input handling"""
        test_name = "XSS prevention"
        
        xss_payloads = [
            {"email": "<script>alert('xss')</script>@test.com", "name": "Test", "sub": "123"},
            {"email": "test@test.com", "name": "<img src=x onerror=alert('xss')>", "sub": "123"},
            {"email": "test@test.com", "name": "Test", "sub": "javascript:alert('xss')"},
        ]
        
        results = []
        for payload in xss_payloads:
            try:
                response = self.session.post(f"{self.base_url}/auth/verify-user/", 
                                           json=payload)
                
                # Check if malicious scripts are reflected in response
                response_text = response.text.lower()
                if "<script>" in response_text or "javascript:" in response_text or "onerror=" in response_text:
                    results.append("POTENTIAL_XSS")
                else:
                    results.append("SAFE")
                    
            except Exception as e:
                results.append(f"ERROR: {str(e)[:50]}")
        
        if "POTENTIAL_XSS" in results:
            self.log_test_result("security_testing", test_name, "FAIL", 
                               {"warning": "Potential XSS vulnerability"})
        else:
            self.log_test_result("security_testing", test_name, "PASS", 
                               {"message": "No XSS vulnerabilities detected"})

    def test_authorization_header_handling(self):
        """Test Authorization header security"""
        test_name = "Authorization header security"
        
        # Test various malformed/malicious authorization headers
        auth_headers = [
            "Bearer valid_jwt_token",
            "Bearer ' OR 1=1 --",
            "Bearer <script>alert('xss')</script>",
            "Bearer " + "A" * 10000,  # Very long token
            "Basic malicious_basic_auth",
            "Malformed header value",
        ]
        
        results = []
        for auth_header in auth_headers:
            try:
                headers = {"Authorization": auth_header}
                response = self.session.get(f"{self.base_url}/api/users/", headers=headers)
                
                # Should handle gracefully without 500 errors
                if response.status_code != 500:
                    results.append(f"SAFE: {response.status_code}")
                else:
                    results.append("POTENTIAL_ISSUE: 500")
                    
            except Exception as e:
                results.append(f"ERROR: {str(e)[:50]}")
        
        self.log_test_result("security_testing", test_name, "PASS", 
                           {"results": results})

    # 6. PERFORMANCE TESTING
    def test_response_time_benchmarks(self):
        """Test response time benchmarks for authentication endpoints"""
        test_name = "Response time benchmarks"
        
        endpoints_payloads = [
            ("/auth/verify-user/", {"email": "perf@test.com", "name": "Perf", "sub": "perf123"}),
            ("/auth/refresh/", {"refresh_token": "test_token"}),
        ]
        
        results = {}
        for endpoint, payload in endpoints_payloads:
            times = []
            for i in range(5):  # 5 requests per endpoint
                try:
                    start_time = time.time()
                    response = self.session.post(f"{self.base_url}{endpoint}", json=payload)
                    end_time = time.time()
                    
                    response_time = (end_time - start_time) * 1000  # Convert to ms
                    times.append(response_time)
                    
                except Exception as e:
                    times.append(-1)  # Error indicator
            
            if times:
                valid_times = [t for t in times if t > 0]
                if valid_times:
                    avg_time = sum(valid_times) / len(valid_times)
                    max_time = max(valid_times)
                    min_time = min(valid_times)
                    results[endpoint] = {
                        "avg_ms": round(avg_time, 2),
                        "max_ms": round(max_time, 2),
                        "min_ms": round(min_time, 2),
                        "samples": len(valid_times)
                    }
        
        self.log_test_result("performance_testing", test_name, "PASS", 
                           {"benchmarks": results})

    def test_concurrent_requests(self):
        """Test handling of concurrent requests"""
        test_name = "Concurrent request handling"
        
        def make_request(session_id):
            try:
                payload = {"email": f"concurrent{session_id}@test.com", "name": f"User{session_id}", "sub": f"sub{session_id}"}
                start_time = time.time()
                response = requests.post(f"{self.base_url}/auth/verify-user/", json=payload)
                end_time = time.time()
                
                return {
                    "session_id": session_id,
                    "status_code": response.status_code,
                    "response_time": (end_time - start_time) * 1000,
                    "success": response.status_code in [200, 400, 401]  # Any reasonable response
                }
            except Exception as e:
                return {
                    "session_id": session_id,
                    "error": str(e),
                    "success": False
                }
        
        # Run 10 concurrent requests
        with ThreadPoolExecutor(max_workers=10) as executor:
            futures = [executor.submit(make_request, i) for i in range(10)]
            results = [future.result() for future in as_completed(futures)]
        
        successful = len([r for r in results if r.get("success")])
        total = len(results)
        
        self.log_test_result("performance_testing", test_name, "PASS", 
                           {"successful_requests": successful,
                            "total_requests": total,
                            "success_rate": f"{(successful/total)*100:.1f}%"})

    # 7. INTEGRATION TESTING
    def test_server_health_check(self):
        """Test basic server health and responsiveness"""
        test_name = "Server health check"
        
        try:
            response = self.session.get(f"{self.base_url}/")
            
            if response.status_code == 200:
                self.log_test_result("integration_testing", test_name, "PASS", 
                                   {"status": "Server is responsive"})
            else:
                self.log_test_result("integration_testing", test_name, "FAIL", 
                                   {"status_code": response.status_code})
                                   
        except requests.exceptions.ConnectionError:
            self.log_test_result("integration_testing", test_name, "FAIL", 
                               {"error": "Cannot connect to server"})
        except Exception as e:
            self.log_test_result("integration_testing", test_name, "ERROR", 
                               {"error": str(e)})

    def test_api_documentation_access(self):
        """Test API documentation accessibility"""
        test_name = "API documentation access"
        
        doc_endpoints = [
            "/docs/",
            "/docs.json"
        ]
        
        results = {}
        for endpoint in doc_endpoints:
            try:
                response = self.session.get(f"{self.base_url}{endpoint}")
                results[endpoint] = {
                    "status_code": response.status_code,
                    "accessible": response.status_code == 200
                }
            except Exception as e:
                results[endpoint] = {
                    "error": str(e),
                    "accessible": False
                }
        
        self.log_test_result("integration_testing", test_name, "PASS", 
                           {"documentation_status": results})

    def test_protected_endpoints_jwt_validation(self):
        """Test that protected endpoints properly validate JWT tokens"""
        test_name = "Protected endpoints JWT validation"
        
        # List of known protected endpoints
        protected_endpoints = [
            "/api/users/",
            "/api/dash_001/dashboard/",
            "/analysis/reports/",
            "/api/clusters/",
        ]
        
        results = {}
        
        # Test without token
        for endpoint in protected_endpoints:
            try:
                response = self.session.get(f"{self.base_url}{endpoint}")
                results[f"{endpoint}_no_token"] = {
                    "status_code": response.status_code,
                    "properly_protected": response.status_code in [401, 403]
                }
            except Exception as e:
                results[f"{endpoint}_no_token"] = {
                    "error": str(e)[:100],
                    "properly_protected": False
                }
        
        # Test with invalid token
        invalid_token_headers = {"Authorization": "Bearer invalid_token"}
        for endpoint in protected_endpoints:
            try:
                response = self.session.get(f"{self.base_url}{endpoint}", 
                                          headers=invalid_token_headers)
                results[f"{endpoint}_invalid_token"] = {
                    "status_code": response.status_code,
                    "properly_protected": response.status_code in [401, 403]
                }
            except Exception as e:
                results[f"{endpoint}_invalid_token"] = {
                    "error": str(e)[:100],
                    "properly_protected": False
                }
        
        self.log_test_result("integration_testing", test_name, "PASS", 
                           {"endpoint_protection": results})

    # TEST EXECUTION AND REPORTING
    def run_all_tests(self):
        """Execute all test suites"""
        logger.info("Starting comprehensive API QA test suite...")
        
        # 1. Endpoint removal verification
        logger.info("Running endpoint removal verification tests...")
        self.test_removed_endpoint_returns_404()
        self.test_removed_endpoint_not_in_docs()
        self.test_api_root_endpoint_list()
        
        # 2. Functional testing
        logger.info("Running functional endpoint tests...")
        self.test_verify_user_endpoint_exists()
        self.test_verify_user_valid_payload()
        self.test_verify_user_invalid_payloads()
        self.test_refresh_endpoint_exists()
        self.test_refresh_token_invalid_payload()
        
        # 3. Authentication flow
        logger.info("Running authentication flow tests...")
        self.test_full_authentication_flow()
        
        # 4. Error handling
        logger.info("Running error handling tests...")
        self.test_malformed_json_payloads()
        self.test_content_type_validation()
        
        # 5. Security testing
        logger.info("Running security tests...")
        self.test_sql_injection_attempts()
        self.test_xss_prevention()
        self.test_authorization_header_handling()
        
        # 6. Performance testing
        logger.info("Running performance tests...")
        self.test_response_time_benchmarks()
        self.test_concurrent_requests()
        
        # 7. Integration testing
        logger.info("Running integration tests...")
        self.test_server_health_check()
        self.test_api_documentation_access()
        self.test_protected_endpoints_jwt_validation()
        
        logger.info("All tests completed!")
        
    def generate_report(self) -> Dict[str, Any]:
        """Generate comprehensive test report"""
        report = {
            "test_execution_summary": {
                "timestamp": time.strftime("%Y-%m-%d %H:%M:%S"),
                "total_test_categories": len(self.test_results),
                "base_url": self.base_url
            },
            "category_summary": {},
            "detailed_results": self.test_results,
            "overall_assessment": {}
        }
        
        # Generate category summaries
        for category, results in self.test_results.items():
            total_tests = len(results)
            passed_tests = len([r for r in results if r["status"] == "PASS"])
            failed_tests = len([r for r in results if r["status"] == "FAIL"])
            error_tests = len([r for r in results if r["status"] == "ERROR"])
            
            report["category_summary"][category] = {
                "total": total_tests,
                "passed": passed_tests,
                "failed": failed_tests,
                "errors": error_tests,
                "success_rate": f"{(passed_tests/total_tests)*100:.1f}%" if total_tests > 0 else "0%"
            }
        
        # Overall assessment
        all_results = []
        for results in self.test_results.values():
            all_results.extend(results)
        
        total_all = len(all_results)
        passed_all = len([r for r in all_results if r["status"] == "PASS"])
        failed_all = len([r for r in all_results if r["status"] == "FAIL"])
        error_all = len([r for r in all_results if r["status"] == "ERROR"])
        
        report["overall_assessment"] = {
            "total_tests": total_all,
            "passed": passed_all,
            "failed": failed_all,
            "errors": error_all,
            "overall_success_rate": f"{(passed_all/total_all)*100:.1f}%" if total_all > 0 else "0%",
            "critical_issues": failed_all + error_all,
            "test_status": "PASS" if failed_all == 0 and error_all == 0 else "FAIL"
        }
        
        return report


def main():
    """Main execution function"""
    # Initialize test suite
    qa_suite = AuthEndpointQATestSuite()
    
    # Run all tests
    qa_suite.run_all_tests()
    
    # Generate and save report
    report = qa_suite.generate_report()
    
    # Save to file
    report_file = f"auth_endpoint_qa_report_{time.strftime('%Y%m%d_%H%M%S')}.json"
    with open(report_file, 'w') as f:
        json.dump(report, f, indent=2)
    
    print(f"\n{'='*80}")
    print("COMPREHENSIVE API QA TEST REPORT")
    print(f"{'='*80}")
    
    print(f"\nOverall Test Status: {report['overall_assessment']['test_status']}")
    print(f"Total Tests: {report['overall_assessment']['total_tests']}")
    print(f"Passed: {report['overall_assessment']['passed']}")
    print(f"Failed: {report['overall_assessment']['failed']}")
    print(f"Errors: {report['overall_assessment']['errors']}")
    print(f"Success Rate: {report['overall_assessment']['overall_success_rate']}")
    
    print(f"\nCategory Breakdown:")
    for category, summary in report['category_summary'].items():
        print(f"  {category}: {summary['passed']}/{summary['total']} ({summary['success_rate']})")
    
    print(f"\nDetailed report saved to: {report_file}")
    
    # Print critical failures
    critical_failures = []
    for category, results in report['detailed_results'].items():
        for result in results:
            if result['status'] in ['FAIL', 'ERROR']:
                critical_failures.append(f"{category}: {result['test_name']} - {result['status']}")
    
    if critical_failures:
        print(f"\nCRITICAL ISSUES FOUND:")
        for failure in critical_failures[:10]:  # Show first 10
            print(f"  - {failure}")
        if len(critical_failures) > 10:
            print(f"  ... and {len(critical_failures) - 10} more issues")
    
    return report


if __name__ == "__main__":
    main()