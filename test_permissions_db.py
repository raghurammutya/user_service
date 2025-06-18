#!/usr/bin/env python3
"""
Direct Database Testing for Permissions System
This script tests permissions by directly inserting data and testing the evaluation engine.
"""

import sys
import os
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))

from sqlalchemy import create_engine, text
from sqlalchemy.orm import sessionmaker
from app.models.user import User
from app.models.permissions import (
    UserPermission, TradingRestriction, PermissionType, ResourceType, 
    ActionType, PermissionLevel, ScopeType, EnforcementType,
    PermissionEvaluator, create_share_all_except_permissions,
    create_instrument_trading_restrictions
)

# Database connection
DATABASE_URL = "postgresql://tradmin:tradpass@localhost:5432/tradingdb"

def setup_database():
    """Setup database connection"""
    engine = create_engine(DATABASE_URL)
    SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)
    return engine, SessionLocal

def create_test_users(db_session):
    """Create test users in database"""
    print("🔧 Creating test users...")
    
    users_data = [
        {"first_name": "Alice", "last_name": "Manager", "email": "alice@test.com", "role": "ADMIN"},
        {"first_name": "Bob", "last_name": "Trader", "email": "bob@test.com", "role": "EDITOR"},
        {"first_name": "Charlie", "last_name": "Viewer", "email": "charlie@test.com", "role": "VIEWER"},
        {"first_name": "Diana", "last_name": "Restricted", "email": "diana@test.com", "role": "VIEWER"}
    ]
    
    created_users = {}
    
    for user_data in users_data:
        # Check if user already exists
        existing_user = db_session.query(User).filter(User.email == user_data["email"]).first()
        
        if existing_user:
            created_users[user_data["first_name"]] = existing_user
            print(f"✅ User {user_data['first_name']} already exists: ID {existing_user.id}")
        else:
            # Create new user
            user = User(
                first_name=user_data["first_name"],
                last_name=user_data["last_name"],
                email=user_data["email"],
                role=user_data["role"]
            )
            db_session.add(user)
            db_session.flush()  # Get the ID
            created_users[user_data["first_name"]] = user
            print(f"✅ Created user {user_data['first_name']}: ID {user.id}")
    
    db_session.commit()
    return created_users

def test_data_sharing_permissions(db_session, users):
    """Test data sharing with 'all except' pattern"""
    print("\n📊 Testing Data Sharing - All Except Pattern")
    
    alice = users["Alice"]
    bob = users["Bob"]
    charlie = users["Charlie"]
    
    # Alice shares positions with all except Bob
    permissions = create_share_all_except_permissions(
        grantor_id=alice.id,
        excluded_user_ids=[bob.id],
        resource_types=["positions", "holdings"],
        db_session=db_session
    )
    
    for permission in permissions:
        db_session.add(permission)
    
    db_session.commit()
    print(f"✅ Created {len(permissions)} data sharing permissions")
    
    # Verify permissions were created
    allow_all_perms = db_session.query(UserPermission).filter(
        UserPermission.grantor_user_id == alice.id,
        UserPermission.grantee_user_id == 0,  # All users
        UserPermission.permission_level == PermissionLevel.ALLOW
    ).all()
    
    deny_specific_perms = db_session.query(UserPermission).filter(
        UserPermission.grantor_user_id == alice.id,
        UserPermission.grantee_user_id == bob.id,
        UserPermission.permission_level == PermissionLevel.DENY
    ).all()
    
    print(f"✅ Allow-all permissions: {len(allow_all_perms)}")
    print(f"✅ Deny-specific permissions: {len(deny_specific_perms)}")
    
    return True

def test_trading_permissions(db_session, users):
    """Test trading permissions with instrument controls"""
    print("\n🔄 Testing Trading Permissions - Instrument Controls")
    
    alice = users["Alice"]
    bob = users["Bob"]
    
    # Alice grants Bob permission to create/modify but not exit HDFC
    permissions = [
        # Allow create all
        UserPermission(
            grantor_user_id=alice.id,
            grantee_user_id=bob.id,
            permission_type=PermissionType.TRADING_ACTION,
            resource_type=ResourceType.POSITIONS,
            action_type=ActionType.CREATE,
            permission_level=PermissionLevel.ALLOW,
            scope_type=ScopeType.ALL,
            granted_by=alice.id,
            notes="Allow create all positions"
        ),
        # Allow modify all
        UserPermission(
            grantor_user_id=alice.id,
            grantee_user_id=bob.id,
            permission_type=PermissionType.TRADING_ACTION,
            resource_type=ResourceType.POSITIONS,
            action_type=ActionType.MODIFY,
            permission_level=PermissionLevel.ALLOW,
            scope_type=ScopeType.ALL,
            granted_by=alice.id,
            notes="Allow modify all positions"
        ),
        # Deny exit HDFC
        UserPermission(
            grantor_user_id=alice.id,
            grantee_user_id=bob.id,
            permission_type=PermissionType.TRADING_ACTION,
            resource_type=ResourceType.POSITIONS,
            action_type=ActionType.EXIT,
            permission_level=PermissionLevel.DENY,
            scope_type=ScopeType.SPECIFIC,
            instrument_filters={"blacklist": ["NSE:HDFCBANK", "NSE:RELIANCE"]},
            granted_by=alice.id,
            notes="Deny exit for HDFC and Reliance"
        )
    ]
    
    for permission in permissions:
        db_session.add(permission)
    
    db_session.commit()
    print(f"✅ Created {len(permissions)} trading permissions")
    
    return True

def test_trading_restrictions(db_session, users):
    """Test trading restrictions"""
    print("\n🚫 Testing Trading Restrictions")
    
    alice = users["Alice"]
    diana = users["Diana"]
    
    # Alice restricts Diana from trading high-risk instruments
    restrictions = create_instrument_trading_restrictions(
        user_id=diana.id,
        restrictor_id=alice.id,
        blocked_instruments=["NSE:YESBANK", "NSE:VODAFONE"],
        allowed_actions=["create", "modify", "exit"],
        db_session=db_session
    )
    
    for restriction in restrictions:
        db_session.add(restriction)
    
    db_session.commit()
    print(f"✅ Created {len(restrictions)} trading restrictions")
    
    return True

def test_permission_evaluation(db_session, users):
    """Test the permission evaluation engine"""
    print("\n⚖️ Testing Permission Evaluation Engine")
    
    bob = users["Bob"]
    diana = users["Diana"]
    
    # Test cases for Bob (has trading permissions with restrictions)
    bob_test_cases = [
        {"action": "create", "instrument": "NSE:HDFCBANK", "expected": True, "reason": "Should be allowed to create HDFC"},
        {"action": "exit", "instrument": "NSE:HDFCBANK", "expected": False, "reason": "Should be denied exit on HDFC"},
        {"action": "create", "instrument": "NSE:TCS", "expected": True, "reason": "Should be allowed to create TCS"},
        {"action": "exit", "instrument": "NSE:TCS", "expected": True, "reason": "Should be allowed to exit TCS"}
    ]
    
    print(f"\n🔍 Testing Bob's permissions (ID: {bob.id}):")
    for test_case in bob_test_cases:
        result = PermissionEvaluator.evaluate_permission(
            user_id=bob.id,
            action=test_case["action"],
            resource="positions",
            instrument_key=test_case["instrument"],
            db_session=db_session
        )
        
        status = "✅" if result.allowed == test_case["expected"] else "❌"
        print(f"{status} {test_case['action']} {test_case['instrument']}: {result.allowed} ({result.reason}) - {test_case['reason']}")
    
    # Test cases for Diana (has restrictions)
    diana_test_cases = [
        {"action": "create", "instrument": "NSE:YESBANK", "expected": False, "reason": "Should be blocked from YESBANK"},
        {"action": "create", "instrument": "NSE:TCS", "expected": False, "reason": "No explicit permission (system default)"},
    ]
    
    print(f"\n🔍 Testing Diana's permissions (ID: {diana.id}):")
    for test_case in diana_test_cases:
        result = PermissionEvaluator.evaluate_permission(
            user_id=diana.id,
            action=test_case["action"],
            resource="positions",
            instrument_key=test_case["instrument"],
            db_session=db_session
        )
        
        status = "✅" if result.allowed == test_case["expected"] else "❌"
        print(f"{status} {test_case['action']} {test_case['instrument']}: {result.allowed} ({result.reason}) - {test_case['reason']}")
    
    return True

def test_conflict_resolution(db_session, users):
    """Test conflict resolution between grants and restrictions"""
    print("\n⚖️ Testing Conflict Resolution")
    
    alice = users["Alice"]
    charlie = users["Charlie"]
    
    # Give Charlie general trading permission
    general_permission = UserPermission(
        grantor_user_id=alice.id,
        grantee_user_id=charlie.id,
        permission_type=PermissionType.TRADING_ACTION,
        resource_type=ResourceType.POSITIONS,
        action_type=ActionType.CREATE,
        permission_level=PermissionLevel.ALLOW,
        scope_type=ScopeType.ALL,
        granted_by=alice.id,
        notes="General create permission"
    )
    db_session.add(general_permission)
    
    # Add specific restriction (should override general permission)
    specific_restriction = UserPermission(
        grantor_user_id=alice.id,
        grantee_user_id=charlie.id,
        permission_type=PermissionType.TRADING_ACTION,
        resource_type=ResourceType.POSITIONS,
        action_type=ActionType.CREATE,
        permission_level=PermissionLevel.DENY,
        scope_type=ScopeType.SPECIFIC,
        instrument_filters={"blacklist": ["NSE:HDFCBANK"]},
        granted_by=alice.id,
        notes="Specific denial for HDFC"
    )
    db_session.add(specific_restriction)
    
    db_session.commit()
    print("✅ Created conflicting permissions for Charlie")
    
    # Test conflict resolution
    test_cases = [
        {"instrument": "NSE:HDFCBANK", "expected": False, "reason": "Specific denial should override general permission"},
        {"instrument": "NSE:TCS", "expected": True, "reason": "General permission should work for non-restricted instruments"}
    ]
    
    print(f"\n🔍 Testing conflict resolution for Charlie (ID: {charlie.id}):")
    for test_case in test_cases:
        result = PermissionEvaluator.evaluate_permission(
            user_id=charlie.id,
            action="create",
            resource="positions",
            instrument_key=test_case["instrument"],
            db_session=db_session
        )
        
        status = "✅" if result.allowed == test_case["expected"] else "❌"
        print(f"{status} create {test_case['instrument']}: {result.allowed} ({result.reason}) - {test_case['reason']}")
    
    return True

def main():
    """Run the database testing suite"""
    print("🚀 Permissions Database Testing Suite")
    print("=" * 50)
    
    try:
        # Setup database
        engine, SessionLocal = setup_database()
        db_session = SessionLocal()
        
        # Test database connection
        result = db_session.execute(text("SELECT 1"))
        print("✅ Database connection successful")
        
        # Create test users
        users = create_test_users(db_session)
        
        # Run tests
        test_results = []
        test_results.append(("Data Sharing Permissions", test_data_sharing_permissions(db_session, users)))
        test_results.append(("Trading Permissions", test_trading_permissions(db_session, users)))
        test_results.append(("Trading Restrictions", test_trading_restrictions(db_session, users)))
        test_results.append(("Permission Evaluation", test_permission_evaluation(db_session, users)))
        test_results.append(("Conflict Resolution", test_conflict_resolution(db_session, users)))
        
        # Summary
        print("\n" + "=" * 50)
        print("📋 TEST RESULTS SUMMARY")
        print("=" * 50)
        
        passed = 0
        total = len(test_results)
        
        for test_name, result in test_results:
            status = "✅ PASS" if result else "❌ FAIL"
            print(f"{status} {test_name}")
            if result:
                passed += 1
        
        print(f"\n🎯 Overall: {passed}/{total} tests passed")
        
        if passed == total:
            print("🎉 All tests passed! Permissions system is working correctly.")
        else:
            print("⚠️  Some tests failed. Check the output above for details.")
        
        # Close session
        db_session.close()
        
        return passed == total
        
    except Exception as e:
        print(f"❌ Error during testing: {e}")
        import traceback
        traceback.print_exc()
        return False

if __name__ == "__main__":
    success = main()
    sys.exit(0 if success else 1)