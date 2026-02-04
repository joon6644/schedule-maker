import pytest
from schedule_maker.ui.viewmodels.config_viewmodel import ConfigViewModel
from schedule_maker.core.config import ScheduleConfig, CourseFilter

# --- Mocks ---

class MockInteractionService:
    def __init__(self):
        self.errors = []
        self.infos = []

    def show_error(self, title, message):
        self.errors.append((title, message))

    def show_info(self, title, message):
        self.infos.append((title, message))

class MockConfigService:
    def __init__(self):
        self._config = ScheduleConfig(
            min_credits=10, 
            max_credits=20,
            required_filters=[],
            desired_filters=[],
            excluded_days=[],
            excluded_time_slots=[]
        )
        self.updated_credits = None
        
    def get_config(self):
        # Return a simple copy logic for test
        import copy
        return copy.deepcopy(self._config)

    def update_credits_range(self, min_c, max_c):
        self._config.min_credits = min_c
        self._config.max_credits = max_c
        self.updated_credits = (min_c, max_c)
        
    def update_excluded_days(self, days):
        self._config.excluded_days = days

# --- Tests ---

@pytest.fixture
def vm():
    config_service = MockConfigService()
    vm = ConfigViewModel(config_service)
    vm.set_interaction_service(MockInteractionService())
    vm.load_data() # Init state
    return vm

def test_set_credits(vm):
    # Test valid input
    vm.set_credits("15", "18")
    assert vm._min_credits == "15"
    assert vm._max_credits == "18"
    assert vm.config_service.updated_credits == (15, 18)
    
    # Test invalid validation (should notify)
    received_status = []
    vm.bind('validation_status', lambda s: received_status.append(s))
    
    # Trigger validation failure (min > max)
    vm.set_credits("20", "18")
    assert received_status[-1][0] is False # is_valid = False
    assert "최소 학점이 최대 학점보다 큽니다" in received_status[-1][1]

def test_excluded_days_update(vm):
    vm.set_excluded_day('Mon', True)
    assert vm._excluded_days['Mon'] is True
    assert 'Mon' in vm.config_service.get_config().excluded_days
    
    vm.set_excluded_day('Mon', False)
    assert vm._excluded_days['Mon'] is False
    assert 'Mon' not in vm.config_service.get_config().excluded_days

def test_validation_logic(vm):
    # Setup: 18 max credits
    vm.set_credits("10", "18")
    
    # Check valid
    vm._validate_configuration() # Triggers notification
    
    # We can also check public method
    is_valid, msg = vm.get_validation_status()
    assert is_valid is True
    
    # Make invalid (Min > Max)
    vm.set_credits("20", "18")
    is_valid, msg = vm.get_validation_status()
    assert is_valid is False
    assert "최소 학점" in msg

def test_dirty_flag_notification(vm):
    flags = []
    vm.bind('is_dirty_changed', lambda val: flags.append(val))
    
    # Explicitly check initial state (should trigger notification)
    vm._check_dirty()
    assert flags[-1] is False
    
    # Change setting
    vm.set_credits("11", "20")
    
    # Should be dirty now (assuming original was 10-20)
    assert flags[-1] is True
