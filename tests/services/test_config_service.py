import pytest
import sys
from schedule_maker.services.config_service import ConfigService
from schedule_maker.core.config import ScheduleConfig, CourseFilter

# --- Fixtures ---

@pytest.fixture
def config_service(mocker):
    """ConfigService with mocked file I/O"""
    mocker.patch('os.makedirs')
    mocker.patch('os.path.exists', return_value=True)
    
    service = ConfigService()
    
    service._config = ScheduleConfig(
        min_credits=10,
        max_credits=20,
        required_filters=[],
        desired_filters=[],
        excluded_days=['Sunday'],
        excluded_time_slots=[]
    )
    return service

# --- Tests ---

def test_update_credits_range(config_service):
    print("\n[DEBUG] test_update_credits_range start")
    assert config_service.get_config().min_credits == 10
    config_service.update_credits_range(15, 22)
    current = config_service.get_config()
    assert current.min_credits == 15
    assert current.max_credits == 22
    print("[DEBUG] test_update_credits_range end")

def test_add_remove_required_course(config_service):
    print("\n[DEBUG] test_add_remove_required_course start")
    f = CourseFilter(name='Test Course')
    config_service.add_required_course(f)
    assert len(config_service.get_required_filters()) == 1
    assert config_service.get_required_filters()[0].name == 'Test Course'
    config_service.remove_required_course(0)
    assert len(config_service.get_required_filters()) == 0
    print("[DEBUG] test_add_remove_required_course end")

def test_excluded_time_slots(config_service):
    print("\n[DEBUG] test_excluded_time_slots start")
    
    # ADD
    config_service.add_excluded_time_slot('Mon', '10:00', '12:00')
    cfg = config_service.get_config()
    print(f"[DEBUG] After add, count: {len(cfg.excluded_time_slots)}")
    print(f"[DEBUG] Content: {cfg.excluded_time_slots}")
    
    if len(cfg.excluded_time_slots) != 1:
        pytest.fail(f"Add failed. Len: {len(cfg.excluded_time_slots)}")

    val = cfg.excluded_time_slots[0]
    expected = ('Mon', '10:00', '12:00')
    if val != expected:
        pytest.fail(f"Value mismatch. Got {val}, expected {expected}")

    # REMOVE
    config_service.remove_excluded_time_slot(0)
    cfg_after = config_service.get_config()
    print(f"[DEBUG] After remove, count: {len(cfg_after.excluded_time_slots)}")
    
    if len(cfg_after.excluded_time_slots) != 0:
        pytest.fail(f"Remove failed. Len: {len(cfg_after.excluded_time_slots)}")
        
    print("[DEBUG] test_excluded_time_slots end")

def test_load_save_config(mocker, config_service):
    print("\n[DEBUG] test_load_save_config start")
    mock_load = mocker.patch('schedule_maker.services.config_service.load_config_from_json')
    mock_save = mocker.patch('schedule_maker.services.config_service.save_config_to_json')
    
    config_service.save_config(path='dummy.json')
    mock_save.assert_called_once()
    
    mock_load.return_value = ScheduleConfig(
        min_credits=99, 
        max_credits=20, 
        required_filters=[], 
        desired_filters=[], 
        excluded_days=[], 
        excluded_time_slots=[]
    )
    config = config_service.load_config(path='dummy.json')
    
    mock_load.assert_called_once_with('dummy.json')
    assert config.min_credits == 99
    assert config_service.get_config().min_credits == 99
    print("[DEBUG] test_load_save_config end")

def test_get_config_encapsulation(config_service):
    original = config_service.get_config()
    original.min_credits = 999 
    assert config_service.get_config().min_credits == 10
