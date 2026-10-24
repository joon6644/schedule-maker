import type { CourseFilter, Day, ExcludedTime, ScheduleConfig } from './types'

/**
 * 데스크톱 앱(save_config_to_json)과 호환되는 설정 JSON 형식
 * 데스크톱 앱에서 저장한 설정을 그대로 불러오거나, 웹에서 내보낸 설정을 데스크톱 앱에서 열 수 있음.
 */
interface ConfigFileCourse {
  name?: string
  professor?: string
  course_id?: string
}

export interface ConfigFile {
  min_credits: number
  max_credits: number
  required_courses: ConfigFileCourse[]
  desired_courses: ConfigFileCourse[]
  excluded_days: string[]
  excluded_time_slots: string[]
}

export const DEFAULT_CONFIG: ScheduleConfig = {
  minCredits: 15,
  maxCredits: 18,
  required: [],
  desired: [],
  excludedDays: [],
  excludedTimes: [],
}

const DAYS = new Set(['월', '화', '수', '목', '금', '토', '일'])

function parseFilters(raw: unknown): CourseFilter[] {
  if (!Array.isArray(raw)) return []
  return raw
    .filter((item): item is Record<string, unknown> => !!item && typeof item === 'object')
    .map((item) => {
      // 구버전 키(강의번호, 조건_검색) 호환
      const legacy = (item['조건_검색'] ?? {}) as Record<string, unknown>
      const filter: CourseFilter = {}
      const courseId = item.course_id ?? item['강의번호']
      const name = item.name ?? legacy['강의명']
      const professor = item.professor ?? legacy['교수명']
      if (courseId) filter.courseId = String(courseId)
      if (name) filter.name = String(name)
      if (professor) filter.professor = String(professor)
      return filter
    })
    .filter((f) => f.courseId || f.name || f.professor)
}

/** "월 09:00~10:29" → ExcludedTime */
export function parseExcludedTime(text: string): ExcludedTime | null {
  const match = text.trim().match(/^(\S)\s+(\d{1,2}:\d{2})~(\d{1,2}:\d{2})$/)
  if (!match || !DAYS.has(match[1])) return null
  const pad = (t: string) => t.padStart(5, '0')
  return { day: match[1] as Day, start: pad(match[2]), end: pad(match[3]) }
}

export function parseConfigFile(data: Record<string, unknown>): ScheduleConfig {
  const credits = (data['학점_설정'] ?? {}) as Record<string, unknown>
  const excludedRaw = (data.excluded_time_slots ?? data['제외_시간'] ?? []) as unknown[]
  const daysRaw = (data.excluded_days ?? data['제외_요일'] ?? []) as unknown[]
  return {
    minCredits: Number(data.min_credits ?? credits['최소_학점'] ?? DEFAULT_CONFIG.minCredits),
    maxCredits: Number(data.max_credits ?? credits['최대_학점'] ?? DEFAULT_CONFIG.maxCredits),
    required: parseFilters(data.required_courses ?? data['필수_강의']),
    desired: parseFilters(data.desired_courses ?? data['희망_강의']),
    excludedDays: daysRaw.map(String).filter((d): d is Day => DAYS.has(d)),
    excludedTimes: excludedRaw
      .map((t) => parseExcludedTime(String(t)))
      .filter((t): t is ExcludedTime => t !== null),
  }
}

export function toConfigFile(config: ScheduleConfig): ConfigFile {
  const toCourses = (filters: CourseFilter[]) =>
    filters.map((f) => {
      const item: ConfigFileCourse = {}
      if (f.name) item.name = f.name
      if (f.professor) item.professor = f.professor
      if (f.courseId) item.course_id = f.courseId
      return item
    })
  return {
    min_credits: config.minCredits,
    max_credits: config.maxCredits,
    required_courses: toCourses(config.required),
    desired_courses: toCourses(config.desired),
    excluded_days: config.excludedDays,
    excluded_time_slots: config.excludedTimes.map((t) => `${t.day} ${t.start}~${t.end}`),
  }
}
