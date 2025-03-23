import os
import psycopg2
from psycopg2.extensions import ISOLATION_LEVEL_AUTOCOMMIT

def setup_database():
    """Create the PostgreSQL database and tables"""
    # Database configuration
    DB_USER = os.getenv('DB_USER', 'postgres')
    DB_PASSWORD = os.getenv('DB_PASSWORD', 'postgres')
    DB_HOST = os.getenv('DB_HOST', 'localhost')
    DB_PORT = os.getenv('DB_PORT', '5432')
    DB_NAME = os.getenv('DB_NAME', 'stock_annotator')

    # Connect to PostgreSQL server
    conn = psycopg2.connect(
        user=DB_USER,
        password=DB_PASSWORD,
        host=DB_HOST,
        port=DB_PORT
    )
    conn.set_isolation_level(ISOLATION_LEVEL_AUTOCOMMIT)
    cur = conn.cursor()

    try:
        # Create database if it doesn't exist
        cur.execute(f"SELECT 1 FROM pg_database WHERE datname = '{DB_NAME}'")
        exists = cur.fetchone()
        
        if not exists:
            print(f"Creating database {DB_NAME}...")
            cur.execute(f'CREATE DATABASE {DB_NAME}')
            print(f"Database {DB_NAME} created successfully")
        else:
            print(f"Database {DB_NAME} already exists")

    except Exception as e:
        print(f"Error creating database: {str(e)}")
    finally:
        cur.close()
        conn.close()

    # Now connect to the specific database and create tables
    conn = psycopg2.connect(
        dbname=DB_NAME,
        user=DB_USER,
        password=DB_PASSWORD,
        host=DB_HOST,
        port=DB_PORT
    )
    cur = conn.cursor()

    try:
        # Create stocks table
        cur.execute("""
            CREATE TABLE IF NOT EXISTS stocks (
                id SERIAL PRIMARY KEY,
                symbol VARCHAR(10) NOT NULL,
                timestamp TIMESTAMP NOT NULL,
                open FLOAT NOT NULL,
                high FLOAT NOT NULL,
                low FLOAT NOT NULL,
                close FLOAT NOT NULL,
                volume INTEGER NOT NULL,
                UNIQUE(symbol, timestamp)
            )
        """)

        # Create annotations table
        cur.execute("""
            CREATE TABLE IF NOT EXISTS annotations (
                id SERIAL PRIMARY KEY,
                timestamp TIMESTAMP NOT NULL,
                stock VARCHAR(10) NOT NULL,
                signal VARCHAR(20) NOT NULL,
                price FLOAT
            )
        """)

        # Create indexes for better performance
        cur.execute("""
            CREATE INDEX IF NOT EXISTS idx_stocks_symbol_timestamp 
            ON stocks(symbol, timestamp)
        """)
        
        cur.execute("""
            CREATE INDEX IF NOT EXISTS idx_annotations_stock_timestamp 
            ON annotations(stock, timestamp)
        """)

        conn.commit()
        print("Tables and indexes created successfully")

    except Exception as e:
        print(f"Error creating tables: {str(e)}")
        conn.rollback()
    finally:
        cur.close()
        conn.close()

if __name__ == '__main__':
    setup_database() 