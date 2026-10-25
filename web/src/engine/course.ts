import type { Course, CourseData, CourseFilter, Day, TimeSlot } from './types'

/** 요일 → 인덱스 (Python models.DAYS_MAP) */
export const DAY_INDEX: Record<Day, number> = { 월: 0, 화: 1, 수: 2, 목: 3, 금: 4, 토: 5, 일: 6 }

/** 하루 = 24시간 × 12슬롯(5분 단위) */
export const SLOTS_PER_DAY = 288

export function toMinutes(time: string): number {
  const [h, m] = time.split(':').map(Number)
  return h * 60 + m
}

/** 요일과 시간을 5분 단위 비트 인덱스로 변환 */
export function timeToIndex(day: Day, time: string): number {
  return DAY_INDEX[day] * SLOTS_PER_DAY + Math.floor(toMinutes(time) / 5)
}

/** [start, end) 구간을 비트마스크로 변환 */
export function rangeMask(startIdx: number, endIdx: number): bigint {
  if (endIdx <= startIdx) return 0n
  return ((1n << BigInt(endIdx - startIdx)) - 1n) << BigInt(startIdx)
}

/** 06시 전에 시작하는 시간(00:00~03:00 등)은 온라인 강의의 자리표시 (Python models.is_placeholder_slot) */
export const isPlaceholderSlot = (s: { start: string }) => toMinutes(s.start) < 6 * 60

/** 강의 시간 비트마스크 — 자리표시 시간은 충돌·제외 시간 검사에서 무시 */
export function slotsMask(slots: { day: Day; start: string; end: string }[]): bigint {
  let mask = 0n
  for (const s of slots) {
    if (isPlaceholderSlot(s)) continue
    mask |= rangeMask(timeToIndex(s.day, s.start), timeToIndex(s.day, s.end))
  }
  return mask
}

export function formatSlot(slot: Pick<TimeSlot, 'day' | 'start' | 'end'>): string {
  return `${slot.day} ${slot.start}~${slot.end}`
}

export function timeSummary(course: Pick<CourseData, 'slots'>): string {
  return course.slots.length ? course.slots.map(formatSlot).join(', ') : '시간 정보 없음'
}

export function toCourse(data: CourseData): Course {
  return {
    ...data,
    mask: slotsMask(data.slots),
    signature: `${data.name}|${data.professor}|${timeSummary(data)}`,
  }
}

/** Python CourseFilter.matches 와 동일한 규칙 */
export function matchesFilter(filter: CourseFilter, course: CourseData): boolean {
  if (filter.courseId) return filter.courseId === course.id
  if (filter.name) {
    const keywords = filter.name.split(/\s+/).filter(Boolean)
    if (!keywords.every((k) => course.name.includes(k))) return false
  }
  if (filter.professor) {
    const keywords = filter.professor.split(/\s+/).filter(Boolean)
    if (!keywords.every((k) => course.professor.includes(k))) return false
  }
  return true
}

export function describeFilter(filter: CourseFilter): string {
  const parts: string[] = []
  if (filter.courseId) parts.push(`#${filter.courseId}`)
  if (filter.name) parts.push(filter.name)
  if (filter.professor) parts.push(filter.professor)
  return parts.join(' · ') || '빈 필터'
}

export function sameFilter(a: CourseFilter, b: CourseFilter): boolean {
  return (a.courseId || '') === (b.courseId || '') && (a.name || '') === (b.name || '') && (a.professor || '') === (b.professor || '')
}
