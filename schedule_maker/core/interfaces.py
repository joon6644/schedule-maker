"""
서비스 계층 인터페이스 정의
의존성 역전 원칙(DIP)을 위한 추상 클래스들
"""
from abc import ABC, abstractmethod
from typing import List, Optional, Callable
from .models import Course, Schedule
from .config import ScheduleConfig, CourseFilter


class IServiceBase(ABC):
    """모든 서비스의 기본 인터페이스"""
    
    @abstractmethod
    def initialize(self) -> bool:
        """서비스 초기화"""
        pass


class ICourseService(ABC):
    """강의 데이터 관리 서비스 인터페이스"""
    
    @abstractmethod
    def load_courses(self, csv_path: str) -> List[Course]:
        """CSV 파일에서 강의 데이터 로드"""
        pass
    
    @abstractmethod
    def get_all_courses(self) -> List[Course]:
        """모든 강의 반환"""
        pass
    
    @abstractmethod
    def get_course_by_id(self, course_id: str) -> Optional[Course]:
        """강좌번호로 강의 검색"""
        pass
    
    @abstractmethod
    def search_courses(
        self, 
        query: str = '', 
        search_by_name: bool = True,
        search_by_professor: bool = True
    ) -> List[Course]:
        """강의 검색"""
        pass
    
    @abstractmethod
    def is_loaded(self) -> bool:
        """데이터 로드 여부"""
        pass
    
    @abstractmethod
    def get_course_count(self) -> int:
        """총 강의 수"""
        pass


class IConfigService(ABC):
    """설정 관리 서비스 인터페이스"""
    
    @abstractmethod
    def load_config(self, path: str = None) -> ScheduleConfig:
        """설정 파일 로드"""
        pass
    
    @abstractmethod
    def save_config(self, config: ScheduleConfig = None, path: str = None):
        """설정 파일 저장"""
        pass
    
    @abstractmethod
    def get_config(self) -> ScheduleConfig:
        """현재 설정 반환"""
        pass
    
    @abstractmethod
    def update_credits_range(self, min_credits: int, max_credits: int):
        """학점 범위 업데이트"""
        pass
    
    @abstractmethod
    def update_excluded_days(self, excluded_days: list):
        """공강 요일 업데이트"""
        pass
    
    @abstractmethod
    def add_required_course(self, course_filter: CourseFilter):
        """필수 강의 추가"""
        pass
    
    @abstractmethod
    def add_desired_course(self, course_filter: CourseFilter):
        """희망 강의 추가"""
        pass
    
    @abstractmethod
    def remove_required_course(self, index: int):
        """필수 강의 제거"""
        pass
    
    @abstractmethod
    def remove_desired_course(self, index: int):
        """희망 강의 제거"""
        pass
    
    @abstractmethod
    def create_default_config(self) -> ScheduleConfig:
        """기본 설정 생성"""
        pass


class IScheduleService(ABC):
    """시간표 생성 서비스 인터페이스"""
    
    @abstractmethod
    def set_progress_callback(self, callback: Callable):
        """진행률 콜백 설정"""
        pass
    
    @abstractmethod
    def generate_schedules(
        self,
        all_courses: List[Course],
        config: ScheduleConfig
    ) -> List[Schedule]:
        """시간표 조합 생성"""
        pass
    
    @abstractmethod
    def get_schedules(self) -> List[Schedule]:
        """생성된 시간표 목록"""
        pass
    
    @abstractmethod
    def export_to_html(
        self,
        output_path: str = 'schedule_results.html',
        required_names: set = None,
        desired_names: set = None,
        open_browser: bool = True
    ) -> str:
        """시간표를 HTML로 내보내기"""
        pass
    
    @abstractmethod
    def get_schedule_count(self) -> int:
        """생성된 시간표 개수"""
        pass


class IInteractionService(ABC):
    """사용자 상호작용 서비스 인터페이스"""
    
    @abstractmethod
    def show_error(self, title: str, message: str):
        """에러 메시지 표시"""
        pass
    
    @abstractmethod
    def show_warning(self, title: str, message: str):
        """경고 메시지 표시"""
        pass
    
    @abstractmethod
    def show_info(self, title: str, message: str):
        """정보 메시지 표시"""
        pass
