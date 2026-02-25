"""
Pytest configuration and fixtures for testing Lambda functions.
"""
import os
import pytest

# Set default AWS region for tests to avoid NoRegionError
os.environ.setdefault('AWS_REGION', 'us-east-1')
os.environ.setdefault('AWS_ACCESS_KEY_ID', 'test')
os.environ.setdefault('AWS_SECRET_ACCESS_KEY', 'test')


