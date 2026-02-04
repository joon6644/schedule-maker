"""
시간표 조합 생성 스케줄러 (Randomized Backtracking + Restart Engine)
DFS 백트래킹을 사용하여 시간표 조합을 생성하되, 다양성을 위해 무작위성을 도입함.

최적화 적용:
- 발견 속도 기반 조기 종료
- 중복 제거 (content hash)
- 휴리스틱 정렬 (학점 우선, 제약 많은 것 우선)
- 로깅 강화
"""
import re
import random
import sys
import time
import logging
from collections import deque
from typing import List, Optional, Callable
from ..core.models import Course, Schedule, time_str_to_index
from ..core.config import ScheduleConfig, CourseFilter
from ..core.models import Course, Schedule, time_str_to_index
from ..core.config import ScheduleConfig, CourseFilter
from ..core.constants import SchedulerConfig as AlgoConfig, BusinessConstants

# 로거 설정
logger = logging.getLogger(__name__)

# 커스텀 예외 정의
class GenerationError(Exception):
    """시간표 생성 중 발생하는 예외 (사용자에게 알릴 메시지 포함)"""
    pass

class ScheduleGenerator:
    
    def __init__(self, all_courses: List[Course], config: ScheduleConfig):
        self.all_courses = all_courses
        self.config = config
        self.results: List[Schedule] = []
        
        # Random Fill을 위한 '전학년' 대상 강의 후보군 미리 필터링
        # (학점 채우기 용도)
        # [Refactor] Regex 대신 하드코딩된 제외 목록 사용 (BusinessConstants.EXCLUDED_RANDOM_FILL_SUBJECTS)
        
        self.random_fill_candidates = [
            c for c in all_courses 
            if ("전학년" in c.target_grade or "전학년" in c.category) 
            and c.name not in BusinessConstants.EXCLUDED_RANDOM_FILL_SUBJECTS
        ]
        
        # [Refactor] 필수 강의 Grouping 로직 개선 (Object-Oriented Fix)
        # 이전 로직: 필터링 결과의 모든 강의를 '강의명' 기준으로 다시 쪼개서 Grouping (필터 1개 -> 여러 Group -> AND 조건)
        # 개선 로직: 각 필터(Requirement) 당 하나의 Group 생성 (필터 1개 -> 1 Group -> OR 조건)
        
        self.required_course_groups = []
        
        print("\n📚 필수 강의 매칭 결과 (Requirement 기반):")
        
        for idx, filter_obj in enumerate(config.required_filters):
            matched_courses = self._find_all_matching_courses(filter_obj)
            
            if not matched_courses:
                # [OOP Fix] 객체 생성 시점에 검증 실패 시 예외 발생
                filter_name = filter_obj.name or filter_obj.professor or "알 수 없는 필터"
                raise GenerationError(f"필수 강의를 찾을 수 없습니다: {filter_name}")
            
            # 이 필터(요구사항)를 만족시키는 후보군 목록
            # 중복 제거 (Course ID 기준이 아니라 필터 매칭 결과 자체 - list(set()))
            unique_candidates = list(set(matched_courses))
            self.required_course_groups.append(unique_candidates)
            
            # 로깅
            filter_desc = filter_obj.name or "조건검색"
            print(f"  ✓ [Req {idx+1}] '{filter_desc}': {len(unique_candidates)}개 강의 중 택1")
            
            # 상세 후보 출력
            if len(unique_candidates) <= 5:
                for c in unique_candidates:
                    print(f"      - {c.name} ({c.professor}) {c.time_summary}")
            else:
                 print(f"      - {unique_candidates[0].name} 외 {len(unique_candidates)-1}개")
        
        # 희망 강의: 각 필터마다 매칭되는 모든 강의를 찾음
        self.desired_course_groups = [
            self._find_all_matching_courses(filter_obj) 
            for filter_obj in config.desired_filters
        ]
        
        # 제외 시간 비트마스크 선계산 (최적화)
        self.excluded_mask = self._calculate_excluded_mask()

        self._print_init_info()

    def _print_init_info(self):
        """초기화 정보 출력"""
        # 필수 강의 정보는 __init__에서 이미 출력함
        
        print(f"\n💡 희망 강의 매칭 결과:")
        for i, group in enumerate(self.desired_course_groups, 1):
            if group:
                print(f"  ○ [{i}] {group[0].name}: {len(group)}개 시간대")
            else:
                print(f"  ⚠️  [{i}] 매칭 실패: {self.config.desired_filters[i-1]}")
        
        print(f"\n🎲 Random Fill 후보군: {len(self.random_fill_candidates)}개 (전학년 대상)")

    def _find_all_matching_courses(self, filter_obj: CourseFilter) -> List[Course]:
        """필터에 매칭되는 모든 강의 찾기"""
        matched = []
        for course in self.all_courses:
            if filter_obj.matches(course):
                matched.append(course)
        return matched
    
    def generate_all_schedules(self, progress_callback: Optional[Callable[[str], None]] = None) -> List[Schedule]:
        """
        Randomized Backtracking + Restart 전략으로 시간표 생성
        
        개선사항:
        - 시간 기반 타임아웃 (AlgoConfig.MAX_TOTAL_TIME_SECONDS)
        - 발견 속도 기반 조기 종료 (최근 N회 성공률 체크)
        - 최대 Restart 횟수 제한
        - 로깅 강화
        """
        print("\n" + "=" * 60)
        print("   시간표 조합 생성 시작 (Randomized Backtracking)")
        print("=" * 60)
        
        logger.info("시간표 생성 시작")
        logger.info(f"설정: 목표={AlgoConfig.TARGET_RESULTS}, 배치={AlgoConfig.BATCH_SIZE}, "
                   f"타임아웃={AlgoConfig.MAX_TOTAL_TIME_SECONDS}초")
        
        # 시작 시각 기록
        start_time = time.time()
        
        # 1. 필수 강의 검증
        if any(len(group) == 0 for group in self.required_course_groups):
            logger.error("일부 필수 강의를 찾을 수 없음")
            print("\n❌ 일부 필수 강의를 찾을 수 없습니다.")
            return []
            
        # [Safety] Reset results
        self.results.clear()
        
        # 2. 필수 강의 조합 생성
        print(f"\n🔄 필수 강의 조합 탐색 중...")
        required_combinations = self._generate_required_combinations(self.required_course_groups)
        
        if not required_combinations:
            logger.error("필수 강의들 간 시간 충돌로 조합 생성 불가")
            # [OOP Fix] 구체적인 에러 메시지 전파
            raise GenerationError(
                "필수 강의들 간 시간 충돌 또는 제외된 시간대와 겹쳐서\n"
                "가능한 조합을 만들 수 없습니다."
            )
        
        # 필수 조합도 휴리스틱 정렬 (총 학점 많은 조합 우선)
        required_combinations.sort(key=lambda sched: -sched.total_credits)
        
        print(f"✅ {len(required_combinations)}개의 필수 강의 조합 발견 (휴리스틱 정렬 완료)")
        logger.info(f"필수 강의 조합: {len(required_combinations)}개 (휴리스틱 적용)")
        
        # 3. 희망 강의 목록 준비 (중복 및 제외 조건 필터링)
        all_required = [course for group in self.required_course_groups for course in group]
        all_desired_raw = [course for group in self.desired_course_groups for course in group]
        
        available_desired = self._filter_available_courses(all_desired_raw, all_required)
        
        # 휴리스틱 정렬 적용 (학점 많은 것 + 시간 슬롯 적은 것 우선)
        available_desired = self._apply_heuristic_sort(available_desired)
        
        print(f"\n📋 탐색 대상:")
        print(f"   ├─ 필수 강의 조합: {len(required_combinations)}개")
        print(f"   └─ 희망 강의(후보): {len(available_desired)}개 (휴리스틱 정렬 완료)")
        
        logger.info(f"탐색 대상: 필수 조합={len(required_combinations)}, 희망 후보={len(available_desired)} (휴리스틱 적용)")
        
        # 4. Randomized Restart Loop with Optimizations
        print(f"\n🔍 Randomized Exploration 시작 (Target: {AlgoConfig.TARGET_RESULTS}, "
              f"Timeout: {AlgoConfig.MAX_TOTAL_TIME_SECONDS}초)...")
        
        # Phase Logic: Pure Mode -> Fill Mode
        allow_fill = False
        consecutive_pure_failures = 0
        
        restart_count = 0
        found_signatures = set()  # 중복 제거용
        
        # 발견 속도 추적 (최근 N회의 발견 개수)
        recent_discoveries = deque(maxlen=AlgoConfig.SATURATION_CHECK_WINDOW)
        
        has_found_pure_ever = False
        
        while len(self.results) < AlgoConfig.TARGET_RESULTS:
            # === Restart 횟수 제한 (타임아웃 대신 자연스러운 임계값 사용) ===
            restart_count += 1
            if restart_count > AlgoConfig.MAX_RESTARTS:
                logger.warning(f"최대 Restart 횟수 초과: {AlgoConfig.MAX_RESTARTS}")
                print(f"\n🛑 최대 Restart 횟수({AlgoConfig.MAX_RESTARTS}) 초과 - 조기 종료")
                break
            
            # 희망 강의 셔플
            random.shuffle(available_desired)
            random.shuffle(required_combinations)
            
            found_this_round = 0  # 이번 라운드에서 찾은 새로운 결과 수
            
            # 이번 라운드 탐색 (Early Pruning 적용)
            for req_schedule in required_combinations:
                cnt = self._run_randomized_dfs(
                    req_schedule, 
                    available_desired, 
                    limit=AlgoConfig.BATCH_SIZE - found_this_round,
                    allow_fill=allow_fill,
                    found_signatures=found_signatures,
                    start_time=start_time
                )
                found_this_round += cnt
                
                if found_this_round >= AlgoConfig.BATCH_SIZE:
                    break
            
            # 발견 기록 추가
            recent_discoveries.append(found_this_round)
            
            # 진행 상황 표시
            if restart_count % AlgoConfig.PROGRESS_REPORT_INTERVAL == 0:
                mode_str = "PURE" if not allow_fill else "FILL"
                
                # Callback 호출 (UI 업데이트)
                if progress_callback:
                    progress_callback(f"시간표 조합 찾는 중... {len(self.results):,}개 발견")
                     
                if sys.stdout:
                    elapsed = time.time() - start_time
                    sys.stdout.write(f"\r  ... Restart #{restart_count} [{mode_str}], Found: {len(self.results)}, Elapsed: {elapsed:.1f}s")
                    sys.stdout.flush()

            # === Phase Logic: Pure -> Fill 전환 ===
            if not allow_fill:
                if found_this_round > 0:
                    has_found_pure_ever = True
                    consecutive_pure_failures = 0 
                else:
                    if not has_found_pure_ever:
                        consecutive_pure_failures += 1
                        if consecutive_pure_failures >= AlgoConfig.MAX_PURE_FAILURES:
                            logger.info(f"Pure 모드에서 {AlgoConfig.MAX_PURE_FAILURES}회 연속 실패 - Fill 모드 전환")
                            print(f"\n💡 [Mode Switch] 순수 시간표 탐색 실패({AlgoConfig.MAX_PURE_FAILURES}회). 무작위 채우기 모드로 전환합니다.")
                            allow_fill = True
                            consecutive_pure_failures = 0
            
            # === 발견 속도 기반 조기 종료 (Saturation Check) ===
            if len(recent_discoveries) >= AlgoConfig.SATURATION_CHECK_WINDOW:
                total_recent_finds = sum(recent_discoveries)
                
                if total_recent_finds < AlgoConfig.SATURATION_THRESHOLD:
                    logger.info(f"포화 감지: 최근 {AlgoConfig.SATURATION_CHECK_WINDOW}회 중 {total_recent_finds}개만 발견")
                    print(f"\n✨ 포화 감지: 최근 {AlgoConfig.SATURATION_CHECK_WINDOW}회 중 {total_recent_finds}개만 발견 - 조기 종료")
                    break
        
        elapsed_total = time.time() - start_time
        print(f"\n\n✨ 총 {len(self.results)}개의 시간표 조합 발견! (Restarts: {restart_count}, 소요: {elapsed_total:.2f}초)")
        print("=" * 60 + "\n")
        
        logger.info(f"생성 완료: {len(self.results)}개, Restarts: {restart_count}, 소요: {elapsed_total:.2f}초")
        
        return self.results

    def _filter_available_courses(self, candidates: List[Course], excluded_courses: List[Course]) -> List[Course]:
        """조건(요일/시간 제외)에 맞는 강의만 필터링"""
        filtered = []
        for course in candidates:
            # 이미 필수에서 쓰인 강의 제외
            if course in excluded_courses:
                continue
                
            is_excluded = False
            # 1. 요일/시간 제외 (비트마스크로 한 번에 처리 가능)
            if self._is_excluded_time(course):
                is_excluded = True
            
            if not is_excluded:
                filtered.append(course)
        return filtered

    def _apply_heuristic_sort(self, courses: List[Course]) -> List[Course]:
        """
        휴리스틱 정렬: 가지치기 효과를 극대화하기 위한 강의 순서 최적화
        
        전략:
        1. 학점이 많은 강의 우선 (큰 것부터 담기 - Bin Packing 휴리스틱)
        2. 시간 슬롯이 적은 강의 우선 (제약이 많은 것부터 - MRV 휴리스틱)
        
        효과:
        - 조기에 큰 학점 채워서 목표 도달 빠름
        - 제약 많은 것 먼저 배치해서 실패 빠르게 판단 (가지치기)
        """
        def sort_key(course: Course):
            # 1순위: 학점 (내림차순) - 음수로 만들어 큰 것부터
            # 2순위: 시간 슬롯 개수 (오름차순) - 적은 것부터
            return (-course.credits, len(course.time_slots))
        
        return sorted(courses, key=sort_key)

    def _run_randomized_dfs(self, base_schedule: Schedule, candidates: List[Course], limit: int, 
                            allow_fill: bool, found_signatures: set, start_time: float) -> int:
        """
        단일 DFS 실행
        allow_fill: True이면 부족 시 채우기 시도, False이면 순수 시간표만 탐색
        found_signatures: 중복 체크용 집합
        start_time: 타임아웃 체크용 시작 시각
        """
        found_pure_count = 0
        filled_buffer: List[Schedule] = []

        def backtrack(current: Schedule, idx: int):
            nonlocal found_pure_count
            if found_pure_count >= limit:
                return

            if current.total_credits > self.config.max_credits:
                return
            
            # === 조기 가지치기 (Early Pruning) ===
            # 현재 학점 + 남은 모든 강의의 최대 학점으로도 min_credits 못 채우면 즉시 중단
            # [Fix] allow_fill 모드일 때는 가지치기 하지 않음 (왜냐하면 Random Fill로 채울 수 있으니까!)
            if not allow_fill and current.total_credits < self.config.min_credits:
                remaining_max_credits = sum(c.credits for c in candidates[idx:])
                if current.total_credits + remaining_max_credits < self.config.min_credits:
                    # 더 이상 탐색해도 목표 학점 도달 불가 → 가지치기
                    return

            extended = False

            for i in range(idx, len(candidates)):
                if found_pure_count >= limit:
                    break
                    
                course = candidates[i]
                
                # 학점 초과시 건너뛰기
                if current.total_credits + course.credits > self.config.max_credits:
                    continue
                # [최적화] 중복 검사 제거: candidates는 이미 _is_excluded_time을 통과한 상태임
                
                if current.add_course(course):
                    extended = True
                    backtrack(current, i + 1)
                    current.remove_course(course)

            if not extended:
                _process_leaf(current)

        def _process_leaf(current: Schedule):
            nonlocal found_pure_count
            
            # 1. 이미 완성된 경우 (Pure Schedule)
            if self.config.min_credits <= current.total_credits <= self.config.max_credits:
                # 중복 체크 (리팩토링: get_content_hash 사용)
                sig = current.get_content_hash()
                if sig in found_signatures:
                    return  # 이미 찾은 조합
                
                found_signatures.add(sig)
                self.results.append(current.copy())
                found_pure_count += 1
                
            # 2. 학점이 모자란 경우 (Filled Schedule) -> allow_fill일 때만 시도
            elif allow_fill and current.total_credits < self.config.min_credits:
                # Buffer가 꽉 찼으면 더 이상 채우기 연산 하지 않음 (최적화)
                if len(filled_buffer) >= limit:
                    return

                final_schedule = self._try_random_fill(current)
                
                # 채운 결과가 조건 만족하면 Buffer에 저장
                if self.config.min_credits <= final_schedule.total_credits <= self.config.max_credits:
                    # Buffer에 추가 (나중에 채택 시 중복 체크)
                    filled_buffer.append(final_schedule)

        # 실행
        backtrack(base_schedule.copy(), 0)
        
        # Pure로 다 못 채웠으면 Filled에서 충당 (단, allow_fill 모드일 때만)
        added_filled_count = 0
        spaces_left = limit - found_pure_count
        
        if allow_fill and spaces_left > 0 and filled_buffer:
            random.shuffle(filled_buffer)
            for s in filled_buffer:
                if added_filled_count >= spaces_left:
                    break
                
                # 리팩토링: get_content_hash 사용
                sig = s.get_content_hash()
                if sig not in found_signatures:
                    found_signatures.add(sig)
                    self.results.append(s)
                    added_filled_count += 1
                
        return found_pure_count + added_filled_count

    def _try_random_fill(self, schedule: Schedule) -> Schedule:
        """
        빈 공강 시간에 '전학년' 대상 강의를 무작위로 채워 넣음
        """
        # 스케줄 복사 (원본 보존)
        new_schedule = schedule.copy()
        
        # 이미 꽉 찼으면 반환
        if new_schedule.total_credits >= self.config.max_credits:
            return new_schedule
            
        # 후보군 셔플
        random.shuffle(self.random_fill_candidates)
        
        filled_any = False

        for course in self.random_fill_candidates:
            # 학점 초과 체크
            if new_schedule.total_credits + course.credits > self.config.max_credits:
                # logger.debug(f"Skip {course.name}: Credit Overflow ({new_schedule.total_credits} + {course.credits} > {self.config.max_credits})")
                continue
            
            # 요일/시간 제외 체크 (비트마스크 최적화)
            if self._is_excluded_time(course):
                # logger.debug(f"Skip {course.name}: Excluded Time")
                continue

            # 충돌 체크 및 추가
            # add_course 내부에서 충돌/중복 체크 함
            if new_schedule.add_course(course):
                filled_any = True
            # else:
                # logger.debug(f"Skip {course.name}: Conflict or Duplicate")
            
            # 꽉 찼으면 중단
            if new_schedule.total_credits >= self.config.max_credits:
                break
        
        if filled_any:
            new_schedule.has_random_filled = True
            # logger.info(f"Random Fill Result: {new_schedule.total_credits} credits (Added {new_schedule.total_credits - schedule.total_credits})")
                
        return new_schedule

    def _generate_required_combinations(self, course_groups: List[List[Course]]) -> List[Schedule]:
        """필수 강의 그룹 조합 생성 (기존 유지)"""
        filtered_groups = []
        for group in course_groups:
            valid_courses = [c for c in group if not self._is_excluded_time(c)]
            if valid_courses:
                filtered_groups.append(valid_courses)
            else:
                filtered_groups.append(group)
        
        combinations = []
        def backtrack(index: int, current_schedule: Schedule):
            if index == len(filtered_groups):
                combinations.append(current_schedule.copy())
                return
            for course in filtered_groups[index]:
                if current_schedule.add_course(course):
                    backtrack(index + 1, current_schedule)
                    current_schedule.remove_course(course)
        
        backtrack(0, Schedule())
        return combinations
    
    # [최적화] 비트마스크 선계산
    def _calculate_excluded_mask(self) -> int:
        mask = 0
        # 1. 특정 시간대 제외
        if self.config.excluded_time_slots:
            from ..core.models import time_str_to_index
            for (day, start, end) in self.config.excluded_time_slots:
                start_idx = time_str_to_index(day, start)
                end_idx = time_str_to_index(day, end)
                for i in range(start_idx, end_idx):
                    mask |= (1 << i)
                    
        # 2. 요일 전체 제외
        if self.config.excluded_days:
            # 하루 = 288 slots (5분 단위)
            from ..core.models import DAYS_MAP
            for day in self.config.excluded_days:
                day_idx = DAYS_MAP.get(day, 0)
                start_idx = day_idx * 288
                end_idx = (day_idx + 1) * 288
                for i in range(start_idx, end_idx):
                    mask |= (1 << i)
                    
        return mask

    def _is_excluded_time(self, course: Course) -> bool:
        """제외 시간 체크 (비트마스크 최적화)"""
        # 비트마스크 연산 (O(1))
        return (course.time_mask & self.excluded_mask) > 0

    def _time_overlaps(self, start1: str, end1: str, start2: str, end2: str) -> bool:
        def to_min(t): h, m = map(int, t.split(':')); return h*60 + m
        return to_min(start1) < to_min(end2) and to_min(start2) < to_min(end1)
