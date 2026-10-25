/**
 * 시간표 조합 생성기 (Exhaustive Backtracking)
 * Python schedule_maker/services/scheduler.py 의 TypeScript 이식판.
 *
 * - 순수 시간표: 한 번의 DFS로 조건을 만족하는 모든 조합을 수집 (결정적)
 * - 순수 시간표가 없으면: 학점 미달 시간표에 '전학년' 강의를 무작위로 채움 (Fill 모드)
 */
import { matchesFilter, rangeMask, SLOTS_PER_DAY, DAY_INDEX, timeToIndex } from './course'
import {
  GenerationError,
  type Course,
  type CourseFilter,
  type GenerationOutput,
  type ScheduleConfig,
  type ScheduleResult, MAX_RESULTS } from './types'

export const ALGO = {
  /** 반환할 최대 시간표 개수 (초과 시 무작위 표본) */
  TARGET_RESULTS: MAX_RESULTS,
  /** 전수 탐색에서 수집할 최대 개수 */
  MAX_ENUMERATED: 100000,
  /** 전수 탐색 제한 시간 */
  MAX_TOTAL_MS: 10000,
  /** Fill 모드 최대 라운드 수 */
  MAX_FILL_ROUNDS: 1000,
  /** Fill 모드 발견율 체크 윈도우 / 임계값 */
  SATURATION_WINDOW: 100,
  SATURATION_THRESHOLD: 3,
}

/** 졸업 요건 등으로 사용자가 직접 골라야 해서 무작위 채우기에서 제외하는 과목 */
export const EXCLUDED_RANDOM_FILL = new Set([
  '영어1', '영어2', '영어3', '영어4',
  '영어회화1', '영어회화2', '영어회화3', '영어회화4',
  '기초영어',
])

export type Rng = () => number

/** 백트래킹용 가변 시간표 */
class Schedule {
  courses: Course[] = []
  names = new Set<string>()
  mask = 0n
  credits = 0
  randomFilled = false

  fits(course: Course, maxCredits: number): boolean {
    return (
      this.credits + course.credits <= maxCredits &&
      !this.names.has(course.name) &&
      (this.mask & course.mask) === 0n
    )
  }

  /** 같은 이름 중복·시간 충돌이 없으면 추가 */
  add(course: Course): boolean {
    if (this.names.has(course.name) || (this.mask & course.mask) !== 0n) return false
    this.courses.push(course)
    this.names.add(course.name)
    this.mask |= course.mask
    this.credits += course.credits
    return true
  }

  /** 마지막에 추가한 강의 제거 (백트래킹 전용, O(1)) */
  pop(): void {
    const course = this.courses.pop()!
    this.names.delete(course.name)
    this.mask &= ~course.mask
    this.credits -= course.credits
  }

  copy(): Schedule {
    const s = new Schedule()
    s.courses = this.courses.slice()
    s.names = new Set(this.names)
    s.mask = this.mask
    s.credits = this.credits
    s.randomFilled = this.randomFilled
    return s
  }

  /** 강의명·교수·시간 기반 서명 (분반 번호만 다른 동일 수업은 같은 시간표로 취급) */
  contentHash(): string {
    return this.courses.map((c) => c.signature).sort().join('\n')
  }

  toResult(): ScheduleResult {
    return { courseIds: this.courses.map((c) => c.id), totalCredits: this.credits, randomFilled: this.randomFilled }
  }
}

function shuffle<T>(items: T[], rng: Rng): T[] {
  for (let i = items.length - 1; i > 0; i--) {
    const j = Math.floor(rng() * (i + 1))
    ;[items[i], items[j]] = [items[j], items[i]]
  }
  return items
}

/** 강의 조합마다 고정된 값 (FNV-1a) — 결과 순서를 섞되, 재계산해도 같은 시간표끼리의 순서가 유지되도록 */
function scheduleHash(s: Schedule): number {
  let h = 0x811c9dc5
  for (const ch of s.courses.map((c) => c.id).sort().join(',')) {
    h ^= ch.charCodeAt(0)
    h = Math.imul(h, 0x01000193)
  }
  return h >>> 0
}

export interface GenerateOptions {
  rng?: Rng
  now?: () => number
  onProgress?: (found: number) => void
}

export function generateSchedules(
  allCourses: Course[],
  config: ScheduleConfig,
  { rng = Math.random, now = () => performance.now(), onProgress }: GenerateOptions = {},
): GenerationOutput {
  const startedAt = now()
  const deadline = startedAt + ALGO.MAX_TOTAL_MS
  const { minCredits, maxCredits } = config

  const findMatching = (filter: CourseFilter) => allCourses.filter((c) => matchesFilter(filter, c))

  // 제외 시간 비트마스크 (요일 전체 + 특정 시간대)
  let excludedMask = 0n
  for (const t of config.excludedTimes) excludedMask |= rangeMask(timeToIndex(t.day, t.start), timeToIndex(t.day, t.end))
  for (const day of config.excludedDays) {
    const start = DAY_INDEX[day] * SLOTS_PER_DAY
    excludedMask |= rangeMask(start, start + SLOTS_PER_DAY)
  }
  const isExcluded = (c: Course) => (c.mask & excludedMask) !== 0n

  // 1. 필수 강의: 필터 하나당 그룹 하나 (그룹 내에서 택1)
  const requiredGroups = config.required.map((filter) => {
    const matched = [...new Map(findMatching(filter).map((c) => [c.id, c])).values()]
    if (matched.length === 0) {
      const label = filter.name || filter.professor || filter.courseId || '알 수 없는 필터'
      throw new GenerationError(`필수 강의를 찾을 수 없습니다: ${label}`)
    }
    return matched
  })
  const desiredGroups = config.desired.map(findMatching)

  // 2. 필수 강의 조합 (제외 시간과 겹치는 분반은 미리 제거)
  const filteredGroups = requiredGroups.map((g) => g.filter((c) => !isExcluded(c)))
  const requiredCombinations: Schedule[] = []
  const combine = (index: number, current: Schedule) => {
    if (index === filteredGroups.length) {
      requiredCombinations.push(current.copy())
      return
    }
    for (const course of filteredGroups[index]) {
      if (current.add(course)) {
        combine(index + 1, current)
        current.pop()
      }
    }
  }
  combine(0, new Schedule())

  if (requiredCombinations.length === 0) {
    throw new GenerationError('필수 강의들 간 시간 충돌 또는 제외된 시간대와 겹쳐서\n가능한 조합을 만들 수 없습니다.')
  }
  requiredCombinations.sort((a, b) => b.credits - a.credits)

  // 3. 희망 강의 후보 (필수에 쓰인 강의·제외 시간 제거 후 학점 많은 순 → 시간 슬롯 적은 순)
  const requiredIds = new Set(requiredGroups.flat().map((c) => c.id))
  const candidates = desiredGroups
    .flat()
    .filter((c) => !requiredIds.has(c.id) && !isExcluded(c))
    .sort((a, b) => b.credits - a.credits || a.slots.length - b.slots.length)

  const seen = new Set<string>()
  let timedOut = false

  // 4. 순수 시간표 전수 탐색
  const n = candidates.length
  const suffixCredits = new Array<number>(n + 1).fill(0)
  for (let i = n - 1; i >= 0; i--) suffixCredits[i] = suffixCredits[i + 1] + candidates[i].credits

  const pure: Schedule[] = []
  let nodes = 0
  let stopped = false

  const enumerate = (current: Schedule, idx: number) => {
    nodes++
    if ((nodes & 0x3ff) === 0 && now() > deadline) {
      timedOut = true
      stopped = true
    }
    if (stopped) return

    const credits = current.credits
    if (credits >= minCredits) {
      const sig = current.contentHash()
      if (!seen.has(sig)) {
        seen.add(sig)
        pure.push(current.copy())
        if (pure.length >= ALGO.MAX_ENUMERATED) {
          stopped = true
          return
        }
        if (onProgress && pure.length % 1000 === 0) onProgress(pure.length)
      }
    }

    for (let i = idx; i < n; i++) {
      // 남은 후보를 전부 담아도 최소 학점 미달 → 이후 인덱스도 모두 불가능
      if (credits + suffixCredits[i] < minCredits) break
      const course = candidates[i]
      if (credits + course.credits > maxCredits) continue
      if (current.add(course)) {
        enumerate(current, i + 1)
        current.pop()
        if (stopped) return
      }
    }
  }

  for (const req of requiredCombinations) {
    if (req.credits > maxCredits) continue
    enumerate(req.copy(), 0)
    if (stopped) break
  }

  let results = pure

  // 5. 순수 시간표가 없으면 무작위 채우기 모드
  if (results.length === 0) {
    const fillCandidates = allCourses.filter(
      (c) => (c.grade.includes('전학년') || c.category.includes('전학년')) && !EXCLUDED_RANDOM_FILL.has(c.name),
    )
    const partials = collectPartials(requiredCombinations, candidates, config, deadline, now)
    results = fillPartials(partials, fillCandidates, config, isExcluded, seen, rng)
  }

  // 다양하게 보이도록 섞되 결정적으로: 조건을 바꿔도 남아 있는 시간표들의 상대 순서는 그대로
  const final = results
    .map((s) => [scheduleHash(s), s] as const)
    .sort((a, b) => a[0] - b[0])
    .slice(0, ALGO.TARGET_RESULTS)
    .map(([, s]) => s)

  return {
    schedules: final.map((s) => s.toResult()),
    requiredNames: [...new Set(requiredGroups.flat().map((c) => c.name))],
    desiredNames: [...new Set(desiredGroups.flat().map((c) => c.name))],
    elapsedMs: now() - startedAt,
    timedOut,
  }
}

/** Fill 모드용: 희망 강의를 더 이상 넣을 수 없는(극대) 학점 미달 시간표 수집 */
function collectPartials(
  requiredCombinations: Schedule[],
  candidates: Course[],
  config: ScheduleConfig,
  deadline: number,
  now: () => number,
): Schedule[] {
  const { minCredits, maxCredits } = config
  const partials: Schedule[] = []
  const seen = new Set<string>()
  let stopped = false

  const walk = (current: Schedule, idx: number) => {
    if (stopped || now() > deadline) {
      stopped = true
      return
    }
    for (let i = idx; i < candidates.length; i++) {
      const course = candidates[i]
      if (current.fits(course, maxCredits)) {
        current.add(course)
        walk(current, i + 1)
        current.pop()
        if (stopped) return
      }
    }
    // 앞에서 건너뛴 후보까지 포함해 어떤 강의도 더 넣을 수 없을 때만 수집
    if (current.credits < minCredits && !candidates.some((c) => current.fits(c, maxCredits))) {
      const sig = current.contentHash()
      if (!seen.has(sig)) {
        seen.add(sig)
        partials.push(current.copy())
        if (partials.length >= ALGO.MAX_ENUMERATED) stopped = true
      }
    }
  }

  for (const req of requiredCombinations) {
    if (req.credits > maxCredits) continue
    walk(req.copy(), 0)
    if (stopped) break
  }
  return partials
}

/** 학점 미달 시간표에 '전학년' 강의를 무작위로 채워 넣음 */
function fillPartials(
  partials: Schedule[],
  fillCandidates: Course[],
  config: ScheduleConfig,
  isExcluded: (c: Course) => boolean,
  seen: Set<string>,
  rng: Rng,
): Schedule[] {
  const { minCredits, maxCredits } = config
  const results: Schedule[] = []
  if (partials.length === 0) return results

  const pool = fillCandidates.filter((c) => !isExcluded(c))
  const tryFill = (base: Schedule): Schedule => {
    const s = base.copy()
    if (s.credits >= maxCredits) return s
    let filledAny = false
    for (const course of shuffle(pool, rng)) {
      if (s.credits + course.credits > maxCredits) continue
      if (s.add(course)) filledAny = true
      if (s.credits >= maxCredits) break
    }
    if (filledAny) s.randomFilled = true
    return s
  }

  const recent: number[] = []
  for (let round = 0; round < ALGO.MAX_FILL_ROUNDS; round++) {
    shuffle(partials, rng)
    let added = 0
    for (const base of partials) {
      const filled = tryFill(base)
      if (filled.credits < minCredits || filled.credits > maxCredits) continue
      const sig = filled.contentHash()
      if (seen.has(sig)) continue
      seen.add(sig)
      results.push(filled)
      added++
      if (results.length >= ALGO.TARGET_RESULTS) return results
    }
    // 발견 속도 기반 조기 종료 (Saturation Check)
    recent.push(added)
    if (recent.length > ALGO.SATURATION_WINDOW) recent.shift()
    if (recent.length === ALGO.SATURATION_WINDOW && recent.reduce((a, b) => a + b, 0) < ALGO.SATURATION_THRESHOLD) break
  }
  return results
}
