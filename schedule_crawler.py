from __future__ import annotations

import argparse
import os
import time
from io import StringIO

import pandas as pd
from selenium import webdriver
from selenium.webdriver.chrome.service import Service
from webdriver_manager.chrome import ChromeDriverManager


DEFAULT_TIMETABLE_URL = "https://msi.mju.ac.kr/servlet/su/sue/Sue00Svl06viewTimetable"
DEFAULT_OUTPUT_TEMPLATE = "mju_{year}_{semester}.csv"


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        description="MJU 시간표 페이지를 수집해서 CSV로 저장합니다."
    )
    parser.add_argument(
        "--year",
        type=int,
        default=2026,
        help="강의 연도. 기본값: 2026",
    )
    parser.add_argument(
        "--semester",
        type=int,
        choices=(1, 2),
        default=2,
        help="학기(1 또는 2). 기본값: 2",
    )
    parser.add_argument(
        "--output",
        default=None,
        help="저장할 CSV 파일명. 미지정 시 mju_{year}_{semester}.csv 형식으로 저장",
    )
    parser.add_argument(
        "--url",
        default=DEFAULT_TIMETABLE_URL,
        help="시간표 조회 URL",
    )
    parser.add_argument(
        "--max-pages",
        type=int,
        default=130,
        help="최대 수집 페이지 수",
    )
    parser.add_argument(
        "--sleep",
        type=float,
        default=1.0,
        help="페이지 전환 대기 시간(초)",
    )
    return parser


def extract_largest_table(html: str) -> pd.DataFrame:
    dfs = pd.read_html(StringIO(html))
    if not dfs:
        raise ValueError("HTML에서 표를 찾지 못했습니다.")
    return max(dfs, key=len)


def crawl_timetable(url: str, max_pages: int = 130, sleep_seconds: float = 1.0) -> pd.DataFrame:
    driver = webdriver.Chrome(service=Service(ChromeDriverManager().install()))
    all_data = []
    try:
        driver.get(url)
        print("[중요] 로그인 후 '교과/수강 -> 학과별강의시간표 -> 조회(모든 학과의 시간표가 나오게)' 화면까지 이동한 뒤 터미널에서 Enter를 눌러주세요.")
        input()

        for page in range(1, max_pages + 1):
            print(f"[수집] {page}/{max_pages} 페이지")
            try:
                all_data.append(extract_largest_table(driver.page_source))
                driver.execute_script(f"go_page({page + 1})")
                time.sleep(sleep_seconds)
            except Exception as exc:
                print(f"[중단] {page}페이지 수집 실패: {exc}")
                break
    finally:
        driver.quit()

    if not all_data:
        raise RuntimeError("수집된 데이터가 없습니다.")

    final_df = pd.concat(all_data, ignore_index=True).drop_duplicates()
    return final_df


def main() -> int:
    args = build_parser().parse_args()
    output = args.output or DEFAULT_OUTPUT_TEMPLATE.format(
        year=args.year,
        semester=args.semester,
    )

    df = crawl_timetable(args.url, max_pages=args.max_pages, sleep_seconds=args.sleep)
    df.to_csv(output, index=False, encoding="utf-8-sig")
    print(f"[완료] {len(df)}개 행을 {os.path.abspath(output)}에 저장했습니다.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
