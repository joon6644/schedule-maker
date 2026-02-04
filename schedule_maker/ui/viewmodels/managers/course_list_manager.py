"""
강의 목록 관리 클래스
ConfigViewModel에서 강의 CRUD 책임을 분리
"""
from typing import List, Tuple, Optional


class CourseListManager:
    """
    필수/희망 강의 목록의 추가, 삭제, 이동, 재정렬 담당
    """
    
    def __init__(self, config_service, course_service=None):
        self.config_service = config_service
        self.course_service = course_service
        
    def add_course(self, list_type: str, name: str, prof: str, course_id: Optional[str] = None) -> bool:
        """강의 추가 (유효성 검사 포함)"""
        # [Fix] Import path correction (4 levels up to schedule_maker)
        try:
            from ....core.config import CourseFilter
        except ImportError:
            from core.config import CourseFilter
        
        # [Validation] Check if course exists in DB
        if self.course_service:
            # 1. ID가 있으면 ID로 검색
            if course_id:
                found = self.course_service.get_course_by_id(course_id)
                if not found:
                    return False # ID 불일치
            
            # 2. 이름/교수명으로 검색 (ID없을 때)
            else:
                # 이름은 필수
                if not name:
                    return False
                
                # 검색 쿼리: 이름 (교수명은 옵션)
                candidates = self.course_service.search_courses(query=name)
                
                # 교수명이 지정된 경우, 해당 교수의 강의가 있는지 확인
                if prof:
                    has_match = any(c.professor == prof for c in candidates)
                    if not has_match:
                        return False # 해당 교수의 강의 없음
                
                # 검색 결과가 아예 없으면 실패
                if not candidates:
                    return False

                # [Strict Validation] 1글자 입력인 경우, 정확히 일치하는 강의가 있어야 함
                # 예: 'd' 입력 시 '3D그래픽스'가 검색되더라도, 'd'라는 강의가 없으면 거절
                if len(name) == 1:
                    has_exact = any(c.name.lower() == name.lower() for c in candidates)
                    if not has_exact:
                        return False

        c_filter = CourseFilter(
            name=name if name else None, 
            professor=prof if prof else None,
            course_id=course_id if course_id else None
        )
        
        if list_type == 'required':
            self.config_service.add_required_course(c_filter)
        else:
            self.config_service.add_desired_course(c_filter)
        
        return True
    
    def remove_course(self, list_type: str, index: int) -> None:
        """강의 삭제"""
        if list_type == 'required':
            self.config_service.remove_required_course(index)
        else:
            self.config_service.remove_desired_course(index)
    
    def move_course(self, source_type: str, target_type: str, index: int) -> bool:
        """강의를 다른 리스트로 이동"""
        config = self.config_service.get_config()
        source_list = config.required_filters if source_type == 'required' else config.desired_filters
        
        if 0 <= index < len(source_list):
            item = source_list[index]
            
            # 삭제
            if source_type == 'required':
                self.config_service.remove_required_course(index)
            else:
                self.config_service.remove_desired_course(index)
            
            # 추가
            if target_type == 'required':
                self.config_service.add_required_course(item)
            else:
                self.config_service.add_desired_course(item)
            
            return True
        return False
    
    def reorder_course(self, list_type: str, old_index: int, new_index: int) -> bool:
        """리스트 내 순서 변경"""
        config = self.config_service.get_config()
        target_list = config.required_filters if list_type == 'required' else config.desired_filters
        
        if 0 <= old_index < len(target_list) and 0 <= new_index <= len(target_list):
            if old_index == new_index:
                return False
            
            # Pop and Insert
            item = target_list.pop(old_index)
            
            # Adjust index if moving down
            if new_index > old_index:
                new_index -= 1
            
            target_list.insert(new_index, item)
            # [Fix] Update Service with modified list
            if list_type == 'required':
                self.config_service.update_required_filters(target_list)
            else:
                self.config_service.update_desired_filters(target_list)
                
            return True
        return False
    
    def rotate_course_slot(self, list_type: str, index: int) -> bool:
        """강의의 다른 시간대(분반)로 변경"""
        if not self.course_service:
            return False
        
        config = self.config_service.get_config()
        target_list = config.required_filters if list_type == 'required' else config.desired_filters
        
        if 0 <= index < len(target_list):
            filter_item = target_list[index]
            
            # 이름으로 모든 분반 검색
            candidates = self.course_service.search_courses(query=filter_item.name)
            if not candidates:
                return False
            
            # 현재 ID와 일치하는 인덱스 찾기
            current_idx = -1
            for i, c in enumerate(candidates):
                if c.course_id == filter_item.course_id:
                    current_idx = i
                    break
            
            # 다음 분반으로 순환
            next_idx = (current_idx + 1) % len(candidates)
            next_course = candidates[next_idx]
            
            # 필터 업데이트
            filter_item.course_id = next_course.course_id
            filter_item.professor = next_course.professor
            
            # [Fix] Update Service with modified list (items are changed in place in target_list)
            if list_type == 'required':
                self.config_service.update_required_filters(target_list)
            else:
                self.config_service.update_desired_filters(target_list)
            
            return True
        return False
    
    def get_formatted_list(self, list_type: str) -> List[Tuple[str, str, str]]:
        """UI 표시용 강의 목록 반환 (ID, Name, Professor)"""
        config = self.config_service.get_config()
        filters = config.required_filters if list_type == 'required' else config.desired_filters
        
        formatted = []
        for cf in filters:
            c_id = cf.course_id or '-'
            name = cf.name or '(모든 강의)'
            prof = cf.professor or '-'
            
            # ID가 있으면 실제 정보를 찾아와서 채우기
            if c_id != '-' and self.course_service:
                actual = self.course_service.get_course_by_id(c_id)
                if actual:
                    name = actual.name
                    prof = actual.professor
            
            formatted.append((c_id, name, prof))
        return formatted
