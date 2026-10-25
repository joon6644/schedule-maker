/**
 * 시간표 보기 상태 (보고 있는 시간표 + 고정한 강의)
 * 결과 화면 밖(App)에 두어서, 재계산하거나 모바일에서 탭을 옮겨도 유지됨
 */
import { describeFilter, sameFilter, timeSummary } from '../engine/course'
import type { CourseData, CourseFilter, ScheduleConfig, ScheduleResult } from '../engine/types'

/** 강의명 → 고정할 시간(timeSummary) / ANY(시간 무관, 포함만) */
export type Pins = Map<string, string>
export const ANY = 'ANY'

export interface ViewerState {
  pins: Pins
  /** 보고 있는 시간표 (강의 id 조합). null 이면 첫 시간표 */
  key: string | null
}

export const EMPTY_VIEWER: ViewerState = { pins: new Map(), key: null }

export const scheduleKey = (s: ScheduleResult) => [...s.courseIds].sort().join(',')

export function matchesPins(s: ScheduleResult, pins: Pins, byId: Map<string, CourseData>, skip?: string) {
  for (const [name, key] of pins) {
    if (name === skip) continue
    const c = s.courseIds.map((id) => byId.get(id)).find((x) => x?.name === name)
    if (!c || (key !== ANY && timeSummary(c) !== key)) return false
  }
  return true
}

export function filterByPins(schedules: ScheduleResult[], pins: Pins, byId: Map<string, CourseData>) {
  return pins.size ? schedules.filter((s) => matchesPins(s, pins, byId)) : schedules
}

/**
 * 새 결과에 보기 상태를 맞춤
 * - 고정은 새 결과에서도 가능한 것만 남김 (앞에서부터 하나씩 시도)
 * - 보던 시간표가 남아 있으면 그대로, 없으면 첫 시간표
 */
export function reconcileViewer(viewer: ViewerState, schedules: ScheduleResult[], byId: Map<string, CourseData>) {
  let pins: Pins = new Map()
  const droppedPins: string[] = []
  for (const [name, key] of viewer.pins) {
    const trial = new Map(pins).set(name, key)
    if (schedules.some((s) => matchesPins(s, trial, byId))) pins = trial
    else droppedPins.push(name)
  }
  const filtered = filterByPins(schedules, pins, byId)
  const kept = viewer.key !== null && filtered.some((s) => scheduleKey(s) === viewer.key)
  return {
    viewer: { pins, key: kept ? viewer.key : filtered[0] ? scheduleKey(filtered[0]) : null },
    /** 보던 시간표가 새 조건에 맞지 않아 바뀌었는지 */
    lostView: viewer.key !== null && !kept,
    droppedPins,
  }
}

const filterLabel = (f: CourseFilter) => f.name || describeFilter(f)

/** 두 설정의 차이를 한 줄로 설명 (변경 알림에 사용) */
export function describeChange(prev: ScheduleConfig, next: ScheduleConfig): string {
  const added = (list: 'required' | 'desired') => next[list].filter((f) => !prev[list].some((p) => sameFilter(p, f)))
  const removed = (list: 'required' | 'desired') => prev[list].filter((f) => !next[list].some((n) => sameFilter(n, f)))
  const lists = [['required', '필수'], ['desired', '희망']] as const

  for (const [list, label] of lists) {
    const other = list === 'required' ? 'desired' : 'required'
    const a = added(list)
    if (a.length) {
      const moved = a.find((f) => prev[other].some((p) => sameFilter(p, f)))
      if (moved) return `'${filterLabel(moved)}' ${list === 'required' ? '필수로' : '희망으로'} 옮김`
      return a.length === 1 ? `${label} '${filterLabel(a[0])}' 담음` : `${label} 강의 ${a.length}개 담음`
    }
  }
  for (const [list, label] of lists) {
    const r = removed(list)
    if (r.length) return r.length === 1 ? `${label} '${filterLabel(r[0])}' 뺌` : `${label} 강의 ${r.length}개 뺌`
  }
  if (prev.minCredits !== next.minCredits || prev.maxCredits !== next.maxCredits) {
    return `학점 범위 ${next.minCredits}–${next.maxCredits}`
  }
  const dayOn = next.excludedDays.find((d) => !prev.excludedDays.includes(d))
  if (dayOn) return `${dayOn}요일 공강`
  const dayOff = prev.excludedDays.find((d) => !next.excludedDays.includes(d))
  if (dayOff) return `${dayOff}요일 공강 해제`
  const key = (t: { day: string; start: string; end: string }) => `${t.day}${t.start}${t.end}`
  const prevTimes = new Set(prev.excludedTimes.map(key))
  const nextTimes = new Set(next.excludedTimes.map(key))
  if (next.excludedTimes.some((t) => !prevTimes.has(key(t)))) return '피하고 싶은 시간 추가'
  if (prev.excludedTimes.some((t) => !nextTimes.has(key(t)))) return '피하고 싶은 시간 해제'
  return '설정 변경'
}
