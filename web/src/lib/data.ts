import { useEffect, useRef, useState } from 'react'
import type { CourseData, GenerationOutput, ScheduleConfig } from '../engine/types'
import type { WorkerRequest, WorkerResponse } from '../engine/worker'

export interface Term {
  key: string
  year: number
  semester: number
  label: string
  count: number
}

const dataUrl = (file: string) => `${import.meta.env.BASE_URL}data/${file}`
/** 데이터 파일은 이름이 고정이라(해시 없음) 매번 서버에 확인 → 새 학기·데이터 수정이 바로 보임 (안 바뀌었으면 304) */
const fetchData = (file: string) => fetch(dataUrl(file), { cache: 'no-cache' })

export function useTerms() {
  const [terms, setTerms] = useState<Term[] | null>(null)
  const [error, setError] = useState<string | null>(null)
  useEffect(() => {
    fetchData('terms.json')
      .then((r) => (r.ok ? r.json() : Promise.reject(new Error(`HTTP ${r.status}`))))
      .then(setTerms)
      .catch((e) => setError(`학기 목록을 불러오지 못했습니다 (${e.message})`))
  }, [])
  return { terms, error }
}

export function useCourses(termKey: string | null) {
  const [state, setState] = useState<{ key: string; courses: CourseData[] } | null>(null)
  const [error, setError] = useState<string | null>(null)
  useEffect(() => {
    if (!termKey) return
    let cancelled = false
    setError(null)
    fetchData(`${termKey}.json`)
      .then((r) => (r.ok ? r.json() : Promise.reject(new Error(`HTTP ${r.status}`))))
      .then((d: { courses: CourseData[] }) => !cancelled && setState({ key: termKey, courses: d.courses }))
      .catch((e) => !cancelled && setError(`강의 데이터를 불러오지 못했습니다 (${e.message})`))
    return () => {
      cancelled = true
    }
  }, [termKey])
  const courses = state && state.key === termKey ? state.courses : null
  return { courses, error }
}

export type GenerationState =
  | { status: 'idle' }
  | { status: 'running'; found: number; previous: GenerationOutput | null }
  | { status: 'done'; output: GenerationOutput; termKey: string; config: ScheduleConfig }
  | { status: 'error'; message: string; expected: boolean; termKey: string; config: ScheduleConfig }

/** 설정이 바뀔 때마다(디바운스) 워커에서 시간표를 다시 생성 */
export function useGeneration(termKey: string | null, courses: CourseData[] | null, config: ScheduleConfig) {
  const workerRef = useRef<Worker | null>(null)
  const loadedRef = useRef<string | null>(null)
  const requestId = useRef(0)
  /** 진행 중인 요청의 학기·설정 (결과와 함께 넘겨서 되돌리기에 사용) */
  const requested = useRef<{ termKey: string; config: ScheduleConfig } | null>(null)
  const [state, setState] = useState<GenerationState>({ status: 'idle' })

  useEffect(() => {
    const worker = new Worker(new URL('../engine/worker.ts', import.meta.url), { type: 'module' })
    workerRef.current = worker
    worker.onmessage = (e: MessageEvent<WorkerResponse>) => {
      const msg = e.data
      if (msg.id !== requestId.current) return // 이미 지난 요청
      if (msg.type === 'progress') setState((s) => (s.status === 'running' ? { ...s, found: msg.found } : s))
      else if (msg.type === 'done') setState({ status: 'done', output: msg.output, ...requested.current! })
      else setState({ status: 'error', message: msg.message, expected: msg.expected, ...requested.current! })
    }
    return () => {
      worker.terminate()
      workerRef.current = null
      loadedRef.current = null
    }
  }, [])

  useEffect(() => {
    const worker = workerRef.current
    if (!worker || !termKey || !courses) return
    if (loadedRef.current !== termKey) {
      worker.postMessage({ type: 'load', termKey, courses } satisfies WorkerRequest)
      loadedRef.current = termKey
    }
    if (config.required.length === 0 && config.desired.length === 0) {
      requestId.current++
      setState({ status: 'idle' })
      return
    }
    const id = ++requestId.current
    const timer = setTimeout(() => {
      setState((s) => ({ status: 'running', found: 0, previous: s.status === 'done' ? s.output : s.status === 'running' ? s.previous : null }))
      requested.current = { termKey, config }
      worker.postMessage({ type: 'generate', id, termKey, config } satisfies WorkerRequest)
    }, 250)
    return () => clearTimeout(timer)
  }, [termKey, courses, config])

  return state
}
