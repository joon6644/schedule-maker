"""
설정 관리 모듈
이수학점 범위, 필수/희망 강의 필터 관리
"""
from dataclasses import dataclass
from typing import List, Optional, Tuple
import json
import os
try:
    from .models import Course
except ImportError:
    from models import Course


@dataclass
class CourseFilter:
    """
    강의 검색 필터
    강의명, 시간 패턴, 교수명 중 하나만 지정해도 매칭 가능
    """
    name: Optional[str] = None  # 예: "영어1"
    professor: Optional[str] = None  # 예: "전미경"
    course_id: Optional[str] = None  # 예: "5924"
    
    def matches(self, course: Course) -> bool:
        """이 필터가 주어진 강의에 매칭되는지 확인 (AND 조건 + 스마트 검색)"""
        # 강의번호가 지정된 경우 최우선 확인 (일치 검색)
        if self.course_id:
            return self.course_id == course.course_id

        # Lv.1 검색 기능: 띄어쓰기는 AND 조건으로 처리 ("영어 회화" -> 영어 AND 회화)
        if self.name:
            keywords = self.name.split()
            if not all(k in course.name for k in keywords):
                return False
        
        if self.professor:
            keywords = self.professor.split()
            if not all(k in course.professor for k in keywords):
                return False
        
        return True

    def __eq__(self, other):
        if not isinstance(other, CourseFilter):
            return NotImplemented
        
        # Treat None and "" as equal for comparison
        def normalize(val):
            return val if val else None

        return (normalize(self.name) == normalize(other.name) and 
                normalize(self.professor) == normalize(other.professor) and 
                normalize(self.course_id) == normalize(other.course_id))
    
    def __str__(self):
        parts = []
        if self.course_id:
            parts.append(f"강의번호:{self.course_id}")
        if self.name:
            parts.append(f"강의명:{self.name}")

        if self.professor:
            parts.append(f"교수:{self.professor}")
        return " AND ".join(parts) if parts else "빈 필터"


@dataclass
class ScheduleConfig:
    """시간표 생성 설정"""
    min_credits: int
    max_credits: int
    required_filters: List[CourseFilter]  # 필수 강의 필터
    desired_filters: List[CourseFilter]  # 희망 강의 필터
    excluded_days: List[str]  # 제외할 요일 리스트 (예: ["금"])
    excluded_time_slots: List[Tuple[str, str, str]]  # 제외할 시간대 [(요일, 시작, 종료)]

    def __eq__(self, other):
        if not isinstance(other, ScheduleConfig):
            return NotImplemented
        
        # 순서 무관 비교를 위해 정렬 또는 set 활용 (단, 리스트 내부 요소가 hashable해야 함)
        # 여기서는 단순 리스트 비교를 진행하되, UI 상에서의 순서 변경도 변경으로 간주할지 여부에 따라 다름.
        # 사용자가 순서만 바꿔도 "변경"으로 보는 것이 직관적일 수 있음.
        # 따라서 단순 equality check 사용.
        
        return (self.min_credits == other.min_credits and
                self.max_credits == other.max_credits and
                self.required_filters == other.required_filters and
                self.desired_filters == other.desired_filters and
                set(self.excluded_days) == set(other.excluded_days) and
                sorted(self.excluded_time_slots) == sorted(other.excluded_time_slots))

    def clone(self):
        """설정 객체 깊은 복사"""
        import copy
        return copy.deepcopy(self)


def load_config_from_json(filepath: str = "config.json") -> ScheduleConfig:
    """JSON 파일에서 설정 로드"""
    if not os.path.exists(filepath):
        print(f"⚠️ 설정 파일을 찾을 수 없습니다: {filepath} (기본값 사용)")
        return ScheduleConfig(12, 18, [], [], [], [])
    
    with open(filepath, 'r', encoding='utf-8') as f:
        data = json.load(f)
    
    # 학점 설정 (신구 호환)
    if '학점_설정' in data:
        min_credits = data['학점_설정'].get('최소_학점', 12)
        max_credits = data['학점_설정'].get('최대_학점', 18)
    else:
        min_credits = data.get('min_credits', 12)
        max_credits = data.get('max_credits', 18)
    
    # 공통 파싱 헬퍼
    def parse_course_list(key_new, key_old):
        result = []
        raw_list = data.get(key_new, data.get(key_old, []))
        for item in raw_list:
            if isinstance(item, dict):
                # 신규 구조 vs 기존 구조
                c_id = item.get('course_id') or item.get('강의번호')
                
                # 조건 검색 객체 처리 (구버전 호환)
                name = item.get('name')
                prof = item.get('professor')
                
                if '조건_검색' in item:
                    name = item['조건_검색'].get('강의명')
                    prof = item['조건_검색'].get('교수명')
                
                result.append(CourseFilter(
                    name=name, 
                    professor=prof, 
                    course_id=c_id
                ))
        return result

    required_filters = parse_course_list('required_courses', '필수_강의')
    desired_filters = parse_course_list('desired_courses', '희망_강의')
    
    # 제외 요일
    excluded_days = data.get('excluded_days', data.get('제외_요일', []))
    
    # 제외 시간
    excluded_time_slots = []
    excluded_time_raw = data.get('excluded_time_slots', data.get('제외_시간', []))
    
    for time_str in excluded_time_raw:
        try:
            # "월 09:00~10:00"
            parts = time_str.strip().split()
            if len(parts) == 2:
                day = parts[0]
                time_range = parts[1].split('~')
                if len(time_range) == 2:
                    excluded_time_slots.append((day, time_range[0], time_range[1]))
        except:
            pass
    
    config = ScheduleConfig(
        min_credits=min_credits,
        max_credits=max_credits,
        required_filters=required_filters,
        desired_filters=desired_filters,
        excluded_days=excluded_days,
        excluded_time_slots=excluded_time_slots
    )
    
    print("\n✅ 설정 로드 완료 (JSON 표준화 모드)")
    print(f"  - 필수: {len(required_filters)}개, 희망: {len(desired_filters)}개")
    return config


def save_config_to_json(config: ScheduleConfig, filepath: str = "config.json"):
    """설정을 표준화된 JSON 구조로 저장"""
    def to_dict_list(filters):
        res = []
        for f in filters:
            item = {}
            if f.name: item['name'] = f.name
            if f.professor: item['professor'] = f.professor
            if f.course_id: item['course_id'] = f.course_id
            res.append(item)
        return res

    data = {
        "min_credits": config.min_credits,
        "max_credits": config.max_credits,
        "required_courses": to_dict_list(config.required_filters),
        "desired_courses": to_dict_list(config.desired_filters),
        "excluded_days": config.excluded_days,
        "excluded_time_slots": [
            f"{day} {start}~{end}" for day, start, end in config.excluded_time_slots
        ]
    }
    
    with open(filepath, 'w', encoding='utf-8') as f:
        json.dump(data, f, ensure_ascii=False, indent=4)
    
    print(f"\n✅ 설정이 저장되었습니다: {filepath}")


def load_config_interactive() -> ScheduleConfig:
    """대화형으로 설정 입력받기"""
    print("\n" + "=" * 50)
    print("   시간표 조합 생성기 설정")
    print("=" * 50)
    
    # 학점 범위 입력
    while True:
        try:
            min_credits = int(input("\n최소 이수학점: "))
            max_credits = int(input("최대 이수학점: "))
            if min_credits <= max_credits:
                break
            print("❌ 최소 학점은 최대 학점보다 작거나 같아야 합니다.")
        except ValueError:
            print("❌ 숫자를 입력해주세요.")
    
    # 필수 강의 입력
    required_filters = []
    print("\n" + "-" * 50)
    print("필수 강의 입력 (최소 1개 이상)")
    print("강의명, 시간, 교수명 중 하나만 입력해도 됩니다.")
    print("\n💡 팁: 여러 강의를 한 번에 입력하려면 첫 번째 강의명에")
    print("    강의 목록을 붙여넣기 하세요 (한 줄에 하나씩)")
    print("종료하려면 모두 빈 칸으로 Enter")
    print("-" * 50)
    
    # 첫 입력 시 복사-붙여넣기 감지
    print(f"\n[필수 강의 입력]")
    first_input = input("  강의명 (또는 목록 붙여넣기): ").strip()
    
    # 여러 줄 입력 감지 (줄바꿈 포함)
    if '\n' in first_input:
        print("\n📋 복사-붙여넣기 모드: 여러 강의 감지")
        lines = first_input.split('\n')
        for line in lines:
            line = line.strip()
            if line:
                # '교과목명|교수명' 형식 지원
                if '|' in line:
                    name, prof = line.split('|', 1)
                    required_filters.append(CourseFilter(name=name.strip(), professor=prof.strip()))
                    print(f"  ✅ {name.strip()} ({prof.strip()})")
                else:
                    required_filters.append(CourseFilter(name=line))
                    print(f"  ✅ {line}")
    else:
        # 단일 입력 모드
        if first_input:
            required_filters.append(CourseFilter(name=first_input))
            print(f"  ✅ {first_input}")
        
        # 추가 입력
        while True:
            print(f"\n[필수 강의 {len(required_filters) + 1}]")
            name = input("  강의명: ").strip()
            
            if not name:
                if len(required_filters) == 0:
                    print("❌ 필수 강의를 최소 1개 이상 입력해주세요.")
                    continue
                break
            
            time = input("  시간 (선택): ").strip()
            prof = input("  교수명 (선택): ").strip()
            
            filter_obj = CourseFilter(
                name=name if name else None,
                time_pattern=time if time else None,
                professor=prof if prof else None
            )
            required_filters.append(filter_obj)
            print(f"  ✅ 추가됨: {filter_obj}")
    
    # 희망 강의 입력
    desired_filters = []
    print("\n" + "-" * 50)
    print("희망 강의 입력 (선택사항)")
    print("종료하려면 모두 빈 칸으로 Enter")
    print("-" * 50)
    
    while True:
        print(f"\n[희망 강의 {len(desired_filters) + 1}]")
        name = input("  강의명: ").strip()
        time = input("  시간: ").strip()
        prof = input("  교수명: ").strip()
        
        if not (name or time or prof):
            break
        
        filter_obj = CourseFilter(
            name=name if name else None,
            time_pattern=time if time else None,
            professor=prof if prof else None
        )
        desired_filters.append(filter_obj)
        print(f"  ✅ 추가됨: {filter_obj}")
    
    # 제외할 요일 입력
    excluded_days = []
    print("\n" + "-" * 50)
    print("제외할 요일 선택 (선택사항)")
    print("예: 금요일에 강의를 듣고 싶지 않으면 '금' 입력")
    print("-" * 50)
    
    available_days = ['월', '화', '수', '목', '금']
    print(f"사용 가능한 요일: {', '.join(available_days)}")
    
    exclude_input = input("\n제외할 요일 (쉼표로 구분, 예: 금,토): ").strip()
    if exclude_input:
        for day in exclude_input.split(','):
            day = day.strip()
            if day in available_days:
                excluded_days.append(day)
                print(f"  ✅ '{day}' 요일 제외")
            else:
                print(f"  ⚠️  '{day}'는 유효하지 않은 요일입니다.")
    
    config = ScheduleConfig(
        min_credits=min_credits,
        max_credits=max_credits,
        required_filters=required_filters,
        desired_filters=desired_filters,
        excluded_days=excluded_days
    )
    
    # 설정 요약 출력
    print("\n" + "=" * 50)
    print("   설정 완료")
    print("=" * 50)
    print(f"학점 범위: {min_credits} ~ {max_credits}")
    print(f"필수 강의: {len(required_filters)}개")
    for i, f in enumerate(required_filters, 1):
        print(f"  {i}. {f}")
    print(f"희망 강의: {len(desired_filters)}개")
    for i, f in enumerate(desired_filters, 1):
        print(f"  {i}. {f}")
    if excluded_days:
        print(f"제외 요일: {', '.join(excluded_days)}")
    print("=" * 50 + "\n")
    
    return config
