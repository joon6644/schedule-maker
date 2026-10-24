/** 시간표 엔진 도메인 타입 (Python schedule_maker/core 와 1:1 대응) */

export type Day = '월' | '화' | '수' | '목' | '금' | '토' | '일'

export const WEEKDAYS: Day[] = ['월', '화', '수', '목', '금']

export interface TimeSlot {
  day: Day
  start: string // HH:MM
  end: string // HH:MM
  room: string
}

/** public/data/*.json 에 저장된 강의 원본 */
export interface CourseData {
  id: string
  name: string
  credits: number
  professor: string
  category: string
  grade: string
  slots: TimeSlot[]
}

/** 엔진 내부용 강의 (충돌 검사용 비트마스크 포함) */
export interface Course extends CourseData {
  mask: bigint
  /** 같은 이름·교수·시간이면 같은 수업으로 취급하기 위한 서명 */
  signature: string
}

/** 강의 필터: 강의번호(정확히 일치) 또는 강의명/교수명(띄어쓰기 = AND) */
export interface CourseFilter {
  courseId?: string
  name?: string
  professor?: string
}

export interface ExcludedTime {
  day: Day
  start: string
  end: string
}

export interface ScheduleConfig {
  minCredits: number
  maxCredits: number
  required: CourseFilter[]
  desired: CourseFilter[]
  excludedDays: Day[]
  excludedTimes: ExcludedTime[]
}

export interface ScheduleResult {
  courseIds: string[]
  totalCredits: number
  /** 순수 조합이 없어 '전학년' 강의로 무작위로 채운 시간표 */
  randomFilled: boolean
}

export interface GenerationOutput {
  schedules: ScheduleResult[]
  /** 필수 강의 필터에 매칭된 강의명 */
  requiredNames: string[]
  /** 희망 강의 필터에 매칭된 강의명 */
  desiredNames: string[]
  elapsedMs: number
  timedOut: boolean
}

export class GenerationError extends Error {}
