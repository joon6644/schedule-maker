/// <reference lib="webworker" />
/** 시간표 생성을 UI 스레드 밖에서 실행 (탐색 중에도 화면이 멈추지 않음) */
import { toCourse } from './course'
import { generateSchedules } from './generator'
import { GenerationError, type Course, type CourseData, type GenerationOutput, type ScheduleConfig } from './types'

export type WorkerRequest =
  | { type: 'load'; termKey: string; courses: CourseData[] }
  | { type: 'generate'; id: number; termKey: string; config: ScheduleConfig }

export type WorkerResponse =
  | { type: 'progress'; id: number; found: number }
  | { type: 'done'; id: number; output: GenerationOutput }
  | { type: 'error'; id: number; message: string; expected: boolean }

const cache = new Map<string, Course[]>()

self.onmessage = (event: MessageEvent<WorkerRequest>) => {
  const msg = event.data
  if (msg.type === 'load') {
    cache.set(msg.termKey, msg.courses.map(toCourse))
    return
  }

  const post = (res: WorkerResponse) => self.postMessage(res)
  const courses = cache.get(msg.termKey)
  if (!courses) {
    post({ type: 'error', id: msg.id, message: '강의 데이터가 아직 로드되지 않았습니다.', expected: false })
    return
  }
  try {
    const output = generateSchedules(courses, msg.config, {
      onProgress: (found) => post({ type: 'progress', id: msg.id, found }),
    })
    post({ type: 'done', id: msg.id, output })
  } catch (err) {
    post({
      type: 'error',
      id: msg.id,
      message: err instanceof Error ? err.message : String(err),
      expected: err instanceof GenerationError,
    })
  }
}
