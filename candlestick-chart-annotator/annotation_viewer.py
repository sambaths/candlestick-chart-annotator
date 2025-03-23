#!/usr/bin/env python3
"""
Annotation Viewer - A script to display and analyze annotation data from the database.
"""

import os
import sys
import argparse
import pandas as pd
from datetime import datetime
from tabulate import tabulate
import matplotlib.pyplot as plt
import seaborn as sns
from sqlalchemy import create_engine, text
import json

# Add the parent directory to sys.path so we can import the db_manager module
sys.path.insert(0, os.path.abspath(os.path.dirname(__file__)))

try:
    from db_manager import DBManager, Annotation, Stock
except ImportError as e:
    print(f"Error importing DBManager: {e}")
    print("Using direct database connection instead.")
    DBManager = None

class AnnotationViewer:
    """A class to view and analyze annotation data."""
    
    def __init__(self, db_url=None):
        """Initialize the viewer, either with a DBManager or direct DB connection."""
        self.db_manager = None
        self.engine = None
        
        if DBManager is not None:
            try:
                self.db_manager = DBManager()
                print("Using DBManager for database access.")
            except Exception as e:
                print(f"Error initializing DBManager: {e}")
                
        if self.db_manager is None and db_url:
            try:
                self.engine = create_engine(db_url)
                print(f"Connected directly to database: {db_url}")
            except Exception as e:
                print(f"Error connecting to database: {e}")
        
        if self.db_manager is None and self.engine is None:
            print("No database connection available. Please provide a valid database URL.")
            sys.exit(1)
    
    def get_annotations(self, stock=None, signal=None, start_date=None, end_date=None):
        """Fetch annotations with optional filtering."""
        try:
            if self.db_manager:
                # Use DBManager to get annotations
                df = self.db_manager.get_annotations()
                
                # Apply filters if provided
                if stock:
                    df = df[df['stock'] == stock]
                if signal:
                    df = df[df['signal'] == signal]
                if start_date:
                    start_date = pd.to_datetime(start_date)
                    df = df[df['timestamp'] >= start_date]
                if end_date:
                    end_date = pd.to_datetime(end_date)
                    df = df[df['timestamp'] <= end_date]
                
                return df
            
            elif self.engine:
                # Direct SQL query to get annotations
                query = "SELECT * FROM annotations"
                conditions = []
                
                if stock:
                    conditions.append(f"stock = '{stock}'")
                if signal:
                    conditions.append(f"signal = '{signal}'")
                if start_date:
                    conditions.append(f"timestamp >= '{start_date}'")
                if end_date:
                    conditions.append(f"timestamp <= '{end_date}'")
                
                if conditions:
                    query += " WHERE " + " AND ".join(conditions)
                
                query += " ORDER BY timestamp DESC"
                
                df = pd.read_sql(query, self.engine)
                
                # Convert timestamp to datetime
                if 'timestamp' in df.columns:
                    df['timestamp'] = pd.to_datetime(df['timestamp'])
                
                return df
            
        except Exception as e:
            print(f"Error fetching annotations: {e}")
            return pd.DataFrame()
    
    def display_annotations(self, annotations_df, format='table', output_file=None):
        """Display annotations in the specified format."""
        if annotations_df.empty:
            print("No annotations found.")
            return
        
        # Create a formatted version for display
        display_df = annotations_df.copy()
        
        # Format timestamp
        if 'timestamp' in display_df.columns:
            display_df['timestamp'] = display_df['timestamp'].dt.strftime('%Y-%m-%d %H:%M:%S')
        
        # Format price
        if 'price' in display_df.columns:
            display_df['price'] = display_df['price'].apply(lambda x: f"₹{float(x):.2f}" if pd.notna(x) else 'N/A')
        
        # Add a color-coded signal column for CSV output
        if format == 'csv':
            # Just use the original signal
            pass
        
        # Handle different output formats
        if format == 'table':
            print("\n=== Annotations ===")
            print(tabulate(display_df, headers='keys', tablefmt='psql', showindex=False))
            
            # Print summary statistics
            self.print_summary(annotations_df)
            
        elif format == 'csv':
            if output_file:
                display_df.to_csv(output_file, index=False)
                print(f"Annotations saved to {output_file}")
            else:
                print(display_df.to_csv(index=False))
                
        elif format == 'json':
            # Convert timestamps to string for JSON serialization
            json_df = annotations_df.copy()
            if 'timestamp' in json_df.columns:
                json_df['timestamp'] = json_df['timestamp'].dt.strftime('%Y-%m-%d %H:%M:%S')
            
            if output_file:
                with open(output_file, 'w') as f:
                    f.write(json_df.to_json(orient='records', indent=2))
                print(f"Annotations saved to {output_file}")
            else:
                print(json.dumps(json.loads(json_df.to_json(orient='records')), indent=2))
                
        elif format == 'plot':
            self.plot_annotations(annotations_df, output_file)
    
    def print_summary(self, df):
        """Print summary statistics about the annotations."""
        if df.empty:
            return
        
        print("\n=== Summary Statistics ===")
        
        # Count by signal type
        signal_counts = df['signal'].value_counts()
        print("\nSignal Counts:")
        for signal, count in signal_counts.items():
            print(f"  {signal}: {count}")
        
        # Count by stock
        stock_counts = df['stock'].value_counts()
        print("\nStock Counts:")
        for stock, count in stock_counts.head(5).items():
            print(f"  {stock}: {count}")
        
        if len(stock_counts) > 5:
            print(f"  ... and {len(stock_counts) - 5} more stocks")
        
        # Date range
        if 'timestamp' in df.columns and not df['timestamp'].empty:
            min_date = df['timestamp'].min()
            max_date = df['timestamp'].max()
            print(f"\nDate Range: {min_date.strftime('%Y-%m-%d')} to {max_date.strftime('%Y-%m-%d')}")
        
        # Annotations count by month
        if 'timestamp' in df.columns:
            df['month'] = df['timestamp'].dt.strftime('%Y-%m')
            monthly_counts = df['month'].value_counts().sort_index()
            if not monthly_counts.empty:
                print("\nAnnotations by Month:")
                for month, count in monthly_counts.items():
                    print(f"  {month}: {count}")
    
    def plot_annotations(self, df, output_file=None):
        """Create visualizations of annotation data."""
        if df.empty:
            print("No data to plot.")
            return
        
        try:
            # Set the style
            sns.set(style="whitegrid")
            
            # Create a figure with multiple subplots
            fig, axs = plt.subplots(2, 2, figsize=(12, 10))
            
            # Plot 1: Signal distribution
            sns.countplot(data=df, x='signal', ax=axs[0, 0])
            axs[0, 0].set_title('Distribution of Signal Types')
            axs[0, 0].set_xticklabels(axs[0, 0].get_xticklabels(), rotation=45)
            
            # Plot 2: Annotations over time
            if 'timestamp' in df.columns:
                df['date'] = df['timestamp'].dt.date
                time_grouped = df.groupby('date').size()
                time_grouped.plot(ax=axs[0, 1])
                axs[0, 1].set_title('Annotations Over Time')
                axs[0, 1].set_xlabel('Date')
                axs[0, 1].set_ylabel('Count')
            
            # Plot 3: Top stocks by annotation count
            top_stocks = df['stock'].value_counts().head(10)
            top_stocks.plot(kind='bar', ax=axs[1, 0])
            axs[1, 0].set_title('Top 10 Stocks by Annotation Count')
            axs[1, 0].set_xlabel('Stock')
            axs[1, 0].set_ylabel('Count')
            axs[1, 0].set_xticklabels(axs[1, 0].get_xticklabels(), rotation=45)
            
            # Plot 4: Signal distribution by top 5 stocks
            if len(df['stock'].unique()) >= 5:
                top_5_stocks = df['stock'].value_counts().head(5).index
                stock_signal_df = df[df['stock'].isin(top_5_stocks)]
                
                # Create a crosstab of stock and signal
                cross_tab = pd.crosstab(stock_signal_df['stock'], stock_signal_df['signal'])
                cross_tab.plot(kind='bar', stacked=True, ax=axs[1, 1])
                axs[1, 1].set_title('Signal Distribution by Top 5 Stocks')
                axs[1, 1].set_xlabel('Stock')
                axs[1, 1].set_ylabel('Count')
                axs[1, 1].set_xticklabels(axs[1, 1].get_xticklabels(), rotation=45)
                axs[1, 1].legend(title='Signal Type')
            else:
                axs[1, 1].axis('off')
                axs[1, 1].text(0.5, 0.5, 'Not enough unique stocks for this plot', 
                             horizontalalignment='center', verticalalignment='center')
            
            # Adjust layout
            plt.tight_layout()
            
            # Save or show the plot
            if output_file:
                plt.savefig(output_file)
                print(f"Plot saved to {output_file}")
            else:
                plt.show()
                
        except Exception as e:
            print(f"Error creating plots: {e}")

def main():
    """Main function to parse command line arguments and run the annotation viewer."""
    parser = argparse.ArgumentParser(description='View annotations from the database.')
    
    parser.add_argument('--db-url', type=str, help='Database URL (if not using DBManager)')
    parser.add_argument('--stock', type=str, help='Filter by stock symbol')
    parser.add_argument('--signal', type=str, help='Filter by signal type (e.g., long_buy, long_exit)')
    parser.add_argument('--start-date', type=str, help='Start date for filtering (YYYY-MM-DD)')
    parser.add_argument('--end-date', type=str, help='End date for filtering (YYYY-MM-DD)')
    parser.add_argument('--format', type=str, choices=['table', 'csv', 'json', 'plot'], 
                       default='table', help='Output format')
    parser.add_argument('--output', type=str, help='Output file path')
    
    args = parser.parse_args()
    
    # Create the annotation viewer
    viewer = AnnotationViewer(db_url=args.db_url)
    
    # Get annotations with optional filters
    annotations = viewer.get_annotations(
        stock=args.stock,
        signal=args.signal,
        start_date=args.start_date,
        end_date=args.end_date
    )
    
    # Display annotations in the specified format
    viewer.display_annotations(annotations, format=args.format, output_file=args.output)

if __name__ == "__main__":
    main() 