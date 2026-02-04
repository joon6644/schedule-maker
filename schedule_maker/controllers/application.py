"""
애플리케이션 컨트롤러
전체 프로그램의 실행 흐름을 제어하는 메인 컨트롤러
"""
import os
import sys
from ..core.config import load_config_from_json, ScheduleConfig
from ..core.exceptions import ScheduleMakerError
from ..services.parser import CsvParser, parse_csv
from ..services.scheduler import ScheduleGenerator
from ..services.visualizer import HtmlVisualizer, generate_html


class ApplicationController:
    """애플리케이션 실행 흐름 제어"""
    
    def __init__(self, base_dir: str = "."):
        self.base_dir = base_dir
        self.csv_file = os.path.join(base_dir, "mju_2026_1.csv")
        self.config_file = os.path.join(base_dir, "config.json")
        self.schedules = []
    
    def run(self) -> str:
        """
        전체 프로세스 실행
        Returns:
            생성된 결과 파일 경로
        """
        # 1. 파일 확인
        self._check_files()
        
        # 2. 로딩
        print(f"\n📂 CSV 파일 로딩: {self.csv_file}")
        all_courses = parse_csv(self.csv_file)
        
        if not all_courses:
            raise ScheduleMakerError("CSV 파일에서 강의를 읽을 수 없습니다.")
            
        try:
            config = load_config_from_json(self.config_file)
        except Exception as e:
            raise ScheduleMakerError(f"설정 파일 로딩 실패: {e}")
            
        # 3. 생성
        generator = ScheduleGenerator(all_courses, config)
        self.schedules = generator.generate_all_schedules()
        
        if not self.schedules:
            raise ScheduleMakerError("조건에 맞는 시간표 조합을 찾을 수 없습니다.\n\n[팁]\n- 학점 범위를 넓혀보세요.\n- 필수 강의를 줄여보세요.\n- 시간 충돌을 확인하세요.")
            
        # 4. 저장 및 시각화
        output_file = os.path.join(self.base_dir, "schedule_results.html")
        
        # 필수/희망 이름 추출 (시각화용)
        required_names = set()
        if hasattr(generator, 'required_course_groups'):
            for group in generator.required_course_groups:
                for course in group:
                    required_names.add(course.name)
        
        desired_names = set()
        if hasattr(generator, 'desired_course_groups'):
            for group in generator.desired_course_groups:
                for course in group:
                    desired_names.add(course.name)
                    
        generate_html(self.schedules, output_file, required_names, desired_names)
        
        return output_file

    def _check_files(self):
        """필요한 파일 존재 여부 확인"""
        if not os.path.exists(self.csv_file):
            raise ScheduleMakerError(f"CSV 파일을 찾을 수 없습니다:\n{self.csv_file}\n\n'mju_2026_1.csv' 파일이 필요합니다.")
            
        if not os.path.exists(self.config_file):
            raise ScheduleMakerError(f"설정 파일을 찾을 수 없습니다:\n{self.config_file}")

    def get_schedule_count(self) -> int:
        return len(self.schedules)
