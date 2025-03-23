import sqlite3
import pandas as pd
from db_manager import save_stock_data, save_annotation
import os
from datetime import datetime

def migrate_data():
    """Migrate data from SQLite to PostgreSQL"""
    # SQLite database path
    SQLITE_DB = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), "annotations.db")
    
    if not os.path.exists(SQLITE_DB):
        print(f"SQLite database not found at {SQLITE_DB}")
        return
    
    print(f"Starting migration from {SQLITE_DB}")
    
    # Connect to SQLite database
    sqlite_conn = sqlite3.connect(SQLITE_DB)
    
    try:
        # Migrate stock data
        print("Migrating stock data...")
        stock_data = pd.read_sql_query("SELECT * FROM stocks", sqlite_conn)
        if not stock_data.empty:
            success = save_stock_data(stock_data)
            if success:
                print(f"Successfully migrated {len(stock_data)} stock records")
            else:
                print("Failed to migrate stock data")
        else:
            print("No stock data to migrate")
        
        # Migrate annotations
        print("Migrating annotations...")
        annotations = pd.read_sql_query("SELECT * FROM annotations", sqlite_conn)
        if not annotations.empty:
            for _, row in annotations.iterrows():
                success = save_annotation(
                    row['timestamp'],
                    row['stock'],
                    row['signal'],
                    row.get('price')
                )
                if not success:
                    print(f"Failed to migrate annotation {row['id']}")
            print(f"Successfully migrated {len(annotations)} annotations")
        else:
            print("No annotations to migrate")
            
    except Exception as e:
        print(f"Error during migration: {str(e)}")
    finally:
        sqlite_conn.close()
    
    print("Migration completed")

if __name__ == '__main__':
    migrate_data() 