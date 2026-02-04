"""
시간표 생성 서비스
ScheduleGenerator 래핑 및 진행률 관리
"""
import os
import webbrowser
from typing import List, Callable, Optional

from .scheduler import ScheduleGenerator
from .visualizer import generate_html
from ..core.models import Schedule
from ..core.config import ScheduleConfig
from ..core.interfaces import IScheduleService


class ScheduleService(IScheduleService):
    """시간표 생성 서비스"""
    
    def __init__(self):
        self._generator: Optional[ScheduleGenerator] = None
        self._schedules: List[Schedule] = []
        self._progress_callback: Optional[Callable] = None
    
    def set_progress_callback(self, callback: Callable):
        """
        진행률 콜백 설정
        
        Args:
            callback: 진행 상태를 받을 함수 (message: str)
        """
        self._progress_callback = callback
    
    def _notify_progress(self, message: str):
        """진행 상태 알림"""
        if self._progress_callback:
            self._progress_callback(message)
    
    def generate_schedules(
        self,
        all_courses: List,
        config: ScheduleConfig
    ) -> List[Schedule]:
        """
        시간표 조합 생성
        
        Args:
            all_courses: 모든 강의 리스트
            config: 시간표 설정
            
        Returns:
            생성된 시간표 조합 리스트
        """
        self._notify_progress("시간표 생성 중...")
        
        # Generator 생성
        self._generator = ScheduleGenerator(all_courses, config)
        
        # 시간표 생성
        # 진행률 콜백 전달
        self._schedules = self._generator.generate_all_schedules(
            progress_callback=self._notify_progress
        )
        
        self._notify_progress(f"총 {len(self._schedules)}개 조합 생성 완료!")
        
        return self._schedules
    
    def get_schedules(self) -> List[Schedule]:
        """생성된 시간표 목록 반환"""
        return self._schedules
    
    def export_to_html(
        self,
        output_path: str = 'schedule_results.html',
        required_names: set = None,
        desired_names: set = None,
        open_browser: bool = True
    ) -> str:
        """
        시간표를 HTML로 내보내기
        
        Args:
            output_path: 출력 파일 경로
            required_names: 필수 강의명 집합
            desired_names: 희망 강의명 집합
            open_browser: 브라우저 자동 열기 여부
            
        Returns:
            생성된 파일의 절대 경로
        """
        if not self._schedules:
            raise ValueError("생성된 시간표가 없습니다.")
        
        self._notify_progress("HTML 파일 생성 중...")
        
        # 필수/희망 강의 이름 추출
        if required_names is None:
            required_names = set()
            if self._generator and hasattr(self._generator, 'required_course_groups'):
                for group in self._generator.required_course_groups:
                    for course in group:
                        required_names.add(course.name)
        
        if desired_names is None:
            desired_names = set()
            if self._generator and hasattr(self._generator, 'desired_course_groups'):
                for group in self._generator.desired_course_groups:
                    for course in group:
                        desired_names.add(course.name)
        
        # HTML 생성
        generate_html(
            self._schedules,
            output_path,
            required_names,
            desired_names
        )
        
        abs_path = os.path.abspath(output_path)
        
        self._notify_progress(f"HTML 파일 생성 완료: {abs_path}")
        
        # 브라우저 열기
        if open_browser:
            try:
                webbrowser.open(f"file://{abs_path}")
                self._notify_progress("브라우저에서 결과를 여는 중...")
            except Exception as e:
                self._notify_progress(f"브라우저 열기 실패: {e}")
        
        return abs_path
    
    def get_schedule_count(self) -> int:
        """생성된 시간표 개수 반환"""
        return len(self._schedules)
