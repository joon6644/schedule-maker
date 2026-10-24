"""
시간표 조합 생성 스케줄러 (Exhaustive Backtracking Engine)
DFS 백트래킹 한 번으로 조건을 만족하는 모든 시간표 조합을 생성함.

최적화 적용:
- 비트마스크 충돌 검사
- 남은 학점 합(suffix sum) 기반 가지치기
- 중복 제거 (content hash)
- 순수 시간표가 없을 때만 무작위 채우기 (Fill 모드)
"""
import random
import time
import logging
from collections import deque
from typing import List, Optional, Callable
from ..core.models import Course, Schedule, time_str_to_index, DAYS_MAP
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
        전수 탐색 DFS로 시간표 생성

        - 순수 시간표: 조건을 만족하는 모든 조합을 한 번의 DFS로 수집 (결정적)
        - 순수 시간표가 없으면: 학점 미달 시간표에 '전학년' 강의를 무작위로 채움 (Fill 모드)
        - 제한 시간 (AlgoConfig.MAX_TOTAL_TIME_SECONDS) 초과 시 찾은 결과까지만 반환
        """
        print("\n" + "=" * 60)
        print("   시간표 조합 생성 시작 (Exhaustive Backtracking)")
        print("=" * 60)

        logger.info("시간표 생성 시작")
        logger.info(f"설정: 목표={AlgoConfig.TARGET_RESULTS}, 타임아웃={AlgoConfig.MAX_TOTAL_TIME_SECONDS}초")
        
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
        
        # 4. 순수 시간표 전수 탐색 (단일 DFS)
        # 이전 방식(셔플 + 재시작 반복)도 결국 '가능한 모든 조합'에 수렴했지만,
        # 결과가 다 나온 뒤에도 재시작마다 같은 트리를 처음부터 다시 탐색하느라 대부분의 시간을 썼음.
        # 한 번의 DFS로 모든 조합을 정확히 한 번씩 방문해 같은 결과를 얻는다.
        print(f"\n🔍 전수 탐색 시작 (최대 {BusinessConstants.MAX_SCHEDULE_RESULTS:,}개, "
              f"제한 시간: {AlgoConfig.MAX_TOTAL_TIME_SECONDS}초)...")

        deadline = start_time + AlgoConfig.MAX_TOTAL_TIME_SECONDS
        found_signatures = set()  # 중복 제거용 (content hash)

        results = self._enumerate_pure_schedules(
            required_combinations, available_desired, found_signatures, deadline, progress_callback
        )

        # 5. 순수 시간표가 하나도 없으면 무작위 채우기 모드
        if not results:
            logger.info("순수 시간표 없음 - Fill 모드 전환")
            print("\n💡 [Mode Switch] 조건을 만족하는 순수 시간표가 없습니다. 무작위 채우기 모드로 전환합니다.")
            partials = self._collect_partial_schedules(required_combinations, available_desired, deadline)
            results = self._fill_partial_schedules(partials, found_signatures, progress_callback)

        # 목표 개수를 넘으면 무작위 표본 추출, 아니면 순서만 섞어서 다양하게 보여줌
        if len(results) > AlgoConfig.TARGET_RESULTS:
            results = random.sample(results, AlgoConfig.TARGET_RESULTS)
        else:
            random.shuffle(results)
        self.results = results

        elapsed_total = time.time() - start_time
        print(f"\n✨ 총 {len(self.results)}개의 시간표 조합 발견! (소요: {elapsed_total:.2f}초)")
        print("=" * 60 + "\n")

        logger.info(f"생성 완료: {len(self.results)}개, 소요: {elapsed_total:.2f}초")

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

    def _enumerate_pure_schedules(self, required_combinations: List[Schedule], candidates: List[Course],
                                  found_signatures: set, deadline: float,
                                  progress_callback: Optional[Callable[[str], None]] = None) -> List[Schedule]:
        """
        필수 조합 × 희망 강의 부분집합을 한 번씩 방문하며 학점 조건을 만족하는 시간표를 모두 수집

        가지치기:
        - 최대 학점 초과 강의는 건너뜀
        - 현재 학점 + 남은 후보 학점 합(suffix sum, O(1) 조회)으로도 최소 학점 미달이면 중단
        """
        min_credits = self.config.min_credits
        max_credits = self.config.max_credits
        cap = BusinessConstants.MAX_SCHEDULE_RESULTS
        n = len(candidates)

        # suffix_credits[i] = candidates[i:]의 학점 합 (i가 커질수록 감소)
        suffix_credits = [0] * (n + 1)
        for i in range(n - 1, -1, -1):
            suffix_credits[i] = suffix_credits[i + 1] + candidates[i].credits

        found: List[Schedule] = []
        node_count = 0
        stopped = False

        def backtrack(current: Schedule, idx: int):
            nonlocal node_count, stopped
            node_count += 1
            # 1024 노드마다 제한 시간 확인
            if node_count & 0x3FF == 0 and time.time() > deadline:
                logger.warning("제한 시간 초과 - 탐색 조기 종료")
                print(f"\n⏱ 제한 시간({AlgoConfig.MAX_TOTAL_TIME_SECONDS}초) 초과 - 지금까지 찾은 결과만 사용합니다.")
                stopped = True
            if stopped:
                return

            credits = current.total_credits
            if credits >= min_credits:
                sig = current.get_content_hash()
                if sig not in found_signatures:
                    found_signatures.add(sig)
                    found.append(current.copy())
                    if len(found) >= cap:
                        stopped = True
                        return
                    if progress_callback and len(found) % 1000 == 0:
                        progress_callback(f"시간표 조합 찾는 중... {len(found):,}개 발견")

            for i in range(idx, n):
                # 남은 후보를 전부 담아도 최소 학점 미달 → 이후 인덱스도 모두 불가능
                if credits + suffix_credits[i] < min_credits:
                    break
                course = candidates[i]
                if credits + course.credits > max_credits:
                    continue
                if current.add_course(course):
                    backtrack(current, i + 1)
                    current.remove_course(course)
                    if stopped:
                        return

        for req_schedule in required_combinations:
            backtrack(req_schedule.copy(), 0)
            if stopped:
                break

        logger.info(f"전수 탐색: 방문 노드 {node_count:,}개, 결과 {len(found):,}개")
        return found

    def _collect_partial_schedules(self, required_combinations: List[Schedule], candidates: List[Course],
                                   deadline: float) -> List[Schedule]:
        """
        Fill 모드용: 희망 강의를 더 이상 넣을 수 없는(극대) 학점 미달 시간표를 수집
        """
        max_credits = self.config.max_credits
        cap = BusinessConstants.MAX_SCHEDULE_RESULTS
        n = len(candidates)
        partials: List[Schedule] = []
        seen = set()
        stopped = False

        def fits(current: Schedule, course: Course) -> bool:
            return (current.total_credits + course.credits <= max_credits
                    and course.name not in current.course_names
                    and (current.total_time_mask & course.time_mask) == 0)

        def backtrack(current: Schedule, idx: int):
            nonlocal stopped
            if stopped or time.time() > deadline:
                stopped = True
                return

            for i in range(idx, n):
                course = candidates[i]
                if fits(current, course):
                    current.add_course(course)
                    backtrack(current, i + 1)
                    current.remove_course(course)
                    if stopped:
                        return

            # 앞에서 건너뛴 후보까지 포함해 어떤 강의도 더 넣을 수 없을 때만 수집 (중복 방문 없음)
            if current.total_credits < self.config.min_credits and not any(fits(current, c) for c in candidates):
                sig = current.get_content_hash()
                if sig not in seen:
                    seen.add(sig)
                    partials.append(current.copy())
                    if len(partials) >= cap:
                        stopped = True

        for req_schedule in required_combinations:
            backtrack(req_schedule.copy(), 0)
            if stopped:
                break

        return partials

    def _fill_partial_schedules(self, partials: List[Schedule], found_signatures: set,
                                progress_callback: Optional[Callable[[str], None]] = None) -> List[Schedule]:
        """
        학점 미달 시간표에 '전학년' 강의를 무작위로 채워 넣어 결과 생성
        (무작위성이 있으므로 새 결과가 거의 나오지 않을 때까지 라운드를 반복)
        """
        results: List[Schedule] = []
        if not partials:
            return results

        recent_discoveries = deque(maxlen=AlgoConfig.SATURATION_CHECK_WINDOW)

        for round_no in range(1, AlgoConfig.MAX_RESTARTS + 1):
            random.shuffle(partials)
            added = 0
            for base in partials:
                filled = self._try_random_fill(base)
                if not (self.config.min_credits <= filled.total_credits <= self.config.max_credits):
                    continue
                sig = filled.get_content_hash()
                if sig in found_signatures:
                    continue
                found_signatures.add(sig)
                results.append(filled)
                added += 1
                if len(results) >= AlgoConfig.TARGET_RESULTS:
                    return results

            if progress_callback and round_no % 10 == 0:
                progress_callback(f"시간표 조합 찾는 중... {len(results):,}개 발견")

            # 발견 속도 기반 조기 종료 (Saturation Check)
            recent_discoveries.append(added)
            if (len(recent_discoveries) == recent_discoveries.maxlen
                    and sum(recent_discoveries) < AlgoConfig.SATURATION_THRESHOLD):
                logger.info(f"포화 감지: 최근 {AlgoConfig.SATURATION_CHECK_WINDOW}라운드 중 "
                            f"{sum(recent_discoveries)}개만 발견")
                break

        return results

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
                continue

            # 요일/시간 제외 체크 (비트마스크 최적화)
            if self._is_excluded_time(course):
                continue

            # 충돌 체크 및 추가
            # add_course 내부에서 충돌/중복 체크 함
            if new_schedule.add_course(course):
                filled_any = True
            
            # 꽉 찼으면 중단
            if new_schedule.total_credits >= self.config.max_credits:
                break
        
        if filled_any:
            new_schedule.has_random_filled = True
                
        return new_schedule

    def _generate_required_combinations(self, course_groups: List[List[Course]]) -> List[Schedule]:
        """필수 강의 그룹 조합 생성 (기존 유지)"""
        filtered_groups = []
        for group in course_groups:
            valid_courses = [c for c in group if not self._is_excluded_time(c)]
            filtered_groups.append(valid_courses)
        
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
            for (day, start, end) in self.config.excluded_time_slots:
                start_idx = time_str_to_index(day, start)
                end_idx = time_str_to_index(day, end)
                for i in range(start_idx, end_idx):
                    mask |= (1 << i)
                    
        # 2. 요일 전체 제외
        if self.config.excluded_days:
            # 하루 = 288 slots (5분 단위)
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
