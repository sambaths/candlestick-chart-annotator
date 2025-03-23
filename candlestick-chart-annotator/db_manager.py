from sqlalchemy import create_engine, Column, Integer, String, Float, DateTime, ForeignKey, Text, UniqueConstraint, func
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import sessionmaker, scoped_session
from sqlalchemy.pool import QueuePool
from sqlalchemy.sql import text
from datetime import datetime
import pandas as pd
import os
import threading
from contextlib import contextmanager
import time
import traceback

# Create the base class for declarative models
Base = declarative_base()

# Database configuration
DB_USER = os.getenv('DB_USER', 'postgres')
DB_PASSWORD = os.getenv('DB_PASSWORD', 'postgres')
DB_HOST = os.getenv('DB_HOST', 'localhost')
DB_PORT = os.getenv('DB_PORT', '5432')
DB_NAME = os.getenv('DB_NAME', 'stock_annotator')

# Create database URL
DATABASE_URL = f"postgresql://{DB_USER}:{DB_PASSWORD}@{DB_HOST}:{DB_PORT}/{DB_NAME}"

# Define models
class Stock(Base):
    __tablename__ = 'stocks'
    
    id = Column(Integer, primary_key=True)
    symbol = Column(String(), nullable=False)
    timestamp = Column(DateTime, nullable=False)
    open = Column(Float, nullable=False)
    high = Column(Float, nullable=False)
    low = Column(Float, nullable=False)
    close = Column(Float, nullable=False)
    volume = Column(Integer, nullable=False)
    resolution = Column(String(), nullable=False, default='1D')
    
    __table_args__ = (
        UniqueConstraint('symbol', 'timestamp', name='uix_symbol_timestamp'),
    )

class Annotation(Base):
    __tablename__ = 'annotations'
    
    id = Column(Integer, primary_key=True)
    timestamp = Column(DateTime, nullable=False)
    stock = Column(String(), nullable=False)
    signal = Column(String(), nullable=False)
    price = Column(Float)
    reason = Column(Text, nullable=True)  # Adding reason column for annotation reasons

class DBManager:
    _instance = None
    _lock = threading.Lock()

    @classmethod
    def get_instance(cls):
        """Singleton pattern to ensure only one instance exists"""
        if cls._instance is None:
            with cls._lock:
                if cls._instance is None:
                    cls._instance = DBManager()
        return cls._instance

    def __init__(self):
        self.engine = create_engine(
            DATABASE_URL,
            poolclass=QueuePool,
            pool_size=5,
            max_overflow=10,
            pool_timeout=30,
            pool_recycle=1800
        )
        self.Session = scoped_session(sessionmaker(bind=self.engine))

    @contextmanager
    def get_session(self):
        """Context manager for database sessions"""
        session = self.Session()
        try:
            yield session
            session.commit()
        except Exception:
            session.rollback()
            raise
        finally:
            session.close()

    def init_db(self):
        """Initialize the database by creating all tables"""
        Base.metadata.create_all(self.engine)

    def drop_and_recreate_tables(self):
        """Drop all tables and recreate them"""
        Base.metadata.drop_all(self.engine)
        Base.metadata.create_all(self.engine)

    def get_available_stocks(self):
        """Get list of available stocks"""
        try:
            with self.get_session() as session:
                # Use distinct to avoid duplicates
                stocks = session.query(Stock.symbol.distinct()).all()
                return sorted([stock[0] for stock in stocks])
        except Exception as e:
            print(f"Error getting available stocks: {str(e)}")
            traceback.print_exc()
            return []

    def get_stock_data(self, symbol, date=None, limit=None):
        """Get stock data for a specific symbol and date"""
        try:
            with self.get_session() as session:
                query = session.query(Stock).filter(Stock.symbol == symbol)
                
                if date:
                    print(f"Filtering by date: {date}")
                    # Try to parse the date if it's a string
                    if isinstance(date, str):
                        try:
                            # Assuming date format is YYYY-MM-DD
                            date_obj = datetime.strptime(date, '%Y-%m-%d').date()
                            print(f"Parsed date: {date_obj}")
                            query = query.filter(func.date(Stock.timestamp) == date_obj)
                        except ValueError as e:
                            print(f"Error parsing date string: {e}")
                            # If date parsing fails, try to use the string directly
                            query = query.filter(func.date(Stock.timestamp) == date)
                    else:
                        # If date is already a date object, use it directly
                        query = query.filter(func.date(Stock.timestamp) == date)
                
                # Order by timestamp
                query = query.order_by(Stock.timestamp)
                
                # Apply limit if specified
                if limit:
                    query = query.limit(limit)
                
                # Execute the query and convert to DataFrame
                result = pd.read_sql(query.statement, session.bind)
                print(f"Query returned {len(result)} rows")
                return result
        except Exception as e:
            print(f"Error in get_stock_data: {e}")
            traceback.print_exc()
            return pd.DataFrame()  # Return empty DataFrame on error

    def get_stock_date_range(self, symbol):
        """Get the date range for a stock"""
        with self.get_session() as session:
            result = session.query(
                func.min(Stock.timestamp),
                func.max(Stock.timestamp)
            ).filter(Stock.symbol == symbol).first()
            return result[0], result[1]

    def save_stock_data(self, df):
        """Save stock data to database"""
        try:
            with self.get_session() as session:
                records = df.to_dict('records')
                stock_objects = []
                for record in records:
                    stock = Stock(
                        symbol=record['symbol'],
                        timestamp=record['timestamp'] if 'timestamp' in record else record['date'],
                        open=record['open'],
                        high=record['high'],
                        low=record['low'],
                        close=record['close'],
                        volume=record['volume'],
                        resolution=record.get('resolution', '1D')
                    )
                    stock_objects.append(stock)
                session.bulk_save_objects(stock_objects)
                return True
        except Exception as e:
            print(f"Error saving stock data: {str(e)}")
            return False

    def save_annotation(self, timestamp, stock, signal, price=None, reason=None):
        """Save annotation to database"""
        try:
            with self.get_session() as session:
                annotation = Annotation(
                    timestamp=timestamp,
                    stock=stock,
                    signal=signal,
                    price=price,
                    reason=reason
                )
                session.add(annotation)
                return True
        except Exception as e:
            print(f"Error saving annotation: {str(e)}")
            return False

    def delete_annotation(self, annotation_id):
        """Delete a specific annotation by ID"""
        try:
            with self.get_session() as session:
                annotation = session.query(Annotation).filter(Annotation.id == annotation_id).first()
                if annotation:
                    session.delete(annotation)
                    return True
                return False
        except Exception as e:
            print(f"Error deleting annotation: {str(e)}")
            return False

    def delete_last_annotation(self):
        """Delete the most recent annotation"""
        try:
            with self.get_session() as session:
                last_annotation = session.query(Annotation).order_by(Annotation.id.desc()).first()
                if last_annotation:
                    session.delete(last_annotation)
                    return True
                return False
        except Exception as e:
            print(f"Error deleting last annotation: {str(e)}")
            return False

    def get_annotations(self):
        """Get all annotations"""
        with self.get_session() as session:
            annotations = session.query(Annotation).all()
            return pd.DataFrame([{
                'id': a.id,
                'timestamp': a.timestamp,
                'stock': a.stock,
                'signal': a.signal,
                'price': a.price,
                'reason': a.reason
            } for a in annotations])

    def get_annotation_status(self):
        """Get annotation status for all stocks"""
        try:
            with self.get_session() as session:
                stocks = self.get_available_stocks()
                if not stocks:
                    return {}
                
                result = {}
                for stock in stocks:
                    total_dates = session.query(
                        func.count(func.distinct(func.date(Stock.timestamp)))
                    ).filter(Stock.symbol == stock).scalar()
                    
                    annotated_dates = session.query(
                        func.distinct(func.date(Annotation.timestamp))
                    ).filter(Annotation.stock == stock).all()
                    annotated_dates = [date[0] for date in annotated_dates]
                    
                    completion = len(annotated_dates) / total_dates if total_dates > 0 else 0
                    
                    all_dates = session.query(
                        func.distinct(func.date(Stock.timestamp))
                    ).filter(Stock.symbol == stock).all()
                    all_dates = [date[0] for date in all_dates]
                    
                    pending_dates = [date for date in all_dates if date not in annotated_dates]
                    
                    result[stock] = {
                        'completion': completion,
                        'total_dates': total_dates,
                        'annotated_dates': annotated_dates,
                        'pending_dates': pending_dates
                    }
                
                return result
        except Exception as e:
            print(f"Error getting annotation status: {str(e)}")
            return {}

    def delete_stock_data(self, symbol):
        """Delete all data for a specific stock from the database"""
        try:
            with self.get_session() as session:
                session.query(Stock).filter(Stock.symbol == symbol).delete()
                session.query(Annotation).filter(Annotation.stock == symbol).delete()
                return True
        except Exception as e:
            print(f"Error deleting stock data: {str(e)}")
            return False

    def get_stocks_summary(self):
        """Get summary of available stock data"""
        try:
            with self.get_session() as session:
                query = """
                    SELECT 
                        symbol,
                        MIN(timestamp) as start_date,
                        MAX(timestamp) as end_date,
                        resolution,
                        COUNT(*) as row_count
                    FROM stocks
                    GROUP BY symbol, resolution
                    ORDER BY symbol
                """
                result = session.execute(text(query))
                
                summary = []
                for row in result:
                    summary.append({
                        'symbol': row.symbol,
                        'start_date': row.start_date.strftime('%Y-%m-%d'),
                        'end_date': row.end_date.strftime('%Y-%m-%d'),
                        'resolution': row.resolution,
                        'row_count': row.row_count
                    })
                return summary
        except Exception as e:
            print(f"Error getting stocks summary: {str(e)}")
            return []

# Create a singleton instance
db = DBManager.get_instance()

# Initialize the database
db.init_db()
# db.drop_and_recreate_tables()

# Export functions for backward compatibility
get_available_stocks = db.get_available_stocks
get_stock_data = db.get_stock_data
get_stock_date_range = db.get_stock_date_range
save_stock_data = db.save_stock_data
save_annotation = db.save_annotation
delete_annotation = db.delete_annotation
delete_last_annotation = db.delete_last_annotation
get_annotations = db.get_annotations
get_annotation_status = db.get_annotation_status
delete_stock_data = db.delete_stock_data
get_stocks_summary = db.get_stocks_summary 