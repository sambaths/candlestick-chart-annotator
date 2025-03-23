from flask import Flask, render_template, jsonify, request, send_from_directory
from flask_caching import Cache
from flask_socketio import SocketIO, emit
import pandas as pd
import numpy as np
from datetime import datetime
import os
import json
import traceback
import pytz
from gevent.pywsgi import WSGIServer

# Try to import the database manager
try:
    from db_manager import DBManager, Stock, Annotation
except ImportError:
    print("Error importing db_manager from current directory")
    try:
        from data_annotator.db_manager import DBManager, Stock, Annotation
    except ImportError:
        print("Error importing db_manager from data_annotator package")
        raise

# Try to import data provider
try:
    from data_provider import get_data_provider
except ImportError:
    print("Error importing data_provider from current directory")
    try:
        from data_annotator.data_provider import get_data_provider
    except ImportError:
        print("Error importing data_provider from data_annotator package")
        # Define a dummy data provider in case the real one is not available

# Pre-defined list of NIFTY 50 stocks
NIFTY50_STOCKS = [
    'AXISBANK', 'INFY', 'WIPRO', 'ONGC', 'RELIANCE', 'APOLLOHOSP', 'POWERGRID', 
    'HCLTECH', 'KOTAKBANK', 'CIPLA', 'HDFCBANK', 'BAJFINANCE', 'TATACONSUM', 
    'JSWSTEEL', 'SHRIRAMFIN', 'MARUTI', 'ADANIPORTS', 'COALINDIA', 'BPCL', 
    'NESTLEIND', 'LT', 'SBILIFE', 'DRREDDY', 'TATASTEEL', 'BAJAJFINSV', 'SBIN', 
    'HINDALCO', 'BHARTIARTL', 'EICHERMOT', 'TITAN', 'ADANIENT', 'TATAMOTORS', 
    'ICICIBANK', 'HDFCLIFE', 'GRASIM', 'TCS', 'ASIANPAINT', 'HEROMOTOCO', 
    'SUNPHARMA', 'ITC', 'BAJAJ-AUTO', 'HINDUNILVR', 'BRITANNIA', 'M&M', 
    'ULTRACEMCO', 'BEL', 'TRENT', 'INDUSINDBK'
]

# Initialize Flask app
app = Flask(__name__)
socketio = SocketIO(app, cors_allowed_origins="*")

# Setup caching
cache = Cache(app, config={
    'CACHE_TYPE': 'filesystem',
    'CACHE_DIR': 'cache-directory',
    'CACHE_DEFAULT_TIMEOUT': 300  # 5 minutes
})

# Constants
VIEW_MODE = 'day'  # 'day' or 'custom'
VIEW_SIZE = 100  # Number of data points to view at a time for custom view

# Colors for annotations
COLORS = {
    "background": "#F9F9F9",
    "text": "#333333",
    "header": "#2C3E50",
    "success": "#4CAF50",
    "warning": "#FF9800",
    "error": "#F44336",
    "long_entry": "#2ca02c",
    "long_exit": "#1f77b4", 
    "short_entry": "#d62728",
    "short_exit": "#ff7f0e"
}

# Initialize database and data provider
db = DBManager()
try:
    data_provider = get_data_provider('fyers')
except Exception as e:
    print(f"Error initializing data provider: {e}")
    # Use dummy provider if real one fails
    data_provider = get_data_provider('dummy')

# Global variable to store sample data
SAMPLE_DATA = {}

# Socket.IO event handlers
@socketio.on('connect')
def handle_connect():
    """Handle client connection"""
    print('Client connected')

@socketio.on('disconnect')
def handle_disconnect():
    """Handle client disconnection"""
    print('Client disconnected')

@socketio.on('get_annotations')
def handle_get_annotations():
    """Send annotations to client"""
    try:
        annotations_df = db.get_annotations()
        if not annotations_df.empty:
            # Add formatted timestamp for display
            annotations_df['formatted_timestamp'] = annotations_df['timestamp'].apply(
                lambda x: x.strftime('%Y-%m-%d %H:%M:%S') if hasattr(x, 'strftime') else str(x)
            )
            # Convert timestamps to ISO strings for JSON serialization
            annotations_df['timestamp'] = annotations_df['timestamp'].apply(
                lambda ts: ts.isoformat() if hasattr(ts, 'isoformat') else str(ts)
            )
            # Convert to dict before sending via socket.io
            annotations_dict = annotations_df.to_dict(orient='records')
            emit('annotations_data', {'annotations': annotations_dict})
        else:
            emit('annotations_data', {'annotations': []})
    except Exception as e:
        emit('error', {'message': str(e)})
        print(f"Error handling get_annotations: {e}")
        traceback.print_exc()

# Flask routes
@app.route('/')
def index():
    """Render the main page"""
    available_stocks = db.get_available_stocks()
    # Get date ranges for each stock
    stock_date_ranges = {}
    for stock in available_stocks:
        try:
            data = db.get_stock_data(stock)
            if data is not None and not data.empty:
                min_date = data['timestamp'].min()
                max_date = data['timestamp'].max()
                stock_date_ranges[stock] = {
                    'min_date': min_date.strftime('%Y-%m-%d'),
                    'max_date': max_date.strftime('%Y-%m-%d')
                }
        except Exception as e:
            print(f"Error getting date range for {stock}: {e}")
    return render_template('index.html', 
                         available_stocks=available_stocks,
                         stock_date_ranges=stock_date_ranges)

@app.route('/data')
def data_management():
    """Render the data management page"""
    return render_template('data_management.html', nifty50_stocks=NIFTY50_STOCKS)

@app.route('/static/<path:filename>')
def serve_static(filename):
    """Serve static files"""
    return send_from_directory('static', filename)

@app.route('/api/stocks/summary', methods=['GET'])
def get_stocks_summary():
    """Get summary of available stock data"""
    try:
        stocks_data = db.get_stocks_summary()
        # Format response according to DataTables requirements
        response = {
            "draw": int(request.args.get('draw', 1)),
            "recordsTotal": len(stocks_data),
            "recordsFiltered": len(stocks_data),
            "data": stocks_data if stocks_data else []
        }
        return jsonify(response)
    except Exception as e:
        print(f"Error in get_stocks_summary: {str(e)}")
        return jsonify({
            "draw": int(request.args.get('draw', 1)),
            "recordsTotal": 0,
            "recordsFiltered": 0,
            "data": [],
            "error": str(e)
        })

@app.route('/api/stocks/download', methods=['POST'])
def download_stocks():
    try:
        data = request.json
        symbols = data.get('symbols', [])
        start_date = data.get('start_date')
        end_date = data.get('end_date')
        resolution = data.get('resolution', '1D')

        success_count = 0
        error_messages = []

        # Download data for each symbol
        for symbol in symbols:
            try:
                # Get data using Fyers provider
                df = data_provider.get_historical_data(
                    ticker=symbol,
                    resolution=resolution,
                    start_date=start_date,
                    end_date=end_date
                )
                if df is not None and not df.empty:
                    # Format the data according to our schema
                    df = df.rename(columns={
                        'datetime': 'timestamp',
                        'open_price': 'open',
                        'high_price': 'high',
                        'low_price': 'low',
                        'ltp': 'close',
                        'last_traded_qty': 'volume'
                    })
                    df['symbol'] = symbol
                    df['resolution'] = resolution
                    print(df.shape)
                    success = db.save_stock_data(df)
                    if success:
                        success_count += 1
                    else:
                        error_messages.append(f"Failed to save data for {symbol}")
                else:
                    error_messages.append(f"No data available for {symbol}")
            except Exception as e:
                error_messages.append(f"Error processing {symbol}: {str(e)}")

        if success_count > 0:
            message = f"Successfully downloaded data for {success_count} symbol(s)"
            if error_messages:
                message += f". Errors: {'; '.join(error_messages)}"
            return jsonify({"message": message})
        else:
            return jsonify({"error": '; '.join(error_messages)}), 500

    except Exception as e:
        return jsonify({"error": str(e)}), 500

@app.route('/api/stocks/nifty50', methods=['GET'])
def get_nifty50_stocks():
    try:
        return jsonify({"stocks": NIFTY50_STOCKS})
    except Exception as e:
        return jsonify({"error": str(e)}), 500

@app.route('/api/data/stocks/summary')
def get_stocks_data_summary():
    """Get detailed summary of available stock data including min/max dates"""
    try:
        stocks = db.get_available_stocks()
        summary = []
        
        for stock in stocks:
            data = db.get_stock_data(stock)
            if not data.empty:
                summary.append({
                    'symbol': stock,
                    'start_date': data['timestamp'].min().isoformat(),
                    'end_date': data['timestamp'].max().isoformat(),
                    'row_count': len(data),
                    'resolution': '1min'  # Assuming all data is 1-minute resolution
                })
        
        return jsonify({'summary': summary})
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@app.route('/api/data/download', methods=['POST'])
def download_stock_data():
    """Download stock data using data provider"""
    try:
        data = request.json
        symbols = data.get('symbols', [])
        start_date = data.get('start_date')
        end_date = data.get('end_date')
        
        if not symbols:
            return jsonify({'error': 'No symbols provided'}), 400
            
        if not data_provider:
            return jsonify({'error': 'Data provider not available'}), 400
            
        # Initialize provider
        provider = get_data_provider('fyers')
        all_data = []
        
        for symbol in symbols:
            try:
                # Get data with 1-minute resolution
                data = provider.get_historical_data(
                    symbol, 
                    resolution='1',
                    start_date=start_date,
                    end_date=end_date
                )
                
                if not data.empty:
                    data['stock'] = symbol
                    all_data.append(data)
                    
            except Exception as e:
                return jsonify({'error': f'Error downloading {symbol}: {str(e)}'}), 500
                
        if not all_data:
            return jsonify({'error': 'No data downloaded'}), 400
            
        # Combine and format data
        df = pd.concat(all_data)
        df = df[['last_traded_time', 'open_price', 'high_price', 'low_price', 'ltp', 'last_traded_qty', 'stock']]
        df.columns = ['timestamp', 'open', 'high', 'low', 'close', 'volume', 'stock']
        df['timestamp'] = df['timestamp'].apply(lambda x: datetime.fromtimestamp(x))
        df = df.sort_values(by=['stock','timestamp'])
        df = df.reset_index(drop=True)
        # Save to database
        success = db.save_stock_data(df)
        
        if success:
            return jsonify({
                'message': 'Data downloaded successfully',
                'rows': len(df),
                'symbols': symbols
            })
        else:
            return jsonify({'error': 'Failed to save data to database'}), 500
            
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@app.route('/api/data/delete/<symbol>', methods=['DELETE'])
def delete_stock_data(symbol):
    """Delete stock data from database"""
    try:
        print(f"Attempting to delete data for symbol: {symbol}")  # Debug log
        success = db.delete_stock_data(symbol)
        if success:
            response = {'message': f'Data for {symbol} deleted successfully'}
            print(f"Successfully deleted data for {symbol}")  # Debug log
            return jsonify(response)
        print(f"Failed to delete data for {symbol}")  # Debug log
        return jsonify({'error': f'Failed to delete data for {symbol}'}), 500
    except Exception as e:
        print(f"Error deleting data for {symbol}: {str(e)}")  # Debug log
        return jsonify({'error': str(e)}), 500

@app.route('/api/stocks')
def get_stocks():
    """Get list of available stocks"""
    stocks = db.get_available_stocks()
    return jsonify({'stocks': stocks})

@app.route('/api/stock/<symbol>/data')
@cache.memoize(timeout=180)
def get_stock_data_route(symbol):
    """Get stock data for a specific symbol"""
    try:
        data = db.get_stock_data(symbol)
        if data is not None and not data.empty:
            data_dict = data.to_dict(orient='records')
            return jsonify({'data': data_dict})
        return jsonify({'error': f'No data available for {symbol}'}), 404
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@app.route('/api/annotations')
def get_annotations_route():
    """Get all annotations"""
    try:
        annotations_df = db.get_annotations()
        if not annotations_df.empty:
            # Add formatted timestamp for display
            annotations_df['formatted_timestamp'] = annotations_df['timestamp'].apply(
                lambda x: x.strftime('%Y-%m-%d %H:%M:%S') if hasattr(x, 'strftime') else str(x)
            )
            # Convert timestamps to ISO strings for JSON serialization
            annotations_df['timestamp'] = annotations_df['timestamp'].apply(
                lambda ts: ts.isoformat() if hasattr(ts, 'isoformat') else str(ts)
            )
            annotations_dict = annotations_df.to_dict(orient='records')
            return jsonify({'annotations': annotations_dict})
        return jsonify({'annotations': []})
    except Exception as e:
        print(f"Error getting annotations: {e}")
        traceback.print_exc()
        return jsonify({'error': str(e)}), 500

@app.route('/api/annotations/status')
def get_annotations_status():
    """Get annotation status for all stocks"""
    try:
        status = db.get_annotation_status()
        return jsonify({'status': status})
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@app.route('/api/annotations', methods=['POST'])
def add_annotation():
    """Add a new annotation"""
    try:
        data = request.json
        print(f"Received annotation data: {data}")
        
        # Parse timestamp if it's a string
        timestamp = data['timestamp']
        if isinstance(timestamp, str):
            try:
                # Try to parse ISO format with timezone info
                # Remove Z and assume local time if no timezone specified
                # timestamp_str = timestamp.replace('Z', '')
                # timestamp = datetime.fromisoformat(timestamp_str)
                timestamp = datetime.strptime(timestamp[4:24], "%b %d %Y %H:%M:%S")
                # timestamp = timestamp.astimezone(pytz.timezone('Asia/Kolkata'))
                print(f"Parsed timestamp: {timestamp}")
            except ValueError as e:
                print(f"Error parsing timestamp: {e}")
                try:
                    # Try alternative format
                    timestamp = datetime.strptime(timestamp, '%Y-%m-%dT%H:%M:%S.%f')
                    print(f"Parsed timestamp with alternative format: {timestamp}")
                except ValueError:
                    print(f"Could not parse timestamp: {timestamp}")
                    return jsonify({'error': f'Invalid timestamp format: {timestamp}'}), 400
        
        # Store the timestamp in the database
        success = db.save_annotation(
            timestamp,
            data['stock'],
            data['signal'],
            data.get('price'),
            data.get('reason')
        )
        
        if success:
            # Get the latest annotations to broadcast to all clients
            annotations_df = db.get_annotations()
            if not annotations_df.empty:
                # Make sure to convert pandas timestamps to strings before sending via Socket.IO
                # First create the formatted_timestamp field for display
                annotations_df['formatted_timestamp'] = annotations_df['timestamp'].apply(
                    lambda x: x.strftime('%Y-%m-%d %H:%M:%S') if hasattr(x, 'strftime') else str(x)
                )
                
                # Convert the original timestamp to ISO strings for proper serialization
                annotations_df['timestamp'] = annotations_df['timestamp'].apply(
                    lambda x: x.isoformat() if hasattr(x, 'isoformat') else str(x)
                )
                
                # Convert to dictionary for JSON serialization
                annotations_dict = annotations_df.to_dict(orient='records')
                socketio.emit('annotations_updated', {'annotations': annotations_dict})
            return jsonify({'message': 'Annotation saved successfully'})
        return jsonify({'error': 'Failed to save annotation'}), 500
    except Exception as e:
        print(f"Error saving annotation: {e}")
        traceback.print_exc()
        return jsonify({'error': str(e)}), 500

@app.route('/api/annotations/last', methods=['DELETE'])
def delete_last():
    """Delete the last annotation"""
    try:
        success = db.delete_last_annotation()
        if success:
            # Broadcast updated annotations
            annotations_df = db.get_annotations()
            if not annotations_df.empty:
                # Make sure to convert pandas timestamps to strings before sending via Socket.IO
                # First create the formatted_timestamp field for display
                annotations_df['formatted_timestamp'] = annotations_df['timestamp'].apply(
                    lambda x: x.strftime('%Y-%m-%d %H:%M:%S') if hasattr(x, 'strftime') else str(x)
                )
                
                # Convert the original timestamp to ISO strings for proper serialization
                annotations_df['timestamp'] = annotations_df['timestamp'].apply(
                    lambda x: x.isoformat() if hasattr(x, 'isoformat') else str(x)
                )
                
                # Convert to dictionary for JSON serialization
                annotations_dict = annotations_df.to_dict(orient='records')
            else:
                annotations_dict = []
            socketio.emit('annotations_updated', {'annotations': annotations_dict})
            return jsonify({'message': 'Last annotation deleted successfully'})
        return jsonify({'error': 'Failed to delete annotation'}), 500
    except Exception as e:
        print(f"Error deleting last annotation: {e}")
        traceback.print_exc()
        return jsonify({'error': str(e)}), 500

@app.route('/api/annotations/<int:annotation_id>', methods=['DELETE'])
def delete_specific(annotation_id):
    """Delete a specific annotation"""
    try:
        success = db.delete_annotation(annotation_id)
        if success:
            # Broadcast updated annotations
            annotations_df = db.get_annotations()
            if not annotations_df.empty:
                # Make sure to convert pandas timestamps to strings before sending via Socket.IO
                # First create the formatted_timestamp field for display
                annotations_df['formatted_timestamp'] = annotations_df['timestamp'].apply(
                    lambda x: x.strftime('%Y-%m-%d %H:%M:%S') if hasattr(x, 'strftime') else str(x)
                )
                
                # Convert the original timestamp to ISO strings for proper serialization
                annotations_df['timestamp'] = annotations_df['timestamp'].apply(
                    lambda x: x.isoformat() if hasattr(x, 'isoformat') else str(x)
                )
                
                # Convert to dictionary for JSON serialization
                annotations_dict = annotations_df.to_dict(orient='records')
            else:
                annotations_dict = []
            socketio.emit('annotations_updated', {'annotations': annotations_dict})
            return jsonify({'message': 'Annotation deleted successfully'})
        return jsonify({'error': 'Failed to delete annotation'}), 500
    except Exception as e:
        print(f"Error deleting annotation {annotation_id}: {e}")
        traceback.print_exc() 
        return jsonify({'error': str(e)}), 500

@app.route('/api/stock/<symbol>/date-range')
@cache.memoize(timeout=300)
def get_date_range(symbol):
    """Get date range for a specific stock"""
    try:
        data = db.get_stock_data(symbol)
        if data is not None and not data.empty:
            min_date = data['timestamp'].min()
            max_date = data['timestamp'].max()
            return jsonify({
                'min_date': min_date.isoformat() if min_date else None,
                'max_date': max_date.isoformat() if max_date else None
            })
        return jsonify({'error': f'No data available for {symbol}'}), 404
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@app.route('/api/stock/<symbol>/dates')
@cache.memoize(timeout=300)
def get_stock_dates(symbol):
    """Get all available dates for a specific stock"""
    try:
        data = db.get_stock_data(symbol)
        if data is not None and not data.empty:
            # Convert timestamps to dates and get unique dates
            dates = data['timestamp'].dt.date.unique()
            return jsonify({
                'dates': [date.strftime('%Y-%m-%d') for date in sorted(dates)],
                'min_date': min(dates).strftime('%Y-%m-%d'),
                'max_date': max(dates).strftime('%Y-%m-%d')
            })
        return jsonify({'dates': [], 'min_date': None, 'max_date': None})
    except Exception as e:
        print(f"Error getting stock dates: {e}")
        return jsonify({'error': str(e)}), 500

@app.route('/api/stock-date-ranges')
@cache.memoize(timeout=300)
def get_all_stock_date_ranges():
    """Get date ranges for all available stocks"""
    try:
        stocks = db.get_available_stocks()
        date_ranges = {}
        for stock in stocks:
            try:
                data = db.get_stock_data(stock)
                if data is not None and not data.empty:
                    min_date = data['timestamp'].min()
                    max_date = data['timestamp'].max()
                    date_ranges[stock] = {
                        'min_date': min_date.strftime('%Y-%m-%d'),
                        'max_date': max_date.strftime('%Y-%m-%d')
                    }
            except Exception as e:
                print(f"Error processing stock {stock}: {e}")
        return jsonify(date_ranges)
    except Exception as e:
        print(f"Error getting stock date ranges: {e}")
        return jsonify({'error': str(e)}), 500

@app.route('/api/stock/<symbol>/date/<date>')
@cache.memoize(timeout=180)
def get_stock_data_for_date(symbol, date):
    """Get stock data for a specific symbol and date"""
    try:
        print(f"API - Getting data for {symbol} on {date}")
        
        # Get data from database
        print(f"Calling db.get_stock_data with symbol={symbol}, date={date}")
        data = db.get_stock_data(symbol, date=date)
        
        # Debug log data properties
        if data is not None and not data.empty:
            print(f"Found {len(data)} records")
            print(f"Data columns: {data.columns.tolist()}")
            print(f"First record timestamp: {data.iloc[0]['timestamp'] if len(data) > 0 else 'N/A'}")
            
            # Handle timestamp serialization
            try:
                # Convert timestamp columns to ISO format strings for JSON serialization
                if 'timestamp' in data.columns:
                    data['timestamp'] = data['timestamp'].apply(lambda x: x.isoformat() if hasattr(x, 'isoformat') else str(x))
                
                # Convert DataFrame to dict for JSON serialization
                data_dict = data.to_dict(orient='records')
                print(f"Returning {len(data_dict)} records for {symbol} on {date}")
                return jsonify({'data': data_dict})
            except Exception as e:
                print(f"Error converting data to JSON: {e}")
                traceback.print_exc()
                return jsonify({'error': f'Error converting data to JSON: {str(e)}'}), 500
        else:
            print(f"No data found for {symbol} on {date}")
            return jsonify({'error': f'No data available for {symbol} on {date}'}), 404
    except Exception as e:
        print(f"Error in get_stock_data_for_date: {e}")
        traceback.print_exc()
        return jsonify({'error': str(e)}), 500

@app.route('/api/test/create-sample-data')
def create_sample_data():
    """Create sample data for testing"""
    try:
        # Create sample data for AXISBANK
        symbol = "AXISBANK"
        
        # Create sample dates in March 2025
        dates = [
            "2025-03-01", "2025-03-02", "2025-03-03", "2025-03-04", "2025-03-05",
            "2025-03-06", "2025-03-07", "2025-03-08", "2025-03-09", "2025-03-10",
            "2025-03-11", "2025-03-12", "2025-03-13", "2025-03-14", "2025-03-15"
        ]
        
        global SAMPLE_DATA
        SAMPLE_DATA[symbol] = {}
        
        all_data = []
        base_price = 1000.0
        
        for date in dates:
            # Create 5 minute data for the trading day (9:15 AM to 3:30 PM)
            start_time = datetime.strptime(f"{date} 09:15:00", "%Y-%m-%d %H:%M:%S")
            end_time = datetime.strptime(f"{date} 15:30:00", "%Y-%m-%d %H:%M:%S")
            
            current_time = start_time
            daily_data = []
            
            # Random walk for the price
            current_price = base_price + np.random.normal(0, 5)
            
            while current_time <= end_time:
                # Generate random price movement
                price_change = np.random.normal(0, 2)
                current_price += price_change
                
                # Generate OHLCV data
                open_price = current_price
                high_price = current_price + abs(np.random.normal(0, 1))
                low_price = current_price - abs(np.random.normal(0, 1))
                close_price = current_price + np.random.normal(0, 0.5)
                volume = int(np.random.randint(100, 1000))
                
                # Create data point
                data_point = {
                    'symbol': symbol,
                    'timestamp': current_time.isoformat(),
                    'open': float(open_price),
                    'high': float(high_price),
                    'low': float(low_price),
                    'close': float(close_price),
                    'volume': volume,
                    'resolution': '5'
                }
                
                daily_data.append(data_point)
                
                # Increment time by 5 minutes
                current_time = current_time + pd.Timedelta(minutes=5)
            
            # Store data by date
            SAMPLE_DATA[symbol][date] = daily_data
            all_data.extend(daily_data)
        
        return jsonify({
            'message': 'Sample data created successfully',
            'count': len(all_data),
            'dates': dates
        })
            
    except Exception as e:
        print(f"Error creating sample data: {e}")
        traceback.print_exc()
        return jsonify({'error': str(e)}), 500

@app.route('/api/test/stocks')
def get_test_stocks():
    """Get list of stocks with sample data"""
    return jsonify({'stocks': list(SAMPLE_DATA.keys())})

@app.route('/api/test/stock/<symbol>/date/<date>')
def get_test_stock_data(symbol, date):
    """Get sample stock data for a specific date"""
    try:
        if symbol not in SAMPLE_DATA or date not in SAMPLE_DATA[symbol]:
            return jsonify({'error': f'No data for {symbol} on {date}'}), 404
            
        return jsonify({'data': SAMPLE_DATA[symbol][date]})
    except Exception as e:
        print(f"Error getting test stock data: {e}")
        return jsonify({'error': str(e)}), 500

if __name__ == '__main__':
    # Use SocketIO for WebSocket support
    socketio.run(app, host='0.0.0.0', port=8050, debug=False)