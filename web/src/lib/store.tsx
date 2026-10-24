import { createContext, useContext, useEffect, useMemo, useReducer, type Dispatch, type ReactNode } from 'react'
import { sameFilter } from '../engine/course'
import { DEFAULT_CONFIG } from '../engine/config'
import type { CourseFilter, Day, ExcludedTime, ScheduleConfig } from '../engine/types'

export type ListType = 'required' | 'desired'
export type ThemePref = 'system' | 'light' | 'dark'

export interface AppState {
  /** 항상 최신 학기 (지난 학기는 보지 않음) */
  termKey: string | null
  /** 학기별 설정 (학기마다 강의가 달라서 따로 보관) */
  configs: Record<string, ScheduleConfig>
  theme: ThemePref
  /** 피하고 싶은 시간을 시간표에 빗금으로 표시 */
  showAvoid: boolean
}

export type Action =
  | { type: 'setTerm'; termKey: string }
  | { type: 'setTheme'; theme: ThemePref }
  | { type: 'setShowAvoid'; show: boolean }
  | { type: 'setLists'; required: CourseFilter[]; desired: CourseFilter[] }
  | { type: 'addFilter'; list: ListType; filter: CourseFilter }
  | { type: 'removeFilter'; list: ListType; index: number }
  | { type: 'moveFilter'; list: ListType; index: number }
  | { type: 'updateFilter'; list: ListType; index: number; filter: CourseFilter }
  | { type: 'setCredits'; min: number; max: number }
  | { type: 'toggleDay'; day: Day }
  | { type: 'addExcludedTime'; time: ExcludedTime }
  | { type: 'removeExcludedTime'; index: number }
  | { type: 'setExcludedTimes'; times: ExcludedTime[] }
  | { type: 'replaceConfig'; config: ScheduleConfig }

const STORAGE_KEY = 'schedule-maker:v1'

function loadState(): AppState {
  const fallback: AppState = { termKey: null, configs: {}, theme: 'system', showAvoid: false }
  try {
    const raw = localStorage.getItem(STORAGE_KEY)
    return raw ? { ...fallback, ...JSON.parse(raw) } : fallback
  } catch {
    return fallback
  }
}

export function configOf(state: AppState): ScheduleConfig {
  return (state.termKey && state.configs[state.termKey]) || DEFAULT_CONFIG
}

function updateConfig(state: AppState, update: (c: ScheduleConfig) => ScheduleConfig): AppState {
  if (!state.termKey) return state
  return { ...state, configs: { ...state.configs, [state.termKey]: update(configOf(state)) } }
}

function reducer(state: AppState, action: Action): AppState {
  switch (action.type) {
    case 'setTerm': {
      // 새 학기로 넘어가면 지난 학기 설정은 지움 (강의가 달라 다시 쓸 일이 없음)
      const kept = state.configs[action.termKey]
      return { ...state, termKey: action.termKey, configs: kept ? { [action.termKey]: kept } : {} }
    }
    case 'setTheme':
      return { ...state, theme: action.theme }
    case 'setShowAvoid':
      return { ...state, showAvoid: action.show }
    case 'setLists':
      return updateConfig(state, (c) => ({ ...c, required: action.required, desired: action.desired }))
    case 'addFilter':
      return updateConfig(state, (c) => {
        // 같은 필터가 이미 있으면 무시, 반대 목록에 있으면 이쪽으로 이동
        const other: ListType = action.list === 'required' ? 'desired' : 'required'
        if (c[action.list].some((f) => sameFilter(f, action.filter))) return c
        return {
          ...c,
          [action.list]: [...c[action.list], action.filter],
          [other]: c[other].filter((f) => !sameFilter(f, action.filter)),
        }
      })
    case 'removeFilter':
      return updateConfig(state, (c) => ({ ...c, [action.list]: c[action.list].filter((_, i) => i !== action.index) }))
    case 'moveFilter':
      return updateConfig(state, (c) => {
        const from = action.list
        const to: ListType = from === 'required' ? 'desired' : 'required'
        const filter = c[from][action.index]
        return { ...c, [from]: c[from].filter((_, i) => i !== action.index), [to]: [...c[to], filter] }
      })
    case 'updateFilter':
      return updateConfig(state, (c) => ({ ...c, [action.list]: c[action.list].map((f, i) => (i === action.index ? action.filter : f)) }))
    case 'setCredits':
      return updateConfig(state, (c) => ({ ...c, minCredits: action.min, maxCredits: action.max }))
    case 'toggleDay':
      return updateConfig(state, (c) => ({
        ...c,
        excludedDays: c.excludedDays.includes(action.day)
          ? c.excludedDays.filter((d) => d !== action.day)
          : [...c.excludedDays, action.day],
      }))
    case 'addExcludedTime':
      return updateConfig(state, (c) =>
        c.excludedTimes.some((t) => t.day === action.time.day && t.start === action.time.start && t.end === action.time.end)
          ? c
          : { ...c, excludedTimes: [...c.excludedTimes, action.time] },
      )
    case 'removeExcludedTime':
      return updateConfig(state, (c) => ({ ...c, excludedTimes: c.excludedTimes.filter((_, i) => i !== action.index) }))
    case 'setExcludedTimes':
      return updateConfig(state, (c) => ({ ...c, excludedTimes: action.times }))
    case 'replaceConfig':
      return updateConfig(state, () => action.config)
  }
}

const StoreContext = createContext<{ state: AppState; dispatch: Dispatch<Action> } | null>(null)

export function StoreProvider({ children }: { children: ReactNode }) {
  const [state, dispatch] = useReducer(reducer, undefined, loadState)

  useEffect(() => {
    try {
      localStorage.setItem(STORAGE_KEY, JSON.stringify(state))
    } catch {
      // 저장 공간이 막힌 환경(시크릿 모드 등)에서는 저장 없이 동작
    }
  }, [state])

  const value = useMemo(() => ({ state, dispatch }), [state])
  return <StoreContext.Provider value={value}>{children}</StoreContext.Provider>
}

export function useStore() {
  const ctx = useContext(StoreContext)
  if (!ctx) throw new Error('useStore must be used inside StoreProvider')
  return ctx
}

export function useConfig() {
  return configOf(useStore().state)
}
