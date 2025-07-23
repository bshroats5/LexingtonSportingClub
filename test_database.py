# test_database.py
import sqlite3
import os

def test_database():
    db_path = 'lsc_database.db'
    
    # Check if database file exists
    if not os.path.exists(db_path):
        print("❌ Database file not found!")
        print("Run your database creation script first:")
        print("python your_database_script.py")
        return False
    
    print("✅ Database file found")
    
    try:
        conn = sqlite3.connect(db_path)
        cursor = conn.cursor()
        
        # Get all tables
        cursor.execute("SELECT name FROM sqlite_master WHERE type='table';")
        tables = cursor.fetchall()
        
        print(f"📋 Found {len(tables)} tables:")
        for table in tables:
            print(f"  - {table[0]}")
            
            # Get row count for each table
            cursor.execute(f"SELECT COUNT(*) FROM [{table[0]}]")
            count = cursor.fetchone()[0]
            print(f"    ({count} rows)")
        
        conn.close()
        return True
        
    except Exception as e:
        print(f"❌ Database error: {e}")
        return False

if __name__ == "__main__":
    test_database()