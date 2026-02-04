"""
시간표 조합 생성 프로그램 - 데이터 모델
"""
from dataclasses import dataclass
from typing import List
from copy import deepcopy

# bitmask constants
DAYS_MAP = {'월': 0, '화': 1, '수': 2, '목': 3, '금': 4, '토': 5, '일': 6}

def time_str_to_index(day: str, time_str: str) -> int:
    """요일과 시간을 비트 인덱스로 변환 (5분 단위)"""
    # 24시간 * 12슬롯(5분) = 288 slots per day
    day_idx = DAYS_MAP.get(day, 0)
    hours, minutes = map(int, time_str.split(':'))
    # 5분 단위 인덱스 (0~287)
    slot_idx = hours * 12 + (minutes // 5)
    return day_idx * 288 + slot_idx

def calculate_time_mask(time_slots: List['TimeSlot']) -> int:
    """시간 목록을 비트마스크로 변환"""
    mask = 0
    for slot in time_slots:
        start_idx = time_str_to_index(slot.day, slot.start_time)
        end_idx = time_str_to_index(slot.day, slot.end_time)
        # end_time은 포함되지 않으므로 range(start, end)
        for i in range(start_idx, end_idx):
            mask |= (1 << i)
    return mask


@dataclass
class TimeSlot:
    """요일과 시간을 표현하는 클래스"""
    day: str  # 월, 화, 수, 목, 금
    start_time: str  # HH:MM 형식
    end_time: str  # HH:MM 형식
    room: str = ""  # 강의실 (선택)
    
    def overlaps(self, other: 'TimeSlot') -> bool:
        """다른 TimeSlot과 시간이 겹치는지 확인"""
        if self.day != other.day:
            return False
        
        # 시간 문자열을 분으로 변환
        def time_to_minutes(time_str: str) -> int:
            hours, minutes = map(int, time_str.split(':'))
            return hours * 60 + minutes
        
        self_start = time_to_minutes(self.start_time)
        self_end = time_to_minutes(self.end_time)
        other_start = time_to_minutes(other.start_time)
        other_end = time_to_minutes(other.end_time)
        
        # 겹침 조건: 한 쪽의 시작이 다른 쪽의 범위 안에 있음
        return not (self_end <= other_start or other_end <= self_start)
    
    def __str__(self):
        return f"{self.day} {self.start_time}~{self.end_time}"


@dataclass
class Course:
    """강의 정보를 저장하는 클래스"""
    course_id: str  # 강좌번호
    name: str  # 교과목명
    credits: int  # 학점
    professor: str  # 담당교수
    time_slots: List[TimeSlot]  # 강의 시간 목록
    category: str = ""  # 이수구분 (예: 전필, 교양 등)
    target_grade: str = ""  # 대상 학년 (예: 1학년, 전학년)
    time_mask: int = 0  # 비트마스크 (충돌 검사용)
    
    def __post_init__(self):
        # 객체 생성 후 비트마스크 계산
        if self.time_mask == 0 and self.time_slots:
            self.time_mask = calculate_time_mask(self.time_slots)

    def has_conflict(self, other: 'Course') -> bool:
        """다른 강의와 시간 충돌이 있는지 확인 (비트마스크 사용)"""
        return (self.time_mask & other.time_mask) > 0
    
    # 레거시 메서드 (혹시 모를 호환성 위해 남겨둠, 필요 없으면 제거 가능)
    def has_conflict_legacy(self, other: 'Course') -> bool:
        """다른 강의와 시간 충돌이 있는지 확인"""
        for slot1 in self.time_slots:
            for slot2 in other.time_slots:
                if slot1.overlaps(slot2):
                    return True
        return False
    
    @property
    def time_summary(self) -> str:
        """시간 정보를 문자열로 반환"""
        if not self.time_slots:
            return "시간 정보 없음"
        return ", ".join(str(slot) for slot in self.time_slots)

    def __hash__(self):
        return hash(self.course_id)

    def __eq__(self, other):
        if not isinstance(other, Course):
            return NotImplemented
        return self.course_id == other.course_id

    def __str__(self):
        return f"{self.name} ({self.professor}) - {self.time_summary}"


class Schedule:
    """시간표 조합을 표현하는 클래스"""
    
    def __init__(self):
        self.courses: List[Course] = []
        self.total_credits: int = 0
        self.course_names: set = set()  # 이미 선택된 강의명 (중복 방지)
        self.total_time_mask: int = 0  # 전체 시간표 비트마스크
        self.has_random_filled: bool = False  # 랜덤 채우기 적용 여부
    
    def add_course(self, course: Course) -> bool:
        """강의를 추가 (충돌 없으면 True 반환)"""
        # 1. 같은 강의명 중복 체크
        if course.name in self.course_names:
            return False
        
        # 2. 비트마스크로 초고속 충돌 검사
        if (self.total_time_mask & course.time_mask) > 0:
            return False
            
        # 3. 추가 (비트마스크 업데이트)
        self.total_time_mask |= course.time_mask
        self.courses.append(course)
        self.total_credits += course.credits
        self.course_names.add(course.name)
        return True
    
    def remove_course(self, course: Course):
        """강의를 제거"""
        if course in self.courses:
            self.courses.remove(course)
            self.total_credits -= course.credits
            self.course_names.discard(course.name)
            # 비트마스크 제거 (XOR 또는 AND NOT)
            # 주의: 겹치는 강의가 절대 없다는 가정하에 XOR가 빠름
            # 하지만 안전하게 AND NOT 사용: mask & (~course_mask)
            self.total_time_mask &= ~course.time_mask
    
    def copy(self) -> 'Schedule':
        """스케줄 복사본 생성"""
        new_schedule = Schedule()
        new_schedule.courses = self.courses.copy()
        new_schedule.total_credits = self.total_credits
        new_schedule.course_names = self.course_names.copy()
        new_schedule.total_time_mask = self.total_time_mask
        new_schedule.has_random_filled = self.has_random_filled
        return new_schedule
    
    def get_content_hash(self) -> tuple:
        """
        시간표의 컨텐츠 기반 해시 생성 (중복 체크용)
        강의명, 교수명, 시간 정보를 조합하여 유일한 시그니처 생성
        """
        signatures = []
        for course in self.courses:
            # 같은 과목명이라도 시간이 다르면 다른 수업으로 취급
            signatures.append(f"{course.name}|{course.professor}|{course.time_summary}")
        return tuple(sorted(signatures))
    
    def __str__(self):
        course_names = [c.name for c in self.courses]
        return f"Schedule ({self.total_credits}학점): {', '.join(course_names)}"
