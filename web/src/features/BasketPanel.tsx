import {
  closestCenter,
  DndContext,
  DragOverlay,
  KeyboardSensor,
  MouseSensor,
  TouchSensor,
  useDroppable,
  useSensor,
  useSensors,
  type DragEndEvent,
  type DragOverEvent,
  type DragStartEvent,
} from '@dnd-kit/core'
import { arrayMove, SortableContext, sortableKeyboardCoordinates, useSortable, verticalListSortingStrategy } from '@dnd-kit/sortable'
import { CSS } from '@dnd-kit/utilities'
import { AlertTriangle, BookOpen, GripVertical, Minus } from 'lucide-react'
import { useEffect, useMemo, useState } from 'react'
import { Button, cx, EmptyState } from '../components/ui'
import { matchesFilter } from '../engine/course'
import type { CourseData, CourseFilter } from '../engine/types'
import { useConfig, useStore, type ListType } from '../lib/store'
import { Dot } from './SearchPanel'

type Lists = Record<ListType, CourseFilter[]>

const LISTS: { type: ListType; title: string; hint: string }[] = [
  { type: 'required', title: '필수 강의', hint: '모든 시간표에 반드시 포함돼요.' },
  { type: 'desired', title: '희망 강의', hint: '학점 범위 안에서 가능한 만큼 조합해요.' },
]

/** 두 목록을 오가도 변하지 않는 항목 id */
const idOf = (f: CourseFilter) => `${f.courseId ?? ''}|${f.name ?? ''}|${f.professor ?? ''}`

export function BasketPanel({ courses, onBrowse }: { courses: CourseData[]; onBrowse: () => void }) {
  const { dispatch } = useStore()
  const config = useConfig()
  // 끄는 동안은 로컬 상태로만 움직이고, 놓을 때 한 번만 반영 (재계산이 계속 일어나지 않도록)
  const [lists, setLists] = useState<Lists>({ required: config.required, desired: config.desired })
  const [activeId, setActiveId] = useState<string | null>(null)
  useEffect(() => {
    if (!activeId) setLists({ required: config.required, desired: config.desired })
  }, [config.required, config.desired, activeId])

  const sensors = useSensors(
    useSensor(MouseSensor, { activationConstraint: { distance: 4 } }),
    // 모바일: 길게 눌러서 끌기 (짧게 쓸어 넘기면 스크롤)
    useSensor(TouchSensor, { activationConstraint: { delay: 180, tolerance: 6 } }),
    useSensor(KeyboardSensor, { coordinateGetter: sortableKeyboardCoordinates }),
  )

  const containerOf = (id: string): ListType | null =>
    id === 'required' || id === 'desired'
      ? id
      : lists.required.some((f) => idOf(f) === id)
        ? 'required'
        : lists.desired.some((f) => idOf(f) === id)
          ? 'desired'
          : null

  const onDragStart = ({ active }: DragStartEvent) => setActiveId(String(active.id))

  /** 다른 목록 위로 끌고 가면 그 자리로 옮겨 보여줌 */
  const onDragOver = ({ active, over }: DragOverEvent) => {
    if (!over) return
    const from = containerOf(String(active.id))
    const to = containerOf(String(over.id))
    if (!from || !to || from === to) return
    setLists((prev) => {
      const item = prev[from].find((f) => idOf(f) === active.id)
      if (!item) return prev
      const overIndex = prev[to].findIndex((f) => idOf(f) === over.id)
      const at = overIndex < 0 ? prev[to].length : overIndex
      return {
        ...prev,
        [from]: prev[from].filter((f) => idOf(f) !== active.id),
        [to]: [...prev[to].slice(0, at), item, ...prev[to].slice(at)],
      }
    })
  }

  const onDragEnd = ({ active, over }: DragEndEvent) => {
    setActiveId(null)
    let next = lists
    const list = containerOf(String(active.id))
    if (over && list && containerOf(String(over.id)) === list) {
      const from = lists[list].findIndex((f) => idOf(f) === active.id)
      const to = lists[list].findIndex((f) => idOf(f) === over.id)
      if (from >= 0 && to >= 0 && from !== to) next = { ...lists, [list]: arrayMove(lists[list], from, to) }
    }
    if (next.required !== config.required || next.desired !== config.desired) {
      dispatch({ type: 'setLists', required: next.required, desired: next.desired })
    }
  }

  const activeFilter = activeId ? [...lists.required, ...lists.desired].find((f) => idOf(f) === activeId) : null

  // 화면 낭독기 안내 (기본값은 영어)
  const nameOf = (id: string | number) => [...lists.required, ...lists.desired].find((f) => idOf(f) === id)?.name ?? '강의'
  const accessibility = {
    screenReaderInstructions: { draggable: '스페이스바로 들어 올리고, 방향키로 옮긴 뒤 스페이스바로 놓으세요. Esc 로 취소합니다.' },
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
        description="강의 검색에서 듣고 싶은 강의를 필수 또는 희망으로 담아 보세요."
        action={<Button onClick={onBrowse}>강의 검색</Button>}
      />
    )
  }

  return (
    <DndContext
      accessibility={accessibility}
      sensors={sensors}
      collisionDetection={closestCenter}
      onDragStart={onDragStart}
      onDragOver={onDragOver}
      onDragEnd={onDragEnd}
      onDragCancel={() => setActiveId(null)}
    >
      <div className="space-y-6 px-4 pt-1 pb-6">
        {LISTS.map(({ type, title, hint }) => (
          <FilterList key={type} type={type} title={title} hint={hint} filters={lists[type]} courses={courses} activeId={activeId} />
        ))}
        <p className="px-4 text-[12px] text-fg-subtle">끌어서 순서를 바꾸거나 필수 ↔ 희망으로 옮길 수 있어요.</p>
      </div>
      <DragOverlay>{activeFilter && <FilterRow filter={activeFilter} courses={courses} overlay />}</DragOverlay>
    </DndContext>
  )
}

/** inset grouped 리스트 — 구분선 없이 여백으로 행을 나눔. 빈 목록에도 놓을 수 있음 */
function FilterList({ type, title, hint, filters, courses, activeId }: {
  type: ListType
  title: string
  hint: string
  filters: CourseFilter[]
  courses: CourseData[]
  activeId: string | null
}) {
  const { setNodeRef, isOver } = useDroppable({ id: type })
  return (
    <section>
      <h3 className="flex items-center gap-1.5 px-4 pb-1.5 text-[13px] font-medium text-fg-muted">
        <Dot tone={type} />
        {title}
        <span className="tabular-nums">{filters.length}</span>
      </h3>
      <div ref={setNodeRef} className={cx('rounded-lg bg-surface-raised p-1.5 transition-shadow', isOver && activeId && 'ring-2 ring-accent-soft')}>
        <SortableContext items={filters.map(idOf)} strategy={verticalListSortingStrategy}>
          {filters.length === 0 ? (
            <p className="px-3 py-3 text-[14px] text-fg-subtle">{activeId ? '여기에 놓기' : '비어 있음'}</p>
          ) : (
            <ul>
              {filters.map((f) => (
                <SortableRow key={idOf(f)} filter={f} list={type} courses={courses} />
              ))}
            </ul>
          )}
        </SortableContext>
      </div>
      <p className="px-4 pt-1.5 text-[12px] text-fg-muted">{hint}</p>
    </section>
  )
}

function SortableRow({ filter, list, courses }: { filter: CourseFilter; list: ListType; courses: CourseData[] }) {
  const { dispatch } = useStore()
  const config = useConfig()
  const { attributes, listeners, setNodeRef, transform, transition, isDragging } = useSortable({ id: idOf(filter) })
  const remove = () => {
    const index = config[list].findIndex((f) => idOf(f) === idOf(filter))
    if (index >= 0) dispatch({ type: 'removeFilter', list, index })
  }
  return (
    <li
      ref={setNodeRef}
      style={{ transform: CSS.Transform.toString(transform), transition }}
      className={cx('touch-manipulation', isDragging && 'opacity-30')}
      {...attributes}
      {...listeners}
    >
      <FilterRow filter={filter} courses={courses} onRemove={remove} />
    </li>
  )
}

function FilterRow({ filter, courses, onRemove, overlay }: {
  filter: CourseFilter
  courses: CourseData[]
  onRemove?: () => void
  overlay?: boolean
}) {
  const matched = useMemo(() => courses.filter((c) => matchesFilter(filter, c)), [filter, courses])
  const credits = [...new Set(matched.map((c) => c.credits))].sort()
  return (
    <div
      className={cx(
        'group flex cursor-grab items-center gap-3 rounded-md px-2.5 py-2 transition-colors active:cursor-grabbing',
        overlay ? 'bg-surface-raised shadow-lg' : 'hover:bg-surface-hover',
      )}
    >
      {/* iOS 편집 모드의 빨간 빼기 버튼 (누를 때 끌기가 시작되지 않도록) */}
      <button
        type="button"
        aria-label="빼기"
        title="빼기"
        onClick={onRemove}
        onPointerDown={(e) => e.stopPropagation()}
        onMouseDown={(e) => e.stopPropagation()}
        onTouchStart={(e) => e.stopPropagation()}
        className="flex size-[22px] shrink-0 items-center justify-center rounded-full bg-required text-fg-on-accent transition active:scale-90"
      >
        <Minus size={14} strokeWidth={3} />
      </button>
      <div className="min-w-0 flex-1">
        <p className="text-[15px] leading-snug font-medium tracking-tight break-keep [overflow-wrap:anywhere]">
          {filter.name || `강의번호 ${filter.courseId}`}
          {filter.courseId && <span className="ml-1.5 text-[12px] font-normal text-fg-subtle">#{filter.courseId}</span>}
        </p>
        {matched.length === 0 ? (
          <p className="mt-0.5 flex items-center gap-1 text-[12px] text-warning">
            <AlertTriangle size={12} /> 이번 학기에 맞는 강의가 없어요
          </p>
        ) : (
          <p className="mt-0.5 truncate text-[13px] text-fg-muted">
            {filter.courseId
              ? '이 분반만'
              : filter.professor
                ? `${filter.professor} 교수님 분반 ${matched.length}개`
                : matched.length > 1
                  ? `분반 ${matched.length}개 중 자동 선택`
                  : '분반 1개'}
            {' · '}
            {credits.join('/')}학점
          </p>
        )}
      </div>
      {/* 끌 수 있다는 표시 */}
      <GripVertical size={16} className="shrink-0 text-fg-subtle opacity-60 group-hover:opacity-100" aria-hidden />
    </div>
  )
}
