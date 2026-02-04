import pytest
import sys
import os

# Ensure the project root is in sys.path
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

@pytest.fixture
def sample_course_data():
    """Provides sample course data for testing."""
    return {
        'to_test': 'data'
    }
