import { AlertCircle, Bookmark, CalendarRange, ChevronLeft, ChevronRight, Loader2, Pin, Plus, Repeat2, Sparkles } from 'lucide-react'
import { useEffect, useMemo, useRef, useState, type ReactNode, type TouchEvent } from 'react'
import { Badge, Button, cx, EmptyState, IconButton, NameForm, nextName, Popover, type ToastData } from '../components/ui'
import { timeSummary } from '../engine/course'
import type { CourseData, GenerationOutput, ScheduleConfig, ScheduleResult } from '../engine/types'
import { assignColors, courseColorVars } from '../lib/courseColors'
import type { GenerationState } from '../lib/data'
import { countLabel, formatCount } from '../lib/format'
import { useConfig, useSaved, useStore, type SavedSchedule } from '../lib/store'
import { ANY, filterByPins, matchesPins, scheduleKey, type Pins, type ViewerState } from '../lib/viewer'
import { Timetable, type PreviewItem } from './Timetable'

type Notify = (message: string, action?: ToastData['action']) => void

interface ViewerProps {
  /** 강의 검색에서 고른 과목·분반 미리보기 */
  preview?: PreviewItem[] | null
  /** 보고 있는 시간표와 고정한 강의 (App 이 보관 → 재계산·탭 이동에도 유지) */
  viewer: ViewerState
  onViewerChange: (viewer: ViewerState) => void
  notify: Notify
}

export function ResultView({ generation, courses, onAddCourses, savedView, onSavedViewChange, emptyGrid, ...viewerProps }: ViewerProps & {
  generation: GenerationState
  courses: CourseData[]
  onAddCourses: () => void
  /** PC: 시간표가 없을 때도 빈 틀을 보여 줌 (강의 검색 미리보기가 보이도록) */
  emptyGrid: boolean
  /** 저장 탭에서 연 시간표 (null = 생성된 조합 보기) */
  savedView: string | null
  onSavedViewChange: (id: string | null) => void
}) {
  const saved = useSaved()
  const entry = saved.find((s) => s.id === savedView)
  const output = generation.status === 'done' ? generation.output : generation.status === 'running' ? generation.previous : null

  // 저장한 시간표는 조건·담은 강의와 상관없이 그대로 보여 줌
  if (entry) {
    return <SavedResult entry={entry} saved={saved} courses={courses} preview={viewerProps.preview} onOpen={onSavedViewChange} />
  }
  if (emptyGrid && (generation.status === 'idle' || generation.status === 'error' || !output)) {
    return (
      <EmptyGrid
        preview={viewerProps.preview}
        subtitle={
          generation.status === 'idle' ? (
            '강의를 담으면 바로 만들어져요'
          ) : generation.status === 'error' ? (
            <span className="text-danger">{generation.expected ? '시간표를 만들 수 없어요' : '오류가 발생했어요'}</span>
          ) : (
            <>
              <Loader2 size={12} className="animate-spin" /> 조합을 찾는 중
            </>
          )
        }
        notice={generation.status === 'error' && generation.message}
      />
    )
  }
  // 모바일: 흐린 빈 틀 위에 지금 상태 메시지
  if (generation.status === 'idle') {
    return (
      <FadedGrid>
        <EmptyState
          icon={<CalendarRange size={44} strokeWidth={1.25} />}
          title="강의를 담으면 바로 시간표가 만들어져요"
          action={<Button variant="primary" onClick={onAddCourses}>강의 담으러 가기</Button>}
        />
      </FadedGrid>
    )
  }
  if (generation.status === 'error') {
    return (
      <FadedGrid>
        <EmptyState
          icon={<AlertCircle size={44} strokeWidth={1.25} />}
          title={generation.expected ? '시간표를 만들 수 없어요' : '오류가 발생했어요'}
          description={<span className="whitespace-pre-line">{generation.message}</span>}
        />
      </FadedGrid>
    )
  }
  if (!output) {
    return (
      <FadedGrid>
        <div className="flex items-center justify-center gap-2 py-24 text-[15px] text-fg-muted">
          <Loader2 size={16} className="animate-spin" /> 조합을 찾는 중…
        </div>
      </FadedGrid>
    )
  }
  return <Results output={output} running={generation.status === 'running'} courses={courses} emptyGrid={emptyGrid} {...viewerProps} />
}

/** 빈 시간표 틀 (PC) — 결과가 생기면 같은 자리에 그대로 채워지도록 레이아웃을 Results 와 맞춤 */
function EmptyGrid({ subtitle, notice, preview }: { subtitle: ReactNode; notice?: ReactNode; preview?: PreviewItem[] | null }) {
  const config = useConfig()
  const showAvoid = useStore().state.showAvoid
  return (
    <div className="grid gap-x-10 gap-y-8 xl:grid-cols-[minmax(0,1fr)_280px]">
      <div className="min-w-0">
        <ResultHeader title="시간표" subtitle={subtitle} />
        <Timetable
          courses={NO_COURSES}
          colors={NO_COLORS}
          avoid={showAvoid ? { days: config.excludedDays, times: config.excludedTimes } : undefined}
          preview={preview ?? undefined}
          pinned={NO_PINS}
        />
        {notice && <p className="mt-4 rounded-md bg-surface-sunken px-3.5 py-2.5 text-[13px] whitespace-pre-line text-fg-muted">{notice}</p>}
      </div>
    </div>
  )
}

/** 흐린 빈 시간표 틀 위에 메시지 (모바일: 미리보기는 없지만 시간표 자리임을 보여 줌) */
function FadedGrid({ children }: { children: ReactNode }) {
  return (
    <div className="relative">
      <div className="pointer-events-none opacity-30" aria-hidden>
        <Timetable courses={NO_COURSES} colors={NO_COLORS} pinned={NO_PINS} />
      </div>
      <div className="absolute inset-x-0 top-8">{children}</div>
    </div>
  )
}

const NO_COURSES: CourseData[] = []
const NO_COLORS = new Map<string, number>()

function Results({ output, running, courses, viewer, onViewerChange, notify, preview, emptyGrid }: ViewerProps & {
  output: GenerationOutput
  running: boolean
  courses: CourseData[]
  emptyGrid: boolean
}) {
  const config = useConfig()
  const { state, dispatch } = useStore()
  const saved = useSaved()
  const byId = useMemo(() => new Map(courses.map((c) => [c.id, c])), [courses])
  const schedules = output.schedules
  const pins = viewer.pins
  const resolve = (s: ScheduleResult) => s.courseIds.map((id) => byId.get(id)).filter((c): c is CourseData => !!c)

  const filtered = useMemo(() => filterByPins(schedules, pins, byId), [schedules, pins, byId])
  const index = Math.max(0, viewer.key ? filtered.findIndex((s) => scheduleKey(s) === viewer.key) : 0)
  const current = filtered[index]
  const currentCourses = current ? resolve(current) : []
  const colors = useShownColors(currentCourses)
  const savedEntry = current ? saved.find((s) => s.id === scheduleKey(current)) : undefined

  const go = (delta: number) => {
    if (!filtered.length) return
    onViewerChange({ pins, key: scheduleKey(filtered[(index + delta + filtered.length) % filtered.length]) })
  }
  useArrowKeys(go)
  const swipe = useSwipe(go)

  /** 고정 조건을 바꾸되, 지금 보던 시간표가 여전히 맞으면 그대로 머묾 */
  const applyPins = (next: Pins, failMessage: string) => {
    const nextFiltered = filterByPins(schedules, next, byId)
    if (nextFiltered.length === 0) {
      notify(failMessage)
      return
    }
    const stay = viewer.key !== null && nextFiltered.some((s) => scheduleKey(s) === viewer.key)
    onViewerChange({ pins: next, key: stay ? viewer.key : scheduleKey(nextFiltered[0]) })
  }

  const unpin = (name: string) => {
    const next = new Map(pins)
    next.delete(name)
    onViewerChange({ pins: next, key: viewer.key })
  }
  const clearPins = () => onViewerChange({ pins: new Map(), key: viewer.key })

  /** 누르면 지금 분반으로 고정, 고정된 강의를 다시 누르면 해제 → 고정할수록 후보가 좁혀짐 */
  const toggleCourse = (course: CourseData) => {
    if (pins.has(course.name)) unpin(course.name)
    else applyPins(new Map(pins).set(course.name, timeSummary(course)), '고정할 수 없어요')
  }

  /** 고정한 강의를 다른 고정 조건 안에서 가능한 다음 분반으로 바꿈 */
  const cycleSection = (course: CourseData) => {
    const options = [
      ...new Set(
        schedules
          .filter((s) => matchesPins(s, pins, byId, course.name))
          .map((s) => resolve(s).find((c) => c.name === course.name))
          .filter((c): c is CourseData => !!c)
          .map(timeSummary),
      ),
    ].sort()
    if (options.length <= 1) {
      notify('다른 분반이 없어요')
      return
    }
    const next = options[(options.indexOf(timeSummary(course)) + 1) % options.length]
    applyPins(new Map(pins).set(course.name, next), '다른 분반이 없어요')
  }

  const save = (name: string) => {
    if (!current) return
    dispatch({
      type: 'saveSchedule',
      schedule: { id: scheduleKey(current), name, courseIds: current.courseIds, totalCredits: current.totalCredits, savedAt: Date.now() },
    })
    notify(`'${name}' 저장함`)
  }
  const unsave = (entry: SavedSchedule) => {
    dispatch({ type: 'removeSaved', id: entry.id })
    notify(`'${entry.name}' 저장 취소`, { label: '되돌리기', onClick: () => dispatch({ type: 'saveSchedule', schedule: entry }) })
  }

  const missingDesired = output.desiredNames.filter((n) => !currentCourses.some((c) => c.name === n))
  const requiredSet = new Set(output.requiredNames)

  return (
    <div className="grid gap-x-10 gap-y-8 xl:grid-cols-[minmax(0,1fr)_280px]">
      <div className="min-w-0">
        <ResultHeader
          title="시간표"
          subtitle={
            running ? (
              <>
                <Loader2 size={12} className="animate-spin" /> 다시 계산 중
              </>
            ) : (
              <>가능한 조합 {countLabel(schedules.length)}</>
            )
          }
          stats={current && { credits: current.totalCredits, count: currentCourses.length, config }}
          controls={
            current && (
              <>
                <SaveButton entry={savedEntry} defaultName={nextName('시간표', saved.map((s) => s.name))} taken={(name) => saved.some((s) => s.name === name)} onSave={save} onUnsave={unsave} />
                <Pager index={index} total={filtered.length} go={go} />
              </>
            )
          }
        />

        {/* 시간표 위에는 아무것도 끼워 넣지 않음 → 고정·재계산해도 시간표가 움직이지 않게 */}
        {current || emptyGrid ? (
          <div className={cx('touch-pan-y transition-opacity', running && 'opacity-50')} {...(current ? swipe : {})}>
            {/* 조합이 0개여도 PC 에서는 빈 틀 유지 (미리보기용) */}
            <Timetable
              courses={currentCourses}
              colors={colors}
              avoid={state.showAvoid ? { days: config.excludedDays, times: config.excludedTimes } : undefined}
              preview={preview ?? undefined}
              pinned={new Set(pins.keys())}
              onCourseClick={toggleCourse}
            />
          </div>
        ) : (
          <FadedGrid>
            <EmptyState
              icon={<CalendarRange size={44} strokeWidth={1.25} />}
              title="조건에 맞는 시간표가 없어요"
              description="학점 범위를 넓히거나, 공강·피하고 싶은 시간을 줄이거나, 희망 강의를 더 담아 보세요."
            />
          </FadedGrid>
        )}

        {(output.timedOut || current?.randomFilled) && (
          <div className="mt-4 space-y-2">
            {output.timedOut && (
              <p className="rounded-md bg-warning-soft px-3.5 py-2.5 text-[13px] text-warning">
                조합이 너무 많아 제한 시간 안에 찾은 결과만 보여드려요. 조건을 좁혀 보세요.
              </p>
            )}
            {current?.randomFilled && (
              <p className="flex items-center gap-2 rounded-md bg-surface-sunken px-3.5 py-2.5 text-[13px] text-fg-muted">
                <Sparkles size={14} /> 담은 강의만으로는 최소 학점을 채울 수 없어서 ‘전학년’ 교양으로 빈 시간을 채웠어요.
              </p>
            )}
          </div>
        )}
      </div>

      {current && (
        <aside className="space-y-8 xl:pt-[72px]">
          <div>
            {/* 높이 고정: '모두 해제'가 생겨도 목록이 밀리지 않게 */}
            <div className="mb-1 flex h-7 items-center justify-between">
              <p className="text-[13px] font-medium text-fg-muted">이 시간표의 강의</p>
              {pins.size > 0 && (
                <Button variant="ghost" size="sm" onClick={clearPins}>
                  고정 모두 해제
                </Button>
              )}
            </div>
            <ul className="-mx-2">
              {currentCourses.map((c) => {
                const isPinned = pins.has(c.name)
                return (
                  <li key={c.id} className="flex items-center rounded-md transition-colors hover:bg-surface-hover">
                    <button type="button" onClick={() => toggleCourse(c)} aria-pressed={isPinned} className="flex min-w-0 flex-1 text-left">
                      <CourseInfo
                        course={c}
                        color={colors.get(c.name)}
                        badge={requiredSet.has(c.name) ? <Badge tone="accent">필수</Badge> : output.desiredNames.includes(c.name) ? null : <Badge>채움</Badge>}
                      />
                    </button>
                    {isPinned && pins.get(c.name) !== ANY && (
                      <IconButton label="다른 분반으로" size="sm" className="text-accent-fg hover:text-accent-fg" onClick={() => cycleSection(c)}>
                        <Repeat2 size={15} />
                      </IconButton>
                    )}
                    {/* 고정 버튼을 항상 보여 줌: 고정하면 이 분반이 든 시간표만 남음 */}
                    <button
                      type="button"
                      onClick={() => toggleCourse(c)}
                      aria-pressed={isPinned}
                      title={isPinned ? '고정 해제' : '이 분반이 든 시간표만 보기'}
                      className={cx(
                        'mr-1 flex h-7 shrink-0 items-center gap-1 rounded-full px-2.5 text-[12px] font-medium transition-colors active:scale-95',
                        isPinned ? 'bg-accent text-fg-on-accent hover:bg-accent-hover' : 'bg-surface-sunken text-fg-muted hover:text-fg',
                      )}
                    >
                      <Pin size={12} fill={isPinned ? 'currentColor' : 'none'} />
                      {isPinned ? '고정됨' : '고정'}
                    </button>
                  </li>
                )
              })}
            </ul>
          </div>

          {missingDesired.length > 0 && (
            <div>
              <p className="mb-2 text-[13px] font-medium text-fg-muted">빠진 희망 강의</p>
              <div className="flex flex-wrap gap-1.5">
                {missingDesired.map((name) => (
                  <Button
                    key={name}
                    size="sm"
                    onClick={() => applyPins(new Map(pins).set(name, ANY), `'${name}'을(를) 넣을 수 있는 조합이 없어요`)}
                  >
                    <Plus size={12} strokeWidth={2.5} />
                    {name}
                  </Button>
                ))}
              </div>
            </div>
          )}
        </aside>
      )}
    </div>
  )
}

/** 저장한 시간표 보기: 조건과 무관하게 저장한 강의 그대로, ← → 로 저장한 것끼리 넘김 */
function SavedResult({ entry, saved, courses, preview, onOpen }: {
  entry: SavedSchedule
  saved: SavedSchedule[]
  courses: CourseData[]
  preview?: PreviewItem[] | null
  onOpen: (id: string | null) => void
}) {
  const config = useConfig()
  const showAvoid = useStore().state.showAvoid
  const byId = useMemo(() => new Map(courses.map((c) => [c.id, c])), [courses])
  const list = entry.courseIds.map((id) => byId.get(id)).filter((c): c is CourseData => !!c)
  const colors = useShownColors(list)
  const index = saved.findIndex((s) => s.id === entry.id)
  const go = (delta: number) => onOpen(saved[(index + delta + saved.length) % saved.length].id)
  useArrowKeys(go)
  const swipe = useSwipe(go)

  return (
    <div className="grid gap-x-10 gap-y-8 xl:grid-cols-[minmax(0,1fr)_280px]">
      <div className="min-w-0">
        <ResultHeader
          title={entry.name}
          subtitle={
            <>
              저장한 시간표 ·
              <button type="button" onClick={() => onOpen(null)} className="font-medium text-accent-fg hover:underline">
                조합으로 돌아가기
              </button>
            </>
          }
          stats={{ credits: entry.totalCredits, count: list.length, config }}
          controls={<Pager index={index} total={saved.length} go={go} />}
        />
        <div className="touch-pan-y" {...swipe}>
          <Timetable
            courses={list}
            colors={colors}
            avoid={showAvoid ? { days: config.excludedDays, times: config.excludedTimes } : undefined}
            preview={preview ?? undefined}
            pinned={NO_PINS}
          />
        </div>
      </div>
      <aside className="xl:pt-[72px]">
        <p className="mb-1 flex h-7 items-center text-[13px] font-medium text-fg-muted">이 시간표의 강의</p>
        <ul className="-mx-2">
          {list.map((c) => (
            <li key={c.id}>
              <CourseInfo course={c} color={colors.get(c.name)} />
            </li>
          ))}
        </ul>
      </aside>
    </div>
  )
}

const NO_PINS = new Set<string>()

/** 큰 제목 + 총 학점 + 오른쪽 조작 버튼 (조합 보기·저장 보기 공통, 높이 고정) */
function ResultHeader({ title, subtitle, stats, controls }: {
  title: string
  subtitle: ReactNode
  stats?: { credits: number; count: number; config: ScheduleConfig } | null | false
  controls?: ReactNode
}) {
  return (
    <div className="mb-5 flex flex-wrap items-end justify-between gap-x-6 gap-y-3">
      <div className="min-w-0">
        <h2 className="truncate text-[28px] leading-tight font-bold tracking-tight">{title}</h2>
        <p className="mt-0.5 flex items-center gap-1.5 text-[13px] text-fg-muted tabular-nums">{subtitle}</p>
      </div>
      {stats && (
        <div className="flex w-full items-center justify-between gap-5 sm:ml-auto sm:w-auto">
          {/* 왼쪽 제목 블록과 같은 글자 크기·줄 높이 → '시간표'↔'20학점', 설명↔'8과목' 이 같은 줄 */}
          <div className="sm:text-right">
            <p className="text-[28px] leading-tight font-bold tracking-tight tabular-nums">
              {stats.credits}
              <span className="ml-0.5 text-[15px] font-semibold text-fg-muted">학점</span>
            </p>
            <p className="mt-0.5 text-[13px] text-fg-muted tabular-nums">
              {stats.count}과목 · 목표 {stats.config.minCredits}–{stats.config.maxCredits}학점
            </p>
          </div>
          <div className="flex items-center gap-1.5">{controls}</div>
        </div>
      )}
    </div>
  )
}

function Pager({ index, total, go }: { index: number; total: number; go: (delta: number) => void }) {
  return (
    <div className="flex h-9 items-center rounded-full bg-surface-sunken px-0.5">
      <IconButton label="이전 시간표 (←)" size="sm" className="size-8" onClick={() => go(-1)}>
        <ChevronLeft size={18} strokeWidth={2.2} />
      </IconButton>
      <span className="min-w-20 text-center text-[14px] font-semibold tabular-nums">
        {(index + 1).toLocaleString()}
        <span className="font-normal text-fg-muted"> / {formatCount(total)}</span>
      </span>
      <IconButton label="다음 시간표 (→)" size="sm" className="size-8" onClick={() => go(1)}>
        <ChevronRight size={18} strokeWidth={2.2} />
      </IconButton>
    </div>
  )
}

/** 저장(북마크): 누르면 이름을 정하는 작은 창, 저장된 상태에서 누르면 저장 취소 */
function SaveButton({ entry, defaultName, taken, onSave, onUnsave }: {
  entry?: SavedSchedule
  defaultName: string
  taken: (name: string) => boolean
  onSave: (name: string) => void
  onUnsave: (entry: SavedSchedule) => void
}) {
  const [open, setOpen] = useState(false)
  return (
    <Popover
      open={open}
      onClose={() => setOpen(false)}
      trigger={
        <IconButton
          label={entry ? `저장됨: ${entry.name} (누르면 저장 취소)` : '이 시간표 저장'}
          className={cx('bg-surface-sunken', entry && 'text-accent-fg hover:text-accent-fg')}
          onClick={() => (entry ? onUnsave(entry) : setOpen((o) => !o))}
        >
          <Bookmark size={17} fill={entry ? 'currentColor' : 'none'} />
        </IconButton>
      }
    >
      <NameForm
        initial={defaultName}
        taken={taken}
        onCancel={() => setOpen(false)}
        onSubmit={(name) => {
          onSave(name)
          setOpen(false)
        }}
      />
    </Popover>
  )
}

/** 강의 한 줄: 색 점 + 과목명(+배지) + 교수·학점·시간 */
function CourseInfo({ course, color, badge }: { course: CourseData; color?: number; badge?: ReactNode }) {
  return (
    <span className="flex min-w-0 flex-1 items-start gap-2.5 px-2 py-2">
      <span className="mt-[5px] size-2.5 shrink-0 rounded-full" style={{ background: courseColorVars(color ?? 1).bar }} />
      <span className="min-w-0 flex-1">
        <span className="flex flex-wrap items-center gap-x-1.5 gap-y-0.5">
          <span className="min-w-0 text-[14px] leading-snug font-semibold tracking-tight break-keep [overflow-wrap:anywhere]">{course.name}</span>
          {badge}
        </span>
        <span className="block truncate text-[12px] text-fg-muted">
          {course.professor} · {course.credits}학점 · {timeSummary(course)}
        </span>
      </span>
    </span>
  )
}

/** 지금 보이는 시간표의 강의끼리만 색을 나눠서, 한 화면 안에서는 색이 겹치지 않게 */
function useShownColors(list: CourseData[]) {
  const names = [...new Set(list.map((c) => c.name))].join('|')
  return useMemo(() => assignColors(names ? names.split('|') : []), [names])
}

/** 터치: 시간표를 옆으로 밀면 다음(←)/이전(→) 시간표. 세로 스크롤은 그대로 */
function useSwipe(go: (delta: number) => void) {
  const start = useRef<{ x: number; y: number } | null>(null)
  return {
    onTouchStart: (e: TouchEvent) => {
      const t = e.touches[0]
      start.current = e.touches.length === 1 ? { x: t.clientX, y: t.clientY } : null
    },
    onTouchEnd: (e: TouchEvent) => {
      const from = start.current
      start.current = null
      if (!from) return
      const t = e.changedTouches[0]
      const dx = t.clientX - from.x
      const dy = t.clientY - from.y
      // 충분히 길고 가로가 뚜렷할 때만 (대각선·세로 스크롤은 무시)
      if (Math.abs(dx) > 50 && Math.abs(dx) > Math.abs(dy) * 1.5) go(dx < 0 ? 1 : -1)
    },
  }
}

/** ← → 키로 넘기기 (입력 중에는 무시) */
function useArrowKeys(go: (delta: number) => void) {
  useEffect(() => {
    const onKey = (e: KeyboardEvent) => {
      if (e.target instanceof HTMLInputElement || e.target instanceof HTMLSelectElement) return
      if (e.key === 'ArrowLeft') go(-1)
      if (e.key === 'ArrowRight') go(1)
    }
    window.addEventListener('keydown', onKey)
    return () => window.removeEventListener('keydown', onKey)
  })
}
