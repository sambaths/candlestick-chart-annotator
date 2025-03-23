# Candlestick Chart Annotator

This guide provides detailed instructions to set up and run the Candlestick Chart Annotator project, a web-based application for visualizing and annotating stock market data. The system allows users to mark trading signals on stock charts and store these annotations for analysis.

_NB: This is mostly created with AI, So expect some errors and issues._

## Table of Contents

1. [Project Overview](#project-overview)
2. [System Requirements](#system-requirements)
3. [Installation](#installation)
   - [PostgreSQL Setup](#postgresql-setup)
   - [Python Environment Setup](#python-environment-setup)
   - [Using UV (Faster Alternative to pip)](#using-uv-faster-alternative-to-pip)
   - [Project Configuration](#project-configuration)
4. [Database Initialization](#database-initialization)
5. [Running the Application](#running-the-application)
6. [Using the Application](#using-the-application)
   - [Stock Selection and Data Viewing](#stock-selection-and-data-viewing)
   - [Creating Annotations](#creating-annotations)
   - [Managing Annotations](#managing-annotations)
7. [Command Line Annotation Viewer](#command-line-annotation-viewer)
8. [Project Structure](#project-structure)
9. [Troubleshooting](#troubleshooting)

## Project Overview

The Data Annotator is designed for traders and analysts who need to mark significant trading signals (entries and exits) on stock price charts. The application provides:

- Interactive candlestick charts for stock visualization
- Tools for adding trading signal annotations
- Persistent storage of annotations in a PostgreSQL database
- Historical annotation browsing and filtering
- Command-line tools for data analysis

## System Requirements

- **Operating System**: Windows, macOS, or Linux
- **Python**: Version 3.10 or higher
- **PostgreSQL**: Version 12 or higher
- **Web Browser**: Chrome, Firefox, or Edge (latest versions)
- **Disk Space**: At least 1GB for application and database

## Installation

### PostgreSQL Setup

1. **Install PostgreSQL**:
   
   For Ubuntu/Debian:
   ```bash
   sudo apt update
   sudo apt install postgresql postgresql-contrib
   ```
   
   For macOS (using Homebrew):
   ```bash
   brew install postgresql
   ```
   
   For Windows, download and install from [postgresql.org](https://www.postgresql.org/download/windows/)

2. **Start PostgreSQL service**:
   
   Ubuntu/Debian:
   ```bash
   sudo service postgresql start
   ```
   
   macOS:
   ```bash
   brew services start postgresql
   ```
   
   Windows: PostgreSQL service should start automatically after installation

3. **Create a database user and database**:
   
   ```bash
   # Connect as postgres user
   sudo -u postgres psql
   
   # Inside PostgreSQL prompt, create user and database
   CREATE USER candlestick-chart-annotator WITH PASSWORD 'your_password';
   CREATE DATABASE candlestick-chart-annotator_db OWNER candlestick-chart-annotator;
   ALTER USER candlestick-chart-annotator WITH SUPERUSER;
   
   # Exit PostgreSQL prompt
   \q
   ```

### Python Environment Setup

1. **Clone or download the repository**:
   
   ```bash
   git clone https://github.com/sambaths/candlestick-chart-annotator
   cd candlestick-chart-annotator
   ```

2. **Create a virtual environment**:
   
   ```bash
   python -m venv venv
   ```

3. **Activate the virtual environment**:
   
   For Linux/macOS:
   ```bash
   source venv/bin/activate
   ```
   
   For Windows:
   ```bash
   venv\Scripts\activate
   ```

4. **Install required packages** (using pip):
   
   ```bash
   pip install flask flask-socketio pandas numpy sqlalchemy plotly matplotlib tabulate seaborn gevent flask-caching python-dateutil
   ```
   
   If you have a pyproject.toml file in the repository, you can use:
   ```bash
   pip install -e .
   ```

### Using UV (Faster Alternative to pip)

[UV](https://github.com/astral-sh/uv) is a much faster alternative to pip for Python package installation. Here's how to use it:

1. **Install UV**:

   ```bash
   curl -sSf https://astral.sh/uv/install.sh | bash
   ```

   For Windows:
   ```bash
   powershell -c "irm https://astral.sh/uv/install.ps1 | iex"
   ```

2. **Create and activate a virtual environment with UV**:

   ```bash
   uv venv
   source .venv/bin/activate  # On Linux/macOS
   # OR
   .venv\Scripts\activate     # On Windows
   ```

3. **Install dependencies using UV**:

   With the project's existing `pyproject.toml` and `uv.lock` files:
   
   ```bash
   # Synchronize your environment with the exact packages in uv.lock
   uv pip sync
   
   # OR install from pyproject.toml
   uv pip install -e .
   ```
   
   The repository includes:
   
   - `pyproject.toml`: Defines project metadata and dependencies with version constraints
   - `uv.lock`: A lock file that contains exact versions of all dependencies and their sub-dependencies for reproducible installs

4. **Understanding pyproject.toml and uv.lock**:

   - **pyproject.toml**: This file defines the project's metadata and dependencies, following Python's modern packaging standards (PEP 621). It includes:
     - Project name, version, and description
     - Python version requirements (`requires-python = ">=3.10"`)
     - Direct dependencies with their version constraints

   ```toml
   [project]
   name = "data-annotator"
   version = "0.1.0"
   description = "Stock market data annotation tool"
   requires-python = ">=3.10"
   dependencies = [
       "flask==3.0.2",
       "flask-socketio>=5.5.1",
       # Other dependencies listed here
   ]
   ```

   - **uv.lock**: This file is automatically generated and maintained by UV when packages are installed. It:
     - Records the exact version of every package installed, including transitive dependencies
     - Ensures consistency across different development environments
     - Enables fast, reproducible installs with `uv pip sync`

5. **Benefits of using UV with lock files**:

   - **Speed**: UV is significantly faster than pip for both installation and resolution
   - **Reproducibility**: The lock file ensures everyone uses exactly the same package versions
   - **Dependency resolution**: UV performs deterministic resolution to avoid conflicts
   - **Virtual environment management**: Integrated environment creation and management

6. **Updating dependencies**:

   To update all dependencies to their latest compatible versions:
   ```bash
   uv pip install -e . --upgrade
   ```

   To update specific packages:
   ```bash
   uv pip install package_name --upgrade
   ```

UV offers significant performance improvements compared to pip, especially for large dependency trees, making the setup process much faster.

### Project Configuration

1. **Database connection string**:
   
   Open `db_manager.py` and locate the database connection string. Modify it to match your PostgreSQL setup:
   
   ```python
   # Look for a line similar to this:
   self.engine = create_engine('postgresql://candlestick-chart-annotator:your_password@localhost/candlestick-chart-annotator_db')
   ```

   Modify this to match your PostgreSQL configuration, replacing the username, password, and database name as needed.

## Database Initialization

1. **Run the database setup script**:
   
   ```bash
   python candlestick-chart-annotator/setup_db.py
   ```
   
   This will create the necessary tables in your PostgreSQL database. If you encounter any errors, make sure your database connection string is correctly configured.

2. **If you have existing data**:
   
   If you need to migrate data from another source, you can use:
   ```bash
   python candlestick-chart-annotator/migrate_data.py
   ```

## Running the Application

1. **Start the Flask application**:
   
   ```bash
   python candlestick-chart-annotator/app.py
   ```
   
   By default, the application will be accessible at `http://localhost:8050`.

2. **Access the web interface**:
   
   Open your web browser and navigate to:
   ```
   http://localhost:8050
   ```

## Using the Application

### Stock Selection and Data Viewing

1. **Select a stock** from the dropdown menu on the left sidebar.
2. **Choose a date** from the calendar interface. The calendar will only show dates for which data is available.
3. **View the stock chart** which displays as a candlestick chart in the main panel.
4. **Navigate the chart** using:
   - Zoom: Use the mousewheel or zoom buttons
   - Pan: Click and drag the chart
   - Reset view: Click "Reset Zoom" button

### Creating Annotations

1. **Click on a point** on the chart where you want to add an annotation.
2. **Select the annotation type** from the left sidebar:
   - **LONG ENTRY**: Starting a long position
   - **LONG EXIT**: Closing a long position
   - **SHORT ENTRY**: Starting a short position
   - **SHORT EXIT**: Closing a short position
3. **Add optional notes** in the reason field.
4. **Click the annotation button** to save your annotation.
5. **Verify** that your annotation appears on the chart and in the annotations table below.

### Managing Annotations

1. **View all annotations** for the selected stock and date in the table below the chart.
2. **Delete an annotation** by clicking the delete button next to it in the table.
3. **Filter annotations** by stock or date by changing your selection in the left sidebar.

## Command Line Annotation Viewer

The project includes a standalone command-line tool for viewing and analyzing annotation data:

```bash
python candlestick-chart-annotator/annotation_viewer.py
```

### Options:

- `--stock SYMBOL`: Filter by stock symbol (e.g., AXISBANK)
- `--signal SIGNAL`: Filter by signal type (long_buy, long_exit, short_buy, short_exit)
- `--start-date YYYY-MM-DD`: Show annotations after this date
- `--end-date YYYY-MM-DD`: Show annotations before this date
- `--format FORMAT`: Output format (table, csv, json, plot)
- `--output FILE`: Save output to a file instead of displaying on screen
- `--db-url URL`: Optional database URL if not using default configuration

### Examples:

Display all annotations in table format:
```bash
python candlestick-chart-annotator/annotation_viewer.py
```

Filter annotations for a specific stock:
```bash
python candlestick-chart-annotator/annotation_viewer.py --stock AXISBANK
```

Generate visualization charts of your annotation data:
```bash
python candlestick-chart-annotator/annotation_viewer.py --format plot --output annotations_analysis.png
```

## Project Structure

```
candlestick-chart-annotator/
├── app.py                  # Main Flask web application
├── db_manager.py           # Database operations and ORM models
├── data_provider.py        # Abstract interface for stock data providers
├── fyers.py                # Implementation of Fyers API data provider
├── annotation_viewer.py    # CLI tool for annotation analysis
├── setup_db.py             # Database schema creation script
├── migrate_data.py         # Optional data migration utility
├── test.py                 # Test utilities
├── static/                 # Static web assets
│   ├── css/                # Stylesheets
│   ├── js/                 # JavaScript files including:
│   │   ├── annotations.js  # Annotation management logic
│   │   └── chart-*.js      # Chart visualization components
└── templates/              # HTML templates
    └── index.html          # Main application UI
```

## Troubleshooting

### Database Connection Issues

If you encounter database connection errors:

1. **Verify PostgreSQL is running**:
   ```bash
   # For Linux
   sudo service postgresql status
   
   # For macOS
   brew services list | grep postgresql
   ```

2. **Test connection credentials**:
   ```bash
   psql -U candlestick-chart-annotator -d candlestick-chart-annotator_db -h localhost
   ```
   
   If this fails, your connection details may be incorrect.

3. **Check the database logs**:
   ```bash
   # Location varies by system, common locations:
   sudo cat /var/log/postgresql/postgresql-12-main.log  # Linux
   cat /usr/local/var/log/postgresql.log  # macOS
   ```

### No Stock Data Available

If you don't see any stocks in the dropdown:

1. **Import stock data** using a data provider. Setup procedures for different data sources:
   
   **Fyers API**:
   - Obtain API credentials from Fyers
   - Configure your credentials in the application
   - Use data loading functions to import historical data

   **CSV Import**:
   - Prepare CSV files with OHLCV (Open, High, Low, Close, Volume) data
   - Use the import functionality in the application

2. **Verify data in database**:
   ```bash
   psql -U candlestick-chart-annotator -d candlestick-chart-annotator_db -c "SELECT DISTINCT symbol FROM stocks"
   ```

### UI Issues

If the interface doesn't respond correctly:

1. **Check browser console** for JavaScript errors (F12 in most browsers)
2. **Clear browser cache** and reload the page
3. **Ensure all JavaScript files are loading** by checking the network tab in browser developer tools

### Annotation Saving Issues

If annotations aren't saving correctly:

1. **Check server logs** for any error messages
2. **Verify database permissions** are correct for insert operations
3. **Test the API directly** using a tool like curl or Postman:
   ```bash
   curl -X POST http://localhost:8050/api/annotations -H "Content-Type: application/json" -d '{"stock":"AXISBANK","timestamp":"2023-01-01T10:30:00","signal":"long_buy","price":100.5}'
   ``` 