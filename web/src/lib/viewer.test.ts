import { describe, expect, it } from 'vitest'
import { DEFAULT_CONFIG } from '../engine/config'
import type { CourseData, ScheduleConfig, ScheduleResult } from '../engine/types'
import { ANY, describeChange, reconcileViewer, scheduleKey } from './viewer'

const course = (id: string, name: string, day: '월' | '화', start: string): CourseData => ({
  id, name, credits: 3, professor: '', category: '', grade: '', slots: [{ day, start, end: '10:00', room: '' }],
})
const A1 = course('1', 'A', '월', '09:00')
const A2 = course('2', 'A', '화', '09:00')
const B1 = course('3', 'B', '월', '09:30')
const byId = new Map([A1, A2, B1].map((c) => [c.id, c]))
const sched = (...ids: string[]): ScheduleResult => ({ courseIds: ids, totalCredits: ids.length * 3, randomFilled: false })

describe('reconcileViewer', () => {
  it('보던 시간표가 새 결과에 있으면 유지', () => {
    const viewer = { pins: new Map(), key: scheduleKey(sched('2', '3')) }
    const r = reconcileViewer(viewer, [sched('1'), sched('3', '2')], byId)
    expect(r.viewer.key).toBe(viewer.key)
    expect(r.lostView).toBe(false)
  })

  it('보던 시간표가 없어지면 첫 시간표로 바꾸고 알림', () => {
    const r = reconcileViewer({ pins: new Map(), key: scheduleKey(sched('2', '3')) }, [sched('1'), sched('3')], byId)
    expect(r.viewer.key).toBe(scheduleKey(sched('1')))
    expect(r.lostView).toBe(true)
  })

  it('불가능해진 고정만 풀고 나머지는 유지', () => {
    const pins = new Map([['A', '화 09:00~10:00'], ['B', ANY]])
    const r = reconcileViewer({ pins, key: null }, [sched('1', '3'), sched('2')], byId)
    expect([...r.viewer.pins.keys()]).toEqual(['A'])
    expect(r.droppedPins).toEqual(['B'])
    expect(r.viewer.key).toBe(scheduleKey(sched('2')))
  })
})

describe('describeChange', () => {
  const base: ScheduleConfig = { ...DEFAULT_CONFIG, desired: [{ name: '경영과학' }] }
  it.each([
    [{ desired: [{ name: '경영과학' }, { name: '재무관리' }] }, "희망 '재무관리' 담음"],
    [{ desired: [] }, "희망 '경영과학' 뺌"],
    [{ desired: [], required: [{ name: '경영과학' }] }, "'경영과학' 필수로 옮김"],
    [{ minCredits: 18, maxCredits: 21 }, '학점 범위 18–21'],
    [{ excludedDays: ['금' as const] }, '금요일 공강'],
    [{ excludedTimes: [{ day: '월' as const, start: '12:00', end: '13:00' }] }, '피하고 싶은 시간 추가'],
  ])('%o → %s', (patch, expected) => {
    expect(describeChange(base, { ...base, ...patch })).toBe(expected)
  })

  it('필수 → 희망으로 옮김', () => {
    const prev: ScheduleConfig = { ...DEFAULT_CONFIG, required: [{ name: '재무관리' }] }
    expect(describeChange(prev, { ...prev, required: [], desired: [{ name: '재무관리' }] })).toBe("'재무관리' 희망으로 옮김")
  })
})
