import { createContext, useContext, useEffect, useMemo, useReducer, type Dispatch, type ReactNode } from 'react'
import { sameFilter } from '../engine/course'
import { DEFAULT_CONFIG } from '../engine/config'
import type { CourseFilter, Day, ExcludedTime, ScheduleConfig } from '../engine/types'

export type ListType = 'required' | 'desired'
export type ThemePref = 'system' | 'light' | 'dark'

/** 이름을 붙여 저장한 시간표 (강의 조합 그대로 보관 → 조건이 바뀌어도 다시 볼 수 있음) */
export interface SavedSchedule {
  /** scheduleKey (정렬한 강좌번호) — 같은 조합은 한 번만 저장 */
  id: string
  name: string
  courseIds: string[]
  totalCredits: number
  savedAt: number
}

/** 이름 붙여 저장한 조건 = 담은 강의 + 학점·공강·피하고 싶은 시간 한 묶음 */
export interface ConditionPreset {
  id: string
  name: string
  config: ScheduleConfig
}

export interface AppState {
  /** 항상 최신 학기 (지난 학기는 보지 않음) */
  termKey: string | null
  /** 학기별 설정 (학기마다 강의가 달라서 따로 보관) */
  configs: Record<string, ScheduleConfig>
  /** 학기별 저장한 시간표 */
  saved: Record<string, SavedSchedule[]>
  /** 학기별 저장한 조건 (담은 강의가 학기마다 달라서 학기별) */
  presets: Record<string, ConditionPreset[]>
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
  | { type: 'saveSchedule'; schedule: SavedSchedule }
  | { type: 'renameSaved'; id: string; name: string }
  | { type: 'removeSaved'; id: string }
  | { type: 'savePreset'; preset: ConditionPreset }
  | { type: 'renamePreset'; id: string; name: string }
  | { type: 'removePreset'; id: string }

const STORAGE_KEY = 'schedule-maker:v1'

function loadState(): AppState {
  const fallback: AppState = { termKey: null, configs: {}, saved: {}, presets: {}, theme: 'system', showAvoid: false }
  try {
    const raw = localStorage.getItem(STORAGE_KEY)
    if (!raw) return fallback
    const loaded = { ...fallback, ...JSON.parse(raw) }
    // 예전 형식(학기 구분 없는 조건 목록)은 버림
    if (Array.isArray(loaded.presets)) loaded.presets = {}
    return loaded
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
      const only = <T,>(record: Record<string, T>) => (record[action.termKey] ? { [action.termKey]: record[action.termKey] } : {})
      return { ...state, termKey: action.termKey, configs: kept ? { [action.termKey]: kept } : {}, saved: only(state.saved), presets: only(state.presets) }
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
    case 'saveSchedule':
      // 같은 조합이나 같은 이름이면 덮어씀
      return updateSaved(state, (list) =>
        [...list.filter((x) => x.id !== action.schedule.id && x.name !== action.schedule.name), action.schedule].sort((a, b) => a.savedAt - b.savedAt),
      )
    case 'renameSaved':
      return updateSaved(state, (list) => list.map((x) => (x.id === action.id ? { ...x, name: action.name } : x)))
    case 'removeSaved':
      return updateSaved(state, (list) => list.filter((x) => x.id !== action.id))
    case 'savePreset':
      // 같은 이름이면 덮어씀 (확인은 NameForm 에서)
      return updatePresets(state, (list) => [...list.filter((p) => p.id !== action.preset.id && p.name !== action.preset.name), action.preset])
    case 'renamePreset':
      return updatePresets(state, (list) => list.map((p) => (p.id === action.id ? { ...p, name: action.name } : p)))
    case 'removePreset':
      return updatePresets(state, (list) => list.filter((p) => p.id !== action.id))
  }
}

function updatePresets(state: AppState, update: (list: ConditionPreset[]) => ConditionPreset[]): AppState {
  if (!state.termKey) return state
  return { ...state, presets: { ...state.presets, [state.termKey]: update(state.presets[state.termKey] ?? []) } }
}

function updateSaved(state: AppState, update: (list: SavedSchedule[]) => SavedSchedule[]): AppState {
  if (!state.termKey) return state
  return { ...state, saved: { ...state.saved, [state.termKey]: update(state.saved[state.termKey] ?? []) } }
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

const NO_SAVED: SavedSchedule[] = []
export function useSaved() {
  const { state } = useStore()
  return (state.termKey && state.saved[state.termKey]) || NO_SAVED
}

const NO_PRESETS: ConditionPreset[] = []
export function usePresets() {
  const { state } = useStore()
  return (state.termKey && state.presets[state.termKey]) || NO_PRESETS
}
