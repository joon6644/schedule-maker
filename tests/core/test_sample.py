def test_environment_setup():
    """Simple test to verify pytest is working."""
    assert True

def test_fixture_usage(sample_course_data):
    """Verify conftest.py fixture loading."""
    assert sample_course_data['to_test'] == 'data'
