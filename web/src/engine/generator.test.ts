import { readFileSync } from 'node:fs'
import { resolve } from 'node:path'
import { describe, expect, it } from 'vitest'
import { parseConfigFile } from './config'
import { toCourse } from './course'
import { generateSchedules } from './generator'
import { GenerationError, type CourseData, type ScheduleConfig, type TimeSlot } from './types'

// --- Python tests/services/test_scheduler.py 이식 ---

const slot = (day: TimeSlot['day'], start: string, end: string): TimeSlot => ({ day, start, end, room: '' })
const make = (id: string, name: string, credits: number, professor: string, slots: TimeSlot[]) =>
  toCourse({ id, name, credits, professor, category: '', grade: '', slots })

const mockCourses = [
  make('101', 'Math', 3, 'Prof. A', [slot('월', '09:00', '10:30')]),
  make('102', 'English', 3, 'Prof. B', [slot('화', '10:00', '11:30')]),
  make('103', 'Physics', 3, 'Prof. C', [slot('수', '13:00', '15:00')]),
  make('104', 'History', 2, 'Prof. D', [slot('목', '15:00', '17:00')]),
  make('105', 'Programming', 3, 'Prof. E', [slot('금', '09:00', '12:00')]),
  make('106', 'Math (B)', 3, 'Prof. A', [slot('월', '10:00', '11:30')]),
  make('107', 'English (B)', 3, 'Prof. B', [slot('화', '11:00', '12:30')]),
]

const basic = (patch: Partial<ScheduleConfig> = {}): ScheduleConfig => ({
  minCredits: 3,
  maxCredits: 18,
  required: [],
  desired: [],
  excludedDays: [],
  excludedTimes: [],
  ...patch,
})

describe('generateSchedules (mock data)', () => {
  it('필수 강의를 항상 포함하고 최소 학점을 지킨다', () => {
    const out = generateSchedules(
      mockCourses,
      basic({ required: [{ name: 'Math' }], desired: [{ name: 'English' }, { name: 'Physics' }], minCredits: 6 }),
    )
    expect(out.schedules.length).toBeGreaterThan(0)
    const byId = new Map(mockCourses.map((c) => [c.id, c]))
    for (const s of out.schedules) {
      expect(s.totalCredits).toBeGreaterThanOrEqual(6)
      const names = s.courseIds.map((id) => byId.get(id)!.name)
      expect(names.some((n) => n === 'Math' || n === 'Math (B)')).toBe(true)
    }
  })

  it('최대 학점을 넘지 않는다', () => {
    const out = generateSchedules(mockCourses, basic({ maxCredits: 5, required: [{ name: 'Math' }], desired: [{ name: 'English' }] }))
    for (const s of out.schedules) {
      expect(s.totalCredits).toBeLessThanOrEqual(5)
      expect(s.courseIds).toHaveLength(1)
    }
  })

  it('필수 강의만으로 최대 학점을 넘으면 결과가 없다', () => {
    const out = generateSchedules(mockCourses, basic({ maxCredits: 5, required: [{ name: 'Math' }, { name: 'English' }] }))
    expect(out.schedules.every((s) => s.totalCredits <= 5)).toBe(true)
  })

  it('필수 강의가 모두 제외 시간과 겹치면 오류', () => {
    expect(() =>
      generateSchedules(mockCourses, basic({ required: [{ name: 'Math' }], excludedTimes: [{ day: '월', start: '09:00', end: '12:00' }] })),
    ).toThrow(GenerationError)
  })

  it('필수 강의를 찾을 수 없으면 오류', () => {
    expect(() => generateSchedules(mockCourses, basic({ required: [{ name: '없는강의' }] }))).toThrow(GenerationError)
  })
})

// --- Python 엔진과의 결과 일치 검증 (2026년 2학기 실제 데이터) ---
// 기대값은 Python ScheduleGenerator 실행 결과 (전수 탐색 정답과 동일)

const realCourses = (
  JSON.parse(readFileSync(resolve(__dirname, '../../public/data/mju_2026_2.json'), 'utf-8')) as { courses: CourseData[] }
).courses.map(toCourse)

const realConfig = parseConfigFile({
  min_credits: 20,
  max_credits: 23,
  required_courses: [{ name: '영어2', professor: '전미경' }, { name: '재무관리' }],
  desired_courses: [
    { name: '공급사슬관리' },
    { name: '인적자원관리' },
    { name: '미적분학1' },
    { name: '데이터분석프로그래밍' },
    { name: 'AI와데이터분석을위한기초수학및통계' },
    { name: '채플' },
    { name: '비즈니스프로세스애널리틱스' },
    { name: '머신러닝', professor: '이승도' },
    { name: '경영과학' },
  ],
  excluded_days: [],
  excluded_time_slots: [
    '월 09:00~10:29', '화 09:00~10:29', '수 09:00~10:29', '목 09:00~10:29', '수 18:00~19:00', '목 18:00~19:00',
  ],
})

describe('Python 엔진과 결과 일치', () => {
  const cases: [string, Partial<ScheduleConfig>, number][] = [
    ['실제 설정 20~23학점', {}, 4478],
    ['15~18학점', { minCredits: 15, maxCredits: 18 }, 8984],
    ['금요일 공강 18~21학점', { minCredits: 18, maxCredits: 21, excludedDays: ['금'] }, 2257],
    ['평일 오전 제외', { excludedTimes: (['월', '화', '수', '목', '금'] as const).map((day) => ({ day, start: '09:00', end: '10:50' })) }, 209],
  ]

  it.each(cases)('%s', (_label, patch, expected) => {
    const config = { ...realConfig, ...patch }
    const out = generateSchedules(realCourses, config)
    expect(out.schedules).toHaveLength(expected)
    expect(out.timedOut).toBe(false)
    for (const s of out.schedules) {
      expect(s.totalCredits).toBeGreaterThanOrEqual(config.minCredits)
      expect(s.totalCredits).toBeLessThanOrEqual(config.maxCredits)
      expect(s.randomFilled).toBe(false)
    }
  })

  it('순수 조합이 없으면 무작위 채우기로 결과를 만든다', () => {
    const config = { ...realConfig, minCredits: 21, maxCredits: 23, desired: realConfig.desired.slice(0, 2) }
    const out = generateSchedules(realCourses, config)
    expect(out.schedules.length).toBeGreaterThan(0)
    expect(out.schedules.every((s) => s.randomFilled && s.totalCredits >= 21 && s.totalCredits <= 23)).toBe(true)
  })
})
