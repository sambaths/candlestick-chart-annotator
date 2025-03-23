# Installing the Data Annotator Package

This guide explains how to install the `data_annotator` package for use in your Python scripts and Jupyter notebooks.

## Prerequisites

- Python 3.10 or higher
- PostgreSQL database (for production use)
- pip package manager

## Installation Steps

### 1. Install as a Development Package

For development work, you can install the package in "editable" mode, which means changes to the source code will immediately be reflected without needing to reinstall:

```bash
# Navigate to the project root directory

# Install in development mode
pip install -e .
```

### 2. Import in Jupyter Notebooks

After installation, you can import the package in Jupyter notebooks:

```python
# Import modules from the data_annotator package
from data_annotator.db_manager import DBManager, Stock, Annotation
from data_annotator.annotation_viewer import AnnotationViewer

# Or import specific utilities
from data_annotator.data_provider import get_data_provider
```

### 3. Example Usage

See the example notebook in the `notebooks` directory:

```bash
jupyter notebook notebooks/data_annotator_example.ipynb
```

### 4. Command-Line Tools

The installation also provides command-line tools:

```bash
# Run the main application
data-annotator

# Use the annotation viewer tool
annotation-viewer --help
```

## Troubleshooting

### Import Errors

If you see import errors like:

```
ModuleNotFoundError: No module named 'data_annotator'
```

Make sure you've installed the package correctly with:

```bash
pip list | grep data_annotator
```

### Database Connection Issues

If you encounter database connection issues, check your PostgreSQL connection settings in the environment variables or .env file.

## Additional Information

For more detailed documentation, see the project README.md file. 