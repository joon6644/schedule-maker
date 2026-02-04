"""
설정 탭 ViewModel (리팩토링 버전)
단일 책임 원칙을 준수하도록 매니저 클래스들로 책임 분리
"""
from typing import List, Any, Optional
from .base_viewmodel import BaseViewModel
from .managers import CourseListManager, SettingsManager

try:
    from ...core.config import CourseFilter
except ImportError:
    from core.config import CourseFilter


class ConfigViewModel(BaseViewModel):
    """
    ConfigTab의 비즈니스 로직 조정 담당
    실제 로직은 CourseListManager와 SettingsManager에 위임
    """
    
    def __init__(self, config_service, course_service=None):
        super().__init__()
        self.config_service = config_service
        self.course_service = course_service
        
        # 매니저 생성 (책임 분리)
        self.course_manager = CourseListManager(config_service, course_service)
        self.settings_manager = SettingsManager(config_service)
        
        # 상태 변수 (UI 바인딩용)
        self._min_credits = "12"
        self._max_credits = "18"
        self._excluded_days = {}
        self._required_list = []
        self._desired_list = []
        self._excluded_times_list = []
        
        # [State Management] Original Snapshot for Dirty Checking (Unsaved)
        self._original_config = None
        
        # [State Management] Last Generated Snapshot for Stale Checking
        self._last_generated_config = None

    def mark_as_generated(self):
        """현재 설정을 '생성됨' 상태로 마킹"""
        current = self.config_service.get_config()
        if current and hasattr(current, 'clone'):
            self._last_generated_config = current.clone()
        else:
            import copy
            self._last_generated_config = copy.deepcopy(current)
        self._check_dirty()

    def _check_dirty(self):
        """현재 설정 상태 확인 (Unsaved & Stale)"""
        current_config = self.config_service.get_config()
        if not current_config:
            return
            
        # 1. Check Unsaved (vs File)
        is_unsaved = False
        if self._original_config:
             is_unsaved = (current_config != self._original_config)
             
        # 2. Check Stale (vs Last Generated)
        is_stale = True # Default to true (if never generated)
        if self._last_generated_config:
            is_stale = (current_config != self._last_generated_config)
        
        # Notify
        self.notify('is_dirty_changed', is_unsaved)       # For "Save" status
        self.notify('needs_generation_changed', is_stale) # For "Generate" status
    
    # --- Setters (Updates Service + Checks Dirty) ---

    def set_credits(self, min_c, max_c):
        """학점 설정 업데이트"""
        self._min_credits = min_c
        self._max_credits = max_c
        
        try:
            val_min = int(min_c)
            val_max = int(max_c)
            
            # [Fix] Update Service properly (get_config returns copy!)
            self.config_service.update_credits_range(val_min, val_max)
            
            self.notify('config_changed', None) # Notify generic change
            self._check_dirty()
            self._validate_configuration() 
        except ValueError:
            pass # Ignore invalid input while typing

    def set_excluded_day(self, day, is_checked):
        """공강 요일 업데이트"""
        self._excluded_days[day] = is_checked
        
        # Reconstruct list from dict state
        current_excluded = [d for d, checked in self._excluded_days.items() if checked]
        
        # [Fix] Update Service properly
        self.config_service.update_excluded_days(current_excluded)

        self.notify('config_changed', None) # Notify generic change
        self._check_dirty()
        self._validate_configuration()

    def _validate_configuration(self):
        """설정 유효성 검사 (학점, 필수 과목 등)"""
        # 1. 학점 파싱
        try:
            min_c = int(self._min_credits)
            max_c = int(self._max_credits)
        except ValueError:
             # 입력 중일 때 등 변환 실패 시 일단 보류
             return

        # 2. 기본 유효성
        if min_c > max_c:
             self.notify('validation_status', (False, "최소 학점이 최대 학점보다 큽니다."))
             return

        # 3. 필수 과목 합계 검사
        total_required_credits = 0
        
        # CourseListManager returns list of tuples: (id, name, prof, time_str) - WAIT.
        # Let's check get_formatted_list output in ViewFile...
        # It calls manager.get_formatted_list
        # I need to access Config object directly for reliability.
        
        config = self.config_service.get_config()
        if not config: return
            
        req_filters = config.required_filters
        # [Fix] Use getter method
        all_courses = self.course_service.get_all_courses() if self.course_service else []
        
        for f in req_filters:
             # Find matching course (Assume 1st match for constraints check)
             match = next((c for c in all_courses if f.matches(c)), None)
             if match:
                 total_required_credits += match.credits
        
        if total_required_credits > max_c:
             self.notify('validation_status', (False, f"필수 강의 학점({total_required_credits})이 최대 학점({max_c})을 초과합니다."))
             return
             
        # All Checks Passed
        self.notify('validation_status', (True, ""))

    def get_validation_status(self):
        """외부에서 유효성 상태 확인용"""
        try:
            min_c = int(self._min_credits)
            max_c = int(self._max_credits)
        except: return (False, "학점 설정 오류")
        
        if min_c > max_c: return (False, "최소 학점이 최대 학점보다 큽니다.")
        
        total = 0
        config = self.config_service.get_config()
        if config:
            req = config.required_filters
            # [Fix] Use getter method
            courses = self.course_service.get_all_courses() if self.course_service else []
            for f in req:
                m = next((c for c in courses if f.matches(c)), None)
                if m: total += m.credits
        
        if total > max_c: return (False, f"필수 강의 학점({total}) 초과")
        
        return (True, "")

    # --- Properties ---
    
    @property
    def interaction_service(self):
        return self._interaction_service

    @property
    def min_credits(self):
        return self._min_credits
    
    @min_credits.setter
    def min_credits(self, value):
        self._min_credits = value
    
    @property
    def max_credits(self):
        return self._max_credits
    
    @max_credits.setter
    def max_credits(self, value):
        self._max_credits = value
    
    @property
    def excluded_days(self):
        return self._excluded_days
    
    # --- Data Loading ---
    
    def load_data(self):
        """설정 로드 및 뷰 갱신"""
        if not self.config_service:
            return
        
        config = self.config_service.get_config()
        if not config:
            return
        
        # 1. 학점 (SettingsManager 사용)
        min_c, max_c = self.settings_manager.get_credits()
        self._min_credits = min_c
        self._max_credits = max_c
        self.notify('credits', (self._min_credits, self._max_credits))
        print(f"[DEBUG] 학점 로드: {self._min_credits} ~ {self._max_credits}")
        
        # 2. 공강 요일 (SettingsManager 사용)
        self._excluded_days = self.settings_manager.get_excluded_days()
        self.notify('excluded_days', self._excluded_days)
        
        # 3. 강의 목록 (CourseListManager 사용)
        self._required_list = self.course_manager.get_formatted_list('required')
        self.notify('required_list', self._required_list)
        print(f"[DEBUG] 필수 강의 로드: {len(self._required_list)}개")
        
        self._desired_list = self.course_manager.get_formatted_list('desired')
        self.notify('desired_list', self._desired_list)
        
        # [State Management] Take Snapshot
        if config and hasattr(config, 'clone'):
            self._original_config = config.clone()
        else:
            # Fallback for mock objects or errors
            import copy
            self._original_config = copy.deepcopy(config)
            
        self._excluded_times_list = self.settings_manager.get_excluded_times()
        self.notify('excluded_times', self._excluded_times_list)
        
        
        # Initial check (should be false)
        self.notify('is_dirty_changed', False)
        
        # Initial Validation
        self._validate_configuration()

    def refresh_ui(self):
        """UI 요소만 갱신 (스냅샷 재설정 안 함)"""
        # 1. 학점
        min_c, max_c = self.settings_manager.get_credits()
        self._min_credits = min_c
        self._max_credits = max_c
        self.notify('credits', (self._min_credits, self._max_credits))
        
        # 2. 공강 요일
        self._excluded_days = self.settings_manager.get_excluded_days()
        self.notify('excluded_days', self._excluded_days)
        
        # 3. 강의 목록
        self._required_list = self.course_manager.get_formatted_list('required')
        self.notify('required_list', self._required_list)
        
        self._desired_list = self.course_manager.get_formatted_list('desired')
        self.notify('desired_list', self._desired_list)
        
        # 4. 제외 시간대
        self._excluded_times_list = self.settings_manager.get_excluded_times()
        self.notify('excluded_times', self._excluded_times_list)
    
    # --- 강의 관리 (CourseListManager에 위임) ---
    
    # --- 강의 관리 (CourseListManager에 위임) ---
    def add_course_filter(self, list_type: str, name: str, prof: str, course_id: str = None):
        """강의 필터 추가"""
        if self.course_manager.add_course(list_type, name, prof, course_id):
            self.show_info("성공", f"강의가 추가되었습니다: {name}")
            self.refresh_ui() 
            self.notify('config_changed', None) # Notify generic change
            self._check_dirty()
            self._validate_configuration()
        else:
            self.show_error("오류", "해당 조건을 만족하는 강의가 없습니다.")

    def remove_course(self, list_type: str, index: int):
        """강의 삭제"""
        self.course_manager.remove_course(list_type, index)
        self.refresh_ui()
        self.notify('config_changed', None)
        self._check_dirty()
        self._validate_configuration()
    
    def move_course(self, source_type: str, target_type: str, index: int):
        """강의를 다른 리스트로 이동"""
        if self.course_manager.move_course(source_type, target_type, index):
            self.refresh_ui()
            self.notify('config_changed', None)
            self._check_dirty()
            return True
        else:
            self.show_error("이동 오류", "강의 이동에 실패했습니다.")
            return False
    
    def reorder_course(self, list_type: str, old_index: int, new_index: int):
        """리스트 내 순서 변경"""
        if self.course_manager.reorder_course(list_type, old_index, new_index):
            self.refresh_ui()
            self.notify('config_changed', None)
            self._check_dirty()
            return True
        else:
            self.show_error("순서 변경 오류", "순서 변경에 실패했습니다.")
            return False
            
    # ... (rotate currently unsed)
    
    # --- 설정 관리 (SettingsManager에 위임) ---
    
    def add_excluded_time(self, day: str, start_time: str, end_time: str):
        """제외 시간대 추가"""
        if self.settings_manager.add_excluded_time(day, start_time, end_time):
            self.refresh_ui()
            self.notify('config_changed', None)
            self._check_dirty()
        else:
            self.show_error("오류", "시간대 추가 실패")
    
    def remove_excluded_time(self, index: int):
        """제외 시간대 삭제"""
        if self.settings_manager.remove_excluded_time(index):
            self.refresh_ui()
            self.notify('config_changed', None)
            self._check_dirty()
        else:
            self.show_error("오류", "시간대 삭제 실패")
    
    def apply_changes(self, min_c, max_c, day_vars):
        """설정 서비스에 현재 값 적용 (메모리 상)"""
        if not self.settings_manager.apply_all_settings(min_c, max_c, day_vars):
            self.show_error("오류", "최소 학점이 최대 학점보다 클 수 없습니다.")
            return False
        return True
    
    # --- 파일 I/O ---
    
    def save_settings_to_file(self, filepath: str, min_c, max_c, day_vars):
        """설정 파일 저장 (경로 지정)"""
        # 먼저 설정 적용
        if not self.apply_changes(min_c, max_c, day_vars):
            return
        
        try:
            # 저장
            self.config_service.save_config(path=filepath)
            self.show_info("성공", f"설정이 저장되었습니다.\\n{filepath}")
            # 저장했으므로 현재 상태가 새로운 '원본'이 됨
            self.load_data() # Re-snapshot
        except Exception as e:
            self.show_error("오류", f"저장 실패: {e}")
    
    def load_config_from_file(self, filepath: str):
        """설정 파일 로드"""
        try:
            print(f"[DEBUG] 설정 파일 로드 시도: {filepath}")
            self.config_service.load_config(filepath)
            self.load_data() # Re-snapshot
            print("[DEBUG] 설정 로드 및 데이터 갱신 완료")
            
            # [Fix] Loading new config invalidates previous state -> Force Dirty Check
            self.notify('config_changed', None)
            self._check_dirty()
            
            self.show_info("성공", f"설정을 불러왔습니다.\\n{filepath}")
        except Exception as e:
            print(f"[ERROR] 설정 로드 실패: {e}")
            self.show_error("오류", f"설정 로드 실패: {e}")
    
    # --- 레거시 메서드 (하위 호환성) ---
    
    def toggle_fixed_status(self, list_type: str, index: int):
        """강의 고정(핀) 상태 토글 (현재 미사용, 향후 구현 가능)"""
        # 이 기능은 현재 UI에서 사용하지 않지만 하위 호환성을 위해 유지
        pass
