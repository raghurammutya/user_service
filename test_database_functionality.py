#!/usr/bin/env python3
"""
Database Functionality Tests - Tests database operations and constraints
"""

import psycopg2
import json
from datetime import datetime, date, timedelta

class DatabaseFunctionalityTests:
    def __init__(self):
        self.db_config = {
            'host': 'localhost',
            'port': 5432,
            'database': 'tradingdb',
            'user': 'tradmin',
            'password': 'tradpass'
        }
        self.test_results = []
        
    def log_test_result(self, test_name: str, success: bool, details: str = ""):
        """Log test results"""
        self.test_results.append({
            "test": test_name,
            "success": success,
            "details": details
        })
        status = "✅ PASS" if success else "❌ FAIL"
        print(f"{status} {test_name}")
        if details:
            print(f"    {details}")
    
    def test_database_connection(self):
        """Test database connectivity"""
        print("\n🔌 Testing Database Connection...")
        
        try:
            conn = psycopg2.connect(**self.db_config)
            cur = conn.cursor()
            
            # Test basic query
            cur.execute("SELECT 1 as test")
            result = cur.fetchone()
            
            if result and result[0] == 1:
                self.log_test_result("Database Connection", True, "Connected successfully")
                conn.close()
                return True
            else:
                self.log_test_result("Database Connection", False, "Query failed")
                return False
                
        except Exception as e:
            self.log_test_result("Database Connection", False, f"Connection error: {e}")
            return False
    
    def test_enhancement_tables_exist(self):
        """Test if all enhancement tables exist"""
        print("\n🗄️ Testing Enhancement Tables Existence...")
        
        try:
            conn = psycopg2.connect(**self.db_config)
            cur = conn.cursor()
            
            enhancement_tables = [
                'user_status_history',
                'user_onboarding', 
                'user_mfa',
                'user_sessions',
                'user_activities',
                'user_preferences',
                'organizations',
                'user_organization_roles',
                'compliance_profiles',
                'user_metrics',
                'audit_trail'
            ]
            
            existing_tables = []
            missing_tables = []
            
            for table in enhancement_tables:
                cur.execute("""
                    SELECT EXISTS (
                        SELECT 1 FROM information_schema.tables 
                        WHERE table_schema = 'tradingdb' 
                        AND table_name = %s
                    )
                """, (table,))
                
                exists = cur.fetchone()[0]
                if exists:
                    existing_tables.append(table)
                    self.log_test_result(f"Table Exists: {table}", True, "Found in database")
                else:
                    missing_tables.append(table)
                    self.log_test_result(f"Table Exists: {table}", False, "Missing from database")
            
            conn.close()
            
            if len(existing_tables) == len(enhancement_tables):
                self.log_test_result("All Enhancement Tables", True, f"All {len(enhancement_tables)} tables exist")
                return True
            else:
                self.log_test_result("All Enhancement Tables", False, f"Missing: {missing_tables}")
                return False
                
        except Exception as e:
            self.log_test_result("Enhancement Tables Existence", False, f"Error: {e}")
            return False
    
    def test_table_constraints(self):
        """Test database constraints and foreign keys"""
        print("\n🔗 Testing Database Constraints...")
        
        try:
            conn = psycopg2.connect(**self.db_config)
            cur = conn.cursor()
            
            # Test foreign key constraints exist
            constraint_queries = [
                ("user_mfa foreign key", """
                    SELECT constraint_name FROM information_schema.table_constraints 
                    WHERE table_schema = 'tradingdb' AND table_name = 'user_mfa' 
                    AND constraint_type = 'FOREIGN KEY'
                """),
                ("user_sessions foreign key", """
                    SELECT constraint_name FROM information_schema.table_constraints 
                    WHERE table_schema = 'tradingdb' AND table_name = 'user_sessions' 
                    AND constraint_type = 'FOREIGN KEY'
                """),
                ("organizations constraints", """
                    SELECT constraint_name FROM information_schema.table_constraints 
                    WHERE table_schema = 'tradingdb' AND table_name = 'organizations'
                """)
            ]
            
            for constraint_name, query in constraint_queries:
                cur.execute(query)
                constraints = cur.fetchall()
                
                if constraints:
                    self.log_test_result(f"Constraints: {constraint_name}", True, f"Found {len(constraints)} constraints")
                else:
                    self.log_test_result(f"Constraints: {constraint_name}", False, "No constraints found")
            
            conn.close()
            return True
            
        except Exception as e:
            self.log_test_result("Database Constraints", False, f"Error: {e}")
            return False
    
    def test_jsonb_functionality(self):
        """Test JSONB column functionality"""
        print("\n📄 Testing JSONB Functionality...")
        
        try:
            conn = psycopg2.connect(**self.db_config)
            cur = conn.cursor()
            
            # Test JSONB operations
            test_json = {"test": "value", "number": 123, "array": [1, 2, 3]}
            
            # Create a temporary test
            cur.execute("""
                SELECT jsonb_extract_path_text(%s::jsonb, 'test') as extracted_value
            """, (json.dumps(test_json),))
            
            result = cur.fetchone()
            if result and result[0] == "value":
                self.log_test_result("JSONB Extract", True, "JSONB extraction works")
            else:
                self.log_test_result("JSONB Extract", False, "JSONB extraction failed")
            
            # Test JSONB array operations
            cur.execute("""
                SELECT jsonb_array_length(%s::jsonb -> 'array') as array_length
            """, (json.dumps(test_json),))
            
            result = cur.fetchone()
            if result and result[0] == 3:
                self.log_test_result("JSONB Array Operations", True, "Array operations work")
            else:
                self.log_test_result("JSONB Array Operations", False, "Array operations failed")
            
            conn.close()
            return True
            
        except Exception as e:
            self.log_test_result("JSONB Functionality", False, f"Error: {e}")
            return False
    
    def test_data_insertion(self):
        """Test inserting sample data into enhancement tables"""
        print("\n📝 Testing Data Insertion...")
        
        try:
            conn = psycopg2.connect(**self.db_config)
            cur = conn.cursor()
            
            # Insert test user if not exists
            cur.execute("""
                INSERT INTO tradingdb.users (first_name, last_name, email, phone_number, role)
                VALUES ('Test', 'User', 'test@functionality.com', '+15551234567', 'VIEWER')
                ON CONFLICT (email) DO UPDATE SET first_name = EXCLUDED.first_name
                RETURNING id
            """)
            user_id = cur.fetchone()[0]
            self.log_test_result("Insert Test User", True, f"User ID: {user_id}")
            
            # Test user preferences insertion
            cur.execute("""
                INSERT INTO tradingdb.user_preferences (user_id, theme, language, timezone)
                VALUES (%s, 'dark', 'en', 'UTC')
                ON CONFLICT (user_id) DO UPDATE SET theme = EXCLUDED.theme
            """, (user_id,))
            self.log_test_result("Insert User Preferences", True, "Preferences inserted")
            
            # Test user activity insertion
            cur.execute("""
                INSERT INTO tradingdb.user_activities 
                (user_id, activity_type, resource_type, action_details, timestamp)
                VALUES (%s, 'test', 'user', %s, %s)
            """, (user_id, json.dumps({"test": True}), datetime.now()))
            self.log_test_result("Insert User Activity", True, "Activity logged")
            
            # Test organization insertion
            cur.execute("""
                INSERT INTO tradingdb.organizations 
                (name, display_name, organization_type, subscription_tier, created_by)
                VALUES ('Test Org', 'Test Organization', 'trading_firm', 'basic', %s)
                ON CONFLICT DO NOTHING
                RETURNING id
            """, (user_id,))
            
            org_result = cur.fetchone()
            if org_result:
                org_id = org_result[0]
                self.log_test_result("Insert Organization", True, f"Organization ID: {org_id}")
            else:
                self.log_test_result("Insert Organization", True, "Organization already exists")
            
            conn.commit()
            conn.close()
            return True
            
        except Exception as e:
            self.log_test_result("Data Insertion", False, f"Error: {e}")
            return False
    
    def test_data_retrieval(self):
        """Test retrieving data with joins and JSONB queries"""
        print("\n🔍 Testing Data Retrieval...")
        
        try:
            conn = psycopg2.connect(**self.db_config)
            cur = conn.cursor()
            
            # Test user preferences retrieval
            cur.execute("""
                SELECT u.first_name, up.theme, up.language, up.email_notifications
                FROM tradingdb.users u
                LEFT JOIN tradingdb.user_preferences up ON u.id = up.user_id
                WHERE u.email = 'test@functionality.com'
            """)
            
            result = cur.fetchone()
            if result:
                self.log_test_result("Retrieve User Preferences", True, f"User: {result[0]}, Theme: {result[1]}")
            else:
                self.log_test_result("Retrieve User Preferences", False, "No data found")
            
            # Test activity retrieval with JSONB
            cur.execute("""
                SELECT activity_type, action_details->>'test' as test_value
                FROM tradingdb.user_activities
                WHERE user_id = (SELECT id FROM tradingdb.users WHERE email = 'test@functionality.com')
                AND activity_type = 'test'
                LIMIT 1
            """)
            
            result = cur.fetchone()
            if result and result[1] == 'true':  # JSON boolean becomes string
                self.log_test_result("Retrieve Activity with JSONB", True, "JSONB query works")
            else:
                self.log_test_result("Retrieve Activity with JSONB", False, "JSONB query failed")
            
            # Test organization join
            cur.execute("""
                SELECT o.name, o.subscription_tier, u.first_name as creator
                FROM tradingdb.organizations o
                JOIN tradingdb.users u ON o.created_by = u.id
                WHERE o.name = 'Test Org'
            """)
            
            result = cur.fetchone()
            if result:
                self.log_test_result("Retrieve Organization with Join", True, f"Org: {result[0]}, Creator: {result[2]}")
            else:
                self.log_test_result("Retrieve Organization with Join", False, "No organization data")
            
            conn.close()
            return True
            
        except Exception as e:
            self.log_test_result("Data Retrieval", False, f"Error: {e}")
            return False
    
    def test_constraint_violations(self):
        """Test constraint violations are properly handled"""
        print("\n🚨 Testing Constraint Violations...")
        
        try:
            conn = psycopg2.connect(**self.db_config)
            cur = conn.cursor()
            
            # Test foreign key constraint violation
            try:
                cur.execute("""
                    INSERT INTO tradingdb.user_mfa (user_id, mfa_type)
                    VALUES (99999, 'totp')
                """)
                conn.commit()
                self.log_test_result("Foreign Key Violation", False, "Should have failed but didn't")
            except psycopg2.IntegrityError:
                conn.rollback()
                self.log_test_result("Foreign Key Violation", True, "Correctly rejected invalid user_id")
            
            # Test check constraint violation (if any)
            try:
                cur.execute("""
                    INSERT INTO tradingdb.user_mfa (user_id, mfa_type)
                    VALUES ((SELECT id FROM tradingdb.users WHERE email = 'test@functionality.com'), 'invalid_type')
                """)
                conn.commit()
                self.log_test_result("Check Constraint Violation", False, "Should have failed but didn't")
            except psycopg2.IntegrityError:
                conn.rollback()
                self.log_test_result("Check Constraint Violation", True, "Correctly rejected invalid MFA type")
            except psycopg2.DataError:
                conn.rollback()
                self.log_test_result("Check Constraint Violation", True, "Correctly rejected invalid MFA type (data error)")
            
            conn.close()
            return True
            
        except Exception as e:
            self.log_test_result("Constraint Violations", False, f"Error: {e}")
            return False
    
    def generate_database_report(self):
        """Generate database test report"""
        print("\n" + "=" * 80)
        print("📊 DATABASE FUNCTIONALITY TEST RESULTS")
        print("=" * 80)
        
        total_tests = len(self.test_results)
        passed_tests = sum(1 for result in self.test_results if result["success"])
        failed_tests = total_tests - passed_tests
        
        print(f"📋 Total Database Tests: {total_tests}")
        print(f"✅ Passed: {passed_tests}")
        print(f"❌ Failed: {failed_tests}")
        print(f"📈 Success Rate: {(passed_tests/total_tests*100):.1f}%")
        
        # Category breakdown
        categories = {}
        for result in self.test_results:
            test_name = result["test"]
            if "Connection" in test_name:
                category = "Connectivity"
            elif "Table" in test_name or "Constraint" in test_name:
                category = "Schema"
            elif "JSONB" in test_name:
                category = "JSONB"
            elif "Insert" in test_name or "Retrieve" in test_name:
                category = "Data Operations"
            elif "Violation" in test_name:
                category = "Constraints"
            else:
                category = "Other"
            
            if category not in categories:
                categories[category] = {"passed": 0, "failed": 0}
            
            if result["success"]:
                categories[category]["passed"] += 1
            else:
                categories[category]["failed"] += 1
        
        print(f"\n📝 Database Test Categories:")
        for category, stats in categories.items():
            total_cat = stats["passed"] + stats["failed"]
            success_rate = (stats["passed"] / total_cat * 100) if total_cat > 0 else 0
            print(f"   {category}: {stats['passed']}/{total_cat} ({success_rate:.1f}%)")
        
        if failed_tests > 0:
            print(f"\n❌ Failed Database Tests:")
            for result in self.test_results:
                if not result["success"]:
                    print(f"   • {result['test']}: {result['details']}")
        
        print(f"\n🎯 Database Summary:")
        if failed_tests == 0:
            print("🎉 All database tests passed! Enhancement schema is working correctly.")
        elif passed_tests > failed_tests:
            print("⚠️ Most database tests passed, but some issues found.")
        else:
            print("🚨 Multiple database failures detected. Schema may need fixes.")
        
        return passed_tests == total_tests
    
    def run_all_database_tests(self):
        """Run all database functionality tests"""
        print("🗄️ Starting Database Functionality Tests")
        print("🔍 Testing database schema, constraints, and operations...")
        print("=" * 80)
        
        # Run all database tests
        if self.test_database_connection():
            self.test_enhancement_tables_exist()
            self.test_table_constraints()
            self.test_jsonb_functionality()
            self.test_data_insertion()
            self.test_data_retrieval()
            self.test_constraint_violations()
        else:
            print("⚠️ Database connection failed, skipping other tests")
        
        # Generate report
        success = self.generate_database_report()
        return success

def main():
    """Run database functionality tests"""
    tester = DatabaseFunctionalityTests()
    success = tester.run_all_database_tests()
    exit(0 if success else 1)

if __name__ == "__main__":
    main()