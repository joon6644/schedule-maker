"""
강의 CSV → 웹 프론트엔드용 JSON 변환
데스크톱 앱과 같은 파서(CsvParser)를 사용하므로 두 앱이 동일한 강의 목록을 사용함.
웹은 최신 학기만 쓰므로 가장 최근 학기 하나만 내보내고, 지난 학기 JSON은 지움.

사용법: python tools/export_courses.py
출력:   web/public/data/terms.json, web/public/data/mju_YYYY_N.json
"""
import contextlib
import glob
import io
import json
import os
import re
import sys

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, ROOT)

from schedule_maker.services.parser import CsvParser  # noqa: E402

CSV_DIR = os.path.join(ROOT, 'data', 'csv')
OUT_DIR = os.path.join(ROOT, 'web', 'public', 'data')


def export_term(csv_path: str) -> dict:
    with contextlib.redirect_stdout(io.StringIO()):
        courses = CsvParser.parse(csv_path)
    return {
        'courses': [
            {
                'id': c.course_id,
                'name': c.name,
                'credits': c.credits,
                'professor': c.professor,
                'category': c.category,
                'grade': c.target_grade,
                'slots': [
                    {'day': s.day, 'start': s.start_time, 'end': s.end_time, 'room': s.room}
                    for s in c.time_slots
                ],
            }
            for c in courses
        ]
    }


def main():
    os.makedirs(OUT_DIR, exist_ok=True)
    found = []
    for csv_path in glob.glob(os.path.join(CSV_DIR, 'mju_*.csv')):
        match = re.match(r'mju_(\d{4})_(\d)\.csv$', os.path.basename(csv_path))
        if match:
            found.append((int(match.group(1)), int(match.group(2)), csv_path))
    if not found:
        sys.exit(f'{CSV_DIR} 에 mju_YYYY_N.csv 파일이 없습니다')

    year, semester, csv_path = max(found)
    key = f'mju_{year}_{semester}'
    data = export_term(csv_path)
    with open(os.path.join(OUT_DIR, f'{key}.json'), 'w', encoding='utf-8') as f:
        json.dump(data, f, ensure_ascii=False, separators=(',', ':'))
    print(f'{key}: {len(data["courses"])}개 강의')

    # 지난 학기 데이터 정리
    for old in glob.glob(os.path.join(OUT_DIR, 'mju_*.json')):
        if os.path.basename(old) != f'{key}.json':
            os.remove(old)
            print(f'삭제: {os.path.basename(old)}')

    terms = [{'key': key, 'year': year, 'semester': semester,
              'label': f'{year}년 {semester}학기', 'count': len(data['courses'])}]
    with open(os.path.join(OUT_DIR, 'terms.json'), 'w', encoding='utf-8') as f:
        json.dump(terms, f, ensure_ascii=False, indent=2)


if __name__ == '__main__':
    main()
