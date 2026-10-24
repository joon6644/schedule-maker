import {
  DndContext,
  DragOverlay,
  KeyboardSensor,
  MouseSensor,
  pointerWithin,
  TouchSensor,
  useDraggable,
  useDroppable,
  useSensor,
  useSensors,
  type DragEndEvent,
  type DragStartEvent,
} from '@dnd-kit/core'
import { AlertTriangle, BookOpen, Check, ChevronDown, GripVertical } from 'lucide-react'
import { useMemo, useState } from 'react'
import { Button, cx, EmptyState, RemoveButton, Segmented } from '../components/ui'
import { matchesFilter, timeSummary } from '../engine/course'
import type { CourseData, CourseFilter } from '../engine/types'
import { useConfig, useStore, type ListType } from '../lib/store'

const LISTS: { type: ListType; title: string }[] = [
  { type: 'required', title: '필수 과목' },
  { type: 'desired', title: '희망 과목' },
]

type Scope = 'any' | 'professor' | 'section'

const idOf = (f: CourseFilter) => `${f.courseId ?? ''}|${f.name ?? ''}|${f.professor ?? ''}`
const labelOf = (f: CourseFilter) => f.name || `강의번호 ${f.courseId}`
const scopeOf = (f: CourseFilter): Scope => (f.courseId ? 'section' : f.professor ? 'professor' : 'any')
/** 칸 안의 순서는 의미가 없으므로 가나다순으로 */
const byName = (a: CourseFilter, b: CourseFilter) => labelOf(a).localeCompare(labelOf(b), 'ko')

/**
 * 담은 강의 — 필수 / 희망 두 칸
 * - 칸 사이는 끌어서 이동 (칸 안의 순서는 가나다 자동)
 * - 강의를 누르면 분반 지정 (상관없이 / 교수님 / 특정 분반)
 */
export function BasketPanel({ courses, onBrowse }: { courses: CourseData[]; onBrowse: () => void }) {
  const { dispatch } = useStore()
  const config = useConfig()
  const [dragging, setDragging] = useState<{ id: string; from: ListType } | null>(null)

  const sensors = useSensors(
    useSensor(MouseSensor, { activationConstraint: { distance: 5 } }),
    // 모바일: 길게 눌러서 끌기 (짧게 쓸어 넘기면 스크롤)
    useSensor(TouchSensor, { activationConstraint: { delay: 180, tolerance: 6 } }),
    useSensor(KeyboardSensor),
  )

  const onDragStart = ({ active }: DragStartEvent) => setDragging(active.data.current as { id: string; from: ListType })
  const onDragEnd = ({ active, over }: DragEndEvent) => {
    setDragging(null)
    const from = (active.data.current as { from: ListType }).from
    const to = over?.id as ListType | undefined
    if (!to || to === from) return
    const index = config[from].findIndex((f) => idOf(f) === active.id)
    if (index >= 0) dispatch({ type: 'moveFilter', list: from, index })
  }

  const draggingFilter = dragging ? config[dragging.from].find((f) => idOf(f) === dragging.id) : null
  const nameOf = (id: string | number) => [...config.required, ...config.desired].find((f) => idOf(f) === id)?.name ?? '강의'
  const accessibility = {
    screenReaderInstructions: { draggable: '스페이스바로 들어 올리고, 방향키로 다른 칸으로 옮긴 뒤 스페이스바로 놓으세요.' },
    announcements: {
      onDragStart: ({ active }: { active: { id: string | number } }) => `${nameOf(active.id)} 들어 올림`,
      onDragOver: ({ active }: { active: { id: string | number } }) => `${nameOf(active.id)} 옮기는 중`,
      onDragEnd: ({ active }: { active: { id: string | number } }) => `${nameOf(active.id)} 놓음`,
      onDragCancel: ({ active }: { active: { id: string | number } }) => `${nameOf(active.id)} 옮기기 취소`,
    },
  }

  if (config.required.length + config.desired.length === 0) {
    return (
      <EmptyState
        icon={<BookOpen size={36} strokeWidth={1.5} />}
        title="담은 강의가 없어요"
        action={<Button onClick={onBrowse}>강의 검색</Button>}
      />
    )
  }

  return (
    <DndContext accessibility={accessibility} sensors={sensors} collisionDetection={pointerWithin} onDragStart={onDragStart} onDragEnd={onDragEnd} onDragCancel={() => setDragging(null)}>
      <div className="space-y-6 px-4 pt-1 pb-6">
        {LISTS.map(({ type, title }) => (
          <FilterList key={type} type={type} title={title} filters={config[type]} courses={courses} dragging={dragging} />
        ))}
      </div>
      <DragOverlay dropAnimation={null}>
        {draggingFilter && (
          <div className="flex items-center gap-2 rounded-md bg-surface-raised py-2.5 pr-3 pl-4 shadow-lg">
            <span className="flex-1 text-[15px] font-medium">{labelOf(draggingFilter)}</span>
            <GripVertical size={16} className="text-fg-subtle" />
          </div>
        )}
      </DragOverlay>
    </DndContext>
  )
}

function FilterList({ type, title, filters, courses, dragging }: {
  type: ListType
  title: string
  filters: CourseFilter[]
  courses: CourseData[]
  dragging: { from: ListType } | null
}) {
  const { setNodeRef, isOver } = useDroppable({ id: type })
  const dropTarget = dragging && dragging.from !== type
  const sorted = useMemo(() => [...filters].sort(byName), [filters])
  return (
    <section>
      <h3 className="flex items-baseline gap-1.5 px-4 pb-1.5 text-[13px] font-medium text-fg-muted">
        {title}
        <span className="tabular-nums">{filters.length}</span>
      </h3>
      <div
        ref={setNodeRef}
        className={cx(
          'rounded-lg bg-surface-raised p-1 transition',
          dropTarget && 'ring-2 ring-accent-soft',
          dropTarget && isOver && 'ring-accent',
        )}
      >
        {sorted.length === 0 ? (
          <p className="px-3 py-3 text-[14px] text-fg-subtle">{dropTarget ? '여기에 놓기' : '비어 있음'}</p>
        ) : (
          <ul>
            {sorted.map((f, i) => {
              // 분반을 바꿔도 같은 행으로 남도록 과목명 기준 key (편집기가 닫히지 않게). 같은 과목이 둘이면 순번
              const name = labelOf(f)
              const nth = sorted.slice(0, i).filter((x) => labelOf(x) === name).length
              return <FilterRow key={`${name}#${nth}`} filter={f} list={type} courses={courses} />
            })}
          </ul>
        )}
      </div>
    </section>
  )
}

function FilterRow({ filter, list, courses }: { filter: CourseFilter; list: ListType; courses: CourseData[] }) {
  const { dispatch } = useStore()
  const config = useConfig()
  const [open, setOpen] = useState(false)
  const id = idOf(filter)
  const { attributes, listeners, setNodeRef, isDragging } = useDraggable({ id, data: { id, from: list } })

  const matched = useMemo(() => courses.filter((c) => matchesFilter(filter, c)), [filter, courses])
  const credits = [...new Set(matched.map((c) => c.credits))].sort()
  const index = config[list].findIndex((f) => idOf(f) === id)
  const remove = () => index >= 0 && dispatch({ type: 'removeFilter', list, index })
  const update = (next: CourseFilter) => index >= 0 && dispatch({ type: 'updateFilter', list, index, filter: next })

  const summary = filter.courseId
    ? (() => {
        const c = matched[0]
        return c ? `${timeSummary(c).split(',')[0]} 분반` : '분반 지정'
      })()
    : filter.professor
      ? `${filter.professor} 교수님 분반 ${matched.length}개 중`
      : matched.length > 1
        ? `분반 ${matched.length}개 중 자동`
        : '분반 1개'

  return (
    <li ref={setNodeRef} className={cx('rounded-md transition-colors', open ? 'bg-surface-sunken/60' : 'hover:bg-surface-hover', isDragging && 'opacity-40')}>
      <div className="flex items-center gap-1 py-1.5 pr-1 pl-3">
        {/* 행을 누르면 분반 편집, 끌면 다른 칸으로 이동 */}
        <button
          type="button"
          onClick={() => setOpen((o) => !o)}
          aria-expanded={open}
          className="flex min-w-0 flex-1 cursor-grab items-center gap-2 py-0.5 text-left active:cursor-grabbing"
          {...attributes}
          {...listeners}
        >
          <span className="min-w-0 flex-1">
            <span className="block text-[15px] leading-snug font-medium tracking-tight break-keep [overflow-wrap:anywhere]">{labelOf(filter)}</span>
            {matched.length === 0 ? (
              <span className="mt-0.5 flex items-center gap-1 text-[12px] text-warning">
                <AlertTriangle size={12} /> 이번 학기에 맞는 강의가 없어요
              </span>
            ) : (
              <span className="mt-0.5 block truncate text-[13px] text-fg-muted">
                {summary} · {credits.join('/')}학점
              </span>
            )}
          </span>
          <ChevronDown size={15} className={cx('shrink-0 text-fg-subtle transition-transform', open && 'rotate-180')} />
        </button>
        <RemoveButton label="빼기" onClick={remove} />
      </div>
      {open && <ScopeEditor filter={filter} courses={courses} onChange={update} />}
    </li>
  )
}

/** 분반 지정: 상관없이 / 교수님 / 특정 분반 */
function ScopeEditor({ filter, courses, onChange }: { filter: CourseFilter; courses: CourseData[]; onChange: (f: CourseFilter) => void }) {
  const name = filter.name ?? courses.find((c) => c.id === filter.courseId)?.name ?? ''
  const sections = useMemo(
    () => courses.filter((c) => c.name === name).sort((a, b) => a.professor.localeCompare(b.professor, 'ko') || timeSummary(a).localeCompare(timeSummary(b))),
    [courses, name],
  )
  const professors = [...new Set(sections.map((c) => c.professor).filter(Boolean))]
  const scope = scopeOf(filter)

  if (sections.length <= 1) return <p className="px-3 pb-3 text-[12px] text-fg-muted">이 과목은 분반이 하나예요.</p>

  const setScope = (s: Scope) => {
    if (s === 'any') onChange({ name })
    if (s === 'professor') onChange({ name, professor: filter.professor ?? sections.find((c) => c.id === filter.courseId)?.professor ?? professors[0] })
    if (s === 'section') onChange({ name, courseId: filter.courseId ?? sections.find((c) => !filter.professor || c.professor === filter.professor)?.id })
  }

  return (
    <div className="animate-fade-in space-y-2 px-3 pb-3">
      <Segmented
        size="sm"
        value={scope}
        onChange={setScope}
        options={[
          { value: 'any', label: '상관없이' },
          ...(professors.length > 1 ? [{ value: 'professor' as const, label: '교수님 지정' }] : []),
          { value: 'section', label: '분반 지정' },
        ]}
      />
      {scope === 'professor' && (
        <div className="flex flex-wrap gap-1.5">
          {professors.map((p) => {
            const on = filter.professor === p
            return (
              <button
                key={p}
                type="button"
                onClick={() => onChange({ name, professor: p })}
                className={cx('h-7 rounded-full px-3 text-[13px] transition', on ? 'bg-accent text-fg-on-accent' : 'bg-surface-raised text-fg hover:brightness-95')}
              >
                {p} <span className={on ? 'opacity-80' : 'text-fg-subtle'}>{sections.filter((c) => c.professor === p).length}</span>
              </button>
            )
          })}
        </div>
      )}
      {scope === 'section' && (
        <ul className="overflow-hidden rounded-md bg-surface-raised">
          {sections.map((c) => {
            const on = filter.courseId === c.id
            return (
              <li key={c.id}>
                <button
                  type="button"
                  onClick={() => onChange({ name, courseId: c.id })}
                  className={cx('flex w-full items-center gap-2 px-3 py-2 text-left text-[13px] transition-colors', on ? 'text-accent-fg' : 'hover:bg-surface-hover')}
                >
                  <span className="min-w-0 flex-1 truncate tabular-nums">{timeSummary(c)}</span>
                  <span className="shrink-0 text-fg-muted">{c.professor}</span>
                  {/* 같은 시간·교수의 분반이 여럿일 수 있어 번호로 구분 */}
                  <span className="shrink-0 text-[12px] text-fg-subtle tabular-nums">#{c.id}</span>
                  <Check size={14} strokeWidth={2.6} className={cx('shrink-0', on ? 'opacity-100' : 'opacity-0')} />
                </button>
              </li>
            )
          })}
        </ul>
      )}
    </div>
  )
}
