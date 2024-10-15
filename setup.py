# Automatically created by: shub deploy

from setuptools import setup, find_packages

setup(
    name         = 'project',
    version      = '1.0',
    packages     = find_packages(),
    entry_points = {'scrapy': ['settings = puppis_project.settings']},
    install_requires=[
        'pandas',               # Ensure pandas is installed
        'BeautifulSoup4',   
        "numpy"# Ensure BeautifulSoup4 is installed
        # Add any other dependencies here
    ],
)
