"""
CSV 파일 파서
명지대 시간표 CSV를 파싱하여 Course 객체 리스트로 변환
"""
import pandas as pd
import re
from typing import List
from ..core.models import Course, TimeSlot


def parse_time_string(time_str: str) -> List[TimeSlot]:
    """
    강의시간 문자열을 TimeSlot 리스트로 파싱
    
    예시:
    - "월 09:00~10:50 (S1221)" → [TimeSlot(day="월", start="09:00", end="10:50", room="S1221")]
    - "화 13:30~14:45 (S1919)  목 13:30~14:45 (S1919)" → 2개의 TimeSlot
    """
    if not time_str or pd.isna(time_str):
        return []
    
    time_slots = []
    
    # 정규식 패턴: (요일) (시작시간)~(종료시간) (강의실)
    # 예: "월 09:00~10:50 (S1221)"
    pattern = r'([월화수목금])\s+(\d{2}:\d{2})~(\d{2}:\d{2})\s*(?:\(([^)]*)\))?'
    
    matches = re.findall(pattern, time_str)
    
    for match in matches:
        day, start_time, end_time, room = match
        time_slots.append(TimeSlot(
            day=day,
            start_time=start_time,
            end_time=end_time,
            room=room if room else ""
        ))
    
    return time_slots


class CsvParser:
    """CSV 파싱을 담당하는 클래스"""
    
    @staticmethod
    def parse(filepath: str) -> List[Course]:
        """
        명지대 시간표 CSV 파일을 파싱하여 Course 리스트 반환
        
        사용 컬럼: 교과목명, 학점, 담당교수, 강좌번호, 강의시간
        """
        print(f"CSV 파일 로딩 중: {filepath}")
        
        # CSV 읽기 (인코딩 자동 감지)
        try:
            df = pd.read_csv(filepath, encoding='utf-8-sig')
        except UnicodeDecodeError:
            df = pd.read_csv(filepath, encoding='cp949')
        
        # 유연한 컬럼명 처리를 위한 매핑
        col_map = {
            'id': ['강좌번호', '번호', 'No', 'no'],
            'name': ['교과목명', '과목명', '강의명', '교과목', '과목'],
            'credits': ['학점', '이수학점'],
            'professor': ['담당교수', '교수명', '교수'],
            'time': ['강의시간', '시간', '요일/교시', '강의시간표'],
            'category': ['이수구분', '이수', '구분', 'category'],
            'grade': ['학년', '대상학년']
        }
        
        # 실제 CSV 컬럼과 매핑 찾기
        actual_cols = {}
        for key, candidates in col_map.items():
            for candidate in candidates:
                if candidate in df.columns:
                    actual_cols[key] = candidate
                    break
            if key not in actual_cols:
                # category, grade는 선택 사항이므로 경고 없이 넘어감
                if key in ['category', 'grade']:
                    continue
                    
                print(f"⚠️  필수 컬럼을 찾을 수 없습니다: {key} (후보: {candidates})")
                # 필수 컬럼이 없으면 진행 불가할 수 있음 (강의시간은 필수)
                if key == 'time' or key == 'name':
                    return []

        courses = []
        skipped = 0
        
        for idx, row in df.iterrows():
            # 데이터 추출 (안전하게)
            time_str = str(row.get(actual_cols['time'], '')).strip()
            
            # 강의시간이 없는 강좌는 스킵
            if not time_str or time_str == 'nan':
                skipped += 1
                continue
            
            # 시간 파싱
            time_slots = parse_time_string(time_str)
            
            if not time_slots:
                skipped += 1
                continue
            
            # 나머지 데이터 추출
            try:
                course_id = str(row.get(actual_cols.get('id', ''), '')).strip()
                name = str(row.get(actual_cols['name'], '')).strip()
                
                # 학점 처리 (숫자가 아닌 경우 대비)
                credits_val = row.get(actual_cols.get('credits', 0), 0)
                try:
                    credits = int(float(credits_val))
                except (ValueError, TypeError):
                    credits = 0
                    
                professor = str(row.get(actual_cols.get('professor', ''), '')).strip()
                if professor == 'nan': professor = ''
                
                category = str(row.get(actual_cols.get('category', ''), '')).strip()
                if category == 'nan': category = ''

                target_grade = str(row.get(actual_cols.get('grade', ''), ''),).strip()
                if target_grade == 'nan': target_grade = ''

                # Course 객체 생성
                course = Course(
                    course_id=course_id,
                    name=name,
                    credits=credits,
                    professor=professor,
                    time_slots=time_slots,
                    category=category,
                    target_grade=target_grade
                )
                
                courses.append(course)
            except Exception as e:
                print(f"  ⚠️  데이터 파싱 오류 (Line {idx}): {e}")
                skipped += 1
                continue
        
        print(f"✅ 총 {len(courses)}개 강의 로드 완료 (스킵: {skipped}개)")
        return courses

# 하위 호환성을 위한 함수 래퍼
def parse_csv(filepath: str) -> List[Course]:
    return CsvParser.parse(filepath)
