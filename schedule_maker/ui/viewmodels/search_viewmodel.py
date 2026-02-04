"""
검색 탭 ViewModel
강의 검색, 필터링, 정렬 로직 관리
"""
from typing import List, Any, Optional, Dict
from .base_viewmodel import BaseViewModel

class SearchViewModel(BaseViewModel):
    """
    SearchTab의 비즈니스 로직을 담당
    """
    
    def __init__(self, course_service, config_service=None):
        super().__init__()
        self.course_service = course_service
        self.config_service = config_service
        
        # 상태 변수
        self._search_results = []
        self._search_query = ""
        self._search_by_name = True
        self._search_by_prof = True
        self._sort_column = None
        self._sort_reverse = False
        self._last_sort_col = None
        self._sort_state = 0 # 0: 기본, 1: 오름차순, 2: 내림차순
        
    @property
    def results(self): return self._search_results
    
    @property
    def query(self): return self._search_query
    @query.setter
    def query(self, value): self._search_query = value
    
    # --- Actions ---
    
    def perform_search(self):
        """검색 수행"""
        if not self.course_service: return
        
        query = self._search_query.strip()
        search_by = []
        if self._search_by_name: search_by.append('name')
        if self._search_by_prof: search_by.append('professor')
        
        # CourseService.search_courses()에 올바른 타입으로 전달
        results = self.course_service.search_courses(
            query=query,
            search_by_name=self._search_by_name,
            search_by_professor=self._search_by_prof
        )
        self._search_results = results
        
        # 정렬 상태가 있으면 유지
        if self._sort_column:
            self._apply_sort()
            
        self.notify('results', self._get_formatted_results())

    def _get_formatted_results(self):
        """Treeview용 데이터 변환"""
        formatted = []
        for c in self._search_results:
            formatted.append((
                c.course_id,
                c.name,
                c.credits,
                c.professor,
                ", ".join(str(slot) for slot in c.time_slots)
            ))
        return formatted

    def set_search_options(self, by_name: bool, by_prof: bool):
        """검색 옵션 설정"""
        self._search_by_name = by_name
        self._search_by_prof = by_prof

    def toggle_sort(self, column_id: str):
        """정렬 토글 (3단계)"""
        # 0 -> 1 (▲) -> 2 (▼) -> 0
        if self._last_sort_col == column_id:
            self._sort_state = (self._sort_state + 1) % 3
        else:
            self._last_sort_col = column_id
            self._sort_state = 1
            
        self._sort_column = column_id
        
        if self._sort_state == 0:
            # 원본 순서로 복구 (재검색 시뮬레이션)
            self.perform_search()
        else:
            self._sort_reverse = (self._sort_state == 2)
            self._apply_sort()
            self.notify('results', self._get_formatted_results())
            
        # UI에 화살표 표시를 위한 알림
        self.notify('sort_changed', (column_id, self._sort_state))

    def _apply_sort(self):
        """현재 상태로 정렬 적용"""
        col_map = {
            'ID': 'course_id',
            'Name': 'name',
            'Credits': 'credits',
            'Professor': 'professor',
            'Time': 'time_slots'
        }
        
        attr = col_map.get(self._sort_column)
        if not attr: return
        
        def sort_key(course):
            val = getattr(course, attr)
            if attr == 'credits': return int(val)
            if attr == 'time_slots': return str(val[0]) if val else ""
            return str(val)
            
        self._search_results.sort(key=sort_key, reverse=self._sort_reverse)

    def add_to_config(self, course_id: str, list_type: str, mode: str = 'fixed'):
        """
        검색 결과를 설정에 추가
        
        Args:
            course_id: 강의 ID
            list_type: 'required' or 'desired'
            mode: 'fixed' (고정), 'name' (강의명), 'name_prof' (강의명+교수)
        """
        if not self.config_service or not self.course_service: return
        
        course = self.course_service.get_course_by_id(course_id)
        if not course: return
        
        from ...core.config import CourseFilter
        
        # 모드에 따른 필터 생성
        if mode == 'fixed':
            c_filter = CourseFilter(course_id=course.course_id, name=course.name) # name은 표시용 보조
        elif mode == 'name':
            c_filter = CourseFilter(name=course.name)
        elif mode == 'name_prof':
            c_filter = CourseFilter(name=course.name, professor=course.professor)
        else:
            return
        
        # 🎯 중복 체크 및 추가
        success = False
        if list_type == 'required':
            success = self.config_service.add_required_course(c_filter)
            type_str = "필수"
        else:
            success = self.config_service.add_desired_course(c_filter)
            type_str = "희망"
        
        # 🎯 사용자 피드백
        if success:
            # 성공: 추가 완료
            msg = f"{course.name}"
            self.show_info("추가 완료", msg)
            self.notify('config_updated', None)
        else:
            # 실패: 중복
            msg = f"{course.name}은(는) 이미 {type_str} 강의에 추가되어 있습니다."
            self.show_warning("중복된 강의", msg)
