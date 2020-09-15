from setuptools import setup, find_packages
setup(
    name='bsm-api',
    version='1.0.0',
    package_dir={'api_db': 'backend/api_db', 'api_config': 'backend/api_config'},
    packages=find_packages() + find_packages('backend'),
)
