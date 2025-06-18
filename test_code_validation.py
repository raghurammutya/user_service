#!/usr/bin/env python3
"""
Code Validation Test Suite - Tests code structure and imports
Tests the enhancements without requiring a running service
"""

import sys
import os
import importlib.util
import inspect
from typing import List, Dict, Any

class CodeValidationTestSuite:
    def __init__(self):
        self.test_results = []
        self.base_path = "/home/stocksadmin/stocksblitz/user_service"
        
    def log_test_result(self, test_name: str, success: bool, details: str = ""):
        """Log test results for summary"""
        self.test_results.append({
            "test": test_name,
            "success": success,
            "details": details
        })
        status = "✅ PASS" if success else "❌ FAIL"
        print(f"{status} {test_name}")
        if details:
            print(f"    {details}")
    
    def test_import_user_enhancements(self):
        """Test if user enhancement models can be imported"""
        print("\n📦 Testing Model Imports...")
        
        try:
            # Add the user_service directory to Python path
            sys.path.insert(0, self.base_path)
            
            # Test importing user enhancements models
            from app.models.user_enhancements import (
                UserStatus, OnboardingStatus, MFAType, RiskLevel,
                UserStatusHistory, UserOnboarding, UserMFA, UserSession,
                UserActivity, UserPreferences, Organization, 
                UserOrganizationRole, ComplianceProfile, UserMetrics, AuditTrail
            )
            
            self.log_test_result("Import User Enhancement Models", True, "All models imported successfully")
            
            # Test enum values
            test_enums = [
                (UserStatus.ACTIVE, "ACTIVE"),
                (MFAType.TOTP, "totp"),
                (RiskLevel.HIGH, "high"),
                (OnboardingStatus.EMAIL_VERIFICATION, "email_verification")
            ]
            
            for enum_val, expected in test_enums:
                if enum_val.value == expected:
                    self.log_test_result(f"Enum {enum_val.__class__.__name__}.{enum_val.name}", True, f"Value: {enum_val.value}")
                else:
                    self.log_test_result(f"Enum {enum_val.__class__.__name__}.{enum_val.name}", False, f"Expected {expected}, got {enum_val.value}")
            
        except ImportError as e:
            self.log_test_result("Import User Enhancement Models", False, f"Import error: {e}")
        except Exception as e:
            self.log_test_result("Import User Enhancement Models", False, f"Error: {e}")
    
    def test_import_api_endpoints(self):
        """Test if API endpoints can be imported"""
        print("\n🌐 Testing API Endpoint Imports...")
        
        try:
            from app.api.endpoints.user_enhancements import router
            
            self.log_test_result("Import User Enhancement API", True, "Router imported successfully")
            
            # Check if router has routes
            route_count = len(router.routes)
            if route_count > 0:
                self.log_test_result("API Routes Count", True, f"Found {route_count} routes")
                
                # List some routes
                for i, route in enumerate(router.routes[:5]):  # First 5 routes
                    if hasattr(route, 'path') and hasattr(route, 'methods'):
                        methods = ', '.join(route.methods) if route.methods else 'GET'
                        self.log_test_result(f"Route {i+1}", True, f"{methods} {route.path}")
            else:
                self.log_test_result("API Routes Count", False, "No routes found")
                
        except ImportError as e:
            self.log_test_result("Import User Enhancement API", False, f"Import error: {e}")
        except Exception as e:
            self.log_test_result("Import User Enhancement API", False, f"Error: {e}")
    
    def test_permissions_models(self):
        """Test if permissions models can be imported"""
        print("\n🔐 Testing Permissions Model Imports...")
        
        try:
            from app.models.permissions import (
                UserPermission, TradingRestriction, PermissionType,
                PermissionEvaluator, PermissionResult
            )
            
            self.log_test_result("Import Permissions Models", True, "All permissions models imported")
            
            # Test PermissionResult functionality
            result = PermissionResult(allowed=True, reason="TEST", priority=5)
            if result.allowed and result.reason == "TEST":
                self.log_test_result("PermissionResult Class", True, "Class instantiation works")
            else:
                self.log_test_result("PermissionResult Class", False, "Class not working properly")
                
        except ImportError as e:
            self.log_test_result("Import Permissions Models", False, f"Import error: {e}")
        except Exception as e:
            self.log_test_result("Import Permissions Models", False, f"Error: {e}")
    
    def test_database_schema_files(self):
        """Test if database schema files exist and are valid"""
        print("\n🗄️ Testing Database Schema Files...")
        
        # Check if init.sql exists and contains our tables
        init_sql_path = "/home/stocksadmin/stocksblitz/init.sql"
        
        try:
            with open(init_sql_path, 'r') as f:
                init_sql_content = f.read()
            
            # Check for our enhancement tables
            enhancement_tables = [
                "user_status_history",
                "user_onboarding", 
                "user_mfa",
                "user_sessions",
                "user_activities",
                "user_preferences",
                "organizations",
                "user_organization_roles",
                "compliance_profiles",
                "user_metrics",
                "audit_trail"
            ]
            
            found_tables = []
            missing_tables = []
            
            for table in enhancement_tables:
                if f"CREATE TABLE IF NOT EXISTS tradingdb.{table}" in init_sql_content:
                    found_tables.append(table)
                else:
                    missing_tables.append(table)
            
            if len(found_tables) == len(enhancement_tables):
                self.log_test_result("Database Schema Tables", True, f"All {len(enhancement_tables)} tables found in init.sql")
            else:
                self.log_test_result("Database Schema Tables", False, f"Missing tables: {missing_tables}")
            
            # Check for indexes
            if "CREATE INDEX IF NOT EXISTS" in init_sql_content:
                self.log_test_result("Database Indexes", True, "Indexes found in init.sql")
            else:
                self.log_test_result("Database Indexes", False, "No indexes found")
                
        except FileNotFoundError:
            self.log_test_result("Database Schema Files", False, "init.sql not found")
        except Exception as e:
            self.log_test_result("Database Schema Files", False, f"Error reading init.sql: {e}")
    
    def test_requirements_file(self):
        """Test if requirements.txt contains new dependencies"""
        print("\n📋 Testing Requirements File...")
        
        requirements_path = f"{self.base_path}/docker/requirements.txt"
        
        try:
            with open(requirements_path, 'r') as f:
                requirements_content = f.read()
            
            # Check for new dependencies
            new_deps = ["pyotp", "qrcode", "phonenumbers", "geoip2", "user-agents", "pillow"]
            found_deps = []
            missing_deps = []
            
            for dep in new_deps:
                if dep in requirements_content:
                    found_deps.append(dep)
                else:
                    missing_deps.append(dep)
            
            if len(found_deps) == len(new_deps):
                self.log_test_result("Requirements Dependencies", True, f"All {len(new_deps)} new dependencies found")
            else:
                self.log_test_result("Requirements Dependencies", False, f"Missing: {missing_deps}")
                
        except FileNotFoundError:
            self.log_test_result("Requirements File", False, "requirements.txt not found")
        except Exception as e:
            self.log_test_result("Requirements File", False, f"Error reading requirements.txt: {e}")
    
    def test_main_app_integration(self):
        """Test if main app includes new enhancements"""
        print("\n🚀 Testing Main App Integration...")
        
        main_py_path = f"{self.base_path}/app/main.py"
        
        try:
            with open(main_py_path, 'r') as f:
                main_content = f.read()
            
            # Check for user_enhancements import
            if "user_enhancements" in main_content:
                self.log_test_result("Main App Import", True, "user_enhancements imported in main.py")
            else:
                self.log_test_result("Main App Import", False, "user_enhancements not imported")
            
            # Check for router inclusion
            if "user_enhancements.router" in main_content:
                self.log_test_result("Router Integration", True, "user_enhancements router included")
            else:
                self.log_test_result("Router Integration", False, "user_enhancements router not included")
                
            # Check for API prefix
            if "/api/user-enhancements" in main_content:
                self.log_test_result("API Prefix", True, "API prefix configured correctly")
            else:
                self.log_test_result("API Prefix", False, "API prefix not found")
                
        except FileNotFoundError:
            self.log_test_result("Main App Integration", False, "main.py not found")
        except Exception as e:
            self.log_test_result("Main App Integration", False, f"Error reading main.py: {e}")
    
    def test_enhancement_functions(self):
        """Test if enhancement functions work correctly"""
        print("\n🔧 Testing Enhancement Functions...")
        
        try:
            # Test enum definitions work
            from app.models.user_enhancements import UserStatus, MFAType
            
            # Test enum values
            statuses = [UserStatus.ACTIVE, UserStatus.SUSPENDED, UserStatus.LOCKED]
            mfa_types = [MFAType.TOTP, MFAType.SMS, MFAType.EMAIL]
            
            self.log_test_result("Enum Definitions", True, f"UserStatus: {len(statuses)} values, MFAType: {len(mfa_types)} values")
            
            # Test if we can create enum instances
            active_status = UserStatus.ACTIVE
            totp_type = MFAType.TOTP
            
            if active_status.value == "active" and totp_type.value == "totp":
                self.log_test_result("Enum Values", True, "Enum values match expected strings")
            else:
                self.log_test_result("Enum Values", False, f"Unexpected values: {active_status.value}, {totp_type.value}")
                
        except Exception as e:
            self.log_test_result("Enhancement Functions", False, f"Error: {e}")
    
    def test_documentation_files(self):
        """Test if documentation files exist"""
        print("\n📖 Testing Documentation Files...")
        
        doc_files = [
            ("USER_SERVICE_ENHANCEMENTS.md", "Main enhancement documentation"),
            ("test_comprehensive.py", "Comprehensive test suite"),
            ("test_user_enhancements.py", "User enhancement tests")
        ]
        
        for filename, description in doc_files:
            file_path = f"{self.base_path}/{filename}"
            
            try:
                with open(file_path, 'r') as f:
                    content = f.read()
                
                if len(content) > 100:  # Basic check for non-empty file
                    self.log_test_result(f"Documentation: {filename}", True, f"{description} ({len(content)} chars)")
                else:
                    self.log_test_result(f"Documentation: {filename}", False, "File too short or empty")
                    
            except FileNotFoundError:
                self.log_test_result(f"Documentation: {filename}", False, "File not found")
            except Exception as e:
                self.log_test_result(f"Documentation: {filename}", False, f"Error: {e}")
    
    def generate_validation_report(self):
        """Generate validation report"""
        print("\n" + "=" * 80)
        print("📊 CODE VALIDATION RESULTS REPORT")
        print("=" * 80)
        
        total_tests = len(self.test_results)
        passed_tests = sum(1 for result in self.test_results if result["success"])
        failed_tests = total_tests - passed_tests
        
        print(f"📋 Total Validation Tests: {total_tests}")
        print(f"✅ Passed: {passed_tests}")
        print(f"❌ Failed: {failed_tests}")
        print(f"📈 Success Rate: {(passed_tests/total_tests*100):.1f}%")
        
        # Category breakdown
        categories = {}
        for result in self.test_results:
            test_name = result["test"]
            if "Import" in test_name:
                category = "Imports"
            elif "Database" in test_name or "Schema" in test_name:
                category = "Database"
            elif "API" in test_name or "Router" in test_name or "Endpoint" in test_name:
                category = "API"
            elif "Documentation" in test_name:
                category = "Documentation"
            elif "Main App" in test_name or "Integration" in test_name:
                category = "Integration"
            else:
                category = "Other"
            
            if category not in categories:
                categories[category] = {"passed": 0, "failed": 0}
            
            if result["success"]:
                categories[category]["passed"] += 1
            else:
                categories[category]["failed"] += 1
        
        print(f"\n📝 Validation Categories:")
        for category, stats in categories.items():
            total_cat = stats["passed"] + stats["failed"]
            success_rate = (stats["passed"] / total_cat * 100) if total_cat > 0 else 0
            print(f"   {category}: {stats['passed']}/{total_cat} ({success_rate:.1f}%)")
        
        if failed_tests > 0:
            print(f"\n❌ Failed Validation Details:")
            for result in self.test_results:
                if not result["success"]:
                    print(f"   • {result['test']}: {result['details']}")
        
        print(f"\n🎯 Code Quality Summary:")
        if failed_tests == 0:
            print("🎉 All code validations passed! The enhancements are properly implemented.")
        elif passed_tests > failed_tests:
            print("⚠️ Most validations passed, but some issues found. Review failed tests above.")
        else:
            print("🚨 Multiple validation failures detected. Code may need fixes.")
        
        return passed_tests == total_tests
    
    def run_all_validations(self):
        """Run all code validation tests"""
        print("🔍 Starting Code Validation Suite for User Service Enhancements")
        print("🧪 Testing code structure, imports, and integration...")
        print("=" * 80)
        
        # Run all validation tests
        self.test_import_user_enhancements()
        self.test_import_api_endpoints()
        self.test_permissions_models()
        self.test_database_schema_files()
        self.test_requirements_file()
        self.test_main_app_integration()
        self.test_enhancement_functions()
        self.test_documentation_files()
        
        # Generate final report
        success = self.generate_validation_report()
        return success

def main():
    """Run the code validation suite"""
    validator = CodeValidationTestSuite()
    success = validator.run_all_validations()
    exit(0 if success else 1)

if __name__ == "__main__":
    main()