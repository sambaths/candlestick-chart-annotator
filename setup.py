from setuptools import setup, find_packages
import os

# Read the package version from the __init__.py file
with open(os.path.join("candlestick-chart-annotator", "__init__.py"), "r") as f:
    for line in f:
        if line.startswith("__version__"):
            version = line.split("=")[1].strip().strip('"\'')
            break

# Read the requirements from requirements.txt or pyproject.toml
with open("pyproject.toml", "r") as f:
    requirements_section = False
    dependencies = []
    for line in f:
        if line.strip() == "dependencies = [":
            requirements_section = True
            continue
        if requirements_section and line.strip() == "]":
            requirements_section = False
            break
        if requirements_section:
            req = line.strip().strip(',').strip('"\'')
            if req:
                dependencies.append(req)

# Define package directories
package_dir = {
    "data_annotator": "candlestick-chart-annotator",
}

setup(
    name="data_annotator",
    version=version,
    description="Tool for annotating stock market data with trading signals",
    author="Data Annotator Team",
    packages=["data_annotator"],
    package_dir=package_dir,
    package_data={
        "data_annotator": [
            "templates/*",
            "static/css/*",
            "static/js/*",
            "static/img/*",
        ],
    },
    include_package_data=True,
    install_requires=dependencies,
    python_requires=">=3.10",
    entry_points={
        "console_scripts": [
            "data-annotator=data_annotator.app:main",
            "annotation-viewer=data_annotator.annotation_viewer:main",
        ],
    },
) 