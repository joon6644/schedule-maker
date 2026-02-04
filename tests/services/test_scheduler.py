import pytest
from schedule_maker.services.scheduler import ScheduleGenerator
from schedule_maker.core.models import Course, TimeSlot
from schedule_maker.core.config import ScheduleConfig, CourseFilter

# --- Fixtures ---

@pytest.fixture
def mock_courses():
    """Generates a small set of mock courses."""
    return [
        Course('101', 'Math', 3, 'Prof. A', [TimeSlot('월', '09:00', '10:30')]),
        Course('102', 'English', 3, 'Prof. B', [TimeSlot('화', '10:00', '11:30')]),
        Course('103', 'Physics', 3, 'Prof. C', [TimeSlot('수', '13:00', '15:00')]),
        Course('104', 'History', 2, 'Prof. D', [TimeSlot('목', '15:00', '17:00')]),
        Course('105', 'Programming', 3, 'Prof. E', [TimeSlot('금', '09:00', '12:00')]),
        # Conflict with 101
        Course('106', 'Math (B)', 3, 'Prof. A', [TimeSlot('월', '10:00', '11:30')]), 
        # Conflict with 102
        Course('107', 'English (B)', 3, 'Prof. B', [TimeSlot('화', '11:00', '12:30')]),
    ]

@pytest.fixture
def basic_config():
    return ScheduleConfig(
        min_credits=3,
        max_credits=18,
        required_filters=[],
        desired_filters=[],
        excluded_days=[],
        excluded_time_slots=[]
    )

# --- Tests ---

def test_find_all_matching_courses(mock_courses, basic_config):
    generator = ScheduleGenerator(mock_courses, basic_config)
    
    # Filter by name
    f = CourseFilter(name='Math')
    matched = generator._find_all_matching_courses(f)
    assert len(matched) == 2 # Math and Math (B)
    assert matched[0].name == 'Math' or matched[0].name == 'Math (B)'

def test_generate_required_combinations(mock_courses, basic_config):
    # Setup: Math is Required
    basic_config.required_filters = [CourseFilter(name='Math')]
    
    generator = ScheduleGenerator(mock_courses, basic_config)
    combinations = generator._generate_required_combinations(generator.required_course_groups)
    
    # Should have 2 combinations (one with Math, one with Math (B))
    assert len(combinations) == 2
    assert combinations[0].total_credits == 3

def test_excluded_time_logic(mock_courses, basic_config):
    # Exclude Monday Morning
    basic_config.excluded_time_slots = [('월', '09:00', '11:00')]
    
    generator = ScheduleGenerator(mock_courses, basic_config)
    
    # Math (Mon 09:00-10:30) should be excluded
    math_course = next(c for c in mock_courses if c.name == 'Math')
    assert generator._is_excluded_time(math_course) is True
    
    # Physics (Wed) should not be excluded
    phy_course = next(c for c in mock_courses if c.name == 'Physics')
    assert generator._is_excluded_time(phy_course) is False

def test_generate_schedules_integration(mock_courses, basic_config):
    # Scenario:
    # Required: Math (3 credits)
    # Desired: English, Physics
    # Min Credits: 6
    
    basic_config.required_filters = [CourseFilter(name='Math')] # Will pick 101 or 106
    basic_config.desired_filters = [CourseFilter(name='English'), CourseFilter(name='Physics')]
    basic_config.min_credits = 6
    
    generator = ScheduleGenerator(mock_courses, basic_config)
    results = generator.generate_all_schedules()
    
    assert len(results) > 0
    for sched in results:
        # Check credits
        assert sched.total_credits >= 6
        # Check required course existence
        course_names = [c.name for c in sched.courses]
        assert 'Math' in course_names or 'Math (B)' in course_names

def test_credit_limit_enforcement(mock_courses, basic_config):
    # Max Credits 5
    # Required Math (3)
    # Desired English (3) -> Total 6 (Overflow)
    basic_config.max_credits = 5
    basic_config.required_filters = [CourseFilter(name='Math')]
    basic_config.desired_filters = [CourseFilter(name='English')]
    
    generator = ScheduleGenerator(mock_courses, basic_config)
    results = generator.generate_all_schedules()
    
    # Should return schedules with ONLY Math (3 credits) because adding English would exceed 5
    # But wait, min_credits is 3 (default fixture). So Math alone is valid.
    
    for sched in results:
        assert sched.total_credits <= 5
        assert len(sched.courses) == 1 # Only Math fits
