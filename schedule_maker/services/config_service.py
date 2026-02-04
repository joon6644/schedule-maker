"""
설정 관리 서비스
ScheduleConfig 로드/저장 및 관리
"""
from ..core.config import (
    ScheduleConfig, 
    CourseFilter,
    load_config_from_json,
    save_config_to_json
)
from ..core.interfaces import IConfigService
import os


class ConfigService(IConfigService):
    """설정 관리 서비스"""
    
    DEFAULT_CONFIG_PATH = 'data/config.json'
    
    def __init__(self):
        self._config: ScheduleConfig = None
        self._config_path: str = None
        
        # 데이터 디렉토리 생성
        self._ensure_data_dir()
    
    def _ensure_data_dir(self):
        """데이터 디렉토리가 없으면 생성"""
        directory = os.path.dirname(self.DEFAULT_CONFIG_PATH)
        if directory and not os.path.exists(directory):
            try:
                os.makedirs(directory)
            except OSError as e:
                print(f"데이터 디렉토리 생성 실패: {e}")
    
    def load_config(self, path: str = None) -> ScheduleConfig:
        """
        설정 파일 로드
        
        Args:
            path: 설정 파일 경로
            
        Returns:
            로드된 ScheduleConfig
        """
        if path is None:
            path = self.DEFAULT_CONFIG_PATH
            
        self._config = load_config_from_json(path)
        self._config_path = path
        return self._config
    
    def save_config(self, config: ScheduleConfig = None, path: str = None):
        """
        설정 파일 저장
        
        Args:
            config: 저장할 설정 (None이면 현재 설정)
            path: 저장 경로 (None이면 기존 경로)
        """
        if config is None:
            config = self._config
        
        if path is None:
            path = self._config_path or self.DEFAULT_CONFIG_PATH
        
        save_config_to_json(config, path)
        self._config = config
        self._config_path = path
    
    def get_config(self) -> ScheduleConfig:
        """
        현재 설정 반환 (복사본)
        캡슐화를 위해 내부 객체를 직접 노출하지 않음
        """
        from copy import deepcopy
        return deepcopy(self._config)
    
    def update_credits_range(self, min_credits: int, max_credits: int):
        """학점 범위 업데이트"""
        if self._config:
            self._config.min_credits = min_credits
            self._config.max_credits = max_credits
    
    def update_excluded_days(self, excluded_days: list[str]):
        """공강 요일 업데이트"""
        if self._config:
            self._config.excluded_days = excluded_days
    
    def _is_duplicate_filter(self, filter_list: list[CourseFilter], new_filter: CourseFilter) -> bool:
        """
        필터 중복 여부 확인
        
        Args:
            filter_list: 기존 필터 리스트
            new_filter: 추가하려는 새 필터
            
        Returns:
            True if duplicate, False otherwise
        """
        for existing in filter_list:
            # 1. ID 기반 비교 (가장 명확한 중복 체크)
            if new_filter.course_id and existing.course_id:
                if new_filter.course_id == existing.course_id:
                    return True
            
            # 2. 강의명 기반 비교
            elif new_filter.name and existing.name:
                if new_filter.name == existing.name:
                    # 교수명도 함께 지정된 경우 둘 다 비교
                    if new_filter.professor and existing.professor:
                        if new_filter.professor == existing.professor:
                            return True
                    # 한쪽만 교수명이 있거나 둘 다 없으면 강의명만으로 중복 판정
                    elif not new_filter.professor and not existing.professor:
                        return True
        
        return False
    
    def add_required_course(self, course_filter: CourseFilter) -> bool:
        """
        필수 강의 추가 (중복 방지)
        
        Returns:
            True if added successfully, False if duplicate
        """
        if self._config:
            if not self._is_duplicate_filter(self._config.required_filters, course_filter):
                self._config.required_filters.append(course_filter)
                return True
            return False
        return False
    
    def add_desired_course(self, course_filter: CourseFilter) -> bool:
        """
        희망 강의 추가 (중복 방지)
        
        Returns:
            True if added successfully, False if duplicate
        """
        if self._config:
            if not self._is_duplicate_filter(self._config.desired_filters, course_filter):
                self._config.desired_filters.append(course_filter)
                return True
            return False
        return False
    
    def remove_required_course(self, index: int):
        """필수 강의 제거 (인덱스로)"""
        if self._config and 0 <= index < len(self._config.required_filters):
            self._config.required_filters.pop(index)
    
    def remove_desired_course(self, index: int):
        """희망 강의 제거 (인덱스로)"""
        if self._config and 0 <= index < len(self._config.desired_filters):
            self._config.desired_filters.pop(index)
    
    def add_excluded_time_slot(self, day: str, start: str, end: str):
        """제외 시간대 추가"""
        if self._config:
            self._config.excluded_time_slots.append((day, start, end))
            
    def remove_excluded_time_slot(self, index: int):
        """제외 시간대 제거 (인덱스로)"""
        if self._config and 0 <= index < len(self._config.excluded_time_slots):
            self._config.excluded_time_slots.pop(index)
    
    def clear_required_courses(self):
        """모든 필수 강의 제거"""
        if self._config:
            self._config.required_filters.clear()
    
    def clear_desired_courses(self):
        """모든 희망 강의 제거"""
        if self._config:
            self._config.desired_filters.clear()
    
    def get_required_filters(self):
        """필수 강의 필터 목록 반환"""
        return self._config.required_filters if self._config else []
    
    def get_desired_filters(self):
        """희망 강의 필터 목록 반환"""
        return self._config.desired_filters if self._config else []
    
    def create_default_config(self) -> ScheduleConfig:
        """기본 설정 생성"""
        self._config = ScheduleConfig(
            min_credits=12,
            max_credits=18,
            required_filters=[],
            desired_filters=[],
            excluded_days=[],
            excluded_time_slots=[]
        )
        return self._config
        
    def update_required_filters(self, filters: list[CourseFilter]):
        """필수 강의 목록 전체 업데이트"""
        if self._config:
            self._config.required_filters = filters
            
    def update_desired_filters(self, filters: list[CourseFilter]):
        """희망 강의 목록 전체 업데이트"""
        if self._config:
            self._config.desired_filters = filters
