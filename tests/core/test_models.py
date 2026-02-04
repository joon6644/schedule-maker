import pytest
from schedule_maker.core.models import TimeSlot, Course, Schedule, time_str_to_index, calculate_time_mask

# --- TimeSlot & Bitmask Tests ---

def test_time_str_to_index():
    # 월요일 09:00 -> idx = 0 (day=0) * 288 + 9 * 12 + 0 = 108
    idx = time_str_to_index('월', '09:00')
    assert idx == 108

    # 월요일 09:05 -> idx = 109
    idx = time_str_to_index('월', '09:05')
    assert idx == 109

def test_calculate_time_mask():
    # 월요일 09:00~09:10 (2 slots: 09:00~09:05, 09:05~09:10)
    slot = TimeSlot('월', '09:00', '09:10')
    mask = calculate_time_mask([slot])
    
    # Expected: bits at 108 and 109 should be 1
    expected_mask = (1 << 108) | (1 << 109)
    assert mask == expected_mask

def test_timeslot_overlaps():
    t1 = TimeSlot('월', '09:00', '10:30')
    t2 = TimeSlot('월', '10:00', '11:00')
    t3 = TimeSlot('월', '10:30', '12:00')
    t4 = TimeSlot('화', '09:00', '10:30') # Different day

    assert t1.overlaps(t2) is True
    assert t1.overlaps(t3) is False # End time inclusive/exclusive check? Implementation says [start, end)
    assert t1.overlaps(t4) is False

# --- Course Tests ---

def test_course_conflict_detection():
    # Monday 9:00 - 10:30
    c1 = Course('1', 'Course A', 3, 'Prof A', 
                [TimeSlot('월', '09:00', '10:30')])
    
    # Monday 10:00 - 11:30 (Overlap)
    c2 = Course('2', 'Course B', 3, 'Prof B', 
                [TimeSlot('월', '10:00', '11:30')])
    
    # Monday 10:30 - 12:00 (No Overlap)
    c3 = Course('3', 'Course C', 3, 'Prof C', 
                [TimeSlot('월', '10:30', '12:00')])

    # Manual mask check
    assert c1.time_mask > 0
    
    # Conflict check
    assert c1.has_conflict(c2) is True
    assert c1.has_conflict(c3) is False

# --- Schedule Tests ---

def test_schedule_add_course():
    s = Schedule()
    c1 = Course('1', 'Logic 101', 3, 'Turing', [TimeSlot('월', '10:00', '12:00')])
    
    assert s.add_course(c1) is True
    assert s.total_credits == 3
    assert len(s.courses) == 1
    assert (s.total_time_mask & c1.time_mask) == c1.time_mask

def test_schedule_conflict_prevention():
    s = Schedule()
    c1 = Course('1', 'Logic 101', 3, 'Turing', [TimeSlot('월', '10:00', '12:00')])
    s.add_course(c1)
    
    # Overlapping course
    c2 = Course('2', 'Math 101', 3, 'Euler', [TimeSlot('월', '11:00', '13:00')])
    
    assert s.add_course(c2) is False # Should fail
    assert len(s.courses) == 1
    assert s.total_credits == 3

def test_schedule_duplicate_name_prevention():
    s = Schedule()
    c1 = Course('1', 'Logic 101', 3, 'Turing', [TimeSlot('월', '10:00', '12:00')])
    s.add_course(c1)
    
    # Same name, different time/ID
    c2 = Course('3', 'Logic 101', 3, 'Gödel', [TimeSlot('화', '10:00', '12:00')])
    
    assert s.add_course(c2) is False # Logic 101 already exists
    assert len(s.courses) == 1

def test_schedule_remove_course():
    s = Schedule()
    c1 = Course('1', 'Logic 101', 3, 'Turing', [TimeSlot('월', '10:00', '12:00')])
    s.add_course(c1)
    
    s.remove_course(c1)
    assert len(s.courses) == 0
    assert s.total_credits == 0
    assert s.total_time_mask == 0
    assert 'Logic 101' not in s.course_names
