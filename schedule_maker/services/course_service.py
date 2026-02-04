"""
강의 데이터 관리 서비스
CSV 로딩, 검색, 필터링 등 강의 관련 모든 작업 처리
"""
from typing import List, Optional
from ..core.models import Course
from ..core.interfaces import ICourseService
from .parser import parse_csv


class CourseService(ICourseService):
    """강의 데이터 관리 서비스"""
    
    def __init__(self):
        self._all_courses: List[Course] = []
        self._courses_by_id: dict = {}
        self._loaded = False
    
    def load_courses(self, csv_path: str) -> List[Course]:
        """
        CSV 파일에서 강의 데이터 로드
        
        Args:
            csv_path: CSV 파일 경로
            
        Returns:
            로드된 강의 리스트
        """
        self._all_courses = parse_csv(csv_path)
        
        # ID로 빠른 검색을 위한 딕셔너리 생성
        self._courses_by_id = {
            course.course_id: course 
            for course in self._all_courses
        }
        
        self._loaded = True
        return self._all_courses
    
    def get_all_courses(self) -> List[Course]:
        """모든 강의 반환"""
        return self._all_courses.copy()
    
    def get_course_by_id(self, course_id: str) -> Optional[Course]:
        """
        강좌번호로 강의 검색
        
        Args:
            course_id: 강좌번호
            
        Returns:
            해당 강의 또는 None
        """
        return self._courses_by_id.get(course_id)
    
    def search_courses(
        self, 
        query: str = '', 
        search_by_name: bool = True,
        search_by_professor: bool = True
    ) -> List[Course]:
        """
        강의 검색
        
        Args:
            query: 검색어
            search_by_name: 강의명으로 검색 여부
            search_by_professor: 교수명으로 검색 여부
            
        Returns:
            검색 결과 강의 리스트
        """
        if not query or not query.strip():
            return self._all_courses.copy()
        
        query = query.strip().lower()
        results = []
        
        for course in self._all_courses:
            # 검색 조건 확인
            match = False
            
            if search_by_name and query in course.name.lower():
                match = True
            
            if search_by_professor and query in course.professor.lower():
                match = True
            
            if match:
                results.append(course)
        
        return results
    
    def filter_courses(
        self,
        courses: List[Course] = None,
        min_credits: int = None,
        max_credits: int = None,
        days: List[str] = None,
        professor: str = None,
    ) -> List[Course]:
        """
        강의 필터링
        
        Args:
            courses: 필터링할 강의 리스트 (None이면 전체)
            min_credits: 최소 학점
            max_credits: 최대 학점
            days: 요일 필터 (포함되어야 할 요일)
            professor: 교수명 필터
            
        Returns:
            필터링된 강의 리스트
        """
        if courses is None:
            courses = self._all_courses
        
        filtered = courses.copy()
        
        # 학점 필터
        if min_credits is not None:
            filtered = [c for c in filtered if c.credits >= min_credits]
        
        if max_credits is not None:
            filtered = [c for c in filtered if c.credits <= max_credits]
        
        # 요일 필터
        if days:
            filtered = [
                c for c in filtered 
                if any(slot.day in days for slot in c.time_slots)
            ]
        
        # 교수 필터
        if professor:
            professor_lower = professor.lower()
            filtered = [
                c for c in filtered 
                if professor_lower in c.professor.lower()
            ]
        
        return filtered
    
    def is_loaded(self) -> bool:
        """데이터 로드 여부 반환"""
        return self._loaded
    
    def get_course_count(self) -> int:
        """총 강의 수 반환"""
        return len(self._all_courses)
