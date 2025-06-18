#!/usr/bin/env python3
"""
Debug database connection and table access for user_service
"""

import sys
import os
sys.path.append('/home/stocksadmin/stocksblitz')

from sqlalchemy import text
import os
# Set local database URL for testing
os.environ['TIMESCALEDB_URL'] = 'postgresql://tradmin:tradpass@localhost:5432/tradingdb'
from shared_architecture.db.session import sync_engine, SessionLocal
from app.models.user import User
from shared_architecture.enums import UserRole

def test_database_connection():
    """Test basic database connection"""
    print("🔍 Testing Database Connection...")
    
    try:
        with sync_engine.connect() as connection:
            result = connection.execute(text("SELECT 1"))
            print(f"   ✅ Basic connection: {result.scalar()}")
            
            # Test schema access
            result = connection.execute(text("SELECT current_schema()"))
            print(f"   📊 Current schema: {result.scalar()}")
            
            # List available tables
            result = connection.execute(text("""
                SELECT table_name 
                FROM information_schema.tables 
                WHERE table_schema = 'tradingdb' 
                ORDER BY table_name
            """))
            tables = [row[0] for row in result.fetchall()]
            print(f"   📋 Available tables: {tables}")
            
            return True
            
    except Exception as e:
        print(f"   ❌ Database connection failed: {e}")
        return False

def test_user_model():
    """Test User model and table access"""
    print("\n👤 Testing User Model...")
    
    try:
        # Check User model configuration
        print(f"   📊 User table name: {User.__tablename__}")
        print(f"   📊 User table args: {getattr(User, '__table_args__', 'None')}")
        
        # Test SQLAlchemy session
        session = SessionLocal()
        
        try:
            # Test query without creating anything
            users = session.query(User).limit(1).all()
            print(f"   ✅ User query successful, found {len(users)} users")
            
            # Check table columns
            columns = [column.name for column in User.__table__.columns]
            print(f"   📊 User table columns: {columns}")
            
            return True
            
        except Exception as e:
            print(f"   ❌ User model query failed: {e}")
            return False
            
        finally:
            session.close()
            
    except Exception as e:
        print(f"   ❌ User model initialization failed: {e}")
        return False

def test_enum_values():
    """Test UserRole enum values"""
    print("\n🔧 Testing UserRole Enum...")
    
    try:
        print(f"   📊 UserRole.ADMIN: {UserRole.ADMIN}")
        print(f"   📊 UserRole.EDITOR: {UserRole.EDITOR}")  
        print(f"   📊 UserRole.VIEWER: {UserRole.VIEWER}")
        
        # Test enum value types
        print(f"   📊 ADMIN type: {type(UserRole.ADMIN)}")
        print(f"   📊 ADMIN value: {UserRole.ADMIN.value}")
        
        return True
        
    except Exception as e:
        print(f"   ❌ Enum test failed: {e}")
        return False

def test_user_creation():
    """Test creating a user directly with SQLAlchemy"""
    print("\n📝 Testing Direct User Creation...")
    
    try:
        session = SessionLocal()
        
        # Create a test user
        test_user = User(
            first_name="Debug",
            last_name="Test",
            email="debug.test@example.com",
            phone_number="+9999999999",
            role=UserRole.VIEWER
        )
        
        session.add(test_user)
        session.commit()
        
        print(f"   ✅ User created successfully with ID: {test_user.id}")
        
        # Query it back
        found_user = session.query(User).filter(User.email == "debug.test@example.com").first()
        if found_user:
            print(f"   ✅ User retrieved: {found_user.first_name} {found_user.last_name}")
            print(f"      Role: {found_user.role}")
            
        session.close()
        return True
        
    except Exception as e:
        print(f"   ❌ Direct user creation failed: {e}")
        session.rollback()
        session.close()
        return False

def main():
    """Run all database debug tests"""
    print("=" * 80)
    print("🔍 DATABASE DEBUG TESTS")
    print("=" * 80)
    
    # Test 1: Database connection
    if not test_database_connection():
        print("\n❌ Database connection failed. Cannot continue.")
        return
    
    # Test 2: User model
    if not test_user_model():
        print("\n❌ User model failed. Cannot continue.")
        return
    
    # Test 3: Enum values  
    if not test_enum_values():
        print("\n❌ Enum values failed.")
        return
    
    # Test 4: Direct user creation
    if test_user_creation():
        print("\n✅ All database tests passed!")
        print("   🎯 The issue is likely in the FastAPI endpoints, not the database.")
    else:
        print("\n❌ User creation failed.")
        print("   🎯 The issue is in the database layer or model configuration.")

if __name__ == "__main__":
    main()