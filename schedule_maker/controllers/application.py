"""
Application execution controller.
"""
import glob
import os
import re

from ..core.config import load_config_from_json
from ..core.exceptions import ScheduleMakerError
from ..services.parser import parse_csv
from ..services.scheduler import ScheduleGenerator
from ..services.visualizer import generate_html


class ApplicationController:
    def __init__(self, base_dir: str = "."):
        self.base_dir = base_dir
        self.csv_file = self._resolve_csv_file()
        self.term_key = self._extract_term_key(self.csv_file)
        self.config_file = self._resolve_config_file(self.term_key)
        self.schedules = []

    def _resolve_csv_file(self) -> str:
        preferred = os.path.join(self.base_dir, "mju_2026_2.csv")
        if os.path.exists(preferred):
            return preferred
        candidates = glob.glob(os.path.join(self.base_dir, "mju_*.csv"))
        if candidates:
            candidates.sort(key=lambda path: os.path.getmtime(path), reverse=True)
            return candidates[0]
        return preferred

    def _extract_term_key(self, csv_path: str):
        filename = os.path.basename(csv_path)
        match = re.match(r"mju_(\d{4})_(\d)\.csv$", filename)
        if match:
            return f"{match.group(1)}_{match.group(2)}"
        return None

    def _resolve_config_file(self, term_key: str):
        config_dir = os.path.join(self.base_dir, "data", "configs")
        os.makedirs(config_dir, exist_ok=True)
        if term_key:
            return os.path.join(config_dir, f"{term_key}.json")
        return os.path.join(config_dir, "default.json")

    def run(self) -> str:
        self._check_files()

        print(f"\n[INFO] CSV file loaded: {self.csv_file}")
        all_courses = parse_csv(self.csv_file)
        if not all_courses:
            raise ScheduleMakerError("Could not read any courses from the CSV file.")

        try:
            config = load_config_from_json(self.config_file)
        except Exception as e:
            raise ScheduleMakerError(f"Failed to load config: {e}")

        generator = ScheduleGenerator(all_courses, config)
        self.schedules = generator.generate_all_schedules()
        if not self.schedules:
            raise ScheduleMakerError(
                "Could not find any schedules matching the conditions.\n\n"
                "[Check]\n"
                "- Reduce credit range\n"
                "- Reduce required courses\n"
                "- Check time conflicts"
            )

        output_file = os.path.join(self.base_dir, "schedule_results.html")
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

        year = self.term_key.split('_')[0] if self.term_key and '_' in self.term_key else None
        semester = self.term_key.split('_')[1] if self.term_key and '_' in self.term_key else None
        generate_html(
            self.schedules,
            output_file,
            required_names,
            desired_names,
            year=year,
            semester=semester
        )
        return output_file

    def _check_files(self):
        if not os.path.exists(self.csv_file):
            raise ScheduleMakerError(
                f"CSV file not found:\n{self.csv_file}\n\n"
                "A file named mju_YYYY_S.csv is required."
            )
        if not os.path.exists(self.config_file):
            raise ScheduleMakerError(f"Config file not found:\n{self.config_file}")

    def get_schedule_count(self) -> int:
        return len(self.schedules)
